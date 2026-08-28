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

import json
import os
import sqlite3
import pathlib
import unittest

from oodarag.chunking import ChunkConfig, chunk_document
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


class GateCoveragePowerTest(unittest.TestCase):
    """The gate and the ranker read the same coverage number, so sharpening one
    silently recalibrates the other.

    Measured on the external corpus: raising `coverage_power` to 2.5 gives the
    best recall@8 in the sweep (0.9419 vs 0.9186) and *loses* a case
    (47/54 vs 48/54), because the abstention floor is a fixed number applied to
    a rescaled quantity. Holding the gate at 1.0 recovers it and one more.

    `gate_coverage_power` is a control, so these assert what the protocol
    demands of one: that its two settings differ, and that the difference lands
    on the gate and not on the ordering.
    """

    def _results(self, texts, query, **kwargs):
        from oodarag.models import Chunk, ScoredChunk
        from oodarag.retrieve.rerank import HeuristicReranker

        # One rare term, two that every document shares - the shape that makes
        # the power matter at all. IDF is supplied rather than measured so the
        # expectation is derived from the formula, not read off a corpus.
        #
        # Every key is its own Porter stem, and a lookup miss raises rather than
        # defaulting. The first draft used "everywhere", which stems to
        # "everywher", missed the table, and silently took the *rare* default -
        # so the fixture disagreed with the derived expectation for a reason
        # that had nothing to do with the code under test.
        idf = {"rare": 8.0, "common": 1.0, "plain": 1.0}

        def idf_of(term: str) -> float:
            if term not in idf:
                raise AssertionError(f"fixture has no IDF for {term!r}; "
                                     "the tokenizer produced a term the table "
                                     "does not key on")
            return idf[term]

        reranker = HeuristicReranker(
            idf=idf_of,
            vocabulary=set(idf),
            min_vocabulary_for_answerability=0,
            **kwargs,
        )
        results = [
            ScoredChunk(chunk=Chunk(chunk_id=f"c{i}", doc_id=f"d{i}", ordinal=0,
                                    text=text, context_header="",
                                    metadata={"authority": 1.0}),
                        score=0.0, components={})
            for i, text in enumerate(texts)
        ]
        return reranker.rerank(query, results)

    #: One chunk holds only the rare term, the other only the common ones.
    TEXTS = ("rare", "common plain")
    QUERY = "rare common plain"

    def test_sharpening_the_shared_power_moves_the_gate_as_well_as_the_order(self):
        """The behaviour the decoupling exists to prevent. `gate_coverage_power`
        is passed as None explicitly: sharing is no longer the default (it is
        1.0 since the corpus widened), so relying on the default here would test
        the shipped configuration rather than the one being argued against."""
        flat = self._results(self.TEXTS, self.QUERY,
                             coverage_power=1.0, gate_coverage_power=None)
        sharp = self._results(self.TEXTS, self.QUERY,
                              coverage_power=3.0, gate_coverage_power=None)
        by_id = lambda rs: {r.chunk.chunk_id: r.components["rerank_relevance"] for r in rs}
        self.assertNotEqual(by_id(flat)["c0"], by_id(sharp)["c0"],
                            "the shared power left the gate's number untouched, "
                            "so there is nothing here to decouple")

    def test_holding_the_gate_flat_leaves_the_gates_number_where_it_was(self):
        flat = self._results(self.TEXTS, self.QUERY, coverage_power=1.0)
        decoupled = self._results(self.TEXTS, self.QUERY,
                                  coverage_power=3.0, gate_coverage_power=1.0)
        for a, b in zip(sorted(flat, key=lambda r: r.chunk.chunk_id),
                        sorted(decoupled, key=lambda r: r.chunk.chunk_id)):
            self.assertAlmostEqual(a.components["rerank_relevance"],
                                   b.components["rerank_relevance"], places=9,
                                   msg="the gate followed the ranker anyway")

    def test_the_ranker_still_sharpens_while_the_gate_is_held(self):
        """A control that changes nothing is dead. This one must still move the
        ordering signal even with the gate pinned - otherwise it is just
        `coverage_power=1.0` under a longer name."""
        flat = self._results(self.TEXTS, self.QUERY, coverage_power=1.0)
        decoupled = self._results(self.TEXTS, self.QUERY,
                                  coverage_power=3.0, gate_coverage_power=1.0)
        by_id = lambda rs: {r.chunk.chunk_id: r.components["rerank_coverage"] for r in rs}
        self.assertNotEqual(by_id(flat)["c0"], by_id(decoupled)["c0"],
                            "the ranking coverage did not sharpen")
        # Derived from the formula: the rare-only chunk's share of total IDF
        # mass, at each power. 8^p / (8^p + 1 + 1).
        for power, results in ((1.0, flat), (3.0, decoupled)):
            expected = 8.0 ** power / (8.0 ** power + 2 * 1.0 ** power)
            self.assertAlmostEqual(by_id(results)["c0"], expected, places=9)

    def test_none_means_the_shared_behaviour_and_the_default_is_decoupled(self):
        """None still means "share", and the shipped default no longer does.

        The default moved to 1.0 with the ranker at 2.0 when the corpus widened
        to 153 documents: rank 2.0 is worth +2 cases with the gate held and
        nothing without it. Asserting the shipped pair here means a silent
        revert to the shared behaviour fails a test rather than a metric.
        """
        from oodarag.retrieve.rerank import HeuristicReranker

        reranker = HeuristicReranker()
        self.assertEqual(reranker.coverage_power, 2.0)
        self.assertEqual(reranker.gate_coverage_power, 1.0)
        shared = self._results(self.TEXTS, self.QUERY,
                               coverage_power=3.0, gate_coverage_power=None)
        explicit = self._results(self.TEXTS, self.QUERY,
                                 coverage_power=3.0, gate_coverage_power=3.0)
        for a, b in zip(sorted(shared, key=lambda r: r.chunk.chunk_id),
                        sorted(explicit, key=lambda r: r.chunk.chunk_id)):
            self.assertAlmostEqual(a.components["rerank_relevance"],
                                   b.components["rerank_relevance"], places=9)


