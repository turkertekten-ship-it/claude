"""The GitHub connector, driven entirely from a routing table.

Not one request in this file leaves the process. That is partly because CI has
no egress, but mostly because the behaviour worth pinning down here is the
behaviour GitHub will not produce on demand: a tree the server truncated, a
`raw.githubusercontent.com` 404 that has to fall back to the blob API, a
`Link` header with the rels in an awkward order, a run that is cut short
half-way through a repository.

The connector's whole reason to exist is spending as few API calls as possible,
so several tests assert on *which* URLs were requested rather than on the
documents that came back. A connector that returns the right documents while
spending a call per file is a connector that stops working at 5,000 files.

The package's stated principle is "degrade, don't die"; the failure paths
(missing README, failed blob, malformed issue, poisoned cursor) get as much
room as the happy path.
"""

from __future__ import annotations

import base64
import json
import unittest

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.github import (
    API_ROOT,
    RAW_ROOT,
    GitHubClient,
    GitHubConnector,
    _next_link,
)
from oodarag.util.http import HttpClient, HttpError, Response, TransportError

OWNER = "acme"
REPO = "widget"
SLUG = f"{OWNER}/{REPO}"
API = f"{API_ROOT}/repos/{SLUG}"

# 40 hex characters, because the connector slices shas for log lines and a
# short stand-in would hide an off-by-one there.
HEAD = "3f7a1c9d" + "0" * 32
OLD_HEAD = "9b2e4d6a" + "1" * 32

# Shaped like a real personal access token so `redact_secrets` has to actually
# match it; a fixture like "SECRET123" would pass a redaction test that a live
# credential would sail through.
LEAKED_TOKEN = "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p"
LEAKED_AWS = "AKIA2E0PQRSTUVWX1234"


# --------------------------------------------------------------------- fixtures


