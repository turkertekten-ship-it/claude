"""Rules that keep documentation honest about the code beside it.

Prose decays quietly. A sentence that stopped being true looks exactly like one
that is still true, so nothing in a normal working day surfaces the moment a
README started lying about the repository under it. The three rules here
therefore restrict themselves, on purpose, to the parts of that decay a machine
can *prove* from the tree: a link whose target is not on disk, an entry point
the README never names, a document older than everything it claims to describe.
None of them reads the prose for meaning. A rule that judged whether a paragraph
was still accurate would be guessing, and a guess is not something a loop that
edits files at 3am is allowed to act on.

The three sit at very different distances from an edit, and their risk tiers say
so:

* a link to a missing `.md` is the one case here where the loop may write
  without asking - creating a file nobody has written destroys nothing, the stub
  says in its own first line that it is a stub, and the alternative is a link
  that stays broken for another week;
* an undocumented `make` target is a `review` edit, because the fix lands in the
  README and the README is the user's prose. The loop may hand over a paragraph;
  it may not insert one;
* staleness proposes nothing at all. It is measured from timestamps, and a
  timestamp cannot distinguish a document that is now wrong from one that was
  simply right the first time. Rewriting somebody's words on that evidence is
  exactly the autonomy this subsystem must not take.

One containment rule runs under all of it: every reference is resolved
workspace-relative, and anything that leaves the root - `../../etc/hosts` in a
link, an absolute path, a URL, a shell glob - is dropped before it can become a
finding, let alone an `EditOp`.
"""

from __future__ import annotations

import posixpath
import re
import time
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from oodarag.reflect.detect.base import DetectContext, Detector, register
from oodarag.reflect.models import (
    KIND_COMMIT,
    KIND_FILE,
    EditOp,
    Evidence,
    Finding,
    Proposal,
    Signal,
)
from oodarag.util.logging import get_logger

log = get_logger("reflect.docs")

#: Extensions scanned as documentation when the source did not label the file.
#: Deliberately narrower than the walker's own doc list: these are the three
#: whose reference syntax this module actually understands.
DOC_SCAN_EXTS = frozenset({".md", ".rst", ".txt"})

#: The only shapes of missing file the loop will offer to create. Fabricating a
#: `.py` because a README mentioned one would be inventing source code out of a
#: typo, and a plausible-looking empty module is worse than an obvious gap.
STUB_EXTS = frozenset({".md", ".rst", ".txt"})

#: What makes a bare token inside a code span path-shaped enough to check.
#: Anything else needs a "/" in it before this module will claim it is a path.
PATH_EXTS = frozenset(
    {".cfg", ".ini", ".json", ".md", ".py", ".rst", ".sh", ".toml", ".txt", ".yaml", ".yml"}
)

#: Used only when a `KIND_FILE` signal carries no `is_code` metadata - some
#: sources are thinner than the workspace walker. Kept short: the staleness rule
#: needs "is this a source file", not a language census.
CODE_EXTS = frozenset(
    {
        ".c", ".cc", ".cfg", ".cpp", ".css", ".go", ".h", ".html", ".ini", ".java", ".js",
        ".json", ".jsx", ".kt", ".lua", ".php", ".pl", ".py", ".rb", ".rs", ".sh", ".sql",
        ".swift", ".tf", ".toml", ".ts", ".tsx", ".yaml", ".yml",
    }
)

#: Docs that speak for a whole directory rather than for their own folder.
README_NAMES = frozenset({"readme.md", "readme.rst", "readme.txt", "index.md", "index.rst"})

DEFAULT_README = "README.md"
DEFAULT_MAKEFILE = "Makefile"
DEFAULT_PYPROJECT = "pyproject.toml"

#: A heading the loop owns, so adding to the README is an append under our own
#: subtitle rather than an edit of a paragraph somebody wrote.
ENTRYPOINTS_HEADING = "## Commands"

#: Make targets that are plumbing rather than entry points a newcomer needs.
DEFAULT_IGNORED_TARGETS = ("help", "all", "default")

DAY_S = 86_400.0

