"""`python3 -m tools.ultrareview` - run the data checkers and print the evidence.

This is the deterministic half of `/ultrareview`. It makes no judgements a
reader cannot reproduce: every line it prints is either a quoted claim, a file
location, or the exit status of a command it actually ran. Run it twice on an
unchanged tree and you get the same findings, in the same order, with the same
verdicts - the timings differ, because they are measurements of the run rather
than of the repository.

The model-driven half of the review (the part that reads for design, for
altitude, for the claim a checker has no rule for) is described in
`.claude/skills/ultrareview/SKILL.md`. It runs *after* this, never instead of
it, and it is not allowed to overturn a measurement - only to add findings this
cannot reach.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.evidence import Severity
from tools.registry import CheckConfig, load_builtin_checkers, run


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ultrareview",
        description="Check a repository's claims against its own evidence.",
    )
    p.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    p.add_argument("--json", dest="json_out", metavar="PATH",
                   help="write the full machine-readable report here")
    p.add_argument("--markdown", dest="md_out", metavar="PATH",
                   help="write the human-readable report here")
    p.add_argument("--only", default="", metavar="A,B",
                   help="run only these checkers")
    p.add_argument("--exclude", default="", metavar="A,B",
                   help="skip these checkers")
    p.add_argument("--no-run-commands", action="store_true",
                   help="never execute a command from the repository's docs")
    p.add_argument("--network", action="store_true",
                   help="allow checks that need the network (off by default: a "
                        "network-dependent result is not reproducible)")
    p.add_argument("--timeout", type=float, default=120.0,
                   help="per-command timeout in seconds (default: 120)")
    p.add_argument("--sibling", action="append", default=[], metavar="PATH",
                   help="another repository this one points at; repeatable. "
                        "Without it, cross-repository references are reported "
                        "unverifiable rather than assumed broken.")
    p.add_argument("--list", action="store_true", help="list the checkers and exit")
    p.add_argument("--quiet", action="store_true", help="print only the summary line")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        for name, checker in sorted(load_builtin_checkers().items()):
            print(f"  {name:<16} {checker.description}")
        return 0

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    config = CheckConfig(
        run_commands=not args.no_run_commands,
        allow_network=args.network,
        command_timeout=args.timeout,
        sibling_roots=tuple(str(Path(x).resolve()) for x in args.sibling),
        only_checkers=tuple(x for x in args.only.split(",") if x),
        exclude_checkers=tuple(x for x in args.exclude.split(",") if x),
    )

    def announce(name: str) -> None:
        if not args.quiet:
            print(f"  running {name}...", file=sys.stderr, flush=True)

    report = run(root, config, on_start=announce)

    if args.json_out:
        Path(args.json_out).write_text(report.to_json(), "utf-8")
    if args.md_out:
        Path(args.md_out).write_text(report.to_markdown(), "utf-8")
    if not args.quiet and not args.md_out:
        print(report.to_markdown())

    errors = len(report.by_severity(Severity.ERROR))
    warns = len(report.by_severity(Severity.WARN))
    print(
        f"\nultrareview: {len(report.checkers_run)} checkers, "
        f"{errors} error, {warns} warn, {len(report.unverifiable)} unverifiable "
        f"({report.duration_s:.1f}s)",
        file=sys.stderr,
    )
    for name, reason in sorted(report.skipped.items()):
        print(f"  skipped {name}: {reason}", file=sys.stderr)
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
