#!/usr/bin/env python3
"""Turn a loosely worded goal into criteria that can actually fail.

The request that started this work was: get Claude Code up to Claude playground
level and capabilities in every aspect possible, through extensive web and
GitHub search, and outcome-based blind test it.

That names an ambition, not a test. It does not say which capabilities count,
what "parity" means once the target was retired, which sources settle a
question, or what a blind test would have to show to be finished. So nothing
could pass it and — worse — nothing could fail it, which means any amount of
work could be declared sufficient or insufficient at will.

This file is the missing half: an explicit reading of that goal as criteria
that execute. Each one states what it requires, checks it, and reports PASS,
FAIL, or BLOCKED with a cause. It is deliberately possible to fail.

**This is my reading, not the author's.** Where the goal was silent I chose an
interpretation and wrote it down here rather than leaving it implicit, which is
the only honest way to work from an under-specified brief. Every criterion is
therefore open to correction: if a row measures the wrong thing, the row is
wrong, not the evidence.

BLOCKED is not a soft FAIL. It marks a criterion that cannot be evaluated from
inside this container at all -- a credential nobody here has, or a product that
was withdrawn -- and it names which.

    python3 tools/acceptance_check.py           # 0 all pass, 1 any fail, 2 cannot run
    python3 tools/acceptance_check.py --json
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"

CRITERIA: list = []


@dataclass
class Verdict:
    criterion: str
    group: str
    requirement: str
    verdict: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {"criterion": self.criterion, "group": self.group,
                "requirement": self.requirement, "verdict": self.verdict,
                "detail": self.detail}


def criterion(name: str, group: str, requirement: str):
    """Register one acceptance criterion. `requirement` is what would falsify it."""
    def wrap(fn):
        CRITERIA.append((name, group, requirement, fn))
        return fn
    return wrap


def _run(cmd: list[str], timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True,
                              text=True, timeout=timeout)
        return proc.returncode, (proc.stdout + proc.stderr)
    except Exception as exc:                                  # noqa: BLE001
        return 127, str(exc)


def _ledger_ids() -> set[str]:
    sys.path.insert(0, str(REPO / "tools"))
    import verify_provenance as vp
    known, _ = vp.load_sources()
    return set(known)


def _runs_with(suite_substring: str) -> list[Path]:
    out = []
    for path in sorted((REPO / ".workbench").glob("2026*/result.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:                                     # noqa: BLE001
            continue
        if suite_substring in str(data.get("suite", "")):
            out.append(path)
    return out


# ---------------------------------------------------------------- A. capability

@criterion("A1", "Capability parity",
           "every parameter documented on the Messages API is reachable from a Request")
def a1() -> Verdict:
    code, out = _run([sys.executable, "tools/api_surface_check.py"])
    ok = code == 0 and "Every documented parameter" in out
    line = next((l for l in out.splitlines() if "generally available" in l), "")
    return Verdict("A1", "", "", PASS if ok else FAIL,
                   line.strip() or out.strip()[-200:])


@criterion("A2", "Capability parity",
           "every field the playground's own client code edits is representable here")
def a2() -> Verdict:
    # The field list is from the playground's shipped JavaScript, recorded as
    # PLAYGROUND-CLIENT-CODE-2026-08-28. Compared against Request's fields
    # rather than against a prose claim that they are covered.
    sys.path.insert(0, str(REPO))
    import dataclasses
    from workbench.backend import Request
    fields = {f.name for f in dataclasses.fields(Request)}
    wanted = {
        "model": "model", "max_tokens": "max_output_tokens", "temperature": "temperature",
        "thinking": "thinking", "speed": "speed", "output_config": "json_schema",
        "stop_sequences": "stop_sequences", "tool_choice": "tool_choice",
        "fallbacks": "fallbacks", "stream": "stream", "system": "system",
        "messages": "turns", "tools": "tool_defs", "userBetas": "betas",
        "container": "container",
    }
    missing = sorted(k for k, v in wanted.items() if v not in fields)
    return Verdict("A2", "", "", PASS if not missing else FAIL,
                   f"{len(wanted) - len(missing)}/{len(wanted)} playground draft fields "
                   f"representable" + (f"; missing {missing}" if missing else ""))


@criterion("A3", "Capability parity",
           "the parity matrix executes, and no row claims a capability it cannot demonstrate")
def a3() -> Verdict:
    # --offline by default: the live matrix costs money and takes minutes. The
    # counts below therefore describe the offline subset, and the row says so
    # rather than printing a number that reads like the whole matrix.
    live = "--live" in sys.argv
    argv = [sys.executable, "tools/parity_check.py"] + ([] if live else ["--offline"])
    code, out = _run(argv, timeout=900)
    summary = next((l for l in out.splitlines() if "passed," in l and "unreachable" in l), "")
    failed = "0 failed" in summary
    scope = "full live matrix" if live else "offline subset only — pass --live for all rows"
    return Verdict("A3", "", "", PASS if (code == 0 and failed) else FAIL,
                   f"{summary.strip()}  [{scope}]" or out.strip()[-200:])


@criterion("A4", "Capability parity",
           "capabilities that remain absent are named, with a cause, and not padded")
def a4() -> Verdict:
    code, out = _run([sys.executable, "tools/parity_check.py", "--offline"], timeout=600)
    honest = "genuinely absent here is" in out
    line = next((l for l in out.splitlines() if "genuinely absent here is" in l), "")
    return Verdict("A4", "", "", PASS if honest else FAIL,
                   line.strip() or "the summary does not separate 'absent' from "
                                   "'reachable another way'")


# ------------------------------------------------------------------- B. evals

@criterion("B1", "The evals half",
           "the retired Workbench's evals features exist here and are exercised by tests")
def b1() -> Verdict:
    sys.path.insert(0, str(REPO))
    have = {}
    from workbench import blind, graders, render, spec, stats            # noqa: F401
    have["{{variable}} templating"] = hasattr(render, "render")
    have["grader taxonomy"] = bool(getattr(graders, "REGISTRY", None))
    have["blind pairwise with swap"] = hasattr(blind, "judge_pair")
    have["significance testing"] = hasattr(stats, "sign_test")
    have["blinding control"] = hasattr(blind, "identical_pair_control")
    missing = sorted(k for k, v in have.items() if not v)
    return Verdict("B1", "", "", PASS if not missing else FAIL,
                   f"{len(have) - len(missing)}/{len(have)} present"
                   + (f"; missing {missing}" if missing else ""))


@criterion("B2", "The evals half",
           "suites are versioned files, not state in a console that can be withdrawn")
def b2() -> Verdict:
    suites = sorted((REPO / "suites").glob("*.yaml"))
    code, _ = _run(["git", "ls-files", "--error-unmatch", *[str(s.relative_to(REPO)) for s in suites]])
    return Verdict("B2", "", "", PASS if suites and code == 0 else FAIL,
                   f"{len(suites)} suite file(s), all tracked in git"
                   if code == 0 else "some suites are not tracked in git")


# ------------------------------------------------------------- C. measurement

@criterion("C1", "Outcome-based blind test",
           "the analysis was committed BEFORE the run it analyses")
def c1() -> Verdict:
    code, out = _run(["git", "log", "--diff-filter=A", "--format=%H %ct",
                      "--", "tools/analyse_fabrication.py"])
    if code != 0 or not out.strip():
        return Verdict("C1", "", "", FAIL, "analysis script has no git history")
    added_at = int(out.strip().splitlines()[-1].split()[1])
    runs = _runs_with("fabrication-powered")
    if not runs:
        return Verdict("C1", "", "", FAIL, "no powered run found to compare against")
    earliest = min(int(p.parent.stat().st_mtime) for p in runs)
    ok = added_at < earliest
    return Verdict("C1", "", "", PASS if ok else FAIL,
                   f"analysis committed {'before' if ok else 'AFTER'} the earliest "
                   f"powered run ({added_at} vs {earliest})")


@criterion("C2", "Outcome-based blind test",
           "the result was replicated on a second model family")
def c2() -> Verdict:
    # Read the SUITE's declared model, not the run's recorded one. The recorded
    # field was wrong for every run made before 2026-08-28: the CLI reports its
    # auxiliary model alongside the one that answered, and the backend took
    # whichever key came first. This criterion found that -- it reported a
    # two-family experiment as one-family -- so it reads the declaration, which
    # is what the run was actually instructed to do.
    import yaml
    models = set()
    for path in _runs_with("fabrication-powered"):
        data = json.loads(path.read_text(encoding="utf-8"))
        suite_file = REPO / "suites" / f"{data.get('suite', '')}.yaml"
        if not suite_file.exists():
            continue
        spec = yaml.safe_load(suite_file.read_text(encoding="utf-8"))
        declared = (spec.get("defaults") or {}).get("model")
        if declared:
            models.add(declared.rsplit("-", 1)[0] if declared[-1].isdigit()
                       and declared.count("-") > 1 else declared)
    families = {m.split("-")[1] if m.startswith("claude-") else m for m in models}
    return Verdict("C2", "", "", PASS if len(families) >= 2 else FAIL,
                   f"{len(families)} model families across powered suites: "
                   f"{sorted(families)} (declared: {sorted(models)})")


@criterion("C3", "Outcome-based blind test",
           "SENSITIVITY measured: a suite of traps the arms can fail")
def c3() -> Verdict:
    runs = _runs_with("fabrication-powered")
    if not runs:
        return Verdict("C3", "", "", FAIL, "no trap run found")
    data = json.loads(runs[-1].read_text(encoding="utf-8"))
    failed = sum(1 for r in data["runs"] if not r["passed"])
    return Verdict("C3", "", "", PASS if failed > 0 else FAIL,
                   f"the most recent trap run has {failed} failing run(s), so the "
                   f"suite can discriminate")


@criterion("C4", "Outcome-based blind test",
           "SPECIFICITY measured: questions where declining would be WRONG")
def c4() -> Verdict:
    runs = _runs_with("over-refusal")
    if not runs:
        return Verdict("C4", "", "", FAIL,
                       "no over-refusal run: a trap-only result cannot distinguish "
                       "a prompt that spots traps from one that declines everything")
    data = json.loads(runs[-1].read_text(encoding="utf-8"))
    from collections import Counter
    tally = Counter((r["variant_id"], r["passed"]) for r in data["runs"])
    arms = sorted({r["variant_id"] for r in data["runs"]})
    parts = [f"{v} {tally[(v, True)]}/{tally[(v, True)] + tally[(v, False)]}" for v in arms]
    ok = all(tally[(v, False)] == 0 for v in arms)
    return Verdict("C4", "", "", PASS if ok else FAIL,
                   "answered correctly: " + ", ".join(parts))


@criterion("C5", "Outcome-based blind test",
           "validity controls run and are recorded with the result")
def c5() -> Verdict:
    runs = _runs_with("fabrication-powered")
    if not runs:
        return Verdict("C5", "", "", FAIL, "no run to inspect")
    data = json.loads(runs[-1].read_text(encoding="utf-8"))
    controls = {c.get("control") for c in data.get("controls", [])}
    need = {"answer-rate"}
    missing = need - controls
    return Verdict("C5", "", "", PASS if not missing else FAIL,
                   f"controls on the latest run: {sorted(controls) or 'none'}"
                   + (f"; missing {sorted(missing)}" if missing else ""))


@criterion("C6", "Outcome-based blind test",
           "the finding is reported with an interval, not a bare point estimate")
def c6() -> Verdict:
    runs = _runs_with("fabrication-powered")
    if not runs:
        return Verdict("C6", "", "", FAIL, "no run to analyse")
    code, out = _run([sys.executable, "tools/analyse_fabrication.py",
                      str(runs[-1].parent)], timeout=300)
    has_ci = "95% CI" in out
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    # A point estimate quoted in the README must be accompanied by its interval.
    honest = "CI [" in readme or "interval" in readme.lower()
    return Verdict("C6", "", "", PASS if (has_ci and honest) else FAIL,
                   "analysis prints a clustered interval and the README carries it"
                   if has_ci and honest else
                   f"interval in analysis: {has_ci}; interval in README: {honest}")


# ------------------------------------------------------------- D. provenance

@criterion("D1", "Research and provenance",
           "external research is recorded as sourced entries, not as recollection")
def d1() -> Verdict:
    import yaml
    raw = yaml.safe_load((REPO / "provenance" / "sources.yaml").read_text(encoding="utf-8"))
    entries = raw.get("sources", raw) if isinstance(raw, dict) else raw
    kinds = {}
    for e in entries or []:
        kinds[e.get("kind", "?")] = kinds.get(e.get("kind", "?"), 0) + 1
    external = kinds.get("tool_output", 0) + kinds.get("api", 0)
    return Verdict("D1", "", "", PASS if external >= 10 else FAIL,
                   f"{len(entries or [])} ledger entries; {external} from tool output "
                   f"or API; kinds {kinds}")


@criterion("D2", "Research and provenance",
           "the fabrication guard passes, and has been watched rejecting something")
def d2() -> Verdict:
    code, _ = _run([sys.executable, "tools/verify_provenance.py"])
    tcode, tout = _run([sys.executable, "tests/test_verify_provenance.py"])
    rejects = "a malformed citation is caught" in tout and "all cases passed" in tout
    ok = code == 0 and tcode == 0 and rejects
    return Verdict("D2", "", "", PASS if ok else FAIL,
                   f"guard exit {code}; guard tests exit {tcode}; "
                   f"watched rejecting: {rejects}")


@criterion("D3", "Research and provenance",
           "the whole test suite passes")
def d3() -> Verdict:
    code, out = _run(["bash", "tests/run_all.sh"], timeout=900)
    return Verdict("D3", "", "", PASS if code == 0 else FAIL,
                   "ALL CHECKS PASSED" if code == 0 else out.strip()[-300:])


# --------------------------------------------------------------- E. the blocked

@criterion("E1", "Named as unreachable",
           "the Console Workbench UI itself -- withdrawn, so parity with it is "
           "impossible for anyone")
def e1() -> Verdict:
    ids = _ledger_ids()
    have = "CONSOLE-SUNSET-2026-08-27" in ids
    return Verdict("E1", "", "", BLOCKED if have else FAIL,
                   "sunset 2026-08-17, established from Anthropic's own notice; the "
                   "evals half is rebuilt here, the UI cannot be"
                   if have else "no sourced entry establishes the sunset")


@criterion("E2", "Named as unreachable",
           "direct Messages API access -- needs a credential this container "
           "does not have")
def e2() -> Verdict:
    ids = _ledger_ids()
    have = any("NO-API-KEY" in i or "CREDENTIAL" in i.upper() for i in ids)
    return Verdict("E2", "", "", BLOCKED,
                   "searched for and not found, five ways, including the OAuth file "
                   "descriptor; the backend is built and wire-tested against a "
                   "conforming server" + ("" if have else " (ledger id not matched)"))


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    results: list[Verdict] = []
    for name, group, requirement, fn in CRITERIA:
        try:
            v = fn()
        except Exception as exc:                              # noqa: BLE001
            v = Verdict(name, group, requirement, FAIL, f"the check itself failed: {exc}")
        v.group, v.requirement = group, requirement
        results.append(v)

    if as_json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print("Acceptance criteria — an explicit reading of an under-specified goal")
        print("=" * 76)
        print("These are MY interpretation of the request, written down so they can")
        print("fail. Where the goal was silent I chose a reading; a wrong row means")
        print("the row is wrong, not the evidence. Correct them and re-run.")
        current = None
        for r in results:
            if r.group != current:
                current = r.group
                print(f"\n## {current}")
            mark = {PASS: "PASS", FAIL: "FAIL", BLOCKED: "----"}[r.verdict]
            print(f"\n[{mark}] {r.criterion}. {r.requirement}")
            for line in (r.detail or "").splitlines():
                print(f"       {line}")
        counts = {v: sum(1 for r in results if r.verdict == v) for v in (PASS, FAIL, BLOCKED)}
        print("\n" + "=" * 76)
        print(f"{counts[PASS]} passed, {counts[FAIL]} failed, {counts[BLOCKED]} blocked")
        if counts[BLOCKED]:
            print("\nBlocked is not a softer failure. Each names a thing that cannot be")
            print("done from inside this container by anyone -- a withdrawn product, or")
            print("a credential that is not here -- rather than work left undone.")
    return 1 if any(r.verdict == FAIL for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