_MD_LINK_RE = re.compile(r"!?\[[^\]\n]{0,200}\]\(([^)\n]{1,300})\)")
_CODE_SPAN_RE = re.compile(r"`([^`\n]{1,200})`")

#: `NAME:` at the start of a line, minus `NAME :=` and friends. Assignments and
#: targets are spelled almost identically in make, and reporting `PYTHONPATH` as
#: an undocumented command would discredit the whole finding.
_MAKE_TARGET_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):(?!=)")
_MAKE_HELP_RE = re.compile(r"##\s*(.+?)\s*$")

#: Anything with a scheme is somebody else's resource, not a path in this tree.
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")

#: Characters that say "this is not a path in this repository": shell globs,
#: template placeholders, angle-bracket stand-ins, make variables, quoting.
_UNPATHY = frozenset("<>*?[]{}$|\"'`\\ \t")


# -- configuration helpers ---------------------------------------------------
# Local rather than shared with the other rule modules on purpose: a detector
# that imports a sibling detector is a detector that cannot be switched off
# without switching off its neighbour.


def _cfg_int(config: dict[str, Any], key: str, default: int) -> int:
    """Read an int setting, falling back on anything unusable.

    Rule config is JSON a human edited, so a quoted number, a null or a typo are
    all normal conditions. A nightly run must not die because a threshold was
    written as a string.
    """
    try:
        return int(config[key])
    except (KeyError, TypeError, ValueError):
        return default


