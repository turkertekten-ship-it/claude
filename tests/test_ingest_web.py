"""Tests for the web connector.

Nothing here opens a socket: `HttpClient._opener` is swapped for a fake that
serves a small in-memory site and 404s anything the test did not plan for. The
retry policy is one attempt with zero backoff and `time.sleep` is mocked, so a
regression shows up as a failed assertion rather than a slow suite.

Three properties are worth more than the mapping itself. Redaction has to reach
*every* indexed field - body, title, headings, description - because a token in
a page title is as leaked as a token in its body. The seed URL has to be
stripped of credentials before it becomes the state-store key and the
`crawl_seed` stamp, because both are written to disk. And a crawl that produced
nothing has to arrive as a failure with a reason, not as a successful ingest of
zero documents: the second is indistinguishable from a site that is genuinely
empty, and the incremental accounting treats those two very differently.
"""

from __future__ import annotations

import email.message
import io
import unittest
import urllib.error
from dataclasses import dataclass, field
from typing import Any
from unittest import mock

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.web import (
    DEFAULT_AUTHORITY,
    MAX_HEADINGS,
    MAX_TITLE_CHARS,
    CrawlProducedNothing,
    WebConnector,
)
from oodarag.util.http import HttpClient, RetryPolicy

SITE = "https://example.com"
TOKEN = "ghp_" + "A" * 36


# ----------------------------------------------------------------------- fakes


@dataclass
class Reply:
    body: bytes = b""
    status: int = 200
    ctype: str = "text/html; charset=utf-8"
    etag: str = ""
    headers: dict[str, str] = field(default_factory=dict)


def message(headers: dict[str, str]) -> email.message.Message:
    msg = email.message.Message()
    for key, value in headers.items():
        msg[key] = value
    return msg


class FakeResponse:
    def __init__(self, reply: Reply, url: str) -> None:
        self.status = reply.status
        headers = {"Content-Type": reply.ctype, "Content-Length": str(len(reply.body))}
        if reply.etag:
            headers["ETag"] = reply.etag
        headers.update(reply.headers)
        self.headers = message(headers)
        self._url = url
        self._stream = io.BytesIO(reply.body)

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


class FakeOpener:
    """Serves a site graph, and honours If-None-Match so a second crawl of an
    unchanged site takes the 304 path the client is built for."""

    def __init__(self, site: dict[str, Reply]) -> None:
        self.site = site
        self.requests: list[str] = []

    def open(self, req: Any, timeout: float | None = None) -> FakeResponse:
        url = req.full_url
        self.requests.append(url)
        reply = self.site.get(url)
        if reply is None:
            raise self._error(url, 404, b"not found")
        inm = next((v for k, v in req.headers.items() if k.lower() == "if-none-match"), "")
        if reply.etag and inm == reply.etag:
            raise self._error(url, 304, b"")
        if reply.status >= 400:
            raise self._error(url, reply.status, reply.body)
        return FakeResponse(reply, url)

    @staticmethod
    def _error(url: str, code: int, body: bytes) -> urllib.error.HTTPError:
        return urllib.error.HTTPError(url, code, f"status {code}", message({}), io.BytesIO(body))


# -------------------------------------------------------------------- fixtures


def html(name: str, links: tuple[str, ...] = (), *, words: int = 60, title: str = "",
         description: str = "", headings: tuple[str, ...] = (), body_extra: str = "") -> bytes:
    filler = " ".join(f"{name}-word{i}" for i in range(words))
    anchors = "".join(f'<a href="{u}">go {i}</a> ' for i, u in enumerate(links))
    head = f"<title>{title or name}</title>"
    if description:
        head += f'<meta name="description" content="{description}">'
    marks = "".join(f"<h2>{h}</h2>" for h in headings)
    return (
        f"<html><head>{head}</head><body><main>{marks}<p>{filler}</p>"
        f"<p>{body_extra}</p><p>{anchors}</p></main></body></html>"
    ).encode()


def page(name: str, links: tuple[str, ...] = (), **kw: Any) -> Reply:
    return Reply(body=html(name, links, **kw))


def small_site() -> dict[str, Reply]:
    return {
        f"{SITE}/": page("seed", ("/a", "/b")),
        f"{SITE}/a": page("a"),
        f"{SITE}/b": page("b"),
    }


class WebConnectorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch("time.sleep")
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)
        self.opener: FakeOpener | None = None

    def client(self, **kw: Any) -> HttpClient:
        kw.setdefault("retry", RetryPolicy(attempts=1, base_delay=0.0, max_delay=0.0, jitter=0.0))
        kw.setdefault("rate_per_sec", 1_000_000.0)
        kw.setdefault("burst", 10_000)
        return HttpClient(**kw)

    def connector(self, site: dict[str, Reply], *, seeds: Any = None,
                  client: HttpClient | None = None, **options: Any) -> WebConnector:
        http = client or self.client()
        self.opener = FakeOpener(site)
        http._opener = self.opener
        options.setdefault("obey_robots", False)
        return WebConnector(seeds if seeds is not None else [f"{SITE}/"], client=http, **options)


class MappingTestCase(WebConnectorTestCase):
    def test_a_crawl_becomes_documents_with_provenance(self) -> None:
        result = self.connector(small_site()).run()
        self.assertEqual(result.delta.new, 3)
        by_id = {d.external_id: d for d in result.documents}
        self.assertEqual(set(by_id), {f"{SITE}/", f"{SITE}/a", f"{SITE}/b"})
        seed = by_id[f"{SITE}/"]
        self.assertEqual(seed.source_system, "web")
        self.assertEqual(seed.uri, f"{SITE}/")
        self.assertEqual(seed.title, "seed")
        self.assertIn("seed-word0", seed.text)
        self.assertEqual(seed.metadata["status"], 200)
        self.assertEqual(seed.metadata["depth"], 0)
        self.assertEqual(seed.metadata["content_type"], "text/html")
        self.assertEqual(seed.metadata["crawl_seed"], f"{SITE}/")
        self.assertGreater(seed.metadata["word_count"], 40)
        self.assertGreater(seed.fetched_at, 0.0)

    def test_every_document_carries_the_authority_weight(self) -> None:
        result = self.connector(small_site()).run()
        self.assertTrue(result.documents)
        for document in result.documents:
            self.assertEqual(document.metadata["authority"], DEFAULT_AUTHORITY)

    def test_authority_defaults_below_one_and_can_be_raised(self) -> None:
        self.assertLess(DEFAULT_AUTHORITY, 1.0)
        trusted = self.connector(small_site(), authority=1.5)
        self.assertEqual(trusted.authority, 1.5)
        self.assertEqual(trusted.run().documents[0].metadata["authority"], 1.5)

    def test_an_unset_authority_does_not_become_none(self) -> None:
        """Config plumbing spells "unset" as None; None in the metadata is a
        TypeError inside the reranker, a long way from here."""
        connector = self.connector(small_site(), authority=None)
        self.assertEqual(connector.authority, DEFAULT_AUTHORITY)

    def test_the_description_falls_back_to_a_summary(self) -> None:
        site = {f"{SITE}/": page("seed", description="the declared description")}
        described = self.connector(site).run().documents[0]
        self.assertEqual(described.metadata["description"], "the declared description")
        summarized = self.connector({f"{SITE}/": page("seed")}).run().documents[0]
        self.assertTrue(summarized.metadata["description"].startswith("seed-word0"))

    def test_headings_are_capped(self) -> None:
        site = {f"{SITE}/": page("seed", headings=tuple(f"h{i}" for i in range(40)))}
        document = self.connector(site).run().documents[0]
        self.assertEqual(len(document.metadata["headings"]), MAX_HEADINGS)
        self.assertEqual(document.metadata["headings"][0], "h0")

    def test_a_page_sized_title_is_capped(self) -> None:
        site = {f"{SITE}/": page("seed", title="T" * 5000)}
        document = self.connector(site).run().documents[0]
        self.assertEqual(len(document.title), MAX_TITLE_CHARS)

    def test_a_titleless_page_falls_back_to_its_url(self) -> None:
        body = b"<html><body><main><p>" + b"word " * 80 + b"</p></main></body></html>"
        document = self.connector({f"{SITE}/": Reply(body=body)}).run().documents[0]
        self.assertEqual(document.title, f"{SITE}/")

    def test_a_seed_string_is_not_crawled_one_character_at_a_time(self) -> None:
        connector = self.connector(small_site(), seeds=f"{SITE}/")
        self.assertEqual(connector.config.seeds, [f"{SITE}/"])
        self.assertEqual(len(connector.run().documents), 3)


