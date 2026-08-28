"""Reranking exists to stop one page filling the context window.

The retriever's job is to find candidates; the reranker's is to decide which of
them are worth spending a limited context budget on. Its whole claim is that
three near-identical passages from one document are worth less together than two
different ones — and that claim is invisible in an aggregate retrieval metric,
because all three near-duplicates are "relevant".

So these tests build the degenerate case directly and assert the reranker
escapes it.
"""

from __future__ import annotations

import unittest

from oodarag.embed.hashing import HashingEmbedder
from oodarag.models import Chunk, Document, ScoredChunk
from oodarag.rerank import RerankConfig, Reranker

QUERY = "why fuse dense and lexical retrieval"

NEAR_DUPLICATE = (
    "Fusing dense and lexical retrieval avoids normalizing two incomparable "
    "score scales, which is why reciprocal rank fusion is used."
)
DIVERSE = (
    "Contextual headers name the document title and heading path so a chunk "
    "stays interpretable when it is retrieved on its own."
)


def _doc(doc_id: str, authority: float = 1.0) -> Document:
    return Document(
        doc_id=doc_id, source_system="files", external_id=doc_id,
        uri=f"file:///{doc_id}.md", title=doc_id.title(), text="body",
        content_hash="h", metadata={"authority": authority},
    )


def _scored(chunk_id: str, text: str, score: float, doc: Document) -> ScoredChunk:
    return ScoredChunk(
        chunk=Chunk(chunk_id=chunk_id, doc_id=doc.doc_id, ordinal=0, text=text),
        score=score, components={"rrf": score}, document=doc,
    )


class Diversity(unittest.TestCase):
    """Three near-identical passages must not take all three slots."""

    def setUp(self) -> None:
        self.embedder = HashingEmbedder(dim=256)
        doc = _doc("hybrid")
        other = _doc("chunking")
        # The duplicates deliberately outscore the diverse chunk: if the
        # reranker were pure relevance it would take all three of them.
        self.candidates = [
            _scored("dup1", NEAR_DUPLICATE, 0.90, doc),
            _scored("dup2", NEAR_DUPLICATE + " It fuses by rank.", 0.88, doc),
            _scored("dup3", NEAR_DUPLICATE + " Ranks, not scores.", 0.86, doc),
            _scored("diverse", DIVERSE, 0.55, other),
        ]

    def test_a_diverse_chunk_is_promoted_over_a_third_duplicate(self) -> None:
        top = Reranker(self.embedder, RerankConfig(mmr_lambda=0.5)).rerank(
            QUERY, list(self.candidates), k=3)
        ids = [s.chunk.chunk_id for s in top]
        self.assertIn("diverse", ids,
                      f"MMR kept three near-duplicates and dropped the diverse chunk: {ids}")

    def test_pure_relevance_keeps_the_duplicates(self) -> None:
        # The control. mmr_lambda=1.0 is relevance only, so the duplicates
        # SHOULD win — this proves the previous test measures diversity rather
        # than some unrelated reordering.
        top = Reranker(self.embedder, RerankConfig(mmr_lambda=1.0)).rerank(
            QUERY, list(self.candidates), k=3)
        self.assertEqual([s.chunk.chunk_id for s in top], ["dup1", "dup2", "dup3"])

    def test_it_returns_at_most_k(self) -> None:
        for k in (1, 2, 4, 10):
            with self.subTest(k=k):
                out = Reranker(self.embedder).rerank(QUERY, list(self.candidates), k=k)
                self.assertLessEqual(len(out), k)
                self.assertLessEqual(len(out), len(self.candidates))

    def test_it_returns_the_same_chunks_not_new_ones(self) -> None:
        out = Reranker(self.embedder).rerank(QUERY, list(self.candidates), k=4)
        self.assertEqual({s.chunk.chunk_id for s in out},
                         {s.chunk.chunk_id for s in self.candidates})


class ScoreBreakdown(unittest.TestCase):
    """The components dict is the debugging surface; losing it makes reranking
    unfalsifiable, which is worse than reranking badly."""

    def test_it_writes_its_own_components(self) -> None:
        doc = _doc("hybrid")
        cands = [_scored("a", NEAR_DUPLICATE, 0.9, doc), _scored("b", DIVERSE, 0.4, doc)]
        for s in Reranker(HashingEmbedder(dim=256)).rerank(QUERY, cands, k=2):
            with self.subTest(chunk_id=s.chunk.chunk_id):
                for key in ("mmr", "authority", "final"):
                    self.assertIn(key, s.components)

    def test_it_preserves_the_upstream_components(self) -> None:
        doc = _doc("hybrid")
        cands = [_scored("a", NEAR_DUPLICATE, 0.9, doc)]
        out = Reranker(HashingEmbedder(dim=256)).rerank(QUERY, cands, k=1)
        self.assertIn("rrf", out[0].components,
                      "reranking discarded the retriever's own score breakdown")

    def test_results_are_ordered_by_final(self) -> None:
        doc = _doc("hybrid")
        cands = [_scored(f"c{i}", NEAR_DUPLICATE if i % 2 else DIVERSE, 0.9 - 0.1 * i, doc)
                 for i in range(4)]
        out = Reranker(HashingEmbedder(dim=256)).rerank(QUERY, cands, k=4)
        finals = [s.components["final"] for s in out]
        self.assertEqual(finals, sorted(finals, reverse=True))


class Authority(unittest.TestCase):
    def test_a_more_authoritative_source_is_preferred_all_else_equal(self) -> None:
        # Identical text and identical retrieval score; only authority differs.
        low = _scored("low", NEAR_DUPLICATE, 0.8, _doc("blog", authority=0.2))
        high = _scored("high", NEAR_DUPLICATE, 0.8, _doc("docs", authority=1.0))
        out = Reranker(HashingEmbedder(dim=256),
                       RerankConfig(authority_weight=0.5)).rerank(QUERY, [low, high], k=2)
        self.assertEqual(out[0].chunk.chunk_id, "high")


class Degenerate(unittest.TestCase):
    def test_an_empty_candidate_set_returns_empty(self) -> None:
        self.assertEqual(Reranker(HashingEmbedder(dim=256)).rerank(QUERY, [], k=5), [])

    def test_a_single_candidate_survives(self) -> None:
        doc = _doc("hybrid")
        out = Reranker(HashingEmbedder(dim=256)).rerank(
            QUERY, [_scored("only", NEAR_DUPLICATE, 0.5, doc)], k=5)
        self.assertEqual([s.chunk.chunk_id for s in out], ["only"])


if __name__ == "__main__":
    unittest.main()
