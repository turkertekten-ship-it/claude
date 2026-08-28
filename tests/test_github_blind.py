"""Blind cross-check of the GitHub connector against local git.

The connector reads a repository over the network: the REST API for metadata
and the tree, `raw.githubusercontent.com` for file bytes. This test verifies
that result against a *completely independent* path to the same truth - the
`git` binary operating on the local clone.

Two independent implementations reading the same repository must agree. Nothing
here is hardcoded from a previous run: every expectation is computed from
`git ls-tree` and `git cat-file` at test time, so the test stays valid as the
repository changes.

Skipped when there is no network, no token, or when the local checkout does not
match the pushed head (an unpushed commit would make the two sides legitimately
disagree).
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from oodarag.ingest.base import MemoryStateStore
from oodarag.ingest.github import GitHubConnector
from oodarag.util.http import HttpError, TransportError
from oodarag.util.text import redact_secrets

REPO_ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True, text=True, check=True,
    ).stdout


def git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True, check=True,
    ).stdout


def _remote_slug() -> tuple[str, str] | None:
    try:
        url = git("remote", "get-url", "origin").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    url = url.removesuffix(".git")
    if "github.com" not in url:
        return None
    tail = url.split("github.com", 1)[1].lstrip(":/")
    parts = tail.split("/")
    return (parts[0], parts[1]) if len(parts) >= 2 else None


class GitHubBlindCrossCheckTest(unittest.TestCase):
    """Two independent readers of one repository must produce identical bytes."""

    @classmethod
    def setUpClass(cls):
        if os.environ.get("OODARAG_SKIP_NETWORK_TESTS"):
            raise unittest.SkipTest("network tests disabled")
        slug = _remote_slug()
        if slug is None:
            raise unittest.SkipTest("not a GitHub clone")
        cls.owner, cls.repo = slug
        if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
            raise unittest.SkipTest("no GitHub token available")

        cls.branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
        cls.local_head = git("rev-parse", "HEAD").strip()

        connector = GitHubConnector(
            owner=cls.owner, repo=cls.repo, ref=cls.branch,
            resources=("repo", "readme", "files"),
        )
        try:
            cls.result = connector.run(MemoryStateStore())
        except (HttpError, TransportError) as e:
            raise unittest.SkipTest(f"GitHub unreachable: {e}") from e
        cls.connector = connector
        if connector.stats.get("head_sha") != cls.local_head:
            raise unittest.SkipTest(
                f"local HEAD {cls.local_head[:8]} != remote head "
                f"{str(connector.stats.get('head_sha'))[:8]}; push first"
            )

        # Ground truth, straight from git.
        cls.tree: dict[str, tuple[str, int]] = {}
        # Pin to the sha captured above, not the moving `HEAD` ref. The remote
        # fetch between them takes seconds, and a commit landing in that window
        # would leave the two sides describing different trees — which surfaces
        # as a byte mismatch that looks like a connector bug and is not one.
        for line in git("ls-tree", "-r", "-l", cls.local_head).splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) >= 4 and parts[1] == "blob":
                size = int(parts[3]) if parts[3].isdigit() else 0
                cls.tree[path] = (parts[2], size)

        cls.files = {d.metadata["path"]: d for d in cls.result.documents
                     if d.metadata.get("kind") == "file"}

    def test_the_run_reported_no_failures(self):
        self.assertEqual(self.result.delta.failed, 0, self.result.delta.errors)
        self.assertGreater(len(self.result.documents), 3)

    def test_every_returned_file_exists_in_the_git_tree(self):
        unknown = set(self.files) - set(self.tree)
        self.assertEqual(unknown, set(), f"connector invented paths: {sorted(unknown)}")

    def test_blob_shas_match_git_exactly(self):
        for path, doc in self.files.items():
            with self.subTest(path=path):
                self.assertEqual(
                    doc.metadata["blob_sha"], self.tree[path][0],
                    "connector reported a blob sha git disagrees with",
                )

    def test_file_contents_match_git_byte_for_byte(self):
        """The strongest assertion here: the bytes GitHub served are the bytes
        git has, after the redaction the connector is documented to apply."""
        checked = 0
        for path, doc in self.files.items():
            with self.subTest(path=path):
                local = git_bytes("cat-file", "blob", self.tree[path][0]).decode("utf-8", "replace")
                self.assertEqual(doc.text, redact_secrets(local),
                                 f"content mismatch for {path}")
                checked += 1
        self.assertGreater(checked, 3, "too few files compared to be meaningful")

    def test_no_source_file_is_silently_missed(self):
        """Recall check on an unambiguous subset: every .py file under src/ that
        is comfortably inside the size cap must have been returned."""
        expected = {
            path for path, (_, size) in self.tree.items()
            if path.startswith("src/") and path.endswith(".py")
            and size < self.connector.max_file_bytes
        }
        missing = expected - set(self.files)
        self.assertEqual(missing, set(), f"connector missed source files: {sorted(missing)}")
        self.assertGreater(len(expected), 5, "sanity: expected several source files")

    def test_permalinks_pin_the_commit_not_the_branch(self):
        for path, doc in self.files.items():
            with self.subTest(path=path):
                self.assertIn(f"/blob/{self.local_head}/", doc.uri,
                              "URI is not pinned to an immutable commit sha")
                self.assertTrue(doc.uri.endswith(path))

    def test_lockfiles_and_binaries_are_excluded(self):
        for path in self.files:
            with self.subTest(path=path):
                self.assertFalse(path.endswith((".lock", ".png", ".jpg", ".zip", ".whl")))
                self.assertNotIn("__pycache__", path)
                self.assertNotIn("node_modules", path)

    def test_language_is_inferred_correctly(self):
        for path, doc in self.files.items():
            if path.endswith(".py"):
                with self.subTest(path=path):
                    self.assertEqual(doc.metadata["language"], "python")

    def test_test_files_are_flagged_for_filtering(self):
        for path, doc in self.files.items():
            if path.startswith("tests/") and path.endswith(".py"):
                with self.subTest(path=path):
                    self.assertTrue(doc.metadata["is_test"],
                                    "a test file was not flagged as such")

    def test_head_unchanged_short_circuits_the_second_run(self):
        state = MemoryStateStore()
        first = GitHubConnector(owner=self.owner, repo=self.repo, ref=self.branch,
                                resources=("files",))
        first_result = first.run(state)
        self.assertGreater(len(first_result.documents), 0)
        before = first.gh.client.stats["requests"]

        second = GitHubConnector(owner=self.owner, repo=self.repo, ref=self.branch,
                                 resources=("files",), gh=first.gh)
        second_result = second.run(state)
        after = second.gh.client.stats["requests"]

        self.assertEqual(len(second_result.documents), 0,
                         "unchanged repository re-emitted documents")
        self.assertEqual(second.stats["skipped"].get("head_unchanged"), len(first_result.documents))
        # Two calls (repo metadata + head commit), not one per file.
        self.assertLessEqual(after - before, 4,
                             f"short circuit still made {after - before} requests")


if __name__ == "__main__":
    unittest.main()
