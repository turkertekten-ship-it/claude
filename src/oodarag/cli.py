"""The single entry point: `python -m oodarag.cli` and the `ooda` console script.

Three constraints shape this module, and each one shows up as something that
looks odd out of context.

**Nothing here raises.** Every subcommand is also a Makefile target, and a
target that dies with a traceback tells its reader that Python was involved and
nothing else. `main` returns an exit code on every path - success, an empty
question, a missing index, an unimportable module, Ctrl-C - and a failure prints
what failed and what to try. The traceback is not discarded, it is gated behind
`OODARAG_LOG_LEVEL=debug`, because the person who wants a traceback is never the
person running `make demo` for the first time.

**Every `oodarag` import happens inside a function.** `get_logger` reads
`OODARAG_LOG_LEVEL` in its constructor and every stage binds its logger at
import time, so a level set after the first `import oodarag.pipeline` reaches
nothing that matters. Deferring the imports until the flags are parsed is what
makes `--quiet` work at all. It also keeps `--help` and a usage error from
paying for sqlite and the whole pipeline, and it means a checkout where one
module is missing degrades to one diagnosed subcommand rather than six broken
ones.

**`demo` never touches a real index.** It writes to `<root>/demo` and clears
that directory on each run. A demo has to produce the same output every time to
be worth watching, and the obvious way to get that - wipe the index first - is
unacceptable when the index might be the one the user spent an afternoon
building.

Exit codes follow the repository convention: 0 clean, 1 ran and found something
(an ingest with failures, an eval under its floor), 2 could not run. An
abstention is deliberately *not* a failure: it is the correct answer to a
question the corpus cannot support, and a `make query` that returned 1 for it
would teach its caller to stop reading the exit code.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
import traceback
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # runtime imports are deferred; see the module docstring
    from oodarag.models import Answer, Citation, IngestDelta, ScoredChunk
    from oodarag.pipeline import Pipeline

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

DEFAULT_ROOT = ".oodarag"
DEFAULT_CORPUS = "evals/corpus"
DEFAULT_GOLDENS = "evals/goldens.jsonl"
DEFAULT_K = 8

#: `(question, what it demonstrates)`. Three, not thirty: the demo has to stay
#: readable on one screen, and each of these puts a different part of the system
#: under load - an exact token, a paraphrase, and a question the corpus cannot
#: answer at all. Each label describes the *question*; what the retriever did
#: with it is what `--verbose` prints, and predicting that here would be
#: asserting a result rather than showing one.
DEMO_QUERIES: tuple[tuple[str, str], ...] = (
    (
        "What does the BM25 parameter k1 control?",
        "an exact identifier: `k1` is a token no embedder generalizes to",
    ),
    (
        "Why keep both a vector search and a keyword search around?",
        "a paraphrase: 'hybrid', 'BM25' and 'fusion' never appear in the question",
    ),
    (
        "What is our support SLA for enterprise customers?",
        "not in the corpus: the correct output is a refusal, not a plausible "
        "sentence with a real-looking citation on it",
    ),
)


# --------------------------------------------------------------------- output


@dataclass(slots=True)
class Console:
    """stdout carries results, stderr carries diagnosis, `--json` carries one object.

    This is an object rather than a scattering of `if args.json` because the
    rule it enforces is easy to break one `print` at a time: in JSON mode
    nothing but the payload may reach stdout, or the caller parsing it gets a
    decode error pointing at a progress message.
    """

    json_mode: bool = False
    quiet: bool = False

    def say(self, text: str = "") -> None:
        """Progress narration. The first thing `--quiet` and `--json` drop."""
        if not self.quiet and not self.json_mode:
            print(text, flush=True)

    def out(self, text: str = "") -> None:
        """A result the user asked for. Survives `--quiet`, suppressed by `--json`."""
        if not self.json_mode:
            print(text, flush=True)

    def warn(self, text: str) -> None:
        """A finding that does not stop the command. Always stderr, never stdout."""
        print(f"! {text}", file=sys.stderr, flush=True)

    def emit(self, payload: Mapping[str, Any]) -> None:
        """The machine-readable form. Exactly one of these per run, or none."""
        if self.json_mode:
            print(json.dumps(payload, indent=2, default=str, ensure_ascii=False), flush=True)

    def fail(self, what: str, hint: str = "", code: int = EXIT_ERROR) -> int:
        """Print a diagnosis and return the exit code, so callers can `return` it.

        Two lines, always in the same order: what failed, then what to try. A
        message that only says what failed leaves the reader with a search
        engine as their next step.
        """
        print(f"x {what}", file=sys.stderr, flush=True)
        if hint:
            print(f"  try: {hint}", file=sys.stderr, flush=True)
        self.emit({"ok": False, "error": what, "hint": hint})
        return code


# ---------------------------------------------------------------- entry point


def main(argv: list[str] | None = None) -> int:
    """Parse, dispatch, and convert every failure into an exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse exits by raising: 0 for `--help`, 2 for a usage error. Both
        # have already printed something useful, so this only unwraps the code.
        return int(e.code or 0)

    _apply_global_defaults(args)
    _configure_logging(args)
    console = Console(json_mode=args.json, quiet=args.quiet)

    if args.handler is None:
        parser.print_help(sys.stderr)
        return console.fail("no subcommand given", "ooda demo")

    try:
        return int(args.handler(args, console))
    except BrokenPipeError:
        # `ooda demo | head` closes stdout mid-write. That is the reader's
        # choice, not a failure, and writing a diagnosis to a closed pipe would
        # raise again inside the handler for the first raise. Redirect stdout to
        # devnull so the interpreter's own flush at exit stays quiet too.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return EXIT_OK
    except KeyboardInterrupt:
        return console.fail("interrupted", "nothing was left half-written; the index is a "
                                           "transaction per document")
    except Exception as e:  # the last line of defence - see the module docstring
        if os.environ.get("OODARAG_LOG_LEVEL", "").lower() == "debug":
            traceback.print_exc()
        return console.fail(
            f"{args.command} failed: {type(e).__name__}: {e}",
            "re-run with OODARAG_LOG_LEVEL=debug for the traceback",
        )


