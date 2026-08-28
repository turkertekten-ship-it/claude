"""The index: documents, chunks, vectors and full-text search in one file.

SQLite rather than a vector database, for three reasons that hold at this scale:

* **One file.** The whole index is copyable, diffable in size, attachable to a
  CI artifact, and deletable. No server to run, no container to orchestrate.
* **FTS5 is already there.** A real BM25 implementation ships with the standard
  library's SQLite, which means the lexical half of hybrid retrieval costs no
  dependency and no second system to keep in sync with the first.
* **Transactional.** Documents, chunks and vectors update atomically. A crash
  mid-index leaves the previous consistent state rather than a half-migrated one
  that silently returns wrong results.

The one thing SQLite does not give is approximate nearest neighbour search, so
vectors are held in a flat in-memory index built from the same file. See
`store/vectors.py` for why flat is the right default here.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from oodarag.models import Chunk, Document
from oodarag.store.vectors import VectorIndex, pack, unpack
from oodarag.util.hashing import content_hash
from oodarag.util.logging import get_logger

log = get_logger("store")

SCHEMA_VERSION = 3

SCHEMA = """
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
    updated_at    REAL NOT NULL,
    indexed_at    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_system);
CREATE INDEX IF NOT EXISTS idx_documents_external ON documents(source_system, external_id);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id       TEXT PRIMARY KEY,
    doc_id         TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    ordinal        INTEGER NOT NULL,
    text           TEXT NOT NULL,
    context_header TEXT NOT NULL DEFAULT '',
    metadata       TEXT NOT NULL DEFAULT '{}',
    char_start     INTEGER NOT NULL DEFAULT 0,
    char_end       INTEGER NOT NULL DEFAULT 0,
    token_estimate INTEGER NOT NULL DEFAULT 0,
    content_hash   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id    TEXT PRIMARY KEY REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL,
    created_at  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embeddings_fingerprint ON embeddings(fingerprint);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle   INTEGER NOT NULL,
    phase   TEXT NOT NULL,
    ts      REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_journal_cycle ON journal(cycle);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, context_header, title,
    content='',
    -- Without this, a contentless FTS5 table cannot be deleted from by rowid;
    -- the only removal path is the 'delete' command supplied with the row's
    -- ORIGINAL column values, and getting that wrong deletes nothing silently.
    -- SQLite >= 3.43. _init_fts falls back for older builds.
    contentless_delete=1,
    -- Porter stemming wrapped around unicode61. Without it the lexical arm is
    -- exact-match only: a query for "abstain" never matches a document that
    -- says "abstained", and the dense arm has to carry the whole query alone.
    -- The dense arm's character n-grams partially cover this, but not in BM25,
    -- which is where exact-term questions are supposed to be answered.
    tokenize='porter unicode61 remove_diacritics 2'
);
"""


class SqliteStore:
    def __init__(self, path: str | Path = ".oodarag/index.db") -> None:
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript(SCHEMA)
        stored_version = self.get_meta("schema_version", 0)
        self.has_fts = self._init_fts(stored_version)
        self._vector_index: VectorIndex | None = None
        self._vector_fingerprint = ""
        self.set_meta("schema_version", SCHEMA_VERSION)

    def _init_fts(self, stored_version: int) -> bool:
        """FTS5 is present in every mainstream Python build, but not guaranteed.
        Without it the lexical arm falls back to a pure-Python BM25 over the
        chunk table, which is slower but keeps hybrid retrieval working rather
        than degrading to dense-only without saying so.

        A tokenizer change is invisible to `CREATE ... IF NOT EXISTS`: an index
        built under the old tokenizer keeps it silently, and half the corpus
        stems while the other half does not. So a schema bump rebuilds the FTS
        table from `chunks`, which is the authoritative copy.
        """
        try:
            if 0 < stored_version < SCHEMA_VERSION:
                log.info("rebuilding FTS index after schema change",
                         from_version=stored_version, to_version=SCHEMA_VERSION)
                self.conn.executescript("DROP TABLE IF EXISTS chunks_fts;")
            try:
                self.conn.executescript(FTS_SCHEMA)
                self.fts_rowid_delete = True
            except sqlite3.OperationalError:
                # SQLite < 3.43: no contentless_delete. Fall back to the
                # values-based delete command, which needs the original text.
                self.conn.executescript(
                    FTS_SCHEMA.replace("    contentless_delete=1,\n", ""))
                self.fts_rowid_delete = False
                log.info("FTS5 build lacks contentless_delete; using values-based deletes")
            if 0 < stored_version < SCHEMA_VERSION:
                self._rebuild_fts()
            return True
        except sqlite3.OperationalError as e:
            log.warn("FTS5 unavailable, lexical search will use the fallback", err=str(e))
            return False

    def _purge_fts(self, doc_id: str) -> None:
        """Remove a document's rows from the lexical index.

        This has to be exact. A contentless FTS5 table cannot be deleted from by
        rowid unless it was created with `contentless_delete=1`, and the
        `'delete'` command silently removes nothing unless it is handed the
        row's *original* column values. Getting it wrong leaves orphaned
        postings behind - and because SQLite reuses rowids, a later chunk
        inherits them: a query for a term that exists nowhere in the corpus
        returns a chunk that does not contain it, under that chunk's citation
        and URI. Deleted text stays retrievable under someone else's provenance.
        """
        if not self.has_fts:
            return
        rows = self.conn.execute(
            """SELECT c.rowid AS rid, c.text AS text, c.context_header AS hdr,
                      COALESCE(d.title, '') AS title
               FROM chunks c LEFT JOIN documents d ON d.doc_id = c.doc_id
               WHERE c.doc_id = ?""",
            (doc_id,),
        ).fetchall()
        if not rows:
            return
        if getattr(self, "fts_rowid_delete", False):
            self.conn.executemany("DELETE FROM chunks_fts WHERE rowid = ?",
                                  [(r["rid"],) for r in rows])
        else:
            self.conn.executemany(
                "INSERT INTO chunks_fts(chunks_fts, rowid, text, context_header, title) "
                "VALUES('delete', ?, ?, ?, ?)",
                [(r["rid"], r["text"], r["hdr"], r["title"]) for r in rows],
            )

    def _rebuild_fts(self) -> None:
        rows = self.conn.execute(
            """SELECT c.rowid, c.text, c.context_header, COALESCE(d.title, '')
               FROM chunks c LEFT JOIN documents d ON d.doc_id = c.doc_id"""
        ).fetchall()
        self.conn.executemany(
            "INSERT INTO chunks_fts(rowid, text, context_header, title) VALUES(?,?,?,?)",
            [tuple(r) for r in rows],
        )
        self.conn.commit()
        log.info("FTS index rebuilt", rows=len(rows))

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()

    def __enter__(self) -> "SqliteStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -------------------------------------------------------------------- meta

    def set_meta(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, default=str)),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    # --------------------------------------------------------------- documents

    def upsert_documents(self, docs: Iterable[Document]) -> int:
        now = time.time()
        rows = [
            (d.doc_id, d.source_system, d.external_id, d.uri, d.title, d.text,
             d.content_hash, json.dumps(d.metadata, default=str),
             d.created_at, d.updated_at, now)
            for d in docs
        ]
        if not rows:
            return 0
        self.conn.executemany(
            """INSERT INTO documents
               (doc_id, source_system, external_id, uri, title, text, content_hash,
                metadata, created_at, updated_at, indexed_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(doc_id) DO UPDATE SET
                 uri=excluded.uri, title=excluded.title, text=excluded.text,
                 content_hash=excluded.content_hash, metadata=excluded.metadata,
                 updated_at=excluded.updated_at, indexed_at=excluded.indexed_at""",
            rows,
        )
        self.conn.commit()
        return len(rows)

    def get_document(self, doc_id: str) -> Document | None:
        row = self.conn.execute("SELECT * FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        return _row_to_document(row) if row else None

    def get_documents(self, doc_ids: Sequence[str]) -> dict[str, Document]:
        if not doc_ids:
            return {}
        placeholders = ",".join("?" * len(doc_ids))
        rows = self.conn.execute(
            f"SELECT * FROM documents WHERE doc_id IN ({placeholders})", tuple(doc_ids)
        ).fetchall()
        return {row["doc_id"]: _row_to_document(row) for row in rows}

    def find_doc_ids(self, source_system: str, external_ids: Sequence[str]) -> dict[str, str]:
        """Map external ids to document ids, scoped to one source system.

        Scoped because external ids are only unique *within* a source: two
        connectors can legitimately both call a document "README.md", and an
        unscoped prune would delete the wrong one.
        """
        if not external_ids:
            return {}
        found: dict[str, str] = {}
        batch = 500  # stay well inside SQLite's variable limit
        for start in range(0, len(external_ids), batch):
            chunk = list(external_ids[start:start + batch])
            placeholders = ",".join("?" * len(chunk))
            rows = self.conn.execute(
                f"""SELECT doc_id, external_id FROM documents
                    WHERE source_system = ? AND external_id IN ({placeholders})""",
                (source_system, *chunk),
            ).fetchall()
            for row in rows:
                found[row["external_id"]] = row["doc_id"]
        return found

    def count_documents(self, source_system: str) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) AS n FROM documents WHERE source_system = ?", (source_system,)
        ).fetchone()["n"]

    def all_documents(self) -> list[Document]:
        return [_row_to_document(r) for r in self.conn.execute("SELECT * FROM documents")]

    def delete_document(self, doc_id: str) -> None:
        with self.conn:
            # Before the cascade drops the chunks, while their text is still
            # readable - the lexical index needs those values to purge itself.
            self._purge_fts(doc_id)
            self.conn.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))
        self._vector_index = None
        self._invalidate_idf()

    # ------------------------------------------------------------------ chunks

    def replace_chunks(self, doc_id: str, chunks: Sequence[Chunk]) -> int:
        """Replace a document's chunks atomically.

        Delete-then-insert inside one transaction, because a document that
        shrank must not keep its orphaned tail chunks: they would stay
        retrievable forever and cite text that no longer exists.
        """
        with self.conn:
            self._purge_fts(doc_id)
            self.conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            title = (self.conn.execute(
                "SELECT title FROM documents WHERE doc_id=?", (doc_id,)).fetchone() or {"title": ""}
            )["title"]
            for chunk in chunks:
                cursor = self.conn.execute(
                    """INSERT INTO chunks
                       (chunk_id, doc_id, ordinal, text, context_header, metadata,
                        char_start, char_end, token_estimate, content_hash)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (chunk.chunk_id, chunk.doc_id, chunk.ordinal, chunk.text,
                     chunk.context_header, json.dumps(chunk.metadata, default=str),
                     chunk.char_start, chunk.char_end, chunk.token_estimate,
                     chunk.content_hash),
                )
                if self.has_fts:
                    self.conn.execute(
                        "INSERT INTO chunks_fts(rowid, text, context_header, title) "
                        "VALUES(?,?,?,?)",
                        (cursor.lastrowid, chunk.text, chunk.context_header, title),
                    )
        self._vector_index = None
        self._invalidate_idf()
        return len(chunks)

    def get_chunks(self, chunk_ids: Sequence[str]) -> dict[str, Chunk]:
        if not chunk_ids:
            return {}
        placeholders = ",".join("?" * len(chunk_ids))
        rows = self.conn.execute(
            f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})", tuple(chunk_ids)
        ).fetchall()
        return {row["chunk_id"]: _row_to_chunk(row) for row in rows}

    def all_chunks(self) -> list[Chunk]:
        return [_row_to_chunk(r) for r in self.conn.execute("SELECT * FROM chunks ORDER BY doc_id, ordinal")]

    def chunk_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]

    # -------------------------------------------------------------- embeddings

    def upsert_embeddings(self, pairs: Iterable[tuple[str, Sequence[float]]],
                          fingerprint: str) -> int:
        now = time.time()
        rows = []
        for chunk_id, vector in pairs:
            rows.append((chunk_id, fingerprint, len(vector), pack(vector), now))
        if not rows:
            return 0
        self.conn.executemany(
            """INSERT INTO embeddings(chunk_id, fingerprint, dim, vector, created_at)
               VALUES(?,?,?,?,?)
               ON CONFLICT(chunk_id) DO UPDATE SET
                 fingerprint=excluded.fingerprint, dim=excluded.dim,
                 vector=excluded.vector, created_at=excluded.created_at""",
            rows,
        )
        self.conn.commit()
        self._vector_index = None
        return len(rows)

    def missing_embeddings(self, fingerprint: str) -> list[str]:
        """Chunks with no vector, or a vector from a different embedding space.

        The fingerprint check is what makes a model or dimension change safe:
        stale vectors are re-embedded rather than compared against new ones,
        which would produce plausible-looking nonsense.
        """
        rows = self.conn.execute(
            """SELECT c.chunk_id FROM chunks c
               LEFT JOIN embeddings e ON e.chunk_id = c.chunk_id
               WHERE e.chunk_id IS NULL OR e.fingerprint != ?""",
            (fingerprint,),
        ).fetchall()
        return [r["chunk_id"] for r in rows]

    def vector_index(self, fingerprint: str) -> VectorIndex:
        if self._vector_index is not None and self._vector_fingerprint == fingerprint:
            return self._vector_index
        rows = self.conn.execute(
            "SELECT chunk_id, dim, vector FROM embeddings WHERE fingerprint=?", (fingerprint,)
        ).fetchall()
        dim = rows[0]["dim"] if rows else 0
        index = VectorIndex(dim)
        for row in rows:
            if row["dim"] != dim:
                continue  # defensive: mixed dims cannot share an index
            index.add(row["chunk_id"], unpack(row["vector"]))
        self._vector_index = index
        self._vector_fingerprint = fingerprint
        log.debug("vector index built", vectors=len(index), dim=dim)
        return index

    # ---------------------------------------------------------------- lexical

    def search_lexical(self, query: str, k: int = 20,
                       allowed: set[str] | None = None) -> list[tuple[str, float]]:
        """BM25 over chunk text, context header and document title.

        Scores are negated because SQLite's `bm25()` returns lower-is-better;
        every other score in this pipeline is higher-is-better, and mixing the
        two conventions is a bug that hides until fusion silently inverts.
        """
        terms = _fts_query(query)
        if not terms:
            return []
        if self.has_fts:
            try:
                if allowed is None:
                    rows = self.conn.execute(
                        """SELECT c.chunk_id AS chunk_id,
                                  bm25(chunks_fts, 1.0, 0.6, 0.4) AS score
                           FROM chunks_fts
                           JOIN chunks c ON c.rowid = chunks_fts.rowid
                           WHERE chunks_fts MATCH ?
                           ORDER BY score LIMIT ?""",
                        (terms, k),
                    ).fetchall()
                else:
                    # Pre-filter in SQL via a temp table. Taking the global
                    # top-k*4 and intersecting afterwards is a post-filter, and
                    # it returns nothing whenever the allowed chunks rank below
                    # that window - which is the normal case when filtering to a
                    # small source inside a large corpus. Retrieval then
                    # silently degrades to dense-only.
                    self.conn.execute(
                        "CREATE TEMP TABLE IF NOT EXISTS _allowed(chunk_id TEXT PRIMARY KEY)")
                    self.conn.execute("DELETE FROM _allowed")
                    self.conn.executemany(
                        "INSERT OR IGNORE INTO _allowed(chunk_id) VALUES(?)",
                        [(cid,) for cid in allowed])
                    rows = self.conn.execute(
                        """SELECT c.chunk_id AS chunk_id,
                                  bm25(chunks_fts, 1.0, 0.6, 0.4) AS score
                           FROM chunks_fts
                           JOIN chunks c ON c.rowid = chunks_fts.rowid
                           JOIN _allowed a ON a.chunk_id = c.chunk_id
                           WHERE chunks_fts MATCH ?
                           ORDER BY score LIMIT ?""",
                        (terms, k),
                    ).fetchall()
            except sqlite3.OperationalError as e:
                log.warn("fts query failed, using fallback", err=str(e)[:120])
                return self._search_lexical_fallback(query, k, allowed)
            return [(r["chunk_id"], -float(r["score"])) for r in rows]
        return self._search_lexical_fallback(query, k, allowed)

    def _search_lexical_fallback(self, query: str, k: int,
                                 allowed: set[str] | None) -> list[tuple[str, float]]:
        """Pure-Python BM25. Only used when FTS5 is missing from the build."""
        import math
        from collections import Counter

        from oodarag.util.text import tokenize

        # Stemmed, so the fallback ranks the same documents FTS5 would.
        query_terms = tokenize(query, stem_words=True)
        if not query_terms:
            return []
        rows = self.conn.execute("SELECT chunk_id, text, context_header FROM chunks").fetchall()
        docs = [(r["chunk_id"],
                 tokenize(f"{r['context_header']} {r['text']}", stem_words=True))
                for r in rows]
        if allowed is not None:
            docs = [d for d in docs if d[0] in allowed]
        if not docs:
            return []
        n = len(docs)
        avg_len = sum(len(t) for _, t in docs) / n
        df: Counter[str] = Counter()
        for _, tokens in docs:
            for term in set(tokens):
                df[term] += 1
        k1, b = 1.5, 0.75
        scored: list[tuple[str, float]] = []
        for chunk_id, tokens in docs:
            counts = Counter(tokens)
            length = len(tokens) or 1
            score = 0.0
            for term in query_terms:
                if not (tf := counts.get(term, 0)):
                    continue
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / avg_len))
            if score > 0:
                scored.append((chunk_id, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]

    # ----------------------------------------------------------------- filters

    def filter_chunk_ids(self, filters: dict[str, Any] | None) -> set[str] | None:
        """Resolve metadata filters to a chunk-id set, or None for "no filter".

        Returning a set lets both retrieval arms pre-filter, which is the only
        way to guarantee k results after filtering.
        """
        if not filters:
            return None
        clauses: list[str] = []
        params: list[Any] = []
        for key, value in filters.items():
            if key == "source_system":
                if isinstance(value, (list, tuple, set)):
                    clauses.append(f"d.source_system IN ({','.join('?' * len(value))})")
                    params.extend(value)
                else:
                    clauses.append("d.source_system = ?")
                    params.append(value)
            elif key == "exclude_source_system":
                values = [value] if isinstance(value, str) else list(value)
                # An empty exclusion is no constraint. Emitting `NOT IN ()`
                # returns every chunk, which is the same *set* but not the same
                # thing: callers use `None` to mean "unfiltered" and skip work.
                if values:
                    clauses.append(
                        f"d.source_system NOT IN ({','.join('?' * len(values))})")
                    params.extend(values)
            elif key == "doc_ids":
                clauses.append(f"c.doc_id IN ({','.join('?' * len(value))})")
                params.extend(value)
            elif key == "exclude_doc_ids":
                values = list(value)
                if values:
                    clauses.append(f"c.doc_id NOT IN ({','.join('?' * len(values))})")
                    params.extend(values)
            elif key == "uri_prefix":
                clauses.append("d.uri LIKE ?")
                params.append(f"{value}%")
            elif key == "updated_after":
                clauses.append("d.updated_at >= ?")
                params.append(float(value))
            else:
                # Arbitrary metadata key on either the chunk or its document.
                clauses.append("(json_extract(c.metadata, ?) = ? OR json_extract(d.metadata, ?) = ?)")
                params.extend([f"$.{key}", value, f"$.{key}", value])
        if not clauses:
            # Every key resolved to "no constraint" (e.g. an empty exclusion
            # list). That is not the same as "match nothing", and it must not
            # build a WHERE with no predicate.
            return None
        sql = ("SELECT c.chunk_id FROM chunks c JOIN documents d ON d.doc_id = c.doc_id "
               f"WHERE {' AND '.join(clauses)}")
        return {r["chunk_id"] for r in self.conn.execute(sql, params)}

    # ----------------------------------------------------------------- journal

    def journal(self, cycle: int, phase: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO journal(cycle, phase, ts, payload) VALUES(?,?,?,?)",
            (cycle, phase, time.time(), json.dumps(payload, default=str)),
        )
        self.conn.commit()

    def read_journal(self, limit: int = 50, cycle: int | None = None) -> list[dict[str, Any]]:
        if cycle is None:
            rows = self.conn.execute(
                "SELECT * FROM journal ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM journal WHERE cycle=? ORDER BY id", (cycle,)).fetchall()
        return [{"id": r["id"], "cycle": r["cycle"], "phase": r["phase"],
                 "ts": r["ts"], **json.loads(r["payload"])} for r in rows]

    # --------------------------------------------------------------------- idf

    def idf_table(self) -> dict[str, float]:
        """Inverse document frequency over stemmed chunk terms.

        Used to weight relevance by how *informative* a term is. Unweighted term
        coverage treats every query word alike, so "what is the recommended
        dosage of ibuprofen" scores as 25% covered by any document containing
        the word "recommended" - and the abstention gate, which exists to catch
        exactly that question, lets it through. Weighted by IDF, the two terms
        that carry the question (ibuprofen, dosage) are the two that count.

        Cached against the chunk count: the table is a corpus property, and
        recomputing it per query would dominate retrieval latency.
        """
        import math
        from collections import Counter

        from oodarag.util.text import tokenize

        # Keyed on a content digest, not just the count. Re-indexing a document
        # with reworded text of the same chunk count leaves the count identical
        # while every term changes - and a stale table gives every term of the
        # new corpus the maximum idf, which feeds the reranker, the extractive
        # generator and the abstention gate.
        signature = self._corpus_signature()
        cached = self.get_meta("idf_table")
        if cached and cached.get("signature") == signature:
            return cached["table"]

        document_frequency: Counter[str] = Counter()
        rows = self.conn.execute("SELECT text, context_header FROM chunks").fetchall()
        for row in rows:
            for term in set(tokenize(f"{row['context_header']} {row['text']}", stem_words=True)):
                document_frequency[term] += 1
        total = max(1, len(rows))
        # Singletons are kept. Dropping them made a term appearing in exactly
        # one chunk indistinguishable from a term appearing nowhere - both fell
        # through to the "unseen" default - so an incidental word looked as
        # informative as one the corpus has never heard of, and the abstention
        # gate could not tell "rare" from "absent".
        table = {
            term: round(math.log(1.0 + (total - df + 0.5) / (df + 0.5)), 4)
            for term, df in document_frequency.items()
        }
        self.set_meta("idf_table", {"signature": signature, "table": table})
        log.debug("idf table built", terms=len(table), chunks=len(rows))
        return table

    def corpus_signature(self) -> str:
        """Content digest of the chunk corpus, for callers holding derived state.

        Anything computed from the corpus - an IDF table, a vocabulary, a fitted
        embedder - is stale the moment the corpus changes, and the change is
        invisible from outside. This is the cheap way to ask.
        """
        return self._corpus_signature()

    def _corpus_signature(self) -> str:
        """Cheap fingerprint of the chunk corpus: count plus a hash of hashes."""
        row = self.conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(group_concat(content_hash), '') AS h "
            "FROM (SELECT content_hash FROM chunks ORDER BY chunk_id)"
        ).fetchone()
        return f"{row['n']}:{content_hash(row['h'])}"

    def _invalidate_idf(self) -> None:
        self.conn.execute("DELETE FROM meta WHERE key='idf_table'")
        self.conn.commit()

    def vocabulary(self) -> set[str]:
        """Every stemmed term the corpus contains.

        A query term absent from this set is categorically different from a rare
        one: it is proof the corpus has never discussed the thing being asked
        about. See HeuristicReranker's answerability.
        """
        return set(self.idf_table())

    def term_frequency(self):
        """Callable giving a term's corpus-wide document frequency as a share.

        Used by expansion to measure lift: how much more common a term is in the
        feedback set than in the corpus at large. Selecting expansion terms on
        raw frequency picks the corpus's most common words, which are the least
        informative ones.
        """
        import math

        table = self.idf_table()
        total = max(1, self.chunk_count())

        def frequency(term: str) -> float:
            idf = table.get(term)
            if idf is None:
                return 0.0
            # Invert the BM25 idf used to build the table.
            value = math.exp(idf) - 1.0
            df = (total + 0.5 - 0.5 * value) / (value + 1.0)
            return max(0.0, min(1.0, df / total))

        return frequency

    def idf_lookup(self):
        """A callable returning the IDF of a stemmed term.

        An unseen term gets the maximum weight: a word absent from the entire
        corpus is the strongest possible evidence that the corpus does not cover
        the question containing it.
        """
        import math

        table = self.idf_table()
        total = max(1, self.chunk_count())
        maximum = math.log(1.0 + (total + 0.5) / 0.5)

        def idf(term: str) -> float:
            return table.get(term, maximum)

        return idf

    # ------------------------------------------------------------------- stats

    def stats(self) -> dict[str, Any]:
        cur = self.conn.execute
        by_source = {r["source_system"]: r["n"] for r in cur(
            "SELECT source_system, COUNT(*) AS n FROM documents GROUP BY source_system")}
        embedded = cur("SELECT COUNT(*) AS n FROM embeddings").fetchone()["n"]
        chunks = self.chunk_count()
        return {
            "documents": cur("SELECT COUNT(*) AS n FROM documents").fetchone()["n"],
            "chunks": chunks,
            "embeddings": embedded,
            "coverage": round(embedded / chunks, 4) if chunks else 0.0,
            "by_source": by_source,
            "fts": self.has_fts,
            "path": str(self.path),
            "size_bytes": self.path.stat().st_size if self.path.exists() else 0,
        }


def _fts_query(query: str) -> str:
    """Build a safe FTS5 MATCH expression.

    User text goes nowhere near the query grammar: every token is quoted, which
    neutralises the operators (`NEAR`, `*`, `-`, `"`) that would otherwise turn
    a question mark into a syntax error or a hyphen into a NOT.
    """
    from oodarag.util.text import tokenize

    # Unstemmed here on purpose: FTS5's porter tokenizer stems both sides of the
    # MATCH itself. Pre-stemming would double-stem the query.
    terms = tokenize(query)
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in dict.fromkeys(terms))


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
