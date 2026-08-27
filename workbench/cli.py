"""``python3 -m workbench`` -- the command surface.

Subcommands, and why each exists:

``doctor``      What can this machine actually do? Backends, judge, cost
                accounting, and what is missing. Run it first.
``plan``        Show the exact request each variant would send, without
                sending it. This is the playground's "see the request" panel:
                the resolved prompt, the resolved system prompt, the flags.
``run``         Produce and grade. Deterministic graders only unless the suite
                asks for a judge.
``blind``       Produce, grade, then compare variants blind in both orders.
``report``      Re-render a stored run. Costs nothing.
``graders``     List the grader types and what kind of evidence each yields.
``export-eval`` Emit the suite as ``claude plugin eval`` cases, so a suite
                written here can be run by the tool that ships with Claude
                Code rather than only by this one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .backend import ClaudeCLIBackend, Request, resolve_backend
from .errors import WorkbenchError
from .graders import describe_registry
from .report import markdown, to_json
from .runner import execute, write_run
from .spec import load_suite

DEFAULT_RUN_DIR = ".workbench"
EXIT_OK, EXIT_FINDINGS, EXIT_CANNOT_RUN = 0, 1, 2


def _reporter(quiet: bool):
    def report(message: str) -> None:
        if not quiet:
            print(message, file=sys.stderr, flush=True)
    return report


# --------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    """Report what this environment can and cannot do, without guessing."""
    print("workbench doctor")
    print("=" * 60)

    cli = ClaudeCLIBackend()
    ok, detail = cli.available()
    print(f"claude CLI backend    : {'yes' if ok else 'NO'} — {detail}")

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"ANTHROPIC_API_KEY     : {'set' if has_key else 'not set'}")
    if not has_key:
        print("                        Direct Messages API calls are unavailable, so")
        print("                        `temperature`/`top_p`/`top_k`/`max_tokens` cannot be")
        print("                        set. On current models those parameters are")
        print("                        deprecated and rejected anyway.")

    plugin_eval = "unknown"
    if shutil.which("claude"):
        probe = subprocess.run(["claude", "plugin", "eval", "--help"],
                               capture_output=True, text=True, timeout=60)
        plugin_eval = "available" if probe.returncode == 0 else "not available"
    print(f"claude plugin eval    : {plugin_eval}")
    if plugin_eval == "available":
        print("                        Plugin-scoped eval cases with a with/without")
        print("                        ablation. Use `export-eval` to hand a suite to it.")

    print(f"echo backend          : yes — offline, free, deterministic")
    print(f"graders registered    : {len(describe_registry())}")
    print()
    print("Controllable per variant on this backend:")
    print("  model, effort, system prompt, appended system prompt,")
    print("  tool availability, JSON output schema, per-run budget ceiling.")
    print("  thinking mode and thinking-token budget    [undocumented flags]")
    print("  max output tokens is PLUMBED but did not work when measured —")
    print("  see `python3 tools/parity_check.py`, which records it as a FAIL")
    print()
    print("  `--thinking` and `--max-thinking-tokens` are accepted by the CLI")
    print("  parser but absent from `claude --help`. They were found by probing")
    print("  the parser, not by reading documentation, and may change without")
    print("  notice. Verified working here: setting a budget changed the")
    print("  reported thinking_tokens on an otherwise identical call.")
    print()
    print("Not controllable:")
    print("  temperature, top_p, top_k, stop_sequences — no CLI flag under any")
    print("  spelling probed, and on models after Opus 4.6 the first three are")
    print("  rejected by the API with a 400 regardless.")
    return EXIT_OK if ok else EXIT_CANNOT_RUN


def cmd_graders(args: argparse.Namespace) -> int:
    by_kind: dict[str, list[str]] = {}
    for name, kind in describe_registry():
        by_kind.setdefault(kind, []).append(name)
    blurb = {
        "deterministic": "same input, same verdict, forever — free and instant",
        "environmental": "depends on this machine: a command, a file, a ceiling",
        "model": "a model decided; reported separately because it is an opinion",
    }
    for kind in ("deterministic", "environmental", "model"):
        names = by_kind.get(kind, [])
        print(f"\n{kind}  — {blurb[kind]}")
        for name in names:
            print(f"  {name}")
    print()
    return EXIT_OK


def cmd_plan(args: argparse.Namespace) -> int:
    """Resolve every request the suite would send, and show it. No calls made."""
    from .runner import _resolve_prompt

    suite = load_suite(args.suite)
    cli = ClaudeCLIBackend()
    total = 0
    print(f"suite {suite.name}: {len(suite.variants)} variant(s) x "
          f"{len(suite.cases)} case(s) x {suite.repeats} repeat(s)")
    for variant in suite.variants:
        for case in suite.cases:
            if case.skip:
                continue
            total += suite.repeats
            prompt, system = _resolve_prompt(suite, case, variant)
            request = Request(
                prompt=prompt, system=system, append_system=variant.append_system,
                model=variant.model, effort=variant.effort, tools=variant.tools,
                json_schema=variant.json_schema, mode=variant.mode,
                thinking=variant.thinking,
                max_thinking_tokens=variant.max_thinking_tokens,
                max_output_tokens=variant.max_output_tokens,
            )
            print("\n" + "=" * 70)
            print(f"{variant.id} / {case.id}   [{variant.mode} mode]")
            print("-" * 70)
            print("argv:")
            argv = cli._argv(request)
            print("  " + " ".join(
                repr(a) if (" " in a or "\n" in a or a == "") else a for a in argv[:6]
            ) + " ...")
            if system:
                print(f"system ({len(system)} chars):")
                print("  " + system.strip()[:400].replace("\n", "\n  "))
            print(f"prompt ({len(prompt)} chars):")
            print("  " + prompt.strip()[:600].replace("\n", "\n  "))
            print(f"graders: {', '.join(g.label for g in case.graders) or 'none'}")
    print("\n" + "=" * 70)
    variants, cases = len(suite.variants), len([c for c in suite.cases if not c.skip])
    pairs = variants * (variants - 1) // 2 * cases
    print(f"{total} model call(s) would be made.")
    if variants > 1:
        print(f"`blind` would add {2 * pairs} judge call(s) — {pairs} variant "
              f"pair(s) x 2 presentation orders — plus 2 for the identical-pair "
              f"blinding control. Total with blind: {total + 2 * pairs + 2}.")
    return EXIT_OK


def _build_backends(args: argparse.Namespace):
    cache = None if args.no_cache else Path(args.run_dir) / "cache"
    backend = resolve_backend(args.backend, cache_dir=cache, transcript=args.transcript)
    if args.judge_backend == "same":
        judge = backend
    elif args.judge_backend == "none":
        judge = None
    else:
        judge = resolve_backend(args.judge_backend, cache_dir=cache)
    return backend, judge


def _run(args: argparse.Namespace, blind: bool) -> int:
    report = _reporter(args.quiet)
    suite = load_suite(args.suite)
    backend, judge = _build_backends(args)

    if blind and not args.judge_model:
        print(
            "workbench: --judge-model was not given, so judges will run on the "
            "backend's default model, which may be the session's (expensive) "
            "default. Pin a cheaper model from a DIFFERENT family than the "
            "variants under test, e.g. --judge-model claude-sonnet-5.",
            file=sys.stderr,
        )

    usable, detail = backend.available()
    if not usable:
        print(f"backend {args.backend!r} cannot run here: {detail}", file=sys.stderr)
        return EXIT_CANNOT_RUN

    result = execute(
        suite, backend, report, blind=blind, judge_backend=judge,
        judge_model=args.judge_model, criterion=args.criterion,
        keep_workdirs=args.keep_workdirs,
    )
    out_dir = write_run(result, args.run_dir)
    rendered = markdown(result)
    (out_dir / "report.md").write_text(rendered, encoding="utf-8")

    if args.json:
        print(to_json(result))
    else:
        print(rendered)
    report(f"\nwritten to {out_dir}")

    failed = sum(1 for r in result.runs if not r.passed)
    if args.threshold is not None:
        rate = 1 - failed / len(result.runs) if result.runs else 0.0
        return EXIT_OK if rate >= args.threshold else EXIT_FINDINGS
    return EXIT_FINDINGS if failed else EXIT_OK


def cmd_run(args: argparse.Namespace) -> int:
    return _run(args, blind=False)


def cmd_blind(args: argparse.Namespace) -> int:
    return _run(args, blind=True)


def cmd_report(args: argparse.Namespace) -> int:
    path = Path(args.run)
    payload = json.loads((path / "result.json").read_text(encoding="utf-8"))
    print(json.dumps(payload, indent=2) if args.json
          else (path / "report.md").read_text(encoding="utf-8"))
    return EXIT_OK


def cmd_export_eval(args: argparse.Namespace) -> int:
    """Write the suite as ``claude plugin eval`` cases.

    A suite written here is not locked in here. ``claude plugin eval`` grades
    tool use and file effects that this package does not, so a case that wants
    those should run there. The translation is partial and says so: only the
    grader types both sides understand are emitted, and anything dropped is
    listed on stderr rather than silently lost.
    """
    from .runner import _resolve_prompt

    suite = load_suite(args.suite)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # `claude plugin eval`'s regex grader takes match: contains | not_contains |
    # count:N, so the substring graders translate into it rather than being
    # dropped. Anything genuinely without an equivalent on the other side is
    # reported, not silently lost.
    translatable = {"regex", "file_exists", "judge", "contains", "not_contains", "equals"}
    dropped: list[str] = []
    written = 0

    for case in suite.cases:
        if case.skip:
            continue
        variant = suite.variants[0]
        prompt, _system = _resolve_prompt(suite, case, variant)
        case_dir = out / case.id
        (case_dir / "graders").mkdir(parents=True, exist_ok=True)

        front = ["---", f"name: {case.id}", f"runs: {suite.repeats}"]
        if variant.model:
            front.append(f"model: {variant.model}")
        front.append("---")
        (case_dir / "prompt.md").write_text(
            "\n".join(front) + "\n\n" + prompt, encoding="utf-8"
        )

        for i, g in enumerate(case.graders):
            if g.type not in translatable:
                dropped.append(f"{case.id}: {g.type}")
                continue
            if g.type == "regex":
                body = ["---", "type: regex",
                        f"pattern: {json.dumps(str(g.config.get('pattern', '')))}",
                        f"match: {g.config.get('match', 'contains')}", "---", ""]
            elif g.type in ("contains", "not_contains", "equals"):
                # A substring check is a regex over its own escaped literal.
                match = "not_contains" if g.type == "not_contains" else "contains"
                pattern = re.escape(str(g.config.get("value", "")))
                body = ["---", "type: regex",
                        f"pattern: {json.dumps(pattern)}",
                        "flags: i" if g.config.get("ignore_case", True) else "",
                        f"match: {match}", "---", ""]
                body = [line for line in body if line != ""] + [""]
                if g.type == "equals":
                    dropped.append(f"{case.id}: equals (exported as a substring "
                                   f"check; it no longer requires an exact match)")
            elif g.type == "file_exists":
                body = ["---", "type: file_exists",
                        f"path: {g.config.get('path', '')}", "---", ""]
            else:
                criterion = g.config.get("criteria") or g.config.get("rubric", "")
                body = ["---", "type: llm", "---", "", str(criterion)]
            (case_dir / "graders" / f"{i:02d}-{g.type}.md").write_text(
                "\n".join(body), encoding="utf-8"
            )
        written += 1

    print(f"wrote {written} case(s) to {out}")
    print(f"run them with:  claude plugin eval --eval-dir {out.name}")
    if dropped:
        print("\nNot translated — `claude plugin eval` has no equivalent grader, "
              "so these checks exist only in the workbench suite:", file=sys.stderr)
        for item in sorted(set(dropped)):
            print(f"  {item}", file=sys.stderr)
    if len(suite.variants) > 1:
        print(f"\nNote: the suite has {len(suite.variants)} variants; "
              f"`claude plugin eval` compares with-plugin against without-plugin, "
              f"not N prompt variants, so only {suite.variants[0].id!r} was "
              f"exported. Use `workbench blind` for the N-way comparison.",
              file=sys.stderr)
    return EXIT_OK


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workbench",
        description="Prompt variants, graded, and compared blind.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="what this environment can do").set_defaults(fn=cmd_doctor)
    sub.add_parser("graders", help="list grader types").set_defaults(fn=cmd_graders)

    plan = sub.add_parser("plan", help="show the requests without sending them")
    plan.add_argument("suite")
    plan.set_defaults(fn=cmd_plan)

    for name, fn, blurb in (
        ("run", cmd_run, "run a suite and grade it"),
        ("blind", cmd_blind, "run a suite, then compare variants blind"),
    ):
        p = sub.add_parser(name, help=blurb)
        p.add_argument("suite")
        p.add_argument("--backend", default="claude-cli",
                       help="claude-cli | echo | replay (default: claude-cli)")
        p.add_argument("--judge-backend", default="same",
                       help="same | none | echo | claude-cli (default: same)")
        p.add_argument("--judge-model", default=None,
                       help="model for judges; defaults to the variant's model")
        p.add_argument("--criterion", default=None,
                       help="override the suite's blind comparison criterion")
        p.add_argument("--transcript", default=None, help="for --backend replay")
        p.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
        p.add_argument("--no-cache", action="store_true",
                       help="do not reuse completions cached on disk")
        p.add_argument("--keep-workdirs", action="store_true",
                       help="agent mode: leave scratch directories in place")
        p.add_argument("--threshold", type=float, default=None,
                       help="exit 0 only if the pass rate reaches this (0-1)")
        p.add_argument("--json", action="store_true", help="emit JSON, not markdown")
        p.add_argument("-q", "--quiet", action="store_true")
        p.set_defaults(fn=fn)

    rep = sub.add_parser("report", help="re-render a stored run")
    rep.add_argument("run", help="path to a run directory under .workbench/")
    rep.add_argument("--json", action="store_true")
    rep.set_defaults(fn=cmd_report)

    exp = sub.add_parser("export-eval", help="emit the suite as claude plugin eval cases")
    exp.add_argument("suite")
    exp.add_argument("--out", default="evals")
    exp.set_defaults(fn=cmd_export_eval)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except WorkbenchError as exc:
        print(f"workbench: {exc}", file=sys.stderr)
        return EXIT_CANNOT_RUN
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
