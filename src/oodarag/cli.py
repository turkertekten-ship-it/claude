"""Command line interface.

    ooda preflight   what can this environment actually reach
    ooda index       ingest configured sources and build the index
    ooda query       ask a question
    ooda eval        run the golden set and report retrieval quality
    ooda loop        run OODA cycles
    ooda status      index and loop state
    ooda journal     what the loop decided, and why
    ooda demo        the whole pipeline end to end on this repository
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from oodarag import __version__
from oodarag.config import Config, SourceConfig


def _build(config: Config):
    from oodarag.embedding import get_embedder
    from oodarag.pipeline import IndexPipeline
    from oodarag.store.sqlite_store import SqliteStore

    store = SqliteStore(config.index_path)
    embedder = get_embedder(config.embedder, **config.embedder_options)
    # Cursors live in the index, not a file beside it. A separate state file can
    # be deleted, restored or copied independently of the data it describes, and
    # when the two diverge every document it lists is reported "unchanged" and
    # never re-added - a silently partial index. IndexPipeline defaults to the
    # SQLite-backed store; a JsonStateStore is still available to library users.
    return store, IndexPipeline(store, embedder)


def _generator(config: Config, pipeline):
    from oodarag.generate.answer import AnswerConfig, AnswerGenerator
    from oodarag.retrieve.hybrid import HybridRetriever

    retriever = HybridRetriever(pipeline.store, pipeline.embedder)
    return AnswerGenerator(retriever, AnswerConfig(generator=config.generator,
                                                   top_k=config.top_k))


def cmd_preflight(args, config: Config) -> int:
    from oodarag.access.probe import probe_all

    report = probe_all(repo_slugs=tuple(args.repo or config.repo_slugs))
    if args.json:
        print(report.to_json())
    else:
        print(report.to_markdown())
    if args.out:
        Path(args.out).write_text(report.to_markdown(), "utf-8")
        print(f"written: {args.out}", file=sys.stderr)
    blocked = [r for r in report.results if not r.usable]
    return 1 if (blocked and args.strict) else 0


def cmd_index(args, config: Config) -> int:
    store, pipeline = _build(config)
    connectors = config.build_connectors()
    if not connectors:
        print("No sources configured. Add [[source]] entries to oodarag.toml, "
              "or run `ooda demo` to index this repository.", file=sys.stderr)
        return 2
    report = pipeline.run(connectors, refit=args.refit)
    print(json.dumps(report.as_dict(), indent=2))
    store.close()
    return 0 if report.ok else 1


def cmd_query(args, config: Config) -> int:
    store, pipeline = _build(config)
    generator = _generator(config, pipeline)
    filters = json.loads(args.filters) if args.filters else None
    answer = generator.answer(" ".join(args.question), filters=filters, top_k=args.k)
    if args.json:
        print(answer.to_json(include_retrieved=args.verbose))
    else:
        print(f"\n{answer.text}\n")
        if answer.citations:
            print("Sources:")
            for citation in answer.citations:
                print(f"  [{citation.marker}] {citation.title}\n      {citation.uri}"
                  + (f"\n      {citation.span}" if citation.span else ""))
        print(f"\nconfidence={answer.confidence}  generator={answer.generator}"
              f"  coverage={answer.metrics.get('citation_coverage')}"
              f"  {answer.metrics.get('total_ms')}ms")
    store.close()
    return 1 if answer.abstained else 0


def cmd_eval(args, config: Config) -> int:
    from oodarag.eval.harness import EvalHarness, load_goldens

    store, pipeline = _build(config)
    goldens = load_goldens(args.goldens or config.goldens_path)
    report = EvalHarness(_generator(config, pipeline), k=args.k,
                         exclude_sources=tuple(args.exclude_source or ())).run(goldens)
    print(report.to_json() if args.json else report.to_markdown())
    if args.out:
        Path(args.out).write_text(report.to_markdown(), "utf-8")
    store.close()
    # A regression gate CI can fail on.
    return 0 if report.pass_rate >= args.min_pass_rate else 1


def cmd_loop(args, config: Config) -> int:
    from oodarag.ooda.loop import LoopConfig, OodaLoop

    store, pipeline = _build(config)
    connectors = config.build_connectors()
    loop = OodaLoop(
        pipeline, connectors,
        LoopConfig(goldens_path=config.goldens_path, probe_access=not args.no_probe,
                   repo_slugs=tuple(config.repo_slugs), dry_run=args.dry_run),
        generator=_generator(config, pipeline),
    )
    for report in loop.run(cycles=args.cycles, interval_s=args.interval):
        print(json.dumps(report.as_dict(), indent=2) if args.json else report.summary())
        if not args.json:
            for outcome in report.outcomes:
                print(f"    {outcome['kind']:<18} {outcome['status']:<10} {outcome['reason'][:70]}")
    store.close()
    return 0


def cmd_status(args, config: Config) -> int:
    store, pipeline = _build(config)
    status = {
        "version": __version__,
        "index": store.stats(),
        "embedder": pipeline.embedder.fingerprint,
        "index_fingerprint": store.get_meta("index_fingerprint"),
        "cycles_run": store.get_meta("ooda_cycle", 0),
        "last_eval": store.get_meta("last_eval"),
        "source_health": store.get_meta("source_health", {}),
    }
    print(json.dumps(status, indent=2, default=str))
    store.close()
    return 0


def cmd_journal(args, config: Config) -> int:
    store, _ = _build(config)
    entries = store.read_journal(limit=args.limit, cycle=args.cycle)
    if args.json:
        print(json.dumps(entries, indent=2, default=str))
    else:
        for entry in entries:
            print(f"cycle {entry['cycle']:>3}  {entry['phase']:<8}  "
                  f"{_journal_line(entry)}")
    store.close()
    return 0


def _journal_line(entry: dict) -> str:
    phase = entry["phase"]
    if phase == "decide":
        return ", ".join(f"{a['kind']}({a['priority']})" for a in entry.get("actions", []))
    if phase == "act":
        return ", ".join(f"{o['kind']}={o['status']}" for o in entry.get("outcomes", []))
    if phase == "observe":
        return (f"ingested={entry.get('documents_ingested')} "
                f"chunks={entry.get('chunks_written')} errors={len(entry.get('errors', []))}")
    if phase == "orient":
        return (f"docs={entry.get('documents')} coverage={entry.get('embedding_coverage')} "
                f"growth={entry.get('corpus_growth')}")
    return f"duration={entry.get('duration_s')}s"


def cmd_demo(args, config: Config) -> int:
    """Index this repository and answer questions about it, end to end."""
    config.sources = [SourceConfig("filesystem", {
        "root": ".",
        "patterns": ["src/**/*.py", "tests/**/*.py", "docs/**/*.md",
                     "internal/**/*.md", "*.md"],
    })]
    print("== index ==", file=sys.stderr)
    if cmd_index(argparse.Namespace(refit=True), config) != 0:
        return 1
    print("\n== eval ==", file=sys.stderr)
    cmd_eval(argparse.Namespace(goldens=None, k=8, json=False, out=None,
                                min_pass_rate=0.0, exclude_source=["chat"]), config)
    print("\n== query ==", file=sys.stderr)
    for question in ("Why is reciprocal rank fusion used instead of a weighted sum?",
                     "How does the crawler avoid indexing duplicate pages?"):
        cmd_query(argparse.Namespace(question=[question], json=False, verbose=False,
                                     k=6, filters=None), config)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ooda", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", help="path to oodarag.toml")
    parser.add_argument("--version", action="version", version=f"oodarag {__version__}")

    # Accepted on either side of the subcommand. `ooda index --config x.toml`
    # is the form everyone types first, and argparse otherwise rejects it with
    # "unrecognized arguments" - which reads like the file is wrong rather than
    # the word order.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", dest="config_after", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("preflight", parents=[common], help="probe what this environment can reach")
    p.add_argument("--repo", action="append", help="owner/repo to probe (repeatable)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out", help="also write the markdown report here")
    p.add_argument("--strict", action="store_true", help="exit non-zero if anything is blocked")
    p.set_defaults(func=cmd_preflight)

    p = subparsers.add_parser("index", parents=[common], help="ingest sources and build the index")
    p.add_argument("--refit", action="store_true", help="refit corpus statistics")
    p.set_defaults(func=cmd_index)

    p = subparsers.add_parser("query", parents=[common], help="ask a question")
    p.add_argument("question", nargs="+")
    p.add_argument("-k", type=int, default=8)
    p.add_argument("--filters", help="JSON metadata filter")
    p.add_argument("--json", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true", help="include retrieved chunks")
    p.set_defaults(func=cmd_query)

    p = subparsers.add_parser("eval", parents=[common], help="run the golden set")
    p.add_argument("--goldens")
    p.add_argument("-k", type=int, default=8)
    p.add_argument("--json", action="store_true")
    p.add_argument("--out")
    p.add_argument("--min-pass-rate", type=float, default=0.8,
                   dest="min_pass_rate", help="exit non-zero below this (CI gate)")
    p.add_argument("--exclude-source", action="append", dest="exclude_source",
                   help="hold a source system out of the eval index (repeatable). "
                        "Use for sources that record the evaluation itself, e.g. chat.")
    p.set_defaults(func=cmd_eval)

    p = subparsers.add_parser("loop", parents=[common], help="run OODA cycles")
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--interval", type=float, default=0.0, help="seconds between cycles")
    p.add_argument("--dry-run", action="store_true", help="decide but do not act")
    p.add_argument("--no-probe", action="store_true", help="skip the access probe")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_loop)

    p = subparsers.add_parser("status", parents=[common], help="index and loop state")
    p.set_defaults(func=cmd_status)

    p = subparsers.add_parser("journal", parents=[common], help="what the loop decided, and why")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--cycle", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_journal)

    p = subparsers.add_parser("demo", parents=[common], help="run the whole pipeline on this repository")
    p.set_defaults(func=cmd_demo)

    args = parser.parse_args(argv)
    config = Config.load(getattr(args, "config_after", None) or args.config)
    return args.func(args, config)


if __name__ == "__main__":
    sys.exit(main())
