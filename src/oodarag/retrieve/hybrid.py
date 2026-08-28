"""The retriever: hybrid search end to end.

    query
      -> dense arm (embedding, cosine over the flat index)
      -> lexical arm (BM25 over FTS5)
      -> reciprocal rank fusion
      -> rerank (transparent heuristics)
      -> MMR diversification
      -> ScoredChunks with full provenance and score breakdown

Both arms are pre-filtered by the same metadata predicate, so a filtered search
still returns k results rather than however many survived a post-filter.

Why hybrid at all: dense retrieval finds paraphrase ("how do I split documents"
matches a passage about chunking that never uses the word "split"); lexical
retrieval finds exact tokens (an error code, a function name, a version string)
that an embedder blurs away. Each fails where the other works, and the failures
are not correlated, which is precisely the condition under which fusion helps.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from oodarag.embedding.base import Embedder
from oodarag.models import ScoredChunk
from oodarag.retrieve.expansion import expand
from oodarag.retrieve.fusion import RankedList, reciprocal_rank_fusion
from oodarag.retrieve.mmr import jaccard, mmr_select
from oodarag.retrieve.rerank import HeuristicReranker, Reranker
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.logging import get_logger
from oodarag.util.text import tokenize

log = get_logger("retrieve")


@dataclass
class RetrievalConfig:
    top_k: int = 8
    #: How deep each arm searches before fusion. Wider than top_k on purpose:
    #: fusion and reranking can only promote what they were given.
    candidate_k: int = 40
    dense_weight: float = 1.0
    lexical_weight: float = 1.0
    rrf_k: int = 60
    use_mmr: bool = True
    mmr_lambda: float = 0.7
    use_rerank: bool = True
    #: Pseudo-relevance feedback. Off by default until it is measured on your
    #: corpus: it helps where a question and its answer share little vocabulary,
    #: and hurts where the initial results are wrong, because it then retrieves
    #: more of the same. See retrieve/expansion.py.
    use_expansion: bool = False
    expansion_feedback_k: int = 5
    expansion_terms: int = 8
    #: Fused below the original arms, so expansion can add candidates but never
    #: evict what the original query found.
    expansion_weight: float = 0.5
    #: Results below this fused-and-reranked score are dropped. Returning weak
    #: matches is how a RAG system ends up confidently citing an irrelevant page.
    min_score: float = 0.0


@dataclass
class RetrievalTrace:
    """Everything that happened during one retrieval. Answers 'why this result?'"""

    query: str = ""
    dense_hits: int = 0
    lexical_hits: int = 0
    expansion_hits: int = 0
    fused_hits: int = 0
    filtered_to: int | None = None
    returned: int = 0
    latency_ms: float = 0.0
    stages: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query, "dense_hits": self.dense_hits,
            "lexical_hits": self.lexical_hits, "expansion_hits": self.expansion_hits,
            "fused_hits": self.fused_hits,
            "filtered_to": self.filtered_to, "returned": self.returned,
            "latency_ms": round(self.latency_ms, 2),
            "stages": {k: round(v, 2) for k, v in self.stages.items()},
            "notes": self.notes,
        }


class HybridRetriever:
    def __init__(self, store: SqliteStore, embedder: Embedder,
                 config: RetrievalConfig | None = None,
                 reranker: Reranker | None = None) -> None:
        self.store = store
        self.embedder = embedder
        self.config = config or RetrievalConfig()
        self.reranker = reranker or HeuristicReranker(
            idf=store.idf_lookup(), vocabulary=store.vocabulary())
        #: Whether this retriever owns the reranker's corpus statistics. An
        #: injected reranker is the caller's to keep current; the default one is
        #: ours, and it must not outlive the corpus it was built from.
        self._owns_reranker = reranker is None
        self._analysis_signature = store.corpus_signature() if reranker is None else ""

    def _refresh_analysis(self) -> None:
        """Re-read the IDF table and vocabulary when the corpus has changed.

        Both were captured once, at construction. `idf_lookup()` closes over the
        table it read at that moment and `vocabulary()` returns a plain set, so a
        retriever built before indexing kept an empty vocabulary for its whole
        life - and `_answerability` returns 1.0 on an empty vocabulary, which
        silently removes the abstention gate's only corpus-aware input. `ooda
        loop` builds its generator before the ACT phase indexes anything, so
        this was every loop run: the system simply stopped abstaining, and
        nothing in the eval output distinguished it from working.

        Keyed on the corpus content digest rather than on a counter, for the
        reason recorded in L27: a corpus rewritten in place moves no counter.
        The digest costs about 0.5ms per query on a 629-chunk index and scales
        with chunk count; a very large index should hold the retriever for the
        life of an index generation instead.
        """
        if not self._owns_reranker:
            return
        signature = self.store.corpus_signature()
        if signature == self._analysis_signature:
            return
        self.reranker.idf = self.store.idf_lookup()
        self.reranker.vocabulary = self.store.vocabulary()
        self._analysis_signature = signature
        log.debug("refreshed reranker corpus statistics",
                  terms=len(self.reranker.vocabulary or ()))

    def retrieve(self, query: str, *, top_k: int | None = None,
                 filters: dict[str, Any] | None = None) -> tuple[list[ScoredChunk], RetrievalTrace]:
        self._refresh_analysis()
        config = self.config
        k = top_k or config.top_k
        trace = RetrievalTrace(query=query)
        started = time.monotonic()

        allowed = self.store.filter_chunk_ids(filters)
        if allowed is not None:
            trace.filtered_to = len(allowed)
            if not allowed:
                trace.notes.append("filter matched no chunks")
                trace.latency_ms = (time.monotonic() - started) * 1000
                return [], trace

        # --- dense arm
        mark = time.monotonic()
        dense: list[tuple[str, float]] = []
        index = self.store.vector_index(self.embedder.fingerprint)
        if len(index):
            query_vector = self.embedder.embed_query(query)
            dense = index.search(query_vector, k=config.candidate_k, allowed=allowed)
        else:
            trace.notes.append(
                f"no vectors for fingerprint {self.embedder.fingerprint!r}; lexical only"
            )
        trace.dense_hits = len(dense)
        trace.stages["dense_ms"] = (time.monotonic() - mark) * 1000

        # --- lexical arm
        mark = time.monotonic()
        lexical = self.store.search_lexical(query, k=config.candidate_k, allowed=allowed)
        trace.lexical_hits = len(lexical)
        trace.stages["lexical_ms"] = (time.monotonic() - mark) * 1000

        if not dense and not lexical:
            trace.latency_ms = (time.monotonic() - started) * 1000
            trace.notes.append("both arms returned nothing")
            return [], trace

        # --- expansion (a third arm, fused below the other two)
        expanded: list[tuple[str, float]] = []
        if config.use_expansion:
            mark = time.monotonic()
            seed_ids = [cid for cid, _ in (dense or lexical)[: config.expansion_feedback_k]]
            feedback = list(self.store.get_chunks(seed_ids).values())
            expansion = expand(
                query, feedback, self.store.idf_lookup(),
                max_terms=config.expansion_terms,
                corpus_frequency=self.store.term_frequency(),
            )
            if expansion.terms:
                trace.notes.append(f"expanded with: {' '.join(expansion.terms)}")
                expanded = self.store.search_lexical(
                    expansion.query, k=config.candidate_k, allowed=allowed)
            trace.stages["expansion_ms"] = (time.monotonic() - mark) * 1000
            trace.expansion_hits = len(expanded)

        # --- fusion
        mark = time.monotonic()
        arms = [
            RankedList("dense", dense, config.dense_weight),
            RankedList("lexical", lexical, config.lexical_weight),
        ]
        if expanded:
            arms.append(RankedList("expanded", expanded, config.expansion_weight))
        fused = reciprocal_rank_fusion(arms, k=config.rrf_k, top_k=config.candidate_k)
        trace.fused_hits = len(fused)
        trace.stages["fusion_ms"] = (time.monotonic() - mark) * 1000

        chunk_map = self.store.get_chunks([item_id for item_id, _, _ in fused])
        doc_map = self.store.get_documents(
            list({c.doc_id for c in chunk_map.values()})
        )
        results: list[ScoredChunk] = []
        for chunk_id, score, components in fused:
            chunk = chunk_map.get(chunk_id)
            if chunk is None:
                continue  # index and store disagree; skip rather than crash
            document = doc_map.get(chunk.doc_id)
            if document is not None:
                chunk.metadata.setdefault("updated_at", document.updated_at)
                chunk.metadata.setdefault("authority", document.metadata.get("authority", 1.0))
            results.append(ScoredChunk(chunk=chunk, score=score,
                                       components=dict(components), document=document))

        # --- score features, then (optionally) reorder by them
        #
        # These are always computed. The abstention gate reads
        # `rerank_relevance`, so making the feature pass conditional on
        # `use_rerank` silently disabled the gate's only input: with reranking
        # off, relevance defaulted to zero and the system abstained on almost
        # everything - 8 of 36 golden cases instead of 32, while recall stayed
        # at 0.857. A configuration flag has to degrade behaviour, not disable
        # an unrelated safety check.
        if results:
            mark = time.monotonic()
            results = self.reranker.rerank(query, results)
            if not config.use_rerank:
                # Restore the fused score itself, not merely the list order:
                # MMR and the score floor below both read `score`, so re-sorting
                # alone left reranking fully in control and made `use_rerank`
                # look like it did nothing.
                for result in results:
                    result.score = result.components.get("pre_rerank_score", result.score)
                results.sort(key=lambda r: r.score, reverse=True)
            trace.stages["rerank_ms"] = (time.monotonic() - mark) * 1000

        if config.min_score > 0:
            before = len(results)
            results = [r for r in results if r.score >= config.min_score]
            if before != len(results):
                trace.notes.append(f"dropped {before - len(results)} below min_score")

        # --- diversify
        if config.use_mmr and len(results) > k:
            mark = time.monotonic()
            token_cache = {r.chunk.chunk_id: tokenize(r.chunk.indexed_text) for r in results}

            def similarity(a: str, b: str) -> float:
                return jaccard(token_cache.get(a, []), token_cache.get(b, []))

            keep = mmr_select([(r.chunk.chunk_id, r.score) for r in results],
                              similarity, k=k, lambda_=config.mmr_lambda)
            order = {chunk_id: i for i, chunk_id in enumerate(keep)}
            results = sorted((r for r in results if r.chunk.chunk_id in order),
                             key=lambda r: order[r.chunk.chunk_id])
            trace.stages["mmr_ms"] = (time.monotonic() - mark) * 1000
        else:
            results = results[:k]

        trace.returned = len(results)
        trace.latency_ms = (time.monotonic() - started) * 1000
        log.debug("retrieved", query=query[:60], returned=len(results),
                  ms=round(trace.latency_ms, 1))
        return results, trace
