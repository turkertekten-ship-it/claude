"""Filesystem connector: the source that works with the network unplugged.

Every other connector in this package needs something outside the process to be
reachable and healthy. That makes them a poor foundation for the two things
this pipeline is judged on - `make demo` and `make eval` - because a demo that
depends on a remote host fails for reasons that have nothing to do with
retrieval, and an eval whose corpus can change underneath it produces numbers
that cannot be compared between runs. A directory of markdown files is a fixed,
versioned corpus: the same bytes on every machine, in CI, and inside an
egress-filtered container.

Two decisions worth stating.

**The citation URI is the local file, not the declared source URL.** Files carry
front matter naming where their content came from, and it is tempting to stamp
that URL as the document's `uri` so citations look like the web. It would be a
lie of exactly the kind `generate.verify_citations` exists to prevent: the bytes
that were indexed are the ones on disk, and a reader following a citation must
land on what was actually read. The declared origin is kept in
`metadata["source_url"]` (and as `metadata["canonical"]`, so the normalizer
deduplicates a local mirror against the same page crawled from the web), where
it is provenance rather than a claim about what was retrieved.

**Errors are per-file and counted.** One unreadable or undecodable file in a
corpus directory must not abort the other hundred, so read failures are logged,
tallied into `stats["skipped"]`, and skipped. The base class's delta counts
whole-source failures; this counts the ones it cannot see.

Redaction runs here as it does in every connector. A seed corpus is unlikely to
contain a credential, but "unlikely" is the assumption that puts one in an
index, and this connector is also the obvious tool for pointing at a directory
of notes that was never curated at all.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("ingest.files")

#: Default extensions. Deliberately narrow: this connector does no format
#: conversion, so anything it cannot read as plain text belongs to a different
#: connector rather than to a lenient extension list here.
DEFAULT_EXTENSIONS: tuple[str, ...] = (".md", ".markdown", ".txt")

#: `<!-- source: https://... -->` on its own line. An HTML comment is used
#: instead of YAML front matter because it survives being rendered by any
#: markdown viewer, so the corpus files stay readable as documents.
_SOURCE_COMMENT_RE = re.compile(
    r"^\s*<!--\s*(?:source|source[_-]url|url)\s*:\s*(\S+?)\s*-->\s*$",
    re.IGNORECASE | re.MULTILINE,
)

#: YAML-style front matter is still parsed when present: other tools write it,
#: and refusing to read a file because of its header format is a bad trade.
_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)

_H1_RE = re.compile(r"^#\s+(.+?)\s*#*$", re.MULTILINE)

#: How far into a file the source header is looked for.
_HEADER_SCAN_CHARS = 512

#: Directories that are never corpus material. Matched by name at any depth.
_SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".oodarag", "dist", "build",
})


class FilesConnector(Connector):
    """Walk a directory of text files and yield one `RawDocument` per file.

    `authority` is 1.0 rather than the web connector's 0.8: a file someone
    deliberately placed in a corpus directory is a curated source, not something
    a crawler happened to reach.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        key: str | None = None,
        authority: float = 1.0,
        extensions: Sequence[str] = DEFAULT_EXTENSIONS,
        recursive: bool = True,
        max_file_bytes: int = 1_000_000,
        max_files: int = 5_000,
        follow_hidden: bool = False,
    ) -> None:
        self.root = Path(root).expanduser()
        # The key is built from the path as given, not from `resolve()`: the
        # cursor is looked up by it, and resolving would change the key (and so
        # silently force a full re-ingest) the first time the same corpus is
        # reached through a symlink or a different working directory.
        self.key = key or f"files:{self.root.as_posix()}"
        self.authority = authority
        self.extensions = tuple(e.lower() if e.startswith(".") else f".{e.lower()}"
                                for e in extensions)
        self.recursive = recursive
        self.max_file_bytes = max_file_bytes
        self.max_files = max_files
        self.follow_hidden = follow_hidden
        self.stats: dict[str, Any] = {}

    # ------------------------------------------------------------------- fetch

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        skipped: dict[str, int] = {}
        emitted = 0
        base = self.root.resolve()

        if not base.is_dir():
            # Not an exception: a missing corpus directory is a fact the ingest
            # report should carry, in the same shape as any other empty source.
            log.warn("corpus directory missing", root=str(self.root))
            self.stats = {"root": str(base), "files": 0, "skipped": {"no_such_directory": 1}}
            return

        for path in self._walk(base):
            if emitted >= self.max_files:
                skipped["max_files"] = skipped.get("max_files", 0) + 1
                continue
            try:
                size = path.stat().st_size
                if size > self.max_file_bytes:
                    skipped["too_large"] = skipped.get("too_large", 0) + 1
                    continue
                # `errors="replace"` rather than a decode failure: one byte of
                # mojibake in an otherwise good document is not a reason to lose
                # the document, and the replacement character is visible.
                text = path.read_text("utf-8", errors="replace")
            except OSError as e:
                skipped["unreadable"] = skipped.get("unreadable", 0) + 1
                log.warn("file unreadable", path=str(path), err=f"{type(e).__name__}: {e}"[:160])
                continue

            if not text.strip():
                skipped["empty"] = skipped.get("empty", 0) + 1
                continue

            emitted += 1
            yield self._document(path, base, text, size)

        self.stats = {"root": str(base), "files": emitted, "skipped": skipped}
        log.info("files connector run", key=self.key, files=emitted, **skipped)

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["root"] = self.stats.get("root", cursor.get("root", str(self.root)))
        cursor["last_stats"] = {k: v for k, v in self.stats.items() if k != "root"}
        cursor["last_walk_at"] = time.time()
        return cursor

    # --------------------------------------------------------------- internals

    def _walk(self, base: Path) -> Iterator[Path]:
        """Candidate files, in a stable order.

        Sorted, because ordering decides which of two identical documents the
        normalizer keeps and which it drops as a duplicate. An unsorted
        `rglob` would make that outcome depend on inode order, i.e. on the
        filesystem, i.e. unreproducible between two machines holding the same
        corpus.
        """
        pattern = "**/*" if self.recursive else "*"
        for path in sorted(base.glob(pattern)):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(base).parts
            if not self.follow_hidden and any(p.startswith(".") for p in rel_parts):
                continue
            if any(p in _SKIP_DIRS for p in rel_parts[:-1]):
                continue
            if path.suffix.lower() not in self.extensions:
                continue
            yield path

    def _document(self, path: Path, base: Path, text: str, size: int) -> RawDocument:
        rel = path.relative_to(base).as_posix()
        source_url, body = _strip_front_matter(text)
        title = _title_of(body, path)
        # POSIX absolute paths already start with "/", so this produces the
        # three-slash `file:///home/...` form a browser will open.
        uri = f"file://{path.as_posix()}"
        return RawDocument(
            source_system="files",
            external_id=rel,
            uri=uri,
            title=title,
            text=redact_secrets(body),
            fetched_at=_mtime(path),
            metadata={
                "kind": "file",
                "path": rel,
                "dir": rel.rsplit("/", 1)[0] if "/" in rel else "",
                "filename": path.name,
                "ext": path.suffix.lower(),
                "size": size,
                "authority": self.authority,
                "root": str(base),
                **({"source_url": source_url, "canonical": source_url} if source_url else {}),
            },
        )


