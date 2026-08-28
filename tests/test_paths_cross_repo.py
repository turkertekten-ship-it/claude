"""Cross-repository path references.

A repository that documents its sibling names that sibling's files on purpose.
Reporting those as missing is the checker inventing a contradiction out of a
tree it was never given - so without the sibling the verdict is UNVERIFIABLE,
and with `--sibling` it is resolved for real. Neither answer is a guess.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.paths import PathsChecker, _foreign_slug, _own_slug
from tools.claims import RepoIndex, SourceFile
from tools.registry import CheckConfig

GIT_CONFIG = """[core]
\trepositoryformatversion = 0
[remote "origin"]
\turl = https://github.com/acme/downstream
\tfetch = +refs/heads/*:refs/remotes/origin/*
"""


def build(tmp: str, readme: str, *, origin: str = GIT_CONFIG) -> Path:
    root = Path(tmp)
    (root / ".git").mkdir(exist_ok=True)
    (root / ".git" / "config").write_text(origin)
    (root / "README.md").write_text(readme)
    return root


class TestOwnSlug(unittest.TestCase):
    def test_slug_from_https_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = build(tmp, "# x\n")
            self.assertEqual(_own_slug(RepoIndex(root)), "acme/downstream")

    def test_slug_from_ssh_remote(self):
        ssh = '[remote "origin"]\n\turl = git@github.com:acme/downstream.git\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = build(tmp, "# x\n", origin=ssh)
            self.assertEqual(_own_slug(RepoIndex(root)), "acme/downstream")

    def test_no_git_config_disables_the_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("# x\n")
            self.assertEqual(_own_slug(RepoIndex(Path(tmp))), "")


class TestForeignSlugDetection(unittest.TestCase):
    def test_own_slug_is_not_foreign(self):
        src = SourceFile(Path("README.md"), "README.md",
                         "Doctrine is in `acme/downstream` — its `tools/`.\n")
        self.assertEqual(_foreign_slug(src, 1, "acme/downstream"), "")

    def test_other_slug_is_foreign(self):
        src = SourceFile(Path("README.md"), "README.md",
                         "Doctrine is in `acme/upstream` — its `tools/`.\n")
        self.assertEqual(_foreign_slug(src, 1, "acme/downstream"), "acme/upstream")

    def test_a_path_is_not_mistaken_for_a_slug(self):
        src = SourceFile(Path("README.md"), "README.md", "See `docs/guide.md` for more.\n")
        self.assertEqual(_foreign_slug(src, 1, "acme/downstream"), "")


class TestCheckerBehaviour(unittest.TestCase):
    README = (
        "# Downstream\n\n"
        "Doctrine lives in `acme/upstream` — its `provenance/` and its `tools/`.\n"
    )

    def _run(self, root: Path, **kw):
        return list(PathsChecker().check(RepoIndex(root), CheckConfig(**kw)))

    def test_without_sibling_the_verdict_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._run(build(tmp, self.README))
            self.assertTrue(findings, "the reference should be reported, not dropped")
            for f in findings:
                self.assertEqual(f.code, "PATH_IN_OTHER_REPO")
                self.assertEqual(f.verdict.value, "unverifiable")
                self.assertFalse(f.is_problem, "an unchecked reference must not fail the run")
                self.assertIn("acme/upstream", f.detail)

    def test_with_sibling_present_references_resolve_silently(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sib:
            root = build(tmp, self.README)
            (Path(sib) / "upstream" / "provenance").mkdir(parents=True)
            (Path(sib) / "upstream" / "tools").mkdir(parents=True)
            findings = self._run(root, sibling_roots=(str(Path(sib) / "upstream"),))
            self.assertEqual(findings, [])

    def test_with_sibling_missing_the_file_stays_unverifiable(self):
        # The sibling exists but does not contain the path. This checker still
        # declines to call it broken: it can see one tree, not the sibling's
        # history, and the reference may name a file added on another branch.
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as sib:
            root = build(tmp, self.README)
            (Path(sib) / "upstream").mkdir(parents=True)
            findings = self._run(root, sibling_roots=(str(Path(sib) / "upstream"),))
            self.assertTrue(all(f.code == "PATH_IN_OTHER_REPO" for f in findings))

    def test_a_local_broken_path_is_still_an_error(self):
        readme = "# Downstream\n\nSee `docs/nope.md` for details.\n"
        with tempfile.TemporaryDirectory() as tmp:
            findings = self._run(build(tmp, readme))
            self.assertEqual([f.code for f in findings], ["PATH_MISSING"])
            self.assertTrue(findings[0].is_problem)


if __name__ == "__main__":
    unittest.main()


class TestSlugShapeIsNotEnough(unittest.TestCase):
    """`packages/api` and `owner/repo` are the same shape.

    Regression: shape alone scoped every path near a two-segment directory
    reference to an imaginary other project, so a comment mentioning
    `packages/api/pyproject.toml` reported it unverifiable instead of checking it.
    """

    def _findings(self, readme: str):
        with tempfile.TemporaryDirectory() as tmp:
            return list(PathsChecker().check(RepoIndex(build(tmp, readme)), CheckConfig()))

    def test_a_directory_pair_does_not_scope_paths_elsewhere(self):
        readme = "# T\n\nIn a workspace, `packages/api` declares it in `packages/api/pyproject.toml`.\n"
        codes = [f.code for f in self._findings(readme)]
        self.assertNotIn("PATH_IN_OTHER_REPO", codes)

    def test_a_slug_with_a_repository_cue_still_scopes(self):
        readme = "# T\n\nDoctrine is in the `acme/upstream` repository — its `provenance/`.\n"
        codes = [f.code for f in self._findings(readme)]
        self.assertIn("PATH_IN_OTHER_REPO", codes)


class TestHostlikeTokens(unittest.TestCase):
    """`github.com/robots.txt` is a URL without its scheme, not a repo path."""

    def _codes(self, readme: str):
        with tempfile.TemporaryDirectory() as tmp:
            return [f.code for f in PathsChecker().check(RepoIndex(build(tmp, readme)),
                                                         CheckConfig())]

    def test_a_bare_hostname_path_is_not_a_repo_path(self):
        for token in ("github.com/robots.txt", "example.org/index.html",
                      "docs.python.org/3/library/ast.html", "pypi.org/simple/"):
            with self.subTest(token=token):
                self.assertEqual(self._codes(f"# T\n\nSee `{token}` for details.\n"), [])

    def test_a_real_broken_repo_path_is_still_reported(self):
        # Not named "missing.md": _ABSENCE_RE matches the word "missing", so a
        # fixture using it would be suppressed by the guard that exists to stop
        # the checker contradicting prose which says a path is absent.
        self.assertEqual(self._codes("# T\n\nSee `docs/guide.md`.\n"), ["PATH_MISSING"])

    def test_a_directory_that_merely_contains_a_dot_is_still_checked(self):
        # `my.package/thing.py` is not a hostname; the TLD list is what
        # separates the two, and over-matching here would silence real findings.
        self.assertEqual(self._codes("# T\n\nSee `my.package/thing.py`.\n"), ["PATH_MISSING"])
