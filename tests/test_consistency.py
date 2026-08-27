"""Facts stated twice must agree.

Drift is the cheapest kind of documentation lie to create - bump a version in
one place, forget the other - and the most expensive to notice by reading,
because both statements look right on their own page.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.consistency import ConsistencyChecker
from tools.claims import RepoIndex
from tools.registry import CheckConfig

PYPROJECT = """[project]
name = "widget"
version = "{version}"
requires-python = ">=3.11"
license = {{ text = "MIT" }}
classifiers = ["Programming Language :: Python :: 3.11"]

[tool.setuptools.packages.find]
where = ["src"]
"""


def repo(tmp: str, *, version: str = "0.1.0", dunder: str | None = "0.1.0",
         license_file: bool = True, pkg: str = "widget") -> Path:
    root = Path(tmp)
    (root / "pyproject.toml").write_text(PYPROJECT.format(version=version))
    (root / "src" / pkg).mkdir(parents=True)
    body = f'__version__ = "{dunder}"\n' if dunder else "x = 1\n"
    (root / "src" / pkg / "__init__.py").write_text(body)
    if license_file:
        (root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026\n")
    (root / "README.md").write_text("# widget\n\nA thing.\n")
    return root


def codes(root: Path) -> list[str]:
    return [f.code for f in ConsistencyChecker().check(RepoIndex(root), CheckConfig())]


class TestConsistency(unittest.TestCase):
    def test_agreeing_versions_produce_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(codes(repo(tmp)), [])

    def test_version_drift_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = ConsistencyChecker().check(RepoIndex(repo(tmp, version="0.2.0")), CheckConfig())
            drift = [f for f in found if f.code == "VERSION_DRIFT"]
            self.assertTrue(drift, "0.2.0 in pyproject vs 0.1.0 in __init__ must be reported")
            # Both sides must be cited: a drift finding naming one location is
            # unactionable, because the reader cannot tell which one is wrong.
            paths = {e.path for f in drift for e in f.evidence if e.path}
            self.assertGreaterEqual(len(paths), 2, f"expected two locations, got {paths}")

    def test_a_package_with_no_dunder_version_is_not_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotIn("VERSION_DRIFT", codes(repo(tmp, dunder=None)))

    def test_declared_license_with_no_license_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn("LICENSE_FILE_MISSING", codes(repo(tmp, license_file=False)))

    def test_a_repo_without_pyproject_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# x\n")
            self.assertEqual(codes(root), [])

    def test_findings_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, version="0.9.0", license_file=False)
            self.assertEqual(codes(root), codes(root))


if __name__ == "__main__":
    unittest.main()
