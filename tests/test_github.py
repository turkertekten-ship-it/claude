"""Tests for the GitHub connector.

Nothing here touches the network. Every test drives the connector through the
one seam its HTTP client has, `HttpClient._opener`, with fakes shaped like what
urllib actually returns - an `email.message.Message` for headers, a real
`urllib.error.HTTPError` for a non-2xx - because the bugs this module is prone
to only appear against the real shapes.

Three properties get more attention than the rest, because each one fails
silently in production and loudly nowhere:

* the token reaches api.github.com and nothing else - not a foreign host, not a
  `repr`, not a log line, not a document, not the cursor;
* a 403 that means "wait" and a 403 that means "you may not" are told apart
  before anything sleeps;
* the cursor never advances past work the run did not actually do, because the
  next run reads an advanced cursor as "nothing to do".
"""

from __future__ import annotations

import contextlib
import email.message
import io
import json
import os
import time
import unittest
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any
from unittest import mock

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.github import (
    MAX_PAGES,
    MAX_RATE_LIMIT_SLEEP_S,
    SECONDARY_LIMIT_SLEEP_S,
    AccessDeniedError,
    AuthError,
    GitHubClient,
    GitHubConnector,
    GitHubError,
    NotFoundError,
    RateLimitError,
    _next_link,
    _safe_repo_path,
    _valid_ref,
)
from oodarag.util.http import HttpClient, RetryPolicy

OWNER, REPO = "acme", "widget"
SLUG = f"{OWNER}/{REPO}"
API = f"https://api.github.com/repos/{SLUG}"
RAW = f"https://raw.githubusercontent.com/{SLUG}"
HEAD = "a1b2c3d4" + "e" * 32
OLD_HEAD = "9f8e7d6c" + "b" * 32

#: Shaped like a real one so `redact_secrets` recognises it, which is the whole
#: point: the connector must not be the thing that keeps it readable.
TOKEN = "ghp_" + "Tk3nTk3nTk3nTk3nTk3nTk3nTk3nTk3n"

REPO_META = {
    "full_name": SLUG,
    "default_branch": "main",
    "description": "a widget",
    "html_url": f"https://github.com/{SLUG}",
    "language": "Python",
    "stargazers_count": 7,
    "forks_count": 1,
    "open_issues_count": 2,
    "license": {"spdx_id": "MIT"},
    "topics": ["rag"],
    "homepage": None,
    "created_at": "2024-01-01T00:00:00Z",
    "pushed_at": "2024-06-01T00:00:00Z",
}


# ------------------------------------------------------------------------ fakes


def message(headers: dict[str, str]) -> email.message.Message:
    msg = email.message.Message()
    for key, value in headers.items():
        msg[key] = value
    return msg


class FakeResponse:
    """What `opener.open()` returns on a 2xx. Re-readable, so one planned
    response can serve a route that is hit more than once."""

    def __init__(self, status: int = 200, headers: dict[str, str] | None = None,
                 body: bytes = b"", url: str = "") -> None:
        self.status = status
        self.headers = message(headers or {})
        self.body = body
        self._pos = 0
        self._url = url

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            chunk = self.body[self._pos :]
        else:
            chunk = self.body[self._pos : self._pos + size]
        self._pos += len(chunk)
        return chunk

    def __enter__(self) -> FakeResponse:
        self._pos = 0
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


def json_response(payload: Any, *, headers: dict[str, str] | None = None,
                  status: int = 200) -> FakeResponse:
    body = json.dumps(payload).encode("utf-8")
    return FakeResponse(status, {"Content-Type": "application/json", **(headers or {})}, body)


def text_response(body: bytes, *, headers: dict[str, str] | None = None) -> FakeResponse:
    return FakeResponse(200, {"Content-Type": "text/plain; charset=utf-8", **(headers or {})}, body)


def http_error(code: int, body: bytes = b"{}", headers: dict[str, str] | None = None,
               url: str = API) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url, code, f"status {code}", message(headers or {}), io.BytesIO(body)
    )


def link(next_url: str) -> dict[str, str]:
    return {"Link": f'<{next_url}>; rel="next", <https://api.github.com/last>; rel="last"'}


@dataclass(slots=True)
class Route:
    match: str
    outcomes: list[Any]
    exact: bool = False
    repeat: bool = False
    hits: int = 0

    def take(self, url: str) -> Any:
        self.hits += 1
        if not self.outcomes:
            raise AssertionError(f"route {self.match!r} has no outcome left for {url}")
        outcome = self.outcomes[0] if self.repeat else self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


@dataclass
class FakeOpener:
    """Serves planned outcomes by URL, and refuses to invent extras.

    Exact routes are consulted before substring ones, so `.../repos/acme/widget`
    can be planned separately from the dozen endpoints hanging beneath it
    without the tests depending on registration order.
    """

    routes: list[Route] = field(default_factory=list)
    requests: list[urllib.request.Request] = field(default_factory=list)

    def exact(self, url: str, *outcomes: Any, repeat: bool = False) -> FakeOpener:
        self.routes.append(Route(url, list(outcomes), exact=True, repeat=repeat))
        return self

    def route(self, fragment: str, *outcomes: Any, repeat: bool = False) -> FakeOpener:
        self.routes.append(Route(fragment, list(outcomes), repeat=repeat))
        return self

    @property
    def urls(self) -> list[str]:
        return [r.full_url for r in self.requests]

    def open(self, req: urllib.request.Request, timeout: float | None = None) -> Any:
        self.requests.append(req)
        url = req.full_url
        for route in self.routes:
            if route.exact and route.match == url:
                return _addressed(route.take(url), url)
        for route in self.routes:
            if not route.exact and route.match in url:
                return _addressed(route.take(url), url)
        raise AssertionError(f"unplanned request: {url}")


def _addressed(response: Any, url: str) -> Any:
    """urllib reports the URL it ended up at; a planned response inherits it."""
    if isinstance(response, FakeResponse) and not response._url:
        response._url = url
    return response


def header_of(req: urllib.request.Request, name: str) -> str | None:
    for key, value in req.header_items():
        if key.lower() == name.lower():
            return value
    return None


def blob_entry(path: str, sha: str = "", size: int = 100, mode: str = "100644",
               kind: str = "blob") -> dict[str, Any]:
    return {"path": path, "sha": sha or ("b" * 39 + str(abs(hash(path)) % 10)),
            "size": size, "mode": mode, "type": kind}


