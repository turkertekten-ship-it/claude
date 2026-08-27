"""Tests for the `deps` checker.

Every fixture is a real tree on disk parsed by a real `RepoIndex`, because the
thing under test is what `ast.parse` and `tomllib` see, and a stubbed index
would test the stub instead.

The negative cases outnumber the positive ones on purpose. This checker's
expensive failure is not missing an undeclared package - it is reporting
`try: import numpy / except ImportError:` as a broken promise, or `import yaml`
as undeclared in a project that declares PyYAML. Those are the shapes a correct
optional dependency actually takes, and a checker that flags them gets switched
off, after which it catches nothing at all.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.deps import DepsChecker
from tools.claims import RepoIndex
from tools.evidence import EvidenceKind, Severity, Verdict
from tools.registry import CheckConfig, registered

PROJECT = """\
[project]
name = "demo"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
fast = ["numpy>=1.26"]
dev = ["pytest>=8.0"]
"""

HEADLINE = "# demo\n\nRuns on the standard library alone.\n"


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


class DepsCase(unittest.TestCase):
    def findings(self, files: dict[str, str], config: CheckConfig | None = None):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(root, files)
        return root, list(DepsChecker().check(RepoIndex(root), config or CheckConfig()))

    def codes(self, files: dict[str, str]) -> list[str]:
        _, found = self.findings(files)
        return [f.code for f in found]

    def one(self, files: dict[str, str], code: str):
        _, found = self.findings(files)
        matching = [f for f in found if f.code == code]
        self.assertEqual(len(matching), 1, [f.code for f in found])
        return matching[0]


class UndeclaredImports(DepsCase):
    def test_an_undeclared_third_party_import_is_contradicted(self):
        finding = self.one(
            {
                "pyproject.toml": PROJECT,
                "src/demo/client.py": "import json\nimport requests\n",
            },
            "UNDECLARED_DEPENDENCY",
        )
        self.assertEqual(finding.checker, "deps")
        self.assertEqual(finding.verdict, Verdict.CONTRADICTED)
        self.assertEqual(finding.severity, Severity.ERROR)
        self.assertEqual(finding.claim.path, "src/demo/client.py")
        self.assertEqual(finding.claim.line, 2)
        self.assertIn("requests", finding.detail)

    def test_the_claim_is_the_import_line_verbatim(self):
        root, found = self.findings(
            {
                "pyproject.toml": PROJECT,
                "src/demo/client.py": '"""Doc."""\n\nfrom requests.adapters import HTTPAdapter\n',
            }
        )
        claim = found[0].claim
        line = (root / claim.path).read_text().split("\n")[claim.line - 1]
        self.assertIn(claim.text, line)
        self.assertEqual(claim.line, 3)

    def test_evidence_names_the_import_site_and_the_search_space(self):
        finding = self.one(
            {"pyproject.toml": PROJECT, "src/demo/a.py": "import requests\n"},
            "UNDECLARED_DEPENDENCY",
        )
        cited = [e for e in finding.evidence if e.kind is EvidenceKind.FILE]
        self.assertEqual(cited[0].path, "src/demo/a.py")
        self.assertEqual(cited[0].line, 1)
        self.assertEqual(cited[0].excerpt, "import requests")
        absence = next(e for e in finding.evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertIn("pyproject.toml [project] dependencies", absence.searched)
        self.assertIn("pyproject.toml [project.optional-dependencies] fast", absence.searched)

    def test_one_finding_per_module_per_file_not_per_line(self):
        finding = self.one(
            {
                "pyproject.toml": PROJECT,
                "src/demo/a.py": "import requests\nimport os\nfrom requests import Session\n",
            },
            "UNDECLARED_DEPENDENCY",
        )
        self.assertEqual(finding.claim.line, 1)
        self.assertEqual(len([e for e in finding.evidence if e.kind is EvidenceKind.FILE]), 2)

    def test_two_files_are_two_findings(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": "import requests\n",
                    "src/demo/b.py": "import requests\n",
                }
            ),
            ["UNDECLARED_DEPENDENCY", "UNDECLARED_DEPENDENCY"],
        )


class NotUndeclared(DepsCase):
    """Imports that resolve, and so must never be reported."""

    def test_standard_library_imports(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": (
                        "import json\nimport urllib.request\nfrom pathlib import Path\n"
                    ),
                }
            ),
            [],
        )

    def test_first_party_package_under_a_source_root(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/__init__.py": "",
                    "src/demo/a.py": "from demo.b import thing\nimport demo\n",
                    "src/demo/b.py": "thing = 1\n",
                }
            ),
            [],
        )

    def test_a_top_level_directory_of_the_repo(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "tools/__init__.py": "",
                    "src/demo/a.py": "import tools\n",
                }
            ),
            [],
        )

    def test_relative_imports(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/__init__.py": "",
                    "src/demo/a.py": "from . import b\nfrom .b import thing\n",
                    "src/demo/b.py": "thing = 1\n",
                }
            ),
            [],
        )

    def test_a_declared_dependency_named_differently_from_its_import(self):
        # `import yaml` is satisfied by PyYAML. Reporting it would be a
        # fabricated finding produced by a naming convention.
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": (
                        '[project]\nname = "d"\n'
                        'dependencies = ["PyYAML>=6", "python-dateutil"]\n'
                    ),
                    "src/demo/a.py": "import yaml\nimport dateutil\n",
                }
            ),
            [],
        )

    def test_a_build_backend_import(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": (
                        '[build-system]\nrequires = ["setuptools>=68"]\n\n'
                        '[project]\nname = "d"\ndependencies = []\n'
                    ),
                    "setup.py": "from setuptools import setup\n\nsetup()\n",
                }
            ),
            [],
        )

    def test_a_module_the_running_interpreter_has_retired(self):
        # 3.13 dropped telnetlib; a 3.11 repository still using it is not
        # importing a third-party package, whatever this interpreter thinks.
        self.assertEqual(
            self.codes(
                {"pyproject.toml": PROJECT, "src/demo/a.py": "import telnetlib\nimport distutils\n"}
            ),
            [],
        )

    def test_no_manifest_means_nothing_is_declared_or_undeclared(self):
        # With no manifest there is no declaration to contradict, and inventing
        # one would be the checker guessing at the project's intent.
        self.assertEqual(self.codes({"src/demo/a.py": "import requests\n"}), [])


class GuardedImports(DepsCase):
    """A guarded import is optional by construction - rule 6's territory."""

    def test_try_except_import_error(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": (
                        "try:\n    import numpy\nexcept ImportError:\n    numpy = None\n"
                    ),
                }
            ),
            [],
        )

    def test_import_inside_a_function_body(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": "def score():\n    import numpy\n    return numpy\n",
                }
            ),
            [],
        )

    def test_import_inside_a_method_body(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": (
                        "class S:\n    def go(self):\n"
                        "        import requests\n        return requests\n"
                    ),
                }
            ),
            [],
        )

    def test_import_under_if_type_checking(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": (
                        "from typing import TYPE_CHECKING\n\n"
                        "if TYPE_CHECKING:\n    import requests\n"
                    ),
                }
            ),
            [],
        )


