"""The command line. What he actually types on a Monday.

Five commands, matching the Makefile: ``demo``, ``index``, ``query``, ``loop``
and ``eval``, plus three that exist because this system's honesty is a feature
worth being able to inspect: ``rules`` prints every decision rule and why its
threshold sits where it does, ``provenance`` prints which configured facts
nobody has confirmed, and ``obligations`` prints the calendar with the
unverified ones marked.

``demo`` runs with no network and no API key, over this repository's own
research documents as its corpus. That is not a toy: it is the honest
demonstration available here, because the firm's real filings could not be
reached [src:EGRESS-BLOCKED-WAM-KAP-2026-08-27], and a demo seeded with invented
fund data would be exactly the fabrication this codebase exists to prevent.

Every command exits 0 clean, 1 findings, 2 could not run — the house rule — and
prints a useful error rather than a traceback.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from oodarag.config import WAM, FirmProfile, load
from oodarag.domain.money import Money
from oodarag.models import Document, RawDocument
from oodarag.util.logging import get_logger

log = get_logger("cli")

EXIT_OK, EXIT_FINDINGS, EXIT_ERROR = 0, 1, 2
DEFAULT_HOME = Path(".oodarag")


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------

def _local_corpus(root: Path) -> list[RawDocument]:
    """This repository's own documents. Real text, no network, no invention."""
    from oodarag.redact import Redactor
    redactor = Redactor()
    docs: list[RawDocument] = []
    for pattern in ("docs/**/*.md", "CLAUDE.md", "README.md",
                    "provenance/*.md", "config/*.toml"):
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            try:
                text = path.read_text("utf-8")
            except (OSError, UnicodeDecodeError) as e:
                log.warn("unreadable file skipped", path=str(path), err=str(e)[:120])
                continue
            if not text.strip():
                continue
            rel = str(path.relative_to(root))
            # Redaction happens here, at the boundary, not at display: anything
            # indexed is on disk, and a leak that reaches disk has happened.
            text = redactor(text)
            docs.append(RawDocument(
                source_system="repo", external_id=rel, uri=f"file://{rel}",
                title=path.stem.replace("-", " "), text=text,
                metadata={"path": rel, "lang": "en"},
            ))
    return docs


def _build_index(root: Path, home: Path, *, quiet: bool = False) -> tuple:
    from oodarag.chunk.splitter import chunk_document
    from oodarag.embed.provider import get_embedder
    from oodarag.index.store import Store
    from oodarag.retrieve.hybrid import HybridRetriever

    raw = _local_corpus(root)
    if not raw:
        raise RuntimeError(f"no documents found under {root}")

    store = Store(home / "index.db")
    embedder = get_embedder("auto")
    n_chunks = 0
    for r in raw:
        doc = Document.from_raw(r, r.text, dict(r.metadata))
        store.upsert_documents([doc])
        chunks = chunk_document(doc)
        vectors = None
        try:
            vecs = embedder.embed([c.indexed_text for c in chunks])
            vectors = {c.chunk_id: v for c, v in zip(chunks, vecs, strict=True)}
        except Exception as e:  # degraded, never fatal
            log.warn("embedding failed; lexical arm only", err=str(e)[:160])
        store.upsert_chunks(chunks, vectors)
        n_chunks += len(chunks)

    retriever = HybridRetriever.from_store(store, embedder=embedder)
    if not quiet:
        stats = store.stats()
        print(f"  indexed {len(raw)} documents, {n_chunks} chunks -> {home / 'index.db'}")
        blind = stats.get("chunks_without_vectors", 0)
        if blind:
            print(f"  note: {blind} chunks have no vector; the dense arm is blind to them")
    return store, retriever


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------

