"""The suite-evidence checker, including the vacuous-pass trap.

`unittest discover` over an empty directory exits zero. That green tick is the
most dangerous output in this whole tool, because it certifies rather than
merely fails to detect - so the empty case gets more tests here than the
failing one.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.tests_evidence import TestsEvidenceChecker, _count, _documented_commands
from tools.claims import RepoIndex
from tools.registry import CheckConfig

PASSING = """import unittest


class T(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(True)
"""

FAILING = """import unittest


class T(unittest.TestCase):
    def test_bad(self):
        self.assertEqual(1, 2)
"""


def repo(tmp: str, *, readme: str = "", tests: dict[str, str] | None = None) -> Path:
    root = Path(tmp)
    (root / "README.md").write_text(readme or "# P\n\n```bash\nmake test\n```\n")
    if tests is not None:
        (root / "tests").mkdir(exist_ok=True)
        (root / "tests" / "__init__.py").write_text("")
        for name, body in tests.items():
            (root / "tests" / name).write_text(body)
    return root


def run(root: Path, **kw):
    return list(TestsEvidenceChecker().check(RepoIndex(root), CheckConfig(**kw)))


class TestCountParsing(unittest.TestCase):
    def test_unittest_output(self):
        self.assertEqual(_count("Ran 14 tests in 0.148s\n\nOK"), 14)

    def test_zero(self):
        self.assertEqual(_count("Ran 0 tests in 0.000s\n\nOK"), 0)

    def test_pytest_output(self):
        self.assertEqual(_count("collected 7 items"), 7)

    def test_unparseable(self):
        self.assertIsNone(_count("everything is fine"))


class TestDiscovery(unittest.TestCase):
    def test_a_repo_promising_nothing_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, readme="# P\n\nNo commands here.\n")
            self.assertEqual(_documented_commands(RepoIndex(root)), [])
            self.assertEqual(run(root), [])

    def test_make_test_is_recognised(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = _documented_commands(RepoIndex(repo(tmp)))
            # line 1 "# P", 2 blank, 3 the fence opener, 4 the command itself
            self.assertEqual([c.line for c, _ in found], [4])


class TestVerdicts(unittest.TestCase):
    def test_documented_suite_with_no_test_files_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = run(repo(tmp), run_commands=False)
            self.assertEqual([f.code for f in findings], ["TESTS_ABSENT"])
            self.assertTrue(findings[0].is_problem)
            # The absence must name where it looked, not just assert emptiness.
            kinds = [e.kind.value for e in findings[0].evidence]
            self.assertIn("absence", kinds)

    def test_an_empty_tests_dir_is_reported_despite_exiting_zero(self):
        # The trap: a tests/ directory holding no test files. `unittest
        # discover` exits 0, and a checker that stopped at the exit code would
        # certify this repository as tested.
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, tests={})
            (root / "tests" / "helper.py").write_text("X = 1\n")
            findings = run(root)
            self.assertEqual([f.code for f in findings], ["TESTS_ABSENT"])

    def test_a_passing_suite_is_confirmed_with_its_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = run(repo(tmp, tests={"test_a.py": PASSING}))
            self.assertEqual([f.code for f in findings], ["TESTS_PASS"])
            self.assertFalse(findings[0].is_problem)
            self.assertIn("1 tests ran", findings[0].detail)

    def test_a_failing_suite_carries_the_real_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = run(repo(tmp, tests={"test_a.py": FAILING}))
            self.assertEqual([f.code for f in findings], ["TESTS_FAIL"])
            self.assertTrue(findings[0].is_problem)
            commands = [e for e in findings[0].evidence if e.kind.value == "command"]
            self.assertTrue(commands, "the failure must carry the command that produced it")
            self.assertIn("AssertionError", commands[0].output)

    def test_without_run_commands_the_answer_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = run(repo(tmp, tests={"test_a.py": PASSING}), run_commands=False)
            self.assertEqual([f.code for f in findings], ["TESTS_NOT_RUN"])
            self.assertEqual(findings[0].verdict.value, "unverifiable")
            self.assertFalse(findings[0].is_problem, "not run must not fail the run")


if __name__ == "__main__":
    unittest.main()
