"""The run loop: variants x cases x repeats, graded, then compared blind.

Two passes, deliberately separate.

**Pass one -- produce.** Every variant answers every case. Nothing is compared
yet, because comparison is where bias enters and it should enter in exactly
one place, under supervision.

**Pass two -- compare.** Candidates are stripped of identity and judged
against each other in both orders. This pass is optional: a suite with only
deterministic graders never needs it, and never pays for it.

Everything a run touches is written to a run directory -- the resolved
prompts, the raw completions, every grader verdict, every judge vote in both
orders. A result that cannot be traced back to the exact prompt that produced
it is an anecdote.
"""

from __future__ import annotations

import itertools
import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from .backend import Backend, Completion, Request
from .blind import (
    Candidate, PairJudgement, identical_pair_control, identity_tokens,
    judge_pair, position_bias_rate, same_family,
)
from .errors import SpecError
from .graders import GradingContext, Verdict, grade
from .render import render
from .spec import Case, Suite, Variant

Reporter = Callable[[str], None]


@dataclass
class CaseRun:
    """One variant's attempt at one case, graded."""

    case_id: str
    variant_id: str
    repeat: int
    prompt: str
    output: str
    verdicts: list[Verdict] = field(default_factory=list)
    completion: Completion | None = None
    workdir: str = ""

    @property
    def blocking(self) -> list[Verdict]:
        return [v for v in self.verdicts if not v.advisory]

    @property
    def passed(self) -> bool:
        """A run passes when every blocking grader passed. Advisory ones report only."""
        blocking = self.blocking
        return bool(blocking) and all(v.passed for v in blocking)

    @property
    def score(self) -> float:
        """Weighted mean of blocking grader scores, 0.0-1.0."""
        blocking = self.blocking
        if not blocking:
            return 0.0
        total = sum(v.weight for v in blocking) or 1.0
        return sum(v.score * v.weight for v in blocking) / total

    @property
    def cost_usd(self) -> float:
        base = (self.completion.cost_usd or 0.0) if self.completion else 0.0
        return base + sum(v.cost_usd for v in self.verdicts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id, "variant_id": self.variant_id,
            "repeat": self.repeat, "passed": self.passed,
            "score": round(self.score, 4), "cost_usd": round(self.cost_usd, 6),
            "prompt": self.prompt, "output": self.output,
            "verdicts": [v.to_dict() for v in self.verdicts],
            "completion": self.completion.to_dict() if self.completion else None,
        }


@dataclass
class RunResult:
    """Everything one invocation of the workbench produced."""

    suite: str
    run_id: str
    backend: str
    started_at: str
    runs: list[CaseRun] = field(default_factory=list)
    judgements: list[PairJudgement] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    duration_s: float = 0.0
    #: Result of the identical-pair blinding control, when a comparison ran.
    controls: list[dict[str, Any]] = field(default_factory=list)
    #: Characters of output per variant, so a length confound stays visible.
    lengths: dict[str, int] = field(default_factory=dict)
    #: The judge model, recorded because a judge is a measuring instrument:
    #: changing it invalidates comparison against every earlier run.
    judge_model: str = ""
    #: Disk-cache hits and misses. Without these, a re-grade of cached
    #: completions reports the original spend as though it had just happened.
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def cost_usd(self) -> float:
        return (sum(r.cost_usd for r in self.runs)
                + sum(j.cost_usd for j in self.judgements))

    def by_variant(self, variant_id: str) -> list[CaseRun]:
        return [r for r in self.runs if r.variant_id == variant_id]

    @property
    def variant_ids(self) -> list[str]:
        seen: list[str] = []
        for r in self.runs:
            if r.variant_id not in seen:
                seen.append(r.variant_id)
        return seen

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite": self.suite, "run_id": self.run_id, "backend": self.backend,
            "started_at": self.started_at, "duration_s": round(self.duration_s, 2),
            "cost_usd": round(self.cost_usd, 6),
            "runs": [r.to_dict() for r in self.runs],
            "judgements": [j.to_dict() for j in self.judgements],
            "position_bias_rate": round(position_bias_rate(self.judgements), 4),
            "controls": self.controls,
            "mean_output_chars": self.lengths,
            "judge_model": self.judge_model or "(backend default)",
            "cache_hits": self.cache_hits, "cache_misses": self.cache_misses,
            "notes": self.notes,
        }


