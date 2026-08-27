"""Reading a repository as a set of quoted claims.

Every checker needs the same three things: the files, the assertions made in
them, and the line each assertion was made on. Doing that once, here, keeps the
checkers from disagreeing about what the repository even says - two checkers
with two different markdown parsers will eventually report two different line
numbers for the same sentence, and a reviewer who cannot reproduce a locator
stops trusting all of them.

Claims are always sliced out of the file verbatim. Nothing in this module
normalises, paraphrases or summarises the text it extracts: the `text` on a
`Claim` is a substring of the file at `path`, and that property is what lets a
reader re-derive any finding with `sed -n '<line>p'`.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from tools.evidence import Claim

# Directories that are never repository content.
SKIP_DIRS = frozenset(
    ".git __pycache__ .mypy_cache .pytest_cache .ruff_cache node_modules "
    ".venv venv build dist htmlcov .data .oodarag .eggs".split()
)
TEXT_SUFFIXES = frozenset(
    ".md .markdown .rst .txt .py .toml .cfg .ini .yaml .yml .json .sh .bash "
    ".mk .cmake .js .ts .html .css .sql".split()
)
NAMED_TEXT_FILES = frozenset({"Makefile", "makefile", "GNUmakefile", "Dockerfile", "CLAUDE.md"})

_SENTENCE_RE = re.compile(r"(?<=[.!?:])\s+(?=[A-Z`*\[(])|\n")
#: A fence opener or closer. CommonMark allows `~~~` as well as ```` ``` ````,
#: and recommends it when the content itself contains backticks. Recognising
#: only backticks does not merely miss those blocks - it feeds their contents to
#: every prose-reading checker as if they were assertions, so a tilde-fenced
#: example path becomes a PATH_MISSING error.
_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})([A-Za-z0-9_+-]*)\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$")
_TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


@dataclass(slots=True)
class CodeFence:
    """A fenced block, with the line its first *content* line sits on."""

    lang: str
    body: str
    start_line: int
    path: str

    @property
    def commands(self) -> list[tuple[int, str]]:
        """Shell command lines inside the fence, as (line_number, command).

        Continuations (`\\` at end of line) are joined, prompts (`$ `) stripped,
        and comment/blank lines dropped, so a checker sees the command a reader
        would actually type.
        """
        if self.lang not in ("", "sh", "bash", "shell", "console", "zsh", "text"):
            return []
        out: list[tuple[int, str]] = []
        pending: list[str] = []
        pending_line = 0
        for offset, raw in enumerate(self.body.split("\n")):
            line = raw.strip()
            if not pending and (not line or line.startswith("#")):
                continue
            if line.startswith("$ "):
                line = line[2:].strip()
            if not pending:
                pending_line = self.start_line + offset
            if line.endswith("\\"):
                pending.append(line[:-1].strip())
                continue
            pending.append(line)
            joined = " ".join(p for p in pending if p).strip()
            if joined:
                out.append((pending_line, joined))
            pending = []
        if pending:
            joined = " ".join(p for p in pending if p).strip()
            if joined:
                out.append((pending_line, joined))
        return out


@dataclass(slots=True)
class SourceFile:
    """One text file, read once, with line offsets precomputed."""

    path: Path
    rel: str
    text: str

    @property
    def lines(self) -> list[str]:
        return self.text.split("\n")

    def line_at(self, offset: int) -> int:
        """1-based line number containing a character offset."""
        return self.text.count("\n", 0, max(0, offset)) + 1

    def line_text(self, line: int) -> str:
        rows = self.lines
        return rows[line - 1] if 1 <= line <= len(rows) else ""

    @property
    def is_markdown(self) -> bool:
        return self.path.suffix.lower() in (".md", ".markdown")

    @property
    def is_python(self) -> bool:
        return self.path.suffix.lower() == ".py"

    # ------------------------------------------------------------- extraction

    def fences(self) -> list[CodeFence]:
        out: list[CodeFence] = []
        open_at: int | None = None
        marker = ""
        lang = ""
        buf: list[str] = []
        for idx, line in enumerate(self.lines, start=1):
            m = _FENCE_RE.match(line)
            if m and open_at is None:
                open_at, marker, lang, buf = idx, m.group(2), m.group(3).lower(), []
            elif m and open_at is not None and m.group(2)[0] == marker[0] \
                    and len(m.group(2)) >= len(marker) and not m.group(3):
                # Same fence character, at least as long, no info string: only
                # such a line closes a block. A ```` ``` ```` inside a `~~~`
                # block is content, which is exactly why tilde fences exist.
                out.append(CodeFence(lang, "\n".join(buf), open_at + 1, self.rel))
                open_at, marker, lang, buf = None, "", "", []
            elif open_at is not None:
                buf.append(line)
        if open_at is not None:  # unterminated fence: keep what we have
            out.append(CodeFence(lang, "\n".join(buf), open_at + 1, self.rel))
        return out

    def prose_claims(self) -> list[Claim]:
        """Sentences, bullets, table cells and headings, outside code fences.

        Prose is where unbacked assertions live. Code fences are excluded here
        because a command in a fence is checked as a command, not as a sentence.
        """
        if not self.is_markdown:
            return []
        fenced: set[int] = set()
        for fence in self.fences():
            # Body line count, not newline count: an empty fence has zero body
            # lines, and treating it as one swallows the first claim after the
            # closing marker.
            span = len(fence.body.split("\n")) if fence.body else 0
            fenced.update(range(fence.start_line - 1, fence.start_line + span + 1))

        claims: list[Claim] = []
        for lineno, raw in enumerate(self.lines, start=1):
            if lineno in fenced:
                continue
            line = _HTML_COMMENT_RE.sub("", raw).strip()
            if not line or line.startswith(("```", "|---", "| ---", ":--")):
                continue
            if m := _HEADING_RE.match(line):
                claims.append(Claim(m.group(2).strip(), self.rel, lineno, kind="heading"))
                continue
            if m := _TABLE_ROW_RE.match(line):
                for cell in m.group(1).split("|"):
                    cell = cell.strip()
                    if cell and not set(cell) <= set("-: "):
                        claims.append(Claim(cell, self.rel, lineno, kind="table_cell"))
                continue
            if m := _BULLET_RE.match(line):
                claims.append(Claim(m.group(1).strip(), self.rel, lineno, kind="bullet"))
                continue
            for part in _SENTENCE_RE.split(line):
                part = part.strip()
                if len(part) > 1:
                    claims.append(Claim(part, self.rel, lineno, kind="prose"))
        return claims

    def comment_claims(self) -> list[Claim]:
        """Python comments and docstrings.

        A docstring that says the module does X is as much a claim on the
        repository as a README bullet, and is likelier to go stale because
        nobody re-reads it when the code beneath it changes.
        """
        if not self.is_python:
            return []
        claims: list[Claim] = []
        for lineno, raw in enumerate(self.lines, start=1):
            stripped = raw.strip()
            if stripped.startswith("#") and len(stripped) > 2:
                claims.append(Claim(stripped.lstrip("# ").strip(), self.rel, lineno, kind="comment"))
        try:
            tree = ast.parse(self.text)
        except SyntaxError:
            return claims
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            doc = ast.get_docstring(node, clean=False)
            if not doc:
                continue
            if not node.body:
                continue
            # The docstring's own start line, never a guess. `1` is wrong for
            # any module with a shebang, a coding cookie or a licence header
            # above the docstring - and a locator that points at the wrong line
            # makes the finding unreproducible, which is the one thing every
            # finding in this tool has to be.
            base = node.body[0].lineno
            for offset, row in enumerate(doc.split("\n")):
                row = row.strip()
                if len(row) > 1:
                    claims.append(Claim(row, self.rel, base + offset, kind="docstring"))
        return claims


@dataclass
class RepoIndex:
    """The repository, read once.

    Checkers receive this rather than a path, so a run reads each file a single
    time and every checker sees byte-identical content. Two checkers disagreeing
    about a file's contents mid-run is a class of bug that is very hard to see
    in a report and very easy to prevent here.
    """

    root: Path
    _cache: dict[str, SourceFile] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()

    def exists(self, rel: str) -> bool:
        candidate = (self.root / rel.lstrip("/")).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return False  # escapes the repo; treat as absent rather than probing the host
        return candidate.exists()

    @cached_property
    def files(self) -> list[SourceFile]:
        out: list[SourceFile] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            # Relative parts, never absolute: `self.root` is resolved, so
            # `path.parts` spans the whole host path. Matching SKIP_DIRS against
            # that means a repository checked out under `~/dev/build/repo` or a
            # CI workspace at `/var/lib/ci/build/job` filters out every one of
            # its own files, and the tool then reports zero findings and exits 0
            # on a tree it never read - a silent clean bill of health, which is
            # the single worst thing this tool can do.
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in NAMED_TEXT_FILES:
                continue
            try:
                text = path.read_text("utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = str(path.relative_to(self.root))
            source = SourceFile(path, rel, text)
            self._cache[rel] = source
            out.append(source)
        return out

    def get(self, rel: str) -> SourceFile | None:
        if not self.files:  # populates the cache
            return None
        return self._cache.get(rel)

    @cached_property
    def markdown(self) -> list[SourceFile]:
        return [f for f in self.files if f.is_markdown]

    @cached_property
    def python(self) -> list[SourceFile]:
        return [f for f in self.files if f.is_python]

    @cached_property
    def all_paths(self) -> set[str]:
        """Every path in the repo, relative and POSIX-style."""
        out: set[str] = set()
        for path in self.root.rglob("*"):
            rel = path.relative_to(self.root)
            if any(part in SKIP_DIRS for part in rel.parts):  # relative, see `files`
                continue
            out.add(rel.as_posix())
        return out

    def prose_claims(self) -> list[Claim]:
        return [c for f in self.markdown for c in f.prose_claims()]

    def comment_claims(self) -> list[Claim]:
        return [c for f in self.python for c in f.comment_claims()]

    def all_claims(self) -> list[Claim]:
        return self.prose_claims() + self.comment_claims()

    def fences(self) -> list[CodeFence]:
        return [fence for f in self.markdown for fence in f.fences()]
