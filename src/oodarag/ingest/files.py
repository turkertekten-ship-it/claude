"""Ingest a directory of local files.

Every other connector needs the network, which makes them all useless as the
default demo path and useless in CI. This one needs nothing, so the pipeline
can be exercised end to end in an air-gapped container — which is the only way
the zero-dependency promise is testable rather than asserted.

It is also the practical path for material that cannot be fetched: an export
downloaded by hand, a PDF converted elsewhere, a transcript pulled on a machine
that *can* reach the source. Blocked egress stops a fetch; it does not stop a
corpus.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("ingest.files")

#: Text-bearing suffixes. Binary formats are skipped rather than decoded to
#: mojibake, which would otherwise poison the index with unsearchable noise.
DEFAULT_SUFFIXES = (
    ".md", ".markdown", ".txt", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".c", ".h", ".cpp", ".sh", ".bash", ".sql",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".json", ".jsonl",
    ".html", ".css", ".vtt", ".srt",
)

DEFAULT_EXCLUDES = (
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".pytest_cache", ".mypy_cache", "htmlcov", ".oodarag", ".data",
    # `evals/` holds the golden questions the retriever is scored on. Indexing
    # them puts the exam inside the syllabus: a question asked verbatim then
    # retrieves itself, and the abstention cases — the ones that check the
    # retriever declines when it should — stop failing for the worst possible
    # reason. Excluded by default so contamination takes a deliberate act.
    "evals",
)

#: Files above this are almost always generated — minified bundles, lockfiles,
#: vendored blobs — and they dominate an index without informing it.
MAX_FILE_BYTES = 1_000_000


class FileConnector(Connector):
    """Walk a directory and yield each readable text file as a document."""

    authority = 1.0

    def __init__(
        self,
        root: str | Path,
        *,
        suffixes: tuple[str, ...] = DEFAULT_SUFFIXES,
        excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
        max_bytes: int = MAX_FILE_BYTES,
        follow_symlinks: bool = False,
        key: str = "",
    ) -> None:
        self.root = Path(root).resolve()
        self.suffixes = tuple(s.lower() for s in suffixes)
        self.excludes = excludes
        self.max_bytes = max_bytes
        self.follow_symlinks = follow_symlinks
        self.key = key or f"files:{self.root.name}"

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        if not self.root.exists():
            raise FileNotFoundError(f"ingest root does not exist: {self.root}")

        for path in self._walk():
            try:
                stat = path.stat()
                if stat.st_size > self.max_bytes:
                    log.debug("skipping large file", path=str(path), bytes=stat.st_size)
                    continue
                text = path.read_text("utf-8", errors="strict")
            except UnicodeDecodeError:
                continue  # binary content wearing a text suffix
            except OSError as e:
                log.warn("unreadable file", path=str(path), err=str(e))
                continue

            if not text.strip():
                continue

            rel = path.relative_to(self.root)
            yield RawDocument(
                source_system="file",
                external_id=str(rel),
                uri=path.as_uri(),
                title=str(rel),
                # Redaction happens at the connector boundary, before anything
                # is written: a secret that reaches the index is retrievable,
                # and deleting it afterwards does not un-retrieve it.
                text=redact_secrets(text),
                metadata={
                    "kind": "file",
                    "path": str(rel),
                    "suffix": path.suffix.lower(),
                    "bytes": stat.st_size,
                    "modified_at": stat.st_mtime,
                },
                fetched_at=stat.st_mtime,
            )

    def _walk(self) -> Iterator[Path]:
        """Depth-first walk that prunes excluded directories rather than
        filtering their files afterwards — pruning skips the traversal too."""
        for dirpath, dirnames, filenames in os.walk(self.root,
                                                    followlinks=self.follow_symlinks):
            dirnames[:] = sorted(d for d in dirnames if d not in self.excludes)
            for name in sorted(filenames):
                path = Path(dirpath) / name
                if path.suffix.lower() not in self.suffixes:
                    continue
                if not self.follow_symlinks and not self._within_root(path):
                    # `os.walk(followlinks=False)` only stops the walk
                    # *descending* into symlinked directories; a symlinked
                    # file is still listed and read. A repository can ship
                    # `notes.md -> ~/.aws/credentials` and have it indexed.
                    log.warn("skipping symlink outside the ingest root",
                             path=str(path))
                    continue
                yield path

    def _within_root(self, path: Path) -> bool:
        """Does this path, fully resolved, still live under the ingest root?

        Redaction blunts some payloads but is not a containment boundary, so
        the boundary is enforced here.
        """
        try:
            path.resolve().relative_to(self.root)
        except (OSError, ValueError):
            return False
        return True

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["root"] = str(self.root)
        return cursor