class EagerOptionalDependency(DepsCase):
    def test_an_extra_imported_at_module_scope_is_a_warning(self):
        finding = self.one(
            {
                "pyproject.toml": PROJECT,
                "src/demo/score.py": "import numpy\n\ndef go():\n    return numpy\n",
            },
            "OPTIONAL_DEP_IMPORTED_EAGERLY",
        )
        self.assertEqual(finding.severity, Severity.WARN)
        self.assertEqual(finding.verdict, Verdict.CONTRADICTED)
        self.assertIn("numpy", finding.detail)
        self.assertIn("fast", finding.detail)

    def test_the_claim_quotes_the_declaration_that_calls_it_optional(self):
        root, found = self.findings(
            {"pyproject.toml": PROJECT, "src/demo/score.py": "import numpy\n"}
        )
        claim = found[0].claim
        self.assertEqual(claim.path, "pyproject.toml")
        line = (root / "pyproject.toml").read_text().split("\n")[claim.line - 1]
        self.assertIn(claim.text, line)
        self.assertIn("numpy", claim.text)
        site = next(e for e in found[0].evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual((site.path, site.line), ("src/demo/score.py", 1))

    def test_a_guarded_extra_is_the_extra_working(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": PROJECT,
                    "src/demo/score.py": (
                        "try:\n    import numpy\nexcept ImportError:\n    numpy = None\n"
                    ),
                }
            ),
            [],
        )

    def test_a_dev_extra_used_by_the_test_suite_is_not_flagged(self):
        # pytest under [dev], imported at module scope in tests/, is exactly
        # what the extra is for; `pip install demo` never imports the tests.
        self.assertEqual(
            self.codes({"pyproject.toml": PROJECT, "tests/test_a.py": "import pytest\n"}), []
        )

    def test_a_required_dependency_imported_eagerly_is_not_flagged(self):
        self.assertEqual(
            self.codes(
                {
                    "pyproject.toml": '[project]\nname = "d"\ndependencies = ["requests>=2"]\n',
                    "src/demo/a.py": "import requests\n",
                }
            ),
            [],
        )


