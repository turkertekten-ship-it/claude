"""Tests for the shared HTTP client.

Every test drives the client through the one seam it has to the network,
`HttpClient._opener`, so nothing here opens a socket. The fakes deliberately
mimic what urllib actually hands back - an `email.message.Message` for headers,
a real `urllib.error.HTTPError` for a non-2xx - because the bugs this module is
prone to (a header read with the wrong case, an error body read twice, a
connection never closed) only show up against the real shapes.
"""

from __future__ import annotations

import email.message
import email.utils
import gzip
import io
import time
import unittest
import urllib.error
import urllib.request
import zlib
from typing import Any
from unittest import mock

from oodarag.util.http import (
    ALLOWED_SCHEMES,
    HttpClient,
    HttpError,
    Response,
    RetryPolicy,
    TransportError,
    _decompress,
    _retry_after,
    _SafeRedirectHandler,
    canonical_host,
    normalize_url,
    redact_url,
    same_site,
    urljoin,
)

URL = "https://example.com/page"


def message(headers: dict[str, str]) -> email.message.Message:
    msg = email.message.Message()
    for key, value in headers.items():
        msg[key] = value
    return msg


class FakeHTTPResponse:
    """What `opener.open()` returns on a 2xx: a context manager over a body."""

    def __init__(
        self,
        status: int = 200,
        headers: dict[str, str] | None = None,
        body: bytes = b"",
        url: str = URL,
    ) -> None:
        self.status = status
        self.headers = message(headers or {})
        self._stream = io.BytesIO(body)
        self._url = url
        self.read_calls = 0
        self.exited = False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        return self._stream.read(size)

    def __enter__(self) -> FakeHTTPResponse:
        return self

    def __exit__(self, *exc: Any) -> bool:
        self.exited = True
        return False


class FakeOpener:
    """Serves one planned outcome per call, and refuses to invent extras."""

    def __init__(self, *plan: Any) -> None:
        self.plan = list(plan)
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float | None] = []

    def open(self, req: urllib.request.Request, timeout: float | None = None) -> Any:
        self.requests.append(req)
        self.timeouts.append(timeout)
        if not self.plan:
            raise AssertionError(f"unplanned request: {req.get_method()} {req.full_url}")
        outcome = self.plan.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class RecordingBucket:
    def __init__(self) -> None:
        self.acquired = 0

    def acquire(self, tokens: float = 1.0) -> float:
        self.acquired += 1
        return 0.0


def http_error(
    code: int,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
    url: str = URL,
) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url, code, f"status {code}", message(headers or {}), io.BytesIO(body)
    )


def header_of(req: urllib.request.Request, name: str) -> str | None:
    """urllib capitalizes header keys on the way in, so look them up loosely."""
    for key, value in req.header_items():
        if key.lower() == name.lower():
            return value
    return None


class HttpTestCase(unittest.TestCase):
    """Base: no test may sleep, whatever the retry policy computes."""

    def setUp(self) -> None:
        patcher = mock.patch("oodarag.util.http.time.sleep")
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)

    def client(self, *plan: Any, **kw: Any) -> HttpClient:
        kw.setdefault("retry", RetryPolicy(attempts=3, base_delay=0.0, max_delay=0.0, jitter=0.0))
        kw.setdefault("rate_per_sec", 1_000_000.0)
        client = HttpClient(**kw)
        client._opener = FakeOpener(*plan)
        return client

    @property
    def waits(self) -> list[float]:
        return [call.args[0] for call in self.sleep.call_args_list]


# --------------------------------------------------------------------- Response


class ResponseTestCase(unittest.TestCase):
    def test_text_uses_the_declared_charset(self) -> None:
        resp = Response(URL, 200, {"content-type": 'text/html; charset="latin-1"'},
                        "café".encode("latin-1"))
        self.assertEqual(resp.text, "café")

    def test_text_falls_back_to_utf8_for_an_unknown_charset(self) -> None:
        resp = Response(URL, 200, {"content-type": "text/html; charset=bogus-9"}, b"caf\xc3\xa9")
        self.assertEqual(resp.text, "café")

    def test_text_replaces_undecodable_bytes_rather_than_raising(self) -> None:
        resp = Response(URL, 200, {"content-type": "text/plain"}, b"a\xffb")
        self.assertEqual(resp.text, "a�b")

    def test_content_type_drops_parameters_and_case(self) -> None:
        resp = Response(URL, 200, {"content-type": "TEXT/HTML; charset=utf-8"}, b"")
        self.assertEqual(resp.content_type, "text/html")
        self.assertEqual(Response(URL, 200, {}, b"").content_type, "")

    def test_json_parses_the_body(self) -> None:
        resp = Response(URL, 200, {}, b'{"a": [1, 2]}')
        self.assertEqual(resp.json(), {"a": [1, 2]})

    def test_not_modified_separates_a_304_from_an_empty_200(self) -> None:
        self.assertTrue(Response(URL, 304, {}, b"", from_cache=True).not_modified)
        self.assertFalse(Response(URL, 200, {}, b"").not_modified)


