"""The deterministic core: money, inflation, obligations, valuation.

Nothing in this package may call a language model, and nothing outside it may
compute a monetary figure. That boundary is the design's central claim and is
argued in docs/adr/0002-deterministic-decision-boundary.md.
"""

from oodarag.domain.inflation import (
    PriceIndex,
    bundled_index,
    monetary_gain_loss,
    purchasing_power_loss,
    real_return,
    restate,
)
from oodarag.domain.money import (
    AmbiguousAmount,
    BasisMismatch,
    CurrencyMismatch,
    FxRate,
    Money,
    MoneyError,
    convert,
    parse_amount,
    parse_en,
    parse_tr,
)
from oodarag.domain.obligations import (
    DueObligation,
    Obligation,
    ObligationCalendar,
    business_days_after,
    business_days_between,
    is_business_day,
)
from oodarag.domain.valuation import (
    CashFlow,
    NavPoint,
    NoSolution,
    ValuationError,
    breaches,
    dpi,
    moic,
    nav_per_unit,
    real_moic,
    real_xirr,
    rvpi,
    tvpi,
    valuation_drift,
    xirr,
)

__all__ = [
    "AmbiguousAmount", "BasisMismatch", "CurrencyMismatch", "FxRate", "Money",
    "MoneyError", "convert", "parse_amount", "parse_en", "parse_tr",
    "PriceIndex", "bundled_index", "monetary_gain_loss", "purchasing_power_loss",
    "real_return", "restate",
    "DueObligation", "Obligation", "ObligationCalendar", "business_days_after",
    "business_days_between", "is_business_day",
    "CashFlow", "NavPoint", "NoSolution", "ValuationError", "breaches", "dpi",
    "moic", "nav_per_unit", "real_moic", "real_xirr", "rvpi", "tvpi",
    "valuation_drift", "xirr",
]