def _apply_global_defaults(args: argparse.Namespace) -> None:
    """Fill in the global flags nobody passed.

    They are declared `SUPPRESS` on a parser shared by every subcommand, so an
    unpassed flag is simply absent from the namespace. Defaulting here, once,
    is what makes `ooda --json query x` and `ooda query x --json` mean the same
    thing; see the comment in `build_parser` for why the obvious `set_defaults`
    does not.
    """
    for name, value in (("root", DEFAULT_ROOT), ("json", False), ("quiet", False)):
        if not hasattr(args, name):
            setattr(args, name, value)


def _configure_logging(args: argparse.Namespace) -> None:
    """Set the log level before anything binds a logger.

    An explicitly set `OODARAG_LOG_LEVEL` always wins, including over `--quiet`.
    The alternative - letting a flag silence a level the user deliberately
    exported - turns the one variable that exists for debugging into something
    that stops working under the exact command being debugged.
    """
    if os.environ.get("OODARAG_LOG_LEVEL"):
        return
    if args.quiet:
        os.environ["OODARAG_LOG_LEVEL"] = "error"


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root", metavar="PATH", default=argparse.SUPPRESS,
        help=f"where the index, embedding cache and cursors live (default: {DEFAULT_ROOT})",
    )
    common.add_argument(
        "--json", action="store_true", default=argparse.SUPPRESS,
        help="print one machine-readable object on stdout and nothing else",
    )
    common.add_argument(
        "-q", "--quiet", action="store_true", default=argparse.SUPPRESS,
        help="drop progress narration; results still print. OODARAG_LOG_LEVEL wins over this",
    )

    parser = argparse.ArgumentParser(
        prog="ooda",
        parents=[common],
        description="oodarag - a zero-dependency RAG pipeline with an OODA loop around it.",
        epilog=(
            "exit codes: 0 clean, 1 ran but found something, 2 could not run.\n"
            "an abstention is a correct answer and exits 0."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Two argparse traps, one after the other, and the global flags land in
    # exactly the wrong spot for both.
    #
    # A subparser parses into a *fresh* namespace and then copies every key that
    # namespace holds onto the main one. A flag declared on both parsers with an
    # ordinary default is therefore reset by the subparser, and `ooda --json
    # query x` prints prose. `default=argparse.SUPPRESS` on the shared actions
    # fixes it by keeping unspecified flags out of the sub-namespace entirely.
    #
    # Which rules out `set_defaults` for those same flags: `parents=` shares
    # action *objects* rather than copying them, and `set_defaults` overwrites
    # `action.default` on every action it matches. Setting `root` here would
    # replace the SUPPRESS on the action the subparsers hold, re-opening the
    # first trap. The real defaults are applied after parsing instead - see
    # `_apply_global_defaults`.
    parser.set_defaults(handler=None, command="")

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    demo = subparsers.add_parser(
        "demo", parents=[common], help="offline end-to-end run: ingest, index, query, eval",
        description="Ingest the seed corpus, index it, answer a few questions, and "
                    "score retrieval. Writes to <root>/demo and never touches a real index.",
    )
    demo.add_argument("--corpus", metavar="DIR", default=DEFAULT_CORPUS,
                      help=f"seed corpus directory (default: {DEFAULT_CORPUS})")
    demo.add_argument("--goldens", metavar="PATH", default=DEFAULT_GOLDENS,
                      help=f"golden set for the eval stage (default: {DEFAULT_GOLDENS})")
    demo.add_argument("-k", type=int, default=DEFAULT_K, metavar="N",
                      help=f"results per query (default: {DEFAULT_K})")
    demo.add_argument("--verbose", action="store_true",
                      help="show the per-citation score breakdown")
    demo.add_argument("--keep", action="store_true",
                      help="reuse the demo index instead of rebuilding it from scratch")
    demo.set_defaults(handler=cmd_demo)

    index = subparsers.add_parser(
        "index", parents=[common], help="ingest sources and (re)build the indexes",
        description="Ingest every named source and rebuild the lexical and dense "
                    "indexes. With no arguments this ingests the offline seed corpus.",
    )
    index.add_argument("--path", metavar="DIR", action="append", default=[],
                       help="a directory of text files to ingest; repeatable")
    index.add_argument("--url", metavar="URL", action="append", default=[],
                       help="a seed URL to crawl; repeatable. The only flag here that "
                            "touches the network")
    index.set_defaults(handler=cmd_index)

    query = subparsers.add_parser(
        "query", parents=[common], help="ask a question against the index",
        description="Retrieve, rerank, answer, and print numbered citations.",
    )
    # nargs="+" so both `ooda query "what is RAG?"` and `ooda query what is RAG`
    # work. `make query` with no Q= passes a single empty string, which arrives
    # here as a satisfied argument and is caught by the handler.
    query.add_argument("question", nargs="+", help="the question to ask")
    query.add_argument("-k", type=int, default=None, metavar="N",
                       help="results to retrieve (default: the pipeline's own k)")
    query.add_argument("--verbose", action="store_true",
                       help="add a one-line score breakdown under each citation")
    query.set_defaults(handler=cmd_query)

    evaluate_cmd = subparsers.add_parser(
        "eval", parents=[common], help="score retrieval against the golden set",
        description="Run every golden question through the pipeline and report "
                    "recall@k, MRR, nDCG@k, citation coverage and abstention rates.",
    )
    evaluate_cmd.add_argument("--goldens", metavar="PATH", default=DEFAULT_GOLDENS,
                              help=f"golden set, one JSON object per line (default: {DEFAULT_GOLDENS})")
    evaluate_cmd.add_argument("-k", type=int, default=DEFAULT_K, metavar="N",
                              help=f"cutoff for the ranked metrics (default: {DEFAULT_K})")
    evaluate_cmd.add_argument("--fail-under", type=float, default=None, metavar="FLOAT",
                              help="exit 1 when recall@k falls below this; for CI gates")
    evaluate_cmd.set_defaults(handler=cmd_eval)

    loop = subparsers.add_parser(
        "loop", parents=[common], help="run OODA cycles over the corpus",
        description="Observe the index, orient on staleness and quality, decide "
                    "what to do, and act. --dry-run stops before acting.",
    )
    loop.add_argument("--cycles", type=int, default=1, metavar="N",
                      help="how many cycles to run (default: 1)")
    loop.add_argument("--interval", type=float, default=0.0, metavar="SECONDS",
                      help="pause between cycles (default: 0)")
    loop.add_argument("--dry-run", action="store_true",
                      help="observe, orient and decide, but change nothing")
    loop.add_argument("--path", metavar="DIR", action="append", default=[],
                      help="a directory the loop may re-ingest; repeatable")
    loop.add_argument("--url", metavar="URL", action="append", default=[],
                      help="a seed URL the loop may re-crawl; repeatable")
    loop.add_argument("--goldens", metavar="PATH", default=DEFAULT_GOLDENS,
                      help=f"golden set the loop scores quality with (default: {DEFAULT_GOLDENS})")
    loop.set_defaults(handler=cmd_loop)

    stats = subparsers.add_parser(
        "stats", parents=[common], help="what is in the index",
        description="Counts, size on disk, and documents per source system.",
    )
    stats.set_defaults(handler=cmd_stats)

    return parser


# ------------------------------------------------------------------- commands


def cmd_demo(args: argparse.Namespace, console: Console) -> int:
    """Ingest, index, query and evaluate the seed corpus with the network unplugged."""
    from oodarag.evals.harness import evaluate, load_goldens
    from oodarag.ingest.files import FilesConnector

    corpus = Path(args.corpus)
    if not corpus.is_dir():
        return console.fail(
            f"the seed corpus is missing: {corpus}",
            "run this from the repository root, or pass --corpus DIR",
        )

    root = _demo_root(args.root)
    if not args.keep:
        _clear_demo_root(root, console)

    pipeline = _open_pipeline(root, console, require_index=False)
    if pipeline is None:
        return EXIT_ERROR

    payload: dict[str, Any] = {
        "command": "demo", "ok": True, "root": str(root), "corpus": str(corpus),
    }
    findings = 0
    try:
        console.say(f"oodarag demo - offline, from {corpus}")
        console.say()

        console.say("[1/4] ingest")
        # A fixed key rather than the path-derived default: the cursor is looked
        # up by it, and the demo should behave identically from any directory.
        deltas = pipeline.ingest([FilesConnector(corpus, key="files:demo-corpus")])
        payload["ingest"] = [d.as_dict() for d in deltas]
        for line in _render_deltas(deltas):
            console.say(line)
        findings += sum(d.failed for d in deltas)

        console.say()
        console.say("[2/4] index")
        pipeline.refresh_indexes()
        stats = pipeline.stats()
        payload["stats"] = stats
        console.say(f"  {stats['documents']} documents, {stats['chunks']} chunks, "
                    f"{stats['vectors']} vectors, {stats['embedder']}")
        if not stats["chunks"]:
            return console.fail(
                f"the demo indexed nothing from {corpus}",
                "check the corpus holds readable .md files, then re-run",
            )

        console.say()
        console.say("[3/4] query")
        console.say(f"  {stats['documents']} documents is small enough that both retrieval "
                    f"arms usually agree;")
        console.say("  --verbose prints the per-arm ranks, and it is their disagreement "
                    "that")
        console.say("  starts to matter on a real corpus.")
        answers: list[dict[str, Any]] = []
        for question, demonstrates in DEMO_QUERIES:
            console.say(f"  # {demonstrates}")
            console.out(f"> {question}")
            answer = pipeline.ask(question, args.k)
            _render_answer(console, answer, verbose=args.verbose)
            console.out()
            answers.append(answer.to_dict())
        payload["answers"] = answers

        console.say("[4/4] eval")
        goldens = load_goldens(args.goldens)
        if not goldens:
            # Not fatal: three quarters of the demo already ran and printed. It
            # is a finding, and the exit code says so.
            console.warn(f"no usable goldens at {args.goldens}; the eval stage was skipped")
            payload["eval"] = None
            findings += 1
        else:
            report = evaluate(pipeline, goldens, args.k)
            payload["eval"] = report.as_dict()
            console.out(report.render())
    finally:
        pipeline.close()

    payload["ok"] = findings == 0
    console.emit(payload)
    return EXIT_FINDINGS if findings else EXIT_OK


def cmd_index(args: argparse.Namespace, console: Console) -> int:
    """Ingest the named sources and rebuild both indexes."""
    connectors = _build_connectors(args.path, args.url, console)
    if connectors is None:
        return EXIT_ERROR

    pipeline = _open_pipeline(args.root, console, require_index=False)
    if pipeline is None:
        return EXIT_ERROR
    try:
        deltas = pipeline.ingest(connectors)
        pipeline.refresh_indexes()
        stats = pipeline.stats()
    finally:
        pipeline.close()

    for line in _render_deltas(deltas):
        console.out(line)
    console.out()
    console.out(f"  index: {stats['documents']} documents, {stats['chunks']} chunks, "
                f"{stats['vectors']} vectors at {stats['path']}")

    failed = sum(d.failed for d in deltas)
    for delta in deltas:
        for message in delta.errors[:3]:
            console.warn(f"{delta.source_key}: {message}")
    console.emit({
        "command": "index", "ok": failed == 0, "root": str(args.root),
        "sources": [d.as_dict() for d in deltas], "stats": stats,
    })
    return EXIT_FINDINGS if failed else EXIT_OK


def cmd_query(args: argparse.Namespace, console: Console) -> int:
    """Answer one question and print its citations."""
    question = " ".join(args.question).strip()
    if not question:
        return console.fail("no question given", 'make query Q="what is RAG?"')

    pipeline = _open_pipeline(args.root, console)
    if pipeline is None:
        return EXIT_ERROR
    try:
        chunks = int(pipeline.stats().get("chunks", 0))
        if not chunks:
            # Distinguished from a real abstention on purpose: an empty index
            # abstains on everything, and "I don't know" is a much more
            # convincing answer than it deserves to be here.
            return console.fail(
                f"the index at {args.root} holds no chunks",
                "`make index` to ingest the seed corpus, or `make demo` for a full run",
            )
        answer = pipeline.ask(question, args.k)
    finally:
        pipeline.close()

    _render_answer(console, answer, verbose=args.verbose)
    console.emit({
        "command": "query", "ok": True,
        **answer.to_dict(include_retrieved=args.verbose),
    })
    return EXIT_OK


def cmd_eval(args: argparse.Namespace, console: Console) -> int:
    """Score retrieval against the golden set."""
    from oodarag.evals.harness import evaluate, load_goldens

    goldens = load_goldens(args.goldens)
    if not goldens:
        return console.fail(
            f"no usable goldens in {args.goldens}",
            "the file is one JSON object per line; see evals/goldens.jsonl",
        )

    pipeline = _open_pipeline(args.root, console)
    if pipeline is None:
        return EXIT_ERROR
    try:
        if not int(pipeline.stats().get("chunks", 0)):
            # An eval over an empty index reports 0.000 across the board, which
            # reads exactly like a retrieval regression and is not one.
            return console.fail(
                f"the index at {args.root} holds no chunks, so every metric would be 0.000",
                "`make index` first, then re-run the eval",
            )
        report = evaluate(pipeline, goldens, args.k)
    finally:
        pipeline.close()

    console.out(report.render())

    passed = True
    if args.fail_under is not None and report.recall_at_k < args.fail_under:
        passed = False
        console.warn(
            f"recall@{args.k} {report.recall_at_k:.3f} is below --fail-under {args.fail_under:.3f}"
        )
    console.emit({
        "command": "eval", "ok": passed, "goldens": str(args.goldens), "k": args.k,
        **report.as_dict(),
    })
    return EXIT_OK if passed else EXIT_FINDINGS


def cmd_loop(args: argparse.Namespace, console: Console) -> int:
    """Run OODA cycles over the corpus."""
    try:
        from oodarag.ooda.loop import LoopPolicy, OodaLoop
    except ImportError as e:
        return console.fail(
            f"the OODA loop is not available in this build: {e}",
            "expected oodarag/ooda/loop.py per internal/CONTRACTS.md; "
            "the other subcommands do not depend on it",
        )

    connectors = _build_connectors(args.path, args.url, console)
    if connectors is None:
        return EXIT_ERROR

    pipeline = _open_pipeline(args.root, console, require_index=False)
    if pipeline is None:
        return EXIT_ERROR

    goldens = Path(args.goldens)
    if not goldens.is_file():
        # The loop scores quality from the eval report; without one it can still
        # observe staleness. Say which half is running rather than pretending.
        console.warn(f"no golden set at {goldens}; the loop will orient on staleness alone")

    try:
        loop = OodaLoop(
            pipeline, connectors,
            LoopPolicy(dry_run=args.dry_run),
            goldens if goldens.is_file() else None,
        )
        reports = loop.run(cycles=max(1, args.cycles), interval_s=max(0.0, args.interval))
    except Exception as e:
        return console.fail(
            f"the loop failed: {type(e).__name__}: {e}",
            "`ooda stats` and `ooda eval` show whether the pipeline underneath it is healthy",
        )
    finally:
        pipeline.close()

    for report in reports:
        console.out(report.render())
        console.out()

    errors = sum(len(r.observation.errors) for r in reports)
    console.emit({
        "command": "loop", "ok": errors == 0, "cycles": len(reports),
        "dry_run": args.dry_run, "reports": [r.as_dict() for r in reports],
    })
    return EXIT_FINDINGS if errors else EXIT_OK


def cmd_stats(args: argparse.Namespace, console: Console) -> int:
    """Report what is in the index. Reports; does not judge."""
    pipeline = _open_pipeline(args.root, console)
    if pipeline is None:
        return EXIT_ERROR
    try:
        stats = pipeline.stats()
    finally:
        pipeline.close()

    for line in _render_stats(stats):
        console.out(line)
    console.emit({"command": "stats", "ok": True, **stats})
    return EXIT_OK


# -------------------------------------------------------------------- helpers


def _open_pipeline(root: str | Path, console: Console, *, require_index: bool = True) -> Pipeline | None:
    """Open a pipeline at `root`, or diagnose why not and return None.

    `require_index` guards the read-only commands. Constructing a `Pipeline`
    creates its directory and an empty sqlite file, so without this check
    `ooda stats` on a fresh checkout would create the very index it then
    reported as empty - a read-only command with a side effect, answering a
    question the user did not ask.
    """
    from oodarag.pipeline import Pipeline, PipelineConfig

    config = PipelineConfig(root=Path(root))
    if require_index and not config.db_path.exists():
        console.fail(
            f"no index at {config.db_path}",
            "`make index` builds one from the seed corpus, `make demo` runs the whole thing",
        )
        return None
    try:
        return Pipeline(config)
    except Exception as e:
        console.fail(
            f"could not open the index at {config.db_path}: {type(e).__name__}: {e}",
            "an index written by a newer oodarag is refused, not migrated: "
            "delete the directory or point --root somewhere else",
        )
        return None


def _build_connectors(paths: Sequence[str], urls: Sequence[str], console: Console) -> list[Any] | None:
    """Turn `--path` and `--url` into connectors, or diagnose and return None.

    With neither flag this falls back to the seed corpus. That default is what
    makes `make index` meaningful on a fresh checkout with nothing configured,
    and it is the only source in the package that needs no network.
    """
    from oodarag.ingest.files import FilesConnector

    directories = [Path(p) for p in paths] or ([Path(DEFAULT_CORPUS)] if not urls else [])
    connectors: list[Any] = []
    for directory in directories:
        if not directory.is_dir():
            console.fail(
                f"not a directory: {directory}",
                "pass --path DIR, or run from the repository root so "
                f"{DEFAULT_CORPUS} resolves",
            )
            return None
        connectors.append(FilesConnector(directory))

    if urls:
        # Imported only on this branch: it pulls in the crawler and the HTTP
        # client, and an offline `make index` should never load either.
        from oodarag.ingest.web import WebConnector

        connectors.append(WebConnector(list(urls)))

    if not connectors:
        console.fail("no sources to ingest", "pass --path DIR or --url URL")
        return None
    return connectors


def _demo_root(root: str | Path) -> Path:
    """`<root>/demo` - a scratch index the demo is free to delete."""
    return Path(root) / "demo"


def _clear_demo_root(path: Path, console: Console) -> None:
    """Delete the demo index so the run is reproducible from empty.

    Guarded on the directory name this module chose rather than on the value of
    `--root`, which is user input: a demo that recursively deletes whatever it
    was pointed at is a footgun with a flag on it.
    """
    if path.name != "demo" or not path.is_dir():
        return
    try:
        shutil.rmtree(path)
    except OSError as e:
        console.warn(f"could not clear {path}: {e}; reusing what is there")


# ------------------------------------------------------------------ rendering


def _render_answer(console: Console, answer: Answer, *, verbose: bool = False) -> None:
    """Answer, then numbered citations, then (optionally) the arithmetic.

    The answer body is rewrapped for the terminal. Extractive sentences carry
    the line breaks of the markdown they were lifted from, which arrive here as
    ragged half-width lines that read as though the answer were truncated.
    Rewrapping changes whitespace only, and `--json` still carries the text
    exactly as the generator verified it.
    """
    console.out(_wrap(answer.text) if answer.text else "(no answer)")

    if answer.abstained:
        reason = answer.metrics.get("reason", "below the confidence floor")
        console.out()
        console.out(f"  abstained: {reason} (confidence {answer.confidence:.3f})")
        return  # citations are empty by contract on this path

    if not answer.citations:
        console.out()
        console.out("  no citations survived verification")
        return

    console.out()
    console.out(f"  sources ({len(answer.citations)}, confidence {answer.confidence:.3f})")
    by_chunk = {hit.chunk.chunk_id: hit for hit in answer.retrieved}
    for citation in answer.citations:
        console.out(f"  [{citation.marker}] {citation.title}")
        console.out(f"      {citation.uri}")
        if verbose:
            console.out(f"      {_score_line(citation, by_chunk.get(citation.chunk_id))}")


def _score_line(citation: Citation, hit: ScoredChunk | None) -> str:
    """One line of arithmetic per citation: which arm found it, and what happened after.

    An arm that never returned the chunk prints `-`, not a zero. That is the
    whole value of the line: a hit both arms agreed on and a hit only BM25 ever
    saw are different kinds of result, and the fused score alone cannot tell
    them apart.
    """
    if hit is None:
        return f"score {citation.score:.4f} (no breakdown: not in the retrieved set)"

    components = hit.components
    parts = [_arm(components, "bm25"), _arm(components, "dense")]
    for key, label in (("rrf", "rrf"), ("mmr", "mmr"), ("authority", "auth"), ("final", "final")):
        if key in components:
            parts.append(f"{label} {components[key]:.4f}")
    return "  ".join(parts)


def _arm(components: Mapping[str, float], name: str) -> str:
    """`bm25 #3 (7.412)`, or `bm25 -` when that arm never returned the chunk."""
    rank = components.get(f"{name}_rank", 0.0)
    if not rank:  # MISSING_RANK is 0.0; real ranks are 1-based
        return f"{name} -"
    return f"{name} #{int(rank)} ({components.get(name, 0.0):.3f})"


def _render_deltas(deltas: Sequence[IngestDelta]) -> list[str]:
    """One aligned row per connector, whatever happened to it."""
    if not deltas:
        return ["  (no sources)"]
    width = max(len(d.source_key) for d in deltas)
    width = min(max(width, 8), 44)
    lines = [
        f"  {'source':<{width}}  {'new':>5} {'chg':>5} {'same':>5} {'fail':>5} {'secs':>7}",
    ]
    for delta in deltas:
        lines.append(
            f"  {_clip(delta.source_key, width):<{width}}  "
            f"{delta.new:>5} {delta.changed:>5} {delta.unchanged:>5} "
            f"{delta.failed:>5} {delta.duration_s:>7.2f}"
        )
    return lines


def _render_stats(stats: Mapping[str, Any]) -> list[str]:
    """What is on disk.

    The in-memory index counts that `Pipeline.stats()` also returns are left out
    here and kept in the JSON payload: they describe a process that started two
    hundred milliseconds ago and has not queried anything, so `indexes_built
    false` is always true and always means nothing.
    """
    lines = [f"index: {stats.get('path', '?')}"]
    for label, key in (
        ("documents", "documents"),
        ("chunks", "chunks"),
        ("vectors", "vectors"),
        ("schema", "schema_version"),
    ):
        lines.append(f"  {label:<12}{stats.get(key, 0):>10}")
    lines.append(f"  {'embedder':<12}{stats.get('embedder', '?'):>10} "
                 f"(dim {stats.get('embed_dim', 0)})")
    lines.append(f"  {'on disk':<12}{_bytes(int(stats.get('bytes', 0))):>10}")

    sources = stats.get("sources") or {}
    lines.append(f"  {'sources':<12}{len(sources):>10}")
    for name, count in sorted(sources.items()):
        lines.append(f"    {_clip(str(name), 24):<24}{count:>6}")
    if not stats.get("documents"):
        lines.append("  the index is empty - `make index` fills it from the seed corpus")
    return lines


def _wrap(text: str, width: int = 88) -> str:
    """Rewrap a block for the terminal, preserving paragraph breaks."""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    return "\n\n".join(textwrap.fill(" ".join(p.split()), width=width) for p in paragraphs)


def _bytes(count: int) -> str:
    size = float(count)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _clip(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


if __name__ == "__main__":  # `python -m oodarag.cli`
    sys.exit(main())
