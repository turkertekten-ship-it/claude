"""End-to-end tests for the nightly cycle.

Everything else in the suite tests one stage in isolation. This file is the one
that would catch the failures that actually matter in production: a cycle that
writes when it was told to be a dry run, a second run that undoes the first
one's work, a revert that does not restore, or - worst of all - a loop that
reads the developer's real home directory because a default leaked through.

Every test here builds its own world in a temp directory and points every
source at it explicitly. If one of these ever touches `~`, that is the bug.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from oodarag.reflect.act.queue import ReviewQueue
from oodarag.reflect.decide.priors import RulePriors
from oodarag.reflect.journal import Journal
from oodarag.reflect.loop import CycleLock, ReflectConfig, ReflectLoop
from oodarag.reflect.models import CycleReport, Outcome

README = """# demo project

Setup lives in [the plan](internal/PLAN.md), which nobody has written yet.

## Quick start

    make test
"""

MAKEFILE = """.PHONY: test lint ship

test: ## Run the tests
\techo test

ship: ## Publish a release
\techo ship
"""

MODULE = '''"""A module with no test file anywhere."""


def compute(value):
    # TODO: handle the empty case
    return value * 2
'''


def chat_session(session_id: str, prompts: list[str], base_ts: float) -> str:
    records = []
    for index, text in enumerate(prompts):
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(base_ts + index * 60))
        records.append({
            "type": "user", "sessionId": session_id, "cwd": "/w",
            "timestamp": stamp, "message": {"role": "user", "content": text},
        })
        records.append({
            "type": "assistant", "sessionId": session_id,
            "timestamp": stamp, "message": {"role": "assistant", "content": "ok"},
        })
    return "\n".join(json.dumps(r) for r in records)


class LoopTestCase(unittest.TestCase):
    """A self-contained world: a workspace, plus chat and shell logs outside it."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "workspace"
        self.outside = base / "outside"
        (self.root / "src" / "pkg").mkdir(parents=True)
        (self.outside / "chat").mkdir(parents=True)

        (self.root / "README.md").write_text(README, encoding="utf-8")
        (self.root / "Makefile").write_text(MAKEFILE, encoding="utf-8")
        (self.root / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        (self.root / "src" / "pkg" / "engine.py").write_text(MODULE, encoding="utf-8")

        now = time.time()
        # The same standing instruction, on three different days.
        for day in range(3):
            (self.outside / "chat" / f"sess-{day}.jsonl").write_text(
                chat_session(
                    f"sess-{day}",
                    ["always run make test before you commit",
                     "no, I meant run the linter too"],
                    now - (day + 1) * 3600,
                ),
                encoding="utf-8",
            )

        self.history = self.outside / ".zsh_history"
        lines = []
        for day in range(3):
            stamp = int(now - (day + 1) * 86400)
            for _ in range(2):
                lines.append(f": {stamp}:0;python -m pytest tests/ --maxfail=1 -q")
        self.history.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def config(self, *, dry_run: bool = True, **kwargs) -> ReflectConfig:
        params = dict(
            root=self.root,
            dry_run=dry_run,
            chat_roots=[self.outside / "chat"],
            shell_history_paths=[self.history],
        )
        params.update(kwargs)
        return ReflectConfig(**params)


class TestObserveAndOrient(LoopTestCase):
    def test_all_four_sources_contribute(self) -> None:
        loop = ReflectLoop(self.config())
        report = loop.run_cycle(since=0)
        self.assertGreater(report.signals, 0)
        self.assertIn("chat:transcripts", report.per_source)
        self.assertIn("shell:history", report.per_source)
        self.assertIn("workspace:files", report.per_source)
        self.assertGreater(report.per_source["chat:transcripts"], 0)
        self.assertGreater(report.per_source["workspace:files"], 0)

    def test_it_finds_the_readmes_broken_link(self) -> None:
        report = ReflectLoop(self.config()).run_cycle(since=0)
        broken = [f for f in report.findings if f.rule_id == "docs.broken_ref"]
        self.assertTrue(broken, "README links to internal/PLAN.md, which does not exist")
        self.assertTrue(any("internal/PLAN.md" in t for f in broken for t in f.targets))
        self.assertTrue(all(f.evidence for f in report.findings),
                        "a finding with no evidence is an opinion")

    def test_findings_carry_stable_fingerprints(self) -> None:
        first = ReflectLoop(self.config()).run_cycle(since=0)
        second = ReflectLoop(self.config()).run_cycle(since=0)
        self.assertEqual(
            sorted(f.fingerprint for f in first.findings),
            sorted(f.fingerprint for f in second.findings),
            "the journal correlates nights by fingerprint; they must not drift",
        )


class TestDryRun(LoopTestCase):
    def test_dry_run_changes_nothing_on_disk(self) -> None:
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = ReflectLoop(self.config(dry_run=True)).run_cycle(since=0)
        after = {p: p.read_bytes() for p in self.root.rglob("*")
                 if p.is_file() and ".oodarag" not in p.parts}
        self.assertEqual(before, after, "a dry run must not touch the workspace")
        self.assertTrue(report.dry_run)
        self.assertFalse((self.root / "internal" / "PLAN.md").exists())

    def test_dry_run_does_not_teach_the_priors(self) -> None:
        """A dry run establishes nothing, so recording outcomes would poison learning."""
        config = self.config(dry_run=True)
        ReflectLoop(config).run_cycle(since=0)
        self.assertEqual(Journal(config.journal_dir).outcomes(), [])


class TestApply(LoopTestCase):
    def test_apply_creates_the_missing_file(self) -> None:
        config = self.config(dry_run=False)
        report = ReflectLoop(config).run_cycle(since=0)
        self.assertTrue(report.applied, "at least the safe doc stub should have applied")
        self.assertTrue((self.root / "internal" / "PLAN.md").exists())
        body = (self.root / "internal" / "PLAN.md").read_text("utf-8")
        self.assertIn("README", body, "the stub should name what referenced it")

    def test_source_files_are_never_machine_edited(self) -> None:
        original = (self.root / "src" / "pkg" / "engine.py").read_bytes()
        ReflectLoop(self.config(dry_run=False)).run_cycle(since=0)
        self.assertEqual((self.root / "src" / "pkg" / "engine.py").read_bytes(), original)

    def test_apply_is_idempotent(self) -> None:
        config = self.config(dry_run=False)
        ReflectLoop(config).run_cycle(since=0)
        snapshot = {
            str(p.relative_to(self.root)): p.read_bytes()
            for p in self.root.rglob("*")
            if p.is_file() and ".oodarag" not in p.parts
        }
        ReflectLoop(config).run_cycle(since=0)
        again = {
            str(p.relative_to(self.root)): p.read_bytes()
            for p in self.root.rglob("*")
            if p.is_file() and ".oodarag" not in p.parts
        }
        self.assertEqual(snapshot, again, "running twice at 22:30 must change nothing")

    def test_revert_undoes_the_cycle(self) -> None:
        config = self.config(dry_run=False)
        loop = ReflectLoop(config)
        report = loop.run_cycle(since=0)
        created = self.root / "internal" / "PLAN.md"
        self.assertTrue(created.exists())
        loop.revert(report.cycle_id)
        self.assertFalse(created.exists(), "a created file must be removed, not blanked")

    def test_revert_is_recorded_so_the_rule_is_penalised(self) -> None:
        config = self.config(dry_run=False)
        loop = ReflectLoop(config)
        report = loop.run_cycle(since=0)
        loop.revert(report.cycle_id)
        verdicts = {o.verdict for o in Journal(config.journal_dir).outcomes()}
        self.assertIn("reverted", verdicts)


class TestJournalAndLearning(LoopTestCase):
    def test_cycle_is_journalled_and_the_window_advances(self) -> None:
        config = self.config()
        loop = ReflectLoop(config)
        report = loop.run_cycle(since=0)
        journal = Journal(config.journal_dir)
        self.assertEqual(len(journal.cycles()), 1)
        self.assertAlmostEqual(journal.last_window_end(), report.ended_at, places=2)

    def test_dismissed_proposals_are_never_proposed_again(self) -> None:
        config = self.config()
        report = ReflectLoop(config).run_cycle(since=0)
        self.assertTrue(report.proposals, "need a proposal to dismiss")
        victim = report.proposals[0]
        Journal(config.journal_dir).record_outcome(
            Outcome(fingerprint=victim.fingerprint,
                    rule_id=victim.finding.rule_id, verdict="dismissed"))

        again = ReflectLoop(config).run_cycle(since=0)
        live = {p.fingerprint for p in again.proposals}
        self.assertNotIn(victim.fingerprint, live, "a dismissal must stick")
        self.assertIn(victim.fingerprint, again.suppressed)

    def test_queued_proposals_reach_the_review_queue(self) -> None:
        config = self.config()
        report = ReflectLoop(config).run_cycle(since=0)
        queue = ReviewQueue(config.queue_path)
        if report.queued:
            self.assertEqual({e["fingerprint"] for e in queue.pending()} & set(report.queued),
                             set(report.queued))


class TestReport(LoopTestCase):
    def test_report_is_written_and_latest_refreshed(self) -> None:
        config = self.config()
        report = ReflectLoop(config).run_cycle(since=0)
        self.assertTrue(report.report_path, "the cycle must say where it wrote the report")
        written = Path(report.report_path)
        self.assertTrue(written.exists())
        latest = config.reports_dir / "latest.md"
        self.assertTrue(latest.exists())
        self.assertEqual(latest.read_text("utf-8"), written.read_text("utf-8"))
        self.assertIn("#", written.read_text("utf-8"))


class TestSafety(LoopTestCase):
    def test_a_second_cycle_cannot_run_concurrently(self) -> None:
        config = self.config(dry_run=False)
        with CycleLock(config.lock_path):
            report = ReflectLoop(config).run_cycle(since=0)
        self.assertEqual(report.applied, [])
        self.assertTrue(any("already running" in e for e in report.errors))

    def test_a_stale_lock_does_not_block_forever(self) -> None:
        config = self.config()
        config.lock_path.parent.mkdir(parents=True, exist_ok=True)
        config.lock_path.write_text("999999")  # a pid that is not alive
        with CycleLock(config.lock_path) as lock:
            self.assertTrue(lock.acquired, "a dead owner's lock must be reclaimed")

    def test_nothing_outside_the_root_is_ever_written(self) -> None:
        before = sorted(p.name for p in self.outside.rglob("*"))
        ReflectLoop(self.config(dry_run=False)).run_cycle(since=0)
        self.assertEqual(sorted(p.name for p in self.outside.rglob("*")), before)

    def test_max_edits_budget_is_respected(self) -> None:
        config = self.config(dry_run=False)
        config.policy.max_auto_edits = 1
        report = ReflectLoop(config).run_cycle(since=0)
        self.assertLessEqual(len(report.applied), 1)


if __name__ == "__main__":
    unittest.main()


class TestVerdictAccounting(LoopTestCase):
    """What the journal learns from a night, and what it must not learn.

    Both bugs pinned here are silent and slow: they do not break a run, they
    corrupt the priors over weeks until the loop distrusts its own best rules.
    """

    def _outcomes(self, config):
        return Journal(config.journal_dir).outcomes()

    def test_a_permanently_satisfied_proposal_is_not_a_failure(self) -> None:
        """`ensure_section` is idempotent, so a stuck convention reports
        applied=False forever. Counting that as failure would punish exactly the
        rules whose suggestions worked."""
        config = self.config(dry_run=False)
        ReflectLoop(config).run_cycle(since=0)
        first = self._outcomes(config)
        self.assertTrue(first, "the first night should have learned something")

        # Second and third nights: the same findings, already satisfied on disk.
        ReflectLoop(config).run_cycle(since=0)
        ReflectLoop(config).run_cycle(since=0)
        failures = [o for o in self._outcomes(config) if o.verdict == "failed"]
        self.assertEqual(
            failures, [],
            f"re-running must not manufacture failures: {[o.rule_id for o in failures]}",
        )

    def test_a_rule_that_keeps_working_does_not_lose_confidence(self) -> None:
        config = self.config(dry_run=False)
        loop = ReflectLoop(config)
        loop.run_cycle(since=0)
        applied = [o for o in self._outcomes(config) if o.verdict == "applied"]
        self.assertTrue(applied, "need an applied proposal to track")
        rule = applied[0].rule_id

        before = RulePriors(Journal(config.journal_dir)).confidence(rule)
        for _ in range(3):
            ReflectLoop(config).run_cycle(since=0)
        after = RulePriors(Journal(config.journal_dir)).confidence(rule)
        # Not assertGreaterEqual: the posterior decays with elapsed wall-clock by
        # design, so three runs a millisecond apart lose ~1e-9. What must not
        # happen is a *material* fall, which is what a manufactured failure per
        # night would cause.
        self.assertAlmostEqual(
            after, before, places=4,
            msg="a rule whose edit is still in place must not decay for repeating",
        )
        self.assertGreater(after, 0.6, "a rule with a clean record should stay trusted")

    def test_results_are_attributed_to_the_proposal_that_caused_them(self) -> None:
        """Two additive proposals may share a file; a {path: result} lookup
        would credit one of them with the other's outcome."""
        from oodarag.reflect.decide.policy import Decision
        from oodarag.reflect.models import EditOp, Finding, Proposal

        config = self.config(dry_run=False)
        loop = ReflectLoop(config)
        (self.root / "CLAUDE.md").write_text(
            "# Memory\n\n## Conventions\n\n- Already written down.\n", encoding="utf-8")

        def proposal(rule: str, body: str) -> Proposal:
            return Proposal(
                finding=Finding(rule_id=rule, title=rule, key=rule),
                title=rule, risk="safe",
                edits=[EditOp(path="CLAUDE.md", op="ensure_section",
                              anchor="## Conventions", text=body)],
            )

        stale = proposal("rule.stale", "- Already written down.")
        fresh = proposal("rule.fresh", "- Brand new thing.")
        decision = Decision(apply=[stale, fresh])
        cycle = CycleReport(cycle_id="attrib", dry_run=False)
        applied = loop.act(decision, "attrib")
        cycle.ended_at = time.time()
        loop.learn(cycle, decision, applied)

        verdicts = {o.rule_id: o.verdict for o in self._outcomes(config)}
        self.assertNotIn("rule.stale", verdicts, "an already-satisfied op teaches nothing")
        self.assertEqual(verdicts.get("rule.fresh"), "applied")
        self.assertIn("Brand new thing.", (self.root / "CLAUDE.md").read_text("utf-8"))


class TestQueueRetirement(LoopTestCase):
    """A queue that never retires anything can never reach empty.

    Fixing a finding by hand used to leave its proposal queued for ever, so the
    user was asked to dismiss work they had already done - and "nothing is open"
    was unreachable by construction.
    """

    def pending_rules(self, config) -> list[str]:
        return [
            (e.get("proposal") or {}).get("finding", {}).get("rule_id", "")
            for e in ReviewQueue(config.queue_path).pending()
        ]

    def test_a_finding_fixed_by_hand_retires_its_proposal(self) -> None:
        # `docs.undocumented_entrypoint` is review-tier, so it reaches the queue;
        # `docs.broken_ref` is safe-tier and is applied instead of queued.
        config = self.config()
        ReflectLoop(config).run_cycle(since=0)
        self.assertIn("docs.undocumented_entrypoint", self.pending_rules(config),
                      "the Makefile has a target the README never mentions")

        # Fix it the way a person would, outside the loop entirely.
        readme = self.root / "README.md"
        readme.write_text(readme.read_text("utf-8") + "\n\nRun `make ship` to publish.\n",
                          encoding="utf-8")

        ReflectLoop(config).run_cycle(since=0)
        self.assertNotIn("docs.undocumented_entrypoint", self.pending_rules(config),
                         "a resolved finding must stop being open")

    def test_retirement_is_not_a_verdict_on_the_rule(self) -> None:
        """Nothing here knows whether this rule's proposal is why it got fixed."""
        config = self.config()
        loop = ReflectLoop(config)
        loop.run_cycle(since=0)
        readme = self.root / "README.md"
        readme.write_text(readme.read_text("utf-8") + "\n\nRun `make ship` to publish.\n",
                          encoding="utf-8")
        loop.run_cycle(since=0)

        journal = Journal(config.journal_dir)
        verdicts = [o.verdict for o in journal.outcomes(rule_id="docs.undocumented_entrypoint")]
        self.assertNotIn("dismissed", verdicts, "retiring is not declining")
        self.assertNotIn("applied", verdicts, "and it is not credit either")

    def test_event_based_rules_are_never_retired_this_way(self) -> None:
        """A friction finding is absent on any quiet day; retiring it would
        discard a real suggestion the first time the user did not repeat
        themselves."""
        from oodarag.reflect.detect.base import registry

        for rule_id, cls in registry().items():
            if rule_id.startswith(("friction.", "terminal.")):
                with self.subTest(rule=rule_id):
                    self.assertNotEqual(
                        set(cls.consumes), {"file"},
                        "an event rule must not look like a state rule",
                    )