class RetryPolicyTestCase(unittest.TestCase):
    def test_backoff_is_exponential_and_capped(self) -> None:
        policy = RetryPolicy(attempts=5, base_delay=1.0, max_delay=4.0, jitter=0.0)
        self.assertEqual([policy.delay_for(n) for n in (1, 2, 3, 4)], [1.0, 2.0, 4.0, 4.0])

    def test_retry_after_wins_but_is_still_capped(self) -> None:
        policy = RetryPolicy(base_delay=1.0, max_delay=5.0, jitter=0.0)
        self.assertEqual(policy.delay_for(1, retry_after=120.0), 5.0)
        self.assertEqual(policy.delay_for(1, retry_after=0.5), 0.5)

    def test_delay_is_never_negative(self) -> None:
        # A negative delay would make time.sleep raise instead of returning.
        self.assertEqual(RetryPolicy(max_delay=5.0).delay_for(1, retry_after=-30.0), 0.0)
        wild = RetryPolicy(base_delay=1.0, max_delay=5.0, jitter=3.0)
        self.assertTrue(all(wild.delay_for(1) >= 0.0 for _ in range(200)))

    def test_attempt_zero_does_not_invert_the_exponent(self) -> None:
        self.assertEqual(RetryPolicy(base_delay=2.0, jitter=0.0).delay_for(0), 2.0)


# ------------------------------------------------------------------ happy paths


class RequestTestCase(HttpTestCase):
    def test_plain_200(self) -> None:
        raw = FakeHTTPResponse(
            200, {"Content-Type": "text/html; charset=utf-8", "Content-Length": "5"}, b"hello"
        )
        client = self.client(raw)

        resp = client.get(URL)

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, b"hello")
        self.assertEqual(resp.url, URL)
        self.assertEqual(resp.headers["content-type"], "text/html; charset=utf-8")
        self.assertFalse(resp.from_cache)
        self.assertGreaterEqual(resp.elapsed_s, 0.0)
        self.assertTrue(raw.exited)
        self.assertEqual(client.stats, {"requests": 1, "retries": 0, "errors": 0,
                                        "not_modified": 0, "bytes": 5})

    def test_request_carries_headers_timeout_and_method(self) -> None:
        client = self.client(FakeHTTPResponse(), default_headers={"X-Default": "d"}, timeout=7.5)

        client.request("POST", URL, headers={"X-Call": "c"}, body=b"payload")

        req = client._opener.requests[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.data, b"payload")
        self.assertEqual(client._opener.timeouts, [7.5])
        self.assertEqual(header_of(req, "user-agent"), client.user_agent)
        self.assertEqual(header_of(req, "accept-encoding"), "gzip, deflate")
        self.assertEqual(header_of(req, "x-default"), "d")
        self.assertEqual(header_of(req, "x-call"), "c")

    def test_explicit_headers_win_over_defaults(self) -> None:
        client = self.client(FakeHTTPResponse(), default_headers={"Accept": "text/plain"})
        client.get(URL, headers={"Accept": "application/json"})
        self.assertEqual(header_of(client._opener.requests[0], "accept"), "application/json")

    def test_gzip_body_is_decompressed(self) -> None:
        payload = gzip.compress(b"hello gzip")
        client = self.client(FakeHTTPResponse(200, {"Content-Encoding": "gzip"}, payload))

        resp = client.get(URL)

        self.assertEqual(resp.body, b"hello gzip")
        self.assertEqual(client.stats["bytes"], len(b"hello gzip"))

    def test_get_json_decodes_and_sets_accept(self) -> None:
        client = self.client(FakeHTTPResponse(200, {}, b'{"ok": true}'))

        self.assertEqual(client.get_json(URL, headers=None), {"ok": True})
        self.assertEqual(header_of(client._opener.requests[0], "accept"), "application/json")

    def test_head_returns_headers_for_a_body_far_over_the_cap(self) -> None:
        # A HEAD advertises the length of the body it is not sending; refusing it
        # would break the one request whose whole job is to ask "how big is it?".
        client = self.client(
            FakeHTTPResponse(200, {"Content-Length": str(50 * 1024 * 1024)}, b""),
            max_bytes=1024,
        )

        resp = client.head(URL)

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, b"")