def _demo_state(profile: FirmProfile, today: date):
    """A worked example over seeded data. Never a reading of the real book.

    The NAV points below are invented, and say so. Fund sizes and unit values
    were not obtainable for this firm (unknown AIR-1), so the alternative to
    clearly-labelled fixtures is either no demonstration at all or invented
    numbers presented as real. The first is useless and the second is the
    failure this repository is built to prevent.
    """
    from oodarag.domain.inflation import PriceIndex
    from oodarag.domain.obligations import ObligationCalendar
    from oodarag.domain.valuation import NavPoint
    from oodarag.ingest.marketdata import TuikCpiConnector
    from oodarag.ingest.regulatory import default_connectors
    from oodarag.ooda.policy import Signal, State
    from oodarag.redact import Redactor

    cal = ObligationCalendar.from_seed()
    # Two due dates set so the deadline rules have something to work on. Real
    # dates come from the compliance officer, not from here.
    for oid, offset in (("pys-capital-adequacy-monthly", 3),
                        ("fund-spk-fee-quarterly", 14)):
        if oid in cal.obligations:
            cal.set_due(oid, today + timedelta(days=offset))
    if "gyf-year-end-appraisal" in cal.obligations:
        cal.set_due("gyf-year-end-appraisal", today - timedelta(days=5))

    # The price index comes through the connector rather than from a constant,
    # so the bundled-data downgrade is exercised and logged on every run. With
    # no network — the case here, since TÜİK is denied at the gateway — the
    # series arrives marked bundled and says so.
    cpi = TuikCpiConnector()
    series = cpi.series("TUFE")
    series.warn_if_bundled()
    index = PriceIndex(series.name, series.as_index_dict(),
                       source_uri="bundled:illustrative")

    # Connector health is read from the connectors, not asserted. Each is
    # constructed and its failure count reported; none is run against the
    # network here, so a fresh connector reports zero and the CONNECTOR-DOWN
    # rule stays quiet until something has actually been tried and failed.
    redactor = Redactor()
    connectors = default_connectors(list(profile.kap_watchlist), redactor=redactor)
    failures = {c.key: c.failures for c in connectors}
    if cpi.downgraded:
        failures["tuik"] = 1

    nav: dict[str, list] = {}
    for code, prev, cur in (("VBR", "100.00", "132.50"),   # ~nominal drift, real ~0
                            ("VIK", "100.00", "104.00")):  # nominal up, real down
        nav[code] = [
            NavPoint(code, date(today.year - 1, 7, 31),
                     Money(Decimal(prev), profile.base_currency.value),
                     valuation_basis="DEMO FIXTURE — not a real unit value"),
            NavPoint(code, date(today.year, 7, 31),
                     Money(Decimal(cur), profile.base_currency.value),
                     valuation_basis="DEMO FIXTURE — not a real unit value"),
        ]

    signals = [
        Signal(kind="fx_move", key="USDTRY", value="0.041", severity="low",
               source_uri="bundled:illustrative",
               evidence="illustrative daily move, not a live reading"),
        Signal(kind="regulatory_change", key="spk-bulletin",
               value="değerleme esasları",
               source_uri="https://spk.gov.tr/ (worked example)",
               evidence=("SPK decision 23/07/2026: exchange-traded GYF/GSYF units to be "
                         "valued at the founder's last announced unit value; compliance "
                         "by 31/07/2026"),
               verified=False),
        Signal(kind="regulatory_deadline", key="spk-bulletin", value=8,
               source_uri="https://spk.gov.tr/ (worked example)",
               evidence="eight days from publication to the compliance date",
               verified=False),
    ]

    return State(
        now=today, profile=profile, calendar=cal, index=index,
        nav_history=nav, signals=signals,
        connector_failures=failures,
        corpus_age_days={"spk": 12.0},
        citation_coverage=None,
        context={"equity_try": Decimal("30000000")},
    )


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def cmd_demo(args: argparse.Namespace) -> int:
    root, home = Path(args.root).resolve(), Path(args.home)
    profile = _profile(args)
    print(f"\n=== {profile.short_name} — end to end, no network ===\n")

    print("[1/5] deterministic core")
    _show_core(profile)

    print("\n[2/5] index")
    store, retriever = _build_index(root, home)

    print("\n[3/5] retrieval")
    hits = retriever.retrieve(args.query, k=3)
    if not hits:
        print("  no hits — the corpus indexed but retrieval returned nothing")
        return EXIT_FINDINGS
    for i, h in enumerate(hits, 1):
        comp = " ".join(f"{k}={v:.3f}" for k, v in sorted(h.components.items())
                        if isinstance(v, (int, float)))
        print(f"  {i}. {h.citation_title}  score={h.score:.4f}  [{comp}]")
        print(f"     {h.chunk.text.strip()[:150].replace(chr(10), ' ')}...")

    print("\n[4/5] one OODA cycle")
    actions = _cycle(profile, home, args)

    print("\n[5/5] brief")
    print()
    print(_brief_text(profile, actions))
    store.close()
    return EXIT_FINDINGS if actions else EXIT_OK


