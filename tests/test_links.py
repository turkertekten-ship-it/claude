"""URL checks. The load-bearing case is what happens with the network off."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.links import LinksChecker, _clean, _github_slug, _urls
from tools.claims import RepoIndex
from tools.registry import CheckConfig

ORIGIN = '[remote "origin"]\n\turl = https://github.com/acme/widget\n'


def repo(tmp: str, readme: str, *, origin: str | None = ORIGIN) -> Path:
    root = Path(tmp)
    if origin is not None:
        (root / ".git").mkdir(exist_ok=True)
        (root / ".git" / "config").write_text(origin)
    (root / "README.md").write_text(readme)
    return root


def run(root: Path, **kw):
    return list(LinksChecker().check(RepoIndex(root), CheckConfig(**kw)))


class TestExtraction(unittest.TestCase):
    def test_sentence_punctuation_is_not_part_of_the_url(self):
        self.assertEqual(_clean("https://a.com/x."), "https://a.com/x")
        self.assertEqual(_clean("(https://a.com/x)"), "(https://a.com/x")

    def test_github_slug(self):
        self.assertEqual(_github_slug("https://github.com/acme/widget/blob/main/x.py"),
                         "acme/widget")
        self.assertEqual(_github_slug("https://github.com/acme/widget.git"), "acme/widget")
        self.assertEqual(_github_slug("https://pypi.org/project/x"), "")

    def test_urls_carry_their_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# T\n\nSee https://github.com/acme/widget for more.\n")
            found = _urls(RepoIndex(root))
            self.assertEqual([(c.line, u) for c, u in found],
                             [(3, "https://github.com/acme/widget")])


class TestOfflineVerdicts(unittest.TestCase):
    def _codes(self, readme: str, **kw) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return [f.code for f in run(repo(tmp, readme), **kw)]

    def test_reachability_is_one_aggregate_unverifiable_not_one_per_link(self):
        readme = ("# T\n\nhttps://github.com/acme/widget\n"
                  "https://docs.python.org/3/\nhttps://pypi.org/project/x\n")
        codes = self._codes(readme)
        self.assertEqual(codes.count("LINK_REACHABILITY_UNCHECKED"), 1)

    def test_the_aggregate_finding_is_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = run(repo(tmp, "# T\n\nhttps://github.com/acme/widget\n"))
            self.assertTrue(all(not f.is_problem for f in findings))

    def test_a_malformed_scheme_is_an_error(self):
        self.assertIn("LINK_MALFORMED", self._codes("# T\n\nhtp://example.io/x\n"))

    def test_a_placeholder_host_is_a_warning(self):
        self.assertIn("LINK_PLACEHOLDER", self._codes("# T\n\nSet the base to https://example.com/api\n"))

    def test_a_line_that_says_example_is_demonstrating_not_shipping(self):
        codes = self._codes("# T\n\nFor example, https://example.com/api works.\n")
        self.assertNotIn("LINK_PLACEHOLDER", codes)

    def test_a_link_naming_another_repository_is_flagged(self):
        codes = self._codes("# T\n\nSee https://github.com/someone-else/other for details.\n")
        self.assertIn("LINK_WRONG_REPO", codes)

    def test_a_link_naming_this_repository_is_not_flagged(self):
        codes = self._codes("# T\n\nSee https://github.com/acme/widget for details.\n")
        self.assertNotIn("LINK_WRONG_REPO", codes)

    def test_without_a_git_origin_the_repo_rule_is_silent(self):
        # Not knowing what "this repository" is called is a reason to say
        # nothing, not a reason to flag every GitHub link in the tree.
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# T\n\nhttps://github.com/someone-else/other\n", origin=None)
            self.assertNotIn("LINK_WRONG_REPO", [f.code for f in run(root)])

    def test_a_repo_with_no_urls_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run(repo(tmp, "# T\n\nNothing here.\n")), [])


if __name__ == "__main__":
    unittest.main()