class ConditionalGetTestCase(HttpTestCase):
    def test_etag_is_stored_then_replayed_as_if_none_match(self) -> None:
        client = self.client(
            FakeHTTPResponse(200, {"ETag": 'W/"v1"'}, b"body"),
            FakeHTTPResponse(200, {"ETag": 'W/"v1"'}, b"body"),
        )

        client.get(URL)
        self.assertIsNone(header_of(client._opener.requests[0], "if-none-match"))

        client.get(URL, conditional=True)
        self.assertEqual(header_of(client._opener.requests[1], "if-none-match"), 'W/"v1"')

    def test_conditional_without_a_stored_etag_sends_nothing(self) -> None:
        client = self.client(FakeHTTPResponse(200, {}, b"body"))
        client.get(URL, conditional=True)
        self.assertIsNone(header_of(client._opener.requests[0], "if-none-match"))

    def test_304_is_a_response_the_caller_can_tell_from_an_empty_200(self) -> None:
        client = self.client(http_error(304, headers={"ETag": 'W/"v1"'}))

        resp = client.get(URL, conditional=True)

        self.assertEqual(resp.status, 304)
        self.assertTrue(resp.from_cache)
        self.assertTrue(resp.not_modified)
        self.assertEqual(resp.body, b"")
        self.assertEqual(resp.headers["etag"], 'W/"v1"')
        self.assertEqual(client.stats["not_modified"], 1)
        self.assertEqual(client.stats["errors"], 0)
        self.assertEqual(client.stats["requests"], 1)
        self.assertEqual(self.waits, [])

    def test_empty_200_is_not_marked_from_cache(self) -> None:
        client = self.client(FakeHTTPResponse(200, {}, b""))
        resp = client.get(URL, conditional=True)

        self.assertEqual(resp.status, 200)
        self.assertFalse(resp.from_cache)
        self.assertFalse(resp.not_modified)
        self.assertEqual(client.stats["not_modified"], 0)

    def test_etag_cache_is_bounded_and_evicts_oldest_first(self) -> None:
        plan = [FakeHTTPResponse(200, {"ETag": f'"{i}"'}, b"x") for i in range(4)]
        client = self.client(*plan, max_etags=2)

        for i in range(4):
            client.get(f"https://example.com/{i}")

        self.assertEqual(len(client._etags), 2)
        self.assertEqual(
            list(client._etags),
            ["https://example.com/2", "https://example.com/3"],
        )

    def test_refreshing_a_known_url_does_not_evict(self) -> None:
        client = self.client(*[FakeHTTPResponse(200, {"ETag": '"v"'}, b"x") for _ in range(3)],
                             max_etags=2)

        client.get("https://example.com/a")
        client.get("https://example.com/b")
        client.get("https://example.com/a")

        self.assertEqual(sorted(client._etags), ["https://example.com/a", "https://example.com/b"])


# ------------------------------------------------------------- status handling


class StatusHandlingTestCase(HttpTestCase):
    def test_each_allowed_status_passes_through_as_a_response(self) -> None:
        for code in (401, 403, 404, 410, 425):
            with self.subTest(code=code):
                client = self.client(http_error(code, b"nope", {"Content-Type": "text/plain"}))

                resp = client.get(URL, allow_status=(401, 403, 404, 410, 425))

                self.assertEqual(resp.status, code)
                self.assertEqual(resp.body, b"nope")
                self.assertEqual(resp.content_type, "text/plain")
                self.assertFalse(resp.from_cache)
                self.assertEqual(client.stats["errors"], 0)
                self.assertEqual(client.stats["requests"], 1)
                self.assertEqual(self.waits, [])

    def test_an_allowed_status_is_not_retried_even_when_retryable(self) -> None:
        client = self.client(http_error(429, b"slow down"))

        resp = client.get(URL, allow_status=(429,))

        self.assertEqual(resp.status, 429)
        self.assertEqual(len(client._opener.requests), 1)

    def test_allowed_status_body_is_decompressed(self) -> None:
        client = self.client(
            http_error(404, gzip.compress(b"missing"), {"Content-Encoding": "gzip"})
        )
        self.assertEqual(client.get(URL, allow_status=(404,)).body, b"missing")

    def test_a_bomb_in_an_allowed_error_body_yields_an_empty_body_not_a_raise(self) -> None:
        bomb = gzip.compress(b"\x00" * 200_000)
        client = self.client(http_error(404, bomb, {"Content-Encoding": "gzip"}), max_bytes=4096)

        resp = client.get(URL, allow_status=(404,))

        self.assertEqual(resp.status, 404)  # the status is what the caller needs
        self.assertEqual(resp.body, b"")

    def test_non_retryable_status_raises_at_once(self) -> None:
        client = self.client(http_error(404, b"gone for good"))

        with self.assertRaises(HttpError) as caught:
            client.get(URL)

        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(caught.exception.body, "gone for good")
        self.assertIn("404", str(caught.exception))
        self.assertEqual(len(client._opener.requests), 1)  # no retry
        self.assertEqual(self.waits, [])
        self.assertEqual(client.stats["errors"], 1)
        self.assertEqual(client.stats["retries"], 0)
        self.assertEqual(client.stats["requests"], 1)

    def test_retryable_status_retries_then_succeeds(self) -> None:
        client = self.client(
            http_error(503, b"nope"),
            http_error(503, b"nope"),
            FakeHTTPResponse(200, {}, b"finally"),
        )

        resp = client.get(URL)

        self.assertEqual(resp.body, b"finally")
        self.assertEqual(len(client._opener.requests), 3)
        self.assertEqual(client.stats["retries"], 2)
        self.assertEqual(client.stats["requests"], 3)
        self.assertEqual(client.stats["errors"], 0)
        self.assertEqual(len(self.waits), 2)

    def test_retryable_status_exhausts_attempts_and_raises_the_last_status(self) -> None:
        client = self.client(*[http_error(500, b"boom") for _ in range(3)])

        with self.assertRaises(HttpError) as caught:
            client.get(URL)

        self.assertEqual(caught.exception.status, 500)
        self.assertEqual(len(client._opener.requests), 3)
        self.assertEqual(client.stats["retries"], 2)  # 3 attempts, 2 of them retries
        self.assertEqual(client.stats["requests"], 3)
        self.assertEqual(client.stats["errors"], 1)  # one failed call, not one per attempt

    def test_retryable_classification(self) -> None:
        retryable = [408, 425, 429, 500, 502, 503, 504, 599]
        not_retryable = [200, 301, 304, 400, 401, 403, 404, 410, 418, 451]
        for code in retryable:
            self.assertTrue(HttpError(code, URL).retryable, code)
        for code in not_retryable:
            self.assertFalse(HttpError(code, URL).retryable, code)

    def test_a_policy_with_no_attempts_still_makes_one(self) -> None:
        client = self.client(FakeHTTPResponse(200, {}, b"ok"),
                             retry=RetryPolicy(attempts=0, base_delay=0.0, jitter=0.0))

        self.assertEqual(client.get(URL).body, b"ok")

    def test_no_attempts_and_a_failure_reports_the_real_error(self) -> None:
        client = self.client(http_error(404, b"x"),
                             retry=RetryPolicy(attempts=0, base_delay=0.0, jitter=0.0))

        with self.assertRaises(HttpError) as caught:
            client.get(URL)
        self.assertEqual(caught.exception.status, 404)

    def test_an_error_response_without_a_readable_body_still_classifies(self) -> None:
        broken = urllib.error.HTTPError(URL, 404, "gone", message({}), None)
        client = self.client(broken)

        with self.assertRaises(HttpError) as caught:
            client.get(URL)
        self.assertEqual(caught.exception.status, 404)


