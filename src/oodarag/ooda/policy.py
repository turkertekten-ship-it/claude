"""Decide: turn a situation assessment into ranked actions.

Rules, not a model. Every decision this loop makes has to be explainable after
the fact - "why did it re-crawl at 3am and burn the API quota" is a question
that needs an answer, and "the policy said so, here is the rule and the
measurement that triggered it" is one. A learned policy would be a better fit
for a system with far more signal than this one has, and a far worse fit for one
that has to be auditable.

Each rule states a condition over the situation, an action, a priority, and the
evidence that fired it. `decide` returns them ranked; `act` executes as many as
the cycle's budget allows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Action kinds the Act phase knows how to execute.
REINDEX = "reindex"
REFIT_EMBEDDER = "refit_embedder"
EMBED_MISSING = "embed_missing"
BACKFILL_SOURCE = "backfill_source"
QUARANTINE_SOURCE = "quarantine_source"
RUN_EVAL = "run_eval"
ALERT = "alert"
NOOP = "noop"


@dataclass(slots=True)
class Action:
    kind: str
    priority: int          # higher runs first
    reason: str            # human-readable rule name
    evidence: dict[str, Any] = field(default_factory=dict)
    target: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "priority": self.priority, "reason": self.reason,
                "target": self.target, "evidence": self.evidence}


@dataclass
class Thresholds:
    """Every number the policy uses, in one place so it is tunable and reviewable."""

    min_embedding_coverage: float = 0.99
    max_source_failure_rate: float = 0.25
    consecutive_failures_to_quarantine: int = 3
    min_eval_pass_rate: float = 0.80
    eval_regression_tolerance: float = 0.05
    corpus_growth_refit: float = 0.25
    stale_source_hours: float = 24.0
    min_docs_for_eval: int = 5


def decide(situation: dict[str, Any], thresholds: Thresholds | None = None) -> list[Action]:
    """Rank the actions this cycle should take."""
    t = thresholds or Thresholds()
    actions: list[Action] = []

    # --- Integrity first. An index that cannot answer correctly is worse than
    # one that is merely out of date, so gaps outrank freshness.
    coverage = situation.get("embedding_coverage", 1.0)
    if coverage < t.min_embedding_coverage:
        actions.append(Action(
            EMBED_MISSING, priority=100,
            reason="chunks without a current-space vector are invisible to dense retrieval",
            evidence={"coverage": coverage, "threshold": t.min_embedding_coverage},
        ))

    if situation.get("fingerprint_mismatch"):
        actions.append(Action(
            REINDEX, priority=95,
            reason="stored vectors are from a different embedding space than the configured embedder",
            evidence={"index_fingerprint": situation.get("index_fingerprint"),
                      "embedder_fingerprint": situation.get("embedder_fingerprint")},
        ))

    growth = situation.get("corpus_growth", 0.0)
    if growth > t.corpus_growth_refit:
        actions.append(Action(
            REFIT_EMBEDDER, priority=70,
            reason="corpus grew enough that term statistics no longer describe it",
            evidence={"growth": round(growth, 3), "threshold": t.corpus_growth_refit},
        ))

    # --- Source health.
    for name, health in (situation.get("sources") or {}).items():
        failures = health.get("consecutive_failures", 0)
        if failures >= t.consecutive_failures_to_quarantine:
            actions.append(Action(
                QUARANTINE_SOURCE, priority=80, target=name,
                reason="source failed repeatedly; stop retrying and surface it",
                evidence={"consecutive_failures": failures,
                          "last_error": health.get("last_error", "")[:200]},
            ))
            continue
        if health.get("failure_rate", 0.0) > t.max_source_failure_rate:
            actions.append(Action(
                ALERT, priority=60, target=name,
                reason="source is failing on a significant fraction of documents",
                evidence={"failure_rate": health.get("failure_rate")},
            ))
        if health.get("hours_since_success", 0.0) > t.stale_source_hours:
            actions.append(Action(
                BACKFILL_SOURCE, priority=50, target=name,
                reason="source has not been successfully read recently",
                evidence={"hours_since_success": round(health.get("hours_since_success", 0), 1)},
            ))

    # --- Blocked capabilities are a first-class finding, not a log line: they
    # mean the corpus is knowably incomplete.
    for note in situation.get("degradations", []):
        if not note.startswith("All probed"):
            actions.append(Action(
                ALERT, priority=40, target="access",
                reason="a required capability is unavailable; the corpus is incomplete",
                evidence={"degradation": note},
            ))

    # --- Quality.
    if situation.get("content_changed") and situation.get("documents", 0) >= t.min_docs_for_eval:
        actions.append(Action(
            RUN_EVAL, priority=30,
            reason="the corpus changed; retrieval quality must be re-measured",
            evidence={"documents": situation.get("documents")},
        ))

    pass_rate = situation.get("eval_pass_rate")
    if pass_rate is not None:
        if pass_rate < t.min_eval_pass_rate:
            actions.append(Action(
                ALERT, priority=90, target="eval",
                reason="retrieval quality is below the acceptable floor",
                evidence={"pass_rate": pass_rate, "floor": t.min_eval_pass_rate},
            ))
        previous = situation.get("previous_eval_pass_rate")
        if previous is not None and previous - pass_rate > t.eval_regression_tolerance:
            actions.append(Action(
                ALERT, priority=92, target="eval",
                reason="retrieval quality regressed against the previous cycle",
                evidence={"previous": previous, "current": pass_rate},
            ))

    if not actions:
        actions.append(Action(NOOP, priority=0, reason="all measured signals within thresholds"))

    actions.sort(key=lambda a: a.priority, reverse=True)
    return actions
