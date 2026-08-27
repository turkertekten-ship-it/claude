"""Where the same fact is stated twice, do the two statements agree?

A repository restates its own facts because the audiences differ. The manifest
states the version for pip, `__version__` states it for a running process, and
a README states it for a person; the manifest names the package for the build
backend, and a directory names it for the import system. Nothing keeps any of
those in step. Bumping one and forgetting the others is not a typo - it is the
repository telling two readers two different things, and neither reader has any
way to know which copy is the stale one.

So this checker never asks whether a statement is *right*. It asks whether the
repository contradicts itself, which is the one kind of wrongness that can be
established from the tree alone: both statements are quoted, both locations
travel on the finding, and the reader decides which of them to change.

The cost of that is silence everywhere two statements are merely *different*.
A README heading and a manifest description are both about the project and are
almost never the same sentence; two differing sentences are not in conflict, and
a checker that reports them as one teaches its reader to skim past it. So every
rule here fires only on a fact with exactly one legal value:

* `VERSION_DRIFT`         - `[project] version` against `__version__` and against
                            a documented `Version:` field.
* `NAME_DRIFT`            - `[project] name` against the package directory that
                            actually exists under a source root.
* `PYTHON_VERSION_DRIFT`  - `requires-python` against the Python classifiers it
                            excludes, and against `[tool.ruff] target-version`.
* `LICENSE_DRIFT`         - the manifest's license against the LICENSE file's and
                            against the one the README names.
* `LICENSE_FILE_MISSING`  - a declared license with no license file to back it.
* `TITLE_DRIFT`           - a README H1 that names a different project.

The last of those is all that survives of "README heading versus manifest
description": a name is an identity claim and two of them can conflict, whereas
a heading and a description that read differently are just prose, and this
checker will not guess which one is wrong.

pyproject.toml is the anchor for every rule. Without it there is no second
statement of anything, and the checker says nothing at all.
"""

from __future__ import annotations

import ast
import posixpath
import re
import tomllib
from dataclasses import dataclass
from typing import Iterator

from tools.claims import RepoIndex, SKIP_DIRS, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

_NAME = "consistency"
MANIFEST = "pyproject.toml"

#: READMEs, in the order a reader would find one. Only the markdown ones are
#: parsed for a heading; all of them are scanned for a license mention, because
#: that scan works on raw lines rather than on markdown structure.
README_FILES = ("README.md", "readme.md", "README.rst", "README.txt")

#: Filenames that carry a license *text*. `LICENSE-MIT` and `COPYING.LESSER`
#: are matched too, which is what makes the dual-license guard below possible:
#: a repository with two of these has not stated one license twice.
_LICENSE_FILE_RE = re.compile(r"^(?:LICEN[CS]E|COPYING)(?:[-._].*)?$", re.IGNORECASE)

#: Directories that are conventionally *not* the distributed package, even when
#: they carry an `__init__.py`. Consulted only after a name match has already
#: failed, so a project whose package really is called `tools` is unaffected.
_NON_PACKAGE_DIRS = frozenset(
    "tests test docs doc tools scripts examples benchmarks bench stubs site".split()
)

#: A file whose whole job is to list versions that are *not* the current one.
#: Reading a release history as a statement about today is the single easiest
#: way for a version check to produce a page of confident nonsense.
_HISTORY_FILE_RE = re.compile(
    r"(?:^|/)(?:changelog|changes|history|news|releases|release-notes)\b", re.IGNORECASE
)

_MARKUP_RE = re.compile(r"[*`]")
_BULLET_RE = re.compile(r"\s*(?:[-*+]|\d+\.)\s+")

#: A version field, anchored at the start of the claim. The anchor is the whole
#: false-positive defence: "Python version: 3.11", "Schema version: 2.0" and
#: "API version 4.1" all state somebody else's version, and all of them fail to
#: match because the word before `version` is not one this pattern allows.
_VERSION_FIELD_RE = re.compile(
    r"^(?:current|latest|released|project|package)?\s*version\b\s*[:=]?\s*"
    r"[\"'`(]*v?(\d+(?:\.\d+)+[\w.+-]*)",
    re.IGNORECASE,
)
_BARE_VERSION_RE = re.compile(r"^v?(\d+(?:\.\d+)+[\w.+-]*)$", re.IGNORECASE)
_VERSION_LABELS = frozenset(
    ("version", "current version", "project version", "package version", "latest version")
)
_RELEASE_RE = re.compile(r"^(\d+(?:\.\d+)*)(.*)$")

