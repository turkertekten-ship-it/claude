"""Tests for the breadth-first crawler.

Nothing here opens a socket: every test swaps `HttpClient._opener` for a fake
serving a small in-memory site graph, and the fake refuses to answer a request
the test did not plan for. The graph carries the shapes a crawler actually dies
on - a cycle, an off-site link, a redirect chain, a 404, a 500 and a response
past the byte cap - because the three ways a crawler fails (runs forever,
escapes its scope, silently crawls nothing) all hide in exactly those.

Retry policies here are one attempt with zero backoff and `time.sleep` is a
mock in every module that can reach it, so a regression in retry handling shows
up as a failed assertion rather than a suite that takes a minute longer.
"""

from __future__ import annotations

import email.message
import io
import itertools
import unittest
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import Any
from unittest import mock

from oodarag.scrape import crawler as crawler_mod
from oodarag.scrape.crawler import (
    MAX_HOST_FAILURES,
    MAX_SITEMAP_FETCHES,
    CrawlConfig,
    Crawler,
    CrawlResult,
)
from oodarag.util.http import HttpClient, RetryPolicy

SITE = "https://example.com"
OTHER = "https://other.example.org"


# ----------------------------------------------------------------------- fakes


@dataclass
class Reply:
    """One planned response. `location` makes the fake opener follow a redirect
    the way urllib would, so the crawler only ever sees the final URL."""

    body: bytes = b""
    status: int = 200
    ctype: str = "text/html; charset=utf-8"
    location: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    error: Exception | None = None


def message(headers: dict[str, str]) -> email.message.Message:
    msg = email.message.Message()
    for key, value in headers.items():
        msg[key] = value
    return msg


class FakeResponse:
    def __init__(self, reply: Reply, url: str) -> None:
        self.status = reply.status
        headers = {"Content-Type": reply.ctype, "Content-Length": str(len(reply.body))}
        headers.update(reply.headers)
        self.headers = message(headers)
        self._url = url
        self._stream = io.BytesIO(reply.body)
        self.closed = False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: Any) -> bool:
        self.closed = True
        return False


class FakeOpener:
    """Serves a site graph. Unknown URLs are a 404, never an invented page."""

    def __init__(self, site: dict[str, Reply]) -> None:
        self.site = site
        self.requests: list[str] = []

    @property
    def page_requests(self) -> list[str]:
        """Requests for documents, i.e. everything but the robots.txt probes."""
        return [u for u in self.requests if not u.endswith("/robots.txt")]

    def open(self, req: Any, timeout: float | None = None) -> FakeResponse:
        url = req.full_url
        self.requests.append(url)
        chain: list[str] = []
        while True:
            reply = self.site.get(url)
            if reply is None:
                raise self._error(url, 404, b"not found")
            if reply.error is not None:
                raise reply.error
            if not reply.location:
                break
            if url in chain:
                # urllib gives up on a cycle by raising the 3xx as an HTTPError.
                raise self._error(url, 302, b"redirect loop")
            chain.append(url)
            url = urllib.parse.urljoin(url, reply.location)
        if reply.status >= 400 or reply.status == 304:
            raise self._error(url, reply.status, reply.body, reply.headers)
        return FakeResponse(reply, url)

    @staticmethod
    def _error(url: str, code: int, body: bytes,
               headers: dict[str, str] | None = None) -> urllib.error.HTTPError:
        return urllib.error.HTTPError(
            url, code, f"status {code}", message(headers or {}), io.BytesIO(body)
        )


# ------------------------------------------------------------------- fixtures


def html(name: str, links: tuple[str, ...] = (), *, words: int = 60, canonical: str = "",
         nofollow: tuple[str, ...] = ()) -> bytes:
    """A page with enough unique words to clear `min_words` and its own content
    hash, so dedupe only fires when a test means it to."""
    filler = " ".join(f"{name}-word{i}" for i in range(words))
    anchors = "".join(f'<a href="{u}">go {i}</a> ' for i, u in enumerate(links))
    anchors += "".join(f'<a href="{u}" rel="nofollow">skip {i}</a> ' for i, u in enumerate(nofollow))
    head = f"<title>{name}</title>"
    if canonical:
        head += f'<link rel="canonical" href="{canonical}">'
    return (
        f"<html><head>{head}</head><body><main><p>{filler}</p>"
        f"<p>{anchors}</p></main></body></html>"
    ).encode()


def page(name: str, links: tuple[str, ...] = (), **kw: Any) -> Reply:
    return Reply(body=html(name, links, **kw))


