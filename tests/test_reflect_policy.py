"""Tests for the Decide stage: what the loop has learned, and what it may do.

These are the tests that stand between the user and an unattended process with
write access to their files. Two failures matter more than the rest and both are
silent: a budget that is off by one is a night that edits more than the user
agreed to, and a rejection with no note is work that vanishes with no way to
find out why. Every gate below is therefore asserted twice - once that it
blocked, once that it said so.

Nothing here reads a real journal or a real repository; every fixture is built
in a temp directory.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oodarag.reflect.decide.policy import (
    DEFAULT_PROTECTED_PATHS,
    PolicyConfig,
    PolicyEngine,
    path_is_protected,
)
from oodarag.reflect.decide.priors import RulePriors
from oodarag.reflect.journal import Journal
from oodarag.reflect.models import CycleReport, EditOp, Finding, Outcome, Proposal

DAY = 86_400.0
NOW = 1_800_000_000.0


def make_proposal(
    rule_id: str = "rule.one",
    *,
    key: str = "k",
    risk: str = "safe",
    paths: tuple[str, ...] = ("notes.md",),
    text: str = "hello",
    severity: str = "high",
    confidence: float = 0.9,
    impact: float = 0.9,
    effort: float = 0.0,
) -> Proposal:
    finding = Finding(
        rule_id=rule_id,
        title=f"finding {key}",
        severity=severity,
        confidence=confidence,
        key=key,
        targets=list(paths),
    )
    return Proposal(
        finding=finding,
        title=f"fix {key}",
        edits=[EditOp(path=p, op="append", text=text) for p in paths],
        risk=risk,
        impact=impact,
        effort=effort,
    )


def note_for(notes: list[str], proposal: Proposal) -> str | None:
    tag = proposal.fingerprint[:8]
    return next((n for n in notes if tag in n), None)


class PriorsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.journal = Journal(self.dir / "journal")

    def record(self, rule_id: str, verdict: str, *, fingerprint: str = "", age_days: float = 0.0):
        self.journal.record_outcome(
            Outcome(
                fingerprint=fingerprint or f"{rule_id}:{verdict}",
                rule_id=rule_id,
                verdict=verdict,
                ts=NOW - age_days * DAY,
            )
        )

    def priors(self, **kwargs) -> RulePriors:
        kwargs.setdefault("now", NOW)
        return RulePriors(self.journal, **kwargs)


class TestRulePriors(PriorsTestCase):
    def test_unseen_rule_sits_exactly_at_one_half(self) -> None:
        self.assertAlmostEqual(self.priors().confidence("never.seen"), 0.5)

    def test_missing_journal_is_a_legitimate_first_night(self) -> None:
        priors = RulePriors(Journal(self.dir / "does" / "not" / "exist"), now=NOW)
        self.assertAlmostEqual(priors.confidence("rule.one"), 0.5)
        self.assertFalse(priors.is_suppressed("anything"))
        self.assertAlmostEqual(priors.nag_factor("anything"), 1.0)

    def test_accepting_raises_and_declining_lowers(self) -> None:
        self.record("rule.good", "applied")
        self.record("rule.bad", "dismissed")
        priors = self.priors()
        self.assertGreater(priors.confidence("rule.good"), 0.5)
        self.assertLess(priors.confidence("rule.bad"), 0.5)

    def test_a_reverted_edit_costs_more_than_a_dismissed_idea(self) -> None:
        # The ordering is the whole point of the weights: being wrong about a
        # file the loop already changed is worse than being wrong out loud.
        self.record("rule.dismissed", "dismissed")
        self.record("rule.failed", "failed")
        self.record("rule.reverted", "reverted")
        priors = self.priors()
        reverted = priors.confidence("rule.reverted")
        failed = priors.confidence("rule.failed")
        dismissed = priors.confidence("rule.dismissed")
        self.assertLess(reverted, failed)
        self.assertLess(failed, dismissed)
        self.assertLess(dismissed, 0.5)

    def test_deferred_teaches_nothing(self) -> None:
        self.record("rule.waiting", "deferred")
        self.assertAlmostEqual(self.priors().confidence("rule.waiting"), 0.5)

    def test_old_verdicts_decay_towards_neutral(self) -> None:
        self.record("rule.recent", "dismissed", age_days=0.0)
        self.record("rule.ancient", "dismissed", age_days=300.0)
        priors = self.priors(half_life_days=30.0)
        self.assertLess(priors.confidence("rule.recent"), 0.4)
        self.assertAlmostEqual(priors.confidence("rule.ancient"), 0.5, places=2)
        self.assertLess(priors.confidence("rule.recent"), priors.confidence("rule.ancient"))

    def test_a_rule_that_reformed_is_judged_on_recent_behaviour(self) -> None:
        for i in range(4):
            self.record("rule.reformed", "dismissed", fingerprint=f"old{i}", age_days=200.0 + i)
        for i in range(2):
            self.record("rule.reformed", "applied", fingerprint=f"new{i}", age_days=1.0)
        priors = self.priors(half_life_days=30.0)
        self.assertGreater(priors.confidence("rule.reformed"), 0.5)

    def test_decay_can_be_switched_off(self) -> None:
        self.record("rule.old", "dismissed", age_days=1000.0)
        undecayed = self.priors(half_life_days=0.0)
        self.assertAlmostEqual(undecayed.confidence("rule.old"), 1.0 / 3.0)

    def test_dismissal_suppresses_that_exact_proposal_only(self) -> None:
        self.record("rule.one", "dismissed", fingerprint="fp-dismissed")
        self.record("rule.one", "applied", fingerprint="fp-applied")
        priors = self.priors()
        self.assertTrue(priors.is_suppressed("fp-dismissed"))
        self.assertFalse(priors.is_suppressed("fp-applied"))
        self.assertFalse(priors.is_suppressed("fp-unknown"))
        self.assertFalse(priors.is_suppressed(""))
        self.assertEqual(priors.suppressed_count(), 1)

    def test_nag_grows_with_repetition_and_stops_at_the_cap(self) -> None:
        proposal = make_proposal(key="nagged")
        seen: list[float] = []
        for i in range(9):
            priors = self.priors()
            seen.append(priors.nag_factor(proposal.fingerprint))
            report = CycleReport(cycle_id=f"c{i}")
            report.proposals = [proposal]
            self.journal.record_cycle(report)
        self.assertAlmostEqual(seen[0], 1.0)
        self.assertLessEqual(seen[0], seen[1])
        self.assertEqual(seen, sorted(seen), "nagging must never go backwards")
        self.assertAlmostEqual(max(seen), 1.5)
        self.assertTrue(all(f <= 1.5 for f in seen), "the escalation must be bounded")
        # Still capped many nights later - persistence must not outrank merit.
        priors = self.priors()
        self.assertAlmostEqual(priors.nag_factor(proposal.fingerprint), 1.5)

    def test_nag_cap_is_configurable(self) -> None:
        proposal = make_proposal(key="nagged")
        for i in range(20):
            report = CycleReport(cycle_id=f"c{i}")
            report.proposals = [proposal]
            self.journal.record_cycle(report)
        self.assertAlmostEqual(self.priors(max_nag=2.0).nag_factor(proposal.fingerprint), 2.0)
        # A cap below 1.0 would *demote* a repeated proposal; clamp it instead.
        self.assertAlmostEqual(self.priors(max_nag=0.1).nag_factor(proposal.fingerprint), 1.0)

    def test_explain_carries_both_the_weights_and_the_raw_counts(self) -> None:
        self.record("rule.one", "applied", fingerprint="a")
        self.record("rule.one", "reverted", fingerprint="b")
        detail = self.priors().explain("rule.one")
        self.assertEqual(detail["rule_id"], "rule.one")
        self.assertEqual(detail["verdicts"], {"applied": 1, "reverted": 1})
        self.assertEqual(detail["observations"], 2)
        self.assertAlmostEqual(detail["successes"], 1.0, places=3)
        self.assertAlmostEqual(detail["failures"], 2.0, places=3)
        self.assertAlmostEqual(detail["confidence"], 2.0 / 5.0, places=3)
        self.assertEqual(self.priors().explain("never.seen")["observations"], 0)

    def test_a_mangled_journal_does_not_abort_the_night(self) -> None:
        path = self.dir / "journal" / "outcomes.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "not json at all",
                    '{"fingerprint": "ok", "rule_id": "rule.one", "verdict": "applied"}',
                    '{"verdict": "applied"}',  # no fingerprint
                    '{"fingerprint": "x", "rule_id": "rule.one", "verdict": "\\u0000weird"}',
                    '{"fingerprint": "y", "rule_id": "rule.one", "verdict": "applied",'
                    ' "ts": "yesterday"}',
                    '{"fingerprint": "z", "rule_id": "", "verdict": "reverted"}',
                    '{"fingerprint": "t", "rule_id": "rule.one", "verdict": "applied", "ts": -5}',
                    '{"fingerprint": "f", "rule_id": "rule.one", "verdict": "applied",',
                ]
            ),
            encoding="utf-8",
        )
        priors = self.priors()
        self.assertGreater(priors.confidence("rule.one"), 0.5)
        self.assertFalse(priors.is_suppressed("z"))
        self.assertAlmostEqual(priors.confidence("other.rule"), 0.5)

    def test_a_future_timestamp_cannot_amplify_a_verdict(self) -> None:
        self.record("rule.one", "dismissed", age_days=-400.0)  # clock skew
        priors = self.priors(half_life_days=30.0)
        self.assertAlmostEqual(priors.confidence("rule.one"), 1.0 / 3.0)


class PolicyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.journal = Journal(self.dir / "journal")

    def engine(self, **overrides) -> PolicyEngine:
        return PolicyEngine(PolicyConfig(**overrides), RulePriors(self.journal, now=NOW))


class TestScoring(PolicyTestCase):
    def test_score_parts_show_the_arithmetic(self) -> None:
        proposal = make_proposal(severity="high", confidence=0.8, impact=0.5, effort=1.0)
        score = self.engine().score(proposal)
        parts = proposal.score_parts
        self.assertAlmostEqual(parts["severity"], 0.75)
        self.assertAlmostEqual(parts["confidence"], 0.8)
        self.assertAlmostEqual(parts["prior"], 0.5)
        self.assertAlmostEqual(parts["impact"], 0.5)
        self.assertAlmostEqual(parts["nag"], 1.0)
        self.assertAlmostEqual(score, 0.75 * 0.8 * 0.5 * 0.5 / 2.0)
        self.assertAlmostEqual(proposal.score, score)

    def test_any_zero_factor_kills_the_proposal(self) -> None:
        engine = self.engine()
        self.assertAlmostEqual(engine.score(make_proposal(impact=0.0)), 0.0)
        self.assertAlmostEqual(engine.score(make_proposal(confidence=0.0)), 0.0)

    def test_hostile_factors_are_clamped_rather_than_trusted(self) -> None:
        # A detector emitting confidence=5.0 must not be able to outrank
        # everything else by arithmetic alone.
        wild = make_proposal(confidence=5.0, impact=-3.0, effort=-9.0, severity="banana")
        sane = make_proposal(key="sane", confidence=1.0, impact=1.0, effort=0.0)
        engine = self.engine()
        self.assertAlmostEqual(engine.score(wild), 0.0)
        self.assertGreater(engine.score(sane), engine.score(wild))
        for value in wild.score_parts.values():
            self.assertGreaterEqual(value, 0.0)

    def test_severity_orders_otherwise_identical_proposals(self) -> None:
        engine = self.engine()
        low = engine.score(make_proposal(key="a", severity="low"))
        critical = engine.score(make_proposal(key="b", severity="critical"))
        self.assertGreater(critical, low)

    def test_a_distrusted_rule_scores_below_a_trusted_one(self) -> None:
        for i in range(3):
            self.journal.record_outcome(
                Outcome(fingerprint=f"d{i}", rule_id="rule.bad", verdict="reverted", ts=NOW)
            )
        self.journal.record_outcome(
            Outcome(fingerprint="g", rule_id="rule.good", verdict="applied", ts=NOW)
        )
        engine = self.engine()
        bad = engine.score(make_proposal("rule.bad", key="a"))
        good = engine.score(make_proposal("rule.good", key="b"))
        self.assertLess(bad, good)


class TestDecide(PolicyTestCase):
    def test_safe_high_scoring_proposals_are_applied(self) -> None:
        proposal = make_proposal()
        decision = self.engine().decide([proposal], tree_clean=True)
        self.assertEqual(decision.apply, [proposal])
        self.assertEqual(decision.queue, [])
        self.assertEqual(decision.suppressed, [])

    def test_apply_list_is_in_descending_score_order(self) -> None:
        low = make_proposal(key="low", severity="low", impact=0.4)
        high = make_proposal(key="high", severity="critical", impact=1.0)
        mid = make_proposal(key="mid", severity="medium", impact=0.8)
        # min_score off: this test is about order alone, not about the floor.
        decision = self.engine(max_auto_edits=10, min_score=0.0).decide(
            [low, high, mid], tree_clean=True
        )
        self.assertEqual([p.finding.key for p in decision.apply], ["high", "mid", "low"])

    def test_risk_above_the_allowed_tier_is_queued_not_applied(self) -> None:
        review = make_proposal(key="r", risk="review")
        manual = make_proposal(key="m", risk="manual")
        safe = make_proposal(key="s", risk="safe")
        decision = self.engine().decide([review, manual, safe], tree_clean=True)
        self.assertEqual(decision.apply, [safe])
        self.assertEqual({p.finding.key for p in decision.queue}, {"r", "m"})
        for proposal in (review, manual):
            note = note_for(decision.notes, proposal)
            self.assertIsNotNone(note)
            self.assertIn("risk tier", note)

    def test_raising_the_allowed_tier_admits_review_proposals(self) -> None:
        review = make_proposal(key="r", risk="review")
        decision = self.engine(allow_risk="review").decide([review], tree_clean=True)
        self.assertEqual(decision.apply, [review])

    def test_a_proposal_below_min_score_is_queued_with_its_number(self) -> None:
        weak = make_proposal(key="weak", severity="low", confidence=0.3, impact=0.3)
        decision = self.engine().decide([weak], tree_clean=True)
        self.assertEqual(decision.apply, [])
        self.assertEqual(decision.queue, [weak])
        self.assertIn("attention floor", note_for(decision.notes, weak) or "")

    def test_a_rule_with_a_bad_record_is_not_trusted_to_act(self) -> None:
        for i in range(4):
            self.journal.record_outcome(
                Outcome(fingerprint=f"r{i}", rule_id="rule.bad", verdict="reverted", ts=NOW)
            )
        proposal = make_proposal("rule.bad")
        # min_score off, so the only thing that can stop it is the earned prior.
        decision = self.engine(min_score=0.0).decide([proposal], tree_clean=True)
        self.assertEqual(decision.apply, [])
        self.assertIn("earned confidence", note_for(decision.notes, proposal) or "")

    def test_source_code_is_never_machine_edited(self) -> None:
        code = make_proposal(key="code", paths=("src/oodarag/thing.py",))
        build = make_proposal(key="build", paths=("Makefile",))
        lock = make_proposal(key="lock", paths=("deps/uv.lock",))
        git = make_proposal(key="git", paths=(".git/config",))
        docs = make_proposal(key="docs", paths=("docs/notes.md",))
        decision = self.engine().decide([code, build, lock, git, docs], tree_clean=True)
        self.assertEqual([p.finding.key for p in decision.apply], ["docs"])
        for proposal in (code, build, lock, git):
            self.assertIn("protected path", note_for(decision.notes, proposal) or "")

    def test_a_protected_path_anywhere_in_the_proposal_blocks_it(self) -> None:
        mixed = make_proposal(key="mixed", paths=("README.md", "setup.py"))
        decision = self.engine().decide([mixed], tree_clean=True)
        self.assertEqual(decision.apply, [])
        self.assertIn("protected path", note_for(decision.notes, mixed) or "")

    def test_protected_globs_match_nested_paths(self) -> None:
        self.assertTrue(path_is_protected("a/b/c.py", DEFAULT_PROTECTED_PATHS))
        self.assertTrue(path_is_protected(".git/refs/heads/main", DEFAULT_PROTECTED_PATHS))
        self.assertFalse(path_is_protected("docs/python.md", DEFAULT_PROTECTED_PATHS))

    def test_dismissed_proposals_are_never_proposed_again(self) -> None:
        proposal = make_proposal(key="nope")
        self.journal.record_outcome(
            Outcome(fingerprint=proposal.fingerprint, rule_id="rule.one", verdict="dismissed")
        )
        other = make_proposal(key="fine")
        decision = self.engine().decide([proposal, other], tree_clean=True)
        self.assertEqual(decision.suppressed, [proposal])
        self.assertEqual(decision.apply, [other])
        self.assertNotIn(proposal, decision.queue)
        self.assertIn("dismissed this before", note_for(decision.notes, proposal) or "")

    def test_an_observation_only_proposal_is_never_applied(self) -> None:
        bare = make_proposal(key="bare")
        bare.edits = []
        decision = self.engine().decide([bare], tree_clean=True)
        self.assertEqual(decision.apply, [])
        self.assertIn("no edits", note_for(decision.notes, bare) or "")

    def test_an_empty_night_decides_nothing_and_says_nothing(self) -> None:
        decision = self.engine().decide([], tree_clean=True)
        self.assertEqual((decision.apply, decision.queue, decision.suppressed), ([], [], []))
        self.assertEqual(decision.notes, [])


class TestBudgets(PolicyTestCase):
    def many(self, count: int, **kwargs) -> list[Proposal]:
        return [make_proposal(key=f"p{i}", paths=(f"n{i}.md",), **kwargs) for i in range(count)]

    def test_edit_budget_cuts_off_at_exactly_the_limit(self) -> None:
        proposals = self.many(5)
        decision = self.engine(max_auto_edits=3, max_files_touched=99).decide(
            proposals, tree_clean=True
        )
        self.assertEqual(len(decision.apply), 3)
        self.assertEqual(len(decision.queue), 2)
        for proposal in decision.queue:
            self.assertIn("automatic edits is spent", note_for(decision.notes, proposal) or "")

    def test_file_budget_counts_distinct_files(self) -> None:
        proposals = self.many(4)
        decision = self.engine(max_auto_edits=99, max_files_touched=2).decide(
            proposals, tree_clean=True
        )
        self.assertEqual(len(decision.apply), 2)
        self.assertEqual(len({p for prop in decision.apply for p in prop.paths}), 2)
        self.assertIn("over the limit", note_for(decision.notes, decision.queue[0]) or "")

    def test_a_proposal_re_editing_an_already_touched_file_is_free(self) -> None:
        first = make_proposal(key="a", paths=("same.md",))
        second = make_proposal(key="b", paths=("same.md",))
        decision = self.engine(max_auto_edits=99, max_files_touched=1).decide(
            [first, second], tree_clean=True
        )
        self.assertEqual(len(decision.apply), 2, "the file budget counts files, not proposals")

    def test_byte_budget_cuts_off_at_exactly_the_limit(self) -> None:
        proposals = self.many(4, text="x" * 60)
        decision = self.engine(
            max_auto_edits=99, max_files_touched=99, max_bytes_changed=130
        ).decide(proposals, tree_clean=True)
        self.assertEqual(len(decision.apply), 2)
        self.assertIn("change budget", note_for(decision.notes, decision.queue[0]) or "")

    def test_byte_budget_counts_utf8_bytes_not_characters(self) -> None:
        wide = make_proposal(key="wide", text="é" * 40)  # 80 bytes, 40 characters
        decision = self.engine(max_bytes_changed=50).decide([wide], tree_clean=True)
        self.assertEqual(decision.apply, [])
        self.assertIn("change budget", note_for(decision.notes, wide) or "")

    def test_an_oversized_proposal_does_not_starve_the_ones_behind_it(self) -> None:
        big = make_proposal(key="big", paths=("big.md",), text="x" * 500, impact=1.0)
        small = make_proposal(key="small", paths=("small.md",), text="x", impact=0.9)
        decision = self.engine(max_bytes_changed=100).decide([big, small], tree_clean=True)
        self.assertEqual([p.finding.key for p in decision.apply], ["small"])
        self.assertEqual([p.finding.key for p in decision.queue], ["big"])

    def test_queue_is_capped_and_the_overflow_is_reported(self) -> None:
        proposals = self.many(6, risk="review")
        decision = self.engine(max_queued=4).decide(proposals, tree_clean=True)
        self.assertEqual(len(decision.queue), 4)
        dropped = [p for p in proposals if p not in decision.queue]
        self.assertEqual(len(dropped), 2)
        for proposal in dropped:
            note = note_for(decision.notes, proposal)
            self.assertIsNotNone(note, "an overflowing queue must not drop work in silence")
            self.assertIn("dropped", note)
            self.assertIn("proposed again", note)


class TestCleanTree(PolicyTestCase):
    def test_a_dirty_tree_blocks_every_edit(self) -> None:
        proposals = [make_proposal(key=f"p{i}", paths=(f"n{i}.md",)) for i in range(3)]
        decision = self.engine().decide(proposals, tree_clean=False)
        self.assertEqual(decision.apply, [])
        self.assertEqual(len(decision.queue), 3)
        self.assertTrue(any("uncommitted changes" in n for n in decision.notes))
        for proposal in proposals:
            self.assertIn("uncommitted", note_for(decision.notes, proposal) or "")

    def test_the_dirty_tree_guard_can_be_waived(self) -> None:
        proposal = make_proposal()
        decision = self.engine(require_clean_tree=False).decide([proposal], tree_clean=False)
        self.assertEqual(decision.apply, [proposal])
        self.assertFalse(any("uncommitted" in n for n in decision.notes))


class TestNothingIsDroppedSilently(PolicyTestCase):
    def test_every_proposal_not_applied_carries_a_reason(self) -> None:
        proposals = [
            make_proposal(key="ok", paths=("ok.md",)),
            make_proposal(key="risky", paths=("risky.md",), risk="review"),
            make_proposal(key="weak", paths=("weak.md",), severity="low", impact=0.05),
            make_proposal(key="code", paths=("mod.py",)),
            make_proposal(key="budget", paths=("budget.md",)),
        ]
        decision = self.engine(max_auto_edits=1).decide(proposals, tree_clean=True)
        accounted = decision.apply + decision.queue + decision.suppressed
        self.assertEqual(len(accounted), len(proposals), "every proposal must land somewhere")
        for proposal in decision.queue + decision.suppressed:
            note = note_for(decision.notes, proposal)
            self.assertIsNotNone(note, f"no reason recorded for {proposal.finding.key}")
            self.assertGreater(len(note), 20, "a reason has to be readable, not a code")

    def test_the_decision_never_mutates_the_input_list(self) -> None:
        proposals = [make_proposal(key="a"), make_proposal(key="b", risk="manual")]
        original = list(proposals)
        self.engine().decide(proposals, tree_clean=True)
        self.assertEqual(proposals, original)


if __name__ == "__main__":
    unittest.main()
