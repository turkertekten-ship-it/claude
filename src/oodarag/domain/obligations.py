"""The compliance calendar, and the honesty flag that keeps it usable.

A filing calendar is the least glamorous thing in this system and the one most
likely to justify it. The SPK's 23 July 2026 valuation decision gave portfolio
managers until 31 July to comply [src:SPK-VALUATION-2026-07-23] — eight days.
Nothing that runs quarterly catches that.

Two design choices carry the weight here.

**Every seeded obligation is unverified until a human says otherwise.** The
thirty obligations shipped in ``data/obligations_tr.json`` came from a delegated
research agent that could not open a single primary source and read the tebliğs
through legal commentary [src:DELEGATED-RECON-2026-08-27]. They are genuinely
useful as a starting calendar and genuinely unsafe as legal deadlines. So
:class:`Obligation` carries ``verified``, it defaults to ``False`` for anything
loaded from the seed, and an unverified obligation says so every time it
surfaces. A wrong deadline presented confidently is worse than no deadline: it
displaces the checking that would have caught it.

**Due rules are predicates, not dates.** The dangerous obligations here are
conditional — a GSYF valuation-firm report is required every period above
TRY 50m of investment, every second period between 25m and 50m, and every third
below; an IT audit runs every two years above TRY 5m of equity and every three
below. A flat date list silently misses all of them, so an obligation carries an
applicability predicate over the firm's own attributes.

Business days are Turkish business days. "Within 6 business days of month end"
has to skip weekends *and* Turkish public holidays, and the religious ones are
lunar — they move about eleven days earlier each year and must be refreshed.
A calendar that drifts without saying so is worse than one that refuses.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal

from oodarag.util.logging import get_logger

log = get_logger("obligations")

Cadence = Literal["daily", "weekly", "monthly", "quarterly", "annual", "event_driven"]
Severity = Literal["low", "medium", "high", "critical"]

DATA_DIR = Path(__file__).parent / "data"

# --------------------------------------------------------------------------
# Turkish business days
# --------------------------------------------------------------------------

#: Fixed-date Turkish public holidays (month, day).
FIXED_HOLIDAYS: tuple[tuple[int, int], ...] = (
    (1, 1),    # Yılbaşı
    (4, 23),   # Ulusal Egemenlik ve Çocuk Bayramı
    (5, 1),    # Emek ve Dayanışma Günü
    (5, 19),   # Atatürk'ü Anma, Gençlik ve Spor Bayramı
    (7, 15),   # Demokrasi ve Millî Birlik Günü
    (8, 30),   # Zafer Bayramı
    (10, 29),  # Cumhuriyet Bayramı
)

#: Religious holidays are LUNAR: they shift roughly eleven days earlier each
#: year and cannot be computed from a fixed rule here. Only years explicitly
#: listed are covered, and :func:`business_days_after` warns rather than
#: silently assuming a date is a working day outside that range. Refresh
#: annually from the official calendar.
LUNAR_HOLIDAYS: dict[int, tuple[tuple[int, int, int], ...]] = {
    # Placeholder ranges, deliberately marked unverified in COVERED_YEARS below.
    2026: (),
    2027: (),
}

#: Years for which the lunar holiday table has actually been filled in. Empty
#: on purpose: nobody has supplied the Ramazan and Kurban Bayramı dates, and
#: pretending otherwise would make every deadline near them quietly wrong.
COVERED_YEARS: frozenset[int] = frozenset()


def is_business_day(day: date, *, extra_holidays: frozenset[date] = frozenset()) -> bool:
    if day.weekday() >= 5:
        return False
    if (day.month, day.day) in FIXED_HOLIDAYS:
        return False
    if day in extra_holidays:
        return False
    return day not in {date(*h) for h in LUNAR_HOLIDAYS.get(day.year, ())}


def business_days_after(start: date, n: int, *,
                        extra_holidays: frozenset[date] = frozenset()) -> date:
    """``n`` Turkish business days after ``start``.

    Warns when the span crosses a year whose lunar holidays are not in the
    table, because the answer is then optimistic by up to nine days — which is
    exactly the size of the SPK's eight-day compliance window.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    day, remaining = start, n
    while remaining > 0:
        day += timedelta(days=1)
        if is_business_day(day, extra_holidays=extra_holidays):
            remaining -= 1
    if day.year not in COVERED_YEARS or start.year not in COVERED_YEARS:
        log.warn(
            "business-day count may be optimistic: religious holidays not in table",
            start=start.isoformat(), result=day.isoformat(),
            covered=sorted(COVERED_YEARS) or "none",
        )
    return day


