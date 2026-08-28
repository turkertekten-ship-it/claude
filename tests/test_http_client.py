"""HTTP client behaviour, exercised over a real socket."""

from __future__ import annotations

import unittest
import urllib.error

from oodarag.util.http import (
    CircuitBreaker,
    CircuitOpenError,
    HttpClient,
    HttpError,
    PolicyDeniedError,
    RetryPolicy,
    TransportError,
    is_policy_denial,
    normalize_url,
    same_site,
)
from tests.support.httpserver import Route, TestSite


class NormalizeUrlTest(unittest.TestCase):
    def test_canonicalises_scheme_host_and_port(self):
        self.assertEqual(normalize_url("HTTP://Example.COM:80/a"), "http://example.com/a")
        self.assertEqual(normalize_url("HTTPS://Example.COM:443/a"), "https://example.com/a")
        self.assertEqual(normalize_url("https://example.com:8443/a"), "https://example.com:8443/a")

    def test_drops_fragment_and_tracking_params_and_sorts_query(self):
        self.assertEqual(
            normalize_url("https://e.com/p?utm_source=x&b=2&a=1&fbclid=z#section"),
            "https://e.com/p?a=1&b=2",
        )

    def test_empty_path_becomes_root(self):
        self.assertEqual(normalize_url("https://e.com"), "https://e.com/")

    def test_index_html_is_equivalent_to_directory(self):
        self.assertEqual(normalize_url("https://e.com/docs/index.html"), "https://e.com/docs/")

    def test_same_site_handles_subdomains(self):
        self.assertTrue(same_site("https://docs.e.com/a", "https://e.com/b"))
        self.assertFalse(same_site("https://docs.e.com/a", "https://e.com/b", include_subdomains=False))
        self.assertFalse(same_site("https://evil.com/a", "https://e.com/b"))


