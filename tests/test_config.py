"""Tests for the firm configuration.

The interesting cases here are not "does it load a value". They are the ones
where a careless implementation would let an assumption pass itself off as a
fact, or let a malformed override look like a successful one.
"""

from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from oodarag.config import WAM, Fact, FirmProfile, FundRef, Thresholds, load


class TestDefaultProfile(unittest.TestCase):
    def test_fund_codes_are_the_real_watchlist(self) -> None:
        self.assertEqual(WAM.fund_codes, ("VBR", "VBI", "VIK", "WQQ"))
        # The company's own disclosure code has to be watched too: a change to
        # the manager's licence arrives under VPG, not under any fund.
        self.assertEqual(WAM.kap_watchlist[0], "VPG")
        self.assertIn("VBR", WAM.kap_watchlist)

    def test_fund_lookup_is_case_insensitive_and_total(self) -> None:
        self.assertIsNotNone(WAM.fund("vbr"))
        self.assertIsNotNone(WAM.fund("  VIK "))
        self.assertIsNone(WAM.fund("NOPE"))

    def test_fund_kinds_split_correctly(self) -> None:
        self.assertTrue(WAM.fund("VBR").is_venture)
        self.assertTrue(WAM.fund("VIK").is_real_estate)
        self.assertFalse(WAM.fund("VBR").is_real_estate)

    def test_unrecovered_fund_is_unknown_not_guessed(self) -> None:
        """WQQ's registered title was never recovered.

        A press summary called it technology-focused, which makes GSYF the
        likely kind — and that is exactly the inference this codebase must not
        quietly bake in. Anything keyed on kind has to meet the gap instead.
        """
        wqq = WAM.fund("WQQ")
        self.assertEqual(wqq.kind, "UNKNOWN")
        self.assertFalse(wqq.is_venture)
        self.assertFalse(wqq.is_real_estate)
        self.assertEqual(wqq.grade, "ASSUMED")

    def test_sourced_facts_carry_a_ledger_id(self) -> None:
        for name in ("legal_name", "short_name", "kap_company_code", "city"):
            fact = getattr(WAM, name)
            if fact.grade == "SOURCED":
                self.assertTrue(fact.source, f"{name} claims SOURCED with no source id")

    def test_assumed_facts_are_not_trustworthy(self) -> None:
        self.assertFalse(WAM.base_currency.trustworthy)
        self.assertTrue(WAM.legal_name.trustworthy)

    def test_authority_order_puts_the_gazette_top(self) -> None:
        """A deadline cited to a blog is wrong even when the blog is right."""
        auth = WAM.authority_map
        self.assertEqual(max(auth, key=auth.get), "resmigazete")
        self.assertGreater(auth["spk"], auth["tspb"])

    def test_provenance_report_names_the_unconfirmed_fields(self) -> None:
        report = WAM.provenance_report()
        self.assertIn("ASSUMED", report)
        self.assertIn("base_currency", report)
        self.assertIn("WQQ", report)
        # The hard gap must be stated, not implied by absence.
        self.assertIn("U-7", report)
        self.assertIn("fund sizes", report.lower())

    def test_profile_has_no_field_inviting_a_fund_size_guess(self) -> None:
        """Fund sizes were not establishable, so there is nowhere to put one."""
        fields = set(FundRef.__dataclass_fields__)
        for forbidden in ("size", "aum", "nav", "units", "commitments"):
            self.assertNotIn(forbidden, fields)


