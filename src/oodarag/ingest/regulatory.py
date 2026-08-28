"""Connectors for the Turkish regulatory sources the Observe phase watches.

**Read this before trusting anything here: none of these has ever run against
its real host.** Thirteen Turkish domains, including every one below, answer
`403` to `CONNECT` at this environment's egress gateway — an organization policy
denial, not a transient failure, and the proxy's own README instructs that such
denials be reported rather than retried [src:EGRESS-POLICY-DENIAL-2026-08-28].
So these connectors are written against the published shape of each site and
tested entirely against local fixtures. Their selectors are the part most likely
to be wrong, and the first person with real access should expect to fix them.

What is *not* speculative is the behaviour around the fetch, and that is most of
what a connector is for:

- **Blocked means empty, never an exception.** A source that cannot be reached
  yields nothing, logs a warning, and increments a failure counter the policy
  engine reads — `CONNECTOR-DOWN` fires after three consecutive failures. A
  crawler that raises on a 403 takes the whole cycle down with it, and the cycle
  has twelve other things to do.
- **Redaction happens here, at the boundary**, before a byte reaches the index.
- **Every item carries a publication date and an authority weight.** A filing
  deadline cited to a blog is wrong even when the blog is right, because the
  citation is what an auditor follows.
- **Budgets are mandatory.** A crawl of a government site with no page cap is a
  way to get an IP banned, which converts a temporary problem into a permanent
  one.

Keyword filtering is deliberately narrow. The Resmî Gazete publishes everything
the state does; a watchlist that matches broadly is a crawler, not a filter, and
a human pays the reading cost of every false positive.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.scrape.crawler import CrawlConfig, Crawler
from oodarag.util.http import HttpClient, HttpError, TransportError, urljoin
from oodarag.util.logging import get_logger
from oodarag.util.text import summarize

log = get_logger("ingest.regulatory")

#: Dates as Turkish sites write them: 23.07.2026, 23/07/2026, 2026-07-23.
_DATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(\d{2})[./](\d{2})[./](\d{4})\b"),
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
)

_TR_MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12,
    "aralik": 12,
}
_TR_DATE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(_TR_MONTHS) + r")\s+(\d{4})\b", re.IGNORECASE
)


def extract_published(text: str) -> str:
    """First date in the text, as ISO. Empty when there is none.

    Order matters: the Turkish long form is tried first because "23 Temmuz 2026"
    often sits above a numeric reference that is not a date at all.
    """
    m = _TR_DATE.search(text)
    if m:
        month = _TR_MONTHS[m.group(2).lower()]
        return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(1)):02d}"
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        a, b, c = m.groups()
        if len(a) == 4:
            return f"{int(a):04d}-{int(b):02d}-{int(c):02d}"
        return f"{int(c):04d}-{int(b):02d}-{int(a):02d}"
    return ""


@dataclass(slots=True)
class Budget:
    """Hard caps. A crawl that can run away will, on the night nobody is watching.

    The field names mirror ``CrawlConfig`` exactly rather than inventing a
    parallel vocabulary — an earlier draft of this file guessed a ``max_bytes``
    that CrawlConfig does not have, and every connector raised TypeError at the
    first fetch instead of degrading. Caps on *fetches* as well as pages matter
    on government sites, where print views and session ids can multiply one
    document into hundreds of URLs.
    """

    max_pages: int = 25
    max_fetches: int = 100
    max_depth: int = 2
    max_seconds: float = 60.0
    rate_per_sec: float = 1.0

    def as_crawl_options(self) -> dict[str, Any]:
        return {"max_pages": self.max_pages, "max_fetches": self.max_fetches,
                "max_depth": self.max_depth, "max_seconds": self.max_seconds,
                "rate_per_sec": self.rate_per_sec}


class RegulatoryConnector(Connector):
    """Shared behaviour for every Turkish regulatory source.

    Subclasses supply seeds, an authority weight, and a relevance test. Nothing
    else differs between them, and keeping it that way is what makes it possible
    to fix all four when one site changes its markup.
    """

    source_system = "regulatory"
    doc_kind = "regulation"

    def __init__(
        self,
        *,
        key: str,
        seeds: Sequence[str],
        authority: float,
        redactor: Callable[[str], str] | None = None,
        budget: Budget | None = None,
        client: HttpClient | None = None,
        keywords: Sequence[str] = (),
    ) -> None:
        self.key = key
        self.authority = authority
        self.seeds = list(seeds)
        self.redactor = redactor
        self.budget = budget or Budget()
        self.client = client
        self.keywords = tuple(k.lower() for k in keywords)
        #: Consecutive failed runs. The policy engine's CONNECTOR-DOWN rule
        #: reads this; three in a row means broken rather than flaky.
        self.failures = 0
        self.last_error = ""
        self.last_report: dict[str, Any] = {}

    # -- relevance ---------------------------------------------------------

    def is_relevant(self, title: str, text: str) -> bool:
        """No keywords means take everything; otherwise match narrowly."""
        if not self.keywords:
            return True
        hay = f"{title}\n{text}".lower()
        return any(k in hay for k in self.keywords)

    # -- fetch -------------------------------------------------------------

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        seen_before = set(cursor.get("hashes", {}))
        produced = 0
        try:
            config = CrawlConfig(seeds=self.seeds, **self.budget.as_crawl_options())
            crawler = Crawler(config, client=self.client)
            for result in crawler.crawl():
                page = result.page
                body = page.markdown or page.text or ""
                if not body.strip():
                    continue
                if not self.is_relevant(page.title or "", body):
                    continue
                if self.redactor is not None:
                    body = self.redactor(body)
                published = page.published or extract_published(
                    f"{page.title or ''}\n{body[:2000]}"
                )
                produced += 1
                yield RawDocument(
                    source_system=self.source_system,
                    external_id=result.url,
                    uri=result.url,
                    title=page.title or result.url,
                    text=body,
                    fetched_at=result.fetched_at,
                    metadata={
                        "authority": self.authority,
                        "doc_kind": self.doc_kind,
                        "lang": "tr",
                        "published_at": published,
                        "regulator": self.key.split(":")[0],
                        "summary": summarize(page.text, 200),
                        "first_seen": result.url not in seen_before,
                    },
                )
            # The crawler is tolerant by design: it catches transport errors per
            # URL and keeps going, so a completely unreachable host raises
            # nothing and simply produces no pages. That makes a dead source
            # indistinguishable from a quiet one — and a quiet source never
            # trips CONNECTOR-DOWN, so the loop would go on reporting a healthy
            # regulatory watch over a feed that has been dark for a month. The
            # report is where the truth is, so the failure verdict is read from
            # it rather than from control flow.
            report = crawler.report
            self.last_report = report.as_dict()
            if produced == 0 and report.errors:
                self.failures += 1
                self.last_error = "; ".join(f"{u}: {e}" for u, e in report.errors[:3])[:300]
                log.warn("regulatory source produced nothing and reported errors",
                         key=self.key, failures=self.failures,
                         errors=len(report.errors), err=self.last_error)
            elif produced == 0 and report.fetched == 0:
                self.failures += 1
                self.last_error = f"nothing fetched (stopped_by={report.stopped_by or 'none'})"
                log.warn("regulatory source fetched nothing", key=self.key,
                         failures=self.failures, err=self.last_error)
            else:
                self.failures = 0
                self.last_error = ""
        except (HttpError, TransportError, OSError) as e:
            # The expected case in this environment. Degrade, never raise: a
            # blocked source must cost one warning, not the whole OODA cycle.
            self.failures += 1
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            log.warn("regulatory source unreachable; yielding nothing",
                     key=self.key, failures=self.failures, err=self.last_error)
        except Exception as e:  # markup changed, parser surprised — same policy
            self.failures += 1
            self.last_error = f"{type(e).__name__}: {e}"[:300]
            log.error("regulatory connector failed", key=self.key,
                      failures=self.failures, err=self.last_error)
        else:
            log.info("regulatory connector run", key=self.key, produced=produced,
                     failures=self.failures)

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["failures"] = self.failures
        cursor["last_error"] = self.last_error
        cursor["last_report"] = self.last_report
        cursor["last_run_at"] = time.time()
        return cursor


# --------------------------------------------------------------------------
# The four sources
# --------------------------------------------------------------------------

#: Terms that make a Resmî Gazete or bulletin item relevant to a GSYF/GYF
#: manager. Mirrors config.WAM.watch_keywords; passed in rather than imported so
#: a connector can be pointed at a different firm without editing this file.
DEFAULT_KEYWORDS: tuple[str, ...] = (
    "portföy yönetim şirketi", "girişim sermayesi yatırım fonu",
    "gayrimenkul yatırım fonu", "nitelikli yatırımcı", "kolektif yatırım",
    "enflasyon muhasebesi", "değerleme esasları", "katılma payı",
    "kurumlar vergisi istisnası", "portföy sınırlamaları",
    "iii-52", "iii-55", "iii-56", "vii-128", "tms 29",
)


class SpkConnector(RegulatoryConnector):
    """SPK weekly bulletins (haftalık bülten), announcements and tebliğs.

    The bulletin is where a decision like 23/07/2026 no. 45/1359 first appears
    with its own number [src:SPK-BULLETIN-45-1359-2026-08-28]. It is the highest
    authority short of the Official Gazette.
    """

    doc_kind = "spk_bulletin"

    def __init__(self, **kw: Any) -> None:
        kw.setdefault("key", "spk")
        kw.setdefault("authority", 0.98)
        kw.setdefault("seeds", ["https://spk.gov.tr/spk-bultenleri",
                                "https://spk.gov.tr/duyurular/basin-duyurulari"])
        kw.setdefault("keywords", DEFAULT_KEYWORDS)
        super().__init__(**kw)


class KapConnector(RegulatoryConnector):
    """KAP disclosures, filtered to a watchlist of fund and company codes.

    The watchlist is the thing that makes this connector specific rather than a
    firehose: KAP carries every listed issuer in Turkey, and this firm cares
    about five codes. Passing an empty watchlist is refused rather than
    silently indexing the market.
    """

    doc_kind = "kap_disclosure"

    def __init__(self, watchlist: Sequence[str], **kw: Any) -> None:
        codes = tuple(c.strip().upper() for c in watchlist if c and c.strip())
        if not codes:
            raise ValueError(
                "KapConnector needs a watchlist. Without one it would index every "
                "disclosure on the platform, which is a firehose, not a feed."
            )
        self.watchlist = codes
        kw.setdefault("key", "kap")
        kw.setdefault("authority", 0.95)
        kw.setdefault("seeds", [f"https://www.kap.org.tr/tr/bildirim-sorgu?code={c}"
                                for c in codes])
        super().__init__(**kw)

    def is_relevant(self, title: str, text: str) -> bool:
        hay = f"{title}\n{text}".upper()
        return any(re.search(rf"\b{re.escape(code)}\b", hay) for code in self.watchlist)


class ResmiGazeteConnector(RegulatoryConnector):
    """The Official Gazette. The only place a rule actually becomes law."""

    doc_kind = "official_gazette"

    def __init__(self, **kw: Any) -> None:
        kw.setdefault("key", "resmigazete")
        kw.setdefault("authority", 1.0)
        kw.setdefault("seeds", ["https://www.resmigazete.gov.tr/"])
        kw.setdefault("keywords", DEFAULT_KEYWORDS)
        super().__init__(**kw)


class TspbConnector(RegulatoryConnector):
    """TSPB genel mektuplar — circulars that reach members before practice settles."""

    doc_kind = "industry_circular"

    def __init__(self, **kw: Any) -> None:
        kw.setdefault("key", "tspb")
        kw.setdefault("authority", 0.85)
        kw.setdefault("seeds", ["https://tspb.org.tr/genel_mektuplar/"])
        kw.setdefault("keywords", DEFAULT_KEYWORDS)
        super().__init__(**kw)


def default_connectors(watchlist: Sequence[str],
                       redactor: Callable[[str], str] | None = None,
                       **kw: Any) -> list[RegulatoryConnector]:
    """The four sources, in descending authority. Wired but not runnable here."""
    return [
        ResmiGazeteConnector(redactor=redactor, **kw),
        SpkConnector(redactor=redactor, **kw),
        KapConnector(watchlist, redactor=redactor, **kw),
        TspbConnector(redactor=redactor, **kw),
    ]


def urljoin_seed(base: str, href: str) -> str:
    """Thin re-export so callers do not reach into util.http for one function."""
    return urljoin(base, href)
