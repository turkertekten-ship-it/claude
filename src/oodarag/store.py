"""Persistence: documents, chunks, their vectors, and a full-text index.

One SQLite file holds everything, which is a deliberate choice over a vector
service. The corpus this pipeline targets fits comfortably in a file, and a
file is copyable, diffable, inspectable with one import, and survives a
container being thrown away — none of which is true of a remote index. The
`sqlite3` module ships with Python and includes FTS5, so the lexical arm costs
no dependency either.

The lexical index is an FTS5 **external-content** table: the text lives once,
in `chunks`, and FTS5 stores only the inverted index over it. Without that, a
corpus is written to disk twice. Triggers keep the two in step, so there is no
code path that can insert a chunk and forget to index it.

`bm25()` in FTS5 returns a *negative* number where more negative is a better
match — the extension multiplies its score by -1 before returning it — so
ascending order is best-first. Scores are negated on the way out, so everything
downstream can assume higher-is-better, which is the convention the dense arm
and the fusion step share.

Two FTS5 properties worth knowing before tuning anything:

  - Its `k1` (1.2) and `b` (0.75) are **compiled in and not configurable**. A
    corpus that wants different saturation or length-normalisation cannot get
    it from this index; it needs its own scorer over the same postings.
  - Its IDF is the unsmoothed Robertson-Sparck-Jones form, which goes negative
    for a term appearing in more than about half the documents; FTS5 clamps it
    to 1e-6 rather than letting a common term subtract from a score. The
    practical consequence is that very common query terms contribute almost
    nothing, rather than contributing negatively — which is why the sanitizer
    below can safely OR every term together without weighting them.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oodarag.embed import Vector, pack, unpack
from oodarag.models import Chunk, Document
from oodarag.util.logging import get_logger

log = get_logger("store")

SCHEMA_VERSION = 1

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

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
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_system);
CREATE INDEX IF NOT EXISTS idx_documents_hash   ON documents(content_hash);

CREATE TABLE IF NOT EXISTS chunks (
    rowid          INTEGER PRIMARY KEY,
    chunk_id       TEXT UNIQUE NOT NULL,
    doc_id         TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    ordinal        INTEGER NOT NULL,
    text           TEXT NOT NULL,
    context_header TEXT NOT NULL DEFAULT '',
    indexed_text   TEXT NOT NULL,
    metadata       TEXT NOT NULL DEFAULT '{}',
    char_start     INTEGER NOT NULL DEFAULT 0,
    char_end       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_rowid INTEGER PRIMARY KEY REFERENCES chunks(rowid) ON DELETE CASCADE,
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    indexed_text,
    content='chunks',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, indexed_text) VALUES (new.rowid, new.indexed_text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, indexed_text)
    VALUES ('delete', old.rowid, old.indexed_text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, indexed_text)
    VALUES ('delete', old.rowid, old.indexed_text);
    INSERT INTO chunks_fts(rowid, indexed_text) VALUES (new.rowid, new.indexed_text);
END;
"""

# FTS5 treats these as query syntax. A user question is not a query expression,
# so they are stripped rather than escaped: a stray quote should not be a
# syntax error the caller has to handle.
_FTS_SPECIAL = re.compile(r'["*():^\-]|\bNOT\b|\bAND\b|\bOR\b|\bNEAR\b')


@dataclass(slots=True)
class LexicalHit:
    chunk_rowid: int
    chunk_id: str
    score: float  # higher is better, already sign-corrected