_CLASSIFIER_RE = re.compile(r"^Programming Language :: Python :: (\d+)\.(\d+)\s*$")
_TARGET_VERSION_RE = re.compile(r"^py(\d)(\d+)$", re.IGNORECASE)
_SPECIFIER_RE = re.compile(r"(>=|<=|==|~=|!=|>|<)\s*(\d+)(?:\.(\d+))?")

_TABLE_HEADER_RE = re.compile(r"^\s*\[\[?\s*([^\]\s]+)\s*\]\]?\s*(?:#.*)?$")
_NAME_TOKEN_RE = re.compile(r"^[A-Za-z][\w.-]*$")

#: Headings that are a section label rather than a project name.
_GENERIC_HEADINGS = frozenset(
    "readme overview introduction about documentation docs notes index home".split()
)

#: License texts, most specific first. Ordered because an LGPL text quotes the
#: GPL and a BSD-3 text contains all of BSD-2: first match wins, so the specific
#: pattern has to be asked first or the general one answers for it.
_LICENSE_TEXTS: tuple[tuple[str, str], ...] = (
    ("apache-2.0", r"apache license.{0,80}version 2"),
    ("agpl-3.0", r"gnu affero general public license.{0,80}version 3"),
    ("lgpl-2.1", r"gnu lesser general public license.{0,80}version 2\.1"),
    ("lgpl-3.0", r"gnu lesser general public license.{0,80}version 3"),
    ("gpl-3.0", r"gnu general public license.{0,80}version 3"),
    ("gpl-2.0", r"gnu general public license.{0,80}version 2"),
    ("mpl-2.0", r"mozilla public license.{0,80}version 2"),
    ("bsl-1.0", r"boost software license"),
    ("cc0-1.0", r"creative commons zero"),
    ("unlicense", r"\bthe unlicense\b|unlicense\.org"),
    ("isc", r"\bisc license\b|permission to use, copy, modify, and/or distribute"),
    ("mit", r"\bmit license\b|permission is hereby granted, free of charge"),
    ("bsd-3-clause", r"redistribution and use in source and binary forms.{0,4000}neither the name"),
    ("bsd-2-clause", r"redistribution and use in source and binary forms"),
)

#: Short forms of the same identities, for a manifest field or a README line.
#: `BSD` alone is deliberately absent: it does not name one license, and a
#: checker that resolves it to a guess is inventing the fact it then reports.
_LICENSE_TOKENS: tuple[tuple[str, str], ...] = (
    ("apache-2.0", r"\bapache[-_ ]?(?:license[-_ ]?)?2(?:\.0)?\b"),
    ("agpl-3.0", r"\bagpl[-_ ]?v?3"),
    ("lgpl-2.1", r"\blgpl[-_ ]?v?2\.1"),
    ("lgpl-3.0", r"\blgpl[-_ ]?v?3"),
    ("gpl-3.0", r"\bgpl[-_ ]?v?3"),
    ("gpl-2.0", r"\bgpl[-_ ]?v?2"),
    ("mpl-2.0", r"\bmpl[-_ ]?v?2"),
    ("bsd-3-clause", r"\bbsd[-_ ]?3"),
    ("bsd-2-clause", r"\bbsd[-_ ]?2"),
    ("mit", r"\bmit\b"),
    ("isc", r"\bisc\b"),
    ("unlicense", r"\bunlicen[cs]e\b"),
    ("cc0-1.0", r"\bcc0\b"),
    ("bsl-1.0", r"\bboost software license\b"),
    ("proprietary", r"\bproprietary\b|\ball rights reserved\b"),
)

