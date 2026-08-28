"""Filesystem connector: index a local directory.

Useful on its own, and the fastest way to smoke-test the whole pipeline without
touching the network.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.ingest.github import LANGUAGE_BY_EXT, SKIP_PATH_RE, TEXT_EXTENSIONS
from oodarag.models import RawDocument
from oodarag.util.logging import get_logger
from oodarag.util.dates import to_timestamp
from oodarag.util.text import redact_secrets, split_front_matter

log = get_logger("ingest.fs")


class FilesystemConnector(Connector):
    def __init__(self, root: str | Path, *, patterns: tuple[str, ...] = ("**/*",),
                 exclude: tuple[str, ...] = (), max_file_bytes: int = 400_000,
                 authority: float = 1.0, key: str | None = None,
                 follow_symlinks: bool = False) -> None:
        self.root = Path(root).resolve()
        self.patterns = patterns
        self.exclude = exclude
        self.max_file_bytes = max_file_bytes
        self.authority = authority
        self.follow_symlinks = follow_symlinks
        self.key = key or f"fs:{self.root}"
        self.source_system = "filesystem"
        self.skipped: dict[str, int] = {}

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        self.skipped = {}
        if not self.root.exists():
            raise FileNotFoundError(f"root does not exist: {self.root}")
        seen: set[Path] = set()
        for pattern in self.patterns:
            for path in sorted(self.root.glob(pattern)):
                if path in seen or not path.is_file():
                    continue
                seen.add(path)
                relative = path.relative_to(self.root).as_posix()
                if not self._wanted(path, relative):
                    continue
                try:
                    data = path.read_bytes()
                except OSError as e:
                    self._skip("unreadable")
                    log.warn("unreadable file", path=relative, err=str(e)[:120])
                    continue
                if b"\x00" in data[:8192]:
                    self._skip("binary")
                    continue
                ext = path.suffix.lower()
                stat = path.stat()
                # A leading `---` block is metadata, not prose. Left in, its
                # keys become corpus terms and the date it records stays
                # invisible to the reranker - the same shape as a connector
                # reading a real date and filing it where nothing scores it.
                front, body = split_front_matter(
                    redact_secrets(data.decode("utf-8", "replace")))
                yield RawDocument(
                    source_system="filesystem",
                    external_id=relative,
                    uri=path.as_uri(),
                    title=relative,
                    text=body,
                    # Front matter first, then the mtime. A `date:` field is
                    # committed and travels with the file; an mtime is set by
                    # whatever last wrote it, so a fresh clone stamps every
                    # file with the checkout time and CI would measure a
                    # different corpus age than a working tree does (L34).
                    #
                    # The mtime is still the file's claim about its own content
                    # rather than when we read it. It used to be stored as
                    # `fetched_at`, which made `Document.created_at` say the
                    # file was ingested at its mtime; `updated_at` came out
                    # right by accident, since it falls back to `fetched_at`.
                    source_updated_at=(to_timestamp(front.get("date"))
                                       or stat.st_mtime),
                    metadata={
                        "kind": "file", "path": relative, "ext": ext,
                        "mtime": stat.st_mtime,
                        **({"front_matter": front} if front else {}),
                        "language": LANGUAGE_BY_EXT.get(ext, "text"),
                        "size": len(data), "authority": self.authority,
                        "is_doc": ext in {".md", ".markdown", ".rst", ".txt", ".adoc"},
                        "root": str(self.root),
                    },
                )

    def _wanted(self, path: Path, relative: str) -> bool:
        if not self.follow_symlinks and path.is_symlink():
            self._skip("symlink")
            return False
        if SKIP_PATH_RE.search(relative):
            self._skip("skip_pattern")
            return False
        if any(fnmatch.fnmatch(relative, pattern) for pattern in self.exclude):
            self._skip("excluded")
            return False
        if path.stat().st_size > self.max_file_bytes:
            self._skip("too_large")
            return False
        name = path.name.lower()
        if path.suffix.lower() not in TEXT_EXTENSIONS and name not in {
            "dockerfile", "makefile", "license", "readme", "changelog", "contributing",
        }:
            self._skip("not_text")
            return False
        return True

    def _skip(self, reason: str) -> None:
        self.skipped[reason] = self.skipped.get(reason, 0) + 1

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["skipped"] = self.skipped
        return cursor