class Store:
    """A SQLite-backed corpus. Safe to open repeatedly; schema is idempotent."""

    def __init__(self, path: str | Path = ".oodarag/corpus.db") -> None:
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------- documents

    def upsert_document(self, doc: Document) -> bool:
        """Insert or update. Returns True when the stored text actually changed.

        The return value is what lets the caller skip re-chunking and
        re-embedding an unchanged document, which is the single largest saving
        in an incremental run.
        """
        row = self.conn.execute(
            "SELECT content_hash FROM documents WHERE doc_id = ?", (doc.doc_id,)
        ).fetchone()
        if row and row["content_hash"] == doc.content_hash:
            return False

        self.conn.execute(
            """INSERT INTO documents
               (doc_id, source_system, external_id, uri, title, text, content_hash,
                metadata, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(doc_id) DO UPDATE SET
                 uri=excluded.uri, title=excluded.title, text=excluded.text,
                 content_hash=excluded.content_hash, metadata=excluded.metadata,
                 updated_at=excluded.updated_at""",
            (doc.doc_id, doc.source_system, doc.external_id, doc.uri, doc.title,
             doc.text, doc.content_hash, json.dumps(doc.metadata, default=str),
             doc.created_at, doc.updated_at),
        )
        # A changed document's old chunks are stale by definition. Deleting
        # them here (rather than leaving them for a sweep) is what stops a
        # shrinking document from leaving orphaned passages retrievable.
        self.conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.doc_id,))
        self.conn.commit()
        return True

    def get_document(self, doc_id: str) -> Document | None:
        row = self.conn.execute(
            "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        return _row_to_document(row) if row else None

    def documents(self) -> list[Document]:
        return [_row_to_document(r) for r in self.conn.execute("SELECT * FROM documents")]

    def delete_document(self, doc_id: str) -> None:
        self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.commit()

    # ---------------------------------------------------------------- chunks

    def add_chunks(self, chunks: Iterable[Chunk], vectors: list[Vector] | None = None) -> int:
        """Store chunks and, optionally, their vectors in one transaction."""
        chunks = list(chunks)
        if not chunks:
            return 0
        if vectors is not None and len(vectors) != len(chunks):
            raise ValueError(
                f"vector count {len(vectors)} does not match chunk count {len(chunks)}"
            )

        with self.conn:  # one transaction: chunks and vectors land together
            for i, chunk in enumerate(chunks):
                cur = self.conn.execute(
                    """INSERT INTO chunks
                       (chunk_id, doc_id, ordinal, text, context_header, indexed_text,
                        metadata, char_start, char_end)
                       VALUES (?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(chunk_id) DO UPDATE SET
                         text=excluded.text, indexed_text=excluded.indexed_text,
                         metadata=excluded.metadata""",
                    (chunk.chunk_id, chunk.doc_id, chunk.ordinal, chunk.text,
                     chunk.context_header, chunk.indexed_text,
                     json.dumps(chunk.metadata, default=str),
                     chunk.char_start, chunk.char_end),
                )
                rowid = cur.lastrowid
                if not rowid:
                    got = self.conn.execute(
                        "SELECT rowid FROM chunks WHERE chunk_id = ?", (chunk.chunk_id,)
                    ).fetchone()
                    rowid = got["rowid"] if got else None
                if rowid and vectors is not None:
                    vec = vectors[i]
                    self.conn.execute(
                        "INSERT OR REPLACE INTO embeddings(chunk_rowid, dim, vector) "
                        "VALUES (?,?,?)",
                        (rowid, len(vec), pack(vec)),
                    )
        return len(chunks)

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        row = self.conn.execute(
            "SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)
        ).fetchone()
        return _row_to_chunk(row) if row else None

    def chunks_by_rowids(self, rowids: list[int]) -> dict[int, Chunk]:
        if not rowids:
            return {}
        marks = ",".join("?" * len(rowids))
        rows = self.conn.execute(
            f"SELECT * FROM chunks WHERE rowid IN ({marks})", rowids
        ).fetchall()
        return {r["rowid"]: _row_to_chunk(r) for r in rows}

    def iter_vectors(self) -> Iterable[tuple[int, str, Vector]]:
        """Stream every stored vector.

        Streaming rather than returning a list keeps peak memory proportional
        to one vector, which is what makes brute-force dense scoring viable on
        a corpus far larger than the machine's comfortable working set.
        """
        sql = ("SELECT e.chunk_rowid AS rowid, c.chunk_id AS chunk_id, e.vector AS vector "
               "FROM embeddings e JOIN chunks c ON c.rowid = e.chunk_rowid")
        with closing(self.conn.execute(sql)) as cur:
            for row in cur:
                yield row["rowid"], row["chunk_id"], unpack(row["vector"])

    # --------------------------------------------------------------- lexical

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Turn a natural-language question into a safe FTS5 MATCH expression."""
        cleaned = _FTS_SPECIAL.sub(" ", query)
        terms = [t for t in cleaned.split() if t.strip()]
        return " OR ".join(f'"{t}"' for t in terms)

    def search_lexical(self, query: str, k: int = 50) -> list[LexicalHit]:
        """BM25 search. Returns higher-is-better scores, best first."""
        expr = self.sanitize_query(query)
        if not expr:
            return []
        try:
            # `ORDER BY rank` is the documented fast path: `rank` is `bm25()`
            # with no arguments, and FTS5 optimises the sort — materially so
            # with a LIMIT, which is always present here. Ordering by the
            # `bm25(...)` call instead forces the score for every match.
            rows = self.conn.execute(
                """SELECT c.rowid AS rowid, c.chunk_id AS chunk_id, bm25(chunks_fts) AS score
                   FROM chunks_fts JOIN chunks c ON c.rowid = chunks_fts.rowid
                   WHERE chunks_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (expr, k),
            ).fetchall()
        except sqlite3.OperationalError as e:
            # A malformed MATCH expression is a bug in sanitize_query, not a
            # reason to fail the whole query: the dense arm can still answer.
            log.warn("lexical search failed", err=str(e), expr=expr[:120])
            return []
        return [LexicalHit(r["rowid"], r["chunk_id"], -float(r["score"])) for r in rows]

    # ----------------------------------------------------------------- stats

    def stats(self) -> dict[str, Any]:
        one = lambda sql: self.conn.execute(sql).fetchone()[0]  # noqa: E731
        by_source = {
            r["source_system"]: r["n"]
            for r in self.conn.execute(
                "SELECT source_system, COUNT(*) AS n FROM documents GROUP BY source_system"
            )
        }
        return {
            "documents": one("SELECT COUNT(*) FROM documents"),
            "chunks": one("SELECT COUNT(*) FROM chunks"),
            "embeddings": one("SELECT COUNT(*) FROM embeddings"),
            "by_source": by_source,
            "path": str(self.path),
            "schema_version": SCHEMA_VERSION,
        }


def _row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        doc_id=row["doc_id"], source_system=row["source_system"],
        external_id=row["external_id"], uri=row["uri"], title=row["title"],
        text=row["text"], content_hash=row["content_hash"],
        metadata=json.loads(row["metadata"]),
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def _row_to_chunk(row: sqlite3.Row) -> Chunk:
    return Chunk(
        chunk_id=row["chunk_id"], doc_id=row["doc_id"], ordinal=row["ordinal"],
        text=row["text"], context_header=row["context_header"],
        metadata=json.loads(row["metadata"]),
        char_start=row["char_start"], char_end=row["char_end"],
    )
