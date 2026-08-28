"""The HTTP client and the small utilities under it, driven entirely offline.

Not one test here opens a socket. `HttpClient` talks to whatever object sits in
its `_opener` attribute, so every response in this file - a 429 that clears on
the second attempt, a server that lies about `Content-Length`, a gzip stream cut
in half - is handed to the client by a `FakeOpener`. That is not only about CI
having no egress: none of those cases can be produced on demand by a real host,
and a test that waits for one is a test that is flaky by construction.

The package's stated principle is "degrade, don't die", so the failure paths get
as much room as the happy path. Where a test encodes a bug that was found and
fixed while writing it, the comment says which bug and what it cost.
"""

from __future__ import annotations

import contextlib
import email.message
import gzip
import io
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
import zlib

from oodarag.util import hashing
from oodarag.util import http as http_module
from oodarag.util.hashing import blake_bucket, blake_sign, content_hash, sha256_hex, stable_id
from oodarag.util.http import (
    HttpClient,
    HttpError,
    Response,
    RetryPolicy,
    TransportError,
    _decompress,
    _NoRedirectOnPost,
    _retry_after,
    normalize_url,
    same_site,
    urljoin,
)
from oodarag.util.logging import Logger, get_logger
from oodarag.util.ratelimit import TokenBucket

# Retries are real sleeps, so every client in this file uses a policy whose
# delays are microscopic. The behaviour under test is the decision to retry,
# never the length of the pause.
FAST = RetryPolicy(attempts=3, base_delay=0.001, max_delay=0.01, jitter=0.0)

# Truncation tests need a body whose compressed form is long enough that half of
# it still decodes to something: half of a 40-byte deflate stream is all header
# and window, and would prove nothing about salvaging a prefix.
LONG_PAGE = b"".join(b"line %04d the quick brown fox jumps over the lazy dog\n" % i
                     for i in range(400))


_LEVEL_SILENT = 100
_LOG_LEVEL = 20


def setUpModule() -> None:
    # The retry paths log a warning per attempt. That is correct behaviour and
    # nothing here asserts on it, but left alone it interleaves with the test
    # results and makes a real failure hard to find.
    global _LOG_LEVEL
    _LOG_LEVEL = http_module.log.level
    http_module.log.level = _LEVEL_SILENT


def tearDownModule() -> None:
    http_module.log.level = _LOG_LEVEL


# --------------------------------------------------------------------- fixtures


def http_headers(pairs: dict[str, str]) -> email.message.Message:
    """The header container urllib hands back: case-insensitive, `.items()`able."""
    msg = email.message.Message()
    for key, value in pairs.items():
        msg[key] = value
    return msg


class FakeResponse:
    """What `opener.open()` returns: a context manager over a body.

    `explode_on_read` proves a check happened *before* the body was touched;
    `reads` counts calls, which is how the streaming cap is shown to stop early
    rather than to buffer everything and measure afterwards.
    """

    def __init__(self, url: str, status: int = 200, headers: dict[str, str] | None = None,
                 body: bytes = b"", explode_on_read: bool = False) -> None:
        self.url = url
        self.status = status
        self.headers = http_headers(headers or {})
        self._stream = io.BytesIO(body)
        self.explode_on_read = explode_on_read
        self.reads = 0

    def read(self, size: int = -1) -> bytes:
        if self.explode_on_read:
            raise AssertionError("the body must not be read once the size cap is known")
        self.reads += 1
        return self._stream.read(size)

    def geturl(self) -> str:
        return self.url

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


class FakeOpener:
    """Stands in for the urllib opener: one method, `.open(req, timeout=...)`.

    Queue entries are `FakeResponse`s, exceptions to raise, or zero-argument
    callables producing either. The last entry repeats, so "every attempt fails"
    needs one entry rather than one per attempt.
    """

    def __init__(self, *items: object) -> None:
        self.items = list(items)
        self.requests: list[urllib.request.Request] = []
        self.served: list[object] = []

    def open(self, req: urllib.request.Request, timeout: float | None = None) -> object:
        self.requests.append(req)
        item = self.items.pop(0) if len(self.items) > 1 else self.items[0]
        if callable(item):
            item = item()
        self.served.append(item)
        if isinstance(item, BaseException):
            raise item
        return item


def make_client(*items: object, **kwargs: object) -> HttpClient:
    kwargs.setdefault("retry", FAST)
    kwargs.setdefault("rate_per_sec", 1000.0)  # the bucket is not what is under test
    client = HttpClient(**kwargs)  # type: ignore[arg-type]
    client._opener = FakeOpener(*items)
    return client


def ok(body: bytes = b"hello", status: int = 200, url: str = "https://x.test/a",
       headers: dict[str, str] | None = None, **kw: object):
    """A callable, so a repeated entry serves a fresh (unread) body each time."""
    hdrs = {"Content-Type": "text/html; charset=utf-8", **(headers or {})}
    return lambda: FakeResponse(url, status, hdrs, body, **kw)  # type: ignore[arg-type]


def http_error(code: int, headers: dict[str, str] | None = None, body: bytes = b"boom",
               url: str = "https://x.test/a"):
    return lambda: urllib.error.HTTPError(url, code, "fake", http_headers(headers or {}),
                                          io.BytesIO(body))


# ----------------------------------------------------------------- retry policy