#: How far below a `## License` heading its value may sit. The heading and the
#: name are hardly ever on the same line - "## License" then a blank then "MIT"
#: is the usual shape - so the section has to be read, not just the line.
_LICENSE_SECTION_LINES = 8
_LICENSED_UNDER_RE = re.compile(r"licen[sc]ed under(?: the)?\s+(.{0,60})", re.IGNORECASE)
_LICENSE_HEADING_RE = re.compile(r"^\s*#{1,6}\s*licen[sc]e\b", re.IGNORECASE)
_HEADING_RE = re.compile(r"^\s*#{1,6}\s")


# --------------------------------------------------------------------- manifest


@dataclass(slots=True)
class _Manifest:
    """pyproject.toml, parsed once, with a way back to the line that said it.

    tomllib gives values and no positions, and a finding without a position is
    exactly the unbacked assertion this package exists to prevent. So every
    value that gets reported is paired with the line it was read from, found by
    scanning the same text `RepoIndex` already held.
    """

    source: SourceFile
    data: dict[str, object]

    @property
    def project(self) -> dict[str, object]:
        table = self.data.get("project")
        return table if isinstance(table, dict) else {}

    def tool(self, *path: str) -> object:
        node: object = self.data
        for step in path:
            if not isinstance(node, dict):
                return None
            node = node.get(step)
        return node

    def cite(self, table: str, key: str) -> tuple[int, str]:
        """The line where `table.key` was assigned, or the closest honest stand-in."""
        assignment = re.compile(rf"^\s*(?:{re.escape(key)}|[\"']{re.escape(key)}[\"'])\s*=")
        current = ""
        header: tuple[int, str] | None = None
        for lineno, raw in enumerate(self.source.lines, start=1):
            if match := _TABLE_HEADER_RE.match(raw):
                current = match.group(1).strip()
                if current == table and header is None:
                    header = (lineno, raw.strip())
                continue
            if current == table and assignment.match(raw):
                return lineno, raw.strip()
        return header or self.first_line()

    def cite_literal(self, needle: str) -> tuple[int, str]:
        for lineno, raw in enumerate(self.source.lines, start=1):
            if needle in raw:
                return lineno, raw.strip()
        return self.first_line()

    def first_line(self) -> tuple[int, str]:
        for lineno, raw in enumerate(self.source.lines, start=1):
            if raw.strip():
                return lineno, raw.strip()
        return 1, ""


def _manifest_evidence(manifest: _Manifest, line: int, text: str, summary: str) -> Evidence:
    return Evidence.at(MANIFEST, line, text, summary=summary)


# ---------------------------------------------------------------------- version


def _version_key(text: str) -> tuple[tuple[int, ...], str] | None:
    """A comparable form of a version, or None if it is not one.

    Trailing zero segments are dropped because `0.1` and `0.1.0` are the same
    release under PEP 440, and reporting them as a contradiction would be this
    checker inventing a disagreement out of a formatting choice.
    """
    cleaned = re.sub(r"^[vV]", "", text.strip().strip("\"'`")).strip()
    match = _RELEASE_RE.match(cleaned)
    if not match:
        return None
    parts = [int(piece) for piece in match.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts), match.group(2).strip().lower()


def _demarkup(text: str) -> str:
    return _MARKUP_RE.sub("", text).strip()


def _is_indented_code(raw: str) -> bool:
    """A four-space block is markdown's other way of saying "this is an example".

    Fenced blocks are already dropped by `prose_claims()`; an indented one is
    just as likely to be a manifest excerpt someone pasted, and its version is
    an illustration rather than a claim about this repository.
    """
    if not raw.startswith(("    ", "\t")):
        return False
    return _BULLET_RE.match(raw) is None


def _row_version(raw: str) -> str:
    """The version in a `| Version | 1.2.3 |` row, or ""."""
    cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
    if len(cells) < 2 or _demarkup(cells[0]).lower() not in _VERSION_LABELS:
        return ""
    for cell in cells[1:]:
        if match := _BARE_VERSION_RE.match(_demarkup(cell)):
            return match.group(1)
    return ""


def _is_test_module(rel: str) -> bool:
    parts = rel.split("/")
    base = parts[-1]
    return (
        any(part in ("tests", "test") for part in parts[:-1])
        or base.startswith("test_")
        or base.endswith("_test.py")
        or base == "conftest.py"
    )


