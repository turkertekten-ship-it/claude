"""The checker contract and the registry that runs them.

A checker is deliberately a very small thing: given the repository, yield
findings. It gets no way to print, no way to decide the exit code, and no way to
mutate the repository. That narrowness is what makes the set of them
composable - and it is what lets `ultrareview` state honestly which checks ran,
because a checker that raises is recorded as *skipped with a reason* rather than
silently contributing nothing to a report that then reads as clean.

Two switches on `CheckConfig` matter more than the rest:

* `run_commands` - a checker may execute a command from the repository's own
  documentation to see whether it works. That is the difference between "the
  README says `make test` works" and "`make test` exits 2 with an ImportError".
  It is opt-out because executing what a repo tells you to execute is a real
  action with real side effects.
* `allow_network` - off by default. A check whose result depends on the network
  is not reproducible, and an unreachable host must never be reported as a
  broken link. With it off, network-dependent checks return UNVERIFIABLE, which
  is the honest answer.
"""

from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Iterable, Protocol, runtime_checkable

from tools.claims import RepoIndex
from tools.evidence import Finding, Report


@dataclass(slots=True)
class CheckConfig:
    """Switches that change what a checker is allowed to do, not what it decides."""

    run_commands: bool = True
    allow_network: bool = False
    command_timeout: float = 120.0
    #: Commands that may be executed verbatim from the repo's own docs. Anything
    #: not matching is inspected statically instead of run - a README is not a
    #: trusted script, and `curl ... | sh` in one must never be executed because
    #: a review tool decided to be thorough.
    command_allowlist: tuple[str, ...] = ("make", "python3", "python", "bash", "sh", "pytest")
    #: Extra directories to treat as importable roots when resolving symbols.
    source_roots: tuple[str, ...] = ("src", ".")
    #: Other repositories on disk that this one legitimately points at. A
    #: reference to a sibling's file is not a broken reference, but without the
    #: sibling present it is not a verified one either - so with none supplied
    #: such references are reported UNVERIFIABLE rather than guessed either way.
    sibling_roots: tuple[str, ...] = ()
    exclude_checkers: tuple[str, ...] = ()
    only_checkers: tuple[str, ...] = ()

    def for_subprocess(self) -> "CheckConfig":
        """The config a nested run must use.

        A repository whose own `make check` invokes this tool - which is exactly
        what a repository that takes its own checks seriously will do - makes
        command execution recursive: the checker runs `make check`, which runs
        the checker, which runs `make check`. This is not hypothetical. It was
        found by running this tool on the repository that contains it.

        The guard is an environment variable rather than a call-depth counter
        because the recursion crosses process boundaries, where a counter cannot
        follow it. The marker is exported before any command runs, so every
        descendant - at any depth, through any shell - sees it and turns command
        execution off. Those checks then report UNVERIFIABLE, which is the
        truthful answer: the inner run genuinely did not establish them.
        """
        return replace(self, run_commands=False)


@runtime_checkable
class Checker(Protocol):
    name: str
    description: str

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterable[Finding]: ...


#: Exported into every subprocess a checker starts. Its presence means "you are
#: already inside an ultrareview run"; see CheckConfig.for_subprocess.
ENV_MARKER = "ULTRAREVIEW_ACTIVE"


def nested() -> bool:
    """True when this process is running underneath another ultrareview run."""
    return bool(os.environ.get(ENV_MARKER))


_REGISTRY: dict[str, Checker] = {}


def register(checker: Checker) -> Checker:
    """Register a checker instance. Duplicate names are a programming error."""
    if checker.name in _REGISTRY:
        raise ValueError(f"duplicate checker name: {checker.name!r}")
    _REGISTRY[checker.name] = checker
    return checker


def registered() -> dict[str, Checker]:
    return dict(_REGISTRY)


def load_builtin_checkers() -> dict[str, Checker]:
    """Import the bundled checkers so importing this module has no side effects."""
    from tools import checkers  # noqa: F401  (its __init__ registers each one)

    return registered()


def import_failures() -> dict[str, str]:
    """Checkers that could not be imported, and why.

    Returned separately from the registry so the runner can put them in the
    report rather than letting a broken module reduce the review silently.
    """
    from tools import checkers

    return dict(checkers.IMPORT_FAILURES)


def run(root: str | Path, config: CheckConfig | None = None,
        on_start: Callable[[str], None] | None = None) -> Report:
    """Run every selected checker and collect one report.

    A checker that raises does not abort the run and does not vanish: it lands
    in `report.skipped` with its traceback's last line. A review that silently
    lost a third of its checks is worse than one that ran none, because it looks
    complete.
    """
    config = config or CheckConfig()
    was_nested = nested()
    if was_nested and config.run_commands:
        config = config.for_subprocess()
    # Set before any checker runs, so every subprocess inherits it - and
    # restored in the `finally` below. Leaving it set would make the *second*
    # run() in one process think it was nested and silently stop executing
    # commands, so a caller looping over several repositories would get a real
    # review of the first and a quietly degraded one of every other.
    previous_marker = os.environ.get(ENV_MARKER)
    os.environ[ENV_MARKER] = "1"
    repo = RepoIndex(Path(root))
    report = Report(root=str(repo.root))
    started = time.monotonic()

    available = load_builtin_checkers()
    for broken, reason in sorted(import_failures().items()):
        report.skipped[broken] = f"failed to import: {reason}"

    for name, checker in sorted(available.items()):
        if config.only_checkers and name not in config.only_checkers:
            continue
        if name in config.exclude_checkers:
            report.skipped[name] = "excluded by configuration"
            continue
        if on_start:
            on_start(name)
        try:
            findings = list(checker.check(repo, config))
        except Exception as e:  # a broken checker must not take the review with it
            report.skipped[name] = f"{type(e).__name__}: {e} ({_where(e)})"
            continue
        report.checkers_run.append(name)
        report.extend(findings)

    if previous_marker is None:
        os.environ.pop(ENV_MARKER, None)
    else:
        os.environ[ENV_MARKER] = previous_marker

    report.duration_s = time.monotonic() - started
    if was_nested:
        report.skipped["(nested run)"] = (
            "command execution was disabled because this run is inside another "
            "ultrareview run; affected checks are reported UNVERIFIABLE"
        )
    return report


def _where(exc: BaseException) -> str:
    tb = traceback.extract_tb(exc.__traceback__)
    if not tb:
        return "unknown location"
    frame = tb[-1]
    return f"{Path(frame.filename).name}:{frame.lineno}"


@dataclass
class BaseChecker:
    """Convenience base: gives a checker a name, a description and equality.

    Checkers are registered as instances rather than classes so that a caller
    can register a configured variant (a stricter numeric checker, a coverage
    checker with a project-specific manifest) without subclassing.
    """

    name: str = "base"
    description: str = ""
    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterable[Finding]:
        raise NotImplementedError
