"""Does the test suite this repository advertises exist, and does it pass now?

Three claims hide inside "run `make test`", and they fail independently:

1. **There is a suite.** A `tests/` directory named in a README is worth exactly
   as much as the files in it. This repository's own README promised one before
   any test file existed, and `make test` exited 2.
2. **It passes.** The only way to know is to run it, so this checker runs it and
   attaches the real output. A summary of a failure is the reviewer's opinion of
   the failure; the traceback is the failure. It also has to be run the way the
   repository says: driving a pytest suite through `unittest discover` produces
   an ImportError that is a fact about the runner, not about the tests.
3. **It asserts something.** This is the one nobody checks. `unittest discover`
   over a directory containing no tests exits **zero**. (pytest is better here -
   it returns `ExitCode.NO_TESTS_COLLECTED`, 5 - but a `make test` wrapper that
   ignores the code, or a `|| true`, restores the same trap.) A green tick with
   an empty suite is
   worse than a red one, because it actively certifies that nothing is wrong -
   and it is easy to create by accident. It happened during the work that
   produced this file: creating `tests/` to hold a shell script turned a
   failing `make test` into a passing one that ran nothing at all.

So a zero exit is not accepted on its own. The count of collected tests is
parsed out of the runner's own output, and a suite that collected none is
reported however green it looked.
"""

from __future__ import annotations

import importlib.util
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

#: Directories conventionally holding a suite.
TEST_DIR_NAMES = ("tests", "test")
#: A file that is a test rather than a helper beside one.
_TEST_FILE_RE = re.compile(r"^(?:test_.+|.+_test)\.py$")
#: Text that makes a command a test command.
_TEST_CMD_RE = re.compile(r"\b(?:unittest|pytest|py\.test|nose2)\b|\bmake\s+(?:tests?|check)\b")
#: Makefile targets that promise a suite.
_TEST_TARGET_RE = re.compile(r"^(?:tests?|check)$")

#: "Ran 12 tests in 0.4s" (unittest) / "12 passed" / "collected 12 items" (pytest).
_COUNT_RES = (
    re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE),
    re.compile(r"collected (\d+) items?", re.MULTILINE),
    re.compile(r"(\d+) passed", re.MULTILINE),
)
#: unittest's own words for "there was nothing to run".
_EMPTY_MARKERS = ("NO TESTS RAN", "no tests ran", "Ran 0 tests", "collected 0 items")


def _test_files(repo: RepoIndex) -> list[str]:
    return sorted(rel for rel in repo.all_paths if _TEST_FILE_RE.match(Path(rel).name))


def _test_dirs(repo: RepoIndex) -> list[str]:
    return [name for name in TEST_DIR_NAMES if (repo.root / name).is_dir()]


def _documented_commands(repo: RepoIndex) -> list[tuple[Claim, str]]:
    """Every place the repository tells someone a test command exists."""
    out: list[tuple[Claim, str]] = []
    for source in repo.markdown:
        for fence in source.fences():
            for line, command in fence.commands:
                if _TEST_CMD_RE.search(command):
                    out.append((Claim(command, source.rel, line, kind="command"), command))
    for name in ("Makefile", "makefile", "GNUmakefile"):
        source = repo.get(name)
        if source is None:
            continue
        current = ""
        for lineno, raw in enumerate(source.lines, start=1):
            if not raw.startswith("\t"):
                head = raw.split(":", 1)[0].strip() if ":" in raw else ""
                current = head if _TEST_TARGET_RE.match(head) else ""
                continue
            body = raw.strip()
            if current and body and _TEST_CMD_RE.search(body):
                out.append((Claim(body, source.rel, lineno, kind="make_recipe"), body))
    return out


def _count(output: str) -> int | None:
    for pattern in _COUNT_RES:
        if m := pattern.search(output):
            return int(m.group(1))
    return None