class TestRetryDecisions(unittest.TestCase):
    def test_a_429_is_retried_and_the_next_response_is_returned(self):
        client = make_client(http_error(429), ok(b"finally"))
        resp = client.get("https://x.test/a")
        self.assertEqual(resp.body, b"finally")
        self.assertEqual(len(client._opener.requests), 2)
        self.assertEqual(client.stats["retries"], 1)
        self.assertEqual(client.stats["requests"], 1)
        self.assertEqual(client.stats["errors"], 0)

    def test_a_500_is_retried(self):
        client = make_client(http_error(503), ok(b"up again"))
        self.assertEqual(client.get("https://x.test/a").body, b"up again")
        self.assertEqual(client.stats["retries"], 1)

    def test_a_404_is_not_retried(self):
        # Retrying a 4xx costs the same wall clock as retrying a 5xx and can
        # never succeed; a crawler that does it turns one dead link into three.
        client = make_client(http_error(404), ok(b"never reached"))
        with self.assertRaises(HttpError) as caught:
            client.get("https://x.test/a")
        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(len(client._opener.requests), 1)
        self.assertEqual(client.stats["retries"], 0)
        self.assertEqual(client.stats["errors"], 1)

    def test_exhausted_attempts_raise_the_last_http_error(self):
        client = make_client(http_error(503, body=b"still down"))
        with self.assertRaises(HttpError) as caught:
            client.get("https://x.test/a")
        self.assertEqual(caught.exception.status, 503)
        self.assertIn("still down", caught.exception.body)
        self.assertEqual(len(client._opener.requests), FAST.attempts)
        self.assertEqual(client.stats["retries"], FAST.attempts - 1)
        self.assertEqual(client.stats["errors"], 1)
        self.assertEqual(client.stats["requests"], 0)

    def test_an_error_body_and_headers_travel_with_the_exception(self):
        # The caller decides what to do about a 403 by reading it - a GitHub
        # rate-limit 403 and a permissions 403 are the same status code.
        client = make_client(http_error(403, {"X-RateLimit-Remaining": "0"}, b"rate limited"))
        with self.assertRaises(HttpError) as caught:
            client.get("https://x.test/a")
        self.assertEqual(caught.exception.body, "rate limited")
        self.assertEqual(caught.exception.headers["x-ratelimit-remaining"], "0")
        self.assertFalse(caught.exception.retryable)


class TestRetryDelays(unittest.TestCase):
    def test_retry_after_wins_over_exponential_backoff(self):
        policy = RetryPolicy(base_delay=1.0, max_delay=30.0, jitter=0.25)
        self.assertEqual(policy.delay_for(1, retry_after=7.0), 7.0)

    def test_a_delay_never_exceeds_max_delay_even_with_jitter(self):
        # Bug (fixed): jitter was applied *after* the cap, so a policy documented
        # as "wait at most 30s" slept up to 37.5s. On a host that 429s a whole
        # crawl, that is minutes of unbudgeted stall per run.
        policy = RetryPolicy(base_delay=10.0, max_delay=30.0, jitter=0.25)
        delays = [policy.delay_for(6) for _ in range(500)]
        self.assertLessEqual(max(delays), policy.max_delay)
        self.assertGreater(max(delays), 0.0)
        self.assertLessEqual(policy.delay_for(1, retry_after=900.0), policy.max_delay)

    def test_a_jitter_wider_than_the_delay_never_goes_negative(self):
        # Bug (fixed): jitter >= 1.0 could make delay_for() return a negative
        # number, and `time.sleep()` rejects those with ValueError - so a
        # retryable 503 surfaced to the caller as an unrelated crash from inside
        # the retry loop, with the real status code nowhere in the traceback.
        policy = RetryPolicy(base_delay=1.0, max_delay=30.0, jitter=1.5)
        self.assertGreaterEqual(min(policy.delay_for(1) for _ in range(500)), 0.0)

    def test_a_wide_jitter_policy_still_completes_a_retry(self):
        # The end-to-end half of the bug above: this call used to raise
        # ValueError instead of returning the retried response.
        client = make_client(http_error(503), ok(b"recovered"),
                             retry=RetryPolicy(attempts=3, base_delay=0.001,
                                               max_delay=0.01, jitter=1.5))
        self.assertEqual(client.get("https://x.test/a").body, b"recovered")


class TestRetryAfterHeader(unittest.TestCase):
    def test_retry_after_seconds_is_honoured(self):
        self.assertEqual(_retry_after({"retry-after": " 12 "}), 12.0)

    def test_a_retry_after_date_falls_back_to_backoff(self):
        # Documented limitation, not an accident: only the delta-seconds form is
        # parsed, and the HTTP-date form yields None so the caller backs off
        # exponentially rather than guessing at a clock skew.
        self.assertIsNone(_retry_after({"retry-after": "Wed, 21 Oct 2015 07:28:00 GMT"}))

    def test_a_spent_github_quota_waits_until_the_reset(self):
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) + 30)}
        wait = _retry_after(headers)
        self.assertIsNotNone(wait)
        assert wait is not None
        self.assertGreater(wait, 25.0)
        self.assertLess(wait, 33.0)

    def test_a_reset_in_the_past_does_not_produce_a_negative_wait(self):
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) - 500)}
        self.assertEqual(_retry_after(headers), 1.0)

    def test_a_quota_with_calls_left_is_not_a_rate_limit(self):
        headers = {"x-ratelimit-remaining": "17", "x-ratelimit-reset": str(int(time.time()) + 30)}
        self.assertIsNone(_retry_after(headers))

    def test_an_unparseable_reset_is_ignored_rather_than_fatal(self):
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "soon"}
        self.assertIsNone(_retry_after(headers))

    def test_headers_without_any_hint_return_none(self):
        self.assertIsNone(_retry_after({}))


# -------------------------------------------------------------- conditional GET