def _resolve_prompt(suite: Suite, case: Case,
                    variant: Variant) -> tuple[str | tuple[str, ...], str | None]:
    """Merge variable scopes and render, returning ``(prompt, system)``.

    Variable precedence is case, then variant, then suite -- narrowest scope
    wins, so a case can pin one value without editing the variant it shares
    with every other case. ``case_id`` and ``variant_id`` are always available.
    """
    variables = {**suite.vars, **variant.vars, **case.vars,
                 "case_id": case.id, "variant_id": variant.id}
    body = render(case.prompt, variables) if case.prompt else ""
    turns = tuple(render(t, variables) for t in case.turns)
    prefix = render(variant.prompt_prefix, variables) if variant.prompt_prefix else ""
    suffix = render(variant.prompt_suffix, variables) if variant.prompt_suffix else ""
    # The system prompt may use the same variables -- that is how one prompt
    # file serves as several variants.
    system = render(variant.system, variables) if variant.system else None
    if turns:
        # Prefix and suffix wrap the last turn: they are framing for the thing
        # being asked, and the earlier turns are setup.
        turns = turns[:-1] + (f"{prefix}{turns[-1]}{suffix}",)
        return turns, system
    return f"{prefix}{body}{suffix}", system


def _prepare_workdir(suite: Suite, case: Case, variant: Variant) -> str:
    """Agent mode: a fresh directory, optionally seeded from a fixture."""
    workdir = tempfile.mkdtemp(prefix=f"wb-{variant.id}-{case.id}-")
    fixture = case.fixture or variant.fixture
    if fixture:
        assert suite.path is not None
        source = (suite.path.parent / fixture).resolve()
        if not source.is_dir():
            raise SpecError(f"fixture directory not found: {source}")
        shutil.copytree(source, workdir, dirs_exist_ok=True)
    for command in variant.setup:
        subprocess.run(command, shell=True, cwd=workdir, capture_output=True,
                       text=True, timeout=120)
    return workdir


def produce(suite: Suite, backend: Backend, report: Reporter,
            variants: Sequence[Variant] | None = None,
            cases: Sequence[Case] | None = None,
            judge_backend: Backend | None = None,
            judge_model: str | None = None,
            keep_workdirs: bool = False) -> list[CaseRun]:
    """Pass one: every variant answers every case, and is graded."""
    variants = list(variants or suite.variants)
    cases = [c for c in (cases or suite.cases) if not c.skip]
    results: list[CaseRun] = []

    for variant, case, repeat in itertools.product(variants, cases, range(suite.repeats)):
        resolved, system = _resolve_prompt(suite, case, variant)
        turns = resolved if isinstance(resolved, tuple) else ()
        prompt = "" if turns else resolved
        workdir = ""
        if variant.mode == "agent":
            workdir = _prepare_workdir(suite, case, variant)

        label = f"{variant.id}/{case.id}"
        if suite.repeats > 1:
            label += f"#{repeat + 1}"
        report(f"  run  {label}")

        completion = backend.complete(Request(
            prompt=prompt, turns=turns,
            system=system, append_system=variant.append_system,
            model=variant.model, effort=variant.effort, tools=variant.tools,
            json_schema=variant.json_schema, mode=variant.mode,
            cwd=workdir or None, max_budget_usd=variant.max_budget_usd,
            thinking=variant.thinking,
            max_thinking_tokens=variant.max_thinking_tokens,
            max_output_tokens=variant.max_output_tokens,
            repeat=repeat,
        ))

        ctx = GradingContext(
            completion=completion, case_id=case.id, variant_id=variant.id,
            vars={**suite.vars, **variant.vars, **case.vars},
            workdir=workdir, judge_backend=judge_backend, judge_model=judge_model,
            suite_dir=str(suite.path.parent) if suite.path else "",
        )
        verdicts = grade(case.graders, ctx)
        results.append(CaseRun(
            case_id=case.id, variant_id=variant.id, repeat=repeat,
            prompt=prompt or "\n---\n".join(turns),
            output=completion.text, verdicts=verdicts,
            completion=completion, workdir=workdir,
        ))
        if workdir and not keep_workdirs:
            shutil.rmtree(workdir, ignore_errors=True)
    return results


