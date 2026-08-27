"""Outcome-based blind tests for the crawler.

"Blind" here means the expected result is never a value copied from a previous
run. It is either

  (a) **derived** at test time by an independent reference implementation
      written from the documented rules rather than from the crawler's code, or
  (b) **observed** from the server's own request log, which is ground truth the
      crawler cannot influence or fake.

(b) is the stronger of the two and is what proves the properties that actually
matter: that a disallowed URL was never *requested*, not merely never returned;
that a budget bounded real work; that nothing was fetched twice.
"""

from __future__ import annotations

import unittest
from collections import deque

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.web import WebConnector
from oodarag.scrape.crawler import CrawlConfig, Crawler
from oodarag.util.http import HttpClient, RetryPolicy, normalize_url
from tests.support.httpserver import Route, TestSite, page, prose

ROBOTS = """
User-agent: *
Disallow: /private/
Allow: /private/allowed/
"""

# --- the site specification -------------------------------------------------
# Declared once, used to build the server AND to derive expectations. The
# crawler never sees it.
CONTENT_PAGES = 8
DUPLICATE_OF = {5: 2}          # /p/5 serves byte-identical content to /p/2
CANONICAL_OF = {6: 4}          # /p/6 declares /p/4 as its canonical
THIN_PAGES = {7}               # /p/7 has fewer words than min_words
MIN_WORDS = 40


def build_site_routes(offsite_origin: str = "http://offsite.invalid") -> dict[str, Route]:
    routes: dict[str, Route] = {"/robots.txt": Route(body=ROBOTS, content_type="text/plain")}
    for i in range(CONTENT_PAGES):
        body_seed = DUPLICATE_OF.get(i, i)
        if i in THIN_PAGES:
            body = "<p>far too short to index</p>"
        else:
            body = prose(90, seed=f"page{body_seed}")
        links = [f"/p/{j}" for j in (i + 1, i + 2) if j < CONTENT_PAGES]
        if i == 0:
            # A direct edge to the thin page, which the i+1/i+2 chain never
            # reaches once its only parents are deduped away.
            links += [f"/p/{t}" for t in sorted(THIN_PAGES)]
        links += ["/private/secret", "/asset.png", f"{offsite_origin}/lure"]
        canonical = f"/p/{CANONICAL_OF[i]}" if i in CANONICAL_OF else ""
        routes[f"/p/{i}"] = Route(body=page(
            f"Page {body_seed}", body, links=links, canonical=canonical, nofollow=["/p/nofollow"],
        ))
    routes["/private/secret"] = Route(body=page("Secret", prose(90, "secret")))
    routes["/asset.png"] = Route(body=b"\x89PNG\r\n\x1a\n" + b"0" * 500, content_type="image/png")
    return routes


def reference_expected_urls(origin: str, max_depth: int) -> set[str]:
    """Independent BFS over the site spec, applying the documented rules.

    Written from the rules, not from `Crawler`. If the two disagree, one of them
    is wrong and the test says so rather than silently blessing the code.

    Rule order mirrors the documented pipeline: thin -> canonical identity ->
    content hash. Thin pages still contribute their links (a hub page is thin by
    nature); deduplicated pages do not, because their links are by definition
    the links of the page they duplicate.
    """
    identity_owner: dict[str, str] = {}
    content_owner: dict[int, str] = {}
    yielded: set[str] = set()
    visited: set[str] = {f"{origin}/p/0"}
    frontier: deque[tuple[int, int]] = deque([(0, 0)])

    while frontier:
        index, depth = frontier.popleft()
        if depth > max_depth:
            continue
        url = f"{origin}/p/{index}"
        follow_links = True

        if index in THIN_PAGES:
            pass  # skipped, but still a source of links
        else:
            identity = (f"{origin}/p/{CANONICAL_OF[index]}"
                        if index in CANONICAL_OF else url)
            owner = identity_owner.setdefault(identity, url)
            if owner != url:
                follow_links = False              # duplicate by canonical
            else:
                seed = DUPLICATE_OF.get(index, index)
                if seed in content_owner:
                    follow_links = False          # duplicate by content
                else:
                    content_owner[seed] = url
                    yielded.add(url)

        if follow_links and depth < max_depth:
            targets = [index + 1, index + 2]
            if index == 0:
                targets += sorted(THIN_PAGES)
            for nxt in targets:
                if nxt >= CONTENT_PAGES:
                    continue
                nxt_url = f"{origin}/p/{nxt}"
                if nxt_url in visited:
                    continue
                visited.add(nxt_url)
                frontier.append((nxt, depth + 1))
    return yielded


def _client() -> HttpClient:
    return HttpClient(rate_per_sec=200, retry=RetryPolicy(attempts=1, base_delay=0.01))


