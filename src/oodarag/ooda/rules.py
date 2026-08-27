"""The rule set, as the design's table turned into predicates.

Each rule carries a ``rationale`` saying why its threshold sits where it does,
because the question that gets asked after a month of use is never "what does
this rule do" but "why does it keep firing". Most rules here are deliberately
demoted to ``digest``: they accumulate into the weekly brief instead of
interrupting. Only things that are genuinely urgent, or genuinely wrong,
escalate.

Two rules deserve explanation before the code.

``OBL-UNVERIFIED`` exists because the obligation calendar is seeded from
research that could not reach a primary source [src:DELEGATED-RECON-2026-08-27].
Rather than suppress those obligations (losing the calendar) or present them as
law (dangerous), the engine surfaces them with the basis flagged, once, until
someone verifies them.

``NAV-BASIS-MIX`` is the design's central correctness invariant made into an
alert. Funds are exempt from TMS 29 while the management company applies it
[src:SPK-FUND-TMS29-EXEMPTION], so the two are denominated in different money.
The money type already refuses to add them; this rule reports that a refusal
happened, because a caught error nobody hears about gets worked around.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from oodarag.config import WAM, FirmProfile
from oodarag.domain.valuation import breaches, valuation_drift
from oodarag.ooda.policy import Action, PolicyEngine, Rule, State

DAY = 86400.0


# --------------------------------------------------------------------------
# Compliance and deadlines
# --------------------------------------------------------------------------

def _thresholds(state: State) -> Any:
    profile: FirmProfile = state.profile or WAM
    return profile.thresholds


def rule_obligation_due_soon(state: State) -> list[Action]:
    if not state.calendar or not state.now:
        return []
    t = _thresholds(state)
    out = []
    for due in state.calendar.due_within(t.deadline_horizon_days, state.now,
                                         state.context):
        if due.overdue or due.business_days_left <= t.deadline_escalate_days:
            continue  # handled by the escalate / overdue rules
        out.append(Action(
            kind="digest", rule_id="OBL-DUE-SOON", target=due.obligation.id,
            reason=f"{due.obligation.title_en} is due {due.due.isoformat()}",
            severity="medium", priority=60, facts=due.as_dict(),
            unverified_basis=not due.obligation.verified,
        ))
    return out


def rule_obligation_escalate(state: State) -> list[Action]:
    if not state.calendar or not state.now:
        return []
    t = _thresholds(state)
    out = []
    for due in state.calendar.due_within(t.deadline_horizon_days, state.now,
                                         state.context):
        if due.overdue or due.business_days_left > t.deadline_escalate_days:
            continue
        out.append(Action(
            kind="escalate", rule_id="OBL-ESCALATE", target=due.obligation.id,
            reason=(f"{due.obligation.title_en} is due {due.due.isoformat()} — "
                    f"{due.business_days_left} business days left"),
            severity="high", priority=10, facts=due.as_dict(),
            requires_signoff=due.obligation.owner or "named owner",
            unverified_basis=not due.obligation.verified,
        ))
    return out


def rule_obligation_overdue(state: State) -> list[Action]:
    if not state.calendar or not state.now:
        return []
    return [
        Action(
            kind="escalate", rule_id="OBL-OVERDUE", target=d.obligation.id,
            reason=f"{d.obligation.title_en} was due {d.due.isoformat()} and is unsatisfied",
            severity="critical", priority=1, facts=d.as_dict(),
            requires_signoff=d.obligation.owner or "named owner",
            unverified_basis=not d.obligation.verified,
        )
        for d in state.calendar.overdue(state.now, state.context)
    ]


def rule_obligation_unverified(state: State) -> list[Action]:
    """Report the researched-not-confirmed calendar once, as one action.

    One action, not thirty: thirty identical warnings is the definition of the
    noise this system is trying to avoid.
    """
    if not state.calendar:
        return []
    unverified = state.calendar.unverified
    if not unverified:
        return []
    return [Action(
        kind="digest", rule_id="OBL-UNVERIFIED", target="calendar",
        reason=(f"{len(unverified)} of {len(state.calendar.obligations)} obligations "
                "come from research that could not reach a primary source; they are "
                "a starting calendar, not legal deadlines"),
        severity="high", priority=20,
        facts={"unverified": [o.id for o in unverified[:40]],
               "total": len(state.calendar.obligations)},
        requires_signoff="compliance officer or counsel",
        unverified_basis=True,
    )]


def rule_obligation_unscheduled(state: State) -> list[Action]:
    if not state.calendar:
        return []
    missing = state.calendar.unscheduled(state.context)
    if not missing:
        return []
    return [Action(
        kind="digest", rule_id="OBL-UNSCHEDULED", target="calendar",
        reason=(f"{len(missing)} applicable obligations have no due date set; a "
                "missing date is a gap in the calendar, not a distant deadline"),
        severity="medium", priority=70,
        facts={"unscheduled": [o.id for o in missing[:40]]},
    )]


# --------------------------------------------------------------------------
# Valuation integrity
# --------------------------------------------------------------------------

def rule_nav_drift(state: State) -> list[Action]:
    t = _thresholds(state)
    out: list[Action] = []
    for code, points in sorted(state.nav_history.items()):
        if len(points) < 2:
            continue
        try:
            drift = valuation_drift(points[-2], points[-1], state.index)
        except Exception as e:
            out.append(Action(
                kind="alert", rule_id="NAV-DRIFT-ERROR", target=code,
                reason=f"could not compute drift for {code}: {e}"[:250],
                severity="high", priority=15, facts={"fund": code},
            ))
            continue
        hit = breaches(drift, real_threshold=t.valuation_drift_real,
                       nominal_threshold=t.valuation_drift_nominal)
        if "nominal" in hit:
            out.append(Action(
                kind="alert", rule_id="NAV-DRIFT-NOMINAL", target=code,
                reason=(f"{code} unit value moved {drift['nominal_move']:.2%} nominally "
                        "— a jump this large is usually a data error, not a valuation event"),
                severity="high", priority=12, facts=drift,
                requires_signoff="fon müdürü",
            ))
        elif "real" in hit:
            out.append(Action(
                kind="alert", rule_id="NAV-DRIFT-REAL", target=code,
                reason=(f"{code} unit value moved {drift['real_move']:.2%} in real terms "
                        f"(nominal {drift['nominal_move']:.2%})"),
                severity="medium", priority=40, facts=drift,
            ))
        if drift.get("inflation_error"):
            out.append(Action(
                kind="alert", rule_id="CPI-STALE", target=code,
                reason=("real drift could not be computed: " +
                        str(drift["inflation_error"])[:200]),
                severity="high", priority=18, facts={"fund": code},
            ))
    return out


def rule_real_return_negative(state: State) -> list[Action]:
    """Nominal up, real down. The number most likely to be misread in this economy."""
    out = []
    for code, points in sorted(state.nav_history.items()):
        if len(points) < 2 or state.index is None:
            continue
        try:
            drift = valuation_drift(points[-2], points[-1], state.index)
        except Exception:
            continue
        nominal, real = drift.get("nominal_move"), drift.get("real_move")
        if nominal is None or real is None:
            continue
        if nominal > 0 and real < 0:
            out.append(Action(
                kind="digest", rule_id="REAL-RETURN-NEGATIVE", target=code,
                reason=(f"{code} is up {nominal:.2%} nominally but down {real:.2%} in "
                        "real terms — reporting only the nominal figure would flatter"),
                severity="medium", priority=45, facts=drift,
            ))
    return out


def rule_nav_stale(state: State) -> list[Action]:
    if not state.now:
        return []
    out = []
    for code, points in sorted(state.nav_history.items()):
        if not points:
            continue
        age = (state.now - points[-1].as_of).days
        if age > 95:  # a quarter plus slack
            out.append(Action(
                kind="alert", rule_id="NAV-STALE", target=code,
                reason=f"{code} has published no unit value in {age} days",
                severity="high", priority=25,
                facts={"fund": code, "last": points[-1].as_of.isoformat(), "age_days": age},
            ))
    return out


def rule_basis_mix(state: State) -> list[Action]:
    """Surface any refused basis mix observed during the cycle.

    The Money type already prevents the error. This rule makes sure the
    prevention is visible, because a silently caught error gets worked around
    rather than fixed.
    """
    hits = state.signals_of("basis_mismatch")
    return [Action(
        kind="alert", rule_id="NAV-BASIS-MIX", target=s.key,
        reason=("a nominal and a restated amount reached one computation — funds are "
                "TMS 29 exempt while the management company is not, so these are "
                "different money"),
        severity="critical", priority=2,
        facts={"where": s.key, "detail": str(s.value)[:300], "source": s.source_uri},
    ) for s in hits]


# --------------------------------------------------------------------------
# Macro
# --------------------------------------------------------------------------

def rule_fx_move(state: State) -> list[Action]:
    t = _thresholds(state)
    out = []
    for s in state.signals_of("fx_move"):
        try:
            move = Decimal(str(s.value))
        except Exception:
            continue
        if abs(move) > t.fx_daily_move:
            out.append(Action(
                kind="digest", rule_id="FX-MOVE", target=s.key,
                reason=f"{s.key} moved {move:.2%} in a day",
                severity="low", priority=80,
                facts={"pair": s.key, "move": move, "source": s.source_uri},
            ))
    return out


def rule_cpi_stale(state: State) -> list[Action]:
    """The index is the input to every real figure. Stale index, silent errors."""
    if state.index is None or not state.now:
        return []
    latest = state.index.latest
    if latest is None:
        return [Action(
            kind="alert", rule_id="CPI-EMPTY", target="tufe",
            reason="the price index is empty; no real-terms figure can be computed",
            severity="critical", priority=3, facts={},
        )]
    prev_month = (state.now.replace(day=1) - timedelta(days=1))
    expected = f"{prev_month.year:04d}-{prev_month.month:02d}"
    if latest.period < expected:
        return [Action(
            kind="alert", rule_id="CPI-STALE", target="tufe",
            reason=(f"price index has no point for {expected}; every real-terms "
                    "figure is being computed against an out-of-date index"),
            severity="high", priority=16,
            facts={"latest": latest.period, "expected": expected,
                   "provisional": latest.provisional},
        )]
    return []


# --------------------------------------------------------------------------
# Regulatory change
# --------------------------------------------------------------------------

def rule_reg_change(state: State) -> list[Action]:
    return [Action(
        kind="alert", rule_id="REG-CHANGE", target=s.key,
        reason=f"watched term appeared at {s.source_uri or s.key}: {str(s.value)[:180]}",
        severity="high", priority=8,
        facts={"source": s.source_uri, "excerpt": str(s.evidence)[:400]},
        requires_signoff="compliance",
    ) for s in state.signals_of("regulatory_change")]


def rule_reg_deadline_short(state: State) -> list[Action]:
    """A detected change with a compliance date inside 30 days.

    The SPK's 23 July 2026 valuation decision gave eight days
    [src:SPK-VALUATION-2026-07-23]. This is the rule that exists because of it.
    """
    out = []
    for s in state.signals_of("regulatory_deadline"):
        try:
            days = int(s.value)
        except (TypeError, ValueError):
            continue
        if days <= 30:
            out.append(Action(
                kind="escalate", rule_id="REG-DEADLINE-SHORT", target=s.key,
                reason=(f"a regulatory change at {s.source_uri or s.key} carries a "
                        f"compliance date {days} days out"),
                severity="critical", priority=1,
                facts={"days": days, "source": s.source_uri,
                       "excerpt": str(s.evidence)[:400]},
                requires_signoff="compliance",
            ))
    return out


# --------------------------------------------------------------------------
# Pipeline health — the rules that stop the system lying quietly
# --------------------------------------------------------------------------

def rule_index_stale(state: State) -> list[Action]:
    t = _thresholds(state)
    return [Action(
        kind="alert", rule_id="IDX-STALE", target=corpus,
        reason=(f"{corpus} has not refreshed in {age:.0f} days; retrieval is "
                "answering from a stale world"),
        severity="medium", priority=55,
        facts={"corpus": corpus, "age_days": age, "threshold": t.index_stale_days},
    ) for corpus, age in sorted(state.corpus_age_days.items())
        if age > t.index_stale_days]


def rule_citation_coverage(state: State) -> list[Action]:
    t = _thresholds(state)
    if state.citation_coverage is None or state.citation_coverage >= t.citation_coverage_floor:
        return []
    return [Action(
        kind="alert", rule_id="CITE-COVERAGE-LOW", target="retrieval",
        reason=(f"verified-citation coverage is {state.citation_coverage:.0%}, below the "
                f"{t.citation_coverage_floor:.0%} floor — answers are not grounded and "
                "the system should abstain rather than hedge"),
        severity="high", priority=14,
        facts={"coverage": state.citation_coverage, "floor": t.citation_coverage_floor},
    )]


def rule_connector_down(state: State) -> list[Action]:
    t = _thresholds(state)
    return [Action(
        kind="alert", rule_id="CONNECTOR-DOWN", target=key,
        reason=f"{key} has failed {n} consecutive runs; treat it as broken, not flaky",
        severity="medium", priority=50, facts={"connector": key, "failures": n},
    ) for key, n in sorted(state.connector_failures.items())
        if n >= t.connector_failure_streak]


def rule_model_changed(state: State) -> list[Action]:
    """Minimum viable model change control.

    The delegated research reports Two Sigma settling with the SEC for roughly
    $90m in January 2025 over a failure of model *change control* rather than
    model quality [src:DELEGATED-RECON-2026-08-27]. This rule is the cheap
    version of the lesson: if the fingerprint moved and the eval set was not
    re-run, say so.
    """
    if not state.model_fingerprint:
        return []
    if state.model_fingerprint == state.last_evaluated_fingerprint:
        return []
    return [Action(
        kind="alert", rule_id="MODEL-CHANGED", target="model",
        reason=("the embedding model or prompt changed since the evaluation set was "
                "last run; re-run it before trusting any answer"),
        severity="high", priority=11,
        facts={"current": state.model_fingerprint,
               "last_evaluated": state.last_evaluated_fingerprint or "never"},
        requires_signoff="whoever did not build the change",
    )]


# --------------------------------------------------------------------------

_RULES: tuple[tuple[str, str, Any, str, float, str], ...] = (
    ("OBL-OVERDUE", "An applicable obligation is past due and unsatisfied.",
     rule_obligation_overdue, "critical", DAY,
     "No threshold: an overdue filing is always worth interrupting for."),
    ("OBL-ESCALATE", "An obligation falls inside the escalation window.",
     rule_obligation_escalate, "high", DAY,
     "5 business days: enough to act, short enough that it is not background noise."),
    ("OBL-DUE-SOON", "An obligation is inside the 21-day horizon.",
     rule_obligation_due_soon, "medium", 7 * DAY,
     "Digest only, 7-day cooldown. At 30 obligations a daily alert here would be "
     "the single loudest thing in the system and would train him to ignore it."),
    ("OBL-UNVERIFIED", "The calendar contains researched, unconfirmed obligations.",
     rule_obligation_unverified, "high", 7 * DAY,
     "One action for the whole calendar, weekly. Thirty separate warnings is the "
     "noise this rule is meant to prevent."),
    ("OBL-UNSCHEDULED", "Applicable obligations have no due date set.",
     rule_obligation_unscheduled, "medium", 7 * DAY,
     "Weekly digest: a gap in the calendar is real but never urgent today."),
    ("NAV-DRIFT", "A fund unit value moved beyond a materiality threshold.",
     rule_nav_drift, "high", DAY,
     "Real 5% / nominal 25%. A nominal-only rule at 5% would fire every month on "
     "inflation alone; 25% nominal catches data errors rather than valuations."),
    ("REAL-RETURN-NEGATIVE", "A fund is up nominally and down in real terms.",
     rule_real_return_negative, "medium", 7 * DAY,
     "Digest. Structural in a 31.75% CPI economy, so it informs rather than alarms."),
    ("NAV-STALE", "A fund has published no unit value in over a quarter.",
     rule_nav_stale, "high", 7 * DAY,
     "95 days: one accounting period plus slack, matching the minimum announcement "
     "cadence rather than an arbitrary month count."),
    ("NAV-BASIS-MIX", "Nominal and restated amounts reached one computation.",
     rule_basis_mix, "critical", DAY,
     "No threshold. This is the design's central invariant; any occurrence matters."),
    ("FX-MOVE", "TRY moved beyond the daily threshold.",
     rule_fx_move, "low", DAY,
     "3% daily. The lira's managed depreciation makes small daily moves normal; a "
     "1% rule would be an alarm clock."),
    ("CPI-STALE", "The price index is missing the last closed month.",
     rule_cpi_stale, "high", DAY,
     "No threshold: every real-terms figure depends on this, so staleness is silent "
     "corruption rather than a delay."),
    ("REG-CHANGE", "A watched term appeared in a regulatory source.",
     rule_reg_change, "high", DAY,
     "Keyword-gated in config rather than threshold-gated. A broad keyword list is a "
     "crawler, not a filter, and a human pays for every false positive."),
    ("REG-DEADLINE-SHORT", "A regulatory change carries a near-term compliance date.",
     rule_reg_deadline_short, "critical", DAY,
     "30 days. Calibrated on the 23 July 2026 SPK decision, which gave eight."),
    ("IDX-STALE", "A corpus has not been refreshed recently.",
     rule_index_stale, "medium", 2 * DAY,
     "7 days. Long enough to survive a holiday week, short enough that a dead "
     "connector does not go a month unnoticed."),
    ("CITE-COVERAGE-LOW", "Answers are not grounded in retrieved sources.",
     rule_citation_coverage, "high", DAY,
     "0.6. Below this the honest move is to abstain, not to hedge."),
    ("CONNECTOR-DOWN", "A source has failed repeatedly.",
     rule_connector_down, "medium", 2 * DAY,
     "3 consecutive failures distinguishes a broken source from a flaky one."),
    ("MODEL-CHANGED", "The model changed without the eval set being re-run.",
     rule_model_changed, "high", DAY,
     "No threshold. Change control, not model quality, is what regulators fine."),
)


def default_ruleset(engine: PolicyEngine | None = None) -> PolicyEngine:
    """The wired rule set, so the system decides something out of the box."""
    engine = engine or PolicyEngine()
    for rid, desc, fn, sev, cooldown, why in _RULES:
        engine.register(Rule(id=rid, description=desc, condition=fn,
                             severity=sev, cooldown_s=cooldown, rationale=why))
    return engine


__all__ = ["default_ruleset", "date"]