class TestConditionalRequests(unittest.TestCase):
    def test_an_etag_is_replayed_as_if_none_match(self):
        client = make_client(ok(b"v1", headers={"ETag": 'W/"abc"'}), ok(b"v2"))
        client.get("https://x.test/a", conditional=True)
        client.get("https://x.test/a", conditional=True)
        self.assertEqual(client._opener.requests[1].get_header("If-none-match"), 'W/"abc"')

    def test_an_etag_is_only_sent_when_the_caller_asks_for_a_conditional_get(self):
        # Sending If-None-Match on a fetch whose caller wants the body would
        # hand back an empty 304 body and look like an empty page.
        client = make_client(ok(b"v1", headers={"ETag": 'W/"abc"'}), ok(b"v2"))
        client.get("https://x.test/a", conditional=True)
        client.get("https://x.test/a")
        self.assertIsNone(client._opener.requests[1].get_header("If-none-match"))

    def test_an_etag_is_scoped_to_its_own_url(self):
        client = make_client(ok(b"v1", headers={"ETag": 'W/"abc"'}), ok(b"other"))
        client.get("https://x.test/a", conditional=True)
        client.get("https://x.test/b", conditional=True)
        self.assertIsNone(client._opener.requests[1].get_header("If-none-match"))

    def test_a_304_comes_back_as_an_empty_cached_response(self):
        client = make_client(http_error(304, {"ETag": 'W/"abc"'}, b""))
        resp = client.get("https://x.test/a", conditional=True)
        self.assertEqual(resp.status, 304)
        self.assertTrue(resp.from_cache)
        self.assertEqual(resp.body, b"")
        self.assertEqual(client.stats["not_modified"], 1)
        self.assertEqual(client.stats["errors"], 0)

    def test_a_304_is_not_retried(self):
        # "Unchanged" is the answer, not a failure: re-fetching it three times
        # would triple the cost of every incremental re-crawl.
        client = make_client(http_error(304))
        client.get("https://x.test/a", conditional=True)
        self.assertEqual(len(client._opener.requests), 1)


# ----------------------------------------------------------------- size ceiling


class TestSizeCaps(unittest.TestCase):
    def test_a_declared_content_length_over_the_cap_is_refused_before_reading(self):
        client = make_client(ok(b"", headers={"Content-Length": "99999"}, explode_on_read=True),
                             max_bytes=1000)
        with self.assertRaises(TransportError) as caught:
            client.get("https://x.test/big")
        self.assertIn("too large", str(caught.exception))
        # Refusing an oversized response is a verdict, not a transient failure:
        # retrying it three times just downloads the same refusal three times.
        self.assertEqual(len(client._opener.requests), 1)

    def test_a_lying_content_length_is_caught_by_the_streaming_cap(self):
        # A hostile or broken host can declare 10 bytes and stream for ever.
        # The cap has to be enforced while reading, or one URL exhausts memory.
        client = make_client(ok(b"x" * 200_000, headers={"Content-Length": "10"}), max_bytes=1000)
        with self.assertRaises(TransportError) as caught:
            client.get("https://x.test/liar")
        self.assertIn("exceeded cap", str(caught.exception))
        self.assertEqual(client._opener.served[0].reads, 1,
                         "the read loop must stop at the cap, not drain the stream first")

    def test_a_body_under_the_cap_is_returned_whole(self):
        client = make_client(ok(b"y" * 900, headers={"Content-Length": "900"}), max_bytes=1000)
        self.assertEqual(len(client.get("https://x.test/ok").body), 900)

    def test_a_non_numeric_content_length_does_not_break_the_fetch(self):
        # Malformed headers are common; the streaming cap is the real defence.
        client = make_client(ok(b"body", headers={"Content-Length": "banana"}), max_bytes=1000)
        self.assertEqual(client.get("https://x.test/ok").body, b"body")


# ---------------------------------------------------------------- decompression