class CrawlerBlindTest(unittest.TestCase):
    def setUp(self):
        # A second, real server stands in for "the rest of the internet". If the
        # crawler ever leaves the seed site, this server records the request and
        # the test fails on observed evidence rather than on a counter.
        self.offsite = TestSite({"/lure": Route(body=page("Lure", prose(120, "lure")))})
        self.offsite.__enter__()
        self.addCleanup(self.offsite.__exit__, None, None, None)
        # Reached by a different *hostname*, not just a different port, so the
        # same-site check is genuinely exercised. localhost and 127.0.0.1 are
        # both loopback and both in NO_PROXY, so this stays hermetic.
        self.offsite_origin = f"http://localhost:{self.offsite.port}"
        self.site = TestSite(build_site_routes(self.offsite_origin))
        self.site.__enter__()
        self.addCleanup(self.site.__exit__, None, None, None)

    def _crawl(self, **overrides):
        options = dict(max_pages=50, max_fetches=100, max_depth=3,
                       min_words=MIN_WORDS, rate_per_sec=200)
        options.update(overrides)
        config = CrawlConfig(seeds=[self.site.url("/p/0")], **options)
        crawler = Crawler(config, client=_client())
        results = list(crawler.crawl())
        return crawler, results

    # ------------------------------------------------- (a) differential outcome

    def test_yielded_pages_match_an_independent_reference_implementation(self):
        crawler, results = self._crawl(max_depth=3)
        self.assertGreater(len(results), 3, "the crawl was too small to be meaningful")
        actual = {normalize_url(r.url) for r in results}
        expected = {normalize_url(u) for u in reference_expected_urls(self.site.origin, 3)}
        self.assertEqual(
            actual, expected,
            f"\ncrawler-only: {sorted(actual - expected)}"
            f"\nreference-only: {sorted(expected - actual)}"
            f"\nskip reasons: {dict(crawler.report.skipped)}",
        )

    # --------------------------------------------- (b) observed from the server

    def test_a_disallowed_url_is_never_requested(self):
        self._crawl()
        requested = self.site.fetched_paths()
        self.assertNotIn("/private/secret", requested,
                         "robots-disallowed URL was actually fetched")
        self.assertIn("/robots.txt", requested, "robots.txt was never consulted")

    def test_binary_assets_are_never_requested(self):
        self._crawl()
        self.assertNotIn("/asset.png", self.site.fetched_paths(),
                         "a binary asset was downloaded despite the extension filter")

    def test_no_url_is_fetched_twice(self):
        self._crawl()
        repeated = {path: n for path, n in self.site.hits.items()
                    if n > 1 and path != "/robots.txt"}
        self.assertEqual(repeated, {}, f"URLs fetched more than once: {repeated}")

    def test_fetch_budget_bounds_real_work_not_just_output(self):
        crawler, results = self._crawl(max_fetches=3, max_depth=3)
        content_fetches = [p for p in self.site.fetched_paths() if p.startswith("/p/")]
        self.assertLessEqual(len(content_fetches), 3,
                             "fetch budget did not bound the number of requests")
        self.assertEqual(crawler.report.stopped_by, "fetch_budget")

    def test_depth_zero_fetches_only_the_seed(self):
        crawler, results = self._crawl(max_depth=0)
        self.assertEqual([r.url for r in results], [self.site.url("/p/0")])
        self.assertEqual([p for p in self.site.fetched_paths() if p.startswith("/p/")], ["/p/0"])

    def test_offsite_links_are_never_requested(self):
        crawler, _ = self._crawl()
        self.assertGreater(crawler.report.skipped["offsite"], 0)
        self.assertEqual(self.offsite.requests, [],
                         "the crawler left the seed site and hit another host")

    def test_offsite_host_is_reachable_so_the_previous_test_means_something(self):
        """Guard against a false pass: prove the offsite server would have
        recorded a request had the crawler made one."""
        _client().get(f"{self.offsite_origin}/lure")
        self.assertEqual(self.offsite.fetched_paths(), {"/lure"})

    def test_same_site_navigation_links_are_followed(self):
        """The nav we strip from the text is still the crawl frontier."""
        self._crawl()
        self.assertIn("/pricing", self.site.fetched_paths(),
                      "navigation links were dropped from the frontier")

    # ------------------------------------------------------ content invariants

    def test_every_result_is_clean_and_traceable(self):
        _, results = self._crawl()
        self.assertGreater(len(results), 2)
        seen_text: dict[str, str] = {}
        for result in results:
            text = result.page.text
            with self.subTest(url=result.url):
                # traceable: the extracted title really is this page's title
                self.assertTrue(result.page.title.startswith("Page "))
                # clean: no script, style or chrome leaked through
                for leaked in ("SHOULD_NOT_APPEAR", "Accept all cookies",
                               "All rights reserved", "console.log"):
                    self.assertNotIn(leaked, text)
                # substantive: above the configured floor
                self.assertGreaterEqual(len(text.split()), MIN_WORDS)
                # unique: dedupe left no two identical bodies
                self.assertNotIn(text, seen_text,
                                 f"duplicate body also returned for {seen_text.get(text)}")
                seen_text[text] = result.url

    def test_nofollow_links_are_not_followed(self):
        crawler, _ = self._crawl()
        self.assertNotIn("/p/nofollow", self.site.fetched_paths())
        self.assertGreater(crawler.report.skipped["nofollow"], 0)

    def test_each_dedupe_path_actually_fires(self):
        """A dedupe rule that never triggers proves nothing. Assert each one ran."""
        crawler, _ = self._crawl()
        skipped = dict(crawler.report.skipped)
        for reason in ("thin", "duplicate_canonical", "duplicate_content",
                       "robots", "binary_ext", "offsite", "nofollow"):
            self.assertGreater(skipped.get(reason, 0), 0,
                               f"skip path {reason!r} never fired; skipped={skipped}")

    def test_report_accounts_for_every_url_considered(self):
        crawler, results = self._crawl()
        report = crawler.report
        self.assertEqual(report.fetched, len(results))
        self.assertGreaterEqual(report.fetches, report.fetched)
        self.assertGreater(sum(report.skipped.values()), 0)
        self.assertIn(report.stopped_by, {"frontier_exhausted", "max_pages"})