class GitHubTestCase(unittest.TestCase):
    """Base: no ambient token, no real sleeping, whatever the code decides."""

    def setUp(self) -> None:
        env = mock.patch.dict(os.environ, {}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        sleeper = mock.patch("oodarag.ingest.github.time.sleep")
        self.sleep = sleeper.start()
        self.addCleanup(sleeper.stop)

    @property
    def waits(self) -> list[float]:
        return [call.args[0] for call in self.sleep.call_args_list]

    def http(self, opener: FakeOpener) -> HttpClient:
        client = HttpClient(
            retry=RetryPolicy(attempts=1, base_delay=0.0, max_delay=0.0, jitter=0.0),
            rate_per_sec=1_000_000.0,
        )
        client._opener = opener
        return client

    def gh(self, opener: FakeOpener, **kw: Any) -> GitHubClient:
        return GitHubClient(client=self.http(opener), **kw)

    def connector(self, opener: FakeOpener, *, token: str | None = None,
                  **kw: Any) -> GitHubConnector:
        kw.setdefault("owner", OWNER)
        kw.setdefault("repo", REPO)
        return GitHubConnector(gh=self.gh(opener, token=token), **kw)

    def repo_opener(self, *, meta: dict[str, Any] | None = None,
                    head: str = HEAD) -> FakeOpener:
        """An opener that can answer the two calls every run starts with."""
        opener = FakeOpener()
        opener.exact(API, json_response(meta if meta is not None else REPO_META), repeat=True)
        opener.route(f"{API}/commits/", json_response({"sha": head}), repeat=True)
        return opener


# ------------------------------------------------------------------ pure pieces


class LinkHeaderTestCase(unittest.TestCase):
    def test_next_in_the_first_position(self) -> None:
        header = '<https://api.github.com/x?page=2>; rel="next", <https://x/9>; rel="last"'
        self.assertEqual(_next_link(header), "https://api.github.com/x?page=2")

    def test_next_in_a_later_position(self) -> None:
        header = '<https://x/9>; rel="last", <https://api.github.com/x?page=2>; rel="next"'
        self.assertEqual(_next_link(header), "https://api.github.com/x?page=2")

    def test_rel_need_not_be_the_first_parameter(self) -> None:
        # The old parser looked only at segment[1] and silently stopped paging.
        self.assertEqual(_next_link('<https://a/b>; type="text/html"; rel="next"'), "https://a/b")

    def test_rel_may_be_unquoted_or_single_quoted(self) -> None:
        self.assertEqual(_next_link("<https://a/b>; rel=next"), "https://a/b")
        self.assertEqual(_next_link("<https://a/b>; rel='next'"), "https://a/b")

    def test_rel_may_carry_several_values(self) -> None:
        self.assertEqual(_next_link('<https://a/b>; rel="prev next"'), "https://a/b")

    def test_a_uri_may_contain_a_comma(self) -> None:
        self.assertEqual(_next_link('<https://a/b?q=1,2>; rel="next"'), "https://a/b?q=1,2")

    def test_no_next_relation(self) -> None:
        self.assertIsNone(_next_link('<https://a/b>; rel="prev"'))
        self.assertIsNone(_next_link('<https://a/b>; rel="nextish"'))

    def test_malformed_headers_yield_nothing(self) -> None:
        for header in ("", "garbage", "<>; rel=\"next\"", "https://a/b; rel=next", "<https://a/b>"):
            with self.subTest(header=header):
                self.assertIsNone(_next_link(header))


class PathSafetyTestCase(unittest.TestCase):
    def test_ordinary_paths_pass(self) -> None:
        for path in ("README.md", "src/a/b.py", "a-b/c_d.e.txt", ".github/workflows/ci.yml"):
            with self.subTest(path=path):
                self.assertTrue(_safe_repo_path(path))

    def test_traversal_and_reroots_are_refused(self) -> None:
        for path in ("../etc/passwd", "a/../../b", "/etc/passwd", "~/.ssh/id_rsa",
                     "C:/Windows/x", "a\\b", "a//b", "a/", "", ".", "..", "a/./b",
                     "x\x00y", "a\nb", ".git/config", "x" * 2000):
            with self.subTest(path=path):
                self.assertFalse(_safe_repo_path(path))


class RefValidationTestCase(GitHubTestCase):
    def test_real_refs_pass(self) -> None:
        for ref in ("main", "release/2.1", "v1.0.0", "a" * 40):
            with self.subTest(ref=ref):
                self.assertTrue(_valid_ref(ref))

    def test_refs_that_would_reshape_the_url_are_refused(self) -> None:
        for ref in ("", "..", "../../users/self", "a b", "-x", "x/", "a//b", "x@{1}",
                    "x.lock", "a?b", "a#b"):
            with self.subTest(ref=ref):
                self.assertFalse(_valid_ref(ref))

    def test_connector_rejects_an_unsafe_ref(self) -> None:
        with self.assertRaises(ValueError):
            GitHubConnector(owner=OWNER, repo=REPO, ref="../../../users/self")

    def test_connector_rejects_owner_or_repo_that_is_not_a_name(self) -> None:
        for owner, repo in (("", "r"), ("o", ""), ("o/x", "r"), ("..", "r"), ("o", "a b"),
                            ("o", "r?x")):
            with self.subTest(owner=owner, repo=repo):
                with self.assertRaises(ValueError):
                    GitHubConnector(owner=owner, repo=repo)

    def test_a_broken_include_pattern_is_dropped_not_raised(self) -> None:
        conn = self.connector(FakeOpener(), include_paths=("[unclosed",), exclude_paths=("(",))
        self.assertEqual(conn._includes, ())
        self.assertEqual(conn._excludes, ())


# ----------------------------------------------------------------------- tokens


class AuthenticationTestCase(GitHubTestCase):
    def test_token_is_sent_to_the_api_host(self) -> None:
        opener = FakeOpener().route("/rate_limit", json_response({"resources": {"core": {}}}))
        self.gh(opener, token=TOKEN).get("/rate_limit")
        self.assertEqual(header_of(opener.requests[0], "authorization"), f"Bearer {TOKEN}")

    def test_token_is_sent_to_the_configured_raw_host(self) -> None:
        opener = FakeOpener().route("raw.githubusercontent.com", text_response(b"x"))
        self.gh(opener, token=TOKEN).request(f"{RAW}/{HEAD}/a.md")
        self.assertEqual(header_of(opener.requests[0], "authorization"), f"Bearer {TOKEN}")

    def test_token_is_never_sent_to_another_host(self) -> None:
        """The whole reason auth is per-request: a URL can come from a server."""
        opener = FakeOpener().route("evil.test", json_response({}))
        self.gh(opener, token=TOKEN).get("https://evil.test/steal")
        self.assertIsNone(header_of(opener.requests[0], "authorization"))

    def test_token_never_reaches_the_shared_http_clients_default_headers(self) -> None:
        client = self.http(FakeOpener())
        self.gh(FakeOpener(), token=TOKEN)  # unrelated client, same process
        gh = GitHubClient(token=TOKEN, client=client)
        self.assertNotIn("Authorization", client.default_headers)
        self.assertEqual(client.default_headers, {})
        self.assertTrue(gh.authenticated)

    def test_a_caller_supplied_client_is_not_modified(self) -> None:
        client = self.http(FakeOpener())
        client.default_headers["X-Mine"] = "1"
        GitHubClient(token=TOKEN, client=client)
        self.assertEqual(client.default_headers, {"X-Mine": "1"})

    def test_the_token_is_not_in_any_repr(self) -> None:
        opener = FakeOpener()
        conn = self.connector(opener, token=TOKEN)
        for text in (repr(conn.gh), repr(conn), f"{conn.gh}", f"{conn}"):
            self.assertNotIn(TOKEN, text)
        self.assertIn("authenticated=True", repr(conn.gh))

    def test_env_supplies_the_token_when_the_caller_does_not(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": TOKEN}, clear=True):
            self.assertTrue(GitHubClient().authenticated)
        with mock.patch.dict(os.environ, {"GH_TOKEN": TOKEN}, clear=True):
            self.assertTrue(GitHubClient().authenticated)
        self.assertFalse(GitHubClient().authenticated)

    def test_api_version_and_accept_travel_with_every_request(self) -> None:
        opener = FakeOpener().route("/rate_limit", json_response({}))
        self.gh(opener).get("/rate_limit")
        req = opener.requests[0]
        self.assertEqual(header_of(req, "x-github-api-version"), "2022-11-28")
        self.assertIn("github", header_of(req, "accept") or "")


# ------------------------------------------------------------------ rate limits


class RateLimitTestCase(GitHubTestCase):
    def limited(self, reset_in: float = 30.0, **headers: str) -> urllib.error.HTTPError:
        base = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(time.time() + reset_in)}
        base.update(headers)
        return http_error(403, b'{"message": "API rate limit exceeded"}', base)

    def test_a_primary_limit_waits_for_the_reset_then_retries(self) -> None:
        opener = FakeOpener().route("/rate_limit", self.limited(30.0),
                                    json_response({"resources": {"core": {"remaining": 10}}}))
        result = self.gh(opener).get("/rate_limit")

        self.assertEqual(result["resources"]["core"]["remaining"], 10)
        self.assertEqual(len(self.waits), 1)
        self.assertAlmostEqual(self.waits[0], 31.0, delta=2.0)

    def test_a_wait_is_capped_however_far_away_the_reset_claims_to_be(self) -> None:
        opener = FakeOpener().route("/rate_limit", self.limited(10_000.0), json_response({}))
        self.gh(opener).get("/rate_limit")
        self.assertEqual(self.waits, [MAX_RATE_LIMIT_SLEEP_S])

    def test_a_reset_already_in_the_past_does_not_produce_a_negative_wait(self) -> None:
        opener = FakeOpener().route("/rate_limit", self.limited(-500.0), json_response({}))
        self.gh(opener).get("/rate_limit")
        self.assertEqual(self.waits, [0.0])

    def test_retry_after_wins_over_the_reset_header(self) -> None:
        err = self.limited(30.0, **{"retry-after": "7"})
        opener = FakeOpener().route("/rate_limit", err, json_response({}))
        self.gh(opener).get("/rate_limit")
        self.assertEqual(self.waits, [7.0])

    def test_a_secondary_limit_without_headers_still_waits(self) -> None:
        err = http_error(403, b'{"message": "You have exceeded a secondary rate limit"}')
        opener = FakeOpener().route("/rate_limit", err, json_response({}))
        self.gh(opener).get("/rate_limit")
        self.assertEqual(self.waits, [SECONDARY_LIMIT_SLEEP_S])

    def test_a_429_is_a_rate_limit_even_with_no_hints_at_all(self) -> None:
        opener = FakeOpener().route("/rate_limit", http_error(429, b"slow down"),
                                    json_response({}))
        self.gh(opener).get("/rate_limit")
        self.assertEqual(self.waits, [SECONDARY_LIMIT_SLEEP_S])

    def test_a_permissions_403_is_not_waited_on(self) -> None:
        """The bug this pins: waiting an hour to fail with the same 403."""
        err = http_error(403, b'{"message": "Resource not accessible by integration"}',
                         {"x-ratelimit-remaining": "4321"})
        opener = FakeOpener().route("/rate_limit", err)

        with self.assertRaises(AccessDeniedError) as caught:
            self.gh(opener, token=TOKEN).get("/rate_limit")

        self.assertEqual(self.waits, [])
        self.assertEqual(caught.exception.status, 403)
        message = str(caught.exception)
        self.assertIn("not a rate limit", message)
        self.assertIn("scope", message)
        self.assertNotIn(TOKEN, message)

    def test_a_limit_that_outlasts_our_patience_raises_rather_than_hangs(self) -> None:
        opener = FakeOpener().route("/rate_limit", *[self.limited(5.0) for _ in range(6)])
        gh = self.gh(opener, max_rate_limit_waits=2)

        with self.assertRaises(RateLimitError):
            gh.get("/rate_limit")

        self.assertEqual(len(self.waits), 2, "waits must be bounded")
        self.assertEqual(len(opener.requests), 3)

    def test_zero_patience_means_no_wait_at_all(self) -> None:
        opener = FakeOpener().route("/rate_limit", self.limited(5.0))
        with self.assertRaises(RateLimitError):
            self.gh(opener, max_rate_limit_waits=0).get("/rate_limit")
        self.assertEqual(self.waits, [])


# --------------------------------------------------------------- classification


class ErrorClassificationTestCase(GitHubTestCase):
    def test_404_without_a_token_names_the_private_repository_case(self) -> None:
        opener = FakeOpener().exact(API, http_error(404, b'{"message": "Not Found"}'))
        conn = self.connector(opener)

        with self.assertRaises(NotFoundError) as caught:
            list(conn.fetch({}))

        message = str(caught.exception)
        self.assertIn("no token is configured", message)
        self.assertIn("404, not 403", message)

    def test_404_with_a_token_names_the_invisible_repository_case(self) -> None:
        opener = FakeOpener().exact(API, http_error(404, b'{"message": "Not Found"}'))
        conn = self.connector(opener, token=TOKEN)

        with self.assertRaises(NotFoundError) as caught:
            list(conn.fetch({}))

        self.assertIn("cannot see it", str(caught.exception))
        self.assertNotIn(TOKEN, str(caught.exception))

    def test_401_says_the_credential_was_rejected(self) -> None:
        opener = FakeOpener().exact(API, http_error(401, b'{"message": "Bad credentials"}'))
        with self.assertRaises(AuthError) as caught:
            list(self.connector(opener, token=TOKEN).fetch({}))
        self.assertIn("rejected", str(caught.exception))
        self.assertNotIn(TOKEN, str(caught.exception))

    def test_other_statuses_keep_their_number(self) -> None:
        opener = FakeOpener().exact(API, http_error(500, b"boom"))
        with self.assertRaises(GitHubError) as caught:
            list(self.connector(opener).fetch({}))
        self.assertEqual(caught.exception.status, 500)
        self.assertNotIsInstance(caught.exception, NotFoundError)

    def test_an_error_body_carrying_a_credential_is_redacted(self) -> None:
        """Proxies rewrite error bodies. The message goes into logs and deltas."""
        body = json.dumps({"message": f"bad token {TOKEN}"}).encode()
        opener = FakeOpener().exact(API, http_error(403, body, {"x-ratelimit-remaining": "10"}))

        with self.assertRaises(AccessDeniedError) as caught:
            list(self.connector(opener).fetch({}))

        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertIn("<redacted:github-token>", str(caught.exception))

    def test_malformed_json_is_an_error_not_a_traceback(self) -> None:
        opener = FakeOpener().exact(API, text_response(b"<html>maintenance</html>"))
        with self.assertRaises(GitHubError) as caught:
            list(self.connector(opener).fetch({}))
        self.assertIn("malformed JSON", str(caught.exception))

    def test_rate_limit_probe_degrades_to_an_error_field(self) -> None:
        opener = FakeOpener().route("/rate_limit", http_error(500, b"nope"))
        self.assertIn("error", self.gh(opener).rate_limit())

    def test_rate_limit_probe_reads_the_core_resource(self) -> None:
        opener = FakeOpener().route(
            "/rate_limit", json_response({"resources": {"core": {"remaining": 4999}}})
        )
        self.assertEqual(self.gh(opener).rate_limit(), {"remaining": 4999})


# ------------------------------------------------------------------- pagination


class PaginationTestCase(GitHubTestCase):
    def test_walks_every_page(self) -> None:
        opener = FakeOpener()
        opener.route("after=beta", json_response([{"id": 3}]))
        opener.route("/things", json_response([{"id": 1}, {"id": 2}],
                                              headers=link("https://api.github.com/x?after=beta")))

        items = list(self.gh(opener).paginate("/things"))

        self.assertEqual([i["id"] for i in items], [1, 2, 3])
        self.assertEqual(len(opener.requests), 2)

    def test_a_missing_link_header_ends_the_walk(self) -> None:
        opener = FakeOpener().route("/things", json_response([{"id": 1}]))
        self.assertEqual(len(list(self.gh(opener).paginate("/things"))), 1)
        self.assertEqual(len(opener.requests), 1)

    def test_a_malformed_link_header_ends_the_walk(self) -> None:
        opener = FakeOpener().route(
            "/things", json_response([{"id": 1}], headers={"Link": "<broken; rel=next"})
        )
        self.assertEqual(len(list(self.gh(opener).paginate("/things"))), 1)
        self.assertEqual(len(opener.requests), 1)

    def test_a_next_link_pointing_backwards_terminates(self) -> None:
        first = "https://api.github.com/things?per_page=100"
        opener = FakeOpener()
        opener.route("after=beta", json_response([{"id": 2}], headers=link(first)))
        opener.route("/things", json_response([{"id": 1}],
                                              headers=link("https://api.github.com/x?after=beta")))

        items = list(self.gh(opener).paginate("/things"))

        self.assertEqual([i["id"] for i in items], [1, 2])
        self.assertEqual(len(opener.requests), 2, "page one must not be read twice")

    def test_a_self_referential_empty_page_terminates(self) -> None:
        """No item is ever yielded, so `max_items` can never end this loop."""
        loop = "https://api.github.com/things?after=beta"
        opener = FakeOpener()
        opener.route("after=beta", json_response([], headers=link(loop)), repeat=True)
        opener.route("/things", json_response([], headers=link(loop)))

        self.assertEqual(list(self.gh(opener).paginate("/things")), [])
        self.assertEqual(len(opener.requests), 2)

    def test_an_endless_chain_of_fresh_pages_stops_at_the_page_cap(self) -> None:
        class Endless:
            """A server that always has one more page, never the same URL twice."""

            def __init__(self) -> None:
                self.calls = 0
                self.requests: list[urllib.request.Request] = []

            def open(self, req: urllib.request.Request, timeout: float | None = None) -> Any:
                self.calls += 1
                nxt = f"https://api.github.com/things?cursor={self.calls}"
                return json_response([{"id": self.calls}], headers=link(nxt))

        opener = Endless()
        gh = self.gh(FakeOpener())
        gh.http._opener = opener

        items = list(gh.paginate("/things", max_items=10_000))

        self.assertEqual(opener.calls, MAX_PAGES)
        self.assertEqual(len(items), MAX_PAGES)

    def test_an_off_origin_next_link_is_refused(self) -> None:
        opener = FakeOpener().route(
            "/things", json_response([{"id": 1}], headers=link("https://evil.test/steal"))
        )
        items = list(self.gh(opener, token=TOKEN).paginate("/things"))

        self.assertEqual(len(items), 1)
        self.assertEqual(len(opener.requests), 1)
        self.assertNotIn("evil.test", " ".join(opener.urls))

    def test_max_items_is_an_exact_cap_and_stops_the_walk(self) -> None:
        opener = FakeOpener().route(
            "/things", json_response([{"id": 1}, {"id": 2}, {"id": 3}],
                                     headers=link("https://api.github.com/x?after=beta"))
        )
        items = list(self.gh(opener).paginate("/things", max_items=2))

        self.assertEqual([i["id"] for i in items], [1, 2])
        self.assertEqual(len(opener.requests), 1, "the next page must not be fetched")

    def test_zero_max_items_makes_no_request_at_all(self) -> None:
        opener = FakeOpener()
        self.assertEqual(list(self.gh(opener).paginate("/things", max_items=0)), [])
        self.assertEqual(opener.requests, [])

    def test_per_page_is_clamped_to_what_is_actually_wanted(self) -> None:
        opener = FakeOpener().route("/things", json_response([]))
        list(self.gh(opener).paginate("/things", per_page=100, max_items=5))
        self.assertIn("per_page=5", opener.urls[0])

    def test_search_shaped_payloads_use_the_items_key(self) -> None:
        opener = FakeOpener().route("/things", json_response({"total_count": 1,
                                                              "items": [{"id": 1}]}))
        self.assertEqual([i["id"] for i in self.gh(opener).paginate("/things")], [1])

    def test_entries_that_are_not_objects_are_skipped(self) -> None:
        opener = FakeOpener().route("/things", json_response([{"id": 1}, None, "x", [1]]))
        self.assertEqual([i["id"] for i in self.gh(opener).paginate("/things")], [1])

    def test_an_unreadable_page_stops_the_walk_without_raising(self) -> None:
        opener = FakeOpener().route("/things", text_response(b"not json"))
        self.assertEqual(list(self.gh(opener).paginate("/things")), [])

    def test_a_rate_limit_mid_walk_is_waited_out(self) -> None:
        limited = http_error(403, b"rate limit", {"x-ratelimit-remaining": "0",
                                                  "x-ratelimit-reset": str(time.time() + 5)})
        opener = FakeOpener().route("/things", limited, json_response([{"id": 1}]))
        self.assertEqual(len(list(self.gh(opener).paginate("/things"))), 1)
        self.assertEqual(len(self.waits), 1)


# -------------------------------------------------------------------- file walk


TREE_TWO_FILES = {
    "sha": HEAD,
    "truncated": False,
    "tree": [
        blob_entry("README.md", "1" * 40, size=12),
        blob_entry("src/app.py", "2" * 40, size=20),
        {"path": "src", "type": "tree", "sha": "3" * 40, "mode": "040000"},
    ],
}


class FileWalkTestCase(GitHubTestCase):
    def walker(self, tree: dict[str, Any], *, files: dict[str, bytes] | None = None,
               head: str = HEAD, **kw: Any) -> tuple[GitHubConnector, FakeOpener]:
        opener = self.repo_opener(head=head)
        opener.route(f"{API}/git/trees/", json_response(tree), repeat=True)
        for path, body in (files or {}).items():
            opener.route(f"/{head}/{path}", text_response(body), repeat=True)
        conn = self.connector(opener, resources=("files",), **kw)
        return conn, opener

    def test_files_become_documents_pinned_at_the_head_sha(self) -> None:
        conn, opener = self.walker(
            TREE_TWO_FILES,
            files={"README.md": b"# hello\n", "src/app.py": b"print('hi')\n"},
        )
        docs = list(conn.fetch({}))

        self.assertEqual([d.external_id for d in docs],
                         [f"{SLUG}#file:README.md", f"{SLUG}#file:src/app.py"])
        self.assertEqual(docs[1].uri, f"https://github.com/{SLUG}/blob/{HEAD}/src/app.py")
        self.assertEqual(docs[1].metadata["language"], "python")
        self.assertEqual(docs[1].metadata["dir"], "src")
        self.assertEqual(docs[1].metadata["commit"], HEAD)
        self.assertEqual(docs[0].text, "# hello\n")
        self.assertTrue(conn.stats["files_complete"])

    def test_a_path_with_a_hash_still_produces_a_usable_permalink(self) -> None:
        tree = {"tree": [blob_entry("docs/a#b.md", "4" * 40, size=3)]}
        conn, opener = self.walker(tree, files={"docs/a%23b.md": b"hi\n"})
        docs = list(conn.fetch({}))
        self.assertEqual(docs[0].uri, f"https://github.com/{SLUG}/blob/{HEAD}/docs/a%23b.md")

    def test_symlink_entries_are_skipped(self) -> None:
        """A symlink is a blob whose content is the path it points at."""
        tree = {"tree": [blob_entry("link.md", "5" * 40, size=9, mode="120000"),
                         blob_entry("real.md", "6" * 40, size=3)]}
        conn, opener = self.walker(tree, files={"real.md": b"ok\n"})

        docs = list(conn.fetch({}))

        self.assertEqual([d.metadata["path"] for d in docs], ["real.md"])
        self.assertEqual(conn.stats["skipped"]["symlink_or_submodule"], 1)
        self.assertNotIn("link.md", " ".join(opener.urls))

    def test_submodule_pointers_are_skipped(self) -> None:
        tree = {"tree": [{"path": "dep", "type": "commit", "sha": "7" * 40, "mode": "160000"},
                         blob_entry("real.md", "6" * 40, size=3)]}
        conn, opener = self.walker(tree, files={"real.md": b"ok\n"})
        self.assertEqual([d.metadata["path"] for d in list(conn.fetch({}))], ["real.md"])

    def test_a_traversing_path_is_never_turned_into_a_url(self) -> None:
        tree = {"tree": [blob_entry("../../../etc/passwd.md", "8" * 40, size=5),
                         blob_entry("/etc/shadow.md", "9" * 40, size=5),
                         blob_entry("real.md", "6" * 40, size=3)]}
        conn, opener = self.walker(tree, files={"real.md": b"ok\n"})

        docs = list(conn.fetch({}))

        self.assertEqual([d.metadata["path"] for d in docs], ["real.md"])
        self.assertEqual(conn.stats["skipped"]["unsafe_path"], 2)
        self.assertNotIn("passwd", " ".join(opener.urls))
        self.assertNotIn("shadow", " ".join(opener.urls))

    def test_a_binary_blob_is_skipped_rather_than_decoded(self) -> None:
        tree = {"tree": [blob_entry("logo.md", "a" * 40, size=8)]}
        conn, _ = self.walker(tree, files={"logo.md": b"\x89PNG\x00\x00\x01ok"})

        self.assertEqual(list(conn.fetch({})), [])
        self.assertEqual(conn.stats["skipped"]["binary"], 1)
        # Binary is a property of the bytes, so the sha is remembered and the
        # next run does not spend a request re-discovering it.
        self.assertEqual(conn.stats["blob_shas"], {"logo.md": "a" * 40})
        self.assertTrue(conn.stats["files_complete"])

    def test_a_file_over_the_cap_is_skipped_from_the_tree_alone(self) -> None:
        tree = {"tree": [blob_entry("big.md", "a" * 40, size=400_001)]}
        conn, opener = self.walker(tree, max_file_bytes=400_000)

        self.assertEqual(list(conn.fetch({})), [])
        self.assertEqual(conn.stats["skipped"]["too_large"], 1)
        self.assertNotIn("big.md", " ".join(opener.urls), "no bytes may be spent on it")

    def test_a_file_exactly_at_the_cap_is_kept(self) -> None:
        tree = {"tree": [blob_entry("edge.md", "a" * 40, size=10)]}
        conn, _ = self.walker(tree, files={"edge.md": b"0123456789"}, max_file_bytes=10)
        self.assertEqual(len(list(conn.fetch({}))), 1)

    def test_a_response_bigger_than_the_tree_promised_is_still_capped(self) -> None:
        tree = {"tree": [blob_entry("lying.md", "a" * 40, size=10)]}
        conn, _ = self.walker(tree, files={"lying.md": b"x" * 5000}, max_file_bytes=100)

        self.assertEqual(list(conn.fetch({})), [])
        self.assertEqual(conn.stats["skipped"]["too_large"], 1)

    def test_skip_patterns_and_extension_gating(self) -> None:
        tree = {"tree": [
            blob_entry("node_modules/x/a.js", "a" * 40, size=5),
            blob_entry("app.min.js", "b" * 40, size=5),
            blob_entry("image.png", "c" * 40, size=5),
            blob_entry("Dockerfile", "d" * 40, size=5),
            blob_entry(".env.example", "e" * 40, size=5),
        ]}
        conn, _ = self.walker(tree, files={"Dockerfile": b"FROM x\n",
                                           ".env.example": b"KEY=\n"})

        docs = list(conn.fetch({}))

        self.assertEqual(sorted(d.metadata["path"] for d in docs), [".env.example", "Dockerfile"])
        self.assertEqual(conn.stats["skipped"]["skip_pattern"], 2)
        self.assertEqual(conn.stats["skipped"]["not_text"], 1)

    def test_include_and_exclude_are_applied(self) -> None:
        tree = {"tree": [blob_entry("docs/a.md", "a" * 40, size=3),
                         blob_entry("src/b.md", "b" * 40, size=3)]}
        conn, _ = self.walker(tree, files={"docs/a.md": b"ok\n"}, include_paths=("^docs/",))
        self.assertEqual([d.metadata["path"] for d in conn.fetch({})], ["docs/a.md"])

        conn, _ = self.walker(tree, files={"src/b.md": b"ok\n"}, exclude_paths=("^docs/",))
        self.assertEqual([d.metadata["path"] for d in conn.fetch({})], ["src/b.md"])

    def test_a_truncated_tree_refuses_to_advance_the_head(self) -> None:
        tree = dict(TREE_TWO_FILES, truncated=True)
        conn, _ = self.walker(tree, files={"README.md": b"a\n", "src/app.py": b"b\n"})

        list(conn.fetch({}))
        cursor = conn.next_cursor({})

        self.assertFalse(conn.stats["files_complete"])
        self.assertNotIn("head_sha", cursor)
        self.assertEqual(conn.stats["skipped"]["tree_truncated"], 1)
        self.assertIn("blob_shas", cursor, "what we did read is still worth remembering")

    def test_the_max_files_budget_stops_emitting_and_marks_the_run_partial(self) -> None:
        conn, _ = self.walker(
            TREE_TWO_FILES, files={"README.md": b"a\n", "src/app.py": b"b\n"}, max_files=1
        )
        docs = list(conn.fetch({}))

        self.assertEqual(len(docs), 1)
        self.assertEqual(conn.stats["skipped"]["max_files"], 1)
        self.assertFalse(conn.stats["files_complete"])
        # The unread file's sha is deliberately absent, so the next run owes it.
        self.assertEqual(set(conn.stats["blob_shas"]), {"README.md"})
        self.assertNotIn("head_sha", conn.next_cursor({}))

    def test_the_budget_walk_converges_over_successive_runs(self) -> None:
        state = MemoryStateStore()
        conn, _ = self.walker(
            TREE_TWO_FILES, files={"README.md": b"a\n", "src/app.py": b"b\n"}, max_files=1
        )
        first = conn.run(state)
        second = conn.run(state)

        self.assertEqual([d.metadata["path"] for d in first.documents], ["README.md"])
        self.assertEqual([d.metadata["path"] for d in second.documents], ["src/app.py"])
        self.assertEqual(second.cursor["head_sha"], HEAD, "now the walk is complete")

    def test_an_entry_without_a_usable_sha_is_skipped(self) -> None:
        tree = {"tree": [{"path": "a.md", "type": "blob", "size": 3, "mode": "100644"},
                         blob_entry("b.md", "c" * 40, size=3)]}
        conn, _ = self.walker(tree, files={"b.md": b"ok\n"})
        self.assertEqual([d.metadata["path"] for d in conn.fetch({})], ["b.md"])
        self.assertEqual(conn.stats["skipped"]["bad_sha"], 1)

    def test_a_non_numeric_size_does_not_abort_the_walk(self) -> None:
        tree = {"tree": [dict(blob_entry("a.md", "c" * 40), size="huge")]}
        conn, _ = self.walker(tree, files={"a.md": b"ok\n"})
        self.assertEqual(len(list(conn.fetch({}))), 1)

    def test_junk_entries_do_not_abort_the_walk(self) -> None:
        tree = {"tree": [None, "nonsense", {"type": "blob"},
                         blob_entry("a.md", "c" * 40, size=3)]}
        conn, _ = self.walker(tree, files={"a.md": b"ok\n"})
        self.assertEqual(len(list(conn.fetch({}))), 1)

    def test_an_empty_tree_is_a_complete_walk(self) -> None:
        conn, _ = self.walker({"tree": [], "truncated": False})
        self.assertEqual(list(conn.fetch({})), [])
        self.assertTrue(conn.stats["files_complete"])
        self.assertEqual(conn.next_cursor({})["head_sha"], HEAD)


# ------------------------------------------------------------------ blob bodies


class BlobFetchTestCase(GitHubTestCase):
    def api_blob(self, payload: Any, *, tree: dict[str, Any] | None = None,
                 raw: Any = None, **kw: Any) -> tuple[GitHubConnector, FakeOpener]:
        tree = tree or {"tree": [blob_entry("a.md", "c" * 40, size=10)]}
        opener = self.repo_opener()
        opener.route(f"{API}/git/trees/", json_response(tree), repeat=True)
        opener.route("raw.githubusercontent.com", raw or http_error(404, b"not found"),
                     repeat=True)
        opener.route(f"{API}/git/blobs/", payload, repeat=True)
        return self.connector(opener, resources=("files",), **kw), opener

    def test_base64_content_is_decoded_when_raw_is_unavailable(self) -> None:
        import base64 as b64

        payload = json_response({"encoding": "base64",
                                 "content": b64.b64encode("héllo\n".encode()).decode()})
        conn, opener = self.api_blob(payload)

        docs = list(conn.fetch({}))

        self.assertEqual(docs[0].text, "héllo\n")
        self.assertIn(f"{API}/git/blobs/{'c' * 40}", opener.urls)

    def test_base64_line_breaks_are_tolerated(self) -> None:
        payload = json_response({"encoding": "base64", "content": "aGVs\nbG8=\n"})
        conn, _ = self.api_blob(payload)
        self.assertEqual(list(conn.fetch({}))[0].text, "hello")

    def test_an_oversized_base64_body_is_refused_before_it_is_decoded(self) -> None:
        payload = json_response({"encoding": "base64", "content": "A" * 100_000})
        conn, _ = self.api_blob(payload, max_file_bytes=1000)

        with mock.patch("oodarag.ingest.github.base64.b64decode") as decode:
            self.assertEqual(list(conn.fetch({})), [])

        decode.assert_not_called()
        self.assertEqual(conn.stats["skipped"]["too_large"], 1)

    def test_a_binary_base64_body_is_skipped(self) -> None:
        import base64 as b64

        payload = json_response({"encoding": "base64",
                                 "content": b64.b64encode(b"\x00\x01\x02").decode()})
        conn, _ = self.api_blob(payload)
        self.assertEqual(list(conn.fetch({})), [])
        self.assertEqual(conn.stats["skipped"]["binary"], 1)

    def test_encoding_none_is_skipped_rather_than_indexed_empty(self) -> None:
        conn, _ = self.api_blob(json_response({"encoding": "none", "content": ""}))
        self.assertEqual(list(conn.fetch({})), [])
        self.assertEqual(conn.stats["skipped"]["unsupported_encoding"], 1)

    def test_undecodable_base64_is_a_failure_not_a_document(self) -> None:
        conn, _ = self.api_blob(json_response({"encoding": "base64", "content": "!!!!"}))
        self.assertEqual(list(conn.fetch({})), [])
        self.assertEqual(conn.stats["skipped"]["failed"], 1)

    def test_a_failed_fetch_does_not_record_the_sha(self) -> None:
        """The regression: a remembered sha means "unchanged" forever after."""
        conn, _ = self.api_blob(http_error(500, b"boom"))

        self.assertEqual(list(conn.fetch({})), [])

        self.assertEqual(conn.stats["skipped"]["failed"], 1)
        self.assertEqual(conn.stats["blob_shas"], {})
        self.assertFalse(conn.stats["files_complete"])
        self.assertNotIn("head_sha", conn.next_cursor({}))

    def test_a_rate_limit_during_a_blob_fetch_is_not_swallowed_as_a_file_failure(self) -> None:
        limited = http_error(403, b"rate limit", {"x-ratelimit-remaining": "0",
                                                  "x-ratelimit-reset": str(time.time() + 5)})
        conn, _ = self.api_blob(limited)
        conn.gh.max_rate_limit_waits = 0

        with self.assertRaises(RateLimitError):
            list(conn.fetch({}))

    def test_a_403_on_raw_falls_back_to_the_api(self) -> None:
        import base64 as b64

        payload = json_response({"encoding": "base64", "content": b64.b64encode(b"ok\n").decode()})
        conn, opener = self.api_blob(payload, raw=http_error(403, b"forbidden",
                                                             {"x-ratelimit-remaining": "9"}))
        self.assertEqual(list(conn.fetch({}))[0].text, "ok\n")
        self.assertEqual(self.waits, [])

    def test_raw_content_is_preferred_and_costs_no_api_call(self) -> None:
        conn, opener = self.api_blob(json_response({}), raw=text_response(b"from raw\n"))
        self.assertEqual(list(conn.fetch({}))[0].text, "from raw\n")
        self.assertFalse([u for u in opener.urls if "/git/blobs/" in u])


# ------------------------------------------------------------------ incremental


class IncrementalTestCase(GitHubTestCase):
    def build(self, *, head: str = HEAD, files: dict[str, bytes] | None = None,
              tree: dict[str, Any] | None = None) -> tuple[GitHubConnector, FakeOpener]:
        opener = self.repo_opener(head=head)
        opener.route(f"{API}/git/trees/", json_response(tree or TREE_TWO_FILES), repeat=True)
        for path, body in (files or {}).items():
            opener.route(f"/{path}", text_response(body), repeat=True)
        return self.connector(opener, resources=("files",)), opener

    def test_an_unchanged_head_skips_the_tree_call_entirely(self) -> None:
        conn, opener = self.build()
        cursor = {"head_sha": HEAD, "blob_shas": {"README.md": "1" * 40}}

        docs = list(conn.fetch(cursor))

        self.assertEqual(docs, [])
        self.assertFalse([u for u in opener.urls if "/git/trees/" in u])
        self.assertEqual(conn.stats["skipped"]["head_unchanged"], 1)
        self.assertEqual(conn.next_cursor(dict(cursor))["head_sha"], HEAD)

    def test_an_unchanged_head_with_no_remembered_blobs_still_walks(self) -> None:
        conn, opener = self.build(files={"README.md": b"a\n", "src/app.py": b"b\n"})
        docs = list(conn.fetch({"head_sha": HEAD}))
        self.assertEqual(len(docs), 2)

    def test_an_unchanged_blob_sha_costs_no_fetch(self) -> None:
        conn, opener = self.build(files={"src/app.py": b"b\n"})
        cursor = {"head_sha": OLD_HEAD, "blob_shas": {"README.md": "1" * 40}}

        docs = list(conn.fetch(cursor))

        self.assertEqual([d.metadata["path"] for d in docs], ["src/app.py"])
        self.assertEqual(conn.stats["skipped"]["blob_unchanged"], 1)
        self.assertNotIn("README.md", " ".join(opener.urls))
        self.assertEqual(conn.stats["blob_shas"]["README.md"], "1" * 40)

    def test_force_refetch_ignores_the_remembered_shas_and_then_clears_itself(self) -> None:
        conn, _ = self.build(files={"README.md": b"a\n", "src/app.py": b"b\n"})
        cursor = {"head_sha": OLD_HEAD, "blob_shas": {"README.md": "1" * 40},
                  "force_refetch": True}

        docs = list(conn.fetch(cursor))

        self.assertEqual(len(docs), 2)
        self.assertNotIn("force_refetch", conn.next_cursor(dict(cursor)))

    def test_a_force_push_to_an_unrelated_sha_refetches_what_moved(self) -> None:
        """The sha is not an ancestor of anything; only the blob shas matter."""
        conn, opener = self.build(files={"src/app.py": b"b\n"})
        cursor = {"head_sha": "f" * 40, "blob_shas": {"README.md": "1" * 40}}

        docs = list(conn.fetch(cursor))

        self.assertEqual([d.metadata["path"] for d in docs], ["src/app.py"])
        self.assertTrue([u for u in opener.urls if "/git/trees/" in u])

    def test_a_commit_response_without_a_sha_is_an_error_not_a_poisoned_cursor(self) -> None:
        """Falling back to the ref name made every later run look unchanged."""
        opener = self.repo_opener()
        opener.routes = [r for r in opener.routes if "/commits/" not in r.match]
        opener.route(f"{API}/commits/", json_response({"message": "no commit"}))
        conn = self.connector(opener, resources=("files",))

        with self.assertRaises(GitHubError) as caught:
            list(conn.fetch({}))

        self.assertIn("no commit sha", str(caught.exception))
        self.assertEqual(conn.next_cursor({}), {"last_stats": {"counts": {}, "skipped": {},
                                                               "files_complete": False}})

    def test_a_run_that_dies_early_does_not_carry_the_previous_head_forward(self) -> None:
        conn, opener = self.build(files={"README.md": b"a\n", "src/app.py": b"b\n"})
        list(conn.fetch({}))
        self.assertEqual(conn.stats["head_sha"], HEAD)

        opener.exact(API, http_error(500, b"boom"))
        opener.routes.insert(0, opener.routes.pop())  # the new exact route wins
        with self.assertRaises(GitHubError):
            list(conn.fetch({}))

        self.assertEqual(conn.next_cursor({}).get("head_sha"), None)

    def test_two_runs_through_the_state_store_report_nothing_changed(self) -> None:
        state = MemoryStateStore()
        conn, opener = self.build(files={"README.md": b"a\n", "src/app.py": b"b\n"})

        first = conn.run(state)
        second = conn.run(state)

        self.assertEqual((first.delta.new, first.delta.changed), (2, 0))
        self.assertEqual(len(second.documents), 0)
        self.assertEqual(second.delta.new + second.delta.changed, 0)
        self.assertEqual(state.get(conn.key)["head_sha"], HEAD)

    def test_a_cursor_that_is_not_a_dict_is_survivable(self) -> None:
        conn, _ = self.build(files={"README.md": b"a\n", "src/app.py": b"b\n"})
        self.assertEqual(len(list(conn.fetch(None))), 2)  # type: ignore[arg-type]

    def test_a_corrupt_blob_map_is_ignored_rather_than_raised(self) -> None:
        conn, _ = self.build(files={"README.md": b"a\n", "src/app.py": b"b\n"})
        self.assertEqual(len(list(conn.fetch({"blob_shas": "not a map"}))), 2)

    def test_the_connector_does_not_claim_to_enumerate_its_source(self) -> None:
        """It short-circuits and caps; the base class must not infer deletions."""
        self.assertFalse(GitHubConnector(owner=OWNER, repo=REPO).enumerates_source)


# ------------------------------------------------------------------- documents


class DocumentTestCase(GitHubTestCase):
    def test_the_repository_overview_carries_provenance(self) -> None:
        opener = self.repo_opener()
        conn = self.connector(opener, resources=("repo",))

        doc = list(conn.fetch({}))[0]

        self.assertEqual(doc.external_id, f"{SLUG}#repo")
        self.assertEqual(doc.metadata["commit"], HEAD)
        self.assertEqual(doc.metadata["authority"], 1.2)
        self.assertIn("Primary language: Python", doc.text)
        self.assertIn("License: MIT", doc.text)

    def test_the_repository_overview_is_redacted_like_every_other_body(self) -> None:
        meta = dict(REPO_META, description=f"deploy with {TOKEN}")
        conn = self.connector(self.repo_opener(meta=meta), resources=("repo",))

        doc = list(conn.fetch({}))[0]

        self.assertNotIn(TOKEN, doc.text)
        self.assertIn("<redacted:github-token>", doc.text)

    def test_a_repository_with_no_topics_or_license_still_renders(self) -> None:
        meta = {"default_branch": "main"}
        conn = self.connector(self.repo_opener(meta=meta), resources=("repo",))
        doc = list(conn.fetch({}))[0]
        self.assertIn("Topics: none", doc.text)
        self.assertEqual(doc.uri, f"https://github.com/{SLUG}")

    def test_the_readme_is_pinned_to_the_commit_being_ingested(self) -> None:
        import base64 as b64

        opener = self.repo_opener()
        opener.route(f"{API}/readme",
                     json_response({"path": "docs/README.md", "sha": "d" * 40,
                                    "encoding": "base64",
                                    "content": b64.b64encode(b"# hi\n").decode()}))
        conn = self.connector(opener, resources=("readme",))

        doc = list(conn.fetch({}))[0]

        self.assertIn(f"ref={HEAD}", [u for u in opener.urls if "/readme" in u][0])
        self.assertEqual(doc.uri, f"https://github.com/{SLUG}/blob/{HEAD}/docs/README.md")
        self.assertEqual(doc.text, "# hi\n")

    def test_the_readme_id_is_stable_when_its_content_changes(self) -> None:
        """Keying it on the blob sha made every edit a new document."""
        import base64 as b64

        ids = []
        for sha, body in (("d" * 40, b"one\n"), ("e" * 40, b"two\n")):
            opener = self.repo_opener()
            opener.route(f"{API}/readme",
                         json_response({"path": "README.md", "sha": sha, "encoding": "base64",
                                        "content": b64.b64encode(body).decode()}))
            ids.append(list(self.connector(opener, resources=("readme",)).fetch({}))[0].external_id)
        self.assertEqual(ids[0], ids[1])

    def test_a_missing_readme_is_not_a_failed_run(self) -> None:
        opener = self.repo_opener()
        opener.route(f"{API}/readme", http_error(404, b'{"message": "Not Found"}'))
        self.assertEqual(list(self.connector(opener, resources=("readme",)).fetch({})), [])

    def test_a_binary_or_oversized_readme_is_skipped(self) -> None:
        import base64 as b64

        for content in (b64.b64encode(b"\x00\x01").decode(), "A" * 10_000):
            with self.subTest(content=content[:8]):
                opener = self.repo_opener()
                opener.route(f"{API}/readme",
                             json_response({"path": "README.md", "encoding": "base64",
                                            "content": content}))
                conn = self.connector(opener, resources=("readme",), max_file_bytes=100)
                self.assertEqual(list(conn.fetch({})), [])

    def test_a_readme_with_a_traversing_path_is_refused(self) -> None:
        import base64 as b64

        opener = self.repo_opener()
        opener.route(f"{API}/readme",
                     json_response({"path": "../../../etc/passwd", "encoding": "base64",
                                    "content": b64.b64encode(b"x\n").decode()}))
        self.assertEqual(list(self.connector(opener, resources=("readme",)).fetch({})), [])

    def test_issues_and_pulls_are_separable(self) -> None:
        page = [
            {"number": 1, "title": "an issue", "state": "open", "body": "b",
             "labels": [{"name": "bug"}], "user": {"login": "ann"}},
            {"number": 2, "title": "a pr", "state": "closed", "pull_request": {"url": "x"},
             "labels": None, "user": None},
        ]
        opener = self.repo_opener()
        opener.route(f"{API}/issues", json_response(page), repeat=True)

        issues = list(self.connector(opener, resources=("issues",)).fetch({}))
        pulls = list(self.connector(opener, resources=("pulls",)).fetch({}))

        self.assertEqual([d.external_id for d in issues], [f"{SLUG}#issue:1"])
        self.assertEqual([d.external_id for d in pulls], [f"{SLUG}#pr:2"])
        self.assertEqual(issues[0].metadata["labels"], ["bug"])
        self.assertEqual(pulls[0].metadata["labels"], [], "a null label list is not a crash")
        self.assertIn("(no description)", pulls[0].text)

    def test_an_issue_title_is_redacted_because_it_is_indexed_too(self) -> None:
        page = [{"number": 1, "title": f"leaked {TOKEN}", "body": "x", "state": "open"}]
        opener = self.repo_opener()
        opener.route(f"{API}/issues", json_response(page))

        doc = list(self.connector(opener, resources=("issues",)).fetch({}))[0]

        self.assertNotIn(TOKEN, doc.title)
        self.assertNotIn(TOKEN, doc.text)

    def test_the_issues_cursor_is_stamped_before_the_walk(self) -> None:
        opener = self.repo_opener()
        opener.route(f"{API}/issues", json_response([]))
        conn = self.connector(opener, resources=("issues",))

        list(conn.fetch({"issues_since": "2024-01-01T00:00:00Z"}))

        self.assertIn("since=2024-01-01", [u for u in opener.urls if "/issues" in u][0])
        self.assertRegex(conn.stats["issues_since"], r"^\d{4}-\d\d-\d\dT")

    def test_commits_become_documents(self) -> None:
        opener = self.repo_opener()
        opener.route(f"{API}/commits?", json_response(
            [{"sha": "c" * 40, "html_url": "https://github.com/x",
              "commit": {"message": "fix: thing\n\nbody", "author": {"name": "ann",
                                                                     "date": "2024-01-01"}}}]
        ))
        conn = self.connector(opener, resources=("commits",))

        doc = list(conn.fetch({}))[0]

        self.assertEqual(doc.external_id, f"{SLUG}#commit:{'c' * 40}")
        self.assertIn("fix: thing", doc.title)
        self.assertEqual(doc.metadata["author"], "ann")

    def test_a_commit_with_no_message_or_author_still_renders(self) -> None:
        opener = self.repo_opener()
        opener.route(f"{API}/commits?", json_response([{"sha": "c" * 40, "commit": None}]))
        doc = list(self.connector(opener, resources=("commits",)).fetch({}))[0]
        self.assertEqual(doc.metadata["author"], None)

    def test_releases_without_notes_are_dropped(self) -> None:
        opener = self.repo_opener()
        opener.route(f"{API}/releases", json_response(
            [{"tag_name": "v1", "body": "  "}, {"tag_name": "v2", "body": "notes", "name": "Two"}]
        ))
        docs = list(self.connector(opener, resources=("releases",)).fetch({}))

        self.assertEqual([d.external_id for d in docs], [f"{SLUG}#release:v2"])
        self.assertIn("notes", docs[0].text)


# ---------------------------------------------------------------- the whole run


class TokenNeverEscapesTestCase(GitHubTestCase):
    """One run, every emitting surface, one assertion: the token is not in it."""

    def build(self) -> tuple[GitHubConnector, FakeOpener]:
        import base64 as b64

        meta = dict(REPO_META, description=f"deploy with {TOKEN}")
        opener = self.repo_opener(meta=meta)
        readme = b64.b64encode(f"# use {TOKEN}\n".encode()).decode()
        opener.route(f"{API}/readme",
                     json_response({"path": "README.md", "sha": "d" * 40,
                                    "encoding": "base64", "content": readme}))
        opener.route(f"{API}/git/trees/", json_response(
            {"truncated": False, "tree": [blob_entry("config.yml", "1" * 40, size=40),
                                          blob_entry("broken.md", "2" * 40, size=10)]}
        ))
        opener.route(f"/{HEAD}/config.yml", text_response(f"token: {TOKEN}\n".encode()))
        # A server that echoes the credential back inside an error body.
        opener.route(f"/{HEAD}/broken.md",
                     http_error(500, json.dumps({"message": f"bad {TOKEN}"}).encode()))
        opener.route(f"{API}/git/blobs/", http_error(500, f"boom {TOKEN}".encode()), repeat=True)
        opener.route(f"{API}/issues", json_response(
            [{"number": 1, "title": f"see {TOKEN}", "body": f"here: {TOKEN}", "state": "open"}]
        ))
        return self.connector(opener, resources=("repo", "readme", "files", "issues"),
                              token=TOKEN), opener

    def test_no_emitted_surface_carries_the_token(self) -> None:
        conn, _ = self.build()
        state = MemoryStateStore()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            result = conn.run(state)

        emitted = json.dumps([asdict(d) for d in result.documents], default=str)
        haystacks = {
            "documents": emitted,
            "delta": json.dumps(result.delta.as_dict(), default=str),
            "cursor": json.dumps(result.cursor, default=str),
            "state": json.dumps(state.get(conn.key), default=str),
            "logs": stderr.getvalue(),
            "repr": f"{conn!r} {conn.gh!r} {conn.gh.http!r}",
            "stats": json.dumps(conn.stats, default=str),
        }
        for name, text in haystacks.items():
            with self.subTest(surface=name):
                self.assertNotIn(TOKEN, text)
                self.assertNotIn("Bearer ", text)

        self.assertTrue(result.documents, "the run must actually have produced something")
        self.assertIn("<redacted:github-token>", emitted, "redacted, not merely absent")

    def test_the_credential_still_reached_github_itself(self) -> None:
        conn, opener = self.build()
        with contextlib.redirect_stderr(io.StringIO()):
            conn.run(MemoryStateStore())

        authed = [r for r in opener.requests if header_of(r, "authorization")]
        self.assertTrue(authed)
        self.assertTrue(all("github" in (r.host or "") for r in authed))

    def test_a_failed_file_is_counted_and_the_run_survives(self) -> None:
        conn, _ = self.build()
        with contextlib.redirect_stderr(io.StringIO()):
            result = conn.run(MemoryStateStore())

        paths = [d.metadata.get("path") for d in result.documents]
        self.assertIn("config.yml", paths)
        self.assertNotIn("broken.md", paths)
        self.assertEqual(conn.stats["skipped"]["failed"], 1)


if __name__ == "__main__":
    unittest.main()
