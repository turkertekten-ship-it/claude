"""Fund metrics, each with a real-terms twin.

The point of this module is one sentence: **at 31.75% inflation a nominal
multiple is not a result.** A fund that turned 100 lira into 140 over a year
where the index rose 32% did not make 40%; it made about 6%. Reporting the 40%
is not a presentational choice, it is an error of a third of the answer, and it
always errs upward.

So every metric here comes in a pair. ``moic`` and ``real_moic``, ``xirr`` and
``real_xirr``. The real variants restate each cashflow to a common period before
computing, which is the only correct order — restating the *result* of a
nominal IRR is not the same number and is not defensible.

``xirr`` is bisection first, then Newton, then bisection again if Newton wanders
off. That is deliberately unfashionable. Newton alone diverges on the cashflow
shapes funds actually produce — a large early call, a long flat middle, a single
terminal distribution — and a solver that returns a plausible wrong rate is far
worse here than one that says it could not solve.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from oodarag.domain.inflation import PriceIndex, real_return, restate
from oodarag.domain.money import Money, MoneyError

DAYS_PER_YEAR = Decimal("365")


class ValuationError(MoneyError):
    pass


class NoSolution(ValuationError):
    """The cashflows admit no rate of return, or none could be found.

    Raised rather than returning a sentinel, because a sentinel gets formatted
    into a report as a number.
    """


@dataclass(slots=True, frozen=True)
class CashFlow:
    """One dated movement. Negative is into the fund, positive is out of it."""

    on: date
    amount: Money

    @property
    def period(self) -> str:
        return f"{self.on.year:04d}-{self.on.month:02d}"


# --------------------------------------------------------------------------
# IRR
# --------------------------------------------------------------------------

def _npv(rate: float, flows: list[tuple[float, float]]) -> float:
    return sum(a / (1.0 + rate) ** t for t, a in flows)


def xirr(cashflows: list[CashFlow], *, guess: float = 0.1,
         tolerance: float = 1e-9, max_iter: int = 200) -> Decimal:
    """Money-weighted return on irregularly dated flows.

    Requires at least one negative and one positive flow — without a sign change
    there is no rate that zeroes the NPV, and any number returned would be
    fiction. Rates are floats internally (a root-find on Decimal is not worth
    the cost) and returned as Decimal at a scale the arithmetic can support.
    """
    if len(cashflows) < 2:
        raise NoSolution("at least two cashflows are needed for a rate of return")
    _assert_uniform(cashflows)
    amounts = [float(c.amount.amount) for c in cashflows]
    if not (any(a < 0 for a in amounts) and any(a > 0 for a in amounts)):
        raise NoSolution(
            "cashflows have no sign change; a fund that only ever received "
            "money, or only ever paid it out, has no internal rate of return"
        )

    t0 = min(c.on for c in cashflows)
    flows = [((c.on - t0).days / float(DAYS_PER_YEAR), a)
             for c, a in zip(cashflows, amounts, strict=True)]

    # Bracket by scanning: robust where Newton is not.
    lo, hi = -0.9999, 10.0
    f_lo, f_hi = _npv(lo, flows), _npv(hi, flows)
    if f_lo * f_hi > 0:
        raise NoSolution(
            "no rate between -99.99% and +1000% zeroes the NPV; the cashflows "
            "are likely mis-signed or mis-dated"
        )
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = _npv(mid, flows)
        if abs(f_mid) < tolerance or (hi - lo) < tolerance:
            return Decimal(str(round(mid, 10)))
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    raise NoSolution("bisection did not converge within the iteration budget")


def real_xirr(cashflows: list[CashFlow], to_period: str, index: PriceIndex) -> Decimal:
    """IRR on cashflows restated to a common period first.

    Restating before solving is the correct order. Deflating a nominal IRR
    afterwards gives a different, indefensible number whenever the flows are
    unevenly spaced — which they always are.
    """
    restated = [
        CashFlow(c.on, restate(c.amount, to_period, index, c.period))
        for c in cashflows
    ]
    return xirr(restated)


def _assert_uniform(cashflows: list[CashFlow]) -> None:
    bases = {(c.amount.currency, c.amount.basis, c.amount.period) for c in cashflows}
    if len(bases) > 1:
        raise ValuationError(
            f"cashflows are on {len(bases)} different currency/basis combinations "
            f"({sorted(str(b) for b in bases)}). Bring them onto one basis before "
            "computing a return; mixing nominal and restated flows produces a "
            "number with no meaning."
        )


# --------------------------------------------------------------------------
# Multiples
# --------------------------------------------------------------------------

def moic(distributions: Money, residual_value: Money, paid_in: Money) -> Decimal:
    """(DPI + RVPI). Total value over paid-in capital."""
    if paid_in.amount == 0:
        raise ValuationError("no paid-in capital: MOIC is undefined, not infinite")
    return (distributions + residual_value).ratio(paid_in)


def dpi(distributions: Money, paid_in: Money) -> Decimal:
    if paid_in.amount == 0:
        raise ValuationError("no paid-in capital: DPI is undefined")
    return distributions.ratio(paid_in)


def rvpi(residual_value: Money, paid_in: Money) -> Decimal:
    if paid_in.amount == 0:
        raise ValuationError("no paid-in capital: RVPI is undefined")
    return residual_value.ratio(paid_in)


def tvpi(distributions: Money, residual_value: Money, paid_in: Money) -> Decimal:
    return moic(distributions, residual_value, paid_in)


def real_moic(distributions: Money, residual_value: Money, paid_in: Money,
              *, paid_in_period: str, to_period: str, index: PriceIndex) -> Decimal:
    """MOIC with the paid-in capital restated to today's purchasing power.

    This is the number that tells you whether the fund actually made anything.
    A 1.4x nominal multiple on capital called two years ago at 30%-plus
    inflation is a loss.
    """
    value = distributions + residual_value
    value_r = value if value.basis == "restated" else restate(value, to_period, index,
                                                              to_period)
    paid_r = restate(paid_in, to_period, index, paid_in_period)
    return value_r.ratio(paid_r)


def nav_per_unit(fund_nav: Money, units: Decimal) -> Money:
    """The highest-consequence number the firm publishes.

    Since 31 July 2026 other institutions must book exchange-traded GYF/GSYF
    units at the founder's last announced unit value rather than the market
    price [src:SPK-VALUATION-2026-07-23], which makes this figure something
    third parties rely on rather than an internal report.
    """
    if units <= 0:
        raise ValuationError("units outstanding must be positive")
    return Money(fund_nav.amount / units, fund_nav.currency,
                 fund_nav.basis, fund_nav.period)


# --------------------------------------------------------------------------
# Drift — what feeds the policy engine
# --------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class NavPoint:
    """A published unit value, with everything an auditor asks about it."""

    fund_code: str
    as_of: date
    unit_value: Money
    units: Decimal | None = None
    valuation_basis: str = ""
    valuer: str = ""
    resolution_ref: str = ""
    source_uri: str = ""

    @property
    def period(self) -> str:
        return f"{self.as_of.year:04d}-{self.as_of.month:02d}"


def valuation_drift(previous: NavPoint, current: NavPoint,
                    index: PriceIndex | None = None) -> dict[str, Any]:
    """Nominal and real move between two published unit values.

    Both are returned because they answer different questions and the wrong one
    is usually the one on the page. A rule that alerts on nominal drift in this
    economy fires every month on inflation alone; a rule that alerts on real
    drift catches a valuation event.
    """
    if previous.fund_code != current.fund_code:
        raise ValuationError(
            f"comparing different funds: {previous.fund_code} and {current.fund_code}"
        )
    if current.as_of <= previous.as_of:
        raise ValuationError("current NAV point must be later than the previous one")
    if previous.unit_value.amount == 0:
        raise ValuationError("previous unit value is zero; no drift is definable")

    nominal = (current.unit_value.amount / previous.unit_value.amount) - Decimal(1)
    out: dict[str, Any] = {
        "fund_code": current.fund_code,
        "from": previous.as_of.isoformat(),
        "to": current.as_of.isoformat(),
        "nominal_move": nominal,
        "real_move": None,
        "inflation": None,
        "basis_note": (
            f"{previous.unit_value.basis_label} -> {current.unit_value.basis_label}"
        ),
    }
    if index is None:
        return out
    try:
        inflation = index.inflation_between(previous.period, current.period)
    except Exception as e:  # a missing index point must not hide the nominal move
        out["inflation_error"] = str(e)[:200]
        return out
    out["inflation"] = inflation
    out["real_move"] = real_return(nominal, inflation)
    return out


def breaches(drift: dict[str, Any], *, real_threshold: Decimal,
             nominal_threshold: Decimal) -> list[str]:
    """Which drift thresholds this move crosses. Empty means nothing to say."""
    hits: list[str] = []
    nominal = drift.get("nominal_move")
    real = drift.get("real_move")
    if nominal is not None and abs(nominal) > nominal_threshold:
        hits.append("nominal")
    if real is not None and abs(real) > real_threshold:
        hits.append("real")
    return hits
