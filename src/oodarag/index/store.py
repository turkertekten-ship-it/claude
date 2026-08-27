"""Durable state for the whole pipeline: documents, chunks, vectors, index blobs.

Why SQLite and not a directory of JSON files, or a vector database:

* **One file is one corpus.** A `.oodarag/index.db` can be copied, diffed by
  size, backed up, and deleted. Recovering a half-written JSON tree is a
  research project; recovering a SQLite file is `cp`.
* **Transactions are the whole point.** Indexing is a multi-table write —
  chunk rows, vector blobs, a fingerprint on the parent document. A crash in
  the middle of that must leave the *previous* chunk set intact, not a document
  with three of its eleven chunks. Every writer here runs inside one
  `BEGIN IMMEDIATE ... COMMIT`, so the failure mode is "nothing happened",
  never "half happened".
* **A vector database is a dependency.** The promise of this codebase is that
  the pipeline runs in an air-gapped container with nothing installed. Brute
  force cosine over float32 blobs is fast enough for corpora up to the low
  hundreds of thousands of chunks, which is the size a single fund manager's
  document set will ever be.

Two design choices that will look odd until they bite you:

**Content-hash guards, not timestamps.** Re-running an ingest over unchanged
sources must cost nothing. Documents carry ``content_hash`` and a
``chunk_set_hash`` covering the identity of every chunk beneath them plus the
embedding model that produced their vectors. Re-indexing identical content is a
handful of SELECTs. Timestamps would not do: mirrors, rebases and re-uploads
all move mtimes without changing a byte.

**Vectors are float32 in native byte order.** ``array('f').tobytes()`` is
four bytes per dimension with no framing overhead, and reloads at memcpy speed.
The cost is that the file is not portable across a big-endian boundary, so the
byte order in force at creation is recorded in ``meta`` and swapped on read if
the reader disagrees. That is a two-line defence against a class of silent
corruption that would otherwise present as "retrieval got worse".

Nothing here raises on absent data. A missing document, a missing chunk, an
orphaned chunk whose parent was deleted between passes: all are logged and
skipped. The single exception is a database written by a *newer* schema
version, which raises :class:`StoreError` — writing v1 rows into a v2 file
corrupts it, and a loud failure beats a quiet one.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import threading
import time
from array import array
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oodarag.models import Chunk, Document
from oodarag.util.hashing import content_hash
from oodarag.util.logging import get_logger

log = get_logger("store")

#: Bump this and add a migration when the schema changes. The version lives in
#: a row rather than in a `PRAGMA user_version` so it is visible to anything
#: that can run a SELECT, including a human with a sqlite browser.
SCHEMA_VERSION = 1

_FLOAT_CODE = "f"  # 4-byte IEEE754 single precision on every CPython build
_INF = float("inf")


class StoreError(RuntimeError):
    """Raised only for conditions where continuing would corrupt data."""


_SCHEMA_V1: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS meta (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        doc_id         TEXT PRIMARY KEY,
        source_system  TEXT NOT NULL DEFAULT '',
        external_id    TEXT NOT NULL DEFAULT '',
        uri            TEXT NOT NULL DEFAULT '',
        title          TEXT NOT NULL DEFAULT '',
        text           TEXT NOT NULL DEFAULT '',
        content_hash   TEXT NOT NULL DEFAULT '',
        metadata       TEXT NOT NULL DEFAULT '{}',
        created_at     REAL NOT NULL DEFAULT 0,
        updated_at     REAL NOT NULL DEFAULT 0,
        chunk_set_hash TEXT NOT NULL DEFAULT '',
        indexed_at     REAL NOT NULL DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_documents_source  ON documents(source_system)",
    "CREATE INDEX IF NOT EXISTS ix_documents_updated ON documents(updated_at)",
    """
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id       TEXT PRIMARY KEY,
        doc_id         TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
        ordinal        INTEGER NOT NULL DEFAULT 0,
        text           TEXT NOT NULL DEFAULT '',
        context_header TEXT NOT NULL DEFAULT '',
        metadata       TEXT NOT NULL DEFAULT '{}',
        char_start     INTEGER NOT NULL DEFAULT 0,
        char_end       INTEGER NOT NULL DEFAULT 0,
        content_hash   TEXT NOT NULL DEFAULT '',
        token_estimate INTEGER NOT NULL DEFAULT 0
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_chunks_doc ON chunks(doc_id, ordinal)",
    """
    CREATE TABLE IF NOT EXISTS vectors (
        chunk_id TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
        dim      INTEGER NOT NULL,
        model    TEXT NOT NULL DEFAULT '',
        data     BLOB NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS blobs (
        name       TEXT PRIMARY KEY,
        payload    BLOB NOT NULL,
        meta       TEXT NOT NULL DEFAULT '{}',
        updated_at REAL NOT NULL DEFAULT 0
    )
    """,
)

