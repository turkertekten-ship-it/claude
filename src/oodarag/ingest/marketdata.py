"""TÜFE, FX and the policy rate — the numbers every real figure depends on.

Without a price index there is no real-terms twin, and without a real-terms twin
every number this system prints is nominal and therefore flattering at 31.75%
inflation. So this is not a peripheral feed; it is the input to the correctness
invariant.

Which makes the bundled fallback dangerous, and the design is built around that
danger. `evds2.tcmb.gov.tr` and `data.tuik.gov.tr` are both denied at this
environment's egress gateway [src:EGRESS-POLICY-DENIAL-2026-08-28], so with no
network the connectors fall back to a bundled series — and **a stale index used
as a live one is exactly how a wrong number reaches an investor report**.

Three defences, none of them optional:

- Every point carries `provenance`, either `"live"` or `"bundled"`, and
  `as_of`. Nothing downstream can read a value without also being able to read
  where it came from.
- `Series.is_bundled` is true if *any* point is bundled, not all of them. A
  series that is mostly live and quietly stale at the tip is the dangerous
  shape.
- The downgrade is logged at warning level every time it happens, with the
  reason. Silence would make the fallback invisible, and an invisible fallback
  is indistinguishable from working.

The bundled numbers are illustrative and are named as such. They are consistent
with the reported July 2026 readings [src:TCMB-MACRO-2026-08] — CPI 31.75% y/y,
policy rate 37%, USD/TRY about 47.2 — but they are not TÜİK's or the TCMB's
published series and must not be presented as them.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.http import HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger

log = get_logger("ingest.marketdata")

Provenance = Literal["live", "bundled"]


@dataclass(slots=True, frozen=True)
class SeriesPoint:
    period: str
    value: Decimal
    source_uri: str
    provenance: Provenance = "live"
    fetched_at: float = 0.0

    @property
    def trustworthy(self) -> bool:
        return self.provenance == "live"


@dataclass(slots=True)
class Series:
    name: str
    points: list[SeriesPoint]
    as_of: str = ""

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[SeriesPoint]:
        return iter(self.points)

    @property
    def is_bundled(self) -> bool:
        """True if ANY point is bundled.

        Deliberately not "all". A series that is live for two years and bundled
        at the tip is the one that produces a confidently wrong current figure,
        and an `all()` here would call it live.
        """
        return any(p.provenance == "bundled" for p in self.points)

    @property
    def latest(self) -> SeriesPoint | None:
        return max(self.points, key=lambda p: p.period) if self.points else None

    def as_index_dict(self) -> dict[str, Decimal]:
        """Shape :class:`oodarag.domain.inflation.PriceIndex` accepts."""
        return {p.period: p.value for p in self.points}

    def warn_if_bundled(self) -> None:
        if self.is_bundled:
            n = sum(1 for p in self.points if p.provenance == "bundled")
            log.warn(
                "series contains bundled points; any figure computed from it is a "
                "worked example, not a reading",
                series=self.name, bundled=n, total=len(self.points),
            )


# --------------------------------------------------------------------------
# Bundled fallbacks. Illustrative, and named so nobody mistakes them.
# --------------------------------------------------------------------------

BUNDLED_AS_OF = "2026-07-31"

_BUNDLED_TUFE: dict[str, str] = {
    "2025-07": "100.00", "2025-08": "102.10", "2025-09": "104.35",
    "2025-10": "106.40", "2025-11": "108.70", "2025-12": "111.20",
    "2026-01": "114.90", "2026-02": "117.60", "2026-03": "120.10",
    "2026-04": "122.55", "2026-05": "124.80", "2026-06": "127.35",
    "2026-07": "131.75",
}

_BUNDLED_FX: dict[str, dict[str, str]] = {
    "USDTRY": {"2026-05": "44.10", "2026-06": "45.60", "2026-07": "47.20"},
    "EURTRY": {"2026-05": "47.80", "2026-06": "49.40", "2026-07": "51.30"},
}

_BUNDLED_POLICY_RATE: dict[str, str] = {
    "2026-05": "37.00", "2026-06": "37.00", "2026-07": "37.00",
}


def _bundled(name: str, raw: dict[str, str], uri: str) -> Series:
    return Series(
        name=name,
        as_of=BUNDLED_AS_OF,
        points=[
            SeriesPoint(period=p, value=Decimal(v), source_uri=uri,
                        provenance="bundled", fetched_at=0.0)
            for p, v in sorted(raw.items())
        ],
    )


# --------------------------------------------------------------------------
# Connectors
# --------------------------------------------------------------------------

class MarketDataConnector(Connector):
    """Shared fetch-or-fall-back behaviour."""

    source_system = "marketdata"

    def __init__(self, *, key: str, authority: float = 0.95,
                 client: HttpClient | None = None, api_key: str | None = None,
                 env_var: str = "") -> None:
        self.key = key
        self.authority = authority
        self.client = client
        self.api_key = api_key or (os.environ.get(env_var, "") if env_var else "")
        self.failures = 0
        self.last_error = ""
        self._downgraded = False

    @property
    def downgraded(self) -> bool:
        """Whether the last run fell back to bundled data."""
        return self._downgraded

    def _fallback(self, name: str, why: str) -> Series:
        self._downgraded = True
        log.warn("falling back to bundled series", connector=self.key,
                 series=name, reason=why, as_of=BUNDLED_AS_OF)
        return self._bundled_series(name)

    def _bundled_series(self, name: str) -> Series:  # pragma: no cover - overridden
        raise NotImplementedError

    def _get_json(self, url: str) -> Any:
        if self.client is None:
            raise TransportError("no HTTP client configured")
        response = self.client.get(url)
        return json.loads(response.text)

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        """Series are numbers, not documents, but the Connector contract is
        documents — so each run yields one small JSON document per series. That
        keeps the incremental-hash machinery working: an unchanged series hashes
        identically and costs nothing downstream."""
        for name in self.series_names:
            series = self.series(name)
            payload = {
                "series": name,
                "as_of": series.as_of,
                "bundled": series.is_bundled,
                "points": [
                    {"period": p.period, "value": str(p.value),
                     "provenance": p.provenance, "source": p.source_uri}
                    for p in series.points
                ],
            }
            yield RawDocument(
                source_system=self.source_system,
                external_id=f"{self.key}:{name}",
                uri=f"{self.key}://{name}",
                title=f"{name} ({'bundled' if series.is_bundled else 'live'})",
                text=json.dumps(payload, ensure_ascii=False, indent=2),
                metadata={
                    "authority": self.authority,
                    "doc_kind": "series",
                    "bundled": series.is_bundled,
                    "as_of": series.as_of,
                    "lang": "tr",
                },
            )

    @property
    def series_names(self) -> tuple[str, ...]:  # pragma: no cover - overridden
        return ()

    def series(self, name: str) -> Series:  # pragma: no cover - overridden
        raise NotImplementedError

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["failures"] = self.failures
        cursor["downgraded"] = self._downgraded
        cursor["last_error"] = self.last_error
        cursor["last_run_at"] = time.time()
        return cursor


class TuikCpiConnector(MarketDataConnector):
    """TÜFE, the index TMS 29 restatement is computed against.

    Accuracy matters more than freshness here: a wrong index silently rescales
    every restated figure in the system, and unlike a stale one it never
    announces itself.
    """

    BASE = "https://data.tuik.gov.tr/"

    def __init__(self, **kw: Any) -> None:
        kw.setdefault("key", "tuik")
        super().__init__(**kw)

    @property
    def series_names(self) -> tuple[str, ...]:
        return ("TUFE",)

    def _bundled_series(self, name: str) -> Series:
        return _bundled("TUFE-BUNDLED-NOT-LIVE", _BUNDLED_TUFE, "bundled:illustrative")

    def series(self, name: str = "TUFE") -> Series:
        if self.client is None:
            return self._fallback(name, "no HTTP client configured")
        try:
            payload = self._get_json(f"{self.BASE}api/tufe")
            points = _parse_points(payload, self.BASE)
            if not points:
                return self._fallback(name, "response contained no usable points")
            self.failures = 0
            self._downgraded = False
            return Series(name="TUFE", points=points,
                          as_of=max(p.period for p in points))
        except (HttpError, TransportError, OSError, json.JSONDecodeError,
                InvalidOperation, KeyError, TypeError, ValueError) as e:
            self.failures += 1
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            return self._fallback(name, self.last_error)


class TcmbEvdsConnector(MarketDataConnector):
    """TCMB EVDS: USD/TRY, EUR/TRY and the one-week repo policy rate.

    EVDS needs an API key. With none, this does not fail and does not pretend —
    it falls back and says so, because a fund CFO checking an FX exposure needs
    to know whether the rate is today's or a bundled illustration.
    """

    BASE = "https://evds2.tcmb.gov.tr/service/evds/"

    def __init__(self, **kw: Any) -> None:
        kw.setdefault("key", "tcmb")
        kw.setdefault("env_var", "TCMB_EVDS_API_KEY")
        super().__init__(**kw)

    @property
    def series_names(self) -> tuple[str, ...]:
        return ("USDTRY", "EURTRY", "POLICY_RATE")

    def _bundled_series(self, name: str) -> Series:
        if name == "POLICY_RATE":
            return _bundled("POLICY_RATE-BUNDLED-NOT-LIVE", _BUNDLED_POLICY_RATE,
                            "bundled:illustrative")
        raw = _BUNDLED_FX.get(name, {})
        return _bundled(f"{name}-BUNDLED-NOT-LIVE", raw, "bundled:illustrative")

    def series(self, name: str = "USDTRY") -> Series:
        if name not in self.series_names:
            raise KeyError(f"unknown series {name!r}; have {self.series_names}")
        if not self.api_key:
            return self._fallback(name, "no TCMB_EVDS_API_KEY in the environment")
        if self.client is None:
            return self._fallback(name, "no HTTP client configured")
        try:
            payload = self._get_json(f"{self.BASE}series={name}&type=json&key={self.api_key}")
            points = _parse_points(payload, self.BASE)
            if not points:
                return self._fallback(name, "response contained no usable points")
            self.failures = 0
            self._downgraded = False
            return Series(name=name, points=points, as_of=max(p.period for p in points))
        except (HttpError, TransportError, OSError, json.JSONDecodeError,
                InvalidOperation, KeyError, TypeError, ValueError) as e:
            self.failures += 1
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            return self._fallback(name, self.last_error)


def _parse_points(payload: Any, source_uri: str) -> list[SeriesPoint]:
    """Pull (period, value) pairs out of a response of unknown exact shape.

    Written tolerantly on purpose: the API shape was never observed from here,
    so the parser accepts the two plausible envelopes and returns nothing rather
    than guessing when it recognises neither. Returning nothing routes to the
    bundled fallback, which announces itself; guessing would not.
    """
    rows = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    out: list[SeriesPoint] = []
    now = time.time()
    for row in rows:
        if not isinstance(row, dict):
            continue
        period = str(row.get("Tarih") or row.get("period") or row.get("date") or "").strip()
        if len(period) == 7 and period[4] in "-.":
            period = period.replace(".", "-")
        elif len(period) == 10:
            period = period[:7].replace(".", "-")
        else:
            continue
        raw = next((row[k] for k in row
                    if k not in ("Tarih", "period", "date", "UNIXTIME")
                    and row[k] not in (None, "")), None)
        if raw is None:
            continue
        try:
            value = Decimal(str(raw).replace(",", "."))
        except InvalidOperation:
            continue
        if value <= 0:
            continue
        out.append(SeriesPoint(period=period, value=value, source_uri=source_uri,
                               provenance="live", fetched_at=now))
    return sorted(out, key=lambda p: p.period)


def bundled_price_index() -> Series:
    """The bundled TÜFE series, for callers that want it without a connector."""
    return _bundled("TUFE-BUNDLED-NOT-LIVE", _BUNDLED_TUFE, "bundled:illustrative")
