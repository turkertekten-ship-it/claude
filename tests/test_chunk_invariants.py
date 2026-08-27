"""Chunking invariants, because provenance is built on top of them.

CLAUDE.md: "Every chunk carries its doc_id and real character offsets. Prevents:
an answer that cannot be traced to its source is indistinguishable from an
invented one." That guarantee is only as good as the offsets, and an offset that
drifts is silent — the citation still renders, it just points at the wrong text.

The code-fence rule has the same shape: half a function is worse than no
function, and nothing downstream can tell it was split.
"""

from __future__ import annotations

import unittest

from oodarag.chunk import ChunkConfig, Chunker
from oodarag.models import Document

FENCE = "```"

MARKDOWN = f"""# Retrieval

Dense retrieval misses exact identifiers such as error codes and function names.
Lexical retrieval with BM25 misses paraphrase entirely.

## Example

{FENCE}python
def rrf(rankings, k=60):
    # A deliberately long fence, so a naive packer would be tempted
    # to split it across two chunks rather than overflow one.
    scores = {{}}
    for arm in rankings:
        for rank, doc in enumerate(arm, 1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: -kv[1])
{FENCE}

## Chunking

A chunk that loses its heading context is hard to retrieve usefully. A
contextual header naming the document title and heading path is embedded with
the chunk body so the passage is interpretable on its own.

## Evaluation

Recall at k, MRR and nDCG are computed over a golden set. A metric nobody reads
is a metric that does not exist, so the report prints the worst questions too.
"""


def _doc(text: str = MARKDOWN) -> Document:
    return Document(
        doc_id="d1", source_system="files", external_id="d1",
        uri="file:///d1.md", title="Retrieval notes", text=text,
        content_hash="h", metadata={},
    )


class OffsetsAreReal(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = _doc()
        self.chunks = Chunker().chunk(self.doc)
        self.assertTrue(self.chunks, "chunker produced nothing")

    def test_offsets_are_within_the_document(self) -> None:
        for c in self.chunks:
            with self.subTest(ordinal=c.ordinal):
                self.assertGreaterEqual(c.char_start, 0)
                self.assertLessEqual(c.char_end, len(self.doc.text))
                self.assertLess(c.char_start, c.char_end, "empty or inverted span")

    def test_the_span_recovers_the_chunk_body(self) -> None:
        # The load-bearing one. If this drifts, every citation still renders and
        # every one of them points somewhere slightly wrong.
        for c in self.chunks:
            with self.subTest(ordinal=c.ordinal):
                span = self.doc.text[c.char_start:c.char_end]
                self.assertEqual(span.strip(), c.text.strip())

    def test_every_chunk_carries_its_document(self) -> None:
        for c in self.chunks:
            with self.subTest(ordinal=c.ordinal):
                self.assertEqual(c.doc_id, self.doc.doc_id)
                self.assertTrue(c.chunk_id)

    def test_chunk_ids_are_unique_and_deterministic(self) -> None:
        ids = [c.chunk_id for c in self.chunks]
        self.assertEqual(len(ids), len(set(ids)), "duplicate chunk_id")
        again = [c.chunk_id for c in Chunker().chunk(_doc())]
        self.assertEqual(ids, again, "chunk ids are not reproducible")

    def test_ordinals_are_a_dense_sequence(self) -> None:
        self.assertEqual([c.ordinal for c in self.chunks], list(range(len(self.chunks))))


class CodeFencesAreAtomic(unittest.TestCase):
    def test_no_chunk_contains_an_unbalanced_fence(self) -> None:
        # An odd number of fence markers means the block was cut in half.
        for c in Chunker().chunk(_doc()):
            with self.subTest(ordinal=c.ordinal):
                self.assertEqual(c.text.count(FENCE) % 2, 0,
                                 "a fenced block was split across chunks")

    def test_the_fence_survives_a_tight_token_budget(self) -> None:
        # The real pressure case: a target so small that packing *wants* to
        # split the fence. Overflowing one chunk is the correct trade.
        chunks = Chunker(ChunkConfig(target_tokens=40, overlap_tokens=8,
                                     min_tokens=5, max_tokens=80)).chunk(_doc())
        self.assertTrue(chunks)
        for c in chunks:
            with self.subTest(ordinal=c.ordinal):
                self.assertEqual(c.text.count(FENCE) % 2, 0,
                                 "a tight budget split a fenced block")
        joined = "\n".join(c.text for c in chunks)
        self.assertIn("def rrf(rankings, k=60):", joined, "the code body was lost entirely")


class ContextHeaders(unittest.TestCase):
    def test_every_chunk_gets_a_context_header(self) -> None:
        for c in Chunker().chunk(_doc()):
            with self.subTest(ordinal=c.ordinal):
                self.assertTrue(c.context_header.strip(),
                                "a chunk without a header is unrankable on its own")

    def test_the_header_is_what_gets_indexed(self) -> None:
        c = Chunker().chunk(_doc())[0]
        self.assertIn(c.context_header.strip().split("\n")[0], c.indexed_text)
        self.assertIn(c.text.strip()[:40], c.indexed_text)

    def test_the_header_names_the_document(self) -> None:
        headers = " ".join(c.context_header for c in Chunker().chunk(_doc()))
        self.assertIn("Retrieval notes", headers)


class DegenerateInput(unittest.TestCase):
    def test_an_empty_document_yields_no_chunks(self) -> None:
        self.assertEqual(Chunker().chunk(_doc("")), [])

    def test_a_whitespace_document_yields_no_chunks(self) -> None:
        self.assertEqual(Chunker().chunk(_doc("   \n\n\t  \n")), [])

    def test_a_single_short_line_still_produces_a_chunk(self) -> None:
        chunks = Chunker().chunk(_doc("A short but genuine sentence about retrieval."))
        self.assertEqual(len(chunks), 1)
        self.assertIn("genuine sentence", chunks[0].text)


if __name__ == "__main__":
    unittest.main()
