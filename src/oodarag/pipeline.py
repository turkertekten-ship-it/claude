"""The indexing pipeline: connectors in, searchable index out.

    connectors -> RawDocument -> Document -> Chunk -> vector -> SQLite

Three properties this is built to guarantee:

**Idempotence.** Running it twice changes nothing. Connectors return only what
changed (content-hash incremental), chunks are replaced per document
transactionally, and embeddings are computed only for chunks whose vector is
missing or from a different embedding space.

**No silent partial index.** A connector that fails is recorded in the run
report with its error, not swallowed. The report is what the OODA loop observes.

**Embedding-space integrity.** The embedder's fingerprint is stored with every
vector and with the index itself. Change the model, the dimension or the corpus
statistics and the affected vectors are recomputed rather than silently compared
across incompatible spaces.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Sequence

from oodarag.chunking import ChunkConfig, chunk_document, summarize_chunking
from oodarag.embedding.base import Embedder
from oodarag.embedding.hashing import HashingEmbedder
from oodarag.ingest.base import Connector, SqliteStateStore, StateStore
from oodarag.models import Document, IngestDelta, RawDocument
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.logging import get_logger
from oodarag.util.text import clean, redact_secrets

log = get_logger("pipeline")


@dataclass
class IndexReport:
    documents_ingested: int = 0
    documents_indexed: int = 0
    chunks_written: int = 0
    vectors_written: int = 0
    deltas: list[IngestDelta] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_s: float = 0.0
    embedder_fingerprint: str = ""
    refit: bool = False
    chunking: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "documents_ingested": self.documents_ingested,
            "documents_indexed": self.documents_indexed,
            "chunks_written": self.chunks_written,
            "vectors_written": self.vectors_written,
            "deltas": [d.as_dict() for d in self.deltas],
            "errors": self.errors,
            "duration_s": round(self.duration_s, 2),
            "embedder_fingerprint": self.embedder_fingerprint,
            "refit": self.refit,
            "chunking": self.chunking,
        }


def normalize(raw: RawDocument) -> Document:
    """RawDocument -> Document: canonicalise text, redact, carry provenance.

    Redaction happens here as well as in the connectors - defence in depth. A
    connector is easy to add and easy to forget; this is the last point before
    text is written to a file that gets copied around.
    """
    text = redact_secrets(clean(raw.text))
    metadata = dict(raw.metadata)
    metadata.setdefault("fetched_at", raw.fetched_at)
    return Document.from_raw(raw, text, metadata)


class IndexPipeline:
    def __init__(self, store: SqliteStore, embedder: Embedder | None = None,
                 chunk_config: ChunkConfig | None = None,
                 state: StateStore | None = None) -> None:
        self.store = store
        self.embedder = embedder or HashingEmbedder()
        self.chunk_config = chunk_config or ChunkConfig()
        # Never None: a pipeline with no state store re-ingests the entire
        # corpus on every run and reports it all as new, which looks like
        # working software until the bill or the rate limit arrives.
        self.state = state or SqliteStateStore(store)
        self._restore_embedder_state()

    def _restore_embedder_state(self) -> None:
        saved = self.store.get_meta("embedder_state")
        if saved and saved.get("name") == self.embedder.name:
            self.embedder.load_state(saved.get("state", {}))
            log.debug("restored embedder state", fingerprint=self.embedder.fingerprint)

    # ------------------------------------------------------------------- run

    def run(self, connectors: Sequence[Connector], *, limit_per_source: int | None = None,
            refit: bool = False) -> IndexReport:
        started = time.monotonic()
        report = IndexReport()

        documents: list[Document] = []
        for connector in connectors:
            result = connector.run(self.state, limit=limit_per_source)
            report.deltas.append(result.delta)
            report.errors.extend(result.delta.errors)
            for raw in result.documents:
                try:
                    documents.append(normalize(raw))
                except Exception as e:
                    report.errors.append(f"normalize {raw.external_id}: {e}")
        report.documents_ingested = len(documents)

        if documents:
            report.documents_indexed = self.store.upsert_documents(documents)

        # Refit corpus statistics when the corpus has moved enough that the old
        # IDF table no longer describes it. Refitting invalidates every vector,
        # so it is a deliberate act, not a per-run default.
        indexed_docs = self.store.all_documents()
        if refit or self._should_refit(len(documents), len(indexed_docs)):
            self.embedder.fit([d.text for d in indexed_docs])
            self.store.set_meta("embedder_state",
                                {"name": self.embedder.name, "state": self.embedder.state()})
            report.refit = True
            log.info("refit embedder", docs=len(indexed_docs),
                     fingerprint=self.embedder.fingerprint)

        all_chunks = []
        for document in documents:
            chunks = chunk_document(document, self.chunk_config)
            self.store.replace_chunks(document.doc_id, chunks)
            report.chunks_written += len(chunks)
            all_chunks.extend(chunks)
        report.chunking = summarize_chunking(all_chunks)

        report.vectors_written = self.embed_missing()
        report.embedder_fingerprint = self.embedder.fingerprint
        self.store.set_meta("index_fingerprint", self.embedder.fingerprint)
        self.store.set_meta("last_index_run", time.time())
        report.duration_s = time.monotonic() - started

        log.info("index run complete", docs=report.documents_ingested,
                 chunks=report.chunks_written, vectors=report.vectors_written,
                 errors=len(report.errors), secs=round(report.duration_s, 2))
        return report

    def _should_refit(self, new_docs: int, total_docs: int) -> bool:
        if not total_docs:
            return False
        if not getattr(self.embedder, "fitted", True):
            return True   # never fitted: every term weighted equally
        fitted_on = self.store.get_meta("fitted_doc_count", 0)
        if not fitted_on:
            return True
        # 25% corpus growth is enough for the term distribution to have shifted.
        return (total_docs - fitted_on) / max(1, fitted_on) > 0.25

    def embed_missing(self, batch_size: int = 256) -> int:
        """Embed chunks with no vector, or a vector from another space."""
        fingerprint = self.embedder.fingerprint
        pending = self.store.missing_embeddings(fingerprint)
        if not pending:
            return 0
        written = 0
        for start in range(0, len(pending), batch_size):
            batch_ids = pending[start:start + batch_size]
            chunks = self.store.get_chunks(batch_ids)
            ordered = [chunks[cid] for cid in batch_ids if cid in chunks]
            if not ordered:
                continue
            vectors = self.embedder.embed_documents([c.indexed_text for c in ordered])
            written += self.store.upsert_embeddings(
                zip((c.chunk_id for c in ordered), vectors), fingerprint
            )
        self.store.set_meta("fitted_doc_count",
                            self.store.conn.execute(
                                "SELECT COUNT(*) AS n FROM documents").fetchone()["n"])
        log.info("embedded", vectors=written, fingerprint=fingerprint)
        return written

    def reindex_all(self) -> IndexReport:
        """Rechunk and re-embed everything already stored.

        Used after a chunking-config change, which the incremental path cannot
        detect: the source did not change, but what a chunk *is* did.
        """
        started = time.monotonic()
        report = IndexReport()
        documents = self.store.all_documents()
        self.embedder.fit([d.text for d in documents])
        self.store.set_meta("embedder_state",
                            {"name": self.embedder.name, "state": self.embedder.state()})
        report.refit = True
        all_chunks = []
        for document in documents:
            chunks = chunk_document(document, self.chunk_config)
            self.store.replace_chunks(document.doc_id, chunks)
            report.chunks_written += len(chunks)
            all_chunks.extend(chunks)
        report.chunking = summarize_chunking(all_chunks)
        report.documents_indexed = len(documents)
        report.vectors_written = self.embed_missing()
        report.embedder_fingerprint = self.embedder.fingerprint
        self.store.set_meta("index_fingerprint", self.embedder.fingerprint)
        report.duration_s = time.monotonic() - started
        return report
