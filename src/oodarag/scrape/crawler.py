"""A breadth-first, robots-aware crawler.

Design notes that matter for a RAG corpus, as opposed to a generic spider:

* **Dedupe on content, not just URL.** Docs sites serve the same page under
  `/latest/`, `/3.11/` and `/stable/`. URL-only dedupe indexes it three times
  and the retriever then returns the same passage three times.
* **Skip thin pages.** A 30-word "redirecting..." page adds noise to the term
  statistics and never usefully answers anything.
* **Record why a URL was skipped.** A crawl that returns 4 pages instead of 400
  must be diagnosable without re-running it under a debugger.
* **Bound everything.** Pages, fetches, depth, bytes, time - and the frontier
  itself. An unbounded crawl on a calendar-generating site never terminates.
  Every budget is checked before the work it pays for, so a budget of zero
  means zero rather than "unlimited".
* **Gate the URL we landed on, not the one we asked for.** Scope, robots and
  pattern checks run against the link as written *and* again against the final
  URL after redirects. A crawler that only checks what it queued is one
  `Location:` header away from being someone's SSRF proxy - and one more away
  from fetching a redirect target whose robots.txt was never consulted.
* **Never let one page end the crawl.** A malformed URL, a hostile document, a
  dead host: each is a skip with a reason attached, not a traceback that takes
  a nightly job down after 300 good pages.
"""

from __future__ import annotations

import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, deque
from collections.abc import Iterator
from dataclasses import dataclass, field

from oodarag.scrape.html import ExtractedPage, extract
from oodarag.scrape.robots import RobotsPolicy
from oodarag.util.hashing import content_hash
from oodarag.util.http import (
    DEFAULT_UA,
    HttpClient,
    HttpError,
    Response,
    TransportError,
    normalize_url,
    redact_url,
    same_site,
)
from oodarag.util.logging import get_logger

log = get_logger("crawler")

HTML_TYPES = frozenset({"text/html", "application/xhtml+xml", ""})
TEXT_TYPES = frozenset({"text/plain", "text/markdown", "text/x-rst", "application/json"})
_BINARY_EXT_RE = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|ico|bmp|tiff?|mp[34g]|m4[av]|wav|ogg|webm|avi|mov|mkv|"
    r"zip|gz|bz2|xz|tar|7z|rar|whl|exe|dmg|deb|rpm|pkg|iso|"
    r"pdf|docx?|xlsx?|pptx?|odt|epub|woff2?|ttf|eot|css|js|map)(\?|$)",
    re.I,
)

#: Hard ceiling on queued URLs. The fetch budget bounds how many pages we
#: *read*, but one page of a link farm can enqueue a million URLs before the
#: next budget check ever runs, and each one costs a normalize plus a set entry.
MAX_FRONTIER = 100_000

#: Consecutive failures (5xx, 429, transport) before a host is left alone for
#: the rest of the crawl. Without it, a host that went down mid-crawl eats the
#: whole fetch budget one retry ladder at a time.
MAX_HOST_FAILURES = 5

#: Sitemap documents fetched per seed. A sitemapindex can name thousands.
MAX_SITEMAP_FETCHES = 5

#: A DTD in a document we fetched from a stranger. `xml.etree` expands internal
#: entities, so `<!ENTITY>` chains are a billion-laughs bomb that inflates
#: inside our address space, well after the client's byte cap has had its say.
#: No real sitemap carries a doctype, so refusing them costs nothing.
_DTD_RE = re.compile(rb"<!\s*(?:doctype|entity)", re.I)

#: Content types come off the wire and end up as report keys. A 64 KiB header
#: must not become a 64 KiB dictionary key repeated once per fetch.
_CTYPE_KEY_MAX = 40


def _split(url: str) -> urllib.parse.SplitResult | None:
    """`urlsplit` that answers "no" instead of raising.

    `urlsplit("http://[::1/x")` raises ValueError, and these strings arrive from
    user config, other people's HTML and `Location:` headers. One unparseable
    URL must cost one skipped fetch, not the remaining 400 pages of the crawl.
    """
    try:
        return urllib.parse.urlsplit(url)
    except ValueError:
        return None


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
    #: Total decoded bytes for the whole crawl; 0 disables the ceiling. The HTTP
    #: client caps each *response*, which bounds one hostile page but says
    #: nothing about a thousand merely large ones. Checked before each fetch, so
    #: the overshoot is bounded by one response.
    max_crawl_bytes: int = 128 * 1024 * 1024
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
        }


