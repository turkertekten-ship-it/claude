"""What the loop has learned about its own rules.

A detector shipped last night and a detector whose suggestions have been
accepted forty times running are not equally trustworthy, and nothing in a
rule's own code can tell them apart - only its record can. This module folds
the journal's verdicts into one number per rule, `confidence`, which the policy
engine multiplies into every score. A rule you keep dismissing therefore loses
the right to your attention on its own, without anybody editing a config file,
and a rule you keep accepting earns more of it.

Three choices carry the design.

**A reverted edit costs more than a dismissed idea.** Dismissing means the loop
noticed the wrong thing: you read one line in the queue and moved on, and the
cost to you was those few seconds. Reverting means the loop *changed a file* and
the change was wrong: you had to notice the damage, work out where it came from
and undo it - and for the time in between, you could not trust the working tree.
The second failure spends far more trust than the first, so it is weighted 2.0
against dismissal's 1.0. `failed` sits between them at 1.5: nothing was damaged,
but the rule proposed an edit whose preconditions did not hold, which means it
was reasoning about a file it does not actually understand, and that is a
sharper warning than merely being unwanted.

**Old verdicts fade.** Weights decay with a half-life so a rule that was bad in
January and good since is judged on what it has been doing lately. Without
decay a rule can never recover from a bad first week, which in practice means
nobody dares improve one - the punishment outlives the bug.

**Nothing starts at zero or one.** The counts are Laplace-smoothed, so an unseen
rule sits at exactly 0.5 rather than at 0 (never proposes, never earns a record,
stays at 0 forever) or at 1 (a brand-new rule outranks one with a year of
accepted proposals behind it). One accepted proposal moves a rule to 0.67, not
to certainty, which is about the right amount of evidence to read into it.
"""

from __future__ import annotations

import math
import time
from collections import Counter
from typing import Any

from oodarag.reflect.journal import Journal
from oodarag.util.logging import get_logger

log = get_logger("reflect.priors")

DAY_S = 86_400.0

#: verdict -> (success weight, failure weight). See the module docstring for why
#: the three ways of failing are not weighted alike. `deferred` is deliberately
#: worth nothing in both columns: it records that a human has not looked yet,
#: which is evidence about the human's evening, not about the rule.
VERDICT_WEIGHTS: dict[str, tuple[float, float]] = {
    "applied": (1.0, 0.0),
    "dismissed": (0.0, 1.0),
    "failed": (0.0, 1.5),
    "reverted": (0.0, 2.0),
    "deferred": (0.0, 0.0),
}

#: Nights of being ignored it takes for the nag to reach its cap.
NAG_SATURATION = 4.0


