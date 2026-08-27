"""Hybrid retrieval: a lexical arm, a dense arm, and rank fusion over both.

The two arms fail in opposite directions, which is the entire reason to run
both. BM25 cannot match a paraphrase — a query for "how do I stop the crawler
running forever" misses a passage titled "budgets". Dense vectors cannot match
a rare exact token — an error code, a flag name, a version string — because the
token was never frequent enough to shape the space. A corpus of prose and code
contains both kinds of query, so a single-arm retriever is wrong for half of it.

Fusion is by **Reciprocal Rank Fusion**: each arm contributes `1 / (k + rank)`
for every document it ranks, and the contributions are summed.

    RRF(d) = Σ_r  1 / (k + rank_r(d))

RRF combines *ranks*, not scores, which is what makes it usable here. BM25
scores and cosine similarities are on incomparable scales and neither is
calibrated across queries, so any weighted sum of the raw numbers is tuned to a
corpus and silently wrong on the next one. Ranks have no such problem.

`k = 60` comes from Cormack, Clarke & Büttcher, "Reciprocal rank fusion
outperforms Condorcet and individual rank learning methods", SIGIR 2009,
pp. 758-759 (doi:10.1145/1571941.1572114), and is the value Elasticsearch also
takes as its default `rank_constant`. It is **convention, not a derived
optimum** — in the paper it was fixed during a pilot and left alone. It damps
the influence of the very top ranks, so one arm's confident first place cannot
by itself outvote broad agreement between both arms. Lower k trusts the top of
each list more; higher k flattens towards a plain vote count.

Ranks here are **1-based**, matching the paper and Elasticsearch. This is worth
pinning down because implementations differ — Qdrant uses 0-based positions and
k = 2 — so a fusion score is only comparable against another implementation
that shares both conventions.

Reranking then applies signals that are about the *source* rather than the
match — how much this connector is trusted, whether the query's exact phrase is
present — because those are the judgements neither arm can make.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from oodarag.embed import Embedder, HashingEmbedder, cosine
from oodarag.models import Chunk, ScoredChunk
from oodarag.store import Store
from oodarag.util.logging import get_logger
from oodarag.util.text import tokenize

log = get_logger("retrieve")

#: The constant from Cormack et al., SIGIR 2009. Convention, not derived.
RRF_K = 60


@dataclass(slots=True)
class RetrievalConfig:
    """How wide to search and how to weight what comes back.

    `candidates` is deliberately much larger than `top_k`: fusion can only
    reorder what the arms surfaced, so an arm that returns 10 results caps the
    recall of the whole retriever no matter how good the reranker is. Retrieve
    wide, then narrow.
    """

    top_k: int = 8
    candidates: int = 60
    use_lexical: bool = True
    use_dense: bool = True
    rrf_k: int = RRF_K
    authority_weight: float = 0.15
    phrase_bonus: float = 0.10
    min_score: float = 0.0
    """Absolute floor on the fused score. Off by default, deliberately.

    A fused RRF score is not a similarity: with k=60 a top-ranked hit in both
    arms scores about 0.033, and the value has no meaning outside the query
    that produced it. A fixed threshold on it would be a magic number that
    silently drops results on one corpus and nothing on another. Abstention is
    handled where it can be judged — in the generator, against the retrieved
    text — rather than here against an uncalibrated number.
    """
    source_authority: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalReport:
    """What the retriever did, for the times the answer looks wrong."""

    query: str
    lexical_hits: int = 0
    dense_hits: int = 0
    fused: int = 0
    returned: int = 0
    filtered_out: int = 0
    arms_used: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "lexical_hits": self.lexical_hits,
            "dense_hits": self.dense_hits,
            "fused": self.fused,
            "returned": self.returned,
            "filtered_out": self.filtered_out,
            "arms_used": self.arms_used,
        }


def reciprocal_rank_fusion(
    ranked_lists: dict[str, list[str]], k: int = RRF_K
) -> dict[str, dict[str, float]]:
    """Fuse ranked id lists. Returns id -> {arm: contribution, ...}.

    Contributions are kept per arm rather than summed immediately so that a
    result can explain itself: "this came only from the lexical arm" is the
    single most useful thing to know when a hit looks wrong.
    """
    out: dict[str, dict[str, float]] = {}
    for arm, ids in ranked_lists.items():
        for rank, ident in enumerate(ids, start=1):
            out.setdefault(ident, {})[arm] = 1.0 / (k + rank)
    return out


class Retriever:
    """Hybrid search over a `Store`."""

    def __init__(
        self,
        store: Store,
        embedder: Embedder | None = None,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.store = store
        self.embedder = embedder or HashingEmbedder()
        self.config = config or RetrievalConfig()

    def search(
        self,
        query: str,
        k: int | None = None,
        filters: dict[str, object] | None = None,
    ) -> list[ScoredChunk]:
        results, _ = self.search_with_report(query, k, filters)
        return results

    def search_with_report(
        self,
        query: str,
        k: int | None = None,
        filters: dict[str, object] | None = None,
    ) -> tuple[list[ScoredChunk], RetrievalReport]:
        """Search, optionally restricted to chunks whose metadata matches.

        Filtering happens *after* fusion rather than inside each arm, so the
        arms still see the whole corpus and their ranks stay comparable. The
        cost is that a narrow filter over a large corpus can return fewer than
        `k`; the report says how many were dropped, so a thin result set is
        diagnosable rather than mysterious.

        A list or set value matches any member, so
        `filters={"source_system": ["github", "file"]}` is one call rather than
        two searches merged by hand.
        """
        cfg = self.config
        top_k = k or cfg.top_k
        report = RetrievalReport(query=query)
        if not query.strip():
            return [], report

        ranked: dict[str, list[str]] = {}
        raw: dict[str, dict[str, float]] = {}

        if cfg.use_lexical:
            hits = self.store.search_lexical(query, cfg.candidates)
            ranked["lexical"] = [h.chunk_id for h in hits]
            raw["lexical"] = {h.chunk_id: h.score for h in hits}
            report.lexical_hits = len(hits)
            if hits:
                report.arms_used.append("lexical")

        if cfg.use_dense:
            dense = self._dense_search(query, cfg.candidates)
            ranked["dense"] = [cid for cid, _ in dense]
            raw["dense"] = dict(dense)
            report.dense_hits = len(dense)
            if dense:
                report.arms_used.append("dense")

        fused = reciprocal_rank_fusion(ranked, cfg.rrf_k)
        report.fused = len(fused)
        if not fused:
            return [], report

        # Fetching only the fused candidates keeps this proportional to the
        # candidate pool rather than to the corpus.
        chunks = self._load_chunks(list(fused))
        scored: list[ScoredChunk] = []
        query_terms = set(tokenize(query))

        for chunk_id, contributions in fused.items():
            chunk = chunks.get(chunk_id)
            if chunk is None:
                continue
            base = sum(contributions.values())
            components = dict(contributions)
            for arm, scores in raw.items():
                if chunk_id in scores:
                    components[f"{arm}_raw"] = scores[chunk_id]

            if filters and not _matches(chunk, filters):
                report.filtered_out += 1
                continue

            adjust = self._rerank_bonus(chunk, query, query_terms, components)
            total = base * (1.0 + adjust)
            if total < cfg.min_score:
                continue
            components["rerank"] = adjust
            scored.append(ScoredChunk(chunk=chunk, score=total, components=components))

        scored.sort(key=lambda s: s.score, reverse=True)
        out = scored[:top_k]
        self._attach_documents(out)
        report.returned = len(out)
        log.debug("retrieved", **report.as_dict())
        return out, report

    # ----------------------------------------------------------------- arms

    def _dense_search(self, query: str, k: int) -> list[tuple[str, float]]:
        """Brute-force cosine over stored vectors.

        Exact rather than approximate: at this corpus size an ANN index costs
        more in build time and recall loss than the scan costs in latency, and
        an exact scan has no tuning parameters to get wrong.
        """
        qvec = self.embedder.embed(query)
        if not any(qvec):
            return []
        scores: list[tuple[str, float]] = []
        for _rowid, chunk_id, vec in self.store.iter_vectors():
            if len(vec) != len(qvec):
                continue  # a vector written by a different embedder configuration
            sim = cosine(qvec, vec)
            if sim > 0.0:
                scores.append((chunk_id, sim))
        scores.sort(key=lambda t: t[1], reverse=True)
        return scores[:k]

    def _load_chunks(self, chunk_ids: list[str]) -> dict[str, Chunk]:
        out: dict[str, Chunk] = {}
        for cid in chunk_ids:
            if chunk := self.store.get_chunk(cid):
                out[cid] = chunk
        return out

    def _attach_documents(self, results: list[ScoredChunk]) -> None:
        """Attach parent documents so a citation can name a title and a URI."""
        cache: dict[str, object] = {}
        for result in results:
            doc_id = result.chunk.doc_id
            if doc_id not in cache:
                cache[doc_id] = self.store.get_document(doc_id)
            doc = cache[doc_id]
            if doc is not None:
                result.document = doc  # type: ignore[assignment]

    # -------------------------------------------------------------- rerank

    def _rerank_bonus(
        self, chunk: Chunk, query: str, query_terms: set[str], components: dict[str, float]
    ) -> float:
        """A small multiplier from signals the arms cannot see.

        Kept as a bounded *relative* adjustment rather than an additive score,
        so it can reorder near-ties without ever promoting an irrelevant chunk
        above a relevant one on source reputation alone.
        """
        cfg = self.config
        bonus = 0.0

        source = str(chunk.metadata.get("source_system", ""))
        if authority := cfg.source_authority.get(source):
            bonus += cfg.authority_weight * (authority - 1.0)

        # An exact phrase match is strong evidence that neither a bag-of-words
        # score nor a hashed vector can represent.
        phrase = query.strip().lower()
        if len(phrase) > 8 and phrase in chunk.text.lower():
            bonus += cfg.phrase_bonus

        # Agreement between both arms is worth more than a strong showing in
        # one, which is the property RRF is chosen for; this makes it explicit.
        if "lexical" in components and "dense" in components:
            bonus += 0.05

        # A chunk whose heading path contains query terms is about the query,
        # not merely adjacent to it.
        headings = " ".join(str(h) for h in chunk.metadata.get("headings", []))
        if headings and query_terms & set(tokenize(headings)):
            bonus += 0.05

        return bonus


def _matches(chunk: Chunk, filters: dict[str, object]) -> bool:
    """Does this chunk's metadata satisfy every filter?

    A chunk missing the key fails rather than passing. Absent metadata is not
    evidence of a match, and treating it as one is how a filtered search
    quietly returns the thing it was told to exclude.
    """
    for key, wanted in filters.items():
        if key not in chunk.metadata:
            return False
        actual = chunk.metadata[key]
        if isinstance(wanted, (list, tuple, set, frozenset)):
            if actual not in wanted:
                return False
        elif actual != wanted:
            return False
    return True


_WORD_RE = re.compile(r"\w+")