class TransportErrorTestCase(HttpTestCase):
    def test_transport_error_retries_then_succeeds(self) -> None:
        client = self.client(
            urllib.error.URLError("connection reset"),
            FakeHTTPResponse(200, {}, b"second time lucky"),
        )

        self.assertEqual(client.get(URL).body, b"second time lucky")
        self.assertEqual(client.stats["retries"], 1)
        self.assertEqual(client.stats["errors"], 0)

    def test_transport_error_exhausts_attempts(self) -> None:
        client = self.client(*[urllib.error.URLError("dns") for _ in range(3)])

        with self.assertRaises(TransportError) as caught:
            client.get(URL)

        self.assertIn("URLError", str(caught.exception))
        self.assertIsInstance(caught.exception.__cause__, urllib.error.URLError)
        self.assertEqual(len(client._opener.requests), 3)
        self.assertEqual(client.stats["errors"], 1)
        self.assertEqual(client.stats["retries"], 2)

    def test_timeouts_and_socket_errors_are_transport_errors(self) -> None:
        for exc in (TimeoutError("timed out"), OSError("broken pipe"),
                    urllib.error.URLError("tls")):
            with self.subTest(exc=type(exc).__name__):
                client = self.client(exc, retry=RetryPolicy(attempts=1, base_delay=0.0))
                with self.assertRaises(TransportError):
                    client.get(URL)

    def test_credentials_in_the_url_never_reach_the_error_or_the_log(self) -> None:
        secret = "https://user:s3cr3t@example.com/private"
        client = self.client(http_error(404, b"nope"), http_error(500, b"boom"),
                             retry=RetryPolicy(attempts=1, base_delay=0.0))

        with self.assertRaises(HttpError) as caught:
            client.get(secret)
        self.assertNotIn("s3cr3t", str(caught.exception))
        self.assertNotIn("s3cr3t", caught.exception.url)

        client._opener.plan = [urllib.error.URLError("dns")]
        with self.assertRaises(TransportError) as transport:
            client.get(secret)
        self.assertNotIn("s3cr3t", str(transport.exception))


# --------------------------------------------------------------------- the cap


