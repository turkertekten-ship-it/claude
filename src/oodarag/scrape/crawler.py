"""A breadth-first, robots-aware crawler.

Design notes that matter for a RAG corpus, as opposed to a generic spider:

* **Dedupe on content, not just URL.** Docs sites serve the same page under
  `/latest/`, `/3.11/` and `/stable/`. URL-only dedupe indexes it three times
  and the retriever then returns the same passage three times.
* **Skip thin pages.** A 30-word "redirecting..." page adds noise to the term
  statistics and never usefully answers anything.
* **Record why a URL was skipped.** A crawl that returns 4 pages instead of 400
  must be diagnosable without re-running it under a debugger.
* **Bound everything.** Pages, depth, bytes, time. An unbounded crawl on a
  calendar-generating site never terminates.
"""

from __future__ import annotations

import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Iterator

from oodarag.scrape.html import ExtractedPage, extract
from oodarag.scrape.robots import RobotsPolicy
from oodarag.util.hashing import content_hash
from oodarag.util.http import HttpClient, HttpError, TransportError, normalize_url, same_site
from oodarag.util.logging import get_logger

log = get_logger("crawler")


def _safe_normalize(url: str) -> str | None:
    """`normalize_url`, but a malformed URL is a URL to drop, not a crawl to lose.

    `normalize_url` reaches `SplitResult.port`/`.hostname`, both of which raise
    `ValueError` on a malformed authority - `http://host:80x/`, an unclosed IPv6
    literal. Those appear in real pages (hand-written hrefs, template variables
    that never got substituted), and one of them anywhere in the frontier used to
    abort `crawl()` mid-generator: the caller kept whatever had already been
    yielded, lost every page still queued, and got a report with no `stopped_by`,
    no duration and no frontier count - so the failure was not even diagnosable
    afterwards. Returning None lets the caller count it and keep going.
    """
    try:
        return normalize_url(url)
    except ValueError:
        return None

HTML_TYPES = frozenset({"text/html", "application/xhtml+xml", ""})
TEXT_TYPES = frozenset({"text/plain", "text/markdown", "text/x-rst", "application/json"})
_BINARY_EXT_RE = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|ico|bmp|tiff?|mp[34g]|m4[av]|wav|ogg|webm|avi|mov|mkv|"
    r"zip|gz|bz2|xz|tar|7z|rar|whl|exe|dmg|deb|rpm|pkg|iso|"
    r"pdf|docx?|xlsx?|pptx?|odt|epub|woff2?|ttf|eot|css|js|map)(\?|$)",
    re.I,
)


@dataclass
class CrawlConfig:
    seeds: list[str] = field(default_factory=list)
    max_pages: int = 50
    #: Hard cap on *requests*, not just yielded pages. Without it a site whose
    #: pages all dedupe to one document (versioned docs, print views, session
    #: ids) will happily fetch thousands of URLs to produce a single result.
    max_fetches: int = 0  # 0 => derived as max_pages * 5
    max_depth: int = 2
    max_seconds: float = 300.0
    same_site_only: bool = True
    include_subdomains: bool = True
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    min_words: int = 40
    obey_robots: bool = True
    robots_on_error: str = "deny"
    use_sitemap: bool = False
    dedupe_canonical: bool = True
    delay_s: float = 0.0
    rate_per_sec: float = 2.0
    user_agent: str = ""
    follow_nofollow: bool = False

    def compiled(self) -> tuple[list[re.Pattern[str]], list[re.Pattern[str]]]:
        return (
            [re.compile(p, re.I) for p in self.include_patterns],
            [re.compile(p, re.I) for p in self.exclude_patterns],
        )


@dataclass(slots=True)
class CrawlResult:
    url: str
    depth: int
    page: ExtractedPage
    status: int
    fetched_at: float
    bytes: int
    content_type: str


@dataclass
class CrawlReport:
    fetched: int = 0
    skipped: Counter = field(default_factory=Counter)
    errors: list[tuple[str, str]] = field(default_factory=list)
    fetches: int = 0
    bytes: int = 0
    duration_s: float = 0.0
    frontier_left: int = 0
    stopped_by: str = ""
    #: URLs the server answered 304 to. They are pages that still exist and have
    #: not changed, so a connector must be able to tell them from pages that
    #: disappeared - see Connector.unchanged_external_ids.
    not_modified: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "fetched": self.fetched,
            "fetches": self.fetches,
            "stopped_by": self.stopped_by,
            "skipped": dict(self.skipped),
            "errors": self.errors[:20],
            "error_count": len(self.errors),
            "bytes": self.bytes,
            "duration_s": round(self.duration_s, 2),
            "frontier_left": self.frontier_left,
            "not_modified": len(self.not_modified),
        }


