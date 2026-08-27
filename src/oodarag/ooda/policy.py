"""The part that decides — and it is not a model.

The design keeps a hard boundary: models read documents and draft prose,
deterministic code decides. This module is the deciding half. Every rule is a
Python predicate over typed state, so an auditor can read one and say whether it
is right, and a test can prove it fires when it should.

The failure mode being engineered against is not missing an event. It is
**alert fatigue**: a system that fires often enough to be ignored has a
detection rate of zero regardless of how good its rules are. Three mechanisms
push back.

- **Materiality thresholds** live in ``config.Thresholds``, in one file, so the
  answer to "where did 5% come from?" is one place.
- **Cooldowns.** A rule that fired on a fact cannot fire again on the same
  unchanged fact until its cooldown expires.
- **Digest severity.** A rule marked ``digest`` never interrupts; it accumulates
  into the weekly brief. Most rules should be digest rules.

Every :class:`Action` records which rule fired and which facts satisfied it.
"The system flagged it" is not an answer to an inspector; the rule id, the
threshold, the observed value and the source URI are.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from oodarag.util.logging import get_logger

log = get_logger("policy")

Severity = Literal["info", "low", "medium", "high", "critical"]
ActionKind = Literal["noop", "digest", "alert", "escalate", "reindex",
                     "recalculate", "brief"]

_SEVERITY_ORDER: dict[str, int] = {
    "info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4,
}


@dataclass(slots=True, frozen=True)
class Signal:
    """One observed fact, with where it came from.

    ``confidence`` and ``verified`` travel with the fact because a rule that
    fires on unverified research must say so in its alert. The obligation
    calendar is seeded from second-hand research
    [src:DELEGATED-RECON-2026-08-27], and an alert that presents a researched
    deadline as a legal one is worse than no alert.
    """

    kind: str
    key: str
    value: Any
    observed_at: float = field(default_factory=time.time)
    severity: Severity = "info"
    source_uri: str = ""
    evidence: str = ""
    verified: bool = True

    @property
    def dedupe_key(self) -> str:
        return f"{self.kind}:{self.key}"

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["value"] = _jsonable(d["value"])
        return d


@dataclass(slots=True)
class Action:
    """What the engine decided, and exactly why."""

    kind: ActionKind
    rule_id: str
    target: str
    reason: str
    severity: Severity = "medium"
    priority: int = 50
    facts: dict[str, Any] = field(default_factory=dict)
    requires_signoff: str = ""
    unverified_basis: bool = False

    @property
    def rank(self) -> tuple[int, int]:
        return (-_SEVERITY_ORDER[self.severity], self.priority)

    def explain(self) -> str:
        lines = [
            f"[{self.severity.upper()}] {self.rule_id} -> {self.kind} on {self.target}",
            f"  because: {self.reason}",
        ]
        for k, v in sorted(self.facts.items()):
            lines.append(f"    {k} = {_jsonable(v)}")
        if self.requires_signoff:
            lines.append(f"  requires sign-off: {self.requires_signoff}")
        if self.unverified_basis:
            lines.append("  BASIS UNVERIFIED: this rule fired on researched, "
                         "not confirmed, source material — confirm before acting")
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["facts"] = {k: _jsonable(v) for k, v in self.facts.items()}
        return d


@dataclass
class State:
    """Everything the rules may look at.

    Deliberately a plain bag rather than a clever object: a rule should be
    readable by someone who does not know this codebase.
    """

    now: Any = None                       # datetime.date
    profile: Any = None                   # config.FirmProfile
    calendar: Any = None                  # domain.ObligationCalendar
    index: Any = None                     # domain.PriceIndex
    nav_history: dict[str, list[Any]] = field(default_factory=dict)
    signals: list[Signal] = field(default_factory=list)
    connector_failures: dict[str, int] = field(default_factory=dict)
    corpus_age_days: dict[str, float] = field(default_factory=dict)
    citation_coverage: float | None = None
    model_fingerprint: str = ""
    last_evaluated_fingerprint: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def signals_of(self, kind: str) -> list[Signal]:
        return [s for s in self.signals if s.kind == kind]


@dataclass(slots=True)
class Rule:
    """A condition and what to do when it holds.

    ``condition`` returns a list of Actions rather than a bool, because most
    real rules fire per-item — one action per overdue obligation, not one action
    saying "some obligations are overdue".
    """

    id: str
    description: str
    condition: Callable[[State], list[Action]]
    severity: Severity = "medium"
    cooldown_s: float = 86400.0
    enabled: bool = True
    #: Why this rule's threshold is where it is. Read by a human deciding
    #: whether to tighten it after a month of watching what fires.
    rationale: str = ""


class PolicyEngine:
    """Registers rules, runs them, suppresses repeats."""

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._rules: dict[str, Rule] = {}
        self._last_fired: dict[str, float] = {}
        self._clock = clock

    def register(self, rule: Rule) -> None:
        if rule.id in self._rules:
            raise ValueError(f"duplicate rule id {rule.id!r}")
        self._rules[rule.id] = rule

    @property
    def rules(self) -> list[Rule]:
        return [self._rules[k] for k in sorted(self._rules)]

    def decide(self, state: State) -> list[Action]:
        """Run every enabled rule. Never raises: one broken rule must not
        silence the other twenty-two."""
        out: list[Action] = []
        now = self._clock()
        for rule in self.rules:
            if not rule.enabled:
                continue
            try:
                actions = rule.condition(state) or []
            except Exception as e:
                log.error("rule raised; skipping it", rule=rule.id, err=str(e)[:300])
                out.append(Action(
                    kind="alert", rule_id="POLICY-RULE-BROKEN", target=rule.id,
                    reason=f"rule {rule.id} raised {type(e).__name__}: {e}"[:300],
                    severity="high", priority=1,
                    facts={"rule": rule.id, "error": str(e)[:300]},
                ))
                continue
            if not actions:
                continue
            for action in actions:
                gate = f"{rule.id}:{action.target}"
                last = self._last_fired.get(gate)
                if last is not None and (now - last) < rule.cooldown_s:
                    log.info("suppressed by cooldown", rule=rule.id, target=action.target)
                    continue
                self._last_fired[gate] = now
                out.append(action)
        out.sort(key=lambda a: a.rank)
        return out

    def reset_cooldowns(self) -> None:
        self._last_fired.clear()

    def describe(self) -> str:
        lines = ["Policy rules", "=" * 60]
        for r in self.rules:
            flag = "" if r.enabled else "  (disabled)"
            lines.append(f"  [{r.severity.upper():8}] {r.id}{flag}")
            lines.append(f"             {r.description}")
            if r.rationale:
                lines.append(f"             why this threshold: {r.rationale}")
        return "\n".join(lines)


def _jsonable(value: Any) -> Any:
    """Make a fact printable without losing exactness in the process."""
    from decimal import Decimal
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def journal_line(action: Action, *, cycle: str, at: float | None = None) -> str:
    """One append-only audit-trail record. JSONL, one action per line."""
    return json.dumps({
        "at": at if at is not None else time.time(),
        "cycle": cycle,
        **action.as_dict(),
    }, ensure_ascii=False, sort_keys=True)
