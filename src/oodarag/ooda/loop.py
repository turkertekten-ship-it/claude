"""The OODA loop.

Observe -> Orient -> Decide -> Act, once per cycle, with every phase journalled.

Why a control loop rather than a cron job that re-indexes everything: the
expensive failure in a retrieval system is not "the index is stale", it is "the
index is stale and nothing noticed". A cron job runs whether or not it is
needed and stays silent whether or not it worked. A loop measures the situation,
decides what the measurements justify, acts, and writes down both the reasoning
and the outcome - so the next cycle starts from evidence rather than from
assumption, and a human reading the journal can see why.

    Observe   what changed, what is reachable, what failed
    Orient    fold it into the index; assess coverage, staleness, quality
    Decide    apply the policy rules (ooda/policy.py) to the assessment
    Act       execute the ranked actions within budget, record outcomes
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from oodarag.access.probe import AccessReport, probe_all
from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerGenerator
from oodarag.ingest.base import Connector
from oodarag.ooda.policy import (
    ALERT,
    BACKFILL_SOURCE,
    EMBED_MISSING,
    NOOP,
    PRUNE_REMOVED,
    QUARANTINE_SOURCE,
    REFIT_EMBEDDER,
    REINDEX,
    RUN_EVAL,
    Action,
    Thresholds,
    decide,
)
from oodarag.pipeline import IndexPipeline, IndexReport
from oodarag.retrieve.hybrid import HybridRetriever
from oodarag.util.logging import get_logger

log = get_logger("ooda")


@dataclass
class LoopConfig:
    goldens_path: str | None = "evals/goldens.jsonl"
    probe_access: bool = True
    repo_slugs: tuple[str, ...] = ()
    max_actions_per_cycle: int = 6
    thresholds: Thresholds = field(default_factory=Thresholds)
    dry_run: bool = False


@dataclass
class CycleReport:
    cycle: int
    observations: dict[str, Any] = field(default_factory=dict)
    situation: dict[str, Any] = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)
    outcomes: list[dict[str, Any]] = field(default_factory=list)
    duration_s: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "observations": self.observations,
            "situation": self.situation,
            "actions": [a.as_dict() for a in self.actions],
            "outcomes": self.outcomes,
            "duration_s": round(self.duration_s, 2),
        }

    def summary(self) -> str:
        acted = ", ".join(f"{o['kind']}={o['status']}" for o in self.outcomes) or "none"
        return (f"cycle {self.cycle}: "
                f"{self.observations.get('documents_ingested', 0)} docs ingested, "
                f"{len(self.actions)} actions decided, acted: {acted}")


class OodaLoop:
    def __init__(self, pipeline: IndexPipeline, connectors: Sequence[Connector],
                 config: LoopConfig | None = None,
                 generator: AnswerGenerator | None = None) -> None:
        self.pipeline = pipeline
        self.store = pipeline.store
        self.connectors = list(connectors)
        self.config = config or LoopConfig()
        self._generator = generator
        self._last_deltas: list[Any] = []
        self.cycle_number = int(self.store.get_meta("ooda_cycle", 0))

    # ------------------------------------------------------------------ phases

    def observe(self) -> dict[str, Any]:
        """Gather evidence - by pulling from the sources, which changes the index.

        The previous version of this line said "nothing is changed here except
        the journal", directly above a call that ingests documents, writes
        chunks, refits the embedder and writes vectors. That is not a small
        inaccuracy in a loop whose whole structure is the separation of looking
        from acting.

        The ingest belongs here, and the reason is worth stating rather than
        assuming: for this system, "what is the world like now" *is* what the
        sources currently hold, and there is no way to observe that without
        fetching. The consequence is that the situation the Decide phase sees is
        the one Observe has already brought about - so the policy rules that
        look like they govern ingestion do not. They govern the case where the
        ingest could not do its job: `embed_missing` fires when a connector
        raised and left chunks without vectors, which is measured in
        `test_a_failed_ingest_leaves_work_the_policy_picks_up`, not when the
        loop is healthy.
        """
        observations: dict[str, Any] = {"at": time.time()}

        if self.config.probe_access:
            report: AccessReport = probe_all(repo_slugs=self.config.repo_slugs)
            observations["access"] = {
                "summary": report.summary,
                "degradations": report.degradations(),
                "blocked": [r.name for r in report.results if not r.usable],
            }

        index_report: IndexReport = self.pipeline.run(self.connectors)
        # Kept so the Act phase can prune with the actual removal lists rather
        # than the truncated copy carried in the journal.
        self._last_deltas = index_report.deltas
        observations.update({
            "documents_ingested": index_report.documents_ingested,
            "chunks_written": index_report.chunks_written,
            "vectors_written": index_report.vectors_written,
            "errors": index_report.errors,
            "deltas": [d.as_dict() for d in index_report.deltas],
            "refit": index_report.refit,
            "ingest_duration_s": round(index_report.duration_s, 2),
        })
        self.store.journal(self.cycle_number, "observe", observations)
        return observations

    def orient(self, observations: dict[str, Any]) -> dict[str, Any]:
        """Fold observations into a situation assessment.

        Orient is where raw counts become meaning: 12 new documents is a number;
        "the corpus grew 30% and the term statistics no longer fit" is a
        situation a policy can act on.
        """
        stats = self.store.stats()
        history = self.store.get_meta("source_health", {})
        now = time.time()

        sources: dict[str, dict[str, Any]] = {}
        for delta in observations.get("deltas", []):
            key = delta["source_key"]
            prior = history.get(key, {})
            touched = delta["new"] + delta["changed"] + delta["unchanged"]
            failed = delta["failed"]
            succeeded = failed == 0 and not delta["errors"]
            consecutive = 0 if succeeded else prior.get("consecutive_failures", 0) + 1
            last_success = now if succeeded else prior.get("last_success", 0.0)
            sources[key] = {
                "new": delta["new"], "changed": delta["changed"],
                "failed": failed,
                "removed": len(delta.get("removed") or []),
                "removed_ids": (delta.get("removed") or [])[:50],
                "source_system": delta.get("source_system", ""),
                "failure_rate": round(failed / max(1, touched + failed), 4),
                "consecutive_failures": consecutive,
                "last_success": last_success,
                "hours_since_success": round((now - last_success) / 3600.0, 2)
                if last_success else 999.0,
                "last_error": (delta["errors"] or [""])[0],
                "quarantined": prior.get("quarantined", False),
            }
        # Merged, not replaced. A source absent from this cycle's deltas -
        # including one just quarantined and removed from the connector set -
        # would otherwise vanish from the record entirely: its quarantine flag
        # would not survive a restart, and an intermittently failing source
        # would have its consecutive-failure count reset every time it
        # reappeared, so it could never reach the quarantine threshold.
        merged = dict(history)
        merged.update(sources)
        self.store.set_meta("source_health", merged)
        sources = merged

        fitted_on = self.store.get_meta("fitted_doc_count", 0) or 0
        growth = ((stats["documents"] - fitted_on) / fitted_on) if fitted_on else 0.0
        index_fingerprint = self.store.get_meta("index_fingerprint", "")

        situation = {
            "documents": stats["documents"],
            "chunks": stats["chunks"],
            "embedding_coverage": stats["coverage"],
            "by_source": stats["by_source"],
            "index_fingerprint": index_fingerprint,
            "embedder_fingerprint": self.pipeline.embedder.fingerprint,
            "fingerprint_mismatch": bool(index_fingerprint)
            and index_fingerprint != self.pipeline.embedder.fingerprint,
            "corpus_growth": round(growth, 4),
            "content_changed": observations.get("documents_ingested", 0) > 0,
            "sources": sources,
            "degradations": (observations.get("access") or {}).get("degradations", []),
            "previous_eval_pass_rate": self.store.get_meta("last_eval_pass_rate"),
            "eval_pass_rate": None,   # filled by a RUN_EVAL action within this cycle
        }
        self.store.journal(self.cycle_number, "orient", situation)
        return situation

    def decide(self, situation: dict[str, Any]) -> list[Action]:
        actions = decide(situation, self.config.thresholds)
        self.store.journal(self.cycle_number, "decide",
                           {"actions": [a.as_dict() for a in actions]})
        return actions

    def act(self, actions: list[Action], situation: dict[str, Any]) -> list[dict[str, Any]]:
        outcomes: list[dict[str, Any]] = []
        budget = self.config.max_actions_per_cycle

        for action in actions:
            if len(outcomes) >= budget:
                outcomes.append({"kind": action.kind, "status": "deferred",
                                 "reason": "cycle action budget exhausted"})
                break
            if self.config.dry_run and action.kind not in (NOOP, ALERT):
                outcomes.append({"kind": action.kind, "status": "dry_run",
                                 "reason": action.reason})
                continue
            outcomes.append(self._execute(action, situation))

        self.store.journal(self.cycle_number, "act", {"outcomes": outcomes})
        return outcomes

    def _execute(self, action: Action, situation: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        result: dict[str, Any] = {"kind": action.kind, "target": action.target,
                                  "reason": action.reason, "status": "done"}
        try:
            if action.kind == EMBED_MISSING:
                result["vectors"] = self.pipeline.embed_missing()
            elif action.kind == REINDEX:
                report = self.pipeline.reindex_all()
                result.update({"chunks": report.chunks_written,
                               "vectors": report.vectors_written})
            elif action.kind == REFIT_EMBEDDER:
                report = self.pipeline.reindex_all()
                result.update({"refit": True, "vectors": report.vectors_written})
            elif action.kind == BACKFILL_SOURCE:
                connector = next((c for c in self.connectors if c.key == action.target), None)
                if connector is None:
                    result.update({"status": "skipped", "detail": "connector not configured"})
                else:
                    report = self.pipeline.run([connector])
                    result["documents"] = report.documents_ingested
            elif action.kind == QUARANTINE_SOURCE:
                health = self.store.get_meta("source_health", {})
                if action.target in health:
                    health[action.target]["quarantined"] = True
                    self.store.set_meta("source_health", health)
                self.connectors = [c for c in self.connectors if c.key != action.target]
                result["detail"] = "source removed from this loop's connector set"
            elif action.kind == PRUNE_REMOVED:
                delta = next((d for d in self._last_deltas
                              if d.source_key == action.target), None)
                if delta is None:
                    result.update({"status": "skipped", "detail": "no delta for source"})
                else:
                    prune = self.pipeline.prune([delta])
                    result.update(prune.as_dict())
                    if prune.refused:
                        result["status"] = "refused"
            elif action.kind == RUN_EVAL:
                result.update(self._run_eval(situation))
            elif action.kind == ALERT:
                # An alert is a durable record, not a print: the journal is what
                # a human or a later cycle reads.
                log.warn("ALERT", target=action.target, reason=action.reason,
                         **{k: str(v)[:120] for k, v in action.evidence.items()})
                result["evidence"] = action.evidence
            elif action.kind == NOOP:
                result["detail"] = "nothing to do"
            else:
                result.update({"status": "unknown_action"})
        except Exception as e:
            result.update({"status": "failed", "error": f"{type(e).__name__}: {e}"[:300]})
            log.error("action failed", kind=action.kind, err=str(e)[:200])
        result["duration_s"] = round(time.monotonic() - started, 3)
        return result

    def _run_eval(self, situation: dict[str, Any]) -> dict[str, Any]:
        path = self.config.goldens_path
        if not path or not Path(path).exists():
            return {"status": "skipped", "detail": "no golden set configured"}
        generator = self._generator or AnswerGenerator(
            HybridRetriever(self.store, self.pipeline.embedder)
        )
        report = EvalHarness(generator).run(load_goldens(path))
        aggregate = report.aggregate()
        situation["eval_pass_rate"] = report.pass_rate
        self.store.set_meta("last_eval_pass_rate", report.pass_rate)
        self.store.set_meta("last_eval", aggregate)
        return {
            "pass_rate": report.pass_rate,
            "cases": len(report.cases),
            "recall": aggregate.get(f"recall@{report.k}", {}).get("mean"),
            "failures": [c.question for c in report.failures()][:5],
        }

    # ------------------------------------------------------------------- cycle

    def cycle(self) -> CycleReport:
        self.cycle_number += 1
        self.store.set_meta("ooda_cycle", self.cycle_number)
        started = time.monotonic()
        log.info("cycle start", cycle=self.cycle_number)

        observations = self.observe()
        situation = self.orient(observations)
        actions = self.decide(situation)
        outcomes = self.act(actions, situation)

        # An eval that ran inside this cycle produced a pass rate the Decide
        # phase could not have seen. Re-deciding on the updated situation is
        # what closes the loop: the measurement taken in Act feeds the next
        # decision instead of waiting a full cycle to matter.
        if situation.get("eval_pass_rate") is not None:
            follow_up = [a for a in decide(situation, self.config.thresholds)
                         if a.kind == ALERT and a.target == "eval"]
            if follow_up:
                outcomes.extend(self.act(follow_up, situation))
                actions.extend(follow_up)

        report = CycleReport(cycle=self.cycle_number, observations=observations,
                             situation=situation, actions=actions, outcomes=outcomes,
                             duration_s=time.monotonic() - started)
        self.store.journal(self.cycle_number, "cycle", report.as_dict())
        log.info("cycle complete", cycle=self.cycle_number,
                 actions=len(actions), secs=round(report.duration_s, 2))
        return report

    def run(self, cycles: int = 1, interval_s: float = 0.0) -> list[CycleReport]:
        reports = []
        for index in range(cycles):
            reports.append(self.cycle())
            if interval_s and index < cycles - 1:
                time.sleep(interval_s)
        return reports
