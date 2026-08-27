"""Data structures for the nightly self-improvement loop.

    Signal -> Finding -> Proposal -> EditOp -> Outcome

One idea carries the whole subsystem: **everything the user produces is a
`Signal`**. A prompt typed into a chat, a command typed into a shell, a file on
disk, a commit in git - all of them normalize to the same five fields (who,
when, where, what kind, what text). Detectors consume `Signal`s and never learn
where a signal came from, which is what makes a rule written for chat prompts
work unchanged on terminal history, and what makes adding a new source a
single class rather than a pass through every rule.

The chain is deliberately one-way and evidential. A `Finding` may not exist
without the `Evidence` that produced it; a `Proposal` may not exist without a
`Finding`; an `EditOp` may not be applied without a `Proposal` whose risk tier
allows it. That is what keeps a loop that edits your files on a timer from
being frightening: every byte it changes traces back to something you actually
did, and the `Outcome` of that change is recorded so the next cycle can learn
from it.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from oodarag.util.hashing import content_hash, stable_id

# Ordered so findings and proposals can be sorted and thresholded numerically
# without every call site re-deciding that "high" outranks "medium".
SEVERITY_ORDER: dict[str, int] = {"critical": 4, "high": 3, "medium": 2, "low": 1}

#: How much autonomy a proposal is allowed. The tier is a property of the
#: *edit*, not of the finding's importance: creating a missing file that
#: something already links to is `safe` even when the finding is trivial, and
#: rewriting a paragraph of someone's prose is `review` even when the finding is
#: critical. Only `safe` is ever applied without a human in the loop.
RISK_ORDER: dict[str, int] = {"safe": 1, "review": 2, "manual": 3}

#: Signal kinds. Sources may emit any string, but these are the ones detectors
#: are written against, so a new source should map onto them where it can.
KIND_PROMPT = "prompt"    # a human instruction (chat, issue, commit message body)
KIND_REPLY = "reply"      # an assistant/tool response to a prompt
KIND_COMMAND = "command"  # a shell invocation
KIND_FILE = "file"        # a file's contents at observation time
KIND_COMMIT = "commit"    # a recorded change to the corpus

ACTOR_HUMAN = "human"
ACTOR_ASSISTANT = "assistant"
ACTOR_MACHINE = "machine"


def _now() -> float:
    return time.time()


def day_key(ts: float) -> str:
    """Local-time YYYY-MM-DD.

    Local rather than UTC on purpose: this loop runs "at the end of *your*
    day", and a signal at 23:40 belongs to the day you experienced, not to
    whichever day it was in Greenwich.
    """
    return time.strftime("%Y-%m-%d", time.localtime(ts))


@dataclass(slots=True)
class Signal:
    """One observed act, from any source.

    `session` is the grouping key that makes sequence-aware rules possible: a
    chat conversation id, a shell session id, a day bucket for sources that
    have no session concept. Rules that look for "the user asked twice in a
    row" are meaningless across sessions, so they group by it.

    `ordinal` orders signals *within* a session. It exists because timestamps
    are unreliable at fine grain - shell history files record whole seconds, so
    six commands can share one timestamp and only their file order says which
    came first.
    """

    kind: str
    source: str
    text: str
    ts: float = field(default_factory=_now)
    uri: str = ""
    session: str = ""
    ordinal: int = 0
    actor: str = ACTOR_HUMAN
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def day(self) -> str:
        return day_key(self.ts)

    @property
    def fingerprint(self) -> str:
        """Identity of the *content*, so the same command run twice collapses."""
        return content_hash(self.kind, self.source, self.text)

    @property
    def preview(self) -> str:
        flat = " ".join(self.text.split())
        return flat if len(flat) <= 160 else flat[:157] + "..."

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Evidence:
    """A quotable observation behind a finding.

    Findings without evidence are opinions. The report prints these verbatim so
    a human can judge the rule's reasoning in one glance rather than trusting a
    score, and `uri`/`ts` make each one navigable back to the source.
    """

    quote: str
    uri: str = ""
    ts: float = 0.0
    session: str = ""
    source: str = ""

    @classmethod
    def from_signal(cls, sig: Signal, quote: str | None = None) -> Evidence:
        return cls(
            quote=quote if quote is not None else sig.preview,
            uri=sig.uri,
            ts=sig.ts,
            session=sig.session,
            source=sig.source,
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Finding:
    """Something observed that could be better.

    A finding is an *observation*, never an action - the split matters because
    the same observation ("you re-explained the test command four times this
    week") can justify very different actions depending on the repo, and
    because a finding the user dismisses should suppress the observation, not
    just one phrasing of the fix.

    `key` distinguishes findings from the same rule: the file path, the command,
    the phrase. It is what makes `fingerprint` stable across days, which is what
    lets the journal say "this is the fifth night in a row you ignored this".
    """

    rule_id: str
    title: str
    detail: str = ""
    severity: str = "medium"
    confidence: float = 0.5
    key: str = ""
    targets: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        return stable_id(self.rule_id, self.key or self.title, *sorted(self.targets)[:1])

    @property
    def severity_rank(self) -> int:
        return SEVERITY_ORDER.get(self.severity, 2)

    def as_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["fingerprint"] = self.fingerprint
        return out


@dataclass(slots=True)
class EditOp:
    """A single mechanical change to one file.

    Every operation is expressed so it can be checked *before* it runs and
    verified after: `create` requires the file to be absent, `replace` requires
    `old` to appear exactly once, `insert_after`/`ensure_section` require their
    anchor. An op whose precondition no longer holds is skipped rather than
    forced, because the loop runs unattended and the file may have changed since
    the proposal was written.
    """

    path: str
    op: str  # create | append | replace | insert_after | ensure_section
    text: str = ""
    anchor: str = ""
    old: str = ""
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Proposal:
    """A concrete, reviewable fix for one finding.

    `risk` gates autonomy and `score` gates attention. They are independent:
    the loop applies `safe` proposals in score order until its budget runs out,
    and queues everything else for review in score order, so a low-risk trivial
    fix never crowds out a high-risk important one - they are different lists.
    """

    finding: Finding
    title: str
    rationale: str = ""
    edits: list[EditOp] = field(default_factory=list)
    risk: str = "review"
    impact: float = 0.5
    effort: float = 0.5
    score: float = 0.0
    score_parts: dict[str, float] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Stable across nights so accept/dismiss decisions stick.

        Derived from the finding plus the *shape* of the fix (paths and ops, not
        their text), so rewording a suggestion does not resurrect something the
        user already dismissed, while genuinely proposing a different fix does.
        """
        shape = ";".join(f"{e.op}:{e.path}" for e in self.edits)
        return stable_id("proposal", self.finding.fingerprint, shape)

    @property
    def paths(self) -> list[str]:
        seen: list[str] = []
        for e in self.edits:
            if e.path not in seen:
                seen.append(e.path)
        return seen

    @property
    def risk_rank(self) -> int:
        return RISK_ORDER.get(self.risk, 2)

    def as_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "title": self.title,
            "rationale": self.rationale,
            "risk": self.risk,
            "impact": round(self.impact, 4),
            "effort": round(self.effort, 4),
            "score": round(self.score, 4),
            "score_parts": {k: round(v, 4) for k, v in self.score_parts.items()},
            "paths": self.paths,
            "edits": [e.as_dict() for e in self.edits],
            "finding": self.finding.as_dict(),
        }


