"""Tests for the `paths` checker.

Every fixture is a real directory tree written to disk. `RepoIndex` is never
monkeypatched, because the thing under test is precisely whether a reference in
prose survives a real filesystem lookup - a stubbed lookup would test the stub.

The bulk of these are negative cases. That is deliberate: this checker's failure
mode is not missing a broken path, it is reporting `application/json` as one.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.paths import PathsChecker
from tools.claims import RepoIndex
from tools.evidence import EvidenceKind, Severity, Verdict
from tools.registry import CheckConfig, registered


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


class PathsCheckerCase(unittest.TestCase):
    def findings(self, files: dict[str, str], config: CheckConfig | None = None):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(root, files)
        repo = RepoIndex(root)
        return root, list(PathsChecker().check(repo, config or CheckConfig()))

    def tokens(self, files: dict[str, str]) -> list[str]:
        """The paths reported, pulled out of each finding's detail."""
        _, found = self.findings(files)
        return [f.detail.split("'")[1] for f in found]


class TruePositives(PathsCheckerCase):
    def test_missing_path_in_prose_is_contradicted(self):
        root, found = self.findings(
            {"README.md": "# P\n\nProgress lives in `internal/PLAN.md` until then.\n"}
        )
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.code, "PATH_MISSING")
        self.assertEqual(finding.verdict, Verdict.CONTRADICTED)
        self.assertEqual(finding.severity, Severity.ERROR)
        self.assertEqual(finding.checker, "paths")
        self.assertEqual(finding.claim.path, "README.md")
        self.assertEqual(finding.claim.line, 3)
        self.assertIn("internal/PLAN.md", finding.detail)

    def test_claim_is_quoted_verbatim_from_the_line(self):
        root, found = self.findings(
            {"README.md": "# P\n\nProgress lives in `internal/PLAN.md` until then.\n"}
        )
        claim = found[0].claim
        line = (root / claim.path).read_text().split("\n")[claim.line - 1]
        self.assertIn(claim.text, line)

    def test_evidence_names_both_the_citation_and_the_search_space(self):
        root, found = self.findings({"README.md": "See `docs/nope.md` for details.\n"})
        kinds = [e.kind for e in found[0].evidence]
        self.assertIn(EvidenceKind.FILE, kinds)
        self.assertIn(EvidenceKind.ABSENCE, kinds)
        absence = next(e for e in found[0].evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertEqual(absence.searched, (str(root.resolve()),))
        cited = next(e for e in found[0].evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual(cited.path, "README.md")
        self.assertEqual(cited.line, 1)

    def test_markdown_link_to_a_missing_relative_target(self):
        self.assertEqual(
            self.tokens({"README.md": "Read the [guide](./docs/guide.md) first.\n"}),
            ["./docs/guide.md"],
        )

    def test_missing_directory_written_with_a_trailing_slash(self):
        self.assertEqual(
            self.tokens({"README.md": "Doctrine lives in `prompts/` alongside the rest.\n"}),
            ["prompts/"],
        )

    def test_python_comment_and_docstring_are_scanned(self):
        tokens = self.tokens(
            {
                "src/pkg/__init__.py": "",
                "src/pkg/a.py": (
                    '"""Reads the fixtures in eval/goldens.jsonl."""\n'
                    "\n"
                    "# budget table lives in conf/limits.yaml\n"
                    "X = 1\n"
                ),
            }
        )
        self.assertEqual(sorted(tokens), ["conf/limits.yaml", "eval/goldens.jsonl"])

    def test_makefile_and_pyproject_raw_text_are_scanned(self):
        tokens = self.tokens(
            {
                "Makefile": "eval: ## run against evals/goldens.jsonl\n\t@true\n",
                "pyproject.toml": '# See docs/adr/0001-core.md\ndependencies = []\n',
            }
        )
        self.assertEqual(
            sorted(tokens), ["docs/adr/0001-core.md", "evals/goldens.jsonl"]
        )


class TrueNegatives(PathsCheckerCase):
    def test_a_path_that_exists_is_not_reported(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": "The plan is in `internal/PLAN.md`.\n",
                    "internal/PLAN.md": "# Plan\n",
                }
            ),
            [],
        )

    def test_existing_directory_needs_no_trailing_slash(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": "Doctrine lives in `docs/adr` and nowhere else.\n",
                    "docs/adr/0001-core.md": "# ADR\n",
                }
            ),
            [],
        )

    def test_abbreviated_path_resolves_against_the_real_tree(self):
        # A README that writes `util/http.py` for src/pkg/util/http.py is
        # abbreviating, not citing something that is missing.
        self.assertEqual(
            self.tokens(
                {
                    "README.md": "| HTTP | `util/http.py` | urllib client |\n",
                    "src/pkg/util/http.py": "X = 1\n",
                }
            ),
            [],
        )

    def test_path_resolving_through_a_source_root(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": "Models are declared in `pkg/models.py`.\n",
                    "src/pkg/models.py": "X = 1\n",
                }
            ),
            [],
        )

    def test_sibling_reference_from_inside_a_package(self):
        self.assertEqual(
            self.tokens(
                {
                    "src/pkg/a.py": '"""Delegates to scrape/robots.py for policy."""\n',
                    "src/pkg/scrape/robots.py": "X = 1\n",
                }
            ),
            [],
        )

    def test_markdown_link_to_a_target_that_exists(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": "Read the [guide](./docs/guide.md) first.\n",
                    "docs/guide.md": "# Guide\n",
                }
            ),
            [],
        )


