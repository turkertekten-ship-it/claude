"""The nightly cycle: Observe -> Orient -> Decide -> Act -> Learn.

This is the whole system in one file, and it is deliberately boring. Every hard
decision has already been made somewhere else - what to look at (`sources`),
what counts as a problem (`detect`), what is worth doing and what is allowed
(`decide`), how to change a file without breaking it (`act`), what happened last
time (`journal`). The loop's only job is to run those in order, under a clock
and a set of budgets, and to leave a record.

Two properties matter more than anything else here:

**It is safe to run unattended.** The default is a dry run. Nothing outside the
workspace root is ever written. Only `safe`-tier proposals are ever applied
without a human, edits are backed up and revertible by cycle id, and a run
refuses to touch files when the working tree is dirty - because an autonomous
edit mixed into someone's uncommitted work makes "who changed this" unanswerable.

**It is safe to run repeatedly.** The observation window starts where the last
cycle ended, edits are idempotent, and anything the user has dismissed is never
proposed again. Running it twice by accident costs a few seconds and changes
nothing, which is the only way a scheduled job survives contact with real life.

The fifth phase, Learn, is what makes it a loop rather than a cron job: every
verdict is written to the journal, and tomorrow's Decide stage reads it.
"""

from __future__ import annotations

import fnmatch
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.reflect.act.edits import ApplyReport, EditApplier
from oodarag.reflect.act.queue import ReviewQueue, proposal_from_dict
from oodarag.reflect.act.report import render_json, render_markdown, write_report
from oodarag.reflect.decide.conflicts import resolve_edit_conflicts
from oodarag.reflect.decide.policy import Decision, PolicyConfig, PolicyEngine
from oodarag.reflect.decide.priors import RulePriors
from oodarag.reflect.detect.base import DetectContext, build_detectors
from oodarag.reflect.journal import Journal
from oodarag.reflect.models import CycleReport, Finding, Outcome, Proposal, Signal
from oodarag.reflect.sources.base import Budget, SignalSource
from oodarag.util.logging import get_logger

log = get_logger("reflect.loop")

#: Sources whose signals describe *current state* rather than *events*.
#: These must always be collected in full, never windowed: a rule that asks
#: "does this file the README links to exist?" needs today's whole file tree,
#: not just the handful of files that happened to change since last night.
SNAPSHOT_SOURCES = frozenset({"workspace:files"})

DEFAULT_STATE_DIR = ".oodarag/reflect"


@dataclass(slots=True)
class ReflectConfig:
    """Everything tunable about a run, in one object that can be serialized."""

    root: Path = field(default_factory=Path.cwd)
    state_dir: Path | None = None
    dry_run: bool = True
    lookback_s: float = 86_400.0
    #: Per-source caps. A nightly job must finish before morning even if the
    #: home directory has grown a 4 GB log file since yesterday.
    source_wall_clock_s: float = 60.0
    max_signals_per_source: int = 20_000
    max_chars_per_signal: int = 20_000
    enabled_rules: list[str] = field(default_factory=list)
    disabled_rules: list[str] = field(default_factory=list)
    enabled_sources: list[str] = field(default_factory=list)
    rule_config: dict[str, dict[str, Any]] = field(default_factory=dict)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    #: Extra chat-transcript roots beyond the defaults, for people who keep
    #: their conversation logs somewhere unusual.
    chat_roots: list[Path] = field(default_factory=list)
    shell_history_paths: list[Path] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        self.state_dir = Path(self.state_dir) if self.state_dir else self.root / DEFAULT_STATE_DIR

    @property
    def journal_dir(self) -> Path:
        return Path(self.state_dir) / "journal"

    @property
    def reports_dir(self) -> Path:
        return Path(self.state_dir) / "reports"

    @property
    def backups_dir(self) -> Path:
        return Path(self.state_dir) / "backups"

    @property
    def queue_path(self) -> Path:
        return Path(self.state_dir) / "queue.json"

    @property
    def lock_path(self) -> Path:
        return Path(self.state_dir) / "lock"


class CycleLock:
    """A best-effort single-instance lock.

    Two cycles running at once would double-apply edits and interleave journal
    records. `O_CREAT | O_EXCL` is atomic on every filesystem this will realistically
    meet, and a lock whose owning pid is gone is treated as stale rather than
    fatal - a machine that lost power mid-cycle must not need manual cleanup
    before the next night works.
    """

    def __init__(self, path: Path, stale_after_s: float = 6 * 3600) -> None:
        self.path = Path(path)
        self.stale_after_s = stale_after_s
        self.acquired = False

    def __enter__(self) -> CycleLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                age = time.time() - self.path.stat().st_mtime
                pid = int(self.path.read_text("utf-8").strip() or 0)
            except (OSError, ValueError):
                age, pid = self.stale_after_s + 1, 0
            if age > self.stale_after_s or not _pid_alive(pid):
                log.warn("clearing stale lock", path=str(self.path), age_s=round(age))
                try:
                    self.path.unlink()
                except OSError:
                    pass
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            self.acquired = True
        except FileExistsError:
            self.acquired = False
        except OSError as e:
            log.warn("could not take lock, proceeding", err=str(e)[:120])
            self.acquired = True
        return self

    def __exit__(self, *exc: object) -> None:
        if self.acquired:
            try:
                self.path.unlink()
            except OSError:
                pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        return False
    except PermissionError:
        return True  # exists, owned by someone else


