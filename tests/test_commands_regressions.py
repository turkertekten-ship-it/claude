"""Regressions found by reviewing this checker against real Makefile shapes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.commands import CommandChecker, _parse_makefile
from tools.claims import RepoIndex
from tools.registry import CheckConfig

MULTI = ("PY ?= python3\n\nhelp:\n\techo hi\n\n"
         "build dist:\n\t$(PY) -m pkg.missing_cli\n\nlint:\n\techo lint\n")


def repo(tmp: str, files: dict[str, str]) -> Path:
    root = Path(tmp)
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    return root


def codes(root: Path, **kw) -> list[str]:
    return [f.code for f in CommandChecker().check(RepoIndex(root), CheckConfig(**kw))]


class TestMultiTargetRules(unittest.TestCase):
    """`build dist:` defines two targets. A single-name pattern matched neither."""

    def test_both_targets_are_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {"Makefile": MULTI})
            mk = _parse_makefile(RepoIndex(root).get("Makefile"))
            self.assertEqual(sorted(mk.targets), ["build", "dist", "help", "lint"])

    def test_the_shared_recipe_belongs_to_every_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {"Makefile": MULTI})
            mk = _parse_makefile(RepoIndex(root).get("Makefile"))
            for name in ("build", "dist"):
                self.assertEqual([r for _, r in mk.targets[name].recipes],
                                 ["python3 -m pkg.missing_cli"], name)

    def test_a_documented_multi_target_goal_is_not_reported_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {"Makefile": MULTI,
                              "README.md": "# P\n\n```bash\nmake build\n```\n"})
            self.assertNotIn("MAKE_TARGET_MISSING", codes(root, run_commands=False))

    def test_the_shared_recipe_is_still_inspected(self):
        # The other half of the bug: the recipe of a multi-target rule was
        # silently never checked, so a broken command inside it was missed.
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {"Makefile": MULTI, "pkg/__init__.py": "",
                              "README.md": "# P\n\n```bash\nmake build\n```\n"})
            self.assertIn("MODULE_MISSING", codes(root, run_commands=False))

    def test_a_variable_assignment_is_not_read_as_a_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {"Makefile": "PY ?= python3\nCFLAGS := -O2\nhelp:\n\techo hi\n"})
            mk = _parse_makefile(RepoIndex(root).get("Makefile"))
            self.assertEqual(sorted(mk.targets), ["help"])


class TestIllustrativeArguments(unittest.TestCase):
    """A usage example promises the command works, not that its samples exist."""

    def test_a_sample_argument_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {
                "pkg/__init__.py": "", "pkg/cli.py": "print('hi')\n",
                "README.md": "# P\n\n```bash\npython3 -m pkg.cli --config config/settings.toml\n```\n",
            })
            found = list(CommandChecker().check(RepoIndex(root),
                                                CheckConfig(run_commands=True)))
            self.assertTrue(all(not f.is_problem for f in found), [f.code for f in found])
            self.assertIn("COMMAND_NOT_RUN", [f.code for f in found])

    def test_a_command_whose_arguments_all_exist_is_still_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, {
                "pkg/__init__.py": "", "pkg/cli.py": "import sys; sys.exit(4)\n",
                "data.txt": "x\n",
                "README.md": "# P\n\n```bash\npython3 -m pkg.cli data.txt\n```\n",
            })
            self.assertIn("COMMAND_FAILS", codes(root, run_commands=True))


if __name__ == "__main__":
    unittest.main()