def _cfg_float(config: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(config[key])
    except (KeyError, TypeError, ValueError):
        return default


def _cfg_str(config: dict[str, Any], key: str, default: str) -> str:
    value = config.get(key, default)
    return value.strip() if isinstance(value, str) and value.strip() else default


def _cfg_bool(config: dict[str, Any], key: str, default: bool) -> bool:
    value = config.get(key, default)
    return bool(value) if isinstance(value, (bool, int, float)) else default


def _cfg_terms(config: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = config.get(key)
    if isinstance(value, (list, tuple)) and value:
        terms = tuple(str(v).strip().lower() for v in value if str(v).strip())
        if terms:
            return terms
    return default


# -- path shapes -------------------------------------------------------------


def _ext(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    # A leading dot is a name, not an extension: ".gitignore" has none.
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name[1:] else ""


def _is_relpath(value: str) -> bool:
    """Whether a string is a path that stays inside the workspace."""
    if not value or value.startswith(("/", "~")) or "\x00" in value:
        return False
    parts = posixpath.normpath(value).split("/")
    return ".." not in parts and parts[0] != ""


def _is_doc_signal(sig: Signal) -> bool:
    """Trust the source's own label first, fall back to the extension."""
    meta = sig.metadata or {}
    if meta.get("is_doc"):
        return True
    return _ext(sig.uri) in DOC_SCAN_EXTS


def _is_code_signal(sig: Signal) -> bool:
    meta = sig.metadata or {}
    if meta.get("is_code"):
        return True
    return _ext(sig.uri) in CODE_EXTS


def _is_readme(rel: str) -> bool:
    return posixpath.basename(rel).lower() in README_NAMES


def _workspace_files(ctx: DetectContext) -> dict[str, Signal]:
    """Root-relative path -> the file signal for it, for the paths we trust."""
    return {s.uri: s for s in ctx.by_kind(KIND_FILE) if s.uri and _is_relpath(s.uri)}


def _file_text(ctx: DetectContext, rel: str, files: dict[str, Signal]) -> str | None:
    """Content of a workspace file, preferring what was actually observed.

    The signal is the state the rest of the cycle reasoned about; disk is the
    fallback for a file the walker skipped (ignored, oversized, unchanged) but
    that a rule still needs to read.
    """
    sig = files.get(rel)
    if sig is not None:
        return sig.text
    return ctx.read_text(rel)


def _evidence_for(files: dict[str, Signal], rel: str, quote: str) -> Evidence:
    sig = files.get(rel)
    if sig is not None:
        return Evidence.from_signal(sig, quote=quote)
    return Evidence(quote=quote, uri=rel)


def _stamp(ts: float) -> str:
    try:
        return time.strftime("%Y-%m-%d", time.localtime(ts))
    except (OSError, OverflowError, ValueError):
        return "an unreadable date"


def _line_at(lines: list[str], index: int, limit: int = 160) -> str:
    if not 0 <= index < len(lines):
        return ""
    flat = " ".join(lines[index].split())
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


# -- reference extraction ----------------------------------------------------


@dataclass(slots=True)
class _Reference:
    """One thing a document points at, as written."""

    target: str
    kind: str  # link | code
    line: int  # 1-based, for the human reading the report
    quote: str


def _mask_code_fences(text: str) -> str:
    """Blank out fenced blocks while keeping the line numbering intact.

    A path inside a fenced example is an illustration - half of them are
    deliberately fictional - and checking them against the filesystem produces
    confident nonsense. An unterminated fence masks everything after it, which
    errs towards reporting less.
    """
    out: list[str] = []
    fenced = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else line)
    return "\n".join(out)


def _clean_target(raw: str) -> str:
    """A candidate workspace path, or "" for anything that is not one."""
    cand = raw.strip().strip("`")
    cand = cand.split("#", 1)[0]  # an anchor points inside a file, not at one
    cand = cand.rstrip(".,;:!?)\"'")
    if not cand:
        return ""
    if _UNPATHY & set(cand):  # glob, placeholder, make variable, quoted string
        return ""
    if cand.startswith(("/", "~")) or _SCHEME_RE.match(cand):  # absolute, http:, mailto:
        return ""
    # Path-shaped or nothing: a bare word like "installation" is far more often
    # a heading reference than a file, and guessing costs the report its
    # credibility for no gain.
    if "/" not in cand and _ext(cand) not in PATH_EXTS:
        return ""
    return cand


def _references(text: str, scan_code_spans: bool) -> list[_Reference]:
    """Every path-shaped thing a document points at, in document order."""
    masked = _mask_code_fences(text)
    lines = text.split("\n")
    out: list[_Reference] = []

    for match in _MD_LINK_RE.finditer(masked):
        parts = match.group(1).split()  # drops a ("path "title"") title
        target = _clean_target(parts[0]) if parts else ""
        if target:
            index = masked.count("\n", 0, match.start())
            out.append(_Reference(target, "link", index + 1, _line_at(lines, index)))

    if scan_code_spans:
        for match in _CODE_SPAN_RE.finditer(masked):
            body = match.group(1).strip()
            # A span containing whitespace is a command or a sentence; the paths
            # inside one are arguments, and pulling them out finds mostly noise.
            if not body or any(ch.isspace() for ch in body):
                continue
            target = _clean_target(body)
            if target:
                index = masked.count("\n", 0, match.start())
                out.append(_Reference(target, "code", index + 1, _line_at(lines, index)))

    return out


def _resolutions(doc: str, target: str, kind: str = "link") -> list[str]:
    """Where a reference could point: beside the doc, and from the repository root.

    Both are checked, because both conventions are in live use in the same file.
    Which one comes *first* matters more than it looks: the head of this list is
    the path a proposal will create, so the wrong order makes the loop create a
    file at a path nobody referenced.

    A markdown link is doc-relative by definition, so it keeps that order. A path
    quoted in a code span *with a directory in it* is almost always written from
    the repository root - `internal/PLAN.md` quoted inside `docs/adr/` means the
    one at the root, not `docs/adr/internal/PLAN.md`, which is a path no reader
    would ever look for and no author intended. A bare filename in a code span
    stays doc-relative, since that is how a sibling file is cited.
    """
    root_first = kind == "code" and "/" in target
    bases = ("", posixpath.dirname(doc)) if root_first else (posixpath.dirname(doc), "")
    out: list[str] = []
    for base in bases:
        joined = posixpath.normpath(posixpath.join(base, target)) if base else \
            posixpath.normpath(target)
        if joined in (".", "..") or joined.startswith("../") or joined.startswith("/"):
            continue
        if joined not in out:
            out.append(joined)
    return out


def _title_from(path: str) -> str:
    stem = posixpath.basename(path).rsplit(".", 1)[0]
    parts = [p for p in re.split(r"[-_\s]+", stem) if p]
    if not parts:
        return "Untitled"
    text = " ".join(parts)
    return text[0].upper() + text[1:]


def _stub_body(missing: str, doc: str) -> str:
    """A placeholder that admits what it is in its first sentence.

    The honesty is the whole point of being allowed to write this file
    unattended: a stub that reads like content is a lie the loop told, while a
    stub that says "nobody has written this yet" is strictly better than a link
    that goes nowhere.
    """
    title = _title_from(missing)
    ext = _ext(missing)
    q = "`" if ext == ".md" else '"'
    lead = (
        f"Stub. {q}{doc}{q} links to this file and it did not exist, so the nightly "
        f"reflect loop created it rather than leave the link broken. Nothing below "
        f"has been written yet: replace this paragraph with the real content, or "
        f"delete the link in {q}{doc}{q}."
    )
    if ext == ".rst":
        return f"{title}\n{'=' * max(3, len(title))}\n\n{lead}\n"
    if ext == ".txt":
        return f"{title}\n\n{lead}\n"
    return f"# {title}\n\n{lead}\n"


# -- rules -------------------------------------------------------------------


@register
class DocsBrokenReference(Detector):
    """A document pointing at a file that is not there.

    This is the only documentation defect that can be checked without reading
    the prose, which is why it is the one rule here with a `high` severity and
    an automatic fix: the claim "this link is broken" is either true or false on
    disk tonight, with no interpretation in between.

    The two syntaxes it understands are deliberately different in confidence. A
    markdown link is an explicit promise that something is over there; a path
    quoted in a code span may be an example, a planned file, or a path in
    somebody else's repository, so it is reported more quietly.
    """

    rule_id = "docs.broken_ref"
    title = "Documentation links to a file that does not exist"
    severity = "high"
    consumes = (KIND_FILE,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.max_per_doc = _cfg_int(self.config, "max_per_doc", 10)
        self.scan_code_spans = _cfg_bool(self.config, "scan_code_spans", True)
        self.link_confidence = _cfg_float(self.config, "link_confidence", 0.8)
        self.code_confidence = _cfg_float(self.config, "code_confidence", 0.55)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        for sig in ctx.by_kind(KIND_FILE):
            if not sig.uri or not _is_relpath(sig.uri) or not _is_doc_signal(sig):
                continue
            yield from self._scan(sig, ctx)

    def _scan(self, sig: Signal, ctx: DetectContext) -> Iterable[Finding]:
        doc = sig.uri
        seen_raw: set[str] = set()
        # The second deduplication is on the *resolved* path rather than on what
        # was written: "setup.md" in a link and "docs/setup.md" in a code span
        # are one missing file, and two findings for it would share a
        # fingerprint - which the journal reads as one finding, reported twice,
        # half of it silently unaccounted for.
        seen_target: set[str] = set()
        emitted = 0
        for ref in _references(sig.text, self.scan_code_spans):
            if ref.target in seen_raw:
                continue
            seen_raw.add(ref.target)
            candidates = _resolutions(doc, ref.target, ref.kind)
            if not candidates:
                # Resolves outside the workspace. Not ours to check, and never
                # ours to create.
                log.debug("reference escapes the workspace", doc=doc, target=ref.target)
                continue
            if any(ctx.exists(rel) for rel in candidates):
                continue
            if candidates[0] in seen_target:
                continue
            seen_target.add(candidates[0])
            yield self._finding(sig, ref, candidates[0], ctx)
            emitted += 1
            if emitted >= self.max_per_doc:
                log.debug("broken-reference cap hit", doc=doc, cap=self.max_per_doc)
                return

    def _finding(
        self, sig: Signal, ref: _Reference, missing: str, ctx: DetectContext
    ) -> Finding:
        doc = sig.uri
        parent = posixpath.dirname(missing)
        parent_exists = ctx.exists(parent) if parent else True
        base = self.link_confidence if ref.kind == "link" else self.code_confidence
        # A missing file in a directory that does exist is a file that moved or
        # was never written; a missing file in a missing directory is more often
        # a path from some other project quoted in passing.
        confidence = base + (0.1 if parent_exists else -0.1)
        kind_word = "links to" if ref.kind == "link" else "refers to"
        return Finding(
            rule_id=self.rule_id,
            title=f"{doc} {kind_word} a missing file: {missing}",
            detail=(
                f"{doc} line {ref.line} {kind_word} \"{ref.target}\", which resolves to "
                f"{missing} and is not in the workspace. Either the file moved and the "
                f"reference did not follow, or it was promised and never written."
            ),
            severity=self.severity,
            confidence=round(max(0.05, min(0.95, confidence)), 3),
            key=f"{doc}->{missing}",
            targets=[doc, missing],
            evidence=[Evidence.from_signal(sig, quote=ref.quote or ref.target)],
            tags=["docs", "links", ref.kind],
            metadata={
                "doc": doc,
                "raw": ref.target,
                "target": missing,
                "ref_kind": ref.kind,
                "line": ref.line,
                "parent_exists": parent_exists,
            },
        )

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        """Create the missing file, but only when it is a document.

        Writing an empty `.md` that something already links to cannot destroy
        information, which is the entire definition of `safe`. The same argument
        does not extend one inch further: a missing `.py` is a claim about code
        that does not exist, and the honest output for that is a finding a human
        reads, not a file the loop invents.
        """
        missing = str(finding.metadata.get("target", ""))
        doc = str(finding.metadata.get("doc", ""))
        if not missing or not _is_relpath(missing):
            return ()
        if _ext(missing) not in STUB_EXTS:
            return ()
        if ctx.exists(missing):
            # Written by hand between the scan and now. Nothing to do, and
            # `create` would fail its precondition anyway.
            return ()
        return [
            Proposal(
                finding=finding,
                title=f"Create the missing {missing} as a stub",
                rationale=(
                    f"{doc} already points at {missing}. A stub that says it is a stub is "
                    f"better than a link that goes nowhere, and nothing can be lost by "
                    f"creating a file that does not exist."
                ),
                edits=[
                    EditOp(
                        path=missing,
                        op="create",
                        text=_stub_body(missing, doc),
                        note=f"{self.rule_id}: referenced by {doc}",
                    )
                ],
                risk="safe",
                impact=0.45,
                effort=0.1,
            )
        ]


@dataclass(slots=True)
class _Entry:
    """One way in to the project, and where it was declared."""

    name: str
    kind: str  # make | script
    help: str
    path: str
    line: int
    quote: str

    def invocation(self) -> str:
        return f"make {self.name}" if self.kind == "make" else self.name

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "help": self.help,
            "path": self.path,
            "line": self.line,
        }


def _make_targets(text: str, path: str, ignored: tuple[str, ...]) -> list[_Entry]:
    """Targets declared in a Makefile, with their `##` help where there is any."""
    lines = text.split("\n")
    out: list[_Entry] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        match = _MAKE_TARGET_RE.match(line)
        if not match:
            continue
        rest = line[match.end() :]
        if rest.startswith("="):  # `NAME::= value`, an assignment in disguise
            continue
        name = match.group(1)
        if name.lower() in ignored or name in seen:
            continue
        seen.add(name)
        help_match = _MAKE_HELP_RE.search(rest)
        out.append(
            _Entry(
                name=name,
                kind="make",
                help=help_match.group(1) if help_match else "",
                path=path,
                line=index + 1,
                quote=_line_at(lines, index),
            )
        )
    return out


def _console_scripts(text: str, path: str) -> list[_Entry]:
    """`[project.scripts]` and `console_scripts`, or nothing at all.

    Parsed with `tomllib` rather than by hand, and a file that does not parse
    yields no entries: a pyproject caught mid-edit is a normal thing to observe
    at night, and half-parsing one would invent entry points out of a syntax
    error.
    """
    try:
        data = tomllib.loads(text)
    except (AttributeError, TypeError, ValueError) as e:
        log.debug("pyproject is not parsable toml", path=path, err=str(e)[:160])
        return []
    project = data.get("project")
    if not isinstance(project, dict):
        return []
    tables: list[Any] = [project.get("scripts")]
    entry_points = project.get("entry-points")
    if isinstance(entry_points, dict):
        tables.append(entry_points.get("console_scripts"))

    lines = text.split("\n")
    out: list[_Entry] = []
    seen: set[str] = set()
    for table in tables:
        if not isinstance(table, dict):
            continue
        for name, target in table.items():
            name = str(name).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            index = _find_declaration(lines, name)
            out.append(
                _Entry(
                    name=name,
                    kind="script",
                    help=f"console script -> {target}" if target else "console script",
                    path=path,
                    line=index + 1,
                    quote=_line_at(lines, index),
                )
            )
    return out


def _find_declaration(lines: list[str], name: str) -> int:
    """Best-effort line number for `name = ...`, so the evidence is navigable."""
    pattern = re.compile(rf"^\s*[\"']?{re.escape(name)}[\"']?\s*=")
    for index, line in enumerate(lines):
        if pattern.match(line):
            return index
    return -1


def _mentions(text: str, name: str) -> bool:
    """Whether a README names an entry point anywhere, in any phrasing.

    Whole-word rather than "make <name>" on purpose: a README that documents a
    target in a table, a code fence or a sentence has documented it, and a rule
    that insisted on one phrasing would keep proposing to re-document things the
    user already wrote about.
    """
    pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])", re.IGNORECASE)
    return pattern.search(text) is not None