class FakeHttp(HttpClient):
    """An `HttpClient` that answers from a dict instead of a socket.

    A route is keyed by full URL, falling back to the URL without its query
    string, so a test only spells out a query when the query is the thing under
    test. Values are `{"json": obj}` / `{"body": str|bytes}` with optional
    `status` and `headers`, or `{"raise": Exception}`. An unrouted URL is an
    `AssertionError` rather than a 404: a request the test did not anticipate is
    a finding, not a fixture.
    """

    def __init__(self, routes: dict | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.routes = dict(routes or {})
        self.requested: list[str] = []

    def request(self, method, url, *, headers=None, body=None, conditional=False,
                allow_status=()):
        self.requested.append(url)
        entry = self.routes.get(url)
        if entry is None:
            entry = self.routes.get(url.split("?", 1)[0])
        if entry is None:
            raise AssertionError(f"unrouted {method} {url}")
        if "raise" in entry:
            raise entry["raise"]
        status = entry.get("status", 200)
        payload = entry.get("body")
        if payload is None:
            payload = json.dumps(entry.get("json", {}))
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        hdrs = {"content-type": "application/json; charset=utf-8"}
        hdrs.update(entry.get("headers", {}))
        if status >= 400 and status not in allow_status:
            raise HttpError(status, url, payload.decode("utf-8", "replace"), hdrs)
        return Response(url=url, status=status, headers=hdrs, body=payload)

    # -- what the tests actually assert on ----------------------------------

    @property
    def api_calls(self) -> list[str]:
        """Requests that cost REST quota. Raw-host requests do not."""
        return [u for u in self.requested if u.startswith(API_ROOT)]

    def asked_for(self, fragment: str) -> list[str]:
        return [u for u in self.requested if fragment in u]


def meta_json(**over) -> dict:
    base = {
        "full_name": SLUG,
        "description": "A widget.",
        "default_branch": "main",
        "language": "Python",
        "topics": ["rag", "search"],
        "license": {"spdx_id": "MIT"},
        "stargazers_count": 12,
        "forks_count": 3,
        "open_issues_count": 1,
        "homepage": "",
        "created_at": "2024-01-01T00:00:00Z",
        "pushed_at": "2024-06-01T00:00:00Z",
        "html_url": f"https://github.com/{SLUG}",
    }
    base.update(over)
    return base


def blob(path: str, sha: str, size: int = 120) -> dict:
    return {"path": path, "type": "blob", "sha": sha, "size": size}


def base_routes(*, head_sha: str = HEAD, meta: dict | None = None) -> dict:
    """The two calls every fetch makes before it decides to do anything."""
    return {
        API: {"json": meta if meta is not None else meta_json()},
        f"{API}/commits/main": {"json": {"sha": head_sha}},
    }


def tree_routes(entries, *, truncated: bool = False, head_sha: str = HEAD) -> dict:
    return {f"{API}/git/trees/{head_sha}": {"json": {"tree": entries,
                                                     "truncated": truncated}}}


def raw_route(path: str, body, *, status: int = 200, head_sha: str = HEAD) -> dict:
    return {f"{RAW_ROOT}/{SLUG}/{head_sha}/{path}": {"body": body, "status": status,
                                                     "headers": {"content-type": "text/plain"}}}


def api_blob_route(sha: str, data: bytes) -> dict:
    return {f"{API}/git/blobs/{sha}": {
        "json": {"encoding": "base64", "content": base64.b64encode(data).decode("ascii")}}}


def readme_route(text: str, *, path: str = "README.md", sha: str = "r" * 40) -> dict:
    return {f"{API}/readme": {"json": {"path": path, "sha": sha,
                                       "content": base64.b64encode(text.encode()).decode()}}}


def connector(http: FakeHttp, **kw) -> GitHubConnector:
    # An explicit token keeps the constructor from picking up a real GITHUB_TOKEN
    # out of the developer's environment and changing behaviour between machines.
    return GitHubConnector(owner=OWNER, repo=REPO,
                           gh=GitHubClient(token="fake-token", client=http), **kw)


def docs_by_kind(docs) -> dict:
    out: dict[str, list] = {}
    for d in docs:
        out.setdefault(d.metadata.get("kind", "?"), []).append(d)
    return out


# ------------------------------------------------------------------ pagination


class LinkHeaderParsing(unittest.TestCase):
    """`_next_link` decides whether pagination continues. Every miss here is a
    silent truncation: the caller gets page one and no error at all."""

    def test_finds_next_among_several_links(self):
        header = (f'<{API}/issues?page=2>; rel="next", '
                  f'<{API}/issues?page=9>; rel="last"')
        self.assertEqual(_next_link(header), f"{API}/issues?page=2")

    def test_accepts_single_quotes_and_stray_spaces(self):
        # Some proxies and GitHub Enterprise rewrite the header; the quoting
        # style is not something the caller controls.
        self.assertEqual(_next_link("<https://h/2> ;  rel = 'next'"), "https://h/2")
        self.assertEqual(_next_link("<https://h/2>;rel='next'"), "https://h/2")

    def test_finds_next_when_other_parameters_come_first(self):
        # BUG (fixed): only the *second* segment of each link was inspected, so
        # a link carrying any other parameter ahead of rel - which RFC 8288
        # allows in any order - was read as "no next page". A 4,000-issue
        # repository silently ingested its first 100 issues and reported
        # success.
        header = f'<{API}/issues?page=2>; type="application/json"; rel="next"'
        self.assertEqual(_next_link(header), f"{API}/issues?page=2")

    def test_accepts_an_unquoted_rel_token(self):
        # rel=next without quotes is legal per RFC 8288 and appears in the wild.
        self.assertEqual(_next_link("<https://h/2>; rel=next"), "https://h/2")

    def test_prev_only_header_has_no_next(self):
        self.assertIsNone(_next_link(f'<{API}/issues?page=1>; rel="prev"'))

    def test_empty_and_junk_headers_are_not_a_next_page(self):
        self.assertIsNone(_next_link(""))
        self.assertIsNone(_next_link("garbage"))
        self.assertIsNone(_next_link("<https://h/2>"))  # no rel at all


class Pagination(unittest.TestCase):
    def client(self, routes) -> tuple[GitHubClient, FakeHttp]:
        http = FakeHttp(routes)
        return GitHubClient(token="fake-token", client=http), http

    def test_follows_next_links_across_pages(self):
        p1 = f"{API_ROOT}/things?per_page=100"
        p2, p3 = f"{API_ROOT}/things?page=2", f"{API_ROOT}/things?page=3"
        gh, http = self.client({
            p1: {"json": [{"id": 1}, {"id": 2}], "headers": {"link": f'<{p2}>; rel="next"'}},
            p2: {"json": [{"id": 3}], "headers": {"link": f'<{p3}>; rel="next"'}},
            p3: {"json": [{"id": 4}], "headers": {"link": f'<{p1}>; rel="prev"'}},
        })
        self.assertEqual([i["id"] for i in gh.paginate("/things")], [1, 2, 3, 4])
        self.assertEqual(len(http.requested), 3)

    def test_stops_at_max_items_without_fetching_the_next_page(self):
        # The bound has to be enforced before the next request, not after:
        # max_items exists to cap spend, and a cap that still pays for one more
        # page has not capped anything.
        p1 = f"{API_ROOT}/things?per_page=100"
        p2 = f"{API_ROOT}/things?page=2"
        gh, http = self.client({
            p1: {"json": [{"id": 1}, {"id": 2}, {"id": 3}],
                 "headers": {"link": f'<{p2}>; rel="next"'}},
            p2: {"json": [{"id": 4}]},
        })
        self.assertEqual([i["id"] for i in gh.paginate("/things", max_items=2)], [1, 2])
        self.assertEqual(http.requested, [p1])

    def test_reads_a_search_style_payload_with_an_items_key(self):
        # /search/* answers with an object, every other endpoint with an array.
        gh, _ = self.client({f"{API_ROOT}/search/code?per_page=100":
                             {"json": {"total_count": 2, "items": [{"id": 1}, {"id": 2}]}}})
        self.assertEqual([i["id"] for i in gh.paginate("/search/code")], [1, 2])

    def test_a_prev_only_link_terminates_the_walk(self):
        # The last page of a GitHub listing carries prev/first and no next. If
        # that were read as "keep going" the walk would re-request forever.
        gh, http = self.client({f"{API_ROOT}/things?per_page=100":
                                {"json": [{"id": 1}],
                                 "headers": {"link": f'<{API_ROOT}/things?page=1>; rel="prev"'}}})
        self.assertEqual(len(list(gh.paginate("/things"))), 1)
        self.assertEqual(len(http.requested), 1)

    def test_a_payload_that_is_neither_list_nor_items_yields_nothing(self):
        # e.g. {"message": "Not Found"} delivered with a 200 by a proxy. Degrade,
        # don't die: the caller gets an empty walk, not an AttributeError that
        # takes the whole ingest down with it.
        gh, _ = self.client({f"{API_ROOT}/things?per_page=100": {"json": {"message": "nope"}}})
        self.assertEqual(list(gh.paginate("/things")), [])

    def test_query_parameters_are_sent_and_none_values_dropped(self):
        gh, http = self.client({f"{API_ROOT}/things": {"json": []}})
        list(gh.paginate("/things", state="all", since=None, per_page=50))
        self.assertIn("state=all", http.requested[0])
        self.assertIn("per_page=50", http.requested[0])
        self.assertNotIn("since", http.requested[0])


# ------------------------------------------------------------------ file walks


class FileWalk(unittest.TestCase):
    def run_fetch(self, http, cursor=None, **kw):
        conn = connector(http, resources=("files",), **kw)
        docs = list(conn.fetch(dict(cursor or {})))
        return conn, docs

    def test_unchanged_head_skips_the_tree_walk_entirely(self):
        # The headline cost optimisation: two calls (repo + head commit) and no
        # tree request at all when nothing moved. If the tree were still walked,
        # a nightly re-ingest of a 5,000-file repository would spend its whole
        # hourly quota discovering that nothing changed.
        http = FakeHttp({**base_routes(), **tree_routes([blob("a.md", "s1")])})
        conn, docs = self.run_fetch(http, {"head_sha": HEAD, "blob_shas": {"a.md": "s1"}})
        self.assertEqual(docs, [])
        self.assertEqual(http.asked_for("git/trees"), [])
        self.assertEqual(conn.stats["skipped"]["head_unchanged"], 1)
        self.assertEqual(len(http.api_calls), 2)

    def test_unchanged_head_with_no_recorded_blobs_still_walks(self):
        # A cursor can carry a head sha and no blob map - the first run was
        # interrupted, or an older cursor format was migrated. Trusting the head
        # alone would leave the repository permanently un-ingested.
        http = FakeHttp({**base_routes(), **tree_routes([blob("a.md", "s1")]),
                         **raw_route("a.md", "hello")})
        conn, docs = self.run_fetch(http, {"head_sha": HEAD})
        self.assertEqual([d.metadata["path"] for d in docs], ["a.md"])
        self.assertEqual(len(http.asked_for("git/trees")), 1)

    def test_unchanged_blob_is_not_refetched_and_a_changed_one_is(self):
        http = FakeHttp({
            **base_routes(),
            **tree_routes([blob("same.md", "sha-same"), blob("moved.md", "sha-new")]),
            **raw_route("moved.md", "new text"),
        })
        conn, docs = self.run_fetch(
            http, {"head_sha": OLD_HEAD,
                   "blob_shas": {"same.md": "sha-same", "moved.md": "sha-old"}})
        self.assertEqual([d.metadata["path"] for d in docs], ["moved.md"])
        self.assertEqual(conn.stats["skipped"]["blob_unchanged"], 1)
        self.assertEqual(http.asked_for("same.md"), [])

    def test_force_refetch_overrides_the_blob_short_circuit(self):
        http = FakeHttp({**base_routes(), **tree_routes([blob("same.md", "sha-same")]),
                         **raw_route("same.md", "text")})
        conn, docs = self.run_fetch(http, {"head_sha": OLD_HEAD,
                                           "blob_shas": {"same.md": "sha-same"},
                                           "force_refetch": True})
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(http.asked_for("same.md")), 1)

    def test_a_truncated_tree_is_recorded_rather_than_passed_off_as_complete(self):
        # GitHub truncates trees over ~100k entries. Reporting a partial walk as
        # a full one is how an index quietly loses half a monorepo.
        http = FakeHttp({**base_routes(),
                         **tree_routes([blob("a.md", "s1")], truncated=True),
                         **raw_route("a.md", "hello")})
        conn, docs = self.run_fetch(http)
        self.assertEqual(conn.stats["skipped"]["tree_truncated"], 1)
        self.assertEqual(len(docs), 1)  # still emits what it did see

    def test_non_blob_tree_entries_are_ignored(self):
        http = FakeHttp({**base_routes(),
                         **tree_routes([{"path": "docs", "type": "tree", "sha": "t1"},
                                        blob("docs/a.md", "s1")]),
                         **raw_route("docs/a.md", "hello")})
        _, docs = self.run_fetch(http)
        self.assertEqual([d.metadata["path"] for d in docs], ["docs/a.md"])

    def test_max_files_caps_emission_and_reports_the_remainder(self):
        http = FakeHttp({**base_routes(),
                         **tree_routes([blob("a.md", "s1"), blob("b.md", "s2")]),
                         **raw_route("a.md", "one"), **raw_route("b.md", "two")})
        conn, docs = self.run_fetch(http, max_files=1)
        self.assertEqual(len(docs), 1)
        self.assertEqual(conn.stats["skipped"]["max_files"], 1)
        self.assertEqual(http.asked_for("b.md"), [])  # budget spent, no fetch

    def test_an_empty_tree_produces_no_documents_and_no_error(self):
        http = FakeHttp({**base_routes(), **tree_routes([])})
        conn, docs = self.run_fetch(http)
        self.assertEqual(docs, [])
        self.assertEqual(conn.stats["counts"]["files"], 0)