class RulePriors:
    """A Beta posterior per rule, folded from the journal at construction time.

    Folded once and cached: the CLI asks for the confidence of every registered
    rule in a loop, and the journal re-reads its file on every query, so a lazy
    implementation would read a year of outcomes once per rule.
    """

    def __init__(
        self,
        journal: Journal,
        half_life_days: float = 30.0,
        max_nag: float = 1.5,
        now: float | None = None,
    ) -> None:
        self.journal = journal
        #: A non-positive half-life means "do not decay", which is the honest
        #: reading of the number rather than a division by zero.
        self.half_life_days = max(0.0, half_life_days)
        self.max_nag = max(1.0, max_nag)
        #: Injectable so a test can age a verdict deterministically, and so a
        #: report can be re-rendered later as of the night it describes.
        self.now = now if now is not None else time.time()
        self._success: dict[str, float] = {}
        self._failure: dict[str, float] = {}
        self._counts: dict[str, Counter[str]] = {}
        self._suppressed: set[str] = set()
        self._nag: dict[str, float] = {}
        self._fold()

    # -- folding -------------------------------------------------------------

    def _fold(self) -> None:
        try:
            outcomes = self.journal.outcomes()
        except (OSError, ValueError) as e:
            # No journal, or an unreadable one, is a legitimate first night.
            # Every rule then sits at 0.5, which is exactly what an empty fold
            # means; refusing to run because of it would be theatre.
            log.warn("priors could not read outcomes", err=str(e)[:200])
            return
        for outcome in outcomes:
            if outcome.verdict == "dismissed" and outcome.fingerprint:
                self._suppressed.add(outcome.fingerprint)
            rule_id = outcome.rule_id
            if not rule_id:
                # A revert is recorded against a cycle rather than a rule, so
                # some outcomes cannot be attributed. They still suppress and
                # still appear in the journal; they just cannot train anything.
                continue
            success, failure = VERDICT_WEIGHTS.get(outcome.verdict, (0.0, 0.0))
            weight = self._decay(outcome.ts)
            self._success[rule_id] = self._success.get(rule_id, 0.0) + success * weight
            self._failure[rule_id] = self._failure.get(rule_id, 0.0) + failure * weight
            self._counts.setdefault(rule_id, Counter())[outcome.verdict] += 1

    def _decay(self, ts: float) -> float:
        """Exponential decay by half-life, clamped so nothing counts more than once."""
        if self.half_life_days <= 0 or ts <= 0:
            # A missing timestamp is an old journal or a hand-written record,
            # not a reason to discard the verdict entirely.
            return 1.0
        age_days = max(0.0, (self.now - ts) / DAY_S)
        return math.pow(0.5, age_days / self.half_life_days)

    # -- queries -------------------------------------------------------------

    def confidence(self, rule_id: str) -> float:
        """Posterior mean of Beta(1 + successes, 1 + failures). Always in (0, 1)."""
        successes = self._success.get(rule_id, 0.0)
        failures = self._failure.get(rule_id, 0.0)
        return (1.0 + successes) / (2.0 + successes + failures)

    def is_suppressed(self, fingerprint: str) -> bool:
        """True once the user has explicitly dismissed this exact proposal.

        Suppression is absolute rather than a penalty. "No" asked again a week
        later is the behaviour that makes people turn a tool off, and the
        dismissal is already recorded permanently in the journal, so honouring
        it costs nothing.
        """
        return bool(fingerprint) and fingerprint in self._suppressed

    def nag_factor(self, fingerprint: str) -> float:
        """A multiplier >= 1.0 that grows with how often this was already proposed.

        A suggestion that has sat in the queue five nights running is in one of
        two states: it matters more than its score says, or it should be
        dropped. The loop cannot tell which, and neither guess is safe to make
        silently - dropping it loses a real finding, repeating it unchanged
        forever is how a queue becomes wallpaper. Escalating it a bounded amount
        (at most `max_nag`, reached after `NAG_SATURATION` nights) is the honest
        middle: it surfaces once, near the top, where a human can settle the
        question by accepting or dismissing it. The cap is what keeps this from
        becoming a ratchet that eventually outranks everything on persistence
        alone.
        """
        if not fingerprint:
            return 1.0
        cached = self._nag.get(fingerprint)
        if cached is not None:
            return cached
        try:
            times = self.journal.times_proposed(fingerprint)
        except (OSError, ValueError):
            times = 0
        step = (self.max_nag - 1.0) / NAG_SATURATION
        factor = min(self.max_nag, 1.0 + max(0, times) * step)
        self._nag[fingerprint] = factor
        return factor

    def explain(self, rule_id: str) -> dict[str, Any]:
        """Everything behind one rule's number, for the nightly report.

        Both the decayed weights and the raw verdict counts, because they answer
        different questions: the weights say why the score came out where it did,
        the counts say what actually happened, and a reader who sees only the
        first has no way to check the second.
        """
        counts = self._counts.get(rule_id, Counter())
        return {
            "rule_id": rule_id,
            "confidence": round(self.confidence(rule_id), 4),
            "successes": round(self._success.get(rule_id, 0.0), 4),
            "failures": round(self._failure.get(rule_id, 0.0), 4),
            "verdicts": dict(sorted(counts.items())),
            "observations": sum(counts.values()),
            "half_life_days": self.half_life_days,
        }

    def suppressed_count(self) -> int:
        """How many proposals are permanently silenced. Shown in `reflect status`."""
        return len(self._suppressed)
