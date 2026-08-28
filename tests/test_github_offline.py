"""GitHub connector against a stand-in API, with no network or token.

The live blind test proves the connector reads the real GitHub correctly. It
cannot prove what happens on the paths GitHub will not produce on demand:
pagination boundaries, a truncated tree, a rate-limited response, raw returning
404 so the blob endpoint has to take over. Those are served here.
"""

from __future__ import annotations

import base64
import json
import unittest

from oodarag.ingest.base import Connector

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.github import GitHubClient, GitHubConnector
from oodarag.util.http import HttpClient, RetryPolicy
from tests.support.httpserver import Route, TestSite
from tests.test_dates import utc_epoch

SLUG = "acme/widgets"
HEAD = "a" * 40

FILES = {
    "README.md": "# Widgets\n\nA library for widgets.",
    "src/widgets/core.py": "def build(spec):\n    return spec\n",
    "src/widgets/util.py": "SECRET = 'ghp_" + "Z9y8X7w6V5u4T3s2R1q0" + "'\n",
    "tests/test_core.py": "def test_build():\n    assert True\n",
    "docs/guide.md": "# Guide\n\nHow to use widgets.",
    "package-lock.json": '{"lockfileVersion": 3}',   # excluded: lockfile
    "assets/logo.png": "\x89PNG binary-ish",          # excluded: not text
    "node_modules/dep/index.js": "module.exports = 1", # excluded: vendored
}


def _json_route(payload) -> Route:
    return Route(body=json.dumps(payload), content_type="application/json")


def build_api_routes(*, truncated: bool = False, raw_404: set[str] | None = None) -> dict[str, Route]:
    raw_404 = raw_404 or set()
    tree = [
        {"path": path, "type": "blob", "sha": f"blob{i:036d}", "size": len(body)}
        for i, (path, body) in enumerate(FILES.items())
    ]
    tree.append({"path": "src", "type": "tree", "sha": "t" * 40})

    routes: dict[str, Route] = {
        f"/repos/{SLUG}": _json_route({
            "full_name": SLUG, "description": "Widget library", "default_branch": "main",
            "language": "Python", "topics": ["widgets", "python"],
            "license": {"spdx_id": "MIT"}, "stargazers_count": 42, "forks_count": 7,
            "open_issues_count": 3, "html_url": f"https://github.com/{SLUG}",
            "created_at": "2024-01-01T00:00:00Z", "pushed_at": "2026-08-01T00:00:00Z",
        }),
        f"/repos/{SLUG}/commits/main": _json_route({"sha": HEAD}),
        f"/repos/{SLUG}/readme": _json_route({
            "path": "README.md", "sha": "readmesha",
            "content": base64.b64encode(FILES["README.md"].encode()).decode(),
        }),
        f"/repos/{SLUG}/git/trees/{HEAD}": _json_route({"tree": tree, "truncated": truncated}),
    }
    for i, (path, body) in enumerate(FILES.items()):
        blob_sha = f"blob{i:036d}"
        if path in raw_404:
            routes[f"/{SLUG}/{HEAD}/{path}"] = Route(body="", status=404)
            routes[f"/repos/{SLUG}/git/blobs/{blob_sha}"] = _json_route({
                "encoding": "base64", "content": base64.b64encode(body.encode()).decode(),
            })
        else:
            routes[f"/{SLUG}/{HEAD}/{path}"] = Route(body=body, content_type="text/plain")
    return routes


def make_connector(site: TestSite, **kwargs) -> GitHubConnector:
    client = HttpClient(rate_per_sec=200, retry=RetryPolicy(attempts=3, base_delay=0.01))
    gh = GitHubClient(token="test-token", client=client, api_root=site.origin)
    return GitHubConnector(owner="acme", repo="widgets", ref="main",
                           gh=gh, raw_root=site.origin, **kwargs)


