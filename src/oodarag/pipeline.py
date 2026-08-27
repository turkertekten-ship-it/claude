"""The wiring layer: one object that owns the handles every entry point needs.

Every stage in this package is independently constructible, which is what makes
each one testable on its own - and it is also three chances to assemble them
differently, because the CLI, the eval harness and the OODA loop all need the
same assembly. Three slightly different assemblies of the same stages give three
different answers to the same question with nothing to indicate which is the
bug. So the assembly exists once, here, and the entry points own none of it.

The parts of that job that are easy to get wrong, and how they are handled:

**Index handles are refilled, never rebound.** `HybridRetriever` holds
references to a `BM25Index` and a `DenseIndex`. Rebinding `self.bm25` to a
freshly built index after an ingest would leave the retriever querying the old
one forever, and stale-but-plausible answers are the hardest kind of wrong to
notice. Both indexes are therefore constructed empty in `__init__` and refilled
through `.build()`, which replaces their contents behind a stable identity.

**Writes mark the indexes stale; they do not rebuild them.** Ingesting ten
connectors would otherwise pay for ten full rebuilds of a corpus that is only
queried at the end. `ask()` rebuilds on demand, once.

**The cache is consulted here, not only inside the embedder.** The embedder is
already cache-aware, so this looks redundant - it is not. Doing the lookup at
this level is what lets an unchanged corpus report *why* re-indexing was free
(a hit rate in the log) rather than merely being fast for unexplained reasons,
and it collapses chunks that share content within a single batch, which the
per-text path inside the embedder cannot see.

**`close()` is not the end of the object.** It flushes and releases the sqlite
connection, and the next call that needs the store reopens it. A pipeline used
inside `with` in one function and again in the next is a completely reasonable
thing for a caller to do; making that an error would buy nothing.

Errors from one connector are counted into that connector's `IngestDelta` and
never propagated: an ingest of eight sources where one host is down is a
seven-source ingest with a recorded failure, not a crash.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.chunk import ChunkConfig, Chunker
from oodarag.embed.base import EmbeddingCache
from oodarag.embed.hashing import HashingEmbedder
from oodarag.generate import ExtractiveGenerator, GenerationConfig
from oodarag.index.bm25 import BM25Index
from oodarag.index.dense import DenseIndex
from oodarag.index.store import Store
from oodarag.ingest.base import Connector, JsonStateStore
from oodarag.models import Answer, Chunk, Document, IngestDelta, RawDocument
from oodarag.normalize import Normalizer
from oodarag.rerank import Reranker, RerankConfig
from oodarag.retrieve import HybridRetriever, RetrievalConfig
from oodarag.util.logging import get_logger

log = get_logger("pipeline")

#: Candidates handed to the reranker per result finally returned. MMR can only
#: drop a near-duplicate if it has something to promote in its place: with a
#: pool the size of `k` the rerank degenerates into a reordering of a fixed set,
#: and the diversity term stops being able to change the answer at all.
RERANK_POOL_FACTOR = 3

#: Error strings kept per connector run. A source that fails on every one of
#: 4,000 documents is fully described by the first twenty; keeping them all
#: turns the delta - which the OODA loop serializes into its cycle report -
#: into megabytes of the same sentence.
MAX_ERRORS_KEPT = 20


@dataclass(slots=True)
class PipelineConfig:
    """Where the pipeline's state lives, and how each stage is tuned.

    One `root` rather than three paths because the index, the embedding cache
    and the connector cursors are a single unit of state: an index restored from
    a backup without the cursors that produced it would report every document as
    new, and a cache from a different root is keyed by a model name that says
    nothing about which corpus it came from. Deleting the directory is the
    supported way to start over, and it has to be one directory for that to be
    true.
    """

    root: Path = Path(".oodarag")
    embed_dim: int = 512
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    @property
    def db_path(self) -> Path:
        return Path(self.root) / "index.db"

    @property
    def cache_path(self) -> Path:
        return Path(self.root) / "embeddings.json"

    @property
    def state_path(self) -> Path:
        return Path(self.root) / "state.json"


@dataclass(slots=True)
class _IndexOutcome:
    """Counts plus the error strings behind them.

    `index_documents` returns `dict[str, int]` by contract, which is the right
    shape for a caller printing a summary and the wrong shape for `ingest`,
    which has to fold the failures into an `IngestDelta` with their messages
    intact. The internal path returns this; the public one returns `counts()`.
    """

    documents: int = 0
    chunks: int = 0
    embedded: int = 0
    reused: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "documents": self.documents,
            "chunks": self.chunks,
            "embedded": self.embedded,
            "reused": self.reused,
            "failed": self.failed,
        }


class Pipeline:
    """Wires the stages together and owns the store handles."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self.root = Path(self.config.root)
        self.root.mkdir(parents=True, exist_ok=True)

        # Stateless stages, built once: they hold configuration and counters,
        # never a file handle, so they survive a close/reopen untouched.
        self.normalizer = Normalizer()
        self.chunker = Chunker(self.config.chunk)
        self.cache = EmbeddingCache(self.config.cache_path)
        self.embedder = HashingEmbedder(self.config.embed_dim, cache=self.cache)
        self.reranker = Reranker(self.embedder, self.config.rerank)
        self.generator = ExtractiveGenerator(self.config.generation)
        self.state = JsonStateStore(self.config.state_path)

        # Empty and cheap; filled by `refresh_indexes` on first use. The dense
        # index takes its width from the embedder rather than from the config so
        # the two can never disagree about what a vector is.
        self.bm25 = BM25Index()
        self.dense = DenseIndex(self.embedder.dim)
        self._indexes_built = False

        self._closed = True  # `_open` is the single place that flips this
        self.store: Store
        self.retriever: HybridRetriever
        self._open()
        log.info(
            "pipeline ready",
            root=str(self.root), embedder=self.embedder.name, dim=self.embedder.dim,
        )

    # ---- lifecycle -------------------------------------------------------

    def _open(self) -> None:
        """Open the store and bind a retriever to it."""
        self.store = Store(self.config.db_path)
        self.retriever = HybridRetriever(
            self.store, self.embedder, self.bm25, self.dense, self.config.retrieval
        )
        self._closed = False

    def _ensure_open(self) -> None:
        if not self._closed:
            return
        self._open()
        # Anything could have written the database while it was closed - that is
        # the whole reason a process closes one. The in-memory indexes are no
        # longer known to describe it, so they are stale by definition.
        self._indexes_built = False
        log.info("pipeline reopened", root=str(self.root))

    def close(self) -> None:
        """Flush the embedding cache and release the store. Idempotent.

        The cache is flushed first and in a `finally`, because the two failures
        are asymmetric: an unflushed cache costs a re-embed on the next run,
        while an unclosed sqlite connection leaks a file descriptor and leaves
        the WAL uncheckpointed for whoever opens the index next.
        """
        if self._closed:
            return
        self._closed = True
        try:
            self.cache.flush()
        finally:
            self.store.close()
        log.debug("pipeline closed", root=str(self.root))

    def __enter__(self) -> Pipeline:
        self._ensure_open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---- ingest ----------------------------------------------------------

    def ingest(self, connectors: Sequence[Connector]) -> list[IngestDelta]:
        """Run every connector, index what it produced, return one delta each.

        A connector is isolated twice over: `Connector.run` already counts its
        own fetch failures into the delta it returns, and everything downstream
        of it here is wrapped as well. The list that comes back therefore always
        has one entry per connector, in the order given, whether that connector
        returned four thousand documents or could not resolve its own hostname.
        """
        self._ensure_open()
        deltas: list[IngestDelta] = []

        for connector in connectors:
            started = time.perf_counter()
            key = getattr(connector, "key", type(connector).__name__)
            delta = IngestDelta(source_key=key)
            try:
                result = connector.run(self.state)
                delta = result.delta
                docs = self._normalize(result.documents, connector)
                outcome = self._index_documents(docs)
                delta.failed += outcome.failed
                _extend_capped(delta.errors, outcome.errors)
            except Exception as e:  # one dead source must not stop the others
                delta.failed += 1
                _extend_capped(delta.errors, [f"{key}: {type(e).__name__}: {e}"])
                log.error("ingest failed", key=key, err=f"{type(e).__name__}: {e}"[:300])
            # Overwrites the fetch-only duration the connector measured: from the
            # loop's point of view a source costs what it costs to make it
            # answerable, and fetch is usually the smaller half of that.
            delta.duration_s = round(time.perf_counter() - started, 3)
            deltas.append(delta)

        log.info(
            "ingest complete",
            sources=len(deltas),
            touched=sum(d.touched for d in deltas),
            failed=sum(d.failed for d in deltas),
        )
        return deltas

    def index_documents(self, docs: Sequence[Document]) -> dict[str, int]:
        """Chunk, embed and store already-normalized documents.

        Separate from `ingest` because it is the seam every other producer of
        documents needs: the offline demo corpus, a test fixture, a backfill of
        one document that a loop decided to re-chunk.
        """
        self._ensure_open()
        return self._index_documents(docs).counts()

    def _normalize(self, raws: Sequence[RawDocument], connector: Connector) -> list[Document]:
        """Normalize one connector's batch, defaulting its declared authority.

        The built-in connectors already stamp `authority` into each document's
        metadata, but it is declared on the connector class, so a third-party
        connector that sets the attribute and forgets the metadata would silently
        be treated as ordinary. `setdefault`, not assignment: a document that
        states its own authority outranks its connector's blanket claim.

        Dedupe scope is deliberately one connector's batch and not the whole run.
        Cross-connector dedupe would drop the second source's copy, and because
        connectors are incremental that copy is never offered again - the losing
        source would be permanently missing a document it really does have.
        """
        authority = float(getattr(connector, "authority", 1.0))
        for raw in raws:
            raw.metadata.setdefault("authority", authority)
        docs, report = self.normalizer.normalize_all(raws)
        if report.seen != report.kept:
            log.info("normalized", key=getattr(connector, "key", "?"), **report.as_dict())
        return docs

    def _index_documents(self, docs: Sequence[Document]) -> _IndexOutcome:
        outcome = _IndexOutcome()
        if not docs:
            return outcome

        # Documents first: `replace_document_chunks` writes rows whose foreign
        # key points at the document, so a chunk written before its document
        # would be rejected wholesale.
        outcome.documents = self.store.upsert_documents(docs)

        by_doc: dict[str, list[Chunk]] = {}
        for doc in docs:
            try:
                by_doc[doc.doc_id] = self.chunker.chunk(doc)
            except Exception as e:  # one pathological document
                outcome.failed += 1
                outcome.errors.append(f"chunk {doc.doc_id}: {type(e).__name__}: {e}")
                log.error("chunking failed", doc=doc.doc_id, err=f"{type(e).__name__}: {e}"[:200])

        chunks = [c for group in by_doc.values() for c in group]
        outcome.chunks = len(chunks)
        vectors, outcome.embedded, outcome.reused = self._embed(chunks)

        for doc_id, group in by_doc.items():
            try:
                # Called even when `group` is empty, on purpose: that is a
                # document whose text no longer chunks (emptied, truncated,
                # replaced by a redirect stub), and the delete half of the swap
                # is what keeps its previous chunks from answering questions
                # about content that is gone.
                self.store.replace_document_chunks(doc_id, group, vectors)
            except Exception as e:  # one document's write
                outcome.failed += 1
                outcome.errors.append(f"store {doc_id}: {type(e).__name__}: {e}")
                log.error("chunk write failed", doc=doc_id, err=f"{type(e).__name__}: {e}"[:200])

        self.cache.flush()
        self._indexes_built = False  # the store moved; the indexes describe the past
        log.info("indexed documents", **outcome.counts())
        return outcome

    def _embed(self, chunks: Sequence[Chunk]) -> tuple[dict[str, list[float]], int, int]:
        """Vectors keyed by chunk_id, plus `(embedded, reused)` counts.

        Only cache misses reach the embedder, so re-indexing an unchanged corpus
        costs essentially nothing and says so in the log. Two things make that
        work and both are load-bearing:

        `Chunk.content_hash` is `content_hash(chunk.indexed_text)` and the
        embedder keys its own cache lookups on `content_hash(text)` for exactly
        that same string. If those two ever diverge, every lookup here misses,
        the embedder recomputes anyway, and the only visible symptom is a hit
        rate that quietly reads 0%.

        Identical content is embedded once per batch regardless of how many
        chunks carry it - a boilerplate footer repeated across 400 pages is one
        vector, not 400 - which is a saving the per-text path inside the embedder
        cannot make because it never sees the batch.
        """
        by_hash: dict[str, list[float]] = {}
        pending: dict[str, str] = {}
        order: list[tuple[str, str]] = []
        reused = 0

        for chunk in chunks:
            digest = chunk.content_hash
            order.append((chunk.chunk_id, digest))
            if digest in by_hash or digest in pending:
                reused += 1
                continue
            hit = self.cache.get(self.embedder.name, digest)
            # The width check catches a cache file carried across a config
            # change by hand; `name` encodes the dim, so it should never fire.
            if hit is not None and len(hit) == self.embedder.dim:
                by_hash[digest] = hit
                reused += 1
                continue
            pending[digest] = chunk.indexed_text

        digests = list(pending)
        if digests:
            # The embedder writes its own cache entries for these; putting them
            # again here would encode every vector to base64 twice.
            computed = self.embedder.embed([pending[d] for d in digests])
            if len(computed) != len(digests):
                # `Embedder.embed` promises positional alignment. A violation
                # would attach every vector after the gap to the wrong chunk -
                # a corpus-wide scrambling that no ranking looks wrong enough to
                # reveal. Drop the batch's vectors instead; those chunks stay
                # retrievable through BM25 until the next run fixes them.
                log.error(
                    "embedder returned a misaligned batch, vectors dropped",
                    expected=len(digests), got=len(computed),
                )
                computed = []
            for digest, vec in zip(digests, computed):
                by_hash[digest] = vec

        vectors = {cid: by_hash[digest] for cid, digest in order if digest in by_hash}
        embedded = len(chunks) - reused
        if chunks:
            log.info(
                "embedded chunks",
                chunks=len(chunks),
                embedded=embedded,
                reused=reused,
                hit_rate=f"{reused / len(chunks):.1%}",
                cached=len(self.cache),
            )
        return vectors, embedded, reused

    # ---- indexes ---------------------------------------------------------

    def refresh_indexes(self) -> None:
        """Rebuild the lexical and dense indexes from the store.

        Both arms stream: `iter_chunks` and `iter_vectors` are cursors, so the
        peak memory here is the indexes themselves rather than the indexes plus
        a materialized copy of the corpus. `build` replaces contents in place,
        which is what lets the retriever hold these two objects for the lifetime
        of the pipeline.
        """
        self._ensure_open()
        started = time.perf_counter()
        self.bm25.build(self.store.iter_chunks())
        self.dense.build(self.store.iter_vectors())
        self._indexes_built = True
        log.info(
            "indexes refreshed",
            bm25=len(self.bm25),
            dense=len(self.dense),
            secs=round(time.perf_counter() - started, 3),
        )

    def _ensure_indexes(self) -> None:
        if not self._indexes_built:
            self.refresh_indexes()

    # ---- query -----------------------------------------------------------

    def ask(self, question: str, k: int | None = None) -> Answer:
        """Retrieve, rerank, generate. Never raises on an empty or unknown query.

        The pool sent to the reranker is deeper than `k` (see
        `RERANK_POOL_FACTOR`), so the diversity and authority terms have room to
        actually change the result rather than reshuffle a fixed set.

        Stage timings land in `Answer.metrics` because "the answer was bad" and
        "the answer took nine seconds" are diagnosed from opposite ends of the
        pipeline, and the second question is unanswerable after the fact unless
        the numbers were recorded while it ran.
        """
        self._ensure_open()
        self._ensure_indexes()

        final_k = self.config.retrieval.k if k is None else k
        pool = max(final_k, min(self.config.retrieval.candidates, final_k * RERANK_POOL_FACTOR))

        started = time.perf_counter()
        retrieved = self.retriever.retrieve(question, pool)
        t_retrieve = time.perf_counter()
        reranked = self.reranker.rerank(question, retrieved, final_k)
        t_rerank = time.perf_counter()
        answer = self.generator.generate(question, reranked)
        done = time.perf_counter()

        answer.metrics.update(
            {
                "k": final_k,
                "pool": pool,
                "retrieved": len(retrieved),
                "reranked": len(reranked),
                "retrieve_ms": round((t_retrieve - started) * 1000, 2),
                "rerank_ms": round((t_rerank - t_retrieve) * 1000, 2),
                "generate_ms": round((done - t_rerank) * 1000, 2),
                "total_ms": round((done - started) * 1000, 2),
            }
        )
        # The generator populates `retrieved` on both its paths; this covers a
        # substituted generator that does not, because a caller checking
        # citations against `answer.retrieved` would otherwise see an answer
        # with no evidence attached and could not tell that from an abstention.
        if not answer.retrieved:
            answer.retrieved = list(reranked)

        log.info(
            "answered",
            chars=len(question),
            abstained=answer.abstained,
            confidence=round(answer.confidence, 4),
            citations=len(answer.citations),
            ms=answer.metrics["total_ms"],
        )
        return answer

    # ---- introspection ---------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Store counts plus the state of everything held in memory.

        `indexes_built` is here because a stale index is invisible in the store's
        own numbers: a store reporting 40,000 chunks and a bm25 arm holding 12 is
        a pipeline that will answer confidently out of a twelfth of its corpus.
        """
        self._ensure_open()
        out: dict[str, Any] = dict(self.store.stats())
        out.update(
            {
                "root": str(self.root),
                "embedder": self.embedder.name,
                "embed_dim": self.embedder.dim,
                "bm25_chunks": len(self.bm25),
                "dense_vectors": len(self.dense),
                "dense_backend": self.dense.backend,
                "indexes_built": self._indexes_built,
                "cache_entries": len(self.cache),
            }
        )
        return out

    def __repr__(self) -> str:
        state = "closed" if self._closed else "open"
        return f"Pipeline(root={str(self.root)!r}, embedder={self.embedder.name!r}, {state})"


def _extend_capped(errors: list[str], new: Sequence[str]) -> None:
    """Append error strings up to `MAX_ERRORS_KEPT`, truncating each."""
    for message in new:
        if len(errors) >= MAX_ERRORS_KEPT:
            return
        errors.append(message[:300])