class HttpClientTest(unittest.TestCase):
    def test_gzip_is_transparently_decoded(self):
        with TestSite({"/g": Route(body="hello gzipped world", gzip_body=True)}) as site:
            resp = HttpClient(rate_per_sec=100).get(site.url("/g"))
            self.assertEqual(resp.text, "hello gzipped world")

    def test_retries_transient_5xx_then_succeeds(self):
        def flaky(hits: int) -> Route | None:
            return Route(body="ok now", status=200) if hits >= 3 else Route(body="boom", status=503)

        with TestSite({"/f": Route(dynamic=flaky)}) as site:
            client = HttpClient(rate_per_sec=100, retry=RetryPolicy(attempts=4, base_delay=0.01))
            resp = client.get(site.url("/f"))
            self.assertEqual(resp.text, "ok now")
            self.assertEqual(client.stats["retries"], 2)
            self.assertEqual(site.hits["/f"], 3)

    def test_does_not_retry_client_errors(self):
        with TestSite({"/gone": Route(body="nope", status=404)}) as site:
            client = HttpClient(rate_per_sec=100, retry=RetryPolicy(attempts=4, base_delay=0.01))
            with self.assertRaises(HttpError) as ctx:
                client.get(site.url("/gone"))
            self.assertEqual(ctx.exception.status, 404)
            self.assertEqual(site.hits["/gone"], 1, "404 must not be retried")

    def test_honours_retry_after_header(self):
        def rate_limited(hits: int) -> Route | None:
            if hits == 1:
                return Route(body="slow down", status=429, headers={"Retry-After": "1"})
            return Route(body="fine", status=200)

        with TestSite({"/r": Route(dynamic=rate_limited)}) as site:
            import time

            client = HttpClient(rate_per_sec=100, retry=RetryPolicy(attempts=3, base_delay=10.0))
            started = time.monotonic()
            resp = client.get(site.url("/r"))
            elapsed = time.monotonic() - started
            self.assertEqual(resp.text, "fine")
            # Retry-After (1s) must win over the 10s exponential backoff.
            self.assertLess(elapsed, 5.0, "Retry-After was ignored in favour of backoff")
            self.assertGreater(elapsed, 0.9)

    def test_allow_status_returns_body_instead_of_raising(self):
        with TestSite({"/robots.txt": Route(body="", status=404)}) as site:
            resp = HttpClient(rate_per_sec=100).get(site.url("/robots.txt"), allow_status=(404,))
            self.assertEqual(resp.status, 404)

    def test_etag_conditional_get_yields_304(self):
        with TestSite({"/e": Route(body="body v1", etag='"abc"')}) as site:
            client = HttpClient(rate_per_sec=100)
            first = client.get(site.url("/e"), conditional=True)
            self.assertEqual(first.status, 200)
            second = client.get(site.url("/e"), conditional=True)
            self.assertEqual(second.status, 304)
            self.assertTrue(second.from_cache)
            self.assertEqual(client.stats["not_modified"], 1)

    def test_response_size_cap_is_enforced(self):
        big = "x" * 200_000
        with TestSite({"/big": Route(body=big)}) as site:
            client = HttpClient(rate_per_sec=100, max_bytes=1000,
                                retry=RetryPolicy(attempts=1, base_delay=0.01))
            with self.assertRaises(TransportError):
                client.get(site.url("/big"))

    def test_post_is_not_replayed_across_a_redirect(self):
        with TestSite({
            "/post": Route(status=302, headers={"Location": "/landing"}),
            "/landing": Route(body="landed"),
        }) as site:
            client = HttpClient(rate_per_sec=100, retry=RetryPolicy(attempts=1, base_delay=0.01))
            resp = client.request("POST", site.url("/post"), body=b"payload",
                                  allow_status=(302,))
            self.assertEqual(resp.status, 302)
            self.assertNotIn(("POST", "/landing"), site.requests)

    def test_circuit_opens_after_repeated_transport_failures(self):
        """A host that cannot be reached must stop costing a full retry cycle."""
        import time as clock

        # Bind and immediately close a port so connections are actively refused.
        import socket

        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        dead = f"http://127.0.0.1:{port}/x"

        client = HttpClient(rate_per_sec=200,
                            retry=RetryPolicy(attempts=2, base_delay=0.01),
                            breaker=CircuitBreaker(threshold=2, cooldown_s=60))
        for _ in range(2):
            with self.assertRaises(TransportError):
                client.get(dead)
        self.assertIn(f"127.0.0.1:{port}", client.breaker.open_hosts)

        started = clock.monotonic()
        with self.assertRaises(CircuitOpenError):
            client.get(dead)
        self.assertLess(clock.monotonic() - started, 0.05,
                        "an open circuit still paid for a connection attempt")
        self.assertEqual(client.stats["short_circuited"], 1)

    def test_an_http_error_does_not_open_the_circuit(self):
        """A 404 means the host answered. Answering is the opposite of unreachable."""
        with TestSite({"/missing": Route(body="", status=404)}) as site:
            client = HttpClient(rate_per_sec=200,
                                retry=RetryPolicy(attempts=1, base_delay=0.01),
                                breaker=CircuitBreaker(threshold=2, cooldown_s=60))
            for _ in range(4):
                with self.assertRaises(HttpError):
                    client.get(site.url("/missing"))
            self.assertEqual(client.breaker.open_hosts, [])

    def test_a_success_closes_the_circuit(self):
        with TestSite({"/ok": Route(body="fine")}) as site:
            client = HttpClient(rate_per_sec=200,
                                retry=RetryPolicy(attempts=1, base_delay=0.01),
                                breaker=CircuitBreaker(threshold=3, cooldown_s=60))
            host = f"127.0.0.1:{site.port}"
            client.breaker.record_failure(host)
            client.breaker.record_failure(host)
            client.get(site.url("/ok"))
            self.assertEqual(client.breaker.open_hosts, [])
            # And the failure count reset, so two more do not immediately open it.
            client.breaker.record_failure(host)
            self.assertEqual(client.breaker.open_hosts, [])

    def test_cooldown_allows_a_probe_through(self):
        breaker = CircuitBreaker(threshold=1, cooldown_s=0.05)
        breaker.record_failure("example.test")
        self.assertTrue(breaker.is_open("example.test"))
        import time as clock

        clock.sleep(0.08)
        self.assertFalse(breaker.is_open("example.test"),
                         "the circuit never reopens, so a recovered host stays blocked")

    def test_rate_limiter_actually_throttles(self):
        import time

        with TestSite({"/x": Route(body="ok")}) as site:
            client = HttpClient(rate_per_sec=5.0, burst=1)
            started = time.monotonic()
            for _ in range(4):
                client.get(site.url("/x"))
            elapsed = time.monotonic() - started
            # 4 requests at 5/s with burst 1 cannot complete faster than ~0.6s.
            self.assertGreater(elapsed, 0.5, f"rate limiter did not throttle (took {elapsed:.3f}s)")


