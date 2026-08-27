"""Tests for the `commands` checker.

The interesting assertions here are the negative ones. Any checker can find a
broken `make` target; the reason this one is allowed near a README is that it
stays silent on an ASCII diagram, on a table rendered inside a fence, and on
the sentence "make sure the tests pass" - all of which live in code fences in
real repositories and none of which are commands.

Fixtures are real files in a temporary directory, never a patched RepoIndex,
so the parsing under test is the parsing that ships.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.commands import MAKEFILE_NAMES, CommandChecker
from tools.claims import RepoIndex
from tools.evidence import EvidenceKind, Finding, Severity, Verdict
from tools.registry import CheckConfig, registered

# A Makefile whose `demo` target invokes a module that was never written - the
# exact drift this checker exists to catch.
BROKEN_MAKEFILE = (
    "PY ?= python3\n"
    "\n"
    ".PHONY: test demo clean\n"
    "\n"
    "test:\n"
    "\t$(PY) -m unittest discover -s tests\n"
    "\n"
    "demo:\n"
    "\t$(PY) -m pkg.cli demo\n"
    "\n"
    "clean:\n"
    "\trm -rf build\n"
)

GOOD_MAKEFILE = (
    "PY ?= python3\n"
    "\n"
    ".PHONY: test clean\n"
    "\n"
    "test:\n"
    "\t$(PY) -m unittest discover -s tests\n"
    "\n"
    "clean:\n"
    "\trm -rf build\n"
)

DIAGRAM_README = """# oodarag

```
Observe  ->  Orient   ->  Decide   ->  Act
ingest       normalize    policy       reindex / backfill
             chunk        engine
             embed
```

