"""The control loop, the eval harness, and contamination detection."""

from __future__ import annotations

import json
import tempfile
import pathlib
import unittest
from pathlib import Path

from oodarag.eval.contamination import detect
from oodarag.eval.harness import EvalHarness, Golden, load_goldens
from oodarag.eval.metrics import mrr, ndcg_at_k, precision_at_k, recall_at_k
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.base import Connector, MemoryStateStore
from oodarag.ingest.youtube import YouTubeConnector, cues_to_transcript, parse_vtt, video_id
from oodarag.models import RawDocument
from oodarag.ooda.loop import LoopConfig, OodaLoop
from oodarag.ooda.policy import (
    ALERT,
    EMBED_MISSING,
    NOOP,
    QUARANTINE_SOURCE,
    REINDEX,
    Thresholds,
    decide,
)
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever
from oodarag.store.sqlite_store import SqliteStore


class MetricsTest(unittest.TestCase):
    def test_recall_and_precision(self):
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "d", "z"}
        self.assertAlmostEqual(recall_at_k(retrieved, relevant, 4), 2 / 3)
        self.assertAlmostEqual(precision_at_k(retrieved, relevant, 4), 2 / 4)

    def test_mrr_uses_the_first_hit(self):
        self.assertEqual(mrr(["x", "y", "a"], {"a", "y"}), 0.5)
        self.assertEqual(mrr(["x", "y"], {"z"}), 0.0)

    def test_ndcg_rewards_earlier_hits(self):
        early = ndcg_at_k(["a", "x", "y"], {"a"}, 3)
        late = ndcg_at_k(["x", "y", "a"], {"a"}, 3)
        self.assertGreater(early, late)
        self.assertAlmostEqual(early, 1.0)

    def test_empty_relevant_set_is_vacuously_satisfied(self):
        self.assertEqual(recall_at_k(["a"], set(), 5), 1.0)


class PolicyTest(unittest.TestCase):
    def test_missing_vectors_outrank_everything_else(self):
        actions = decide({"embedding_coverage": 0.5, "corpus_growth": 5.0,
                          "content_changed": True, "documents": 100})
        self.assertEqual(actions[0].kind, EMBED_MISSING)

    def test_fingerprint_mismatch_triggers_a_reindex(self):
        actions = decide({"fingerprint_mismatch": True, "index_fingerprint": "old",
                          "embedder_fingerprint": "new"})
        self.assertIn(REINDEX, [a.kind for a in actions])

    def test_repeated_source_failures_quarantine_it(self):
        actions = decide({"sources": {"web:x": {"consecutive_failures": 3,
                                                "last_error": "boom"}}})
        quarantines = [a for a in actions if a.kind == QUARANTINE_SOURCE]
        self.assertEqual(len(quarantines), 1)
        self.assertEqual(quarantines[0].target, "web:x")

    def test_a_single_failure_does_not_quarantine(self):
        actions = decide({"sources": {"web:x": {"consecutive_failures": 1,
                                                "failure_rate": 0.1}}})
        self.assertNotIn(QUARANTINE_SOURCE, [a.kind for a in actions])

    def test_eval_regression_raises_an_alert(self):
        actions = decide({"eval_pass_rate": 0.70, "previous_eval_pass_rate": 0.95})
        alerts = [a for a in actions if a.kind == ALERT and a.target == "eval"]
        self.assertTrue(alerts)
        self.assertGreaterEqual(max(a.priority for a in alerts), 90)

    def test_healthy_situation_is_a_noop(self):
        actions = decide({"embedding_coverage": 1.0, "corpus_growth": 0.0,
                          "content_changed": False, "sources": {}, "degradations": []})
        self.assertEqual([a.kind for a in actions], [NOOP])

    def test_every_action_carries_its_evidence(self):
        actions = decide({"embedding_coverage": 0.4}, Thresholds())
        for action in actions:
            if action.kind != NOOP:
                self.assertTrue(action.reason, "an action with no stated reason is unauditable")


