"""Tests for the deterministic core.

Weighted deliberately towards the failure cases. A guard is only real once you
have watched it reject something, and every test here that asserts a raise is
asserting that a specific class of silently-wrong number cannot be produced.
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from oodarag.domain import (
    AmbiguousAmount,
    BasisMismatch,
    CashFlow,
    CurrencyMismatch,
    FxRate,
    Money,
    MoneyError,
    NavPoint,
    NoSolution,
    ObligationCalendar,
    PriceIndex,
    bundled_index,
    business_days_after,
    business_days_between,
    convert,
    is_business_day,
    monetary_gain_loss,
    moic,
    nav_per_unit,
    parse_amount,
    parse_en,
    parse_tr,
    real_moic,
    real_return,
    restate,
    valuation_drift,
    xirr,
)
from oodarag.domain.inflation import IndexError_, naive_real_return
from oodarag.domain.obligations import Obligation

D = Decimal


class TestTurkishParsing(unittest.TestCase):
    """The 1000x bug. float('1.500') is 1.5; in Turkish it is one thousand five
    hundred, and it appears in capital-call notices."""

    def test_turkish_grouping(self) -> None:
        self.assertEqual(parse_tr("1.234.567,89"), D("1234567.89"))
        self.assertEqual(parse_tr("1.500"), D("1500"))
        self.assertEqual(parse_tr("0,05"), D("0.05"))

    def test_english_grouping(self) -> None:
        self.assertEqual(parse_en("1,234,567.89"), D("1234567.89"))
        self.assertEqual(parse_en("1.500"), D("1.5"))

    def test_the_two_conventions_disagree_by_a_thousand(self) -> None:
        self.assertEqual(parse_tr("1.500") / parse_en("1.500"), D("1000"))

    def test_auto_refuses_the_ambiguous_case(self) -> None:
        for text in ("1.500", "1,500", "12.345"):
            with self.assertRaises(AmbiguousAmount, msg=text):
                parse_amount(text)

    def test_auto_accepts_what_is_unambiguous(self) -> None:
        self.assertEqual(parse_amount("1.234.567,89"), D("1234567.89"))
        self.assertEqual(parse_amount("1,234,567.89"), D("1234567.89"))
        self.assertEqual(parse_amount("1.234.567"), D("1234567"))
        self.assertEqual(parse_amount("1,25"), D("1.25"))
        self.assertEqual(parse_amount("1500"), D("1500"))

    def test_explicit_locale_always_wins(self) -> None:
        self.assertEqual(parse_amount("1.500", "tr"), D("1500"))
        self.assertEqual(parse_amount("1.500", "en"), D("1.5"))

    def test_currency_symbols_and_spaces_are_stripped(self) -> None:
        self.assertEqual(parse_tr("₺ 1.500,00"), D("1500.00"))
        self.assertEqual(parse_tr("1.500,00 TL"), D("1500.00"))

    def test_negatives(self) -> None:
        self.assertEqual(parse_tr("-1.500,50"), D("-1500.50"))

    def test_garbage_raises(self) -> None:
        for text in ("", "   ", "abc", "1,2,3.4.5"):
            with self.assertRaises(MoneyError, msg=text):
                parse_tr(text)


class TestMoneyInvariants(unittest.TestCase):
    def test_floats_are_refused_at_construction(self) -> None:
        with self.assertRaises(MoneyError):
            Money(1.5, "TRY")  # type: ignore[arg-type]

    def test_nominal_plus_restated_is_refused(self) -> None:
        """The single highest-value correctness invariant in the system.

        Funds are TMS 29 exempt; the management company is not. Adding the two
        at 31.75% CPI is wrong by roughly a third per year of divergence.
        """
        fund = Money(D("1000"), "TRY")
        company = Money(D("1000"), "TRY", "restated", "2026-07")
        with self.assertRaises(BasisMismatch):
            fund + company

    def test_restated_to_different_periods_is_refused(self) -> None:
        a = Money(D("1"), "TRY", "restated", "2026-06")
        b = Money(D("1"), "TRY", "restated", "2026-07")
        with self.assertRaises(BasisMismatch):
            a + b

    def test_same_basis_adds_normally(self) -> None:
        a = Money(D("1000"), "TRY", "restated", "2026-07")
        b = Money(D("500"), "TRY", "restated", "2026-07")
        self.assertEqual((a + b).amount, D("1500"))

    def test_currency_mix_is_refused(self) -> None:
        with self.assertRaises(CurrencyMismatch):
            Money(D("1"), "TRY") + Money(D("1"), "USD")

    def test_restated_amount_must_carry_a_period(self) -> None:
        with self.assertRaises(MoneyError):
            Money(D("1"), "TRY", "restated")

    def test_nominal_amount_must_not_carry_a_period(self) -> None:
        """A period on an unadjusted figure reads as though it were adjusted."""
        with self.assertRaises(MoneyError):
            Money(D("1"), "TRY", "nominal", "2026-07")

    def test_ratio_is_basis_checked_too(self) -> None:
        with self.assertRaises(BasisMismatch):
            Money(D("2"), "TRY").ratio(Money(D("1"), "TRY", "restated", "2026-07"))

    def test_turkish_formatting(self) -> None:
        self.assertEqual(Money(D("1234567.891"), "TRY").format_tr(), "1.234.567,89 TRY")
        self.assertEqual(Money(D("-1500"), "TRY").format_tr(0), "-1.500 TRY")

    def test_rounding_is_half_up_not_bankers(self) -> None:
        """Python's round(2.675, 2) is 2.67. Turkish accounting expects 2.68."""
        self.assertEqual(Money(D("2.675"), "TRY").quantize(2).amount, D("2.68"))
        self.assertEqual(Money(D("2.665"), "TRY").quantize(2).amount, D("2.67"))

    def test_basis_label_is_always_available(self) -> None:
        self.assertEqual(Money(D("1"), "TRY").basis_label, "nominal")
        self.assertEqual(Money(D("1"), "TRY", "restated", "2026-07").basis_label,
                         "restated to 2026-07")

    def test_conversion_preserves_basis_and_period(self) -> None:
        amount = Money(D("100"), "USD", "restated", "2026-07")
        rate = FxRate("USD", "TRY", D("47.2"), "2026-07-31", "tcmb")
        got = convert(amount, rate)
        self.assertEqual(got.currency, "TRY")
        self.assertEqual(got.amount, D("4720.0"))
        self.assertEqual(got.basis, "restated")
        self.assertEqual(got.period, "2026-07")

    def test_conversion_inverts_when_needed(self) -> None:
        rate = FxRate("USD", "TRY", D("47.2"), "2026-07-31")
        got = convert(Money(D("4720"), "TRY"), rate)
        self.assertEqual(got.currency, "USD")
        self.assertAlmostEqual(float(got.amount), 100.0, places=6)

    def test_unrelated_rate_is_refused(self) -> None:
        with self.assertRaises(CurrencyMismatch):
            convert(Money(D("1"), "EUR"), FxRate("USD", "TRY", D("47.2"), "2026-07-31"))