def demo_site() -> dict[str, Reply]:
    """The graph every structural test runs against.

    `/` links to: two ordinary pages, a cycle, a 404, a 500, an oversize page,
    an off-site page, and a redirect chain that lands back on-site.
    """
    return {
        f"{SITE}/": page("seed", (
            "/a", "/b", "/loop", "/missing", "/boom", "/huge", f"{OTHER}/x", "/hop",
        )),
        f"{SITE}/a": page("a", ("/b", "/")),          # back-edges: the cycle
        f"{SITE}/b": page("b", ("/a",)),
        f"{SITE}/loop": page("loop", ("/loop",)),     # self-edge
        f"{SITE}/missing": Reply(status=404, body=b"gone"),
        f"{SITE}/boom": Reply(status=500, body=b"kaboom"),
        f"{SITE}/huge": Reply(body=b"x" * 50_000),
        f"{SITE}/hop": Reply(location="/hop2"),
        f"{SITE}/hop2": Reply(location="/landing"),
        f"{SITE}/landing": page("landing"),
        f"{OTHER}/x": page("offsite"),
    }


class CrawlerTestCase(unittest.TestCase):
    """Base: no test sleeps, and every fetch goes through the fake opener."""

    def setUp(self) -> None:
        # One patch covers the crawler, the client and the token bucket: they
        # all reach the same `time` module object, so patching it per-module
        # would just stack three mocks on one attribute and record on the last.
        patcher = mock.patch("time.sleep")
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)
        self.opener: FakeOpener | None = None

    def client(self, **kw: Any) -> HttpClient:
        kw.setdefault("retry", RetryPolicy(attempts=1, base_delay=0.0, max_delay=0.0, jitter=0.0))
        kw.setdefault("rate_per_sec", 1_000_000.0)
        kw.setdefault("burst", 10_000)
        return HttpClient(**kw)

    def crawler(self, site: dict[str, Reply], *, client: HttpClient | None = None,
                **options: Any) -> Crawler:
        options.setdefault("seeds", [f"{SITE}/"])
        options.setdefault("obey_robots", False)
        http = client or self.client()
        self.opener = FakeOpener(site)
        http._opener = self.opener
        return Crawler(CrawlConfig(**options), client=http)

    def crawl_site(self, site: dict[str, Reply], **options: Any) -> tuple[list[CrawlResult], Crawler]:
        crawler = self.crawler(site, **options)
        return list(crawler.crawl()), crawler

    def urls(self, results: list[CrawlResult]) -> list[str]:
        return [r.url for r in results]


# ------------------------------------------------------------------ happy path


class HappyPathTestCase(CrawlerTestCase):
    def test_single_page_site_yields_one_document(self) -> None:
        results, crawler = self.crawl_site({f"{SITE}/": page("seed")})

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        result = results[0]
        self.assertEqual(result.depth, 0)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.content_type, "text/html")
        self.assertEqual(result.page.title, "seed")
        self.assertGreater(result.bytes, 0)
        self.assertGreater(result.fetched_at, 0.0)
        self.assertEqual(crawler.report.fetched, 1)
        self.assertEqual(crawler.report.fetches, 1)
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")
        self.assertEqual(crawler.report.frontier_left, 0)
        self.assertEqual(crawler.report.bytes, result.bytes)

    def test_frontier_is_breadth_first_in_document_order(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/a", "/b")),
            f"{SITE}/a": page("a", ("/c",)),
            f"{SITE}/b": page("b", ("/d",)),
            f"{SITE}/c": page("c"),
            f"{SITE}/d": page("d"),
        }
        results, _ = self.crawl_site(site, max_depth=2)

        self.assertEqual(
            self.urls(results),
            [f"{SITE}/", f"{SITE}/a", f"{SITE}/b", f"{SITE}/c", f"{SITE}/d"],
        )
        self.assertEqual([r.depth for r in results], [0, 1, 1, 2, 2])

    def test_output_order_and_report_are_stable_across_runs(self) -> None:
        first, crawler_a = self.crawl_site(demo_site(), max_depth=2)
        second, crawler_b = self.crawl_site(demo_site(), max_depth=2)

        self.assertEqual(self.urls(first), self.urls(second))
        drop = ("duration_s",)
        self.assertEqual(
            {k: v for k, v in crawler_a.report.as_dict().items() if k not in drop},
            {k: v for k, v in crawler_b.report.as_dict().items() if k not in drop},
        )

    def test_plain_text_documents_are_kept_with_a_filename_title(self) -> None:
        body = " ".join(f"line{i}" for i in range(80)).encode("utf-8")
        site = {f"{SITE}/notes.txt": Reply(body=body, ctype="text/plain; charset=utf-8")}

        results, _ = self.crawl_site(site, seeds=[f"{SITE}/notes.txt"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].page.title, "notes.txt")
        self.assertEqual(results[0].page.text, body.decode("utf-8"))
        self.assertEqual(results[0].content_type, "text/plain")


# --------------------------------------------------------------------- budgets


