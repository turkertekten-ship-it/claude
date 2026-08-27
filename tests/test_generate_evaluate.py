"""Answering and measuring. The property under test is that it declines."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.chunk import chunk_document  # noqa: E402
from oodarag.embed import HashingEmbedder  # noqa: E402
from oodarag.evaluate import (  # noqa: E402
    GoldenCase,
    dedupe,
    detect_contamination,
    evaluate,
    load_goldens,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
)
from oodarag.generate import ExtractiveGenerator, GenerateConfig, verify_citations  # noqa: E402
from oodarag.models import Answer, Citation, Document, RawDocument  # noqa: E402
from oodarag.retrieve import RetrievalConfig, Retriever  # noqa: E402
from oodarag.store import Store  # noqa: E402

TEXT = (
    "# Incremental ingest\n\n"
    "The pipeline decides a document has changed by hashing its text and comparing the "
    "hash with the one stored from the previous run. Timestamps are not used because "
    "mirrors, rebases and re-uploads all move a timestamp without changing content. "
    "An unchanged document is skipped before chunking, which is the largest single "
    "saving in an incremental run."
)


def build() -> tuple[Store, Retriever]:
    store = Store(":memory:")
    embedder = HashingEmbedder()
    raw = RawDocument("file", "ingest.md", "file:///ingest.md", "Incremental ingest", TEXT)
    doc = Document.from_raw(raw, TEXT, {})
    store.upsert_document(doc)
    chunks = chunk_document(doc)
    store.add_chunks(chunks, embedder.embed_batch([c.indexed_text for c in chunks]))
    return store, Retriever(store, embedder, RetrievalConfig(top_k=5, candidates=20))


class TestGeneration(unittest.TestCase):
    def setUp(self) -> None:
        self.store, self.retriever = build()
        self.addCleanup(self.store.close)
        self.generator = ExtractiveGenerator()

    def test_answers_a_question_the_corpus_covers(self) -> None:
        hits = self.retriever.search("how does it decide a document changed?")
        answer = self.generator.generate("how does it decide a document changed?", hits)
        self.assertFalse(answer.abstained)
        self.assertIn("hash", answer.text.lower())

    def test_every_sentence_in_the_answer_came_from_a_chunk(self) -> None:
        question = "why are timestamps not used?"
        answer = self.generator.generate(question, self.retriever.search(question))
        self.assertFalse(answer.abstained)
        for citation in answer.citations:
            chunk = next(h.chunk for h in answer.retrieved
                         if h.chunk.chunk_id == citation.chunk_id)
            self.assertIn(citation.quote[:60], chunk.text)

    def test_abstains_when_nothing_was_retrieved(self) -> None:
        answer = self.generator.generate("what colour is the sky on Mars?", [])
        self.assertTrue(answer.abstained)
        self.assertEqual(answer.citations, [])

    def test_abstains_rather_than_assembling_an_unrelated_passage(self) -> None:
        question = "what is the airspeed velocity of an unladen swallow?"
        answer = self.generator.generate(question, self.retriever.search(question))
        self.assertTrue(answer.abstained)

    def test_an_echo_of_the_question_is_not_accepted_as_an_answer(self) -> None:
        # The pathological case: a corpus containing the question verbatim
        # scores perfectly on term overlap while answering nothing.
        question = "how does the pipeline decide a document has changed?"
        echo_store = Store(":memory:")
        self.addCleanup(echo_store.close)
        embedder = HashingEmbedder()
        raw = RawDocument("file", "faq.md", "file:///faq.md", "FAQ", question)
        doc = Document.from_raw(raw, question, {})
        echo_store.upsert_document(doc)
        chunks = chunk_document(doc)
        echo_store.add_chunks(chunks, embedder.embed_batch([c.indexed_text for c in chunks]))
        retriever = Retriever(echo_store, embedder, RetrievalConfig(top_k=5))
        answer = self.generator.generate(question, retriever.search(question))
        self.assertTrue(answer.abstained, f"echoed the question back: {answer.text!r}")

    def test_a_block_too_long_to_be_a_sentence_is_not_quoted_as_one(self) -> None:
        generator = ExtractiveGenerator(GenerateConfig(max_sentence_chars=50))
        question = "how does it decide a document changed?"
        answer = generator.generate(question, self.retriever.search(question))
        for citation in answer.citations:
            self.assertLessEqual(len(citation.quote), 50)

    def test_confidence_threshold_is_honoured(self) -> None:
        strict = ExtractiveGenerator(GenerateConfig(min_confidence=0.99))
        question = "how does it decide a document changed?"
        answer = strict.generate(question, self.retriever.search(question))
        self.assertTrue(answer.abstained)


class TestCitationVerification(unittest.TestCase):
    def test_a_citation_naming_an_unretrieved_chunk_is_caught(self) -> None:
        answer = Answer(question="q", text="claim [1]", retrieved=[])
        answer.citations = [Citation(1, "missing", "d", "t", "u", "quote", 1.0)]
        problems = verify_citations(answer)
        self.assertEqual(len(problems), 1)
        self.assertIn("not retrieved", problems[0])

    def test_a_clean_answer_has_no_problems(self) -> None:
        store, retriever = build()
        self.addCleanup(store.close)
        question = "why are timestamps not used?"
        answer = ExtractiveGenerator().generate(question, retriever.search(question))
        self.assertEqual(verify_citations(answer), [])


class TestMetrics(unittest.TestCase):
    def test_recall_counts_distinct_documents(self) -> None:
        self.assertEqual(recall_at_k(["a", "b", "c"], {"a", "b"}, 3), 1.0)
        self.assertEqual(recall_at_k(["a", "b", "c"], {"a", "b"}, 1), 0.5)

    def test_reciprocal_rank_uses_the_first_hit(self) -> None:
        self.assertAlmostEqual(reciprocal_rank(["x", "y", "a"], {"a"}), 1 / 3)
        self.assertEqual(reciprocal_rank(["x"], {"a"}), 0.0)

    def test_ndcg_is_one_for_a_perfect_ordering(self) -> None:
        self.assertAlmostEqual(ndcg_at_k(["a", "b", "x"], {"a", "b"}, 3), 1.0)

    def test_ndcg_never_exceeds_one_when_a_document_occupies_several_ranks(self) -> None:
        # The bug this pins: chunks of one document each contributed gain, so
        # DCG exceeded the ideal and nDCG came back above 1.
        self.assertLessEqual(ndcg_at_k(["a", "a", "a", "a"], {"a"}, 8), 1.0)

    def test_dedupe_keeps_first_position(self) -> None:
        self.assertEqual(dedupe(["b", "a", "b", "c", "a"]), ["b", "a", "c"])

    def test_metrics_are_zero_with_no_relevant_documents(self) -> None:
        self.assertEqual(recall_at_k(["a"], set(), 5), 0.0)
        self.assertEqual(ndcg_at_k(["a"], set(), 5), 0.0)


class TestGoldenLoading(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, body: str) -> Path:
        p = Path(self.tmp.name) / "goldens.jsonl"
        p.write_text(body, "utf-8")
        return p

    def test_comments_and_blank_lines_are_skipped(self) -> None:
        path = self.write('# a comment\n\n{"question":"q","relevant_uris":["u"]}\n')
        loaded, errors = load_goldens(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(errors, [])

    def test_a_malformed_line_is_reported_not_silently_dropped(self) -> None:
        # An eval set that quietly shrank scores better, which is exactly why
        # it must be loud.
        loaded, errors = load_goldens(
            self.write('{"question":"q","relevant_uris":["u"]}\n{not json}\n')
        )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(len(errors), 1)

    def test_a_case_with_no_expectation_cannot_pass_and_is_rejected(self) -> None:
        loaded, errors = load_goldens(self.write('{"question":"q"}\n'))
        self.assertEqual(loaded, [])
        self.assertIn("no expectation", errors[0])

    def test_a_missing_file_is_an_error_not_an_empty_pass(self) -> None:
        loaded, errors = load_goldens(Path(self.tmp.name) / "absent.jsonl")
        self.assertEqual(loaded, [])
        self.assertTrue(errors)


class TestContamination(unittest.TestCase):
    QUESTION = "how does the pipeline decide a document has changed?"

    def test_a_verbatim_copy_of_the_question_is_detected(self) -> None:
        found = detect_contamination(
            self.QUESTION,
            ["some preamble " + self.QUESTION + " and a trailing note"],
        )
        self.assertTrue(found)

    def test_punctuation_and_whitespace_do_not_hide_a_leak(self) -> None:
        leaked = "  how does   the pipeline decide a document has changed  "
        self.assertTrue(detect_contamination(self.QUESTION, [leaked]))

    def test_a_document_merely_about_the_same_topic_is_not_flagged(self) -> None:
        # The check must be crude enough not to punish a corpus for containing
        # the answer, which is the entire point of the corpus.
        self.assertEqual(
            detect_contamination(
                self.QUESTION,
                ["The pipeline hashes a document's text and compares the hash "
                 "with the one stored from the previous run."],
            ),
            "",
        )

    def test_a_short_question_is_not_checked(self) -> None:
        self.assertEqual(detect_contamination("why?", ["why? because."]), "")

    def test_a_contaminated_case_fails_however_good_its_metrics(self) -> None:
        # The flattering failure mode: every number improves while the
        # evaluation stops measuring anything.
        store = Store(":memory:")
        self.addCleanup(store.close)
        embedder = HashingEmbedder()
        raw = RawDocument("file", "leak.md", "file:///leak.md", "leak", self.QUESTION)
        doc = Document.from_raw(raw, self.QUESTION, {})
        store.upsert_document(doc)
        chunks = chunk_document(doc)
        store.add_chunks(chunks, embedder.embed_batch([c.indexed_text for c in chunks]))
        retriever = Retriever(store, embedder, RetrievalConfig(top_k=5))

        report = evaluate(
            retriever,
            [GoldenCase(question=self.QUESTION, relevant_uris=["file:///leak.md"])],
            k=5,
        )
        case = report.cases[0]
        self.assertEqual(case.recall, 1.0)      # metrics look perfect
        self.assertTrue(case.contaminated_by)   # and the case still fails
        self.assertFalse(case.passed)
        self.assertEqual(report.exit_code, 1)
        self.assertIn("verbatim", report.render())


class TestEvaluation(unittest.TestCase):
    def test_an_abstention_case_passes_only_by_abstaining(self) -> None:
        store, retriever = build()
        self.addCleanup(store.close)
        report = evaluate(
            retriever,
            [GoldenCase(question="what is the capital of Neptune?", should_abstain=True)],
            k=5,
        )
        self.assertEqual(report.summary["passed"], 1)
        self.assertEqual(report.exit_code, 0)

    def test_a_load_error_fails_the_run_even_if_every_case_passed(self) -> None:
        store, retriever = build()
        self.addCleanup(store.close)
        report = evaluate(retriever, [], k=5, load_errors=["goldens.jsonl:3: broken"])
        self.assertEqual(report.exit_code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
