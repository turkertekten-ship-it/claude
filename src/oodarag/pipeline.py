"""Wire the stages together: connector -> store -> chunk -> embed -> index.

The one rule this module enforces is that **unchanged documents cost nothing**.
A connector reports new, changed and unchanged; only the first two are chunked
and embedded. Re-embedding an unchanged corpus is the single largest waste in a
naive pipeline, and it is invisible — the run simply takes longer every time
until someone profiles it.

Failures are collected rather than raised. One connector being unreachable is
information about that connector, not a reason to abandon the other five and
leave the index in whatever half-state the exception interrupted.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from oodarag.chunk import ChunkConfig, chunk_document
from oodarag.embed import Embedder, HashingEmbedder
from oodarag.generate import ExtractiveGenerator, Generator
from oodarag.ingest.base import Connector, StateStore
from oodarag.models import Answer, Document, IngestDelta
from oodarag.retrieve import RetrievalConfig, Retriever
from oodarag.store import Store
from oodarag.util.logging import get_logger

log = get_logger("pipeline")


@dataclass(slots=True)
class IngestReport:
    """What a whole ingest run did, per source."""

    deltas: list[IngestDelta] = field(default_factory=list)
    chunks_written: int = 0
    documents_changed: int = 0
    duration_s: float = 0.0
    unreachable: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(d.failed for d in self.deltas)

    def as_dict(self) -> dict[str, Any]:
        return {
            "sources": [d.as_dict() for d in self.deltas],
            "documents_changed": self.documents_changed,
            "chunks_written": self.chunks_written,
            "unreachable": self.unreachable,
            "duration_s": round(self.duration_s, 3),
        }

    def render(self) -> str:
        lines = [f"{'SOURCE':<34} {'NEW':>5} {'CHG':>5} {'SAME':>5} {'FAIL':>5}"]
        lines.append("-" * 62)
        for d in self.deltas:
            lines.append(
                f"{d.source_key[:34]:<34} {d.new:>5} {d.changed:>5} "
                f"{d.unchanged:>5} {d.failed:>5}"
            )
            for err in d.errors[:3]:
                lines.append(f"    ! {err[:100]}")
        lines.append("-" * 62)
        lines.append(
            f"{self.documents_changed} document(s) changed, "
            f"{self.chunks_written} chunk(s) written in {self.duration_s:.2f}s"
        )
        for key, reason in self.unreachable.items():
            lines.append(f"  unreachable: {key}: {reason}")
        return "\n".join(lines)


class Pipeline:
    """The end-to-end pipeline over one `Store`."""

    def __init__(
        self,
        store: Store,
        *,
        embedder: Embedder | None = None,
        chunk_config: ChunkConfig | None = None,
        retrieval_config: RetrievalConfig | None = None,
        generator: Generator | None = None,
    ) -> None:
        self.store = store
        self.embedder = embedder or HashingEmbedder()
        self.chunk_config = chunk_config or ChunkConfig()
        self.retriever = Retriever(store, self.embedder, retrieval_config)
        self.generator = generator or ExtractiveGenerator()

    # ---------------------------------------------------------------- ingest

    def ingest(
        self,
        connectors: list[Connector],
        *,
        state: StateStore | None = None,
        limit: int | None = None,
    ) -> IngestReport:
        """Run every connector and index what changed."""
        started = time.monotonic()
        report = IngestReport()

        for connector in connectors:
            try:
                result = connector.run(state=state, limit=limit)
            except Exception as e:
                # `Connector.run` already absorbs per-document and per-source
                # failures; reaching here means the connector object itself is
                # broken, which is still not a reason to skip the others.
                report.unreachable[connector.key] = f"{type(e).__name__}: {e}"
                log.error("connector aborted", key=connector.key, err=str(e)[:200])
                continue

            report.deltas.append(result.delta)
            if result.delta.errors:
                report.unreachable.setdefault(connector.key, result.delta.errors[0])

            authority = getattr(connector, "authority", 1.0)
            self.retriever.config.source_authority.setdefault(
                _source_of(result), authority
            )

            for raw in result.documents:
                doc = Document.from_raw(raw, raw.text, dict(raw.metadata))
                if not self.store.upsert_document(doc):
                    continue
                report.documents_changed += 1
                report.chunks_written += self._index_document(doc)

        report.duration_s = time.monotonic() - started
        log.info("ingest complete", **{k: v for k, v in report.as_dict().items()
                                       if k != "sources"})
        return report

    def _index_document(self, doc: Document) -> int:
        """Chunk, embed and store one document. Returns the chunk count."""
        chunks = chunk_document(doc, self.chunk_config)
        if not chunks:
            return 0
        vectors = self.embedder.embed_batch([c.indexed_text for c in chunks])
        return self.store.add_chunks(chunks, vectors)

    def reindex(self) -> int:
        """Re-chunk and re-embed every stored document.

        Needed after a change to chunking or to the embedder: the stored
        vectors were produced by the old configuration and comparing them with
        new query vectors silently degrades every result.
        """
        total = 0
        for doc in self.store.documents():
            self.store.conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.doc_id,))
            self.store.conn.commit()
            total += self._index_document(doc)
        log.info("reindex complete", chunks=total)
        return total

    # ----------------------------------------------------------------- query

    def query(self, question: str, k: int | None = None) -> Answer:
        hits = self.retriever.search(question, k)
        return self.generator.generate(question, hits)

    def stats(self) -> dict[str, Any]:
        return self.store.stats()


def _source_of(result: Any) -> str:
    docs = getattr(result, "documents", None) or []
    return docs[0].source_system if docs else ""
