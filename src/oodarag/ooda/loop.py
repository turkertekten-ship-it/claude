"""The control loop: the pipeline steering itself, in four separable phases.

An OODA loop whose phases bleed into each other is just a cron job with better
branding. The value is not in the four names; it is in the fact that each phase
can be exercised, argued about and tested on its own. So the boundaries here are
mechanical rather than aspirational:

**`observe` states facts and nothing else.** Counts out of the store, cursor
timestamps out of the state file, the last eval numbers, the errors that already
happened. It never says a source is *too* old - only how old it is against the
interval that source declared. The moment a threshold appears in Observe, the
policy is scattered across two phases and can no longer be changed in one place.

**`orient` turns facts into scores in [0,1] and touches no IO.** Every formula
is one named pure function (`staleness_score`, `quality_score`, `index_deficit`)
so the number in a cycle report can be reproduced from the report itself.

**`decide` is a pure function of `(Orientation, Observation)`.** No clock, no
network, no store, no logging - not even a log line, because purity you have to
remember to maintain is purity you will lose. A policy change is therefore
testable with two literal dataclasses and no fixtures at all, which is the only
reason anyone will actually test it. It reads `self.policy` and its arguments;
that is the whole of its input.

**`act` is the only phase permitted to mutate anything**, and it is the only one
that can be skipped: `policy.dry_run` is checked once, centrally, before any
handler runs, because a handler that forgets the check is a dry run that writes.

Three consequences of that split worth knowing before reading the code:

*Deltas arrive one cycle late, on purpose.* `observe` cannot run connectors -
that is a mutation - so the `IngestDelta`s it reports are the ones the previous
cycle's `act` produced. The loop therefore reacts to what its last action
actually did, rather than to what it hoped that action would do, and cycle one
correctly reports no evidence rather than fabricating some.

*A reingest does not bundle its own reindex.* It marks the in-memory indexes
stale and stops; the next cycle observes the deficit and decides to rebuild.
Bundling would be one line shorter and would make the cycle report unable to
explain why a rebuild happened. Nothing is broken in between - `Pipeline.ask`
rebuilds on demand - so the reindex action is about moving that cost out of the
first query's latency and into a decision that is visible.

*Unknown quality is not zero quality.* With no goldens configured there is no
eval report, and an absent measurement scored as 0.0 would have the loop
alerting forever about a number nobody ever asked it to measure. Unmeasured
quality scores 1.0 and `decide` additionally refuses to apply the quality floor
unless a report is actually present.

Every phase degrades instead of raising: an unreadable state file, a missing
eval harness, a connector that cannot resolve its own hostname all land in
`Observation.errors` or in a result dict with `ok=False`. A control loop that
crashes when the world misbehaves is a control loop for a world that does not
need one.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import IngestDelta
from oodarag.pipeline import Pipeline
from oodarag.util.logging import get_logger

log = get_logger("ooda")

#: How often a source is expected to be re-fetched when it does not say.
#: `Connector` (frozen in CONTRACTS.md) declares no refresh interval, so one is
#: read off the instance as `refresh_interval_s` when present and defaulted here
#: when not. Six hours: long enough that a docs corpus is not re-fetched all day,
#: short enough that a day-old answer is never served without the loop noticing.
DEFAULT_REFRESH_INTERVAL_S = 6 * 3600.0

#: Share of attempted documents that may fail before a human is told. Below this
#: an ingest is degraded; above it the source is broken and no amount of
#: re-fetching by the loop will fix it.
ERROR_RATE_ALERT = 0.2

#: Recall leads the quality blend because it is the ceiling: what retrieval never
#: fetched, no reranker and no generator can recover. MRR describes the ordering
#: *within* what was fetched, which is a smaller and more recoverable problem.
RECALL_WEIGHT = 0.6

#: Magnitude assigned to "the in-memory indexes were never built over this
#: store". The count deficit is 0 in that case - the numbers agree, they were
#: just never loaded - so without a floor a rebuild would rank below every other
#: candidate and never fit in the action budget.
UNBUILT_INDEX_MAGNITUDE = 0.5

#: Expected value of one unit of each action's magnitude. The order encodes cost
#: against reach: a reindex is seconds of local CPU and fixes every query at
#: once; a reingest is network but repairs the input to everything downstream; a
#: backfill re-fetches whole sources for a less certain payoff; retune and alert
#: change no data at all and only ask a human to do something.
ACTION_VALUE = {
    "reindex": 1.0,
    "reingest": 0.8,
    "backfill": 0.6,
    "retune": 0.45,
    "alert": 0.35,
    "noop": 0.0,
}

#: Errors carried in one Observation. A source failing on every one of 4,000
#: documents is fully described by the first twenty, and the cycle report is
#: serialized into logs.
MAX_ERRORS_CARRIED = 20

#: Failing goldens quoted into an action's params. The full list stays in the
#: eval report; this is the part a human reads in a terminal.
MAX_GAPS_REPORTED = 8

#: Targets meaning "every connector this loop was given".
ALL_TARGETS = ("", "*", "all")


# ---- scoring primitives -------------------------------------------------
#
# Public and pure, so a number in a cycle report can be re-derived from the
# report's own facts, and so `orient` and `decide` can never drift into two
# slightly different versions of the same formula.


def staleness_score(age_s: float | None, interval_s: float) -> float:
    """How overdue one source is, in [0,1].

        score = clamp((age - interval) / interval, 0, 1)

    0.0 while the source is still within its refresh interval, 1.0 once it is a
    full interval past due, linear in between. Expressed as *overdue* rather
    than as elapsed fraction because `LoopPolicy.staleness_threshold` reads as
    "how far past due is too far" - with an elapsed-fraction formula the default
    of 0.25 would re-fetch every source a quarter of the way through its own
    interval, which is not a policy anyone would write down on purpose.

    A source with no recorded run scores 1.0: there is no evidence any of its
    documents ever landed, which is the most stale a source can be.
    """
    if age_s is None:
        return 1.0
    interval = max(float(interval_s), 1.0)
    return _clamp01((float(age_s) - interval) / interval)


def quality_score(recall_at_k: float, mrr: float) -> float:
    """Blend the two retrieval metrics into one [0,1] score.

        score = 0.6 * recall@k + 0.4 * MRR

    See `RECALL_WEIGHT` for why recall leads.
    """
    return _clamp01(RECALL_WEIGHT * _num(recall_at_k) + (1.0 - RECALL_WEIGHT) * _num(mrr))


def index_deficit(stats: Mapping[str, Any]) -> float:
    """How far the in-memory indexes are from the store, in [0,1].

        deficit = max(|bm25 - chunks| / chunks, |dense - vectors| / vectors)

    Absolute difference, not a shortfall: an index holding 40,000 entries over a
    store of 12 is exactly as wrong as one holding 12 over 40,000, and only the
    first is survivable by accident - it answers, confidently, out of documents
    that were deleted.
    """
    chunks, vectors = _num(stats.get("chunks")), _num(stats.get("vectors"))
    gaps = []
    if chunks > 0:
        gaps.append(abs(_num(stats.get("bm25_chunks")) - chunks) / chunks)
    if vectors > 0:
        gaps.append(abs(_num(stats.get("dense_vectors")) - vectors) / vectors)
    return _clamp01(max(gaps, default=0.0))


# ---- phase payloads -----------------------------------------------------


@dataclass(slots=True)
class Observation:
    """Observe: facts about the world, no judgement."""

    stats: dict[str, Any]
    deltas: list[IngestDelta]
    eval_report: dict[str, Any] | None = None
    stale_sources: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Orientation:
    """Orient: what the facts mean, scored."""

    staleness: float  # 0..1
    quality: float  # 0..1, from the eval report
    error_rate: float
    coverage_gaps: list[str]
    notes: list[str]


@dataclass(slots=True)
class Action:
    kind: str  # reingest | reindex | retune | backfill | alert | noop
    target: str = ""
    reason: str = ""
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LoopPolicy:
    staleness_threshold: float = 0.25
    quality_floor: float = 0.55
    max_actions_per_cycle: int = 3
    dry_run: bool = False


@dataclass(slots=True)
class CycleReport:
    cycle: int
    observation: Observation
    orientation: Orientation
    decided: list[Action]
    results: list[dict[str, Any]]
    duration_s: float

    def as_dict(self) -> dict[str, Any]:
        obs, orient = self.observation, self.orientation
        return {
            "cycle": self.cycle,
            "duration_s": round(self.duration_s, 3),
            "observation": {
                "stats": obs.stats,
                "deltas": [d.as_dict() for d in obs.deltas],
                "eval_report": obs.eval_report,
                "stale_sources": list(obs.stale_sources),
                "errors": list(obs.errors),
            },
            "orientation": {
                "staleness": round(orient.staleness, 4),
                "quality": round(orient.quality, 4),
                "error_rate": round(orient.error_rate, 4),
                "coverage_gaps": list(orient.coverage_gaps),
                "notes": list(orient.notes),
            },
            "decided": [asdict(a) for a in self.decided],
            "results": [dict(r) for r in self.results],
        }

    def render(self) -> str:
        """Four blocks, one per phase, for a terminal or a log.

        The phases are printed separately for the same reason they are coded
        separately: reading "decided: reingest" without the staleness number
        above it leaves the reader unable to tell a working policy from a stuck
        one.
        """
        obs, orient = self.observation, self.orientation
        stats = obs.stats
        lines = [f"OODA cycle {self.cycle}  ({self.duration_s:.2f}s)"]

        lines.append(
            "  OBSERVE  "
            + "  ".join(
                [
                    f"docs={_show(stats.get('documents'))}",
                    f"chunks={_show(stats.get('chunks'))}",
                    f"vectors={_show(stats.get('vectors'))}",
                    f"sources={len(stats.get('sources') or {})}",
                    f"deltas={len(obs.deltas)}",
                    f"stale={len(obs.stale_sources)}",
                    f"errors={len(obs.errors)}",
                ]
            )
        )
        if obs.eval_report:
            lines.append(
                "           eval  "
                + "  ".join(
                    [
                        f"n={_show(obs.eval_report.get('n'))}",
                        f"recall@k={_num(obs.eval_report.get('recall_at_k')):.3f}",
                        f"mrr={_num(obs.eval_report.get('mrr')):.3f}",
                        f"citations={_num(obs.eval_report.get('citation_coverage')):.3f}",
                    ]
                )
            )
        if obs.stale_sources:
            lines.append("           past due: " + _join(obs.stale_sources, 4))
        for err in obs.errors[:2]:
            lines.append(f"           ! {_cut(err, 84)}")

        lines.append(
            f"  ORIENT   staleness={orient.staleness:.2f}  quality={orient.quality:.2f}  "
            f"error_rate={orient.error_rate:.2f}  gaps={len(orient.coverage_gaps)}"
        )
        for note in orient.notes[:4]:
            lines.append(f"           - {_cut(note, 84)}")

        lines.append(f"  DECIDE   {len(self.decided)} action(s)")
        for i, action in enumerate(self.decided, 1):
            target = f" {action.target}" if action.target else ""
            ev = action.params.get("expected_value")
            suffix = f" [ev={ev}]" if isinstance(ev, (int, float)) else ""
            reason = _cut(action.reason, 66)
            lines.append(f"           {i}. {action.kind}{target}{suffix}  {reason}")

        lines.append(f"  ACT      {len(self.results)} result(s)")
        for result in self.results:
            mark = "ok " if result.get("ok") else "FAIL"
            dry = "would " if result.get("dry_run") else ""
            target = f" {result.get('target')}" if result.get("target") else ""
            detail = result.get("error") or result.get("detail") or ""
            lines.append(
                f"           {mark} {dry}{result.get('kind')}{target} "
                f"{_num(result.get('duration_s')):.2f}s  {_cut(str(detail), 56)}".rstrip()
            )
        return "\n".join(lines)


class OodaLoop:
    """Observe -> Orient -> Decide -> Act over a live pipeline."""

    def __init__(
        self,
        pipeline: Pipeline,
        connectors: Sequence[Connector],
        policy: LoopPolicy | None = None,
        goldens_path: str | Path | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.connectors = list(connectors)
        self.policy = policy or LoopPolicy()
        self.goldens_path = Path(goldens_path) if goldens_path is not None else None

        self._cycle = 0
        # What the previous cycle's `act` produced. Observe reports these rather
        # than running connectors itself; `act` reassigns the list every cycle,
        # including to empty, so a cycle that acted on nothing cannot inherit the
        # error rate of a cycle that did.
        self._last_deltas: list[IngestDelta] = []
        # Last eval numbers plus the store fingerprint they were measured over.
        # Retrieval quality cannot move while documents, chunks and vectors all
        # sit still, so re-running the goldens against an unchanged store would
        # buy a number that is already known and pay full query cost for it.
        self._eval_cache: dict[str, Any] | None = None
        self._eval_fingerprint: tuple[float, float, float] | None = None

        log.info(
            "loop ready",
            connectors=len(self.connectors),
            goldens=str(self.goldens_path) if self.goldens_path else "-",
            dry_run=self.policy.dry_run,
        )

    # ---- observe ---------------------------------------------------------

    def observe(self) -> Observation:
        """Read the world. No thresholds, no verdicts, no writes.

        Ordering matters in one place: the store and index counts are read
        *before* quality is measured, because measuring quality runs queries and
        `Pipeline.ask` builds the in-memory indexes on demand. Read after, they
        would always report freshly-built indexes and the loop could never
        observe - and so never repair - an index that is behind its store.
        """
        now = time.time()
        errors: list[str] = []

        stats = self._read_stats(errors)
        cursors = self._read_cursors(now, errors)
        # Per-source clock facts live under `stats` because Observation's field
        # list is frozen in CONTRACTS.md and this is the one shape it has for
        # arbitrary facts. Keeping them in the Observation (rather than reading
        # them again later) is what lets `orient` and `decide` stay functions of
        # their arguments alone.
        stats["cursors"] = cursors

        # A clock comparison, not a verdict: a source is "past due" when more
        # time has elapsed than the interval it declared. Whether that *matters*
        # is `staleness_threshold`, and it is applied two phases from here.
        stale = [
            key
            for key, cursor in cursors.items()
            if cursor["age_s"] is None or cursor["age_s"] > cursor["interval_s"]
        ]

        deltas = list(self._last_deltas)
        for delta in deltas:
            _extend_capped(errors, [f"{delta.source_key}: {e}" for e in delta.errors])

        observation = Observation(
            stats=stats,
            deltas=deltas,
            eval_report=self._read_eval(stats, errors),
            stale_sources=stale,
            errors=errors,
        )
        log.info(
            "observe",
            cycle=self._cycle,
            documents=stats.get("documents", "?"),
            chunks=stats.get("chunks", "?"),
            stale=len(stale),
            deltas=len(deltas),
            errors=len(errors),
        )
        return observation

    def _read_stats(self, errors: list[str]) -> dict[str, Any]:
        try:
            return dict(self.pipeline.stats())
        except Exception as e:  # a locked or corrupt index must not end the loop
            _extend_capped(errors, [f"stats: {type(e).__name__}: {e}"])
            log.error("stats unreadable", err=f"{type(e).__name__}: {e}"[:200])
            return {}

    def _read_cursors(self, now: float, errors: list[str]) -> dict[str, dict[str, Any]]:
        """Each connector's last run, its declared interval, and the gap between.

        A cursor that cannot be read is reported as a source that has never run.
        That is the honest reading - there is no evidence of a run - and its cost
        is one redundant re-fetch, which incremental ingest absorbs at the far
        end because unchanged content hashes stop before anything is re-embedded.
        """
        state = getattr(self.pipeline, "state", None)
        cursors: dict[str, dict[str, Any]] = {}

        for connector in self.connectors:
            key = str(getattr(connector, "key", type(connector).__name__))
            if key in cursors:
                # Two connectors sharing a key also share one cursor slot in the
                # state store, so each run erases the other's incremental state.
                _extend_capped(errors, [f"duplicate connector key: {key}"])
                continue

            interval = _num(getattr(connector, "refresh_interval_s", None), 0.0)
            if interval <= 0:
                interval = DEFAULT_REFRESH_INTERVAL_S

            last_run: float | None = None
            try:
                raw = state.get(key).get("last_run") if state is not None else None
                last_run = float(raw) if isinstance(raw, (int, float)) else None
            except Exception as e:
                _extend_capped(errors, [f"cursor {key}: {type(e).__name__}: {e}"])

            age: float | None = None
            if last_run is not None:
                if last_run > now + 60.0:
                    # Clock skew or a restored backup. It reads as freshly run
                    # forever, so it is surfaced rather than silently trusted.
                    _extend_capped(errors, [f"cursor {key}: last_run is in the future"])
                age = max(0.0, now - last_run)

            cursors[key] = {
                "last_run": last_run,
                "age_s": None if age is None else round(age, 1),
                "interval_s": interval,
            }
        return cursors

    def _read_eval(self, stats: Mapping[str, Any], errors: list[str]) -> dict[str, Any] | None:
        """The current eval numbers, re-measured only when the store has moved.

        Measurement is a read: it asks questions, it does not change the corpus.
        The harness is imported here rather than at module scope so this module
        loads - and the loop runs on staleness and errors alone - in an install
        where `oodarag.evals` is absent.
        """
        if self.goldens_path is None:
            return None

        fingerprint = (_num(stats.get("documents")), _num(stats.get("chunks")),
                       _num(stats.get("vectors")))
        if self._eval_cache is not None and self._eval_fingerprint == fingerprint:
            return self._eval_cache

        try:
            from oodarag.evals.harness import evaluate, load_goldens
        except ImportError as e:
            _extend_capped(errors, [f"evals unavailable: {e}"])
            return self._eval_cache

        try:
            goldens = load_goldens(self.goldens_path)
            report = evaluate(self.pipeline, goldens)
            payload = report.as_dict() if hasattr(report, "as_dict") else _as_dict(report)
        except Exception as e:
            # The previous numbers are kept rather than degraded to zeros: a
            # harness that failed to run is not a pipeline that answers badly,
            # and scoring it as one would have the loop retuning against noise.
            _extend_capped(errors, [f"eval: {type(e).__name__}: {e}"])
            log.error("eval failed", err=f"{type(e).__name__}: {e}"[:200])
            return self._eval_cache

        self._eval_cache = dict(payload)
        self._eval_fingerprint = fingerprint
        log.info(
            "evaluated",
            n=payload.get("n"),
            recall=payload.get("recall_at_k"),
            mrr=payload.get("mrr"),
        )
        return self._eval_cache

    # ---- orient ----------------------------------------------------------

    def orient(self, obs: Observation) -> Orientation:
        """Score the facts. Arithmetic only - no IO, and no clock.

        The clock is deliberately absent: every age was frozen in `observe`, so
        orienting the same Observation twice gives the same scores, and a cycle
        report can be replayed months later and still add up.
        """
        cursors = obs.stats.get("cursors") or {}
        per_source = {
            key: staleness_score(cursor.get("age_s"), _num(cursor.get("interval_s"),
                                                           DEFAULT_REFRESH_INTERVAL_S))
            for key, cursor in cursors.items()
            if isinstance(cursor, dict)
        }
        # Max, not mean: averaging lets nine fresh sources hide one dead one, and
        # the dead one is the entire reason to run a loop.
        staleness = max(per_source.values(), default=0.0)

        report = obs.eval_report
        if report:
            quality = quality_score(_num(report.get("recall_at_k")), _num(report.get("mrr")))
        else:
            quality = 1.0  # unmeasured, not bad - see the module docstring

        # Denominator is every document the connectors attempted, not just the
        # ones they touched: `IngestDelta.touched` excludes unchanged documents,
        # so dividing by it would report one unreadable file in a 4,000-file
        # repository as a 100% failure rate and trigger an alert every cycle.
        failed = sum(d.failed for d in obs.deltas)
        attempted = sum(d.new + d.changed + d.unchanged + d.failed for d in obs.deltas)
        error_rate = failed / attempted if attempted else 0.0

        gaps = _failing_goldens(report)

        notes: list[str] = []
        if per_source:
            worst = max(per_source, key=lambda k: per_source[k])
            overdue = [k for k, v in per_source.items() if v > 0.0]
            notes.append(
                f"{len(overdue)} of {len(per_source)} sources overdue; "
                f"worst {worst} at {per_source[worst]:.2f}"
            )
        if report:
            notes.append(
                f"quality {quality:.2f} from recall@k={_num(report.get('recall_at_k')):.2f}, "
                f"mrr={_num(report.get('mrr')):.2f} over n={_show(report.get('n'))}"
            )
        else:
            notes.append("quality unmeasured: no goldens configured, scored as passing")
        if gaps:
            notes.append(f"{len(gaps)} golden(s) currently failing: {_join(gaps, 2)}")
        if failed:
            notes.append(f"{failed} of {attempted} documents failed last ingest")
        deficit = index_deficit(obs.stats)
        if deficit > 0 or not obs.stats.get("indexes_built", True):
            notes.append(
                f"indexes {'unbuilt' if not obs.stats.get('indexes_built', True) else 'behind'} "
                f"(deficit {deficit:.2f})"
            )
        if obs.errors:
            notes.append(f"{len(obs.errors)} error(s) recorded while observing")

        orientation = Orientation(
            staleness=staleness,
            quality=quality,
            error_rate=error_rate,
            coverage_gaps=gaps,
            notes=notes,
        )
        log.info(
            "orient",
            cycle=self._cycle,
            staleness=round(staleness, 3),
            quality=round(quality, 3),
            error_rate=round(error_rate, 3),
            gaps=len(gaps),
        )
        return orientation

    # ---- decide ----------------------------------------------------------

    def decide(self, orientation: Orientation, obs: Observation) -> list[Action]:
        """Apply the policy. Pure: same inputs, same actions, every time.

        Nothing in here reads the clock, the network, the store or `self` beyond
        `self.policy`, and nothing in here logs. That is what makes a policy
        change testable from two literal dataclasses - and it is the reason the
        loop's most opinionated code is also its cheapest code to argue about.

        Candidates are scored as `ACTION_VALUE[kind] * magnitude` and the budget
        goes to the highest first. The scores are not probabilities; they exist
        to make the ordering explicit and reviewable rather than an artifact of
        the order the `if` statements happen to be written in.
        """
        policy = self.policy
        candidates: list[tuple[float, Action]] = []
        cursors = obs.stats.get("cursors") or {}

        # -- stale sources -> reingest.
        # Orientation.staleness is the max over these, so testing each source
        # individually fires exactly when the aggregate would, and names which.
        for key in obs.stale_sources:
            cursor = cursors.get(key) or {}
            interval = _num(cursor.get("interval_s"), DEFAULT_REFRESH_INTERVAL_S)
            score = staleness_score(cursor.get("age_s"), interval)
            if score <= policy.staleness_threshold:
                continue
            age = cursor.get("age_s")
            elapsed = "never run" if age is None else f"last run {_duration(_num(age))} ago"
            candidates.append(
                (
                    ACTION_VALUE["reingest"] * score,
                    Action(
                        kind="reingest",
                        target=key,
                        reason=(
                            f"{elapsed}, {score:.2f} overdue against a "
                            f"{_duration(interval)} refresh interval "
                            f"(> {policy.staleness_threshold:g})"
                        ),
                        params={"staleness": round(score, 4), "interval_s": interval},
                    ),
                )
            )

        # -- indexes behind the store -> reindex.
        deficit = index_deficit(obs.stats)
        built = bool(obs.stats.get("indexes_built", True))
        if _num(obs.stats.get("chunks")) > 0 and (deficit > 0.0 or not built):
            magnitude = max(deficit, 0.0 if built else UNBUILT_INDEX_MAGNITUDE)
            candidates.append(
                (
                    ACTION_VALUE["reindex"] * magnitude,
                    Action(
                        kind="reindex",
                        target="store",
                        reason=(
                            f"in-memory indexes {'not built' if not built else 'behind'}: "
                            f"bm25={_show(obs.stats.get('bm25_chunks'))}/"
                            f"{_show(obs.stats.get('chunks'))} chunks, "
                            f"dense={_show(obs.stats.get('dense_vectors'))}/"
                            f"{_show(obs.stats.get('vectors'))} vectors"
                        ),
                        params={"deficit": round(deficit, 4), "indexes_built": built},
                    ),
                )
            )

        # -- goldens failing for want of material -> backfill.
        # Gated on the share of failures rather than on any failure, and gated
        # again on the previous cycle's evidence: if the last ingest already ran
        # and brought in nothing, the missing answers are not missing because of
        # a fetch, and re-fetching every source each cycle is a livelock with a
        # network bill attached.
        gaps = orientation.coverage_gaps
        total = max(_num((obs.eval_report or {}).get("n")), float(len(gaps)))
        gap_ratio = len(gaps) / total if total else 0.0
        fetch_was_productive = not obs.deltas or any(d.touched for d in obs.deltas)
        if gaps and gap_ratio > (1.0 - policy.quality_floor) and fetch_was_productive:
            candidates.append(
                (
                    ACTION_VALUE["backfill"] * gap_ratio,
                    Action(
                        kind="backfill",
                        target="*",
                        reason=(
                            f"{len(gaps)} of {int(total)} goldens fail "
                            f"({gap_ratio:.0%} > {1.0 - policy.quality_floor:.0%}); "
                            "re-fetching sources ignoring incremental cursors"
                        ),
                        params={"gaps": gaps[:MAX_GAPS_REPORTED],
                                "gap_ratio": round(gap_ratio, 4)},
                    ),
                )
            )
        elif gaps and not fetch_was_productive:
            candidates.append(
                (
                    ACTION_VALUE["alert"] * gap_ratio,
                    Action(
                        kind="alert",
                        target="coverage",
                        reason=(
                            f"{len(gaps)} golden(s) still failing after an ingest that "
                            "brought in nothing new - the material is not in any source"
                        ),
                        params={"gaps": gaps[:MAX_GAPS_REPORTED]},
                    ),
                )
            )

        # -- measured quality under the floor -> retune (advisory).
        # The `is not None` guard is the second half of "unknown is not bad":
        # orientation.quality is 1.0 when unmeasured, but a caller constructing
        # an Orientation by hand should not be able to trip the floor with a
        # score that no eval report backs.
        if obs.eval_report is not None and orientation.quality < policy.quality_floor:
            recall = _num(obs.eval_report.get("recall_at_k"))
            mrr = _num(obs.eval_report.get("mrr"))
            # Recall weak means the right chunk was never fetched - widen the
            # candidate pool. Recall fine but MRR weak means it was fetched and
            # ranked badly - push the reranker back towards pure relevance.
            knob, direction = (
                ("retrieval.candidates", "increase")
                if recall <= mrr
                else ("rerank.mmr_lambda", "increase")
            )
            floor = max(policy.quality_floor, 1e-9)
            shortfall = (policy.quality_floor - orientation.quality) / floor
            candidates.append(
                (
                    ACTION_VALUE["retune"] * _clamp01(shortfall),
                    Action(
                        kind="retune",
                        target=knob,
                        reason=(
                            f"quality {orientation.quality:.2f} below floor "
                            f"{policy.quality_floor:g} (recall@k={recall:.2f}, mrr={mrr:.2f}); "
                            f"{direction} {knob}"
                        ),
                        params={"knob": knob, "direction": direction, "recall": round(recall, 4),
                                "mrr": round(mrr, 4)},
                    ),
                )
            )

        # -- ingest failing -> alert. No knob the loop owns can fix a source
        # that will not answer, so the only honest action is to say so.
        if orientation.error_rate > ERROR_RATE_ALERT:
            worst = max(obs.deltas, key=lambda d: d.failed, default=None)
            detail = worst.errors[0] if worst and worst.errors else "no error text recorded"
            candidates.append(
                (
                    ACTION_VALUE["alert"] * _clamp01(orientation.error_rate),
                    Action(
                        kind="alert",
                        target=worst.source_key if worst else "*",
                        reason=(
                            f"ingest error rate {orientation.error_rate:.0%} exceeds "
                            f"{ERROR_RATE_ALERT:.0%}: {_cut(detail, 120)}"
                        ),
                        params={"error_rate": round(orientation.error_rate, 4)},
                    ),
                )
            )

        budget = max(0, policy.max_actions_per_cycle)
        # Stable order: by expected value, then by kind and target, so two runs
        # over identical facts produce byte-identical cycle reports.
        candidates.sort(key=lambda pair: (-pair[0], pair[1].kind, pair[1].target))
        chosen = candidates[:budget]

        for rank, (value, action) in enumerate(chosen, 1):
            action.params["expected_value"] = round(value, 4)
            action.params["rank"] = rank
            action.params["of_warranted"] = len(candidates)

        if not chosen:
            # "The loop decided to do nothing" is a decision and it is reported
            # as one. An empty list here is indistinguishable from a loop that
            # crashed before deciding, and an operator cannot tell a healthy
            # steady state from a broken one by looking at an absence.
            skipped = (
                f" ({len(candidates)} warranted, budget {budget})" if candidates else ""
            )
            return [
                Action(
                    kind="noop",
                    target="",
                    reason=(
                        f"nothing warranted{skipped}: staleness {orientation.staleness:.2f} "
                        f"<= {policy.staleness_threshold:g}, quality {orientation.quality:.2f} "
                        f">= {policy.quality_floor:g}, error_rate "
                        f"{orientation.error_rate:.2f}, gaps {len(orientation.coverage_gaps)}"
                    ),
                    params={"warranted": len(candidates), "budget": budget},
                )
            ]
        return [action for _, action in chosen]

    # ---- act -------------------------------------------------------------

    def act(self, actions: Sequence[Action]) -> list[dict[str, Any]]:
        """Execute. The only phase that writes anything.

        One result dict per action, in order, always - an action that raised is
        a result with `ok=False` and the exception text, never a missing entry
        and never an aborted batch. Three failing connectors out of five is a
        two-source cycle with three recorded failures.
        """
        handlers = {
            "reingest": self._act_reingest,
            "reindex": self._act_reindex,
            "backfill": self._act_backfill,
            "retune": self._act_retune,
            "alert": self._act_alert,
            "noop": self._act_noop,
        }
        results: list[dict[str, Any]] = []
        # Reassigned unconditionally: the next observe must see what *this*
        # cycle did, including nothing.
        self._last_deltas = []

        for action in actions:
            started = time.perf_counter()
            result: dict[str, Any] = {
                "kind": action.kind,
                "target": action.target,
                "ok": True,
                "duration_s": 0.0,
                "error": "",
                "dry_run": bool(self.policy.dry_run),
                "reason": action.reason,
            }
            try:
                handler = handlers.get(action.kind)
                if handler is None:
                    result["ok"] = False
                    result["error"] = f"unknown action kind: {action.kind!r}"
                elif self.policy.dry_run and action.kind != "noop":
                    # Checked once, here, instead of inside six handlers: a
                    # handler that forgets the check is a dry run that writes.
                    result["detail"] = self._would(action)
                else:
                    handler(action, result)
            except Exception as e:  # a failed action is data, not an exception
                result["ok"] = False
                result["error"] = f"{type(e).__name__}: {e}"[:300]
                log.error("action failed", kind=action.kind, target=action.target,
                          err=f"{type(e).__name__}: {e}"[:200])
            result["duration_s"] = round(time.perf_counter() - started, 3)
            log.info(
                "act",
                kind=action.kind, target=action.target or "-", ok=result["ok"],
                dry_run=result["dry_run"], secs=result["duration_s"],
            )
            results.append(result)
        return results

    def _would(self, action: Action) -> str:
        """What this action would have done, for a dry run's result dict."""
        targets = ", ".join(c.key for c in self._connectors_for(action.target)) or "-"
        return {
            "reingest": f"would run connectors: {targets}",
            "backfill": f"would clear cursors and fully re-fetch: {targets}",
            "reindex": "would rebuild the bm25 and dense indexes from the store",
            "retune": f"would recommend {action.params.get('direction', 'changing')} "
                      f"{action.target}",
            "alert": f"would alert: {_cut(action.reason, 120)}",
        }.get(action.kind, f"would {action.kind}")

    def _act_reingest(self, action: Action, result: dict[str, Any]) -> None:
        connectors = self._connectors_for(action.target)
        if not connectors:
            result["ok"] = False
            result["error"] = f"no connector matches target {action.target!r}"
            return
        deltas = self.pipeline.ingest(connectors)
        self._record(deltas, result)

    def _act_backfill(self, action: Action, result: dict[str, Any]) -> None:
        """Re-fetch sources with their incremental cursors cleared.

        Clearing `hashes` makes every document read as new, which is the point:
        a document dropped by a past normalization change, or one that arrived
        while a run was failing, is invisible to incremental ingest forever
        because its hash is already on file. The re-fetch is not as expensive as
        it sounds - unchanged content still hits the embedding cache by hash, so
        the cost is bandwidth and chunking, not embedding.
        """
        connectors = self._connectors_for(action.target)
        if not connectors:
            result["ok"] = False
            result["error"] = f"no connector matches target {action.target!r}"
            return
        state = getattr(self.pipeline, "state", None)
        cleared = 0
        for connector in connectors:
            if state is None:
                break
            cursor = state.get(connector.key)
            if cursor.get("hashes"):
                cursor["hashes"] = {}
                state.set(connector.key, cursor)
                cleared += 1
        deltas = self.pipeline.ingest(connectors)
        self._record(deltas, result)
        result["cursors_cleared"] = cleared

    def _act_reindex(self, action: Action, result: dict[str, Any]) -> None:
        self.pipeline.refresh_indexes()
        bm25, dense = len(self.pipeline.bm25), len(self.pipeline.dense)
        result["bm25_chunks"] = bm25
        result["dense_vectors"] = dense
        result["detail"] = f"bm25={bm25} dense={dense}"

    def _act_retune(self, action: Action, result: dict[str, Any]) -> None:
        """Record the proposal; do not apply it.

        A loop that edits retrieval knobs on its own invalidates the very eval
        numbers used to judge whether the edit helped: the next cycle measures a
        different pipeline and cannot attribute the change. Retuning stays a
        human decision made one knob at a time against a before/after, and the
        loop's job is to say which knob and in which direction.
        """
        result["applied"] = False
        result["proposal"] = dict(action.params)
        result["detail"] = f"advisory: {action.params.get('direction', '?')} {action.target}"
        log.warn("retune proposed", knob=action.target, reason=_cut(action.reason, 160))

    def _act_alert(self, action: Action, result: dict[str, Any]) -> None:
        result["message"] = action.reason
        result["detail"] = _cut(action.reason, 120)
        log.warn("ALERT", target=action.target or "*", reason=_cut(action.reason, 200))

    def _act_noop(self, action: Action, result: dict[str, Any]) -> None:
        result["detail"] = _cut(action.reason, 120)

    def _record(self, deltas: Sequence[IngestDelta], result: dict[str, Any]) -> None:
        """Fold ingest deltas into a result dict and hand them to the next cycle."""
        self._last_deltas.extend(deltas)
        failed = sum(d.failed for d in deltas)
        result["new"] = sum(d.new for d in deltas)
        result["changed"] = sum(d.changed for d in deltas)
        result["unchanged"] = sum(d.unchanged for d in deltas)
        result["failed"] = failed
        result["sources"] = [d.source_key for d in deltas]
        result["detail"] = (
            f"new={result['new']} changed={result['changed']} "
            f"unchanged={result['unchanged']} failed={failed}"
        )
        if failed:
            # The action ran; it did not fully succeed. Both facts are recorded
            # because "ok" alone cannot distinguish a dead source from a slow one.
            result["ok"] = False
            result["error"] = "; ".join(e for d in deltas for e in d.errors[:2])[:300]

    def _connectors_for(self, target: str) -> list[Connector]:
        if target in ALL_TARGETS:
            return list(self.connectors)
        return [c for c in self.connectors if str(getattr(c, "key", "")) == target]

    # ---- the loop --------------------------------------------------------

    def cycle(self) -> CycleReport:
        """One full pass. Never raises: every phase already degrades in place."""
        self._cycle += 1
        started = time.perf_counter()

        observation = self.observe()
        orientation = self.orient(observation)
        actions = self.decide(orientation, observation)
        log.info(
            "decide",
            cycle=self._cycle,
            actions=len(actions),
            kinds=",".join(a.kind for a in actions),
        )
        results = self.act(actions)

        report = CycleReport(
            cycle=self._cycle,
            observation=observation,
            orientation=orientation,
            decided=actions,
            results=results,
            duration_s=round(time.perf_counter() - started, 3),
        )
        log.info(
            "cycle complete",
            cycle=self._cycle,
            acted=len(results),
            failed=sum(1 for r in results if not r.get("ok")),
            secs=report.duration_s,
        )
        return report

    def run(self, cycles: int = 1, interval_s: float = 0.0) -> list[CycleReport]:
        """Iterate `cycles` times, pausing `interval_s` between them.

        The pause is between cycles and not after the last one, so
        `run(1, 3600)` returns immediately rather than sleeping for an hour on
        the way out. An interrupt returns the reports collected so far: a loop
        stopped by hand still has to hand back what it learned before it stopped.
        """
        reports: list[CycleReport] = []
        for i in range(max(0, cycles)):
            try:
                if i and interval_s > 0:
                    time.sleep(interval_s)
                reports.append(self.cycle())
            except KeyboardInterrupt:
                log.warn("loop interrupted", completed=len(reports))
                break
        return reports

    def __repr__(self) -> str:
        mode = "dry-run" if self.policy.dry_run else "live"
        return f"OodaLoop(connectors={len(self.connectors)}, cycle={self._cycle}, {mode})"