def _code_versions(repo: RepoIndex) -> Iterator[tuple[Claim, str]]:
    """Every `__version__ = "..."` in non-test Python, found with ast.

    ast rather than a regex because a regex cannot tell an assignment from the
    same characters inside a string literal or a comment - and a test fixture
    that *contains* the text of a manifest is exactly the shape this checker
    would otherwise trip over. Test modules are skipped for the same reason:
    a version there is a fixture, not the package's own statement.
    """
    for source in repo.python:
        if _is_test_module(source.rel):
            continue
        try:
            tree = ast.parse(source.text)
        except SyntaxError:
            continue  # unparseable source is another checker's finding, not this one's
        found: list[tuple[int, str]] = []
        for node in ast.walk(tree):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            else:
                continue
            if not any(isinstance(t, ast.Name) and t.id == "__version__" for t in targets):
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                found.append((node.lineno, value.value))
        for lineno, value in sorted(found):
            text = source.line_text(lineno).strip()
            yield Claim(text, source.rel, lineno, kind="code"), value


def _doc_versions(repo: RepoIndex) -> Iterator[tuple[Claim, str]]:
    """Every documented `Version: x.y.z` field, outside release histories."""
    for source in repo.markdown:
        if _HISTORY_FILE_RE.search(source.rel):
            continue
        seen: set[int] = set()
        for claim in source.prose_claims():
            if claim.line in seen:
                continue
            raw = source.line_text(claim.line)
            if _is_indented_code(raw):
                continue
            if claim.kind == "table_cell":
                stated, text = _row_version(raw), raw.strip()
            else:
                match = _VERSION_FIELD_RE.match(_demarkup(claim.text))
                stated, text = (match.group(1) if match else ""), claim.text
            stated = stated.rstrip(".,;:)]}\"'`")
            if not stated:
                continue
            seen.add(claim.line)
            yield Claim(text, source.rel, claim.line, kind=claim.kind), stated


def _version_findings(repo: RepoIndex, manifest: _Manifest) -> Iterator[Finding]:
    declared = manifest.project.get("version")
    if not isinstance(declared, str) or not declared.strip():
        return  # dynamic or absent: there is no anchor, so there is no disagreement
    anchor = _version_key(declared)
    if anchor is None:
        return
    line, text = manifest.cite("project", "version")
    for claim, stated in [*_code_versions(repo), *_doc_versions(repo)]:
        key = _version_key(stated)
        if key is None or key == anchor:
            continue
        yield Finding(
            checker=_NAME,
            code="VERSION_DRIFT",
            verdict=Verdict.CONTRADICTED,
            severity=Severity.ERROR,
            claim=claim,
            evidence=[
                Evidence.at(
                    claim.path,
                    claim.line,
                    claim.text,
                    summary=f"{claim.path}:{claim.line} states version {stated}",
                ),
                _manifest_evidence(
                    manifest, line, text, f"{MANIFEST}:{line} declares version {declared}"
                ),
            ],
            detail=(
                f"{claim.path}:{claim.line} says {stated!r} while "
                f"{MANIFEST}:{line} says {declared!r}"
            ),
            remedy="publish one version and have the other read it, rather than restating it",
        )


# ------------------------------------------------------------------- package name


def _normalise_name(text: str) -> str:
    return re.sub(r"[-_.]+", "-", text.strip().lower())


def _packages(repo: RepoIndex, config: CheckConfig) -> tuple[str, list[str]]:
    """The importable package directories under the first source root that has any."""
    for root in config.source_roots:
        base = repo.root if root in ("", ".") else repo.root / root
        if not base.is_dir():
            continue
        found = [
            child.name
            for child in sorted(base.iterdir())
            if child.is_dir()
            and child.name not in SKIP_DIRS
            and not child.name.startswith(".")
            and (child / "__init__.py").is_file()
        ]
        if found:
            return root, found
    return "", []