#: version -> statements that take the database *to* that version.
_MIGRATIONS: dict[int, tuple[str, ...]] = {1: _SCHEMA_V1}


@dataclass(slots=True)
class UpsertReport:
    """What a write actually did, so an ingest run can report a real delta.

    ``skipped`` is the interesting number: on a healthy incremental run it
    should be almost everything. A run that reports zero skips is re-indexing
    the world, which means a hash somewhere is unstable.
    """

    written: int = 0
    skipped: int = 0
    deleted: int = 0
    vectors: int = 0
    orphaned: int = 0

    def __add__(self, other: UpsertReport) -> UpsertReport:
        return UpsertReport(
            written=self.written + other.written,
            skipped=self.skipped + other.skipped,
            deleted=self.deleted + other.deleted,
            vectors=self.vectors + other.vectors,
            orphaned=self.orphaned + other.orphaned,
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "written": self.written,
            "skipped": self.skipped,
            "deleted": self.deleted,
            "vectors": self.vectors,
            "orphaned": self.orphaned,
        }


@dataclass(slots=True)
class Blob:
    """An opaque payload keyed by name — how a built index survives a restart."""

    name: str
    payload: bytes
    meta: dict[str, Any]
    updated_at: float


def _dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):  # a metadata dict with something exotic in it
        return json.dumps({"_unserializable": repr(obj)[:500]}, ensure_ascii=False)


def _loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        val = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return val if isinstance(val, dict) else {}