class GitHubOfflineTest(unittest.TestCase):
    def _run(self, routes=None, state=None, **kwargs):
        site = TestSite(routes if routes is not None else build_api_routes())
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        connector = make_connector(site, **kwargs)
        return connector, connector.run(state or MemoryStateStore()), site

    def test_yields_expected_document_kinds(self):
        connector, result, _ = self._run()
        kinds = {}
        for doc in result.documents:
            kinds[doc.metadata["kind"]] = kinds.get(doc.metadata["kind"], 0) + 1
        self.assertEqual(kinds.get("repo"), 1)
        self.assertEqual(kinds.get("readme"), 1)
        self.assertEqual(kinds.get("file"), 5, f"unexpected file set: {kinds}")

    def test_excludes_lockfiles_vendored_and_binary_paths(self):
        _, result, _ = self._run()
        paths = {d.metadata["path"] for d in result.documents if d.metadata["kind"] == "file"}
        self.assertEqual(paths, {"README.md", "src/widgets/core.py", "src/widgets/util.py",
                                 "tests/test_core.py", "docs/guide.md"})
        for excluded in ("package-lock.json", "assets/logo.png", "node_modules/dep/index.js"):
            self.assertNotIn(excluded, paths)

    def test_secrets_in_source_are_redacted(self):
        _, result, _ = self._run()
        util = next(d for d in result.documents if d.metadata.get("path") == "src/widgets/util.py")
        self.assertNotIn("ghp_Z9y8X7w6V5u4T3s2R1q0", util.text)
        self.assertIn("<redacted:github-token>", util.text)

    def test_permalinks_pin_the_head_sha(self):
        _, result, _ = self._run()
        for doc in result.documents:
            if doc.metadata["kind"] == "file":
                self.assertEqual(
                    doc.uri,
                    f"https://github.com/{SLUG}/blob/{HEAD}/{doc.metadata['path']}",
                )

    def test_raw_404_falls_back_to_the_blob_api(self):
        routes = build_api_routes(raw_404={"src/widgets/core.py"})
        _, result, site = self._run(routes)
        core = next(d for d in result.documents if d.metadata.get("path") == "src/widgets/core.py")
        self.assertEqual(core.text, FILES["src/widgets/core.py"])
        self.assertIn(f"/repos/{SLUG}/git/blobs/blob{1:036d}", site.fetched_paths())

    def test_truncated_tree_is_recorded_not_swallowed(self):
        connector, _, _ = self._run(build_api_routes(truncated=True))
        self.assertEqual(connector.stats["skipped"].get("tree_truncated"), 1,
                         "a truncated tree must be reported: results are incomplete")

    def test_unchanged_blob_shas_are_not_refetched(self):
        state = MemoryStateStore()
        site = TestSite(build_api_routes())
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)

        first = make_connector(site)
        first_result = first.run(state)
        self.assertGreater(len(first_result.documents), 3)

        # Force the file walk to run again by clearing only the head-sha cursor,
        # so blob-level skipping is what is under test rather than the head
        # short circuit that would otherwise hide it.
        cursor = state.get(first.key)
        cursor.pop("head_sha")
        state.set(first.key, cursor)

        raw_before = len([p for p in site.requests if p[1].startswith(f"/{SLUG}/{HEAD}/")])
        second = make_connector(site)
        second_result = second.run(state)
        raw_after = len([p for p in site.requests if p[1].startswith(f"/{SLUG}/{HEAD}/")])

        self.assertEqual(raw_after, raw_before, "unchanged blobs were re-downloaded")
        self.assertEqual(second.stats["skipped"].get("blob_unchanged"), 5)
        self.assertEqual(len(second_result.documents), 0)

    def test_changed_blob_is_refetched_and_reported_as_changed(self):
        state = MemoryStateStore()
        routes = build_api_routes()
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        make_connector(site).run(state)

        # Same path, new blob sha and new body: the shape of a real commit.
        new_tree = json.loads(routes[f"/repos/{SLUG}/git/trees/{HEAD}"].body)
        for entry in new_tree["tree"]:
            if entry["path"] == "docs/guide.md":
                entry["sha"] = "changedsha"
                break
        site.add(f"/repos/{SLUG}/git/trees/{HEAD}", _json_route(new_tree))
        site.add(f"/{SLUG}/{HEAD}/docs/guide.md",
                 Route(body="# Guide\n\nCompletely rewritten.", content_type="text/plain"))
        cursor = state.get(f"github:{SLUG}")
        cursor.pop("head_sha")
        state.set(f"github:{SLUG}", cursor)

        second = make_connector(site)
        result = second.run(state)
        self.assertEqual(len(result.documents), 1)
        self.assertEqual(result.delta.changed, 1)
        self.assertEqual(result.delta.new, 0)
        self.assertIn("Completely rewritten", result.documents[0].text)

    def test_rate_limited_response_is_retried_after_the_reset(self):
        import time

        routes = build_api_routes()
        reset_at = str(int(time.time()) + 1)

        def limited(hits: int) -> Route | None:
            if hits == 1:
                return Route(body='{"message":"rate limited"}', status=403,
                             content_type="application/json",
                             headers={"x-ratelimit-remaining": "0",
                                      "x-ratelimit-reset": reset_at})
            return None

        original = routes[f"/repos/{SLUG}"]
        routes[f"/repos/{SLUG}"] = Route(
            body=original.body, content_type=original.content_type, dynamic=limited,
        )
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        connector = make_connector(site)
        result = connector.run(MemoryStateStore())
        self.assertEqual(result.delta.failed, 0, result.delta.errors)
        self.assertGreater(len(result.documents), 3)
        self.assertEqual(site.hits[f"/repos/{SLUG}"], 2, "403 rate limit was not retried")

    def test_a_permission_403_fails_fast_and_is_not_retried(self):
        """Only rate-limit 403s are retryable. A real access denial must not
        burn four attempts and the backoff between them."""
        routes = build_api_routes()
        routes[f"/repos/{SLUG}"] = Route(
            body='{"message":"Must have admin rights to Repository."}',
            status=403, content_type="application/json",
        )
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        connector = make_connector(site)
        result = connector.run(MemoryStateStore())
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(site.hits[f"/repos/{SLUG}"], 1,
                         "a permission 403 was retried as if it were a rate limit")

    def test_pagination_walks_every_page_of_issues(self):
        routes = build_api_routes()
        page_one = [{"number": n, "title": f"Issue {n}", "state": "open", "body": f"body {n}",
                     "user": {"login": "alice"}, "labels": [{"name": "bug"}], "comments": 0,
                     "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-02T00:00:00Z",
                     "html_url": f"https://github.com/{SLUG}/issues/{n}"} for n in range(1, 4)]
        page_two = [{"number": n, "title": f"Issue {n}", "state": "closed", "body": f"body {n}",
                     "user": {"login": "bob"}, "labels": [], "comments": 2,
                     "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-03T00:00:00Z",
                     "html_url": f"https://github.com/{SLUG}/issues/{n}"} for n in range(4, 6)]
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        site.add(f"/repos/{SLUG}/issues", Route(
            body=json.dumps(page_one), content_type="application/json",
            headers={"Link": f'<{site.origin}/repos/{SLUG}/issues?page=2>; rel="next"'},
        ))
        site.add(f"/repos/{SLUG}/issues?page=2",
                 Route(body=json.dumps(page_two), content_type="application/json"))

        connector = make_connector(site, resources=("issues",))
        result = connector.run(MemoryStateStore())
        numbers = sorted(d.metadata["number"] for d in result.documents)
        self.assertEqual(numbers, [1, 2, 3, 4, 5], "pagination stopped early")
        self.assertEqual(connector.stats["counts"]["issues_and_pulls"], 5)

    def test_a_source_failure_is_reported_not_raised(self):
        routes = build_api_routes()
        routes[f"/repos/{SLUG}"] = Route(body='{"message":"Not Found"}', status=404,
                                         content_type="application/json")
        connector, result, _ = self._run(routes)
        self.assertEqual(result.documents, [])
        self.assertEqual(result.delta.failed, 1)
        self.assertTrue(any("404" in e for e in result.delta.errors), result.delta.errors)