# ------------------------------------------------------------------ blob fetch


class BlobFetching(unittest.TestCase):
    def fetch_one(self, routes, *, path="a.md", sha="s1", size=120):
        http = FakeHttp({**base_routes(), **tree_routes([blob(path, sha, size)]), **routes})
        conn = connector(http, resources=("files",))
        return conn, list(conn.fetch({})), http

    def test_a_raw_hit_costs_no_api_call(self):
        # raw.githubusercontent.com does not spend REST quota. This is the third
        # of the three cost controls in the module docstring, and the only one
        # that is invisible in the documents it produces.
        conn, docs, http = self.fetch_one(raw_route("a.md", "# Title\nbody"))
        self.assertEqual(docs[0].text, "# Title\nbody")
        self.assertEqual(http.asked_for("git/blobs"), [])
        self.assertEqual(len(http.api_calls), 3)  # repo, head commit, tree

    def test_the_raw_url_is_pinned_to_the_commit_not_the_branch(self):
        _, _, http = self.fetch_one(raw_route("a.md", "text"))
        self.assertEqual(http.asked_for("raw.githubusercontent.com"),
                         [f"{RAW_ROOT}/{SLUG}/{HEAD}/a.md"])

    def test_a_raw_404_falls_back_to_the_api_blob_and_decodes_base64(self):
        # Raw 404s for a path that exists in the tree but not on the CDN yet, and
        # for anything the CDN declines. The blob endpoint is keyed by sha, so it
        # always works, and it is the only reason a fresh commit is fetchable.
        conn, docs, http = self.fetch_one({**raw_route("a.md", "not found", status=404),
                                           **api_blob_route("s1", b"recovered body")})
        self.assertEqual(docs[0].text, "recovered body")
        self.assertEqual(len(http.asked_for("git/blobs")), 1)

    def test_a_raw_403_falls_back_rather_than_raising(self):
        # The raw host rate-limits with 403; that is a fallback signal, not a
        # failure of the ingest.
        _, docs, _ = self.fetch_one({**raw_route("a.md", "", status=403),
                                     **api_blob_route("s1", b"recovered")})
        self.assertEqual(docs[0].text, "recovered")

    def test_a_raw_transport_error_falls_back_to_the_api(self):
        http_routes = {f"{RAW_ROOT}/{SLUG}/{HEAD}/a.md": {"raise": TransportError("dns")},
                       **api_blob_route("s1", b"recovered")}
        _, docs, _ = self.fetch_one(http_routes)
        self.assertEqual(docs[0].text, "recovered")

    def test_a_nul_byte_from_raw_marks_the_file_binary_and_skips_it(self):
        # A .json or .md can still be binary (a checked-in sqlite dump named
        # data.json). Indexing its bytes poisons the lexical index with garbage
        # tokens, so it is skipped and counted.
        conn, docs, http = self.fetch_one(raw_route("a.md", b"text\x00\x01more"))
        self.assertEqual(docs, [])
        self.assertEqual(conn.stats["skipped"]["binary_or_failed"], 1)
        self.assertEqual(http.asked_for("git/blobs"), [])  # no second attempt

    def test_a_nul_byte_in_the_api_blob_marks_the_file_binary_too(self):
        conn, docs, _ = self.fetch_one({**raw_route("a.md", "", status=404),
                                        **api_blob_route("s1", b"\x00\x00binary")})
        self.assertEqual(docs, [])
        self.assertEqual(conn.stats["skipped"]["binary_or_failed"], 1)

    def test_a_nul_byte_after_the_first_8192_bytes_is_not_scanned_for(self):
        # The scan is deliberately bounded: reading further would mean holding
        # and scanning every byte of every file to decide something the first
        # page already answers for real binaries.
        body = b"a" * 9000 + b"\x00"
        conn, docs, _ = self.fetch_one(raw_route("a.md", body), size=9001)
        self.assertEqual(len(docs), 1)

    def test_a_failed_blob_is_counted_not_raised(self):
        # One unreachable file must not abort the other 3,999.
        http = FakeHttp({**base_routes(),
                         **tree_routes([blob("bad.md", "s1"), blob("good.md", "s2")]),
                         **raw_route("bad.md", "", status=404),
                         f"{API}/git/blobs/s1": {"status": 500, "body": "boom"},
                         **raw_route("good.md", "fine")})
        conn = connector(http, resources=("files",))
        docs = list(conn.fetch({}))
        self.assertEqual([d.metadata["path"] for d in docs], ["good.md"])
        self.assertEqual(conn.stats["skipped"]["binary_or_failed"], 1)

    def test_a_failed_blob_is_not_recorded_as_successfully_fetched(self):
        # BUG (fixed): the blob sha was written to the cursor before the bytes
        # were fetched, so a file whose fetch failed once was treated as
        # unchanged on every later run and never fetched again. One transient
        # 500 removed a file from the index permanently, and the delta reported
        # a clean run while it happened.
        http = FakeHttp({**base_routes(), **tree_routes([blob("bad.md", "s1")]),
                         **raw_route("bad.md", "", status=404),
                         f"{API}/git/blobs/s1": {"status": 500, "body": "boom"}})
        conn = connector(http, resources=("files",))
        list(conn.fetch({}))
        self.assertNotIn("bad.md", conn.stats.get("blob_shas", {}))

        # ... and the next run, with that cursor, tries again.
        http2 = FakeHttp({**base_routes(), **tree_routes([blob("bad.md", "s1")]),
                          **raw_route("bad.md", "recovered")})
        conn2 = connector(http2, resources=("files",))
        docs = list(conn2.fetch(conn.next_cursor({})))
        self.assertEqual([d.metadata["path"] for d in docs], ["bad.md"])