@register
class DocsUndocumentedEntrypoint(Detector):
    """Ways in to the project that the README never mentions.

    The failure this addresses is specific: the commands are all there, in the
    Makefile and in `[project.scripts]`, and the only person who knows they
    exist is the person who wrote them. Every newcomer - and every assistant
    reading the repository cold - starts at the README, so a target that is not
    named there does not exist as far as they are concerned.

    All of them are reported as one finding rather than one each. Six findings
    that say "and also this target" is a report nobody reads to the end of, and
    the fix is a single section either way.
    """

    rule_id = "docs.undocumented_entrypoint"
    title = "Entry points missing from the README"
    severity = "medium"
    consumes = (KIND_FILE,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.readme = _cfg_str(self.config, "readme", DEFAULT_README)
        self.makefile = _cfg_str(self.config, "makefile", DEFAULT_MAKEFILE)
        self.pyproject = _cfg_str(self.config, "pyproject", DEFAULT_PYPROJECT)
        self.section = _cfg_str(self.config, "section", ENTRYPOINTS_HEADING)
        self.min_missing = _cfg_int(self.config, "min_missing", 1)
        self.max_listed = _cfg_int(self.config, "max_listed", 12)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 4)
        self.ignored_targets = _cfg_terms(self.config, "ignore_targets", DEFAULT_IGNORED_TARGETS)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        if not _is_relpath(self.readme):
            log.warn("readme is not a workspace-relative path", path=self.readme)
            return
        files = _workspace_files(ctx)
        entries: list[_Entry] = []
        make_text = _file_text(ctx, self.makefile, files) if _is_relpath(self.makefile) else None
        if make_text:
            entries.extend(_make_targets(make_text, self.makefile, self.ignored_targets))
        py_text = _file_text(ctx, self.pyproject, files) if _is_relpath(self.pyproject) else None
        if py_text:
            entries.extend(_console_scripts(py_text, self.pyproject))
        if not entries:
            return

        readme_text = _file_text(ctx, self.readme, files)
        missing = [e for e in entries if not _mentions(readme_text or "", e.name)]
        if len(missing) < self.min_missing:
            return
        yield self._finding(missing, entries, readme_text is not None, files)

    def _finding(
        self,
        missing: list[_Entry],
        entries: list[_Entry],
        readme_exists: bool,
        files: dict[str, Signal],
    ) -> Finding:
        names = [e.invocation() for e in missing]
        listed = ", ".join(names[: self.max_listed])
        where = self.readme if readme_exists else f"{self.readme} (which does not exist)"
        evidence = [
            Evidence(
                quote=f"{where} names none of: {listed}",
                uri=self.readme,
            )
        ]
        for entry in missing[: self.max_evidence]:
            evidence.append(_evidence_for(files, entry.path, entry.quote or entry.name))
        # More undocumented entry points is not more certain that each one
        # matters, so confidence rises slowly and stops well short of certain.
        confidence = 0.5 + 0.05 * len(missing) + (0.0 if readme_exists else 0.1)
        return Finding(
            rule_id=self.rule_id,
            title=f"{len(missing)} entry point(s) not documented in {self.readme}",
            detail=(
                f"This project declares {len(entries)} entry point(s); {where} mentions "
                f"{len(entries) - len(missing)} of them. Undocumented: {listed}. Someone "
                f"cloning this repository has no way to discover them without reading "
                f"the build files."
            ),
            severity=self.severity,
            confidence=round(min(0.85, confidence), 3),
            key="readme-entrypoints",
            targets=[self.readme],
            evidence=evidence,
            tags=["docs", "readme", "entrypoints"],
            metadata={
                "missing": [e.as_dict() for e in missing],
                "declared": len(entries),
                "readme_exists": readme_exists,
                "readme": self.readme,
            },
        )

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        """Offer the section; never insert into the user's own paragraphs.

        `ensure_section` is the strongest thing that stays honest here: it adds
        under a heading this loop owns, so review is a matter of reading one
        block rather than diffing prose. Only the case where the README does not
        exist at all is `safe`, and only because there is nothing there to lose.
        """
        raw = finding.metadata.get("missing")
        entries = [e for e in raw if isinstance(e, dict)][: self.max_listed] if raw else []
        body = "".join(_entry_line(e) for e in entries)
        if not body:
            return ()
        readme = str(finding.metadata.get("readme") or self.readme)
        if not _is_relpath(readme):
            return ()
        existing = ctx.read_text(readme)
        note = f"{self.rule_id}: {len(entries)} entry point(s)"
        if existing is None:
            edit = EditOp(
                path=readme,
                op="create",
                text=f"# {ctx.root.name or 'Project'}\n\n{self.section}\n\n{body}",
                note=note,
            )
            risk = "safe"
        else:
            edit = EditOp(path=readme, op="ensure_section", anchor=self.section, text=body,
                          note=note)
            risk = "review"
        return [
            Proposal(
                finding=finding,
                title=f"List the undocumented entry points in {readme}",
                rationale=(
                    "These commands already exist; the README is the only place someone "
                    "looks for them. The section is appended under a heading the loop "
                    "owns, so no existing prose is touched."
                ),
                edits=[edit],
                risk=risk,
                impact=0.5,
                effort=0.2,
            )
        ]