def build_sources(config: ReflectConfig) -> list[SignalSource]:
    """Instantiate the sources, skipping any the machine cannot offer.

    Imported here rather than at module scope so that a source with a broken
    optional dependency degrades to "that source is unavailable" instead of
    taking the whole CLI down with an ImportError.
    """
    from oodarag.reflect.sources.shell import ShellHistorySource
    from oodarag.reflect.sources.transcripts import ChatTranscriptSource
    from oodarag.reflect.sources.workspace import GitHistorySource, WorkspaceFileSource

    candidates: list[SignalSource] = [
        ChatTranscriptSource(roots=config.chat_roots or None),
        ShellHistorySource(paths=config.shell_history_paths or None),
        WorkspaceFileSource(root=config.root),
        GitHistorySource(root=config.root),
    ]
    selected: list[SignalSource] = []
    for src in candidates:
        if config.enabled_sources and not any(
            src.key == e or src.key.startswith(e) for e in config.enabled_sources
        ):
            continue
        if not src.available():
            log.debug("source unavailable, skipping", key=src.key)
            continue
        selected.append(src)
    return selected


class ReflectLoop:
    def __init__(self, config: ReflectConfig | None = None) -> None:
        self.config = config or ReflectConfig()
        self._deferred: list[Proposal] = []
        self.journal = Journal(self.config.journal_dir)
        self.queue = ReviewQueue(self.config.queue_path)
        self.priors = RulePriors(self.journal)
        self.policy = PolicyEngine(self.config.policy, self.priors)

    # -- Observe -------------------------------------------------------------

    def observe(self, since: float) -> tuple[list[Signal], dict[str, int], list[str]]:
        signals: list[Signal] = []
        per_source: dict[str, int] = {}
        errors: list[str] = []
        for src in build_sources(self.config):
            budget = Budget(
                max_signals=self.config.max_signals_per_source,
                max_chars_per_signal=self.config.max_chars_per_signal,
                wall_clock_s=self.config.source_wall_clock_s,
            )
            window = 0.0 if src.key in SNAPSHOT_SOURCES else since
            result = src.run(since=window, budget=budget)
            signals.extend(result.signals)
            per_source[src.key] = len(result.signals)
            errors.extend(result.errors)
            if result.truncated:
                errors.append(f"{src.key}: truncated at budget")
        log.info("observed", signals=len(signals), sources=len(per_source))
        return signals, per_source, errors

    # -- Orient --------------------------------------------------------------

    def orient(self, signals: list[Signal], window_start: float) -> tuple[
        list[Finding], list[Proposal], list[str]
    ]:
        ctx = DetectContext(
            signals=signals,
            root=self.config.root,
            now=time.time(),
            window_start=window_start,
            config=self.config.rule_config,
        )
        detectors = build_detectors(
            config=self.config.rule_config,
            enabled=self.config.enabled_rules or None,
            disabled=self.config.disabled_rules or None,
        )
        available_kinds = {s.kind for s in signals}
        findings: list[Finding] = []
        proposals: list[Proposal] = []
        errors: list[str] = []
        for det in detectors:
            if det.consumes and not (set(det.consumes) & available_kinds):
                continue  # nothing this rule can even look at tonight
            rule_findings = det.run(ctx)
            findings.extend(rule_findings)
            for finding in rule_findings:
                proposals.extend(det.run_propose(finding, ctx))
        log.info("oriented", findings=len(findings), proposals=len(proposals))
        return findings, proposals, errors

    # -- Decide --------------------------------------------------------------

    def decide(self, proposals: list[Proposal]) -> Decision:
        return self.policy.decide(proposals, tree_clean=self.tree_is_clean())

    def tree_is_clean(self) -> bool:
        """True when git reports no uncommitted changes.

        A non-repository counts as clean: plenty of people keep notes and docs
        in a plain directory, and refusing to help them because there is no
        `.git` would be pedantry rather than safety.
        """
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.config.root),
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            return True
        if proc.returncode != 0:
            return True
        return not proc.stdout.strip()

    # -- Act -----------------------------------------------------------------

    def act(self, decision: Decision, cycle_id: str) -> ApplyReport:
        applier = EditApplier(
            root=self.config.root,
            backup_root=self.config.backups_dir,
            dry_run=self.config.dry_run,
        )
        # Human-accepted proposals from previous nights go first, and bypass the
        # risk gate - a person already looked at the diff and said yes, which is
        # exactly the authority the risk tiers exist to stand in for.
        approved = self._accepted_proposals()
        # Two rules may both want to create the same file; settle that here,
        # visibly, rather than letting the loser fail a precondition in silence.
        to_apply, conflict_notes = resolve_edit_conflicts(approved + decision.apply)
        decision.notes.extend(conflict_notes)
        survived = {p.fingerprint for p in to_apply}
        self._deferred = [p for p in decision.apply if p.fingerprint not in survived]
        report = applier.apply_all(to_apply, cycle_id)
        # Deferred proposals are queued rather than dropped, so they stay visible.
        self.queue.put(decision.queue + self._deferred, cycle_id)
        for entry in approved:
            self.queue.drop(entry.fingerprint)
        return report

    def _accepted_proposals(self) -> list[Proposal]:
        out: list[Proposal] = []
        for entry in self.queue.accepted():
            try:
                out.append(proposal_from_dict(entry["proposal"]))
            except (KeyError, TypeError, ValueError) as e:
                log.warn("could not rebuild accepted proposal", err=str(e)[:160])
        return out

    # -- Learn ---------------------------------------------------------------

    def learn(self, report: CycleReport, decision: Decision, applied: ApplyReport) -> None:
        outcomes: list[Outcome] = []
        by_path = {r.path: r for r in applied.results}
        deferred = {p.fingerprint for p in self._deferred}
        for proposal in decision.apply:
            if proposal.fingerprint in deferred:
                continue  # it never ran, so there is no verdict to learn from
            results = [by_path.get(p) for p in proposal.paths]
            ok = all(r is not None and r.applied for r in results)
            if self.config.dry_run:
                continue  # a dry run establishes nothing; recording it would poison the priors
            outcomes.append(
                Outcome(
                    fingerprint=proposal.fingerprint,
                    rule_id=proposal.finding.rule_id,
                    verdict="applied" if ok else "failed",
                    cycle_id=report.cycle_id,
                    note="" if ok else "; ".join(
                        r.reason for r in applied.results if r and not r.applied
                    )[:300],
                )
            )
        self.journal.record_outcomes(outcomes)
        self.journal.record_cycle(report)

    # -- the whole cycle -----------------------------------------------------

    def run_cycle(self, since: float | None = None) -> CycleReport:
        cycle_id = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        window_start = (
            since
            if since is not None
            else self.journal.last_window_end(self.config.lookback_s)
        )
        report = CycleReport(
            cycle_id=cycle_id, dry_run=self.config.dry_run, window_start=window_start
        )

        with CycleLock(self.config.lock_path) as lock:
            if not lock.acquired:
                report.errors.append("another cycle is already running; skipped")
                report.ended_at = time.time()
                log.warn("cycle already running, skipping")
                return report

            signals, per_source, errors = self.observe(window_start)
            report.signals = len(signals)
            report.per_source = per_source
            report.errors.extend(errors)

            findings, proposals, orient_errors = self.orient(signals, window_start)
            report.findings = findings
            report.errors.extend(orient_errors)

            decision = self.decide(proposals)
            report.proposals = decision.apply + decision.queue
            report.suppressed = [p.fingerprint for p in decision.suppressed]

            applied = self.act(decision, cycle_id)
            report.applied = [
                p.fingerprint
                for p in decision.apply
                # An all() over an empty sequence is True, which would report a
                # proposal that changed nothing as applied.
                if p.paths
                and all(
                    any(r.path == path and r.applied for r in applied.results)
                    for path in p.paths
                )
            ]
            report.queued = [p.fingerprint for p in decision.queue]
            report.ended_at = time.time()

            self.learn(report, decision, applied)

            markdown = render_markdown(
                report=report,
                apply_report=applied,
                decision_notes=decision.notes,
                priors_explain={
                    rule: self.priors.explain(rule)
                    for rule in sorted({f.rule_id for f in findings})
                },
            )
            path = write_report(self.config.reports_dir, report, markdown)
            log.info(
                "cycle complete",
                cycle=cycle_id, signals=report.signals, findings=len(findings),
                applied=len(report.applied), queued=len(report.queued), report=str(path),
            )
            report.report_path = str(path)
        return report

    # -- helpers used by the CLI --------------------------------------------

    def render(self, report: CycleReport, as_json: bool = False) -> str:
        if as_json:
            return render_json(report)
        return render_markdown(report, None, [], {})

    def revert(self, cycle_id: str) -> ApplyReport:
        applier = EditApplier(
            root=self.config.root, backup_root=self.config.backups_dir, dry_run=False
        )
        result = applier.revert(cycle_id)
        self.journal.record_outcomes(
            [
                Outcome(fingerprint=fp, rule_id="", verdict="reverted", cycle_id=cycle_id)
                for fp in self._fingerprints_of_cycle(cycle_id)
            ]
        )
        return result

    def _fingerprints_of_cycle(self, cycle_id: str) -> list[str]:
        for record in self.journal.cycles():
            if record.get("cycle_id") == cycle_id:
                return list(record.get("applied") or [])
        return []


def path_is_protected(relpath: str, patterns: tuple[str, ...]) -> bool:
    """Shared with the policy engine's gate; kept here so the loop can explain itself."""
    return any(fnmatch.fnmatch(relpath, pat) for pat in patterns)
