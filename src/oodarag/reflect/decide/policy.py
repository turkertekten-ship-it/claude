"""The gate: what gets done tonight, what waits for a person, what is dropped.

Orient produces more proposals than any evening deserves. This module turns
that pile into two short lists and a paper trail. Ranking answers "what is worth
doing"; gating answers "what is this loop allowed to do at 22:30 with nobody
watching". They are separate questions and they are asked in that order, because
a high score is an argument for attention, never for autonomy.

Two properties are worth more here than any tuning of the numbers.

**The score is a product of factors in [0, 1], scaled by the nag.** Severity,
the finding's own confidence, the rule's earned confidence and the proposal's
impact all multiply, then effort divides. That makes any single zero fatal - a
rule with no credibility cannot be rescued by a dramatic severity - and it keeps
the number readable: every part is written into `score_parts` so the report can
show the arithmetic rather than a bare 0.42 nobody can argue with.

**Nothing is dropped silently.** Every proposal that could have been applied and
was not leaves a sentence in `Decision.notes` saying which gate or budget
stopped it. A nightly job that quietly discards work is indistinguishable from
one that is broken, and the first time a user suspects that, the loop is over.
The notes are the difference between "it decided not to" and "it forgot".
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field

from oodarag.reflect.decide.priors import RulePriors
from oodarag.reflect.models import RISK_ORDER, SEVERITY_ORDER, Proposal
from oodarag.util.logging import get_logger

log = get_logger("reflect.policy")

_MAX_SEVERITY = max(SEVERITY_ORDER.values())

#: Globs this loop never edits unattended, matched against workspace-relative
#: paths. `.git/*` because rewriting repository internals is how a day's work
#: disappears; `*.lock` because a lockfile is generated, never authored;
#: `pyproject.toml` and `Makefile` because they are the build, and a wrong line
#: in either breaks everything downstream of it.
#:
#: `*.py` is the important one: **source code is never machine-edited by this
#: loop, at any risk tier.** A detector cannot know whether the line it is
#: rewriting is load-bearing, and an edit that is syntactically fine and
#: semantically wrong is exactly the kind of damage nobody notices until it
#: reaches production. The loop improves the material *around* the code - docs,
#: conventions, entry points - and reports on the code itself.
DEFAULT_PROTECTED_PATHS: tuple[str, ...] = (
    ".git/*",
    "*.lock",
    "pyproject.toml",
    "Makefile",
    "*.py",
)


def path_is_protected(relpath: str, patterns: tuple[str, ...]) -> bool:
    """Glob match against a workspace-relative path (`fnmatch`'s `*` spans `/`)."""
    return any(fnmatch.fnmatch(relpath, pattern) for pattern in patterns)


@dataclass(slots=True)
class PolicyConfig:
    """The whole autonomy envelope, in numbers a user can read and change.

    The budgets are small on purpose. They are not performance limits - applying
    fifty edits would take no longer than three - they are a bound on how much
    of a morning a bad night can cost. Three edits across five files is a diff
    somebody will actually read; two hundred is one they will revert wholesale,
    losing the good with the bad.
    """

    max_auto_edits: int = 3
    max_queued: int = 20
    max_files_touched: int = 5
    max_bytes_changed: int = 20_000
    min_score: float = 0.15
    allow_risk: str = "safe"
    #: Applying edits on top of uncommitted work makes "what changed, and who
    #: changed it" unanswerable: the user's diff and the loop's diff arrive in
    #: one undifferentiated blob, `git checkout` is no longer a safe undo, and
    #: the backups cannot be reasoned about without knowing which lines were
    #: already there. Waiting for a clean tree costs one night; the alternative
    #: costs the user's confidence that their own changes are still theirs.
    require_clean_tree: bool = True
    protected_paths: tuple[str, ...] = DEFAULT_PROTECTED_PATHS
    min_confidence: float = 0.25

    @property
    def allow_risk_rank(self) -> int:
        return RISK_ORDER.get(self.allow_risk, 1)


@dataclass(slots=True)
class Decision:
    """One night's verdict on the whole pile, plus the reasoning behind it."""

    apply: list[Proposal] = field(default_factory=list)
    queue: list[Proposal] = field(default_factory=list)
    suppressed: list[Proposal] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class PolicyEngine:
    def __init__(self, config: PolicyConfig, priors: RulePriors) -> None:
        self.config = config
        self.priors = priors

    # -- ranking -------------------------------------------------------------

    def score(self, proposal: Proposal) -> float:
        """Rank one proposal, recording the arithmetic in `score_parts`.

        Severity is normalized against the highest tier so it lands in (0, 1]
        like the other factors; effort divides rather than multiplies so that
        zero effort is neutral instead of fatal.
        """
        finding = proposal.finding
        severity = _clamp01(finding.severity_rank / _MAX_SEVERITY)
        confidence = _clamp01(finding.confidence)
        prior = _clamp01(self.priors.confidence(finding.rule_id))
        impact = _clamp01(proposal.impact)
        nag = max(1.0, self.priors.nag_factor(proposal.fingerprint))
        effort = max(0.0, proposal.effort)

        score = severity * confidence * prior * impact * nag / (1.0 + effort)
        proposal.score_parts = {
            "severity": severity,
            "confidence": confidence,
            "prior": prior,
            "impact": impact,
            "nag": nag,
            "effort": effort,
            "score": score,
        }
        proposal.score = score
        return score

    # -- gating --------------------------------------------------------------

    def decide(self, proposals: list[Proposal], *, tree_clean: bool) -> Decision:
        """Split tonight's proposals into apply / queue / suppressed, with reasons."""
        decision = Decision()
        ranked: list[Proposal] = []

        for proposal in proposals:
            if self.priors.is_suppressed(proposal.fingerprint):
                decision.suppressed.append(proposal)
                decision.notes.append(
                    f"{_tag(proposal)} suppressed: you dismissed this before, "
                    f"so it is not proposed again"
                )
                continue
            self.score(proposal)
            ranked.append(proposal)

        # Ties broken on rule then title so two runs over the same night produce
        # the same order - a report that reshuffles itself cannot be diffed.
        ranked.sort(key=lambda p: (-p.score, p.finding.rule_id, p.title))

        if self.config.require_clean_tree and not tree_clean:
            decision.notes.append(
                "working tree has uncommitted changes: nothing is applied tonight, "
                "so your diff stays yours alone"
            )

        edits_used = 0
        files_touched: set[str] = set()
        bytes_used = 0

        for proposal in ranked:
            reason = self._blocking_reason(
                proposal,
                tree_clean=tree_clean,
                edits_used=edits_used,
                files_touched=files_touched,
                bytes_used=bytes_used,
            )
            if reason is None:
                decision.apply.append(proposal)
                # Counted per proposal rather than per `EditOp`: the actuator
                # applies a proposal all-or-nothing, so the proposal is the unit
                # a person reviews in the morning.
                edits_used += 1
                files_touched.update(proposal.paths)
                bytes_used += _bytes_of(proposal)
                continue

            if len(decision.queue) < self.config.max_queued:
                decision.queue.append(proposal)
                decision.notes.append(f"{_tag(proposal)} queued: {reason}")
            else:
                decision.notes.append(
                    f"{_tag(proposal)} dropped: {reason}, and the review queue is "
                    f"full at {self.config.max_queued}; it will be proposed again "
                    f"next run"
                )

        log.info(
            "decided",
            applied=len(decision.apply),
            queued=len(decision.queue),
            suppressed=len(decision.suppressed),
            tree_clean=tree_clean,
        )
        return decision

    def _blocking_reason(
        self,
        proposal: Proposal,
        *,
        tree_clean: bool,
        edits_used: int,
        files_touched: set[str],
        bytes_used: int,
    ) -> str | None:
        """Why this proposal may not be applied unattended, or None if it may.

        Checks run most-specific first, so the sentence a user reads names the
        real obstacle rather than whichever one happened to be tested earliest.
        """
        cfg = self.config

        if not proposal.edits:
            return "it carries no edits; it is an observation, reported only"

        if proposal.risk_rank > cfg.allow_risk_rank:
            return (
                f"risk tier '{proposal.risk}' needs a person; only "
                f"'{cfg.allow_risk}' edits are applied unattended"
            )

        if proposal.score < cfg.min_score:
            return (
                f"score {proposal.score:.3f} is below the attention floor of "
                f"{cfg.min_score:.3f}"
            )

        prior = self.priors.confidence(proposal.finding.rule_id)
        if prior < cfg.min_confidence:
            return (
                f"rule {proposal.finding.rule_id} has earned confidence "
                f"{prior:.2f}, below the {cfg.min_confidence:.2f} needed to act "
                f"unattended; accept one of its proposals and it will apply itself"
            )

        protected = [p for p in proposal.paths if path_is_protected(p, cfg.protected_paths)]
        if protected:
            return f"it would edit protected path {protected[0]!r}, which is never machine-edited"

        if cfg.require_clean_tree and not tree_clean:
            return "the working tree has uncommitted changes"

        if edits_used >= cfg.max_auto_edits:
            return f"tonight's budget of {cfg.max_auto_edits} automatic edits is spent"

        new_files = [p for p in proposal.paths if p not in files_touched]
        if len(files_touched) + len(new_files) > cfg.max_files_touched:
            return (
                f"applying it would touch {len(files_touched) + len(new_files)} files, "
                f"over the limit of {cfg.max_files_touched}"
            )

        size = _bytes_of(proposal)
        if bytes_used + size > cfg.max_bytes_changed:
            return (
                f"its {size} bytes would take the night past the "
                f"{cfg.max_bytes_changed}-byte change budget"
            )

        return None


# -- helpers -----------------------------------------------------------------


def _clamp01(value: float) -> float:
    """Keep a detector's stray 1.4 or -0.2 from inverting the ranking."""
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _bytes_of(proposal: Proposal) -> int:
    """Bytes this proposal would write. UTF-8 length, not character count."""
    return sum(len(edit.text.encode("utf-8", "replace")) for edit in proposal.edits)


def _tag(proposal: Proposal) -> str:
    """The short handle a user sees in the queue, so a note can be matched to a row."""
    return f"{proposal.fingerprint[:8]} ({proposal.finding.rule_id})"
