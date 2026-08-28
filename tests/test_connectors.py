"""Tests for the regulatory and market-data connectors.

No network, ever — and in this environment that is not a testing convention but
the actual condition: every host these connectors name answers 403 at the egress
gateway. So the behaviour under test is mostly what happens when the fetch does
NOT work, which is the behaviour that will actually run.
"""

from __future__ import annotations

import json
import unittest
from decimal import Decimal
from typing import Any

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.marketdata import (
    BUNDLED_AS_OF,
    Series,
    SeriesPoint,
    TcmbEvdsConnector,
    TuikCpiConnector,
    _parse_points,
    bundled_price_index,
)
from oodarag.ingest.regulatory import (
    Budget,
    KapConnector,
    RegulatoryConnector,
    ResmiGazeteConnector,
    SpkConnector,
    TspbConnector,
    default_connectors,
    extract_published,
)
from oodarag.util.http import TransportError


class BlockedClient:
    """What this environment actually does: refuse at CONNECT.

    Carries the attributes the crawler reads off a client, so the test exercises
    the real path — an over-thin fake would fail with AttributeError and prove
    only that the fake was thin.
    """

    user_agent = "oodarag-test"

    def get(self, url: str, **kw: Any) -> Any:
        raise TransportError("gateway answered 403 to CONNECT (policy denial)")

    def head(self, url: str, **kw: Any) -> Any:
        raise TransportError("gateway answered 403 to CONNECT (policy denial)")


class BrokenJsonClient:
    user_agent = "oodarag-test"

    def get(self, url: str, **kw: Any) -> Any:
        class R:
            text = "<html>not json at all</html>"
        return R()


class FakeJsonClient:
    user_agent = "oodarag-test"

    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def get(self, url: str, **kw: Any) -> Any:
        payload = self.payload

        class R:
            text = json.dumps(payload)
        return R()


class TestDateExtraction(unittest.TestCase):
    def test_turkish_long_form(self) -> None:
        self.assertEqual(extract_published("23 Temmuz 2026 tarihli karar"), "2026-07-23")
        self.assertEqual(extract_published("1 Ocak 2027"), "2027-01-01")

    def test_dotted_and_slashed(self) -> None:
        self.assertEqual(extract_published("31.07.2026 tarihine kadar"), "2026-07-31")
        self.assertEqual(extract_published("23/07/2026"), "2026-07-23")

    def test_iso(self) -> None:
        self.assertEqual(extract_published("published 2026-07-23"), "2026-07-23")

    def test_long_form_wins_over_a_later_number(self) -> None:
        """'23 Temmuz 2026 ... 45/1359' must not yield a date from the decision no."""
        self.assertEqual(extract_published("23 Temmuz 2026 karar 45/1359"), "2026-07-23")

    def test_no_date_returns_empty_not_a_guess(self) -> None:
        self.assertEqual(extract_published("no date here at all"), "")


class TestRegulatoryConnectors(unittest.TestCase):
    def test_blocked_host_yields_nothing_and_does_not_raise(self) -> None:
        """The behaviour that actually runs here. A 403 must cost one warning,
        not the whole OODA cycle."""
        c = SpkConnector(client=BlockedClient())
        result = c.run(MemoryStateStore())
        self.assertEqual(result.documents, [])
        self.assertGreaterEqual(c.failures, 1)
        # The crawler swallows per-URL transport errors, so the failure verdict
        # has to come from the crawl report. If this ever passes with failures
        # at 0, a dead source has become indistinguishable from a quiet one and
        # CONNECTOR-DOWN will never fire.
        self.assertTrue(c.last_error)

    def test_consecutive_failures_accumulate_for_the_policy_rule(self) -> None:
        c = SpkConnector(client=BlockedClient())
        store = MemoryStateStore()
        for _ in range(3):
            c.run(store)
        self.assertGreaterEqual(c.failures, 3)
        self.assertEqual(store.get(c.key)["failures"], c.failures)

    def test_every_source_is_wired_with_an_authority(self) -> None:
        conns = default_connectors(["VPG", "VBR"])
        keys = [c.key for c in conns]
        self.assertEqual(keys, ["resmigazete", "spk", "kap", "tspb"])
        # The Official Gazette outranks everything: it is where a rule becomes law.
        self.assertEqual(max(conns, key=lambda c: c.authority).key, "resmigazete")

    def test_kap_refuses_an_empty_watchlist(self) -> None:
        """Without one it would index every disclosure in Turkey."""
        with self.assertRaises(ValueError):
            KapConnector([])
        with self.assertRaises(ValueError):
            KapConnector(["", "  "])

    def test_kap_relevance_matches_only_the_watchlist(self) -> None:
        c = KapConnector(["VBR", "vik"])
        self.assertTrue(c.is_relevant("VBR fon bildirimi", "body"))
        self.assertTrue(c.is_relevant("x", "kod VIK için"))
        self.assertFalse(c.is_relevant("AKBNK bildirimi", "unrelated issuer"))

    def test_keyword_filter_is_narrow(self) -> None:
        c = ResmiGazeteConnector()
        self.assertTrue(c.is_relevant("Tebliğ", "girişim sermayesi yatırım fonu esasları"))
        self.assertFalse(c.is_relevant("Atama Kararı", "bir vali atanmıştır"))

    def test_no_keywords_means_take_everything(self) -> None:
        c = RegulatoryConnector(key="k", seeds=["https://x/"], authority=0.5)
        self.assertTrue(c.is_relevant("anything", "at all"))

    def test_redactor_is_applied_at_the_boundary(self) -> None:
        seen: list[str] = []

        def redactor(text: str) -> str:
            seen.append(text)
            return "REDACTED"

        c = TspbConnector(client=BlockedClient(), redactor=redactor)
        c.run(MemoryStateStore())          # blocked, so nothing to redact
        self.assertEqual(seen, [])
        self.assertIs(c.redactor, redactor)

    def test_budget_is_always_bounded(self) -> None:
        b = Budget()
        opts = b.as_crawl_options()
        for field in ("max_pages", "max_fetches", "max_depth", "max_seconds"):
            self.assertGreater(opts[field], 0, field)
        # Every key must be one CrawlConfig actually accepts: an invented one
        # turns a degrade-gracefully connector into a TypeError at first fetch.
        from dataclasses import fields as dc_fields

        from oodarag.scrape.crawler import CrawlConfig
        known = {f.name for f in dc_fields(CrawlConfig)}
        self.assertLessEqual(set(opts), known)