@dataclass(slots=True)
class Outcome:
    """What became of a proposal. The training signal for the next cycle.

    `reverted` is deliberately distinct from `dismissed`: dismissing means the
    idea was wrong, reverting means the *edit* was wrong. The first should
    silence the rule, the second should make it more careful - and a rule whose
    edits keep getting reverted is worse than one whose ideas keep getting
    declined, so they are weighted differently in `decide.priors`.
    """

    fingerprint: str
    rule_id: str
    verdict: str  # applied | dismissed | reverted | deferred | failed
    ts: float = field(default_factory=_now)
    cycle_id: str = ""
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CycleReport:
    """One night's run, start to finish."""

    cycle_id: str
    started_at: float = field(default_factory=_now)
    ended_at: float = 0.0
    dry_run: bool = True
    window_start: float = 0.0
    signals: int = 0
    per_source: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    proposals: list[Proposal] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    queued: list[str] = field(default_factory=list)
    suppressed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    report_path: str = ""

    @property
    def duration_s(self) -> float:
        return round((self.ended_at or _now()) - self.started_at, 3)

    def as_dict(self, include_detail: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "cycle_id": self.cycle_id,
            "started_at": round(self.started_at, 3),
            "ended_at": round(self.ended_at, 3),
            "duration_s": self.duration_s,
            "dry_run": self.dry_run,
            "window_start": round(self.window_start, 3),
            "signals": self.signals,
            "per_source": self.per_source,
            "counts": {
                "findings": len(self.findings),
                "proposals": len(self.proposals),
                "applied": len(self.applied),
                "queued": len(self.queued),
                "suppressed": len(self.suppressed),
                "errors": len(self.errors),
            },
            "applied": self.applied,
            "queued": self.queued,
            "suppressed": self.suppressed,
            "errors": self.errors,
            "report_path": self.report_path,
        }
        if include_detail:
            out["proposals"] = [p.as_dict() for p in self.proposals]
        return out

    def to_json(self, include_detail: bool = True) -> str:
        return json.dumps(self.as_dict(include_detail), indent=2, ensure_ascii=False)