def _mtime(path: Path) -> float:
    """File mtime as the fetch time, falling back to now.

    The mtime is what makes staleness meaningful for a local corpus - "when did
    this document last change" rather than "when did we last look at it", which
    is what a wall-clock stamp would record on every run.
    """
    try:
        return path.stat().st_mtime
    except OSError:
        return time.time()


def _strip_front_matter(text: str) -> tuple[str, str]:
    """Return `(source_url, body)`.

    The header is removed from the body on purpose: a `<!-- source: ... -->`
    line is metadata, and leaving it in the indexed text means it is embedded,
    ranked and quotable as if it were prose the author wrote.
    """
    source_url = ""
    body = text

    if (fm := _FRONT_MATTER_RE.match(body)) is not None:
        for line in fm.group(1).split("\n"):
            field, sep, value = line.partition(":")
            if sep and field.strip().lower() in {"source", "source_url", "url"}:
                source_url = value.strip().strip("\"'")
                break
        body = body[fm.end():]

    # Only the head of the file is searched: a `<!-- source: -->` line further
    # down belongs to whatever the author was writing about, and stripping it
    # would edit the document's content rather than read its header.
    if (comment := _SOURCE_COMMENT_RE.search(body[:_HEADER_SCAN_CHARS])) is not None:
        source_url = source_url or comment.group(1)
        body = body[: comment.start()] + body[comment.end():]

    return source_url, body.lstrip("\n")


def _title_of(body: str, path: Path) -> str:
    """First `# heading`, else a readable form of the filename.

    A title is never left empty: it is the first segment of every chunk's
    context header, so a document without one produces chunks that cannot say
    where they came from.
    """
    if (h1 := _H1_RE.search(body)) is not None:
        if heading := h1.group(1).strip():
            return heading
    return path.stem.replace("-", " ").replace("_", " ").strip() or path.name