class TestInflation(unittest.TestCase):
    def setUp(self) -> None:
        self.idx = bundled_index()

    def test_fisher_not_subtraction(self) -> None:
        real = real_return(D("0.40"), D("0.32"))
        naive = naive_real_return(D("0.40"), D("0.32"))
        self.assertAlmostEqual(float(real), 0.060606, places=5)
        self.assertEqual(naive, D("0.08"))
        # The naive answer overstates by roughly a third of the true answer.
        self.assertGreater(float(naive - real) / float(real), 0.30)

    def test_the_error_grows_with_inflation(self) -> None:
        small = naive_real_return(D("0.05"), D("0.02")) - real_return(D("0.05"), D("0.02"))
        large = naive_real_return(D("0.40"), D("0.32")) - real_return(D("0.40"), D("0.32"))
        self.assertGreater(large, small * 10)

    def test_nominal_gain_can_be_a_real_loss(self) -> None:
        self.assertLess(real_return(D("0.30"), D("0.3175")), 0)

    def test_restatement_uses_the_index_ratio(self) -> None:
        got = restate(Money(D("10000000"), "TRY"), "2026-07", self.idx, "2025-07")
        self.assertEqual(got.basis, "restated")
        self.assertEqual(got.period, "2026-07")
        self.assertEqual(got.amount, D("13175000.00"))

    def test_restating_a_nominal_amount_needs_a_from_period(self) -> None:
        with self.assertRaises(MoneyError):
            restate(Money(D("1"), "TRY"), "2026-07", self.idx)

    def test_restated_amount_re_restates_from_its_own_period(self) -> None:
        once = restate(Money(D("100"), "TRY"), "2026-01", self.idx, "2025-07")
        twice = restate(once, "2026-07", self.idx)
        direct = restate(Money(D("100"), "TRY"), "2026-07", self.idx, "2025-07")
        self.assertAlmostEqual(float(twice.amount), float(direct.amount), places=6)

    def test_missing_period_refuses_rather_than_interpolating(self) -> None:
        """A fabricated index point makes a fabricated restated figure that is
        indistinguishable from a real one."""
        with self.assertRaises(IndexError_) as ctx:
            self.idx.point("2020-01")
        self.assertIn("not be interpolated", str(ctx.exception))

    def test_index_rejects_bad_input(self) -> None:
        idx = PriceIndex("t")
        with self.assertRaises(IndexError_):
            idx.add("2026-13", "100")
        with self.assertRaises(IndexError_):
            idx.add("2026-01", "-5")

    def test_provisional_flag_propagates(self) -> None:
        idx = PriceIndex("t", {"2026-01": "100", "2026-02": "110"},
                         provisional={"2026-02"})
        _, provisional = idx.factor("2026-01", "2026-02")
        self.assertTrue(provisional)

    def test_bundled_index_is_named_as_not_live(self) -> None:
        """Nobody should be able to mistake the fixture for TÜİK data."""
        self.assertIn("NOT-LIVE", self.idx.name)

    def test_monetary_position_gain_for_a_net_borrower(self) -> None:
        """A net monetary liability gains purchasing power in inflation."""
        liability = Money(D("-1000000"), "TRY")
        got = monetary_gain_loss(liability, "2025-07", "2026-07", self.idx)
        self.assertGreater(got.amount, 0)
        self.assertEqual(got.basis, "restated")


