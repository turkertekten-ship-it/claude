"""Tests for chunking and embedding.

The happy path here is nearly self-evident and nearly worthless. What these
tests are actually for is the set of inputs that quietly produce a broken index:
a fenced code block cut in half, a table row split so the columns shift, a
document that is nothing but headings, a 200k-character line with nothing to cut
on, CRLF, Turkish casing, and - on the embedding side - every way a hosted
provider can fail while still returning HTTP 200.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from oodarag.chunk import build_context_header, chunk_document, fold, verify_spans
from oodarag.embed.hashing import HAS_NUMPY, HashingEmbedder, cosine, l2_normalize
from oodarag.embed.provider import (
    EmbeddingCache,
    HostedEmbedder,
    _parse_embeddings,
    get_embedder,
)
from oodarag.models import Document
from oodarag.util.http import HttpError, Response, TransportError
from oodarag.util.text import estimate_tokens

SRC = str(Path(__file__).resolve().parents[1] / "src")


def make_doc(text: str, *, title: str = "Test Document", doc_id: str = "doc-1") -> Document:
    return Document(
        doc_id=doc_id,
        source_system="web",
        external_id="ext-1",
        uri="https://example.invalid/a",
        title=title,
        text=text,
        content_hash="deadbeef",
    )


PROSE = "\n\n".join(
    f"Paragraf {i} burada duruyor ve bu cumle yeterince uzun olsun diye biraz daha yaziliyor. "
    f"Ikinci cumle de var, cunku tek cumlelik paragraflar bolme mantigini test etmez."
    for i in range(12)
)

MARKDOWN = f"""# Ana Baslik

Giris paragrafi. Kisa ama anlamli.

## Alt Baslik

{PROSE}

### Kod

```python
def chunk(text):
    # bu bir baslik degil
    return text.split("\\n\\n")
```

### Tablo