def _entry_line(entry: dict[str, Any]) -> str:
    name = str(entry.get("name") or "").strip()
    if not name:
        return ""
    invocation = f"make {name}" if entry.get("kind") == "make" else name
    help_text = " ".join(str(entry.get("help") or "").split())
    return f"- `{invocation}` - {help_text}\n" if help_text else f"- `{invocation}`\n"


@register
class DocsStaleAgainstCode(Detector):
    """A document older than everything it plausibly describes.

    Deliberately observation-only, and that is the interesting part of the rule.
    A timestamp gap is evidence that a document *may* have fallen behind; it is
    not evidence of a single wrong sentence, and there is no edit that follows
    from it. Rewriting somebody's prose because a file next to it was touched
    last week would be the loop inventing content it cannot check, in the user's
    voice, unattended - the exact failure this subsystem exists to avoid. So
    this rule reports the gap, names the newest file, and stops. The human
    decides whether the words are still true; only they can.

    Pairing is by directory proximity because that is the weakest assumption
    that still means something: a doc sitting next to code is about that code,
    and a README at the top of a package speaks for the package under it.
    """

    rule_id = "docs.stale"
    title = "Documentation older than the code it describes"
    severity = "low"
    consumes = (KIND_FILE,)
    max_findings = 10

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.stale_days = _cfg_float(self.config, "stale_days", 30.0)
        self.min_code_files = _cfg_int(self.config, "min_code_files", 1)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 3)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        docs: list[Signal] = []
        code: list[Signal] = []
        for sig in ctx.by_kind(KIND_FILE):
            if not sig.uri or not _is_relpath(sig.uri) or sig.ts <= 0:
                continue
            if _is_doc_signal(sig):
                docs.append(sig)
            elif _is_code_signal(sig):
                code.append(sig)
        if not docs or not code:
            return

        threshold = max(0.0, self.stale_days) * DAY_S
        for doc in docs:
            paired = [c for c in code if _pairs_with(doc.uri, c.uri)]
            if len(paired) < max(1, self.min_code_files):
                continue
            newest = max(paired, key=lambda s: s.ts)
            gap = newest.ts - doc.ts
            if gap <= threshold:
                continue
            yield self._finding(doc, newest, paired, gap, ctx)

    def _finding(
        self,
        doc: Signal,
        newest: Signal,
        paired: list[Signal],
        gap: float,
        ctx: DetectContext,
    ) -> Finding:
        gap_days = round(gap / DAY_S, 1)
        # Confidence rises with how far past the threshold the gap is, and stops
        # low: a timestamp is weak evidence about prose, however large the gap.
        ratio = gap / (max(self.stale_days, 1.0) * DAY_S)
        evidence = [
            Evidence.from_signal(doc, quote=f"{doc.uri} last modified {_stamp(doc.ts)}"),
            Evidence.from_signal(
                newest,
                quote=(
                    f"{newest.uri} last modified {_stamp(newest.ts)}, "
                    f"{gap_days} days after {doc.uri}"
                ),
            ),
        ]
        commit = _newest_commit_touching(ctx, newest.uri)
        if commit is not None and len(evidence) < self.max_evidence:
            evidence.append(Evidence.from_signal(commit))
        return Finding(
            rule_id=self.rule_id,
            title=f"{doc.uri} is {gap_days} days behind {newest.uri}",
            detail=(
                f"{doc.uri} has not changed since {_stamp(doc.ts)}, while {len(paired)} "
                f"file(s) it sits with have - most recently {newest.uri} on "
                f"{_stamp(newest.ts)}, {gap_days} days later. That is a reason to reread "
                f"it, not evidence that any particular sentence is wrong, so nothing is "
                f"proposed: whether the words still hold is a judgement only you can make."
            ),
            severity=self.severity,
            confidence=round(min(0.6, 0.25 + 0.1 * ratio), 3),
            key=doc.uri,
            targets=[doc.uri],
            evidence=evidence,
            tags=["docs", "staleness"],
            metadata={
                "doc": doc.uri,
                "doc_mtime": round(doc.ts, 3),
                "newest_code": newest.uri,
                "newest_code_mtime": round(newest.ts, 3),
                "gap_days": gap_days,
                "code_files": len(paired),
                "stale_days": self.stale_days,
            },
        )


def _pairs_with(doc: str, code: str) -> bool:
    """Whether a doc plausibly describes a code file.

    Two shapes only. Same directory: a design note beside the module it
    discusses. A README (or index) at a directory root: the file everybody reads
    to understand everything beneath it. Anything looser - matching by name,
    by import graph - would pair files that merely share a word.
    """
    doc_dir = posixpath.dirname(doc)
    code_dir = posixpath.dirname(code)
    if doc_dir == code_dir:
        return True
    if not _is_readme(doc):
        return False
    return code.startswith(doc_dir + "/") if doc_dir else True


def _newest_commit_touching(ctx: DetectContext, path: str) -> Signal | None:
    """The most recent commit that recorded a change to `path`, if we saw one.

    Commits are read only to make the finding legible - "changed here, on this
    day, for this reason" - never to decide it. Timestamps already answered
    that, and a repository with no history must produce the same finding.
    """
    best: Signal | None = None
    for sig in ctx.by_kind(KIND_COMMIT):
        files = (sig.metadata or {}).get("files")
        if isinstance(files, list) and path in files and (best is None or sig.ts > best.ts):
            best = sig
    return best