class RedactionTestCase(WebConnectorTestCase):
    """The docstring promises redaction; these pin it field by field."""

    def leaky_site(self) -> dict[str, Reply]:
        return {
            f"{SITE}/": page(
                "seed",
                title=f"deploy with {TOKEN}",
                description=f"use {TOKEN} to authenticate",
                headings=(f"step 1: export {TOKEN}",),
                body_extra=f"run: curl -H 'Authorization: token {TOKEN}' https://api.test",
            )
        }

    def test_a_credential_in_the_body_is_stripped(self) -> None:
        document = self.connector(self.leaky_site()).run().documents[0]
        self.assertNotIn(TOKEN, document.text)
        self.assertIn("<redacted:github-token>", document.text)

    def test_a_credential_in_the_title_is_stripped(self) -> None:
        document = self.connector(self.leaky_site()).run().documents[0]
        self.assertNotIn(TOKEN, document.title)
        self.assertIn("<redacted:github-token>", document.title)

    def test_a_credential_in_the_headings_and_description_is_stripped(self) -> None:
        document = self.connector(self.leaky_site()).run().documents[0]
        self.assertNotIn(TOKEN, document.metadata["description"])
        self.assertNotIn(TOKEN, " ".join(document.metadata["headings"]))

    def test_a_synthesised_description_is_redacted_too(self) -> None:
        """No declared description, so it is cut out of the body - which is
        where the credential is."""
        site = {f"{SITE}/": page("seed", body_extra=f"export TOKEN={TOKEN}", words=3)}
        document = self.connector(site, min_words=2).run().documents[0]
        self.assertNotIn(TOKEN, document.metadata["description"])
        self.assertIn("<redacted", document.metadata["description"])

    def test_no_indexed_field_carries_the_credential(self) -> None:
        """The end-to-end version: nothing that reaches the index has it."""
        document = self.connector(self.leaky_site()).run().documents[0]
        blob = repr((document.title, document.text, document.metadata))
        self.assertNotIn(TOKEN, blob)

    def test_a_credential_in_the_seed_url_never_reaches_the_state_key(self) -> None:
        seed = f"https://user:{TOKEN}@example.com/"
        connector = self.connector(small_site(), seeds=[seed])
        self.assertNotIn(TOKEN, connector.key)
        self.assertNotIn(TOKEN, connector.seed_label)
        self.assertEqual(connector.key, f"web:{SITE}/")

    def test_a_credential_in_the_seed_url_never_reaches_a_document(self) -> None:
        seed = f"https://user:{TOKEN}@example.com/"
        result = self.connector(small_site(), seeds=[seed]).run()
        self.assertTrue(result.documents)
        for document in result.documents:
            self.assertNotIn(TOKEN, document.metadata["crawl_seed"])

    def test_an_unparseable_seed_still_loses_its_userinfo(self) -> None:
        """`urlsplit` raises on this one, so both `normalize_url` and
        `redact_url` hand it back untouched - and the key would have carried a
        live token into the state file."""
        connector = self.connector(small_site(), seeds=[f"https://user:{TOKEN}@[::1/x"])
        self.assertNotIn(TOKEN, connector.key)
        self.assertNotIn(TOKEN, connector.seed_label)
        self.assertIn("<redacted>@", connector.key)


class EmptyCrawlTestCase(WebConnectorTestCase):
    """A crawl that produced nothing says why, and the delta carries it."""

    def test_a_dead_host_is_a_failed_delta_not_an_empty_success(self) -> None:
        site = {f"{SITE}/": Reply(status=500, body=b"kaboom")}
        result = self.connector(site).run()
        self.assertEqual(result.documents, [])
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.delta.touched, 0)
        self.assertIn("CrawlProducedNothing", result.delta.errors[0])
        self.assertIn("http_500", result.delta.errors[0])

    def test_a_robots_denied_crawl_says_robots(self) -> None:
        site = {
            f"{SITE}/robots.txt": Reply(body=b"User-agent: *\nDisallow: /", ctype="text/plain"),
            f"{SITE}/": page("seed"),
        }
        result = self.connector(site, obey_robots=True).run()
        self.assertEqual(result.delta.failed, 1)
        self.assertIn("robots=1", result.delta.errors[0])

    def test_a_connector_with_no_seeds_fails_rather_than_succeeding_emptily(self) -> None:
        connector = self.connector(small_site(), seeds=[])
        self.assertEqual(connector.key, "web:empty")
        result = connector.run()
        self.assertEqual(result.delta.failed, 1)
        self.assertIn("crawl produced no documents", result.delta.errors[0])

    def test_the_exception_is_raised_out_of_fetch(self) -> None:
        site = {f"{SITE}/": Reply(status=500, body=b"kaboom")}
        connector = self.connector(site)
        with self.assertRaises(CrawlProducedNothing):
            list(connector.fetch({}))

    def test_a_failed_crawl_does_not_forget_the_previous_run(self) -> None:
        state = MemoryStateStore()
        good = self.connector(small_site()).run(state=state)
        dead = self.connector({f"{SITE}/": Reply(status=500)}).run(state=state)
        self.assertEqual(dead.cursor["hashes"], good.cursor["hashes"])
        self.assertEqual(dead.cursor["removed_last_run"], [])
        self.assertFalse(dead.cursor["complete_run"])

    def test_an_all_304_crawl_is_an_honest_empty_success(self) -> None:
        """The one empty crawl that is not a failure: every page came back "not
        modified", which is the conditional-GET path working as designed."""
        site = {
            f"{SITE}/": Reply(body=html("seed", ("/a",)), etag='"v1"'),
            f"{SITE}/a": Reply(body=html("a"), etag='"v2"'),
        }
        http = self.client()
        first = self.connector(site, client=http).run()
        self.assertEqual(first.delta.new, 2)
        again = WebConnector([f"{SITE}/"], client=http, obey_robots=False)
        second = again.run()
        self.assertEqual(second.documents, [])
        self.assertEqual(second.delta.failed, 0, "a fully cached crawl is not a failure")
        # One, not two: a 304 carries no body, so the seed contributes no links
        # and discovery stops there. That belongs to the crawler; what matters
        # here is that the connector reports it as an empty success.
        self.assertEqual(again.last_report["skipped"].get("not_modified"), 1)