# ---- small helpers ------------------------------------------------------


def _clamp01(value: float) -> float:
    return 0.0 if value < 0.0 else (1.0 if value > 1.0 else float(value))


def _num(value: Any, default: float = 0.0) -> float:
    """Coerce a value out of a JSON-ish payload to a float, or give up quietly.

    Scoring runs over an eval report the loop did not produce, so every read of
    it goes through here: a string where a float was expected must not be able
    to raise inside `orient` and take the whole cycle with it.
    """
    if isinstance(value, bool) or value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extend_capped(errors: list[str], new: Sequence[str]) -> None:
    for message in new:
        if len(errors) >= MAX_ERRORS_CARRIED:
            return
        errors.append(str(message)[:300])


#: Per-question keys the harness may use to mark a golden as answered. Truthy
#: means success; the first one present decides.
_SUCCESS_FLAGS = ("ok", "passed", "hit", "found", "success")
#: ...and the score keys, where <= 0 means the relevant chunk never surfaced.
_SUCCESS_SCORES = ("recall_at_k", "recall", "reciprocal_rank", "rr", "ndcg_at_k", "ndcg")


def _failing_goldens(eval_report: Mapping[str, Any] | None) -> list[str]:
    """Questions the eval report says currently fail.

    `EvalReport.per_question` is frozen as `list[dict[str, Any]]` with no schema,
    so this reads whichever of the conventional keys the harness actually wrote
    and treats an entry it cannot interpret as *passing*. That default is
    deliberate: inventing failures out of an unrecognized payload would have the
    loop re-fetching the whole corpus, every cycle, over nothing.
    """
    if not eval_report:
        return []
    entries = eval_report.get("per_question")
    if not isinstance(entries, list):
        return []

    gaps: list[str] = []
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        if _entry_failed(entry):
            question = entry.get("question") or entry.get("q") or f"golden #{position}"
            gaps.append(_cut(str(question), 160))
    return gaps


def _entry_failed(entry: Mapping[str, Any]) -> bool:
    for flag in _SUCCESS_FLAGS:
        if flag in entry:
            return not bool(entry[flag])
    for score in _SUCCESS_SCORES:
        if score in entry:
            return _num(entry[score]) <= 0.0
    return False


def _as_dict(obj: Any) -> dict[str, Any]:
    """Best-effort dict view of an eval report that has no `as_dict`."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    return dict(obj) if isinstance(obj, Mapping) else {"report": str(obj)}


def _duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    if seconds < 172800:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def _cut(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _join(items: Sequence[str], limit: int) -> str:
    shown = ", ".join(_cut(i, 40) for i in items[:limit])
    extra = len(items) - limit
    return f"{shown} (+{extra} more)" if extra > 0 else shown


def _show(value: Any) -> str:
    return "?" if value is None else str(value)
