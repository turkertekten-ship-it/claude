"""Tests for the data structures the whole pipeline passes around.

These are "just dataclasses", which is exactly why they are worth pinning. Two
of the properties here are load-bearing in a way that fails silently:

`RawDocument.content_hash` is what `Connector.run` compares to decide new versus
changed versus unchanged. If it stopped being deterministic across processes,
every incremental ingest would re-fetch the world and nobody would see an error.

`Chunk.content_hash` covers `indexed_text`, not `text`. The contextual header is
embedded and indexed *with* the body, so two chunks with the same body under
different headings are different retrievable units. A hash that ignored the
header would silently collapse them in any cache keyed by it.
"""

from __future__ import annotations

import json
import unittest

from oodarag.models import (
    Answer,
    Chunk,
    Citation,
    Document,
    IngestDelta,
    RawDocument,
    ScoredChunk,
)


def raw(**kw) -> RawDocument:
    base = dict(
        source_system="github",
        external_id="owner/repo@abc123:README.md",
        uri="https://github.com/owner/repo/blob/abc123/README.md",
        title="README",
        text="hello world",
    )
    base.update(kw)
    return RawDocument(**base)


class TestRawDocument(unittest.TestCase):
    def test_content_hash_is_deterministic(self) -> None:
        self.assertEqual(raw().content_hash, raw().content_hash)

    def test_content_hash_is_independent_of_when_it_was_fetched(self) -> None:
        """Timestamps lie - mirrors, rebases, re-uploads. The hash must not."""
        self.assertEqual(raw(fetched_at=1.0).content_hash, raw(fetched_at=9e9).content_hash)

    def test_content_hash_tracks_text_and_title(self) -> None:
        self.assertNotEqual(raw().content_hash, raw(text="goodbye world").content_hash)
        self.assertNotEqual(raw().content_hash, raw(title="CHANGELOG").content_hash)

    def test_the_field_separator_prevents_a_shifted_collision(self) -> None:
        """("ab","c") must not hash the same as ("a","bc")."""
        self.assertNotEqual(
            raw(text="ab", title="c").content_hash,
            raw(text="a", title="bc").content_hash,
        )

    def test_metadata_is_not_shared_between_instances(self) -> None:
        first, second = raw(), raw()
        first.metadata["stars"] = 1
        self.assertEqual(second.metadata, {})


class TestDocument(unittest.TestCase):
    def test_doc_id_is_stable_and_source_scoped(self) -> None:
        a = Document.from_raw(raw(), "hello world", {})
        b = Document.from_raw(raw(), "different normalization", {})
        self.assertEqual(a.doc_id, b.doc_id, "identity is the source's id, not the text")
        other = Document.from_raw(raw(source_system="web"), "hello world", {})
        self.assertNotEqual(a.doc_id, other.doc_id, "same path, different system")

    def test_provenance_survives_normalization(self) -> None:
        source = raw()
        doc = Document.from_raw(source, "cleaned text", {"kind": "markdown"})
        self.assertEqual(doc.uri, source.uri)
        self.assertEqual(doc.external_id, source.external_id)
        self.assertEqual(doc.source_system, source.source_system)
        self.assertEqual(doc.metadata["kind"], "markdown")

    def test_hash_covers_the_normalized_text_not_the_raw_text(self) -> None:
        source = raw(text="  hello   world  ")
        doc = Document.from_raw(source, "hello world", {})
        self.assertNotEqual(doc.content_hash, source.content_hash)
        self.assertEqual(doc.content_hash, Document.from_raw(source, "hello world", {}).content_hash)


