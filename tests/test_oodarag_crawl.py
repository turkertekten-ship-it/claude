"""The crawler and the robots.txt gate, driven entirely offline.

Every request in this file is served from a dict by `FakeHttp`. That is not
only about CI having no egress: a crawler test that reaches a real site is
testing the site, and the interesting cases here - a 5xx robots.txt, a redirect
onto an already-seen URL, a page whose canonical points elsewhere - are ones no
real site will reliably produce on demand.

The package's stated principle is "degrade, don't die", so the failure paths
(malformed URLs, truncated XML, transport errors, exhausted budgets) get as
much room as the happy path.
"""

from __future__ import annotations

import time
import unittest

from oodarag.scrape.crawler import CrawlConfig, Crawler
from oodarag.scrape.robots import RobotsPolicy
from oodarag.util.http import HttpClient, HttpError, Response, TransportError

UA = "oodarag/0.1 (+https://example.invalid/bot)"


# --------------------------------------------------------------------- fixtures


class FakeHttp(HttpClient):
    """An `HttpClient` that serves a small site out of a dict.

    Entries are `{"body": str|bytes, "status": int, "ctype": str, "final": str}`
    or `{"raise": Exception}`. A URL that is not in the dict is a 404, which is
    also how a host with no robots.txt behaves.
    """

    def __init__(self, site: dict[str, dict], *, latency: float = 0.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.site = site
        self.requested: list[str] = []
        self.latency = latency

    def request(self, method, url, *, headers=None, body=None, conditional=False,
                allow_status=()):
        self.requested.append(url)
        if self.latency:
            time.sleep(self.latency)
        entry = self.site.get(url, {"status": 404})
        if "raise" in entry:
            raise entry["raise"]
        status = entry.get("status", 200)
        if status >= 400 and status not in allow_status:
            raise HttpError(status, url)
        payload = entry.get("body", "")
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        return Response(
            url=entry.get("final", url),
            status=status,
            headers={"content-type": entry.get("ctype", "text/html; charset=utf-8")},
            body=payload,
        )


def words(tag: str, n: int = 80) -> str:
    """`n` distinct words, so two pages built with different tags never collide
    in the content hash and `min_words` is comfortably cleared."""
    return " ".join(f"{tag}{i}" for i in range(n))


def doc(body: str, *, links=(), canonical: str = "", title: str = "T") -> dict:
    head = f"<title>{title}</title>"
    if canonical:
        head += f'<link rel="canonical" href="{canonical}">'
    anchors = "".join(f'<a href="{u}"{extra}>link</a>' for u, extra in _pairs(links))
    return {"body": f"<html><head>{head}</head><body><article><p>{body}</p>"
                    f"{anchors}</article></body></html>"}


def _pairs(links):
    for item in links:
        yield item if isinstance(item, tuple) else (item, "")


def robots(body: str) -> dict:
    return {"body": body, "ctype": "text/plain"}


def crawl(site: dict[str, dict], **config) -> tuple[Crawler, list]:
    config.setdefault("max_pages", 20)
    crawler = Crawler(CrawlConfig(**config), client=FakeHttp(site))
    return crawler, list(crawler.crawl())


# ------------------------------------------------------------------ robots.txt


class TestRobotsStatusHandling(unittest.TestCase):
    """RFC 9309 makes the *status* of robots.txt load-bearing, so each branch
    gets its own case: getting one wrong either blocks a crawl entirely or
    crawls a site that said no."""

    def policy(self, entry: dict, **kw) -> RobotsPolicy:
        return RobotsPolicy(client=FakeHttp({"https://h.test/robots.txt": entry}),
                            user_agent=UA, **kw)

    def test_rules_from_a_200_are_obeyed(self):
        p = self.policy(robots("User-agent: *\nDisallow: /private/\n"))
        self.assertTrue(p.allows("https://h.test/docs/a"))
        self.assertFalse(p.allows("https://h.test/private/a"))

    def test_a_404_means_no_restrictions(self):
        p = self.policy({"status": 404})
        self.assertTrue(p.allows("https://h.test/anything"))
        self.assertEqual(p.rules_for("https://h.test/").status, 404)

    def test_a_410_means_no_restrictions(self):
        # 410 is a 4xx and RFC 9309 groups it with "unavailable": crawl freely.
        self.assertTrue(self.policy({"status": 410}).allows("https://h.test/x"))

    def test_401_and_403_disallow_everything(self):
        # Access to the rules is itself restricted; assuming permission there
        # is how a crawler ends up blocked at the network edge.
        for status in (401, 403):
            with self.subTest(status=status):
                p = self.policy({"status": status})
                self.assertFalse(p.allows("https://h.test/x"))
                self.assertTrue(p.rules_for("https://h.test/").disallow_all)

    def test_a_5xx_disallows_everything_by_default(self):
        p = self.policy({"status": 503})
        self.assertFalse(p.allows("https://h.test/x"))
        # The status is recorded as 0, not 503: the fetch never produced rules.
        self.assertEqual(p.rules_for("https://h.test/").status, 0)

    def test_a_5xx_allows_everything_under_on_error_allow(self):
        self.assertTrue(self.policy({"status": 503}, on_error="allow").allows("https://h.test/x"))

    def test_a_transport_failure_follows_the_on_error_policy(self):
        deny = self.policy({"raise": TransportError("dns failure")})
        allow = self.policy({"raise": TransportError("dns failure")}, on_error="allow")
        self.assertFalse(deny.allows("https://h.test/x"))
        self.assertTrue(allow.allows("https://h.test/x"))

    def test_obey_false_never_fetches_and_never_blocks(self):
        p = self.policy(robots("User-agent: *\nDisallow: /\n"), obey=False)
        self.assertTrue(p.allows("https://h.test/x"))
        self.assertEqual(p.client.requested, [])

    def test_an_unparseable_robots_txt_does_not_raise(self):
        # Real robots.txt files contain HTML error pages, NUL bytes and
        # directives with no colon. Any of those raising here would take the
        # whole crawl down before the first page was fetched.
        for body in ("\x00\x01\xff <html>404</html>", "Disallow /no-colon",
                     "Disallow: /rule-before-any-user-agent\n", ":::\n" * 50, ""):
            with self.subTest(body=body[:20]):
                p = self.policy(robots(body))
                self.assertIsInstance(p.allows("https://h.test/x"), bool)


class TestRobotsRules(unittest.TestCase):
    def policy(self, body: str, **kw) -> RobotsPolicy:
        return RobotsPolicy(client=FakeHttp({"https://h.test/robots.txt": robots(body)}),
                            user_agent=UA, **kw)

    def test_a_wildcard_group_applies_when_no_named_group_matches(self):
        p = self.policy("User-agent: googlebot\nDisallow: /\n\n"
                        "User-agent: *\nDisallow: /admin/\n")
        self.assertTrue(p.allows("https://h.test/docs/"))
        self.assertFalse(p.allows("https://h.test/admin/x"))

    def test_a_named_group_wins_over_the_wildcard_group(self):
        p = self.policy("User-agent: oodarag\nDisallow: /ours/\n\n"
                        "User-agent: *\nDisallow: /\n")
        self.assertTrue(p.allows("https://h.test/anything"))
        self.assertFalse(p.allows("https://h.test/ours/x"))

    def test_allow_beats_a_broader_disallow_regardless_of_line_order(self):
        # Bug (fixed): `urllib.robotparser` returns the *first* matching rule in
        # file order, but RFC 9309 2.2.2 says the longest match wins. The
        # standard "close the section, open a subtree" shape below is written
        # Disallow-first by nearly every site that uses it, so a docs site that
        # published /docs/public/ yielded zero pages instead of its whole public
        # corpus - and the crawl report just said "robots".
        p = self.policy("User-agent: *\nDisallow: /docs/\nAllow: /docs/public/\n")
        self.assertFalse(p.allows("https://h.test/docs/internal/x"))
        self.assertTrue(p.allows("https://h.test/docs/public/x"))

    def test_an_equal_length_allow_and_disallow_resolves_to_allow(self):
        p = self.policy("User-agent: *\nDisallow: /x\nAllow: /x\n")
        self.assertTrue(p.allows("https://h.test/x"))

    def test_an_empty_disallow_permits_everything(self):
        self.assertTrue(self.policy("User-agent: *\nDisallow:\n").allows("https://h.test/x"))

    def test_a_fractional_crawl_delay_is_honoured(self):
        # Bug (fixed): the stdlib parser accepts a delay only when the value
        # `.isdigit()`, so `Crawl-delay: 0.5` parsed to no delay at all and the
        # crawler went straight back to its own rate - the exact "get the IP
        # blocked" outcome this module exists to prevent.
        self.assertEqual(self.policy("User-agent: *\nCrawl-delay: 0.5\n")
                         .crawl_delay("https://h.test/x"), 0.5)

    def test_an_integer_crawl_delay_is_honoured(self):
        self.assertEqual(self.policy("User-agent: *\nCrawl-delay: 3\n")
                         .crawl_delay("https://h.test/x"), 3.0)

    def test_a_named_groups_crawl_delay_wins_over_the_wildcards(self):
        p = self.policy("User-agent: oodarag\nCrawl-delay: 0.25\n\n"
                        "User-agent: *\nCrawl-delay: 30\n")
        self.assertEqual(p.crawl_delay("https://h.test/x"), 0.25)

    def test_a_nonsense_crawl_delay_is_no_delay(self):
        self.assertEqual(self.policy("User-agent: *\nCrawl-delay: soon\n")
                         .crawl_delay("https://h.test/x"), 0.0)

    def test_sitemap_directives_are_surfaced(self):
        p = self.policy("User-agent: *\nSitemap: https://h.test/a.xml\n"
                        "Sitemap: https://h.test/b.xml\n")
        self.assertEqual(p.sitemaps("https://h.test/x"),
                         ["https://h.test/a.xml", "https://h.test/b.xml"])


class TestRobotsCacheAndExplain(unittest.TestCase):
    def test_a_second_call_within_the_ttl_does_not_refetch(self):
        client = FakeHttp({"https://h.test/robots.txt": robots("User-agent: *\nDisallow: /p/\n")})
        p = RobotsPolicy(client=client, user_agent=UA, ttl_s=3600.0)
        for _ in range(5):
            p.allows("https://h.test/a")
            p.crawl_delay("https://h.test/a")
            p.sitemaps("https://h.test/a")
        self.assertEqual(client.requested, ["https://h.test/robots.txt"])

    def test_an_expired_ttl_refetches(self):
        client = FakeHttp({"https://h.test/robots.txt": robots("User-agent: *\n")})
        p = RobotsPolicy(client=client, user_agent=UA, ttl_s=0.0)
        p.allows("https://h.test/a")
        p.allows("https://h.test/a")
        self.assertEqual(len(client.requested), 2)

    def test_each_host_is_cached_separately(self):
        site = {"https://a.test/robots.txt": robots("User-agent: *\nDisallow: /\n"),
                "https://b.test/robots.txt": robots("User-agent: *\n")}
        p = RobotsPolicy(client=FakeHttp(site), user_agent=UA)
        self.assertFalse(p.allows("https://a.test/x"))
        self.assertTrue(p.allows("https://b.test/x"))

    def test_explain_names_the_rule_that_blocked_the_url(self):
        # A crawl that returns 4 pages instead of 400 has to be diagnosable
        # without a debugger; "allowed: false" alone sends the reader back to
        # robots.txt to guess which of forty Disallow lines mattered.
        p = RobotsPolicy(
            client=FakeHttp({"https://h.test/robots.txt": robots(
                "User-agent: *\nDisallow: /a/\nDisallow: /private/\nCrawl-delay: 2\n"
                "Sitemap: https://h.test/s.xml\n")}),
            user_agent=UA,
        )
        blocked = p.explain("https://h.test/private/deep/page")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["rule"], "Disallow: /private/")
        self.assertEqual(blocked["robots_status"], 200)
        self.assertEqual(blocked["crawl_delay"], 2.0)
        self.assertEqual(blocked["sitemaps"], ["https://h.test/s.xml"])
        self.assertTrue(p.explain("https://h.test/ok")["allowed"])

    def test_explain_reports_a_restricted_robots_txt_as_disallow_all(self):
        p = RobotsPolicy(client=FakeHttp({"https://h.test/robots.txt": {"status": 403}}),
                         user_agent=UA)
        detail = p.explain("https://h.test/x")
        self.assertFalse(detail["allowed"])
        self.assertTrue(detail["disallow_all"])
        self.assertEqual(detail["robots_status"], 403)


