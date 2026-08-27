"""The remaining modules: connector selection logic, hashing, logging, budgeting.

None of these reach the network. The GitHub connector's interesting behaviour is
its *selection* — which paths are worth indexing and which are noise — and that
is a pure function of a path and a size.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import oodarag  # noqa: E402
from oodarag.cli import EXIT_CANNOT_RUN, EXIT_FINDINGS, EXIT_OK, build_parser, main  # noqa: E402
from oodarag.ingest.github import GitHubClient, GitHubConnector, _next_link  # noqa: E402
from oodarag.ingest.web import WebConnector  # noqa: E402
from oodarag.util.hashing import (  # noqa: E402
    blake_bucket,
    blake_sign,
    content_hash,
    sha256_hex,
    stable_id,
)
from oodarag.util.logging import Logger  # noqa: E402
from oodarag.util.ratelimit import TokenBucket  # noqa: E402


class TestPackageSurface(unittest.TestCase):
    def test_the_documented_exports_exist(self) -> None:
        for name in oodarag.__all__:
            self.assertTrue(hasattr(oodarag, name), name)

    def test_version_is_set(self) -> None:
        self.assertTrue(oodarag.__version__)


class TestHashing(unittest.TestCase):
    def test_the_unit_separator_stops_field_confusion(self) -> None:
        # Without a separator, ("ab","c") and ("a","bc") hash identically, and
        # two different documents collide into one id.
        self.assertNotEqual(sha256_hex("ab", "c"), sha256_hex("a", "bc"))

    def test_ids_are_deterministic(self) -> None:
        self.assertEqual(stable_id("github", "owner/repo"), stable_id("github", "owner/repo"))

    def test_content_hash_changes_with_content(self) -> None:
        self.assertNotEqual(content_hash("a body"), content_hash("a body."))

    def test_buckets_stay_in_range(self) -> None:
        for token in ("retrieval", "bm25", "", "a" * 200, "ünïcødé"):
            self.assertTrue(0 <= blake_bucket(token, 512) < 512, token[:20])

    def test_salt_gives_an_independent_hash_function(self) -> None:
        collisions = sum(
            1 for i in range(500)
            if blake_bucket(f"t{i}", 512) == blake_bucket(f"t{i}", 512, salt="n")
        )
        # Roughly 1/512 of 500 should coincide by chance; a shared function
        # would make all 500 coincide.
        self.assertLess(collisions, 25)

    def test_signs_are_balanced_enough_to_cancel(self) -> None:
        positives = sum(1 for i in range(1000) if blake_sign(f"token{i}") > 0)
        self.assertTrue(400 < positives < 600, positives)


class TestTokenBucket(unittest.TestCase):
    def test_burst_capacity_is_available_immediately(self) -> None:
        bucket = TokenBucket(rate_per_sec=1000.0, burst=5)
        started = time.monotonic()
        for _ in range(5):
            bucket.acquire()
        self.assertLess(time.monotonic() - started, 0.2)

    def test_exceeding_the_rate_actually_waits(self) -> None:
        bucket = TokenBucket(rate_per_sec=20.0, burst=1)
        bucket.acquire()
        waited = bucket.acquire()
        self.assertGreater(waited, 0.0)

    def test_a_zero_rate_does_not_divide_by_zero(self) -> None:
        self.assertGreaterEqual(TokenBucket(rate_per_sec=0.0, burst=1).acquire(), 0.0)


class TestLogger(unittest.TestCase):
    def test_a_level_below_the_threshold_is_suppressed(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            Logger("t", level="error").info("should not appear")
        self.assertEqual(buf.getvalue(), "")

    def test_a_level_at_the_threshold_is_emitted(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            Logger("t", level="warn").error("should appear")
        self.assertIn("should appear", buf.getvalue())

    def test_json_mode_emits_parseable_records(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            Logger("t", level="debug", json_mode=True).info("hello", count=3)
        payload = json.loads(buf.getvalue().strip())
        self.assertEqual(payload["msg"], "hello")
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["logger"], "t")

    def test_silent_suppresses_everything(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            Logger("t", level="silent").error("nothing")
        self.assertEqual(buf.getvalue(), "")


class TestGitHubSelection(unittest.TestCase):
    def connector(self, **kw: object) -> GitHubConnector:
        return GitHubConnector(owner="o", repo="r", **kw)  # type: ignore[arg-type]

    def test_owner_and_repo_are_required(self) -> None:
        with self.assertRaises(ValueError):
            GitHubConnector(owner="", repo="r")

    def test_the_key_identifies_the_repository(self) -> None:
        self.assertEqual(self.connector().key, "github:o/r")

    def test_source_code_and_prose_are_wanted(self) -> None:
        c = self.connector()
        for path in ("src/app.py", "README.md", "docs/guide.md", "Makefile", "Dockerfile"):
            wanted, why = c._wanted_path(path, 1000)
            self.assertTrue(wanted, f"{path}: {why}")

    def test_binaries_are_not_wanted(self) -> None:
        c = self.connector()
        for path in ("logo.png", "app.zip", "font.woff2"):
            wanted, why = c._wanted_path(path, 1000)
            self.assertFalse(wanted, path)
            self.assertTrue(why)

    def test_an_oversized_file_is_refused_with_a_reason(self) -> None:
        wanted, why = self.connector(max_file_bytes=100)._wanted_path("src/a.py", 5000)
        self.assertFalse(wanted)
        self.assertEqual(why, "too_large")

    def test_include_paths_narrow_the_selection(self) -> None:
        c = self.connector(include_paths=(r"^docs/",))
        self.assertTrue(c._wanted_path("docs/a.md", 10)[0])
        self.assertEqual(c._wanted_path("src/a.py", 10)[1], "not_included")

    def test_exclude_paths_win_over_inclusion(self) -> None:
        c = self.connector(include_paths=(r"^src/",), exclude_paths=(r"_test\.py$",))
        self.assertTrue(c._wanted_path("src/a.py", 10)[0])
        self.assertEqual(c._wanted_path("src/a_test.py", 10)[1], "excluded")

    def test_a_permalink_pins_the_commit_not_the_branch(self) -> None:
        # A branch link rots as soon as the branch moves; a citation must not.
        link = self.connector()._permalink("src/a.py", "abc123", line=42)
        self.assertIn("/blob/abc123/", link)
        self.assertTrue(link.endswith("#L42"))


class TestLinkHeaderPagination(unittest.TestCase):
    def test_the_next_link_is_extracted(self) -> None:
        header = ('<https://api.github.com/x?page=2>; rel="next", '
                  '<https://api.github.com/x?page=9>; rel="last"')
        self.assertEqual(_next_link(header), "https://api.github.com/x?page=2")

    def test_a_last_page_has_no_next(self) -> None:
        self.assertIsNone(_next_link('<https://api.github.com/x?page=1>; rel="prev"'))

    def test_an_empty_header_is_handled(self) -> None:
        self.assertIsNone(_next_link(""))


class TestGitHubClientAuth(unittest.TestCase):
    """Token resolution: explicit argument, then GITHUB_TOKEN, then GH_TOKEN."""

    def setUp(self) -> None:
        self.saved = {k: os.environ.pop(k, None) for k in ("GITHUB_TOKEN", "GH_TOKEN")}

        def restore() -> None:
            for key, value in self.saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.addCleanup(restore)

    def test_an_explicit_token_authenticates(self) -> None:
        self.assertTrue(GitHubClient(token="ghp_x").authenticated)

    def test_with_no_token_anywhere_it_reports_unauthenticated(self) -> None:
        # Unauthenticated still works against public repositories, at a much
        # lower rate limit — so this must be reported, not silently assumed
        # either way.
        self.assertFalse(GitHubClient(token="").authenticated)

    def test_it_falls_back_to_the_environment(self) -> None:
        os.environ["GITHUB_TOKEN"] = "ghp_from_env"
        self.assertTrue(GitHubClient().authenticated)

    def test_gh_token_is_the_second_fallback(self) -> None:
        os.environ["GH_TOKEN"] = "ghp_from_gh"
        self.assertTrue(GitHubClient().authenticated)

    def test_an_explicit_token_beats_the_environment(self) -> None:
        os.environ["GITHUB_TOKEN"] = "ghp_from_env"
        self.assertEqual(GitHubClient(token="ghp_explicit").token, "ghp_explicit")


class TestWebConnector(unittest.TestCase):
    def test_authority_defaults_below_a_repository(self) -> None:
        # An arbitrary page is weaker evidence than a project's own source.
        self.assertLess(WebConnector(["https://e.com/"]).authority,
                        GitHubConnector(owner="o", repo="r").authority)

    def test_the_key_names_the_seed(self) -> None:
        self.assertEqual(WebConnector(["https://e.com/a"]).key, "web:https://e.com/a")

    def test_no_seeds_still_constructs(self) -> None:
        self.assertEqual(WebConnector([]).key, "web:empty")

    def test_crawl_options_reach_the_config(self) -> None:
        connector = WebConnector(["https://e.com/"], max_pages=7, max_depth=2)
        self.assertEqual(connector.config.max_pages, 7)
        self.assertEqual(connector.config.max_depth, 2)


class TestCli(unittest.TestCase):
    def test_a_subcommand_is_required(self) -> None:
        with self.assertRaises(SystemExit):
            build_parser().parse_args([])

    def test_every_subcommand_binds_a_handler(self) -> None:
        for command in ("index", "query", "eval", "loop", "reachability", "skills",
                        "stats", "demo"):
            args = build_parser().parse_args(
                [command] + (["a question"] if command == "query" else [])
            )
            self.assertTrue(callable(args.func), command)

    def test_querying_an_empty_corpus_says_so_rather_than_answering(self) -> None:
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = main(["--db", ":memory:", "query", "anything at all"])
        self.assertEqual(code, EXIT_CANNOT_RUN)
        self.assertIn("empty", buf.getvalue())

    def test_linting_a_directory_with_no_skills_is_clean_not_an_error(self) -> None:
        self.assertEqual(main(["skills", "/nonexistent/skills"]), EXIT_OK)

    def test_exit_codes_are_distinct(self) -> None:
        # 1 means "ran and found something wrong"; 2 means "could not run".
        self.assertEqual((EXIT_OK, EXIT_FINDINGS, EXIT_CANNOT_RUN), (0, 1, 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
