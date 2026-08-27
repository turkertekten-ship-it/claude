"""Do the code symbols this repository advertises actually exist in the code?

A repository points at its own code constantly, and every pointer is a promise.
A console script in `pyproject.toml` promises that installing the package puts a
working command on the reader's PATH. A `python -m` line promises the module is
there to be run. A dotted name in a README or a docstring promises the reader
can go and look at it. All three rot the same way - a rename moves the code and
leaves the sentence behind - and no test suite notices, because nothing executes
a sentence.

Nothing here imports what it resolves. Importing is how a review tool acquires
side effects it never asked for: module-level code runs, which in this codebase
means an HTTP client can be constructed and the checker can end up waiting on a
socket, and a module that raises at import time would be reported as missing
when it is merely broken. `ast.parse` reads the same file and answers the same
question - is there a module-level name spelled like this - without running a
line of it.

The whole risk in this check is over-reading. `a.b` is also the shape of a
hostname, a filename, a version number and two sentences that ran into each
other, and a checker that reads all of them as module references produces a page
of nonsense on any repository with prose in it - after which somebody switches
it off and it catches nothing at all. So a dotted name in prose is only looked
at when its first segment is a package that actually exists under a source root,
and a name that turns out to be an attribute chain into a class -
`pkg.mod.Class.field` - is left alone, because deciding that needs type
information this checker does not have and will not guess at.
"""

from __future__ import annotations

import ast
import keyword
import posixpath
import re
import tomllib
from dataclasses import dataclass, field
from typing import Iterator, Sequence

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

PYPROJECT = "pyproject.toml"

#: `[project.<table>]` tables whose values are `"pkg.mod:func"` entry points.
#: `scripts` is singled out below: it is the one an install turns into a file on
#: the reader's PATH, so confirming it is worth saying out loud.
ENTRY_POINT_TABLES: tuple[str, ...] = ("scripts", "gui-scripts")

#: `python -m pkg.mod`, wherever it is written - a fence, a shell script, a YAML
#: provenance record. A runnable module gets named in all of them.
_DASH_M_RE = re.compile(
    r"\bpython(?:[0-9]+(?:\.[0-9]+)*)?\s+-m\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)"
)

