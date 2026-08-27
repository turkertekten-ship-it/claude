"""End to end: ingest, index, query, and the loop that decides when to re-run."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.ingest.base import Connector, MemoryStateStore  # noqa: E402
from oodarag.ingest.files import FileConnector  # noqa: E402
from oodarag.loop import Action, OodaLoop  # noqa: E402
from oodarag.models import RawDocument  # noqa: E402
from oodarag.pipeline import Pipeline  # noqa: E402
from oodarag.store import Store  # noqa: E402


class ExplodingConnector(Connector):
    """A source that fails outright, to prove one failure does not stop the rest."""

    key = "exploding"

    def fetch(self, cursor: dict) -> object:
        raise ConnectionError("Tunnel connection failed: 403 Forbidden")


class StaticConnector(Connector):
    key = "static"

    def __init__(self, docs: list[RawDocument]) -> None:
        self.docs = docs

    def fetch(self, cursor: dict):  # type: ignore[no-untyped-def]
        yield from self.docs


def raw(name: str, text: str) -> RawDocument:
    return RawDocument("file", name, f"file:///{name}", name, text)


class TestFileConnector(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "notes.md").write_text("# Notes\n\nSome prose about budgets.", "utf-8")
        (self.root / "code.py").write_text("def f():\n    return 1\n", "utf-8")
        (self.root / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00binary")
        skipped = self.root / "node_modules"
        skipped.mkdir()
        (skipped / "vendor.js").write_text("module.exports = {}", "utf-8")

    def test_reads_text_files_and_skips_binaries(self) -> None:
        names = {d.external_id for d in FileConnector(self.root).run().documents}
        self.assertIn("notes.md", names)
        self.assertIn("code.py", names)
        self.assertNotIn("image.png", names)

    def test_excluded_directories_are_not_walked(self) -> None:
        names = {d.external_id for d in FileConnector(self.root).run().documents}
        self.assertFalse(any("node_modules" in n for n in names))

    def test_second_run_reports_everything_unchanged(self) -> None:
        state = MemoryStateStore()
        connector = FileConnector(self.root)
        first = connector.run(state=state)
        second = connector.run(state=state)
        self.assertEqual(first.delta.new, len(first.documents))
        self.assertEqual(second.delta.new, 0)
        self.assertEqual(second.delta.changed, 0)
        self.assertGreater(second.delta.unchanged, 0)

    def test_an_edited_file_is_reported_as_changed(self) -> None:
        state = MemoryStateStore()
        connector = FileConnector(self.root)
        connector.run(state=state)
        (self.root / "notes.md").write_text("# Notes\n\nCompletely different prose.", "utf-8")
        self.assertEqual(connector.run(state=state).delta.changed, 1)

    def test_a_missing_root_is_reported_in_the_delta_not_raised(self) -> None:
        result = FileConnector(self.root / "nope").run()
        self.assertEqual(result.delta.failed, 1)
        self.assertTrue(result.delta.errors)


class TestPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.pipe = Pipeline(self.store)

    def test_ingest_indexes_and_answers(self) -> None:
        docs = [raw("fusion.md",
                    "# Fusion\n\nReciprocal rank fusion combines ranked lists rather than "
                    "raw scores, because the two arms produce incomparable scales.")]
        report = self.pipe.ingest([StaticConnector(docs)])
        self.assertEqual(report.documents_changed, 1)
        self.assertGreater(report.chunks_written, 0)
        answer = self.pipe.query("why combine ranks rather than scores?")
        self.assertFalse(answer.abstained)

    def test_one_failing_connector_does_not_stop_the_others(self) -> None:
        docs = [raw("ok.md", "# Fine\n\nThis source is reachable and has real content.")]
        report = self.pipe.ingest([ExplodingConnector(), StaticConnector(docs)])
        self.assertEqual(report.documents_changed, 1)
        self.assertIn("exploding", report.unreachable)
        self.assertFalse(report.ok)

    def test_reingesting_unchanged_documents_writes_no_chunks(self) -> None:
        docs = [raw("a.md", "# A\n\nStable content that does not change between runs.")]
        state = MemoryStateStore()
        connector = StaticConnector(docs)
        self.pipe.ingest([connector], state=state)
        second = self.pipe.ingest([connector], state=state)
        self.assertEqual(second.documents_changed, 0)
        self.assertEqual(second.chunks_written, 0)

    def test_reindex_rebuilds_every_vector(self) -> None:
        docs = [raw("a.md", "# A\n\nContent worth embedding twice over.")]
        self.pipe.ingest([StaticConnector(docs)])
        before = self.pipe.stats()["chunks"]
        self.assertEqual(self.pipe.reindex(), before)
        after = self.pipe.stats()
        self.assertEqual(after["chunks"], after["embeddings"])


class TestOodaLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.pipe = Pipeline(self.store)
        self.docs = [raw("a.md", "# A\n\nEnough content to chunk and embed properly.")]

    def test_an_empty_index_decides_to_ingest(self) -> None:
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=MemoryStateStore())
        report = loop.cycle()
        self.assertIs(report.decision.action, Action.INGEST)
        self.assertIn("empty", report.orientation.reading)

    def test_an_empty_index_is_recorded_as_a_surprise(self) -> None:
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=MemoryStateStore())
        self.assertTrue(loop.cycle().orientation.surprise)

    def test_every_decision_states_what_would_falsify_it(self) -> None:
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=MemoryStateStore())
        for report in loop.run(2):
            self.assertTrue(report.decision.falsifier.strip())

    def test_a_populated_fresh_index_settles_on_doing_nothing(self) -> None:
        state = MemoryStateStore()
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=state)
        reports = loop.run(3)
        self.assertIs(reports[-1].decision.action, Action.NOTHING)

    def test_the_loop_stops_early_rather_than_repeating_a_no_op(self) -> None:
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=MemoryStateStore())
        self.assertLess(len(loop.run(5)), 5)

    def test_no_connectors_is_blocked_not_nothing(self) -> None:
        # "Nothing to do" and "nothing configured" are different situations
        # and must not report the same way.
        report = OodaLoop(self.pipe, [], state=MemoryStateStore()).cycle()
        self.assertIs(report.decision.action, Action.BLOCKED)

    def test_missing_vectors_trigger_a_reindex(self) -> None:
        self.pipe.ingest([StaticConnector(self.docs)])
        self.store.conn.execute("DELETE FROM embeddings")
        self.store.conn.commit()
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=MemoryStateStore())
        report = loop.cycle()
        self.assertIs(report.decision.action, Action.REINDEX)
        stats = self.pipe.stats()
        self.assertEqual(stats["chunks"], stats["embeddings"])

    def test_all_four_phases_appear_in_the_report(self) -> None:
        loop = OodaLoop(self.pipe, [StaticConnector(self.docs)], state=MemoryStateStore())
        payload = loop.cycle().as_dict()
        self.assertEqual(set(payload) >= {"observe", "orient", "decide", "act"}, True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