class Crawler:
    def __init__(self, config: CrawlConfig, client: HttpClient | None = None) -> None:
        self.config = config
        self.client = client or HttpClient(
            rate_per_sec=config.rate_per_sec,
            user_agent=config.user_agent or DEFAULT_UA,
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
        self._host_failures: dict[str, int] = {}
        self._seeds = {normalize_url(seed) for seed in config.seeds}

    # ------------------------------------------------------------------ gating

    def _wanted(self, url: str, depth: int) -> tuple[bool, str]:
        if depth > self.config.max_depth:
            return False, "depth"
        if not url.startswith(("http://", "https://")):
            return False, "scheme"
        parts = _split(url)
        if parts is None:
            return False, "unparseable"
        if _BINARY_EXT_RE.search(parts.path):
            return False, "binary_ext"
        if self.config.same_site_only and self.config.seeds:
            if not any(
                same_site(url, seed, include_subdomains=self.config.include_subdomains)
                for seed in self.config.seeds
            ):
                return False, "offsite"
        if self._exclude and any(p.search(url) for p in self._exclude):
            return False, "exclude_pattern"
        # Seeds are exempt from the include patterns: a pattern narrows what a
        # crawl *discovers*, and a seed is what the caller explicitly asked for.
        # Filtering the seed out empties the frontier before the first fetch,
        # and "crawled nothing" is the failure this module exists to prevent.
        if self._include and url not in self._seeds:
            if not any(p.search(url) for p in self._include):
                return False, "include_pattern"
        if not self.robots.allows(url):
            return False, "robots"
        return True, ""

    def _host_of(self, url: str) -> str:
        parts = _split(url)
        return parts.netloc.lower() if parts else ""

    def _throttle(self, url: str) -> None:
        host = self._host_of(url)
        delay = max(self.config.delay_s, self.robots.crawl_delay(url))
        if delay <= 0:
            return
        elapsed = time.monotonic() - self._last_hit.get(host, 0.0)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_hit[host] = time.monotonic()

    def _note_failure(self, host: str) -> None:
        """Count a failure against its host so a dead origin stops being polled.

        Only failures that say something about the *host* count: a 404 is a
        missing page and must not lock the crawler out of the rest of the site.
        """
        if host:
            self._host_failures[host] = self._host_failures.get(host, 0) + 1

    # ------------------------------------------------------------------ crawl

    def crawl(self) -> Iterator[CrawlResult]:
        started = time.monotonic()
        frontier: deque[tuple[str, int]] = deque()
        try:
            for seed in self.config.seeds:
                normalized = normalize_url(seed)
                if normalized not in self._seen_urls:
                    self._seen_urls.add(normalized)
                    frontier.append((normalized, 0))

            fetch_budget = self.config.max_fetches or max(self.config.max_pages * 5, 10)

            if self.config.use_sitemap:
                for seed in list(self.config.seeds):
                    # A sitemap is the seed's own inventory, not a link found on
                    # it: its entries are seeds too. Filing them one level deeper
                    # made `max_depth=0` discover a sitemap and then refuse every
                    # URL in it.
                    for loc in self._sitemap_urls(seed, fetch_budget):
                        normalized = normalize_url(loc)
                        if normalized not in self._seen_urls:
                            self._seen_urls.add(normalized)
                            frontier.append((normalized, 0))

            while frontier and self.report.fetched < self.config.max_pages:
                if time.monotonic() - started >= self.config.max_seconds:
                    self.report.skipped["time_budget"] += len(frontier)
                    self.report.stopped_by = "time_budget"
                    break
                if self.report.fetches >= fetch_budget:
                    self.report.skipped["fetch_budget"] += len(frontier)
                    self.report.stopped_by = "fetch_budget"
                    log.warn("fetch budget exhausted", fetches=self.report.fetches,
                             yielded=self.report.fetched, frontier=len(frontier))
                    break
                if self.config.max_crawl_bytes and self.report.bytes >= self.config.max_crawl_bytes:
                    self.report.skipped["byte_budget"] += len(frontier)
                    self.report.stopped_by = "byte_budget"
                    break
                url, depth = frontier.popleft()

                ok, reason = self._wanted(url, depth)
                if not ok:
                    self.report.skipped[reason] += 1
                    continue
                host = self._host_of(url)
                if self._host_failures.get(host, 0) >= MAX_HOST_FAILURES:
                    self.report.skipped["host_unavailable"] += 1
                    continue

                self._throttle(url)
                self.report.fetches += 1
                try:
                    resp = self.client.get(url, conditional=True)
                except HttpError as e:
                    self.report.errors.append((redact_url(url), f"http {e.status}"))
                    self.report.skipped[f"http_{e.status}"] += 1
                    if e.retryable:
                        self._note_failure(host)
                    continue
                except TransportError as e:
                    self.report.errors.append((redact_url(url), str(e)[:160]))
                    self.report.skipped["transport"] += 1
                    self._note_failure(host)
                    continue
                self._host_failures.pop(host, None)

                if resp.status == 304:
                    self.report.skipped["not_modified"] += 1
                    continue

                # Bytes we paid for, whatever we end up doing with them: a
                # budget that only counts the pages we liked is not a budget.
                self.report.bytes += len(resp.body)

                # The gate ran against the URL we queued. A redirect means the
                # server, not us, chose what we actually fetched, so every check
                # has to run again on where we landed - scope and robots above
                # all, or an off-site `Location:` walks the crawl off the site.
                final = normalize_url(resp.url)
                if final != url:
                    ok, reason = self._wanted(final, depth)
                    if not ok:
                        self.report.skipped[f"redirect_{reason}"] += 1
                        log.warn("redirect left the crawl scope", frm=redact_url(url),
                                 to=redact_url(final), why=reason)
                        continue
                    if final in self._seen_urls:
                        self.report.skipped["redirect_dupe"] += 1
                        continue
                self._seen_urls.add(final)

                ctype = resp.content_type
                if ctype not in HTML_TYPES and ctype not in TEXT_TYPES:
                    self.report.skipped[f"ctype_{ctype[:_CTYPE_KEY_MAX] or 'unknown'}"] += 1
                    continue

                page = self._page_of(resp, ctype)
                if page is None:
                    continue

                if page.word_count < self.config.min_words:
                    self.report.skipped["thin"] += 1
                    self._enqueue(frontier, page, depth)
                    continue

                # A declared canonical URL is the site telling us two URLs are
                # the same document. Version-pinned doc pages are the common
                # case: they differ by a few words but are one page for
                # retrieval purposes. The first URL to claim a canonical is the
                # one we keep - including when a later page *is* the canonical,
                # which otherwise slipped through and indexed the pair twice.
                if self.config.dedupe_canonical and page.canonical:
                    canonical = normalize_url(page.canonical)
                    first = self._seen_canonical.setdefault(canonical, final)
                    if first != final:
                        self.report.skipped["duplicate_canonical"] += 1
                        log.debug("duplicate canonical", url=final, same_as=first)
                        continue

                digest = content_hash(page.text)
                if (first := self._seen_content.get(digest)) is not None:
                    self.report.skipped["duplicate_content"] += 1
                    log.debug("duplicate content", url=final, same_as=first)
                    continue
                self._seen_content[digest] = final

                self.report.fetched += 1
                self._enqueue(frontier, page, depth)
                yield CrawlResult(
                    url=final, depth=depth, page=page, status=resp.status,
                    fetched_at=time.time(), bytes=len(resp.body), content_type=ctype,
                )
        finally:
            # In a generator the tail of `crawl` is not reached when the consumer
            # stops pulling (islice, a `break`, an exception downstream). Leaving
            # the report at its zero values would then read as "the crawl found
            # nothing" instead of "nobody asked for more".
            if not self.report.stopped_by:
                if self.report.fetched >= self.config.max_pages:
                    self.report.stopped_by = "max_pages"
                elif frontier:
                    self.report.stopped_by = "abandoned"
                else:
                    self.report.stopped_by = "frontier_exhausted"
            self.report.duration_s = time.monotonic() - started
            self.report.frontier_left = len(frontier)
            log.info("crawl finished", **{k: v for k, v in self.report.as_dict().items()
                                          if k in ("fetched", "bytes", "duration_s")})

    def _page_of(self, resp: Response, ctype: str) -> ExtractedPage | None:
        """Extract one response, or None if the document defeated the parser.

        The extractor walks a tree built from a stranger's HTML with recursive
        functions; a few thousand nested `<div>`s is a RecursionError, and that
        is one page failing, not the crawl failing. Blanket catch on purpose:
        the interesting failures here are the ones nobody predicted.
        """
        try:
            if ctype in TEXT_TYPES:
                parts = _split(resp.url)
                name = parts.path.rsplit("/", 1)[-1] if parts else ""
                return ExtractedPage(
                    url=resp.url, title=name or resp.url,
                    text=resp.text, markdown=resp.text,
                )
            return extract(resp.text, resp.url)
        except Exception as e:
            self.report.errors.append((redact_url(resp.url), f"extract: {type(e).__name__}"))
            self.report.skipped["extract_error"] += 1
            log.warn("extraction failed", url=redact_url(resp.url),
                     err=f"{type(e).__name__}: {e}"[:160])
            return None

    def _enqueue(self, frontier: deque[tuple[str, int]], page: ExtractedPage, depth: int) -> None:
        if depth >= self.config.max_depth:
            return
        for index, link in enumerate(page.links):
            if len(frontier) >= MAX_FRONTIER:
                # Dropping the tail of one page's links beats letting a link
                # farm decide this process's memory profile.
                self.report.skipped["frontier_full"] += len(page.links) - index
                log.warn("frontier full", cap=MAX_FRONTIER, dropped=len(page.links) - index)
                return
            if link.nofollow and not self.config.follow_nofollow:
                self.report.skipped["nofollow"] += 1
                continue
            normalized = normalize_url(link.url)
            if normalized in self._seen_urls:
                continue
            self._seen_urls.add(normalized)
            frontier.append((normalized, depth + 1))

    # ---------------------------------------------------------------- sitemaps

    def _in_scope_sitemap(self, url: str, seed: str) -> bool:
        """Whether a sitemap URL may be fetched.

        A `Sitemap:` line and a sitemapindex entry are both strings a remote
        host chose, and we hand them straight to the HTTP client. Unscoped, that
        is a request to any host on the internet on someone else's say-so.
        """
        if not url.lower().startswith(("http://", "https://")):
            return False
        if not self.config.same_site_only:
            return True
        return same_site(url, seed, include_subdomains=self.config.include_subdomains)

    def _sitemap_urls(self, seed: str, fetch_budget: int) -> list[str]:
        """Read sitemaps declared in robots.txt (or the conventional path).

        Sitemaps are the honest inventory of a site. Following one beats guessing
        at link structure, and it is a fraction of the requests - but they are
        still requests, so they are counted against the fetch budget like any
        other, and their URLs are scoped like any other.
        """
        cap = self.config.max_pages * 4
        if cap <= 0:
            return []
        found: list[str] = []
        sitemaps = [u for u in self.robots.sitemaps(seed) if self._in_scope_sitemap(u, seed)]
        if not sitemaps:
            parts = _split(seed)
            if parts is None or not parts.netloc:
                return []
            sitemaps = [f"{parts.scheme}://{parts.netloc}/sitemap.xml"]
        queue = deque(sitemaps[:MAX_SITEMAP_FETCHES])
        seen_maps: set[str] = set()
        while queue and len(found) < cap:
            if self.report.fetches >= fetch_budget:
                break
            sm_url = queue.popleft()
            if sm_url in seen_maps:
                continue
            seen_maps.add(sm_url)
            self.report.fetches += 1
            try:
                resp = self.client.get(sm_url, allow_status=(404, 403))
            except (HttpError, TransportError) as e:
                log.warn("sitemap unreadable", url=redact_url(sm_url), err=str(e)[:120])
                continue
            if resp.status >= 400:
                continue
            root = _parse_sitemap(resp.body)
            if root is None:
                log.warn("sitemap unparseable", url=redact_url(sm_url), bytes=len(resp.body))
                continue
            is_index = root.tag.rsplit("}", 1)[-1] == "sitemapindex"
            for element in root.iter():
                if element.tag.rsplit("}", 1)[-1] != "loc":
                    continue
                loc = (element.text or "").strip()
                if not loc:
                    continue
                if is_index:
                    # `<loc>` inside an index names another sitemap, never a
                    # page: putting one in `found` would queue an XML file as a
                    # document and spend a fetch discovering it is not one.
                    if len(seen_maps) + len(queue) < MAX_SITEMAP_FETCHES:
                        if self._in_scope_sitemap(loc, seed):
                            queue.append(loc)
                    continue
                found.append(loc)
                if len(found) >= cap:
                    break  # a 1M-entry sitemap must not be materialised first
        log.info("sitemap discovery", seed=redact_url(seed), maps=len(seen_maps), urls=len(found))
        return found[: self.config.max_pages * 2]


def _parse_sitemap(body: bytes) -> ET.Element | None:
    """Parse sitemap XML, or None for anything we will not hand to the parser.

    See `_DTD_RE`: the byte cap upstream bounds what arrives, not what a DTD
    expands to once it is here.
    """
    if _DTD_RE.search(body):
        return None
    try:
        return ET.fromstring(body)
    except (ET.ParseError, ValueError, UnicodeDecodeError):
        return None