class TestDecompression(unittest.TestCase):
    def test_a_gzip_body_is_decompressed(self):
        self.assertEqual(_decompress(gzip.compress(b"hello"), "gzip"), b"hello")

    def test_encoding_matching_ignores_case_and_padding(self):
        self.assertEqual(_decompress(gzip.compress(b"hello"), " GZIP "), b"hello")

    def test_both_flavours_of_deflate_are_accepted(self):
        # RFC 1950 (zlib-wrapped) is what the spec means; several real servers
        # send RFC 1951 raw deflate under the same header, and refusing those
        # would lose the page for a difference the caller cannot see.
        self.assertEqual(_decompress(zlib.compress(b"payload"), "deflate"), b"payload")
        raw = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        self.assertEqual(_decompress(raw.compress(b"payload") + raw.flush(), "deflate"), b"payload")

    def test_a_server_lying_about_gzip_yields_the_raw_bytes(self):
        self.assertEqual(_decompress(b"<html>not gzipped</html>", "gzip"), b"<html>not gzipped</html>")

    def test_a_server_lying_about_deflate_yields_the_raw_bytes(self):
        self.assertEqual(_decompress(b"plain text", "deflate"), b"plain text")

    def test_an_unknown_encoding_is_passed_through(self):
        self.assertEqual(_decompress(b"br-ish", "br"), b"br-ish")

    def test_a_truncated_gzip_body_keeps_the_part_that_decoded(self):
        # Bug (fixed): a stream cut mid-body raises EOFError, which is neither
        # OSError nor zlib.error - the two families `_decompress` caught - and
        # neither is it caught by `request()`, whose handlers cover URLError and
        # OSError. So one truncated response (a reset connection, a proxy that
        # gave up) escaped as a bare EOFError and killed the whole fetch. Now
        # the prefix that did decompress is kept: a partial page degrades.
        full = gzip.compress(LONG_PAGE)
        salvaged = _decompress(full[: len(full) // 2], "gzip")
        self.assertTrue(salvaged.startswith(b"line 0000 the quick brown fox"))
        self.assertLess(len(salvaged), len(LONG_PAGE))

    def test_a_truncated_gzip_body_does_not_escape_the_client(self):
        truncated = gzip.compress(LONG_PAGE)
        client = make_client(ok(truncated[: len(truncated) // 2],
                                headers={"Content-Encoding": "gzip"}))
        body = client.get("https://x.test/cut").body
        self.assertTrue(body.startswith(b"line 0000 the quick brown fox"))

    def test_a_truncated_deflate_body_keeps_the_part_that_decoded(self):
        full = zlib.compress(LONG_PAGE)
        salvaged = _decompress(full[: len(full) // 2], "deflate")
        self.assertTrue(salvaged.startswith(b"line 0000 the quick brown fox"))

    def test_a_truncation_too_early_to_salvage_returns_the_bytes_rather_than_raising(self):
        # Nothing decodes out of a stump of a gzip header. The contract is only
        # that the caller gets bytes back instead of an exception from a code
        # path that has no handler for one.
        stump = gzip.compress(LONG_PAGE)[:12]
        self.assertEqual(_decompress(stump, "gzip"), stump)

    def test_an_empty_body_with_a_compression_header_is_empty_not_fatal(self):
        # HEAD responses and 204s arrive with the encoding header and no body.
        self.assertEqual(_decompress(b"", "gzip"), b"")
        self.assertEqual(_decompress(b"", "deflate"), b"")

    def test_a_compressed_response_is_decompressed_end_to_end(self):
        client = make_client(ok(gzip.compress(b"<html>hi</html>"),
                                headers={"Content-Encoding": "gzip"}))
        resp = client.get("https://x.test/a")
        self.assertEqual(resp.body, b"<html>hi</html>")
        # `bytes` accounting is what the caller sees, not what crossed the wire.
        self.assertEqual(client.stats["bytes"], len(b"<html>hi</html>"))


# -------------------------------------------------------------------- responses


class TestResponseDecoding(unittest.TestCase):
    def test_the_declared_charset_is_used(self):
        resp = Response("u", 200, {"content-type": "text/html; charset=iso-8859-1"},
                        "café".encode("iso-8859-1"))
        self.assertEqual(resp.text, "café")

    def test_an_uppercase_charset_parameter_is_honoured(self):
        # Bug (fixed): the parameter name was matched case-sensitively, but
        # RFC 2045 says it is case-insensitive and servers do send `Charset=`.
        # Such a page was decoded as utf-8, so every accented character in it
        # became U+FFFD and the text reached the index as mojibake.
        resp = Response("u", 200, {"content-type": "text/html; Charset=ISO-8859-1"},
                        "café".encode("iso-8859-1"))
        self.assertEqual(resp.text, "café")

    def test_an_unknown_charset_falls_back_to_utf8(self):
        # A made-up charset must not take the page down: LookupError from
        # `bytes.decode` is the one exception this property has to absorb.
        resp = Response("u", 200, {"content-type": "text/html; charset=x-mac-klingon"},
                        "héllo".encode("utf-8"))
        self.assertEqual(resp.text, "héllo")

    def test_an_empty_charset_parameter_falls_back_to_utf8(self):
        resp = Response("u", 200, {"content-type": "text/html; charset="}, b"plain")
        self.assertEqual(resp.text, "plain")

    def test_undecodable_bytes_are_replaced_rather_than_raising(self):
        resp = Response("u", 200, {"content-type": "text/plain; charset=utf-8"}, b"a\xffb")
        self.assertEqual(resp.text, "a�b")

    def test_content_type_drops_parameters_and_lowercases(self):
        resp = Response("u", 200, {"content-type": "TEXT/HTML; charset=utf-8"}, b"")
        self.assertEqual(resp.content_type, "text/html")

    def test_a_missing_content_type_is_empty_not_none(self):
        # Callers compare against a frozenset of types; None would blow up there.
        self.assertEqual(Response("u", 200, {}, b"").content_type, "")

    def test_json_parses_the_body(self):
        self.assertEqual(Response("u", 200, {}, b'{"a": 1}').json(), {"a": 1})

    def test_json_on_a_non_json_body_raises_a_json_error(self):
        # get_json() callers catch ValueError; an HTML error page served with a
        # JSON content type must land there and not somewhere unexpected.
        with self.assertRaises(json.JSONDecodeError):
            Response("u", 200, {}, b"<html>502</html>").json()


# -------------------------------------------------------------------- redirects


class TestRedirectHandling(unittest.TestCase):
    def setUp(self):
        self.handler = _NoRedirectOnPost()

    def _redirect(self, method: str, body: bytes | None = None):
        req = urllib.request.Request("https://x.test/a", data=body, method=method)
        return self.handler.redirect_request(req, io.BytesIO(b""), 302, "Found",
                                             http_headers({}), "https://x.test/b")

    def test_a_redirect_on_post_is_not_followed(self):
        # Replaying a POST at a new URL can submit the same form twice; urllib's
        # default even downgrades 301/302 POSTs to GET silently.
        self.assertIsNone(self._redirect("POST", b"payload=1"))

    def test_a_redirect_on_get_is_followed(self):
        new = self._redirect("GET")
        self.assertIsInstance(new, urllib.request.Request)
        assert new is not None
        self.assertEqual(new.full_url, "https://x.test/b")

    def test_a_redirect_on_head_is_followed(self):
        new = self._redirect("HEAD")
        self.assertIsInstance(new, urllib.request.Request)

    def test_a_redirect_on_put_or_delete_is_not_followed(self):
        self.assertIsNone(self._redirect("PUT", b"x"))
        self.assertIsNone(self._redirect("DELETE"))

    def test_the_final_url_is_the_one_reported_on_the_response(self):
        # Dedupe and link resolution both key off the URL that actually served
        # the body; reporting the requested one would re-crawl the redirect.
        client = make_client(ok(b"moved", url="https://x.test/final"))
        self.assertEqual(client.get("https://x.test/start").url, "https://x.test/final")


# --------------------------------------------------------------- transport path


class TestTransportErrors(unittest.TestCase):
    def test_a_dns_failure_becomes_a_transport_error(self):
        client = make_client(urllib.error.URLError("Name or service not known"))
        with self.assertRaises(TransportError) as caught:
            client.get("https://nope.invalid/a")
        self.assertIn("nope.invalid", str(caught.exception))
        self.assertEqual(len(client._opener.requests), FAST.attempts)
        self.assertEqual(client.stats["retries"], FAST.attempts - 1)
        self.assertEqual(client.stats["errors"], 1)
        self.assertEqual(client.stats["requests"], 0)

    def test_a_timeout_becomes_a_transport_error(self):
        client = make_client(TimeoutError("timed out"))
        with self.assertRaises(TransportError):
            client.get("https://x.test/slow")

    def test_a_connection_reset_is_retried_and_can_succeed(self):
        # The common case on a flaky link: one reset, then the page.
        client = make_client(ConnectionResetError("reset by peer"), ok(b"second try"))
        self.assertEqual(client.get("https://x.test/a").body, b"second try")
        self.assertEqual(client.stats["retries"], 1)
        self.assertEqual(client.stats["requests"], 1)
        self.assertEqual(client.stats["errors"], 0)

    def test_a_client_with_no_attempts_left_still_raises_rather_than_returning_none(self):
        # A misconfigured policy must not hand the caller a None response.
        client = make_client(ok(b"unreachable"), retry=RetryPolicy(attempts=0))
        with self.assertRaises(TransportError):
            client.get("https://x.test/a")


class TestStatsCounters(unittest.TestCase):
    def test_a_successful_request_counts_once_with_its_bytes(self):
        client = make_client(ok(b"12345"))
        client.get("https://x.test/a")
        self.assertEqual(client.stats,
                         {"requests": 1, "retries": 0, "errors": 0, "not_modified": 0, "bytes": 5})

    def test_an_allowed_non_2xx_is_returned_as_a_response_and_counted(self):
        # Bug (fixed): an allowed status - a missing robots.txt, a 404 blob that
        # triggers the API fallback - was the one outcome that touched no
        # counter at all. It is not an error, and it was not counted as a
        # request either, so a crawl that fetched a thousand robots.txt files
        # reported zero traffic and its cost could not be read off the stats the
        # client publishes for exactly that purpose.
        client = make_client(http_error(404, {"Content-Type": "text/plain"}, b"not found"))
        resp = client.get("https://x.test/robots.txt", allow_status=(404,))
        self.assertEqual(resp.status, 404)
        self.assertEqual(resp.body, b"not found")
        self.assertEqual(client.stats["requests"], 1)
        self.assertEqual(client.stats["bytes"], len(b"not found"))
        self.assertEqual(client.stats["errors"], 0)

    def test_a_status_that_was_not_allowed_still_raises(self):
        client = make_client(http_error(410))
        with self.assertRaises(HttpError):
            client.get("https://x.test/a", allow_status=(404,))


class TestRequestShape(unittest.TestCase):
    def test_the_user_agent_and_default_headers_are_sent(self):
        client = make_client(ok(), user_agent="test-ua/1.0",
                             default_headers={"Authorization": "token xyz"})
        client.get("https://x.test/a")
        sent = client._opener.requests[0]
        self.assertEqual(sent.get_header("User-agent"), "test-ua/1.0")
        self.assertEqual(sent.get_header("Authorization"), "token xyz")
        self.assertEqual(sent.get_header("Accept-encoding"), "gzip, deflate")

    def test_a_per_call_header_overrides_a_default_header(self):
        client = make_client(ok(), default_headers={"Accept": "text/html"})
        client.get("https://x.test/a", headers={"Accept": "application/json"})
        self.assertEqual(client._opener.requests[0].get_header("Accept"), "application/json")

    def test_head_uses_the_head_method(self):
        client = make_client(ok(b""))
        client.head("https://x.test/a")
        self.assertEqual(client._opener.requests[0].get_method(), "HEAD")

    def test_get_json_asks_for_json_and_parses_it(self):
        client = make_client(ok(b'{"ok": true}', headers={"Content-Type": "application/json"}))
        self.assertEqual(client.get_json("https://x.test/a"), {"ok": True})
        self.assertEqual(client._opener.requests[0].get_header("Accept"), "application/json")


# --------------------------------------------------------------- url canonicals


class TestNormalizeUrl(unittest.TestCase):
    def test_tracking_parameters_are_stripped(self):
        # Without this every share link looks like a new page and the crawler
        # fetches the same document once per campaign parameter.
        self.assertEqual(
            normalize_url("https://x.test/p?utm_source=news&utm_medium=email&id=7&fbclid=zz"),
            "https://x.test/p?id=7")

    def test_a_query_of_only_tracking_parameters_becomes_no_query(self):
        self.assertEqual(normalize_url("https://x.test/p?utm_source=news"), "https://x.test/p")

    def test_query_parameters_are_sorted(self):
        self.assertEqual(normalize_url("https://x.test/p?b=2&a=1"), "https://x.test/p?a=1&b=2")

    def test_a_repeated_parameter_keeps_both_values(self):
        self.assertEqual(normalize_url("https://x.test/p?a=2&a=1"), "https://x.test/p?a=1&a=2")

    def test_a_blank_value_is_kept(self):
        # `?q=` and `?q=x` are different pages on plenty of search endpoints.
        self.assertEqual(normalize_url("https://x.test/p?q="), "https://x.test/p?q=")

    def test_default_ports_are_dropped(self):
        self.assertEqual(normalize_url("https://x.test:443/p"), "https://x.test/p")
        self.assertEqual(normalize_url("http://x.test:80/p"), "http://x.test/p")

    def test_a_non_default_port_is_kept(self):
        # Dropping it would merge two different services into one document.
        self.assertEqual(normalize_url("http://x.test:8080/p"), "http://x.test:8080/p")
        self.assertEqual(normalize_url("https://x.test:8443/p"), "https://x.test:8443/p")

    def test_scheme_and_host_are_lowercased_but_the_path_is_not(self):
        # Hosts are case-insensitive; paths are not, on every server that matters.
        self.assertEqual(normalize_url("HTTPS://X.Test/Path"), "https://x.test/Path")

    def test_the_fragment_is_dropped_unless_asked_for(self):
        self.assertEqual(normalize_url("https://x.test/p#section"), "https://x.test/p")
        self.assertEqual(normalize_url("https://x.test/p#s", drop_fragment=False),
                         "https://x.test/p#s")

    def test_index_html_collapses_to_the_directory(self):
        self.assertEqual(normalize_url("https://x.test/docs/index.html"), "https://x.test/docs/")

    def test_a_path_that_merely_ends_in_index_html_is_left_alone(self):
        # `/myindex.html` is a page, not a directory listing.
        self.assertEqual(normalize_url("https://x.test/myindex.html"),
                         "https://x.test/myindex.html")

    def test_an_empty_path_becomes_a_slash(self):
        self.assertEqual(normalize_url("https://x.test"), "https://x.test/")

    def test_percent_encoding_is_normalised(self):
        # The same page linked as `%7Euser` and `~user` must dedupe to one URL.
        self.assertEqual(normalize_url("https://x.test/%7Euser/a%20b"),
                         normalize_url("https://x.test/~user/a b"))
        self.assertEqual(normalize_url("https://x.test/a%20b"), "https://x.test/a%20b")

    def test_drop_query_removes_the_whole_query(self):
        self.assertEqual(normalize_url("https://x.test/p?a=1&b=2", drop_query=True),
                         "https://x.test/p")

    def test_surrounding_whitespace_is_ignored(self):
        # hrefs in real HTML are routinely written with a newline in them.
        self.assertEqual(normalize_url("  https://x.test/p\n"), "https://x.test/p")

    def test_a_schemeless_url_is_assumed_https(self):
        self.assertEqual(normalize_url("//x.test/p"), "https://x.test/p")

    def test_a_malformed_authority_raises_value_error(self):
        # Not a fix but a contract: `SplitResult.port` raises on `:80x` and on an
        # unclosed IPv6 literal, both of which occur in hand-written hrefs. The
        # crawler wraps this call (`crawler._safe_normalize`) to drop the link
        # and keep the frontier, so the exception must stay a ValueError rather
        # than become some other type that the wrapper does not catch.
        for bad in ("http://x.test:80x/", "http://x.test:99999/", "http://[unclosed/p"):
            with self.subTest(url=bad), self.assertRaises(ValueError):
                normalize_url(bad)

    def test_urljoin_resolves_a_relative_link(self):
        self.assertEqual(urljoin("https://x.test/docs/a.html", "../b.html"), "https://x.test/b.html")


class TestSameSite(unittest.TestCase):
    def test_the_same_host_is_the_same_site(self):
        self.assertTrue(same_site("https://x.test/a", "http://x.test/b"))

    def test_a_subdomain_counts_by_default(self):
        self.assertTrue(same_site("https://docs.x.test/a", "https://x.test/b"))
        self.assertTrue(same_site("https://x.test/a", "https://docs.x.test/b"))

    def test_a_subdomain_does_not_count_when_subdomains_are_excluded(self):
        self.assertFalse(same_site("https://docs.x.test/a", "https://x.test/b",
                                   include_subdomains=False))

    def test_a_host_that_merely_ends_in_the_other_is_a_different_site(self):
        # `notx.test` is somebody else's domain; suffix matching without the dot
        # would let a crawl scoped to one site wander onto it.
        self.assertFalse(same_site("https://notx.test/a", "https://x.test/b"))

    def test_case_is_ignored(self):
        self.assertTrue(same_site("https://X.Test/a", "https://x.test/b"))

    def test_a_url_without_a_host_is_never_the_same_site(self):
        # `mailto:` and `javascript:` hrefs reach this function from real pages.
        self.assertFalse(same_site("mailto:a@x.test", "https://x.test/b"))
        self.assertFalse(same_site("", "https://x.test/b"))


# ------------------------------------------------------------------- ratelimit


class TestTokenBucket(unittest.TestCase):
    def test_a_full_bucket_hands_out_its_burst_without_waiting(self):
        bucket = TokenBucket(rate_per_sec=50.0, burst=3)
        self.assertEqual([bucket.acquire() for _ in range(3)], [0.0, 0.0, 0.0])

    def test_an_empty_bucket_waits_for_the_refill(self):
        # The wait is asserted from the return value rather than from the wall
        # clock: a loaded CI box makes elapsed-time assertions flaky, and the
        # contract is "tell the caller how long it throttled you".
        bucket = TokenBucket(rate_per_sec=50.0, burst=2)
        bucket.acquire()
        bucket.acquire()
        waited = bucket.acquire()
        self.assertGreater(waited, 0.0)
        self.assertLess(waited, 0.5)

    def test_tokens_refill_over_time(self):
        bucket = TokenBucket(rate_per_sec=100.0, burst=1)
        bucket.acquire()
        time.sleep(0.05)  # 100/s for 50ms is five tokens' worth, capacity is one
        self.assertEqual(bucket.acquire(), 0.0)

    def test_a_fractional_rate_still_serves_the_first_request_immediately(self):
        # A one-request-per-hour connector must not stall on its first call.
        self.assertEqual(TokenBucket(rate_per_sec=0.001, burst=1).acquire(), 0.0)

    def test_asking_for_more_tokens_than_the_bucket_holds_returns(self):
        # Bug (fixed): refill is capped at `capacity`, so a request for more than
        # capacity could never be satisfied - acquire() slept, woke, found the
        # same deficit and slept again, for ever. The calling thread hung with no
        # error and no log line, which in a pipeline reads as "the run is slow".
        # A watchdog thread is used because a regression here does not fail this
        # test, it hangs the whole suite.
        bucket = TokenBucket(rate_per_sec=1000.0, burst=2)
        done = threading.Event()

        def take() -> None:
            bucket.acquire(5.0)
            done.set()

        worker = threading.Thread(target=take, daemon=True)
        worker.start()
        self.assertTrue(done.wait(timeout=5.0), "acquire() for more than capacity never returned")

    def test_a_zero_burst_bucket_does_not_hang(self):
        # Same failure, reached through configuration instead of a big request:
        # a bucket that can never hold one token can never hand one out.
        bucket = TokenBucket(rate_per_sec=1000.0, burst=0)
        done = threading.Event()
        threading.Thread(target=lambda: (bucket.acquire(), done.set()), daemon=True).start()
        self.assertTrue(done.wait(timeout=5.0), "a zero-burst bucket deadlocked")

    def test_a_bucket_is_safe_to_share_between_threads(self):
        # Connectors hand one bucket to several workers; the accounting has to
        # hold or the "polite" rate is silently exceeded.
        bucket = TokenBucket(rate_per_sec=10_000.0, burst=20)
        results: list[float] = []
        lock = threading.Lock()

        def take() -> None:
            waited = bucket.acquire()
            with lock:
                results.append(waited)

        threads = [threading.Thread(target=take) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
        self.assertEqual(len(results), 20)


# --------------------------------------------------------------------- hashing


class TestHashing(unittest.TestCase):
    def test_digests_are_identical_in_a_separate_process(self):
        # The docstring's stated reason for not using builtin hash(): ids have to
        # survive a restart, because incremental ingest decides "new vs changed
        # vs unchanged" by comparing today's hash with one stored yesterday. This
        # runs the same call under two hash seeds and shows builtin hash() moving
        # while these digests do not.
        src = pathlib.Path(hashing.__file__).resolve().parents[2]
        script = (
            "import sys; sys.path.insert(0, %r);"
            "from oodarag.util.hashing import sha256_hex, stable_id, content_hash, blake_bucket;"
            "print(sha256_hex('doc', 'v1'), stable_id('doc', 'v1'), content_hash('doc', 'v1'),"
            "      blake_bucket('token', 4096), hash('doc'))" % str(src)
        )
        out = []
        for seed in ("0", "12345"):
            env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"}
            proc = subprocess.run([sys.executable, "-c", script], capture_output=True,
                                  text=True, env=env, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out.append(proc.stdout.split())
        stable_here = [sha256_hex("doc", "v1"), stable_id("doc", "v1"),
                       content_hash("doc", "v1"), str(blake_bucket("token", 4096))]
        self.assertEqual(out[0][:4], stable_here)
        self.assertEqual(out[1][:4], stable_here)
        self.assertNotEqual(out[0][4], out[1][4],
                            "builtin hash() should differ per seed - that is why it is not used")

    def test_the_separator_keeps_neighbouring_parts_apart(self):
        # Without the unit separator ("ab", "c") and ("a", "bc") would collide,
        # and a chunk id built from (doc_id, offset) could name another chunk.
        self.assertNotEqual(sha256_hex("ab", "c"), sha256_hex("a", "bc"))

    def test_a_missing_part_is_not_the_same_as_an_empty_part(self):
        self.assertNotEqual(sha256_hex("a"), sha256_hex("a", ""))

    def test_the_short_ids_are_prefixes_of_the_full_digest(self):
        full = sha256_hex("doc", "1")
        self.assertEqual(content_hash("doc", "1"), full[:16])
        self.assertEqual(stable_id("doc", "1"), full[:24])
        self.assertTrue(all(c in "0123456789abcdef" for c in stable_id("doc", "1")))

    def test_surrogates_do_not_break_hashing(self):
        # Scraped text reaches this after a lossy decode; a UnicodeEncodeError
        # here would abort ingest over one bad byte in one page.
        self.assertEqual(len(sha256_hex("bad \ud800 text")), 64)

    def test_blake_bucket_stays_inside_the_range(self):
        buckets = 64
        seen = {blake_bucket(f"token-{i}", buckets) for i in range(500)}
        self.assertTrue(all(0 <= b < buckets for b in seen))
        self.assertGreater(len(seen), 32, "a hashing trick that uses half its buckets is broken")

    def test_blake_bucket_is_stable_and_salt_sensitive(self):
        self.assertEqual(blake_bucket("token", 128), blake_bucket("token", 128))
        salted = [blake_bucket(f"t{i}", 128, salt="s") != blake_bucket(f"t{i}", 128) for i in range(50)]
        self.assertTrue(any(salted), "the salt must change the mapping")

    def test_blake_sign_is_plus_or_minus_one_and_deterministic(self):
        signs = [blake_sign(f"token-{i}") for i in range(200)]
        self.assertEqual(set(signs), {1, -1}, "signs must occur both ways or they cannot cancel")
        self.assertEqual(blake_sign("token-1"), blake_sign("token-1"))


# --------------------------------------------------------------------- logging


def capture(fn) -> tuple[str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        fn()
    return out.getvalue(), err.getvalue()


class TestLogging(unittest.TestCase):
    def test_json_mode_emits_one_parseable_object_per_event(self):
        log = Logger("ingest", level="debug", json_mode=True)
        _, err = capture(lambda: (log.info("fetched", url="https://x.test/a", n=3),
                                  log.error("failed", err="timeout")))
        events = [json.loads(line) for line in err.splitlines() if line.strip()]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["level"], "info")
        self.assertEqual(events[0]["logger"], "ingest")
        self.assertEqual(events[0]["msg"], "fetched")
        self.assertEqual(events[0]["url"], "https://x.test/a")
        self.assertEqual(events[0]["n"], 3)
        self.assertIsInstance(events[0]["ts"], float)
        self.assertEqual(events[1]["level"], "error")

    def test_a_caller_field_cannot_overwrite_the_events_own_level(self):
        # Bug (fixed): fields were merged over the event, so a data key named
        # `level`, `msg`, `ts` or `logger` replaced the real one - and those
        # four are exactly what a log reader filters on. `log.error(...,
        # level="chunk")` produced an event that no `level=error` query found,
        # which is the one event you cannot afford to lose. Field dicts come
        # from **counts in the connectors, so the collision is not theoretical.
        log = Logger("ingest", json_mode=True)
        _, err = capture(lambda: log.error("failed", **{"level": "chunk", "msg": "other", "n": 1}))
        event = json.loads(err.strip())
        self.assertEqual(event["level"], "error")
        self.assertEqual(event["msg"], "failed")
        self.assertEqual(event["field_level"], "chunk")
        self.assertEqual(event["field_msg"], "other")
        self.assertEqual(event["n"], 1)

    def test_a_data_key_called_msg_is_logged_instead_of_raising(self):
        # Bug (fixed): `msg` was an ordinary named parameter, so a caller doing
        # `log.info("ingest done", **counts)` with a key named `msg` in the data
        # got "TypeError: got multiple values for argument 'msg'" - the run died
        # at the line whose only job was to report that the run had finished.
        # The same shape of collision has already cost this pipeline one release
        # (see the `repo=` regression noted in tests/test_oodarag_live.py).
        log = Logger("ingest", json_mode=True)
        _, err = capture(lambda: log.info("ingest done", **{"msg": "other", "n": 1}))
        event = json.loads(err.strip())
        self.assertEqual(event["msg"], "ingest done")
        self.assertEqual(event["field_msg"], "other")

    def test_a_value_that_is_not_json_serialisable_is_stringified(self):
        # Logging must never be the thing that fails a run.
        log = Logger("ingest", json_mode=True)
        _, err = capture(lambda: log.info("state", when=object()))
        self.assertIn("object object", json.loads(err.strip())["when"])

    def test_levels_below_the_threshold_are_dropped(self):
        log = Logger("ingest", level="warn", json_mode=True)
        _, err = capture(lambda: (log.debug("d"), log.info("i"), log.warn("w"), log.error("e")))
        levels = [json.loads(line)["level"] for line in err.splitlines() if line.strip()]
        self.assertEqual(levels, ["warn", "error"])

    def test_the_silent_level_drops_everything(self):
        log = Logger("ingest", level="silent", json_mode=True)
        _, err = capture(lambda: log.error("e"))
        self.assertEqual(err, "")

    def test_an_unknown_level_name_falls_back_to_info(self):
        # A typo in OODARAG_LOG_LEVEL must not silence the run.
        log = Logger("ingest", level="verbose", json_mode=True)
        _, err = capture(lambda: (log.debug("d"), log.info("i")))
        self.assertEqual([json.loads(l)["level"] for l in err.splitlines() if l.strip()], ["info"])

    def test_logs_go_to_stderr_so_stdout_stays_machine_readable(self):
        # Pipeline stages write their results to stdout; a log line in there
        # corrupts whatever is parsing it downstream.
        log = Logger("ingest", json_mode=True)
        out, err = capture(lambda: log.info("hello"))
        self.assertEqual(out, "")
        self.assertIn("hello", err)

    def test_human_mode_marks_the_level_and_keeps_the_fields(self):
        log = Logger("ingest", json_mode=False)
        out, err = capture(lambda: log.warn("retrying", url="https://x.test/a", attempt=2))
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("! [ingest] retrying"), err)
        self.assertIn("url=https://x.test/a", err)
        self.assertIn("attempt=2", err)

    def test_the_environment_configures_a_logger_from_get_logger(self):
        previous = {k: os.environ.get(k) for k in ("OODARAG_LOG_LEVEL", "OODARAG_LOG_FORMAT")}
        os.environ["OODARAG_LOG_LEVEL"] = "error"
        os.environ["OODARAG_LOG_FORMAT"] = "json"
        try:
            log = get_logger("cfg")
            _, err = capture(lambda: (log.warn("dropped"), log.error("kept")))
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        events = [json.loads(line) for line in err.splitlines() if line.strip()]
        self.assertEqual([e["msg"] for e in events], ["kept"])


if __name__ == "__main__":
    unittest.main()
