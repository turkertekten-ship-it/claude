"""robots.txt enforcement, per RFC 9309."""

from __future__ import annotations

import unittest

from oodarag.scrape.robots import RobotsPolicy
from oodarag.util.http import HttpClient, RetryPolicy
from tests.support.httpserver import Route, TestSite

ROBOTS = """
User-agent: *
Disallow: /private/
Disallow: /admin
Crawl-delay: 2
Allow: /private/public-corner/

Sitemap: https://example.com/sitemap.xml
"""


def _client() -> HttpClient:
    return HttpClient(rate_per_sec=100, retry=RetryPolicy(attempts=1, base_delay=0.01))


class RobotsTest(unittest.TestCase):
    def test_disallowed_paths_are_blocked_and_others_allowed(self):
        with TestSite({"/robots.txt": Route(body=ROBOTS, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client())
            self.assertFalse(policy.allows(site.url("/private/secret")))
            self.assertFalse(policy.allows(site.url("/admin")))
            self.assertTrue(policy.allows(site.url("/docs/guide")))
            self.assertTrue(policy.allows(site.url("/private/public-corner/ok")))

    def test_crawl_delay_and_sitemaps_are_surfaced(self):
        with TestSite({"/robots.txt": Route(body=ROBOTS, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client())
            self.assertEqual(policy.crawl_delay(site.url("/x")), 2.0)
            self.assertEqual(policy.sitemaps(site.url("/x")), ["https://example.com/sitemap.xml"])

    def test_404_robots_means_crawling_is_allowed(self):
        with TestSite({"/robots.txt": Route(body="", status=404)}) as site:
            self.assertTrue(RobotsPolicy(client=_client()).allows(site.url("/anything")))

    def test_403_robots_means_full_disallow(self):
        with TestSite({"/robots.txt": Route(body="denied", status=403)}) as site:
            self.assertFalse(RobotsPolicy(client=_client()).allows(site.url("/anything")))

    def test_5xx_robots_defaults_to_deny(self):
        with TestSite({"/robots.txt": Route(body="oops", status=500)}) as site:
            self.assertFalse(RobotsPolicy(client=_client()).allows(site.url("/anything")))

    def test_5xx_robots_can_be_configured_to_allow(self):
        with TestSite({"/robots.txt": Route(body="oops", status=500)}) as site:
            policy = RobotsPolicy(client=_client(), on_error="allow")
            self.assertTrue(policy.allows(site.url("/anything")))

    def test_robots_is_fetched_once_per_host_and_cached(self):
        with TestSite({"/robots.txt": Route(body=ROBOTS, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client())
            for path in ("/a", "/b", "/c", "/private/x"):
                policy.allows(site.url(path))
            self.assertEqual(site.hits.get("/robots.txt"), 1, "robots.txt was re-fetched")

    def test_obey_false_bypasses_everything(self):
        with TestSite({"/robots.txt": Route(body=ROBOTS, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client(), obey=False)
            self.assertTrue(policy.allows(site.url("/private/secret")))

    def test_longest_match_wins_over_file_order(self):
        """RFC 9309 2.2.2: the most specific rule wins, not the first one."""
        rules = """
User-agent: *
Disallow: /docs/
Allow: /docs/public/
Disallow: /docs/public/drafts/
"""
        with TestSite({"/robots.txt": Route(body=rules, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client())
            self.assertFalse(policy.allows(site.url("/docs/internal")))
            self.assertTrue(policy.allows(site.url("/docs/public/guide")),
                            "Allow after Disallow was ignored (first-match bug)")
            self.assertFalse(policy.allows(site.url("/docs/public/drafts/wip")))

    def test_wildcards_and_end_anchors(self):
        rules = """
User-agent: *
Disallow: /*.pdf$
Disallow: /tmp/*/cache
"""
        with TestSite({"/robots.txt": Route(body=rules, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client())
            self.assertFalse(policy.allows(site.url("/reports/annual.pdf")))
            self.assertTrue(policy.allows(site.url("/reports/annual.pdf.html")),
                            "$ anchor was not honoured")
            self.assertFalse(policy.allows(site.url("/tmp/abc/cache")))
            self.assertTrue(policy.allows(site.url("/tmp/abc/keep")))

    def test_named_agent_group_overrides_wildcard(self):
        rules = """
User-agent: *
Disallow: /

User-agent: oodarag
Allow: /
Crawl-delay: 0.5
"""
        with TestSite({"/robots.txt": Route(body=rules, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client(), user_agent="oodarag/0.1 (+https://x)")
            self.assertTrue(policy.allows(site.url("/anything")))
            self.assertEqual(policy.crawl_delay(site.url("/")), 0.5)
            other = RobotsPolicy(client=_client(), user_agent="SomeOtherBot/2.0")
            self.assertFalse(other.allows(site.url("/anything")))

    def test_empty_disallow_means_allow_everything(self):
        rules = "User-agent: *\nDisallow:\n"
        with TestSite({"/robots.txt": Route(body=rules, content_type="text/plain")}) as site:
            self.assertTrue(RobotsPolicy(client=_client()).allows(site.url("/anything")))

    def test_dots_in_patterns_are_literal_not_wildcards(self):
        rules = "User-agent: *\nDisallow: /a.b\n"
        with TestSite({"/robots.txt": Route(body=rules, content_type="text/plain")}) as site:
            policy = RobotsPolicy(client=_client())
            self.assertFalse(policy.allows(site.url("/a.b")))
            self.assertTrue(policy.allows(site.url("/axb")), "'.' was treated as a wildcard")

    def test_explain_reports_the_decision_inputs(self):
        with TestSite({"/robots.txt": Route(body=ROBOTS, content_type="text/plain")}) as site:
            explanation = RobotsPolicy(client=_client()).explain(site.url("/private/x"))
            self.assertFalse(explanation["allowed"])
            self.assertEqual(explanation["robots_status"], 200)
            self.assertEqual(explanation["crawl_delay"], 2.0)


if __name__ == "__main__":
    unittest.main()