class IncrementalTestCase(WebConnectorTestCase):
    def test_an_unchanged_site_reports_unchanged(self) -> None:
        state = MemoryStateStore()
        self.connector(small_site()).run(state=state)
        result = self.connector(small_site()).run(state=state)
        self.assertEqual((result.delta.new, result.delta.unchanged), (0, 3))
        self.assertEqual(result.documents, [])

    def test_an_edited_page_is_the_only_one_re_emitted(self) -> None:
        state = MemoryStateStore()
        self.connector(small_site()).run(state=state)
        edited = small_site()
        edited[f"{SITE}/a"] = page("a", body_extra="a brand new paragraph of prose")
        result = self.connector(edited).run(state=state)
        self.assertEqual((result.delta.changed, result.delta.unchanged), (1, 2))
        self.assertEqual([d.external_id for d in result.documents], [f"{SITE}/a"])

    def test_a_page_that_disappears_is_not_reported_as_deleted(self) -> None:
        """A crawl is a sample: 404 today, back tomorrow, and the frontier never
        promised to reach it in the first place."""
        state = MemoryStateStore()
        self.connector(small_site()).run(state=state)
        gone = small_site()
        del gone[f"{SITE}/b"]
        result = self.connector(gone).run(state=state)
        self.assertEqual(result.cursor["removed_last_run"], [])
        self.assertIn(f"{SITE}/b", result.cursor["hashes"])

    def test_the_connector_does_not_claim_to_enumerate_its_source(self) -> None:
        self.assertFalse(WebConnector([f"{SITE}/"]).enumerates_source)

    def test_the_cursor_carries_the_crawl_report(self) -> None:
        state = MemoryStateStore()
        result = self.connector(small_site()).run(state=state)
        stored = state.get(result.delta.source_key)
        self.assertEqual(stored["last_report"]["fetched"], 3)
        self.assertEqual(stored["last_report"]["stopped_by"], "frontier_exhausted")
        self.assertGreater(stored["last_crawl_at"], 0.0)

    def test_a_limited_run_still_records_a_true_report(self) -> None:
        """The regression: `last_report` was assigned after the crawl loop, so a
        run that stopped early stored an empty report and the next run's cursor
        claimed the crawl had never happened."""
        state = MemoryStateStore()
        result = self.connector(small_site(), max_pages=3).run(state=state, limit=1)
        self.assertEqual(len(result.documents), 1)
        self.assertFalse(result.cursor["complete_run"])
        self.assertEqual(result.cursor["last_report"]["stopped_by"], "abandoned")
        self.assertGreaterEqual(result.cursor["last_report"]["fetched"], 1)

    def test_a_limited_run_does_not_lose_the_pages_it_skipped(self) -> None:
        state = MemoryStateStore()
        full = self.connector(small_site()).run(state=state)
        self.connector(small_site()).run(state=state, limit=1)
        self.assertEqual(state.get(full.delta.source_key)["hashes"], full.cursor["hashes"])

    def test_budgets_reach_the_crawl_config(self) -> None:
        connector = self.connector(small_site(), max_pages=1, max_depth=0)
        self.assertEqual(connector.config.max_pages, 1)
        result = connector.run()
        self.assertEqual(len(result.documents), 1)


if __name__ == "__main__":
    unittest.main()