# ----------------------------------------------------------------- path gating


class PathGating(unittest.TestCase):
    def setUp(self):
        self.conn = connector(FakeHttp(), resources=("files",))

    def wanted(self, path, size=100, **kw):
        conn = connector(FakeHttp(), resources=("files",), **kw) if kw else self.conn
        return conn._wanted_path(path, size)

    def test_text_extensions_are_kept_and_others_rejected(self):
        for path in ("README.md", "src/app.py", "conf/ci.yaml", "web/index.html"):
            self.assertEqual(self.wanted(path), (True, ""), path)
        for path in ("logo.png", "fonts/x.woff2", "data/db.sqlite"):
            self.assertEqual(self.wanted(path)[1], "not_text", path)

    def test_extensionless_files_worth_reading_are_kept(self):
        # Dockerfile and Makefile carry as much build knowledge as any .yaml.
        for path in ("Dockerfile", "Makefile", "LICENSE", "docs/CONTRIBUTING"):
            self.assertTrue(self.wanted(path)[0], path)

    def test_extension_matching_is_case_insensitive(self):
        self.assertTrue(self.wanted("SRC/MAIN.PY")[0])

    def test_lockfiles_are_skipped(self):
        # Machine-generated, enormous, and they answer no question anyone asks.
        for path in ("package-lock.json", "web/yarn.lock", "poetry.lock",
                     "Cargo.lock", "go.sum", "sub/Gemfile.lock"):
            self.assertEqual(self.wanted(path)[1], "skip_pattern", path)

    def test_vendored_and_build_directories_are_skipped(self):
        for path in ("node_modules/left-pad/index.js", "vendor/x/y.go",
                     "dist/bundle.js", "a/b/__pycache__/m.py", ".git/config"):
            self.assertEqual(self.wanted(path)[1], "skip_pattern", path)

    def test_minified_and_generated_files_are_skipped(self):
        for path in ("static/app.min.js", "static/site.min.css",
                     "api/service.pb.go", "gen/model.generated.ts"):
            self.assertEqual(self.wanted(path)[1], "skip_pattern", path)

    def test_a_directory_named_like_a_skip_token_is_not_skipped_by_prefix(self):
        # ".gitignore" is not the ".git" directory, and "buildings.md" is not
        # "build/". Over-eager prefix matching here silently drops real docs.
        self.assertTrue(self.wanted(".gitignore")[0] or
                        self.wanted(".gitignore")[1] == "not_text")
        self.assertTrue(self.wanted("docs/buildings.md")[0])
        self.assertTrue(self.wanted("outline.md")[0])

    def test_files_over_the_byte_budget_are_rejected_before_any_fetch(self):
        self.assertEqual(self.wanted("huge.md", 500_000)[1], "too_large")
        self.assertTrue(self.wanted("huge.md", 399_999)[0])

    def test_exclude_paths_wins_over_a_wanted_extension(self):
        self.assertEqual(self.wanted("docs/legacy/a.md", exclude_paths=(r"^docs/legacy/",))[1],
                         "excluded")

    def test_include_paths_restricts_to_the_named_subtrees(self):
        conn = connector(FakeHttp(), resources=("files",), include_paths=(r"^docs/",))
        self.assertTrue(conn._wanted_path("docs/a.md", 10)[0])
        self.assertEqual(conn._wanted_path("src/a.py", 10)[1], "not_included")

    def test_the_gate_is_applied_during_the_walk_and_counted_by_reason(self):
        http = FakeHttp({**base_routes(),
                         **tree_routes([blob("keep.md", "s1"), blob("logo.png", "s2"),
                                        blob("package-lock.json", "s3"),
                                        blob("huge.md", "s4", 500_000)]),
                         **raw_route("keep.md", "text")})
        conn = connector(http, resources=("files",))
        docs = list(conn.fetch({}))
        self.assertEqual([d.metadata["path"] for d in docs], ["keep.md"])
        self.assertEqual(conn.stats["skipped"],
                         {"not_text": 1, "skip_pattern": 1, "too_large": 1})
        # Nothing rejected was ever fetched - the gate exists to save requests.
        self.assertEqual(http.asked_for("logo.png"), [])