def _name_findings(repo: RepoIndex, manifest: _Manifest, config: CheckConfig) -> Iterator[Finding]:
    declared = manifest.project.get("name")
    if not isinstance(declared, str) or not declared.strip():
        return
    root, packages = _packages(repo, config)
    if not packages:
        return  # a single module, a namespace package, or no source root here
    wanted = _normalise_name(declared)
    if any(_normalise_name(package) == wanted for package in packages):
        return
    candidates = [p for p in packages if p not in _NON_PACKAGE_DIRS]
    if len(candidates) != 1:
        # Two packages and no match means the distribution may legitimately ship
        # neither name; picking one to accuse would be a guess with a locator.
        return
    package = candidates[0]
    rel = package if root in ("", ".") else posixpath.join(root, package)
    line, text = manifest.cite("project", "name")
    yield Finding(
        checker=_NAME,
        code="NAME_DRIFT",
        verdict=Verdict.CONTRADICTED,
        severity=Severity.WARN,
        claim=Claim(text, MANIFEST, line, kind="config"),
        evidence=[
            _manifest_evidence(manifest, line, text, f"{MANIFEST}:{line} names the project"),
            Evidence.measured(
                f"the only importable package under {root or '.'}/ is {package!r}",
                value=rel,
                path=rel,
            ),
        ],
        detail=f"{MANIFEST}:{line} declares {declared!r} but the package on disk is {rel!r}",
        remedy=f"rename one of them, or add a [tool.setuptools] mapping from {declared!r}",
    )


# ----------------------------------------------------------------- python version


def _bounds(spec: str) -> tuple[tuple[int, int] | None, tuple[int, int] | None, bool]:
    """(floor, ceiling, ceiling_is_inclusive) for a requires-python specifier."""
    floor: tuple[int, int] | None = None
    ceiling: tuple[int, int] | None = None
    inclusive = False
    for op, major, minor in _SPECIFIER_RE.findall(spec):
        maj, mnr = int(major), int(minor) if minor else 0
        if op in (">=", "==", "~="):
            candidate = (maj, mnr)
        elif op == ">":
            # Python minors are integers, so `>3.10` and `>=3.11` select the
            # same set of interpreters; normalising here keeps one comparison.
            candidate = (maj, mnr + 1) if minor else (maj + 1, 0)
        elif op in ("<", "<="):
            bound = (maj, mnr)
            if ceiling is None or bound < ceiling:
                ceiling, inclusive = bound, op == "<="
            continue
        else:
            continue
        if floor is None or candidate > floor:
            floor = candidate
    return floor, ceiling, inclusive


def _excluded(version: tuple[int, int], floor: tuple[int, int],
              ceiling: tuple[int, int] | None, inclusive: bool) -> bool:
    if version < floor:
        return True
    if ceiling is None:
        return False
    return version > ceiling if inclusive else version >= ceiling