def compare(suite: Suite, runs: Sequence[CaseRun], judge_backend: Backend,
            report: Reporter, criterion: str, judge_model: str | None = None,
            extra_redactions: Sequence[str] = (),
            controls: list[dict[str, Any]] | None = None) -> list[PairJudgement]:
    """Pass two: blind pairwise comparison of every variant pair, per case."""
    controls = controls if controls is not None else []
    variant_ids = sorted({r.variant_id for r in runs})
    if len(variant_ids) < 2:
        report("  skip blind comparison: fewer than two variants")
        return []

    models = {r.completion.model for r in runs if r.completion}
    tokens = identity_tokens(variant_ids, models, list(extra_redactions))
    judgements: list[PairJudgement] = []

    # Before spending anything on real comparisons, prove the judge cannot tell
    # two identical candidates apart. If it can, nothing below means anything.
    sample = next((r.output for r in runs if r.output.strip()), "")
    if sample:
        control = identical_pair_control(judge_backend, criterion, sample, judge_model)
        controls.append(control)
        report(f"  control identical-pair: {'PASS' if control['passed'] else 'FAIL'}"
               f" — {control['detail'][:120]}")

    case_ids = sorted({r.case_id for r in runs})
    for case_id in case_ids:
        # Repeat 0 only: comparing repeats of the same variant would inflate n
        # with correlated observations.
        pool = {r.variant_id: r for r in runs if r.case_id == case_id and r.repeat == 0}
        for a_id, b_id in itertools.combinations(variant_ids, 2):
            if a_id not in pool or b_id not in pool:
                continue
            a, b = pool[a_id], pool[b_id]
            report(f"  judge {case_id}: {a_id} vs {b_id} (both orders)")
            judgements.append(judge_pair(
                judge_backend, criterion,
                Candidate(a_id, a.output, a.completion.model if a.completion else ""),
                Candidate(b_id, b.output, b.completion.model if b.completion else ""),
                case_id=case_id, tokens=tokens, model=judge_model,
                seed=f"{suite.name}:{case_id}:{a_id}:{b_id}",
            ))
    return judgements


def execute(suite: Suite, backend: Backend, report: Reporter,
            blind: bool = False, judge_backend: Backend | None = None,
            judge_model: str | None = None, criterion: str | None = None,
            keep_workdirs: bool = False) -> RunResult:
    """Run a suite end to end."""
    started = time.time()
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(started))
    result = RunResult(
        suite=suite.name, run_id=run_id, backend=backend.name,
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
    )

    report(f"suite {suite.name}: {len(suite.variants)} variant(s) x "
           f"{len(suite.cases)} case(s) x {suite.repeats} repeat(s)")
    result.runs = produce(
        suite, backend, report, judge_backend=judge_backend,
        judge_model=judge_model, keep_workdirs=keep_workdirs,
    )

    if blind:
        chosen = criterion or suite.blind.get("criteria") or suite.blind.get("criterion")
        if not chosen:
            result.notes.append(
                "blind comparison requested but the suite defines no `blind.criteria`; "
                "no pairwise judging was run"
            )
            report("  ! no blind criterion configured; skipping comparison")
        elif judge_backend is None:
            result.notes.append("blind comparison requested but no judge backend available")
            report("  ! no judge backend; skipping comparison")
        else:
            result.judge_model = judge_model or ""
            if not judge_model:
                result.notes.append(
                    "no judge model was pinned, so judging ran on whatever the "
                    "backend defaults to. Pin one with --judge-model: a judge is "
                    "a measuring instrument, and an unpinned one makes this run "
                    "incomparable with any other"
                )
            result.judgements = compare(
                suite, result.runs, judge_backend, report, chosen,
                judge_model=judge_model,
                extra_redactions=suite.blind.get("redact", []),
                controls=result.controls,
            )
            # A judge from the same family as a candidate is measured to
            # favour it. Not refused -- sometimes it is the only model
            # available -- but never left unsaid.
            for variant in suite.variants:
                if variant.model and judge_model and same_family(variant.model, judge_model):
                    result.notes.append(
                        f"judge model {judge_model!r} shares a family with variant "
                        f"{variant.id!r} ({variant.model!r}); judges are measured to "
                        f"favour their own family, so read this comparison with that "
                        f"in mind"
                    )
                    break
    # Output length per variant, so a length confound cannot hide behind a
    # win rate.
    per_variant: dict[str, list[int]] = {}
    for run in result.runs:
        per_variant.setdefault(run.variant_id, []).append(len(run.output))
    result.lengths = {vid: round(sum(v) / len(v)) for vid, v in per_variant.items()}

    for candidate in (backend, judge_backend):
        hits = getattr(candidate, "hits", None)
        if hits is not None:
            result.cache_hits += hits
            result.cache_misses += getattr(candidate, "misses", 0)

    result.duration_s = time.time() - started
    return result


def write_run(result: RunResult, directory: str | Path) -> Path:
    """Persist a run so it can be reported on, diffed, or replayed later."""
    out = Path(directory) / result.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (out / "transcript.jsonl").open("w", encoding="utf-8") as fh:
        for run in result.runs:
            if run.completion is None:
                continue
            payload = asdict(run.completion)
            payload.pop("raw", None)
            fh.write(json.dumps({
                "cache_key": Request(
                    prompt=run.prompt, model=run.completion.model, repeat=run.repeat,
                ).cache_key(),
                "case_id": run.case_id, "variant_id": run.variant_id,
                "completion": payload,
            }, ensure_ascii=False) + "\n")
    return out
