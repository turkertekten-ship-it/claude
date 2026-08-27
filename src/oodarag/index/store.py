"""Persistent storage for documents, chunks and vectors: one SQLite file.

Everything downstream of chunking reads from here, so the store is the only
place in the pipeline allowed to own durable state. That concentration is the
point: a directory of JSON sidecars plus a pickled matrix - the obvious
zero-dependency alternative - has no transactions, so a crash halfway through
re-indexing a document leaves a corpus that is *silently* wrong, with half a
document's chunks pointing at text that no longer exists. SQLite is in the
standard library, gives us that transaction for free, and keeps the whole index
in a single file that can be copied, diffed by size, and deleted with one `rm`.

Design decisions worth knowing about:

**WAL plus `synchronous=NORMAL`.** An ingest is one long writer and many short
readers (`iter_chunks` rebuilding BM25 while the next connector still writes);
under the default rollback journal those readers block. `NORMAL` trades an fsync
per commit for an fsync per checkpoint, and the exposure is bounded by what this
file actually is: a *derived* index. Losing the last few transactions to a power
cut costs a re-ingest, never source data - the connectors' hashes still know
what changed.

**Vectors are float32 BLOBs, not JSON arrays or one column per dimension.**
`array("f", vec).tobytes()` is 4 bytes per dimension against roughly twenty for
decimal text, and the round trip is a C memcpy rather than a parse of half a
million float literals. A BLOB is also deliberately opaque: nothing can be
tempted to write a SQL query that scores vectors, which is `index/dense.py`'s
job. The bytes are canonicalised to little-endian so an index file stays
readable if it is copied to a machine of the other endianness - `array` uses
native order, and a silently byteswapped vector produces plausible-looking
nonsense scores rather than an error.

**Opening a newer schema is refused, loudly.** `meta.schema_version` is checked
before a single `CREATE` runs. A future build that adds a column would leave
this build reading rows it half-understands and answering questions from them;
a refusal that names both versions costs one confusing minute, a silent misread
costs a week of doubting the retriever.

**Upserts are `ON CONFLICT DO UPDATE`, never `INSERT OR REPLACE`.** With foreign
keys enabled - and they are - `REPLACE` *deletes* the conflicting row first,
which fires `ON DELETE CASCADE` and takes every chunk of that document (and
every vector of that chunk) with it. Re-ingesting an unchanged document would
quietly empty it. That trap is the entire reason the verbose upsert form is
spelled out below.

**Batch writes count their casualties.** One chunk whose document was never
upserted trips a foreign key; `executemany` would abort the batch and take the
other four thousand chunks with it, so a failed batch is replayed row by row and
the offenders are counted out and logged. Replay is safe precisely because every
write here is an idempotent upsert.

No ranking structure is stored. BM25 statistics and the dense matrix are cheap
to rebuild from `iter_chunks()` / `iter_vectors()` and expensive to keep
consistent across a partial write, so they live in memory and are rebuilt.
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
from itertools import islice
from pathlib import Path
from typing import Any, TypeVar

from oodarag.models import Chunk, Document
from oodarag.util.logging import get_logger

log = get_logger("index")

#: Bumped on any change to the tables below. Written into `meta` on open and
#: compared on every subsequent open.
SCHEMA_VERSION = 1

#: Rows per `executemany`. Large enough that the per-statement overhead
#: disappears, small enough that an iterator of a million chunks is never
#: materialized in memory.
_WRITE_BATCH = 1000

#: Rows pulled per round trip by the streaming iterators.
_ITER_BATCH = 512

#: Ids per `IN (...)` lookup. SQLite's compiled-in parameter ceiling is 999 on
#: builds older than 3.32; a retrieval batch never comes close anyway.
_LOOKUP_BATCH = 400

_MEMORY = ":memory:"

_LITTLE_ENDIAN = sys.byteorder == "little"

_T = TypeVar("_T")


class SchemaVersionError(RuntimeError):
    """Raised when an index file was written by a newer build of oodarag."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id        TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    external_id   TEXT NOT NULL,
    uri           TEXT NOT NULL,
    title         TEXT NOT NULL,
    text          TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    metadata      TEXT NOT NULL DEFAULT '{}',
    created_at    REAL NOT NULL,
    updated_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id       TEXT PRIMARY KEY,
    doc_id         TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    ordinal        INTEGER NOT NULL,
    text           TEXT NOT NULL,
    context_header TEXT NOT NULL DEFAULT '',
    metadata       TEXT NOT NULL DEFAULT '{}',
    char_start     INTEGER NOT NULL DEFAULT 0,
    char_end       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vectors (
    chunk_id TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    dim      INTEGER NOT NULL,
    vec      BLOB NOT NULL
);

