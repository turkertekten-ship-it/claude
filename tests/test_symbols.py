"""Tests for the `symbols` checker.

The negative assertions carry the weight here. Finding a console script that
points at nothing is easy; the reason this checker is allowed near a README is
that it stays silent on a hostname, on a stdlib module, on an attribute chain
into a class, and on a roadmap row whose whole point is that the module has not
been written yet - and every one of those appears in real documentation next to
the references that matter.

Fixtures are real files in a temporary directory, never a patched RepoIndex, so
the resolution under test is the resolution that ships. Nothing here is named
"missing": the word is one of the absence cues, and a fixture that used it would
silence the very finding it was written to provoke.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.symbols import SymbolsChecker
from tools.claims import RepoIndex
from tools.evidence import EvidenceKind, Finding, Severity, Verdict
from tools.registry import CheckConfig, registered

PKG_INIT = '"""The pkg package."""\n'

CLI_WITH_MAIN = (
    '"""Command line entry point."""\n'
    "\n"
    "\n"
    "def main() -> int:\n"
    "    return 0\n"
)

CLI_WITHOUT_MAIN = (
    '"""Command line entry point."""\n'
    "\n"
    "\n"
    "def run() -> int:\n"
    "    return 0\n"
)


def _pyproject(scripts: str = "", extra: str = "") -> str:
    body = (
        "[project]\n"
        'name = "pkg"\n'
        'version = "0.1.0"\n'
    )
    if scripts:
        body += f"\n{scripts}\n"
    if extra:
        body += f"\n{extra}\n"
    return body


class SymbolsCheckerTest(unittest.TestCase):
    def repo(self, files: dict[str, str]) -> RepoIndex:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for rel, body in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, "utf-8")
        return RepoIndex(root)

    def check(self, files: dict[str, str], config: CheckConfig | None = None) -> list[Finding]:
        repo = self.repo(files)
        self._root = repo.root
        return list(SymbolsChecker().check(repo, config or CheckConfig()))

    def codes(self, findings: list[Finding]) -> list[str]:
        return [f.code for f in findings]

    def assertQuoted(self, findings: list[Finding]) -> None:
        """Every claim must be re-derivable with `sed -n '<line>p' <path>`."""
        for finding in findings:
            line = (self._root / finding.claim.path).read_text("utf-8").split("\n")
            self.assertIn(finding.claim.text, line[finding.claim.line - 1],
                          f"{finding.code} quoted text not on {finding.claim.locator}")

    # ------------------------------------------------------------ true positives

    def test_entry_point_to_absent_module_is_contradicted(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
        })
        self.assertEqual(self.codes(findings), ["MODULE_MISSING"])
        found = findings[0]
        self.assertIs(found.verdict, Verdict.CONTRADICTED)
        self.assertIs(found.severity, Severity.ERROR)
        self.assertEqual(found.claim.line, 6)
        self.assertEqual(found.claim.text, 'ooda = "pkg.cli:main"')
        absence = [e for e in found.evidence if e.kind is EvidenceKind.ABSENCE]
        self.assertEqual(len(absence), 1)
        self.assertIn("src/pkg/cli.py", absence[0].searched)
        self.assertIn("src", absence[0].summary)
        self.assertQuoted(findings)

    def test_entry_point_to_absent_symbol_is_contradicted(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": CLI_WITHOUT_MAIN,
        })
        self.assertEqual(self.codes(findings), ["SYMBOL_MISSING"])
        absence = [e for e in findings[0].evidence if e.kind is EvidenceKind.ABSENCE]
        self.assertEqual(absence[0].searched, ("src/pkg/cli.py",))
        self.assertIn("run", absence[0].summary)  # what the module does define
        self.assertQuoted(findings)

    def test_dash_m_module_that_was_never_written(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": "# pkg\n\n```bash\npython3 -m pkg.ghost --help\n```\n",
        })
        self.assertEqual(self.codes(findings), ["MODULE_MISSING"])
        self.assertEqual(findings[0].claim.line, 4)
        self.assertEqual(findings[0].claim.text, "python3 -m pkg.ghost --help")
        self.assertQuoted(findings)

    def test_documented_dotted_name_that_is_not_there(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": "# pkg\n\nRetrieval lives in `pkg.ghost`, which you can read.\n",
        })
        self.assertEqual(self.codes(findings), ["MODULE_MISSING"])
        self.assertIs(findings[0].verdict, Verdict.CONTRADICTED)
        self.assertQuoted(findings)

    def test_documented_name_absent_from_an_existing_module(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": CLI_WITH_MAIN,
            "README.md": "# pkg\n\nCall `pkg.cli.launch` to start it.\n",
        })
        self.assertEqual(self.codes(findings), ["SYMBOL_MISSING"])
        self.assertIn("launch", findings[0].detail)
        self.assertQuoted(findings)

    def test_docstring_reference_is_read_as_documentation(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/core.py": '"""Scoring.\n\nSee `pkg.ghost` for the index it reads.\n"""\n',
        })
        self.assertEqual(self.codes(findings), ["MODULE_MISSING"])
        self.assertEqual(findings[0].claim.path, "src/pkg/core.py")
        self.assertQuoted(findings)

    # ------------------------------------------------------------ true negatives

    def test_everything_resolving_says_only_the_packaging_promise(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": CLI_WITH_MAIN,
            "README.md": (
                "# pkg\n\nThe entry point is `pkg.cli`, and `pkg.cli.main` returns an exit "
                "code.\n\n```bash\npython3 -m pkg.cli\n```\n"
            ),
        })
        self.assertEqual(self.codes(findings), ["ENTRY_POINT_RESOLVES"])
        found = findings[0]
        self.assertIs(found.verdict, Verdict.SUPPORTED)
        self.assertIs(found.severity, Severity.INFO)
        definition = [e for e in found.evidence if e.path == "src/pkg/cli.py"]
        self.assertEqual(definition[0].line, 4)          # the `def main` line, not the file
        self.assertIn("def main", definition[0].excerpt)
        self.assertQuoted(findings)

    def test_gui_scripts_resolve_without_a_finding(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.gui-scripts]\noodagui = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": CLI_WITH_MAIN,
        })
        self.assertEqual(findings, [])

    def test_reexported_symbol_counts_as_defined(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/core.py": "def main() -> int:\n    return 0\n",
            "src/pkg/cli.py": "from pkg.core import main\n",
        })
        self.assertEqual(self.codes(findings), ["ENTRY_POINT_RESOLVES"])

    def test_conditionally_defined_symbol_counts_as_defined(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": "import sys\n\nif sys.version_info >= (3, 11):\n    def main() -> int:\n        return 0\n",
        })
        self.assertEqual(self.codes(findings), ["ENTRY_POINT_RESOLVES"])

    def test_package_dir_declared_in_pyproject_is_searched(self):
        findings = self.check({
            "pyproject.toml": _pyproject(
                '[project.scripts]\nooda = "pkg.cli:main"',
                '[tool.setuptools.packages.find]\nwhere = ["lib"]',
            ),
            "lib/pkg/__init__.py": PKG_INIT,
            "lib/pkg/cli.py": CLI_WITH_MAIN,
        })
        self.assertEqual(self.codes(findings), ["ENTRY_POINT_RESOLVES"])

    # ------------------------------------------------- ambiguity: stay silent

    def test_dotted_prose_that_is_not_a_module_reference(self):
        """Rule 6: hostnames, stdlib modules and class attributes are not code refs."""
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": (
                "# pkg\n\n"
                "Fetch from `www.example.com` using `html.parser`.\n"
                "`Chunk.context_header` is a field, `report.skipped` a mapping, and\n"
                "`config.allow_network` a switch. Version `1.2.3` is current.\n"
            ),
        })
        self.assertEqual(findings, [])

    def test_attribute_chain_into_a_class_is_left_alone(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": "class Widget:\n    size = 3\n",
            "README.md": "# pkg\n\nRead `pkg.cli.Widget.size` for the default.\n",
        })
        self.assertEqual(findings, [])

    def test_stdlib_and_third_party_dash_m_are_not_this_repos_promise(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": (
                "# pkg\n\n```bash\npython3 -m unittest discover -s tests\n"
                "python3 -m nosuchthirdparty.cli\n```\n"
            ),
        })
        self.assertEqual(findings, [])

    def test_prose_that_says_the_module_is_absent_is_not_contradicted(self):
        """The sentence and the evidence agree; a finding here invents a conflict."""
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": "# pkg\n\n| CLI (`pkg.ghost`) | not started | - |\n",
            "provenance/sources.yaml": (
                "sources:\n"
                "  - id: S-4\n"
                "    command: python3 -m pkg.ghost --help\n"
                "    exit_code: 1\n"
                '    observed: "ModuleNotFoundError: No module named \'pkg.ghost\'"\n'
            ),
        })
        self.assertEqual(findings, [])

    def test_a_weak_absence_cue_only_silences_its_own_line(self):
        """"a missing API key" is English; five lines away it is not evidence."""
        files = {
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": (
                "# pkg\n\n"
                "A missing API key reduces what the pipeline can do.\n\n"
                "The index lives in `pkg.ghost`.\n"
            ),
        }
        findings = self.check(files)
        self.assertEqual(self.codes(findings), ["MODULE_MISSING"])
        self.assertEqual(findings[0].claim.line, 5)

        files["README.md"] = "# pkg\n\nThe `pkg.ghost` module is missing.\n"
        self.assertEqual(self.check(files), [])

    def test_namespace_directory_is_not_reported_as_absent(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/plugins/thing.py": "VALUE = 1\n",
            "README.md": "# pkg\n\n```bash\npython3 -m pkg.plugins\n```\n",
        })
        self.assertEqual(findings, [])

    def test_reference_outside_a_source_root_package_is_ignored(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "docs/notes.md": "# notes\n\nThe schema is `docs.adr.0001`, sort of.\n",
        })
        self.assertEqual(findings, [])

    # --------------------------------------------------------------- machinery

    def test_unparseable_pyproject_is_unverifiable_not_a_pass(self):
        findings = self.check({
            "pyproject.toml": "[project\nname = broken\n",
            "src/pkg/__init__.py": PKG_INIT,
        })
        self.assertEqual(self.codes(findings), ["PYPROJECT_UNPARSEABLE"])
        self.assertIs(findings[0].verdict, Verdict.UNVERIFIABLE)
        self.assertTrue(findings[0].detail)
        self.assertQuoted(findings)

    def test_unparseable_module_is_unverifiable_not_a_symbol_failure(self):
        findings = self.check({
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "src/pkg/cli.py": "def main( ->\n",
        })
        self.assertEqual(self.codes(findings), ["MODULE_UNPARSEABLE"])
        self.assertIs(findings[0].verdict, Verdict.UNVERIFIABLE)

    def test_one_line_naming_a_module_twice_reports_once(self):
        findings = self.check({
            "pyproject.toml": _pyproject(),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": "# pkg\n\nRun `pkg.ghost` with python3 -m pkg.ghost today.\n",
        })
        self.assertEqual(self.codes(findings), ["MODULE_MISSING"])

    def test_repeated_runs_agree(self):
        files = {
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": "# pkg\n\nSee `pkg.ghost` and `pkg.other`.\n",
        }
        repo = self.repo(files)
        first = [f.as_dict() for f in SymbolsChecker().check(repo, CheckConfig())]
        second = [f.as_dict() for f in SymbolsChecker().check(RepoIndex(repo.root), CheckConfig())]
        self.assertEqual(first, second)
        self.assertEqual([f["code"] for f in first],
                         ["MODULE_MISSING", "MODULE_MISSING", "MODULE_MISSING"])

    def test_the_checker_writes_nothing(self):
        files = {
            "pyproject.toml": _pyproject('[project.scripts]\nooda = "pkg.cli:main"'),
            "src/pkg/__init__.py": PKG_INIT,
            "README.md": "# pkg\n\nSee `pkg.ghost`.\n",
        }
        repo = self.repo(files)
        before = sorted(p.relative_to(repo.root).as_posix() for p in repo.root.rglob("*"))
        list(SymbolsChecker().check(repo, CheckConfig()))
        after = sorted(p.relative_to(repo.root).as_posix() for p in repo.root.rglob("*"))
        self.assertEqual(before, after)

    def test_registered_under_its_contract_name(self):
        checker = registered().get("symbols")
        self.assertIsNotNone(checker)
        self.assertEqual(checker.name, "symbols")
        self.assertTrue(checker.description)


if __name__ == "__main__":
    unittest.main()
