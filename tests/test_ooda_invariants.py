"""The phase boundary is the design, so it is what gets tested.

CLAUDE.md states two invariants for this module: `decide()` is a pure function
of the orientation, and `act()` is the only phase permitted to mutate anything.
Both are easy to state and easy to erode — one convenient `self.pipeline.` call
inside `decide` and the policy stops being testable without a network and an
index.

These tests are the thing that notices.
"""

from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from oodarag.ingest.files import FilesConnector
from oodarag.ooda.loop import LoopPolicy, Observation, OodaLoop

CORPUS = Path("evals/corpus")

STATS = {"documents": 9, "chunks": 48, "vectors": 48}


def _loop_without_wiring() -> OodaLoop:
    """An OodaLoop that was never given a pipeline.

    If `orient` or `decide` ever need one, constructing the loop this way stops
    working — which is the point. The purity claim is only meaningful if the
    phases genuinely run with nothing attached.
    """
    loop = OodaLoop.__new__(OodaLoop)
    loop.policy = LoopPolicy()
    loop._cycle = 0
    return loop


def _observation(**over) -> Observation:
    base = dict(
        stats=dict(STATS),
        deltas=[],
        eval_report={"recall_at_k": 0.41, "mrr": 0.33, "ndcg_at_k": 0.38},
        stale_sources=["web:https://example.com"],
        errors=["web:https://example.com: TransportError"],
    )
    base.update(over)
    return Observation(**base)


class DecideIsPure(unittest.TestCase):
    def test_decide_runs_with_no_pipeline_attached(self) -> None:
        loop = _observation()
        obj = _loop_without_wiring()
        actions = OodaLoop.decide(obj, OodaLoop.orient(obj, loop), loop)
        self.assertIsInstance(actions, list)

    def test_decide_is_deterministic(self) -> None:
        obj, obs = _loop_without_wiring(), _observation()
        orientation = OodaLoop.orient(obj, obs)
        key = lambda acts: [(a.kind, a.target, a.reason, sorted(a.params.items())) for a in acts]
        self.assertEqual(key(OodaLoop.decide(obj, orientation, obs)),
                         key(OodaLoop.decide(obj, orientation, obs)))

    def test_decide_touches_no_io(self) -> None:
        source = inspect.getsource(OodaLoop.decide)
        for forbidden in ("open(", "urllib", "sqlite3", "self.pipeline.",
                          "self.connectors", "time.sleep", ".run("):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden, source,
                                 f"decide() reaches for {forbidden!r}; it is no longer pure")

    def test_every_action_states_a_reason(self) -> None:
        # An automation that acts without a stated reason cannot be audited
        # afterwards, and an unauditable automation gets switched off.
        obj, obs = _loop_without_wiring(), _observation()
        for action in OodaLoop.decide(obj, OodaLoop.orient(obj, obs), obs):
            with self.subTest(kind=action.kind):
                self.assertTrue(action.reason.strip(), f"{action.kind} carries no reason")

    def test_it_respects_max_actions_per_cycle(self) -> None:
        obj = _loop_without_wiring()
        obj.policy = LoopPolicy(max_actions_per_cycle=1)
        obs = _observation()
        self.assertLessEqual(len(OodaLoop.decide(obj, OodaLoop.orient(obj, obs), obs)), 1)

    def test_a_healthy_corpus_still_produces_an_explicit_decision(self) -> None:
        # Printing nothing when it decides nothing makes the loop look broken,
        # so "do nothing" has to be a reportable decision rather than silence.
        obj = _loop_without_wiring()
        obs = _observation(
            stats={**STATS, "bm25": 48, "dense": 48},
            eval_report={"recall_at_k": 0.98, "mrr": 0.97, "ndcg_at_k": 0.96},
            stale_sources=[], errors=[],
        )
        actions = OodaLoop.decide(obj, OodaLoop.orient(obj, obs), obs)
        self.assertTrue(actions, "decide() returned nothing at all on a healthy corpus")
        self.assertTrue(all(a.reason.strip() for a in actions))


class OrientationIsBounded(unittest.TestCase):
    def test_every_score_is_a_fraction(self) -> None:
        obj = _loop_without_wiring()
        for obs in (_observation(),
                    _observation(eval_report=None, stale_sources=[], errors=[]),
                    _observation(eval_report={"recall_at_k": 1.0, "mrr": 1.0, "ndcg_at_k": 1.0})):
            orientation = OodaLoop.orient(obj, obs)
            for name in ("staleness", "quality", "error_rate"):
                with self.subTest(name=name):
                    value = getattr(orientation, name)
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLessEqual(value, 1.0)

    def test_orient_takes_no_clock(self) -> None:
        # Ages are frozen in observe(), so a cycle report replays identically
        # months later. A clock in orient() would quietly break that.
        source = inspect.getsource(OodaLoop.orient)
        for forbidden in ("time.time(", "datetime.now", "time.monotonic("):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden, source)


class DryRunMutatesNothing(unittest.TestCase):
    def test_a_dry_cycle_leaves_the_store_untouched(self) -> None:
        if not CORPUS.is_dir():
            self.skipTest(f"{CORPUS} is missing")
        from oodarag.pipeline import Pipeline, PipelineConfig

        with tempfile.TemporaryDirectory() as tmp:
            pipe = Pipeline(PipelineConfig(root=Path(tmp)))
            try:
                pipe.ingest([FilesConnector(str(CORPUS))])
                pipe.refresh_indexes()
                before = pipe.stats()
                # Without this, an ingest that silently did nothing would make
                # every assertion below trivially true — the exact shape of test
                # that passes while proving nothing.
                self.assertGreater(before.get("documents", 0), 0, "nothing was ingested")
                self.assertGreater(before.get("chunks", 0), 0, "nothing was chunked")
                self.assertGreater(before.get("vectors", 0), 0, "nothing was embedded")

                loop = OodaLoop(pipe, [FilesConnector(str(CORPUS))],
                                policy=LoopPolicy(dry_run=True))
                report = loop.cycle()

                after = pipe.stats()
                for key in ("documents", "chunks", "vectors"):
                    with self.subTest(key=key):
                        self.assertEqual(before.get(key), after.get(key),
                                         f"dry run changed {key}")
                # A dry run that decides nothing proves nothing about act().
                self.assertTrue(report.decided, "dry cycle decided nothing to skip")
            finally:
                pipe.close()


if __name__ == "__main__":
    unittest.main()