# ------------------------------------------------------------------- documents


class Documents(unittest.TestCase):
    def full_repo(self, **routes) -> FakeHttp:
        return FakeHttp({
            **base_routes(),
            **tree_routes([blob("src/app.py", "s1", 200)]),
            **raw_route("src/app.py", "print('hi')\n"),
            **readme_route("# Widget\n\nDocs here."),
            **routes,
        })

    def test_file_permalinks_pin_the_commit_sha_never_the_branch(self):
        # The stated provenance guarantee: a citation must resolve to the exact
        # bytes that were indexed. A /blob/main/ link rots the moment the branch
        # moves, and rots silently - the URL still resolves, to different text.
        http = self.full_repo()
        conn = connector(http, resources=("files",))
        doc = list(conn.fetch({}))[0]
        self.assertEqual(doc.uri, f"https://github.com/{SLUG}/blob/{HEAD}/src/app.py")
        self.assertNotIn("/blob/main/", doc.uri)

    def test_readme_permalinks_pin_the_commit_sha_too(self):
        http = self.full_repo()
        conn = connector(http, resources=("readme",))
        doc = list(conn.fetch({}))[0]
        self.assertEqual(doc.uri, f"https://github.com/{SLUG}/blob/{HEAD}/README.md")

    def test_file_metadata_carries_what_the_retriever_filters_on(self):
        http = self.full_repo()
        conn = connector(http, resources=("files",))
        md = list(conn.fetch({}))[0].metadata
        self.assertEqual(md["path"], "src/app.py")
        self.assertEqual(md["dir"], "src")
        self.assertEqual(md["filename"], "app.py")
        self.assertEqual(md["language"], "python")
        self.assertEqual(md["blob_sha"], "s1")
        self.assertEqual(md["commit"], HEAD)
        self.assertFalse(md["is_doc"])
        self.assertFalse(md["is_test"])

    def test_test_files_are_flagged_so_they_can_be_down_ranked(self):
        http = FakeHttp({**base_routes(),
                         **tree_routes([blob("tests/test_app.py", "s1")]),
                         **raw_route("tests/test_app.py", "assert True")})
        conn = connector(http, resources=("files",))
        self.assertTrue(list(conn.fetch({}))[0].metadata["is_test"])

    def test_the_repo_overview_reports_the_facts_the_meta_call_returned(self):
        conn = connector(self.full_repo(), resources=("repo",))
        doc = list(conn.fetch({}))[0]
        self.assertIn("Primary language: Python", doc.text)
        self.assertIn("Topics: rag, search", doc.text)
        self.assertEqual(doc.metadata["license"], "MIT")
        self.assertEqual(doc.external_id, f"{SLUG}#repo")

    def test_a_missing_license_or_topics_block_does_not_break_the_overview(self):
        http = FakeHttp({**base_routes(meta=meta_json(license=None, topics=None,
                                                      description=None))})
        conn = connector(http, resources=("repo",))
        doc = list(conn.fetch({}))[0]
        self.assertIn("License: none", doc.text)
        self.assertIn("Topics: none", doc.text)

    def test_the_ref_falls_back_to_the_default_branch_from_the_repo_metadata(self):
        conn = connector(self.full_repo(), resources=("repo",))
        list(conn.fetch({}))
        self.assertEqual(conn.stats["ref"], "main")
        self.assertEqual(conn.stats["head_sha"], HEAD)


