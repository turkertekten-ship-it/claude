"""Is the repository's dependency story true?

Three assertions live in a Python project's dependency story, and all three are
made in places that never see a test:

* `pyproject.toml` says what has to be installed for the code to import;
* `[project.optional-dependencies]` says which of those are *optional*;
* the prose - a README headline, a package docstring, an ADR - says what the
  whole thing costs to run, usually as some form of "zero dependencies".

None of the three is checked by the import that would actually fail. A package
added during a refactor and never declared installs cleanly and raises
`ModuleNotFoundError` on first use; an accelerator declared under an extra but
imported at module scope makes the extra mandatory in fact while the manifest
still calls it optional; and a "runs on the standard library alone" headline
survives the commit that stops it being true, because nothing reads headlines.

So this checker does not read any of the three as evidence. It builds the import
graph with `ast.parse` over every Python file in the tree and reads the answer
off that, then holds each of the three assertions to it.

Two decisions here are about *not* crying wolf, which CONTRACT.md rule 6 makes
the expensive failure:

**A guarded import is not a dependency.** `try: import numpy / except
ImportError:` and an import inside a function body both execute only sometimes,
so neither is required to import the module that contains them - which is
exactly how an optional accelerator is meant to be written. Contradicting a
zero-dependency claim on the strength of one would be reporting the correct
implementation of the claim as a violation of it. Imports under an `if` are
treated the same way and for the same reason: `if TYPE_CHECKING:` and
`if sys.version_info >= ...` never run unconditionally either.

**The import name is not the distribution name.** `import yaml` is satisfied by
PyYAML and `import bs4` by beautifulsoup4. Matching on the import name alone
would report a correctly declared dependency as undeclared, so a declared name
matches through an alias table and through the `python-`/`-py` affixes that
account for most of the rest. Every mapping here can only ever *suppress* a
finding, so a gap in the table costs a miss and never a fabrication.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from tools.claims import SKIP_DIRS, RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

MANIFEST = "pyproject.toml"

#: A zero-dependency assertion, in the spellings projects actually use.
_ZERO_DEP_RE = re.compile(
    r"zero[- ](?:required[- ])?dependenc"
    r"|no required dependenc"
    r"|standard library alone"
    r"|stdlib alone"
    r"|only the standard library"
    r"|dependency-free",
    re.IGNORECASE,
)

#: Path-shaped tokens are removed before the sentence is matched. The ADR here
#: is called `docs/adr/0001-zero-dependency-core.md`, and a filename is a label,
#: not an assertion - citing one is not claiming what it says.
_PATHISH_RE = re.compile(r"`[^`\s]*\.(?:md|py|toml|rst|txt|cfg|ini)`|\S*[/\\]\S*")

#: Nodes whose body does not run every time the module is imported. An import
#: inside one of these is optional by construction; see the module docstring.
_GUARDING = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Try,
    ast.TryStar,
    ast.If,
    ast.While,
    ast.For,
    ast.AsyncFor,
)

#: Modules that are standard library in some CPython this repository may target
#: but not in the interpreter running the check (PEP 594 removals, and distutils
#: per PEP 632). Without them a 3.13 checker would report a 3.11 repository's
#: `import telnetlib` as an undeclared third-party package - a finding produced
#: by the reviewer's environment rather than by the repository.
_RETIRED_STDLIB = frozenset(
    "aifc asynchat asyncore audioop cgi cgitb chunk crypt distutils imghdr imp "
    "mailcap msilib nis nntplib ossaudiodev pipes smtpd sndhdr spwd sunau "
    "telnetlib uu xdrlib".split()
)

#: import name -> distributions that provide it, normalised. Only ever
#: suppresses a finding: a missing entry costs a miss, never a fabrication.
_PROVIDED_BY: dict[str, tuple[str, ...]] = {
    "OpenSSL": ("pyopenssl",),
    "PIL": ("pillow",),
    "attr": ("attrs",),
    "bs4": ("beautifulsoup4",),
    "cv2": ("opencv-python", "opencv-python-headless", "opencv-contrib-python"),
    "dateutil": ("python-dateutil",),
    "docx": ("python-docx",),
    "dotenv": ("python-dotenv",),
    "fitz": ("pymupdf",),
    "git": ("gitpython",),
    "grpc": ("grpcio",),
    "jwt": ("pyjwt",),
    "magic": ("python-magic",),
    "markdown_it": ("markdown-it-py",),
    "mpl_toolkits": ("matplotlib",),
    "nacl": ("pynacl",),
    "pkg_resources": ("setuptools",),
    "pptx": ("python-pptx",),
    "serial": ("pyserial",),
    "skimage": ("scikit-image",),
    "sklearn": ("scikit-learn",),
    "usb": ("pyusb",),
    "win32com": ("pywin32",),
    "yaml": ("pyyaml",),
    "zmq": ("pyzmq",),
}

_TEST_DIRS = frozenset({"test", "tests"})

#: Other places a project may declare dependencies. They are not parsed - they
#: are looked for, so that "nothing is declared" is never concluded from the
#: absence of the one file this checker knows how to read.
_OTHER_MANIFESTS = (
    "requirements.txt",
    "requirements-dev.txt",
    "requirements/base.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "environment.yml",
)

#: The `dependencies` key itself, not the word: `description = "... zero
#: dependencies"` is a sentence about the key, and quoting it as the key would
#: put a finding's locator on the wrong line.
_DEPS_KEY_RE = re.compile(r"^\s*dependencies\s*=")


# ------------------------------------------------------------------- the graph


@dataclass(slots=True, frozen=True)
class _Import:
    """One import statement: the top-level name, and where it was written."""

    module: str
    path: str
    line: int
    text: str
    guarded: bool


def _descend(node: ast.AST, guarded: bool, source: SourceFile, out: list[_Import]) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Import):
            for alias in child.names:
                out.append(_record(alias.name, child.lineno, source, guarded))
        elif isinstance(child, ast.ImportFrom):
            # `from . import x` is first-party by construction; there is nothing
            # a manifest could declare that would satisfy or fail to satisfy it.
            if not child.level and child.module:
                out.append(_record(child.module, child.lineno, source, guarded))
        else:
            _descend(child, guarded or isinstance(child, _GUARDING), source, out)


def _record(dotted: str, line: int, source: SourceFile, guarded: bool) -> _Import:
    return _Import(dotted.split(".")[0], source.rel, line, source.line_text(line).strip(), guarded)


def _parse(source: SourceFile) -> tuple[list[_Import], str, int]:
    """Imports in one file, or the reason the file could not be read as Python."""
    try:
        tree = ast.parse(source.text, filename=source.rel)
    except (SyntaxError, ValueError) as e:
        line = getattr(e, "lineno", None) or 1
        return [], f"{type(e).__name__}: {e}", line
    out: list[_Import] = []
    _descend(tree, False, source, out)
    return out, "", 0


def _first_party(repo: RepoIndex, config: CheckConfig) -> frozenset[str]:
    """Top-level names this repository provides itself.

    The repository root is always scanned as well as `config.source_roots`: a
    checker run with `source_roots=("src",)` must still know that `import tools`
    in this tree resolves to the directory next to `src`, not to PyPI.
    """
    names: set[str] = set()
    bases = [repo.root]
    for rel in config.source_roots:
        candidate = (repo.root / rel).resolve()
        try:
            candidate.relative_to(repo.root)
        except ValueError:
            continue  # escapes the repo; a checker never probes the host
        bases.append(candidate)
    for base in bases:
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            name = child.name
            if name in SKIP_DIRS or name.startswith("."):
                continue
            if child.is_dir() and name.isidentifier():
                names.add(name)
            elif child.suffix == ".py" and child.stem.isidentifier():
                names.add(child.stem)
    return frozenset(names)


def _is_stdlib(module: str) -> bool:
    return module in sys.stdlib_module_names or module in _RETIRED_STDLIB


def _is_test_file(rel: str) -> bool:
    """Is this file part of the test suite rather than of the shipped package?

    It matters twice: a dev extra imported at module scope in a test file is the
    extra working as designed, and `pip install pkg` never imports the tests, so
    neither case says anything about what the package itself requires.
    """
    parts = rel.replace("\\", "/").split("/")
    if any(part in _TEST_DIRS for part in parts[:-1]):
        return True
    name = parts[-1]
    return name == "conftest.py" or name.startswith("test_") or name.endswith("_test.py")


# ---------------------------------------------------------------- the manifest


@dataclass(slots=True)
class _Manifest:
    """What `pyproject.toml` declares, and whether it can be read at all."""

    runtime: dict[str, str]              # normalised distribution -> requirement
    optional: dict[str, tuple[str, str]]  # normalised distribution -> (group, requirement)
    build: dict[str, str]                # [build-system] requires, same shape as runtime
    groups: tuple[str, ...]
    has_project: bool
    dynamic: bool = False
    error: str = ""

    @property
    def usable(self) -> bool:
        return self.has_project and not self.error and not self.dynamic


def _normalise(name: str) -> str:
    """PEP 503 normalisation: the only spelling two names can be compared in."""
    return re.sub(r"[-_.]+", "-", name.strip()).lower()


def _requirement_name(requirement: str) -> str:
    """The distribution name out of a PEP 508 requirement string."""
    head = re.split(r"[\s\[<>=!~;(@,]", requirement.strip(), maxsplit=1)[0]
    return _normalise(head)


def _strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _load_manifest(repo: RepoIndex) -> _Manifest | None:
    source = repo.get(MANIFEST)
    if source is None:
        return None
    try:
        # Parsed from the text RepoIndex already read, so the manifest a finding
        # quotes and the manifest it reasons about are the same bytes.
        data = tomllib.loads(source.text)
    except (tomllib.TOMLDecodeError, ValueError) as e:
        return _Manifest({}, {}, {}, (), has_project=False, error=f"{type(e).__name__}: {e}")
    project = data.get("project")
    if not isinstance(project, dict):
        return _Manifest({}, {}, {}, (), has_project=False)

    runtime = {_requirement_name(r): r for r in _strings(project.get("dependencies"))}
    optional: dict[str, tuple[str, str]] = {}
    extras = project.get("optional-dependencies")
    groups: list[str] = []
    if isinstance(extras, dict):
        for group in sorted(extras):
            groups.append(group)
            for requirement in _strings(extras[group]):
                optional.setdefault(_requirement_name(requirement), (group, requirement))
    build_table = data.get("build-system")
    build: dict[str, str] = {}
    if isinstance(build_table, dict):
        build = {_requirement_name(r): r for r in _strings(build_table.get("requires"))}
    dynamic = any(
        key in ("dependencies", "optional-dependencies") for key in _strings(project.get("dynamic"))
    )
    return _Manifest(runtime, optional, build, tuple(groups), has_project=True, dynamic=dynamic)


def _keys(module: str) -> set[str]:
    """Every distribution name that could plausibly ship `module`."""
    out = {_normalise(module)}
    for alias in _PROVIDED_BY.get(module, ()) or _PROVIDED_BY.get(module.lower(), ()):
        out.add(_normalise(alias))
    return out


def _dist_keys(dist: str) -> set[str]:
    out = {dist, dist.replace("-", "")}
    for prefix in ("python-", "py-"):
        if dist.startswith(prefix):
            out.add(dist[len(prefix):])
    for suffix in ("-python", "-py"):
        if dist.endswith(suffix):
            out.add(dist[: -len(suffix)])
    return out


def _declared(module: str, manifest: _Manifest) -> tuple[str, str] | None:
    """Where `module` is declared, as (where, requirement), or None."""
    keys = _keys(module)
    for dist, requirement in sorted(manifest.runtime.items()):
        if keys & _dist_keys(dist):
            return "dependencies", requirement
    for dist, (group, requirement) in sorted(manifest.optional.items()):
        if keys & _dist_keys(dist):
            return f"optional-dependencies.{group}", requirement
    # A build backend is declared, just for a different phase: reporting
    # `from setuptools import setup` as undeclared would be a fabrication.
    for dist, requirement in sorted(manifest.build.items()):
        if keys & _dist_keys(dist):
            return "build-system.requires", requirement
    return None


def _quote(source: SourceFile, *needles: str | re.Pattern[str]) -> tuple[int, str] | None:
    """The first line matching any needle, in the order given, quoted verbatim.

    Findings quote the manifest rather than describing it, so a reader can run
    `sed -n` on the locator and see the declaration the verdict rests on.
    """
    for needle in needles:
        for lineno, raw in enumerate(source.lines, start=1):
            hit = needle.search(raw) if isinstance(needle, re.Pattern) else needle in raw
            if hit:
                return lineno, raw.strip()
    return None


def _undecidable(repo: RepoIndex, manifest: _Manifest | None) -> str:
    """Why the declared set cannot be read, or "" when it can.

    Returned as a sentence rather than a flag because it becomes the `detail` of
    an UNVERIFIABLE finding, and CONTRACT.md rule 3 wants the reason named.
    """
    if manifest is None:
        others = [name for name in _OTHER_MANIFESTS if repo.exists(name)]
        if others:
            return f"there is no {MANIFEST}, and " + ", ".join(others) + " may declare dependencies"
        return ""
    if manifest.error:
        return f"{MANIFEST} does not parse ({manifest.error})"
    if not manifest.has_project:
        return f"{MANIFEST} has no [project] table"
    if manifest.dynamic:
        return f"{MANIFEST} declares its dependencies dynamically"
    return ""


def _own_path(repo: RepoIndex) -> str:
    """This module's path inside the repository under review, if it is in it.

    A checker must not quote its own source as the repository's claim: this file
    contains the very phrase it searches for, and confirming a sentence it wrote
    itself would be the tool reviewing the tool rather than the repository.
    """
    try:
        return Path(__file__).resolve().relative_to(repo.root).as_posix()
    except (ValueError, OSError):
        return ""


# ------------------------------------------------------------------ the checks


@dataclass
class DepsChecker:
    name: str = "deps"
    description: str = (
        "Every import resolves to the stdlib, this repo, or a declared dependency - "
        "and a zero-dependency headline is confirmed against the import graph."
    )

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        manifest = _load_manifest(repo)
        first_party = _first_party(repo, config)

        imports: list[_Import] = []
        unparsed: list[str] = []
        for source in repo.python:
            found, error, line = _parse(source)
            imports.extend(found)
            if not error:
                continue
            unparsed.append(source.rel)
            # A file that will not parse is a hole in the graph. Saying so is
            # the only honest option: the imports it makes were never seen.
            yield Finding(
                checker=self.name,
                code="IMPORT_GRAPH_INCOMPLETE",
                verdict=Verdict.UNVERIFIABLE,
                severity=Severity.INFO,
                claim=Claim(source.line_text(line).strip(), source.rel, line, kind="python"),
                detail=f"{source.rel} does not parse ({error}); its imports are not in the graph",
            )
        third_party = [
            imp
            for imp in imports
            if not _is_stdlib(imp.module) and imp.module not in first_party
        ]
        headline = _headline(repo)
        undecidable = _undecidable(repo, manifest)

        if undecidable and (third_party or headline):
            yield self._unreadable(repo, headline, undecidable)
        elif not undecidable and manifest is not None:
            yield from self._undeclared(manifest, third_party)
            yield from self._eager_optional(repo, manifest, third_party)

        if headline is not None:
            yield from self._zero_dep(
                repo, manifest, headline, imports, third_party, first_party, unparsed, undecidable
            )

    # ------------------------------------------------------------------ pieces

    def _unreadable(self, repo: RepoIndex, headline: Claim | None, reason: str) -> Finding:
        source = repo.get(MANIFEST)
        claim = headline
        if claim is None and source is not None:
            spot = _quote(source, _DEPS_KEY_RE, "[project]") or (1, source.line_text(1).strip())
            claim = Claim(spot[1], MANIFEST, spot[0], kind="config")
        return Finding(
            checker=self.name,
            code="DEPENDENCY_MANIFEST_UNREADABLE",
            verdict=Verdict.UNVERIFIABLE,
            severity=Severity.INFO,
            claim=claim or Claim("", MANIFEST, 1, kind="config"),
            detail=f"cannot tell what is declared: {reason}",
        )

    def _undeclared(self, manifest: _Manifest, third_party: list[_Import]) -> Iterator[Finding]:
        # Only unguarded imports are reported. A guarded one is optional by
        # construction (module docstring), and an ERROR on it would be the
        # checker calling the documented way of writing an optional import a
        # broken promise.
        for (module, path), sites in sorted(_group(third_party, guarded=False).items()):
            if _declared(module, manifest) is not None:
                continue
            first = sites[0]
            searched = [f"{MANIFEST} [project] dependencies"]
            searched += [f"{MANIFEST} [project.optional-dependencies] {g}" for g in manifest.groups]
            searched += [f"{MANIFEST} [build-system] requires", "sys.stdlib_module_names"]
            yield Finding(
                checker=self.name,
                code="UNDECLARED_DEPENDENCY",
                verdict=Verdict.CONTRADICTED,
                severity=Severity.ERROR,
                claim=Claim(first.text, path, first.line, kind="import"),
                evidence=[
                    Evidence.at(
                        site.path,
                        site.line,
                        site.text,
                        summary=f"{site.path}:{site.line} imports {module}",
                    )
                    for site in sites[:3]
                ]
                + [
                    Evidence.absent(
                        f"{module!r} is not the standard library, not provided by this "
                        f"repository, and matches nothing declared in {MANIFEST}",
                        searched=searched,
                    )
                ],
                detail=(
                    f"{path}:{first.line} imports {module!r}, which nothing declares; "
                    f"an install from {MANIFEST} raises ModuleNotFoundError here"
                ),
                remedy=f"add {module} to [project] dependencies, or drop the import",
            )

    def _eager_optional(
        self, repo: RepoIndex, manifest: _Manifest, third_party: list[_Import]
    ) -> Iterator[Finding]:
        source = repo.get(MANIFEST)
        for (module, path), sites in sorted(_group(third_party, guarded=False).items()):
            if _is_test_file(path):
                continue  # a dev extra used by the test suite is the extra working
            where = _declared(module, manifest)
            if where is None or not where[0].startswith("optional-dependencies."):
                continue
            group, requirement = where[0].split(".", 1)[1], where[1]
            first = sites[0]
            spot = (
                _quote(source, requirement, "[project.optional-dependencies]")
                if source is not None
                else None
            )
            claim = (
                Claim(spot[1], MANIFEST, spot[0], kind="config")
                if spot
                else Claim(first.text, path, first.line, kind="import")
            )
            yield Finding(
                checker=self.name,
                code="OPTIONAL_DEP_IMPORTED_EAGERLY",
                verdict=Verdict.CONTRADICTED,
                severity=Severity.WARN,
                claim=claim,
                evidence=[
                    Evidence.at(
                        first.path,
                        first.line,
                        first.text,
                        summary=f"{first.path}:{first.line} imports {module} at module scope",
                    )
                ],
                detail=(
                    f"{requirement!r} is declared only under the optional group {group!r}, "
                    f"but {path} imports {module!r} unconditionally at module scope: without "
                    f"the extra installed, importing that module fails"
                ),
                remedy=(
                    f"guard the import (try/except ImportError, or import {module} inside the "
                    f"function that uses it), or move {requirement!r} into [project] dependencies"
                ),
            )

    def _zero_dep(
        self,
        repo: RepoIndex,
        manifest: _Manifest | None,
        headline: Claim,
        imports: list[_Import],
        third_party: list[_Import],
        first_party: frozenset[str],
        unparsed: list[str],
        undecidable: str,
    ) -> Iterator[Finding]:
        names = sorted({imp.module for imp in imports})
        stdlib = [n for n in names if _is_stdlib(n)]
        mine = [n for n in names if not _is_stdlib(n) and n in first_party]
        outside = sorted({imp.module for imp in third_party})
        totals = {
            "python_files": len(repo.python),
            "distinct_imports": len(names),
            "stdlib": len(stdlib),
            "first_party": len(mine),
            "third_party": len(outside),
        }
        measured = Evidence.measured(
            f"{totals['python_files']} python files import {totals['distinct_imports']} distinct "
            f"top-level modules: {totals['stdlib']} standard library, "
            f"{totals['first_party']} from this repository, {totals['third_party']} from elsewhere",
            value=totals,
        )

        # A guarded third-party import is not an offender: see the module
        # docstring. A declared one imported only by the test suite is not one
        # either - `pip install pkg` never imports the tests.
        offenders = [
            imp
            for imp in third_party
            if not imp.guarded
            and not (
                _is_test_file(imp.path)
                and manifest is not None
                and manifest.usable
                and _declared(imp.module, manifest) is not None
            )
        ]
        source = repo.get(MANIFEST)
        declared_line = _quote(source, _DEPS_KEY_RE) if source is not None else None
        required = (
            sorted(manifest.runtime.values())
            if manifest is not None and manifest.usable
            else []
        )

        reasons: list[str] = []
        against: list[Evidence] = [
            Evidence.at(
                imp.path,
                imp.line,
                imp.text,
                summary=f"{imp.path}:{imp.line} imports {imp.module} unconditionally",
            )
            for imp in sorted(offenders, key=lambda i: (i.path, i.line, i.module))[:4]
        ]
        if offenders:
            named = sorted({imp.module for imp in offenders})
            reasons.append(
                ", ".join(named)
                + (" is" if len(named) == 1 else " are")
                + " imported unconditionally and neither standard library nor part of this"
                + " repository"
            )
        if required and declared_line:
            against.append(
                Evidence.at(
                    MANIFEST,
                    declared_line[0],
                    declared_line[1],
                    summary=f"{MANIFEST} requires {', '.join(required)}",
                )
            )
            reasons.append(f"{MANIFEST} declares {', '.join(required)} as required")

        if against and reasons:
            yield Finding(
                checker=self.name,
                code="ZERO_DEP_CONTRADICTED",
                verdict=Verdict.CONTRADICTED,
                severity=Severity.ERROR,
                claim=headline,
                evidence=against + [measured],
                detail=(
                    f"{headline.path}:{headline.line} claims no required dependencies, but "
                    + "; ".join(reasons)
                ),
                remedy="guard the import, or stop claiming the repository needs nothing installed",
            )
            return

        # Everything below is the SUPPORTED case CONTRACT.md rule 5 allows: a
        # headline worth confirming, confirmed once, from the graph rather than
        # from the sentence next to it. Anything that left the graph or the
        # manifest undecided was reported above, so silence is the answer here.
        if undecidable or unparsed or outside or required:
            return

        declaration = (
            Evidence.at(
                MANIFEST,
                declared_line[0],
                declared_line[1],
                summary=f"{MANIFEST} declares no dependencies",
            )
            if declared_line
            else Evidence.absent(
                "no dependency manifest in the tree declares anything",
                searched=[MANIFEST, *_OTHER_MANIFESTS],
            )
        )
        yield Finding(
            checker=self.name,
            code="ZERO_DEP_CONFIRMED",
            verdict=Verdict.SUPPORTED,
            severity=Severity.INFO,
            claim=headline,
            evidence=[measured, declaration],
            detail=(
                "the import graph agrees: every import in the tree is standard library or "
                "first-party, and [project] dependencies is empty"
            ),
        )


def _group(imports: list[_Import], *, guarded: bool) -> dict[tuple[str, str], list[_Import]]:
    """Imports by (module, file), sorted by line.

    One finding per module per file: the second `import numpy` in a file has the
    same cause and the same fix as the first, and a report that repeats itself
    is a report that gets skimmed.
    """
    out: dict[tuple[str, str], list[_Import]] = {}
    for imp in imports:
        if imp.guarded != guarded:
            continue
        out.setdefault((imp.module, imp.path), []).append(imp)
    for sites in out.values():
        sites.sort(key=lambda i: i.line)
    return out


def _headline(repo: RepoIndex) -> Claim | None:
    """The zero-dependency claim to hold the graph to, or None.

    Only one is returned even when a project repeats itself, because rule 5
    means a confirmation is worth stating once and worth nothing nine times.
    README first, then by path: the headline claim is the one a reader meets.
    """
    mine = _own_path(repo)
    candidates = [
        claim
        for claim in [*repo.prose_claims(), *repo.comment_claims()]
        if not _is_test_file(claim.path)
        and claim.path != mine
        and _ZERO_DEP_RE.search(_PATHISH_RE.sub(" ", claim.text))
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda c: (0 if c.path == "README.md" else 1, c.path, c.line))
    return candidates[0]


register(DepsChecker())
