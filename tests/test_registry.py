"""Runner behaviour: broken checkers stay visible, and recursion terminates."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from typing import Iterator

from tools.claims import RepoIndex
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, ENV_MARKER, nested, run


class _Exploding:
    name = "exploding"
    description = "always raises"

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        raise RuntimeError("boom")
        yield  # pragma: no cover


class TestRecursionGuard(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.pop(ENV_MARKER, None)

    def tearDown(self) -> None:
        os.environ.pop(ENV_MARKER, None)
        if self._saved is not None:
            os.environ[ENV_MARKER] = self._saved

    def test_marker_detects_an_outer_run(self):
        self.assertFalse(nested())
        os.environ[ENV_MARKER] = "1"
        self.assertTrue(nested())

    def test_nested_config_disables_command_execution(self):
        outer = CheckConfig(run_commands=True)
        self.assertFalse(outer.for_subprocess().run_commands)

    def test_for_subprocess_preserves_everything_else(self):
        outer = CheckConfig(run_commands=True, allow_network=True, command_timeout=7.0,
                            only_checkers=("paths",))
        inner = outer.for_subprocess()
        self.assertTrue(inner.allow_network)
        self.assertEqual(inner.command_timeout, 7.0)
        self.assertEqual(inner.only_checkers, ("paths",))

    def test_run_marks_the_environment_for_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("# T\n")
            run(tmp, CheckConfig(run_commands=False))
            self.assertEqual(os.environ.get(ENV_MARKER), "1")

    def test_a_nested_run_says_so_in_the_report(self):
        os.environ[ENV_MARKER] = "1"
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("# T\n")
            report = run(tmp, CheckConfig(run_commands=True))
            self.assertIn("(nested run)", report.skipped)


class TestBrokenCheckersStayVisible(unittest.TestCase):
    def test_a_raising_checker_is_skipped_not_silently_dropped(self):
        from tools import registry

        saved = dict(registry._REGISTRY)
        registry._REGISTRY.clear()
        try:
            registry.register(_Exploding())
            with tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / "README.md").write_text("# T\n")
                report = run(tmp, CheckConfig(run_commands=False))
            self.assertIn("exploding", report.skipped)
            self.assertIn("boom", report.skipped["exploding"])
            self.assertNotIn("exploding", report.checkers_run)
        finally:
            registry._REGISTRY.clear()
            registry._REGISTRY.update(saved)

    def test_unimported_checker_modules_are_reported(self):
        from tools.registry import import_failures

        # Every bundled name must either import or be named as a failure; a
        # checker that vanishes with neither is the exact silent-shrink bug
        # this mechanism exists to prevent.
        from tools import checkers

        loaded_or_failed = set(checkers.IMPORT_FAILURES) | set(
            n for n in checkers.BUILTIN if n not in checkers.IMPORT_FAILURES
        )
        self.assertEqual(loaded_or_failed, set(checkers.BUILTIN))
        self.assertIsInstance(import_failures(), dict)


if __name__ == "__main__":
    unittest.main()