def _show_core(profile: FirmProfile) -> int:
    from oodarag.domain.inflation import bundled_index, naive_real_return, real_return
    from oodarag.domain.money import AmbiguousAmount, BasisMismatch, parse_amount, parse_tr

    print(f"  Turkish parse   '1.234.567,89' -> {parse_tr('1.234.567,89')}")
    try:
        parse_amount("1.500")
        print("  AMBIGUITY NOT CAUGHT — this is a bug")
        return EXIT_FINDINGS
    except AmbiguousAmount:
        print("  Ambiguity       '1.500' -> refused (1.5 or 1500 is a 1000x error)")

    try:
        Money(Decimal("1"), "TRY") + Money(Decimal("1"), "TRY", "restated", "2026-07")
        print("  BASIS MIX NOT CAUGHT — this is a bug")
        return EXIT_FINDINGS
    except BasisMismatch:
        print("  Basis guard     nominal + restated -> refused")

    n, i = Decimal("0.40"), Decimal("0.32")
    print(f"  Fisher          40% nominal at 32% CPI -> {real_return(n, i):.2%} real "
          f"(the naive answer, {naive_real_return(n, i):.2%}, overstates by a third)")
    idx = bundled_index()
    called = Money(Decimal("10000000"), "TRY")
    from oodarag.domain.inflation import restate
    print(f"  TMS 29          10.000.000 TRY of 2025-07 = "
          f"{restate(called, '2026-07', idx, '2025-07').format_tr(0)} of 2026-07")
    return EXIT_OK


def _cycle(profile: FirmProfile, home: Path, args: argparse.Namespace) -> list:
    from oodarag.ooda.act import DecisionJournal
    from oodarag.ooda.rules import default_ruleset

    today = date.fromisoformat(args.today) if getattr(args, "today", None) else date.today()
    state = _demo_state(profile, today)
    engine = default_ruleset()
    actions = engine.decide(state)
    journal = DecisionJournal(home / "decisions.jsonl")
    written = journal.record(actions, cycle=today.isoformat())
    print(f"  {len(engine.rules)} rules ran, {len(actions)} actions, "
          f"{written} journalled -> {home / 'decisions.jsonl'}")
    return actions


def _brief_text(profile: FirmProfile, actions: list) -> str:
    from oodarag.ooda.act import Brief, render_brief
    return render_brief(Brief(
        as_of=date.today(), firm=str(profile.short_name), actions=actions,
        notes=[
            "NAV figures in this brief are demo fixtures, not real unit values: the "
            "firm's own filings were unreachable from this container (unknown AIR-1).",
            "The price index is an illustrative series, not TÜİK's published one.",
        ],
    ))


def cmd_index(args: argparse.Namespace) -> int:
    store, _ = _build_index(Path(args.root).resolve(), Path(args.home))
    store.close()
    return EXIT_OK


def cmd_query(args: argparse.Namespace) -> int:
    from oodarag.answer.extractive import ExtractiveAnswerer
    from oodarag.answer.verify import coverage, verify_citations
    from oodarag.index.store import Store
    from oodarag.retrieve.hybrid import HybridRetriever
    home = Path(args.home)
    if not (home / "index.db").exists():
        print(f"no index at {home / 'index.db'} — run `ooda index` first", file=sys.stderr)
        return EXIT_ERROR
    store = Store(home / "index.db")
    try:
        hits = HybridRetriever.from_store(store).retrieve(args.question, k=args.k)
        answer = verify_citations(ExtractiveAnswerer().answer(args.question, hits), hits)
        print()
        print(answer.text)
        if answer.abstained:
            print("\nAbstention is a result, not a failure: the corpus does not "
                  "support an answer, and saying so beats inventing one.")
            return EXIT_FINDINGS
        print(f"\nconfidence {answer.confidence:.2f} · verified-citation coverage "
              f"{coverage(answer):.0%} · {answer.metrics.get('citations_dropped', 0)} dropped")
        print("\nSources — every quote above was checked against these:")
        # Several sentences can come from one chunk and share a marker; list
        # each source once, in marker order.
        seen: set[int] = set()
        for c in sorted(answer.citations, key=lambda x: x.marker):
            if c.marker in seen:
                continue
            seen.add(c.marker)
            print(f"  [{c.marker}] {c.title}  ({c.uri})")
        return EXIT_OK
    finally:
        store.close()


def cmd_loop(args: argparse.Namespace) -> int:
    profile = _profile(args)
    home = Path(args.home)
    found = 0
    for n in range(max(1, args.cycles)):
        print(f"--- cycle {n + 1} ---")
        actions = _cycle(profile, home, args)
        found += len(actions)
        for a in actions[:args.show]:
            print(a.explain())
    return EXIT_FINDINGS if found else EXIT_OK


def cmd_brief(args: argparse.Namespace) -> int:
    profile = _profile(args)
    actions = _cycle(profile, Path(args.home), args)
    text = _brief_text(profile, actions)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written to {args.out}")
    else:
        print(text)
    return EXIT_FINDINGS if actions else EXIT_OK


def cmd_rules(args: argparse.Namespace) -> int:
    from oodarag.ooda.rules import default_ruleset
    print(default_ruleset().describe())
    return EXIT_OK


def cmd_provenance(args: argparse.Namespace) -> int:
    profile = _profile(args)
    print(profile.provenance_report())
    unconfirmed = [n for n in ("base_currency", "auditor")
                   if not getattr(profile, n).trustworthy]
    return EXIT_FINDINGS if unconfirmed else EXIT_OK