```text
| Area | Module |
|---|---|
| HTTP | util/http.py |
```
"""


def _fence(*lines: str, lang: str = "bash") -> str:
    body = "\n".join(lines)
    return f"# doc\n\n```{lang}\n{body}\n```\n"


class CommandCheckerTest(unittest.TestCase):
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
        self._last_root = repo.root
        return list(CommandChecker().check(repo, config or CheckConfig(run_commands=False)))

    @staticmethod
    def codes(findings: list[Finding], code: str) -> list[Finding]:
        return [f for f in findings if f.code == code]

    @staticmethod
    def problems(findings: list[Finding]) -> list[Finding]:
        return [f for f in findings if f.is_problem]

    # ---------------------------------------------------------- true positives

    def test_documented_make_target_that_does_not_exist_is_contradicted(self):
        findings = self.check({
            "Makefile": GOOD_MAKEFILE,
            "README.md": _fence("make release"),
        })
        missing = self.codes(findings, "MAKE_TARGET_MISSING")
        self.assertEqual(len(missing), 1, [f.as_dict() for f in findings])
        finding = missing[0]
        self.assertIs(finding.verdict, Verdict.CONTRADICTED)
        self.assertIs(finding.severity, Severity.ERROR)
        self.assertEqual(finding.claim.path, "README.md")
        self.assertEqual(finding.claim.text, "make release")
        self.assertIn("release", finding.detail)
        absences = [e for e in finding.evidence if e.kind is EvidenceKind.ABSENCE]
        self.assertEqual([e.searched for e in absences], [("Makefile",)])
        self.assertIn("test", absences[0].summary)  # the targets that do exist are named

    def test_missing_makefile_names_the_files_it_looked_for(self):
        findings = self.check({"README.md": _fence("make test")})
        missing = self.codes(findings, "MAKE_TARGET_MISSING")
        self.assertEqual(len(missing), 1)
        absence = [e for e in missing[0].evidence if e.kind is EvidenceKind.ABSENCE][0]
        self.assertEqual(absence.searched, MAKEFILE_NAMES)

    def test_recipe_invoking_a_module_with_no_file_is_contradicted(self):
        findings = self.check({"Makefile": BROKEN_MAKEFILE, "src/pkg/__init__.py": ""})
        missing = self.codes(findings, "MODULE_MISSING")
        self.assertEqual(len(missing), 1, [f.as_dict() for f in findings])
        finding = missing[0]
        self.assertIs(finding.verdict, Verdict.CONTRADICTED)
        self.assertIs(finding.severity, Severity.ERROR)
        self.assertEqual(finding.claim.path, "Makefile")
        self.assertEqual(finding.claim.line, 9)
        self.assertEqual(finding.claim.text, "$(PY) -m pkg.cli demo")
        absence = [e for e in finding.evidence if e.kind is EvidenceKind.ABSENCE][0]
        self.assertIn("src/pkg/cli.py", absence.searched)
        self.assertIn("src/pkg/cli/__init__.py", absence.searched)

    def test_recipe_reached_from_a_doc_is_reported_once_and_cites_the_doc(self):
        findings = self.check({
            "Makefile": BROKEN_MAKEFILE,
            "src/pkg/__init__.py": "",
            "README.md": _fence("make demo          # end-to-end: ingest -> index"),
        })
        missing = self.codes(findings, "MODULE_MISSING")
        self.assertEqual(len(missing), 1, "the Makefile scan must not duplicate the doc walk")
        cited = {e.path for e in missing[0].evidence if e.kind is EvidenceKind.FILE}
        self.assertEqual(cited, {"README.md", "Makefile"})

    def test_a_documented_command_that_fails_is_run_and_its_stderr_attached(self):
        findings = self.check(
            {"src/failing.py": "import sys\n\nsys.exit(3)\n", "README.md": _fence("python3 -m failing")},
            CheckConfig(run_commands=True, command_timeout=60.0),
        )
        failures = self.codes(findings, "COMMAND_FAILS")
        self.assertEqual(len(failures), 1, [f.as_dict() for f in findings])
        finding = failures[0]
        self.assertIs(finding.verdict, Verdict.CONTRADICTED)
        self.assertIs(finding.severity, Severity.ERROR)
        ran = [e for e in finding.evidence if e.kind is EvidenceKind.COMMAND]
        self.assertEqual(len(ran), 1)
        self.assertEqual(ran[0].exit_code, 3)
        self.assertEqual(ran[0].argv, ("python3", "-m", "failing"))

    # ---------------------------------------------------------- true negatives

    def test_a_working_documented_command_produces_no_problem(self):
        findings = self.check(
            {"src/ok.py": "print('ok')\n", "README.md": _fence("python3 -m ok")},
            CheckConfig(run_commands=True, command_timeout=60.0),
        )
        self.assertEqual(self.problems(findings), [], [f.as_dict() for f in findings])
        self.assertEqual(findings, [], "rule 5: a command that works is not news")

    def test_existing_target_and_stdlib_module_are_not_flagged(self):
        findings = self.check({
            "Makefile": GOOD_MAKEFILE,
            "README.md": _fence("make test", 'python3 -m pip install -e ".[dev]"'),
        })
        self.assertEqual(self.problems(findings), [], [f.as_dict() for f in findings])

    def test_unallowlisted_but_resolvable_command_is_silent(self):
        findings = self.check({"README.md": _fence("grep -n oodarag README.md")})
        self.assertEqual(findings, [])

    # ------------------------------------------------- ambiguity (CONTRACT #6)

    def test_diagrams_and_tables_inside_fences_produce_nothing(self):
        self.assertEqual(self.check({"README.md": DIAGRAM_README}), [])

    def test_the_sentence_make_sure_is_not_read_as_a_target(self):
        findings = self.check({
            "Makefile": GOOD_MAKEFILE,
            "README.md": _fence("make sure the tests pass first", "make sure"),
        })
        self.assertEqual(self.codes(findings, "MAKE_TARGET_MISSING"), [])

    def test_make_in_another_directory_is_not_guessed_at(self):
        findings = self.check({
            "Makefile": GOOD_MAKEFILE,
            "README.md": _fence("make -C vendor release"),
        })
        self.assertEqual(self.codes(findings, "MAKE_TARGET_MISSING"), [])

    def test_unresolvable_module_is_unverifiable_not_missing(self):
        findings = self.check({"README.md": _fence("python3 -m nosuchthirdparty --help")})
        unresolved = self.codes(findings, "MODULE_UNRESOLVED")
        self.assertEqual(len(unresolved), 1, [f.as_dict() for f in findings])
        self.assertIs(unresolved[0].verdict, Verdict.UNVERIFIABLE)
        self.assertTrue(unresolved[0].detail)
        self.assertEqual(self.problems(findings), [])

    # ------------------------------------------------------------ run fencing

    def test_run_commands_off_reports_unverifiable_rather_than_a_pass(self):
        findings = self.check(
            {"src/failing.py": "import sys\n\nsys.exit(3)\n", "README.md": _fence("python3 -m failing")},
            CheckConfig(run_commands=False),
        )
        self.assertEqual(self.problems(findings), [])
        not_run = self.codes(findings, "COMMAND_NOT_RUN")
        self.assertEqual(len(not_run), 1)
        self.assertIs(not_run[0].verdict, Verdict.UNVERIFIABLE)
        self.assertIn("run_commands", not_run[0].detail)

    def test_a_target_whose_recipe_deletes_files_is_never_executed(self):
        repo = self.repo({
            "Makefile": GOOD_MAKEFILE,
            "README.md": _fence("make clean"),
            "build/keep.txt": "still here\n",
        })
        findings = list(CommandChecker().check(repo, CheckConfig(run_commands=True,
                                                                command_timeout=60.0)))
        self.assertTrue((repo.root / "build" / "keep.txt").exists(),
                        "the checker executed a destructive recipe")
        not_run = self.codes(findings, "COMMAND_NOT_RUN")
        self.assertEqual(len(not_run), 1, [f.as_dict() for f in findings])
        self.assertIn("'rm'", not_run[0].detail)

    # ----------------------------------------------------------- the contract

    def test_every_claim_is_verbatim_at_the_line_it_names(self):
        files = {
            "Makefile": BROKEN_MAKEFILE,
            "src/pkg/__init__.py": "",
            "README.md": _fence("make release", "make demo"),
        }
        repo = self.repo(files)
        findings = list(CommandChecker().check(repo, CheckConfig(run_commands=False)))
        self.assertTrue(findings)
        for finding in findings:
            rows = (repo.root / finding.claim.path).read_text("utf-8").split("\n")
            line = rows[finding.claim.line - 1]
            self.assertIn(finding.claim.text, line,
                          f"{finding.claim.locator} is not re-derivable with sed")

    def test_every_non_unverifiable_finding_carries_evidence(self):
        findings = self.check({
            "Makefile": BROKEN_MAKEFILE,
            "src/pkg/__init__.py": "",
            "README.md": _fence("make release"),
        })
        for finding in findings:
            if finding.verdict is not Verdict.UNVERIFIABLE:
                self.assertTrue(finding.evidence, finding.code)

    def test_two_runs_over_one_repository_agree(self):
        files = {
            "Makefile": BROKEN_MAKEFILE,
            "src/pkg/__init__.py": "",
            "README.md": _fence("make release", "make demo", "python3 -m unittest discover"),
        }
        repo = self.repo(files)
        config = CheckConfig(run_commands=False)
        first = [f.as_dict() for f in CommandChecker().check(repo, config)]
        second = [f.as_dict() for f in CommandChecker().check(repo, config)]
        self.assertEqual(first, second)
        self.assertTrue(first)

    def test_registered_under_the_name_the_report_will_print(self):
        self.assertIn("commands", registered())
        self.assertEqual(registered()["commands"].name, "commands")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