def _python_findings(manifest: _Manifest) -> Iterator[Finding]:
    spec = manifest.project.get("requires-python")
    if not isinstance(spec, str) or not spec.strip():
        return
    raw_classifiers = manifest.project.get("classifiers")
    classifiers: list[tuple[tuple[int, int], str]] = []
    if isinstance(raw_classifiers, list):
        for entry in raw_classifiers:
            if isinstance(entry, str) and (match := _CLASSIFIER_RE.match(entry)):
                classifiers.append(((int(match.group(1)), int(match.group(2))), entry))
    target = manifest.tool("tool", "ruff", "target-version")
    target_match = _TARGET_VERSION_RE.match(target) if isinstance(target, str) else None
    if not classifiers and target_match is None:
        return  # only one statement of the fact; nothing to disagree with

    spec_line, spec_text = manifest.cite("project", "requires-python")
    floor, ceiling, inclusive = _bounds(spec)
    if floor is None:
        yield Finding(
            checker=_NAME,
            code="PYTHON_VERSION_DRIFT",
            verdict=Verdict.UNVERIFIABLE,
            severity=Severity.INFO,
            claim=Claim(spec_text, MANIFEST, spec_line, kind="config"),
            detail=(
                f"requires-python {spec!r} states no lower bound this checker can read, so "
                "the classifiers and target-version cannot be compared against it"
            ),
        )
        return

    for version, entry in sorted(classifiers):
        if not _excluded(version, floor, ceiling, inclusive):
            continue
        line, text = manifest.cite_literal(entry)
        shown = f"{version[0]}.{version[1]}"
        yield Finding(
            checker=_NAME,
            code="PYTHON_VERSION_DRIFT",
            verdict=Verdict.CONTRADICTED,
            severity=Severity.WARN,
            claim=Claim(text, MANIFEST, line, kind="config"),
            evidence=[
                _manifest_evidence(
                    manifest, line, text, f"{MANIFEST}:{line} advertises Python {shown}"
                ),
                _manifest_evidence(
                    manifest,
                    spec_line,
                    spec_text,
                    f"{MANIFEST}:{spec_line} requires Python {spec}",
                ),
            ],
            detail=(
                f"the classifier advertises Python {shown}, which requires-python "
                f"{spec!r} excludes"
            ),
            remedy=f"drop the {shown} classifier, or widen requires-python to admit it",
        )

    if target_match is None:
        return
    stated = (int(target_match.group(1)), int(target_match.group(2)))
    if stated == floor:
        return
    line, text = manifest.cite("tool.ruff", "target-version")
    yield Finding(
        checker=_NAME,
        code="PYTHON_VERSION_DRIFT",
        verdict=Verdict.CONTRADICTED,
        severity=Severity.WARN,
        claim=Claim(text, MANIFEST, line, kind="config"),
        evidence=[
            _manifest_evidence(manifest, line, text, f"{MANIFEST}:{line} lints as {target}"),
            _manifest_evidence(
                manifest, spec_line, spec_text, f"{MANIFEST}:{spec_line} requires Python {spec}"
            ),
        ],
        detail=(
            f"[tool.ruff] target-version is {target!r} (Python {stated[0]}.{stated[1]}) but "
            f"requires-python {spec!r} floors at {floor[0]}.{floor[1]}"
        ),
        remedy="set target-version from requires-python, or drop it and let ruff infer it",
    )


# ---------------------------------------------------------------------- license


def _identify_text(text: str) -> str:
    """The license a full license text is, by first match, or ""."""
    flat = " ".join(text[:20000].split()).lower()
    for spdx, pattern in _LICENSE_TEXTS:
        if re.search(pattern, flat, re.IGNORECASE | re.DOTALL):
            return spdx
    return ""


def _identify_mentions(text: str) -> set[str]:
    """Every license a short phrase could be naming.

    A set rather than a first match, because the ambiguity is the useful part:
    "MIT or Apache-2.0" names two licenses and therefore states no single fact,
    and a caller that gets two ids back is expected to stay quiet.
    """
    flat = " ".join(text.split()).lower()
    out = {spdx for spdx, pattern in _LICENSE_TEXTS if re.search(pattern, flat, re.IGNORECASE)}
    out |= {spdx for spdx, pattern in _LICENSE_TOKENS if re.search(pattern, flat, re.IGNORECASE)}
    return out


def _sole_mention(text: str) -> str:
    found = _identify_mentions(text)
    return next(iter(found)) if len(found) == 1 else ""


def _declared_license(manifest: _Manifest) -> tuple[str, str, int, str]:
    """(spdx, declared_text, line, referenced_file) from the manifest's license fields."""
    project = manifest.project
    value = project.get("license")
    referenced = ""
    declared = ""
    if isinstance(value, str):
        declared = value
    elif isinstance(value, dict):
        if isinstance(value.get("text"), str):
            declared = str(value["text"])
        if isinstance(value.get("file"), str):
            referenced = str(value["file"])
    files = project.get("license-files")
    if not declared and not referenced and isinstance(files, list) and files:
        referenced = str(files[0]) if isinstance(files[0], str) else ""
    if not declared and not referenced:
        return "", "", 0, ""
    key = "license" if value is not None else "license-files"
    line, text = manifest.cite("project", key)
    return _sole_mention(declared), declared, line, referenced


def _license_files(repo: RepoIndex) -> list[str]:
    out = [
        rel
        for rel in sorted(repo.all_paths)
        if _LICENSE_FILE_RE.match(rel.rsplit("/", 1)[-1]) and (repo.root / rel).is_file()
    ]
    out.sort(key=lambda rel: (rel.count("/"), rel))
    return out


def _read(repo: RepoIndex, rel: str) -> str:
    try:
        return (repo.root / rel).read_text("utf-8", errors="replace")
    except OSError:
        return ""


