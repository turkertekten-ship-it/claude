"""HTTP client behaviour, exercised over a real socket."""

from __future__ import annotations

import unittest

from oodarag.util.http import HttpClient, HttpError, RetryPolicy, TransportError, normalize_url, same_site
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
