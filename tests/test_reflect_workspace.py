"""Tests for the workspace file and git-history signal sources."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from oodarag.reflect.models import ACTOR_HUMAN, ACTOR_MACHINE, KIND_COMMIT, KIND_FILE
from oodarag.reflect.sources.base import Budget
from oodarag.reflect.sources.workspace import (
    GitHistorySource,
    GitIgnore,
    WorkspaceFileSource,
)

# Fixed so mtime-window assertions do not depend on when the suite runs.
MTIME = 1_756_300_000.0
NEWER = MTIME + 10_000.0

GITIGNORE = """
# noise
*.log
build/
/secret.txt
node_modules
!keep.log
"""

#: Every readable text file in the fixture tree, in walk order: root files
#: first, then directories, both sorted.
EXPECTED = [
    ".gitignore",
    "README.md",
    "notes.txt",
    ".github/workflows/ci.yml",
    "src/main.py",
    "src/deep/util.py",
    "sub/secret.txt",
    "tests/test_main.py",
]


class WorkspaceFileTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.build_tree()

    # -- fixtures ------------------------------------------------------------

    def write(self, rel: str, text: str, mtime: float = MTIME) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        os.utime(path, (mtime, mtime))
        return path

    def write_bytes(self, rel: str, raw: bytes, mtime: float = MTIME) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        os.utime(path, (mtime, mtime))
        return path

    def build_tree(self) -> None:
        self.write(".gitignore", GITIGNORE)
        self.write("README.md", "# Project\n\nSee docs/guide.md for the setup.\n")
        self.write("notes.txt", "buy milk\n")
        self.write("src/main.py", "def main() -> None:\n    pass\n")
        self.write("src/deep/util.py", "X = 1\n")
        self.write("tests/test_main.py", "def test_main():\n    assert True\n")
        self.write(".github/workflows/ci.yml", "on: push\n")
        # ignored by .gitignore, one pattern each
        self.write("app.log", "log line\n")
        self.write("keep.log", "negations are deliberately not honoured\n")
        self.write("secret.txt", "token\n")
        self.write("build/generated.py", "GENERATED = True\n")
        self.write("node_modules/pkg/index.js", "module.exports = {}\n")
        # anchored "/secret.txt" must not reach down into a subdirectory
        self.write("sub/secret.txt", "not the anchored one\n")
        # skipped by directory name rather than by pattern
        self.write(".cache/notes.md", "cached\n")
        self.write("__pycache__/x.py", "junk\n")
        # unreadable / not worth reading
        self.write_bytes("bin/blob.bin", b"\x00\x01\x02binary junk\n")
        self.write("big.txt", "x" * 500_001)
        self.write("empty.md", "")

    def signals(self, since: float = 0.0, budget: Budget | None = None, **config: object) -> list:
        source = WorkspaceFileSource(root=self.root, config=config)
        result = source.run(since=since, budget=budget)
        self.assertEqual(result.errors, [])
        self.last_source = source
        self.last_result = result
        return result.signals

    # -- happy path ----------------------------------------------------------

    def test_one_signal_per_text_file_in_walk_order(self) -> None:
        sigs = self.signals()

        self.assertEqual([s.uri for s in sigs], EXPECTED)
        self.assertEqual([s.ordinal for s in sigs], list(range(len(EXPECTED))))
        self.assertTrue(all(s.kind == KIND_FILE for s in sigs))
        self.assertTrue(all(s.actor == ACTOR_MACHINE for s in sigs))
        self.assertTrue(all(s.source == "workspace:files" for s in sigs))
        self.assertTrue(all(s.session == "workspace" for s in sigs))
        self.assertTrue(all(s.ts == MTIME for s in sigs))

        readme = _by_uri(sigs, "README.md")
        self.assertIn("See docs/guide.md", readme.text)

    def test_metadata_describes_the_file(self) -> None:
        sigs = self.signals()

        readme = _by_uri(sigs, "README.md").metadata
        self.assertEqual(readme["ext"], ".md")
        self.assertIs(readme["is_doc"], True)
        self.assertIs(readme["is_code"], False)
        self.assertIs(readme["is_test"], False)
        self.assertEqual(readme["depth"], 0)
        self.assertEqual(readme["line_count"], 3)
        self.assertEqual(readme["size"], (self.root / "README.md").stat().st_size)
        self.assertEqual(readme["mtime"], MTIME)

        deep = _by_uri(sigs, "src/deep/util.py").metadata
        self.assertEqual(deep["ext"], ".py")
        self.assertIs(deep["is_code"], True)
        self.assertIs(deep["is_doc"], False)
        self.assertEqual(deep["depth"], 2)

        # "test" anywhere in the path, directory included
        self.assertIs(_by_uri(sigs, "tests/test_main.py").metadata["is_test"], True)
        # a dotfile has a name, not an extension
        self.assertEqual(_by_uri(sigs, ".gitignore").metadata["ext"], "")

    # -- pruning and .gitignore ---------------------------------------------

    def test_gitignore_subset(self) -> None:
        uris = {s.uri for s in self.signals()}

        self.assertNotIn("app.log", uris)  # "*.log"
        self.assertNotIn("secret.txt", uris)  # "/secret.txt"
        self.assertNotIn("build/generated.py", uris)  # "build/"
        self.assertNotIn("node_modules/pkg/index.js", uris)
        # the anchored pattern must not reach a same-named file further down
        self.assertIn("sub/secret.txt", uris)
        # negation is dropped rather than approximated, so "keep.log" stays out
        self.assertNotIn("keep.log", uris)

    def test_gitignore_can_be_turned_off(self) -> None:
        uris = {s.uri for s in self.signals(use_gitignore=False)}

        self.assertIn("app.log", uris)
        self.assertIn("secret.txt", uris)
        # directory skips are not pattern-driven, so they still apply
        self.assertNotIn("build/generated.py", uris)
        self.assertNotIn("node_modules/pkg/index.js", uris)
        self.assertNotIn("__pycache__/x.py", uris)

    def test_dot_directories_are_skipped_except_github(self) -> None:
        uris = {s.uri for s in self.signals()}

        self.assertNotIn(".cache/notes.md", uris)
        self.assertIn(".github/workflows/ci.yml", uris)

    def test_git_directory_is_skipped_even_with_no_gitignore(self) -> None:
        (self.root / ".gitignore").unlink()
        self.write(".git/objects/pack/thing.txt", "loose object noise\n")
        self.write(".git/COMMIT_EDITMSG", "wip\n")

        uris = {s.uri for s in self.signals()}
        self.assertFalse([u for u in uris if u.startswith(".git/")])
        self.assertIn("app.log", uris)  # nothing else is filtered any more

    # -- hostile input -------------------------------------------------------

    def test_binary_oversized_and_empty_files_are_skipped_silently(self) -> None:
        sigs = self.signals()
        uris = {s.uri for s in sigs}

        self.assertNotIn("bin/blob.bin", uris)
        self.assertNotIn("big.txt", uris)
        self.assertNotIn("empty.md", uris)
        self.assertEqual(self.last_result.errors, [])
        self.assertGreaterEqual(self.last_source.skipped, 3)

    def test_undecodable_bytes_are_read_with_replacement(self) -> None:
        self.write_bytes("latin.md", "caf\xe9 pr\xe9cis\n".encode("latin-1"))
        text = _by_uri(self.signals(), "latin.md").text

        self.assertTrue(text)  # not silently dropped: it is text, just not utf-8
        self.assertIn("caf", text)

    def test_unreadable_gitignore_degrades_to_no_patterns(self) -> None:
        self.write_bytes(".gitignore", b"\x00\x00\x01binary\n")
        uris = {s.uri for s in self.signals()}

        self.assertEqual(self.last_result.errors, [])
        self.assertIn("app.log", uris)  # no patterns parsed, so nothing filtered

    def test_symlink_loop_does_not_hang_the_walk(self) -> None:
        try:
            (self.root / "loop").symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError) as e:  # unprivileged Windows, odd fs
            raise unittest.SkipTest(f"symlinks unavailable: {e}") from e

        sigs = self.signals()
        self.assertEqual([s.uri for s in sigs], EXPECTED)

    def test_missing_root_is_not_an_error(self) -> None:
        source = WorkspaceFileSource(root=self.root / "nope")
        result = source.run()

        self.assertFalse(source.available())
        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    # -- budgets and caps ----------------------------------------------------

    def test_max_file_bytes_is_configurable(self) -> None:
        sigs = self.signals(max_file_bytes=40)
        uris = {s.uri for s in sigs}

        self.assertIn("notes.txt", uris)  # 9 bytes
        self.assertNotIn("README.md", uris)  # 42 bytes
        self.assertTrue(all(s.metadata["size"] <= 40 for s in sigs))

    def test_max_files_caps_the_walk(self) -> None:
        sigs = self.signals(max_files=2)
        self.assertLessEqual(len(sigs), 2)

    def test_budget_max_signals_truncates(self) -> None:
        result = WorkspaceFileSource(root=self.root).run(budget=Budget(max_signals=3))

        self.assertEqual(len(result.signals), 3)
        self.assertTrue(result.truncated)
        self.assertEqual([s.uri for s in result.signals], EXPECTED[:3])

    def test_expired_wall_clock_yields_nothing(self) -> None:
        budget = Budget(wall_clock_s=0.0001)
        budget.started -= 10.0  # as if the source had already been running

        result = WorkspaceFileSource(root=self.root).run(budget=budget)
        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_per_signal_char_cap_comes_from_the_budget(self) -> None:
        result = WorkspaceFileSource(root=self.root).run(budget=Budget(max_chars_per_signal=10))

        readme = _by_uri(result.signals, "README.md")
        self.assertIn("[truncated]", readme.text)
        # the count is of the real file, not of the truncated copy
        self.assertEqual(readme.metadata["line_count"], 3)

    # -- windowing -----------------------------------------------------------

    def test_since_filters_on_mtime(self) -> None:
        self.write("src/main.py", "def main() -> None:\n    return\n", mtime=NEWER)

        sigs = self.signals(since=NEWER - 1)
        self.assertEqual([s.uri for s in sigs], ["src/main.py"])
        self.assertEqual(sigs[0].ordinal, 0)  # ordinals number what was emitted


class GitIgnoreMatcherTestCase(unittest.TestCase):
    """The matcher on its own, where its subset is easiest to pin down."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def load(self, text: str) -> GitIgnore:
        path = self.root / ".gitignore"
        path.write_text(text, encoding="utf-8")
        return GitIgnore.load(path)

    def test_comments_blanks_and_negations_are_dropped(self) -> None:
        ignore = self.load("# a comment\n\n   \n!important.log\n*.log\n")

        self.assertEqual(len(ignore), 1)
        self.assertTrue(ignore.match("important.log"))

    def test_name_patterns_match_at_any_depth(self) -> None:
        ignore = self.load("secrets.env\n")

        self.assertTrue(ignore.match("secrets.env"))
        self.assertTrue(ignore.match("a/b/secrets.env"))
        self.assertFalse(ignore.match("a/secrets.env.example"))

    def test_leading_slash_anchors_to_the_root(self) -> None:
        ignore = self.load("/dist\n")

        self.assertTrue(ignore.match("dist", is_dir=True))
        self.assertTrue(ignore.match("dist/app.js"))
        self.assertFalse(ignore.match("packages/dist/app.js"))

    def test_trailing_slash_is_directory_only(self) -> None:
        ignore = self.load("cache/\n")

        self.assertTrue(ignore.match("cache", is_dir=True))
        self.assertFalse(ignore.match("cache", is_dir=False))  # a *file* named cache
        self.assertTrue(ignore.match("a/cache/x.txt"))  # an ancestor still counts

    def test_interior_slash_anchors_and_globs(self) -> None:
        ignore = self.load("docs/*.gen.md\n")

        self.assertTrue(ignore.match("docs/api.gen.md"))
        self.assertFalse(ignore.match("api.gen.md"))
        self.assertFalse(ignore.match("site/docs/api.gen.md"))

    def test_missing_file_matches_nothing(self) -> None:
        ignore = GitIgnore.load(self.root / "absent")

        self.assertEqual(len(ignore), 0)
        self.assertFalse(ignore.match("anything/at/all.py"))


