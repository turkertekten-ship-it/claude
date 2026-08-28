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
class PruneReport:
    """What a prune did, or refused to do, per source."""

    deleted: int = 0
    skipped: int = 0
    refused: list[str] = field(default_factory=list)
    per_source: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"deleted": self.deleted, "skipped": self.skipped,
                "refused": self.refused, "per_source": self.per_source}


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
            self._reconcile_cursor(connector)
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
        indexed_bytes = sum(len(d.text) for d in indexed_docs)
        if refit or self._should_refit(len(documents), len(indexed_docs), indexed_bytes):
            self.embedder.fit([d.text for d in indexed_docs])
            self.store.set_meta("embedder_state",
                                {"name": self.embedder.name, "state": self.embedder.state()})
            # Recorded here, at the fit, and nowhere else. Writing it after every
            # embedding pass measured growth against the last *run* rather than
            # the last *fit*, so growth never accumulated: a corpus growing in
            # increments below the threshold grew without bound while the term
            # statistics stayed fitted on the original documents, and the OODA
            # loop's REFIT_EMBEDDER rule could never fire either.
            self.store.set_meta("fitted_doc_count", len(indexed_docs))
            self.store.set_meta("fitted_text_bytes",
                                sum(len(d.text) for d in indexed_docs))
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

    def _reconcile_cursor(self, connector: Connector) -> None:
        """Drop cursor entries for documents the index does not actually have.

        Incremental ingest decides "unchanged, skip" from the cursor alone. If
        the index is rebuilt, restored from an older copy, or partly pruned
        while the cursor survives, every one of those documents is reported
        unchanged and never re-added - and the result is an index that is
        silently missing most of its corpus while every counter reads zero
        errors. Deleting an index and re-running produced 19 documents out of
        33, and the only visible symptom was the eval score halving.

        The cursor is not the authority on what the index contains; the index
        is. Anything the cursor claims and the store lacks is re-fetched.
        """
        if self.state is None or not connector.source_system:
            return
        cursor = self.state.get(connector.key)
        hashes = cursor.get("hashes") or {}
        if not hashes:
            return
        present = self.store.find_doc_ids(connector.source_system, list(hashes))
        missing = [external_id for external_id in hashes if external_id not in present]
        if not missing:
            return
        for external_id in missing:
            hashes.pop(external_id, None)
        cursor["hashes"] = hashes
        self.state.set(connector.key, cursor)
        log.warn("cursor referenced documents missing from the index; they will be "
                 "re-fetched", source=connector.key, missing=len(missing))

    def _should_refit(self, new_docs: int, total_docs: int,
                      total_bytes: int = 0) -> bool:
        if not total_docs:
            return False
        if not getattr(self.embedder, "fitted", True):
            return True   # never fitted: every term weighted equally
        fitted_on = self.store.get_meta("fitted_doc_count", 0)
        if not fitted_on:
            return True
        # 25% corpus growth is enough for the term distribution to have shifted.
        if (total_docs - fitted_on) / max(1, fitted_on) > 0.25:
            return True
        # Document count alone cannot see a corpus rewritten in place. Removing
        # the site template from the 33-page external corpus deleted 90.9% of
        # its text and left the count at 33, so no refit fired and the embedder
        # stayed fitted on a term distribution that no longer existed. The same
        # corpus then scored recall 1.0 through the incremental path and 0.9821
        # rebuilt from scratch - identical inputs, different answers, no error.
        # This is the reasoning idf_table already applies to itself.
        fitted_bytes = self.store.get_meta("fitted_text_bytes", 0)
        if fitted_bytes and total_bytes:
            # Symmetric: a corpus that shrinks by 25% has moved as far as one
            # that grows by 25%, and only the growth case was ever checked.
            return abs(total_bytes - fitted_bytes) / fitted_bytes > 0.25
        return False

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
        log.info("embedded", vectors=written, fingerprint=fingerprint)
        return written

    def prune(self, deltas: Sequence[IngestDelta],
              max_removal_fraction: float = 0.25) -> PruneReport:
        """Delete documents their source no longer has.

        Without this, a document removed upstream stays in the index and stays
        citable for ever - an answer quoting text that no longer exists, with a
        URI that no longer resolves. That is the same class of failure as a
        stale lexical posting, one level up.

        The guard is the reason this is not automatic. A source can return
        nothing for reasons that have nothing to do with deletion: an expired
        token, a truncated listing, a path that is temporarily unmounted. Acting
        on that would empty the index in one run, and the next successful run
        would silently re-fetch everything as new. So a removal set larger than
        `max_removal_fraction` of the source is refused and reported, and a
        connector that failed at all contributes no removals in the first place.
        """
        report = PruneReport()
        for delta in deltas:
            if not delta.removed:
                continue
            system = delta.source_system
            if not system:
                report.refused.append(
                    f"{delta.source_key}: connector reports no source_system; cannot scope a prune")
                report.skipped += len(delta.removed)
                continue
            total = self.store.count_documents(system)
            fraction = len(delta.removed) / total if total else 1.0
            if fraction > max_removal_fraction:
                report.refused.append(
                    f"{delta.source_key}: {len(delta.removed)}/{total} documents "
                    f"({fraction:.0%}) disappeared at once, above the "
                    f"{max_removal_fraction:.0%} guard - not pruning. If this is a real "
                    f"bulk deletion, prune explicitly."
                )
                report.skipped += len(delta.removed)
                log.warn("prune refused", source=delta.source_key,
                         removed=len(delta.removed), total=total)
                continue
            found = self.store.find_doc_ids(system, delta.removed)
            for doc_id in found.values():
                self.store.delete_document(doc_id)
            report.deleted += len(found)
            report.per_source[delta.source_key] = len(found)
            log.info("pruned removed documents", source=delta.source_key,
                     deleted=len(found), reported=len(delta.removed))
        return report

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
        self.store.set_meta("fitted_doc_count", len(documents))
        self.store.set_meta("fitted_text_bytes", sum(len(d.text) for d in documents))
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
