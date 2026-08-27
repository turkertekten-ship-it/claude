"""The OODA loop that decides when the index is wrong, and does something.

A pipeline that only runs when a human types `index` is a pipeline whose index
is stale exactly as often as the human forgets. The loop closes that gap, and
it is structured as the four phases rather than as a cron job because the
interesting part is not *when* to re-fetch but *what the evidence says*:

  Observe   what the store holds, what each source reported, what is stale
  Orient    what that means — and specifically where it differs from expectation
  Decide    the smallest action that would test the reading, plus its falsifier
  Act       carry it out and capture the result as the next Observe

The phase that earns its place is **Orient**, and the field that earns its place
is `surprise`. A loop that never records a surprise has almost always skipped
Observe and is reasoning from what it expected to find. Making the surprise a
required output means an empty one is visible.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from oodarag.ingest.base import Connector, StateStore
from oodarag.pipeline import IngestReport, Pipeline
from oodarag.util.logging import get_logger

log = get_logger("loop")

#: A source untouched for longer than this is a re-fetch candidate. Six hours
#: is a working default for documentation and repository sources, which change
#: on the order of a day; a faster-moving source should set its own.
DEFAULT_STALE_AFTER_S = 6 * 3600


class Action(str, Enum):
    """What a cycle decided to do."""

    INGEST = "ingest"
    REINDEX = "reindex"
    NOTHING = "nothing"
    BLOCKED = "blocked"


@dataclass(slots=True)
class Observation:
    """Phase 1. Facts only — no interpretation belongs in this object."""

    documents: int = 0
    chunks: int = 0
    embeddings: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    stale_sources: list[str] = field(default_factory=list)
    unreachable: dict[str, str] = field(default_factory=dict)
    observed_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict[str, Any]:
        return {
            "documents": self.documents,
            "chunks": self.chunks,
            "embeddings": self.embeddings,
            "by_source": self.by_source,
            "stale_sources": self.stale_sources,
            "unreachable": self.unreachable,
        }


@dataclass(slots=True)
class Orientation:
    """Phase 2. The reading, and where reality diverged from expectation."""

    reading: str
    surprise: str = ""
    unknowns: list[str] = field(default_factory=list)

    @property
    def looked(self) -> bool:
        """A loop with no surprise and no unknowns probably did not observe."""
        return bool(self.surprise or self.unknowns)


@dataclass(slots=True)
class Decision:
    """Phase 3. One action, and the cheapest thing that would prove it wrong."""

    action: Action
    reason: str
    falsifier: str
    targets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CycleReport:
    """All four artifacts of one loop, kept together so none can be skipped."""

    observation: Observation
    orientation: Orientation
    decision: Decision
    result: IngestReport | None = None
    duration_s: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "observe": self.observation.as_dict(),
            "orient": {
                "reading": self.orientation.reading,
                "surprise": self.orientation.surprise,
                "unknowns": self.orientation.unknowns,
            },
            "decide": {
                "action": self.decision.action.value,
                "reason": self.decision.reason,
                "falsifier": self.decision.falsifier,
                "targets": self.decision.targets,
            },
            "act": self.result.as_dict() if self.result else {"skipped": True},
            "duration_s": round(self.duration_s, 3),
        }

    def render(self) -> str:
        o, r, d = self.observation, self.orientation, self.decision
        lines = [
            "OBSERVE",
            f"  {o.documents} document(s), {o.chunks} chunk(s), "
            f"{o.embeddings} embedding(s)",
            f"  by source: {o.by_source or '(none)'}",
            f"  stale: {o.stale_sources or '(none)'}",
        ]
        for key, reason in o.unreachable.items():
            lines.append(f"  unreachable: {key}: {reason[:90]}")
        lines += [
            "",
            "ORIENT",
            f"  reading:  {r.reading}",
            f"  surprise: {r.surprise or '(none recorded — did Observe actually look?)'}",
        ]
        for u in r.unknowns:
            lines.append(f"  unknown:  {u}")
        lines += [
            "",
            "DECIDE",
            f"  action:     {d.action.value}",
            f"  reason:     {d.reason}",
            f"  falsifier:  {d.falsifier}",
            "",
            "ACT",
        ]
        lines.append(
            "  " + (self.result.render().replace("\n", "\n  ") if self.result
                    else "(no action taken)")
        )
        return "\n".join(lines)


class OodaLoop:
    """Run cycles over a pipeline and a set of connectors."""

    def __init__(
        self,
        pipeline: Pipeline,
        connectors: list[Connector],
        *,
        state: StateStore | None = None,
        stale_after_s: float = DEFAULT_STALE_AFTER_S,
    ) -> None:
        self.pipeline = pipeline
        self.connectors = connectors
        self.state = state
        self.stale_after_s = stale_after_s

    # ------------------------------------------------------------- phase one

    def observe(self) -> Observation:
        stats = self.pipeline.stats()
        obs = Observation(
            documents=stats["documents"],
            chunks=stats["chunks"],
            embeddings=stats["embeddings"],
            by_source=dict(stats["by_source"]),
        )
        now = time.time()
        for connector in self.connectors:
            cursor = self.state.get(connector.key) if self.state else {}
            last = float(cursor.get("last_run", 0.0) or 0.0)
            if now - last > self.stale_after_s:
                obs.stale_sources.append(connector.key)
        return obs

    # ------------------------------------------------------------- phase two

    def orient(self, obs: Observation) -> Orientation:
        """Interpret, and name what did not match expectation.

        The surprises checked for are the ones that silently break a pipeline:
        an index with chunks but no vectors answers every dense query with
        nothing, and a source that contributed zero documents looks identical
        to a source that was never configured.
        """
        unknowns: list[str] = []
        surprises: list[str] = []

        if obs.documents == 0:
            reading = "the index is empty; nothing has been successfully ingested"
            surprises.append("a configured pipeline holds no documents at all")
        elif obs.chunks == 0:
            reading = "documents are stored but none are chunked, so nothing is retrievable"
            surprises.append("documents exist without chunks — chunking produced nothing")
        elif obs.embeddings < obs.chunks:
            reading = (
                f"{obs.chunks - obs.embeddings} chunk(s) have no vector; "
                "the dense arm cannot see them"
            )
            surprises.append("chunk and embedding counts disagree")
        elif obs.stale_sources:
            reading = f"{len(obs.stale_sources)} source(s) are past the staleness window"
        else:
            reading = "the index is populated and every source is within its window"

        configured = {c.key for c in self.connectors}
        contributing = set(obs.by_source)
        for connector in self.connectors:
            source_hint = connector.key.split(":")[0]
            if contributing and source_hint not in contributing:
                unknowns.append(
                    f"{connector.key} has contributed no documents; "
                    "unconfigured, empty, or unreachable is not distinguishable from here"
                )
        if not configured:
            unknowns.append("no connectors are configured, so staleness cannot be assessed")

        for key, reason in obs.unreachable.items():
            surprises.append(f"{key} was unreachable: {reason[:80]}")

        return Orientation(
            reading=reading,
            surprise="; ".join(surprises),
            unknowns=unknowns,
        )

    # ----------------------------------------------------------- phase three

    def decide(self, obs: Observation, orient: Orientation) -> Decision:
        """Choose the smallest action that would test the reading."""
        if obs.chunks and obs.embeddings < obs.chunks:
            return Decision(
                Action.REINDEX,
                reason=f"{obs.chunks - obs.embeddings} chunk(s) lack vectors",
                falsifier="after reindex, embeddings should equal chunks; if not, "
                          "the embedder is failing rather than the index being incomplete",
            )
        if not self.connectors:
            return Decision(
                Action.BLOCKED,
                reason="no connectors configured",
                falsifier="configure one source and the next cycle should ingest",
            )
        if obs.documents == 0 or obs.stale_sources:
            targets = obs.stale_sources or [c.key for c in self.connectors]
            return Decision(
                Action.INGEST,
                reason=("the index is empty" if obs.documents == 0
                        else f"{len(targets)} source(s) past the staleness window"),
                falsifier="if ingest reports every document unchanged, the sources were "
                          "not stale and the window is set too short",
                targets=targets,
            )
        return Decision(
            Action.NOTHING,
            reason="every source is within its window and the index is consistent",
            falsifier="a source that changed upstream without this loop noticing "
                      "means the window is too long",
        )

    # ------------------------------------------------------------ phase four

    def act(self, decision: Decision) -> IngestReport | None:
        if decision.action is Action.INGEST:
            targets = set(decision.targets)
            chosen = [c for c in self.connectors if not targets or c.key in targets]
            return self.pipeline.ingest(chosen, state=self.state)
        if decision.action is Action.REINDEX:
            written = self.pipeline.reindex()
            report = IngestReport(chunks_written=written)
            return report
        return None

    # ------------------------------------------------------------- the cycle

    def cycle(self) -> CycleReport:
        """One full loop. Every phase runs; none is skippable."""
        started = time.monotonic()
        obs = self.observe()
        orientation = self.orient(obs)
        decision = self.decide(obs, orientation)
        result = self.act(decision)

        if result is not None:
            obs.unreachable.update(result.unreachable)

        report = CycleReport(obs, orientation, decision, result,
                             time.monotonic() - started)
        log.info("cycle complete", action=decision.action.value,
                 documents=obs.documents, chunks=obs.chunks)
        return report

    def run(self, cycles: int = 1) -> list[CycleReport]:
        """Run several cycles, stopping early once there is nothing left to do.

        Stopping on NOTHING is what keeps a scheduled loop from re-running an
        identical no-op and reporting it as work.
        """
        out: list[CycleReport] = []
        for _ in range(max(1, cycles)):
            report = self.cycle()
            out.append(report)
            if report.decision.action in (Action.NOTHING, Action.BLOCKED):
                break
        return out