class RedactionIsStructuralTest(unittest.TestCase):
    """Non-negotiable 5 says secrets are redacted at the connector boundary,
    before text can reach an index file.

    It was being kept by convention - each connector calling `redact_secrets`
    on the body it had just built - and a sweep of all seven found two holes:
    the YouTube connector called it nowhere, and *no* connector redacted the
    title. A title is not decoration; `chunking._context_header` puts it at the
    front of `Chunk.indexed_text`, so it is embedded and indexed.
    """

    #: Real credential shapes, one per pattern class the redactor carries.
    SECRET = "ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"

    def test_the_boundary_type_redacts_rather_than_each_connector_remembering(self):
        from oodarag.models import RawDocument

        raw = RawDocument(source_system="anything", external_id="1",
                          uri="u", title=f"leak {self.SECRET}",
                          text=f"body {self.SECRET}")
        self.assertNotIn(self.SECRET, raw.text)
        self.assertNotIn(self.SECRET, raw.title,
                         "a title carrying a token reaches indexed_text unredacted")

    def test_a_title_carrying_a_secret_does_not_reach_the_indexed_text(self):
        """The path that made titles matter, asserted end to end rather than
        by reading `_context_header`."""
        from oodarag.chunking import chunk_document
        from oodarag.models import Document, RawDocument

        raw = RawDocument(source_system="chat", external_id="s1", uri="file:///s1",
                          title=f"Session: here is my key {self.SECRET}",
                          text="user: how do budgets bound a crawl?\n\n"
                               "assistant: requests, bytes and wall clock.")
        document = Document.from_raw(raw, raw.text, dict(raw.metadata))
        chunks = chunk_document(document)
        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertNotIn(self.SECRET, chunk.indexed_text)

    def test_the_youtube_connector_redacts_a_curated_notes_file(self):
        """The connector that called `redact_secrets` nowhere. Driven through
        its own manifest and notes file, not a hand-built RawDocument."""
        import json
        from tempfile import TemporaryDirectory

        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.youtube import YouTubeConnector

        with TemporaryDirectory() as tmp:
            notes = pathlib.Path(tmp) / "notes.md"
            notes.write_text(
                "# Retrieval-augmented generation\n\n"
                f"Run it with the token {self.SECRET} in your environment.\n"
                "Chunking, embedding and retrieval are the three stages.\n",
                "utf-8")
            manifest = pathlib.Path(tmp) / "videos.json"
            manifest.write_text(json.dumps({"videos": [{
                "video_id": "T-D1OfcDW1M",
                "title": f"Live demo with {self.SECRET}",
                "notes_file": "notes.md",
            }]}), "utf-8")

            docs = YouTubeConnector(manifest=manifest, allow_network=False) \
                .run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1)
        self.assertNotIn(self.SECRET, docs[0].text,
                         "a curated notes file reached the index unredacted")
        self.assertNotIn(self.SECRET, docs[0].title)
        # Redaction must not have eaten the content it was protecting.
        self.assertIn("Chunking", docs[0].text)

    def test_every_connector_yields_redacted_documents(self):
        """The sweep itself, as a test.

        A new connector inherits the guarantee by constructing a RawDocument,
        which is the point of putting it there - but asserting it per connector
        is what would have caught the YouTube hole, and a hand-built document
        would not have.
        """
        import json
        from tempfile import TemporaryDirectory

        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.chat import ChatTranscriptConnector
        from oodarag.ingest.filesystem import FilesystemConnector

        leak = f"please use {self.SECRET} to authenticate against the service"
        with TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "guide.md").write_text(f"# Guide\n\n{leak}\n", "utf-8")
            (root / "session.jsonl").write_text("\n".join(json.dumps(e) for e in [
                {"type": "user", "timestamp": "2026-03-01T10:00:00Z", "cwd": "/w",
                 "message": {"role": "user", "content": leak}},
                {"type": "assistant", "timestamp": "2026-03-01T10:01:00Z",
                 "message": {"role": "assistant", "content": "Rotate that key."}},
            ]), "utf-8")

            runs = {
                "filesystem": FilesystemConnector(root=tmp, patterns=["**/*.md"]),
                "chat": ChatTranscriptConnector(root=tmp),
            }
            for name, connector in runs.items():
                with self.subTest(connector=name):
                    docs = connector.run(MemoryStateStore()).documents
                    self.assertTrue(docs, f"{name} produced nothing to check")
                    for doc in docs:
                        self.assertNotIn(self.SECRET, doc.text)
                        self.assertNotIn(self.SECRET, doc.title)

    def test_metadata_is_redacted_because_the_rule_is_about_the_index_file(self):
        """The third hole, and the one that shows why the rule is worded the way
        it is. The web connector built `metadata["description"]` from
        `page.text` - the copy it had *not* redacted - so a credential on a
        crawled page reached the index in full while the body beside it was
        clean. Nothing embeds a description; it is written to the index anyway.
        """
        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.web import WebConnector
        from tests.support.httpserver import Route, TestSite

        html = f"""<html><head><title>Setup</title></head><body><article>
        <h1>Setup</h1><p>Authenticate by exporting {self.SECRET} before running
        the tool, and the client picks it up from the environment on every
        later invocation without any further configuration being needed.</p>
        <p>The token is read once at startup and cached for the lifetime of the
        process, so rotating it requires a restart rather than a reload.</p>
        </article></body></html>"""

        with TestSite({"/": Route(body=html),
                       "/robots.txt": Route(body="User-agent: *\nAllow: /",
                                            content_type="text/plain")}) as site:
            docs = WebConnector([site.url("/")], max_pages=1,
                                max_depth=0).run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1, "the test page was not crawled")
        blob = json.dumps(docs[0].metadata)
        self.assertNotIn(self.SECRET, blob,
                         "a secret reached the index through metadata")
        self.assertNotIn(self.SECRET, docs[0].text)

    def test_redacting_metadata_does_not_mangle_legitimate_values(self):
        """A redactor applied to structured data is a false-positive risk: a
        commit sha, a content hash and a canonical URL all look secret-ish. If
        any of these were rewritten, provenance would silently break."""
        from oodarag.models import _redacted

        legitimate = {
            "head_sha": "3f8535df9b1a2c4e5d6f708192a3b4c5d6e7f809",
            "content_hash": "a5619f704bb76aaf",
            "canonical": "https://pypi.org/project/aiohttp/",
            # Underscores and dots, so a redactor that normalises before
            # matching is caught rewriting a value it should have left alone.
            "path": "src/oodarag/retrieve/hybrid_rerank.py",
            "crawl_seed": "https://example.test/docs/getting_started",
            "headings": ["Installation", "API tokens and authentication"],
            "published": "2026-01-02T00:00:00Z",
            "size": 4096, "authority": 1.0, "is_doc": True,
            "nested": {"license": "MIT", "topics": ["widgets", "python_3"]},
        }
        self.assertEqual(_redacted(legitimate), legitimate)

    def test_a_secret_inside_a_list_is_redacted(self):
        """`headings` is a list of strings lifted straight off the page, so the
        recursion has to descend into sequences and not only into dicts."""
        from oodarag.models import _redacted

        out = _redacted({"headings": ["Setup", f"Use {self.SECRET} here"],
                         "nested": {"lines": [f"export {self.SECRET}"]},
                         "tags": ("clean", f"token {self.SECRET}")})
        self.assertNotIn(self.SECRET, json.dumps(out))
        self.assertEqual(out["headings"][0], "Setup",
                         "redaction rewrote a heading that held no secret")
        # A tuple comes back as a list on purpose - see the note in `_redacted`.
        self.assertEqual(out["tags"][0], "clean")
        self.assertIsInstance(out["tags"], list)

    def test_a_credential_in_a_uri_is_redacted_too(self):
        """A clone URL with an embedded password is provenance and a secret at
        once. Redacting it keeps the URL usable as a citation and strips the
        part that must not be copied around."""
        from oodarag.models import RawDocument

        raw = RawDocument(source_system="git", external_id="1",
                          uri="https://svc:hunter2@example.com/repo.git",
                          title="repo", text="body")
        self.assertNotIn("hunter2", raw.uri)
        self.assertIn("example.com/repo.git", raw.uri)

    def test_redaction_is_idempotent_so_the_double_call_is_free(self):
        """Both the connector and the boundary redact. That is only safe if a
        second pass is a no-op - otherwise the placeholder from the first pass
        would be re-redacted into something else."""
        from oodarag.util.text import redact_secrets

        for secret in (self.SECRET,
                       "sk-ant-api03-" + "A" * 48,
                       "https://user:hunter2@example.com/repo.git",
                       "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEX"):
            with self.subTest(secret=secret[:24]):
                once = redact_secrets(secret)
                self.assertEqual(once, redact_secrets(once))


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

    def test_the_default_sharpens_ranking_while_the_gate_stays_flat(self):
        """The pair is the shipped configuration and only makes sense together.

        Ranking sharpens to 2.0; the abstention gate is pinned at 1.0 so a fixed
        floor is not silently recalibrated by it. Measured at 153 documents:
        rank 2.0 with the gate shared is 47/54, with the gate held it is 49/54.
        Pinning both numbers means a revert of either half fails here rather
        than quietly costing cases.
        """
        from oodarag.retrieve.rerank import HeuristicReranker

        reranker = HeuristicReranker()
        self.assertEqual(reranker.coverage_power, 2.0)
        self.assertEqual(reranker.gate_coverage_power, 1.0)
        self.assertNotEqual(reranker.coverage_power, reranker.gate_coverage_power,
                            "the two powers are equal, so the decoupling is inert")

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