class SecretRedaction(unittest.TestCase):
    """An index is a file that gets copied around. Nothing credential-shaped may
    reach one, whichever resource it came in through."""

    def leaky(self, extra: str = "") -> str:
        return f"config token: {LEAKED_TOKEN}\naws: {LEAKED_AWS}\n{extra}"

    def assert_clean(self, doc):
        self.assertNotIn(LEAKED_TOKEN, doc.text)
        self.assertNotIn(LEAKED_AWS, doc.text)
        self.assertIn("redacted", doc.text)

    def test_file_documents_are_redacted(self):
        http = FakeHttp({**base_routes(), **tree_routes([blob("conf.yaml", "s1")]),
                         **raw_route("conf.yaml", self.leaky())})
        conn = connector(http, resources=("files",))
        self.assert_clean(list(conn.fetch({}))[0])

    def test_readme_documents_are_redacted(self):
        http = FakeHttp({**base_routes(), **readme_route(self.leaky())})
        conn = connector(http, resources=("readme",))
        self.assert_clean(list(conn.fetch({}))[0])

    def test_issue_documents_are_redacted(self):
        # Pasting a token into a bug report is exactly how they leak.
        http = FakeHttp({**base_routes(), f"{API}/issues": {"json": [
            {"number": 1, "title": "broken", "state": "open", "body": self.leaky(),
             "user": {"login": "ann"}, "labels": [], "html_url": "https://h/1"}]}})
        conn = connector(http, resources=("issues",))
        self.assert_clean(list(conn.fetch({}))[0])

    def test_commit_documents_are_redacted(self):
        http = FakeHttp({**base_routes(), f"{API}/commits": {"json": [
            {"sha": "c" * 40, "html_url": "https://h/c",
             "commit": {"message": f"oops\n\n{self.leaky()}",
                        "author": {"name": "Ann", "date": "2024-01-01T00:00:00Z"}}}]}})
        conn = connector(http, resources=("commits",))
        self.assert_clean(list(conn.fetch({}))[0])

    def test_release_documents_are_redacted(self):
        http = FakeHttp({**base_routes(), f"{API}/releases": {"json": [
            {"tag_name": "v1", "name": "one", "body": self.leaky(),
             "published_at": "2024-01-01T00:00:00Z", "html_url": "https://h/r"}]}})
        conn = connector(http, resources=("releases",))
        self.assert_clean(list(conn.fetch({}))[0])


class IssuesAndPulls(unittest.TestCase):
    ISSUE = {"number": 7, "title": "Crash on empty input", "state": "open",
             "body": "steps to reproduce", "user": {"login": "ann"},
             "labels": [{"name": "bug"}, {"name": "p1"}], "comments": 3,
             "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-02-01T00:00:00Z",
             "html_url": f"https://github.com/{SLUG}/issues/7"}
    PULL = {"number": 8, "title": "Fix the crash", "state": "closed", "body": "patch",
            "user": {"login": "bob"}, "labels": [], "comments": 1,
            "pull_request": {"url": f"{API}/pulls/8"},
            "created_at": "2024-01-03T00:00:00Z", "updated_at": "2024-02-03T00:00:00Z",
            "html_url": f"https://github.com/{SLUG}/pull/8"}

    def fetch(self, resources, cursor=None):
        http = FakeHttp({**base_routes(),
                         f"{API}/issues": {"json": [self.ISSUE, self.PULL]}})
        conn = connector(http, resources=resources)
        return conn, list(conn.fetch(dict(cursor or {}))), http

    def test_issues_only_excludes_pull_requests(self):
        # /issues returns both; the "pull_request" key is the only thing that
        # tells them apart, and a caller who asked for issues did not ask for
        # every merged PR in the repository's history.
        _, docs, _ = self.fetch(("issues",))
        self.assertEqual([d.metadata["number"] for d in docs], [7])
        self.assertEqual(docs[0].metadata["kind"], "issue")
        self.assertEqual(docs[0].external_id, f"{SLUG}#issue:7")

    def test_pulls_only_excludes_issues(self):
        _, docs, _ = self.fetch(("pulls",))
        self.assertEqual([d.metadata["number"] for d in docs], [8])
        self.assertEqual(docs[0].metadata["kind"], "pull_request")
        self.assertEqual(docs[0].external_id, f"{SLUG}#pr:8")
        self.assertTrue(docs[0].title.startswith(f"{SLUG} PR #8"))

    def test_asking_for_both_emits_both(self):
        _, docs, _ = self.fetch(("issues", "pulls"))
        self.assertEqual(sorted(d.metadata["number"] for d in docs), [7, 8])

    def test_issue_metadata_and_body_survive_intact(self):
        _, docs, _ = self.fetch(("issues",))
        doc = docs[0]
        self.assertEqual(doc.metadata["labels"], ["bug", "p1"])
        self.assertEqual(doc.metadata["author"], "ann")
        self.assertEqual(doc.metadata["state"], "open")
        self.assertIn("steps to reproduce", doc.text)

    def test_a_stored_since_cursor_is_sent_so_old_issues_are_not_refetched(self):
        _, _, http = self.fetch(("issues",), {"issues_since": "2024-05-05T00:00:00Z"})
        self.assertIn("since=2024-05-05", http.asked_for("/issues")[0])

    def test_an_issue_with_null_labels_does_not_abort_the_whole_run(self):
        # BUG (fixed): `issue.get("labels", [])` returns None when the key is
        # present and null, and iterating None raised TypeError out of the
        # generator - which `Connector.run` catches as a *source* failure, so a
        # single odd issue ended the run and every document after it was lost.
        http = FakeHttp({**base_routes(), f"{API}/issues": {"json": [
            {"number": 1, "title": "odd", "labels": None, "user": None, "body": None},
            {**self.ISSUE, "number": 9}]}})
        conn = connector(http, resources=("issues",))
        docs = list(conn.fetch({}))
        self.assertEqual([d.metadata["number"] for d in docs], [1, 9])
        self.assertEqual(docs[0].metadata["labels"], [])
        self.assertIn("(no description)", docs[0].text)


