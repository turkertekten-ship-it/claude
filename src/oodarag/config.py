"""The firm this system is pointed at, as data rather than as scattered literals.

A retrieval pipeline is generic. The thing that makes one *useful* to a
particular fund manager is the small, boring set of facts about which funds
exist, which regulator publishes what, and how far a number may move before a
human should look at it. Those facts belong in one file, versioned, so that
changing them is a reviewable diff rather than a grep through the codebase.

There is a second reason this module exists, and it is the more important one.

Every field here is either something a source established or something this
codebase assumed. Those two categories look identical once they are written as
Python literals, and a system that blurs them will eventually put an assumption
into an investor report. So each fact carries its provenance inline, and
:func:`provenance_report` prints the split. Anything marked ``ASSUMED`` is a
placeholder awaiting the owner, not a finding — and a rule that fires on an
assumed threshold should say so when it fires.

The defaults describe WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi
A.Ş. What could be established about it is recorded in
``docs/research/02-subject-profile.md`` and backed by ``provenance/sources.yaml``.
What could not — fund sizes, holdings, AUM — is registered as unknown U-7,
because the firm's own site and its KAP record are both unreachable from this
container. Supply them with :func:`load`; do not invent them here.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields as dc_fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from oodarag.util.logging import get_logger

log = get_logger("config")

#: Provenance grades. ``SOURCED`` means a ledger entry backs it; ``ASSUMED``
#: means this codebase chose it and nobody has confirmed it; ``OWNER`` means the
#: owner supplied it directly, which outranks both.
Grade = Literal["SOURCED", "ASSUMED", "OWNER"]

FundKind = Literal["GSYF", "GYF", "UNKNOWN"]


@dataclass(slots=True, frozen=True)
class Fact:
    """A configuration value that remembers where it came from.

    Wrapping a scalar in an object is friction, and friction is the point: it is
    deliberately awkward to add a fact here without saying whether anyone
    checked it.
    """

    value: Any
    grade: Grade
    source: str = ""
    note: str = ""

    def __str__(self) -> str:  # so a Fact interpolates readably into a brief
        return str(self.value)

    @property
    def trustworthy(self) -> bool:
        return self.grade in ("SOURCED", "OWNER")


@dataclass(slots=True, frozen=True)
class FundRef:
    """One fund the firm founds and manages.

    ``code`` is the KAP disclosure code and is the join key everywhere else in
    the system: it is what the KAP connector filters on, what an obligation is
    attributed to, and what a NAV series is keyed by.

    Note what is *absent*: size, holdings, unit count, inception. Those were not
    establishable for this firm from outside — GSYF and GYF are
    qualified-investor vehicles and do not publish them — so the dataclass has
    no field inviting a guess. They arrive through :func:`load` or not at all.
    """

    code: str
    name_tr: str
    kind: FundKind
    grade: Grade = "ASSUMED"
    source: str = ""

    @property
    def is_venture(self) -> bool:
        return self.kind == "GSYF"

    @property
    def is_real_estate(self) -> bool:
        return self.kind == "GYF"


@dataclass(slots=True, frozen=True)
class SourceRef:
    """A publisher the Observe phase watches.

    ``authority`` is the reranker's trust weight. The ordering it encodes is not
    a preference: a rule about a filing deadline that cites a blog over the
    Official Gazette is wrong even when the blog happens to be right, because
    the citation is what an auditor follows.
    """

    key: str
    name: str
    base_url: str
    authority: float
    lang: str = "tr"
    kind: str = "regulator"
    note: str = ""


@dataclass(slots=True, frozen=True)
class Thresholds:
    """The numbers a rule compares against.

    Every one of these is ``ASSUMED`` until the owner sets it. They are gathered
    here rather than scattered through the ruleset precisely so that the honest
    answer to "where did 5% come from?" is one file away.

    They are set deliberately loose. An alerting system's failure mode is not
    missing an event; it is firing so often that the reader stops looking, at
    which point it misses every event. Tightening a threshold after a month of
    silence is easy. Recovering a reader's attention is not.
    """

    #: Fund unit value move, period over period, that warrants a human look.
    #: Expressed in REAL terms: at ~32% inflation a nominal move of this size is
    #: noise, and a rule written against nominal values would fire every month.
    valuation_drift_real: Decimal = Decimal("0.05")

    #: Nominal move that warrants a look regardless of inflation, because a jump
    #: this large is usually a data error rather than a valuation event.
    valuation_drift_nominal: Decimal = Decimal("0.25")

    #: How far ahead the obligation calendar looks when building the brief.
    deadline_horizon_days: int = 21

    #: Inside this many days, an unsatisfied obligation escalates rather than
    #: appearing in a digest.
    deadline_escalate_days: int = 5

    #: Daily TRY move against USD that is worth remarking on. The lira's
    #: managed depreciation means small daily moves are the normal state, so a
    #: rule at 1% would be a daily alarm clock.
    fx_daily_move: Decimal = Decimal("0.03")

    #: An appraisal older than this is stale for valuation purposes.
    appraisal_max_age_days: int = 365

    #: If a corpus has not been refreshed in this long, retrieval is answering
    #: from a stale world and should say so.
    index_stale_days: int = 7

    #: Below this citation coverage, an answer is not trustworthy enough to put
    #: in front of anyone, and the pipeline should abstain rather than hedge.
    citation_coverage_floor: float = 0.6

    #: Consecutive failed runs of one connector before it is treated as broken
    #: rather than flaky.
    connector_failure_streak: int = 3


@dataclass(slots=True, frozen=True)
class FirmProfile:
    """Everything the system needs to know about whose books it is watching."""

    legal_name: Fact
    short_name: Fact
    kap_company_code: Fact
    city: Fact
    base_currency: Fact
    auditor: Fact
    funds: tuple[FundRef, ...] = ()
    sources: tuple[SourceRef, ...] = ()
    watch_keywords: tuple[str, ...] = ()
    thresholds: Thresholds = field(default_factory=Thresholds)

    def fund(self, code: str) -> FundRef | None:
        code = code.strip().upper()
        for f in self.funds:
            if f.code == code:
                return f
        return None

    @property
    def fund_codes(self) -> tuple[str, ...]:
        return tuple(f.code for f in self.funds)

    @property
    def kap_watchlist(self) -> tuple[str, ...]:
        """Codes the KAP connector filters on: the company plus every fund."""
        company = str(self.kap_company_code.value)
        return (company,) + self.fund_codes if company else self.fund_codes

    def source(self, key: str) -> SourceRef | None:
        for s in self.sources:
            if s.key == key:
                return s
        return None

    @property
    def authority_map(self) -> dict[str, float]:
        """Connector key -> trust weight, for the reranker."""
        return {s.key: s.authority for s in self.sources}

    def provenance_report(self) -> str:
        """Print which of these facts anyone actually checked.

        Run this before trusting a brief. A field marked ASSUMED that turns out
        to matter is the cheapest bug in this system to fix and the most
        expensive one to discover downstream.
        """
        lines = ["Firm configuration — provenance", "=" * 40]
        scalars = [
            ("legal_name", self.legal_name),
            ("short_name", self.short_name),
            ("kap_company_code", self.kap_company_code),
            ("city", self.city),
            ("base_currency", self.base_currency),
            ("auditor", self.auditor),
        ]
        for name, fact in scalars:
            tag = fact.grade.ljust(8)
            src = f"  [{fact.source}]" if fact.source else ""
            lines.append(f"  {tag} {name}: {fact.value}{src}")
            if fact.note:
                lines.append(f"           note: {fact.note}")

        lines.append("")
        lines.append("  Funds:")
        for f in self.funds:
            src = f"  [{f.source}]" if f.source else ""
            lines.append(f"    {f.grade.ljust(8)} {f.code}  {f.kind}  {f.name_tr}{src}")

        assumed = [n for n, f in scalars if f.grade == "ASSUMED"]
        assumed += [f"fund:{f.code}" for f in self.funds if f.grade == "ASSUMED"]
        lines.append("")
        n_thresholds = len(dc_fields(self.thresholds))
        lines.append(
            f"  Thresholds: {n_thresholds} values, all set by this codebase "
            "and confirmed by nobody."
        )
        if assumed:
            lines.append(f"  Unconfirmed fields: {', '.join(assumed)}")
        else:
            lines.append("  No unconfirmed fields.")
        lines.append("")
        lines.append("  NOT established anywhere: fund sizes, holdings, unit counts, AUM.")
        lines.append("  See provenance/unknowns.md U-7. Supply via config.load(); never guess.")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# The default profile: WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi A.Ş.
#
# Source ids below resolve to entries in provenance/sources.yaml.
# --------------------------------------------------------------------------

_WAM_FUNDS: tuple[FundRef, ...] = (
    FundRef(
        code="VBR",
        name_tr="WAM ... Birinci Girişim Sermayesi Yatırım Fonu",
        kind="GSYF",
        grade="SOURCED",
        source="WAM-FUND-CODES-2026-08-27",
    ),
    FundRef(
        code="VBI",
        name_tr="WAM ... Birinci Proje Gayrimenkul Yatırım Fonu",
        kind="GYF",
        grade="SOURCED",
        source="WAM-FUND-CODES-2026-08-27",
    ),
    FundRef(
        code="VIK",
        name_tr="WAM ... İkinci Gayrimenkul Yatırım Fonu",
        kind="GYF",
        grade="SOURCED",
        source="WAM-FUND-CODES-2026-08-27",
    ),
    # WQQ has KAP filings under the firm's name, but the fund's registered title
    # was not recovered and its kind is inferred from a single press summary
    # describing a technology focus. Recorded as UNKNOWN rather than guessed
    # into GSYF, so that anything keyed on kind has to confront the gap.
    FundRef(
        code="WQQ",
        name_tr="(registered title not recovered)",
        kind="UNKNOWN",
        grade="ASSUMED",
        source="WAM-FUND-CODES-2026-08-27",
    ),
)

_TR_SOURCES: tuple[SourceRef, ...] = (
    SourceRef(
        key="resmigazete",
        name="T.C. Resmî Gazete",
        base_url="https://www.resmigazete.gov.tr/",
        authority=1.0,
        kind="official_gazette",
        note="The only place a rule becomes law. Outranks every summary of it.",
    ),
    SourceRef(
        key="spk",
        name="Sermaye Piyasası Kurulu",
        base_url="https://spk.gov.tr/",
        authority=0.98,
        kind="regulator",
        note="Weekly bulletins carry the decisions that bind a portföy yönetim şirketi.",
    ),
    SourceRef(
        key="kap",
        name="Kamuyu Aydınlatma Platformu",
        base_url="https://www.kap.org.tr/",
        authority=0.95,
        kind="disclosure",
        note="The firm's and the funds' own filings. Blocked by egress here; see U-7.",
    ),
    SourceRef(
        key="tspb",
        name="Türkiye Sermaye Piyasaları Birliği",
        base_url="https://www.tspb.org.tr/",
        authority=0.85,
        kind="industry_body",
        note="Genel mektuplar reach members before the practice settles.",
    ),
    SourceRef(
        key="tcmb",
        name="Türkiye Cumhuriyet Merkez Bankası",
        base_url="https://www.tcmb.gov.tr/",
        authority=0.95,
        kind="central_bank",
        note="Policy rate and FX. Feeds the real-terms twin of every figure.",
    ),
    SourceRef(
        key="tuik",
        name="Türkiye İstatistik Kurumu",
        base_url="https://www.tuik.gov.tr/",
        authority=0.95,
        kind="statistics",
        note="TÜFE, the index TMS 29 restatement is computed against.",
    ),
    SourceRef(
        key="gib",
        name="Gelir İdaresi Başkanlığı",
        base_url="https://www.gib.gov.tr/",
        authority=0.9,
        kind="tax",
        note="The GSYF/GYF participation-income exemption lives or dies here.",
    ),
)

#: Terms that make a Resmî Gazete or SPK item relevant to this firm. Kept
#: deliberately narrow: a keyword list that matches everything is a crawler, not
#: a filter, and the reading cost of a false positive is paid by a human.
_WATCH_KEYWORDS: tuple[str, ...] = (
    "portföy yönetim şirketi",
    "girişim sermayesi yatırım fonu",
    "gayrimenkul yatırım fonu",
    "nitelikli yatırımcı",
    "kolektif yatırım",
    "enflasyon muhasebesi",
    "değerleme esasları",
    "katılma payı",
    "kurumlar vergisi istisnası",
    "portföy sınırlamaları",
    "III-52",
    "III-55",
    "III-56",
    "TMS 29",
)

WAM = FirmProfile(
    legal_name=Fact(
        "WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi A.Ş.",
        "SOURCED",
        "WAM-FIRM-2026-08-27",
    ),
    short_name=Fact("WAM Portföy", "SOURCED", "WAM-FIRM-2026-08-27"),
    kap_company_code=Fact("VPG", "SOURCED", "WAM-FUND-CODES-2026-08-27"),
    city=Fact("İstanbul (Teşvikiye)", "SOURCED", "WAM-FIRM-2026-08-27"),
    base_currency=Fact(
        "TRY",
        "ASSUMED",
        note=(
            "Turkish funds report in lira, but a GYF holding hard-currency "
            "leases or a GSYF with USD-denominated commitments may keep a "
            "different functional currency. Confirm before any conversion is "
            "presented as authoritative."
        ),
    ),
    auditor=Fact(
        "CNS Bağımsız Denetim A.Ş.",
        "ASSUMED",
        "SUBAGENT-PROFILE-2026-08-27",
        note="Second-hand: reported by a delegated agent from a KAP summary, not verified here.",
    ),
    funds=_WAM_FUNDS,
    sources=_TR_SOURCES,
    watch_keywords=_WATCH_KEYWORDS,
    thresholds=Thresholds(),
)


def load(path: str | Path, base: FirmProfile = WAM) -> FirmProfile:
    """Overlay a TOML file onto a profile, grading everything it sets as OWNER.

    This is how the unknowns get closed without a code change. A file like::

        legal_name = "..."
        base_currency = "TRY"

        [thresholds]
        valuation_drift_real = "0.03"

        [[funds]]
        code = "WQQ"
        name_tr = "WAM ... İkinci Girişim Sermayesi Yatırım Fonu"
        kind = "GSYF"

    replaces the matching defaults. Anything the file sets is graded ``OWNER``,
    which outranks both ``SOURCED`` and ``ASSUMED``, because the person who
    signs the accounts is a better authority on his own fund list than a search
    engine is.

    Funds are matched on ``code`` and merged, so a file may correct one fund
    without restating the others. A missing or unreadable file is a no-op with a
    warning rather than an error: a system that refuses to start because an
    optional override is absent is a system that gets started less often.

    Decimals are read from strings. TOML floats would silently round a
    threshold, and a threshold is compared against money.
    """
    p = Path(path)
    if not p.exists():
        log.warn("config override not found, using defaults", path=str(p))
        return base
    try:
        data = tomllib.loads(p.read_text("utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        log.error("config override unreadable, using defaults", path=str(p), err=str(e)[:200])
        return base

    changes: dict[str, Any] = {}
    for name in ("legal_name", "short_name", "kap_company_code", "city",
                 "base_currency", "auditor"):
        if name in data:
            changes[name] = Fact(data[name], "OWNER", source=str(p))

    if "watch_keywords" in data:
        changes["watch_keywords"] = tuple(str(k) for k in data["watch_keywords"])

    if "thresholds" in data and isinstance(data["thresholds"], dict):
        changes["thresholds"] = _merge_thresholds(base.thresholds, data["thresholds"], p)

    if "funds" in data and isinstance(data["funds"], list):
        changes["funds"] = _merge_funds(base.funds, data["funds"], p)

    if not changes:
        log.warn("config override contained nothing recognised", path=str(p))
        return base
    log.info("config override applied", path=str(p), fields=sorted(changes))
    return replace(base, **changes)


def _merge_thresholds(base: Thresholds, raw: dict[str, Any], path: Path) -> Thresholds:
    out: dict[str, Any] = {}
    known = {f.name: getattr(base, f.name) for f in dc_fields(base)}
    for name, current in known.items():
        if name not in raw:
            continue
        given = raw[name]
        try:
            if isinstance(current, Decimal):
                out[name] = Decimal(str(given))
            elif isinstance(current, int) and not isinstance(current, bool):
                out[name] = int(given)
            else:
                out[name] = float(given)
        except (ValueError, ArithmeticError) as e:
            log.warn("threshold ignored, unparseable", name=name, value=repr(given),
                     path=str(path), err=str(e))
    unknown = set(raw) - set(known)
    if unknown:
        # Silence here would let a typo'd threshold read as "configured".
        log.warn("unknown thresholds ignored", names=sorted(unknown), path=str(path))
    return replace(base, **out) if out else base


def _merge_funds(base: tuple[FundRef, ...], raw: list[Any], path: Path) -> tuple[FundRef, ...]:
    by_code = {f.code: f for f in base}
    order = [f.code for f in base]
    for entry in raw:
        if not isinstance(entry, dict) or "code" not in entry:
            log.warn("fund entry ignored, no code", entry=repr(entry)[:120], path=str(path))
            continue
        code = str(entry["code"]).strip().upper()
        existing = by_code.get(code)
        kind = str(entry.get("kind", existing.kind if existing else "UNKNOWN")).upper()
        if kind not in ("GSYF", "GYF", "UNKNOWN"):
            log.warn("fund kind not recognised, recorded as UNKNOWN", code=code, kind=kind)
            kind = "UNKNOWN"
        by_code[code] = FundRef(
            code=code,
            name_tr=str(entry.get("name_tr", existing.name_tr if existing else "")),
            kind=kind,  # type: ignore[arg-type]
            grade="OWNER",
            source=str(path),
        )
        if code not in order:
            order.append(code)
    return tuple(by_code[c] for c in order)