-- Every write path is per-document (replace this doc's chunks) and every
-- citation walks chunk -> document, so this index is load-bearing, not a
-- precaution.
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id, ordinal);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_system);
"""

_SELECT_DOCUMENT = """
SELECT doc_id, source_system, external_id, uri, title, text, content_hash,
       metadata, created_at, updated_at
FROM documents
"""

_SELECT_CHUNK = """
SELECT chunk_id, doc_id, ordinal, text, context_header, metadata,
       char_start, char_end
FROM chunks
"""

# Spelled out rather than using INSERT OR REPLACE: REPLACE deletes the old row,
# which cascades into chunks (and from there into vectors). See the module
# docstring - re-ingesting an unchanged document would empty it.
_UPSERT_DOCUMENT = """
INSERT INTO documents
    (doc_id, source_system, external_id, uri, title, text, content_hash,
     metadata, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(doc_id) DO UPDATE SET
    source_system = excluded.source_system,
    external_id   = excluded.external_id,
    uri           = excluded.uri,
    title         = excluded.title,
    text          = excluded.text,
    content_hash  = excluded.content_hash,
    metadata      = excluded.metadata,
    created_at    = excluded.created_at,
    updated_at    = excluded.updated_at
"""

_UPSERT_CHUNK = """
INSERT INTO chunks
    (chunk_id, doc_id, ordinal, text, context_header, metadata,
     char_start, char_end)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(chunk_id) DO UPDATE SET
    doc_id         = excluded.doc_id,
    ordinal        = excluded.ordinal,
    text           = excluded.text,
    context_header = excluded.context_header,
    metadata       = excluded.metadata,
    char_start     = excluded.char_start,
    char_end       = excluded.char_end
"""

_UPSERT_VECTOR = """
INSERT INTO vectors (chunk_id, dim, vec)
VALUES (?, ?, ?)
ON CONFLICT(chunk_id) DO UPDATE SET
    dim = excluded.dim,
    vec = excluded.vec
"""


def _batches(items: Iterable[_T], size: int) -> Iterator[list[_T]]:
    """Slice an iterable into lists of at most `size`, without materializing it."""
    iterator = iter(items)
    while True:
        batch = list(islice(iterator, size))
        if not batch:
            return
        yield batch


def pack_vector(vec: Sequence[float]) -> bytes:
    """float32 bytes, little-endian regardless of host order."""
    buf = array("f", vec)
    if not _LITTLE_ENDIAN:
        buf.byteswap()
    return buf.tobytes()


def unpack_vector(blob: bytes) -> list[float]:
    """Inverse of `pack_vector`. Raises ValueError on a truncated blob."""
    buf = array("f")
    buf.frombytes(blob)
    if not _LITTLE_ENDIAN:
        buf.byteswap()
    return buf.tolist()


def _dump_json(value: Mapping[str, Any] | None) -> str:
    """Serialize a metadata dict. Never raises: metadata is provenance, and
    losing a whole batch over one unserializable value would be a bad trade."""
    if not value:
        return "{}"
    try:
        return json.dumps(dict(value), ensure_ascii=False, default=str)
    except (TypeError, ValueError) as e:  # circular reference, mostly
        log.warn("metadata not serializable, stored empty", err=str(e)[:200])
        return "{}"


def _load_json(raw: Any) -> dict[str, Any]:
    if not raw or raw == "{}":
        return {}
    try:
        loaded = json.loads(raw)
    except (TypeError, ValueError):
        log.warn("metadata unreadable, returned empty")
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        doc_id=row["doc_id"],
        source_system=row["source_system"],
        external_id=row["external_id"],
        uri=row["uri"],
        title=row["title"],
        text=row["text"],
        content_hash=row["content_hash"],
        metadata=_load_json(row["metadata"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_chunk(row: sqlite3.Row) -> Chunk:
    return Chunk(
        chunk_id=row["chunk_id"],
        doc_id=row["doc_id"],
        ordinal=row["ordinal"],
        text=row["text"],
        context_header=row["context_header"],
        metadata=_load_json(row["metadata"]),
        char_start=row["char_start"],
        char_end=row["char_end"],
    )


class Store:
    """SQLite-backed document/chunk/vector store. WAL mode, one file.

    The connection is opened with `check_same_thread=False` so a threaded
    ingest can share one store, and writers are serialized by an internal lock
    so a multi-statement transaction stays atomic against a second writer.
    Readers take no lock: they must not, because `iter_chunks` hands control
    back to the caller mid-cursor and holding a lock across that yield would
    deadlock the first consumer that decided to write.
    """

    def __init__(self, path: str | Path = ".oodarag/index.db") -> None:
        self._in_memory = str(path) == _MEMORY
        self.path = Path(path)
        if not self._in_memory:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._closed = False
        self._conn = sqlite3.connect(
            _MEMORY if self._in_memory else str(self.path),
            timeout=30.0,
            # Autocommit: transaction boundaries are stated explicitly in
            # `_transaction` rather than inferred by the driver from statement
            # shape, which is what makes "delete then insert, atomically"
            # something this module controls instead of hopes for.
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        # If validation refuses the file, close the handle before propagating.
        # A caller that catches SchemaVersionError has no reference to this
        # connection and cannot close it, so leaving it open leaks the handle
        # and, on Windows, the file lock with it.
        try:
            self._configure()
            self.schema_version = self._open_schema()
        except BaseException:
            self._conn.close()
            self._closed = True
            raise

    # ---- lifecycle -------------------------------------------------------

    def _configure(self) -> None:
        conn = self._conn
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA temp_store=MEMORY")
        if self._in_memory:
            return
        mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()
        # WAL is unavailable on some network filesystems. The rollback journal
        # is slower and still correct, so this is a note, not a failure.
        if mode is not None and str(mode[0]).lower() != "wal":
            log.warn("WAL unavailable", path=str(self.path), journal_mode=str(mode[0]))

    def _open_schema(self) -> int:
        """Validate the on-disk schema version, then create/patch the tables."""
        conn = self._conn
        found: int | None = None
        has_meta = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'"
        ).fetchone()
        if has_meta is not None:
            row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            if row is not None:
                try:
                    found = int(row[0])
                except (TypeError, ValueError):
                    log.warn("schema_version unreadable, treating as current", value=str(row[0])[:40])
        # Checked before any CREATE runs: a newer file must be left exactly as
        # it was found, not half-migrated backwards by this build's schema.
        if found is not None and found > SCHEMA_VERSION:
            raise SchemaVersionError(
                f"index at {self.path} was written with schema version {found}, "
                f"but this build of oodarag understands version {SCHEMA_VERSION}. "
                f"Upgrade oodarag, or rebuild the index from source with this build - "
                f"reading version {found} rows as version {SCHEMA_VERSION} would answer "
                f"questions from data it does not understand."
            )
        conn.executescript(_SCHEMA)
        if found is not None and found < SCHEMA_VERSION:
            # Every migration so far is covered by the idempotent CREATEs above,
            # so the stamp is simply advanced. A real one runs here, before it.
            log.info("index schema upgraded", path=str(self.path), was=found, now=SCHEMA_VERSION)
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(SCHEMA_VERSION),),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('created_at', ?) ON CONFLICT(key) DO NOTHING",
            (f"{time.time():.3f}",),
        )
        return SCHEMA_VERSION

    def close(self) -> None:
        """Checkpoint and close. Idempotent, so `with` plus an explicit close
        in a `finally` is not an error."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                if not self._in_memory:
                    # Folds the WAL back into the main file, so the number
                    # `stats()["bytes"]` reports next run is the real one and a
                    # copied index.db is complete on its own.
                    self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self._conn.execute("PRAGMA optimize")
            except sqlite3.Error as e:
                log.debug("checkpoint on close skipped", err=str(e)[:200])
            finally:
                self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---- writes ----------------------------------------------------------

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        """One explicit transaction. Never nested - `_insert_chunks` and the
        batch loops run *inside* a caller's transaction, they do not open one."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            self._conn.execute("COMMIT")

    def _write_rows(self, sql: str, rows: Sequence[tuple[Any, ...]], *, table: str) -> int:
        """Write `rows`, returning how many landed.

        The fast path is one `executemany`. A single bad row - a chunk whose
        document was never upserted, so the foreign key bites - would abort the
        whole batch, so on a per-row failure the batch is replayed one statement
        at a time and the offenders are counted out. Replaying rows that already
        succeeded is harmless because `sql` is always an idempotent upsert.
        """
        if not rows:
            return 0
        try:
            self._conn.executemany(sql, rows)
            return len(rows)
        except (sqlite3.IntegrityError, sqlite3.InterfaceError):
            pass  # a data problem in some row; find out which below
        written = 0
        failed = 0
        first_error = ""
        for row in rows:
            try:
                self._conn.execute(sql, row)
                written += 1
            except sqlite3.Error as e:
                failed += 1
                if not first_error:
                    first_error = f"{type(e).__name__}: {e}"
        if failed:
            log.warn(
                "rows rejected", table=table, failed=failed, written=written, err=first_error[:200]
            )
        return written

    def upsert_documents(self, docs: Iterable[Document]) -> int:
        """Insert or update documents; returns the number of rows written.

        Batched per `_WRITE_BATCH` so an iterator over a large corpus streams.
        Each batch is its own transaction: upserts are idempotent, so a failure
        partway leaves a consistent prefix that the next run simply rewrites.
        """
        written = 0
        for batch in _batches(docs, _WRITE_BATCH):
            rows = [
                (
                    d.doc_id,
                    d.source_system,
                    d.external_id,
                    d.uri,
                    d.title,
                    d.text,
                    d.content_hash,
                    _dump_json(d.metadata),
                    float(d.created_at),
                    float(d.updated_at),
                )
                for d in batch
            ]
            with self._transaction():
                written += self._write_rows(_UPSERT_DOCUMENT, rows, table="documents")
        return written

    def _insert_chunks(
        self, chunks: Sequence[Chunk], vectors: Mapping[str, Sequence[float]] | None
    ) -> int:
        """Write chunks and any vectors keyed to them. Requires an open
        transaction, so the chunk and its vector commit together or not at all."""
        rows = [
            (
                c.chunk_id,
                c.doc_id,
                int(c.ordinal),
                c.text,
                c.context_header,
                _dump_json(c.metadata),
                int(c.char_start),
                int(c.char_end),
            )
            for c in chunks
        ]
        written = self._write_rows(_UPSERT_CHUNK, rows, table="chunks")
        if vectors:
            # Looked up per chunk rather than iterated: `vectors` may legitimately
            # cover a whole run while this batch is 1,000 of its chunks, and a
            # vector whose chunk is not here would only trip a foreign key.
            vec_rows = [
                (c.chunk_id, len(vec), pack_vector(vec))
                for c in chunks
                if (vec := vectors.get(c.chunk_id)) is not None
            ]
            self._write_rows(_UPSERT_VECTOR, vec_rows, table="vectors")
        return written

    def upsert_chunks(
        self, chunks: Iterable[Chunk], vectors: Mapping[str, Sequence[float]] | None = None
    ) -> int:
        """Insert or update chunks (and their vectors); returns chunks written.

        The count is of chunk rows: vectors ride along and are reported by
        `stats()`. Chunks whose `doc_id` has no document row are rejected by the
        foreign key, counted, and logged - the rest of the batch still lands.
        """
        written = 0
        for batch in _batches(chunks, _WRITE_BATCH):
            with self._transaction():
                written += self._insert_chunks(batch, vectors)
        return written

    def replace_document_chunks(
        self,
        doc_id: str,
        chunks: list[Chunk],
        vectors: Mapping[str, Sequence[float]] | None = None,
    ) -> int:
        """Swap a document's chunks for a new set, atomically.

        Delete and insert share one transaction, so a crash cannot leave a
        document holding half its chunks - which would not look like damage from
        the outside, it would look like a document that answers questions badly.
        The old vectors go with the old chunks via ON DELETE CASCADE.
        """
        own = [c for c in chunks if c.doc_id == doc_id]
        if len(own) != len(chunks):
            # A chunk carrying someone else's doc_id is a caller bug. Writing it
            # would make it invisible to the next replace of *this* document and
            # so unreachable by any later delete: refuse it here, loudly.
            log.warn("chunks with foreign doc_id dropped", doc_id=doc_id, dropped=len(chunks) - len(own))
        written = 0
        with self._transaction():
            self._conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            # Batched only to bound statement size; the transaction spans them all.
            for batch in _batches(own, _WRITE_BATCH):
                written += self._insert_chunks(batch, vectors)
        return written

    def delete_document(self, doc_id: str) -> int:
        """Delete a document; returns 1 if it existed, 0 if it did not.

        Its chunks and their vectors go too, by cascade. The return value is
        deliberately the document count and not the row count, so a caller can
        read it as "did this exist" and sum it across a purge.
        """
        with self._transaction():
            n_chunks = self._conn.execute(
                "SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchone()[0]
            cur = self._conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            removed = max(cur.rowcount, 0)
        if removed:
            log.info("document deleted", doc_id=doc_id, chunks=n_chunks)
        return removed

    # ---- reads -----------------------------------------------------------

    def get_document(self, doc_id: str) -> Document | None:
        row = self._conn.execute(f"{_SELECT_DOCUMENT} WHERE doc_id = ?", (doc_id,)).fetchone()
        return _row_to_document(row) if row is not None else None

    def documents(self) -> list[Document]:
        """Every document, oldest first. `doc_id` breaks ties so the order is
        stable across runs and an eval report is diffable."""
        cur = self._conn.execute(f"{_SELECT_DOCUMENT} ORDER BY created_at, doc_id")
        return [_row_to_document(row) for row in cur.fetchall()]

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        row = self._conn.execute(f"{_SELECT_CHUNK} WHERE chunk_id = ?", (chunk_id,)).fetchone()
        return _row_to_chunk(row) if row is not None else None

    def get_chunks(self, chunk_ids: Sequence[str]) -> dict[str, Chunk]:
        """Look up many chunks at once.

        Ids that no longer exist are simply absent from the result rather than
        raising: a ranking computed against an in-memory index outlives the
        re-index that dropped one of its chunks, and losing one hit is a far
        better outcome for that query than a KeyError.
        """
        found: dict[str, Chunk] = {}
        for batch in _batches(chunk_ids, _LOOKUP_BATCH):
            placeholders = ",".join("?" * len(batch))
            cur = self._conn.execute(
                f"{_SELECT_CHUNK} WHERE chunk_id IN ({placeholders})", tuple(batch)
            )
            for row in cur.fetchall():
                found[row["chunk_id"]] = _row_to_chunk(row)
        return found

    def iter_chunks(self) -> Iterator[Chunk]:
        """Stream every chunk in document order.

        Ordered, not arbitrary: BM25 and the dense index break score ties by
        insertion order, so a rebuild from an unordered scan would reshuffle
        equal-scoring results between runs and make an eval delta unreadable.
        """
        cur = self._conn.execute(f"{_SELECT_CHUNK} ORDER BY doc_id, ordinal")
        try:
            while True:
                rows = cur.fetchmany(_ITER_BATCH)
                if not rows:
                    return
                for row in rows:
                    yield _row_to_chunk(row)
        finally:
            cur.close()

    def iter_vectors(self) -> Iterator[tuple[str, list[float]]]:
        """Stream `(chunk_id, vector)` pairs in a stable order.

        A blob that cannot be decoded is skipped and counted, not raised: one
        damaged vector costs one chunk its dense arm, while an exception here
        would cost the whole index its rebuild.
        """
        cur = self._conn.execute("SELECT chunk_id, vec FROM vectors ORDER BY chunk_id")
        damaged = 0
        try:
            while True:
                rows = cur.fetchmany(_ITER_BATCH)
                if not rows:
                    break
                for row in rows:
                    try:
                        yield row["chunk_id"], unpack_vector(row["vec"])
                    except (ValueError, TypeError):
                        damaged += 1
        finally:
            cur.close()
            if damaged:
                log.warn("undecodable vectors skipped", count=damaged)

    def get_vector(self, chunk_id: str) -> list[float] | None:
        row = self._conn.execute(
            "SELECT vec FROM vectors WHERE chunk_id = ?", (chunk_id,)
        ).fetchone()
        if row is None:
            return None
        try:
            return unpack_vector(row["vec"])
        except (ValueError, TypeError):
            log.warn("vector undecodable", chunk_id=chunk_id)
            return None

    # ---- reporting -------------------------------------------------------

    def _bytes_on_disk(self) -> int:
        """Size of the index including its WAL sidecars.

        The sidecars count because they hold committed data: right after an
        ingest the main file can still be nearly empty, and reporting that
        number would make the index look like it lost the corpus.
        """
        if self._in_memory:
            return 0
        total = 0
        for suffix in ("", "-wal", "-shm"):
            try:
                total += Path(f"{self.path}{suffix}").stat().st_size
            except OSError:
                continue  # not yet created, or already checkpointed away
        return total

    def stats(self) -> dict[str, Any]:
        """Counts, size on disk, and documents per source system."""
        conn = self._conn
        sources = {
            str(row[0]): int(row[1])
            for row in conn.execute(
                "SELECT source_system, COUNT(*) FROM documents "
                "GROUP BY source_system ORDER BY source_system"
            ).fetchall()
        }
        dim_row = conn.execute(
            "SELECT dim, COUNT(*) AS n FROM vectors GROUP BY dim ORDER BY n DESC LIMIT 1"
        ).fetchone()
        return {
            "path": str(self.path),
            "schema_version": self.schema_version,
            "documents": int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]),
            "chunks": int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]),
            "vectors": int(conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]),
            # The dominant width, so a caller can size a DenseIndex from the
            # store alone. Mixed widths mean two embedders got crossed.
            "vector_dim": int(dim_row[0]) if dim_row is not None else 0,
            "bytes": self._bytes_on_disk(),
            "sources": sources,
        }
