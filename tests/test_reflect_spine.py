"""Tests for the contracts every other part of the loop is written against.

These matter more than they look. The fingerprints are what let the journal
recognise a finding it saw last night, so a change that quietly destabilises
one would not break a build - it would make the loop suggest the same thing
forever and never learn. That failure is invisible without a test that pins the
behaviour down.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from oodarag.reflect.detect.base import (
    DetectContext,
    Detector,
    build_detectors,
    jaccard,
    normalize_phrase,
    register,
    registry,
)
from oodarag.reflect.detect import base as detect_base
from oodarag.reflect.journal import Journal
from oodarag.reflect.models import (
    KIND_COMMAND,
    KIND_PROMPT,
    CycleReport,
    EditOp,
    Evidence,
    Finding,
    Outcome,
    Proposal,
    Signal,
    day_key,
)
from oodarag.reflect.sources.base import Budget, SignalSource, safe_read_text


def sig(text: str, *, kind: str = KIND_PROMPT, session: str = "s", ts: float = 1000.0,
        ordinal: int = 0) -> Signal:
    return Signal(kind=kind, source="test", text=text, ts=ts, session=session, ordinal=ordinal)


class TestSignal(unittest.TestCase):
    def test_day_is_local(self) -> None:
        now = time.time()
        self.assertEqual(day_key(now), time.strftime("%Y-%m-%d", time.localtime(now)))

    def test_fingerprint_is_content_identity(self) -> None:
        a = sig("make test", ts=1.0)
        b = sig("make test", ts=99999.0, session="other")
        self.assertEqual(a.fingerprint, b.fingerprint, "same content must collapse")
        self.assertNotEqual(a.fingerprint, sig("make lint").fingerprint)

    def test_preview_is_flattened_and_bounded(self) -> None:
        s = sig("a\n\n   b" + "x" * 500)
        self.assertNotIn("\n", s.preview)
        self.assertLessEqual(len(s.preview), 160)


class TestFingerprintStability(unittest.TestCase):
    """The journal correlates across nights by fingerprint; these must not drift."""

    def finding(self, **kw) -> Finding:
        base = dict(rule_id="r.x", title="T", key="k", targets=["a.md"])
        base.update(kw)
        return Finding(**base)

    def test_finding_fingerprint_ignores_volatile_fields(self) -> None:
        a = self.finding(detail="one", confidence=0.1, evidence=[Evidence(quote="q")])
        b = self.finding(detail="two", confidence=0.9)
        self.assertEqual(a.fingerprint, b.fingerprint)

    def test_finding_fingerprint_tracks_identity_fields(self) -> None:
        base = self.finding()
        self.assertNotEqual(base.fingerprint, self.finding(rule_id="r.y").fingerprint)
        self.assertNotEqual(base.fingerprint, self.finding(key="other").fingerprint)
        self.assertNotEqual(base.fingerprint, self.finding(targets=["b.md"]).fingerprint)

    def test_proposal_fingerprint_follows_fix_shape_not_wording(self) -> None:
        f = self.finding()
        edits = [EditOp(path="a.md", op="create", text="hello")]
        a = Proposal(finding=f, title="Do it", edits=edits)
        b = Proposal(finding=f, title="Completely different wording",
                     edits=[EditOp(path="a.md", op="create", text="different body")])
        self.assertEqual(a.fingerprint, b.fingerprint,
                         "rewording a suggestion must not resurrect a dismissed one")
        c = Proposal(finding=f, title="Do it", edits=[EditOp(path="b.md", op="create")])
        self.assertNotEqual(a.fingerprint, c.fingerprint, "a different fix is a new proposal")

    def test_proposal_paths_are_deduped_in_order(self) -> None:
        f = self.finding()
        p = Proposal(finding=f, title="t", edits=[
            EditOp(path="b.md", op="append"), EditOp(path="a.md", op="append"),
            EditOp(path="b.md", op="append"),
        ])
        self.assertEqual(p.paths, ["b.md", "a.md"])


class TestCycleReport(unittest.TestCase):
    def test_serializes_and_counts(self) -> None:
        f = Finding(rule_id="r", title="t", key="k")
        p = Proposal(finding=f, title="p", edits=[EditOp(path="x.md", op="create")])
        r = CycleReport(cycle_id="c1", findings=[f], proposals=[p], applied=[p.fingerprint])
        r.ended_at = r.started_at + 2
        payload = json.loads(r.to_json())
        self.assertEqual(payload["counts"]["findings"], 1)
        self.assertEqual(payload["counts"]["applied"], 1)
        self.assertAlmostEqual(payload["duration_s"], 2, places=2)
        self.assertIn("proposals", payload)
        self.assertNotIn("proposals", json.loads(r.to_json(include_detail=False)))


class TestJournal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = Journal(Path(self.tmp.name) / "j")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _report(self, cycle_id: str, proposal: Proposal) -> CycleReport:
        r = CycleReport(cycle_id=cycle_id, findings=[proposal.finding], proposals=[proposal])
        r.ended_at = time.time()
        return r

    def _proposal(self) -> Proposal:
        f = Finding(rule_id="rule.a", title="t", key="k", targets=["a.md"])
        return Proposal(finding=f, title="p", edits=[EditOp(path="a.md", op="create")])

    def test_round_trip(self) -> None:
        p = self._proposal()
        self.assertTrue(self.journal.record_cycle(self._report("c1", p)))
        self.assertTrue(self.journal.record_outcome(
            Outcome(fingerprint=p.fingerprint, rule_id="rule.a", verdict="applied", cycle_id="c1")))
        self.assertEqual(len(self.journal.cycles()), 1)
        self.assertEqual(self.journal.applied(), {p.fingerprint})
        self.assertEqual(self.journal.verdict_counts("rule.a")["applied"], 1)

    def test_times_proposed_counts_cycles(self) -> None:
        p = self._proposal()
        for cycle in ("c1", "c2", "c3"):
            self.journal.record_cycle(self._report(cycle, p))
        self.assertEqual(self.journal.times_proposed(p.fingerprint), 3)
        self.assertEqual(self.journal.times_proposed("nope"), 0)

    def test_dismissed_and_reverted_are_distinct(self) -> None:
        self.journal.record_outcome(Outcome(fingerprint="f1", rule_id="r", verdict="dismissed"))
        self.journal.record_outcome(Outcome(fingerprint="f2", rule_id="r", verdict="reverted"))
        self.assertEqual(self.journal.dismissed(), {"f1"})
        self.assertEqual(self.journal.reverted(), {"f2"})

    def test_torn_final_line_is_skipped_not_fatal(self) -> None:
        """A run killed mid-write leaves a partial line; the next run must cope."""
        p = self._proposal()
        self.journal.record_cycle(self._report("c1", p))
        with self.journal.cycles_path.open("a", encoding="utf-8") as fh:
            fh.write('{"cycle_id": "c2", "ende')
        self.assertEqual(len(self.journal.cycles()), 1)

    def test_last_window_end_falls_back_to_lookback(self) -> None:
        before = time.time()
        got = self.journal.last_window_end(default_lookback_s=3600)
        self.assertAlmostEqual(got, before - 3600, delta=5)

    def test_last_window_end_uses_previous_cycle(self) -> None:
        p = self._proposal()
        report = self._report("c1", p)
        self.journal.record_cycle(report)
        self.assertAlmostEqual(self.journal.last_window_end(), report.ended_at, places=2)

    def test_unwritable_directory_does_not_raise(self) -> None:
        journal = Journal(Path(self.tmp.name) / "nested" / "j")
        blocker = Path(self.tmp.name) / "nested"
        blocker.write_text("not a directory")  # mkdir will fail against a file
        self.assertFalse(journal.record_outcome(Outcome(fingerprint="f", rule_id="r", verdict="applied")))
        self.assertEqual(journal.cycles(), [])


class TestDetectContext(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_text("hello", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_sessions_are_chronological(self) -> None:
        ctx = DetectContext(signals=[
            sig("third", ts=3, ordinal=2), sig("first", ts=1, ordinal=0), sig("second", ts=1, ordinal=1),
        ], root=self.root)
        self.assertEqual([s.text for s in ctx.sessions()["s"]], ["first", "second", "third"])

    def test_by_kind_filters_and_sorts(self) -> None:
        ctx = DetectContext(signals=[
            sig("cmd", kind=KIND_COMMAND, ts=2), sig("prompt", ts=1),
        ], root=self.root)
        self.assertEqual([s.text for s in ctx.by_kind(KIND_PROMPT)], ["prompt"])
        self.assertEqual(len(ctx.by_kind(KIND_PROMPT, KIND_COMMAND)), 2)

    def test_read_text_caches_and_tolerates_absence(self) -> None:
        ctx = DetectContext(signals=[], root=self.root)
        self.assertEqual(ctx.read_text("README.md"), "hello")
        (self.root / "README.md").write_text("changed", encoding="utf-8")
        self.assertEqual(ctx.read_text("README.md"), "hello", "second read must hit the cache")
        self.assertIsNone(ctx.read_text("nope.md"))

    def test_within_root_blocks_escape(self) -> None:
        ctx = DetectContext(signals=[], root=self.root)
        self.assertTrue(ctx.within_root(ctx.resolve("README.md")))
        self.assertFalse(ctx.within_root(Path("/etc/passwd")))


class TestDetectorPlumbing(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.added: list[str] = []

    def tearDown(self) -> None:
        for rule_id in self.added:
            detect_base._REGISTRY.pop(rule_id, None)
        self.tmp.cleanup()

    def _register(self, cls: type[Detector]) -> type[Detector]:
        self.added.append(cls.rule_id)
        return register(cls)

    def test_exception_in_detect_is_contained(self) -> None:
        class Boom(Detector):
            rule_id = "spine.boom"

            def detect(self, ctx):
                raise RuntimeError("rule exploded")

        self.assertEqual(Boom().run(DetectContext(signals=[], root=self.root)), [])

    def test_findings_are_capped_and_ordered(self) -> None:
        class Many(Detector):
            rule_id = "spine.many"
            max_findings = 2

            def detect(self, ctx):
                yield Finding(rule_id=self.rule_id, title="low", severity="low", key="1")
                yield Finding(rule_id=self.rule_id, title="crit", severity="critical", key="2")
                yield Finding(rule_id=self.rule_id, title="high", severity="high", key="3")

        found = Many().run(DetectContext(signals=[], root=self.root))
        self.assertEqual([f.title for f in found], ["crit", "high"])

    def test_proposals_escaping_the_root_are_rejected(self) -> None:
        class Escape(Detector):
            rule_id = "spine.escape"

            def detect(self, ctx):
                return ()

            def propose(self, finding, ctx):
                yield Proposal(finding=finding, title="abs",
                               edits=[EditOp(path="/etc/passwd", op="append")])
                yield Proposal(finding=finding, title="rel",
                               edits=[EditOp(path="../outside.md", op="create")])
                yield Proposal(finding=finding, title="ok",
                               edits=[EditOp(path="inside.md", op="create")])

        finding = Finding(rule_id="spine.escape", title="t", key="k")
        kept = Escape().run_propose(finding, DetectContext(signals=[], root=self.root))
        self.assertEqual([p.title for p in kept], ["ok"])

    def test_duplicate_rule_id_is_refused(self) -> None:
        class A(Detector):
            rule_id = "spine.dup"

            def detect(self, ctx):
                return ()

        self._register(A)

        with self.assertRaises(ValueError):
            class B(Detector):
                rule_id = "spine.dup"

                def detect(self, ctx):
                    return ()

            register(B)

    def test_build_detectors_honours_prefixes(self) -> None:
        class One(Detector):
            rule_id = "spinefam.one"

            def detect(self, ctx):
                return ()

        class Two(Detector):
            rule_id = "spinefam.two"

            def detect(self, ctx):
                return ()

        self._register(One)
        self._register(Two)
        built = build_detectors(enabled=["spinefam"])
        self.assertEqual({d.rule_id for d in built}, {"spinefam.one", "spinefam.two"})
        built = build_detectors(enabled=["spinefam"], disabled=["spinefam.two"])
        self.assertEqual({d.rule_id for d in built}, {"spinefam.one"})
        self.assertIn("spinefam.one", registry())

    def test_helpers(self) -> None:
        self.assertEqual(jaccard(set("abc"), set("abc")), 1.0)
        self.assertEqual(jaccard(set(), set("a")), 0.0)
        self.assertNotIn("the", normalize_phrase("the make test"))


class TestSourceBoundary(unittest.TestCase):
    """The three guarantees sources/base.run() makes on every source's behalf."""

    class Fake(SignalSource):
        key = "test:fake"

        def __init__(self, signals, explode=False):
            self._signals = signals
            self._explode = explode

        def collect(self, since, budget):
            if self._explode:
                raise RuntimeError("source died")
            yield from self._signals

    def test_redaction_is_applied_at_the_boundary(self) -> None:
        secret = "export GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123"
        result = self.Fake([sig(secret, kind=KIND_COMMAND)]).run(budget=Budget())
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz0123", result.signals[0].text)
        self.assertIn("redacted", result.signals[0].text)

    def test_redaction_is_recorded_as_metadata(self) -> None:
        """Whether redaction fired is the observer's to know, not a rule's to guess.

        A rule that infers it by matching the marker text cannot tell a redacted
        secret from a file that *defines* the markers, and reports a critical
        finding against the redaction module itself.
        """
        secret = "export GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123"
        fired = self.Fake([sig(secret, kind=KIND_COMMAND)]).run(budget=Budget())
        self.assertIs(fired.signals[0].metadata["redacted"], True)

        # Text that merely *contains* a marker was not redacted, and must say so.
        quoting = self.Fake([sig("we replace it with <redacted:github-token>")]).run(
            budget=Budget())
        self.assertIs(quoting.signals[0].metadata["redacted"], False)

    def test_source_key_is_stamped(self) -> None:
        s = Signal(kind=KIND_COMMAND, source="", text="ls")
        result = self.Fake([s]).run(budget=Budget())
        self.assertEqual(result.signals[0].source, "test:fake")

    def test_signal_cap_truncates(self) -> None:
        result = self.Fake([sig(f"c{i}") for i in range(50)]).run(
            budget=Budget(max_signals=5))
        self.assertEqual(len(result.signals), 5)
        self.assertTrue(result.truncated)

    def test_oversized_signal_is_trimmed(self) -> None:
        result = self.Fake([sig("x" * 5000)]).run(budget=Budget(max_chars_per_signal=100))
        self.assertLess(len(result.signals[0].text), 200)
        self.assertIn("truncated", result.signals[0].text)

    def test_since_filter(self) -> None:
        result = self.Fake([sig("old", ts=100), sig("new", ts=5000)]).run(since=1000, budget=Budget())
        self.assertEqual([s.text for s in result.signals], ["new"])

    def test_failure_is_contained(self) -> None:
        result = self.Fake([], explode=True).run(budget=Budget())
        self.assertEqual(result.signals, [])
        self.assertTrue(result.errors)
        self.assertIn("source died", result.errors[0])

    def test_budget_expiry(self) -> None:
        import time as _time

        # Backdate `started` rather than sleeping: the clock is monotonic, so this
        # is the only way to test expiry without making the suite slow.
        spent = Budget(wall_clock_s=1.0, started=_time.monotonic() - 60)
        self.assertTrue(spent.expired())
        self.assertFalse(Budget(wall_clock_s=300).expired())
        self.assertFalse(Budget(wall_clock_s=0).expired(), "non-positive disables the clock")
        self.assertFalse(Budget(wall_clock_s=-1).expired(), "negative disables it too")

    def test_child_budget_inherits_caps_but_resets_the_clock(self) -> None:
        import time as _time

        parent = Budget(max_signals=7, wall_clock_s=5.0, started=_time.monotonic() - 60)
        self.assertTrue(parent.expired())
        child = parent.child()
        self.assertEqual(child.max_signals, 7)
        self.assertFalse(child.expired(), "a child gets a fresh clock")