| Fon | Tur | Deger |
|-----|-----|-------|
| VBR | GSYF | 100 |
| VBI | GYF | 200 |
"""


class TestChunkSpans(unittest.TestCase):
    def test_spans_trace_back_to_source(self) -> None:
        doc = make_doc(MARKDOWN)
        chunks = chunk_document(doc, target_tokens=60, overlap_tokens=10, min_tokens=10)
        self.assertTrue(chunks)
        self.assertEqual(verify_spans(doc, chunks), [])
        for chunk in chunks:
            self.assertEqual(doc.text[chunk.char_start : chunk.char_end], chunk.text)
            self.assertEqual(chunk.doc_id, doc.doc_id)

    def test_every_byte_of_content_is_covered(self) -> None:
        """Chunking may overlap, but it may not silently drop a paragraph."""
        doc = make_doc(MARKDOWN)
        chunks = chunk_document(doc, target_tokens=60, overlap_tokens=10, min_tokens=10)
        covered = bytearray(len(doc.text))
        for chunk in chunks:
            for i in range(chunk.char_start, chunk.char_end):
                covered[i] = 1
        missed = [i for i, seen in enumerate(covered) if not seen and not doc.text[i].isspace()]
        self.assertEqual(missed, [], f"dropped source characters at {missed[:10]}")

    def test_deterministic_across_calls(self) -> None:
        doc = make_doc(MARKDOWN)
        first = chunk_document(doc)
        second = chunk_document(doc)
        self.assertEqual([c.chunk_id for c in first], [c.chunk_id for c in second])
        self.assertEqual([c.context_header for c in first], [c.context_header for c in second])

    def test_empty_and_whitespace_documents_produce_no_chunks(self) -> None:
        for text in ("", "   ", "\n\n\t\n", "\r\n\r\n"):
            self.assertEqual(chunk_document(make_doc(text)), [], repr(text))

    def test_crlf_is_folded_but_offsets_stay_pinned(self) -> None:
        text = "# Baslik\r\n\r\nBirinci satir.\r\nIkinci satir.\r\n"
        doc = make_doc(text)
        chunks = chunk_document(doc)
        self.assertTrue(chunks)
        self.assertEqual(verify_spans(doc, chunks), [])
        for chunk in chunks:
            self.assertNotIn("\r", chunk.text)
            # The range still points at the CRLF source, which is the point:
            # the rendering changed, the provenance did not.
            self.assertIn("\r", doc.text[chunk.char_start : chunk.char_end])

    def test_giant_line_without_whitespace_is_cut_on_length(self) -> None:
        doc = make_doc("x" * 200_000)
        chunks = chunk_document(doc, target_tokens=450, overlap_tokens=60, min_tokens=40)
        self.assertGreater(len(chunks), 50)
        self.assertEqual(verify_spans(doc, chunks), [])
        self.assertLessEqual(max(c.token_estimate for c in chunks), 450 * 2)
        self.assertEqual("".join(c.text for c in chunks), "x" * 200_000)

    def test_giant_line_of_combining_characters_does_not_orphan_marks(self) -> None:
        """Cutting between a base letter and its combining dot would corrupt "İ"."""
        doc = make_doc("i̇" * 40_000)
        chunks = chunk_document(doc, target_tokens=64, overlap_tokens=0, min_tokens=0)
        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertFalse(chunk.text.startswith("̇"), "chunk starts with an orphan mark")

    def test_fenced_code_block_is_never_split(self) -> None:
        fence = "```python\n" + "\n".join(f"line_{i} = {i}" for i in range(80)) + "\n```"
        doc = make_doc(f"# T\n\nintro paragraph here.\n\n{fence}\n\noutro paragraph here.\n")
        chunks = chunk_document(doc, target_tokens=40, overlap_tokens=8, min_tokens=5)
        holders = [c for c in chunks if fence in c.text]
        self.assertEqual(len(holders), 1, "the fence must survive intact in exactly one chunk")
        for chunk in chunks:
            markers = sum(1 for line in chunk.text.split("\n") if line.startswith("```"))
            self.assertEqual(markers % 2, 0, f"chunk cuts a fence: {chunk.text[:60]!r}")

    def test_table_rows_are_never_split(self) -> None:
        rows = "\n".join(f"| VBR{i} | GSYF | {i * 1000} |" for i in range(60))
        doc = make_doc(f"# T\n\n| Fon | Tur | Deger |\n|---|---|---|\n{rows}\n")
        chunks = chunk_document(doc, target_tokens=40, overlap_tokens=6, min_tokens=5)
        self.assertGreater(len(chunks), 1, "the table should have been split across chunks")
        source_rows = {line for line in doc.text.split("\n") if line.startswith("|")}
        for chunk in chunks:
            for line in chunk.text.split("\n"):
                if "|" in line:
                    self.assertIn(line, source_rows, f"partial table row: {line!r}")

    def test_all_headings_document_collapses_into_few_chunks(self) -> None:
        text = "\n".join("#" * ((i % 6) + 1) + f" Baslik {i}" for i in range(300))
        doc = make_doc(text)
        chunks = chunk_document(doc, target_tokens=200, overlap_tokens=20, min_tokens=40)
        self.assertEqual(verify_spans(doc, chunks), [])
        # 300 sections, each ~4 tokens. Without runt merging this would be 300
        # useless chunks; with it, a couple of dozen usable ones.
        self.assertLess(len(chunks), 40)
        self.assertTrue(all(c.token_estimate >= 40 for c in chunks[:-1]))

    def test_runts_are_merged_into_a_neighbour(self) -> None:
        text = "# A\n\nbir.\n\n## B\n\niki.\n\n## C\n\nuc.\n\n## D\n\n" + PROSE
        doc = make_doc(text)
        chunks = chunk_document(doc, target_tokens=200, overlap_tokens=0, min_tokens=30)
        self.assertEqual(verify_spans(doc, chunks), [])
        for chunk in chunks:
            self.assertGreaterEqual(chunk.token_estimate, 30, repr(chunk.text[:60]))

    def test_a_document_smaller_than_min_tokens_is_still_one_chunk(self) -> None:
        """Merging has no neighbour to use. Dropping the text would be worse."""
        doc = make_doc("kisa.")
        chunks = chunk_document(doc, min_tokens=40)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "kisa.")

    def test_overlap_exists_and_is_bounded(self) -> None:
        doc = make_doc("# T\n\n" + " ".join(f"Cumle numara {i} burada." for i in range(200)))
        chunks = chunk_document(doc, target_tokens=80, overlap_tokens=20, min_tokens=10)
        self.assertGreater(len(chunks), 2)
        overlaps = [
            estimate_tokens(doc.text[chunks[i].char_start : chunks[i - 1].char_end])
            for i in range(1, len(chunks))
            if chunks[i].char_start < chunks[i - 1].char_end
        ]
        self.assertTrue(overlaps, "no overlap at all between adjacent chunks")
        self.assertLessEqual(max(overlaps), 80, "overlap must stay well inside the target budget")

    def test_overlap_is_disabled_cleanly(self) -> None:
        doc = make_doc("# T\n\n" + " ".join(f"Cumle numara {i} burada." for i in range(120)))
        chunks = chunk_document(doc, target_tokens=60, overlap_tokens=0, min_tokens=10)
        for i in range(1, len(chunks)):
            self.assertGreaterEqual(chunks[i].char_start, chunks[i - 1].char_end)

    def test_overlap_never_reaches_back_into_a_fence(self) -> None:
        fence = "```\n" + "\n".join(f"row {i}" for i in range(30)) + "\n```"
        doc = make_doc(f"# T\n\n{fence}\n\n" + " ".join(f"Cumle {i} burada." for i in range(80)))
        chunks = chunk_document(doc, target_tokens=40, overlap_tokens=15, min_tokens=5)
        for chunk in chunks:
            markers = sum(1 for line in chunk.text.split("\n") if line.startswith("```"))
            self.assertEqual(
                markers % 2, 0, f"overlap dragged in half a fence: {chunk.text[:80]!r}"
            )

    def test_metadata_flags_code_and_tables(self) -> None:
        doc = make_doc(MARKDOWN)
        chunks = chunk_document(doc, target_tokens=60, overlap_tokens=10, min_tokens=10)
        self.assertTrue(any(c.metadata["has_code"] for c in chunks))
        self.assertTrue(any(c.metadata["has_table"] for c in chunks))
        for chunk in chunks:
            self.assertEqual(chunk.metadata["doc_title"], doc.title)
            json.dumps(chunk.metadata)  # must survive a trip through the index

    def test_verify_spans_catches_a_tampered_chunk(self) -> None:
        """The guard is only real once it has been watched rejecting something."""
        doc = make_doc(MARKDOWN)
        chunks = chunk_document(doc, target_tokens=60)
        self.assertEqual(verify_spans(doc, chunks), [])
        chunks[0].text = chunks[0].text + " (uydurma)"
        chunks[-1].char_end = len(doc.text) + 500
        problems = verify_spans(doc, chunks)
        self.assertEqual(len(problems), 2)
        self.assertIn("does not match its source range", problems[0])
        self.assertIn("out of bounds", problems[1])


class TestContextHeader(unittest.TestCase):
    def test_header_is_deterministic_and_positional(self) -> None:
        doc = make_doc(MARKDOWN, title="Fon Raporu")
        first = build_context_header(doc, ["Fon Raporu", "Alt Baslik"], 2, 7)
        again = build_context_header(doc, ["Fon Raporu", "Alt Baslik"], 2, 7)
        self.assertEqual(first, again)
        self.assertIn("Document: Fon Raporu", first)
        self.assertIn("Section: Alt Baslik", first)
        self.assertIn("Part 3 of 7", first)
        # The title is not repeated as a section heading.
        self.assertNotIn("Fon Raporu > Alt Baslik", first)

    def test_single_chunk_document_has_no_position_line(self) -> None:
        doc = make_doc("kisa metin", title="T")
        self.assertNotIn("Part", build_context_header(doc, [], 0, 1))
        self.assertIn("Part 1 of 2", build_context_header(doc, [], 0, 2))

    def test_turkish_case_is_preserved_in_output(self) -> None:
        doc = make_doc("x", title="İstanbul Şubesi")
        header = build_context_header(doc, ["Yıllık Değerleme"], 0, 3)
        self.assertIn("İstanbul Şubesi", header)
        self.assertIn("Yıllık Değerleme", header)

    def test_dotted_and_dotless_i_dedupe_against_the_title(self) -> None:
        """str.lower() would leave "İSTANBUL" and "istanbul" as different headings."""
        doc = make_doc("x", title="İSTANBUL")
        header = build_context_header(doc, ["istanbul", "Detay"], 0, 3)
        self.assertNotIn("Section: istanbul", header)
        self.assertIn("Section: Detay", header)
        self.assertEqual(fold("İSTANBUL"), fold("istanbul"))
        self.assertEqual(fold("ISTANBUL"), fold("ıstanbul"))

    def test_header_survives_missing_title_and_nonsense_positions(self) -> None:
        doc = make_doc("x", title="")
        header = build_context_header(doc, [""], -5, 0)
        self.assertIn("https://example.invalid/a", header)
        self.assertNotIn("Part", header)
        bad_positions = build_context_header(doc, [], "bad", "worse")  # type: ignore[arg-type]
        self.assertEqual(bad_positions, header)

    def test_header_is_prepended_to_the_indexed_text(self) -> None:
        doc = make_doc(MARKDOWN)
        chunk = chunk_document(doc, target_tokens=60)[0]
        self.assertTrue(chunk.indexed_text.startswith(chunk.context_header))
        self.assertIn(chunk.text, chunk.indexed_text)


class TestHashingEmbedder(unittest.TestCase):
    def setUp(self) -> None:
        self.embedder = HashingEmbedder(dim=128)

    def test_dim_and_unit_norm(self) -> None:
        vectors = self.embedder.embed(["portfoy yonetimi", "gayrimenkul yatirim fonu"])
        for vec in vectors:
            self.assertEqual(len(vec), 128)
            self.assertAlmostEqual(sum(v * v for v in vec) ** 0.5, 1.0, places=9)

    def test_same_text_same_vector(self) -> None:
        a = self.embedder.embed_one("İstanbul'da bir fon")
        b = self.embedder.embed_one("İstanbul'da bir fon")
        self.assertEqual(a, b)

    def test_identical_vector_in_a_separate_process(self) -> None:
        """The whole promise of this embedder. Different hash seeds must not matter."""
        script = (
            "from oodarag.embed.hashing import HashingEmbedder;"
            "import json;"
            "print(json.dumps(HashingEmbedder(dim=64).embed_one('İstanbul fonlarin degeri 42')))"
        )
        outputs = []
        for seed in ("0", "1", "12345"):
            env = {**os.environ, "PYTHONPATH": SRC, "PYTHONHASHSEED": seed}
            proc = subprocess.run(
                [sys.executable, "-c", script], capture_output=True, text=True, env=env, check=True
            )
            outputs.append(proc.stdout.strip())
        self.assertEqual(len(set(outputs)), 1, "vector changed with PYTHONHASHSEED")
        self.assertEqual(
            json.loads(outputs[0]), HashingEmbedder(dim=64).embed_one("İstanbul fonlarin degeri 42")
        )

    def test_empty_and_punctuation_only_text_is_a_zero_vector(self) -> None:
        for text in ("", "   ", "!!! ... ???"):
            vec = self.embedder.embed_one(text)
            self.assertEqual(vec, [0.0] * 128, repr(text))
            self.assertEqual(cosine(vec, self.embedder.embed_one("fon")), 0.0)

    def test_character_ngrams_carry_turkish_morphology(self) -> None:
        """"fonlarin" and "fonun" share no whole word and no 4-gram either.

        Turkish suffixes mutate the stem, so this pair is close to the worst case
        for a lexical embedder; the n-grams still have to pull it clearly away
        from noise. Measured at the default dimension because a small vector is
        dominated by hash collisions rather than by the signal under test.
        """
        embedder = HashingEmbedder()
        related = cosine(
            embedder.embed_one("fonlarin degerleme raporu"),
            embedder.embed_one("fonun degerlemesi raporlari"),
        )
        unrelated = cosine(
            embedder.embed_one("fonlarin degerleme raporu"),
            embedder.embed_one("quantum chromodynamics lattice"),
        )
        inflected = cosine(
            embedder.embed_one("gayrimenkul yatirim fonu"),
            embedder.embed_one("gayrimenkul yatirim fonlari"),
        )
        self.assertGreater(related, 0.25)
        self.assertGreater(inflected, 0.7)
        self.assertGreater(related, unrelated + 0.15)

    def test_ngrams_can_be_switched_off(self) -> None:
        words_only = HashingEmbedder(dim=128, ngram_weight=0.0)
        related = cosine(
            words_only.embed_one("fonlarin degerleme"), words_only.embed_one("fonun degerlemesi")
        )
        self.assertAlmostEqual(related, 0.0, places=9)  # no shared whole word at all

    def test_dotted_and_dotless_i_land_in_the_same_bucket(self) -> None:
        base = self.embedder.embed_one("İstanbul")
        for variant in ("istanbul", "ISTANBUL", "ıstanbul", "İSTANBUL"):
            self.assertAlmostEqual(cosine(base, self.embedder.embed_one(variant)), 1.0, places=9)

    def test_turkish_text_is_not_mangled_into_ascii_fragments(self) -> None:
        """util.text.tokenize would reduce "şirket" to "irket"; this must not."""
        rich = self.embedder.embed_one("şirket çalışması ölçüsünde ığdır")
        stripped = self.embedder.embed_one("irket alimasi lsnde dr")
        self.assertLess(cosine(rich, stripped), 0.5)

    def test_bad_dim_is_clamped_not_raised(self) -> None:
        self.assertEqual(HashingEmbedder(dim=0).dim, 8)
        self.assertEqual(HashingEmbedder(dim=-17).dim, 8)

    def test_max_tokens_truncation_is_deterministic(self) -> None:
        capped = HashingEmbedder(dim=64, max_tokens=10)
        text = " ".join(f"kelime{i}" for i in range(500))
        self.assertEqual(capped.embed_one(text), capped.embed_one(text))
        self.assertEqual(capped.embed_one(text), capped.embed_one(" ".join(text.split()[:10])))

    def test_name_identifies_the_vector_space(self) -> None:
        self.assertEqual(HashingEmbedder(dim=64, ngram=5).name, "hash-64d-5g")
        self.assertNotEqual(HashingEmbedder(dim=64).name, HashingEmbedder(dim=128).name)
        self.assertNotEqual(
            HashingEmbedder(dim=64, salt="a").embed_one("fon"),
            HashingEmbedder(dim=64, salt="b").embed_one("fon"),
        )

    def test_cosine_refuses_to_compare_different_spaces(self) -> None:
        with self.assertRaises(ValueError):
            cosine([0.1] * 8, [0.1] * 16)

    def test_l2_normalize_survives_degenerate_vectors(self) -> None:
        self.assertEqual(l2_normalize([0.0, 0.0, 0.0]), [0.0, 0.0, 0.0])
        self.assertEqual(l2_normalize([float("inf"), 1.0]), [0.0, 0.0])
        self.assertEqual(l2_normalize([]), [])
        self.assertEqual(cosine([0.0, 0.0], [1.0, 1.0]), 0.0)

    def test_optional_numpy_import_is_guarded(self) -> None:
        """Whichever way this environment is configured, the module works."""
        self.assertIsInstance(HAS_NUMPY, bool)
        forced_stdlib = HashingEmbedder(dim=64, use_numpy=False)
        auto = HashingEmbedder(dim=64)
        text = " ".join(f"kelime{i} deger{i}" for i in range(300))  # enough to trip the numpy path
        self.assertEqual(forced_stdlib.embed_one(text), auto.embed_one(text))

    @unittest.skipUnless(HAS_NUMPY, "numpy not installed")
    def test_numpy_path_is_bit_identical(self) -> None:  # pragma: no cover - env dependent
        text = " ".join(f"kelime{i} deger{i}" for i in range(500))
        self.assertEqual(
            HashingEmbedder(dim=256, use_numpy=True).embed_one(text),
            HashingEmbedder(dim=256, use_numpy=False).embed_one(text),
        )


# --------------------------------------------------------------------- doubles


#: The hosted-embedder tests run at the smallest dimension the stack allows, so
#: that a mismatch between the declared dim and the fallback's would show up.
DIM = 8
V0 = [1.0] + [0.0] * (DIM - 1)
V1 = [0.0, 1.0] + [0.0] * (DIM - 2)
VH = [0.5] * DIM
ZERO = [0.0] * DIM


def http_response(payload: object, status: int = 200) -> Response:
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    return Response(
        url="https://api.invalid/v1/embeddings",
        status=status,
        headers={"content-type": "application/json"},
        body=body,
    )


def api_payload(vectors: list[list[float]]) -> dict[str, object]:
    return {"data": [{"index": i, "embedding": v} for i, v in enumerate(vectors)]}


class FakeClient:
    """Stands in for HttpClient. Yields scripted responses, or raises them."""

    def __init__(self, script: list[object]) -> None:
        self.script = list(script)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kw: object) -> Response:
        self.calls.append({"method": method, "url": url, **kw})
        item = self.script.pop(0) if self.script else None
        if isinstance(item, BaseException):
            raise item
        if item is None:
            raise TransportError("no scripted response left")
        assert isinstance(item, Response)
        return item

    @property
    def bodies(self) -> list[dict[str, object]]:
        return [json.loads(c["body"]) for c in self.calls]  # type: ignore[arg-type]


class CountingEmbedder:
    """Minimal Embedder used to prove the cache actually avoids work."""

    def __init__(self, dim: int = 16, name: str = "counting") -> None:
        self.dim = dim
        self.name = name
        self.calls = 0
        self.texts: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        self.texts.extend(texts)
        return [[float(len(t))] + [0.0] * (self.dim - 1) for t in texts]


class TestHostedEmbedder(unittest.TestCase):
    def hosted(self, script: list[object], **kw: object) -> tuple[HostedEmbedder, FakeClient]:
        client = FakeClient(script)
        embedder = HostedEmbedder(
            dim=kw.pop("dim", DIM),  # type: ignore[arg-type]
            api_key="test-key",
            endpoint="https://api.invalid/v1/embeddings",
            client=client,  # type: ignore[arg-type]
            **kw,  # type: ignore[arg-type]
        )
        return embedder, client

    def test_missing_key_degrades_before_any_request(self) -> None:
        client = FakeClient([])
        embedder = HostedEmbedder(
            dim=DIM, api_key="", api_key_env=(), client=client,  # type: ignore[arg-type]
        )
        vectors = embedder.embed(["fon", "rapor"])
        self.assertTrue(embedder.degraded)
        self.assertEqual(embedder.reason, "no api key in environment")
        self.assertEqual(client.calls, [])
        self.assertEqual(vectors, HashingEmbedder(8).embed(["fon", "rapor"]))

    def test_successful_call_returns_hosted_vectors(self) -> None:
        embedder, client = self.hosted([http_response(api_payload([V0]))])
        self.assertEqual(embedder.embed(["fon"]), [V0])
        self.assertFalse(embedder.degraded)
        self.assertEqual(embedder.space, f"text-embedding-3-small@{DIM}")
        self.assertEqual(client.calls[0]["method"], "POST")
        self.assertEqual(client.bodies[0]["input"], ["fon"])
        self.assertEqual(client.bodies[0]["dimensions"], DIM)

    def test_out_of_order_response_is_reordered_by_index(self) -> None:
        payload = {"data": [
            {"index": 1, "embedding": V1},
            {"index": 0, "embedding": V0},
        ]}
        embedder, _ = self.hosted([http_response(payload)])
        self.assertEqual(embedder.embed(["a", "b"]), [V0, V1])

    def test_transport_failure_falls_back_and_never_raises(self) -> None:
        embedder, _ = self.hosted([TransportError("egress blocked")])
        vectors = embedder.embed(["fon", "rapor"])
        self.assertTrue(embedder.degraded)
        self.assertIn("TransportError", embedder.reason)
        self.assertEqual(vectors, HashingEmbedder(DIM).embed(["fon", "rapor"]))

    def test_auth_failure_degrades(self) -> None:
        embedder, _ = self.hosted([HttpError(401, "https://api.invalid/v1/embeddings", "nope")])
        embedder.embed(["fon"])
        self.assertEqual(embedder.reason, "http 401")

    def test_rate_limit_exhaustion_degrades(self) -> None:
        rate_limited = HttpError(429, "https://api.invalid/v1/embeddings", "slow down")
        embedder, _ = self.hosted([rate_limited])
        vectors = embedder.embed(["fon"])
        self.assertTrue(embedder.degraded)
        self.assertEqual(len(vectors[0]), DIM)

    def test_truncated_response_is_rejected(self) -> None:
        """Two inputs, one vector back. Accepting it would misalign every chunk after it."""
        embedder, _ = self.hosted([http_response(api_payload([V0]))])
        vectors = embedder.embed(["fon", "rapor"])
        self.assertTrue(embedder.degraded)
        self.assertIn("malformed", embedder.reason)
        self.assertEqual(vectors, HashingEmbedder(DIM).embed(["fon", "rapor"]))

    def test_wrong_dimension_response_is_rejected(self) -> None:
        embedder, _ = self.hosted([http_response(api_payload([[1.0, 0.0]]))])
        embedder.embed(["fon"])
        self.assertTrue(embedder.degraded)

    def test_garbage_bodies_are_rejected(self) -> None:
        for payload in (
            b"<html>proxy error</html>",
            b'{"data": [{"embedding": [1.0, 0.0, 0.0',
            {"data": "not-a-list"},
            {"error": {"message": "quota"}},
            {"data": [{"embedding": [1.0, None] + [0.0] * (DIM - 2)}]},
            {"data": [{"embedding": ["a"] * DIM}]},
        ):
            with self.subTest(payload=str(payload)[:40]):
                embedder, _ = self.hosted([http_response(payload)])
                vectors = embedder.embed(["fon"])
                self.assertTrue(embedder.degraded)
                self.assertEqual(len(vectors[0]), DIM)

    def test_alternative_embeddings_key_is_accepted(self) -> None:
        embedder, _ = self.hosted([http_response({"embeddings": [VH]})])
        self.assertEqual(embedder.embed(["fon"]), [VH])
        self.assertFalse(embedder.degraded)

    def test_a_partly_failed_call_returns_one_vector_space(self) -> None:
        """Mixing hosted and hashing vectors in one index is the failure this prevents."""
        embedder, client = self.hosted(
            [http_response(api_payload([V0])), TransportError("reset")],
            batch_size=1,
        )
        vectors = embedder.embed(["bir", "iki", "uc"])
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(vectors, HashingEmbedder(DIM).embed(["bir", "iki", "uc"]))
        self.assertNotIn(V0, vectors)

    def test_empty_strings_are_never_sent(self) -> None:
        embedder, client = self.hosted([http_response(api_payload([V0]))])
        vectors = embedder.embed(["", "fon", "   "])
        self.assertEqual(client.bodies[0]["input"], ["fon"])
        self.assertEqual(vectors[0], ZERO)
        self.assertEqual(vectors[1], V0)
        self.assertEqual(vectors[2], ZERO)

    def test_provider_rejecting_dimensions_is_retried_without_it(self) -> None:
        embedder, client = self.hosted([
            HttpError(400, "https://api.invalid/v1/embeddings", "unknown field: dimensions"),
            http_response(api_payload([V1])),
        ])
        self.assertEqual(embedder.embed(["fon"]), [V1])
        self.assertFalse(embedder.degraded)
        self.assertIn("dimensions", client.bodies[0])
        self.assertNotIn("dimensions", client.bodies[1])

    def test_degrade_is_sticky(self) -> None:
        embedder, client = self.hosted([
            TransportError("reset"),
            http_response(api_payload([V0])),
        ])
        embedder.embed(["fon"])
        embedder.embed(["rapor"])
        self.assertEqual(len(client.calls), 1, "a degraded embedder must stop calling out")
        self.assertEqual(embedder.stats["fallback_texts"], 2)

    def test_long_input_is_truncated_before_sending(self) -> None:
        embedder, client = self.hosted(
            [http_response(api_payload([V0]))], max_input_tokens=32
        )
        embedder.embed(["kelime " * 5000])
        sent = client.bodies[0]["input"][0]  # type: ignore[index]
        self.assertLess(len(sent), 400)

    def test_empty_batch_is_a_no_op(self) -> None:
        embedder, client = self.hosted([])
        self.assertEqual(embedder.embed([]), [])
        self.assertEqual(client.calls, [])

    def test_parse_rejects_short_and_long_lists(self) -> None:
        self.assertIsNone(_parse_embeddings({"data": []}, 1, 4))
        self.assertIsNone(_parse_embeddings(api_payload([[1.0] * 4] * 2), 1, 4))
        self.assertIsNone(_parse_embeddings("not a dict", 1, 4))
        self.assertEqual(_parse_embeddings(api_payload([[1.0] * 4]), 1, 4), [[1.0] * 4])


class TestGetEmbedder(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {
            k: os.environ.pop(k, None) for k in ("OODARAG_EMBED_API_KEY", "OPENAI_API_KEY")
        }

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_auto_without_a_key_is_the_hashing_embedder(self) -> None:
        self.assertIsInstance(get_embedder("auto"), HashingEmbedder)

    def test_auto_with_a_key_is_hosted(self) -> None:
        os.environ["OODARAG_EMBED_API_KEY"] = "sk-test"
        embedder = get_embedder("auto")
        self.assertIsInstance(embedder, HostedEmbedder)
        self.assertFalse(embedder.degraded)

    def test_explicit_names(self) -> None:
        self.assertIsInstance(get_embedder("hash", dim=32), HashingEmbedder)
        self.assertIsInstance(get_embedder("hosted", api_key="k"), HostedEmbedder)

    def test_unknown_name_degrades_instead_of_raising(self) -> None:
        embedder = get_embedder("gpt-9-super-embed", dim=32)
        self.assertIsInstance(embedder, HashingEmbedder)
        self.assertEqual(embedder.dim, 32)

    def test_unsupported_options_are_dropped_not_fatal(self) -> None:
        """A config file eventually carries a key meant for a different embedder."""
        embedder = get_embedder("hash", dim=32, temperature=0.7, model="nonsense")
        self.assertIsInstance(embedder, HashingEmbedder)
        self.assertEqual(embedder.dim, 32)


class TestEmbeddingCache(unittest.TestCase):
    def test_a_repeat_costs_nothing(self) -> None:
        inner = CountingEmbedder()
        cache = EmbeddingCache(inner)
        first = cache.embed(["fon", "rapor"])
        second = cache.embed(["fon", "rapor"])
        self.assertEqual(first, second)
        self.assertEqual(inner.calls, 1)
        self.assertEqual(cache.stats, {"hits": 2, "misses": 2, "evicted": 0, "loaded": 0})

    def test_duplicates_within_one_batch_are_embedded_once(self) -> None:
        inner = CountingEmbedder()
        cache = EmbeddingCache(inner)
        cache.embed(["fon", "fon", "fon"])
        self.assertEqual(inner.texts, ["fon"])

    def test_it_satisfies_the_embedder_protocol(self) -> None:
        cache = EmbeddingCache(HashingEmbedder(dim=32))
        self.assertEqual(cache.dim, 32)
        self.assertEqual(len(cache.embed(["fon"])[0]), 32)

    def test_embed_chunks_uses_the_context_header(self) -> None:
        inner = CountingEmbedder()
        cache = EmbeddingCache(inner)
        chunks = chunk_document(make_doc(MARKDOWN), target_tokens=60)
        cache.embed_chunks(chunks)
        self.assertTrue(all(t.startswith("Document: Test Document") for t in inner.texts))

    def test_roundtrip_through_disk_is_exact(self) -> None:
        embedder = HashingEmbedder(dim=64)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "cache.json"
            cache = EmbeddingCache(embedder, path)
            expected = cache.embed(["İstanbul fonu", "gayrimenkul"])
            self.assertTrue(cache.save())
            reloaded = EmbeddingCache(embedder, path)
            self.assertEqual(len(reloaded), 2)
            self.assertEqual(reloaded.embed(["İstanbul fonu", "gayrimenkul"]), expected)
            self.assertEqual(reloaded.stats["misses"], 0)

    def test_corrupt_cache_file_is_an_empty_cache_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for content in ("", "{", '{"entries": "nope"}', "[1,2,3]"):
                path = Path(tmp) / "cache.json"
                path.write_text(content, encoding="utf-8")
                cache = EmbeddingCache(HashingEmbedder(dim=16), path)
                self.assertEqual(len(cache), 0, repr(content))
                self.assertEqual(len(cache.embed(["fon"])[0]), 16)

    def test_entries_of_a_foreign_dimension_are_never_served(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cache.json"
            small = EmbeddingCache(HashingEmbedder(dim=16), path)
            small.embed(["fon"])
            small.save()
            big = EmbeddingCache(HashingEmbedder(dim=64), path)
            vectors = big.embed(["fon"])
            self.assertEqual(len(vectors[0]), 64)
            self.assertEqual(big.stats["misses"], 1)

    def test_key_changes_when_the_embedder_degrades(self) -> None:
        """Otherwise a hosted vector would be served to a caller now getting hashing vectors."""
        client = FakeClient([TransportError("blocked")])
        hosted = HostedEmbedder(dim=DIM, api_key="k", client=client)  # type: ignore[arg-type]
        cache = EmbeddingCache(hosted)
        before = cache.key("fon")
        cache.embed(["fon"])
        self.assertTrue(hosted.degraded)
        self.assertNotEqual(before, cache.key("fon"))

    def test_eviction_is_bounded(self) -> None:
        cache = EmbeddingCache(CountingEmbedder(), max_entries=10)
        cache.embed([f"metin {i}" for i in range(50)])
        self.assertEqual(len(cache), 10)
        self.assertEqual(cache.stats["evicted"], 40)

    def test_save_without_a_path_is_a_no_op(self) -> None:
        self.assertFalse(EmbeddingCache(CountingEmbedder()).save())


if __name__ == "__main__":
    unittest.main()