#: A backtick span that is *entirely* a dotted name. Requiring the whole span
#: keeps `$(PY) -m oodarag.cli` and `see pkg.mod for details` out: a span with
#: prose in it is a phrase being quoted, not a name being cited.
_BACKTICK_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)`")

#: Prose that asserts the thing it names is *not* there. Absence evidence agrees
#: with such a sentence, so reporting one would be this checker inventing a
#: conflict - CONTRACT.md rule 4. This is not hypothetical: this repository
#: records `python3 -m oodarag.cli` in `provenance/sources.yaml` as a
#: measurement of the ModuleNotFoundError it produced, and names it in a README
#: roadmap row marked "not started". Both are true sentences about a module that
#: does not exist, and flagging either would be reporting the point of the
#: sentence back at its author.
_ABSENCE_RE = re.compile(
    r"\bnot\s+started\b"
    r"|\bnot\s+(?:yet\s+)?(?:been\s+)?(?:built|written|created|implemented|added|shipped)\b"
    r"|\b(?:does|do|did|will|would|could|should)\s+not\s+(?:yet\s+)?exist"
    r"|\bnever\s+exist(?:s|ed)?\b"
    r"|\bno\s+such\b"
    r"|\bModuleNotFoundError\b|\bImportError\b|\bAttributeError\b"
    r"|\bno\s+module\s+named\b"
    r"|\bthere\s+(?:is|are|was|were)\s+(?:deliberately\s+)?no\b"
    r"|\b(?:was|were|been)\s+(?:removed|deleted)\b"
    r"|\bno\s+longer\s+(?:exists?|there)\b",
    re.IGNORECASE,
)
#: Cues that mean absence next to a name and nothing at all six lines away.
#: "a missing API key" and "planned work" are ordinary English, and this
#: repository's README has the first of them four lines from a live module
#: reference: windowed, they would silence a real finding. On the line that
#: names the module they are unambiguous, so that is the only place they count.
_WEAK_ABSENCE_RE = re.compile(
    r"\bmissing\b|\bplanned\b|\broadmap\b|\bnot\s+yet\b|\bnot\s+there\b|\buncreated\b",
    re.IGNORECASE,
)
#: Wide enough to reach the clause that says "did not exist", which is routinely
#: not on the line holding the name: in `provenance/sources.yaml` the observed
#: ModuleNotFoundError sits four lines below the command it describes.
_ABSENCE_WINDOW = 6

#: Statements that bind names at module level without being one. A name bound in
#: an `if` or a `try` is still `module.name` at runtime; one bound inside a `def`
#: is not, which is why function and class bodies are not descended into.
_BLOCK_NODES: tuple[type, ...] = (
    ast.If, ast.Try, ast.TryStar, ast.With, ast.AsyncWith, ast.For, ast.AsyncFor, ast.While,
)


# ------------------------------------------------------------------ references


@dataclass(frozen=True, slots=True)
class _Ref:
    """One place the repository names a module, and how it named it.

    `mode` decides how much the reference is allowed to prove. An entry point is
    machine-consumed and unambiguous; a dotted name in prose is neither, and is
    read far more cautiously.
    """

    dotted: str
    symbol: str          # the part after ':' in an entry point, else ""
    claim: Claim
    origin: str          # human-readable, used in `detail`
    mode: str            # "entry" | "module" | "dotted"
    announce: bool = False

    @property
    def sort_key(self) -> tuple[str, int, str, str, str]:
        return (self.claim.path, self.claim.line, self.dotted, self.symbol, self.mode)


def _is_dotted(name: str) -> bool:
    parts = name.split(".")
    return bool(name) and all(p.isidentifier() and not keyword.iskeyword(p) for p in parts)


def _first_line(source: SourceFile) -> tuple[int, str]:
    """The first line with something on it - a quotable anchor for a whole file."""
    for lineno, raw in enumerate(source.lines, start=1):
        if raw.strip():
            return lineno, raw.strip()
    return 1, ""


def _locate(source: SourceFile, needles: Sequence[str]) -> int:
    """The line a TOML entry was written on.

    `tomllib` parses values, not positions, and CONTRACT.md rule 1 requires the
    claim to be a verbatim slice of a real line. So the line is recovered by
    looking for the text, needle by needle in order of how specific it is.
    """
    for needle in needles:
        if not needle:
            continue
        for lineno, raw in enumerate(source.lines, start=1):
            if needle in raw:
                return lineno
    return 0


def _pyproject(repo: RepoIndex) -> tuple[dict, str]:
    source = repo.get(PYPROJECT)
    if source is None:
        return {}, ""
    try:
        data = tomllib.loads(source.text)
    except (tomllib.TOMLDecodeError, ValueError) as e:
        return {}, f"{type(e).__name__}: {e}"
    return (data if isinstance(data, dict) else {}), ""


def _search_roots(configured: Sequence[str], data: dict) -> tuple[str, ...]:
    """The configured roots, plus the ones the build backend is told to look in.

    A `package-dir` or a `packages.find.where` this checker does not know about
    turns every entry point in the file into a false MODULE_MISSING: an install
    finds the package where the backend was told to look, and the checker is
    looking somewhere else. Reading them costs nothing and removes a whole class
    of wrong answer.
    """
    roots: list[str] = []
    extra: list[str] = []
    tool = data.get("tool")
    setuptools = tool.get("setuptools") if isinstance(tool, dict) else None
    if isinstance(setuptools, dict):
        package_dir = setuptools.get("package-dir")
        if isinstance(package_dir, dict):
            extra.extend(v for v in package_dir.values() if isinstance(v, str))
        packages = setuptools.get("packages")
        find = packages.get("find") if isinstance(packages, dict) else None
        where = find.get("where") if isinstance(find, dict) else None
        if isinstance(where, list):
            extra.extend(w for w in where if isinstance(w, str))
    for candidate in [*configured, *extra]:
        normalised = posixpath.normpath(candidate) if candidate else "."
        # An absolute or escaping root names the host's filesystem, not this
        # tree, and nothing repo-relative can honestly resolve against it.
        if normalised.startswith(("/", "..")) or normalised in roots:
            continue
        roots.append(normalised)
    return tuple(roots)


def _entry_point_refs(repo: RepoIndex, data: dict) -> list[_Ref]:
    project = data.get("project")
    source = repo.get(PYPROJECT)
    if not isinstance(project, dict) or source is None:
        return []
    refs: list[_Ref] = []
    for table in ENTRY_POINT_TABLES:
        entries = project.get(table)
        if not isinstance(entries, dict):
            continue
        header = _locate(source, [f"[project.{table}]", f"{table} ="])
        for name in sorted(entries):
            value = entries[name]
            if not isinstance(value, str):
                continue
            module, _, attribute = value.partition(":")
            module = module.strip()
            symbol = attribute.split("[")[0].strip()
            # A value this checker cannot read is not a finding. `pkg.mod:` with
            # nothing after it, or a name with a hyphen in it, is a packaging
            # error somebody else's tooling reports far better than this one.
            if not _is_dotted(module) or (attribute and not _is_dotted(symbol)):
                continue
            line = _locate(source, [f"{name} = ", value]) or header
            if line == 0:
                continue  # unquotable, and rule 1 forbids reporting what cannot be quoted
            refs.append(_Ref(
                dotted=module,
                symbol=symbol,
                claim=Claim(source.line_text(line).strip(), PYPROJECT, line,
                            kind="entry_point", context=name),
                origin=f"[project.{table}] entry point {name!r}",
                mode="entry",
                announce=(table == "scripts"),
            ))
    return refs


def _dash_m_refs(repo: RepoIndex) -> list[_Ref]:
    refs: list[_Ref] = []
    for source in repo.files:
        for lineno, raw in enumerate(source.lines, start=1):
            for module in _DASH_M_RE.findall(raw):
                if not _is_dotted(module):
                    continue
                refs.append(_Ref(
                    dotted=module,
                    symbol="",
                    claim=Claim(raw.strip(), source.rel, lineno, kind="command"),
                    origin="`python -m`",
                    mode="module",
                ))
    return refs


def _doc_refs(repo: RepoIndex) -> list[_Ref]:
    """Backtick-quoted dotted names in markdown prose and in docstrings.

    Comments are deliberately not included. A docstring describes the module a
    reader is looking at and is read as documentation; a `#` comment is as often
    a note to the next maintainer, and widening the input here buys coverage
    only where the false-positive risk is highest.
    """
    claims = [*repo.prose_claims(), *(c for c in repo.comment_claims() if c.kind == "docstring")]
    refs: list[_Ref] = []
    for claim in claims:
        for dotted in _BACKTICK_RE.findall(claim.text):
            if not _is_dotted(dotted):
                continue
            refs.append(_Ref(
                dotted=dotted,
                symbol="",
                claim=claim,
                origin="documentation",
                mode="dotted",
            ))
    return refs


def _references(repo: RepoIndex, data: dict) -> list[_Ref]:
    """Every reference, deduplicated and in a fixed order.

    One line routinely carries the same name twice - a README fence holding
    `python -m pkg.mod` next to prose citing `pkg.mod` - and a reader who is
    told about it twice trusts the report less, not more.
    """
    seen: set[tuple[str, int, str, str]] = set()
    out: list[_Ref] = []
    for ref in sorted(
        [*_entry_point_refs(repo, data), *_dash_m_refs(repo), *_doc_refs(repo)],
        key=lambda r: r.sort_key,
    ):
        key = (ref.claim.path, ref.claim.line, ref.dotted, ref.symbol)
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return out


def _asserts_absence(source: SourceFile | None, line: int) -> bool:
    if source is None:
        return False
    rows = source.lines
    if _WEAK_ABSENCE_RE.search(source.line_text(line)):
        return True
    lo = max(0, line - 1 - _ABSENCE_WINDOW)
    window = " ".join(rows[lo : line + _ABSENCE_WINDOW])
    return _ABSENCE_RE.search(" ".join(window.split())) is not None


# ------------------------------------------------------------------ resolution


@dataclass
class _Resolver:
    """Dotted names to files, by looking, never by importing."""

    repo: RepoIndex
    roots: tuple[str, ...]
    packages: frozenset[str] = frozenset()
    _symbols: dict[str, dict[str, int] | None] = field(default_factory=dict, repr=False)

    @classmethod
    def of(cls, repo: RepoIndex, roots: tuple[str, ...]) -> _Resolver:
        return cls(repo=repo, roots=roots, packages=_top_level_packages(repo, roots))

    def candidates(self, dotted: str) -> list[str]:
        stem = dotted.replace(".", "/")
        out: list[str] = []
        for root in self.roots:
            for tail in (f"{stem}.py", f"{stem}/__init__.py"):
                rel = posixpath.normpath(posixpath.join(root, tail))
                if rel not in out:
                    out.append(rel)
        return out

    def file_for(self, dotted: str) -> str:
        for rel in self.candidates(dotted):
            if self.repo.exists(rel):
                return rel
        return ""

    def resolves(self, dotted: str) -> bool:
        if self.file_for(dotted):
            return True
        # A directory with no `__init__.py` is still importable - a namespace
        # package - so its bare existence is not evidence that anything is
        # missing, and this checker does not report what it cannot decide.
        stem = dotted.replace(".", "/")
        return any(
            self.repo.exists(posixpath.normpath(posixpath.join(root, stem)))
            for root in self.roots
        )

    def symbols(self, rel: str) -> dict[str, int] | None:
        if rel not in self._symbols:
            self._symbols[rel] = _module_level_names(self.repo, rel)
        return self._symbols[rel]


def _top_level_packages(repo: RepoIndex, roots: tuple[str, ...]) -> frozenset[str]:
    """Directories directly under a source root that contain Python files.

    `__init__.py` alone is too strict a test - namespace packages and test
    directories are real - and "any directory" is far too loose: it would admit
    `docs.adr` and, worse, let a hostname like `www.example.com` through the
    only gate standing between this checker and every dotted token in the prose.
    """
    out: set[str] = set()
    for rel in sorted(repo.all_paths):
        if not rel.endswith(".py"):
            continue
        parts = rel.split("/")
        for root in roots:
            prefix = [] if root == "." else root.split("/")
            if parts[: len(prefix)] != prefix:
                continue
            rest = parts[len(prefix) :]
            if len(rest) == 2 and rest[0].isidentifier() and not keyword.iskeyword(rest[0]):
                out.add(rest[0])
    return frozenset(out)


def _module_level_names(repo: RepoIndex, rel: str) -> dict[str, int] | None:
    """Module-level names to the line that binds them, or None if unreadable."""
    source = repo.get(rel)
    if source is not None:
        text = source.text
    else:
        try:
            text = (repo.root / rel).read_text("utf-8")
        except (OSError, UnicodeDecodeError):
            return None
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    names: dict[str, int] = {}
    _collect(tree.body, names)
    return names


def _collect(body: Sequence[ast.stmt], names: dict[str, int]) -> None:
    """Names bound at module level, imports included.

    An entry point that points at a name a module re-exports works perfectly
    when the installed script runs it, so refusing to see imported names would
    manufacture a failure out of a working promise. Nested `def` and `class`
    bodies are not descended into for the opposite reason: a name bound inside a
    function is not reachable as `module.name`, and counting it would hide the
    exact drift this checker exists to catch.
    """
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.setdefault(node.name, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                _bind(target, names)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            _bind(node.target, names)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if bound != "*":
                    names.setdefault(bound, node.lineno)
        elif isinstance(node, _BLOCK_NODES):
            _collect(node.body, names)
            _collect(getattr(node, "orelse", []), names)
            _collect(getattr(node, "finalbody", []), names)
            for handler in getattr(node, "handlers", []):
                _collect(handler.body, names)


def _bind(target: ast.expr, names: dict[str, int]) -> None:
    if isinstance(target, ast.Name):
        names.setdefault(target.id, target.lineno)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            _bind(element, names)


# --------------------------------------------------------------------- checker


@dataclass
class SymbolsChecker:
    name: str = "symbols"
    description: str = "Every module and entry point this repository names resolves to code in the tree."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        data, parse_error = _pyproject(repo)
        if parse_error:
            source = repo.get(PYPROJECT)
            line, text = _first_line(source) if source else (1, "")
            yield Finding(
                checker=self.name, code="PYPROJECT_UNPARSEABLE",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO,
                claim=Claim(text, PYPROJECT, line, kind="config"),
                detail=(f"{PYPROJECT} is not readable as TOML ({parse_error}), so the entry "
                        "points it declares were not resolved."),
            )
        roots = _search_roots(config.source_roots, data)
        if not roots:
            return  # with nowhere to look, "not found" would be a guess
        resolver = _Resolver.of(repo, roots)

        for ref in _references(repo, data):
            yield from self._inspect(ref, repo, resolver)

    # ----------------------------------------------------------------- verdicts

    def _inspect(self, ref: _Ref, repo: RepoIndex, resolver: _Resolver) -> list[Finding]:
        source = repo.get(ref.claim.path)
        here = Evidence.at(
            ref.claim.path, ref.claim.line, ref.claim.text,
            summary=f"{ref.claim.path}:{ref.claim.line} names "
                    + (f"{ref.dotted}:{ref.symbol}" if ref.symbol else ref.dotted),
        )
        if ref.mode == "entry":
            return self._entry_point(ref, repo, resolver, here)

        # Prose is allowed to talk about code that is not there, and routinely
        # does; an entry point is not, which is why the gate and the guard below
        # apply only here.
        if ref.dotted.split(".")[0] not in resolver.packages:
            return []
        if _asserts_absence(source, ref.claim.line):
            return []
        if ref.mode == "module":
            if resolver.resolves(ref.dotted):
                return []
            return [self._missing_module(ref, resolver, here)]
        return self._dotted(ref, repo, resolver, here)

    def _entry_point(self, ref: _Ref, repo: RepoIndex, resolver: _Resolver,
                     here: Evidence) -> list[Finding]:
        if not resolver.resolves(ref.dotted):
            return [self._missing_module(ref, resolver, here)]
        rel = resolver.file_for(ref.dotted)
        if not rel:
            return []  # a namespace package: there is no module file to read a name out of
        if not ref.symbol:
            return self._announce(ref, repo, rel, here, "")
        names = resolver.symbols(rel)
        if names is None:
            return [Finding(
                checker=self.name, code="MODULE_UNPARSEABLE",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=ref.claim,
                detail=(f"{rel} could not be parsed, so whether it defines {ref.symbol!r} "
                        "was not established."),
            )]
        # Only the head of `mod:Class.method` is decidable without types; the
        # rest is an attribute lookup on an object this checker never builds.
        head = ref.symbol.split(".")[0]
        if head not in names:
            return [Finding(
                checker=self.name, code="SYMBOL_MISSING",
                verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=ref.claim,
                evidence=[here, Evidence.absent(
                    f"{rel} binds {len(names)} module-level names and {head!r} is not among "
                    f"them: {', '.join(sorted(names)) or '(none)'}",
                    (rel,))],
                detail=(f"{ref.origin} points at {ref.dotted}:{ref.symbol}, and {rel} defines "
                        f"no module-level {head!r}."),
                remedy=f"define {head} in {rel}, or correct the entry point.",
            )]
        return self._announce(ref, repo, rel, here, head, names[head])

    def _dotted(self, ref: _Ref, repo: RepoIndex, resolver: _Resolver,
                here: Evidence) -> list[Finding]:
        segments = ref.dotted.split(".")
        best = 0
        for count in range(len(segments), 0, -1):
            if resolver.resolves(".".join(segments[:count])):
                best = count
                break
        if best == len(segments):
            return []  # it names a module in the tree: rule 5, say nothing
        if best == 0:
            return []  # the gate saw a package here and the filesystem does not; do not guess
        rel = resolver.file_for(".".join(segments[:best]))
        if not rel:
            return []
        names = resolver.symbols(rel)
        if names is None:
            return [Finding(
                checker=self.name, code="MODULE_UNPARSEABLE",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=ref.claim,
                detail=(f"{rel} could not be parsed, so whether {ref.dotted} resolves through "
                        "it was not established."),
            )]
        wanted = segments[best]
        if wanted in names:
            # `pkg.mod.Class.field`: the class is real and the rest is an
            # attribute chain, which needs types to follow. Silence beats a guess.
            return []
        deeper = resolver.candidates(".".join(segments[: best + 1]))
        # Inside a package a dotted child reads as a submodule; inside a plain
        # module it reads as a name defined in it. Same evidence either way -
        # the code just says which reading was available.
        code = "MODULE_MISSING" if rel.endswith("/__init__.py") else "SYMBOL_MISSING"
        return [Finding(
            checker=self.name, code=code,
            verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=ref.claim,
            evidence=[here, Evidence.absent(
                f"nothing provides {wanted!r} for {ref.dotted}: no module file under source "
                f"roots {', '.join(resolver.roots)}, and no module-level name in {rel}",
                tuple([*deeper, rel]))],
            detail=(f"{ref.origin} cites {ref.dotted}, but {wanted!r} is neither a module nor "
                    f"a module-level name in {rel}."),
            remedy=f"create {deeper[0]}, define {wanted} in {rel}, or correct the reference.",
        )]

    def _missing_module(self, ref: _Ref, resolver: _Resolver, here: Evidence) -> Finding:
        candidates = resolver.candidates(ref.dotted)
        return Finding(
            checker=self.name, code="MODULE_MISSING",
            verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=ref.claim,
            evidence=[here, Evidence.absent(
                f"no file provides module {ref.dotted!r} under source roots "
                f"{', '.join(resolver.roots)}",
                tuple(candidates))],
            detail=f"{ref.origin} names {ref.dotted}, and no module file backs it.",
            remedy=f"create {candidates[0]}, or correct the reference.",
        )

    def _announce(self, ref: _Ref, repo: RepoIndex, rel: str, here: Evidence,
                  symbol: str, line: int = 0) -> list[Finding]:
        """A resolved `[project.scripts]` entry, and only that, is worth stating.

        Rule 5 keeps confirmations rare, and this is the case it exempts: the
        promise is made to whoever runs an install, it is invisible in the source
        tree, and nothing else in a normal build checks it. Everything else that
        resolves here resolves silently.
        """
        if not ref.announce:
            return []
        source = repo.get(rel)
        if source is None:
            return []
        anchor, text = (line, source.line_text(line).strip()) if line else _first_line(source)
        target = f"{ref.dotted}:{symbol}" if symbol else ref.dotted
        return [Finding(
            checker=self.name, code="ENTRY_POINT_RESOLVES",
            verdict=Verdict.SUPPORTED, severity=Severity.INFO, claim=ref.claim,
            evidence=[here, Evidence.at(rel, anchor, text,
                                        summary=f"{target} resolves to {rel}:{anchor}")],
            detail=f"{ref.origin} resolves: {target} is defined at {rel}:{anchor}.",
        )]


register(SymbolsChecker())