class Store:
    """A SQLite-backed corpus.

    Safe to share between threads: every statement runs under one re-entrant
    lock, which is cheaper than a connection pool and correct for the workload
    (one indexer, several readers). ``check_same_thread`` is therefore off; the
    lock, not sqlite3's thread check, is what provides the guarantee.
    """

    def __init__(
        self,
        path: str | Path = ":memory:",
        *,
        timeout: float = 30.0,
        synchronous: str = "NORMAL",
    ) -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._depth = 0  # nested _tx() calls join the outer transaction
        self._closed = False
        if self.path != ":memory:":
            Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            self.path = str(Path(self.path).expanduser())
        self._conn = sqlite3.connect(self.path, timeout=timeout, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.isolation_level = None  # explicit transactions only; see _tx()
        self._configure(synchronous)
        self._migrate()
        self._swap_vectors = self._read_meta("vector_byteorder", sys.byteorder) != sys.byteorder
        if self._swap_vectors:
            log.warn(
                "index built on the other endianness; vectors will be byte-swapped on read",
                path=self.path,
            )

    # ---------------------------------------------------------------- setup

    def _configure(self, synchronous: str) -> None:
        # WAL lets a query run while an indexer writes. An in-memory database
        # has no write-ahead log to speak of and silently stays in "memory"
        # mode; that is fine and must not be treated as a failure.
        for pragma in (
            "PRAGMA journal_mode=WAL",
            f"PRAGMA synchronous={synchronous}",
            "PRAGMA foreign_keys=ON",
            "PRAGMA temp_store=MEMORY",
            "PRAGMA busy_timeout=30000",
        ):
            try:
                self._conn.execute(pragma)
            except sqlite3.Error as e:  # a locked or exotic build; not fatal
                log.warn("pragma refused", pragma=pragma, err=str(e))

    def _migrate(self) -> None:
        cur = 0
        try:
            row = self._conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            ).fetchone()
            cur = int(row["value"]) if row else 0
        except (sqlite3.Error, ValueError):
            cur = 0  # no meta table yet: a fresh file
        if cur > SCHEMA_VERSION:
            raise StoreError(
                f"{self.path} was written by schema v{cur}; this build understands "
                f"v{SCHEMA_VERSION}. Refusing to write into it."
            )
        if cur == SCHEMA_VERSION:
            return
        with self._tx() as conn:
            for version in sorted(_MIGRATIONS):
                if version <= cur:
                    continue
                for stmt in _MIGRATIONS[version]:
                    conn.execute(stmt)
                cur = version
            conn.execute(
                "INSERT INTO meta(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(cur),),
            )
            conn.execute(
                "INSERT INTO meta(key,value) VALUES('vector_byteorder',?) "
                "ON CONFLICT(key) DO NOTHING",
                (sys.byteorder,),
            )
            conn.execute(
                "INSERT INTO meta(key,value) VALUES('created_at',?) "
                "ON CONFLICT(key) DO NOTHING",
                (str(time.time()),),
            )
        log.info("schema ready", path=self.path, version=cur)

    def _read_meta(self, key: str, default: str = "") -> str:
        row = self._conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    # ----------------------------------------------------------- lifecycle

    def _require(self) -> sqlite3.Connection:
        if self._closed:
            raise StoreError("store is closed")
        return self._conn

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        """One transaction, however deeply nested the call is.

        ``BEGIN IMMEDIATE`` takes the write lock up front rather than upgrading
        halfway through, which is what turns a concurrent indexer from a
        mid-transaction ``SQLITE_BUSY`` into a clean wait.
        """
        with self._lock:
            conn = self._require()
            if self._depth:
                self._depth += 1
                try:
                    yield conn
                finally:
                    self._depth -= 1
                return
            conn.execute("BEGIN IMMEDIATE")
            self._depth = 1
            try:
                yield conn
            except BaseException:
                self._depth = 0
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error as e:
                    log.error("rollback failed", err=str(e))
                raise
            else:
                self._depth = 0
                conn.execute("COMMIT")

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            try:
                self._conn.execute("PRAGMA optimize")
            except sqlite3.Error:
                pass
            self._conn.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --------------------------------------------------------------- write

    def upsert_documents(self, docs: Iterable[Document]) -> UpsertReport:
        """Insert or update documents, skipping any whose content is unchanged.

        The guard compares content hash *and* uri *and* metadata: a document
        whose text is identical but which moved to a new canonical URL is a
        change worth recording, because the citation an answer emits comes from
        the uri, not the text.
        """
        report = UpsertReport()
        with self._tx() as conn:
            for doc in docs:
                meta_json = _dumps(doc.metadata)
                row = conn.execute(
                    "SELECT content_hash, uri, metadata FROM documents WHERE doc_id=?",
                    (doc.doc_id,),
                ).fetchone()
                if (
                    row is not None
                    and row["content_hash"] == doc.content_hash
                    and row["uri"] == doc.uri
                    and row["metadata"] == meta_json
                ):
                    report.skipped += 1
                    continue
                conn.execute(
                    """
                    INSERT INTO documents(doc_id, source_system, external_id, uri, title,
                                          text, content_hash, metadata, created_at, updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(doc_id) DO UPDATE SET
                        source_system=excluded.source_system,
                        external_id=excluded.external_id,
                        uri=excluded.uri,
                        title=excluded.title,
                        text=excluded.text,
                        content_hash=excluded.content_hash,
                        metadata=excluded.metadata,
                        updated_at=excluded.updated_at
                    """,
                    (
                        doc.doc_id, doc.source_system, doc.external_id, doc.uri, doc.title,
                        doc.text, doc.content_hash, meta_json,
                        float(doc.created_at), float(doc.updated_at),
                    ),
                )
                report.written += 1
        log.info("documents upserted", **report.as_dict())
        return report

    def upsert_chunks(
        self,
        chunks: Iterable[Chunk],
        vectors: Mapping[str, Sequence[float]] | None = None,
        *,
        model: str = "",
        replace: bool = True,
        force: bool = False,
    ) -> UpsertReport:
        """Write a document's chunks (and optionally their vectors) atomically.

        With ``replace=True`` — the default, and what re-chunking actually means
        — the chunks handed in are the *complete* set for each document they
        mention: the previous set is deleted and the new one inserted inside one
        transaction. Half a chunk set is therefore not a state this store can be
        left in. Callers streaming chunks for one document across several calls
        must pass ``replace=False``, which upserts row by row and leaves
        unmentioned chunks alone.

        The no-op guard is a fingerprint over every chunk id and content hash in
        ordinal order, plus the embedding model and vector dimension. Model is
        part of it deliberately: identical text re-embedded by a different model
        is not the same index entry, and a guard that ignored that would pin the
        corpus to whichever model happened to run first.

        Chunks whose parent document is absent are counted as ``orphaned`` and
        dropped rather than raising. That happens routinely when a delete races
        an indexing pass, and losing one chunk is a better outcome than losing
        the batch.
        """
        vectors = vectors or {}
        report = UpsertReport()
        by_doc: dict[str, list[Chunk]] = {}
        for chunk in chunks:
            by_doc.setdefault(chunk.doc_id, []).append(chunk)
        if not by_doc:
            return report

        with self._tx() as conn:
            for doc_id, group in by_doc.items():
                group.sort(key=lambda c: (c.ordinal, c.chunk_id))
                row = conn.execute(
                    "SELECT chunk_set_hash FROM documents WHERE doc_id=?", (doc_id,)
                ).fetchone()
                if row is None:
                    report.orphaned += len(group)
                    log.warn("chunks dropped, parent document absent", doc_id=doc_id,
                             count=len(group))
                    continue

                dim = 0
                for chunk in group:
                    vec = vectors.get(chunk.chunk_id)
                    if vec is not None:
                        dim = len(vec)
                        break
                fingerprint = content_hash(
                    model, str(dim), str(len(group)),
                    *(f"{c.chunk_id}:{c.content_hash}:{c.ordinal}" for c in group),
                )
                if replace and not force and row["chunk_set_hash"] == fingerprint:
                    report.skipped += len(group)
                    continue

                if replace:
                    cur = conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
                    report.deleted += cur.rowcount if cur.rowcount > 0 else 0

                for chunk in group:
                    conn.execute(
                        """
                        INSERT INTO chunks(chunk_id, doc_id, ordinal, text, context_header,
                                           metadata, char_start, char_end, content_hash,
                                           token_estimate)
                        VALUES(?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(chunk_id) DO UPDATE SET
                            doc_id=excluded.doc_id, ordinal=excluded.ordinal,
                            text=excluded.text, context_header=excluded.context_header,
                            metadata=excluded.metadata, char_start=excluded.char_start,
                            char_end=excluded.char_end, content_hash=excluded.content_hash,
                            token_estimate=excluded.token_estimate
                        """,
                        (
                            chunk.chunk_id, chunk.doc_id, int(chunk.ordinal), chunk.text,
                            chunk.context_header, _dumps(chunk.metadata),
                            int(chunk.char_start), int(chunk.char_end),
                            chunk.content_hash, int(chunk.token_estimate),
                        ),
                    )
                    report.written += 1
                    vec = vectors.get(chunk.chunk_id)
                    if vec is None:
                        continue
                    # ON CONFLICT DO UPDATE, never INSERT OR REPLACE: REPLACE
                    # deletes the row first, and with foreign_keys ON that
                    # cascade would take the vector with it.
                    conn.execute(
                        """
                        INSERT INTO vectors(chunk_id, dim, model, data) VALUES(?,?,?,?)
                        ON CONFLICT(chunk_id) DO UPDATE SET
                            dim=excluded.dim, model=excluded.model, data=excluded.data
                        """,
                        (chunk.chunk_id, len(vec), model, encode_vector(vec)),
                    )
                    report.vectors += 1

                conn.execute(
                    "UPDATE documents SET chunk_set_hash=?, indexed_at=? WHERE doc_id=?",
                    (fingerprint, time.time(), doc_id),
                )
        log.info("chunks upserted", docs=len(by_doc), **report.as_dict())
        return report

    def put_vector(self, chunk_id: str, vec: Sequence[float], model: str = "") -> bool:
        """Attach or replace one vector. Returns False if the chunk is gone."""
        with self._tx() as conn:
            exists = conn.execute(
                "SELECT 1 FROM chunks WHERE chunk_id=?", (chunk_id,)
            ).fetchone()
            if exists is None:
                log.warn("vector dropped, chunk absent", chunk_id=chunk_id)
                return False
            conn.execute(
                """
                INSERT INTO vectors(chunk_id, dim, model, data) VALUES(?,?,?,?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    dim=excluded.dim, model=excluded.model, data=excluded.data
                """,
                (chunk_id, len(vec), model, encode_vector(vec)),
            )
        return True

    def delete_document(self, doc_id: str) -> int:
        """Remove a document and everything beneath it. Returns chunks deleted.

        A missing document is a logged no-op returning 0, not an error: deletes
        are replayed from ingest deltas and replaying one twice is normal.
        """
        with self._tx() as conn:
            row = conn.execute("SELECT 1 FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
            if row is None:
                log.warn("delete skipped, no such document", doc_id=doc_id)
                return 0
            n = conn.execute(
                "SELECT COUNT(*) AS n FROM chunks WHERE doc_id=?", (doc_id,)
            ).fetchone()["n"]
            # Belt and braces: the FK cascade does this, but only when
            # foreign_keys is ON, and a pragma can be refused (see _configure).
            conn.execute(
                "DELETE FROM vectors WHERE chunk_id IN (SELECT chunk_id FROM chunks "
                "WHERE doc_id=?)",
                (doc_id,),
            )
            conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))
        log.info("document deleted", doc_id=doc_id, chunks=n)
        return int(n)

    def put_blob(self, name: str, payload: bytes, meta: Mapping[str, Any] | None = None) -> None:
        """Store a built index (or anything else opaque) under a name."""
        with self._tx() as conn:
            conn.execute(
                """
                INSERT INTO blobs(name, payload, meta, updated_at) VALUES(?,?,?,?)
                ON CONFLICT(name) DO UPDATE SET
                    payload=excluded.payload, meta=excluded.meta,
                    updated_at=excluded.updated_at
                """,
                (name, sqlite3.Binary(payload), _dumps(dict(meta or {})), time.time()),
            )

    def get_blob(self, name: str) -> Blob | None:
        with self._lock:
            row = self._require().execute(
                "SELECT name, payload, meta, updated_at FROM blobs WHERE name=?", (name,)
            ).fetchone()
        if row is None:
            return None
        return Blob(row["name"], bytes(row["payload"]), _loads(row["meta"]), row["updated_at"])

    def delete_blob(self, name: str) -> bool:
        with self._tx() as conn:
            return conn.execute("DELETE FROM blobs WHERE name=?", (name,)).rowcount > 0

    # ---------------------------------------------------------------- read

    def get_document(self, doc_id: str) -> Document | None:
        with self._lock:
            row = self._require().execute(
                "SELECT * FROM documents WHERE doc_id=?", (doc_id,)
            ).fetchone()
        return _row_to_document(row) if row else None

    def get_documents(self, doc_ids: Iterable[str]) -> dict[str, Document]:
        """Batch fetch. One query per 500 ids, because SQLITE_MAX_VARIABLE_NUMBER
        is 999 on older builds and a retriever will happily ask for more."""
        ids = list(dict.fromkeys(doc_ids))
        out: dict[str, Document] = {}
        with self._lock:
            conn = self._require()
            for start in range(0, len(ids), 500):
                batch = ids[start : start + 500]
                marks = ",".join("?" * len(batch))
                for row in conn.execute(
                    f"SELECT * FROM documents WHERE doc_id IN ({marks})", batch  # noqa: S608
                ):
                    out[row["doc_id"]] = _row_to_document(row)
        return out

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        with self._lock:
            row = self._require().execute(
                "SELECT * FROM chunks WHERE chunk_id=?", (chunk_id,)
            ).fetchone()
        return _row_to_chunk(row) if row else None

    def get_chunks(self, chunk_ids: Iterable[str]) -> dict[str, Chunk]:
        ids = list(dict.fromkeys(chunk_ids))
        out: dict[str, Chunk] = {}
        with self._lock:
            conn = self._require()
            for start in range(0, len(ids), 500):
                batch = ids[start : start + 500]
                marks = ",".join("?" * len(batch))
                for row in conn.execute(
                    f"SELECT * FROM chunks WHERE chunk_id IN ({marks})", batch  # noqa: S608
                ):
                    out[row["chunk_id"]] = _row_to_chunk(row)
        return out

    def iter_documents(
        self, source_system: str | None = None, batch_size: int = 200
    ) -> Iterator[Document]:
        sql = "SELECT * FROM documents"
        params: list[Any] = []
        if source_system:
            sql += " WHERE source_system=?"
            params.append(source_system)
        sql += " ORDER BY doc_id"
        yield from (_row_to_document(r) for r in self._stream(sql, params, batch_size))

    def iter_chunks(self, doc_id: str | None = None, batch_size: int = 500) -> Iterator[Chunk]:
        sql = "SELECT * FROM chunks"
        params: list[Any] = []
        if doc_id:
            sql += " WHERE doc_id=?"
            params.append(doc_id)
        sql += " ORDER BY doc_id, ordinal, chunk_id"
        yield from (_row_to_chunk(r) for r in self._stream(sql, params, batch_size))

    def iter_vectors(self, batch_size: int = 500) -> Iterator[tuple[str, array]]:
        """Stream (chunk_id, float32 array). Vectors orphaned by a failed delete
        are skipped by the join rather than handed to an index that would then
        return hits pointing at nothing."""
        sql = (
            "SELECT v.chunk_id AS chunk_id, v.data AS data FROM vectors v "
            "JOIN chunks c ON c.chunk_id = v.chunk_id ORDER BY v.chunk_id"
        )
        for row in self._stream(sql, [], batch_size):
            yield row["chunk_id"], decode_vector(bytes(row["data"]), swap=self._swap_vectors)

    def get_vector(self, chunk_id: str) -> array | None:
        with self._lock:
            row = self._require().execute(
                "SELECT data FROM vectors WHERE chunk_id=?", (chunk_id,)
            ).fetchone()
        if row is None:
            return None
        return decode_vector(bytes(row["data"]), swap=self._swap_vectors)

    def _stream(
        self, sql: str, params: Sequence[Any], batch_size: int
    ) -> Iterator[sqlite3.Row]:
        """Fetch in batches, taking the lock per batch rather than for the walk.

        Holding the lock across every yield would be simpler and is a trap: an
        iterator the caller starts and abandons would pin the lock until the
        generator is finalised, and an indexer thread would block behind it
        forever. Per-batch locking makes that impossible. The price is SQLite's
        own same-connection isolation caveat — a walk started before a
        concurrent write may or may not observe that write — which is the
        correct guarantee to expose rather than one this layer cannot keep.
        """
        with self._lock:
            cur = self._require().execute(sql, tuple(params))
        try:
            while True:
                with self._lock:
                    rows = cur.fetchmany(batch_size)
                if not rows:
                    return
                yield from rows
        finally:
            with self._lock:
                cur.close()

    def find_chunk_ids(
        self,
        *,
        source_system: str | Sequence[str] | None = None,
        doc_ids: Sequence[str] | None = None,
        metadata: Mapping[str, Any] | None = None,
        updated_after: float | None = None,
        updated_before: float | None = None,
    ) -> set[str]:
        """Chunk ids whose *parent document* matches. The filter push-down.

        Source and time go into SQL because they are indexed. Metadata equality
        is evaluated in Python against the decoded JSON, deliberately: the JSON1
        extension is present on every build we have seen but is not guaranteed
        by the stdlib contract, and a retriever that silently returns nothing
        because ``json_extract`` is missing is a bad way to find that out. A
        filter value that is a list or set means "any of".
        """
        clauses: list[str] = []
        params: list[Any] = []
        if source_system:
            systems = [source_system] if isinstance(source_system, str) else list(source_system)
            if systems:
                clauses.append(f"d.source_system IN ({','.join('?' * len(systems))})")
                params.extend(systems)
        if doc_ids:
            ids = list(doc_ids)
            clauses.append(f"d.doc_id IN ({','.join('?' * len(ids))})")
            params.extend(ids)
        if updated_after is not None:
            clauses.append("d.updated_at >= ?")
            params.append(float(updated_after))
        if updated_before is not None:
            clauses.append("d.updated_at <= ?")
            params.append(float(updated_before))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT c.chunk_id AS chunk_id, d.metadata AS metadata "  # noqa: S608
            "FROM chunks c JOIN documents d ON d.doc_id = c.doc_id" + where
        )
        out: set[str] = set()
        wanted = dict(metadata) if metadata else None
        for row in self._stream(sql, params, 1000):
            if wanted and not _metadata_matches(_loads(row["metadata"]), wanted):
                continue
            out.add(row["chunk_id"])
        return out

    def stats(self) -> dict[str, Any]:
        """A one-glance health check. Read `chunks_without_vectors` first: a
        non-zero number there means the dense arm is silently blind to part of
        the corpus, which looks like "retrieval is a bit worse" and never like
        an error."""
        with self._lock:
            conn = self._require()

            def scalar(sql: str, default: Any = 0) -> Any:
                try:
                    row = conn.execute(sql).fetchone()
                except sqlite3.Error:
                    return default
                return default if row is None or row[0] is None else row[0]

            dims = [
                int(r["dim"]) for r in conn.execute("SELECT DISTINCT dim FROM vectors ORDER BY dim")
            ]
            sources = {
                r["source_system"]: int(r["n"])
                for r in conn.execute(
                    "SELECT source_system, COUNT(*) AS n FROM documents "
                    "GROUP BY source_system ORDER BY n DESC"
                )
            }
            blobs = [r["name"] for r in conn.execute("SELECT name FROM blobs ORDER BY name")]
            out = {
                "path": self.path,
                "schema_version": int(self._read_meta("schema_version", "0") or 0),
                "documents": int(scalar("SELECT COUNT(*) FROM documents")),
                "chunks": int(scalar("SELECT COUNT(*) FROM chunks")),
                "vectors": int(scalar("SELECT COUNT(*) FROM vectors")),
                "chunks_without_vectors": int(
                    scalar(
                        "SELECT COUNT(*) FROM chunks c LEFT JOIN vectors v "
                        "ON v.chunk_id=c.chunk_id WHERE v.chunk_id IS NULL"
                    )
                ),
                "vector_dims": dims,
                "sources": sources,
                "blobs": blobs,
                "oldest_updated_at": float(scalar("SELECT MIN(updated_at) FROM documents", 0.0)),
                "newest_updated_at": float(scalar("SELECT MAX(updated_at) FROM documents", 0.0)),
                "total_tokens": int(scalar("SELECT SUM(token_estimate) FROM chunks")),
            }
        # The -wal and -shm sidecars hold everything written since the last
        # checkpoint. Reporting only the main file makes a freshly indexed
        # corpus look like an empty one.
        size = 0
        if self.path != ":memory:":
            for suffix in ("", "-wal", "-shm"):
                try:
                    size += Path(self.path + suffix).stat().st_size
                except OSError:
                    pass
        out["size_bytes"] = size
        return out

    def __repr__(self) -> str:
        state = "closed" if self._closed else "open"
        return f"<Store {self.path!r} {state}>"


