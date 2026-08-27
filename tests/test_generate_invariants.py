"""The guards that stop a confident fabrication reaching a caller.

CLAUDE.md names two invariants that live in this module: citations are verified
by substring containment and never trusted, and an abstention is a correct
answer. Both are stated in prose in several places; this file is where they are
actually enforced.

Every case here constructs the failure and asserts it is caught, rather than
asserting the happy path still works.
"""

from __future__ import annotations

import unittest

from oodarag.generate import ExtractiveGenerator, GenerationConfig, verify_citations
from oodarag.models import Chunk, Citation, Document, ScoredChunk


def _doc(doc_id: str = "d1") -> Document:
    return Document(
        doc_id=doc_id, source_system="files", external_id=doc_id,
        uri=f"file:///{doc_id}.md", title="Retrieval notes",
        text="body", content_hash="h", metadata={"authority": 1.0},
    )


def _scored(chunk_id: str, text: str, score: float, doc: Document | None = None) -> ScoredChunk:
    doc = doc or _doc()
    return ScoredChunk(
        chunk=Chunk(chunk_id=chunk_id, doc_id=doc.doc_id, ordinal=0, text=text),
        score=score, components={"rrf": score}, document=doc,
    )


class CitationVerification(unittest.TestCase):
    """verify_citations is the last gate before an answer leaves the pipeline."""

    def setUp(self) -> None:
        self.doc = _doc()
        self.retrieved = [
            _scored("c1", "Dense retrieval misses exact identifiers.", 0.9, self.doc),
            _scored("c2", "BM25 misses paraphrase entirely.", 0.5, self.doc),
        ]

    def _cite(self, chunk_id: str, quote: str) -> Citation:
        return Citation(marker=1, chunk_id=chunk_id, doc_id=self.doc.doc_id,
                        title=self.doc.title, uri=self.doc.uri, quote=quote, score=0.9)

    def test_a_quote_absent_from_its_chunk_is_dropped(self) -> None:
        # The core fabrication shape: a real chunk id carrying a sentence the
        # chunk never contained.
        fabricated = self._cite("c1", "Dense retrieval solves paraphrase perfectly.")
        kept = verify_citations("some answer", [fabricated], self.retrieved)
        self.assertEqual(kept, [], "a quote not in its chunk survived verification")

    def test_a_citation_naming_an_unretrieved_chunk_is_dropped(self) -> None:
        # A plausible-looking citation to a chunk that was never retrieved is
        # indistinguishable from an invented source to a reader.
        orphan = self._cite("c-not-retrieved", "Dense retrieval misses exact identifiers.")
        kept = verify_citations("some answer", [orphan], self.retrieved)
        self.assertEqual(kept, [], "a citation to an unretrieved chunk survived")

    def test_a_genuine_citation_survives(self) -> None:
        good = self._cite("c1", "Dense retrieval misses exact identifiers.")
        kept = verify_citations("some answer", [good], self.retrieved)
        self.assertEqual([c.chunk_id for c in kept], ["c1"])

    def test_verification_drops_only_the_bad_one(self) -> None:
        good = self._cite("c1", "Dense retrieval misses exact identifiers.")
        bad = self._cite("c2", "A sentence chunk two never contained.")
        kept = verify_citations("some answer", [good, bad], self.retrieved)
        self.assertEqual([c.chunk_id for c in kept], ["c1"])


class Abstention(unittest.TestCase):
    """An honest refusal beats a confident answer with a real-looking URL."""

    def test_it_abstains_below_the_confidence_floor(self) -> None:
        gen = ExtractiveGenerator(GenerationConfig(min_confidence=0.9))
        answer = gen.generate("anything at all", [_scored("c1", "Weakly related text.", 0.01)])
        self.assertTrue(answer.abstained)

    def test_an_abstention_carries_no_citations(self) -> None:
        # An abstention that still cites sources invites the reader to treat it
        # as a partial answer, which is the failure it exists to avoid.
        gen = ExtractiveGenerator(GenerationConfig(min_confidence=0.9))
        answer = gen.generate("anything at all", [_scored("c1", "Weakly related text.", 0.01)])
        self.assertEqual(answer.citations, [])

    def test_it_abstains_on_an_empty_retrieval(self) -> None:
        answer = ExtractiveGenerator().generate("anything at all", [])
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.citations, [])

    def test_confidence_is_always_a_probability(self) -> None:
        gen = ExtractiveGenerator()
        for scored in ([], [_scored("c1", "Dense retrieval misses identifiers.", 0.0)],
                       [_scored("c1", "Dense retrieval misses identifiers.", 1.0)],
                       [_scored("c1", "Dense retrieval misses identifiers.", 99.0)]):
            with self.subTest(n=len(scored), score=scored[0].score if scored else None):
                answer = gen.generate("what does dense retrieval miss?", scored)
                self.assertGreaterEqual(answer.confidence, 0.0)
                self.assertLessEqual(answer.confidence, 1.0)


class AnsweredCitationsResolve(unittest.TestCase):
    def test_every_citation_on_an_answer_points_at_a_retrieved_chunk(self) -> None:
        retrieved = [
            _scored("c1", "Dense retrieval misses exact identifiers such as error codes.", 0.9),
            _scored("c2", "Lexical retrieval with BM25 misses paraphrase.", 0.8),
        ]
        answer = ExtractiveGenerator().generate("what does dense retrieval miss?", retrieved)
        if answer.abstained:
            self.skipTest("generator abstained; citation resolution is vacuous here")
        self.assertTrue(answer.citations, "answered without citing anything")
        ids = {s.chunk.chunk_id for s in retrieved}
        for citation in answer.citations:
            with self.subTest(chunk_id=citation.chunk_id):
                self.assertIn(citation.chunk_id, ids)
                body = next(s.chunk.text for s in retrieved if s.chunk.chunk_id == citation.chunk_id)
                self.assertIn(citation.quote, body,
                              "quote is not a substring of the chunk it names")


if __name__ == "__main__":
    unittest.main()