class TestValuation(unittest.TestCase):
    def setUp(self) -> None:
        self.idx = bundled_index()

    def test_xirr_on_a_simple_doubling(self) -> None:
        flows = [CashFlow(date(2025, 1, 1), Money(D("-100"), "TRY")),
                 CashFlow(date(2026, 1, 1), Money(D("200"), "TRY"))]
        self.assertAlmostEqual(float(xirr(flows)), 1.0, places=3)

    def test_xirr_needs_a_sign_change(self) -> None:
        flows = [CashFlow(date(2025, 1, 1), Money(D("-100"), "TRY")),
                 CashFlow(date(2026, 1, 1), Money(D("-50"), "TRY"))]
        with self.assertRaises(NoSolution):
            xirr(flows)

    def test_xirr_refuses_mixed_bases(self) -> None:
        flows = [CashFlow(date(2025, 1, 1), Money(D("-100"), "TRY")),
                 CashFlow(date(2026, 1, 1), Money(D("200"), "TRY", "restated", "2026-01"))]
        with self.assertRaises(Exception):
            xirr(flows)

    def test_a_strong_nominal_multiple_can_be_a_real_loss(self) -> None:
        """The headline result of this whole module."""
        paid = Money(D("1000000"), "TRY")
        dist = Money(D("1250000"), "TRY")
        residual = Money(D("0"), "TRY")
        self.assertEqual(moic(dist, residual, paid), D("1.25"))
        real = real_moic(dist, residual, paid,
                         paid_in_period="2025-07", to_period="2026-07", index=self.idx)
        self.assertLess(real, 1)

    def test_moic_with_no_paid_in_is_undefined_not_infinite(self) -> None:
        with self.assertRaises(Exception):
            moic(Money(D("1"), "TRY"), Money(D("0"), "TRY"), Money(D("0"), "TRY"))

    def test_nav_per_unit_preserves_basis(self) -> None:
        got = nav_per_unit(Money(D("1000"), "TRY", "restated", "2026-07"), D("10"))
        self.assertEqual(got.amount, D("100"))
        self.assertEqual(got.period, "2026-07")

    def test_drift_reports_nominal_and_real_separately(self) -> None:
        prev = NavPoint("VIK", date(2025, 7, 31), Money(D("100"), "TRY"))
        cur = NavPoint("VIK", date(2026, 7, 31), Money(D("104"), "TRY"))
        drift = valuation_drift(prev, cur, self.idx)
        self.assertAlmostEqual(float(drift["nominal_move"]), 0.04, places=6)
        self.assertLess(drift["real_move"], 0)  # up nominally, down in real terms

    def test_drift_without_an_index_still_gives_the_nominal_move(self) -> None:
        prev = NavPoint("VIK", date(2025, 7, 31), Money(D("100"), "TRY"))
        cur = NavPoint("VIK", date(2026, 7, 31), Money(D("104"), "TRY"))
        drift = valuation_drift(prev, cur, None)
        self.assertIsNotNone(drift["nominal_move"])
        self.assertIsNone(drift["real_move"])

    def test_drift_refuses_to_compare_different_funds(self) -> None:
        a = NavPoint("VBR", date(2025, 7, 31), Money(D("100"), "TRY"))
        b = NavPoint("VIK", date(2026, 7, 31), Money(D("104"), "TRY"))
        with self.assertRaises(Exception):
            valuation_drift(a, b, self.idx)