if __name__ == "__main__":
    unittest.main()


class PolicyDenialTest(unittest.TestCase):
    """A proxy that refuses CONNECT is stating a rule, not reporting a fault.

    Retrying it costs the full attempt count plus backoff for a result known in
    advance - measured at about seven seconds per host against this
    environment's proxy, paid again by every code path that touches the host.
    LEARNINGS has said "a permanent failure is not a transient one" since early
    on; the HTTP client was the one place it was not implemented.

    The denial string is recorded verbatim from the live proxy rather than
    invented, so a change in its wording shows up here.
    """

    LIVE_DENIAL = "<urlopen error Tunnel connection failed: 403 Forbidden>"

    def test_the_live_proxy_wording_is_recognised(self):
        self.assertTrue(is_policy_denial(urllib.error.URLError(
            "Tunnel connection failed: 403 Forbidden")))
        self.assertTrue(is_policy_denial(Exception(self.LIVE_DENIAL)))

    def test_an_ordinary_failure_is_not_a_denial(self):
        for text in ("Connection refused", "timed out", "Tunnel connection failed: 502",
                     "[SSL] certificate verify failed", "Name or service not known"):
            with self.subTest(text=text):
                self.assertFalse(is_policy_denial(Exception(text)))

    def _client_raising(self, error: Exception):
        client = HttpClient(rate_per_sec=1000,
                            retry=RetryPolicy(attempts=4, base_delay=0.01))
        attempts = []

        class _Opener:
            def open(self, req, timeout=None):
                attempts.append(req.full_url)
                raise error

        client._opener = _Opener()
        return client, attempts

    def test_a_denial_is_not_retried(self):
        client, attempts = self._client_raising(
            urllib.error.URLError("Tunnel connection failed: 403 Forbidden"))
        with self.assertRaises(PolicyDeniedError):
            client.get("https://blocked.example/x")
        self.assertEqual(len(attempts), 1,
                         f"a policy denial was retried {len(attempts)} times")

    def test_a_transient_failure_is_still_retried(self):
        """The fast path must not have been bought by disabling retries."""
        client, attempts = self._client_raising(urllib.error.URLError("Connection refused"))
        with self.assertRaises(TransportError):
            client.get("https://flaky.example/x")
        self.assertEqual(len(attempts), 4)

    def test_a_denial_does_not_trip_the_circuit_breaker(self):
        """The breaker exists to stop paying for a *flaky* host. A refused one
        is not flaky, and conflating them makes the breaker's own accounting -
        three consecutive transport failures - mean two different things."""
        client, _ = self._client_raising(
            urllib.error.URLError("Tunnel connection failed: 403 Forbidden"))
        for _ in range(5):
            with self.assertRaises(PolicyDeniedError):
                client.get("https://blocked.example/x")
        self.assertFalse(client.breaker.is_open("blocked.example"))

    def test_a_denial_is_a_transport_error_so_callers_still_catch_it(self):
        """Narrowing an exception type must not make existing handlers miss it."""
        self.assertTrue(issubclass(PolicyDeniedError, TransportError))

    def test_the_capability_probe_classifies_by_type_not_substring(self):
        """`"403" in str(e)` also matches a URL containing 403, a byte count of
        403 and a port number. The probe reports "blocked" to a human deciding
        whether a source is reachable, so a false positive there is a false
        blocker - the thing the capability protocol exists to prevent."""
        from oodarag.access.probe import BLOCKED, UNREACHABLE, _classify_http_error

        denied = PolicyDeniedError("egress policy refused https://x/403.html")
        self.assertEqual(_classify_http_error(denied)[0], BLOCKED)

        # A genuine fault whose text merely contains the digits.
        fault = TransportError("URLError: connection reset (https://x/page-403.html)")
        self.assertEqual(_classify_http_error(fault)[0], UNREACHABLE)

        sized = TransportError("response too large: 403 bytes > cap 100")
        self.assertEqual(_classify_http_error(sized)[0], UNREACHABLE)