def business_days_between(a: date, b: date, *,
                          extra_holidays: frozenset[date] = frozenset()) -> int:
    """Business days from ``a`` to ``b``; negative when ``b`` precedes ``a``."""
    if b < a:
        return -business_days_between(b, a, extra_holidays=extra_holidays)
    n, day = 0, a
    while day < b:
        day += timedelta(days=1)
        if is_business_day(day, extra_holidays=extra_holidays):
            n += 1
    return n


def month_end(d: date) -> date:
    return date(d.year + d.month // 12, d.month % 12 + 1, 1) - timedelta(days=1)


def quarter_end(d: date) -> date:
    return month_end(date(d.year, ((d.month - 1) // 3) * 3 + 3, 1))


def year_end(d: date) -> date:
    return date(d.year, 12, 31)


# --------------------------------------------------------------------------
# Obligations
# --------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class Obligation:
    """One recurring or conditional duty.

    ``verified`` is the field that matters. False means: this came from
    research, not from the tebliğ, and it must not be presented as a legal
    deadline. It is carried into every alert the obligation produces.
    """

    id: str
    authority: str
    title_tr: str
    title_en: str
    cadence: Cadence
    due_rule: str
    severity: Severity = "medium"
    owner: str = ""
    evidence_uri: str = ""
    source_hash: str = ""
    verified: bool = False
    notes: str = ""
    #: Applicability predicate over firm attributes, e.g. equity or fund kinds.
    #: ``None`` means "always applies". Conditional obligations are the ones a
    #: flat calendar misses, so the hook is first-class rather than bolted on.
    applies_if: Callable[[dict[str, Any]], bool] | None = None
    #: Upstream obligations that must be satisfied first. The binding constraint
    #: on a filing is almost never the filing date — it is the appraisal that
    #: has to exist before it.
    depends_on: tuple[str, ...] = ()

    def applies(self, context: dict[str, Any] | None = None) -> bool:
        if self.applies_if is None:
            return True
        try:
            return bool(self.applies_if(context or {}))
        except Exception as e:  # a bad predicate must not hide an obligation
            log.warn("applicability predicate failed; assuming it applies",
                     obligation=self.id, err=str(e)[:200])
            return True

    @property
    def label(self) -> str:
        mark = "" if self.verified else "  [UNVERIFIED]"
        return f"{self.id} · {self.authority} · {self.title_en}{mark}"


@dataclass(slots=True)
class DueObligation:
    obligation: Obligation
    due: date
    business_days_left: int
    overdue: bool = False

    @property
    def severity(self) -> Severity:
        return self.obligation.severity

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.obligation.id,
            "authority": self.obligation.authority,
            "title": self.obligation.title_en,
            "due": self.due.isoformat(),
            "business_days_left": self.business_days_left,
            "overdue": self.overdue,
            "severity": self.obligation.severity,
            "verified": self.obligation.verified,
            "due_rule": self.obligation.due_rule,
            "evidence_uri": self.obligation.evidence_uri,
        }


@dataclass
class ObligationCalendar:
    """The set of duties, with satisfaction state and a due-date view."""

    obligations: dict[str, Obligation] = field(default_factory=dict)
    #: obligation id -> (satisfied_on, evidence_uri)
    satisfied: dict[str, tuple[date, str]] = field(default_factory=dict)
    #: Explicit due dates, set by whoever knows the real calendar. Obligations
    #: with no explicit date are reported as scheduling-unknown rather than
    #: given a guessed one.
    due_dates: dict[str, date] = field(default_factory=dict)

    def add(self, obligation: Obligation) -> None:
        self.obligations[obligation.id] = obligation

    def set_due(self, obligation_id: str, due: date) -> None:
        if obligation_id not in self.obligations:
            raise KeyError(f"unknown obligation {obligation_id!r}")
        self.due_dates[obligation_id] = due

    def satisfy(self, obligation_id: str, when: date, evidence_uri: str = "") -> None:
        if obligation_id not in self.obligations:
            raise KeyError(f"unknown obligation {obligation_id!r}")
        if not evidence_uri:
            log.warn("obligation satisfied with no evidence link", obligation=obligation_id)
        self.satisfied[obligation_id] = (when, evidence_uri)

    def is_satisfied(self, obligation_id: str, on_or_after: date | None = None) -> bool:
        rec = self.satisfied.get(obligation_id)
        if not rec:
            return False
        return on_or_after is None or rec[0] >= on_or_after

    def due_within(self, days: int, now: date,
                   context: dict[str, Any] | None = None) -> list[DueObligation]:
        """Everything applicable, unsatisfied and due within ``days``.

        Sorted by urgency. Obligations with no known due date are excluded here
        and reported by :meth:`unscheduled` instead — a missing date is a gap in
        the calendar, not a deadline that happens to be far away.
        """
        out: list[DueObligation] = []
        horizon = now + timedelta(days=days)
        for oid, ob in self.obligations.items():
            if not ob.applies(context) or self.is_satisfied(oid):
                continue
            due = self.due_dates.get(oid)
            if due is None or due > horizon:
                continue
            out.append(DueObligation(ob, due,
                                     business_days_between(now, due),
                                     overdue=due < now))
        out.sort(key=lambda d: (d.due, d.obligation.id))
        return out

    def overdue(self, now: date,
                context: dict[str, Any] | None = None) -> list[DueObligation]:
        return [d for d in self.due_within(3650, now, context) if d.overdue]

    def unscheduled(self, context: dict[str, Any] | None = None) -> list[Obligation]:
        """Applicable obligations with no due date set. A real gap, not a silence."""
        return [ob for oid, ob in sorted(self.obligations.items())
                if ob.applies(context) and oid not in self.due_dates]

    @property
    def unverified(self) -> list[Obligation]:
        return [ob for _, ob in sorted(self.obligations.items()) if not ob.verified]

    def verify(self, obligation_id: str, *, by: str, evidence_uri: str = "") -> None:
        """Mark an obligation as confirmed against the primary source."""
        ob = self.obligations[obligation_id]
        note = f"verified by {by}" + (f" against {evidence_uri}" if evidence_uri else "")
        self.obligations[obligation_id] = replace(
            ob, verified=True, evidence_uri=evidence_uri or ob.evidence_uri,
            notes=(ob.notes + "; " + note).strip("; "),
        )

    # -- loading -----------------------------------------------------------

    @classmethod
    def from_seed(cls, path: Path | str | None = None) -> ObligationCalendar:
        """Load the shipped Turkish obligation seed. Everything comes in
        unverified, whatever the file says — the file is research output."""
        p = Path(path) if path else DATA_DIR / "obligations_tr.json"
        cal = cls()
        try:
            data = json.loads(p.read_text("utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log.error("obligation seed unreadable; calendar is empty",
                      path=str(p), err=str(e)[:200])
            return cal
        meta = data.get("_meta", {})
        if meta.get("status") == "UNVERIFIED":
            log.warn("obligation seed is unverified research, not legal advice",
                     source=meta.get("source", "?"), count=len(data.get("obligations", [])))
        for raw in data.get("obligations", []):
            try:
                cal.add(Obligation(
                    id=str(raw["id"]),
                    authority=str(raw.get("authority", "")),
                    title_tr=str(raw.get("title_tr", "")),
                    title_en=str(raw.get("title_en", "")),
                    cadence=_cadence(raw.get("cadence")),
                    due_rule=str(raw.get("due_rule", "")),
                    severity=_severity(raw.get("severity")),
                    evidence_uri=str(raw.get("evidence_url", "")),
                    verified=False,
                    notes=str(meta.get("source", "")),
                ))
            except (KeyError, TypeError) as e:
                log.warn("obligation entry skipped", entry=repr(raw)[:120], err=str(e))
        log.info("obligation calendar seeded", count=len(cal.obligations), verified=0)
        return cal

    def to_json(self) -> str:
        return json.dumps({
            "obligations": [
                {
                    "id": o.id, "authority": o.authority, "title_tr": o.title_tr,
                    "title_en": o.title_en, "cadence": o.cadence,
                    "due_rule": o.due_rule, "severity": o.severity,
                    "owner": o.owner, "evidence_uri": o.evidence_uri,
                    "verified": o.verified, "notes": o.notes,
                }
                for _, o in sorted(self.obligations.items())
            ],
            "satisfied": {k: [v[0].isoformat(), v[1]] for k, v in self.satisfied.items()},
            "due_dates": {k: v.isoformat() for k, v in self.due_dates.items()},
        }, ensure_ascii=False, indent=2)


def _cadence(value: object) -> Cadence:
    v = str(value or "").strip().lower()
    return v if v in ("daily", "weekly", "monthly", "quarterly", "annual",
                      "event_driven") else "event_driven"  # type: ignore[return-value]


def _severity(value: object) -> Severity:
    v = str(value or "").strip().lower()
    return v if v in ("low", "medium", "high", "critical") else "medium"  # type: ignore[return-value]
