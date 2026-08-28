"""Regressions for defects found by an independent adversarial review.

Every test here corresponds to a bug that was live in the codebase, passed the
entire existing suite, and was found only by someone deliberately trying to
break it. Each one is written to fail against the original code.

The common shape is worth noticing: almost none of these threw an exception.
They returned plausible wrong answers - a metric pinned at 1.0, a secret written
to the index, a deleted document retrievable under a different document's
citation. That is what makes an adversarial pass worth its cost.
"""

from __future__ import annotations

import sqlite3
import unittest

from oodarag.chunking import chunk_document
from oodarag.ingest.base import Connector
from oodarag.eval.contamination import _longest_run, _longest_run_span, detect
from oodarag.eval.harness import EvalHarness, Golden
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.models import Chunk, Document, RawDocument
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever
from oodarag.retrieve.rerank import HeuristicReranker, _longest_common_run
from oodarag.scrape.html import extract
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.http import normalize_url
from oodarag.util.stemming import stem
from oodarag.util.text import redact_secrets, tokenize


def _doc(doc_id: str, title: str, text: str) -> Document:
    return Document(doc_id, "filesystem", doc_id, f"file:///{doc_id}", title, text, "h")


class FtsPurgeTest(unittest.TestCase):
    """#1 - the lexical index was never actually purged."""

    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.addCleanup(self.store.close)

    def test_deleted_content_is_not_retrievable(self):
        self.store.upsert_documents([_doc("dA", "A", "x")])
        self.store.replace_chunks("dA", [Chunk("ca", "dA", 0, "pangolin classified salary")])
        self.assertTrue(self.store.search_lexical("pangolin"))
        self.store.delete_document("dA")
        self.assertEqual(self.store.search_lexical("pangolin"), [],
                         "deleted text is still in the lexical index")

    def test_a_stale_posting_cannot_resolve_to_another_document(self):
        """The severe form: SQLite reuses rowids, so an orphaned posting is
        inherited by whatever chunk lands on that rowid next - and the answer
        cites the wrong document for text it does not contain."""
        self.store.upsert_documents([_doc("dA", "A", "x"), _doc("dB", "B", "y")])
        self.store.replace_chunks("dA", [Chunk("ca", "dA", 0, "pangolin classified salary")])
        self.store.delete_document("dA")
        self.store.replace_chunks("dB", [Chunk("cb", "dB", 0, "public weather notes")])
        for chunk_id, _ in self.store.search_lexical("pangolin"):
            chunk = self.store.get_chunks([chunk_id])[chunk_id]
            self.fail(f"'pangolin' resolved to {chunk.doc_id}: {chunk.text!r}")

    def test_replacing_chunks_removes_the_old_text_from_the_index(self):
        self.store.upsert_documents([_doc("d1", "D", "x")])
        self.store.replace_chunks("d1", [Chunk("k1", "d1", 0, "aardvark provisioning notes")])
        self.store.replace_chunks("d1", [Chunk("k2", "d1", 0, "completely different words")])
        self.assertEqual(self.store.search_lexical("aardvark"), [])
        self.assertTrue(self.store.search_lexical("completely"))


class RedactionTest(unittest.TestCase):
    """#2 - `\\b` before the keyword never matched a prefixed name."""

    def test_prefixed_key_names_are_redacted(self):
        for text in ["GITHUB_TOKEN=s3cretValue1234567890",
                     "DB_PASSWORD=p@ssw0rd!longenough",
                     "export SERVICE_API_KEY='abcdefgh12345678'",
                     "MY_APP_SECRET: hunter2hunter2hunter2"]:
            with self.subTest(text=text):
                self.assertIn("<redacted", redact_secrets(text),
                              "a prefixed credential name was not redacted")
                self.assertNotIn("s3cretValue1234567890", redact_secrets(text))

    def test_values_with_punctuation_are_still_redacted(self):
        self.assertNotIn("p@ssw0rd!longenough",
                         redact_secrets("DB_PASSWORD=p@ssw0rd!longenough"))

    def test_a_specific_marker_is_not_overwritten_by_the_generic_rule(self):
        out = redact_secrets("SECRET = 'ghp_Z9y8X7w6V5u4T3s2R1q0'")
        self.assertIn("<redacted:github-token>", out,
                      "the generic rule overwrote the specific one")

    def test_ordinary_prose_is_untouched(self):
        for text in ["The token budget is bounded.",
                     "This is a secret to nobody.",
                     "password reset instructions are in the docs"]:
            with self.subTest(text=text):
                self.assertEqual(redact_secrets(text), text)


class RecallMetricTest(unittest.TestCase):
    """#3 - recall was computed against a relevant set built from the retrieved
    list, making it a subset by construction and the metric a constant."""

    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        docs = [
            _doc("d1", "alpha.md", "Hybrid retrieval fuses dense and lexical arms together."),
            _doc("d2", "beta.md", "Budgets bound requests bytes depth and wall clock time."),
            _doc("d3", "gamma.md", "Citations are verified against the retrieved chunks."),
        ]
        self.store.upsert_documents(docs)
        self.pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            self.store.replace_chunks(d.doc_id, chunk_document(d))
        self.pipeline.embed_missing()
        self.generator = AnswerGenerator(
            HybridRetriever(self.store, self.pipeline.embedder),
            AnswerConfig(generator="extractive"))
        self.addCleanup(self.store.close)

    def test_recall_is_zero_when_nothing_expected_is_retrieved(self):
        report = EvalHarness(self.generator, k=5).run(
            [Golden(question="how are dense and lexical arms combined?",
                    expect_sources=["NONEXISTENT.md"])])
        self.assertEqual(report.cases[0].recall, 0.0,
                         "recall reported a hit for a source that was never retrieved")
        self.assertEqual(report.aggregate()["recall@5"]["mean"], 0.0)

    def test_partial_recall_is_a_fraction_not_one(self):
        report = EvalHarness(self.generator, k=5).run(
            [Golden(question="how are dense and lexical arms combined?",
                    expect_sources=["alpha.md", "NOPE1.md", "NOPE2.md"])])
        self.assertAlmostEqual(report.cases[0].recall, 1 / 3,
                               msg="recall did not fall for the two missing sources")

    def test_full_recall_when_everything_expected_is_retrieved(self):
        report = EvalHarness(self.generator, k=8).run(
            [Golden(question="budgets bound requests and citations are verified",
                    expect_sources=["beta.md", "gamma.md"])])
        self.assertEqual(report.cases[0].recall, 1.0, report.cases[0].retrieved_uris)