# ------------------------------------------------------------------ codecs


def encode_vector(vec: Sequence[float]) -> bytes:
    """Pack to float32. Values that are NaN or infinite are zeroed rather than
    stored: one inf in a corpus turns every cosine into NaN and the whole dense
    arm returns garbage in an order nobody can explain."""
    values: list[float] = []
    for x in vec:
        try:
            f = float(x)
        except (TypeError, ValueError):
            f = 0.0
        if f != f or f in (_INF, -_INF):
            f = 0.0
        values.append(f)
    return array(_FLOAT_CODE, values).tobytes()


def decode_vector(blob: bytes, *, swap: bool = False) -> array:
    arr = array(_FLOAT_CODE)
    usable = len(blob) - (len(blob) % arr.itemsize)
    if usable != len(blob):
        # A truncated blob is a partially-written file, not a reason to abort a
        # query. Take the whole dimensions and let the dimension check upstream
        # reject it.
        log.warn("vector blob truncated", bytes=len(blob))
    arr.frombytes(blob[:usable])
    if swap:
        arr.byteswap()
    return arr


def _metadata_matches(actual: Mapping[str, Any], wanted: Mapping[str, Any]) -> bool:
    for key, want in wanted.items():
        got = actual.get(key)
        if isinstance(want, list | tuple | set | frozenset):
            if got not in want:
                return False
        elif got != want:
            return False
    return True


def _row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        doc_id=row["doc_id"],
        source_system=row["source_system"],
        external_id=row["external_id"],
        uri=row["uri"],
        title=row["title"],
        text=row["text"],
        content_hash=row["content_hash"],
        metadata=_loads(row["metadata"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_chunk(row: sqlite3.Row) -> Chunk:
    return Chunk(
        chunk_id=row["chunk_id"],
        doc_id=row["doc_id"],
        ordinal=int(row["ordinal"]),
        text=row["text"],
        context_header=row["context_header"],
        metadata=_loads(row["metadata"]),
        char_start=int(row["char_start"]),
        char_end=int(row["char_end"]),
    )
