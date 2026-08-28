"""Command line entry point.

Subcommands are grouped by the stage of the pipeline they drive. Only the
`reflect` group - the nightly self-improvement loop - is built today; the
retrieval commands are declared here so `make` targets and `--help` tell the
truth about what exists rather than dying with an ImportError. See
`internal/PLAN.md` for the build order.

Imports of the loop are deliberately deferred into each handler. `ooda --help`
and `ooda reflect schedule` must work on a machine where some optional piece is
broken, and a top-level import would make the entire CLI hostage to the
weakest module in it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_BUILT = 2

_SINCE_RE = re.compile(r"^(\d+(?:\.\d+)?)([smhdw])$")
_SINCE_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_since(value: str | None) -> float | None:
    """Accept "36h", "2d", "2026-08-01", or a bare unix timestamp.

    Returns an absolute unix time, or None to mean "carry on from where the last
    cycle finished" - which is the default and almost always the right answer.
    """
    if not value:
        return None
    value = value.strip()
    match = _SINCE_RE.match(value)
    if match:
        return time.time() - float(match.group(1)) * _SINCE_UNITS[match.group(2)]
    if value in {"all", "always", "0"}:
        return 0.0
    try:
        return float(value)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return time.mktime(time.strptime(value, fmt))
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"--since: expected 36h / 2d / YYYY-MM-DD / a unix timestamp, got {value!r}"
    )


def _build_config(args: argparse.Namespace):
    from oodarag.reflect.decide.policy import PolicyConfig
    from oodarag.reflect.loop import ReflectConfig

    policy = PolicyConfig()
    if getattr(args, "max_edits", None) is not None:
        policy.max_auto_edits = args.max_edits
    return ReflectConfig(
        root=Path(getattr(args, "root", ".") or ".").resolve(),
        dry_run=not getattr(args, "apply", False),
        enabled_rules=list(getattr(args, "rule", []) or []),
        disabled_rules=list(getattr(args, "skip_rule", []) or []),
        enabled_sources=list(getattr(args, "source", []) or []),
        policy=policy,
    )


# -- reflect handlers --------------------------------------------------------


def cmd_reflect_run(args: argparse.Namespace) -> int:
    from oodarag.reflect.loop import ReflectLoop

    config = _build_config(args)
    loop = ReflectLoop(config)
    report = loop.run_cycle(since=parse_since(args.since))

    if args.json:
        print(report.to_json())
        return EXIT_OK

    path = Path(report.report_path) if report.report_path else None
    if path and path.exists() and not args.quiet:
        print(path.read_text("utf-8"))
    verdict = "dry run" if config.dry_run else "applied"
    print(
        f"\n[{report.cycle_id}] {report.signals} signals -> "
        f"{len(report.findings)} findings -> {len(report.applied)} applied "
        f"({verdict}), {len(report.queued)} awaiting review",
        file=sys.stderr,
    )
    if path:
        print(f"report: {path}", file=sys.stderr)
    if config.dry_run and report.proposals:
        print("re-run with --apply to let it make the safe-tier changes", file=sys.stderr)
    return EXIT_OK


def cmd_reflect_status(args: argparse.Namespace) -> int:
    from oodarag.reflect.journal import Journal
    from oodarag.reflect.act.queue import ReviewQueue

    config = _build_config(args)
    journal = Journal(config.journal_dir)
    queue = ReviewQueue(config.queue_path)
    summary = journal.summary()
    summary["queue_pending"] = len(queue.pending())
    summary["queue_accepted"] = len(queue.accepted())
    summary["root"] = str(config.root)
    summary["state_dir"] = str(config.state_dir)
    last = journal.last_cycle()
    if last:
        summary["last_run_at"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(last.get("ended_at") or 0)
        )
    if args.json:
        print(json.dumps(summary, indent=2))
        return EXIT_OK
    for key, value in summary.items():
        print(f"{key:16} {value}")
    return EXIT_OK


def cmd_reflect_report(args: argparse.Namespace) -> int:
    config = _build_config(args)
    reports = config.reports_dir
    if not reports.exists():
        print("no reports yet - run `ooda reflect run` first", file=sys.stderr)
        return EXIT_ERROR
    if args.list:
        for path in sorted(reports.glob("*.md")):
            if path.name != "latest.md":
                print(path.stem)
        return EXIT_OK
    target = reports / (f"{args.cycle}.md" if args.cycle else "latest.md")
    if not target.exists():
        print(f"no such report: {target}", file=sys.stderr)
        return EXIT_ERROR
    print(target.read_text("utf-8"))
    return EXIT_OK


def cmd_reflect_queue(args: argparse.Namespace) -> int:
    from oodarag.reflect.act.queue import ReviewQueue

    config = _build_config(args)
    queue = ReviewQueue(config.queue_path)
    items = queue.items() if args.all else queue.pending()
    if args.json:
        print(json.dumps(items, indent=2, default=str))
        return EXIT_OK
    if not items:
        print("queue is empty")
        return EXIT_OK
    for entry in items:
        proposal = entry.get("proposal", {})
        fingerprint = entry.get("fingerprint", "")[:8]
        seen = entry.get("times_seen", 1)
        nag = f"  (seen {seen}x)" if seen > 1 else ""
        print(f"{fingerprint}  [{proposal.get('risk','?'):6}] {proposal.get('title','')}{nag}")
        for path in proposal.get("paths", []):
            print(f"          {path}")
    print("\naccept: ooda reflect accept <id>   dismiss: ooda reflect dismiss <id>")
    return EXIT_OK


def _queue_verdict(args: argparse.Namespace, action: str) -> int:
    from oodarag.reflect.act.queue import ReviewQueue
    from oodarag.reflect.journal import Journal
    from oodarag.reflect.models import Outcome

    config = _build_config(args)
    queue = ReviewQueue(config.queue_path)
    try:
        entry = queue.accept(args.fingerprint) if action == "accept" else queue.dismiss(
            args.fingerprint, note=getattr(args, "note", "") or ""
        )
    except ValueError as e:  # ambiguous prefix
        print(str(e), file=sys.stderr)
        return EXIT_ERROR
    if not entry:
        print(f"no queued proposal matching {args.fingerprint!r}", file=sys.stderr)
        return EXIT_ERROR

    if action == "dismiss":
        # Recorded immediately, not at the next cycle: a dismissal is the user's
        # verdict and must suppress the suggestion even if the loop never runs again.
        Journal(config.journal_dir).record_outcome(
            Outcome(
                fingerprint=entry["fingerprint"],
                rule_id=entry.get("proposal", {}).get("finding", {}).get("rule_id", ""),
                verdict="dismissed",
                note=getattr(args, "note", "") or "",
            )
        )
        print(f"dismissed {entry['fingerprint'][:8]} - it will not be suggested again")
        return EXIT_OK

    print(f"accepted {entry['fingerprint'][:8]}: {entry.get('proposal', {}).get('title', '')}")
    if args.now:
        from oodarag.reflect.loop import ReflectLoop

        config.dry_run = False
        report = ReflectLoop(config).run_cycle(since=time.time())
        print(f"applied in cycle {report.cycle_id}")
    else:
        print("it will be applied on the next `ooda reflect run --apply` (or use --now)")
    return EXIT_OK


def cmd_reflect_accept(args: argparse.Namespace) -> int:
    return _queue_verdict(args, "accept")


def cmd_reflect_dismiss(args: argparse.Namespace) -> int:
    return _queue_verdict(args, "dismiss")


def cmd_reflect_revert(args: argparse.Namespace) -> int:
    from oodarag.reflect.loop import ReflectLoop

    config = _build_config(args)
    config.dry_run = False
    result = ReflectLoop(config).revert(args.cycle)
    print(f"reverted {result.applied_count} file(s) from cycle {args.cycle}")
    for item in result.results:
        print(f"  {'ok  ' if item.applied else 'skip'} {item.path}  {item.reason}")
    return EXIT_OK if result.applied_count or not result.results else EXIT_ERROR


def cmd_reflect_rules(args: argparse.Namespace) -> int:
    from oodarag.reflect.decide.priors import RulePriors
    from oodarag.reflect.detect.base import registry
    from oodarag.reflect.journal import Journal

    config = _build_config(args)
    priors = RulePriors(Journal(config.journal_dir))
    rows = []
    for rule_id, cls in sorted(registry().items()):
        rows.append(
            {
                "rule": rule_id,
                "severity": cls.severity,
                "consumes": ",".join(cls.consumes),
                "confidence": round(priors.confidence(rule_id), 3),
                "title": cls.title,
            }
        )
    if args.json:
        print(json.dumps(rows, indent=2))
        return EXIT_OK
    if not rows:
        print("no rules registered", file=sys.stderr)
        return EXIT_ERROR
    width = max(len(r["rule"]) for r in rows)
    for row in rows:
        print(f"{row['rule']:<{width}}  {row['confidence']:.2f}  {row['severity']:<8} {row['title']}")
    print(f"\n{len(rows)} rules. confidence is learned from your accept/dismiss history.")
    return EXIT_OK


def cmd_reflect_schedule(args: argparse.Namespace) -> int:
    from oodarag.reflect.schedule import ScheduleSpec, install_hint, render

    root = Path(args.root or ".").resolve()
    try:
        spec = ScheduleSpec.parse(root, args.at, apply=args.apply)
        files = render(args.kind, spec)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return EXIT_ERROR

    if not args.write:
        for name, content in files.items():
            print(f"# ---- {name} ----")
            print(content)
        print("# pass --write to save these", file=sys.stderr)
        return EXIT_OK

    out_dir = Path(args.write)
    written: list[Path] = []
    for name, content in files.items():
        # A backend may name a path (the GitHub workflow) rather than a bare file.
        target = (root / name) if "/" in name else (out_dir / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(target)
    print(install_hint(args.kind, spec, written))
    return EXIT_OK


# -- ingest ------------------------------------------------------------------


def _write_documents(path: Path, documents: list, *, truncate: bool) -> int:
    """Persist RawDocuments as JSON Lines.

    JSONL rather than one file per document: the next stage reads this as a
    stream, and a directory of 4,000 small files is slower to walk than one file
    is to read.

    The file is an append-only *delta stream*, not a snapshot, because that is
    what an incremental connector produces. A connector returns only what is new
    or changed, so rewriting the file each run would delete every document that
    happened not to change - and the run that does the damage is the quiet one
    that reports "unchanged 1, written 0". Only `--fresh`, which deliberately
    re-reads the whole source, truncates. Downstream takes the last record per
    external_id.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if truncate:
        # Atomic for the full-snapshot case: an interrupted --fresh leaves the
        # previous output intact rather than a half-written mixture of two.
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            written = _dump(tmp, documents, mode="w")
            tmp.replace(path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        return written
    if not documents:
        return 0
    return _dump(path, documents, mode="a")


def _dump(path: Path, documents: list, mode: str) -> int:
    written = 0
    with path.open(mode, encoding="utf-8") as fh:
        for doc in documents:
            fh.write(json.dumps({
                "source_system": doc.source_system,
                "external_id": doc.external_id,
                "uri": doc.uri,
                "title": doc.title,
                "text": doc.text,
                "metadata": doc.metadata,
                "fetched_at": round(doc.fetched_at, 3),
                "content_hash": doc.content_hash,
            }, ensure_ascii=False, default=str) + "\n")
            written += 1
    return written


def _report_delta(delta, documents: int, out: Path, as_json: bool) -> None:
    payload = delta.as_dict()
    payload["documents_written"] = documents
    payload["output"] = str(out)
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
        return
    print(f"source     {delta.source_key}")
    print(f"new        {delta.new}")
    print(f"changed    {delta.changed}")
    print(f"unchanged  {delta.unchanged}")
    print(f"failed     {delta.failed}")
    print(f"seconds    {delta.duration_s}")
    print(f"written    {documents} document(s) -> {out}")
    for err in delta.errors[:5]:
        print(f"  ! {err}", file=sys.stderr)
    if delta.failed and not delta.touched:
        print("nothing was ingested; see the errors above", file=sys.stderr)


def _run_connector(connector, args) -> int:
    from oodarag.ingest.base import JsonStateStore

    root = Path(args.root or ".").resolve()
    state_path = Path(args.state) if args.state else root / ".oodarag" / "ingest" / "state.json"
    out = Path(args.out) if args.out else (
        root / ".data" / "raw" / f"{connector.key.replace(':', '_').replace('/', '_')}.jsonl"
    )
    # --fresh drops the cursor rather than the output: re-reading a source is
    # cheap to ask for and impossible to undo if it also deleted what you had.
    state = None if args.fresh else JsonStateStore(state_path)
    result = connector.run(state=state, limit=args.limit)
    written = _write_documents(out, result.documents, truncate=args.fresh)
    _report_delta(result.delta, written, out, args.json)
    return EXIT_OK if not (result.delta.failed and not result.delta.touched) else EXIT_ERROR


def cmd_ingest_web(args: argparse.Namespace) -> int:
    from oodarag.ingest.web import WebConnector

    options = {}
    for name in ("max_pages", "max_depth", "max_bytes", "max_seconds"):
        value = getattr(args, name, None)
        if value is not None:
            options[name] = value
    return _run_connector(WebConnector(seeds=args.seeds, **options), args)


def cmd_ingest_github(args: argparse.Namespace) -> int:
    from oodarag.ingest.github import GitHubConnector

    if "/" not in args.repo:
        print(f"expected OWNER/REPO, got {args.repo!r}", file=sys.stderr)
        return EXIT_ERROR
    owner, _, repo = args.repo.partition("/")
    return _run_connector(
        GitHubConnector(owner=owner, repo=repo, ref=args.ref,
                        include_paths=tuple(args.include or ()),
                        exclude_paths=tuple(args.exclude or ())),
        args,
    )


# -- not-yet-built pipeline stages -------------------------------------------


def cmd_not_built(args: argparse.Namespace) -> int:
    print(
        f"`ooda {args.command}` is not built yet.\n"
        f"The retrieval pipeline is under construction; see internal/PLAN.md for the\n"
        f"build order and what landed already. `ooda reflect --help` works today.",
        file=sys.stderr,
    )
    return EXIT_NOT_BUILT


# -- parser ------------------------------------------------------------------


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="workspace root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ooda",
        description="An OODA-driven retrieval pipeline, and a nightly loop that improves "
        "your files from what you actually did all day.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    reflect = sub.add_parser(
        "reflect",
        help="the nightly self-improvement loop",
        description="Observe your prompts, commands, files and commits; find what could be "
        "better; propose and apply the safe changes; learn from your verdicts.",
    )
    rsub = reflect.add_subparsers(dest="subcommand", required=True)

    run = rsub.add_parser("run", help="run one OODA cycle (dry run unless --apply)")
    _add_common(run)
    run.add_argument("--apply", action="store_true", help="actually write the safe-tier edits")
    run.add_argument("--since", help="observation window start: 36h, 2d, YYYY-MM-DD, or 'all'")
    run.add_argument("--rule", action="append", help="only run these rules (repeatable, prefix ok)")
    run.add_argument("--skip-rule", action="append", help="disable rules (repeatable, prefix ok)")
    run.add_argument("--source", action="append", help="only these sources (repeatable)")
    run.add_argument("--max-edits", type=int, help="cap auto-applied edits this cycle")
    run.add_argument("--quiet", action="store_true", help="suppress the report body")
    run.set_defaults(func=cmd_reflect_run)

    status = rsub.add_parser("status", help="what the loop knows so far")
    _add_common(status)
    status.set_defaults(func=cmd_reflect_status)

    report = rsub.add_parser("report", help="print a nightly report")
    _add_common(report)
    report.add_argument("--cycle", help="cycle id (default: latest)")
    report.add_argument("--list", action="store_true", help="list available reports")
    report.set_defaults(func=cmd_reflect_report)

    queue = rsub.add_parser("queue", help="proposals awaiting your call")
    _add_common(queue)
    queue.add_argument("--all", action="store_true", help="include accepted and dismissed")
    queue.set_defaults(func=cmd_reflect_queue)

    accept = rsub.add_parser("accept", help="approve a queued proposal")
    _add_common(accept)
    accept.add_argument("fingerprint", help="id from the report or queue (8 chars is enough)")
    accept.add_argument("--now", action="store_true", help="apply it immediately")
    accept.set_defaults(func=cmd_reflect_accept)

    dismiss = rsub.add_parser("dismiss", help="decline a proposal, permanently")
    _add_common(dismiss)
    dismiss.add_argument("fingerprint", help="id from the report or queue")
    dismiss.add_argument("--note", help="why - recorded in the journal")
    dismiss.set_defaults(func=cmd_reflect_dismiss)

    revert = rsub.add_parser("revert", help="undo everything one cycle applied")
    _add_common(revert)
    revert.add_argument("cycle", help="cycle id, e.g. 20260827-223000")
    revert.set_defaults(func=cmd_reflect_revert)

    rules = rsub.add_parser("rules", help="list rules and their learned confidence")
    _add_common(rules)
    rules.set_defaults(func=cmd_reflect_rules)

    schedule = rsub.add_parser("schedule", help="generate an end-of-day schedule")
    schedule.add_argument("--root", default=".", help="workspace root")
    schedule.add_argument(
        "--kind", default="systemd", choices=["cron", "systemd", "launchd", "github"]
    )
    schedule.add_argument("--at", default="22:30", help="local time, HH:MM (default 22:30)")
    schedule.add_argument("--apply", action="store_true", help="schedule it in applying mode")
    schedule.add_argument("--write", nargs="?", const=".", help="write the files (default: print)")
    schedule.set_defaults(func=cmd_reflect_schedule)

    ingest = sub.add_parser(
        "ingest",
        help="fetch documents from a source, without indexing them",
        description="Run one connector and write the documents it returns as JSON Lines. "
        "Incremental by content hash: a second run reports what actually changed.",
    )
    isub = ingest.add_subparsers(dest="source", required=True)

    def _add_ingest_common(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--root", default=".", help="workspace root (default: cwd)")
        parser.add_argument("--out", help="output JSONL path")
        parser.add_argument("--state", help="cursor file (default: .oodarag/ingest/state.json)")
        parser.add_argument("--limit", type=int, help="stop after N documents")
        parser.add_argument("--fresh", action="store_true",
                            help="ignore the stored cursor, re-read everything, and "
                                 "replace the output instead of appending to it")
        parser.add_argument("--json", action="store_true", help="machine-readable delta")

    web = isub.add_parser("web", help="crawl one or more seed URLs")
    _add_ingest_common(web)
    web.add_argument("seeds", nargs="+", help="seed URLs")
    web.add_argument("--max-pages", type=int, dest="max_pages")
    web.add_argument("--max-depth", type=int, dest="max_depth")
    web.add_argument("--max-bytes", type=int, dest="max_bytes")
    web.add_argument("--max-seconds", type=float, dest="max_seconds")
    web.set_defaults(func=cmd_ingest_web)

    gh = isub.add_parser("github", help="read a repository (OWNER/REPO)")
    _add_ingest_common(gh)
    gh.add_argument("repo", help="OWNER/REPO")
    gh.add_argument("--ref", help="branch, tag or sha (default: the repo default branch)")
    gh.add_argument("--include", action="append", help="only these path globs (repeatable)")
    gh.add_argument("--exclude", action="append", help="skip these path globs (repeatable)")
    gh.set_defaults(func=cmd_ingest_github)

    for name, help_text in [
        ("index", "ingest and index all configured sources"),
        ("query", "ask a question against the index"),
        ("eval", "run the retrieval evaluation harness"),
        ("demo", "end-to-end demo over the seed corpus"),
        ("loop", "run the retrieval freshness OODA loop"),
    ]:
        stub = sub.add_parser(name, help=f"{help_text} (not built yet)")
        stub.add_argument("args", nargs="*", help=argparse.SUPPRESS)
        stub.set_defaults(func=cmd_not_built)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except argparse.ArgumentTypeError as e:
        print(str(e), file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:  # a broken run must not print a traceback at 22:30
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        if "--debug" in (argv or sys.argv):
            raise
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