class TestChunk(unittest.TestCase):
    def chunk(self, **kw) -> Chunk:
        base = dict(chunk_id="c1", doc_id="d1", ordinal=0, text="it depends on the chunk size")
        base.update(kw)
        return Chunk(**base)

    def test_indexed_text_prefixes_the_header(self) -> None:
        c = self.chunk(context_header="README > Chunking")
        self.assertTrue(c.indexed_text.startswith("README > Chunking"))
        self.assertIn(c.text, c.indexed_text)

    def test_indexed_text_is_the_body_when_there_is_no_header(self) -> None:
        self.assertEqual(self.chunk().indexed_text, self.chunk().text)

    def test_a_header_only_chunk_does_not_leave_stray_whitespace(self) -> None:
        self.assertEqual(self.chunk(text="", context_header="H").indexed_text, "H")

    def test_content_hash_covers_the_header(self) -> None:
        """The header is embedded with the body, so it is part of the unit."""
        plain = self.chunk()
        headed = self.chunk(context_header="README > Chunking")
        other = self.chunk(context_header="API > Limits")
        self.assertNotEqual(plain.content_hash, headed.content_hash)
        self.assertNotEqual(headed.content_hash, other.content_hash)

    def test_token_estimate_grows_with_the_header(self) -> None:
        self.assertGreater(
            self.chunk(context_header="README > Chunking > Overlap").token_estimate,
            self.chunk().token_estimate,
        )


class TestScoredChunk(unittest.TestCase):
    def test_citation_falls_back_to_the_doc_id_without_a_document(self) -> None:
        s = ScoredChunk(chunk=Chunk("c1", "d1", 0, "body"), score=0.5)
        self.assertEqual(s.citation_uri, "d1")
        self.assertEqual(s.citation_title, "d1")

    def test_citation_prefers_the_document(self) -> None:
        doc = Document.from_raw(raw(), "hello world", {})
        s = ScoredChunk(chunk=Chunk("c1", doc.doc_id, 0, "body"), score=0.5, document=doc)
        self.assertEqual(s.citation_uri, doc.uri)
        self.assertEqual(s.citation_title, doc.title)


class TestAnswer(unittest.TestCase):
    def answer(self, **kw) -> Answer:
        base = dict(
            question="what is chunking?",
            text="Splitting a document into retrievable units [1].",
            citations=[Citation(1, "c1", "d1", "README", "https://x/y", "a quote", 0.9)],
            confidence=0.812345,
        )
        base.update(kw)
        return Answer(**base)

    def test_serializes_to_valid_json(self) -> None:
        payload = json.loads(self.answer().to_json())
        self.assertEqual(payload["question"], "what is chunking?")
        self.assertEqual(payload["citations"][0]["marker"], 1)
        self.assertEqual(payload["confidence"], 0.8123, "confidence is rounded for display")

    def test_retrieved_chunks_are_omitted_unless_asked_for(self) -> None:
        scored = ScoredChunk(chunk=Chunk("c1", "d1", 0, "b" * 500), score=0.4,
                             components={"dense": 0.31111, "bm25": 0.29})
        answer = self.answer(retrieved=[scored])
        self.assertNotIn("retrieved", answer.to_dict())
        detailed = answer.to_dict(include_retrieved=True)
        self.assertEqual(len(detailed["retrieved"][0]["preview"]), 200, "previews are capped")
        self.assertEqual(detailed["retrieved"][0]["components"]["dense"], 0.3111)

    def test_an_abstention_still_serializes(self) -> None:
        payload = self.answer(text="", citations=[], abstained=True, confidence=0.0).to_dict()
        self.assertTrue(payload["abstained"])
        self.assertEqual(payload["citations"], [])

    def test_non_ascii_survives_serialization(self) -> None:
        payload = json.loads(self.answer(text="naïve café — ok").to_json())
        self.assertEqual(payload["answer"], "naïve café — ok")


class TestIngestDelta(unittest.TestCase):
    def test_touched_counts_work_downstream_stages_must_redo(self) -> None:
        delta = IngestDelta(source_key="web:example", new=3, changed=2, unchanged=99)
        self.assertEqual(delta.touched, 5, "unchanged documents cost nothing downstream")

    def test_serializes_with_its_errors(self) -> None:
        delta = IngestDelta(source_key="web:example", failed=1, errors=["boom"])
        payload = delta.as_dict()
        self.assertEqual(payload["failed"], 1)
        self.assertEqual(payload["errors"], ["boom"])

    def test_errors_are_not_shared_between_deltas(self) -> None:
        first, second = IngestDelta(source_key="a"), IngestDelta(source_key="b")
        first.errors.append("boom")
        self.assertEqual(second.errors, [])


if __name__ == "__main__":
    unittest.main()