class EveryGitHubDocumentKindCarriesItsOwnDateTest(unittest.TestCase):
    """Issues were one of four. The repo, each commit and each release also
    state a date, and all three filed it in metadata where nothing scores it.

    L43: when a fix applies to one member of a family, ask the question of
    every sibling before closing the cycle.
    """

    def _site(self, extra: dict[str, Route] | None = None) -> TestSite:
        routes = build_api_routes()
        routes.update(extra or {})
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        return site

    def test_the_repository_is_dated_by_its_last_push(self):
        site = self._site()
        docs = make_connector(site, resources=("repo",)).run(MemoryStateStore()).documents
        self.assertEqual(len(docs), 1)
        # The fixture's own pushed_at, read back from the route rather than
        # restated here, so the two cannot drift apart.
        pushed = json.loads(site.server.routes[f"/repos/{SLUG}"].body)["pushed_at"]
        self.assertEqual(docs[0].source_updated_at, utc_epoch(pushed.rstrip("Z")))
        self.assertLess(docs[0].source_updated_at, docs[0].fetched_at)

    def test_a_commit_is_dated_by_when_it_was_authored(self):
        authored = "2026-05-06T07:08:09Z"
        commits = [{"sha": "c" * 40, "html_url": f"https://github.com/{SLUG}/commit/{'c'*40}",
                    "commit": {"message": "Bound the crawler by wall clock as well as pages",
                               "author": {"name": "alice", "date": authored}}}]
        site = self._site({f"/repos/{SLUG}/commits": Route(
            body=json.dumps(commits), content_type="application/json")})
        docs = make_connector(site, resources=("commits",)).run(MemoryStateStore()).documents
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].source_updated_at, utc_epoch(authored.rstrip("Z")),
                         "the commit stated its date and the connector discarded it")

    def test_a_release_is_dated_by_its_publication(self):
        published = "2026-04-05T06:07:08Z"
        releases = [{"tag_name": "v2.0.0", "name": "Widgets 2.0",
                     "body": "Budgets now bound fetches rather than accepted pages.",
                     "html_url": f"https://github.com/{SLUG}/releases/tag/v2.0.0",
                     "draft": False, "prerelease": False,
                     "published_at": published}]
        site = self._site({f"/repos/{SLUG}/releases": Route(
            body=json.dumps(releases), content_type="application/json")})
        docs = make_connector(site, resources=("releases",)).run(MemoryStateStore()).documents
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].source_updated_at, utc_epoch(published.rstrip("Z")),
                         "the release stated its date and the connector discarded it")


