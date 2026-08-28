"""Tests for robots.txt parsing, the status matrix and the per-origin cache.

Nothing here touches the network: every test that reaches the HTTP layer swaps
`HttpClient._opener` for a fake, and the fakes count their calls so "this path
must not make a request" is an assertion rather than a hope.
"""

from __future__ import annotations

import io
import unittest
import urllib.error
from dataclasses import dataclass, field

from oodarag.scrape.robots import (
    MAX_CRAWL_DELAY_S,
    MAX_ROBOTS_BYTES,
    MAX_SITEMAPS,
    HostRules,
    RobotsPolicy,
    match_target,
    parse_robots,
    product_token,
)
from oodarag.util.http import HttpClient, RetryPolicy

UA = "oodarag/0.1 (+https://github.com/example/oodarag; research pipeline)"
TOKEN = "oodarag"
ORIGIN = "https://example.com"


# --------------------------------------------------------------------- fakes


@dataclass
class Reply:
    """One programmed HTTP response for the fake opener."""

    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=lambda: {"content-type": "text/plain"})
    final_url: str | None = None

    @classmethod
    def text(cls, body: str, status: int = 200, ctype: str = "text/plain") -> Reply:
        return cls(status, body.encode("utf-8"), {"content-type": ctype})

    @classmethod
    def raw(cls, body: bytes, status: int = 200, ctype: str = "text/plain") -> Reply:
        return cls(status, body, {"content-type": ctype})


class _FakeHTTPResponse:
    """The subset of `http.client.HTTPResponse` that HttpClient actually uses."""

    def __init__(self, reply: Reply, url: str) -> None:
        self.status = reply.status
        self.headers = dict(reply.headers)
        self._url = url
        self._buf = io.BytesIO(reply.body)

    def __enter__(self) -> _FakeHTTPResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def read(self, size: int = -1) -> bytes:
        return self._buf.read(size)

    def geturl(self) -> str:
        return self._url


class FakeOpener:
    """Programmed replies, in order; the last one repeats.

    Repeating rather than exhausting is deliberate: a test that expects one
    request asserts on `len(opener.requests)`, so an accidental second request
    shows up as a count mismatch instead of an exception the module under test
    would helpfully swallow.
    """

    def __init__(self, replies: list[Reply | Exception]) -> None:
        self.replies = list(replies) or [Reply()]
        self.requests: list[str] = []
        self.timeouts: list[float | None] = []

    def open(self, req: object, timeout: float | None = None):  # noqa: ANN201
        url = req.full_url  # type: ignore[attr-defined]
        self.requests.append(url)
        self.timeouts.append(timeout)
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        if reply.status >= 400 or reply.status in (304,):
            raise urllib.error.HTTPError(
                url, reply.status, f"status {reply.status}", reply.headers, io.BytesIO(reply.body)
            )
        return _FakeHTTPResponse(reply, reply.final_url or url)


class FakeClient:
    """Stands in for HttpClient when the point of the test is what the policy
    does with a client that misbehaves in a way HttpClient never should."""

    def __init__(self, exc: Exception) -> None:
        self.exc = exc
        self.calls: list[str] = []
        self.user_agent = UA

    def get(self, url: str, **kw: object) -> object:
        self.calls.append(url)
        raise self.exc


def make_policy(*replies: Reply | Exception, **kw: object) -> tuple[RobotsPolicy, FakeOpener]:
    client = HttpClient(
        rate_per_sec=10_000.0, burst=1000, retry=RetryPolicy(attempts=1, base_delay=0.0)
    )
    opener = FakeOpener(list(replies))
    client._opener = opener
    kw.setdefault("user_agent", UA)
    return RobotsPolicy(client=client, **kw), opener  # type: ignore[arg-type]


def robots_policy(body: str, **kw: object) -> tuple[RobotsPolicy, FakeOpener]:
    return make_policy(Reply.text(body), **kw)


# ------------------------------------------------------------------- parsing


class ProductTokenTestCase(unittest.TestCase):
    def test_token_is_the_product_name_not_the_whole_header(self) -> None:
        self.assertEqual(product_token(UA), "oodarag")
        self.assertEqual(product_token("oodarag"), "oodarag")
        self.assertEqual(product_token("  OodaRag/2.0  "), "oodarag")
        self.assertEqual(product_token("Mozilla 5.0 (compatible)"), "mozilla")
        self.assertEqual(product_token(""), "")
        self.assertEqual(product_token("   "), "")

    def test_full_user_agent_header_selects_the_named_group(self) -> None:
        """The header we send is `oodarag/0.1 (+url)`; sites write `oodarag`."""
        txt = "User-agent: oodarag\nDisallow: /private\n\nUser-agent: *\nDisallow: /\n"
        robots = parse_robots(txt, product_token(UA))

        self.assertEqual(robots.agent, "oodarag")
        self.assertTrue(robots.allowance("https://e.com/public")[0])
        self.assertFalse(robots.allowance("https://e.com/private")[0])

    def test_group_match_is_exact_not_substring(self) -> None:
        """`User-agent: rag` is a different crawler. stdlib's substring match
        would hand us its rules; RFC 9309 says match the token."""
        robots = parse_robots("User-agent: rag\nDisallow: /\n", product_token(UA))

        self.assertEqual(robots.agent, "")
        self.assertTrue(robots.allowance("https://e.com/anything")[0])

    def test_group_match_is_case_insensitive(self) -> None:
        robots = parse_robots("User-Agent: OODARAG\nDisallow: /x\n", TOKEN)

        self.assertEqual(robots.agent, "oodarag")
        self.assertFalse(robots.allowance("https://e.com/x")[0])