class TestOverride(unittest.TestCase):
    def _write(self, body: str) -> Path:
        d = Path(tempfile.mkdtemp())
        p = d / "firm.toml"
        p.write_text(body, encoding="utf-8")
        return p

    def test_owner_outranks_sourced(self) -> None:
        p = self._write('legal_name = "Corrected Legal Name A.Ş."\n')
        got = load(p)
        self.assertEqual(got.legal_name.value, "Corrected Legal Name A.Ş.")
        self.assertEqual(got.legal_name.grade, "OWNER")
        self.assertTrue(got.legal_name.trustworthy)

    def test_missing_file_is_a_noop_not_a_crash(self) -> None:
        """An absent optional override must not stop the system starting."""
        got = load("/nonexistent/firm.toml")
        self.assertIs(got, WAM)

    def test_malformed_file_is_a_noop_not_a_crash(self) -> None:
        p = self._write("this is not = = toml [[[\n")
        self.assertIs(load(p), WAM)

    def test_fund_merge_corrects_one_without_restating_the_rest(self) -> None:
        p = self._write(
            '[[funds]]\n'
            'code = "WQQ"\n'
            'name_tr = "WAM ... İkinci Girişim Sermayesi Yatırım Fonu"\n'
            'kind = "GSYF"\n'
        )
        got = load(p)
        self.assertEqual(got.fund_codes, ("VBR", "VBI", "VIK", "WQQ"))
        wqq = got.fund("WQQ")
        self.assertEqual(wqq.kind, "GSYF")
        self.assertEqual(wqq.grade, "OWNER")
        # The untouched funds keep their original grading.
        self.assertEqual(got.fund("VBR").grade, "SOURCED")

    def test_new_fund_is_appended(self) -> None:
        p = self._write('[[funds]]\ncode = "vzz"\nkind = "GYF"\nname_tr = "Üçüncü"\n')
        got = load(p)
        self.assertIn("VZZ", got.fund_codes)  # upper-cased on the way in
        self.assertEqual(got.fund("VZZ").kind, "GYF")

    def test_unrecognised_fund_kind_becomes_unknown_not_an_error(self) -> None:
        p = self._write('[[funds]]\ncode = "VBR"\nkind = "HEDGE"\nname_tr = "x"\n')
        self.assertEqual(load(p).fund("VBR").kind, "UNKNOWN")

    def test_fund_entry_without_a_code_is_dropped(self) -> None:
        p = self._write('[[funds]]\nname_tr = "no code here"\n')
        self.assertEqual(load(p).fund_codes, WAM.fund_codes)

    def test_thresholds_read_as_decimal_not_float(self) -> None:
        """A threshold is compared against money, so it must not be a float.

        TOML has no decimal type. Reading 0.03 as a float and comparing it to a
        Decimal raises, or worse, compares against 0.029999999999999998.
        """
        p = self._write('[thresholds]\nvaluation_drift_real = "0.03"\n')
        t = load(p).thresholds
        self.assertIsInstance(t.valuation_drift_real, Decimal)
        self.assertEqual(t.valuation_drift_real, Decimal("0.03"))
        # Untouched thresholds survive.
        self.assertEqual(t.deadline_horizon_days, Thresholds().deadline_horizon_days)

    def test_integer_threshold_stays_integer(self) -> None:
        p = self._write("[thresholds]\ndeadline_horizon_days = 30\n")
        t = load(p).thresholds
        self.assertIsInstance(t.deadline_horizon_days, int)
        self.assertEqual(t.deadline_horizon_days, 30)

    def test_unparseable_threshold_is_ignored_not_defaulted_to_zero(self) -> None:
        """Silently becoming 0.0 would make the rule fire on every observation."""
        p = self._write('[thresholds]\nvaluation_drift_real = "not a number"\n')
        t = load(p).thresholds
        self.assertEqual(t.valuation_drift_real, Thresholds().valuation_drift_real)

    def test_typo_in_a_threshold_name_does_not_read_as_configured(self) -> None:
        p = self._write('[thresholds]\nvaluation_drift_reel = "0.01"\n')
        t = load(p).thresholds
        self.assertEqual(t.valuation_drift_real, Thresholds().valuation_drift_real)

    def test_empty_override_returns_the_base_unchanged(self) -> None:
        p = self._write("# nothing here\n")
        self.assertIs(load(p), WAM)

    def test_base_profile_is_not_mutated_by_an_override(self) -> None:
        p = self._write('legal_name = "Something Else"\n')
        load(p)
        self.assertEqual(
            WAM.legal_name.value,
            "WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi A.Ş.",
        )


class TestThresholdDefaults(unittest.TestCase):
    def test_real_drift_is_tighter_than_nominal(self) -> None:
        """At ~32% inflation, a nominal move the size of the real threshold is
        noise. If these were ever inverted the rule would fire monthly."""
        t = Thresholds()
        self.assertLess(t.valuation_drift_real, t.valuation_drift_nominal)

    def test_escalation_window_sits_inside_the_horizon(self) -> None:
        t = Thresholds()
        self.assertLess(t.deadline_escalate_days, t.deadline_horizon_days)

    def test_money_thresholds_are_decimal(self) -> None:
        t = Thresholds()
        for name in ("valuation_drift_real", "valuation_drift_nominal", "fx_daily_move"):
            self.assertIsInstance(getattr(t, name), Decimal, name)


class TestFactAndProfileShape(unittest.TestCase):
    def test_fact_interpolates_as_its_value(self) -> None:
        self.assertEqual(f"{Fact('x', 'OWNER')}", "x")

    def test_profile_is_frozen(self) -> None:
        with self.assertRaises(Exception):
            WAM.legal_name = Fact("nope", "OWNER")  # type: ignore[misc]

    def test_empty_company_code_still_yields_fund_watchlist(self) -> None:
        p = FirmProfile(
            legal_name=Fact("x", "OWNER"),
            short_name=Fact("x", "OWNER"),
            kap_company_code=Fact("", "ASSUMED"),
            city=Fact("x", "OWNER"),
            base_currency=Fact("TRY", "OWNER"),
            auditor=Fact("x", "OWNER"),
            funds=(FundRef("AAA", "a", "GSYF"),),
        )
        self.assertEqual(p.kap_watchlist, ("AAA",))


if __name__ == "__main__":
    unittest.main()
