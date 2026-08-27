"""TMS 29 restatement and real returns, for an economy running at 31.75%.

At Turkish inflation levels [src:TCMB-MACRO-2026-08] the difference between a
nominal and a real figure is not a refinement, it is the sign of the answer. A
fund reporting a 30% nominal year has lost purchasing power. A report that
prints only the nominal number is not neutral — it is wrong in the direction
that flatters, every single time.

Two things in here are easy to get subtly wrong and are therefore written out
in full.

**The Fisher relation, not subtraction.** Real return is ``(1+n)/(1+i) - 1``,
not ``n - i``. At a 40% nominal return and 32% inflation the correct answer is
about 6.06%; the subtraction gives 8%, overstating by a third of the answer.
The error grows with the level of inflation, which is precisely when it matters.

**Restatement is a ratio of index values,** ``index[to] / index[from]`` — the
IAS 29 conversion factor. The temptation is to interpolate a missing month so
the arithmetic never fails. :class:`PriceIndex` refuses instead: a fabricated
index point produces a fabricated restated figure that looks exactly like a
real one, and there is no way to detect it downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from oodarag.domain.money import Money, MoneyError

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class IndexError_(MoneyError):
    """A period was asked for that the index does not have."""


@dataclass(slots=True, frozen=True)
class IndexPoint:
    period: str
    value: Decimal
    source_uri: str = ""
    provisional: bool = False


class PriceIndex:
    """A monthly price index — TÜFE, in this system's case.

    ``provisional`` marks a point that the statistics office may revise. A
    restatement computed against a provisional point is itself provisional, and
    :meth:`factor` says so, because a number that quietly changes next month is
    worse than one that was never published.
    """

    def __init__(self, name: str, points: dict[str, Decimal | str] | None = None,
                 *, source_uri: str = "", provisional: set[str] | None = None) -> None:
        self.name = name
        self.source_uri = source_uri
        self._points: dict[str, IndexPoint] = {}
        for period, value in (points or {}).items():
            self.add(period, value, provisional=period in (provisional or set()))

    def add(self, period: str, value: Decimal | str, *, source_uri: str = "",
            provisional: bool = False) -> None:
        if not _PERIOD_RE.match(period):
            raise IndexError_(f"period must be YYYY-MM, got {period!r}")
        try:
            v = value if isinstance(value, Decimal) else Decimal(str(value))
        except InvalidOperation as e:
            raise IndexError_(f"index value not a number: {value!r}") from e
        if v <= 0:
            raise IndexError_(f"index value must be positive, got {v}")
        self._points[period] = IndexPoint(period, v, source_uri or self.source_uri,
                                          provisional)

    def __contains__(self, period: str) -> bool:
        return period in self._points

    def __len__(self) -> int:
        return len(self._points)

    @property
    def periods(self) -> list[str]:
        return sorted(self._points)

    @property
    def latest(self) -> IndexPoint | None:
        return self._points[self.periods[-1]] if self._points else None

    def point(self, period: str) -> IndexPoint:
        try:
            return self._points[period]
        except KeyError:
            near = ", ".join(self.periods[-3:]) or "none"
            raise IndexError_(
                f"{self.name} has no point for {period}. It will not be "
                f"interpolated: a fabricated index value produces a fabricated "
                f"restated figure that is indistinguishable from a real one. "
                f"Latest available: {near}."
            ) from None

    def factor(self, from_period: str, to_period: str) -> tuple[Decimal, bool]:
        """The IAS 29 conversion factor, and whether it rests on provisional data."""
        a, b = self.point(from_period), self.point(to_period)
        return b.value / a.value, (a.provisional or b.provisional)

    def inflation_between(self, from_period: str, to_period: str) -> Decimal:
        """Cumulative inflation over the span, as a decimal fraction."""
        factor, _ = self.factor(from_period, to_period)
        return factor - 1


def restate(amount: Money, to_period: str, index: PriceIndex,
            from_period: str | None = None) -> Money:
    """Restate an amount into lira of ``to_period`` purchasing power.

    A nominal amount needs ``from_period`` — the period it was actually incurred
    in — because nominal money carries no date of its own. An already-restated
    amount knows its own period and is re-restated from there, which is how two
    figures on different periods are brought onto one basis before they may be
    added.
    """
    if amount.basis == "nominal":
        if not from_period:
            raise MoneyError(
                "restating a nominal amount requires from_period: nominal money "
                "carries no date, so there is nothing to restate from"
            )
        origin = from_period
    else:
        origin = amount.period  # type: ignore[assignment]
        if from_period and from_period != origin:
            raise MoneyError(
                f"amount is already restated to {origin}; passing "
                f"from_period={from_period!r} would restate from the wrong base"
            )
    factor, _ = index.factor(origin, to_period)
    return Money(amount.amount * factor, amount.currency, "restated", to_period)


def real_return(nominal_return: Decimal, inflation_rate: Decimal) -> Decimal:
    """The Fisher relation: ``(1+n)/(1+i) - 1``.

    Not ``n - i``. At n=0.40 and i=0.32 this returns ~0.0606 where the
    subtraction gives 0.08 — an overstatement of a third of the answer, and the
    gap widens as inflation rises.
    """
    denom = Decimal(1) + inflation_rate
    if denom == 0:
        raise MoneyError("inflation rate of -100% leaves no real return defined")
    return (Decimal(1) + nominal_return) / denom - Decimal(1)


def naive_real_return(nominal_return: Decimal, inflation_rate: Decimal) -> Decimal:
    """The wrong formula, kept so a test can assert how wrong it is.

    Exported deliberately: the gap between this and :func:`real_return` is the
    argument for the whole module, and an argument you can run beats one you
    have to trust.
    """
    return nominal_return - inflation_rate


def real_return_over(nominal_return: Decimal, from_period: str, to_period: str,
                     index: PriceIndex) -> Decimal:
    """Real return over a span, taking inflation from the index."""
    return real_return(nominal_return, index.inflation_between(from_period, to_period))


def annualize(period_return: Decimal, periods_per_year: int) -> Decimal:
    """Compound a per-period return to a year. Uses float internally for the
    fractional power, then returns to Decimal — the only place in the money path
    where that is tolerated, and it is a ratio rather than an amount."""
    if periods_per_year <= 0:
        raise MoneyError("periods_per_year must be positive")
    base = float(Decimal(1) + period_return)
    if base <= 0:
        raise MoneyError("cannot annualize a return of -100% or worse")
    return Decimal(str(base ** periods_per_year)) - Decimal(1)


def cumulative(returns: list[Decimal]) -> Decimal:
    """Chain-link a series of period returns."""
    total = Decimal(1)
    for r in returns:
        total *= Decimal(1) + r
    return total - Decimal(1)


def purchasing_power_loss(amount: Money, from_period: str, to_period: str,
                          index: PriceIndex) -> Money:
    """How much of a held nominal amount inflation ate over the span.

    Returned as a restated amount so it cannot be added to the nominal original
    by accident — which is exactly the mistake this figure invites.
    """
    if amount.basis != "nominal":
        raise MoneyError("purchasing-power loss is computed on a nominal holding")
    restated = restate(amount, to_period, index, from_period)
    still_worth = Money(amount.amount, amount.currency, "restated", to_period)
    return still_worth - restated


def monetary_gain_loss(net_monetary_position: Money, from_period: str,
                       to_period: str, index: PriceIndex) -> Money:
    """The IAS 29 gain or loss on a net monetary position.

    Holding net monetary assets through inflation loses purchasing power;
    holding net monetary liabilities gains it. The sign follows the position, so
    a net borrower in Turkey shows a monetary gain — which is real, and is the
    part of hyperinflationary accounting that most surprises people reading it
    for the first time.
    """
    if net_monetary_position.basis != "nominal":
        raise MoneyError("the net monetary position is a nominal figure by definition")
    factor, _ = index.factor(from_period, to_period)
    loss = net_monetary_position.amount * (factor - Decimal(1))
    return Money(-loss, net_monetary_position.currency, "restated", to_period)


#: A small bundled TÜFE series so the pipeline is demonstrable with no network.
#: CLEARLY NOT A LIVE READING: these are illustrative index levels consistent
#: with the reported 31.75% year-on-year rate for July 2026
#: [src:TCMB-MACRO-2026-08], not TÜİK's published series. Anything computed
#: from them is a worked example. Replace with the real series before any
#: figure leaves the building.
BUNDLED_TUFE_ILLUSTRATIVE: dict[str, str] = {
    "2025-07": "100.00",
    "2025-08": "102.10",
    "2025-09": "104.35",
    "2025-10": "106.40",
    "2025-11": "108.70",
    "2025-12": "111.20",
    "2026-01": "114.90",
    "2026-02": "117.60",
    "2026-03": "120.10",
    "2026-04": "122.55",
    "2026-05": "124.80",
    "2026-06": "127.35",
    "2026-07": "131.75",
}


def bundled_index() -> PriceIndex:
    """The illustrative index, named so nobody mistakes it for TÜİK data."""
    return PriceIndex(
        "TUFE-ILLUSTRATIVE-NOT-LIVE",
        dict(BUNDLED_TUFE_ILLUSTRATIVE),
        source_uri="bundled:illustrative",
    )