# --------------------------------------------------------------------- budgets


class TestCrawlBudgets(unittest.TestCase):
    def hub_site(self, n: int, *, unique: bool) -> dict:
        """A hub page linking to `n` others. With `unique=False` every linked
        page carries identical text, so the whole site collapses to one document
        no matter how many URLs are fetched."""
        targets = [f"https://b.test/p{i}" for i in range(n)]
        site = {"https://b.test/": doc(words("hub"), links=targets)}
        for i, url in enumerate(targets):
            site[url] = doc(words(f"p{i}") if unique else words("same"))
        return site

    def test_max_pages_stops_the_crawl_and_is_named_in_the_report(self):
        crawler, pages = crawl(self.hub_site(10, unique=True),
                               seeds=["https://b.test/"], max_pages=4)
        self.assertEqual(len(pages), 4)
        self.assertEqual(crawler.report.stopped_by, "max_pages")
        self.assertGreater(crawler.report.frontier_left, 0)

    def test_max_fetches_stops_a_site_that_dedupes_to_a_single_document(self):
        # This is the case the CrawlConfig comment describes: versioned docs,
        # print views and session ids all render the same document, so
        # `max_pages` is never reached and only a request cap ends the crawl.
        # Without one the crawler happily spends every URL on the site to
        # produce one result.
        site = self.hub_site(40, unique=False)
        unbounded, pages = crawl(site, seeds=["https://b.test/"], max_pages=50)
        # The hub, plus one document standing in for all forty of its targets.
        self.assertEqual(len(pages), 2)
        self.assertEqual(unbounded.report.fetches, 41)
        self.assertEqual(unbounded.report.skipped["duplicate_content"], 39)

        bounded, pages = crawl(site, seeds=["https://b.test/"], max_pages=50, max_fetches=5)
        self.assertEqual(len(pages), 2)
        self.assertEqual(bounded.report.fetches, 5)
        self.assertEqual(bounded.report.stopped_by, "fetch_budget")
        # Everything still queued is accounted for rather than silently dropped.
        self.assertEqual(bounded.report.skipped["fetch_budget"], bounded.report.frontier_left)

    def test_max_depth_bounds_how_far_links_are_followed(self):
        site = {
            "https://b.test/": doc(words("d0"), links=["https://b.test/one"]),
            "https://b.test/one": doc(words("d1"), links=["https://b.test/two"]),
            "https://b.test/two": doc(words("d2"), links=["https://b.test/three"]),
            "https://b.test/three": doc(words("d3")),
        }
        crawler, pages = crawl(site, seeds=["https://b.test/"], max_depth=1)
        self.assertEqual([p.url for p in pages], ["https://b.test/", "https://b.test/one"])
        self.assertEqual([p.depth for p in pages], [0, 1])
        # Nothing beyond the limit is ever enqueued, so the frontier empties.
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")
        self.assertEqual(crawler.report.frontier_left, 0)

    def test_max_seconds_stops_the_crawl_and_is_named_in_the_report(self):
        site = self.hub_site(8, unique=True)
        crawler = Crawler(
            CrawlConfig(seeds=["https://b.test/"], max_pages=50, max_seconds=0.02),
            client=FakeHttp(site, latency=0.05),
        )
        pages = list(crawler.crawl())
        self.assertEqual(crawler.report.stopped_by, "time_budget")
        self.assertLess(len(pages), 8)
        self.assertGreater(crawler.report.frontier_left, 0)
        self.assertEqual(crawler.report.skipped["time_budget"], crawler.report.frontier_left)


