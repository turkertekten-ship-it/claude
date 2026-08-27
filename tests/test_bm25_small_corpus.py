"""Regression: the lexical arm must not go silent on a small corpus.

This is here because the bug it covers fails quietly. With a clamped-at-zero
IDF, every term in a small corpus sits in more than half the documents, so every
weight clamps to zero and `search()` returns nothing. Hybrid retrieval then
degenerates to dense-only — but the dense arm still answers, the eval still
produces numbers, and nothing anywhere reports that an entire arm contributed
zero.

A test asserting "search returns results" on a large fixture would have passed
throughout. The corpus has to be small for the failure to appear, which is why
this file exists separately from the general index tests.
"""

from __future__ import annotations

import unittest

from oodarag.chunk import Chunker
from oodarag.index.bm25 import BM25Index
from oodarag.models import RawDocument
from oodarag.normalize import Normalizer

TEXT = """# Hybrid retrieval

Dense retrieval misses exact identifiers such as error codes and function names.
Lexical retrieval with BM25 misses paraphrase. Fusing both with Reciprocal Rank
Fusion avoids normalizing two incomparable score scales.

## Chunking

A chunk that loses its heading context is hard to retrieve usefully. A
contextual header naming the document title and heading path is embedded with
the chunk body.
"""


def _chunks():
    doc = Normalizer().normalize(
        RawDocument(source_system="files", external_id="d", uri="file:///d.md",
                    title="Retrieval notes", text=TEXT)
    )
    assert doc is not None
    return Chunker().chunk(doc)


class SmallCorpusBM25(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = _chunks()
        self.assertGreaterEqual(len(self.chunks), 2, "fixture must produce a small corpus")
        self.index = BM25Index().build(self.chunks)

    def test_search_returns_hits_on_a_two_chunk_corpus(self) -> None:
        hits = self.index.search("why fuse dense and BM25?", k=5)
        self.assertTrue(hits, "lexical arm returned nothing on a small corpus")

    def test_every_indexed_term_is_findable(self) -> None:
        # Each of these appears verbatim in the fixture. On a corpus this size
        # each also sits in a large fraction of the documents, which is exactly
        # the condition that used to zero them out.
        for term in ("paraphrase", "identifiers", "chunking", "retrieval"):
            with self.subTest(term=term):
                self.assertTrue(self.index.search(term, k=5),
                                f"no hit for {term!r}, which is in the corpus")

    def test_idf_stays_positive_for_a_term_in_every_document(self) -> None:
        # "retrieval" appears in both chunks. A term in 100% of the corpus is
        # the worst case for the clamp, and must still carry weight.
        hits = self.index.search("retrieval", k=5)
        self.assertTrue(hits)
        self.assertGreater(hits[0][1], 0.0, "a term in every document scored zero")

    def test_ranking_still_discriminates(self) -> None:
        # Keeping common terms is only correct if the ranking still separates
        # documents: tf saturation and length normalization have to do the work.
        chunking = self.index.search("chunking heading context", k=5)
        retrieval = self.index.search("dense identifiers error codes", k=5)
        self.assertTrue(chunking and retrieval)
        self.assertNotEqual(chunking[0][0], retrieval[0][0],
                            "both queries ranked the same chunk first; "
                            "scores are no longer discriminating")

    def test_absent_term_returns_nothing(self) -> None:
        # The other direction: the fix must not make everything match.
        self.assertEqual(self.index.search("kubernetes helm chart", k=5), [])


if __name__ == "__main__":
    unittest.main()