class SizeCapTestCase(HttpTestCase):
    def test_declared_length_over_the_cap_is_refused_before_reading(self) -> None:
        raw = FakeHTTPResponse(200, {"Content-Length": "9999"}, b"x" * 9999)
        client = self.client(raw, max_bytes=1024)

        with self.assertRaises(TransportError) as caught:
            client.get(URL)

        self.assertIn("too large", str(caught.exception))
        self.assertEqual(raw.read_calls, 0)
        self.assertEqual(client.stats["errors"], 1)

    def test_undeclared_length_over_the_cap_trips_on_the_read(self) -> None:
        # Content-Length is a claim; a chunked response makes no claim at all.
        client = self.client(FakeHTTPResponse(200, {}, b"x" * 5000), max_bytes=1024)

        with self.assertRaises(TransportError) as caught:
            client.get(URL)
        self.assertIn("exceeded cap", str(caught.exception))

    def test_a_lying_content_length_does_not_get_a_free_pass(self) -> None:
        client = self.client(FakeHTTPResponse(200, {"Content-Length": "10"}, b"x" * 5000),
                             max_bytes=1024)

        with self.assertRaises(TransportError):
            client.get(URL)

    def test_exactly_at_the_cap_is_allowed(self) -> None:
        body = b"x" * 1024
        client = self.client(FakeHTTPResponse(200, {"Content-Length": "1024"}, body),
                             max_bytes=1024)

        self.assertEqual(client.get(URL).body, body)

    def test_one_byte_over_the_cap_is_not(self) -> None:
        client = self.client(FakeHTTPResponse(200, {"Content-Length": "1025"}, b"x" * 1025),
                             max_bytes=1024)

        with self.assertRaises(TransportError):
            client.get(URL)

    def test_a_hostile_content_length_is_ignored_not_fatal(self) -> None:
        for declared in ("²", "  ", "1,1", "10 bytes"):
            with self.subTest(declared=declared):
                client = self.client(
                    FakeHTTPResponse(200, {"Content-Length": declared}, b"body"), max_bytes=1024
                )
                self.assertEqual(client.get(URL).body, b"body")

    def test_the_cap_is_applied_after_decompression_too(self) -> None:
        # 200 KB of zeroes compresses to a few hundred bytes: a body that passes
        # every wire-side check and then owns the process's memory.
        bomb = gzip.compress(b"\x00" * 200_000)
        self.assertLess(len(bomb), 4096)
        client = self.client(FakeHTTPResponse(
            200, {"Content-Encoding": "gzip", "Content-Length": str(len(bomb))}, bomb
        ), max_bytes=4096)

        with self.assertRaises(TransportError) as caught:
            client.get(URL)

        self.assertIn("decompressed", str(caught.exception))
        self.assertEqual(client.stats["errors"], 1)

    def test_a_cap_failure_is_not_retried(self) -> None:
        client = self.client(FakeHTTPResponse(200, {}, b"x" * 5000), max_bytes=16)

        with self.assertRaises(TransportError):
            client.get(URL)
        self.assertEqual(len(client._opener.requests), 1)
        self.assertEqual(self.waits, [])


class DecompressTestCase(unittest.TestCase):
    def test_gzip_and_both_flavours_of_deflate(self) -> None:
        raw = b"the same bytes either way"
        self.assertEqual(_decompress(gzip.compress(raw), "gzip"), raw)
        self.assertEqual(_decompress(zlib.compress(raw), "deflate"), raw)

        compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        headerless = compressor.compress(raw) + compressor.flush()
        self.assertEqual(_decompress(headerless, "deflate"), raw)

    def test_identity_and_unknown_codings_pass_through(self) -> None:
        for coding in ("", "  ", "identity", "br", "zstd", "identity, identity"):
            with self.subTest(coding=coding):
                self.assertEqual(_decompress(b"plain bytes", coding), b"plain bytes")

    def test_coding_names_are_case_and_alias_tolerant(self) -> None:
        self.assertEqual(_decompress(gzip.compress(b"hi"), " GZIP "), b"hi")
        self.assertEqual(_decompress(gzip.compress(b"hi"), "x-gzip"), b"hi")

    def test_a_body_that_is_not_compressed_at_all_survives_the_lie(self) -> None:
        self.assertEqual(_decompress(b"totally plain", "gzip"), b"totally plain")
        self.assertEqual(_decompress(b"totally plain", "deflate"), b"totally plain")

    def test_a_truncated_gzip_body_degrades_instead_of_raising(self) -> None:
        # gzip.decompress raises EOFError here, which used to escape the client.
        truncated = gzip.compress(b"a useful prefix, then nothing" * 40)[:-20]
        out = _decompress(truncated, "gzip")
        self.assertIn(b"a useful prefix", out)

    def test_an_empty_body_is_not_an_error(self) -> None:
        self.assertEqual(_decompress(b"", "gzip"), b"")

    def test_a_bomb_raises_rather_than_allocating(self) -> None:
        with self.assertRaises(TransportError):
            _decompress(gzip.compress(b"\x00" * 100_000), "gzip", max_bytes=1000)

    def test_output_exactly_at_the_cap_is_allowed(self) -> None:
        self.assertEqual(len(_decompress(gzip.compress(b"\x00" * 1000), "gzip", max_bytes=1000)),
                         1000)
        with self.assertRaises(TransportError):
            _decompress(gzip.compress(b"\x00" * 1001), "gzip", max_bytes=1000)


# ---------------------------------------------------------- politeness plumbing


class RateLimitTestCase(HttpTestCase):
    def test_every_attempt_takes_a_token(self) -> None:
        client = self.client(
            http_error(503, b"x"),
            FakeHTTPResponse(200, {}, b"ok"),
        )
        bucket = RecordingBucket()
        client._bucket = bucket

        client.get(URL)

        self.assertEqual(bucket.acquired, 2)  # the retry is a request too

    def test_the_bucket_is_configured_from_the_client(self) -> None:
        client = HttpClient(rate_per_sec=3.0, burst=7)
        self.assertEqual(client._bucket.rate, 3.0)
        self.assertEqual(client._bucket.capacity, 7.0)