class ParseTestCase(unittest.TestCase):
    def parse(self, text: str, token: str = TOKEN):  # noqa: ANN201
        return parse_robots(text, token)

    def test_empty_file_allows_everything(self) -> None:
        robots = self.parse("")

        self.assertEqual(robots.rules, [])
        self.assertIsNone(robots.crawl_delay)
        self.assertEqual(robots.sitemaps, [])
        self.assertEqual(robots.allowance("https://e.com/x"), (True, "no_matching_rule"))

    def test_whitespace_only_file_allows_everything(self) -> None:
        self.assertTrue(self.parse("\n\n   \n\t\n").allowance("https://e.com/x")[0])

    def test_wildcard_group_used_when_our_token_is_absent(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /admin\n")

        self.assertEqual(robots.agent, "*")
        self.assertFalse(robots.allowance("https://e.com/admin/users")[0])

    def test_our_group_wins_over_wildcard_even_when_wildcard_is_first(self) -> None:
        txt = "User-agent: *\nDisallow: /\n\nUser-agent: oodarag\nDisallow: /tmp\n"
        robots = self.parse(txt)

        self.assertTrue(robots.allowance("https://e.com/anything")[0])
        self.assertFalse(robots.allowance("https://e.com/tmp/x")[0])

    def test_repeated_groups_for_one_agent_are_merged(self) -> None:
        txt = "User-agent: oodarag\nDisallow: /a\n\nUser-agent: oodarag\nDisallow: /b\n"
        robots = self.parse(txt)

        self.assertFalse(robots.allowance("https://e.com/a")[0])
        self.assertFalse(robots.allowance("https://e.com/b")[0])

    def test_stacked_user_agent_lines_share_one_rule_block(self) -> None:
        txt = "User-agent: other\nUser-agent: oodarag\nDisallow: /shared\n"
        robots = self.parse(txt)

        self.assertEqual(robots.agent, "oodarag")
        self.assertFalse(robots.allowance("https://e.com/shared")[0])

    def test_a_rule_line_ends_the_agent_block(self) -> None:
        """`User-agent: a / Disallow: / / User-agent: b` is two groups even
        without a blank line between them."""
        txt = "User-agent: other\nDisallow: /\nUser-agent: oodarag\nDisallow: /only\n"
        robots = self.parse(txt)

        self.assertEqual(robots.agent, "oodarag")
        self.assertTrue(robots.allowance("https://e.com/elsewhere")[0])
        self.assertFalse(robots.allowance("https://e.com/only")[0])

    def test_directives_before_any_user_agent_are_ignored(self) -> None:
        robots = self.parse("Disallow: /\n\nUser-agent: *\nDisallow: /x\n")

        self.assertTrue(robots.allowance("https://e.com/home")[0])
        self.assertFalse(robots.allowance("https://e.com/x")[0])

    def test_comments_and_blank_lines_are_stripped(self) -> None:
        txt = "# top comment\nUser-agent: *   # who\n\nDisallow: /x  # why\n"
        robots = self.parse(txt)

        self.assertFalse(robots.allowance("https://e.com/x")[0])

    def test_empty_disallow_means_no_restriction(self) -> None:
        robots = self.parse("User-agent: *\nDisallow:\n")

        self.assertEqual(robots.rules, [])
        self.assertTrue(robots.allowance("https://e.com/anything")[0])

    def test_unknown_and_malformed_lines_are_skipped(self) -> None:
        txt = "User-agent: *\nnonsense\nHost: example.com\nDisallow: /x\n"
        self.assertFalse(self.parse(txt).allowance("https://e.com/x")[0])

    def test_pattern_without_leading_slash_is_dropped(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: admin\n")

        self.assertEqual(robots.rules, [])
        self.assertTrue(robots.allowance("https://e.com/admin")[0])

    # -- line endings --------------------------------------------------------

    def test_crlf_line_endings(self) -> None:
        robots = self.parse("User-agent: *\r\nDisallow: /x\r\nSitemap: https://e.com/s.xml\r\n")

        self.assertFalse(robots.allowance("https://e.com/x")[0])
        self.assertEqual(robots.sitemaps, ["https://e.com/s.xml"])

    def test_bare_cr_line_endings(self) -> None:
        robots = self.parse("User-agent: *\rDisallow: /x\r")

        self.assertFalse(robots.allowance("https://e.com/x")[0])

    def test_unicode_line_separator_is_not_a_line_break(self) -> None:
        """`str.splitlines()` would cut here and leave a bare `Disallow: /a`,
        which blocks every path starting with /a. Only CR/LF end a line."""
        robots = self.parse("User-agent: *\nDisallow: /a b\n")

        self.assertTrue(robots.allowance("https://e.com/announcements")[0])
        self.assertFalse(robots.allowance("https://e.com/a b")[0])

    def test_leading_utf8_bom_does_not_void_the_first_group(self) -> None:
        robots = self.parse("﻿User-agent: *\nDisallow: /\n")

        self.assertEqual(robots.agent, "*")
        self.assertFalse(robots.allowance("https://e.com/anything")[0])

    # -- matching ------------------------------------------------------------

    def test_prefix_match_is_not_a_path_segment_match(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /admin\n")

        self.assertFalse(robots.allowance("https://e.com/administrator")[0])

    def test_star_wildcard_inside_a_pattern(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /a/*/secret\n")

        self.assertFalse(robots.allowance("https://e.com/a/b/secret")[0])
        self.assertFalse(robots.allowance("https://e.com/a/b/c/secret/x")[0])
        self.assertTrue(robots.allowance("https://e.com/a/secretish")[0])

    def test_dollar_anchors_the_end_of_the_pattern(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /*.pdf$\n")

        self.assertFalse(robots.allowance("https://e.com/docs/report.pdf")[0])
        self.assertTrue(robots.allowance("https://e.com/docs/report.pdf.html")[0])

    def test_dollar_on_a_literal_pattern(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /page$\n")

        self.assertFalse(robots.allowance("https://e.com/page")[0])
        self.assertTrue(robots.allowance("https://e.com/page/sub")[0])

    def test_repeated_stars_collapse(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /a**b\n")

        self.assertFalse(robots.allowance("https://e.com/a-x-b-y")[0])

    def test_trailing_star_is_a_plain_prefix(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /x*\n")

        self.assertFalse(robots.allowance("https://e.com/xyz")[0])
        self.assertTrue(robots.allowance("https://e.com/y")[0])

    def test_longest_match_wins_over_file_order(self) -> None:
        """The canonical pair. First-match-wins would block the whole subtree
        the site went out of its way to open."""
        robots = self.parse("User-agent: *\nDisallow: /docs\nAllow: /docs/public\n")

        self.assertFalse(robots.allowance("https://e.com/docs/private")[0])
        allowed, reason = robots.allowance("https://e.com/docs/public/guide")
        self.assertTrue(allowed)
        self.assertEqual(reason, "allow:/docs/public")

    def test_allow_beats_disallow_on_equal_length(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /x\nAllow: /x\n")

        self.assertEqual(robots.allowance("https://e.com/x"), (True, "allow:/x"))

    def test_allow_beats_disallow_regardless_of_declaration_order(self) -> None:
        robots = self.parse("User-agent: *\nAllow: /x\nDisallow: /x\n")

        self.assertTrue(robots.allowance("https://e.com/x")[0])

    def test_disallow_root_blocks_everything_including_the_bare_origin(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /\n")

        self.assertFalse(robots.allowance("https://e.com")[0])
        self.assertFalse(robots.allowance("https://e.com/")[0])
        self.assertFalse(robots.allowance("https://e.com/deep/path?q=1")[0])

    def test_dollar_on_root_matches_only_the_root(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /$\n")

        self.assertFalse(robots.allowance("https://e.com")[0])
        self.assertFalse(robots.allowance("https://e.com/")[0])
        self.assertTrue(robots.allowance("https://e.com/anything")[0])

    def test_our_group_is_used_even_when_it_carries_no_path_rules(self) -> None:
        """Group selection is exclusive: once our token has a group, the
        wildcard group stops applying, empty or not."""
        txt = "User-agent: oodarag\nCrawl-delay: 1\n\nUser-agent: *\nDisallow: /\n"
        robots = self.parse(txt)

        self.assertEqual(robots.agent, "oodarag")
        self.assertEqual(robots.rules, [])
        self.assertTrue(robots.allowance("https://e.com/anything")[0])

    def test_query_string_participates_in_the_match(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /*?session=\n")

        self.assertFalse(robots.allowance("https://e.com/p?session=abc")[0])
        self.assertTrue(robots.allowance("https://e.com/p?page=2")[0])

    def test_fragment_is_not_part_of_the_match(self) -> None:
        """The `$` anchor only matches if the fragment was dropped first."""
        robots = self.parse("User-agent: *\nDisallow: /p$\n")

        self.assertFalse(robots.allowance("https://e.com/p#section")[0])

    def test_a_hash_inside_a_value_starts_a_comment(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /a#b\n")

        self.assertFalse(robots.allowance("https://e.com/a")[0])
        self.assertTrue(robots.allowance("https://e.com/b")[0])

    def test_percent_encoding_is_normalised_on_both_sides(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /a%20b\n")

        self.assertFalse(robots.allowance("https://e.com/a%20b")[0])
        self.assertFalse(robots.allowance("https://e.com/a b")[0])

    def test_non_ascii_pattern_matches_its_encoded_url(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: /café\n")

        self.assertFalse(robots.allowance("https://e.com/caf%C3%A9/menu")[0])
        self.assertTrue(robots.allowance("https://e.com/cafe")[0])

    def test_match_target_normalises_the_empty_path(self) -> None:
        self.assertEqual(match_target("https://e.com"), "/")
        self.assertEqual(match_target("https://e.com/a?b=c#d"), "/a?b=c")

    def test_many_wildcards_do_not_blow_up(self) -> None:
        robots = self.parse("User-agent: *\nDisallow: " + "/*" * 40 + "x\n")

        self.assertFalse(robots.allowance("https://e.com/" + "a/" * 60 + "x")[0])
        self.assertTrue(robots.allowance("https://e.com/" + "a/" * 60 + "y")[0])

    # -- crawl-delay ---------------------------------------------------------

    def test_integer_crawl_delay(self) -> None:
        self.assertEqual(self.parse("User-agent: *\nCrawl-delay: 3\n").crawl_delay, 3.0)

    def test_fractional_crawl_delay_is_honoured(self) -> None:
        """stdlib's parser requires `isdigit()` and silently drops `0.5`."""
        self.assertEqual(self.parse("User-agent: *\nCrawl-delay: 0.5\n").crawl_delay, 0.5)

    def test_explicit_zero_in_our_group_beats_the_wildcard_delay(self) -> None:
        txt = "User-agent: oodarag\nCrawl-delay: 0\n\nUser-agent: *\nCrawl-delay: 30\n"

        self.assertEqual(self.parse(txt).crawl_delay, 0.0)

    def test_wildcard_delay_applies_when_our_group_is_silent_about_it(self) -> None:
        txt = "User-agent: oodarag\nDisallow: /x\n\nUser-agent: *\nCrawl-delay: 7\n"

        self.assertEqual(self.parse(txt).crawl_delay, 7.0)

    def test_unspecified_crawl_delay_is_none_not_zero(self) -> None:
        self.assertIsNone(self.parse("User-agent: *\nDisallow: /x\n").crawl_delay)

    def test_absurd_crawl_delay_is_clamped(self) -> None:
        self.assertEqual(
            self.parse("User-agent: *\nCrawl-delay: 86400\n").crawl_delay, MAX_CRAWL_DELAY_S
        )

    def test_invalid_crawl_delays_are_ignored(self) -> None:
        for value in ("soon", "-5", "nan", "inf", ""):
            with self.subTest(value=value):
                self.assertIsNone(self.parse(f"User-agent: *\nCrawl-delay: {value}\n").crawl_delay)

    def test_last_crawl_delay_in_a_group_wins(self) -> None:
        robots = self.parse("User-agent: *\nCrawl-delay: 1\nCrawl-delay: 4\n")

        self.assertEqual(robots.crawl_delay, 4.0)

    # -- sitemaps ------------------------------------------------------------

    def test_sitemaps_are_collected_outside_any_group(self) -> None:
        txt = ("Sitemap: https://e.com/a.xml\nUser-agent: *\nDisallow: /\n"
               "Sitemap: http://e.com/b.xml\n")

        self.assertEqual(parse_robots(txt, TOKEN).sitemaps,
                         ["https://e.com/a.xml", "http://e.com/b.xml"])

    def test_non_http_sitemaps_are_dropped(self) -> None:
        txt = ("Sitemap: file:///etc/passwd\n"
               "Sitemap: /relative.xml\n"
               "Sitemap: ftp://e.com/s.xml\n"
               "Sitemap: https://e.com/ok.xml\n")

        self.assertEqual(parse_robots(txt, TOKEN).sitemaps, ["https://e.com/ok.xml"])

    def test_sitemap_list_is_capped(self) -> None:
        txt = "".join(f"Sitemap: https://e.com/{i}.xml\n" for i in range(MAX_SITEMAPS + 20))

        self.assertEqual(len(parse_robots(txt, TOKEN).sitemaps), MAX_SITEMAPS)

    # -- size ----------------------------------------------------------------

    def test_oversized_file_is_truncated_at_a_line_boundary(self) -> None:
        head = "User-agent: *\nDisallow: /early\n"
        filler = "".join(f"# padding line {i}\n" for i in range(40_000))
        text = head + filler + "Disallow: /late\n"
        self.assertGreater(len(text), MAX_ROBOTS_BYTES)

        robots = self.parse(text)

        self.assertTrue(robots.truncated)
        self.assertFalse(robots.allowance("https://e.com/early")[0])
        self.assertTrue(robots.allowance("https://e.com/late")[0])

    def test_file_at_the_cap_is_not_truncated(self) -> None:
        text = "User-agent: *\nDisallow: /x\n"
        text += "#" + "p" * (MAX_ROBOTS_BYTES - len(text) - 2) + "\n"
        self.assertEqual(len(text), MAX_ROBOTS_BYTES)

        robots = self.parse(text)

        self.assertFalse(robots.truncated)
        self.assertFalse(robots.allowance("https://e.com/x")[0])

    def test_a_repeated_agent_in_one_block_does_not_multiply_its_rules(self) -> None:
        text = "User-agent: *\n" * 500 + "Disallow: /x\n" * 10
        robots = self.parse(text)

        self.assertEqual(len(robots.rules), 10)
        self.assertFalse(robots.allowance("https://e.com/x")[0])

    def test_rule_count_is_capped(self) -> None:
        text = "User-agent: *\n" + "".join(f"Disallow: /p{i}\n" for i in range(3000))

        self.assertEqual(len(self.parse(text).rules), 2000)


# -------------------------------------------------------------- status matrix


class StatusMatrixTestCase(unittest.TestCase):
    def test_2xx_parses_and_obeys(self) -> None:
        policy, opener = robots_policy("User-agent: *\nDisallow: /private\n")

        self.assertTrue(policy.allows(f"{ORIGIN}/public"))
        self.assertFalse(policy.allows(f"{ORIGIN}/private/x"))
        self.assertEqual(opener.requests, [f"{ORIGIN}/robots.txt"])

    def test_204_empty_body_allows_everything(self) -> None:
        policy, _ = make_policy(Reply(204, b""))

        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))
        self.assertEqual(policy.rules_for(ORIGIN).status, 204)

    def test_404_allows_everything(self) -> None:
        policy, _ = make_policy(Reply(404, b"not found"))
        rules = policy.rules_for(f"{ORIGIN}/x")

        self.assertTrue(rules.allow_all)
        self.assertFalse(rules.disallow_all)
        self.assertEqual(rules.reason, "unavailable")
        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))

    def test_410_allows_everything(self) -> None:
        policy, _ = make_policy(Reply(410, b"gone"))

        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))

    def test_other_4xx_allow_rather_than_being_read_as_unreachable(self) -> None:
        """400/451 are not in the client's allow_status, so they arrive as
        HttpError. Classifying by exception type instead of status turned every
        one of them into a full deny."""
        for status in (400, 405, 429, 451):
            with self.subTest(status=status):
                policy, _ = make_policy(Reply(status, b"nope"))
                rules = policy.rules_for(ORIGIN)

                self.assertTrue(rules.allow_all, f"{status} should allow")
                self.assertEqual(rules.status, status)
                self.assertTrue(policy.allows(f"{ORIGIN}/anything"))

    def test_401_denies_everything(self) -> None:
        policy, _ = make_policy(Reply(401, b"auth required"))
        rules = policy.rules_for(ORIGIN)

        self.assertTrue(rules.disallow_all)
        self.assertFalse(rules.allow_all)
        self.assertEqual(rules.reason, "restricted")
        self.assertFalse(policy.allows(f"{ORIGIN}/anything"))

    def test_403_denies_everything(self) -> None:
        policy, _ = make_policy(Reply(403, b"forbidden"))

        self.assertFalse(policy.allows(f"{ORIGIN}/anything"))
        self.assertEqual(policy.rules_for(ORIGIN).status, 403)

    def test_401_is_checked_before_the_generic_4xx_branch(self) -> None:
        """Ordering regression: a `status >= 400 -> allow` test placed first
        would swallow 401/403 and never deny."""
        allow_policy, _ = make_policy(Reply(404, b""))
        deny_policy, _ = make_policy(Reply(403, b""))

        self.assertTrue(allow_policy.allows(f"{ORIGIN}/x"))
        self.assertFalse(deny_policy.allows(f"{ORIGIN}/x"))

    def test_5xx_denies_by_default(self) -> None:
        policy, _ = make_policy(Reply(500, b"boom"))
        rules = policy.rules_for(ORIGIN)

        self.assertTrue(rules.disallow_all)
        self.assertEqual(rules.reason, "server_error")
        self.assertEqual(rules.status, 500)
        self.assertFalse(policy.allows(f"{ORIGIN}/anything"))

    def test_5xx_allows_when_on_error_is_allow(self) -> None:
        policy, _ = make_policy(Reply(503, b"down"), on_error="allow")

        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))
        self.assertTrue(policy.rules_for(ORIGIN).allow_all)

    def test_transport_failure_denies_by_default(self) -> None:
        policy, _ = make_policy(urllib.error.URLError("dns nope"))
        rules = policy.rules_for(ORIGIN)

        self.assertTrue(rules.disallow_all)
        self.assertEqual(rules.status, 0)
        self.assertEqual(rules.reason, "unreachable")

    def test_transport_failure_allows_when_configured_to(self) -> None:
        policy, _ = make_policy(urllib.error.URLError("dns nope"), on_error="allow")

        self.assertTrue(policy.allows(f"{ORIGIN}/x"))

    def test_unexpected_client_exception_fails_closed(self) -> None:
        policy = RobotsPolicy(client=FakeClient(ValueError("unknown url type")), user_agent=UA)
        rules = policy.rules_for(ORIGIN)

        self.assertTrue(rules.disallow_all)
        self.assertEqual(rules.reason, "fetch_error")

    def test_on_error_typo_falls_back_to_deny(self) -> None:
        for value in ("Deny", "ALLOW-ish", "", "nonsense", None):
            with self.subTest(value=value):
                policy, _ = make_policy(Reply(500, b""), on_error=value)

                self.assertEqual(policy.on_error, "deny")
                self.assertFalse(policy.allows(f"{ORIGIN}/x"))

    def test_on_error_allow_is_accepted_case_insensitively(self) -> None:
        policy, _ = make_policy(Reply(500, b""), on_error="  ALLOW ")

        self.assertEqual(policy.on_error, "allow")
        self.assertTrue(policy.allows(f"{ORIGIN}/x"))

    def test_empty_robots_txt_allows_everything(self) -> None:
        policy, _ = robots_policy("")

        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))
        self.assertEqual(policy.rules_for(ORIGIN).reason, "no_group")

    def test_html_soft_404_allows_and_is_reported_as_such(self) -> None:
        policy, _ = make_policy(
            Reply.raw(b"<!DOCTYPE html><html><body>Not found</body></html>", ctype="text/html")
        )

        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))
        self.assertEqual(policy.explain(f"{ORIGIN}/x")["reason"], "html_no_rules")

    def test_html_page_that_does_contain_rules_is_still_obeyed(self) -> None:
        """Being served text/html is not a licence to ignore what the body
        says: over-blocking is the safe direction."""
        policy, _ = make_policy(
            Reply.raw(b"<html><body><pre>\nUser-agent: *\nDisallow: /\n</pre></body></html>",
                      ctype="text/html")
        )

        self.assertFalse(policy.allows(f"{ORIGIN}/anything"))

    def test_gzip_encoded_robots_is_decoded_before_parsing(self) -> None:
        import gzip

        body = gzip.compress(b"User-agent: *\nDisallow: /z\n")
        policy, _ = make_policy(
            Reply(200, body, {"content-type": "text/plain", "content-encoding": "gzip"})
        )

        self.assertFalse(policy.allows(f"{ORIGIN}/z"))

    def test_latin1_declared_charset_is_honoured(self) -> None:
        body = "User-agent: *\nDisallow: /café\n".encode("latin-1")
        policy, _ = make_policy(
            Reply(200, body, {"content-type": "text/plain; charset=iso-8859-1"})
        )

        self.assertFalse(policy.allows(f"{ORIGIN}/caf%C3%A9"))

    def test_unsolicited_304_is_treated_as_no_usable_rules(self) -> None:
        """We never send If-None-Match here, so a 304 is a broken server, not a
        cache hit: it carries no rules and must not read as allow-all."""
        policy, _ = make_policy(Reply(304, b""))
        rules = policy.rules_for(ORIGIN)

        self.assertTrue(rules.disallow_all)
        self.assertEqual(rules.reason, "bad_status")

    def test_rules_are_cached_under_the_requested_origin_not_the_redirect_target(self) -> None:
        policy, opener = make_policy(
            Reply(200, b"User-agent: *\nDisallow: /x\n", {"content-type": "text/plain"},
                  final_url="https://cdn.example.net/robots.txt")
        )

        self.assertFalse(policy.allows(f"{ORIGIN}/x"))
        self.assertIn(ORIGIN, policy._cache)
        self.assertNotIn("https://cdn.example.net", policy._cache)
        self.assertEqual(len(opener.requests), 1)

    def test_utf8_bom_over_the_wire(self) -> None:
        policy, _ = make_policy(Reply.raw("﻿User-agent: *\nDisallow: /\n".encode()))

        self.assertFalse(policy.allows(f"{ORIGIN}/anything"))


# --------------------------------------------------------------------- cache


class CacheTestCase(unittest.TestCase):
    def test_one_fetch_serves_many_urls_on_one_origin(self) -> None:
        policy, opener = robots_policy("User-agent: *\nDisallow: /x\n")

        for path in ("/a", "/b", "/x", "/c"):
            policy.allows(ORIGIN + path)

        self.assertEqual(len(opener.requests), 1)

    def test_error_results_are_cached_too(self) -> None:
        """`fetched_at` must be set on every path, or a dead host is re-fetched
        once per URL for the whole crawl."""
        for reply in (Reply(500, b""), Reply(404, b""), Reply(403, b""),
                      urllib.error.URLError("down")):
            with self.subTest(reply=type(reply).__name__):
                policy, opener = make_policy(reply)
                policy.allows(f"{ORIGIN}/a")
                policy.allows(f"{ORIGIN}/b")

                self.assertEqual(len(opener.requests), 1)
                self.assertGreater(policy.rules_for(ORIGIN).fetched_at, 0.0)

    def test_expired_entry_is_refetched(self) -> None:
        policy, opener = make_policy(
            Reply.text("User-agent: *\nDisallow: /x\n"),
            Reply.text("User-agent: *\nDisallow: /y\n"),
            ttl_s=100.0,
        )
        self.assertFalse(policy.allows(f"{ORIGIN}/x"))

        policy._cache[ORIGIN].fetched_at -= 101.0

        self.assertTrue(policy.allows(f"{ORIGIN}/x"))
        self.assertFalse(policy.allows(f"{ORIGIN}/y"))
        self.assertEqual(len(opener.requests), 2)

    def test_entry_exactly_at_the_ttl_boundary_is_stale(self) -> None:
        policy, opener = make_policy(Reply.text(""), Reply.text(""), ttl_s=100.0)
        policy.allows(ORIGIN)

        policy._cache[ORIGIN].fetched_at -= 100.0
        policy.allows(ORIGIN)

        self.assertEqual(len(opener.requests), 2)

    def test_zero_ttl_never_caches(self) -> None:
        policy, opener = make_policy(Reply.text(""), ttl_s=0.0)
        policy.allows(ORIGIN)
        policy.allows(ORIGIN)

        self.assertEqual(len(opener.requests), 2)

    def test_scheme_is_part_of_the_key(self) -> None:
        policy, opener = make_policy(
            Reply.text("User-agent: *\nDisallow: /\n"), Reply.text("")
        )

        self.assertFalse(policy.allows("http://example.com/a"))
        self.assertTrue(policy.allows("https://example.com/a"))
        self.assertEqual(opener.requests,
                         ["http://example.com/robots.txt", "https://example.com/robots.txt"])

    def test_port_is_part_of_the_key(self) -> None:
        policy, opener = make_policy(Reply.text(""), Reply.text(""))
        policy.allows("https://example.com:8443/a")
        policy.allows("https://example.com:9443/a")

        self.assertEqual(opener.requests, ["https://example.com:8443/robots.txt",
                                           "https://example.com:9443/robots.txt"])

    def test_default_port_and_host_case_share_one_key(self) -> None:
        policy, opener = make_policy(Reply.text("User-agent: *\nDisallow: /x\n"))

        self.assertFalse(policy.allows("https://example.com/x"))
        self.assertFalse(policy.allows("https://EXAMPLE.com:443/x"))
        self.assertFalse(policy.allows("HTTPS://Example.COM/x"))
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(opener.requests[0], "https://example.com/robots.txt")

    def test_http_default_port_is_dropped_too(self) -> None:
        policy, opener = make_policy(Reply.text(""))
        policy.allows("http://example.com:80/x")

        self.assertEqual(opener.requests, ["http://example.com/robots.txt"])

    def test_ipv6_origin_keeps_its_brackets(self) -> None:
        policy, opener = make_policy(Reply.text("User-agent: *\nDisallow: /x\n"))

        self.assertFalse(policy.allows("https://[2001:db8::1]:8443/x"))
        self.assertEqual(opener.requests, ["https://[2001:db8::1]:8443/robots.txt"])

    def test_changing_the_user_agent_invalidates_the_cache(self) -> None:
        body = "User-agent: alpha\nDisallow: /\n\nUser-agent: beta\nDisallow: /nothing\n"
        policy, opener = make_policy(Reply.text(body), user_agent="alpha/1.0")

        self.assertFalse(policy.allows(f"{ORIGIN}/x"))
        policy.user_agent = "beta/2.0"

        self.assertTrue(policy.allows(f"{ORIGIN}/x"))
        self.assertEqual(len(opener.requests), 2)

    def test_cache_is_bounded(self) -> None:
        policy, opener = make_policy(Reply.text(""), max_entries=4)
        for i in range(20):
            policy.allows(f"https://host{i}.example/x")

        self.assertLessEqual(len(policy._cache), 4)
        self.assertIn("https://host19.example", policy._cache)
        self.assertEqual(len(opener.requests), 20)

    def test_pruning_drops_expired_entries_first(self) -> None:
        policy, _ = make_policy(Reply.text(""), max_entries=2, ttl_s=100.0)
        policy.allows("https://a.example/x")
        policy.allows("https://b.example/x")
        policy._cache["https://a.example"].fetched_at -= 500.0

        policy.allows("https://c.example/x")

        self.assertNotIn("https://a.example", policy._cache)
        self.assertIn("https://b.example", policy._cache)
        self.assertIn("https://c.example", policy._cache)

    def test_clear_cache_forces_a_refetch(self) -> None:
        policy, opener = make_policy(Reply.text(""))
        policy.allows(f"{ORIGIN}/x")
        policy.clear_cache()
        policy.allows(f"{ORIGIN}/x")

        self.assertEqual(len(opener.requests), 2)


# ------------------------------------------------------------------ url safety


class UrlSafetyTestCase(unittest.TestCase):
    def test_credentials_in_the_url_never_reach_the_request_or_the_report(self) -> None:
        policy, opener = make_policy(Reply.text("User-agent: *\nDisallow: /x\n"))
        url = "https://user:s3cr3t-token@example.com/x"

        self.assertFalse(policy.allows(url))
        self.assertEqual(opener.requests, ["https://example.com/robots.txt"])
        report = policy.explain(url)
        self.assertEqual(report["host"], "example.com")
        self.assertNotIn("s3cr3t", str(report["host"]))
        self.assertNotIn("s3cr3t", "".join(policy._cache))

    def test_non_http_schemes_are_denied_without_a_request(self) -> None:
        policy, opener = make_policy(Reply.text(""))

        for url in ("file:///etc/passwd", "ftp://example.com/x", "mailto:a@b.c",
                    "javascript:alert(1)", "data:text/plain,hi"):
            with self.subTest(url=url):
                self.assertFalse(policy.allows(url))

        self.assertEqual(opener.requests, [])
        self.assertEqual(policy.rules_for("file:///etc/passwd").reason, "unsupported_scheme")

    def test_urls_without_a_host_are_denied_without_a_request(self) -> None:
        policy, opener = make_policy(Reply.text(""))

        for url in ("", "/relative/path", "https://", "not a url at all"):
            with self.subTest(url=url):
                self.assertFalse(policy.allows(url))

        self.assertEqual(opener.requests, [])

    def test_malformed_authority_does_not_raise(self) -> None:
        policy, opener = make_policy(Reply.text(""))

        for url in ("https://[::1", "https://example.com:notaport/x", "https://ex ample.com/"):
            with self.subTest(url=url):
                self.assertIsInstance(policy.allows(url), bool)

        self.assertEqual(opener.requests, [])

    def test_unsupported_scheme_is_not_cached(self) -> None:
        policy, _ = make_policy(Reply.text(""))
        policy.allows("file:///etc/passwd")

        self.assertEqual(policy._cache, {})


# ------------------------------------------------------------ policy surface


class PolicySurfaceTestCase(unittest.TestCase):
    def test_crawl_delay_is_surfaced(self) -> None:
        policy, _ = robots_policy("User-agent: *\nCrawl-delay: 2.5\n")

        self.assertEqual(policy.crawl_delay(f"{ORIGIN}/x"), 2.5)

    def test_crawl_delay_defaults_to_zero_when_unspecified(self) -> None:
        policy, _ = robots_policy("User-agent: *\nDisallow: /x\n")

        self.assertEqual(policy.crawl_delay(f"{ORIGIN}/x"), 0.0)
        self.assertIsNone(policy.rules_for(ORIGIN).crawl_delay)

    def test_explicit_zero_delay_is_distinguishable_from_unspecified(self) -> None:
        policy, _ = robots_policy("User-agent: *\nCrawl-delay: 0\n")

        self.assertEqual(policy.crawl_delay(f"{ORIGIN}/x"), 0.0)
        self.assertEqual(policy.rules_for(ORIGIN).crawl_delay, 0.0)

    def test_crawl_delay_on_an_error_response_is_zero(self) -> None:
        policy, _ = make_policy(Reply(500, b""))

        self.assertEqual(policy.crawl_delay(f"{ORIGIN}/x"), 0.0)

    def test_sitemaps_are_surfaced(self) -> None:
        policy, _ = robots_policy(
            "Sitemap: https://example.com/sitemap.xml\nUser-agent: *\nDisallow: /x\n"
        )

        self.assertEqual(policy.sitemaps(f"{ORIGIN}/x"), ["https://example.com/sitemap.xml"])

    def test_sitemaps_returns_a_copy_so_callers_cannot_poison_the_cache(self) -> None:
        policy, _ = robots_policy("Sitemap: https://example.com/a.xml\n")
        got = policy.sitemaps(ORIGIN)
        got.append("https://evil.example/b.xml")

        self.assertEqual(policy.sitemaps(ORIGIN), ["https://example.com/a.xml"])

    def test_sitemaps_on_an_error_response_is_empty(self) -> None:
        policy, _ = make_policy(urllib.error.URLError("down"))

        self.assertEqual(policy.sitemaps(ORIGIN), [])


class ObeyDisabledTestCase(unittest.TestCase):
    def test_allows_makes_no_request(self) -> None:
        policy, opener = make_policy(Reply.text("User-agent: *\nDisallow: /\n"), obey=False)

        self.assertTrue(policy.allows(f"{ORIGIN}/anything"))
        self.assertEqual(opener.requests, [])
        self.assertEqual(policy._cache, {})

    def test_crawl_delay_makes_no_request(self) -> None:
        policy, opener = make_policy(Reply.text("User-agent: *\nCrawl-delay: 30\n"), obey=False)

        self.assertEqual(policy.crawl_delay(f"{ORIGIN}/x"), 0.0)
        self.assertEqual(opener.requests, [])

    def test_explain_makes_no_request_and_says_why(self) -> None:
        policy, opener = make_policy(Reply.text("User-agent: *\nDisallow: /\n"), obey=False)
        report = policy.explain(f"{ORIGIN}/x")

        self.assertEqual(opener.requests, [])
        self.assertTrue(report["allowed"])
        self.assertEqual(report["reason"], "robots_disabled")
        self.assertFalse(report["obey"])
        self.assertEqual(report["host"], "example.com")

    def test_sitemaps_still_fetch_because_discovery_is_not_enforcement(self) -> None:
        policy, opener = make_policy(Reply.text("Sitemap: https://example.com/s.xml\n"), obey=False)

        self.assertEqual(policy.sitemaps(ORIGIN), ["https://example.com/s.xml"])
        self.assertEqual(len(opener.requests), 1)


class ExplainTestCase(unittest.TestCase):
    def test_explain_names_the_rule_that_blocked_the_url(self) -> None:
        policy, _ = robots_policy(
            "User-agent: oodarag\nDisallow: /docs\nAllow: /docs/public\nCrawl-delay: 1\n"
            "Sitemap: https://example.com/s1.xml\n"
        )

        blocked = policy.explain(f"{ORIGIN}/docs/private")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason"], "disallow:/docs")
        self.assertEqual(blocked["agent"], "oodarag")
        self.assertEqual(blocked["host"], "example.com")
        self.assertEqual(blocked["robots_status"], 200)
        self.assertEqual(blocked["crawl_delay"], 1.0)
        self.assertEqual(blocked["sitemaps"], ["https://example.com/s1.xml"])
        self.assertEqual(blocked["sitemap_count"], 1)
        self.assertTrue(blocked["obey"])
        self.assertFalse(blocked["allow_all"])
        self.assertFalse(blocked["disallow_all"])

        allowed = policy.explain(f"{ORIGIN}/docs/public/x")
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["reason"], "allow:/docs/public")

    def test_explain_agrees_with_allows(self) -> None:
        policy, _ = robots_policy("User-agent: *\nDisallow: /a\nAllow: /a/b\n")

        for path in ("/", "/a", "/a/b", "/a/b/c", "/z"):
            with self.subTest(path=path):
                self.assertEqual(policy.explain(ORIGIN + path)["allowed"],
                                 policy.allows(ORIGIN + path))

    def test_explain_reports_the_deny_reason_for_a_dead_host(self) -> None:
        policy, _ = make_policy(Reply(503, b""))
        report = policy.explain(f"{ORIGIN}/x")

        self.assertFalse(report["allowed"])
        self.assertEqual(report["reason"], "server_error")
        self.assertTrue(report["disallow_all"])
        self.assertEqual(report["robots_status"], 503)

    def test_explain_truncates_the_sitemap_list_but_reports_the_count(self) -> None:
        body = "".join(f"Sitemap: https://example.com/{i}.xml\n" for i in range(9))
        policy, _ = robots_policy(body)
        report = policy.explain(ORIGIN)

        self.assertEqual(len(report["sitemaps"]), 5)
        self.assertEqual(report["sitemap_count"], 9)

    def test_explain_key_set_is_stable(self) -> None:
        """The crawl report serialises this dict; both branches must agree on
        its shape or a disabled-robots run drops columns."""
        expected = {"url", "host", "allowed", "reason", "obey", "robots_status",
                    "allow_all", "disallow_all", "crawl_delay", "sitemaps",
                    "sitemap_count", "agent"}
        on, _ = robots_policy("User-agent: *\nDisallow: /x\n")
        off, _ = robots_policy("User-agent: *\nDisallow: /x\n", obey=False)

        self.assertEqual(set(on.explain(f"{ORIGIN}/x")), expected)
        self.assertEqual(set(off.explain(f"{ORIGIN}/x")), expected)

    def test_explain_does_not_re_fetch(self) -> None:
        policy, opener = robots_policy("User-agent: *\nDisallow: /x\n")
        policy.explain(f"{ORIGIN}/x")
        policy.explain(f"{ORIGIN}/y")

        self.assertEqual(len(opener.requests), 1)

    def test_explain_of_an_unsupported_scheme_is_honest(self) -> None:
        policy, _ = make_policy(Reply.text(""))
        report = policy.explain("file:///etc/passwd")

        self.assertFalse(report["allowed"])
        self.assertEqual(report["reason"], "unsupported_scheme")


class HostRulesTestCase(unittest.TestCase):
    def test_default_sitemaps_list_is_not_shared_between_instances(self) -> None:
        a = HostRules("a", None, True, False, None)
        b = HostRules("b", None, True, False, None)
        a.sitemaps.append("https://a/s.xml")

        self.assertEqual(b.sitemaps, [])


if __name__ == "__main__":
    unittest.main()
