"""Integration tests that talk to the real network.

Skipped unless `OODARAG_LIVE=1`. They are here because some things are only
true when a real server answers, and the unit tests deliberately fake that away:
whether GitHub's raw host really serves a blob without spending REST quota,
whether a live `robots.txt` parses, whether a real page survives extraction with
its structure intact. A fake transport can prove the code handles the response it
was handed; only this can show the response was ever shaped that way.

They are opt-in rather than skipped-on-failure because a network test that
quietly passes when the network is missing is worse than no test - it is a green
tick asserting something nobody checked.

    PYTHONPATH=src:. OODARAG_LIVE=1 python3 -m unittest tests.test_oodarag_live -v

Environment notes, measured in the sandbox this was written in and true of
locked-down CI generally:

* Arbitrary web egress may be blocked. `pypi.org` was reachable and
  `docs.python.org` was not, so the web tests use pypi.org and assert on
  structure rather than on wording, which changes.
* `github.com/robots.txt` answered 403 through the proxy. `robots.py` treats a
  restricted rules file as disallow-all per RFC 9309, so a crawl of github.com
  correctly yields nothing. That is the policy working, not a failure.
* GitHub's `Link: rel="next"` header uses numeric-ID paths
  (`/repositories/<id>/commits?page=2`) which some proxies reject, so multi-page
  pagination is not asserted here. The fake-transport tests cover it.
"""

from __future__ import annotations

import os
import unittest

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.github import GitHubClient, GitHubConnector
from oodarag.scrape.crawler import CrawlConfig, Crawler
from oodarag.scrape.html import extract
from oodarag.scrape.robots import RobotsPolicy
from oodarag.util.http import HttpClient

LIVE = os.environ.get("OODARAG_LIVE") == "1"
OWNER, REPO = "turkertekten-ship-it", "claude"
WEB_SEED = "https://pypi.org/help/"

requires_live = unittest.skipUnless(LIVE, "set OODARAG_LIVE=1 to run network tests")