@dataclass
class TestsEvidenceChecker:
    name: str = "tests_evidence"
    description: str = "The advertised test suite exists, runs, passes, and asserts something."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        documented = _documented_commands(repo)
        files = _test_files(repo)
        dirs = _test_dirs(repo)

        if not documented:
            return  # nothing promises a suite; not this checker's business

        first_claim = documented[0][0]

        if not files:
            searched = [*dirs, str(repo.root)] if dirs else [str(repo.root)]
            for claim, command in documented:
                yield Finding(
                    checker=self.name, code="TESTS_ABSENT",
                    verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                    evidence=[
                        Evidence.at(claim.path, claim.line, claim.text,
                                    summary=f"{claim.path}:{claim.line} documents `{command}`"),
                        Evidence.absent(
                            "no file matching test_*.py or *_test.py exists anywhere in the tree",
                            searched=searched),
                    ],
                    detail=f"`{command}` is documented, but the repository contains no test files.",
                    remedy="Add the suite, or remove the command that promises one.",
                )
            return

        if not config.run_commands:
            yield Finding(
                checker=self.name, code="TESTS_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=first_claim,
                detail=(f"{len(files)} test file(s) exist but were not executed: run_commands is "
                        "off, so whether the suite passes is not established here."),
            )
            return

        wants_pytest = any("pytest" in cmd for _, cmd in documented)
        if wants_pytest and importlib.util.find_spec("pytest") is None:
            yield Finding(
                checker=self.name, code="TESTS_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=first_claim,
                detail=("this repository documents pytest, which is not installed here. "
                        "Driving a pytest suite through `unittest discover` would report an "
                        "ImportError about the runner rather than anything about the tests, "
                        "so the suite was not run."),
            )
            return

        argv = (["python3", "-m", "pytest", "-q", dirs[0] if dirs else "."]
                if wants_pytest else
                ["python3", "-m", "unittest", "discover", "-s", dirs[0] if dirs else ".", "-t", "."])
        ran = Evidence.ran(argv, cwd=repo.root, timeout=max(config.command_timeout, 300.0),
                           env=self._env(repo, config))

        if ran.exit_code is None:
            yield Finding(
                checker=self.name, code="TESTS_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=first_claim,
                detail=(f"the suite produced no exit status: "
                        f"{ran.output.splitlines()[-1] if ran.output else 'no output'}"),
            )
            return

        collected = _count(ran.output)
        listing = Evidence.measured(
            f"{len(files)} test file(s) found: " + ", ".join(files[:8])
            + (f" (+{len(files) - 8} more)" if len(files) > 8 else ""),
            value=len(files), path=str(repo.root))

        # `unittest discover` needs the start directory to be an importable
        # package. A pytest-style suite with no `__init__.py` is the standard
        # layout, not a broken one, and reporting it as a failing suite blames
        # the repository for this checker's choice of runner.
        if ran.exit_code != 0 and "Start directory is not importable" in ran.output:
            yield Finding(
                checker=self.name, code="TESTS_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=first_claim,
                detail=(f"`{' '.join(argv)}` could not import the start directory, which is the "
                        "normal layout for a pytest suite. That is a fact about the runner this "
                        "checker chose, not about the tests, so the suite is not called failing."),
            )
            return

        if ran.exit_code != 0:
            yield Finding(
                checker=self.name, code="TESTS_FAIL",
                verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=first_claim,
                evidence=[Evidence.at(first_claim.path, first_claim.line, first_claim.text),
                          ran, listing],
                detail=f"the documented suite exits {ran.exit_code}; the output is attached.",
                remedy="Fix the failing tests, or stop documenting the command as working.",
            )
            return

        # Exit zero. That is necessary and not sufficient - see the module docstring.
        if collected == 0 or any(marker in ran.output for marker in _EMPTY_MARKERS):
            yield Finding(
                checker=self.name, code="TESTS_VACUOUS",
                verdict=Verdict.UNSUPPORTED, severity=Severity.ERROR, claim=first_claim,
                evidence=[Evidence.at(first_claim.path, first_claim.line, first_claim.text),
                          ran, listing],
                detail=("the suite exits 0 but collected no tests, so the green result asserts "
                        "nothing. A passing empty suite certifies that nothing is wrong."),
                remedy="Make the runner discover the tests, or remove the empty suite.",
            )
            return

        if collected is None:
            yield Finding(
                checker=self.name, code="TESTS_COUNT_UNKNOWN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=first_claim,
                detail=("the suite exits 0, but no test count could be parsed from its output, "
                        "so it cannot be distinguished from a suite that collected nothing."),
            )
            return

        yield Finding(
            checker=self.name, code="TESTS_PASS",
            verdict=Verdict.SUPPORTED, severity=Severity.INFO, claim=first_claim,
            evidence=[ran, Evidence.measured(f"{collected} tests collected and passed",
                                             value=collected, path=str(repo.root)), listing],
            detail=f"{collected} tests ran and passed.",
        )

    def _env(self, repo: RepoIndex, config: CheckConfig) -> dict[str, str]:
        env = dict(os.environ)
        roots = [str((repo.root / r).resolve()) for r in config.source_roots]
        prior = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join([*roots, prior] if prior else roots)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env


register(TestsEvidenceChecker())