class TestMarketData(unittest.TestCase):
    def test_no_client_falls_back_and_says_so(self) -> None:
        c = TuikCpiConnector()
        s = c.series("TUFE")
        self.assertTrue(s.is_bundled)
        self.assertTrue(c.downgraded)
        self.assertIn("NOT-LIVE", s.name)

    def test_blocked_host_falls_back_rather_than_raising(self) -> None:
        c = TuikCpiConnector(client=BlockedClient())
        s = c.series("TUFE")
        self.assertTrue(s.is_bundled)
        self.assertGreaterEqual(c.failures, 1)

    def test_unparseable_response_falls_back_rather_than_guessing(self) -> None:
        c = TuikCpiConnector(client=BrokenJsonClient())
        self.assertTrue(c.series("TUFE").is_bundled)

    def test_a_recognisable_response_is_used_and_marked_live(self) -> None:
        payload = {"items": [{"Tarih": "2026-06", "TP_FE_OKTG01": "127.35"},
                             {"Tarih": "2026-07", "TP_FE_OKTG01": "131.75"}]}
        c = TuikCpiConnector(client=FakeJsonClient(payload))
        s = c.series("TUFE")
        self.assertFalse(s.is_bundled)
        self.assertFalse(c.downgraded)
        self.assertEqual(s.latest.period, "2026-07")
        self.assertEqual(s.latest.value, Decimal("131.75"))
        self.assertTrue(s.latest.trustworthy)

    def test_tcmb_without_a_key_falls_back(self) -> None:
        c = TcmbEvdsConnector(client=FakeJsonClient({"items": []}), api_key="")
        s = c.series("USDTRY")
        self.assertTrue(s.is_bundled)
        self.assertIn("47.20", str(s.latest.value))

    def test_tcmb_rejects_an_unknown_series(self) -> None:
        with self.assertRaises(KeyError):
            TcmbEvdsConnector().series("GOLD")

    def test_a_partly_bundled_series_counts_as_bundled(self) -> None:
        """The dangerous shape: live history, stale tip. `all()` would call it live."""
        s = Series(name="mix", points=[
            SeriesPoint("2026-06", Decimal("1"), "u", "live"),
            SeriesPoint("2026-07", Decimal("2"), "u", "bundled"),
        ])
        self.assertTrue(s.is_bundled)

    def test_bundled_series_is_named_so_it_cannot_be_mistaken(self) -> None:
        s = bundled_price_index()
        self.assertIn("NOT-LIVE", s.name)
        self.assertEqual(s.as_of, BUNDLED_AS_OF)
        self.assertTrue(all(p.provenance == "bundled" for p in s))
        self.assertFalse(any(p.trustworthy for p in s))

    def test_bundled_index_feeds_the_domain_price_index(self) -> None:
        from oodarag.domain.inflation import PriceIndex
        idx = PriceIndex("t", bundled_price_index().as_index_dict())
        self.assertIn("2026-07", idx)
        factor, _ = idx.factor("2025-07", "2026-07")
        self.assertGreater(factor, 1)

    def test_parse_points_returns_nothing_on_an_unknown_shape(self) -> None:
        """Returning nothing routes to the fallback, which announces itself.
        Guessing would not."""
        self.assertEqual(_parse_points({"unexpected": "shape"}, "u"), [])
        self.assertEqual(_parse_points("not even a list", "u"), [])

    def test_parse_points_skips_bad_rows_without_dropping_good_ones(self) -> None:
        rows = [{"Tarih": "2026-07", "v": "131.75"},
                {"Tarih": "nonsense", "v": "1"},
                {"Tarih": "2026-06", "v": "not a number"},
                {"Tarih": "2026-05", "v": "-5"}]
        got = _parse_points(rows, "u")
        self.assertEqual([p.period for p in got], ["2026-07"])

    def test_connector_yields_one_document_per_series(self) -> None:
        c = TcmbEvdsConnector()
        docs = list(c.fetch({}))
        self.assertEqual(len(docs), 3)
        for d in docs:
            self.assertTrue(d.metadata["bundled"])
            self.assertIn("bundled", d.title)
            json.loads(d.text)   # the payload must be readable


if __name__ == "__main__":
    unittest.main()