class ContaminationAnalysisTest(unittest.TestCase):
    """#4 and #5 - the two sides were analysed differently, so the check both
    missed real quotations and invented false ones."""

    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.addCleanup(self.store.close)

    def _index(self, docs: dict[str, str]):
        self.store.upsert_documents([_doc(k, k, v) for k, v in docs.items()])
        for k, v in docs.items():
            self.store.replace_chunks(k, chunk_document(_doc(k, k, v)))

    def test_the_excerpt_quotes_what_was_actually_matched(self):
        """The excerpt is the evidence for quarantining a document, and it used
        to be sliced from the wrong string: the offset indexed the stemmed token
        text and then sliced the raw document, so every excerpt showed unrelated
        content. It also re-searched for the question's *first* words, assuming
        the run began at the question's start."""
        question = "Who won the 1998 World Cup final?"
        filler = "Padding sentence about chunking and budgets. " * 20
        self._index({"leak.md": f"{filler}A transcript line: {question} And the reply."})
        report = detect(self.store, [question], negative_questions={question})
        excerpts = [f.excerpt for f in report.findings if f.excerpt]
        self.assertTrue(excerpts, "a verbatim finding carried no excerpt")
        for excerpt in excerpts:
            self.assertIn("world cup", excerpt.lower(),
                          f"excerpt does not contain the matched run: {excerpt!r}")

    def test_an_excerpt_is_produced_when_the_run_starts_late(self):
        """The old code re-searched for the question's *first* words. When the
        matched run begins later in the question that search fails, and a
        verbatim finding was reported with no evidence attached at all."""
        question = "Who won the 1998 World Cup final?"
        # The document quotes the tail of the question, never its opening words.
        self._index({"leak.md": "Coverage of the world cup final is discussed here."})
        report = detect(self.store, [question], negative_questions={question})
        verbatim = [f for f in report.findings if f.excerpt]
        self.assertTrue(verbatim,
                        "a run matching the end of the question produced no excerpt")
        for finding in verbatim:
            self.assertIn("world cup final", finding.excerpt.lower())

    def test_the_matched_run_is_returned_even_when_it_starts_late(self):
        """`_longest_run` may match a run beginning anywhere in the question."""
        words = tokenize("unrelated preamble reciprocal rank fusion", stem_words=True)
        haystack = " ".join(tokenize("the paper describes reciprocal rank fusion",
                                     stem_words=True))
        fraction, run = _longest_run_span(words, haystack)
        self.assertGreater(fraction, 0.0)
        self.assertIn("reciproc", run)
        self.assertNotIn("preambl", run)

    def test_a_question_with_a_comma_is_still_detected(self):
        question = "How does RRF work, exactly and completely?"
        self._index({"leak.md": f"Someone asked in the session: {question} Here is the reply."})
        report = detect(self.store, [question], negative_questions={question})
        self.assertFalse(report.clean,
                         "punctuation in the question hid a verbatim quotation")

    def test_a_stopword_run_is_not_contamination(self):
        query = tokenize("Who won the 1998 World Cup?", stem_words=True)
        haystack = " ".join(tokenize(
            "The journal records who won the argument about chunk sizes.", stem_words=True))
        self.assertEqual(_longest_run(query, haystack), 0.0)

    def test_a_positive_golden_is_never_quarantined(self):
        """Quarantining a positive case removes the source it expects, which
        turns a passing case into a failing one."""
        self._index({"beta.md": "Budgets bound requests, bytes, depth and wall clock time."})
        report = detect(self.store,
                        ["what bounds requests bytes depth and wall clock time?"],
                        negative_questions=set())
        self.assertTrue(report.clean, report.summary())


class PhraseBoundaryTest(unittest.TestCase):
    """#13 - a run matched the tail of a longer token."""

    def test_a_run_does_not_match_inside_a_longer_token(self):
        self.assertEqual(_longest_common_run(["rank", "fusion"], "prank fusion unrel"), 0.0)

    def test_a_genuine_run_still_matches(self):
        self.assertEqual(_longest_common_run(["rank", "fusion"], "use rank fusion here"), 1.0)

    def test_a_leading_partial_token_does_not_match(self):
        self.assertEqual(_longest_common_run(["ate", "plan"], "plate planning"), 0.0)