class Releases(unittest.TestCase):
    def fetch(self, releases):
        http = FakeHttp({**base_routes(), f"{API}/releases": {"json": releases}})
        conn = connector(http, resources=("releases",))
        return conn, list(conn.fetch({}))

    def test_a_release_with_an_empty_body_yields_nothing(self):
        # A tag with no notes carries no retrievable content; emitting a document
        # whose text is a heading and a date only pollutes retrieval.
        conn, docs = self.fetch([{"tag_name": "v0.1", "body": "", "html_url": "https://h"},
                                 {"tag_name": "v0.2", "body": "   \n ", "html_url": "https://h"},
                                 {"tag_name": "v0.3", "body": None, "html_url": "https://h"}])
        self.assertEqual(docs, [])
        self.assertEqual(conn.stats["counts"]["releases"], 0)

    def test_a_release_with_notes_is_emitted_with_its_tag(self):
        conn, docs = self.fetch([{"tag_name": "v1.0", "name": "First",
                                  "body": "## Added\n- things", "prerelease": False,
                                  "published_at": "2024-03-01T00:00:00Z",
                                  "html_url": "https://h/v1"}])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["tag"], "v1.0")
        self.assertIn("- things", docs[0].text)


# -------------------------------------------------------------- failure paths


class FailurePaths(unittest.TestCase):
    def test_a_404_on_readme_yields_no_document_and_does_not_raise(self):
        # Plenty of repositories have no README. That is not an ingest failure,
        # and treating it as one would mark a healthy source unhealthy.
        http = FakeHttp({**base_routes(), f"{API}/readme": {"status": 404,
                                                            "body": '{"message":"Not Found"}'},
                         **tree_routes([]), })
        conn = connector(http, resources=("readme", "files"))
        docs = list(conn.fetch({}))
        self.assertEqual(docs, [])
        self.assertNotIn("readme", conn.stats["counts"])

    def test_an_undecodable_readme_yields_no_document(self):
        http = FakeHttp({**base_routes(),
                         f"{API}/readme": {"json": {"path": "README.md",
                                                    "content": "!!!not base64!!!"}}})
        conn = connector(http, resources=("readme",))
        self.assertEqual(list(conn.fetch({})), [])

    def test_a_repo_level_failure_is_reported_in_the_delta_not_raised(self):
        # `Connector.run` is the contract boundary: a dead source becomes a
        # delta with failed=1, because the OODA loop reads deltas to decide
        # whether a source is healthy.
        http = FakeHttp({API: {"status": 404, "body": '{"message":"Not Found"}'}})
        conn = connector(http)
        result = conn.run(MemoryStateStore())
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.documents, [])
        self.assertTrue(any("HTTP 404" in e for e in result.delta.errors))

    def test_run_reports_new_changed_and_unchanged_across_two_runs(self):
        def http():
            return FakeHttp({**base_routes(), **tree_routes([blob("a.md", "s1")]),
                             **raw_route("a.md", "hello"), **readme_route("# Widget")})
        state = MemoryStateStore()
        first = connector(http()).run(state)
        self.assertEqual((first.delta.new, first.delta.changed), (3, 0))

        # Second run: same head, so the file walk is skipped entirely and only
        # the repo overview and README come back. All three documents are
        # unchanged - including a.md, which the head-sha short circuit proved
        # unchanged without fetching it. It is counted here rather than being
        # invisible: when it was invisible, `run()` inferred absence from silence
        # and reported every short-circuited file in `removed_last_run` while
        # dropping its stored hash, so the optimisation proposed wiping the index
        # and paid for a full re-ingest on the run after. See
        # Connector.unchanged_external_ids.
        second = connector(http()).run(state)
        self.assertEqual((second.delta.new, second.delta.changed), (0, 0))
        self.assertEqual(second.delta.unchanged, 3)
        self.assertEqual(state.get(f"github:{SLUG}").get("removed_last_run", []), [],
                         "a short-circuited file must never look deleted")


# -------------------------------------------------------------------- cursors