if __name__ == "__main__":
    unittest.main()


class IssueDateReachesRetrievalTest(unittest.TestCase):
    """A GitHub issue's real date was discarded before it could be scored.

    The connector reads `updated_at` from the API and stores it in metadata, but
    `Document.updated_at` came from `fetched_at` for every connector - so the
    reranker's recency factor scored an issue last touched in January as brand
    new, because it had been fetched a moment ago. Measured before the fix:
    recency 0.99999998. After: 0.520, for an eight-month-old issue.

    That is also why recency moved nothing on either eval corpus (L43): every
    document in a run shared one fetch time, making the factor a constant.

    This carries the connector's real output through indexing to retrieval, so
    the shape under test is the connector's rather than one invented here.
    """

    def _issue_documents(self):
        routes = build_api_routes()
        issues = [{"number": 1, "title": "Crawler runs forever on a cyclic site",
                   "state": "open",
                   "body": "The crawler follows a redirect loop and never stops. "
                           "Budgets should bound requests, bytes and wall clock.",
                   "user": {"login": "alice"}, "labels": [{"name": "bug"}],
                   "comments": 2,
                   "created_at": "2026-01-01T00:00:00Z",
                   "updated_at": "2026-01-02T00:00:00Z",
                   "html_url": f"https://github.com/{SLUG}/issues/1"}]
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        site.add(f"/repos/{SLUG}/issues",
                 Route(body=json.dumps(issues), content_type="application/json"))
        connector = make_connector(site, resources=("issues",))
        return connector.run(MemoryStateStore()).documents

    def test_the_connector_parses_the_issue_date_it_was_given(self):
        """`source_updated_at` is the source's claim about its own content;
        `fetched_at` is when we asked. Conflating them is what made every
        document in a run equally fresh."""
        docs = self._issue_documents()
        self.assertTrue(docs)
        self.assertEqual(docs[0].metadata.get("updated_at"), "2026-01-02T00:00:00Z")
        self.assertIsNotNone(docs[0].source_updated_at,
                             "the connector read the date and threw it away")
        self.assertLess(docs[0].source_updated_at, docs[0].fetched_at)

    def test_an_absent_date_is_not_invented(self):
        """None means the source did not say, which is a different claim from
        "it changed now" - and the document then falls back to the fetch time
        rather than to zero.

        Asserted through the connector rather than against the parser: the
        parser is unit-tested in `tests/test_dates.py`, and what is at issue
        here is whether the connector passes the field along at all.
        """
        routes = build_api_routes()
        issues = [{"number": 2, "title": "Undated issue", "state": "open",
                   "body": "An issue whose payload carries no updated_at at all.",
                   "user": {"login": "bob"}, "labels": [], "comments": 0,
                   "html_url": f"https://github.com/{SLUG}/issues/2"}]
        site = TestSite(routes)
        site.__enter__()
        self.addCleanup(site.__exit__, None, None, None)
        site.add(f"/repos/{SLUG}/issues",
                 Route(body=json.dumps(issues), content_type="application/json"))
        docs = make_connector(site, resources=("issues",)).run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1)
        self.assertIsNone(docs[0].source_updated_at,
                          "a date the API never sent was invented")

    def test_an_issue_is_scored_on_its_own_date_not_the_fetch_time(self):
        from oodarag.pipeline import IndexPipeline
        from oodarag.retrieve.hybrid import HybridRetriever
        from oodarag.store.sqlite_store import SqliteStore

        store = SqliteStore(":memory:")
        self.addCleanup(store.close)
        pipeline = IndexPipeline(store)

        class _Stub(Connector):
            key = "gh"
            source_system = "github"

            def __init__(self, docs):
                self._docs = docs

            def fetch(self, cursor):
                yield from self._docs

        pipeline.run([_Stub(self._issue_documents())])
        retriever = HybridRetriever(store, pipeline.embedder)
        results, _ = retriever.retrieve("what stops a crawler running forever")
        self.assertTrue(results, "the issue was not retrieved at all")
        # The issue is months old. Scored from the fetch time it reads as
        # brand new - which is what it did before `source_updated_at` existed.
        recency = results[0].components["rerank_recency"]
        self.assertLess(recency, 0.9,
                        "the issue was scored as freshly updated, so its own "
                        "date was discarded in favour of the fetch time")
        self.assertGreater(recency, 0.0)

        doc = store.all_documents()[0]
        self.assertLess(doc.updated_at, doc.created_at,
                        "updated_at should be the issue's date, older than the fetch")
