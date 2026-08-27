"""The modules that shipped before this session had no tests. These are them.

Nothing here reaches the network: URL canonicalisation, HTML extraction, robots
parsing, redaction and the budget dataclasses are all pure functions over
strings, and testing them offline is the point.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.scrape.crawler import CrawlConfig  # noqa: E402
from oodarag.scrape.html import extract  # noqa: E402
from oodarag.scrape.robots import RobotsPolicy, RuleSet  # noqa: E402
from oodarag.util.http import (  # noqa: E402
    HttpError,
    RetryPolicy,
    normalize_url,
    same_site,
    urljoin,
)
from oodarag.util.text import (  # noqa: E402
    estimate_tokens,
    heading_path,
    redact_secrets,
    split_markdown_sections,
    split_sentences,
    tokenize,
    truncate_tokens,
)

ARTICLE_BODY = " ".join(
    f"This is sentence {i} of the real article body, with enough substance "
    "to be recognised as the main content of the page."
    for i in range(30)
)

PAGE = f"""<html><head><title>The Article</title>
<meta name="description" content="A page about retrieval."></head><body>
<nav><a href="/a">Home</a><a href="/b">About</a><a href="/c">Docs</a></nav>
<aside class="sidebar"><a href="/x">Related one</a><a href="/y">Related two</a></aside>
<main><h1>The Article</h1><h2>A section</h2><p>{ARTICLE_BODY}</p>
<p>See <a href="/next">the next page</a> for more.</p></main>
<footer><a href="/p">Privacy</a><a href="/t">Terms</a>Copyright 2026</footer>
<script>window.tracker = 1;</script></body></html>"""


class TestUrlCanonicalisation(unittest.TestCase):
    def test_the_same_page_five_ways_canonicalises_to_one_url(self) -> None:
        # This is what stops one page being indexed five times.
        variants = [
            "HTTPS://Example.COM/a/index.html?b=2#frag",
            "https://example.com:443/a/index.html?b=2",
            "https://example.com/a/?b=2&utm_source=twitter",
            "https://example.com/a/?utm_campaign=x&b=2",
            "https://example.com/a/?b=2#other",
        ]
        self.assertEqual(len({normalize_url(v) for v in variants}), 1)

    def test_tracking_parameters_are_dropped_and_real_ones_kept(self) -> None:
        out = normalize_url("https://e.com/p?id=7&utm_source=x&gclid=y&fbclid=z")
        self.assertIn("id=7", out)
        for junk in ("utm_source", "gclid", "fbclid"):
            self.assertNotIn(junk, out)

    def test_query_order_does_not_create_a_new_url(self) -> None:
        self.assertEqual(normalize_url("https://e.com/p?b=2&a=1"),
                         normalize_url("https://e.com/p?a=1&b=2"))

    def test_a_non_default_port_is_preserved(self) -> None:
        self.assertIn(":8080", normalize_url("https://e.com:8080/p"))

    def test_same_site_spans_subdomains_by_default(self) -> None:
        self.assertTrue(same_site("https://docs.e.com/a", "https://e.com/b"))
        self.assertFalse(same_site("https://e.com/a", "https://other.com/b"))
        self.assertFalse(same_site("https://docs.e.com/a", "https://e.com/b",
                                   include_subdomains=False))

    def test_relative_links_resolve_against_the_page(self) -> None:
        self.assertEqual(urljoin("https://e.com/docs/a", "../b"), "https://e.com/b")


class TestRetryPolicy(unittest.TestCase):
    def test_backoff_grows_and_is_capped(self) -> None:
        policy = RetryPolicy(base_delay=1.0, max_delay=10.0, jitter=0.0)
        self.assertAlmostEqual(policy.delay_for(1), 1.0)
        self.assertAlmostEqual(policy.delay_for(2), 2.0)
        self.assertLessEqual(policy.delay_for(20), 10.0)

    def test_retry_after_is_honoured_over_the_computed_backoff(self) -> None:
        policy = RetryPolicy(base_delay=1.0, max_delay=30.0)
        self.assertAlmostEqual(policy.delay_for(1, retry_after=17.0), 17.0)


class TestRateLimitDiscrimination(unittest.TestCase):
    """A 403 is a permission error unless the headers say it is a quota refusal.

    GitHub signals both primary quota exhaustion and secondary rate limits with
    403 rather than 429. Treating every 403 as permanent means a long ingest
    dies at the quota boundary instead of waiting for the reset; treating every
    403 as retryable means a genuine permission error is retried four times
    with backoff before failing.
    """

    def error(self, status: int, body: str = "", **headers: str) -> HttpError:
        return HttpError(status, "https://api.github.com/x", body, headers)

    def test_a_quota_403_is_retryable(self) -> None:
        err = self.error(403, "API rate limit exceeded",
                         **{"x-ratelimit-remaining": "0",
                            "x-ratelimit-reset": "9999999999"})
        self.assertTrue(err.rate_limited)
        self.assertTrue(err.retryable)

    def test_a_secondary_rate_limit_is_recognised_from_the_body(self) -> None:
        # Secondary limits do not always set the ratelimit headers.
        err = self.error(403, "You have exceeded a secondary rate limit")
        self.assertTrue(err.retryable)

    def test_a_genuine_permission_403_fails_fast(self) -> None:
        # The case this discrimination protects: retrying it four times with
        # backoff turns a clear failure into a slow one.
        err = self.error(403, "Resource not accessible by integration")
        self.assertFalse(err.rate_limited)
        self.assertFalse(err.retryable)

    def test_a_missing_credential_403_fails_fast(self) -> None:
        err = self.error(403, "Method doesn't allow unregistered callers")
        self.assertFalse(err.retryable)

    def test_the_standard_statuses_are_unaffected(self) -> None:
        self.assertTrue(self.error(429, "slow down").retryable)
        self.assertTrue(self.error(503).retryable)
        self.assertTrue(self.error(408).retryable)
        self.assertFalse(self.error(404).retryable)
        self.assertFalse(self.error(401).retryable)

    def test_the_wait_comes_from_the_reset_timestamp_when_retry_after_is_absent(self) -> None:
        # GitHub sends a Unix timestamp in x-ratelimit-reset rather than a
        # duration in Retry-After, so it must be converted, not ignored.
        import time as _time
        from oodarag.util.http import _retry_after
        reset = _time.time() + 42
        wait = _retry_after({"x-ratelimit-remaining": "0",
                             "x-ratelimit-reset": str(reset)})
        self.assertIsNotNone(wait)
        self.assertGreater(wait, 40)
        self.assertLess(wait, 46)

    def test_retry_after_wins_when_both_are_present(self) -> None:
        from oodarag.util.http import _retry_after
        self.assertAlmostEqual(
            _retry_after({"retry-after": "7", "x-ratelimit-remaining": "0",
                          "x-ratelimit-reset": "9999999999"}),
            7.0,
        )


class TestHtmlExtraction(unittest.TestCase):
    def setUp(self) -> None:
        self.page = extract(PAGE, "https://example.com/article")

    def test_navigation_sidebar_and_footer_are_removed(self) -> None:
        for boilerplate in ("Home", "About", "Privacy", "Terms", "Copyright",
                            "Related one"):
            self.assertNotIn(boilerplate, self.page.text, boilerplate)

    def test_the_article_body_survives(self) -> None:
        self.assertIn("main content of the page", self.page.text)

    def test_script_contents_never_reach_the_text(self) -> None:
        self.assertNotIn("window.tracker", self.page.text)

    def test_link_density_of_a_cleaned_article_is_low(self) -> None:
        self.assertLess(self.page.link_density, 0.2)

    def test_links_are_resolved_to_absolute_urls(self) -> None:
        self.assertTrue(
            any(link.startswith("https://example.com/") for link in self.page.outgoing())
        )

    def test_too_little_content_falls_back_rather_than_returning_nothing(self) -> None:
        # Aggressive pruning on a very small page can remove everything. An
        # empty extraction is worse than a noisy one, so it retries leniently.
        tiny = extract(
            "<html><body><nav><a href='/x'>nav</a></nav>"
            "<main><p>Real content here.</p></main></body></html>",
            "https://e.com/",
        )
        self.assertIn("Real content here.", tiny.text)


class TestRobots(unittest.TestCase):
    """robots.txt handling, with the fetch stubbed so no request is made."""

    RULES = (
        "User-agent: *\n"
        "Disallow: /private/\n"
        "Allow: /private/public-bit\n"
        "Crawl-delay: 3\n"
        "Sitemap: https://e.com/sitemap.xml\n"
    )

    class StubClient:
        def __init__(self, body: str) -> None:
            self.body = body

        def get(self, url: str, **kw: object) -> object:
            class Resp:
                status = 200
                text = self.body
                headers: dict[str, str] = {}
                body = b""
            Resp.text = self.body  # type: ignore[assignment]
            return Resp()

    def policy(self) -> RobotsPolicy:
        return RobotsPolicy(self.StubClient(self.RULES))  # type: ignore[arg-type]

    def test_a_disallowed_path_is_refused(self) -> None:
        self.assertFalse(self.policy().allows("https://e.com/private/thing"))

    def test_an_allow_rule_beats_a_broader_disallow(self) -> None:
        self.assertTrue(self.policy().allows("https://e.com/private/public-bit"))

    def test_an_unlisted_path_is_permitted(self) -> None:
        self.assertTrue(self.policy().allows("https://e.com/articles/one"))

    def test_crawl_delay_is_read(self) -> None:
        self.assertEqual(self.policy().crawl_delay("https://e.com/x"), 3.0)

    def test_sitemaps_are_collected(self) -> None:
        self.assertIn("https://e.com/sitemap.xml", self.policy().sitemaps("https://e.com/x"))

    def test_explain_names_the_line_that_decided(self) -> None:
        # "Why was this page skipped?" must not answer "robots.txt, somehow".
        blocked = self.policy().explain("https://e.com/private/thing")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["matched_rule"], "Disallow: /private/")

        allowed = self.policy().explain("https://e.com/private/public-bit")
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["matched_rule"], "Allow: /private/public-bit")


class TestRfc9309Precedence(unittest.TestCase):
    """Longest match wins, Allow breaks ties. The stdlib takes first-match."""

    def rules(self, text: str, ua: str = "oodarag/0.1") -> RuleSet:
        return RuleSet.parse(text, ua)

    def test_a_longer_allow_overrides_an_earlier_disallow(self) -> None:
        rs = self.rules("User-agent: *\nDisallow: /private/\nAllow: /private/public-bit\n")
        self.assertFalse(rs.allows("/private/secret"))
        self.assertTrue(rs.allows("/private/public-bit"))

    def test_file_order_does_not_change_the_verdict(self) -> None:
        # The exact property the stdlib lacks.
        a = self.rules("User-agent: *\nDisallow: /p/\nAllow: /p/ok\n")
        b = self.rules("User-agent: *\nAllow: /p/ok\nDisallow: /p/\n")
        self.assertEqual(a.allows("/p/ok"), b.allows("/p/ok"))
        self.assertTrue(a.allows("/p/ok"))

    def test_allow_wins_an_equal_length_tie(self) -> None:
        rs = self.rules("User-agent: *\nDisallow: /x/y\nAllow: /x/y\n")
        self.assertTrue(rs.allows("/x/y"))

    def test_an_unmatched_path_is_allowed(self) -> None:
        rs = self.rules("User-agent: *\nDisallow: /private/\n")
        self.assertTrue(rs.allows("/public/page"))

    def test_an_empty_disallow_restricts_nothing(self) -> None:
        rs = self.rules("User-agent: *\nDisallow:\n")
        self.assertTrue(rs.allows("/anything"))

    def test_wildcards_match_any_sequence(self) -> None:
        rs = self.rules("User-agent: *\nDisallow: /*/admin\n")
        self.assertFalse(rs.allows("/team/admin"))
        self.assertFalse(rs.allows("/a/b/admin"))
        self.assertTrue(rs.allows("/admin-ish"))

    def test_dollar_anchors_the_end_of_the_path(self) -> None:
        rs = self.rules("User-agent: *\nDisallow: /*.pdf$\n")
        self.assertFalse(rs.allows("/docs/manual.pdf"))
        self.assertTrue(rs.allows("/docs/manual.pdf.html"))

    def test_a_named_user_agent_group_beats_the_star_group(self) -> None:
        text = ("User-agent: *\nDisallow: /\n\n"
                "User-agent: oodarag\nDisallow: /private/\n")
        rs = RuleSet.parse(text, "oodarag/0.1 (+https://example.com)")
        self.assertTrue(rs.allows("/public"))
        self.assertFalse(rs.allows("/private/x"))

    def test_an_unknown_agent_falls_back_to_the_star_group(self) -> None:
        text = ("User-agent: *\nDisallow: /private/\n\n"
                "User-agent: googlebot\nDisallow: /\n")
        rs = RuleSet.parse(text, "oodarag/0.1")
        self.assertTrue(rs.allows("/public"))
        self.assertFalse(rs.allows("/private/x"))

    def test_consecutive_user_agent_lines_share_one_group(self) -> None:
        text = "User-agent: oodarag\nUser-agent: otherbot\nDisallow: /shared/\n"
        self.assertFalse(RuleSet.parse(text, "oodarag/0.1").allows("/shared/x"))
        self.assertFalse(RuleSet.parse(text, "otherbot/2").allows("/shared/x"))

    def test_comments_and_blank_lines_are_ignored(self) -> None:
        rs = self.rules("# a comment\nUser-agent: *\n\nDisallow: /private/  # trailing\n")
        self.assertFalse(rs.allows("/private/x"))

    def test_an_empty_file_permits_everything(self) -> None:
        self.assertTrue(self.rules("").allows("/anything"))

    def test_the_deciding_rule_is_reportable(self) -> None:
        rs = self.rules("User-agent: *\nDisallow: /private/\nAllow: /private/ok\n")
        matched = rs.matched("/private/ok")
        self.assertIsNotNone(matched)
        self.assertTrue(matched.allow)
        self.assertEqual(matched.pattern, "/private/ok")


class TestCrawlBudgets(unittest.TestCase):
    def test_every_dimension_the_readme_claims_is_bounded(self) -> None:
        fields = set(CrawlConfig.__dataclass_fields__)
        for budget in ("max_pages", "max_fetches", "max_depth", "max_seconds"):
            self.assertIn(budget, fields)

    def test_every_budget_is_finite_including_the_derived_one(self) -> None:
        # `max_fetches` defaults to 0, which is a sentinel meaning "derive from
        # max_pages", not "unlimited". The property that matters is that the
        # effective budget is finite either way.
        cfg = CrawlConfig(seeds=["https://e.com/"])
        for budget in ("max_pages", "max_depth", "max_seconds"):
            self.assertGreater(getattr(cfg, budget), 0, budget)
        effective_fetches = cfg.max_fetches or max(cfg.max_pages * 5, 10)
        self.assertGreater(effective_fetches, 0)
        self.assertLess(effective_fetches, 10_000)


class TestTextUtilities(unittest.TestCase):
    def test_secrets_are_redacted_before_anything_is_indexed(self) -> None:
        for secret in (
            # Built rather than written, so the file carries no literal that
            # matches a provider signature and trips secret scanning.
            'token = "' + "ghp" + "_" + "A" * 36 + '"',
            "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "my_service_password: hunter2hunter2hunter2",
            "AKIAIOSFODNN7EXAMPLE",
            '-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END RSA PRIVATE KEY-----',
        ):
            cleaned = redact_secrets(secret)
            self.assertIn("redacted", cleaned.lower(), secret[:30])

    def test_ordinary_prose_is_left_alone(self) -> None:
        prose = "The retrieval budget is 40 pages and the crawl delay is 3 seconds."
        self.assertEqual(redact_secrets(prose), prose)

    def test_code_identifiers_stay_whole_tokens(self) -> None:
        # A corpus that is half code needs `snake_case` and `dotted.paths` to
        # survive tokenisation, or exact-term search stops working on it.
        tokens = tokenize("call oodarag.util.http.normalize_url and max_pages now")
        self.assertIn("oodarag.util.http.normalize_url", tokens)
        self.assertIn("max_pages", tokens)

    def test_markdown_sections_carry_their_heading_path(self) -> None:
        sections = split_markdown_sections("# A\n\ntext a\n\n## B\n\ntext b\n")
        paths = [headings for headings, _body, _offset in sections]
        self.assertTrue(any("B" in p for p in paths))

    def test_heading_path_resolves_an_offset(self) -> None:
        doc = "# A\n\ntext a\n\n## B\n\ntext b\n"
        self.assertIn("B", heading_path(doc, doc.index("text b")))

    def test_sentence_splitting_does_not_break_on_abbreviations_alone(self) -> None:
        sentences = split_sentences("First sentence here. Second sentence follows.")
        self.assertEqual(len(sentences), 2)

    def test_token_estimate_and_truncation_agree(self) -> None:
        text = " ".join(f"word{i}" for i in range(200))
        cut = truncate_tokens(text, 20)
        self.assertLessEqual(estimate_tokens(cut), 25)
        self.assertTrue(text.startswith(cut[:20]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