class ZeroDependencyHeadline(DepsCase):
    def test_a_confirmed_headline_is_stated_once_with_its_counts(self):
        finding = self.one(
            {
                "README.md": HEADLINE,
                "pyproject.toml": PROJECT,
                "src/demo/__init__.py": "",
                "src/demo/a.py": "import json\nfrom demo import b\n",
                "src/demo/b.py": "import os\n",
            },
            "ZERO_DEP_CONFIRMED",
        )
        self.assertEqual(finding.verdict, Verdict.SUPPORTED)
        self.assertEqual(finding.severity, Severity.INFO)
        self.assertEqual(finding.claim.path, "README.md")
        self.assertEqual(finding.claim.text, "Runs on the standard library alone.")
        measured = next(e for e in finding.evidence if e.kind is EvidenceKind.VALUE)
        self.assertEqual(
            measured.value,
            {
                "python_files": 3,
                "distinct_imports": 3,
                "stdlib": 2,
                "first_party": 1,
                "third_party": 0,
            },
        )
        cited = next(e for e in finding.evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual((cited.path, cited.excerpt), ("pyproject.toml", "dependencies = []"))

    def test_a_repeated_claim_is_confirmed_once_not_nine_times(self):
        _, found = self.findings(
            {
                "README.md": HEADLINE + "\nZero dependencies. Dependency-free, in fact.\n",
                "docs/adr/0001.md": "The core runs on the standard library alone.\n",
                "pyproject.toml": PROJECT,
                "src/demo/a.py": "import json\n",
            }
        )
        self.assertEqual([f.code for f in found], ["ZERO_DEP_CONFIRMED"])
        self.assertEqual(found[0].claim.path, "README.md")

    def test_a_docstring_headline_is_found_too(self):
        finding = self.one(
            {
                "pyproject.toml": PROJECT,
                "src/demo/__init__.py": '"""The package is deliberately dependency-free."""\n',
            },
            "ZERO_DEP_CONFIRMED",
        )
        self.assertEqual(finding.claim.path, "src/demo/__init__.py")

    def test_an_unguarded_third_party_import_contradicts_the_headline(self):
        _, found = self.findings(
            {
                "README.md": HEADLINE,
                "pyproject.toml": PROJECT,
                "src/demo/a.py": "import requests\n",
            }
        )
        codes = sorted(f.code for f in found)
        self.assertEqual(codes, ["UNDECLARED_DEPENDENCY", "ZERO_DEP_CONTRADICTED"])
        contradiction = next(f for f in found if f.code == "ZERO_DEP_CONTRADICTED")
        self.assertEqual(contradiction.verdict, Verdict.CONTRADICTED)
        self.assertEqual(contradiction.severity, Severity.ERROR)
        self.assertEqual(contradiction.claim.path, "README.md")
        self.assertIn("requests", contradiction.detail)
        site = next(e for e in contradiction.evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual(
            (site.path, site.line, site.excerpt), ("src/demo/a.py", 1, "import requests")
        )

    def test_declared_runtime_dependencies_contradict_the_headline(self):
        finding = self.one(
            {
                "README.md": HEADLINE,
                "pyproject.toml": '[project]\nname = "d"\ndependencies = ["requests>=2"]\n',
                "src/demo/a.py": "import json\n",
            },
            "ZERO_DEP_CONTRADICTED",
        )
        cited = next(e for e in finding.evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual(cited.path, "pyproject.toml")
        self.assertIn("requests", finding.detail)

    def test_a_guarded_third_party_import_does_not_contradict_it(self):
        # The whole point of the claim is that the accelerator is optional, and
        # this is what an optional accelerator looks like in source.
        self.assertEqual(
            self.codes(
                {
                    "README.md": HEADLINE,
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": (
                        "try:\n    import numpy\nexcept ImportError:\n    numpy = None\n"
                    ),
                }
            ),
            [],
        )

    def test_a_filename_that_contains_the_phrase_is_not_a_claim(self):
        # "never expand a name into content": citing
        # docs/adr/0001-zero-dependency-core.md is not asserting what it says.
        self.assertEqual(
            self.codes(
                {
                    "README.md": "See `docs/adr/0001-zero-dependency-core.md` for the rationale.\n",
                    "docs/adr/0001-zero-dependency-core.md": "# ADR\n",
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": "import json\n",
                }
            ),
            [],
        )

    def test_no_headline_claim_means_no_confirmation(self):
        self.assertEqual(
            self.codes(
                {"README.md": "# demo\n\nA pipeline.\n", "pyproject.toml": PROJECT,
                 "src/demo/a.py": "import json\n"}
            ),
            [],
        )

    def test_a_guarded_third_party_import_blocks_confirmation_as_well(self):
        # Not a contradiction, but not a confirmation either: "every import is
        # stdlib or first-party" is simply not true here, and rounding that to
        # SUPPORTED is what CONTRACT.md rule 3 exists to prevent.
        self.assertEqual(
            self.codes(
                {
                    "README.md": HEADLINE,
                    "pyproject.toml": PROJECT,
                    "src/demo/a.py": "def go():\n    import numpy\n    return numpy\n",
                }
            ),
            [],
        )


class Undecidable(DepsCase):
    def test_an_unparseable_file_is_reported_as_a_hole_in_the_graph(self):
        finding = self.one(
            {"pyproject.toml": PROJECT, "src/demo/a.py": "def broken(:\n    pass\n"},
            "IMPORT_GRAPH_INCOMPLETE",
        )
        self.assertEqual(finding.verdict, Verdict.UNVERIFIABLE)
        self.assertTrue(finding.detail)
        self.assertEqual(finding.claim.path, "src/demo/a.py")

    def test_an_unparseable_file_blocks_confirmation(self):
        codes = self.codes(
            {
                "README.md": HEADLINE,
                "pyproject.toml": PROJECT,
                "src/demo/a.py": "import json\n",
                "src/demo/b.py": "def broken(:\n",
            }
        )
        self.assertEqual(codes, ["IMPORT_GRAPH_INCOMPLETE"])

    def test_dynamic_dependencies_are_unverifiable_not_a_pass(self):
        finding = self.one(
            {
                "README.md": HEADLINE,
                "pyproject.toml": '[project]\nname = "d"\ndynamic = ["dependencies"]\n',
                "src/demo/a.py": "import json\n",
            },
            "DEPENDENCY_MANIFEST_UNREADABLE",
        )
        self.assertEqual(finding.verdict, Verdict.UNVERIFIABLE)
        self.assertIn("dynamic", finding.detail)

    def test_an_unparseable_manifest_is_unverifiable_not_a_pass(self):
        finding = self.one(
            {
                "README.md": HEADLINE,
                "pyproject.toml": "[project\nname = \n",
                "src/demo/a.py": "import requests\n",
            },
            "DEPENDENCY_MANIFEST_UNREADABLE",
        )
        self.assertEqual(finding.verdict, Verdict.UNVERIFIABLE)

    def test_another_manifest_kind_is_unverifiable_not_a_pass(self):
        # requirements.txt is not parsed here, so "nothing is declared" would be
        # a conclusion drawn from a file this checker never read.
        finding = self.one(
            {
                "README.md": HEADLINE,
                "requirements.txt": "requests>=2\n",
                "src/demo/a.py": "import json\n",
            },
            "DEPENDENCY_MANIFEST_UNREADABLE",
        )
        self.assertEqual(finding.verdict, Verdict.UNVERIFIABLE)
        self.assertIn("requirements.txt", finding.detail)


class Hygiene(DepsCase):
    def test_the_checker_is_registered_under_its_name(self):
        self.assertIn("deps", registered())
        self.assertEqual(registered()["deps"].name, "deps")

    def test_an_empty_tree_produces_nothing(self):
        self.assertEqual(self.codes({}), [])

    def test_repeated_runs_agree(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(
            root,
            {
                "README.md": HEADLINE,
                "pyproject.toml": PROJECT,
                "src/demo/a.py": "import requests\nimport numpy\n",
                "src/demo/b.py": "import httpx\n",
            },
        )
        first = [f.as_dict() for f in DepsChecker().check(RepoIndex(root), CheckConfig())]
        second = [f.as_dict() for f in DepsChecker().check(RepoIndex(root), CheckConfig())]
        self.assertEqual(first, second)
        self.assertEqual(
            [f["code"] for f in first],
            [
                "UNDECLARED_DEPENDENCY",
                "UNDECLARED_DEPENDENCY",
                "OPTIONAL_DEP_IMPORTED_EAGERLY",
                "ZERO_DEP_CONTRADICTED",
            ],
        )

    def test_the_checker_does_not_write_to_the_repository(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(
            root,
            {
                "README.md": HEADLINE,
                "pyproject.toml": PROJECT,
                "src/demo/a.py": "import requests\n",
            },
        )

        def snapshot() -> list[tuple[str, int, int]]:
            return sorted(
                (str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns)
                for p in root.rglob("*")
            )

        before = snapshot()
        list(DepsChecker().check(RepoIndex(root), CheckConfig()))
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main()