class RetryAfterTestCase(unittest.TestCase):
    def test_delta_seconds(self) -> None:
        self.assertEqual(_retry_after({"retry-after": "12"}), 12.0)
        self.assertEqual(_retry_after({"retry-after": " 12 "}), 12.0)

    def test_http_date(self) -> None:
        future = email.utils.formatdate(time.time() + 45, usegmt=True)
        delay = _retry_after({"retry-after": future})
        self.assertIsNotNone(delay)
        self.assertGreater(delay, 30.0)
        self.assertLess(delay, 60.0)

    def test_an_http_date_in_the_past_means_now_not_a_negative_delay(self) -> None:
        past = email.utils.formatdate(time.time() - 600, usegmt=True)
        self.assertEqual(_retry_after({"retry-after": past}), 0.0)

    def test_an_absurd_delay_is_clamped(self) -> None:
        self.assertEqual(_retry_after({"retry-after": "99999999"}), 3600.0)

    def test_garbage_and_absent_headers_yield_none(self) -> None:
        self.assertIsNone(_retry_after({}))
        self.assertIsNone(_retry_after({"retry-after": "soon"}))
        self.assertIsNone(_retry_after({"retry-after": ""}))
        self.assertIsNone(_retry_after({"retry-after": "²"}))

    def test_github_rate_limit_reset(self) -> None:
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) + 30)}
        delay = _retry_after(headers)
        self.assertGreater(delay, 25.0)
        self.assertLess(delay, 40.0)

    def test_rate_limit_reset_is_ignored_while_quota_remains(self) -> None:
        headers = {"x-ratelimit-remaining": "7", "x-ratelimit-reset": str(int(time.time()) + 30)}
        self.assertIsNone(_retry_after(headers))

    def test_a_reset_already_past_is_not_negative(self) -> None:
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) - 500)}
        self.assertEqual(_retry_after(headers), 0.0)

    def test_an_unparseable_reset_is_ignored(self) -> None:
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "never"}
        self.assertIsNone(_retry_after(headers))

    def test_retry_after_is_honoured_by_the_retry_loop(self) -> None:
        with mock.patch("oodarag.util.http.time.sleep") as sleep:
            client = HttpClient(
                rate_per_sec=1_000_000.0,
                retry=RetryPolicy(attempts=2, base_delay=30.0, max_delay=60.0, jitter=0.0),
            )
            client._opener = FakeOpener(
                http_error(429, b"slow", {"Retry-After": "3"}),
                FakeHTTPResponse(200, {}, b"ok"),
            )
            client.get(URL)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [3.0])


# -------------------------------------------------------------- transport gates


class SchemeGateTestCase(HttpTestCase):
    def test_non_http_schemes_are_refused_without_a_request(self) -> None:
        for url in ("file:///etc/passwd", "ftp://example.com/x", "data:text/plain,hi",
                    "gopher://example.com", "/relative/path"):
            with self.subTest(url=url):
                client = self.client()  # an empty plan: any open() call is a failure
                with self.assertRaises(TransportError) as caught:
                    client.get(url)
                self.assertIn("scheme", str(caught.exception))
                self.assertEqual(client._opener.requests, [])
                self.assertEqual(client.stats["errors"], 1)

    def test_an_unparseable_url_is_a_transport_error_not_a_valueerror(self) -> None:
        client = self.client()
        with self.assertRaises(TransportError):
            client.get("http://[::1")

    def test_the_real_opener_cannot_read_local_files(self) -> None:
        # build_opener() would have installed File/FTP/Data handlers here, and
        # this call would have returned the contents of the file.
        opener = HttpClient()._opener
        for url in ("file:///etc/hostname", "data:text/plain,hi"):
            with self.subTest(url=url), self.assertRaises(urllib.error.URLError) as caught:
                opener.open(urllib.request.Request(url))
            self.assertIn("unknown url type", str(caught.exception))

        installed = {type(h).__name__ for h in opener.handlers}
        self.assertNotIn("FileHandler", installed)
        self.assertNotIn("FTPHandler", installed)
        self.assertNotIn("DataHandler", installed)
        self.assertIn("HTTPSHandler", installed)
        self.assertIn("_SafeRedirectHandler", installed)
        self.assertEqual(ALLOWED_SCHEMES, {"http", "https"})


class RedirectHandlerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = _SafeRedirectHandler()

    def redirect(self, req: urllib.request.Request, newurl: str,
                 code: int = 302) -> urllib.request.Request | None:
        return self.handler.redirect_request(
            req, io.BytesIO(b""), code, "Found", message({"Location": newurl}), newurl
        )

    def test_a_get_is_followed(self) -> None:
        req = urllib.request.Request("https://example.com/a", method="GET")
        new = self.redirect(req, "https://example.com/b")

        self.assertIsNotNone(new)
        self.assertEqual(new.full_url, "https://example.com/b")

    def test_a_post_is_never_replayed(self) -> None:
        req = urllib.request.Request("https://example.com/a", data=b"x", method="POST")
        self.assertIsNone(self.redirect(req, "https://example.com/b"))

    def test_a_redirect_out_of_http_is_refused(self) -> None:
        req = urllib.request.Request("https://example.com/a", method="GET")
        for target in ("file:///etc/passwd", "ftp://example.com/x", "data:text/html,hi"):
            with self.subTest(target=target):
                self.assertIsNone(self.redirect(req, target))

    def test_credentials_are_dropped_when_the_host_changes(self) -> None:
        req = urllib.request.Request(
            "https://api.github.com/repos",
            headers={"Authorization": "Bearer ghp_secret", "Cookie": "s=1", "Accept": "text/*"},
            method="GET",
        )

        new = self.redirect(req, "https://codeload.example.net/repos")

        self.assertIsNotNone(new)
        names = {k.lower() for k in new.headers}
        self.assertNotIn("authorization", names)
        self.assertNotIn("cookie", names)
        self.assertIn("accept", names)

    def test_credentials_survive_a_same_host_redirect(self) -> None:
        req = urllib.request.Request(
            "https://api.github.com/a",
            headers={"Authorization": "Bearer ghp_secret"},
            method="GET",
        )

        new = self.redirect(req, "https://API.github.com./b")

        self.assertIsNotNone(new)
        self.assertIn("authorization", {k.lower() for k in new.headers})

    def test_the_chain_is_still_capped(self) -> None:
        # The cap lives in the inherited http_error_302, so overriding
        # redirect_request must not cost us the loop protection.
        req = urllib.request.Request("https://example.com/0", method="GET")
        req.redirect_dict = {f"https://example.com/{i}": 1 for i in range(20)}

        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.handler.http_error_302(
                req, io.BytesIO(b""), 302, "Found",
                message({"Location": "https://example.com/21"}),
            )
        self.assertIn("infinite loop", str(caught.exception))

    def test_a_blocked_redirect_is_handed_on_and_becomes_an_http_error(self) -> None:
        # http_error_302 declining (returning None) passes the 3xx down the
        # handler chain to HTTPDefaultErrorHandler, which raises: the caller sees
        # the status rather than a silent None or a replayed POST.
        req = urllib.request.Request("https://example.com/a", data=b"x", method="POST")
        headers = message({"Location": "https://example.com/b"})

        declined = self.handler.http_error_302(req, io.BytesIO(b""), 302, "Found", headers)
        self.assertIsNone(declined)

        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.HTTPDefaultErrorHandler().http_error_default(
                req, io.BytesIO(b""), 302, "Found", headers
            )
        self.assertEqual(caught.exception.code, 302)


# ----------------------------------------------------------------- URL helpers


class NormalizeUrlTestCase(unittest.TestCase):
    def test_scheme_and_host_are_lowercased(self) -> None:
        self.assertEqual(normalize_url("HTTPS://Example.COM/Path"), "https://example.com/Path")

    def test_default_ports_are_dropped_and_others_kept(self) -> None:
        self.assertEqual(normalize_url("http://example.com:80/a"), "http://example.com/a")
        self.assertEqual(normalize_url("https://example.com:443/a"), "https://example.com/a")
        self.assertEqual(normalize_url("https://example.com:8443/a"), "https://example.com:8443/a")
        self.assertEqual(normalize_url("http://example.com:443/a"), "http://example.com:443/a")

    def test_userinfo_is_dropped(self) -> None:
        self.assertEqual(normalize_url("https://user:pw@example.com/a"), "https://example.com/a")

    def test_trailing_dot_hosts_collapse(self) -> None:
        self.assertEqual(normalize_url("https://example.com./a"), "https://example.com/a")

    def test_idn_hosts_become_punycode(self) -> None:
        self.assertEqual(normalize_url("https://Bücher.de/a"), "https://xn--bcher-kva.de/a")
        self.assertEqual(normalize_url("https://xn--bcher-kva.de/a"), "https://xn--bcher-kva.de/a")

    def test_ipv6_hosts_keep_their_brackets(self) -> None:
        self.assertEqual(normalize_url("http://[::1]:8080/a"), "http://[::1]:8080/a")
        self.assertEqual(normalize_url("http://[::1]/a"), "http://[::1]/a")

    def test_encoded_slashes_are_not_decoded_into_real_ones(self) -> None:
        # /a%2Fb and /a/b are different resources; conflating them merges two
        # pages and lets a link escape the path prefix a crawl was scoped to.
        self.assertEqual(normalize_url("https://example.com/a%2Fb"), "https://example.com/a%2Fb")
        self.assertEqual(normalize_url("https://example.com/a%2fb"), "https://example.com/a%2Fb")
        self.assertEqual(normalize_url("https://example.com/a%2E%2E%2Fb"),
                         "https://example.com/a..%2Fb")

    def test_redundant_escapes_are_folded(self) -> None:
        self.assertEqual(normalize_url("https://example.com/%41%7Eb"), "https://example.com/A~b")

    def test_unsafe_characters_are_escaped_consistently(self) -> None:
        self.assertEqual(normalize_url("https://example.com/a b"), "https://example.com/a%20b")
        self.assertEqual(normalize_url("https://example.com/café"), "https://example.com/caf%C3%A9")
        self.assertEqual(normalize_url("https://example.com/caf%c3%a9"),
                         "https://example.com/caf%C3%A9")
        self.assertEqual(normalize_url("https://example.com/100%"), "https://example.com/100%25")

    def test_empty_path_becomes_root_and_index_html_is_folded(self) -> None:
        self.assertEqual(normalize_url("https://example.com"), "https://example.com/")
        self.assertEqual(normalize_url("https://example.com/docs/index.html"),
                         "https://example.com/docs/")

    def test_fragments_go_unless_asked_to_stay(self) -> None:
        self.assertEqual(normalize_url("https://example.com/a#frag"), "https://example.com/a")
        self.assertEqual(normalize_url("https://example.com/a#frag", drop_fragment=False),
                         "https://example.com/a#frag")

    def test_query_is_sorted_and_tracking_params_are_stripped(self) -> None:
        self.assertEqual(
            normalize_url("https://example.com/a?b=2&a=1&utm_source=x&UTM_MEDIUM=y"),
            "https://example.com/a?a=1&b=2",
        )
        self.assertEqual(normalize_url("https://example.com/a?b=2&a=1", drop_query=True),
                         "https://example.com/a")
        self.assertEqual(normalize_url("https://example.com/a?utm_source=x"),
                         "https://example.com/a")

    def test_two_spellings_of_one_url_normalize_to_one_key(self) -> None:
        spellings = [
            "HTTP://User@Example.com.:80/a/../b/index.html?utm_source=n&z=1#top",
            "http://example.com/a/../b/index.html?z=1",
        ]
        self.assertEqual(len({normalize_url(u) for u in spellings}), 1)

    def test_whitespace_is_stripped(self) -> None:
        self.assertEqual(normalize_url("  https://example.com/a\n"), "https://example.com/a")

    def test_malformed_urls_come_back_unchanged_rather_than_invented(self) -> None:
        for url in ("http://[::1", "https://example.com:notaport/a", "http://example.com:99999/a",
                    "mailto:someone@example.com", "javascript:alert(1)", "", "   ",
                    "/just/a/path"):
            with self.subTest(url=url):
                self.assertEqual(normalize_url(url), url.strip())

    def test_protocol_relative_urls_get_https(self) -> None:
        self.assertEqual(normalize_url("//example.com/a"), "https://example.com/a")