def _git_available() -> bool:
    return shutil.which("git") is not None


class GitHistoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        if not _git_available():
            raise unittest.SkipTest("git is not installed")
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.git("init", "-q", ".")
        self.git("config", "user.email", "dev@example.com")
        self.git("config", "user.name", "T Dev")
        self.git("config", "commit.gpgsign", "false")

    # -- fixtures ------------------------------------------------------------

    def git(self, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            raise unittest.SkipTest(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout

    def commit(self, message: str, files: dict[str, str]) -> None:
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def two_commits(self) -> None:
        self.commit("add the reader", {"reader.py": "X = 1\n"})
        self.commit(
            "rename the reader\n\nThe old name said how it worked,\nnot what it was for.\n",
            {"reader.py": "X = 1\nY = 2\n", "docs/reader.md": "# Reader\n"},
        )

    def signals(self, since: float = 0.0, budget: Budget | None = None, **config: object) -> list:
        source = GitHistorySource(root=self.root, config=config)
        result = source.run(since=since, budget=budget)
        self.assertEqual(result.errors, [])
        self.last_result = result
        return result.signals

    # -- happy path ----------------------------------------------------------

    def test_commits_become_signals_newest_first(self) -> None:
        self.two_commits()
        sigs = self.signals()

        self.assertEqual(len(sigs), 2)
        self.assertEqual([s.ordinal for s in sigs], [0, 1])
        self.assertTrue(all(s.kind == KIND_COMMIT for s in sigs))
        self.assertTrue(all(s.actor == ACTOR_HUMAN for s in sigs))
        self.assertTrue(all(s.source == "git:log" for s in sigs))
        self.assertTrue(all(s.session == "git" for s in sigs))
        self.assertTrue(all(s.ts > 1_500_000_000 for s in sigs))

        newest, oldest = sigs
        self.assertEqual(newest.metadata["subject"], "rename the reader")
        self.assertEqual(oldest.metadata["subject"], "add the reader")

    def test_multiline_body_survives_intact(self) -> None:
        self.two_commits()
        newest = self.signals()[0]

        self.assertTrue(newest.text.startswith("rename the reader\n\n"))
        self.assertIn("The old name said how it worked,", newest.text)
        self.assertIn("not what it was for.", newest.text)
        # a body-less commit is its subject and nothing more
        self.assertEqual(self.signals()[1].text, "add the reader")

    def test_metadata_carries_sha_author_and_diffstat(self) -> None:
        self.two_commits()
        newest = self.signals()[0]
        meta = newest.metadata

        self.assertEqual(len(meta["sha"]), 40)
        self.assertEqual(newest.uri, "git:" + meta["sha"][:12])
        self.assertEqual(meta["author"], "T Dev")
        self.assertEqual(sorted(meta["files"]), ["docs/reader.md", "reader.py"])
        self.assertEqual(meta["insertions"], 2)  # one new line, one new file
        self.assertEqual(meta["deletions"], 0)

        oldest = self.signals()[1].metadata
        self.assertEqual(oldest["files"], ["reader.py"])
        self.assertEqual(oldest["insertions"], 1)

    def test_available_needs_a_git_entry(self) -> None:
        self.assertTrue(GitHistorySource(root=self.root).available())
        self.assertFalse(GitHistorySource(root=self.root / "sub").available())

    # -- windowing and caps --------------------------------------------------

    def test_since_narrows_the_window(self) -> None:
        self.two_commits()
        now = self.signals()[0].ts

        self.assertEqual(len(self.signals(since=now - 86_400)), 2)
        self.assertEqual(self.signals(since=now + 86_400), [])

    def test_max_commits_caps_the_log(self) -> None:
        self.commit("one", {"a.txt": "1\n"})
        self.commit("two", {"a.txt": "2\n"})
        self.commit("three", {"a.txt": "3\n"})

        sigs = self.signals(max_commits=2)
        self.assertEqual([s.metadata["subject"] for s in sigs], ["three", "two"])

    def test_budget_max_signals_truncates(self) -> None:
        self.two_commits()
        result = GitHistorySource(root=self.root).run(budget=Budget(max_signals=1))

        self.assertEqual(len(result.signals), 1)
        self.assertTrue(result.truncated)

    # -- hostile input -------------------------------------------------------

    def test_a_body_that_looks_like_numstat_is_not_read_as_a_file_list(self) -> None:
        self.commit("looks like a diff\n\n9\t9\tnot-a-file.txt\n", {"real.py": "X = 1\n"})
        meta = self.signals()[0].metadata

        self.assertEqual(meta["files"], ["real.py"])
        self.assertEqual(meta["insertions"], 1)
        self.assertIn("not-a-file.txt", self.signals()[0].text)

    def test_separators_pasted_into_a_message_do_not_desync_the_parse(self) -> None:
        self.commit("first", {"a.txt": "1\n"})
        self.commit("hostile \x1f and \x1e in the subject", {"b.txt": "2\n"})
        sigs = self.signals()

        # The record may be unreadable, but the *other* commit must survive and
        # no exception may escape.
        self.assertEqual(self.last_result.errors, [])
        self.assertIn("first", [s.metadata["subject"] for s in sigs])

    def test_an_empty_repository_yields_nothing(self) -> None:
        result = GitHistorySource(root=self.root).run()

        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_binary_files_do_not_break_the_diffstat(self) -> None:
        (self.root / "blob.bin").write_bytes(b"\x00\x01\x02\x03")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "add a blob")
        meta = self.signals()[0].metadata

        self.assertEqual(meta["files"], ["blob.bin"])  # numstat reports "-" counts
        self.assertEqual(meta["insertions"], 0)


class GitDegradationTestCase(unittest.TestCase):
    """Failure paths, none of which need git to be installed."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_a_plain_directory_is_unavailable_and_yields_nothing(self) -> None:
        source = GitHistorySource(root=self.root)
        result = source.run()

        self.assertFalse(source.available())
        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_a_broken_gitfile_yields_nothing_without_raising(self) -> None:
        if not _git_available():
            raise unittest.SkipTest("git is not installed")
        (self.root / ".git").write_text("gitdir: /nowhere/at/all\n", encoding="utf-8")

        source = GitHistorySource(root=self.root)
        result = source.run()

        self.assertTrue(source.available())  # the entry exists...
        self.assertEqual(result.signals, [])  # ...but git refuses it
        self.assertEqual(result.errors, [])

    def test_git_not_installed_degrades_to_nothing(self) -> None:
        (self.root / ".git").mkdir()
        with mock.patch(
            "oodarag.reflect.sources.workspace.subprocess.run", side_effect=FileNotFoundError("git")
        ):
            result = GitHistorySource(root=self.root).run()

        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_a_timeout_degrades_to_nothing(self) -> None:
        (self.root / ".git").mkdir()
        boom = subprocess.TimeoutExpired(cmd=["git"], timeout=1.0)
        with mock.patch(
            "oodarag.reflect.sources.workspace.subprocess.run", side_effect=boom
        ):
            result = GitHistorySource(root=self.root, config={"timeout_s": 1}).run()

        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_garbage_on_stdout_is_parsed_into_nothing(self) -> None:
        (self.root / ".git").mkdir()
        source = GitHistorySource(root=self.root)
        source._git_log = lambda since: "not a record\n1\t2\tstray.txt\n\x1e\x1fhalf\x1fa\x1erecord"

        result = source.run()
        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_a_record_with_an_unreadable_timestamp_still_yields_the_commit(self) -> None:
        (self.root / ".git").mkdir()
        sha = "a" * 40
        source = GitHistorySource(root=self.root)
        source._git_log = lambda since: f"{sha}\x1fnot-a-clock\x1fT Dev\x1fsubject\x1f\x1e\n"

        sigs = source.run().signals
        self.assertEqual(len(sigs), 1)
        self.assertEqual(sigs[0].ts, 0.0)
        self.assertEqual(sigs[0].metadata["sha"], sha)
        self.assertEqual(sigs[0].text, "subject")

    def test_a_commit_touching_thousands_of_files_caps_its_path_list(self) -> None:
        (self.root / ".git").mkdir()
        sha = "b" * 40
        stat = "".join(f"1\t0\tf{i}.txt\n" for i in range(500))
        header = f"{sha}\x1f1756300000\x1fT Dev\x1fvendor bump\x1f\x1e\n"
        source = GitHistorySource(root=self.root)
        source._git_log = lambda since: header + stat

        meta = source.run().signals[0].metadata
        self.assertEqual(len(meta["files"]), 200)
        self.assertEqual(meta["insertions"], 500)  # counted in full, listed in part


def _by_uri(signals: list, uri: str):
    match = [s for s in signals if s.uri == uri]
    if not match:
        raise AssertionError(f"no signal for {uri!r} in {[s.uri for s in signals]}")
    return match[0]


if __name__ == "__main__":
    unittest.main()