class WebConnectorIncrementalTest(unittest.TestCase):
    """The incremental contract, observed end to end."""

    def setUp(self):
        self.routes = build_site_routes()
        self.site = TestSite(self.routes)
        self.site.__enter__()
        self.addCleanup(self.site.__exit__, None, None, None)
        self.state = MemoryStateStore()

    def _connector(self):
        return WebConnector(
            seeds=[self.site.url("/p/0")], max_pages=20, max_fetches=40, max_depth=2,
            min_words=MIN_WORDS, rate_per_sec=200, client=_client(),
        )

    def test_second_run_reports_everything_unchanged(self):
        first = self._connector().run(self.state)
        self.assertGreater(len(first.documents), 1)
        second = self._connector().run(self.state)
        self.assertEqual(second.delta.new, 0)
        self.assertEqual(second.delta.changed, 0)
        self.assertEqual(second.delta.unchanged, first.delta.new)
        self.assertEqual(len(second.documents), 0,
                         "unchanged documents must not be re-emitted downstream")

    def test_a_changed_page_is_detected_and_re_emitted_alone(self):
        first = self._connector().run(self.state)
        self.site.add("/p/1", Route(body=page(
            "Page 1", prose(90, "REWRITTEN") + "<p>brand new sentence about reranking</p>",
            links=["/p/2"],
        )))
        second = self._connector().run(self.state)
        self.assertEqual(second.delta.changed, 1, f"delta was {second.delta.as_dict()}")
        self.assertEqual(second.delta.new, 0)
        self.assertEqual(len(second.documents), 1)
        self.assertIn("reranking", second.documents[0].text)
        self.assertEqual(second.documents[0].external_id, self.site.url("/p/1"))
        self.assertLess(len(second.documents), len(first.documents))

    def test_documents_carry_provenance_that_resolves(self):
        result = self._connector().run(self.state)
        for doc in result.documents:
            with self.subTest(doc=doc.external_id):
                self.assertEqual(doc.source_system, "web")
                # the citation URI is the URL actually fetched, not a canonical
                self.assertEqual(doc.uri, doc.external_id)
                self.assertTrue(doc.uri.startswith(self.site.origin))
                self.assertIn("word_count", doc.metadata)
                self.assertGreater(doc.metadata["word_count"], 0)

    def test_secrets_are_redacted_before_a_document_leaves_the_connector(self):
        leaked = "ghp_" + "A1b2C3d4E5f6G7h8I9j0" + " and sk-ant-" + "x" * 30
        self.site.add("/p/0", Route(body=page(
            "Page 0", prose(90, "page0") + f"<p>token {leaked}</p>", links=["/p/1"],
        )))
        result = self._connector().run(self.state)
        blob = "\n".join(doc.text for doc in result.documents)
        self.assertNotIn("ghp_A1b2C3d4E5f6G7h8I9j0", blob, "a GitHub token reached a document")
        self.assertNotIn("sk-ant-xxxx", blob, "an Anthropic key reached a document")
        self.assertIn("<redacted:github-token>", blob)


if __name__ == "__main__":
    unittest.main()