class SameSiteTestCase(unittest.TestCase):
    def test_exact_and_subdomain_matches(self) -> None:
        self.assertTrue(same_site("https://example.com/a", "https://example.com/b"))
        self.assertTrue(same_site("https://docs.example.com/a", "https://example.com/"))
        self.assertTrue(same_site("https://example.com/", "https://docs.example.com/a"))

    def test_subdomains_can_be_excluded(self) -> None:
        self.assertFalse(same_site("https://docs.example.com/a", "https://example.com/",
                                   include_subdomains=False))
        self.assertTrue(same_site("https://example.com/a", "https://example.com/b",
                                  include_subdomains=False))

    def test_a_suffix_that_is_not_a_subdomain_is_off_site(self) -> None:
        # The classic scope escape: notexample.com endswith example.com.
        self.assertFalse(same_site("https://notexample.com/a", "https://example.com/"))
        self.assertFalse(same_site("https://example.com.evil.test/a", "https://example.com/"))
        self.assertFalse(same_site("https://a.co.uk/", "https://b.co.uk/"))

    def test_case_ports_and_trailing_dots_do_not_matter(self) -> None:
        self.assertTrue(same_site("https://EXAMPLE.com:8443/a", "http://example.com./b"))

    def test_idn_and_punycode_are_the_same_site(self) -> None:
        self.assertTrue(same_site("https://Bücher.de/a", "https://xn--bcher-kva.de/b"))

    def test_unparseable_or_hostless_urls_fail_closed(self) -> None:
        self.assertFalse(same_site("http://[::1", "https://example.com/"))
        self.assertFalse(same_site("", "https://example.com/"))
        self.assertFalse(same_site("/relative", "https://example.com/"))
        self.assertFalse(same_site("https://example.com/", ""))


class HostAndUrlHelperTestCase(unittest.TestCase):
    def test_canonical_host(self) -> None:
        self.assertEqual(canonical_host("EXAMPLE.com."), "example.com")
        self.assertEqual(canonical_host("Bücher.de"), "xn--bcher-kva.de")
        self.assertEqual(canonical_host("::1"), "::1")
        self.assertEqual(canonical_host(""), "")
        self.assertEqual(canonical_host("a" * 80 + ".com"), "a" * 80 + ".com")

    def test_urljoin_resolves_relative_links(self) -> None:
        self.assertEqual(urljoin("https://example.com/docs/a.html", "../b.html"),
                         "https://example.com/b.html")

    def test_urljoin_degrades_on_a_malformed_link(self) -> None:
        self.assertEqual(urljoin("https://example.com/", "http://[::1"), "")

    def test_redact_url(self) -> None:
        self.assertEqual(redact_url("https://user:pw@example.com/a?b=1"),
                         "https://<redacted>@example.com/a?b=1")
        self.assertEqual(redact_url("https://example.com/a"), "https://example.com/a")
        self.assertEqual(redact_url("not a url"), "not a url")


if __name__ == "__main__":
    unittest.main()