class BudgetTestCase(CrawlerTestCase):
    def chain(self, length: int) -> dict[str, Reply]:
        """`/p0 -> /p1 -> ... -> /pN`, one new page per fetch."""
        site = {f"{SITE}/": page("seed", ("/p0",))}
        for i in range(length):
            site[f"{SITE}/p{i}"] = page(f"p{i}", (f"/p{i + 1}",))
        return site

    def test_max_pages_stops_at_exactly_that_many(self) -> None:
        results, crawler = self.crawl_site(self.chain(10), max_pages=3, max_depth=10)

        self.assertEqual(len(results), 3)
        self.assertEqual(crawler.report.fetched, 3)
        self.assertEqual(crawler.report.fetches, 3)
        self.assertEqual(crawler.report.stopped_by, "max_pages")
        self.assertGreater(crawler.report.frontier_left, 0)

    def test_max_pages_of_zero_fetches_nothing(self) -> None:
        results, crawler = self.crawl_site(self.chain(3), max_pages=0)

        self.assertEqual(results, [])
        self.assertEqual(crawler.report.fetches, 0)
        self.assertEqual(self.opener.requests, [])
        self.assertEqual(crawler.report.stopped_by, "max_pages")

    def test_fetch_budget_counts_requests_not_documents(self) -> None:
        # Every page carries the same text, so nothing after the first is
        # yielded and only the fetch budget can end the crawl.
        same = html("dup")
        site = {f"{SITE}/": Reply(body=html("dup", tuple(f"/d{i}" for i in range(20))))}
        for i in range(20):
            site[f"{SITE}/d{i}"] = Reply(body=same)

        results, crawler = self.crawl_site(site, max_pages=50, max_fetches=4)

        # Four requests bought two documents: the budget has to count requests.
        self.assertEqual(len(results), 2)
        self.assertEqual(crawler.report.fetches, 4)
        self.assertEqual(len(self.opener.page_requests), 4)
        self.assertEqual(crawler.report.stopped_by, "fetch_budget")
        self.assertEqual(crawler.report.skipped["duplicate_content"], 2)
        self.assertEqual(crawler.report.skipped["fetch_budget"], crawler.report.frontier_left)

    def test_fetch_budget_defaults_to_five_per_page_with_a_floor_of_ten(self) -> None:
        # Every page is thin, so nothing is ever yielded and the derived fetch
        # budget is the only thing that can end the crawl.
        site = {f"{SITE}/": Reply(body=html("hub", tuple(f"/d{i}" for i in range(40)), words=2))}
        for i in range(40):
            site[f"{SITE}/d{i}"] = Reply(body=html(f"d{i}", words=2))

        _, one_page = self.crawl_site(site, max_pages=1, max_depth=3, min_words=200)
        self.assertEqual(one_page.report.fetched, 0)
        self.assertEqual(one_page.report.fetches, 10)  # floor, not 1 * 5
        self.assertEqual(one_page.report.stopped_by, "fetch_budget")

        _, four_pages = self.crawl_site(site, max_pages=4, max_depth=3, min_words=200)
        self.assertEqual(four_pages.report.fetches, 20)  # 4 * 5

    def test_depth_budget_is_inclusive_of_the_seed(self) -> None:
        site = self.chain(4)

        only_seed, report0 = self.crawl_site(site, max_depth=0)
        self.assertEqual(self.urls(only_seed), [f"{SITE}/"])
        self.assertEqual(report0.report.frontier_left, 0)  # nothing was enqueued

        one_hop, _ = self.crawl_site(site, max_depth=1)
        self.assertEqual(self.urls(one_hop), [f"{SITE}/", f"{SITE}/p0"])

        two_hops, _ = self.crawl_site(site, max_depth=2)
        self.assertEqual(self.urls(two_hops), [f"{SITE}/", f"{SITE}/p0", f"{SITE}/p1"])

    def test_time_budget_of_zero_is_respected_rather_than_unlimited(self) -> None:
        # Frozen clock: elapsed is exactly 0.0, which is the boundary. A budget
        # compared with `>` lets a zero-second crawl run the whole site.
        with mock.patch("oodarag.scrape.crawler.time.monotonic", lambda: 1_000.0):
            results, crawler = self.crawl_site(self.chain(3), max_seconds=0.0)

        self.assertEqual(results, [])
        self.assertEqual(self.opener.requests, [])
        self.assertEqual(crawler.report.stopped_by, "time_budget")
        self.assertEqual(crawler.report.skipped["time_budget"], 1)

    def test_time_budget_stops_the_crawl_and_accounts_for_the_frontier(self) -> None:
        ticks = itertools.count(0.0, 5.0)
        with mock.patch("oodarag.scrape.crawler.time.monotonic", lambda: next(ticks)):
            results, crawler = self.crawl_site(self.chain(20), max_seconds=30.0, max_depth=20)

        self.assertEqual(crawler.report.stopped_by, "time_budget")
        self.assertGreater(crawler.report.frontier_left, 0)
        self.assertEqual(crawler.report.skipped["time_budget"], crawler.report.frontier_left)
        self.assertLess(len(results), 20)

    def test_byte_budget_stops_after_one_response_over_the_line(self) -> None:
        results, crawler = self.crawl_site(self.chain(5), max_crawl_bytes=1, max_depth=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(crawler.report.fetches, 1)
        self.assertEqual(crawler.report.stopped_by, "byte_budget")
        self.assertGreaterEqual(crawler.report.bytes, 1)

    def test_byte_budget_of_zero_means_unlimited(self) -> None:
        results, crawler = self.crawl_site(self.chain(3), max_crawl_bytes=0, max_depth=5)

        self.assertEqual(len(results), 4)
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")

    def test_bytes_are_counted_even_for_documents_we_throw_away(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/img.bin",)),
            f"{SITE}/img.bin": Reply(body=b"\x00" * 900, ctype="application/octet-stream"),
        }
        _, crawler = self.crawl_site(site)

        self.assertEqual(crawler.report.skipped["ctype_application/octet-stream"], 1)
        self.assertGreater(crawler.report.bytes, 900)

    def test_frontier_is_capped_so_one_page_cannot_own_the_heap(self) -> None:
        links = tuple(f"/x{i}" for i in range(10))
        site = {f"{SITE}/": page("seed", links)}
        for i in range(10):
            site[f"{SITE}/x{i}"] = page(f"x{i}")

        with mock.patch.object(crawler_mod, "MAX_FRONTIER", 3):
            results, crawler = self.crawl_site(site, max_pages=50)

        self.assertEqual(crawler.report.skipped["frontier_full"], 7)
        self.assertEqual(len(results), 4)  # seed plus the three that fit


# ----------------------------------------------------------------------- scope


class ScopeTestCase(CrawlerTestCase):
    def test_offsite_links_are_never_requested(self) -> None:
        site = {
            f"{SITE}/": page("seed", (f"{OTHER}/x",)),
            f"{OTHER}/x": page("offsite"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["offsite"], 1)
        self.assertNotIn(f"{OTHER}/x", self.opener.requests)

    def test_offsite_links_are_followed_when_scope_is_off(self) -> None:
        site = {
            f"{SITE}/": page("seed", (f"{OTHER}/x",)),
            f"{OTHER}/x": page("offsite"),
        }
        results, _ = self.crawl_site(site, same_site_only=False)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{OTHER}/x"])

    def test_subdomains_are_in_scope_only_when_asked_for(self) -> None:
        sub = "https://docs.example.com/guide"
        site = {f"{SITE}/": page("seed", (sub,)), sub: page("guide")}

        included, _ = self.crawl_site(site, include_subdomains=True)
        self.assertEqual(self.urls(included), [f"{SITE}/", sub])

        excluded, crawler = self.crawl_site(site, include_subdomains=False)
        self.assertEqual(self.urls(excluded), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["offsite"], 1)

    def test_a_redirect_cannot_carry_the_crawl_off_site(self) -> None:
        # The gate ran against /hop, which is in scope. Only a second check
        # against the URL we landed on keeps this from being an SSRF.
        site = {
            f"{SITE}/": page("seed", ("/hop",)),
            f"{SITE}/hop": Reply(location=f"{OTHER}/evil"),
            f"{OTHER}/evil": page("evil"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["redirect_offsite"], 1)
        self.assertNotIn(f"{OTHER}/evil", [r.page.url for r in results])
        self.assertEqual(crawler.report.fetches, 2)  # the hop still cost a fetch

    def test_a_redirect_is_re_checked_against_the_exclude_patterns(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/hop",)),
            f"{SITE}/hop": Reply(location="/private/secret"),
            f"{SITE}/private/secret": page("secret"),
        }
        results, crawler = self.crawl_site(site, exclude_patterns=["/private/"])

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["redirect_exclude_pattern"], 1)

    def test_a_redirect_is_re_checked_against_robots(self) -> None:
        site = {
            f"{SITE}/robots.txt": Reply(body=b"User-agent: *\nDisallow: /private\n",
                                        ctype="text/plain"),
            f"{SITE}/": page("seed", ("/hop",)),
            f"{SITE}/hop": Reply(location="/private/secret"),
            f"{SITE}/private/secret": page("secret"),
        }
        results, crawler = self.crawl_site(site, obey_robots=True)

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["redirect_robots"], 1)

    def test_an_in_scope_redirect_chain_is_followed_and_reported_by_final_url(self) -> None:
        results, _ = self.crawl_site({
            f"{SITE}/": page("seed", ("/hop",)),
            f"{SITE}/hop": Reply(location="/hop2"),
            f"{SITE}/hop2": Reply(location="/landing"),
            f"{SITE}/landing": page("landing"),
        })

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/landing"])
        self.assertEqual(results[1].page.title, "landing")

    def test_a_redirect_loop_is_a_skip_not_a_hang(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/spin", "/good")),
            f"{SITE}/spin": Reply(location="/spin2"),
            f"{SITE}/spin2": Reply(location="/spin"),
            f"{SITE}/good": page("good"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/good"])
        self.assertEqual(crawler.report.skipped["http_302"], 1)

    def test_a_redirect_onto_an_already_seen_page_is_not_yielded_twice(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/a", "/alias")),
            f"{SITE}/a": page("a"),
            f"{SITE}/alias": Reply(location="/a"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a"])
        self.assertEqual(crawler.report.skipped["redirect_dupe"], 1)
        self.assertEqual(crawler.report.fetches, 3)  # the alias still cost one

    def test_robots_disallow_blocks_the_fetch_entirely(self) -> None:
        site = {
            f"{SITE}/robots.txt": Reply(body=b"User-agent: *\nDisallow: /private\n",
                                        ctype="text/plain"),
            f"{SITE}/": page("seed", ("/private/x", "/public")),
            f"{SITE}/private/x": page("private"),
            f"{SITE}/public": page("public"),
        }
        results, crawler = self.crawl_site(site, obey_robots=True)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/public"])
        self.assertEqual(crawler.report.skipped["robots"], 1)
        self.assertNotIn(f"{SITE}/private/x", self.opener.requests)

    def test_include_and_exclude_patterns_gate_the_frontier(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/docs/a", "/blog/b")),
            f"{SITE}/docs/a": page("docs"),
            f"{SITE}/blog/b": page("blog"),
        }
        # The seed is exempt - it is what the caller asked for - but everything
        # discovered from it has to match.
        included, crawler = self.crawl_site(site, include_patterns=[r"/docs/"])
        self.assertEqual(self.urls(included), [f"{SITE}/", f"{SITE}/docs/a"])
        self.assertEqual(crawler.report.skipped["include_pattern"], 1)

        excluded, crawler = self.crawl_site(site, exclude_patterns=[r"/blog/"])
        self.assertEqual(self.urls(excluded), [f"{SITE}/", f"{SITE}/docs/a"])
        self.assertEqual(crawler.report.skipped["exclude_pattern"], 1)

    def test_binary_extensions_are_never_requested(self) -> None:
        site = {f"{SITE}/": page("seed", ("/a.pdf", "/b.png", "/c.js?v=2"))}
        _, crawler = self.crawl_site(site)

        self.assertEqual(crawler.report.skipped["binary_ext"], 3)
        self.assertEqual(self.opener.page_requests, [f"{SITE}/"])

    def test_nofollow_links_are_skipped_unless_configured_otherwise(self) -> None:
        site = {
            f"{SITE}/": Reply(body=html("seed", (), nofollow=("/sponsored",))),
            f"{SITE}/sponsored": page("sponsored"),
        }
        results, crawler = self.crawl_site(site)
        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["nofollow"], 1)

        followed, _ = self.crawl_site(site, follow_nofollow=True)
        self.assertEqual(self.urls(followed), [f"{SITE}/", f"{SITE}/sponsored"])


# ------------------------------------------------------------------ termination


class TerminationTestCase(CrawlerTestCase):
    def test_a_cycle_terminates_and_fetches_each_page_once(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/a",)),
            f"{SITE}/a": page("a", ("/b", "/")),
            f"{SITE}/b": page("b", ("/a", "/b")),
        }
        results, crawler = self.crawl_site(site, max_depth=9, max_pages=100)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a", f"{SITE}/b"])
        self.assertEqual(crawler.report.fetches, 3)
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")

    def test_one_url_is_enqueued_once_however_it_is_spelled(self) -> None:
        variants = (
            "/a/",
            "/a/?utm_source=newsletter",
            "/a/#section",
            "HTTPS://EXAMPLE.COM/a/",
            "https://example.com:443/a/",
            "/a/index.html",
        )
        site = {f"{SITE}/": page("seed", variants), f"{SITE}/a/": page("a")}

        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a/"])
        self.assertEqual(crawler.report.fetches, 2)

    def test_a_seed_that_cannot_be_parsed_is_a_skip_not_a_crash(self) -> None:
        # urlsplit raises ValueError on this; one bad seed must not end a crawl.
        results, crawler = self.crawl_site(
            {f"{SITE}/": page("seed")}, seeds=["http://[::1/x", f"{SITE}/"]
        )

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["unparseable"], 1)

    def test_a_report_is_finalised_even_when_the_consumer_stops_pulling(self) -> None:
        crawler = self.crawler(self.big_site(), max_pages=50, max_depth=3)
        stream = crawler.crawl()

        first = list(itertools.islice(stream, 2))
        stream.close()

        self.assertEqual(len(first), 2)
        self.assertEqual(crawler.report.stopped_by, "abandoned")
        self.assertGreater(crawler.report.frontier_left, 0)
        self.assertGreater(crawler.report.duration_s, 0.0)

    def big_site(self) -> dict[str, Reply]:
        site = {f"{SITE}/": page("seed", tuple(f"/p{i}" for i in range(8)))}
        for i in range(8):
            site[f"{SITE}/p{i}"] = page(f"p{i}")
        return site


# -------------------------------------------------------------------- failures


class FailureTestCase(CrawlerTestCase):
    def test_a_404_and_a_500_are_skips_the_crawl_survives(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/missing", "/boom", "/good")),
            f"{SITE}/missing": Reply(status=404, body=b"nope"),
            f"{SITE}/boom": Reply(status=500, body=b"kaboom"),
            f"{SITE}/good": page("good"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/good"])
        self.assertEqual(crawler.report.skipped["http_404"], 1)
        self.assertEqual(crawler.report.skipped["http_500"], 1)
        self.assertEqual(
            sorted(crawler.report.errors),
            [(f"{SITE}/boom", "http 500"), (f"{SITE}/missing", "http 404")],
        )

    def test_a_response_past_the_byte_cap_is_a_skip_not_an_abort(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/huge", "/good")),
            f"{SITE}/huge": Reply(body=b"x" * 50_000),
            f"{SITE}/good": page("good"),
        }
        crawler = self.crawler(site, client=self.client(max_bytes=5_000))
        results = list(crawler.crawl())

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/good"])
        self.assertEqual(crawler.report.skipped["transport"], 1)
        self.assertIn("too large", crawler.report.errors[0][1])

    def test_a_transport_failure_is_a_skip(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/dead", "/good")),
            f"{SITE}/dead": Reply(error=urllib.error.URLError("name resolution failed")),
            f"{SITE}/good": page("good"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/good"])
        self.assertEqual(crawler.report.skipped["transport"], 1)

    def test_a_host_that_keeps_failing_is_backed_off_not_hammered(self) -> None:
        count = MAX_HOST_FAILURES + 4
        site = {f"{SITE}/": page("seed", tuple(f"/e{i}" for i in range(count)))}
        for i in range(count):
            site[f"{SITE}/e{i}"] = Reply(status=503, body=b"down")

        _, crawler = self.crawl_site(site, max_pages=50)

        self.assertEqual(crawler.report.skipped["http_503"], MAX_HOST_FAILURES)
        self.assertEqual(crawler.report.skipped["host_unavailable"], 4)
        # One request for the seed plus exactly the failures we allowed.
        self.assertEqual(len(self.opener.page_requests), 1 + MAX_HOST_FAILURES)

    def test_missing_pages_do_not_trip_the_host_breaker(self) -> None:
        count = MAX_HOST_FAILURES + 4
        site = {f"{SITE}/": page("seed", tuple(f"/m{i}" for i in range(count)))}
        for i in range(count):
            site[f"{SITE}/m{i}"] = Reply(status=404, body=b"nope")

        _, crawler = self.crawl_site(site, max_pages=50)

        self.assertEqual(crawler.report.skipped["http_404"], count)
        self.assertNotIn("host_unavailable", crawler.report.skipped)

    def test_one_good_response_clears_the_failure_streak(self) -> None:
        links = ["/e0", "/e1", "/e2", "/e3", "/ok", "/e4", "/e5", "/late"]
        site = {f"{SITE}/": page("seed", tuple(links))}
        for name in links:
            site[f"{SITE}{name}"] = Reply(status=503, body=b"down")
        site[f"{SITE}/ok"] = page("ok")
        site[f"{SITE}/late"] = page("late")

        results, crawler = self.crawl_site(site, max_pages=50)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/ok", f"{SITE}/late"])
        self.assertNotIn("host_unavailable", crawler.report.skipped)

    def test_an_unextractable_page_is_skipped_and_the_crawl_continues(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/bad", "/good")),
            f"{SITE}/bad": page("bad"),
            f"{SITE}/good": page("good"),
        }
        real = crawler_mod.extract

        def explode(text: str, url: str = "", **kw: Any) -> Any:
            if url.endswith("/bad"):
                raise RecursionError("maximum recursion depth exceeded")
            return real(text, url, **kw)

        with mock.patch.object(crawler_mod, "extract", explode):
            results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/good"])
        self.assertEqual(crawler.report.skipped["extract_error"], 1)
        self.assertEqual(crawler.report.errors, [(f"{SITE}/bad", "extract: RecursionError")])

    def test_a_304_is_not_a_document(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/cached",)),
            f"{SITE}/cached": Reply(status=304),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/"])
        self.assertEqual(crawler.report.skipped["not_modified"], 1)
        self.assertEqual(crawler.report.errors, [])

    def test_a_hostile_content_type_cannot_grow_the_report(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/weird",)),
            f"{SITE}/weird": Reply(body=b"...", ctype="application/" + "z" * 500),
        }
        _, crawler = self.crawl_site(site)

        key = next(k for k in crawler.report.skipped if k.startswith("ctype_"))
        self.assertLessEqual(len(key), len("ctype_") + 40)


# --------------------------------------------------------------------- dedupe


class DedupeTestCase(CrawlerTestCase):
    def test_identical_content_under_two_urls_is_yielded_once(self) -> None:
        body = html("shared")
        site = {
            f"{SITE}/": page("seed", ("/one", "/two")),
            f"{SITE}/one": Reply(body=body),
            f"{SITE}/two": Reply(body=body),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/one"])
        self.assertEqual(crawler.report.skipped["duplicate_content"], 1)

    def test_a_declared_canonical_collapses_a_version_pinned_pair(self) -> None:
        # Different text on each page, so only the canonical link can dedupe
        # them - and the canonical page itself must not slip through as a
        # second copy just because it is its own canonical.
        site = {
            f"{SITE}/": page("seed", ("/latest/", "/stable/")),
            f"{SITE}/latest/": page("latest", canonical=f"{SITE}/stable/"),
            f"{SITE}/stable/": page("stable", canonical=f"{SITE}/stable/"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/latest/"])
        self.assertEqual(crawler.report.skipped["duplicate_canonical"], 1)

    def test_canonical_dedupe_can_be_switched_off(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/latest/", "/stable/")),
            f"{SITE}/latest/": page("latest", canonical=f"{SITE}/stable/"),
            f"{SITE}/stable/": page("stable", canonical=f"{SITE}/stable/"),
        }
        results, _ = self.crawl_site(site, dedupe_canonical=False)

        self.assertEqual(len(results), 3)

    def test_a_thin_page_is_skipped_but_its_links_are_still_followed(self) -> None:
        site = {
            f"{SITE}/": Reply(body=html("hub", ("/deep",), words=3)),
            f"{SITE}/deep": page("deep"),
        }
        results, crawler = self.crawl_site(site)

        self.assertEqual(self.urls(results), [f"{SITE}/deep"])
        self.assertEqual(crawler.report.skipped["thin"], 1)


# ------------------------------------------------------------------- sitemaps


def sitemap(*locs: str) -> bytes:
    body = "".join(f"<url><loc>{loc}</loc></url>" for loc in locs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
    ).encode()


def sitemap_index(*locs: str) -> bytes:
    body = "".join(f"<sitemap><loc>{loc}</loc></sitemap>" for loc in locs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</sitemapindex>'
    ).encode()


class SitemapTestCase(CrawlerTestCase):
    def test_sitemap_urls_are_crawled_as_seeds_not_as_links(self) -> None:
        # depth 0: a sitemap is the seed's own inventory. Filed one level down,
        # `max_depth=0` would discover the sitemap and then refuse every URL.
        site = {
            f"{SITE}/sitemap.xml": Reply(body=sitemap(f"{SITE}/a", f"{SITE}/b"),
                                         ctype="application/xml"),
            f"{SITE}/": page("seed"),
            f"{SITE}/a": page("a"),
            f"{SITE}/b": page("b"),
        }
        results, _ = self.crawl_site(site, use_sitemap=True, max_depth=0)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a", f"{SITE}/b"])

    def test_sitemap_requests_are_charged_to_the_fetch_budget(self) -> None:
        site = {
            f"{SITE}/sitemap.xml": Reply(body=sitemap(f"{SITE}/a"), ctype="application/xml"),
            f"{SITE}/": page("seed"),
            f"{SITE}/a": page("a"),
        }
        _, crawler = self.crawl_site(site, use_sitemap=True, max_fetches=2)

        # One sitemap request plus one page: the budget stops it there.
        self.assertEqual(crawler.report.fetches, 2)
        self.assertEqual(crawler.report.stopped_by, "fetch_budget")

    def test_an_offsite_sitemap_is_not_fetched(self) -> None:
        site = {
            f"{SITE}/robots.txt": Reply(
                body=f"Sitemap: {OTHER}/sitemap.xml\nSitemap: {SITE}/sitemap.xml\n".encode(),
                ctype="text/plain",
            ),
            f"{SITE}/sitemap.xml": Reply(body=sitemap(f"{SITE}/a"), ctype="application/xml"),
            f"{OTHER}/sitemap.xml": Reply(body=sitemap(f"{OTHER}/evil"), ctype="application/xml"),
            f"{SITE}/": page("seed"),
            f"{SITE}/a": page("a"),
        }
        results, _ = self.crawl_site(site, use_sitemap=True, obey_robots=True)

        self.assertNotIn(f"{OTHER}/sitemap.xml", self.opener.requests)
        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a"])

    def test_a_sitemap_index_is_followed_as_sitemaps_not_as_pages(self) -> None:
        site = {
            f"{SITE}/sitemap.xml": Reply(body=sitemap_index(f"{SITE}/inner.xml"),
                                         ctype="application/xml"),
            f"{SITE}/inner.xml": Reply(body=sitemap(f"{SITE}/a"), ctype="application/xml"),
            f"{SITE}/": page("seed"),
            f"{SITE}/a": page("a"),
        }
        results, crawler = self.crawl_site(site, use_sitemap=True)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a"])
        self.assertNotIn("ctype_application/xml", crawler.report.skipped)

    def test_sitemap_index_recursion_is_bounded(self) -> None:
        # Every index points at the next one; without a bound this walks forever.
        site: dict[str, Reply] = {f"{SITE}/": page("seed")}
        for i in range(20):
            site[f"{SITE}/map{i}.xml"] = Reply(body=sitemap_index(f"{SITE}/map{i + 1}.xml"),
                                               ctype="application/xml")
        site[f"{SITE}/sitemap.xml"] = site[f"{SITE}/map0.xml"]

        _, crawler = self.crawl_site(site, use_sitemap=True)

        maps = [u for u in self.opener.requests if u.endswith(".xml")]
        self.assertLessEqual(len(maps), MAX_SITEMAP_FETCHES)

    def test_a_sitemap_with_a_dtd_is_refused_before_it_is_parsed(self) -> None:
        bomb = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;">]>'
            b"<urlset><url><loc>https://example.com/a</loc></url></urlset>"
        )
        site = {
            f"{SITE}/sitemap.xml": Reply(body=bomb, ctype="application/xml"),
            f"{SITE}/": page("seed"),
            f"{SITE}/a": page("a"),
        }
        results, _ = self.crawl_site(site, use_sitemap=True)

        self.assertEqual(self.urls(results), [f"{SITE}/"])

    def test_an_unparseable_or_missing_sitemap_leaves_the_crawl_running(self) -> None:
        site = {
            f"{SITE}/sitemap.xml": Reply(body=b"<urlset><broken>", ctype="application/xml"),
            f"{SITE}/": page("seed"),
        }
        results, crawler = self.crawl_site(site, use_sitemap=True)
        self.assertEqual(self.urls(results), [f"{SITE}/"])

        missing = {f"{SITE}/": page("seed")}
        results, _ = self.crawl_site(missing, use_sitemap=True)
        self.assertEqual(self.urls(results), [f"{SITE}/"])

    def test_sitemap_urls_are_still_gated_by_scope(self) -> None:
        site = {
            f"{SITE}/sitemap.xml": Reply(body=sitemap(f"{OTHER}/evil", f"{SITE}/a"),
                                         ctype="application/xml"),
            f"{SITE}/": page("seed"),
            f"{SITE}/a": page("a"),
            f"{OTHER}/evil": page("evil"),
        }
        results, crawler = self.crawl_site(site, use_sitemap=True)

        self.assertEqual(self.urls(results), [f"{SITE}/", f"{SITE}/a"])
        self.assertEqual(crawler.report.skipped["offsite"], 1)
        self.assertNotIn(f"{OTHER}/evil", self.opener.requests)


# --------------------------------------------------------------------- report


class ReportTestCase(CrawlerTestCase):
    def test_the_report_explains_a_thin_crawl(self) -> None:
        crawler = self.crawler(demo_site(), max_depth=2, max_pages=50,
                               client=self.client(max_bytes=5_000))
        results = list(crawler.crawl())
        report = crawler.report.as_dict()

        self.assertEqual(
            self.urls(results),
            [f"{SITE}/", f"{SITE}/a", f"{SITE}/b", f"{SITE}/loop", f"{SITE}/landing"],
        )
        self.assertEqual(report["fetched"], 5)
        self.assertEqual(report["stopped_by"], "frontier_exhausted")
        skipped = report["skipped"]
        self.assertEqual(skipped["offsite"], 1)
        self.assertEqual(skipped["http_404"], 1)
        self.assertEqual(skipped["http_500"], 1)
        self.assertEqual(skipped["transport"], 1)  # the oversize page
        self.assertEqual(report["error_count"], 3)
        self.assertEqual(report["fetches"], 8)
        self.assertGreater(report["bytes"], 0)
        self.assertEqual(report["frontier_left"], 0)

    def test_the_error_list_is_truncated_in_the_report_but_counted_in_full(self) -> None:
        count = 30
        site = {f"{SITE}/": page("seed", tuple(f"/m{i}" for i in range(count)))}
        for i in range(count):
            site[f"{SITE}/m{i}"] = Reply(status=404, body=b"nope")

        _, crawler = self.crawl_site(site, max_pages=50)
        report = crawler.report.as_dict()

        self.assertEqual(len(report["errors"]), 20)
        self.assertEqual(report["error_count"], count)

    def test_credentials_in_a_seed_never_reach_the_report_or_the_results(self) -> None:
        site = {f"{SITE}/": page("seed", ("/boom",)), f"{SITE}/boom": Reply(status=500)}

        results, crawler = self.crawl_site(site, seeds=["https://user:hunter2@example.com/"])

        blob = repr(crawler.report.as_dict()) + repr(self.urls(results))
        self.assertNotIn("hunter2", blob)
        self.assertEqual(crawler.report.skipped["http_500"], 1)


# ------------------------------------------------------------------- throttling


class ThrottleTestCase(CrawlerTestCase):
    def test_the_configured_delay_is_applied_between_hits_on_a_host(self) -> None:
        site = {
            f"{SITE}/": page("seed", ("/a",)),
            f"{SITE}/a": page("a"),
        }
        _, crawler = self.crawl_site(site, delay_s=0.25)

        waits = [call.args[0] for call in self.sleep.call_args_list]
        self.assertEqual(len(waits), 1)  # nothing to wait for on the first hit
        self.assertGreater(waits[0], 0.0)
        self.assertLessEqual(waits[0], 0.25)
        self.assertEqual(crawler.report.fetched, 2)

    def test_no_delay_means_no_sleeping(self) -> None:
        self.crawl_site({f"{SITE}/": page("seed")})
        self.sleep.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