class Cursors(unittest.TestCase):
    def test_next_cursor_advances_head_blobs_and_since_and_clears_force_refetch(self):
        http = FakeHttp({**base_routes(), **tree_routes([blob("a.md", "s1")]),
                         **raw_route("a.md", "hello"),
                         f"{API}/issues": {"json": [{"number": 1, "title": "t",
                                                     "labels": [], "body": "b"}]}})
        conn = connector(http, resources=("files", "issues"))
        list(conn.fetch({}))
        cursor = conn.next_cursor({"head_sha": OLD_HEAD, "force_refetch": True,
                                   "blob_shas": {"gone.md": "s0"}})
        self.assertEqual(cursor["head_sha"], HEAD)
        self.assertEqual(cursor["ref"], "main")
        self.assertEqual(cursor["blob_shas"], {"a.md": "s1"})
        self.assertNotIn("force_refetch", cursor)
        self.assertRegex(cursor["issues_since"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(cursor["last_stats"]["counts"]["files"], 1)

    def test_the_blob_map_is_preserved_when_the_walk_was_skipped(self):
        # The head-unchanged path records no blob shas of its own; overwriting
        # the stored map with an empty one would force a full refetch on the
        # run after next.
        http = FakeHttp({**base_routes()})
        conn = connector(http, resources=("files",))
        list(conn.fetch({"head_sha": HEAD, "blob_shas": {"a.md": "s1"}}))
        cursor = conn.next_cursor({"head_sha": HEAD, "blob_shas": {"a.md": "s1"}})
        self.assertEqual(cursor["blob_shas"], {"a.md": "s1"})

    def test_a_failed_tree_call_does_not_advance_the_head_sha(self):
        # BUG (fixed): head_sha was written to the cursor as soon as the head
        # commit was read, before the file walk had run. If the tree call then
        # failed - or the run was cut short by `limit` - the next run saw
        # "head unchanged" against a full blob map and skipped the walk
        # entirely. Every file added in that commit was then invisible to the
        # index forever, with no error anywhere to say so.
        http = FakeHttp({**base_routes(),
                         f"{API}/git/trees/{HEAD}": {"status": 500, "body": "boom"}})
        conn = connector(http, resources=("files",))
        state = MemoryStateStore()
        state.set(conn.key, {"head_sha": OLD_HEAD, "blob_shas": {"a.md": "s1"}})
        result = conn.run(state)
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.cursor["head_sha"], OLD_HEAD)

        # Proof that it matters: the next run walks the tree instead of
        # short-circuiting on a head sha it never finished processing.
        http2 = FakeHttp({**base_routes(), **tree_routes([blob("a.md", "s2")]),
                          **raw_route("a.md", "new text")})
        second = connector(http2, resources=("files",)).run(state)
        self.assertEqual([d.metadata["path"] for d in second.documents], ["a.md"])

    def test_an_interrupted_walk_does_not_advance_the_head_sha(self):
        # `run(limit=...)` abandons the generator part-way through the tree.
        # Same failure mode as above, reached the way a caller actually reaches
        # it: sampling a large repository and then running it again in full.
        http = FakeHttp({**base_routes(),
                         **tree_routes([blob("a.md", "s1"), blob("b.md", "s2"),
                                        blob("c.md", "s3")]),
                         **raw_route("a.md", "one"), **raw_route("b.md", "two"),
                         **raw_route("c.md", "three")})
        conn = connector(http, resources=("files",))
        state = MemoryStateStore()
        result = conn.run(state, limit=1)
        self.assertEqual(len(result.documents), 1)
        self.assertNotEqual(result.cursor.get("head_sha"), HEAD)

        http2 = FakeHttp({**base_routes(),
                          **tree_routes([blob("a.md", "s1"), blob("b.md", "s2"),
                                         blob("c.md", "s3")]),
                          **raw_route("a.md", "one"), **raw_route("b.md", "two"),
                          **raw_route("c.md", "three")})
        second = connector(http2, resources=("files",)).run(state)
        # a.md was already ingested and hashes unchanged, so `run` reports it
        # rather than re-emitting it; the point is that b.md and c.md are not
        # lost behind a head sha that claims they were done.
        self.assertEqual(sorted(d.metadata["path"] for d in second.documents),
                         ["b.md", "c.md"])
        self.assertEqual(second.delta.unchanged, 1)

    def test_the_head_sha_advances_for_resources_that_have_no_file_walk(self):
        http = FakeHttp({**base_routes(), **readme_route("# Widget")})
        conn = connector(http, resources=("repo", "readme"))
        list(conn.fetch({}))
        self.assertEqual(conn.next_cursor({})["head_sha"], HEAD)


class ClientConstruction(unittest.TestCase):
    def test_owner_and_repo_are_required_and_key_identifies_the_source(self):
        with self.assertRaises(ValueError):
            GitHubConnector(owner="", repo="x")
        self.assertEqual(connector(FakeHttp()).key, f"github:{SLUG}")

    def test_an_injected_client_keeps_its_own_settings_and_gains_auth_headers(self):
        http = FakeHttp()
        GitHubClient(token="fake-token", client=http)
        self.assertEqual(http.default_headers["Authorization"], "Bearer fake-token")
        self.assertEqual(http.default_headers["X-GitHub-Api-Version"], "2022-11-28")

    def test_rate_limit_degrades_to_an_error_dict_rather_than_raising(self):
        http = FakeHttp({f"{API_ROOT}/rate_limit": {"status": 403, "body": "no"}})
        gh = GitHubClient(token="fake-token", client=http)
        self.assertIn("error", gh.rate_limit())


if __name__ == "__main__":
    unittest.main()