def _readme(repo: RepoIndex) -> SourceFile | None:
    for candidate in README_FILES:
        if (source := repo.get(candidate)) is not None:
            return source
    return None


def _readme_license(source: SourceFile) -> tuple[str, int, str]:
    """(spdx, line, text) for the one license the README names, or ("", 0, "").

    Two different licenses named anywhere in the README - a dual license, or a
    note about a vendored file - means the README has not stated one fact, and
    this returns nothing rather than picking the first.
    """
    fenced: set[int] = set()
    for fence in source.fences():
        span = len(fence.body.split("\n")) if fence.body else 0
        fenced.update(range(fence.start_line - 1, fence.start_line + span + 1))

    section_until = -1
    hits: dict[str, tuple[int, str]] = {}
    for lineno, raw in enumerate(source.lines, start=1):
        if lineno in fenced:
            continue
        line = raw.strip()
        if _LICENSE_HEADING_RE.match(line):
            section_until = lineno + _LICENSE_SECTION_LINES
            continue
        if not line:
            continue
        if _HEADING_RE.match(line) and lineno <= section_until:
            section_until = -1  # the section ended; anything after is another subject
        scope = ""
        if match := _LICENSED_UNDER_RE.search(line):
            scope = match.group(1)
        elif lineno <= section_until or re.search(r"\blicen[sc]e\b", line, re.IGNORECASE):
            scope = line
        if not scope:
            continue
        for spdx in sorted(_identify_mentions(scope)):
            hits.setdefault(spdx, (lineno, line))
    if len(hits) != 1:
        return "", 0, ""
    spdx, (lineno, text) = next(iter(sorted(hits.items())))
    return spdx, lineno, text


def _license_findings(repo: RepoIndex, manifest: _Manifest) -> Iterator[Finding]:
    spdx, declared, line, referenced = _declared_license(manifest)
    files = _license_files(repo)
    if referenced and referenced in files:
        files = [referenced]

    if (declared or referenced) and not files:
        searched = [referenced] if referenced else ["LICENSE", "LICENCE", "COPYING", "LICENSE.*"]
        named = declared or referenced
        yield Finding(
            checker=_NAME,
            code="LICENSE_FILE_MISSING",
            verdict=Verdict.UNSUPPORTED,
            severity=Severity.WARN,
            claim=Claim(manifest.source.line_text(line).strip(), MANIFEST, line, kind="config"),
            evidence=[
                _manifest_evidence(
                    manifest,
                    line,
                    manifest.source.line_text(line),
                    f"{MANIFEST}:{line} declares the license as {named!r}",
                ),
                Evidence.absent(
                    f"no license file anywhere in the tree; looked for {', '.join(searched)}",
                    searched=[*searched, str(repo.root)],
                ),
            ],
            detail=f"{MANIFEST} declares {named!r} but the tree carries no license text",
            remedy=f"add a LICENSE file containing the {named} text",
        )

    statements: list[tuple[str, str, int, str, str]] = []
    # A repository with two license files (LICENSE-MIT, LICENSE-APACHE) is dual
    # licensed: its files do not restate one fact, so comparing them to a single
    # declaration would manufacture a contradiction out of a deliberate choice.
    if len(files) == 1:
        text = _read(repo, files[0])
        if found := _identify_text(text):
            cite_line, cite_text = 1, ""
            for lineno, raw in enumerate(text.split("\n"), start=1):
                if raw.strip():
                    cite_line, cite_text = lineno, raw.strip()
                    break
            statements.append((found, files[0], cite_line, cite_text, "the license file"))

    if (source := _readme(repo)) is not None and source.is_markdown:
        found, readme_line, readme_text = _readme_license(source)
        if found:
            statements.append((found, source.rel, readme_line, readme_text, "the README"))

    if spdx:
        anchor, anchor_path, anchor_line, anchor_text = spdx, MANIFEST, line, declared
    elif statements:
        anchor, anchor_path, anchor_line, anchor_text, _ = statements.pop(0)
    else:
        return

    for found, path, found_line, found_text, where in statements:
        if found == anchor:
            continue
        yield Finding(
            checker=_NAME,
            code="LICENSE_DRIFT",
            verdict=Verdict.CONTRADICTED,
            severity=Severity.WARN,
            claim=Claim(found_text, path, found_line, kind="prose"),
            evidence=[
                Evidence.at(
                    path,
                    found_line,
                    found_text,
                    summary=f"{path}:{found_line} reads as {found}",
                ),
                Evidence.at(
                    anchor_path,
                    anchor_line,
                    anchor_text or manifest.source.line_text(anchor_line),
                    summary=f"{anchor_path}:{anchor_line} reads as {anchor}",
                ),
            ],
            detail=(
                f"{where} is {found} but {anchor_path}:{anchor_line} says {anchor}"
            ),
            remedy="state one license and have the other places quote it",
        )