class StaleChunkTest(unittest.TestCase):
    """A chunker change left the index serving chunks from the old chunker.

    `IndexPipeline` guards the embedding space - change the model or the
    dimension and every affected vector is recomputed - and had no equivalent
    one stage upstream. Chunking is not a function of the document, so an
    unchanged document meant an unchanged chunk: re-indexing the 153-page
    external corpus with a 5x smaller chunker rewrote **0 of 1,822** chunks
    and reported a clean run. Every measurement taken that way describes a
    chunker that is no longer in the tree (L63).
    """

    def _connector(self, texts: dict[str, str]):
        docs = [RawDocument(source_system="test", external_id=name, uri=f"mem://{name}",
                            title=name, text=text, metadata={})
                for name, text in texts.items()]

        class _MemoryConnector(Connector):
            key = "test:chunker"
            source_system = "test"

            def fetch(self, cursor):
                yield from docs

        return _MemoryConnector()

    def _corpus(self):
        # Long enough that the chunk sizes below actually bind: a corpus of
        # one-line documents chunks identically at every setting and the test
        # would pass against the bug.
        return {f"d{i}.md": f"# Doc {i}\n\n" + " ".join(
            f"Sentence {j} of document {i} says something specific." for j in range(120))
            for i in range(4)}

    def test_a_chunker_change_rebuilds_chunks_the_documents_did_not_change(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        texts = self._corpus()

        first = IndexPipeline(store, chunk_config=ChunkConfig()).run([self._connector(texts)])
        self.assertGreater(first.chunks_written, 0)
        before = store.chunk_count()

        smaller = ChunkConfig(target_tokens=64, hard_max_tokens=128, overlap_tokens=12)
        report = IndexPipeline(store, chunk_config=smaller).run([self._connector(texts)])

        # Ordered so the first failure is the behaviour, not a missing field:
        # a test that reports `no attribute 'rechunked'` when the guard is
        # removed is testing the report object, not the index.
        self.assertGreater(store.chunk_count(), before,
                           "a 5x smaller chunker left the stored chunks alone")
        self.assertTrue(report.rechunked,
                        "the chunks were rebuilt and the run did not say so")
        # Vectors are downstream of chunks: leaving the new chunks unembedded
        # would trade a stale index for an empty one.
        self.assertEqual(store.chunk_count(),
                         len(store.get_chunks([c.chunk_id for c in store.all_chunks()])))
        self.assertGreater(report.vectors_written, 0)

    def test_an_unchanged_chunker_still_writes_nothing(self):
        """Idempotence is the property this guard is most likely to break: a
        fingerprint that varies per run rebuilds the corpus on every index."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        texts = self._corpus()
        IndexPipeline(store, chunk_config=ChunkConfig()).run([self._connector(texts)])
        report = IndexPipeline(store, chunk_config=ChunkConfig()).run([self._connector(texts)])
        self.assertFalse(report.rechunked)
        self.assertEqual(report.chunks_written, 0)


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


class CitationMarkerTest(unittest.TestCase):
    """A citation marker and an array subscript are the same characters.

    `\\[(\\d{1,2})\\]` matched both, on a corpus that is half source code:

    * `sys.argv[1]` counted as a citation of chunk 1, so a sentence that merely
      quoted code read as grounded;
    * `chunks[7]`, with no seventh citation, was treated as a marker pointing at
      nothing and deleted from the quoted code - `values[12] = compute(x)`
      became `values = compute(x)`, an answer presenting altered code as a
      quotation from the document it cites;
    * the two-digit cap meant `[999999999999]` was neither recognised nor
      removed, so a marker pointing at nothing shipped as evidence - the exact
      thing the cleaning step exists to prevent.
    """

    def _citations(self, n=2):
        from oodarag.models import Citation

        return [Citation(marker=i, chunk_id=f"c{i}", doc_id=f"d{i}", title="t",
                         uri=f"mem://{i}", quote="q", score=1.0)
                for i in range(1, n + 1)]

    def test_a_subscript_is_not_a_citation(self):
        from oodarag.generate.contract import verify

        check = verify("Read the flag with sys.argv[1] to start.", self._citations())
        self.assertEqual(check.citations, [],
                         "quoted code was counted as a citation")
        self.assertFalse(check.grounded)

    def test_an_out_of_range_subscript_is_not_deleted_from_the_text(self):
        from oodarag.generate.contract import verify

        text = "The loop reads chunks[7] for each result [1]."
        check = verify(text, self._citations())
        self.assertIn("chunks[7]", check.text,
                      "the verifier altered code it was quoting")
        self.assertEqual(check.invalid_markers, [])

    def test_fenced_code_is_never_rewritten(self):
        """The lookbehind cannot save `x = [12]` - a list literal follows a
        space, exactly like a marker - so fences are skipped outright."""
        from oodarag.generate.contract import verify

        text = "```\nvalues[12] = compute(x)\nx = [12]\n```\nThat is the assignment [1]."
        check = verify(text, self._citations())
        self.assertIn("values[12] = compute(x)", check.text)
        self.assertIn("x = [12]", check.text)
        self.assertEqual(check.invalid_markers, [])

    def test_a_marker_too_long_to_match_is_detected_and_removed(self):
        from oodarag.generate.contract import verify

        check = verify("Budgets bound the crawl [999999999999] and so on [1].",
                       self._citations())
        self.assertEqual(check.invalid_markers, [999999999999])
        self.assertNotIn("999999999999", check.text,
                         "a marker pointing at nothing was shipped as evidence")

    def test_a_genuine_invalid_marker_is_still_removed(self):
        """The fix must not have been bought by no longer cleaning anything."""
        from oodarag.generate.contract import verify

        check = verify("See the spec [3] for the grammar [1].", self._citations())
        self.assertEqual(check.invalid_markers, [3])
        self.assertNotIn("[3]", check.text)
        self.assertIn("[1]", check.text)

    def test_a_marker_at_the_start_of_the_text_still_counts(self):
        """The lookbehind must not require a preceding character to exist."""
        from oodarag.generate.contract import verify

        check = verify("[1] Budgets bound the crawl.", self._citations())
        self.assertEqual([c.marker for c in check.citations], [1])


class SecretRedactionTest(unittest.TestCase):
    """Secrets are redacted at the connector boundary - non-negotiable 5.

    Redaction runs on every ingested document (`pipeline.py`, and each
    connector), so it has two failure directions and they are not symmetric:
    a missed credential is written into a file that gets copied around, and an
    over-eager rule rewrites the corpus itself. Both are measured here.
    """

    def test_the_credential_classes_that_were_leaking(self):
        """Five classes found by attacking the redactor, each demonstrated
        leaking before the pattern that now catches it."""
        for name, text, marker in [
            ("basic auth", "Authorization: Basic YWRtaW46aHVudGVyMg==", "redacted"),
            ("url password", "https://user:s3cr3tpass@github.com/x.git", "url-password"),
            ("db url", "postgres://admin:hunter2hunter@db:5432/app", "url-password"),
            ("aws secret", "aws_secret_access_key = wJalrXUtnFEMI/K7MDENGbPxRfi", "aws-secret"),
            ("aws session", "AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjELb1234567890", "aws-secret"),
            ("jwt", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abcdefgh", "jwt"),
        ]:
            with self.subTest(name=name):
                out = redact_secrets(text)
                self.assertIn(marker, out, f"{name} leaked: {out}")

    def test_a_url_keeps_its_user_and_loses_only_the_password(self):
        """The user is provenance - which account fetched this - and the
        password is the secret. Redacting the whole authority would make the
        citation less useful for no security gain."""
        out = redact_secrets("https://alice:s3cr3tpass@github.com/org/repo.git")
        self.assertIn("alice", out)
        self.assertNotIn("s3cr3tpass", out)
        self.assertIn("github.com/org/repo.git", out)

    def test_an_ordinary_url_is_untouched(self):
        for url in ("https://pypi.org/project/blinker/",
                    "http://localhost:8080/health",
                    "file:///home/user/claude/src/oodarag/util/text.py"):
            with self.subTest(url=url):
                self.assertEqual(redact_secrets(f"See {url} for details."),
                                 f"See {url} for details.")

    def test_source_code_is_not_rewritten(self):
        """The reason two attempted improvements were reverted. Allowing the
        keyword a suffix catches `aws_secret_access_key = ...` and also
        `unit_tokens = estimate_tokens(...)`; measured, that rewrote 14 of 51
        source files in this repository against a baseline of 3."""
        for line in ("unit_tokens = estimate_tokens(unit_text)",
                     "max_tokens=self.max_tokens,",
                     "def _idf(self, token: str) -> float:",
                     "context = format_context(citations, max_tokens=cfg.tokens)"):
            with self.subTest(line=line):
                self.assertEqual(redact_secrets(line), line,
                                 "redaction rewrote source code")

    def test_a_short_secret_is_knowingly_not_caught(self):
        """Pinning an accepted cost rather than a success.

        `password: hunter2` is seven characters and survives the eight-character
        floor. Lowering the floor catches it and also catches `token: str)`, so
        the floor stays and this test exists to make a future change confront
        the trade rather than discover it. If this ever fails because the floor
        moved, re-run the false-positive measurement in L38 first.
        """
        self.assertEqual(redact_secrets("password: hunter2"), "password: hunter2")

    def test_a_specific_marker_is_not_overwritten_by_the_generic_rule(self):
        out = redact_secrets("GITHUB_TOKEN=ghp_abcdefghijklmnop0123456789")
        self.assertIn("github-token", out,
                      "the generic rule overwrote a more specific marker")


class DegradeWithoutShrinkingTest(unittest.TestCase):
    """Non-negotiable 4: a failure reduces what the pipeline can do and says so.
    It never crashes, and it never silently shrinks the corpus.

    The existing coverage takes a connector that yields nothing and then raises.
    The realistic and more dangerous shape is a *partial* failure - a listing
    that is truncated part way through, a token that expires mid-page, a mount
    that goes away - because the documents it did not reach look exactly like
    documents that were deleted upstream.
    """

    def _raw(self, i):
        return RawDocument(source_system="s", external_id=f"d{i}", uri=f"mem://d{i}",
                           title=f"d{i}", text=f"Document {i} about budgets and crawling.",
                           metadata={})

    def _full(self, n=8):
        outer = self

        class _Full(Connector):
            key = "s"
            source_system = "s"

            def fetch(self, cursor):
                for i in range(n):
                    yield outer._raw(i)

        return _Full()

    def _partial(self, yielded=3):
        outer = self

        class _Partial(Connector):
            key = "s"
            source_system = "s"

            def fetch(self, cursor):
                for i in range(yielded):
                    yield outer._raw(i)
                raise RuntimeError("source went away mid-iteration")

        return _Partial()

    def _silently_empty(self):
        class _Empty(Connector):
            key = "s"
            source_system = "s"

            def fetch(self, cursor):
                return
                yield  # pragma: no cover

        return _Empty()

    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.addCleanup(self.store.close)
        self.pipeline = IndexPipeline(self.store)
        self.pipeline.run([self._full()])
        self.assertEqual(self.store.stats()["documents"], 8)

    def test_a_partial_failure_reports_no_removals(self):
        """The five documents it never reached are not evidence of deletion."""
        report = self.pipeline.run([self._partial()])
        delta = report.deltas[0]
        self.assertEqual(delta.failed, 1)
        self.assertEqual(delta.removed, [],
                         "documents an interrupted listing never reached were "
                         "reported as removed")
        self.assertEqual(self.store.stats()["documents"], 8)

    def test_a_partial_failure_prunes_nothing(self):
        report = self.pipeline.run([self._partial()])
        pruned = self.pipeline.prune(report.deltas)
        self.assertEqual(pruned.deleted, 0)
        self.assertEqual(self.store.stats()["documents"], 8)

    def test_a_partial_failure_does_not_raise_and_says_what_happened(self):
        """Degrade, don't die - and *say so*. A run that swallows the failure
        silently is not degrading, it is hiding."""
        report = self.pipeline.run([self._partial()])
        self.assertFalse(report.ok, "a failed source left the run reporting ok")
        self.assertTrue(report.errors, "the failure was not reported anywhere")
        self.assertIn("mid-iteration", " ".join(report.errors),
                      f"the reported error does not name the cause: {report.errors}")

    def test_a_source_that_succeeds_but_returns_nothing_is_caught_by_the_guard(self):
        """The ambiguous case: no error, and everything gone. Indistinguishable
        from a real bulk deletion, so the fraction guard is the only thing
        standing between an expired token and an empty index."""
        report = self.pipeline.run([self._silently_empty()])
        self.assertEqual(report.deltas[0].failed, 0)
        self.assertEqual(len(report.deltas[0].removed), 8)

        pruned = self.pipeline.prune(report.deltas)
        self.assertEqual(pruned.deleted, 0)
        self.assertEqual(pruned.skipped, 8)
        self.assertTrue(pruned.refused)
        self.assertIn("100%", pruned.refused[0])
        self.assertEqual(self.store.stats()["documents"], 8,
                         "an empty listing emptied the index")


class ZeroDependencyTest(unittest.TestCase):
    """Non-negotiable 1: the core runs on a bare Python 3.11.

    CI enforces this by having no install step, and its comment calls a green
    build "evidence of that claim". It is evidence for the paths the suite
    exercises. A module no test imports could carry a top-level `import numpy`
    and CI would stay green - the same gap as a test named for more than it
    checks. These two close it by walking the package rather than sampling it.
    """

    def _modules(self) -> list[str]:
        import pathlib

        root = pathlib.Path(__file__).resolve().parent.parent / "src"
        names = []
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(root).with_suffix("")
            parts = [p for p in rel.parts if p != "__init__"]
            if parts:
                names.append(".".join(parts))
        return sorted(set(names))

    def test_every_module_imports_on_the_standard_library_alone(self):
        import importlib

        modules = self._modules()
        self.assertGreater(len(modules), 30, "the module walk found almost nothing")
        failures = []
        for name in modules:
            try:
                importlib.import_module(name)
            except Exception as e:  # noqa: BLE001 - the failure is the result
                failures.append(f"{name}: {type(e).__name__}: {e}")
        self.assertEqual(failures, [], "modules failed to import: " + "; ".join(failures))

    def test_no_third_party_import_at_module_scope(self):
        """Import-time is what matters: an optional accelerator imported inside
        a function degrades to the pure-Python path, and one imported at the top
        of a module makes the package unusable without it."""
        import ast
        import pathlib
        import sys

        allowed = set(sys.stdlib_module_names) | {"oodarag"}
        offenders = []
        root = pathlib.Path(__file__).resolve().parent.parent / "src"
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if node.col_offset != 0:
                    continue  # inside a function or a try block: deferred, fine
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""])
                for name in names:
                    root_pkg = name.split(".")[0]
                    if root_pkg and root_pkg not in allowed:
                        offenders.append(
                            f"{path.relative_to(root)}:{node.lineno} imports {root_pkg}")
        self.assertEqual(offenders, [],
                         "third-party imports at module scope: " + "; ".join(offenders))


from oodarag.chunking import _balance_fences  # noqa: E402


class ChunkFenceTest(unittest.TestCase):
    """A code fence split across chunks left both halves malformed.

    Packing works in prose or code units and knows nothing about fences, so a
    long fenced block lands in two chunks: the first ends inside the fence, the
    second opens with the orphaned tail and a closing marker that opens nothing.
    Measured on the 91-document external corpus, 20 of 1,148 chunks carried an
    odd number of markers.

    It reaches the user because the extractive generator quotes chunk text
    verbatim: an unclosed fence renders everything after it as code, and a stray
    closing one renders the prose before it as code.
    """

    FENCE = "`" * 3

    def _markers(self, text: str) -> int:
        return sum(1 for line in text.splitlines()
                   if line.strip().startswith(self.FENCE))

    def test_a_chunk_left_open_is_closed(self):
        out = _balance_fences(f"Here is an example:\n{self.FENCE}\nprint(1)")
        self.assertEqual(self._markers(out) % 2, 0)
        self.assertTrue(out.startswith("Here is an example:"))
        self.assertTrue(out.rstrip().endswith(self.FENCE))

    def test_a_chunk_starting_inside_a_fence_is_opened_not_closed(self):
        """Which end is missing decides where the marker goes, and asserting
        only "the count is even" cannot tell the two apart: appending to a chunk
        that opens with a dangling marker balances the count *and* wraps the
        prose in a code block. The prose has to end up outside."""
        text = f"{self.FENCE}\nAnd then the prose continues."
        out = _balance_fences(text)
        self.assertEqual(self._markers(out) % 2, 0)
        self.assertFalse(out.rstrip().endswith(self.FENCE),
                         "the marker was appended, putting the prose inside the fence")
        self.assertTrue(out.rstrip().endswith("And then the prose continues."))

    def test_balanced_text_is_returned_unchanged(self):
        """No boundary moves and no text is added when nothing is broken."""

        for text in ("plain prose with no fence at all",
                     f"before\n{self.FENCE}\ncode()\n{self.FENCE}\nafter",
                     ""):
            with self.subTest(text=text[:24]):
                self.assertEqual(_balance_fences(text), text)

    def test_no_chunk_of_the_real_corpus_has_an_unbalanced_fence(self):
        """Measured over the corpus rather than a fixture: this is the property
        the fixture cases are standing in for, and it is what regressed."""
        import pathlib

        from oodarag.chunking import chunk_document
        from oodarag.models import Document

        root = pathlib.Path(__file__).resolve().parent.parent / "corpus/external/pypi"
        files = sorted(root.glob("*.md"))
        if not files:
            self.skipTest("external corpus not present")
        offenders, total = [], 0
        for path in files:
            doc = Document(doc_id=path.stem, source_system="fs", external_id=path.stem,
                           uri=f"file://{path}", title=path.stem,
                           text=path.read_text(encoding="utf-8"), content_hash="h",
                           metadata={}, created_at=0.0, updated_at=0.0)
            for chunk in chunk_document(doc):
                total += 1
                if self._markers(chunk.text) % 2:
                    offenders.append(f"{path.stem}#{chunk.ordinal}")
        self.assertGreater(total, 500, "the corpus walk found almost nothing")
        self.assertEqual(offenders, [],
                         f"{len(offenders)} of {total} chunks have an unbalanced "
                         f"fence: {offenders[:5]}")


class GoldenDiscriminationTest(unittest.TestCase):
    """The harness checked whether the corpus leaks the answer, and not whether
    the expectation picks anything out.

    `expect_sources` entries are substrings matched against a document's uri and
    title. Every uri in a filesystem corpus shares a directory, so an
    expectation of `"pypi"` matches all 91 documents and the case passes with
    recall 1.0 whatever retrieval returns - a test that cannot fail, inside the
    instrument every other measurement is taken with.

    The opposite is as bad and quieter: an expectation matching nothing makes a
    case that can never pass, which reads as a retrieval failure for ever.
    """

    def _store(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        docs = [_doc(f"d{i}", f"pkg{i}.md", f"Package {i} does something distinct.")
                for i in range(10)]
        for i, d in enumerate(docs):
            d.uri = f"file:///corpus/external/pypi/pkg{i}.md"
            d.title = f"pkg{i}"
        store.upsert_documents(docs)
        return store

    def test_an_expectation_matching_the_whole_corpus_is_reported(self):
        from oodarag.eval.discrimination import check

        report = check(self._store(), [Golden(question="q?", expect_sources=["pypi"])])
        self.assertFalse(report.clean)
        self.assertEqual(report.findings[0].matched, 10)
        self.assertIn("without discriminating", report.findings[0].describe())

    def test_an_expectation_matching_nothing_is_reported(self):
        """Different failure, same cause: nobody checked the expectation
        against the corpus."""
        from oodarag.eval.discrimination import check

        report = check(self._store(), [Golden(question="q?", expect_sources=["nonesuch"])])
        self.assertFalse(report.clean)
        self.assertEqual(report.findings[0].matched, 0)
        self.assertIn("never pass", report.findings[0].describe())

    def test_a_specific_expectation_is_clean(self):
        from oodarag.eval.discrimination import check

        report = check(self._store(), [Golden(question="q?", expect_sources=["pkg3"])])
        self.assertTrue(report.clean, report.summary())

    def test_an_abstention_golden_has_nothing_to_check(self):
        from oodarag.eval.discrimination import check

        report = check(self._store(), [Golden(question="q?", expect_abstain=True)])
        self.assertTrue(report.clean)

    def test_an_answer_expectation_the_corpus_repeats_is_reported(self):
        """The answer is assembled from the corpus, so a term the corpus repeats
        everywhere turns up in almost any answer. `"sha"` appeared in 38% of this
        repository's documents - satisfied by "shared" and "shape" as readily as
        by a commit sha - and the golden that used it now says "commit sha", at
        6%."""
        from oodarag.eval.discrimination import check

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        # "sha" is in every document as a substring of "shared" and "shape";
        # "commit sha" is in one. That is the whole distinction the check makes.
        docs = [_doc(f"d{i}", f"pkg{i}.md",
                     f"Package {i} mentions the shared shape of a value.")
                for i in range(10)]
        docs[0].text += " The cursor stores a commit sha to skip the walk."
        store.upsert_documents(docs)

        broad = check(store, [Golden(question="q?", expect_answer_contains=["sha"])])
        self.assertFalse(broad.clean)
        self.assertEqual(broad.findings[0].kind, "answer")
        self.assertIn("answer expectation", broad.findings[0].describe())

        narrow = check(store, [Golden(question="q?",
                                      expect_answer_contains=["commit sha"])])
        self.assertTrue(narrow.clean, narrow.summary())

    def test_both_expectation_kinds_are_labelled(self):
        """A report naming only the string leaves the reader guessing which
        field to fix."""
        from oodarag.eval.discrimination import check

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        docs = [_doc(f"d{i}", f"pkg{i}.md", "shared text in every document")
                for i in range(10)]
        for i, d in enumerate(docs):
            d.uri = f"file:///corpus/pkg{i}.md"
        store.upsert_documents(docs)
        report = check(store, [Golden(question="q?", expect_sources=["corpus"],
                                      expect_answer_contains=["shared"])])
        self.assertEqual({f.kind for f in report.findings}, {"source", "answer"})

    def test_the_real_primary_golden_set_discriminates(self):
        """The set that caught `"sha"`. Runs against the repository itself."""
        import pathlib

        from oodarag.eval.discrimination import check
        from oodarag.eval.harness import load_goldens
        from oodarag.ingest.filesystem import FilesystemConnector
        from oodarag.pipeline import IndexPipeline

        root = pathlib.Path(__file__).resolve().parent.parent
        goldens = root / "evals/goldens.jsonl"
        if not goldens.exists():
            self.skipTest("primary golden set not present")
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        IndexPipeline(store).run([FilesystemConnector(
            str(root), patterns=("src/**/*.py", "tests/**/*.py", "docs/**/*.md",
                                 "internal/**/*.md", "*.md"), key="fs:disc2")])
        report = check(store, load_goldens(str(goldens)))
        self.assertTrue(report.clean, report.summary())

    def test_the_real_external_golden_set_discriminates(self):
        """Measured against the corpus in the repository, because that is the
        set the regression gate is read from. If a future golden is written too
        broadly, this is where it surfaces."""
        import pathlib

        from oodarag.eval.discrimination import check
        from oodarag.eval.harness import load_goldens
        from oodarag.ingest.filesystem import FilesystemConnector
        from oodarag.pipeline import IndexPipeline

        root = pathlib.Path(__file__).resolve().parent.parent
        corpus = root / "corpus/external/pypi"
        goldens = root / "evals/goldens-external.jsonl"
        if not corpus.exists() or not goldens.exists():
            self.skipTest("external corpus or golden set not present")

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        IndexPipeline(store).run(
            [FilesystemConnector(str(corpus), patterns=("**/*.md",), key="fs:disc")])
        report = check(store, load_goldens(str(goldens)))
        self.assertTrue(report.clean, report.summary())


class PipelineDeterminismTest(unittest.TestCase):
    """ADR 0001 calls this pipeline deterministic. Measured end to end, across
    processes with different hash seeds, two things are true and they are easy
    to confuse:

    * the **ranking** is identical - same chunks, same order, and the coverage,
      relevance and abstention decisions match to the last digit;
    * the **scores** differ by around 1e-8, and they differ between two runs with
      the *same* seed as well. It is not hash order, it is `time.time()` in the
      recency factor: a document's age is recomputed against a clock that moved
      between the runs.

    The first version of this investigation reported "retrieval is not
    deterministic across processes" on the strength of four different digests,
    which was true of the digest and wrong about the cause. Running the same
    seed twice is what separated them.
    """

    FROZEN = 1_700_000_000.0

    def _index(self):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        docs = [_doc(f"d{i}", f"{i}.md", text) for i, text in enumerate([
            "Reciprocal rank fusion combines a dense arm and a lexical arm by rank.",
            "Budgets bound requests, bytes, depth and wall clock time for a crawl.",
            "Citation markers are verified against the chunks actually retrieved.",
            "Porter stemming is applied by the FTS5 index and by the reranker.",
            "Contextual headers are embedded with each chunk of a document.",
        ])]
        # The recency factor only applies to a chunk that carries an age; with
        # none it falls back to "neither fresh nor stale" and the clock cannot
        # matter. Without this the test would pass for the wrong reason.
        for doc in docs:
            doc.updated_at = self.FROZEN - 86_400 * 30
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()
        return store, pipeline

    def _retrieve(self, store, pipeline, clock=None, recency_weight=None):
        retriever = HybridRetriever(store, pipeline.embedder)
        if clock is not None:
            retriever.reranker.clock = clock
        if recency_weight is not None:
            retriever.reranker.recency_weight = recency_weight
        results, _ = retriever.retrieve("how are dense and lexical arms combined")
        return ([r.chunk.chunk_id for r in results],
                [round(r.score, 15) for r in results])

    def test_a_frozen_clock_makes_scores_bit_identical(self):
        store, pipeline = self._index()
        first = self._retrieve(store, pipeline, clock=lambda: self.FROZEN)
        second = self._retrieve(store, pipeline, clock=lambda: self.FROZEN)
        self.assertEqual(first, second)

    def test_the_clock_is_what_moves_the_score_when_recency_is_on(self):
        """Not hash order. With recency enabled, the same query scores
        differently a hundred days later - which was the whole finding: four
        differing digests across four hash seeds turned out to be a wall-clock
        term, not hash order (L29).

        `recency_weight` is passed explicitly because it is now 0.0 by default,
        measured (L61). Relying on the default here would silently stop testing
        the thing this was written for.
        """
        store, pipeline = self._index()
        now = self._retrieve(store, pipeline, clock=lambda: self.FROZEN,
                             recency_weight=0.08)
        later = self._retrieve(store, pipeline, clock=lambda: self.FROZEN + 86_400 * 120,
                               recency_weight=0.08)
        self.assertEqual(now[0], later[0], "the clock changed the ranking, not just the score")
        self.assertNotEqual(now[1], later[1], "the clock had no effect at all")

    def test_the_shipped_default_does_not_depend_on_the_clock_at_all(self):
        """A stronger property than the project had, and worth pinning.

        With recency off, no scoring term reads the wall clock, so the same
        index and query give bit-identical scores whenever they are run. That
        makes a stored result comparable to one produced months later - the
        thing an injectable clock was introduced to approximate.
        """
        store, pipeline = self._index()
        now = self._retrieve(store, pipeline, clock=lambda: self.FROZEN)
        much_later = self._retrieve(store, pipeline,
                                    clock=lambda: self.FROZEN + 86_400 * 3650)
        self.assertEqual(now, much_later,
                         "a decade of wall clock changed the result, so something "
                         "still reads the clock")

    def test_the_ranking_is_identical_across_processes(self):
        """Run in subprocesses with different hash seeds, because that is the
        only way to exercise Python's per-process string hashing."""
        import json
        import pathlib
        import subprocess
        import sys

        script = (
            "import sys, json; sys.path.insert(0, 'src');"
            "from oodarag.chunking import chunk_document;"
            "from oodarag.models import Document;"
            "from oodarag.pipeline import IndexPipeline;"
            "from oodarag.retrieve.hybrid import HybridRetriever;"
            "from oodarag.store.sqlite_store import SqliteStore;"
            "s = SqliteStore(':memory:'); p = IndexPipeline(s);"
            "ts = ['Reciprocal rank fusion combines a dense arm and a lexical arm.',"
            " 'Budgets bound requests, bytes, depth and wall clock time.',"
            " 'Citation markers are verified against retrieved chunks.',"
            " 'Porter stemming is applied by the index and by the reranker.'];"
            "ds = [Document(doc_id=f'd{i}', source_system='t', external_id=f'd{i}',"
            " uri=f'mem://{i}', title=f'{i}.md', text=t, content_hash=f'h{i}',"
            " metadata={}, created_at=0.0, updated_at=0.0) for i, t in enumerate(ts)];"
            "s.upsert_documents(ds); p.embedder.fit([d.text for d in ds]);"
            "[s.replace_chunks(d.doc_id, chunk_document(d)) for d in ds];"
            "p.embed_missing();"
            "r = HybridRetriever(s, p.embedder); r.reranker.clock = lambda: 1700000000.0;"
            "res, _ = r.retrieve('how are dense and lexical arms combined');"
            "print(json.dumps([[c.chunk.chunk_id for c in res],"
            " [round(c.score, 12) for c in res]]))"
        )
        cwd = str(pathlib.Path(__file__).resolve().parent.parent)
        outputs = set()
        for seed in ("0", "1", "42", "999"):
            env = {**os.environ, "PYTHONHASHSEED": seed}
            done = subprocess.run([sys.executable, "-c", script], capture_output=True,
                                  text=True, cwd=cwd, env=env)
            self.assertEqual(done.returncode, 0, done.stderr[-400:])
            outputs.add(done.stdout.strip().splitlines()[-1])
        self.assertEqual(len(outputs), 1,
                         f"retrieval differed across hash seeds: {outputs}")
        self.assertTrue(json.loads(outputs.pop())[0], "the subprocess retrieved nothing")


class RecencyTest(unittest.TestCase):
    """The recency factor is inert on both eval corpora and tested only here.

    Both are written in one pass, so their documents share a timestamp - 0.00
    days of spread on the external corpus, 0.91 on the primary one - and a
    factor identical across every candidate cannot reorder anything. Measured,
    switching it off leaves both sets at 48/54 and 18/20 with every metric
    unchanged. The gates cannot see this weight, so these tests are the whole of
    its coverage.
    """

    NOW = 1_700_000_000.0

    def _ranked(self, ages_days, weight=0.08):
        """Identical documents differing only in age; returns their order."""
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        text = "Reciprocal rank fusion combines a dense arm and a lexical arm by rank."
        docs = []
        for i, age in enumerate(ages_days):
            doc = _doc(f"d{i}", f"{i}.md", text)
            doc.updated_at = self.NOW - age * 86_400
            docs.append(doc)
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()

        retriever = HybridRetriever(store, pipeline.embedder)
        retriever.reranker.clock = lambda: self.NOW
        retriever.reranker.recency_weight = weight
        results, _ = retriever.retrieve("how are dense and lexical arms combined")
        return [r.chunk.doc_id for r in results]

    def test_a_fresher_document_outranks_an_identical_stale_one(self):
        """The feature's entire purpose, asserted on documents that differ in
        nothing else - same text, same terms, same authority."""
        order = self._ranked([2000, 1000, 1])
        self.assertEqual(order[0], "d2", f"the newest document did not win: {order}")
        self.assertEqual(order[-1], "d0", f"the oldest document did not lose: {order}")

    def test_with_the_weight_at_zero_age_stops_mattering(self):
        """The other half: the ordering above must come from the weight, not
        from insertion order or some other tiebreak."""
        aged = self._ranked([2000, 1000, 1], weight=0.08)
        flat = self._ranked([2000, 1000, 1], weight=0.0)
        self.assertNotEqual(aged, flat,
                            "the ranking was the same with recency switched off, "
                            "so the test above proves nothing about recency")

    def test_a_document_with_no_date_is_neither_fresh_nor_stale(self):
        """Unknown age must not read as infinitely old, which would bury every
        document from a source that carries no timestamps."""
        from oodarag.models import ScoredChunk
        from oodarag.retrieve.rerank import HeuristicReranker

        reranker = HeuristicReranker(idf=lambda t: 1.0, vocabulary=set())
        reranker.clock = lambda: self.NOW
        chunk = Chunk(chunk_id="c", doc_id="d", ordinal=0, text="text",
                      context_header="", metadata={})
        scored = ScoredChunk(chunk=chunk, score=1.0, components={})
        reranker.rerank("text", [scored])
        self.assertAlmostEqual(scored.components["rerank_recency"], 0.5, places=6)


class AuthorityTest(unittest.TestCase):
    """Authority is the other weight no gate can see.

    Both eval corpora are a single filesystem source at authority 1.0, so the
    factor is constant across every candidate and cannot reorder anything -
    measured by zeroing each reranker weight in turn: coverage, phrase and
    position all move the metrics on both corpora, authority and recency move
    neither. These tests are its whole coverage.
    """

    def _ranked(self, authorities, weight=0.12):
        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)
        text = "Reciprocal rank fusion combines a dense arm and a lexical arm by rank."
        docs = [_doc(f"d{i}", f"{i}.md", text) for i in range(len(authorities))]
        for doc, authority in zip(docs, authorities):
            doc.metadata = {**doc.metadata, "authority": authority}
        store.upsert_documents(docs)
        pipeline.embedder.fit([d.text for d in docs])
        for d in docs:
            store.replace_chunks(d.doc_id, chunk_document(d))
        pipeline.embed_missing()

        retriever = HybridRetriever(store, pipeline.embedder)
        retriever.reranker.clock = lambda: 1_700_000_000.0
        retriever.reranker.authority_weight = weight
        results, _ = retriever.retrieve("how are dense and lexical arms combined")
        return [r.chunk.doc_id for r in results]

    def test_a_trusted_source_outranks_an_identical_untrusted_one(self):
        order = self._ranked([0.2, 0.6, 1.4])
        self.assertEqual(order[0], "d2", f"the trusted source did not win: {order}")
        self.assertEqual(order[-1], "d0", f"the least trusted did not lose: {order}")

    def test_with_the_weight_at_zero_authority_stops_mattering(self):
        """Otherwise the ordering above could be insertion order."""
        weighted = self._ranked([0.2, 0.6, 1.4], weight=0.12)
        flat = self._ranked([0.2, 0.6, 1.4], weight=0.0)
        self.assertNotEqual(weighted, flat,
                            "the ranking was unchanged with authority switched off, "
                            "so the test above proves nothing about authority")

    def test_authority_is_clamped_so_one_source_cannot_dominate(self):
        """A connector is free to report any number. Without a ceiling, a source
        claiming authority 1000 outranks every relevant document from every
        other source, and relevance stops mattering at all."""
        from oodarag.models import Chunk, ScoredChunk
        from oodarag.retrieve.rerank import HeuristicReranker

        reranker = HeuristicReranker(idf=lambda t: 1.0, vocabulary=set())
        reranker.clock = lambda: 1_700_000_000.0
        scores = {}
        for label, authority in (("huge", 1000.0), ("ceiling", 1.5), ("negative", -5.0)):
            chunk = Chunk(chunk_id="c", doc_id="d", ordinal=0, text="text",
                          context_header="", metadata={"authority": authority})
            scored = ScoredChunk(chunk=chunk, score=1.0, components={})
            reranker.rerank("text", [scored])
            scores[label] = scored.components["rerank_authority"]
        self.assertEqual(scores["huge"], scores["ceiling"],
                         "an unbounded authority was not clamped")
        self.assertEqual(scores["negative"], 0.0,
                         "a negative authority was not floored")