def cmd_obligations(args: argparse.Namespace) -> int:
    from oodarag.domain.obligations import ObligationCalendar
    cal = ObligationCalendar.from_seed()
    if not cal.obligations:
        print("calendar is empty", file=sys.stderr)
        return EXIT_ERROR
    for _, ob in sorted(cal.obligations.items()):
        print(f"  [{ob.severity.upper():8}] {ob.label}")
        print(f"             {ob.due_rule}")
    n = len(cal.unverified)
    print(f"\n  {len(cal.obligations)} obligations, {n} unverified.")
    if n:
        print("  UNVERIFIED means: read from research that could not reach a primary")
        print("  source. A starting calendar, not legal deadlines. Confirm the tebliğ")
        print("  text — especially every 'iş günü' versus 'gün' — before acting.")
    return EXIT_FINDINGS if n else EXIT_OK


def cmd_eval(args: argparse.Namespace) -> int:
    from oodarag.eval.harness import EvalHarness, compare
    from oodarag.index.store import Store
    from oodarag.retrieve.hybrid import HybridRetriever
    home, root = Path(args.home), Path(args.root).resolve()
    goldens = EvalHarness.load(args.goldens)
    if not goldens:
        print(f"no goldens at {args.goldens}", file=sys.stderr)
        return EXIT_ERROR
    if not (home / "index.db").exists():
        _build_index(root, home, quiet=True)
    store = Store(home / "index.db")
    try:
        report = EvalHarness(HybridRetriever.from_store(store)).run(goldens)
        print(report.to_markdown())
        baseline_path = Path(args.baseline)
        if args.save_baseline:
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            baseline_path.write_text(report.to_json(), encoding="utf-8")
            print(f"\nbaseline written to {baseline_path}")
            return EXIT_OK
        if baseline_path.exists():
            import json as _json
            drops = compare(report, _json.loads(baseline_path.read_text("utf-8")))
            if drops:
                print("\nREGRESSION against the baseline:", file=sys.stderr)
                for d in drops:
                    print(f"  {d}", file=sys.stderr)
                return EXIT_FINDINGS
            print("\nNo material regression against the baseline.")
        else:
            print(f"\nNo baseline at {baseline_path}. Run with --save-baseline to set one; "
                  "until then a change cannot be told from a regression.")
        return EXIT_OK if report.passed == len(report.cases) else EXIT_FINDINGS
    finally:
        store.close()


def _profile(args: argparse.Namespace) -> FirmProfile:
    path = getattr(args, "config", None)
    return load(path) if path else WAM


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ooda",
        description="An OODA loop over a Turkish fund manager's obligations and numbers.",
    )
    p.add_argument("--home", default=str(DEFAULT_HOME), help="state directory")
    p.add_argument("--root", default=".", help="repository root used as the corpus")
    p.add_argument("--config", default=None, help="firm.toml overriding the defaults")
    p.add_argument("--today", default=None, help="override today's date (YYYY-MM-DD)")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("demo", help="end to end, offline")
    d.add_argument("--query", default="what does the system deliberately not do")
    d.set_defaults(func=cmd_demo)

    sub.add_parser("index", help="ingest and index the corpus").set_defaults(func=cmd_index)

    q = sub.add_parser("query", help="retrieve passages with their sources")
    q.add_argument("question")
    q.add_argument("-k", type=int, default=5)
    q.set_defaults(func=cmd_query)

    lo = sub.add_parser("loop", help="run OODA cycles")
    lo.add_argument("--cycles", type=int, default=1)
    lo.add_argument("--show", type=int, default=8, help="actions to explain in full")
    lo.set_defaults(func=cmd_loop)

    b = sub.add_parser("brief", help="render the Monday-morning brief")
    b.add_argument("--out", default=None)
    b.set_defaults(func=cmd_brief)

    sub.add_parser("rules", help="print every rule and why its threshold is there"
                   ).set_defaults(func=cmd_rules)
    sub.add_parser("provenance", help="print which configured facts nobody confirmed"
                   ).set_defaults(func=cmd_provenance)
    sub.add_parser("obligations", help="print the calendar, unverified ones marked"
                   ).set_defaults(func=cmd_obligations)
    ev = sub.add_parser("eval", help="score retrieval against the golden set")
    ev.add_argument("--goldens", default="evals/goldens.jsonl")
    ev.add_argument("--baseline", default="evals/baseline.json")
    ev.add_argument("--save-baseline", action="store_true",
                    help="write this run as the baseline future runs are compared to")
    ev.set_defaults(func=cmd_eval)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        if "--debug" in (argv or sys.argv):
            traceback.print_exc()
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
