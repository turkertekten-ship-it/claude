"""The control loop, the eval harness, and contamination detection."""

from __future__ import annotations

import json
import tempfile
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


if __name__ == "__main__":
    unittest.main()