# ---------------------------------------------------------------------- dedupe


class TestCrawlDedupe(unittest.TestCase):
    def test_identical_content_under_two_urls_yields_one_page(self):
        site = {
            "https://d.test/": doc(words("hub"), links=["https://d.test/a", "https://d.test/b"]),
            "https://d.test/a": doc(words("body")),
            "https://d.test/b": doc(words("body")),
        }
        crawler, pages = crawl(site, seeds=["https://d.test/"])
        self.assertEqual([p.url for p in pages], ["https://d.test/", "https://d.test/a"])
        self.assertEqual(crawler.report.skipped["duplicate_content"], 1)

    def test_a_declared_canonical_pointing_elsewhere_skips_the_duplicate(self):
        site = {
            "https://d.test/": doc(words("hub"),
                                   links=["https://d.test/stable/", "https://d.test/3.11/"]),
            "https://d.test/stable/": doc(words("stable"), canonical="https://d.test/stable/"),
            "https://d.test/3.11/": doc(words("pinned"), canonical="https://d.test/stable/"),
        }
        crawler, pages = crawl(site, seeds=["https://d.test/"])
        self.assertEqual([p.url for p in pages], ["https://d.test/", "https://d.test/stable/"])
        self.assertEqual(crawler.report.skipped["duplicate_canonical"], 1)

    def test_canonical_dedupe_does_not_depend_on_which_url_is_reached_first(self):
        # Bug (fixed): a page whose canonical is itself was exempt from the
        # duplicate check, so the dedupe only worked in one direction. Reaching
        # /3.11/ before /stable/ - the normal order when a site is seeded at a
        # version-pinned URL - kept both, and the retriever then returned the
        # same passage twice, which is what dedupe exists to prevent.
        site = {
            "https://d.test/3.11/": doc(words("pinned"), canonical="https://d.test/stable/",
                                        links=["https://d.test/stable/"]),
            "https://d.test/stable/": doc(words("stable"), canonical="https://d.test/stable/"),
        }
        crawler, pages = crawl(site, seeds=["https://d.test/3.11/"])
        self.assertEqual([p.url for p in pages], ["https://d.test/3.11/"])
        self.assertEqual(crawler.report.skipped["duplicate_canonical"], 1)

    def test_pages_without_a_canonical_are_not_deduped_against_each_other(self):
        # An absent canonical is not a shared canonical; treating "" as a key
        # would collapse an entire site into its first page.
        site = {
            "https://d.test/": doc(words("hub"), links=["https://d.test/a", "https://d.test/b"]),
            "https://d.test/a": doc(words("aaa")),
            "https://d.test/b": doc(words("bbb")),
        }
        _, pages = crawl(site, seeds=["https://d.test/"])
        self.assertEqual(len(pages), 3)

    def test_dedupe_canonical_off_keeps_both_copies(self):
        site = {
            "https://d.test/": doc(words("hub"),
                                   links=["https://d.test/stable/", "https://d.test/3.11/"]),
            "https://d.test/stable/": doc(words("stable"), canonical="https://d.test/stable/"),
            "https://d.test/3.11/": doc(words("pinned"), canonical="https://d.test/stable/"),
        }
        crawler, pages = crawl(site, seeds=["https://d.test/"], dedupe_canonical=False)
        self.assertEqual(len(pages), 3)
        self.assertNotIn("duplicate_canonical", crawler.report.skipped)

    def test_a_malformed_canonical_costs_the_dedupe_not_the_page(self):
        # `<link rel="canonical">` is site-authored and absolute hrefs are passed
        # through untouched, so a broken one reaches the crawler intact. It must
        # cost this page its canonical dedupe, not its place in the corpus.
        site = {"https://d.test/": doc(words("body"), canonical="http://d.test:80x/p")}
        crawler, pages = crawl(site, seeds=["https://d.test/"])
        self.assertEqual([p.url for p in pages], ["https://d.test/"])
        self.assertEqual(crawler.report.skipped["bad_canonical"], 1)

    def test_a_redirect_onto_an_already_seen_url_is_skipped(self):
        site = {
            "https://d.test/": doc(words("hub"),
                                   links=["https://d.test/a", "https://d.test/alias"]),
            "https://d.test/a": doc(words("body")),
            # /alias 30x-es onto /a, which the crawler has already indexed.
            "https://d.test/alias": {**doc(words("body")), "final": "https://d.test/a"},
        }
        crawler, pages = crawl(site, seeds=["https://d.test/"])
        self.assertEqual([p.url for p in pages], ["https://d.test/", "https://d.test/a"])
        self.assertEqual(crawler.report.skipped["redirect_dupe"], 1)
        # The redirect branch runs before content hashing, so the reason
        # reported is the one that actually decided it.
        self.assertNotIn("duplicate_content", crawler.report.skipped)

    def test_a_redirect_to_a_new_url_reports_the_url_it_landed_on(self):
        site = {
            "https://d.test/": doc(words("hub"), links=["https://d.test/old"]),
            "https://d.test/old": {**doc(words("moved")), "final": "https://d.test/new"},
        }
        _, pages = crawl(site, seeds=["https://d.test/"])
        self.assertEqual([p.url for p in pages], ["https://d.test/", "https://d.test/new"])