class LexicalPreFilterTest(unittest.TestCase):
    """#10 - the lexical arm post-filtered, so a filtered search returned
    nothing whenever the allowed chunks ranked below the global window."""

    def test_a_low_ranked_allowed_chunk_is_still_found(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        docs = [_doc(f"n{i}", f"n{i}.md", "budget budget budget bytes depth") for i in range(200)]
        target = _doc("T1", "target.md", "budget considerations for one small source")
        store.upsert_documents(docs + [target])
        for d in docs + [target]:
            store.replace_chunks(d.doc_id, [Chunk(f"c{d.doc_id}", d.doc_id, 0, d.text)])
        allowed = {"cT1"}
        hits = store.search_lexical("budget", k=10, allowed=allowed)
        self.assertEqual([h[0] for h in hits], ["cT1"],
                         "the filtered lexical arm returned nothing")


class EmptyFilterTest(unittest.TestCase):
    """#15 - an empty exclusion list built a WHERE with no predicate."""

    def test_an_empty_exclusion_means_no_constraint(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        store.upsert_documents([_doc("d1", "a.md", "text here")])
        store.replace_chunks("d1", [Chunk("c1", "d1", 0, "text here")])
        self.assertIsNone(store.filter_chunk_ids({"exclude_doc_ids": []}))
        self.assertIsNone(store.filter_chunk_ids({"exclude_source_system": []}))


class IdfCacheTest(unittest.TestCase):
    """#9 - the cache key was the chunk count, so equal-count edits went stale."""

    def test_reworded_content_of_the_same_size_invalidates_the_cache(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        store.upsert_documents([_doc("d1", "a.md", "x"), _doc("d2", "b.md", "y")])
        store.replace_chunks("d1", [Chunk("c1", "d1", 0, "alpha alpha alpha")])
        store.replace_chunks("d2", [Chunk("c2", "d2", 0, "alpha beta gamma")])
        self.assertIn("alpha", store.idf_table())
        store.replace_chunks("d1", [Chunk("c3", "d1", 0, "delta delta delta")])
        store.replace_chunks("d2", [Chunk("c4", "d2", 0, "delta epsilon zeta")])
        table = store.idf_table()
        self.assertIn("delta", table, "the idf table was served stale after a rewrite")
        self.assertNotIn("alpha", table)


class RefitBaselineTest(unittest.TestCase):
    """#8 - the refit baseline was rewritten on every run, so growth measured
    against the last run rather than the last fit and never accumulated."""

    def test_the_baseline_only_moves_when_a_fit_happens(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        docs = [_doc(f"d{i}", f"{i}.md", f"document number {i} about retrieval") for i in range(20)]
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        store.set_meta("fitted_doc_count", len(docs))
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()
        self.assertEqual(store.get_meta("fitted_doc_count"), 20,
                         "embedding moved the refit baseline")

        more = [_doc(f"e{i}", f"e{i}.md", f"another document {i}") for i in range(4)]
        store.upsert_documents(more)
        for d in more:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()
        self.assertEqual(store.get_meta("fitted_doc_count"), 20,
                         "the baseline drifted with the corpus, so growth never accumulates")


class UrlNormalizationTest(unittest.TestCase):
    """#11 - %2F was decoded into a real separator."""

    def test_encoded_and_literal_separators_stay_distinct(self):
        self.assertNotEqual(normalize_url("http://x.test/a%2Fb"),
                            normalize_url("http://x.test/a/b"))

    def test_escape_case_is_normalised(self):
        self.assertEqual(normalize_url("http://x.test/a%2fb"),
                         normalize_url("http://x.test/a%2Fb"))


class HtmlRobustnessTest(unittest.TestCase):
    """#7 and #14 - fence parity and an unclosed script."""

    def test_stray_backticks_in_prose_do_not_corrupt_a_code_block(self):
        code = "def f():\n    if x:\n        return    1"
        html = ("<html><body><main><h1>T</h1>"
                "<p>Use ``` to open a fence in markdown.</p>"
                f"<pre><code>{code}</code></pre>"
                f"<p>{'word ' * 40}</p></main></body></html>")
        markdown = extract(html, "https://e.com/").markdown
        lines = markdown.split("\n")
        fences = [i for i, line in enumerate(lines) if line.startswith("```")]
        self.assertGreaterEqual(len(fences), 2, markdown)
        block = "\n".join(lines[fences[0] + 1:fences[1]])
        self.assertIn("        return    1", block,
                      "code-block indentation was collapsed")

    def test_an_unclosed_script_does_not_swallow_the_page(self):
        body = "Real article content that should be extracted. " + "word " * 40
        html = f"<html><body><main><h1>T</h1><script>var a=1;<p>{body}</p></main></body></html>"
        page = extract(html, "https://e.com/")
        self.assertGreater(page.word_count, 20,
                           "an unclosed <script> discarded the rest of the document")
        self.assertIn("Real article content", page.text)


class TranscriptTimestampTest(unittest.TestCase):
    """#6 - timestamps were estimated from word counts and saturated on the
    last cue, so every deep link pointed at the end of the video."""

    def test_each_chunk_carries_the_timestamp_of_the_cue_it_starts_at(self):
        cues = "\n".join(
            f"[0:{i:02d}] cue number {i} with enough words to fill out the window here"
            for i in range(60))
        doc = Document.from_raw(
            RawDocument("youtube", "v", "https://www.youtube.com/watch?v=abc", "V", cues),
            cues, {"kind": "transcript"})
        chunks = chunk_document(doc)
        self.assertGreater(len(chunks), 2)
        seconds = [int(c.metadata["timestamp"].split(":")[1]) for c in chunks]
        self.assertEqual(seconds, sorted(seconds), "timestamps are not monotonic")
        self.assertEqual(len(set(seconds)), len(seconds),
                         f"timestamps saturated: {seconds}")
        for chunk in chunks:
            with self.subTest(ordinal=chunk.ordinal):
                # The chunk must actually begin at the cue it claims.
                claimed = int(chunk.metadata["timestamp"].split(":")[1])
                self.assertIn(f"cue number {claimed} ", chunk.text[:60])
                self.assertTrue(chunk.metadata["deep_link"].endswith(f"t={claimed}"))


if __name__ == "__main__":
    unittest.main()


class PruneRemovedDocumentsTest(unittest.TestCase):
    """Documents removed at the source stayed in the index and stayed citable.

    The connector detected the removal and recorded it in its cursor; nothing
    downstream could see it, because the delta did not carry it. An answer could
    therefore quote text that no longer existed, with a URI that no longer
    resolved - the same class of failure as a stale lexical posting, one level
    up from it.
    """

    def setUp(self):
        import shutil
        import tempfile
        from pathlib import Path

        from oodarag.ingest.filesystem import FilesystemConnector

        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "keep.md").write_text(
            "# Keep\n\nThis document describes the retention policy for archives.\n")
        (self.root / "gone.md").write_text(
            "# Gone\n\nThe pangolin protocol governs classified salary bands.\n")
        for i in range(8):
            (self.root / f"f{i}.md").write_text(
                f"# Doc {i}\n\nRoutine content about indexing number {i}.\n")
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        self.connector = FilesystemConnector(self.root, patterns=("**/*.md",))
        self.pipeline.run([self.connector])
        self.addCleanup(self.store.close)

    def test_the_delta_carries_the_removed_ids(self):
        (self.root / "gone.md").unlink()
        report = self.pipeline.run([self.connector])
        self.assertEqual(report.deltas[0].removed, ["gone.md"])
        self.assertEqual(report.deltas[0].source_system, "filesystem")

    def test_pruning_deletes_the_document_and_it_stops_being_retrievable(self):
        before = self.store.stats()["documents"]
        (self.root / "gone.md").unlink()
        report = self.pipeline.run([self.connector])
        prune = self.pipeline.prune(report.deltas)
        self.assertEqual(prune.deleted, 1)
        self.assertEqual(self.store.stats()["documents"], before - 1)
        retriever = HybridRetriever(self.store, self.pipeline.embedder)
        hits, _ = retriever.retrieve("pangolin protocol classified", top_k=3)
        for hit in hits:
            self.assertNotIn("gone.md", hit.citation_title)
        # And its text is gone from the lexical index too, not just the table.
        for chunk_id, _ in self.store.search_lexical("pangolin", k=5):
            chunk = self.store.get_chunks([chunk_id])[chunk_id]
            self.assertNotIn("pangolin", chunk.text.lower())

    def test_a_bulk_disappearance_is_refused_not_obeyed(self):
        """A source can return almost nothing for reasons unrelated to deletion:
        an expired token, a truncated listing, an unmounted path. Obeying that
        empties the index in one run."""
        before = self.store.stats()["documents"]
        for path in sorted(self.root.glob("*.md"))[:-1]:
            path.unlink()
        report = self.pipeline.run([self.connector])
        prune = self.pipeline.prune(report.deltas)
        self.assertEqual(prune.deleted, 0)
        self.assertTrue(prune.refused)
        self.assertIn("guard", prune.refused[0])
        self.assertEqual(self.store.stats()["documents"], before,
                         "the guard did not hold and the index was emptied")

    def test_an_explicit_bulk_prune_is_still_possible(self):
        before = self.store.stats()["documents"]
        for path in sorted(self.root.glob("*.md"))[:-1]:
            path.unlink()
        report = self.pipeline.run([self.connector])
        prune = self.pipeline.prune(report.deltas, max_removal_fraction=1.0)
        self.assertEqual(prune.deleted, before - 1)

    def test_a_failed_connector_reports_no_removals(self):
        """A source that failed part way through has not proved anything is
        gone; treating a truncated listing as deletion is how an index empties
        itself."""
        from oodarag.ingest.filesystem import FilesystemConnector

        class Failing(FilesystemConnector):
            def fetch(self, cursor):
                yield from ()
                raise RuntimeError("source unavailable")

        failing = Failing(self.root, patterns=("**/*.md",), key=self.connector.key)
        report = self.pipeline.run([failing])
        self.assertEqual(report.deltas[0].failed, 1)
        self.assertEqual(report.deltas[0].removed, [])

    def test_a_prune_is_scoped_to_one_source_system(self):
        """Two sources may legitimately use the same external id."""
        from oodarag.models import Document

        self.store.upsert_documents([
            Document("other", "web", "gone.md", "https://e.com/gone.md",
                     "someone else's gone.md", "unrelated text", "h")])
        (self.root / "gone.md").unlink()
        report = self.pipeline.run([self.connector])
        self.pipeline.prune(report.deltas)
        self.assertIsNotNone(self.store.get_document("other"),
                             "the prune crossed a source boundary")


class AnswerabilityTest(unittest.TestCase):
    """A query using words the corpus has never seen is not answerable by it.

    Fractional IDF-weighted coverage hides *which* part of a query matched. On a
    corpus of Python package pages, "what is the boiling point of mercury"
    matched the word "point", took a third of its coverage from that one
    incidental word, and was answered with confidence 0.76 - while neither
    "boiling" nor "mercury" occurs anywhere in that corpus.
    """

    def setUp(self):
        from oodarag.retrieve.rerank import HeuristicReranker

        self.reranker = HeuristicReranker(
            idf=lambda t: {"common": 1.0}.get(t, 8.0),
            vocabulary={"common", "chunk", "retriev", "index"},
            min_vocabulary_for_answerability=0,
        )

    def test_a_fully_known_query_is_unpenalised(self):
        self.assertEqual(self.reranker._answerability({"chunk", "retriev"}), 1.0)

    def test_a_query_of_unknown_terms_collapses(self):
        self.assertEqual(self.reranker._answerability({"mercuri", "boil"}), 0.0)

    def test_one_incidental_known_word_does_not_carry_the_query(self):
        # "common" is known but uninformative; the two unknown terms dominate.
        value = self.reranker._answerability({"common", "mercuri", "boil"})
        self.assertLess(value, 0.1, "an incidental common word carried an unanswerable query")

    def test_it_is_disabled_on_a_corpus_too_small_for_absence_to_mean_anything(self):
        from oodarag.retrieve.rerank import HeuristicReranker

        small = HeuristicReranker(idf=lambda t: 8.0, vocabulary={"a", "b"},
                                  min_vocabulary_for_answerability=2000)
        self.assertEqual(small._answerability({"mercuri", "boil"}), 1.0)

    def test_it_is_deterministic_across_processes(self):
        """The first version of this used max(query_set, key=idf), which picks
        an arbitrary element when terms tie - and Python randomises string
        hashing per process, so the same question abstained or answered
        depending on the run."""
        import pathlib
        import subprocess
        import sys

        script = (
            "import sys; sys.path.insert(0, 'src');"
            "from oodarag.retrieve.rerank import HeuristicReranker;"
            "r = HeuristicReranker(idf=lambda t: 8.0, vocabulary={'point'},"
            " min_vocabulary_for_answerability=0);"
            "print(round(r._answerability({'boil', 'point', 'mercuri'}), 6))"
        )
        seen = {
            subprocess.run([sys.executable, "-c", script], capture_output=True,
                           text=True,
                           cwd=str(pathlib.Path(__file__).resolve().parent.parent)).stdout.strip()
            for _ in range(4)
        }
        self.assertEqual(len(seen), 1, f"non-deterministic across processes: {seen}")


class QueryExpansionTest(unittest.TestCase):
    """Pseudo-relevance feedback: implemented, measured, and left off.

    It made retrieval measurably worse on the primary corpus and changed nothing
    on the external one (see retrieve/expansion.py for the table). These tests
    pin the default and the properties that bound the damage, so the decision
    survives someone flipping it on by reflex.
    """

    def test_it_is_off_by_default(self):
        from oodarag.retrieve.hybrid import RetrievalConfig

        self.assertFalse(RetrievalConfig().use_expansion,
                         "expansion was enabled by default despite measuring worse")

    def test_expansion_never_selects_the_original_query_terms(self):
        from oodarag.retrieve.expansion import expand

        chunks = [Chunk(f"c{i}", "d", i, "budget bytes depth wall clock crawl")
                  for i in range(4)]
        result = expand("crawl budget", chunks, idf=lambda t: 5.0)
        self.assertNotIn("crawl", result.terms)
        self.assertNotIn("budget", result.terms)

    def test_a_term_common_across_the_corpus_is_not_selected(self):
        """Selecting on raw frequency picks the corpus's most common words,
        which are by definition its least informative ones."""
        from oodarag.retrieve.expansion import expand

        chunks = [Chunk(f"c{i}", "d", i, "ubiquitous rare_signal text here")
                  for i in range(4)]
        result = expand("query", chunks, idf=lambda t: 5.0,
                        corpus_frequency=lambda t: 0.99 if t == "ubiquitous" else 0.01)
        self.assertNotIn("ubiquitous", result.terms)
        self.assertIn("rare_signal", result.terms)

    def test_empty_feedback_expands_to_nothing(self):
        from oodarag.retrieve.expansion import expand

        self.assertEqual(expand("anything", [], idf=lambda t: 1.0).terms, [])

    def test_enabling_it_still_returns_results(self):
        """Off by default is a judgement about quality, not a broken path."""
        from oodarag.ingest.filesystem import FilesystemConnector
        from oodarag.retrieve.hybrid import RetrievalConfig

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        docs = [_doc(f"d{i}", f"{i}.md",
                     f"Crawling is bounded by requests, bytes and depth, item {i}.")
                for i in range(6)]
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()
        retriever = HybridRetriever(store, pipeline.embedder,
                                    RetrievalConfig(use_expansion=True))
        results, trace = retriever.retrieve("what bounds a crawl")
        self.assertTrue(results)
        self.assertIn("expansion_ms", trace.stages)


class GradedMetricScopeTest(unittest.TestCase):
    """Retrieval metrics were averaged over abstention cases too.

    An `expect_abstain` case has nothing to retrieve, so its recall is
    definitionally zero. Averaging those zeros in meant that *adding a negative
    case* lowered reported recall - the metric moved for a reason that had
    nothing to do with retrieval. Reported external recall@8 read 0.80 while
    every graded case was in fact fully satisfied.
    """

    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        docs = [
            _doc("d1", "alpha.md", "Hybrid retrieval fuses dense and lexical arms together."),
            _doc("d2", "beta.md", "Budgets bound requests bytes depth and wall clock time."),
        ]
        self.store.upsert_documents(docs)
        self.pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            self.store.replace_chunks(d.doc_id, chunk_document(d))
        self.pipeline.embed_missing()
        self.generator = AnswerGenerator(
            HybridRetriever(self.store, self.pipeline.embedder),
            AnswerConfig(generator="extractive"))
        self.addCleanup(self.store.close)

    def test_abstention_cases_are_excluded_from_retrieval_metrics(self):
        satisfiable = Golden(question="how are dense and lexical arms combined?",
                             expect_sources=["alpha.md"])
        negative = Golden(question="what is the melting point of gallium?",
                          expect_abstain=True)

        alone = EvalHarness(self.generator, k=5).run([satisfiable])
        with_negative = EvalHarness(self.generator, k=5).run([satisfiable, negative])

        self.assertEqual(alone.aggregate()["recall@5"]["mean"],
                         with_negative.aggregate()["recall@5"]["mean"],
                         "adding a negative case changed reported recall")
        self.assertEqual(with_negative.aggregate()["recall@5"]["n"], 1)

    def test_only_cases_with_expectations_are_graded(self):
        report = EvalHarness(self.generator, k=5).run([
            Golden(question="how are dense and lexical arms combined?",
                   expect_sources=["alpha.md"]),
            Golden(question="what is the melting point of gallium?", expect_abstain=True),
        ])
        self.assertEqual([c.graded for c in report.cases], [True, False])


class CoveragePowerTest(unittest.TestCase):
    """IDF concentration: measured, and deliberately left at its default.

    Raising it improved pass rate and precision on both corpora and cost 0.031
    of recall on the primary one. Recall is the ceiling on everything
    downstream, so the default did not move on evidence that mixed - see the
    table in rerank.py.
    """

    def test_the_default_is_plain_idf_weighting(self):
        from oodarag.retrieve.rerank import HeuristicReranker

        self.assertEqual(HeuristicReranker().coverage_power, 1.0)

    def test_raising_it_concentrates_weight_on_the_rare_term(self):
        from oodarag.retrieve.rerank import HeuristicReranker
        from oodarag.models import Chunk, ScoredChunk

        idf = {"rare": 8.0, "common": 1.0}.get
        # A chunk with the generic terms but not the distinctive one.
        chunk = Chunk("c", "d", 0, "common common words only here")
        def coverage(power):
            rr = HeuristicReranker(idf=lambda t: idf(t, 1.0), coverage_power=power)
            scored = [ScoredChunk(chunk=chunk, score=0.5)]
            rr.rerank("rare common", scored)
            return scored[0].components["rerank_coverage"]

        self.assertGreater(coverage(1.0), coverage(3.0),
                           "concentration did not reduce the generic-only match")


class CursorIndexDesyncTest(unittest.TestCase):
    """A cursor that outlives its index produced a silently partial corpus.

    Incremental ingest decides "unchanged, skip" from the cursor alone. Rebuild
    the index while a separate state file survives and every document it lists
    is reported unchanged and never re-added. Observed for real: deleting an
    index and re-running produced 19 documents out of 33, with zero errors
    reported - the only symptom was the eval score halving.
    """

    def setUp(self):
        import shutil
        import tempfile
        from pathlib import Path

        from oodarag.ingest.filesystem import FilesystemConnector

        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.source = self.root / "src"
        self.source.mkdir()
        for i in range(6):
            (self.source / f"d{i}.md").write_text(
                f"# Doc {i}\n\nContent about retrieval number {i}.\n")
        self.connector = FilesystemConnector(self.source, patterns=("**/*.md",))

    def test_a_surviving_cursor_does_not_hide_a_rebuilt_index(self):
        from oodarag.ingest.base import JsonStateStore

        state = JsonStateStore(self.root / "state.json")
        first = SqliteStore(":memory:")
        self.addCleanup(first.close)
        IndexPipeline(first, state=state).run([self.connector])
        self.assertEqual(first.stats()["documents"], 6)

        rebuilt = SqliteStore(":memory:")
        self.addCleanup(rebuilt.close)
        report = IndexPipeline(rebuilt, state=state).run([self.connector])
        self.assertEqual(rebuilt.stats()["documents"], 6,
                         "the rebuilt index is missing documents the cursor claimed")
        self.assertEqual(report.deltas[0].new, 6)

    def test_cursors_default_to_living_inside_the_index(self):
        from oodarag.ingest.base import SqliteStateStore

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        self.assertIsInstance(IndexPipeline(store).state, SqliteStateStore)

    def test_an_intact_index_still_skips_unchanged_documents(self):
        """The reconciliation must not defeat incrementality when nothing is
        actually missing."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        pipeline.run([self.connector])
        second = pipeline.run([self.connector])
        self.assertEqual(second.deltas[0].new, 0)
        self.assertEqual(second.deltas[0].unchanged, 6)


class RerankCouplingTest(unittest.TestCase):
    """Turning off reranking silently disabled the abstention gate.

    The gate reads `rerank_relevance`, which only the reranker computes. Making
    the feature pass conditional on `use_rerank` meant relevance defaulted to
    zero and the system abstained on almost everything - 8 of 36 golden cases
    instead of 32, while recall stayed at 0.857. A configuration flag must
    degrade the behaviour it names, not disable an unrelated safety check.
    """

    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        docs = [
            _doc("d1", "fusion.md",
                 "Reciprocal rank fusion combines a dense arm and a lexical arm by rank."),
            _doc("d2", "budgets.md",
                 "Budgets bound requests, bytes, depth and wall clock time for a crawl."),
            _doc("d3", "citations.md",
                 "Citation markers are verified against the chunks actually retrieved."),
        ]
        self.store.upsert_documents(docs)
        self.pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            self.store.replace_chunks(d.doc_id, chunk_document(d))
        self.pipeline.embed_missing()
        self.addCleanup(self.store.close)

    def _answer(self, use_rerank: bool):
        from oodarag.retrieve.hybrid import RetrievalConfig

        retriever = HybridRetriever(self.store, self.pipeline.embedder,
                                    RetrievalConfig(use_rerank=use_rerank))
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        return generator.answer("how are dense and lexical arms combined by rank?")

    def test_relevance_is_computed_even_with_reranking_off(self):
        """Every result must still carry the gate's input, and its score must be
        the fused one - not the reranked one the flag was meant to suppress."""
        from oodarag.retrieve.hybrid import RetrievalConfig

        results, _ = HybridRetriever(
            self.store, self.pipeline.embedder,
            RetrievalConfig(use_rerank=False),
        ).retrieve("dense and lexical arms")
        self.assertTrue(results)
        for result in results:
            self.assertIn("rerank_relevance", result.components,
                          "the abstention gate lost its only input")
            self.assertIn("pre_rerank_score", result.components)
            self.assertAlmostEqual(result.score, result.components["pre_rerank_score"],
                                   places=6,
                                   msg="use_rerank=False left the reranked score in place")
        self.assertGreater(max(r.components["rerank_relevance"] for r in results), 0.0)

    def test_disabling_rerank_does_not_cause_a_blanket_abstention(self):
        with_rerank = self._answer(True)
        without = self._answer(False)
        self.assertFalse(with_rerank.abstained, with_rerank.text)
        self.assertFalse(without.abstained,
                         f"turning off reranking made the system abstain: {without.text[:120]}")
        self.assertGreater(without.metrics["best_relevance"], 0.0,
                           "relevance was not computed with reranking off")

    def test_disabling_rerank_actually_changes_the_score(self):
        """The first fix restored list order but not the score, so MMR and the
        score floor still read the reranked value and the flag did nothing."""
        from oodarag.retrieve.hybrid import RetrievalConfig

        query = "how are dense and lexical arms combined by rank?"
        reranked, _ = HybridRetriever(self.store, self.pipeline.embedder,
                                      RetrievalConfig(use_rerank=True)).retrieve(query)
        plain, _ = HybridRetriever(self.store, self.pipeline.embedder,
                                   RetrievalConfig(use_rerank=False)).retrieve(query)
        self.assertNotAlmostEqual(reranked[0].score, plain[0].score, places=4,
                                  msg="use_rerank=False left the reranked score in place")
        # The features are still there either way - the gate needs them.
        self.assertIn("rerank_relevance", plain[0].components)


class GhostCompoundTest(unittest.TestCase):
    """A hyphenated query term was an unmatchable term with the maximum idf.

    `tokenize` keeps `snake_case`, `dotted.paths` and hyphenated words whole so
    identifiers survive a corpus that is half code. FTS5's unicode61 splits on
    those separators, so the lexical arm matched a quoted "in-process" against a
    document saying "in process" - and the reranker then scored that same
    document as containing neither. Because a term the corpus has never held
    gets the maximum idf, the ghost dominated the coverage denominator and
    answerability: a retrieved, relevant document was abstained on at relevance
    0.13 against a 0.15 floor.
    """

    def test_sqlite_and_the_tokenizer_really_do_disagree(self):
        """The premise, observed from SQLite rather than asserted about it.

        If FTS5 ever stops splitting on these separators the fix below is
        unnecessary, and this test is how we would find out.
        """
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        try:
            conn.execute("CREATE VIRTUAL TABLE t USING fts5"
                         "(x, tokenize='porter unicode61 remove_diacritics 2')")
        except sqlite3.OperationalError:
            self.skipTest("FTS5 unavailable in this SQLite build")
        conn.execute("INSERT INTO t VALUES (?)",
                     ("blinker provides fast in process signal dispatching",))
        matched = conn.execute(
            "SELECT count(*) FROM t WHERE t MATCH ?", ('"in-process"',)).fetchone()[0]
        self.assertEqual(matched, 1,
                         "FTS5 no longer treats a hyphen as a separator")
        # The Python tokenizer, given the same string, keeps it whole.
        self.assertIn("in-process", tokenize("in-process notifications"))

    def _reranker(self, vocabulary: set[str]):
        return HeuristicReranker(idf=lambda t: 8.56 if t not in vocabulary else 2.0,
                                 vocabulary=vocabulary)

    def test_a_compound_the_corpus_lacks_is_replaced_by_its_parts(self):
        reranker = self._reranker({"process", "notif", "signal"})
        query_set = reranker._query_set(tokenize("in-process notifications", stem_words=True))
        self.assertNotIn("in-process", query_set,
                         "a term the corpus cannot contain was left in the query")
        self.assertIn("process", query_set)
        self.assertIn("notif", query_set)

    def test_a_compound_the_corpus_has_keeps_its_atomic_identity(self):
        """Splitting unconditionally would dissolve every identifier in a corpus
        that is half code, which is what the whole-token regex exists to stop."""
        vocabulary = {"oodarag.util.text", "oodarag", "util", "text"}
        reranker = self._reranker(vocabulary)
        query_set = reranker._query_set(tokenize("oodarag.util.text", stem_words=True))
        self.assertEqual(query_set, {"oodarag.util.text"})

    def test_an_unsplittable_unknown_term_survives(self):
        """A plain unknown word is real evidence of absence - that is what
        answerability is for - so it must not be dropped."""
        reranker = self._reranker({"process"})
        query_set = reranker._query_set(tokenize("mercury boiling", stem_words=True))
        self.assertEqual(query_set, {"mercuri", "boil"})

    def test_the_ghost_no_longer_dominates_answerability(self):
        """Derived, not copied from a run: with the ghost present the query's
        known idf mass is 2.0 of 10.56; split, it is all of it."""
        vocabulary = {"process", "notif"}
        reranker = self._reranker(vocabulary)
        terms = tokenize("in-process notifications", stem_words=True)
        reranker.min_vocabulary_for_answerability = 0
        with_ghost = reranker._answerability(set(terms))
        repaired = reranker._answerability(reranker._query_set(terms))
        self.assertAlmostEqual(with_ghost, 2.0 / 10.56, places=4)
        self.assertAlmostEqual(repaired, 1.0, places=4)
        self.assertGreater(repaired, with_ghost)


class StaleFitTest(unittest.TestCase):
    """A corpus rewritten in place left the embedder fitted on the old text.

    `_should_refit` compared document counts. Removing the site template from
    the 33-page external corpus deleted 90.9% of its text and left the count at
    33, so no refit fired. The same corpus and the same code then produced
    recall 1.0 through the incremental path and 0.9821 rebuilt from scratch -
    identical inputs, different answers, and nothing logged. `idf_table` already
    keys itself on corpus content for exactly this reason; the fit did not.
    """

    def _connector(self, texts: dict[str, str]):
        """A real Connector subclass, not a stand-in: the pipeline reads
        `source_system` and the cursor protocol off this interface, and a stub
        that omits them tests the stub."""
        docs = [RawDocument(source_system="test", external_id=name, uri=f"mem://{name}",
                            title=name, text=text, metadata={})
                for name, text in texts.items()]

        class _MemoryConnector(Connector):
            key = "test:stale"
            source_system = "test"

            def fetch(self, cursor):
                yield from docs

        return _MemoryConnector()

    def _pipeline(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        return IndexPipeline(store), store

    def test_a_corpus_rewritten_in_place_forces_a_refit(self):
        pipeline, store = self._pipeline()
        verbose = {f"d{i}.md": f"Package {i} does something. " + ("filler text " * 200)
                   for i in range(8)}
        pipeline.run([self._connector(verbose)])
        fitted_before = store.get_meta("fitted_text_bytes", 0)
        self.assertGreater(fitted_before, 0, "the fit did not record the corpus volume")

        # Same document count, same names, 90% less text - the shape of the
        # boilerplate removal that exposed this.
        terse = {f"d{i}.md": f"Package {i} does something." for i in range(8)}
        report = pipeline.run([self._connector(terse)])
        self.assertTrue(report.refit,
                        "the corpus lost 90% of its text and the embedder was not refit")
        self.assertLess(store.get_meta("fitted_text_bytes", 0), fitted_before)

    def test_an_ordinary_edit_does_not_force_a_refit(self):
        """Refitting invalidates every vector, so it must not fire on noise -
        otherwise the incremental path costs the same as a full rebuild."""
        pipeline, store = self._pipeline()
        texts = {f"d{i}.md": f"Package {i} does something. " + ("filler text " * 200)
                 for i in range(8)}
        pipeline.run([self._connector(texts)])
        texts["d0.md"] = texts["d0.md"] + " One more sentence."
        report = pipeline.run([self._connector(texts)])
        self.assertFalse(report.refit,
                         "a single-sentence edit triggered a full refit")

    def test_growth_still_triggers_a_refit(self):
        """The original rule must survive the new one."""
        pipeline, store = self._pipeline()
        texts = {f"d{i}.md": f"Package {i} does something distinct." for i in range(8)}
        pipeline.run([self._connector(texts)])
        texts.update({f"e{i}.md": f"New package {i} with its own vocabulary."
                      for i in range(6)})
        report = pipeline.run([self._connector(texts)])
        self.assertTrue(report.refit, "75% corpus growth did not trigger a refit")


class StaleRerankerAnalysisTest(unittest.TestCase):
    """A retriever built before indexing kept an empty vocabulary for ever.

    `HybridRetriever.__init__` captured `store.idf_lookup()` and
    `store.vocabulary()` once. `idf_lookup` closes over the table it read at that
    moment and `vocabulary` returns a plain set, so neither ever saw a later
    index run. `_answerability` returns 1.0 when the vocabulary is empty - the
    guard for a corpus too small to judge absence - so an empty *stale*
    vocabulary silently removed the abstention gate's only corpus-aware input.

    `ooda loop` constructs its generator before the ACT phase indexes anything,
    which made this every loop run: the system stopped abstaining and nothing in
    the eval output said so.
    """

    def _connector(self, texts: list[str]):
        docs = [RawDocument(source_system="t", external_id=f"d{i}", uri=f"mem://d{i}",
                            title=f"d{i}", text=text, metadata={})
                for i, text in enumerate(texts)]

        class _MemoryConnector(Connector):
            key = "t"
            source_system = "t"

            def fetch(self, cursor):
                yield from docs

        return _MemoryConnector()

    def _corpus(self) -> list[str]:
        return [
            "Reciprocal rank fusion combines a dense arm and a lexical arm by rank.",
            "Crawl budgets bound requests, bytes, depth and wall clock time.",
            "Citation markers are verified against the chunks actually retrieved.",
            "Porter stemming is applied by the FTS5 index and by the reranker.",
            "Contextual headers are embedded with each chunk of a document.",
        ]

    def test_a_retriever_built_before_indexing_sees_the_corpus(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        retriever = HybridRetriever(store, pipeline.embedder)
        self.assertFalse(retriever.reranker.vocabulary)

        pipeline.run([self._connector(self._corpus())])
        retriever.retrieve("how are dense and lexical arms combined")
        self.assertEqual(retriever.reranker.vocabulary, store.vocabulary(),
                         "the reranker kept the vocabulary it captured before indexing")

    def test_a_corpus_rewritten_in_place_updates_the_idf_table(self):
        """Keyed on content, not on a counter: same document count, new words."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        pipeline.run([self._connector(self._corpus())])
        retriever = HybridRetriever(store, pipeline.embedder)
        retriever.retrieve("fusion")
        self.assertNotIn("quokka", retriever.reranker.vocabulary)

        replacement = [f"Quokka telemetry calibration, note {i}." for i in range(5)]
        pipeline.run([self._connector(replacement)])
        retriever.retrieve("dosage")
        self.assertIn("quokka", retriever.reranker.vocabulary,
                      "the corpus was replaced and the reranker did not notice")

    def test_an_injected_reranker_is_left_alone(self):
        """Overriding the reranker is how a caller supplies its own analysis;
        overwriting it here would silently discard that."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        mine = HeuristicReranker(idf=lambda t: 1.0, vocabulary={"sentinel"})
        retriever = HybridRetriever(store, pipeline.embedder, reranker=mine)
        pipeline.run([self._connector(self._corpus())])
        retriever.retrieve("fusion")
        self.assertEqual(retriever.reranker.vocabulary, {"sentinel"})

    def test_the_gate_still_abstains_after_a_late_index(self):
        """The end-to-end consequence, not just the field: an out-of-corpus
        question must be refused by a retriever that predates the corpus."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        retriever = HybridRetriever(store, pipeline.embedder)
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        pipeline.run([self._connector(self._corpus() * 8)])
        retriever.reranker.min_vocabulary_for_answerability = 0
        answer = generator.answer("What is the boiling point of mercury?")
        self.assertTrue(answer.abstained,
                        f"answered an out-of-corpus question: {answer.text[:120]}")


class StemmerStepFourTest(unittest.TestCase):
    """Step 4 removed two suffixes, so the reranker and the index disagreed.

    Porter's step 4 removes at most one suffix. "ion" sat outside the loop as an
    unconditional rule, so "additionally" lost "al" in the loop and then "ion"
    after it, giving "addit" where SQLite's Porter tokenizer - the thing that
    actually builds the lexical index - gives "addition". The reranker then
    scored a chunk the lexical arm had ranked first as containing none of the
    query term.

    The `if suffix in ("ion",)` guard inside the loop was unreachable: "ion" was
    not in the list it iterated.
    """

    def test_step_four_removes_one_suffix_not_two(self):
        for word, expected in [("additionally", "addition"),
                               ("intentionally", "intention"),
                               ("occasional", "occasion"),
                               ("professional", "profession"),
                               ("transactionally", "transaction")]:
            with self.subTest(word=word):
                self.assertEqual(stem(word), expected)

    def test_the_ion_condition_is_reachable_and_applied(self):
        """"ion" comes off only after s or t, so a nation is not a nat."""
        from oodarag.util.stemming import _STEP4

        self.assertIn("ion", _STEP4, "the guard inside the loop is unreachable again")
        self.assertEqual(stem("nation"), "nation")
        self.assertEqual(stem("station"), "station")

    def test_agreement_with_the_index_that_actually_stems_the_corpus(self):
        """Third-party evidence: SQLite's own Porter tokenizer, read back through
        fts5vocab. Our stemmer's correctness is not the requirement - agreeing
        with the tokenizer that built the index is."""
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        try:
            conn.execute("CREATE VIRTUAL TABLE t USING fts5"
                         "(x, tokenize='porter unicode61 remove_diacritics 2')")
        except sqlite3.OperationalError:
            self.skipTest("FTS5 unavailable in this SQLite build")
        conn.execute("CREATE VIRTUAL TABLE v USING fts5vocab(t, row)")
        for word in ("additionally", "intentionally", "relationally", "occasional",
                     "professional", "transactionally", "internationalized",
                     "definitionally", "directionality", "provisionally"):
            with self.subTest(word=word):
                conn.execute("DELETE FROM t")
                conn.execute("INSERT INTO t VALUES (?)", (word,))
                terms = [row[0] for row in conn.execute("SELECT term FROM v")]
                self.assertEqual(terms, [stem(word)],
                                 f"{word!r}: the reranker and the index disagree")


class AnalyserCacheKeyTest(unittest.TestCase):
    """The cached IDF table was keyed on corpus content but not on the analyser.

    The table's *terms* are the analyser's output, not the corpus's. Change the
    stemmer and an existing index keeps serving vocabulary in the old term space
    while queries arrive in the new one - so every query term reads as absent
    from the corpus, and an absent term gets the maximum weight, which is the
    input the coverage denominator and the abstention gate both read. The FTS
    table already guards against this with a schema version.
    """

    def test_the_signature_changes_when_the_analyser_changes(self):
        from oodarag.util import stemming
        from oodarag.util.text import analysis_fingerprint

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        store.upsert_documents([_doc("d1", "a.md", "Additionally the crawl stops.")])
        store.replace_chunks("d1", chunk_document(_doc("d1", "a.md",
                                                       "Additionally the crawl stops.")))
        before = store.corpus_signature()

        original = list(stemming._STEP4)
        stemming._STEP4.remove("ion")
        analysis_fingerprint.cache_clear()
        self.addCleanup(analysis_fingerprint.cache_clear)
        self.addCleanup(lambda: stemming._STEP4.__setitem__(slice(None), original))
        after = store.corpus_signature()

        self.assertNotEqual(before, after,
                            "a stemming rule changed and the cache key did not")

    def test_the_signature_is_stable_when_nothing_changes(self):
        """A key that changes on its own defeats the cache it protects."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        store.upsert_documents([_doc("d1", "a.md", "Budgets bound requests and bytes.")])
        store.replace_chunks("d1", chunk_document(_doc("d1", "a.md",
                                                       "Budgets bound requests and bytes.")))
        self.assertEqual(store.corpus_signature(), store.corpus_signature())

    def test_a_stale_table_is_rebuilt_rather_than_served(self):
        from oodarag.util import stemming
        from oodarag.util.text import analysis_fingerprint

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        text = ("Additionally the transactional relationality of a national "
                "organisation is occasionally provisional.")
        store.upsert_documents([_doc("d1", "a.md", text)])
        store.replace_chunks("d1", chunk_document(_doc("d1", "a.md", text)))
        before = store.vocabulary()

        original = list(stemming._STEP4)
        stemming._STEP4.remove("ion")
        analysis_fingerprint.cache_clear()
        self.addCleanup(analysis_fingerprint.cache_clear)
        self.addCleanup(lambda: stemming._STEP4.__setitem__(slice(None), original))
        # The corpus is untouched; only the analyser moved. A cache keyed on
        # corpus content alone hands back the terms of the old term space.
        self.assertNotEqual(before, store.vocabulary(),
                            "the vocabulary was served from a table built by a "
                            "different analyser")


class FilterAndMetricEdgeTest(unittest.TestCase):
    """Three findings from an independent review, each small and each silent."""

    def test_a_uri_prefix_does_not_match_more_than_it_was_asked_for(self):
        """`%` and `_` are LIKE wildcards and a URI is full of both, so
        "file:///home/my_docs" also matched "file:///home/myXdocs"."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        wanted = _doc("d1", "a.md", "Text in the intended directory.")
        wanted.uri = "file:///home/my_docs/a.md"
        other = _doc("d2", "b.md", "Text in a directory that merely looks alike.")
        other.uri = "file:///home/myXdocs/b.md"
        store.upsert_documents([wanted, other])
        for doc in (wanted, other):
            store.replace_chunks(doc.doc_id, chunk_document(doc))

        allowed = store.filter_chunk_ids({"uri_prefix": "file:///home/my_docs"})
        uris = {store.get_chunks([cid])[cid].chunk_id for cid in allowed}
        self.assertTrue(allowed)
        docs = {store.get_chunks([cid])[cid].doc_id for cid in allowed}
        self.assertEqual(docs, {"d1"},
                         "an underscore in the prefix acted as a wildcard")

    def test_precision_deduplicates_both_sides_of_the_ratio(self):
        """The numerator credited a relevant item once and the denominator
        counted duplicates, so a repeated chunk read as a precision loss."""
        from oodarag.eval.metrics import precision_at_k

        self.assertEqual(precision_at_k(["a", "a", "b"], {"a"}, 3), 0.5)
        self.assertEqual(precision_at_k(["a", "b"], {"a"}, 3), 0.5)
        self.assertEqual(precision_at_k([], {"a"}, 3), 0.0)

    def test_the_mmr_guard_against_an_uncomparable_score_actually_fires(self):
        """`if best_id is None: break` looked unreachable - `remaining` is
        non-empty - but a NaN relevance makes every comparison false. A guard
        that has never fired is untested, so this fires it."""
        from oodarag.retrieve.mmr import mmr_select

        scored = [("a", float("nan")), ("b", float("nan")), ("c", float("nan"))]
        selected = mmr_select(scored, similarity=lambda x, y: 0.0, k=3, lambda_=0.7)
        self.assertEqual(len(selected), 1,
                         "the loop kept going on scores it could not compare")


class ScanBudgetTest(unittest.TestCase):
    """The contamination scan's budget bounded its output, not its work.

    `all_documents()[:max_docs_scanned]` reads every document's full text out of
    SQLite and then throws most of it away. On the corpus that motivated the
    limit - session transcripts - the discarded part is the large part.
    """

    def test_the_limit_reaches_the_query(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        store.upsert_documents([_doc(f"d{i}", f"{i}.md", f"Document number {i}.")
                                for i in range(12)])
        self.assertEqual(len(store.all_documents(limit=5)), 5)
        self.assertEqual(len(store.all_documents()), 12)

    def test_the_scan_reads_no_more_documents_than_its_budget(self):
        """Counts rows actually returned by SQLite, not documents examined
        afterwards - the distinction the fix is about."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        docs = [_doc(f"d{i}", f"{i}.md", f"Document number {i} about budgets.")
                for i in range(12)]
        store.upsert_documents(docs)
        for doc in docs:
            store.replace_chunks(doc.doc_id, chunk_document(doc))

        statements: list[str] = []
        store.conn.set_trace_callback(statements.append)
        self.addCleanup(store.conn.set_trace_callback, None)
        detect(store, ["What is the boiling point of mercury?"], max_docs_scanned=4)

        # Observed from SQLite rather than asserted about the caller: the
        # statement it actually ran must carry the bound.
        selects = [sql for sql in statements if "FROM documents" in sql]
        self.assertTrue(selects, "the scan never read the documents table")
        for sql in selects:
            self.assertIn("LIMIT", sql.upper(),
                          f"the budget never reached SQLite: {sql!r}")


class SurfaceAnswerabilityTest(unittest.TestCase):
    """Stemming conflates, so "absent from the corpus" was not proof of absence.

    "mercury" and "mercurial" share the stem `mercuri`. A corpus mentioning the
    version control system reported the chemical element as known, and "What is
    the boiling point of mercury?" was answered with confidence 0.83 on that
    basis. The surface check asks the same question of the unstemmed vocabulary.
    """

    def _reranker(self, surface, **kw):
        # The small-corpus guard is switched off here on purpose: these tests
        # are about the arithmetic, and a three-word vocabulary would otherwise
        # (correctly) make the factor decline to have an opinion.
        kw.setdefault("min_vocabulary_for_answerability", 0)
        return HeuristicReranker(
            idf=lambda t: 2.0 if t in {"point", "mercuri"} else 8.0,
            vocabulary={"point", "mercuri", "boil"},
            surface_vocabulary=surface, **kw)

    def test_a_conflated_term_is_not_counted_as_present(self):
        """Derived, not copied. The query stems to boil/point/mercuri with idf
        8/2/2, so the total is 12. The corpus holds "boiling" and "point" by
        surface form but only "mercurial", never "mercury" - so 10 of 12, and
        the missing 2 is exactly the term stemming had hidden."""
        reranker = self._reranker({"mercurial", "point", "boiling"})
        factor = reranker._surface_factor("What is the boiling point of mercury?")
        self.assertAlmostEqual(factor, 10.0 / 12.0, places=4)
        # And the stemmed check, on its own, sees nothing wrong.
        self.assertEqual(reranker._answerability({"boil", "point", "mercuri"}), 1.0)

    def test_a_query_the_corpus_really_holds_is_not_penalised(self):
        reranker = self._reranker({"mercury", "point", "boiling"})
        self.assertAlmostEqual(
            reranker._surface_factor("What is the boiling point of mercury?"),
            1.0, places=4)

    def test_no_surface_vocabulary_means_no_opinion(self):
        """A reranker built without one must not silently gate everything."""
        reranker = self._reranker(None)
        self.assertEqual(reranker._surface_factor("boiling point of mercury"), 1.0)

    def test_the_flag_turns_it_off(self):
        reranker = self._reranker({"mercurial"}, use_surface_answerability=False)
        self.assertEqual(reranker._surface_factor("boiling point of mercury"), 1.0)

    def test_a_small_corpus_gets_no_opinion(self):
        """A corpus lacking most surface forms of the words it does discuss
        would be gated to silence. This is the guard that stopped it, and it is
        here because turning the factor on without it failed a suite test that
        answers from a five-document corpus."""
        reranker = self._reranker({"mercurial", "point", "boiling"},
                                  min_vocabulary_for_answerability=2000)
        self.assertEqual(
            reranker._surface_factor("What is the boiling point of mercury?"), 1.0)

    def test_the_factor_actually_reaches_the_gate(self):
        """A feature computed and never applied passes every test about the
        feature. Asserted end to end: the corpus mentions Mercurial the version
        control system and nothing else in the query, so the question must be
        refused - and with the flag off, it is not."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        # Every *stem* of the question is present - "mercurial" gives `mercuri`,
        # "boiled" gives `boil`, "point" gives `point` - so the stemmed check has
        # no objection. Not one *surface form* the question uses is here: no
        # "mercury", no "boiling".
        #
        # The two conflated terms are confined to a single document so their idf
        # is high, as it is in the corpus this came from. A corpus that repeats
        # them everywhere makes them worthless and the factor has nothing to
        # remove - which is how the first version of this test passed while
        # proving nothing.
        docs = [_doc(f"d{i}", f"{i}.md",
                     f"Chunking splits a document at a structural point, note {i}. "
                     f"Retrieval fuses two arms and reranks what they return.")
                for i in range(8)]
        docs.append(_doc("d8", "8.md",
                         "Mercurial is a distributed version control system. The "
                         "kettle boiled at a point during the demonstration."))
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()

        question = "What is the boiling point of mercury?"
        answers = {}
        for flag in (False, True):
            retriever = HybridRetriever(store, pipeline.embedder)
            retriever.reranker.use_surface_answerability = flag
            retriever.reranker.min_vocabulary_for_answerability = 0
            generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
            answers[flag] = generator.answer(question)
        self.assertFalse(answers[False].abstained,
                         "the premise is gone: the stemmed check now refuses this")
        self.assertTrue(answers[True].abstained,
                        f"the surface factor never reached the gate: "
                        f"{answers[True].text[:120]}")

    def test_it_gates_without_reordering(self):
        """The property that makes it safe: a function of the query and the
        corpus scales every candidate equally, so it cannot change the ranking.
        Asserted rather than assumed - the whole point of separating the gate
        from the ranking is lost if this is false."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        docs = [_doc(f"d{i}", f"{i}.md", text) for i, text in enumerate([
            "Reciprocal rank fusion combines a dense arm and a lexical arm.",
            "Budgets bound requests, bytes, depth and wall clock time.",
            "Citation markers are verified against the chunks retrieved.",
            "Mercurial and git are both distributed version control systems.",
        ])]
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()

        order = {}
        for flag in (False, True):
            retriever = HybridRetriever(store, pipeline.embedder)
            retriever.reranker.use_surface_answerability = flag
            results, _ = retriever.retrieve("how are dense and lexical arms combined")
            order[flag] = [r.chunk.chunk_id for r in results]
        self.assertEqual(order[False], order[True],
                         "the surface factor reordered the results")


class DerivedCacheTest(unittest.TestCase):
    """Two caches over the same corpus, invalidated differently.

    `idf_table` and `surface_vocabulary` are both functions of the chunk corpus
    and both validate against its signature, so either is safe on its own. The
    eager drop on write named only the first, which is the asymmetry that makes
    the next reader assume the derived caches are cleared when one of them is
    not - the shape L20 records three separate instances of.
    """

    def _store_with(self, text: str) -> SqliteStore:
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        doc = _doc("d1", "a.md", text)
        store.upsert_documents([doc])
        store.replace_chunks("d1", chunk_document(doc))
        return store

    def test_both_caches_follow_the_corpus(self):
        store = self._store_with("Reciprocal rank fusion combines two arms by rank.")
        self.assertIn("fusion", store.vocabulary())
        self.assertIn("fusion", store.surface_vocabulary())
        self.assertNotIn("quokka", store.surface_vocabulary())

        replacement = _doc("d1", "a.md", "Quokka telemetry calibration notes.")
        store.upsert_documents([replacement])
        store.replace_chunks("d1", chunk_document(replacement))

        self.assertIn("quokka", store.vocabulary())
        self.assertIn("quokka", store.surface_vocabulary(),
                      "the surface vocabulary did not follow the corpus")
        self.assertNotIn("fusion", store.surface_vocabulary())

    def test_the_eager_drop_names_every_derived_cache(self):
        """Asserted against the meta table rather than the constant, so adding a
        cache without adding it here fails."""
        store = self._store_with("Budgets bound requests, bytes and wall clock time.")
        store.vocabulary()
        store.surface_vocabulary()
        cached = {row[0] for row in store.conn.execute(
            "SELECT key FROM meta WHERE key IN ('idf_table', 'surface_vocabulary')")}
        self.assertEqual(cached, {"idf_table", "surface_vocabulary"})

        store._invalidate_derived()
        remaining = [row[0] for row in store.conn.execute(
            "SELECT key FROM meta WHERE key IN ('idf_table', 'surface_vocabulary')")]
        self.assertEqual(remaining, [],
                         f"a derived cache survived invalidation: {remaining}")

    def test_a_deleted_document_leaves_neither_cache_behind(self):
        store = self._store_with("Citation markers are verified against retrieved chunks.")
        store.vocabulary()
        store.surface_vocabulary()
        store.delete_document("d1")
        remaining = [row[0] for row in store.conn.execute(
            "SELECT key FROM meta WHERE key IN ('idf_table', 'surface_vocabulary')")]
        self.assertEqual(remaining, [])