@requires_live
class TestGitHubConnectorLive(unittest.TestCase):
    """The connector against the real API."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.gh = GitHubClient()
        if not cls.gh.authenticated:
            raise unittest.SkipTest("no GITHUB_TOKEN/GH_TOKEN in the environment")
        cls.conn = GitHubConnector(owner=OWNER, repo=REPO, gh=cls.gh)
        meta = cls.gh.get(f"/repos/{OWNER}/{REPO}")
        cls.head = cls.gh.get(f"/repos/{OWNER}/{REPO}/commits/{meta['default_branch']}")["sha"]
        cls.tree = cls.gh.get(f"/repos/{OWNER}/{REPO}/git/trees/{cls.head}", recursive="1")

    def _readme_entry(self) -> dict:
        return next(e for e in self.tree["tree"] if e.get("path") == "README.md")

    def test_a_cold_run_produces_documents_with_pinned_permalinks(self):
        conn = GitHubConnector(owner=OWNER, repo=REPO, gh=self.gh,
                               resources=("repo", "readme", "files"), max_files=10)
        result = conn.run(state=MemoryStateStore())
        self.assertTrue(result.documents, "a cold run must produce documents")
        head = conn.stats["head_sha"]
        files = [d for d in result.documents if d.metadata.get("kind") == "file"]
        self.assertTrue(files)
        for doc in files:
            # The stated provenance guarantee: a citation resolves to a
            # permalink pinned at a commit, never a branch that moves underneath.
            self.assertIn(f"/blob/{head}/", doc.uri, doc.uri)

    def test_a_cold_run_reports_no_failures(self):
        # Regression: `log.info("...", repo=self.slug, **counts)` collided with
        # counts["repo"], raising TypeError at the end of every default run. The
        # delta then carried failed=1 forever, and that delta is the signal the
        # OODA loop reads to decide whether ingest is healthy.
        conn = GitHubConnector(owner=OWNER, repo=REPO, gh=self.gh,
                               resources=("repo", "readme"), max_files=1)
        result = conn.run(state=MemoryStateStore())
        self.assertEqual(result.delta.failed, 0, result.delta.errors)
        self.assertEqual(result.delta.errors, [])

    def test_an_unchanged_head_skips_the_whole_file_walk(self):
        state = MemoryStateStore()
        conn = GitHubConnector(owner=OWNER, repo=REPO, gh=self.gh,
                               resources=("files",), max_files=5)
        conn.run(state=state)
        before = dict(self.gh.client.stats)
        conn.run(state=state)
        self.assertIn("head_unchanged", conn.stats.get("skipped", {}))
        # The point of the short circuit is cost: the second run must not walk
        # the tree or fetch a single blob.
        self.assertEqual(self.gh.client.stats["requests"] - before["requests"], 2,
                         "only the repo-meta and head-commit calls should remain")

    def test_blob_fetch_costs_one_request_when_the_raw_host_serves_it(self):
        """Raw-first is a cost optimisation, so assert the cost, not just the bytes.

        Which path runs is an environment fact, not a code fact: this repository
        is public, and the raw host still answered 404 for its blobs through the
        sandbox proxy this was written under - so the API fallback did the work
        and the fetch cost two requests. An earlier version of this test asserted
        one unconditionally and passed for the wrong reason, because the
        `allow_status` branch in HttpClient was not incrementing the counter. The
        raw path is therefore asserted only when the raw host is actually
        serving; otherwise the fallback's cost is asserted instead.
        """
        entry = self._readme_entry()
        raw_url = (f"https://raw.githubusercontent.com/{OWNER}/{REPO}/"
                   f"{self.head}/README.md")
        probe = self.gh.client.get(raw_url, allow_status=(403, 404))
        before = dict(self.gh.client.stats)
        text = self.conn._fetch_blob("README.md", entry["sha"], self.head)
        spent = self.gh.client.stats["requests"] - before["requests"]

        self.assertTrue(text and text.startswith("#"))
        if probe.status == 200:
            self.assertEqual(spent, 1, "raw host is serving; no API call should be needed")
        else:
            self.assertEqual(spent, 2, "raw 404 then the git/blobs fallback")

    def test_the_api_blob_fallback_returns_identical_bytes(self):
        entry = self._readme_entry()
        raw = self.conn._fetch_blob("README.md", entry["sha"], self.head)
        # A path the raw host does not have forces the git/blobs fallback, which
        # is keyed by sha - so it returns the same blob.
        viafallback = self.conn._fetch_blob("does/not/exist.md", entry["sha"], self.head)
        self.assertEqual(viafallback, raw)

    def test_secrets_are_redacted_before_a_document_exists(self):
        entry = self._readme_entry()
        doc = self.conn._file_document(
            "x.md", "token: ghp_" + "A" * 36 + "\ntail", 10, self.head, entry["sha"], "main")
        self.assertNotIn("ghp_A", doc.text)
        self.assertIn("<redacted:github-token>", doc.text)

    def test_path_gating_over_a_real_tree_keeps_source_and_drops_data(self):
        kept, dropped = [], []
        for entry in self.tree["tree"]:
            if entry.get("type") != "blob":
                continue
            ok, _ = self.conn._wanted_path(entry["path"], int(entry.get("size") or 0))
            (kept if ok else dropped).append(entry["path"])
        self.assertTrue(any(p.endswith(".py") for p in kept))
        self.assertTrue(any(p.endswith(".md") for p in kept))
        self.assertNotIn(".gitignore", kept)


@requires_live
class TestRobotsLive(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = RobotsPolicy(client=HttpClient(rate_per_sec=1.0))

    def test_a_real_robots_txt_parses_and_gates(self):
        rules = self.policy.rules_for(WEB_SEED)
        if rules.status != 200:
            self.skipTest(f"robots.txt for pypi.org answered {rules.status} here")
        self.assertFalse(rules.disallow_all)
        self.assertTrue(self.policy.allows(WEB_SEED))
        # pypi.org disallows /simple/ - the point is that a real rule is obeyed,
        # so this asserts the gate discriminates rather than a specific path.
        self.assertNotEqual(self.policy.allows(WEB_SEED),
                            self.policy.allows("https://pypi.org/simple/"))

    def test_sitemaps_are_surfaced(self):
        rules = self.policy.rules_for(WEB_SEED)
        if rules.status != 200:
            self.skipTest("robots.txt unavailable here")
        self.assertTrue(any("sitemap" in s.lower() for s in rules.sitemaps), rules.sitemaps)

    def test_a_restricted_robots_file_disallows_everything(self):
        # github.com answered 403 to robots.txt through the proxy this was
        # written under. RFC 9309 says a site that will not tell us its rules
        # does not get crawled on the assumption they are permissive.
        rules = self.policy.rules_for("https://github.com/")
        if rules.status not in (401, 403):
            self.skipTest(f"github.com/robots.txt answered {rules.status} here")
        self.assertTrue(rules.disallow_all)
        self.assertFalse(self.policy.allows("https://github.com/anything"))


@requires_live
class TestCrawlLive(unittest.TestCase):
    def test_a_real_page_extracts_with_its_structure_intact(self):
        client = HttpClient(rate_per_sec=1.0)
        resp = client.get(WEB_SEED)
        self.assertEqual(resp.status, 200)
        page = extract(resp.text, WEB_SEED)
        self.assertTrue(page.title)
        self.assertEqual(page.lang[:2], "en")
        self.assertGreater(page.word_count, 200)
        self.assertTrue(page.headings, "a real docs page has headings")
        self.assertTrue(page.markdown.lstrip().startswith("#"))
        # Boilerplate removal is the reason this package parses HTML itself.
        body = page.text.lower()
        for chrome in ("skip to main content", "cookie"):
            self.assertNotIn(chrome, body)
        # And the metric that reports whether removal worked must agree.
        self.assertLess(page.link_density, 0.5, "extraction is mostly link text")

    def test_a_bounded_crawl_stops_where_it_says_it_did(self):
        client = HttpClient(rate_per_sec=1.0)
        crawler = Crawler(
            CrawlConfig(seeds=[WEB_SEED], max_pages=2, max_depth=1,
                        max_seconds=120, rate_per_sec=1.0, delay_s=1.0),
            client=client,
        )
        pages = list(crawler.crawl())
        if not pages:
            self.skipTest(f"crawl yielded nothing: {crawler.report.as_dict()}")
        self.assertLessEqual(len(pages), 2)
        self.assertEqual(crawler.report.stopped_by, "max_pages")
        self.assertEqual(len({p.url for p in pages}), len(pages), "URLs must be deduped")
        self.assertTrue(all(p.page.word_count >= 40 for p in pages))


if __name__ == "__main__":
    unittest.main()