class StubConnector(Connector):
    """Yields a fixed set of documents; can be made to fail on demand."""

    def __init__(self, key: str, docs: dict[str, str], fail: bool = False):
        self.key = key
        self.docs = docs
        self.fail = fail
        self.authority = 1.0

    def fetch(self, cursor):
        if self.fail:
            raise RuntimeError("source unavailable")
        for name, text in self.docs.items():
            yield RawDocument("filesystem", name, f"file:///{name}", name, text)


CORPUS = {
    "alpha.md": ("# Retrieval\n\nHybrid retrieval fuses a dense arm and a lexical arm "
                 "with reciprocal rank fusion, because their failures are uncorrelated."),
    "beta.md": ("# Budgets\n\nEvery network loop is bounded by requests, bytes, depth "
                "and wall clock time, so that work cannot run away invisibly."),
    "gamma.md": ("# Citations\n\nCitation markers are verified against the chunks that "
                 "were actually retrieved, and invalid markers are stripped."),
}


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        self.addCleanup(self.store.close)

    def _loop(self, connectors, **kwargs):
        options = dict(probe_access=False, goldens_path=None)
        options.update(kwargs)
        return OodaLoop(self.pipeline, connectors, LoopConfig(**options))

    def test_a_cycle_indexes_and_journals_every_phase(self):
        loop = self._loop([StubConnector("stub", CORPUS)])
        report = loop.cycle()
        self.assertEqual(report.observations["documents_ingested"], 3)
        self.assertEqual(self.store.stats()["documents"], 3)
        phases = {entry["phase"] for entry in self.store.read_journal(limit=50)}
        self.assertEqual(phases, {"observe", "orient", "decide", "act", "cycle"})

    def test_a_second_cycle_ingests_nothing_new(self):
        connector = StubConnector("stub", CORPUS)
        loop = self._loop([connector])
        loop.cycle()
        second = loop.cycle()
        self.assertEqual(second.observations["documents_ingested"], 0)
        self.assertEqual(second.situation["embedding_coverage"], 1.0)

    def test_the_loop_converges_on_a_corpus_that_stops_changing(self):
        """The defining property of a control loop, and the one nothing asserted.

        A loop that keeps acting on an unchanging system is thrashing, and the
        usual cause is an action that does not clear its own trigger: it fires,
        the situation is re-measured, the same condition still holds, and it
        fires again for ever. Neither the per-rule unit tests nor "a second
        cycle ingests nothing" catch that - the first tests one decision from a
        hand-built situation, the second only looks at ingestion.
        """
        connector = StubConnector("stub", CORPUS)
        loop = self._loop([connector])
        reports = [loop.cycle() for _ in range(5)]

        after_settling = reports[1:]
        for index, report in enumerate(after_settling, start=2):
            kinds = {action.kind for action in report.actions}
            self.assertEqual(
                kinds, {"noop"},
                f"cycle {index} still wanted to act on an unchanged corpus: {kinds}")

    def test_no_action_is_decided_twice_on_an_unchanged_corpus(self):
        """Whatever the first cycle decided, the second must not decide again.

        **What this does not prove.** It does not show that the *action* cleared
        the condition. The observe phase ingests, and ingesting embeds, so a
        broken `embed_missing` is masked - replacing that call with a no-op
        leaves both these tests green, which was checked rather than assumed.
        What it does catch is the loop-level failure: a rule whose condition
        survives the cycle, which makes the loop act for ever. Mutating the
        coverage rule to fire unconditionally fails this and the convergence
        test above.

        Naming it for the loop-level property rather than the per-action one,
        because a test that claims more than it checks is worse than no test.
        """
        # Chunks written without vectors, so embedding coverage is below
        # threshold and the highest-priority rule genuinely fires. A cycle that
        # decides nothing cannot demonstrate that decisions clear themselves,
        # which is why this is set up rather than hoped for.
        from oodarag.chunking import chunk_document
        from oodarag.models import Document

        docs = [Document(doc_id=f"x{i}", source_system="stub", external_id=f"x{i}",
                         uri=f"mem://x{i}", title=f"x{i}",
                         text=f"Document {i} about budgets, crawling and citations.",
                         content_hash=f"h{i}", metadata={},
                         created_at=0.0, updated_at=0.0)
                for i in range(3)]
        self.store.upsert_documents(docs)
        for doc in docs:
            self.store.replace_chunks(doc.doc_id, chunk_document(doc))

        loop = self._loop([StubConnector("stub", CORPUS)])
        first = loop.cycle()
        second = loop.cycle()

        acted = {a.kind for a in first.actions if a.kind != "noop"}
        self.assertTrue(acted, "the first cycle did nothing, so this proves nothing")
        repeated = acted & {a.kind for a in second.actions}
        self.assertFalse(
            repeated,
            f"these actions did not clear the condition that triggered them: {repeated}")

    def test_a_failed_ingest_leaves_work_the_policy_picks_up(self):
        """`embed_missing` looks unreachable and is not, which is why this is
        here rather than only in the policy unit tests.

        Observe ingests, and ingesting embeds, so on every healthy path the
        condition is already cleared before Decide runs - measured directly:
        three chunks without vectors go in, and the situation Decide sees
        reports coverage 1.0. The rule earns its place in the one case where the
        ingest could not do its job. Concluding it was dead from the healthy
        paths alone would have deleted a live safety rule.
        """
        class _Failing(Connector):
            key = "bad"
            source_system = "bad"

            def fetch(self, cursor):
                raise RuntimeError("source unavailable")

        loop = self._loop([_Failing()])
        kinds = set()
        for _ in range(2):
            kinds |= {a.kind for a in loop.cycle().actions}
        self.assertIn("embed_missing", kinds,
                      f"a failed ingest produced no repair action: {sorted(kinds)}")

    def test_the_healthy_path_never_needs_the_repair_action(self):
        """The other half of the same claim. If this ever fails, either the
        ingest stopped embedding or the coverage threshold moved."""
        loop = self._loop([StubConnector("stub", CORPUS)])
        report = loop.cycle()
        self.assertEqual(report.situation["embedding_coverage"], 1.0)
        self.assertNotIn("embed_missing", {a.kind for a in report.actions})

    def test_cycle_numbers_increment_and_persist(self):
        loop = self._loop([StubConnector("stub", CORPUS)])
        loop.cycle()
        loop.cycle()
        self.assertEqual(self.store.get_meta("ooda_cycle"), 2)

    def test_a_failing_source_is_recorded_not_raised(self):
        loop = self._loop([StubConnector("broken", {}, fail=True)])
        report = loop.cycle()
        health = report.situation["sources"]["broken"]
        self.assertEqual(health["consecutive_failures"], 1)
        self.assertIn("source unavailable", health["last_error"])

    def test_repeated_failure_leads_to_quarantine(self):
        connector = StubConnector("broken", {}, fail=True)
        loop = self._loop([connector])
        for _ in range(3):
            report = loop.cycle()
        kinds = [outcome["kind"] for outcome in report.outcomes]
        self.assertIn(QUARANTINE_SOURCE, kinds)
        self.assertNotIn(connector, loop.connectors)

    def test_dry_run_decides_but_does_not_act(self):
        loop = self._loop([StubConnector("stub", CORPUS)], dry_run=True)
        loop.cycle()
        # Ingestion still happens (that is Observe); the decided actions do not.
        second = self._loop([StubConnector("stub", CORPUS)], dry_run=True)
        report = second.cycle()
        for outcome in report.outcomes:
            self.assertIn(outcome["status"], {"dry_run", "done"})
            if outcome["kind"] not in (NOOP, ALERT):
                self.assertEqual(outcome["status"], "dry_run")

    def test_action_budget_defers_the_remainder(self):
        loop = self._loop([StubConnector("stub", CORPUS)], max_actions_per_cycle=1)
        loop.cycle()
        self.store.set_meta("index_fingerprint", "a-different-space")
        report = loop.cycle()
        if len(report.actions) > 1:
            self.assertIn("deferred", [o["status"] for o in report.outcomes])


