"""Hybrid retrieval: two arms, one rank fusion, and why the scores never meet.

The lexical arm (`index/bm25.py`) and the dense arm (`index/dense.py`) disagree
about what a number means. BM25 is an unbounded sum of idf-weighted term
contributions: its scale depends on how rare the query terms happen to be in
*this* corpus, so the same query against the same chunk scores differently once
another thousand documents land. Cosine is bounded in [-1, 1] and, for a
hashing embedder over real text, spends almost all of its time in a narrow band
above zero. Adding them is meaningless and averaging them is worse, because the
result looks reasonable.

The obvious repair - normalize each arm per query, then blend - was rejected.
Min-max normalization makes the top hit of each arm exactly 1.0 whether it was
a perfect match or the best of a bad lot, which is a fabricated score; it also
re-weights the blend silently as the corpus grows, since the spread it divides
by is a property of the corpus, not of the query. Z-scores need a distribution
neither arm has. Every variant shares the same defect: the weighting that
actually decides the ranking is a guess, it is invisible in the output, and it
drifts.

Reciprocal Rank Fusion reads only what both arms genuinely mean the same way:
*rank order*. A chunk's contribution from an arm is `weight / (rrf_k + rank)`,
summed across arms. Nothing here can be miscalibrated, because nothing is
calibrated: an arm votes with its ordering and the votes add up. `rrf_k` is the
single knob and its effect is legible - it sets how much better rank 1 is than
rank 10 (at the default 60, about 15% better, so no single arm's favourite can
dictate the fused winner on its own). The value 60 is the constant the original
RRF work settled on and it is kept because a tuned-per-corpus fusion constant
would reintroduce exactly the drift this design exists to avoid.

What RRF gives up is worth stating plainly: the fused score is ordinal, so it
cannot tell "the best of forty excellent chunks" from "the best of forty
terrible ones". That information is not thrown away - each arm's raw score
rides along in `components` - it is simply not what the ranking is built on.

Three details that are decisions, not incidentals:

**Over-fetch, then cut.** Both arms are queried for `candidates` (40) results to
produce `k` (8). Fusion can only rank what it was handed, and the chunk that
both arms rank tenth is usually a better answer than the one a single arm ranks
first - it cannot win if the arms were only asked for eight.

**A missing arm gets a sentinel rank, never a substitute score.** When only one
arm returns a chunk, `components["<arm>_rank"]` is `MISSING_RANK` (0.0, out of
band because real ranks are 1-based) and the arm contributes nothing to the
sum. Writing a plausible-looking 0.0 *score* instead would be a lie the dense
arm can tell convincingly, since a cosine of 0.0 is a real value meaning
"orthogonal" rather than "never looked at this chunk".

**`source_filter` runs after fusion.** Neither index knows what source a chunk
came from - that lives on the `Document` - so a pre-fusion filter would mean a
per-source index. Filtering afterwards keeps every rank meaning what it meant
(the chunk's position in the whole corpus) at the cost of sometimes returning
fewer than `k` results. That is the honest outcome: the filtered source really
does not have `k` relevant chunks, and padding the tail with junk to reach the
requested count would hide it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from oodarag.embed.base import Embedder
from oodarag.index.bm25 import BM25Index
from oodarag.index.dense import DenseIndex
from oodarag.index.store import Store
from oodarag.models import Chunk, Document, ScoredChunk
from oodarag.util.logging import get_logger

log = get_logger("retrieve")

#: Arm names. They are the `components` keys the rest of the pipeline reads, so
#: they are constants rather than string literals scattered across two files.
ARM_LEXICAL = "bm25"
ARM_DENSE = "dense"

#: Rank recorded for an arm that never returned the chunk. Ranks are 1-based,
#: so 0.0 is unambiguous, sorts nowhere near a real rank, and survives JSON -
#: `float("inf")` was rejected because `Answer.to_json` would emit `Infinity`,
#: which is not valid JSON for whatever reads the log next.
MISSING_RANK = 0.0


@dataclass(slots=True)
class RetrievalConfig:
    """Knobs for one hybrid query.

    `candidates` is the depth each arm is asked for, `k` the depth returned.
    `rrf_k` damps the head of the reciprocal curve (see the module docstring).
    The two weights are arm votes, not score multipliers: raising
    `lexical_weight` makes the BM25 ordering count for more, and because the
    arms only ever contribute `weight / (rrf_k + rank)`, doubling one cannot
    make it swamp the other by a factor of its raw scale.
    """

    k: int = 8
    candidates: int = 40
    rrf_k: int = 60
    dense_weight: float = 1.0
    lexical_weight: float = 1.0


def rrf_fuse(
    rankings: Mapping[str, list[tuple[str, float]]],
    *,
    rrf_k: int = 60,
    weights: Mapping[str, float] | None = None,
) -> list[tuple[str, float, dict[str, float]]]:
    """Fuse per-arm rankings into `(chunk_id, fused_score, components)`, best first.

    Pure: no store, no config object, no logging. Fusion is the one piece of
    retrieval whose behaviour is worth pinning down in a test with three
    handwritten lists, and it stays testable exactly as long as it stays free of
    everything else in this module.

    Each arm contributes `weight / (rrf_k + rank)` for the chunks it ranked.
    Every returned `components` dict carries the same keys whatever the arms
    returned - `<arm>` (that arm's raw score), `<arm>_rank` (1-based, or
    `MISSING_RANK`), and `rrf` - so a caller can read them positionally without
    a membership check.
    """
    if rrf_k < 0:
        # A negative constant makes the denominator shrink towards zero and then
        # cross it, which inverts the ranking somewhere in the middle of the
        # list. There is no sane query that wants this.
        raise ValueError(f"rrf_k must be >= 0, got {rrf_k}")

    arms = list(rankings)
    weight_of = {arm: float((weights or {}).get(arm, 1.0)) for arm in arms}
    fused: dict[str, dict[str, float]] = {}

    for arm in arms:
        seen: set[str] = set()
        for rank, (chunk_id, score) in enumerate(rankings[arm] or [], start=1):
            # An arm that returns the same chunk twice would otherwise vote
            # twice and outrank a chunk both arms agree on. Indexes dedupe on
            # add, but this function is also handed rankings by tests and by
            # future arms, so the guard lives with the arithmetic.
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            components = fused.get(chunk_id)
            if components is None:
                components = {arm_name: 0.0 for arm_name in arms}
                components.update({f"{arm_name}_rank": MISSING_RANK for arm_name in arms})
                components["rrf"] = 0.0
                fused[chunk_id] = components
            components[arm] = float(score)
            components[f"{arm}_rank"] = float(rank)
            components["rrf"] += weight_of[arm] / (rrf_k + rank)

    # Ties break on chunk_id, matching both indexes: two chunks that appear at
    # the same rank in the same arms fuse to bit-identical floats, and without a
    # total order the winner would depend on dict insertion order, i.e. on which
    # arm happened to run first.
    ranked = [(chunk_id, comp["rrf"], comp) for chunk_id, comp in fused.items()]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked


class HybridRetriever:
    """Queries both arms, fuses by rank, and resolves the winners to chunks."""

    def __init__(
        self,
        store: Store,
        embedder: Embedder,
        bm25: BM25Index,
        dense: DenseIndex,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.bm25 = bm25
        self.dense = dense
        self.config = config or RetrievalConfig()

    def retrieve(
        self, query: str, k: int | None = None, *, source_filter: str | None = None
    ) -> list[ScoredChunk]:
        """Top-`k` chunks for `query`, each carrying its score breakdown and document.

        An empty query returns `[]` rather than a ranking. This is not just
        tidiness: an empty string embeds to the zero vector, every dot product
        is then 0.0, and the dense arm would hand back the alphabetically first
        `candidates` chunk ids with a straight face - a fabricated ranking that
        RRF would happily score.
        """
        top_k = self.config.k if k is None else k
        if top_k <= 0 or not query.strip():
            return []
        # Asking for fewer candidates than results makes no sense; a caller
        # asking for k=100 from a 40-candidate config gets 100 per arm.
        candidates = max(self.config.candidates, top_k)

        rankings = {
            ARM_LEXICAL: self._lexical(query, candidates),
            ARM_DENSE: self._dense(query, candidates),
        }
        fused = rrf_fuse(
            rankings,
            rrf_k=self.config.rrf_k,
            weights={
                ARM_LEXICAL: self.config.lexical_weight,
                ARM_DENSE: self.config.dense_weight,
            },
        )
        if not fused:
            log.info("no candidates", chars=len(query), source_filter=source_filter or "")
            return []

        # One round trip for every candidate. Per-chunk lookups would turn a
        # single query into eighty SQLite statements, and the ids are already
        # known here - there is nothing to stream.
        chunks: dict[str, Chunk] = self.store.get_chunks([chunk_id for chunk_id, _, _ in fused])
        # No batched document read exists on Store, so documents are memoized by
        # doc_id instead: a page's chunks cluster in any ranking, so the eighty
        # candidates are typically a handful of documents. `None` is a cached
        # answer too, hence the `in` test rather than `.get`.
        documents: dict[str, Document | None] = {}

        results: list[ScoredChunk] = []
        stale = 0
        for chunk_id, score, components in fused:
            chunk = chunks.get(chunk_id)
            if chunk is None:
                # The in-memory indexes outlive the re-index that dropped a
                # chunk. Losing one hit beats failing the query.
                stale += 1
                continue
            if chunk.doc_id not in documents:
                documents[chunk.doc_id] = self.store.get_document(chunk.doc_id)
            document = documents[chunk.doc_id]
            if source_filter is not None and (
                document is None or document.source_system != source_filter
            ):
                # A chunk whose document is missing cannot be shown to match the
                # filter, so it is dropped rather than given the benefit of the
                # doubt - a filtered query must never return another source.
                continue
            results.append(
                ScoredChunk(chunk=chunk, score=score, components=components, document=document)
            )
            if len(results) >= top_k:
                break

        if stale:
            log.warn("candidates missing from store", count=stale, hint="indexes are stale")
        log.info(
            "retrieved",
            chars=len(query),
            lexical=len(rankings[ARM_LEXICAL]),
            dense=len(rankings[ARM_DENSE]),
            fused=len(fused),
            returned=len(results),
            source_filter=source_filter or "",
        )
        return results

    def _lexical(self, query: str, candidates: int) -> list[tuple[str, float]]:
        """BM25 arm. Best-effort: a dead arm degrades the answer, it does not fail it."""
        try:
            return self.bm25.search(query, candidates)
        except Exception as e:  # noqa: BLE001 - one arm must not take the query down
            log.error("lexical arm failed", err=f"{type(e).__name__}: {e}"[:200])
            return []

    def _dense(self, query: str, candidates: int) -> list[tuple[str, float]]:
        """Dense arm: embed the query, then scan.

        The embed call is the one that can fail for boring reasons - a hosted
        embedder is a network call - so it degrades. The search call is *not*
        wrapped: the only error it raises is a dimension mismatch, which means
        the index and the embedder disagree, affects every query equally, and
        would otherwise hide behind lexical-only answers that look fine.
        """
        try:
            vector = self.embedder.embed_one(query)
        except Exception as e:  # noqa: BLE001 - see docstring
            log.error(
                "query embedding failed, dense arm skipped",
                err=f"{type(e).__name__}: {e}"[:200],
            )
            return []
        return self.dense.search(vector, candidates)

    def __repr__(self) -> str:
        return (
            f"HybridRetriever(k={self.config.k}, candidates={self.config.candidates}, "
            f"rrf_k={self.config.rrf_k}, bm25={len(self.bm25)}, dense={len(self.dense)})"
        )