# ---------------------------------------------------------------------- gating


class TestCrawlGating(unittest.TestCase):
    def test_offsite_links_are_skipped(self):
        site = {
            "https://g.test/": doc(words("hub"), links=["https://elsewhere.test/x",
                                                        "https://g.test/a"]),
            "https://g.test/a": doc(words("a")),
            "https://elsewhere.test/x": doc(words("x")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"])
        self.assertEqual([p.url for p in pages], ["https://g.test/", "https://g.test/a"])
        self.assertEqual(crawler.report.skipped["offsite"], 1)
        self.assertNotIn("https://elsewhere.test/x", crawler.client.requested)

    def test_a_subdomain_counts_as_the_same_site_by_default(self):
        site = {
            "https://g.test/": doc(words("hub"), links=["https://docs.g.test/a"]),
            "https://docs.g.test/a": doc(words("a")),
        }
        _, pages = crawl(site, seeds=["https://g.test/"])
        self.assertEqual(len(pages), 2)

    def test_include_subdomains_off_treats_a_subdomain_as_offsite(self):
        site = {
            "https://g.test/": doc(words("hub"), links=["https://docs.g.test/a"]),
            "https://docs.g.test/a": doc(words("a")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"], include_subdomains=False)
        self.assertEqual(len(pages), 1)
        self.assertEqual(crawler.report.skipped["offsite"], 1)

    def test_an_exclude_pattern_skips_matching_urls(self):
        site = {
            "https://g.test/": doc(words("hub"), links=["https://g.test/blog/1",
                                                        "https://g.test/docs/1"]),
            "https://g.test/blog/1": doc(words("blog")),
            "https://g.test/docs/1": doc(words("docs")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"], exclude_patterns=["/blog/"])
        self.assertEqual([p.url for p in pages], ["https://g.test/", "https://g.test/docs/1"])
        self.assertEqual(crawler.report.skipped["exclude_pattern"], 1)

    def test_an_include_pattern_skips_everything_else(self):
        site = {
            "https://g.test/docs/": doc(words("hub"), links=["https://g.test/blog/1",
                                                             "https://g.test/docs/1"]),
            "https://g.test/blog/1": doc(words("blog")),
            "https://g.test/docs/1": doc(words("docs")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/docs/"],
                               include_patterns=["/docs/"])
        self.assertEqual([p.url for p in pages], ["https://g.test/docs/", "https://g.test/docs/1"])
        self.assertEqual(crawler.report.skipped["include_pattern"], 1)

    def test_binary_extensions_are_never_requested(self):
        site = {"https://g.test/": doc(words("hub"), links=["https://g.test/manual.pdf",
                                                            "https://g.test/logo.png",
                                                            "https://g.test/app.js"])}
        crawler, _ = crawl(site, seeds=["https://g.test/"])
        self.assertEqual(crawler.report.skipped["binary_ext"], 3)
        # Gating on the extension means the bytes are never pulled at all.
        self.assertEqual(crawler.client.requested,
                         ["https://g.test/robots.txt", "https://g.test/"])

    def test_a_non_html_content_type_is_skipped_and_named(self):
        site = {
            "https://g.test/": doc(words("hub"), links=["https://g.test/data"]),
            "https://g.test/data": {"body": "id,name\n1,a\n", "ctype": "text/csv"},
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"])
        self.assertEqual(len(pages), 1)
        self.assertEqual(crawler.report.skipped["ctype_text/csv"], 1)

    def test_nofollow_links_are_not_enqueued(self):
        site = {
            "https://g.test/": doc(words("hub"),
                                   links=[("https://g.test/sponsored", ' rel="nofollow"')]),
            "https://g.test/sponsored": doc(words("ad")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"])
        self.assertEqual(len(pages), 1)
        self.assertEqual(crawler.report.skipped["nofollow"], 1)

    def test_follow_nofollow_opts_back_in(self):
        site = {
            "https://g.test/": doc(words("hub"),
                                   links=[("https://g.test/sponsored", ' rel="nofollow"')]),
            "https://g.test/sponsored": doc(words("ad")),
        }
        _, pages = crawl(site, seeds=["https://g.test/"], follow_nofollow=True)
        self.assertEqual(len(pages), 2)

    def test_a_thin_page_is_not_yielded_but_its_links_are_still_followed(self):
        # A "redirecting..." interstitial carries no text worth indexing and is
        # very often the only path to the page that does. Dropping its links
        # with its text would strand whole sections of a site.
        site = {
            "https://g.test/": doc(words("hub"), links=["https://g.test/gate"]),
            "https://g.test/gate": doc("redirecting you now",
                                       links=["https://g.test/real"]),
            "https://g.test/real": doc(words("real")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"], max_depth=3)
        self.assertEqual([p.url for p in pages], ["https://g.test/", "https://g.test/real"])
        self.assertEqual(crawler.report.skipped["thin"], 1)

    def test_a_url_disallowed_by_robots_is_skipped_and_named(self):
        site = {
            "https://g.test/robots.txt": robots("User-agent: *\nDisallow: /private/\n"),
            "https://g.test/": doc(words("hub"), links=["https://g.test/private/x",
                                                        "https://g.test/open"]),
            "https://g.test/private/x": doc(words("secret")),
            "https://g.test/open": doc(words("open")),
        }
        crawler, pages = crawl(site, seeds=["https://g.test/"])
        self.assertEqual([p.url for p in pages], ["https://g.test/", "https://g.test/open"])
        self.assertEqual(crawler.report.skipped["robots"], 1)
        self.assertNotIn("https://g.test/private/x", crawler.client.requested)


# ------------------------------------------------------------- errors and 304s


class TestCrawlDegradesWithoutDying(unittest.TestCase):
    def test_an_http_error_on_one_url_does_not_abort_the_crawl(self):
        site = {
            "https://x.test/": doc(words("hub"), links=["https://x.test/gone",
                                                        "https://x.test/boom",
                                                        "https://x.test/ok"]),
            "https://x.test/gone": {"raise": HttpError(404, "https://x.test/gone")},
            "https://x.test/boom": {"raise": HttpError(500, "https://x.test/boom")},
            "https://x.test/ok": doc(words("ok")),
        }
        crawler, pages = crawl(site, seeds=["https://x.test/"])
        self.assertEqual([p.url for p in pages], ["https://x.test/", "https://x.test/ok"])
        self.assertEqual(crawler.report.skipped["http_404"], 1)
        self.assertEqual(crawler.report.skipped["http_500"], 1)
        self.assertEqual(len(crawler.report.errors), 2)
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")

    def test_a_transport_error_on_one_url_does_not_abort_the_crawl(self):
        site = {
            "https://x.test/": doc(words("hub"), links=["https://x.test/dead",
                                                        "https://x.test/ok"]),
            "https://x.test/dead": {"raise": TransportError("connection reset")},
            "https://x.test/ok": doc(words("ok")),
        }
        crawler, pages = crawl(site, seeds=["https://x.test/"])
        self.assertEqual([p.url for p in pages], ["https://x.test/", "https://x.test/ok"])
        self.assertEqual(crawler.report.skipped["transport"], 1)
        self.assertEqual(crawler.report.errors[0][0], "https://x.test/dead")

    def test_a_304_is_skipped_rather_than_indexed_as_an_empty_page(self):
        # A conditional GET that says "unchanged" has no body. Treating it as a
        # page would replace a good document with an empty one on every
        # incremental re-crawl.
        site = {
            "https://x.test/": doc(words("hub"), links=["https://x.test/cached"]),
            "https://x.test/cached": {"status": 304},
        }
        crawler, pages = crawl(site, seeds=["https://x.test/"])
        self.assertEqual(len(pages), 1)
        self.assertEqual(crawler.report.skipped["not_modified"], 1)
        self.assertEqual(crawler.report.errors, [])

    def test_a_malformed_href_drops_one_link_not_the_whole_crawl(self):
        # Bug (fixed): `normalize_url` reaches `SplitResult.port`, which raises
        # ValueError on `http://host:80x/`. That exception escaped `crawl()`
        # mid-generator, so a single hand-written href anywhere on a site cost
        # the caller every page still in the frontier *and* left the report with
        # no stopped_by, no duration and no frontier count - the crawl failed and
        # was not even diagnosable afterwards.
        site = {
            "https://x.test/": doc(words("hub"), links=["http://x.test:80x/bad",
                                                        "https://x.test/good"]),
            "https://x.test/good": doc(words("good")),
        }
        crawler, pages = crawl(site, seeds=["https://x.test/"])
        self.assertEqual([p.url for p in pages], ["https://x.test/", "https://x.test/good"])
        self.assertEqual(crawler.report.skipped["bad_url"], 1)
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")
        self.assertGreater(crawler.report.duration_s, 0.0)

    def test_a_malformed_seed_is_dropped_and_the_other_seeds_still_run(self):
        site = {"https://x.test/": doc(words("ok"))}
        crawler, pages = crawl(site, seeds=["http://x.test:99x/", "https://x.test/"])
        self.assertEqual([p.url for p in pages], ["https://x.test/"])
        self.assertEqual(crawler.report.skipped["bad_url"], 1)

    def test_a_crawl_with_no_seeds_produces_an_empty_finished_report(self):
        crawler, pages = crawl({}, seeds=[])
        self.assertEqual(pages, [])
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")
        self.assertEqual(crawler.report.fetches, 0)


class TestPlainTextPages(unittest.TestCase):
    """text/plain and text/markdown must not go through the HTML parser: an
    `# heading` in Markdown is content, and `<` in a text file is not a tag."""

    def test_a_text_plain_page_is_kept_verbatim(self):
        body = words("plain") + "\n1 < 2 && 3 > 2\n"
        site = {
            "https://p.test/": doc(words("hub"), links=["https://p.test/notes.txt"]),
            "https://p.test/notes.txt": {"body": body, "ctype": "text/plain; charset=utf-8"},
        }
        _, pages = crawl(site, seeds=["https://p.test/"])
        page = next(p for p in pages if p.url.endswith("notes.txt"))
        self.assertEqual(page.content_type, "text/plain")
        self.assertEqual(page.page.text, body)
        self.assertEqual(page.page.markdown, body)
        # The filename is the only title a text file has.
        self.assertEqual(page.page.title, "notes.txt")
        self.assertEqual(page.page.links, [])

    def test_a_markdown_page_keeps_its_heading_syntax(self):
        body = "# Title\n\n" + words("md")
        site = {
            "https://p.test/": doc(words("hub"), links=["https://p.test/readme.md"]),
            "https://p.test/readme.md": {"body": body, "ctype": "text/markdown"},
        }
        _, pages = crawl(site, seeds=["https://p.test/"])
        page = next(p for p in pages if p.url.endswith("readme.md"))
        self.assertTrue(page.page.markdown.startswith("# Title"))


# --------------------------------------------------------------------- sitemap


SITEMAP_INDEX = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    "<sitemap><loc>https://m.test/sitemap-1.xml</loc></sitemap>"
    "</sitemapindex>"
)
URLSET = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    "<url><loc>https://m.test/one</loc></url>"
    "<url><loc>https://m.test/two</loc></url>"
    "<url><loc>   </loc></url>"
    "</urlset>"
)


class TestSitemapDiscovery(unittest.TestCase):
    def base_site(self) -> dict:
        return {
            "https://m.test/robots.txt": robots(
                "User-agent: *\nSitemap: https://m.test/sitemap.xml\n"),
            "https://m.test/": doc(words("home")),
            "https://m.test/one": doc(words("one")),
            "https://m.test/two": doc(words("two")),
        }

    def test_a_sitemapindex_is_followed_one_level_to_its_urls(self):
        site = self.base_site()
        site["https://m.test/sitemap.xml"] = {"body": SITEMAP_INDEX, "ctype": "application/xml"}
        site["https://m.test/sitemap-1.xml"] = {"body": URLSET, "ctype": "application/xml"}
        crawler, pages = crawl(site, seeds=["https://m.test/"], use_sitemap=True)
        self.assertEqual([p.url for p in pages],
                         ["https://m.test/", "https://m.test/one", "https://m.test/two"])
        # Sitemap URLs enter the frontier below the seed, not beside it.
        self.assertEqual([p.depth for p in pages], [0, 1, 1])

    def test_a_malformed_sitemap_is_skipped_without_raising(self):
        # Truncated XML is what a sitemap looks like when the response was cut
        # short. It must cost the site its sitemap, not its crawl.
        site = self.base_site()
        site["https://m.test/sitemap.xml"] = {"body": "<urlset><url><loc>https://m.test/one",
                                              "ctype": "application/xml"}
        crawler, pages = crawl(site, seeds=["https://m.test/"], use_sitemap=True)
        self.assertEqual([p.url for p in pages], ["https://m.test/"])
        self.assertEqual(crawler.report.stopped_by, "frontier_exhausted")

    def test_a_missing_sitemap_leaves_the_seed_crawl_intact(self):
        site = self.base_site()
        del site["https://m.test/robots.txt"]  # no robots, so the conventional path is tried
        crawler, pages = crawl(site, seeds=["https://m.test/"], use_sitemap=True)
        self.assertEqual([p.url for p in pages], ["https://m.test/"])
        self.assertIn("https://m.test/sitemap.xml", crawler.client.requested)

    def test_a_deeply_nested_sitemapindex_never_yields_sitemaps_as_pages(self):
        # Bug (fixed): past the five-map cap the "is this a sitemap or a page?"
        # branch fell through to the page list, so nested index entries were
        # enqueued as documents. They cost fetches, and a host serving .xml as
        # text/plain would have had raw sitemap markup indexed as a page.
        def index(child: str) -> dict:
            return {"body": '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                            f"<sitemap><loc>{child}</loc></sitemap></sitemapindex>",
                    "ctype": "application/xml"}

        site = {
            "https://m.test/robots.txt": robots(
                "User-agent: *\nSitemap: https://m.test/sitemap.xml\n"),
            "https://m.test/": doc(words("home")),
            "https://m.test/sitemap.xml": index("https://m.test/sm-1.xml"),
        }
        for i in range(1, 8):
            site[f"https://m.test/sm-{i}.xml"] = index(f"https://m.test/sm-{i + 1}.xml")
        crawler, pages = crawl(site, seeds=["https://m.test/"], use_sitemap=True)
        self.assertEqual([p.url for p in pages], ["https://m.test/"])
        self.assertNotIn("https://m.test/sm-5.xml", crawler.client.requested)

    def test_sitemap_urls_are_still_subject_to_the_robots_gate(self):
        site = self.base_site()
        site["https://m.test/robots.txt"] = robots(
            "User-agent: *\nDisallow: /two\nSitemap: https://m.test/sitemap.xml\n")
        site["https://m.test/sitemap.xml"] = {"body": URLSET, "ctype": "application/xml"}
        crawler, pages = crawl(site, seeds=["https://m.test/"], use_sitemap=True)
        self.assertEqual([p.url for p in pages], ["https://m.test/", "https://m.test/one"])
        self.assertEqual(crawler.report.skipped["robots"], 1)


if __name__ == "__main__":
    unittest.main()