class TestSafeReadText(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_binary_and_missing_and_dir_return_empty(self) -> None:
        (self.root / "b.bin").write_bytes(b"\x00\x01\x02binary")
        self.assertEqual(safe_read_text(self.root / "b.bin"), "")
        self.assertEqual(safe_read_text(self.root / "missing"), "")
        self.assertEqual(safe_read_text(self.root), "")

    def test_text_is_read_and_capped(self) -> None:
        (self.root / "t.txt").write_text("hello", encoding="utf-8")
        self.assertEqual(safe_read_text(self.root / "t.txt"), "hello")
        (self.root / "big.txt").write_text("y" * 5000, encoding="utf-8")
        self.assertEqual(len(safe_read_text(self.root / "big.txt", max_bytes=100)), 100)


if __name__ == "__main__":
    unittest.main()


class TestEditConflictResolution(unittest.TestCase):
    """Two rules can want the same file. Only one may have it in a cycle.

    Without this, the second proposal fails its `create` precondition inside the
    actuator and the finding behind it disappears for the night with nothing
    said - the exact silent loss the nightly report exists to prevent.
    """

    def proposal(self, rule: str, path: str, op: str, key: str = "") -> Proposal:
        finding = Finding(rule_id=rule, title=rule, key=key or rule, targets=[path])
        return Proposal(finding=finding, title=f"{op} {path}",
                        edits=[EditOp(path=path, op=op, text="body", anchor="## H")])

    def resolve(self, proposals):
        from oodarag.reflect.decide.conflicts import resolve_edit_conflicts

        return resolve_edit_conflicts(proposals)

    def test_two_creates_on_one_path_keep_the_first(self) -> None:
        first = self.proposal("friction.repeated_instruction", "CLAUDE.md", "create")
        second = self.proposal("friction.correction", "CLAUDE.md", "create")
        kept, notes = self.resolve([first, second])
        self.assertEqual([p.fingerprint for p in kept], [first.fingerprint])
        self.assertEqual(len(notes), 1)
        self.assertIn(second.fingerprint[:8], notes[0])
        self.assertIn("friction.correction", notes[0])
        self.assertIn("next run", notes[0], "the note must say it is deferred, not dropped")

    def test_additive_ops_may_share_a_file(self) -> None:
        """ensure_section and append are idempotent, so several rules may contribute."""
        a = self.proposal("friction.repeated_instruction", "CLAUDE.md", "ensure_section")
        b = self.proposal("friction.correction", "CLAUDE.md", "ensure_section")
        kept, notes = self.resolve([a, b])
        self.assertEqual(len(kept), 2)
        self.assertEqual(notes, [])

    def test_a_create_blocks_a_later_additive_op_on_the_same_file(self) -> None:
        create = self.proposal("docs.broken_ref", "internal/PLAN.md", "create")
        append = self.proposal("docs.undocumented_entrypoint", "internal/PLAN.md", "append")
        kept, notes = self.resolve([create, append])
        self.assertEqual([p.fingerprint for p in kept], [create.fingerprint])
        self.assertEqual(len(notes), 1)

    def test_replace_is_exclusive_too(self) -> None:
        """The first replace may move the text the second is anchored to."""
        a = self.proposal("r.a", "README.md", "replace")
        b = self.proposal("r.b", "README.md", "replace")
        kept, _ = self.resolve([a, b])
        self.assertEqual(len(kept), 1)

    def test_different_files_never_conflict(self) -> None:
        kept, notes = self.resolve([
            self.proposal("r.a", "a.md", "create"),
            self.proposal("r.b", "b.md", "create"),
        ])
        self.assertEqual(len(kept), 2)
        self.assertEqual(notes, [])

    def test_order_decides_the_winner(self) -> None:
        """The loop hands proposals over in score order, so first claim wins."""
        low = self.proposal("r.low", "CLAUDE.md", "create")
        high = self.proposal("r.high", "CLAUDE.md", "create")
        kept, _ = self.resolve([high, low])
        self.assertEqual([p.finding.rule_id for p in kept], ["r.high"])