class Crawler:
    def __init__(self, config: CrawlConfig, client: HttpClient | None = None) -> None:
        self.config = config
        self.client = client or HttpClient(
            rate_per_sec=config.rate_per_sec,
            user_agent=config.user_agent or HttpClient().user_agent,
        )
        self.robots = RobotsPolicy(
            client=self.client,
            user_agent=self.client.user_agent,
            obey=config.obey_robots,
            on_error=config.robots_on_error,
        )
        self.report = CrawlReport()
        self._include, self._exclude = config.compiled()
        self._seen_urls: set[str] = set()
        self._seen_content: dict[str, str] = {}
        self._seen_canonical: dict[str, str] = {}
        self._last_hit: dict[str, float] = {}

    # ------------------------------------------------------------------ gating

    def _wanted(self, url: str, depth: int) -> tuple[bool, str]:
        if depth > self.config.max_depth:
            return False, "depth"
        if not url.startswith(("http://", "https://")):
            return False, "scheme"
        if _BINARY_EXT_RE.search(urllib.parse.urlsplit(url).path):
            return False, "binary_ext"
        if self.config.same_site_only and self.config.seeds:
            if not any(
                same_site(url, seed, include_subdomains=self.config.include_subdomains)
                for seed in self.config.seeds
            ):
                return False, "offsite"
        if self._exclude and any(p.search(url) for p in self._exclude):
            return False, "exclude_pattern"
        if self._include and not any(p.search(url) for p in self._include):
            return False, "include_pattern"
        if not self.robots.allows(url):
            return False, "robots"
        return True, ""

    def _throttle(self, url: str) -> None:
        host = urllib.parse.urlsplit(url).netloc
        delay = max(self.config.delay_s, self.robots.crawl_delay(url))
        if delay <= 0:
            return
        elapsed = time.monotonic() - self._last_hit.get(host, 0.0)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_hit[host] = time.monotonic()

    # ------------------------------------------------------------------ crawl

    def crawl(self) -> Iterator[CrawlResult]:
        started = time.monotonic()
        frontier: deque[tuple[str, int]] = deque()

        for seed in self.config.seeds:
            normalized = _safe_normalize(seed)
            if normalized is None:
                self.report.skipped["bad_url"] += 1
                continue
            if normalized not in self._seen_urls:
                self._seen_urls.add(normalized)
                frontier.append((normalized, 0))

        if self.config.use_sitemap:
            for seed in list(self.config.seeds):
                for loc in self._sitemap_urls(seed):
                    normalized = _safe_normalize(loc)
                    if normalized is None:
                        self.report.skipped["bad_url"] += 1
                        continue
                    if normalized not in self._seen_urls:
                        self._seen_urls.add(normalized)
                        frontier.append((normalized, 1))

        fetch_budget = self.config.max_fetches or max(self.config.max_pages * 5, 10)
        while frontier and self.report.fetched < self.config.max_pages:
            if time.monotonic() - started > self.config.max_seconds:
                self.report.skipped["time_budget"] += len(frontier)
                self.report.stopped_by = "time_budget"
                break
            if self.report.fetches >= fetch_budget:
                self.report.skipped["fetch_budget"] += len(frontier)
                self.report.stopped_by = "fetch_budget"
                log.warn("fetch budget exhausted", fetches=self.report.fetches,
                         yielded=self.report.fetched, frontier=len(frontier))
                break
            url, depth = frontier.popleft()

            ok, reason = self._wanted(url, depth)
            if not ok:
                self.report.skipped[reason] += 1
                continue

            self._throttle(url)
            self.report.fetches += 1
            try:
                resp = self.client.get(url, conditional=True)
            except HttpError as e:
                self.report.errors.append((url, f"http {e.status}"))
                self.report.skipped[f"http_{e.status}"] += 1
                continue
            except TransportError as e:
                self.report.errors.append((url, str(e)[:160]))
                self.report.skipped["transport"] += 1
                continue

            if resp.status == 304:
                # Unchanged, not gone. Recording the URL is what lets the
                # connector classify it as unchanged; without it a second crawl
                # through a shared client (the documented way to share a rate
                # limit) made every unchanged page look deleted.
                self.report.skipped["not_modified"] += 1
                self.report.not_modified.append(url)
                continue

            ctype = resp.content_type
            if ctype not in HTML_TYPES and ctype not in TEXT_TYPES:
                self.report.skipped[f"ctype_{ctype or 'unknown'}"] += 1
                continue

            self.report.bytes += len(resp.body)

            if ctype in TEXT_TYPES and ctype != "text/html":
                page = ExtractedPage(
                    url=resp.url,
                    title=urllib.parse.urlsplit(resp.url).path.rsplit("/", 1)[-1] or resp.url,
                    text=resp.text,
                    markdown=resp.text,
                )
            else:
                page = extract(resp.text, resp.url)

            # A redirect can land two frontier entries on the same final page.
            # A server that redirects to a malformed Location still gave us a
            # page; fall back to the URL we asked for rather than dropping it.
            final = _safe_normalize(resp.url) or url
            if final != url and final in self._seen_urls:
                self.report.skipped["redirect_dupe"] += 1
                continue
            self._seen_urls.add(final)

            if page.word_count < self.config.min_words:
                self.report.skipped["thin"] += 1
                self._enqueue(frontier, page, depth)
                continue

            # A declared canonical URL is the site telling us two URLs are the
            # same document. Version-pinned doc pages are the common case: they
            # differ by a few words but are one page for retrieval purposes.
            if self.config.dedupe_canonical and page.canonical:
                # One canonical URL means one document, whichever of its URLs we
                # happened to reach first. The `canonical == final` case used to
                # be exempt from the duplicate check, which made the dedupe
                # order-dependent: crawling /stable/ then /latest/ kept one page,
                # crawling /latest/ then /stable/ kept both - and seeding a docs
                # site at /latest/ is the normal way round. The retriever then
                # returns the same passage twice, which is the exact failure this
                # module's docstring says dedupe exists to prevent.
                canonical = _safe_normalize(page.canonical)
                if canonical is None:
                    self.report.skipped["bad_canonical"] += 1
                elif (first := self._seen_canonical.get(canonical)) is not None:
                    if first != final:
                        self.report.skipped["duplicate_canonical"] += 1
                        log.debug("duplicate canonical", url=final, same_as=first)
                        continue
                else:
                    self._seen_canonical[canonical] = final

            digest = content_hash(page.text)
            if (first := self._seen_content.get(digest)) is not None:
                self.report.skipped["duplicate_content"] += 1
                log.debug("duplicate content", url=url, same_as=first)
                continue
            self._seen_content[digest] = final

            self.report.fetched += 1
            self._enqueue(frontier, page, depth)
            yield CrawlResult(
                url=final, depth=depth, page=page, status=resp.status,
                fetched_at=time.time(), bytes=len(resp.body), content_type=ctype,
            )

        if not self.report.stopped_by:
            self.report.stopped_by = "max_pages" if self.report.fetched >= self.config.max_pages \
                else "frontier_exhausted"
        self.report.duration_s = time.monotonic() - started
        self.report.frontier_left = len(frontier)
        log.info("crawl finished", **{k: v for k, v in self.report.as_dict().items()
                                      if k in ("fetched", "bytes", "duration_s")})

    def _enqueue(self, frontier: deque[tuple[str, int]], page: ExtractedPage, depth: int) -> None:
        if depth >= self.config.max_depth:
            return
        for link in page.links:
            if link.nofollow and not self.config.follow_nofollow:
                self.report.skipped["nofollow"] += 1
                continue
            normalized = _safe_normalize(link.url)
            if normalized is None:
                self.report.skipped["bad_url"] += 1
                continue
            if normalized in self._seen_urls:
                continue
            self._seen_urls.add(normalized)
            frontier.append((normalized, depth + 1))

    def _sitemap_urls(self, seed: str) -> list[str]:
        """Read sitemaps declared in robots.txt (or the conventional path).

        Sitemaps are the honest inventory of a site. Following one beats guessing
        at link structure, and it is a fraction of the requests.
        """
        found: list[str] = []
        sitemaps = list(self.robots.sitemaps(seed))
        if not sitemaps:
            parts = urllib.parse.urlsplit(seed)
            sitemaps = [f"{parts.scheme}://{parts.netloc}/sitemap.xml"]
        queue = deque(sitemaps[:5])
        seen_maps: set[str] = set()
        while queue and len(found) < self.config.max_pages * 4:
            sm_url = queue.popleft()
            if sm_url in seen_maps:
                continue
            seen_maps.add(sm_url)
            try:
                resp = self.client.get(sm_url, allow_status=(404, 403))
                if resp.status >= 400:
                    continue
                root = ET.fromstring(resp.body)
            except (HttpError, TransportError, ET.ParseError) as e:
                log.warn("sitemap unreadable", url=sm_url, err=str(e)[:120])
                continue
            # What a <loc> means is decided by the document it came from: in a
            # <sitemapindex> it is another sitemap, in a <urlset> it is a page.
            is_index = root.tag.endswith("sitemapindex")
            for element in root.iter():
                tag = element.tag.rsplit("}", 1)[-1]
                if tag != "loc" or not (element.text or "").strip():
                    continue
                loc = element.text.strip()
                if is_index:
                    # The map cap used to fall through to `found`, so past five
                    # maps a nested index's children were handed to the frontier
                    # as if they were pages - the crawler then spent fetches on
                    # sitemap XML, and any host serving it as text/plain got raw
                    # XML into the corpus. Over the cap, drop them.
                    if len(seen_maps) < 5:
                        queue.append(loc)
                else:
                    found.append(loc)
        log.info("sitemap discovery", seed=seed, maps=len(seen_maps), urls=len(found))
        return found[: self.config.max_pages * 2]