class EvalHarnessTest(unittest.TestCase):
    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        OodaLoop(self.pipeline, [StubConnector("stub", CORPUS)],
                 LoopConfig(probe_access=False, goldens_path=None)).cycle()
        self.generator = AnswerGenerator(
            HybridRetriever(self.store, self.pipeline.embedder),
            AnswerConfig(generator="extractive"),
        )
        self.addCleanup(self.store.close)

    def test_a_satisfiable_golden_passes(self):
        report = EvalHarness(self.generator, k=5).run(
            [Golden(question="how are dense and lexical results combined?",
                    expect_sources=["alpha.md"])])
        self.assertEqual(report.pass_rate, 1.0, report.cases[0].failures)
        self.assertGreater(report.cases[0].recall, 0.0)

    def test_an_unsatisfiable_golden_fails_with_a_reason(self):
        report = EvalHarness(self.generator, k=5).run(
            [Golden(question="how are dense and lexical results combined?",
                    expect_sources=["nonexistent.md"])])
        self.assertEqual(report.pass_rate, 0.0)
        self.assertIn("nonexistent.md", report.cases[0].failures[0])

    def test_a_negative_golden_passes_when_the_system_abstains(self):
        report = EvalHarness(self.generator, k=5).run(
            [Golden(question="what is the melting point of gallium?", expect_abstain=True)])
        self.assertEqual(report.pass_rate, 1.0, report.cases[0].failures)

    def test_goldens_round_trip_through_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g.jsonl"
            path.write_text(
                "# a comment\n\n"
                + json.dumps({"question": "q1", "expect_sources": ["a"]}) + "\n"
                + json.dumps({"question": "q2", "expect_abstain": True}) + "\n",
                encoding="utf-8")
            goldens = load_goldens(path)
        self.assertEqual([g.question for g in goldens], ["q1", "q2"])
        self.assertTrue(goldens[1].expect_abstain)

    def test_a_malformed_golden_names_its_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text('{"question": "ok"}\n{not json}\n', encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_goldens(path)
        self.assertIn(":2:", str(ctx.exception))


class ContaminationTest(unittest.TestCase):
    def setUp(self):
        self.store = SqliteStore(":memory:")
        self.pipeline = IndexPipeline(self.store)
        self.addCleanup(self.store.close)

    def _index(self, docs: dict[str, str]):
        OodaLoop(self.pipeline, [StubConnector("stub", docs)],
                 LoopConfig(probe_access=False, goldens_path=None)).cycle()

    def test_a_clean_corpus_reports_clean(self):
        self._index(CORPUS)
        report = detect(self.store, ["what is the capital of France?"],
                        negative_questions={"what is the capital of France?"})
        self.assertTrue(report.clean, report.summary())

    def test_a_verbatim_question_in_the_corpus_is_fatal(self):
        docs = dict(CORPUS)
        docs["leak.md"] = ("Test cases we assert are unanswerable: "
                           "What is the capital of France? and others.")
        self._index(docs)
        report = detect(self.store, ["What is the capital of France?"],
                        negative_questions={"What is the capital of France?"})
        self.assertFalse(report.clean)
        self.assertEqual(report.fatal_findings[0].kind, "verbatim")

    def test_paraphrase_contaminates_a_negative_case(self):
        docs = dict(CORPUS)
        # Deliberately not verbatim: the wording differs, the terms do not.
        docs["leak.md"] = "We check that questions about the 1998 World Cup final abstain."
        self._index(docs)
        question = "Who won the 1998 FIFA World Cup final?"
        report = detect(self.store, [question], negative_questions={question})
        self.assertFalse(report.clean, "near-miss paraphrase went undetected")

    def test_a_positive_golden_matching_its_answer_is_not_contamination(self):
        self._index(CORPUS)
        # The corpus contains the answer, which is the entire point.
        report = detect(self.store, ["what bounds requests bytes depth and wall clock time?"],
                        negative_questions=set())
        self.assertTrue(report.clean, report.summary())

    def test_the_harness_quarantines_contaminated_documents(self):
        docs = dict(CORPUS)
        docs["leak.md"] = ("A negative test case: what is the melting point of gallium? "
                           "The system must abstain on this question.")
        self._index(docs)
        generator = AnswerGenerator(
            HybridRetriever(self.store, self.pipeline.embedder),
            AnswerConfig(generator="extractive"))
        question = "what is the melting point of gallium?"

        leaked = EvalHarness(generator, k=5, quarantine_contaminated=False).run(
            [Golden(question=question, expect_abstain=True)])
        quarantined = EvalHarness(generator, k=5, quarantine_contaminated=True).run(
            [Golden(question=question, expect_abstain=True)])

        self.assertFalse(leaked.contamination.clean)
        self.assertTrue(quarantined.quarantined, "nothing was quarantined")
        self.assertEqual(quarantined.pass_rate, 1.0,
                         f"quarantine did not restore abstention: {quarantined.cases[0].failures}")


class YouTubeConnectorTest(unittest.TestCase):
    VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.500
Large language models are limited to

2
00:00:04.500 --> 00:00:08.000
the data they were trained on.

3
00:00:41.000 --> 00:00:45.000
Retrieval augmented generation addresses that.
"""

    def test_video_ids_are_parsed_from_every_url_shape(self):
        for candidate in ["https://www.youtube.com/watch?v=T-D1OfcDW1M",
                          "https://youtu.be/T-D1OfcDW1M",
                          "https://www.youtube.com/embed/T-D1OfcDW1M",
                          "T-D1OfcDW1M"]:
            with self.subTest(candidate=candidate):
                self.assertEqual(video_id(candidate), "T-D1OfcDW1M")

    def test_a_non_video_string_yields_none(self):
        self.assertIsNone(video_id("https://example.com/not-a-video"))

    def test_vtt_and_srt_both_parse(self):
        srt = self.VTT.replace("WEBVTT\n\n", "").replace(".", ",")
        self.assertEqual(len(parse_vtt(self.VTT)), 3)
        self.assertEqual(len(parse_vtt(srt)), 3)

    def test_cues_are_grouped_into_timestamped_windows(self):
        transcript = cues_to_transcript(parse_vtt(self.VTT), window_seconds=30)
        lines = transcript.split("\n")
        self.assertEqual(len(lines), 2, "cues were not grouped into windows")
        self.assertTrue(lines[0].startswith("[00:01]"))
        self.assertIn("limited to the data they were trained on", lines[0])
        self.assertTrue(lines[1].startswith("[00:41]"))

    def test_captions_file_is_used_and_labelled_as_captions(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "c.vtt").write_text(self.VTT, encoding="utf-8")
            (base / "m.json").write_text(json.dumps({"videos": [
                {"video_id": "T-D1OfcDW1M", "title": "RAG", "channel": "IBM Technology",
                 "captions_file": "c.vtt"}]}), encoding="utf-8")
            connector = YouTubeConnector(base / "m.json", allow_network=False)
            docs = connector.run(MemoryStateStore()).documents
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["transcript_source"], "captions")
        self.assertIn("Large language models", docs[0].text)
        self.assertEqual(docs[0].uri, "https://www.youtube.com/watch?v=T-D1OfcDW1M")

    def test_a_curated_note_is_labelled_in_the_text_not_only_the_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "m.json").write_text(json.dumps({"videos": [
                {"video_id": "T-D1OfcDW1M", "title": "RAG",
                 "summary": "RAG grounds a model in retrieved documents."}]}),
                encoding="utf-8")
            docs = YouTubeConnector(base / "m.json",
                                    allow_network=False).run(MemoryStateStore()).documents
        self.assertEqual(docs[0].metadata["transcript_source"], "curated_note")
        # A reader of the retrieved passage must be able to tell a summary from
        # a quotation without inspecting metadata.
        self.assertIn("not a verbatim transcript", docs[0].text)

    def test_a_video_with_no_transcript_says_so_rather_than_inventing_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "m.json").write_text(json.dumps({"videos": [
                {"video_id": "T-D1OfcDW1M", "title": "RAG", "channel": "IBM Technology"}]}),
                encoding="utf-8")
            docs = YouTubeConnector(base / "m.json",
                                    allow_network=False).run(MemoryStateStore()).documents
        self.assertEqual(docs[0].metadata["transcript_source"], "metadata_only")
        self.assertIn("No transcript available", docs[0].text)

    def test_the_committed_ibm_manifest_is_well_formed(self):
        manifest = Path(__file__).resolve().parent.parent / "corpus" / "ibm-technology" / "manifest.json"
        if not manifest.exists():
            self.skipTest("manifest not present")
        docs = YouTubeConnector(manifest, allow_network=False).run(MemoryStateStore()).documents
        self.assertGreater(len(docs), 3)
        for doc in docs:
            with self.subTest(uri=doc.uri):
                self.assertTrue(video_id(doc.uri), "manifest entry has no resolvable video id")
                self.assertIn(doc.metadata["verification"],
                              {"search_confirmed", "search_listed", "unverified"})
                # Nothing in the committed manifest may claim to be a transcript.
                self.assertNotEqual(doc.metadata["transcript_source"], "captions")


class QuarantineCountsSayWhatTheyCountTest(unittest.TestCase):
    """The run log and the report counted the same operation differently and
    labelled both "documents": 14 in one line, 29 in the other. A document that
    contaminates two questions is held out twice and is still one document.
    `internal/PLAN.md` had recorded the holdout total as a document count.
    """

    def _report_with(self, quarantined):
        from oodarag.eval.harness import EvalReport

        report = EvalReport()
        report.quarantined = quarantined
        return report.to_markdown()

    def test_one_document_contaminating_two_questions_is_still_one_document(self):
        # Derived, not copied: two questions share doc "a", so the distinct
        # count is 2 (a, b) and the holdout count is 3.
        text = self._report_with({"q1": ["a", "b"], "q2": ["a"]})
        self.assertIn("2 distinct document(s)", text)
        self.assertIn("3 per-question holdout(s)", text)
        self.assertIn("across 2 question(s)", text)

    def test_the_two_counts_coincide_when_nothing_overlaps(self):
        text = self._report_with({"q1": ["a"], "q2": ["b"]})
        self.assertIn("2 distinct document(s)", text)
        self.assertIn("2 per-question holdout(s)", text)

    def test_nothing_is_claimed_when_nothing_was_quarantined(self):
        self.assertNotIn("Quarantined", self._report_with({}))


class GuardReachabilityTest(unittest.TestCase):
    """Two abstention guards that have never fired, for different reasons.

    "I could not make it fire" and "it cannot fire" are different claims, and
    only the second justifies calling a safety check dead (L25). These compute
    the bound rather than sampling for it.
    """

    def test_a_chunk_matching_nothing_still_clears_min_top_score(self):
        """So `min_top_score` cannot fire on a non-empty result list.

        Derived from the weights, not observed: the query-independent priors are
        present whatever the chunk says.
        """
        from oodarag.generate.answer import AnswerConfig
        from oodarag.retrieve.rerank import HeuristicReranker

        r = HeuristicReranker()
        authority_of_a_chunk_with_no_metadata = 1.0 / 1.5
        floor = (r.authority_weight * authority_of_a_chunk_with_no_metadata
                 + r.position_weight * 1.0)
        self.assertGreater(floor, AnswerConfig().min_top_score * 10,
                           "min_top_score is now within reach, so it is no longer "
                           "dead and its docstring is wrong")

    def test_zeroing_the_query_independent_priors_brings_it_back_to_life(self):
        """The condition under which the guard stops being dead, asserted so
        the claim in its docstring is checked rather than believed."""
        from oodarag.generate.answer import AnswerConfig
        from oodarag.retrieve.rerank import HeuristicReranker

        r = HeuristicReranker(authority_weight=0.0, position_weight=0.0)
        floor = r.authority_weight * (1.0 / 1.5) + r.position_weight * 1.0
        self.assertLess(floor, AnswerConfig().min_top_score,
                        "with no query-independent priors a chunk matching "
                        "nothing should fall under the floor")


class RelevanceStatisticIsARealControlTest(unittest.TestCase):
    """The two settings must decide differently, not merely run different code.

    A control that names a behaviour and does not change it is L17's failure
    mode: both settings looked like success because the output was identical.
    `mean` is measurably worse on the gate corpus and better on the held-out
    set, so it is a real alternative kept behind a default - which only means
    anything if the flag reaches the decision.

    Built on a real index and a real retrieval rather than a stub: the floor is
    *derived* from the relevances the pipeline actually produces, so the test
    cannot pass by agreeing with numbers invented to make it pass (L31).
    """

    def test_the_two_settings_decide_differently(self):
        import statistics
        from tempfile import TemporaryDirectory

        from oodarag.generate.answer import AnswerConfig, AnswerGenerator
        from oodarag.ingest.filesystem import FilesystemConnector
        from oodarag.pipeline import IndexPipeline
        from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
        from oodarag.store.sqlite_store import SqliteStore

        question = "which library formats source code?"
        with TemporaryDirectory() as tmp:
            store = SqliteStore(f"{tmp}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector("corpus/external/pypi",
                                              patterns=["**/*.md"], key="fs:t")])
            retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            results, _trace = retriever.retrieve(question)
            relevances = [r.components.get("rerank_relevance", 0.0) for r in results]
            top, average = max(relevances), statistics.mean(relevances)
            # A maximum over eight values exceeds their mean unless every value
            # is identical, which for a real query it is not. If this ever
            # fails, the two statistics cannot be distinguished on this input
            # and the rest of the test would be vacuous.
            self.assertGreater(top, average,
                               f"max {top} not above mean {average}; nothing to test")
            floor = (top + average) / 2

            def abstains(statistic: str) -> bool:
                config = AnswerConfig(generator="extractive",
                                      relevance_statistic=statistic,
                                      min_relevance=floor)
                return AnswerGenerator(retriever, config).answer(question).abstained

            self.assertFalse(abstains("max"),
                             "max is above the floor by construction and must answer")
            self.assertTrue(abstains("mean"),
                            "mean is below the floor by construction and must abstain")
            store.close()


class EmptyIndexIsNotAQualityCollapseTest(unittest.TestCase):
    """An eval against an empty index reported 22 failing cases and every metric
    at 0.0 - identical to the retriever having failed completely.

    It happened in CI: a new eval step was ordered before the step that builds
    its index, and the run read as a catastrophic regression rather than a
    workflow mistake. "Empty" is *blocked*, *filtered* or *absent*, and a report
    that cannot say which is a report that misleads (L69).
    """

    def _config(self, path):
        from oodarag.config import Config

        return Config(index_path=str(path), state_path=str(path) + ".state",
                      goldens_path="evals/goldens-heldout.jsonl")

    def test_it_refuses_rather_than_reporting_every_case_as_a_failure(self):
        import argparse
        from tempfile import TemporaryDirectory

        from oodarag.cli import cmd_eval

        with TemporaryDirectory() as tmp:
            args = argparse.Namespace(goldens="evals/goldens-heldout.jsonl", k=8,
                                      exclude_source=(), json=False, out=None,
                                      min_pass_rate=0.0)
            code = cmd_eval(args, self._config(pathlib.Path(tmp) / "empty.db"))
        self.assertEqual(code, 2,
                         "an empty index must not exit 0, and must not exit 1 "
                         "either - 1 is a quality regression and this is not one")

    def test_a_populated_index_still_evaluates(self):
        """The refusal must not fire on a real index, or it is just an outage."""
        import argparse
        from tempfile import TemporaryDirectory

        from oodarag.cli import cmd_eval
        from oodarag.ingest.filesystem import FilesystemConnector
        from oodarag.pipeline import IndexPipeline
        from oodarag.store.sqlite_store import SqliteStore

        with TemporaryDirectory() as tmp:
            db = pathlib.Path(tmp) / "full.db"
            store = SqliteStore(str(db))
            IndexPipeline(store).run([FilesystemConnector(
                "corpus/external/pypi", patterns=["**/*.md"], key="fs:e")])
            store.close()
            args = argparse.Namespace(goldens="evals/goldens-heldout.jsonl", k=8,
                                      exclude_source=(), json=False, out=None,
                                      min_pass_rate=0.0)
            code = cmd_eval(args, self._config(db))
        self.assertEqual(code, 0, "the refusal fired on a populated index")


if __name__ == "__main__":
    unittest.main()


class TheMeasuringInstrumentIsItselfMeasuredTest(unittest.TestCase):
    """The metrics that gate CI, mutation-tested and found unguarded.

    L28 says whatever produces your numbers deserves adversarial attention
    first, because every conclusion is conditional on it. Mutating
    `eval/metrics.py` found four corruptions the suite did not notice:

        recall ignores k entirely                 SURVIVED
        ndcg credits repeats (dedup removed)      SURVIVED
        ndcg ideal not truncated to k             SURVIVED
        ndcg ignores k in the retrieved list      SURVIVED

    The second is the exact bug `ndcg_at_k`'s docstring records as fixed - "the
    metric went above 1.0, which for a *normalised* measure is a loud signal" -
    with no test to stop it coming back. Every retrieval number in this project
    is a recall@8 or an nDCG@8, so a silent regression here would not break a
    build; it would move every reported figure.

    Expected values are derived from the definitions, not copied from a passing
    run, and each is chosen so the correct and broken implementations differ.
    """

    def test_recall_counts_only_the_first_k(self):
        from oodarag.eval.metrics import recall_at_k

        # Two relevant items, one inside k and one past it. Truncating gives
        # 1/2; ignoring k gives 2/2.
        retrieved = ["a"] + [f"filler{i}" for i in range(8)] + ["b"]
        self.assertEqual(recall_at_k(retrieved, {"a", "b"}, 8), 0.5)

    def test_ndcg_credits_a_repeated_item_once(self):
        from oodarag.eval.metrics import ndcg_at_k

        # dcg([1,0])/dcg([1]) = 1.0; crediting the repeat gives 1.63, and a
        # normalised measure above 1.0 is the signal the docstring names.
        score = ndcg_at_k(["a", "a"], {"a"}, 2)
        self.assertLessEqual(score, 1.0, "nDCG exceeded 1.0; the dedup is gone")
        self.assertAlmostEqual(score, 1.0, places=6)

    def test_ndcg_ideal_is_truncated_to_k(self):
        from oodarag.eval.metrics import ndcg_at_k

        # Three relevant, only two slots: a perfect top-2 must score 1.0.
        # Against an untruncated ideal it scores 0.7654.
        self.assertAlmostEqual(ndcg_at_k(["a", "b"], {"a", "b", "c"}, 2), 1.0, places=6)

    def test_ndcg_ignores_hits_beyond_k(self):
        from oodarag.eval.metrics import ndcg_at_k

        # The only relevant item sits at rank 3 with k=2, so nothing is found.
        # Without truncation it would score 0.5.
        self.assertEqual(ndcg_at_k(["a", "b", "c"], {"c"}, 2), 0.0)