class AmbiguityStaysSilent(PathsCheckerCase):
    """CONTRACT rule 6: when the token cannot be decided, say nothing."""

    def test_urls_are_not_filesystem_paths(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": (
                        "Fetched from https://example.com/docs/x.md and\n"
                        "http://example.com/a.py, or mail to mailto:x@example.com.\n"
                    )
                }
            ),
            [],
        )

    def test_absolute_system_paths_are_the_hosts_business(self):
        self.assertEqual(
            self.tokens(
                {"README.md": "Installed to /usr/share/pkg/x.md, config in /etc/pkg.cfg.\n"}
            ),
            [],
        )

    def test_placeholder_segments_are_shapes_not_names(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": (
                        "Each checker ships `tests/test_<name>.py`.\n"
                        "Config goes in `{env}/settings.yaml` or `$HOME/pkg.toml`.\n"
                        "Everything under `docs/*.md` is generated.\n"
                        "Run `curl ... | sh` never; see `a/.../b.py`.\n"
                    )
                }
            ),
            [],
        )

    def test_slash_idioms_that_are_not_paths(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": (
                        "| Accept | `application/json` | and `text/html` |\n"
                        "Opened in read/write mode, and/or appended, at 2 requests/second,\n"
                        "24/7, keyed by `github:owner/repo`.\n"
                    )
                }
            ),
            [],
        )

    def test_bare_filename_with_no_directory_is_a_name_not_a_path(self):
        # `PLAN.md` here is an illustration of "a name is not its contents", and
        # robots.txt belongs to someone else's host. Neither is decidable from
        # this tree, so neither is reported.
        self.assertEqual(
            self.tokens(
                {
                    "SKILL.md": "A file called `PLAN.md` tells you a label exists.\n",
                    "src/pkg/robots.py": '"""Honours the robots.txt of each host."""\n',
                }
            ),
            [],
        )

    def test_dotted_module_names_belong_to_the_symbols_checker(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": "Entry point is `pkg.cli:main`, built on `tools.registry`.\n"
                }
            ),
            [],
        )

    def test_fenced_examples_are_illustrations(self):
        self.assertEqual(
            self.tokens(
                {
                    "README.md": (
                        "# P\n\n```bash\ncat nope/missing.md\n```\n\nDone.\n"
                    )
                }
            ),
            [],
        )

    def test_indented_examples_are_illustrations(self):
        self.assertEqual(
            self.tokens(
                {"README.md": "# P\n\nExample:\n\n    open('nope/missing.md')\n\nDone.\n"}
            ),
            [],
        )

    def test_indented_bullets_are_still_prose(self):
        # Nesting a list is not quoting code, so the guard above must not
        # swallow a real reference indented as a sub-bullet.
        self.assertEqual(
            self.tokens({"README.md": "# P\n\n- Top\n    - See `internal/PLAN.md`\n"}),
            ["internal/PLAN.md"],
        )

    def test_relative_prefix_outside_a_markdown_link_is_a_demonstration(self):
        self.assertEqual(
            self.tokens(
                {"src/pkg/a.py": '"""A README promises `./scripts/setup.sh` works."""\n'}
            ),
            [],
        )


class AbsenceProseIsNotContradicted(PathsCheckerCase):
    """CONTRACT rule 4: absence evidence agrees with prose asserting absence."""

    def test_prose_saying_the_path_does_not_exist(self):
        self.assertEqual(
            self.tokens(
                {
                    "provenance/observations.md": (
                        "# Observations\n\n"
                        "The harness has no goldens: `evals/goldens.jsonl` does not\n"
                        "exist, and no target has been set.\n"
                    )
                }
            ),
            [],
        )

    def test_absence_clause_a_few_lines_from_the_path(self):
        self.assertEqual(
            self.tokens(
                {
                    "provenance/observations.md": (
                        "# Observations\n\n"
                        "* Four paths were referenced by name and did not exist:\n"
                        "  `internal/PLAN.md` (README), `evals/goldens.jsonl`\n"
                        "  (Makefile), and the rest.\n"
                    )
                }
            ),
            [],
        )

    def test_the_same_sentence_without_the_absence_clause_is_reported(self):
        # The control for the guard above: nothing else about the line changed.
        self.assertEqual(
            self.tokens(
                {
                    "provenance/observations.md": (
                        "# Observations\n\n"
                        "* Four paths are referenced by name:\n"
                        "  `internal/PLAN.md` (README), `evals/goldens.jsonl`\n"
                        "  (Makefile), and the rest.\n"
                    )
                }
            ),
            ["internal/PLAN.md", "evals/goldens.jsonl"],
        )


class Contract(PathsCheckerCase):
    def test_registered_under_the_name_paths(self):
        self.assertIn("paths", registered())
        self.assertEqual(registered()["paths"].name, "paths")
        self.assertTrue(registered()["paths"].description)

    def test_same_tree_same_verdicts(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(
            root,
            {
                "README.md": "See `a/one.md`, `b/two.md`, `c/three.md`.\n",
                "Makefile": "run: ## uses d/four.json\n\t@true\n",
                "src/pkg/a.py": "# see e/five.yml\n",
            },
        )
        first = [f.as_dict() for f in PathsChecker().check(RepoIndex(root), CheckConfig())]
        second = [f.as_dict() for f in PathsChecker().check(RepoIndex(root), CheckConfig())]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)

    def test_the_checker_does_not_write_to_the_repository(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(
            root,
            {
                "README.md": "See `internal/PLAN.md` and `docs/guide.md`.\n",
                "pyproject.toml": "# See docs/adr/0001-core.md\n",
            },
        )

        def snapshot() -> list[tuple[str, int, int]]:
            return sorted(
                (str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns)
                for p in root.rglob("*")
            )

        before = snapshot()
        list(PathsChecker().check(RepoIndex(root), CheckConfig()))
        self.assertEqual(before, snapshot())

    def test_an_empty_tree_produces_nothing(self):
        self.assertEqual(self.tokens({}), [])


if __name__ == "__main__":
    unittest.main()
