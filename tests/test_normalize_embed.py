"""The two stages between a fetched document and a searchable vector.

Normalization is the second redaction gate, and the one that matters: the first
lives in each connector and depends on every present and future connector having
remembered. Embedding is where determinism stops being a nicety — the index is
keyed by content hash, so an embedder that drifts between processes silently
invalidates every cached vector.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from oodarag.embed.base import EmbeddingCache, cosine
from oodarag.embed.hashing import HashingEmbedder
from oodarag.models import RawDocument
from oodarag.normalize import Normalizer

FAKE_TOKENS = [
    # Shaped like the real thing, generated here, valid nowhere.
    ("github", "ghp_" + "A1b2C3d4E5f6G7h8I9j0" + "K1L2M3"),
    ("anthropic", "sk-ant-" + "api03-" + "z" * 24),
    ("aws", "AKIA" + "IOSFODNN7EXAMPLE"[:16]),
    ("slack", "xoxb-" + "1111111111-2222222222-abcdefghijklmnop"),
]

BODY = (
    "Retrieval systems fuse a lexical arm and a dense arm so that exact "
    "identifiers and paraphrase are both reachable. The index is a file that "
    "gets copied between machines, which is why credentials must never reach it. "
    "Chunk boundaries follow document structure rather than a fixed stride."
)


def _raw(text: str, **meta) -> RawDocument:
    return RawDocument(source_system="files", external_id=meta.pop("eid", "d1"),
                       uri=meta.pop("uri", "file:///d1.md"), title="Notes",
                       text=text, metadata=meta)


class RedactionIsUnavoidable(unittest.TestCase):
    def test_no_credential_shape_survives_normalization(self) -> None:
        for family, token in FAKE_TOKENS:
            with self.subTest(family=family):
                doc = Normalizer().normalize(_raw(f"{BODY}\n\nkey: {token}\n"))
                self.assertIsNotNone(doc)
                self.assertNotIn(token, doc.text,
                                 f"a {family}-shaped credential reached a Document")

    def test_the_surrounding_text_survives(self) -> None:
        # Redaction that ate the document would be safe and useless.
        doc = Normalizer().normalize(_raw(f"{BODY}\n\nkey: {FAKE_TOKENS[0][1]}\n"))
        self.assertIn("Chunk boundaries follow document structure", doc.text)

    def test_a_private_key_block_does_not_survive(self) -> None:
        pem = ("-----BEGIN RSA PRIVATE KEY-----\n" + "QUJDREVG\n" * 4 +
               "-----END RSA PRIVATE KEY-----")
        doc = Normalizer().normalize(_raw(f"{BODY}\n\n{pem}\n"))
        self.assertNotIn("BEGIN RSA PRIVATE KEY", doc.text)


class WhatGetsDropped(unittest.TestCase):
    def test_a_thin_document_is_dropped(self) -> None:
        # Thin pages poison term statistics and answer nothing.
        self.assertIsNone(Normalizer(min_words=25).normalize(_raw("Redirecting...")))

    def test_a_substantial_document_is_kept(self) -> None:
        self.assertIsNotNone(Normalizer(min_words=25).normalize(_raw(BODY)))

    def test_identical_content_is_deduped(self) -> None:
        n = Normalizer()
        docs, report = n.normalize_all([_raw(BODY, eid="a", uri="file:///a.md"),
                                        _raw(BODY, eid="b", uri="file:///b.md")])
        self.assertEqual(len(docs), 1, "the same text was indexed twice")
        self.assertEqual(report.dropped_duplicate, 1)

    def test_a_shared_canonical_url_is_deduped(self) -> None:
        # Docs sites serve one page under /latest/, /stable/ and /3.11/.
        n = Normalizer()
        docs, _ = n.normalize_all([
            _raw(BODY, eid="a", uri="file:///latest.md", canonical="https://x/doc"),
            _raw(BODY + " Extra sentence to change the hash.", eid="b",
                 uri="file:///stable.md", canonical="https://x/doc"),
        ])
        self.assertEqual(len(docs), 1, "two URLs with one canonical were both kept")

    def test_the_report_accounts_for_every_document(self) -> None:
        n = Normalizer(min_words=25)
        _, report = n.normalize_all([_raw(BODY, eid="a", uri="file:///a.md"),
                                     _raw(BODY, eid="b", uri="file:///b.md"),
                                     _raw("too short", eid="c", uri="file:///c.md")])
        self.assertEqual(report.seen, 3)
        self.assertEqual(report.kept + report.dropped_thin + report.dropped_duplicate,
                         report.seen, f"report does not balance: {report.as_dict()}")


class EmbedderDeterminism(unittest.TestCase):
    def test_two_constructions_agree_exactly(self) -> None:
        # The index is keyed by content hash. An embedder that drifts between
        # processes invalidates every cached vector without saying so.
        a, b = HashingEmbedder(dim=256), HashingEmbedder(dim=256)
        self.assertEqual(a.embed_one("hybrid retrieval"), b.embed_one("hybrid retrieval"))

    def test_vectors_with_content_are_l2_normalized(self) -> None:
        for text in ("hybrid retrieval", "chunking", BODY):
            with self.subTest(text=text[:20]):
                norm = sum(x * x for x in HashingEmbedder(dim=256).embed_one(text)) ** 0.5
                self.assertAlmostEqual(norm, 1.0, places=6)

    def test_content_free_text_embeds_to_zero_rather_than_noise(self) -> None:
        # "a", "" and a string of pure stopwords all tokenize to nothing. A zero
        # vector is the honest representation of that: it matches everything
        # equally badly. Inventing a unit vector for it would make empty input
        # rank against real documents.
        e = HashingEmbedder(dim=256)
        for text in ("a", "", "   ", "the and of"):
            with self.subTest(text=repr(text)):
                self.assertEqual(sum(abs(x) for x in e.embed_one(text)), 0.0)

    def test_a_zero_vector_does_not_break_similarity(self) -> None:
        # The safety half. A content-free query reaching the dense arm must
        # score zero, not raise a ZeroDivisionError mid-retrieval.
        e = HashingEmbedder(dim=256)
        empty, real = e.embed_one(""), e.embed_one("chunking")
        self.assertEqual(cosine(empty, real), 0.0)
        self.assertEqual(cosine(empty, empty), 0.0)

    def test_dimension_is_respected(self) -> None:
        for dim in (64, 256, 512):
            with self.subTest(dim=dim):
                self.assertEqual(len(HashingEmbedder(dim=dim).embed_one("text")), dim)

    def test_batch_and_single_agree(self) -> None:
        e = HashingEmbedder(dim=256)
        texts = ["hybrid retrieval", "chunk boundaries", "secret redaction"]
        self.assertEqual(e.embed(texts), [e.embed_one(t) for t in texts])

    def test_related_text_scores_above_unrelated(self) -> None:
        e = HashingEmbedder(dim=512)
        q = e.embed_one("how are chunk boundaries chosen")
        near = e.embed_one("Chunk boundaries follow document structure.")
        far = e.embed_one("Interest rates fell across the eurozone last quarter.")
        self.assertGreater(cosine(q, near), cosine(q, far))

    def test_subword_robustness_beats_an_unrelated_string(self) -> None:
        # Character n-grams are why the dense arm survives typos, which is the
        # entire basis of the fusion invariant.
        e = HashingEmbedder(dim=512)
        q = e.embed_one("chunking")
        self.assertGreater(cosine(q, e.embed_one("chunked")),
                           cosine(q, e.embed_one("eurozone")))


class CacheDegradesQuietly(unittest.TestCase):
    def test_a_corrupt_cache_file_is_treated_as_empty(self) -> None:
        # A cache is an optimisation. Losing one must never be an outage.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cache.json"
            path.write_text("{not json at all,,,")
            cache = EmbeddingCache(path)          # must not raise
            self.assertIsNone(cache.get("model", "deadbeef"))

    def test_a_round_trip_returns_the_vector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = EmbeddingCache(Path(tmp) / "cache.json")
            cache.put("model", "hash1", [0.5, 0.5])
            self.assertEqual(cache.get("model", "hash1"), [0.5, 0.5])

    def test_a_miss_is_none_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(EmbeddingCache(Path(tmp) / "c.json").get("model", "absent"))

    def test_it_survives_a_file_that_is_valid_json_but_wrong_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cache.json"
            path.write_text(json.dumps(["not", "a", "mapping"]))
            self.assertIsNone(EmbeddingCache(path).get("model", "deadbeef"))


if __name__ == "__main__":
    unittest.main()
