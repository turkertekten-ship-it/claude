"""Tests for the decision layer.

The rules themselves are simple; what needs proving is the machinery around
them — that a broken rule cannot silence the others, that a cooldown actually
suppresses, that severity ordering puts the urgent thing first, and that an
alert built on unverified research says so.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from oodarag.config import WAM
from oodarag.domain.inflation import bundled_index
from oodarag.domain.money import Money
from oodarag.domain.obligations import ObligationCalendar
from oodarag.domain.valuation import NavPoint
from oodarag.ooda.act import Brief, DecisionJournal, render_brief
from oodarag.ooda.policy import Action, PolicyEngine, Rule, Signal, State
from oodarag.ooda.rules import default_ruleset

D = Decimal
TODAY = date(2026, 8, 27)


def _action(rule_id: str = "R", target: str = "t", **kw: object) -> Action:
    return Action(kind=kw.pop("kind", "alert"), rule_id=rule_id,  # type: ignore[arg-type]
                  target=target, reason="because", **kw)  # type: ignore[arg-type]


class TestPolicyEngine(unittest.TestCase):
    def test_a_broken_rule_does_not_silence_the_others(self) -> None:
        """One bad predicate must not turn the whole system off quietly."""
        def boom(_: State) -> list[Action]:
            raise RuntimeError("kaboom")

        engine = PolicyEngine()
        engine.register(Rule("BOOM", "raises", boom))
        engine.register(Rule("FINE", "works", lambda s: [_action("FINE")]))
        actions = engine.decide(State())
        ids = {a.rule_id for a in actions}
        self.assertIn("FINE", ids)
        self.assertIn("POLICY-RULE-BROKEN", ids)  # and the breakage is reported

    def test_cooldown_suppresses_the_same_target(self) -> None:
        clock = [1000.0]
        engine = PolicyEngine(clock=lambda: clock[0])
        engine.register(Rule("R", "d", lambda s: [_action("R", "same")],
                             cooldown_s=100.0))
        self.assertEqual(len(engine.decide(State())), 1)
        clock[0] += 50
        self.assertEqual(len(engine.decide(State())), 0)   # inside cooldown
        clock[0] += 100
        self.assertEqual(len(engine.decide(State())), 1)   # expired

    def test_cooldown_is_per_target_not_per_rule(self) -> None:
        """Two funds breaching the same rule are two events, not one."""
        clock = [1000.0]
        engine = PolicyEngine(clock=lambda: clock[0])
        engine.register(Rule("R", "d",
                             lambda s: [_action("R", "VBR"), _action("R", "VIK")],
                             cooldown_s=100.0))
        self.assertEqual(len(engine.decide(State())), 2)

    def test_severity_orders_before_priority(self) -> None:
        engine = PolicyEngine()
        engine.register(Rule("LOW", "d", lambda s: [
            _action("LOW", "a", severity="low", priority=1)]))
        engine.register(Rule("CRIT", "d", lambda s: [
            _action("CRIT", "b", severity="critical", priority=99)]))
        self.assertEqual(engine.decide(State())[0].rule_id, "CRIT")

    def test_duplicate_rule_ids_are_refused(self) -> None:
        engine = PolicyEngine()
        engine.register(Rule("R", "d", lambda s: []))
        with self.assertRaises(ValueError):
            engine.register(Rule("R", "d", lambda s: []))

    def test_disabled_rules_do_not_run(self) -> None:
        engine = PolicyEngine()
        engine.register(Rule("R", "d", lambda s: [_action()], enabled=False))
        self.assertEqual(engine.decide(State()), [])

    def test_explain_names_the_rule_the_facts_and_the_signoff(self) -> None:
        a = _action("R", "VBR", severity="high", facts={"move": D("0.32")},
                    requires_signoff="fon müdürü")
        text = a.explain()
        self.assertIn("R", text)
        self.assertIn("VBR", text)
        self.assertIn("0.32", text)
        self.assertIn("fon müdürü", text)

    def test_unverified_basis_is_visible_in_the_explanation(self) -> None:
        self.assertIn("BASIS UNVERIFIED",
                      _action(unverified_basis=True).explain())


class TestDefaultRuleset(unittest.TestCase):
    def _state(self, **kw: object) -> State:
        base = dict(now=TODAY, profile=WAM, index=bundled_index())
        base.update(kw)
        return State(**base)  # type: ignore[arg-type]

    def test_the_ruleset_wires_up(self) -> None:
        engine = default_ruleset()
        self.assertGreaterEqual(len(engine.rules), 15)
        self.assertTrue(all(r.rationale for r in engine.rules),
                        "every rule must say why its threshold is where it is")

    def test_quiet_state_produces_nothing(self) -> None:
        """A system that always fires is a system nobody reads."""
        self.assertEqual(default_ruleset().decide(self._state()), [])

    def test_overdue_obligation_escalates_and_carries_the_unverified_flag(self) -> None:
        cal = ObligationCalendar.from_seed()
        oid = next(iter(cal.obligations))
        cal.set_due(oid, TODAY - timedelta(days=3))
        actions = default_ruleset().decide(self._state(calendar=cal))
        overdue = [a for a in actions if a.rule_id == "OBL-OVERDUE"]
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].severity, "critical")
        self.assertTrue(overdue[0].unverified_basis)

    def test_unverified_calendar_reports_once_not_per_obligation(self) -> None:
        """Thirty identical warnings is the noise this design exists to avoid."""
        cal = ObligationCalendar.from_seed()
        actions = default_ruleset().decide(self._state(calendar=cal))
        self.assertEqual(len([a for a in actions if a.rule_id == "OBL-UNVERIFIED"]), 1)

    def test_nominal_only_drift_does_not_fire_the_real_rule(self) -> None:
        """A fund tracking inflation exactly has not moved in real terms.

        This is the rule that would fire every month if it were written against
        nominal values, which is the whole reason for the real/nominal split.
        """
        nav = {"VBR": [
            NavPoint("VBR", date(2025, 7, 31), Money(D("100"), "TRY")),
            NavPoint("VBR", date(2026, 7, 31), Money(D("131.75"), "TRY")),
        ]}
        actions = default_ruleset().decide(self._state(nav_history=nav))
        self.assertEqual([a for a in actions if a.rule_id == "NAV-DRIFT-REAL"], [])

    def test_real_loss_under_a_nominal_gain_is_surfaced(self) -> None:
        nav = {"VIK": [
            NavPoint("VIK", date(2025, 7, 31), Money(D("100"), "TRY")),
            NavPoint("VIK", date(2026, 7, 31), Money(D("104"), "TRY")),
        ]}
        ids = {a.rule_id for a in default_ruleset().decide(self._state(nav_history=nav))}
        self.assertIn("NAV-DRIFT-REAL", ids)
        self.assertIn("REAL-RETURN-NEGATIVE", ids)

    def test_short_regulatory_deadline_is_critical(self) -> None:
        """Calibrated on the SPK decision that gave eight days."""
        sig = Signal(kind="regulatory_deadline", key="spk", value=8,
                     source_uri="https://spk.gov.tr/")
        actions = default_ruleset().decide(self._state(signals=[sig]))
        hit = [a for a in actions if a.rule_id == "REG-DEADLINE-SHORT"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0].severity, "critical")
        self.assertEqual(hit[0].kind, "escalate")

    def test_small_fx_move_stays_quiet(self) -> None:
        sig = Signal(kind="fx_move", key="USDTRY", value="0.005")
        ids = {a.rule_id for a in default_ruleset().decide(self._state(signals=[sig]))}
        self.assertNotIn("FX-MOVE", ids)

    def test_stale_index_is_reported(self) -> None:
        from oodarag.domain.inflation import PriceIndex
        old = PriceIndex("t", {"2025-01": "100"})
        ids = {a.rule_id for a in default_ruleset().decide(self._state(index=old))}
        self.assertIn("CPI-STALE", ids)

    def test_model_change_without_a_rerun_is_flagged(self) -> None:
        ids = {a.rule_id for a in default_ruleset().decide(
            self._state(model_fingerprint="v2", last_evaluated_fingerprint="v1"))}
        self.assertIn("MODEL-CHANGED", ids)

    def test_model_unchanged_is_quiet(self) -> None:
        ids = {a.rule_id for a in default_ruleset().decide(
            self._state(model_fingerprint="v1", last_evaluated_fingerprint="v1"))}
        self.assertNotIn("MODEL-CHANGED", ids)

    def test_low_citation_coverage_fires(self) -> None:
        ids = {a.rule_id for a in default_ruleset().decide(
            self._state(citation_coverage=0.2))}
        self.assertIn("CITE-COVERAGE-LOW", ids)

    def test_connector_failures_below_the_streak_stay_quiet(self) -> None:
        ids = {a.rule_id for a in default_ruleset().decide(
            self._state(connector_failures={"kap": 1}))}
        self.assertNotIn("CONNECTOR-DOWN", ids)


class TestJournalAndBrief(unittest.TestCase):
    def test_journal_appends_and_never_rewrites(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            j = DecisionJournal(Path(d) / "decisions.jsonl")
            j.record([_action("A")], cycle="c1")
            j.record([_action("B"), _action("C")], cycle="c2")
            rows = j.read()
            self.assertEqual([r["rule_id"] for r in rows], ["A", "B", "C"])
            self.assertEqual({r["cycle"] for r in rows}, {"c1", "c2"})

    def test_journal_lines_are_valid_json_with_decimals_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            j = DecisionJournal(Path(d) / "j.jsonl")
            j.record([_action("A", facts={"move": D("0.3175")})], cycle="c")
            row = json.loads(j.path.read_text("utf-8").splitlines()[0])
            self.assertEqual(row["facts"]["move"], "0.3175")  # exact, as a string

    def test_empty_journal_reads_as_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(DecisionJournal(Path(d) / "none.jsonl").read(), [])

    def test_brief_sorts_escalations_first(self) -> None:
        brief = Brief(as_of=TODAY, firm="WAM Portföy", actions=[
            _action("A", kind="digest"),
            _action("B", kind="escalate", requires_signoff="board"),
            _action("C", kind="alert"),
        ])
        text = render_brief(brief)
        self.assertLess(text.index("Needs a decision today"), text.index("Wrong, or about"))
        self.assertIn("board", text)

    def test_brief_says_it_was_not_sent(self) -> None:
        """Drafting is the deliverable; sending is a human decision."""
        self.assertIn("not sent", render_brief(Brief(as_of=TODAY, firm="x")))

    def test_quiet_brief_says_so_rather_than_being_blank(self) -> None:
        self.assertIn("Nothing fired", render_brief(Brief(as_of=TODAY, firm="x")))

    def test_brief_marks_unverified_actions(self) -> None:
        brief = Brief(as_of=TODAY, firm="x",
                      actions=[_action("A", kind="escalate", unverified_basis=True)])
        self.assertIn("UNVERIFIED", render_brief(brief))

    def test_percentages_are_formatted_not_dumped(self) -> None:
        brief = Brief(as_of=TODAY, firm="x", actions=[
            _action("A", facts={"real_move": D("-0.2106261859582542694497153700")})])
        text = render_brief(brief)
        self.assertIn("-21.06%", text)
        self.assertNotIn("0.2106261859", text)


if __name__ == "__main__":
    unittest.main()
