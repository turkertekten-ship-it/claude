"""Money that refuses to be added to money on a different basis.

Two failure modes justify this module existing at all, and neither raises an
exception in ordinary Python.

**The 1000x parse.** In Turkish formatting ``1.234.567,89`` is one and a
quarter million. ``float("1.500")`` is ``1.5``. That is a factor-of-a-thousand
error, it is silent, and it sits directly in the path of capital-call notices
and appraisal reports. Worse, ``1.500`` is genuinely ambiguous out of context —
it is one and a half in English and one thousand five hundred in Turkish — so
the safe parser is the one that *refuses* rather than the one that picks.

**The basis mix.** SPK decision 16.02.2024 no. 11/255 exempts investment funds
from TMS 29, while the management company itself restates
[src:SPK-FUND-TMS29-EXEMPTION]. So a fund NAV and a company balance are
denominated in different money: one is nominal lira, the other is lira of a
stated purchasing power. At 31.75% inflation [src:TCMB-MACRO-2026-08], adding
them is wrong by roughly a third per year of divergence, in the direction that
flatters. Nothing in the type system of a plain ``Decimal`` stops that addition,
so :class:`Money` carries its basis and refuses.

Everything here is exact. ``float`` never touches an amount, and rounding is
ROUND_HALF_UP because Python's built-in ``round`` is banker's rounding —
``round(2.675, 2)`` is ``2.67`` where Turkish accounting expects ``2.68``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Literal

#: ``nominal`` — lira as they were on the day, unadjusted.
#: ``restated`` — lira of the purchasing power of :attr:`Money.period`, i.e.
#: TMS 29 / IAS 29 restated.
Basis = Literal["nominal", "restated"]

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class MoneyError(ValueError):
    """Base for every refusal in this module. Never raised for arithmetic that
    is merely inconvenient — only for arithmetic that would be wrong."""


class CurrencyMismatch(MoneyError):
    pass


class BasisMismatch(MoneyError):
    """Raised when nominal and restated amounts, or amounts restated to
    different periods, are combined.

    This is the exception the whole module exists to raise. If it fires in
    production it has just prevented a materially wrong number reaching a
    report — treat it as a finding, not a bug to be worked around with a cast.
    """


def _q(value: Decimal, scale: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)


@dataclass(slots=True, frozen=True)
class Money:
    """An exact amount, its currency, and the basis it is stated on.

    ``period`` is required when ``basis == "restated"`` and forbidden when it is
    ``"nominal"``: a restated figure without a stated purchasing-power date is
    meaningless, and a nominal one with a period invites the reader to think it
    has been adjusted when it has not.
    """

    amount: Decimal
    currency: str = "TRY"
    basis: Basis = "nominal"
    period: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise MoneyError(
                f"amount must be Decimal, got {type(self.amount).__name__}. "
                "Constructing Money from a float is how rounding error enters."
            )
        if not self.currency or len(self.currency) != 3 or not self.currency.isalpha():
            raise MoneyError(f"currency must be a 3-letter code, got {self.currency!r}")
        object.__setattr__(self, "currency", self.currency.upper())
        if self.basis == "restated":
            if not self.period:
                raise MoneyError("a restated amount must state the period it is restated to")
            if not _PERIOD_RE.match(self.period):
                raise MoneyError(f"period must be YYYY-MM, got {self.period!r}")
        elif self.period is not None:
            raise MoneyError(
                "a nominal amount must not carry a period; a period on an "
                "unadjusted figure reads as though it had been adjusted"
            )

    # -- construction ------------------------------------------------------

    @classmethod
    def try_(cls, amount: Decimal | int | str, **kw: object) -> Money:
        """Convenience constructor for lira. Accepts str/int, never float."""
        return cls(_to_decimal(amount), "TRY", **kw)  # type: ignore[arg-type]

    @classmethod
    def zero(cls, currency: str = "TRY", basis: Basis = "nominal",
             period: str | None = None) -> Money:
        return cls(Decimal(0), currency, basis, period)

    # -- arithmetic --------------------------------------------------------

    def _check(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(
                f"cannot combine {self.currency} and {other.currency} without an "
                "explicit FxRate: an implicit conversion has no traceable rate"
            )
        if self.basis != other.basis:
            raise BasisMismatch(
                f"cannot combine a {self.basis} amount with a {other.basis} one. "
                "Fund figures are nominal and management-company figures are TMS 29 "
                "restated; adding them silently is the single largest correctness "
                "risk in this system. Restate one side first."
            )
        if self.basis == "restated" and self.period != other.period:
            raise BasisMismatch(
                f"both amounts are restated but to different periods "
                f"({self.period} and {other.period}). Restate one to the other "
                "before combining."
            )

    def __add__(self, other: Money) -> Money:
        self._check(other)
        return replace(self, amount=self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        self._check(other)
        return replace(self, amount=self.amount - other.amount)

    def __neg__(self) -> Money:
        return replace(self, amount=-self.amount)

    def __mul__(self, factor: Decimal | int) -> Money:
        return replace(self, amount=self.amount * _to_decimal(factor))

    __rmul__ = __mul__

    def ratio(self, other: Money) -> Decimal:
        """Divide two amounts, returning a dimensionless Decimal.

        Basis-checked like addition: a nominal-over-restated ratio is a
        meaningless number that looks like a multiple.
        """
        self._check(other)
        if other.amount == 0:
            raise MoneyError("division by a zero amount")
        return self.amount / other.amount

    # -- presentation ------------------------------------------------------

    def quantize(self, scale: int = 2) -> Money:
        return replace(self, amount=_q(self.amount, scale))

    def format_tr(self, scale: int = 2) -> str:
        """Turkish presentation: ``1.234.567,89 TRY``."""
        q = _q(self.amount, scale)
        sign = "-" if q < 0 else ""
        whole, _, frac = f"{abs(q):.{scale}f}".partition(".")
        grouped = "{:,}".format(int(whole)).replace(",", ".")
        body = f"{grouped},{frac}" if scale else grouped
        return f"{sign}{body} {self.currency}"

    @property
    def basis_label(self) -> str:
        """Never print an amount without this. It is the whole invariant."""
        return "nominal" if self.basis == "nominal" else f"restated to {self.period}"

    def __str__(self) -> str:
        return f"{self.format_tr()} ({self.basis_label})"


def _to_decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool) or isinstance(value, float):
        raise MoneyError(
            f"refusing to build an exact amount from {type(value).__name__}; "
            "pass a str or Decimal"
        )
    if isinstance(value, int):
        return Decimal(value)
    try:
        return Decimal(value)
    except InvalidOperation as e:
        raise MoneyError(f"not a number: {value!r}") from e


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

class AmbiguousAmount(MoneyError):
    """The string could be read two ways with a 1000x difference between them.

    Raised rather than guessed. ``1.500`` is one and a half in English and one
    thousand five hundred in Turkish, and no amount of cleverness recovers the
    intent from the string alone — only the document's locale does.
    """


_CLEAN = re.compile(r"[^\d,.\-+]")


def parse_tr(text: str) -> Decimal:
    """Parse Turkish formatting: ``.`` groups thousands, ``,`` is the decimal."""
    return _parse(text, group=".", decimal_sep=",")


def parse_en(text: str) -> Decimal:
    """Parse Anglo formatting: ``,`` groups thousands, ``.`` is the decimal."""
    return _parse(text, group=",", decimal_sep=".")


def parse_amount(text: str, locale: Literal["tr", "en", "auto"] = "auto") -> Decimal:
    """Parse an amount, refusing rather than guessing when it is ambiguous.

    With ``locale="auto"`` a string is only accepted when its formatting is
    self-evident — both separators present, or a separator group that cannot be
    a decimal (``1.234.567``), or a fractional part of a length that only one
    convention produces. ``1.500`` and ``1,500`` are rejected, because reading
    either one wrongly is a 1000x error in a capital call.
    """
    if locale == "tr":
        return parse_tr(text)
    if locale == "en":
        return parse_en(text)

    s = _CLEAN.sub("", (text or "").strip())
    if not s:
        raise MoneyError(f"not a number: {text!r}")
    dots, commas = s.count("."), s.count(",")

    if dots and commas:
        # Whichever appears last is the decimal separator: 1.234,56 / 1,234.56
        return parse_tr(text) if s.rindex(",") > s.rindex(".") else parse_en(text)
    if dots == 0 and commas == 0:
        return _to_decimal(s)

    sep = "." if dots else ","
    parts = s.replace("-", "").replace("+", "").split(sep)
    tail = parts[-1]
    if len(parts) > 2:
        # Repeated separator can only be grouping: 1.234.567
        return _parse(text, group=sep, decimal_sep="," if sep == "." else ".")
    if len(tail) != 3:
        # A 3-digit tail is the ambiguous case; anything else is a decimal.
        return _parse(text, group="," if sep == "." else ".", decimal_sep=sep)
    raise AmbiguousAmount(
        f"{text!r} is ambiguous: as Turkish it is {parse_tr(text)}, as English "
        f"it is {parse_en(text)} — a 1000x difference. Pass locale='tr' or "
        "locale='en' from the document's own language; do not let this be guessed."
    )


def _parse(text: str, *, group: str, decimal_sep: str) -> Decimal:
    s = _CLEAN.sub("", (text or "").strip())
    if not s:
        raise MoneyError(f"not a number: {text!r}")
    negative = s.startswith("-") or (text or "").strip().startswith("(")
    s = s.lstrip("+-").replace(group, "")
    if s.count(decimal_sep) > 1:
        raise MoneyError(f"more than one decimal separator in {text!r}")
    s = s.replace(decimal_sep, ".")
    try:
        value = Decimal(s)
    except InvalidOperation as e:
        raise MoneyError(f"not a number: {text!r}") from e
    return -value if negative else value


# --------------------------------------------------------------------------
# FX
# --------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class FxRate:
    """A rate that remembers where it came from.

    A converted figure whose rate cannot be traced is not auditable, so the
    source and as-of date travel with the rate rather than being logged
    somewhere else and lost.
    """

    base: str
    quote: str
    rate: Decimal
    as_of: str
    source_uri: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.rate, Decimal):
            raise MoneyError("FxRate.rate must be Decimal")
        if self.rate <= 0:
            raise MoneyError(f"FxRate.rate must be positive, got {self.rate}")

    def invert(self) -> FxRate:
        return FxRate(self.quote, self.base, Decimal(1) / self.rate,
                      self.as_of, self.source_uri)


def convert(amount: Money, rate: FxRate) -> Money:
    """Convert, preserving basis and period.

    Conversion does not change what kind of money this is: a restated TRY amount
    converted at a rate is still restated, and still to the same period.
    """
    if amount.currency == rate.base:
        pass
    elif amount.currency == rate.quote:
        rate = rate.invert()
    else:
        raise CurrencyMismatch(
            f"rate {rate.base}/{rate.quote} does not apply to {amount.currency}"
        )
    return Money(amount.amount * rate.rate, rate.quote, amount.basis, amount.period)
