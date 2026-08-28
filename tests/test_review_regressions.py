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

import unittest

from oodarag.chunking import chunk_document
from oodarag.eval.contamination import _longest_run, _normalize, detect
from oodarag.eval.harness import EvalHarness, Golden
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.models import Chunk, Document, RawDocument
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever
from oodarag.retrieve.rerank import _longest_common_run
from oodarag.scrape.html import extract
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.http import normalize_url
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

    def test_normalize_collapses_whitespace(self):
        self.assertEqual(_normalize("How does RRF work, exactly and completely?"),
                         "how does rrf work exactly and completely")

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