# ------------------------------------------------------------------ readme title


def _title_findings(repo: RepoIndex, manifest: _Manifest) -> Iterator[Finding]:
    """The README H1 against the project name.

    This is the whole of the heading-versus-description comparison that can be
    made without guessing. A heading that is a sentence and a description that
    is a different sentence are not in conflict - they are two descriptions -
    and there is no test for "contradictory prose" that does not eventually
    report a rewording as a defect. A heading that is a bare *name*, though, is
    an identity claim, and two identity claims can genuinely disagree.
    """
    declared = manifest.project.get("name")
    source = _readme(repo)
    if not isinstance(declared, str) or not declared.strip() or source is None:
        return
    if not source.is_markdown:
        return
    heading = next(
        (
            claim
            for claim in source.prose_claims()
            if claim.kind == "heading" and source.line_text(claim.line).lstrip().startswith("# ")
        ),
        None,
    )
    if heading is None:
        return
    token = _demarkup(heading.text)
    if not _NAME_TOKEN_RE.match(token) or token.lower() in _GENERIC_HEADINGS:
        return
    titled, named = _normalise_name(token), _normalise_name(declared)
    # `python-dateutil` documented as `# dateutil` is a shortened display name,
    # not a different project. Containment either way is treated as agreement.
    if titled == named or titled in named or named in titled:
        return
    line, text = manifest.cite("project", "name")
    yield Finding(
        checker=_NAME,
        code="TITLE_DRIFT",
        verdict=Verdict.CONTRADICTED,
        severity=Severity.WARN,
        claim=heading,
        evidence=[
            Evidence.at(
                source.rel,
                heading.line,
                source.line_text(heading.line),
                summary=f"{source.rel}:{heading.line} titles the project {token!r}",
            ),
            _manifest_evidence(manifest, line, text, f"{MANIFEST}:{line} names it {declared!r}"),
        ],
        detail=f"the README is titled {token!r} but {MANIFEST} declares the name {declared!r}",
        remedy="use one name in both, or make the heading say which is the distribution name",
    )


# ----------------------------------------------------------------------- checker


@dataclass
class ConsistencyChecker:
    name: str = _NAME
    description: str = "Facts this repository states twice agree with each other."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        source = repo.get(MANIFEST)
        if source is None:
            return  # no manifest, no second statement of anything: rule 5, be quiet
        try:
            data = tomllib.loads(source.text)
        except (tomllib.TOMLDecodeError, ValueError) as e:
            line, text = 1, ""
            for lineno, raw in enumerate(source.lines, start=1):
                if raw.strip():
                    line, text = lineno, raw.strip()
                    break
            yield Finding(
                checker=self.name,
                code="PYPROJECT_UNREADABLE",
                verdict=Verdict.UNVERIFIABLE,
                severity=Severity.INFO,
                claim=Claim(text, MANIFEST, line, kind="config"),
                detail=(
                    f"{MANIFEST} did not parse ({type(e).__name__}: {e}), so none of the facts "
                    "it anchors could be compared"
                ),
            )
            return
        manifest = _Manifest(source, data)
        if not manifest.project:
            return  # a [tool]-only pyproject declares none of the facts checked here
        yield from _version_findings(repo, manifest)
        yield from _name_findings(repo, manifest, config)
        yield from _python_findings(manifest)
        yield from _license_findings(repo, manifest)
        yield from _title_findings(repo, manifest)


register(ConsistencyChecker())
