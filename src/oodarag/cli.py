"""Command line entry point.

Exit codes follow the house rule so the commands compose in a shell and in CI:

    0  clean — the thing ran and found nothing wrong
    1  findings — it ran and something is wrong (failed eval, lint errors,
       an unreachable source, an abstained answer)
    2  could not run — bad arguments, a missing corpus, an unreadable file

The distinction between 1 and 2 is what lets a scheduled job treat "retrieval
got worse" differently from "the job is broken", which are otherwise identical
from the outside.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from oodarag.chunk import ChunkConfig
from oodarag.embed import HashingEmbedder
from oodarag.evaluate import evaluate, load_goldens
from oodarag.ingest.base import Connector, JsonStateStore
from oodarag.ingest.files import FileConnector
from oodarag.ingest.github import GitHubConnector
from oodarag.ingest.skills import SkillConnector, discover_skills, lint_skill
from oodarag.ingest.web import WebConnector
from oodarag.ingest.youtube import YouTubeConnector
from oodarag.loop import OodaLoop
from oodarag.net.reachability import Barrier, probe_all, render_json, render_table
from oodarag.pipeline import Pipeline
from oodarag.retrieve import RetrievalConfig
from oodarag.store import Store

EXIT_OK, EXIT_FINDINGS, EXIT_CANNOT_RUN = 0, 1, 2

DEFAULT_DB = ".oodarag/corpus.db"
DEFAULT_STATE = ".oodarag/state.json"
DEFAULT_GOLDENS = "evals/goldens.jsonl"

#: Hosts worth knowing the status of before a run plans any fetching. Each is
#: a real endpoint rather than a bare origin, because an origin that answers
#: says nothing about whether the path a connector needs is reachable.
DEFAULT_PROBES = [
    "https://api.github.com/rate_limit",
    "https://raw.githubusercontent.com/anthropics/skills/main/README.md",
    "https://pypi.org/simple/",
    "https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ",
    "https://www.youtube.com/robots.txt",
]


def _pipeline(args: argparse.Namespace) -> Pipeline:
    store = Store(args.db)
    return Pipeline(
        store,
        embedder=HashingEmbedder(dim=args.dim),
        chunk_config=ChunkConfig(target_tokens=args.chunk_tokens),
        retrieval_config=RetrievalConfig(top_k=args.k),
    )


# --------------------------------------------------------------- subcommands


def build_connectors(args: argparse.Namespace) -> tuple[list[Connector], list[str]]:
    """Assemble the sources named on the command line.

    Every connector the package ships was previously unreachable from here
    except the file one, which made the rest built-but-uninvocable — the same
    class of defect as a console script pointing at a module that does not
    exist. Each source is independent: one that cannot be configured is
    reported and skipped rather than aborting the others, because a partial
    index is worth more than none.
    """
    connectors: list[Connector] = []
    notes: list[str] = []

    for root in args.paths or ([] if (args.youtube or args.skills or args.github
                                      or args.web) else ["."]):
        connectors.append(FileConnector(root))

    if args.skills is not None:
        roots = args.skills or [".claude/skills", str(Path.home() / ".claude/skills")]
        connectors.append(SkillConnector([r for r in roots if Path(r).exists()]))

    if args.youtube:
        for manifest in args.youtube:
            if not Path(manifest).exists():
                notes.append(f"youtube: no manifest at {manifest}")
                continue
            # A manifest needs neither a key nor egress; the API is used only
            # to enrich it when one happens to be configured.
            connectors.append(YouTubeConnector(manifest=manifest))

    for slug in args.github or []:
        owner, _, repo = slug.partition("/")
        if not owner or not repo:
            notes.append(f"github: expected owner/repo, got {slug!r}")
            continue
        connectors.append(GitHubConnector(owner=owner, repo=repo))

    if args.web:
        connectors.append(WebConnector(list(args.web)))

    return connectors, notes


def cmd_index(args: argparse.Namespace) -> int:
    pipe = _pipeline(args)
    connectors, notes = build_connectors(args)
    for note in notes:
        print(f"  skipped — {note}", file=sys.stderr)
    if not connectors:
        print("no sources selected; pass paths or --skills/--youtube/--github/--web",
              file=sys.stderr)
        return EXIT_CANNOT_RUN
    report = pipe.ingest(connectors, state=JsonStateStore(args.state))
    print(report.render())
    return EXIT_OK if (report.ok and not notes) else EXIT_FINDINGS


def cmd_query(args: argparse.Namespace) -> int:
    pipe = _pipeline(args)
    if pipe.stats()["chunks"] == 0:
        print(f"corpus at {args.db} is empty — run `index` first", file=sys.stderr)
        return EXIT_CANNOT_RUN

    answer = pipe.query(args.question, args.k)
    if args.json:
        print(answer.to_json(include_retrieved=args.verbose))
    else:
        print(answer.text)
        if args.verbose:
            print("\n--- retrieval ---")
            for hit in answer.retrieved:
                parts = " ".join(f"{k}={v:.4f}" for k, v in sorted(hit.components.items()))
                print(f"  {hit.score:.5f}  {hit.citation_title[:44]:<44} {parts}")
    # An abstention is a finding: the corpus could not answer.
    return EXIT_FINDINGS if answer.abstained else EXIT_OK


def cmd_eval(args: argparse.Namespace) -> int:
    pipe = _pipeline(args)
    cases, errors = load_goldens(args.goldens)
    if not cases and errors:
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return EXIT_CANNOT_RUN
    report = evaluate(pipe.retriever, cases, k=args.k,
                      generator=pipe.generator, load_errors=errors)
    print(report.render())
    return report.exit_code


def cmd_loop(args: argparse.Namespace) -> int:
    pipe = _pipeline(args)
    connectors, notes = build_connectors(args)
    for note in notes:
        print(f"  skipped — {note}", file=sys.stderr)
    loop = OodaLoop(pipe, connectors, state=JsonStateStore(args.state))
    reports = loop.run(args.cycles)
    for i, report in enumerate(reports, start=1):
        print(f"===== cycle {i}/{len(reports)} =====")
        print(report.render() if not args.json else json.dumps(report.as_dict(), indent=2))
        print()
    return EXIT_OK


def cmd_reachability(args: argparse.Namespace) -> int:
    urls = args.urls or DEFAULT_PROBES
    results = probe_all(urls, timeout=args.timeout)
    print(render_json(results) if args.json else render_table(results))
    # Being blocked is a finding about the environment, not a broken command.
    blocked = [r for r in results if r.barrier is Barrier.EGRESS_BLOCKED]
    if blocked and not args.json:
        print(f"\n{len(blocked)} of {len(results)} host(s) refused at CONNECT. "
              "These cannot be reached by any code path from here.")
    return EXIT_FINDINGS if blocked else EXIT_OK


def cmd_skills(args: argparse.Namespace) -> int:
    roots = args.paths or [".claude/skills", str(Path.home() / ".claude/skills")]
    skills = discover_skills(roots)
    if not skills:
        print(f"no SKILL.md found under: {', '.join(str(r) for r in roots)}")
        return EXIT_OK

    total_errors = 0
    for skill in sorted(skills, key=lambda s: (s.scope, s.name)):
        findings = lint_skill(skill)
        errors = [f for f in findings if f.severity == "error"]
        total_errors += len(errors)
        status = "ERROR" if errors else ("warn" if findings else "ok")
        print(f"[{status:>5}] {skill.command:<28} {skill.scope:<8} "
              f"{skill.body_lines:>4} lines  {skill.name}")
        for finding in findings:
            print(f"          {finding}")
    print(f"\n{len(skills)} skill(s), {total_errors} error(s)")
    return EXIT_FINDINGS if total_errors else EXIT_OK


def cmd_stats(args: argparse.Namespace) -> int:
    print(json.dumps(_pipeline(args).stats(), indent=2))
    return EXIT_OK


def cmd_demo(args: argparse.Namespace) -> int:
    """Ingest this repository, then query and evaluate it. No network needed."""
    args.db = args.db or DEFAULT_DB
    pipe = _pipeline(args)

    # The demo corpus is the source and the prose, not the whole repository:
    # `tests/` and `provenance/raw/` contain the golden questions and captured
    # reports from previous runs, so indexing them would score the evaluation
    # against its own answer key.
    roots = args.paths or [r for r in ("src", "docs", "README.md", "CLAUDE.md")
                           if Path(r).exists()]
    print("== 1. ingest ==")
    report = pipe.ingest([FileConnector(r) for r in roots],
                         state=JsonStateStore(args.state))
    print(report.render())

    print("\n== 2. index ==")
    print(json.dumps(pipe.stats(), indent=2))

    print("\n== 3. query ==")
    for question in [
        "how does the pipeline decide a document has changed?",
        "why is reciprocal rank fusion used instead of adding the scores?",
        "what happens when a source is blocked by the network?",
    ]:
        answer = pipe.query(question, args.k)
        verdict = "ABSTAINED" if answer.abstained else f"confidence {answer.confidence:.3f}"
        print(f"\nQ: {question}\n[{verdict}]")
        print(answer.text[:600])

    print("\n== 4. eval ==")
    cases, errors = load_goldens(args.goldens)
    if cases:
        result = evaluate(pipe.retriever, cases, k=args.k, generator=pipe.generator,
                          load_errors=errors)
        print(result.render())
        return result.exit_code
    print(f"no golden cases at {args.goldens}; skipping evaluation")
    return EXIT_OK


# -------------------------------------------------------------------- parser


def _add_source_args(p: argparse.ArgumentParser) -> None:
    """Source selection, shared by the commands that ingest."""
    p.add_argument("paths", nargs="*", help="local directories or files to ingest")
    p.add_argument("--skills", nargs="*", metavar="DIR",
                   help="index SKILL.md files; with no value, the usual skill locations")
    p.add_argument("--youtube", nargs="+", metavar="MANIFEST", default=[],
                   help="index videos from a manifest; needs no API key and no egress")
    p.add_argument("--github", nargs="+", metavar="OWNER/REPO", default=[],
                   help="index a repository through the GitHub API")
    p.add_argument("--web", nargs="+", metavar="URL", default=[],
                   help="crawl from these seed URLs, within the configured budgets")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ooda",
        description="An OODA-driven retrieval pipeline with zero required dependencies.",
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="corpus database path")
    parser.add_argument("--state", default=DEFAULT_STATE, help="connector cursor file")
    parser.add_argument("--dim", type=int, default=512, help="embedding dimensions")
    parser.add_argument("--chunk-tokens", type=int, default=320, help="target chunk size")
    parser.add_argument("-k", type=int, default=8, help="results to retrieve")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("index", help="ingest and index the selected sources")
    _add_source_args(p)
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("query", help="ask the corpus a question")
    p.add_argument("question")
    p.set_defaults(func=cmd_query)

    p = sub.add_parser("eval", help="score retrieval against golden cases")
    p.add_argument("--goldens", default=DEFAULT_GOLDENS)
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("loop", help="run OODA cycles over the selected sources")
    _add_source_args(p)
    p.add_argument("--cycles", type=int, default=1)
    p.set_defaults(func=cmd_loop)

    p = sub.add_parser("reachability", help="report what this host can fetch, and why not")
    p.add_argument("urls", nargs="*")
    p.add_argument("--timeout", type=float, default=12.0)
    p.set_defaults(func=cmd_reachability)

    p = sub.add_parser("skills", help="discover and lint SKILL.md files")
    p.add_argument("paths", nargs="*")
    p.set_defaults(func=cmd_skills)

    p = sub.add_parser("stats", help="what the corpus holds")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("demo", help="end to end, offline: ingest, index, query, eval")
    p.add_argument("paths", nargs="*")
    p.add_argument("--goldens", default=DEFAULT_GOLDENS)
    p.set_defaults(func=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_CANNOT_RUN
    except FileNotFoundError as e:
        print(f"{e}", file=sys.stderr)
        return EXIT_CANNOT_RUN
    except BrokenPipeError:
        return EXIT_OK  # piped into `head`; not an error


if __name__ == "__main__":
    raise SystemExit(main())