class TestBusinessDays(unittest.TestCase):
    def test_weekends_are_not_business_days(self) -> None:
        self.assertFalse(is_business_day(date(2026, 8, 29)))  # Saturday
        self.assertFalse(is_business_day(date(2026, 8, 30)))  # Sunday, and Zafer Bayramı
        self.assertTrue(is_business_day(date(2026, 8, 27)))   # Thursday

    def test_fixed_turkish_holidays_are_excluded(self) -> None:
        for d in (date(2026, 4, 23), date(2026, 5, 1), date(2026, 5, 19),
                  date(2026, 7, 15), date(2026, 8, 30), date(2026, 10, 29),
                  date(2026, 1, 1)):
            self.assertFalse(is_business_day(d), d.isoformat())

    def test_counting_forward_skips_non_business_days(self) -> None:
        # Thu 27 Aug 2026 + 3 business days: Fri 28, Mon 31, Tue 1 Sep.
        self.assertEqual(business_days_after(date(2026, 8, 27), 3), date(2026, 9, 1))

    def test_counting_is_symmetric(self) -> None:
        start, n = date(2026, 8, 27), 6
        end = business_days_after(start, n)
        self.assertEqual(business_days_between(start, end), n)
        self.assertEqual(business_days_between(end, start), -n)

    def test_zero_days_is_the_same_day(self) -> None:
        self.assertEqual(business_days_after(date(2026, 8, 27), 0), date(2026, 8, 27))


class TestObligationCalendar(unittest.TestCase):
    def test_seed_loads_and_everything_is_unverified(self) -> None:
        """The seed is research, not law. If this ever passes with verified
        obligations, someone has marked a guess as a legal deadline."""
        cal = ObligationCalendar.from_seed()
        self.assertGreater(len(cal.obligations), 20)
        self.assertEqual(len(cal.unverified), len(cal.obligations))

    def test_unverified_obligations_say_so_in_their_label(self) -> None:
        cal = ObligationCalendar.from_seed()
        any_ob = next(iter(cal.obligations.values()))
        self.assertIn("UNVERIFIED", any_ob.label)

    def test_verifying_flips_the_flag_and_records_who(self) -> None:
        cal = ObligationCalendar.from_seed()
        oid = next(iter(cal.obligations))
        cal.verify(oid, by="compliance officer", evidence_uri="https://spk.gov.tr/x")
        self.assertTrue(cal.obligations[oid].verified)
        self.assertIn("compliance officer", cal.obligations[oid].notes)
        self.assertNotIn("UNVERIFIED", cal.obligations[oid].label)

    def test_due_within_excludes_satisfied(self) -> None:
        cal = ObligationCalendar.from_seed()
        oid = next(iter(cal.obligations))
        today = date(2026, 8, 27)
        cal.set_due(oid, today + __import__("datetime").timedelta(days=5))
        self.assertEqual(len(cal.due_within(21, today)), 1)
        cal.satisfy(oid, today, "file://evidence.pdf")
        self.assertEqual(len(cal.due_within(21, today)), 0)

    def test_undated_obligations_are_reported_as_gaps_not_silence(self) -> None:
        cal = ObligationCalendar.from_seed()
        self.assertEqual(len(cal.unscheduled()), len(cal.obligations))

    def test_applicability_predicate_can_exclude(self) -> None:
        cal = ObligationCalendar()
        cal.add(Obligation(
            id="it-audit", authority="SPK", title_tr="", title_en="IS audit",
            cadence="event_driven", due_rule="every 2 years above TRY 5m equity",
            applies_if=lambda ctx: ctx.get("equity", 0) > 5_000_000,
        ))
        self.assertEqual(len(cal.unscheduled({"equity": 10_000_000})), 1)
        self.assertEqual(len(cal.unscheduled({"equity": 1_000_000})), 0)

    def test_a_broken_predicate_shows_the_obligation_rather_than_hiding_it(self) -> None:
        cal = ObligationCalendar()
        cal.add(Obligation(
            id="boom", authority="SPK", title_tr="", title_en="x",
            cadence="annual", due_rule="",
            applies_if=lambda ctx: 1 / 0,  # type: ignore[misc]
        ))
        self.assertEqual(len(cal.unscheduled({})), 1)

    def test_missing_seed_file_gives_an_empty_calendar_not_a_crash(self) -> None:
        cal = ObligationCalendar.from_seed("/nonexistent/obligations.json")
        self.assertEqual(len(cal.obligations), 0)

    def test_round_trip_json(self) -> None:
        cal = ObligationCalendar.from_seed()
        import json
        data = json.loads(cal.to_json())
        self.assertEqual(len(data["obligations"]), len(cal.obligations))
        self.assertTrue(all(o["verified"] is False for o in data["obligations"]))


if __name__ == "__main__":
    unittest.main()
