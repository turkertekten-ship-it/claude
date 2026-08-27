"""Reranking: buy diversity with a little relevance, then nudge for source and age.

Retrieval, working perfectly, returns near-duplicates. That is not a bug to fix
upstream - it is what a correct ranker does when the corpus genuinely contains
the same sentence four times. The chunker overlaps by 64 tokens, so adjacent
chunks of one section literally share text. A documentation site repeats its
navigation, its version banner and its footer on every page. A monorepo carries
the same install stanza in nine READMEs. Ask "how do I configure the cache" and
the top eight can be three windows onto one paragraph, a stale copy of that
paragraph from an older release, and five pages of boilerplate that happen to
contain the word cache.

The cost is the context window. Eight chunks at ~320 tokens is the entire
budget the generator gets; spending three of those slots re-reading one fact
means the qualifying condition that lived in a different document never gets
seen, and the answer is confidently incomplete. Ranking by relevance alone
cannot notice this, because every one of those duplicates *is* relevant. The
missing question is not "is this good?" but "does this add anything the picks
already made do not have?"

Maximal Marginal Relevance asks exactly that, greedily: pick the candidate
maximizing `mmr_lambda * relevance - (1 - mmr_lambda) * max similarity to what
is already picked`. Greedy, not optimal: choosing the best diverse subset is a
max-dispersion problem, and its one failure mode - an early pick that cannot be
taken back - costs nothing measurable at k=8 while the exact version costs an
exponential search. Clustering the candidates first was rejected for needing a
cluster count that is exactly as arbitrary as the thing it replaces.

**Relevance is scaled by the best candidate, and that is not the normalization
`retrieve.py` refuses.** The fusion arms are refused a common scale because
theirs is a guess about two incomparable distributions. Here there is one
scale, already fused, and the ratio `score / best_score` is monotone: it cannot
reorder the candidates, it only fixes the units so `mmr_lambda` means what it
says. Without it the trade-off is not a trade-off - RRF scores live around
0.02-0.03 while cosine similarity runs to 1.0, so the diversity term would
decide every pick and lambda would be decoration. The consequence a caller must
know is in `rerank`'s docstring: the top candidate always scales to 1.0, so
`final` ranks within a query and is not a calibrated confidence.

**Vectors are recomputed through the embedder, not read from the store.** The
reranker is handed `ScoredChunk`s and is deliberately given no store handle: an
eval harness, a cache, or a future retriever that fuses three arms can all hand
it candidates whose vectors the store never held, and a store that *was* written
by an older embedder generation would hand back numbers from a different
coordinate system that cosine would compare without complaint. One batched
`embed` call over the candidate set costs one pass and removes the whole class
of problem. `EmbeddingCache` makes it nearly free on the second query.

**Authority and recency nudge, they do not rank.** `authority_weight *
authority` is added after the MMR term, so a trusted source wins ties and close
calls and cannot buy its way past a chunk that is actually more relevant.
Recency multiplies that nudge rather than the score: an old document keeps
everything it earned on merit and loses only the benefit of the doubt. The trap
that follows is worth stating - `authority_weight` is the magnitude of the
entire prior, so setting it to 0 disables recency too. That coupling is
deliberate: an independently-weighted recency term would need a second knob the
frozen config does not have, and an unbounded one would let a fresh irrelevant
page outrank a relevant one, which is the failure mode of every "sort by date"
search anyone has ever regretted.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, replace

from oodarag.embed.base import Embedder, cosine
from oodarag.models import Document, ScoredChunk
from oodarag.util.logging import get_logger

log = get_logger("rerank")

_SECONDS_PER_DAY = 86400.0


@dataclass(slots=True)
class RerankConfig:
    """Knobs for one rerank pass.

    `mmr_lambda` is the relevance/diversity split: 1.0 is pure relevance (the
    retriever's order, minus nothing), 0.0 is pure diversity (the eight most
    mutually unlike candidates, relevance ignored). The default leans towards
    relevance because diversity is a correction, not a goal - a query with one
    right answer should still get it.

    `authority_weight` is the size of the whole source prior, on the same scale
    as the MMR term (which lands in roughly [-0.3, 1.0]): 0.15 is a tiebreak,
    not an override.

    `recency_half_life_days` is off by default because most of this corpus is
    documentation and code, where age is weak evidence of anything. It earns its
    keep on sources that supersede themselves - release notes, changelogs, chat.
    """

    mmr_lambda: float = 0.7
    authority_weight: float = 0.15
    recency_half_life_days: float = 0.0


class Reranker:
    """Reorders retrieved candidates for diversity, source authority and age."""

    def __init__(self, embedder: Embedder, config: RerankConfig | None = None) -> None:
        self.embedder = embedder
        self.config = config or RerankConfig()

    def rerank(self, query: str, scored: list[ScoredChunk], k: int = 8) -> list[ScoredChunk]:
        """Select and reorder the best `k` of `scored`.

        Returns new `ScoredChunk`s - the inputs are left untouched so an eval
        harness can compare the pre- and post-rerank rankings - whose
        `components` carry the retrieval breakdown *plus* `relevance`,
        `diversity`, `mmr`, `authority`, `recency` and `final`. `score` becomes
        `final`.

        `final` is a within-query ranking score, not a confidence: relevance is
        scaled against the best candidate, so the top result scores about
        `mmr_lambda + authority_weight` whether retrieval found a perfect match
        or the best of a bad lot. A caller that needs an absolute measure should
        read `components["rrf"]` or a raw arm score, which pass through
        unmodified.

        `query` is unused by the arithmetic and is kept in the signature on
        purpose: it is what a cross-encoder or an LLM reranker would need, and
        this is the seam they would be dropped into.
        """
        if k <= 0 or not scored:
            return []
        # Out-of-range lambda would flip the sign of a term and silently invert
        # the meaning of the knob; clamping keeps a typo to a dull result.
        lam = min(1.0, max(0.0, self.config.mmr_lambda))
        limit = min(k, len(scored))

        relevance = _scale_relevance([s.score for s in scored])
        vectors = self._vectors(scored)
        now = time.time()
        priors = [self._prior(s.document, now) for s in scored]

        # Highest similarity between each candidate and anything already picked.
        # Maintained incrementally: k*n cosines instead of recomputing the max
        # over the picked set on every pass. Floored at 0.0 - a negative cosine
        # means "points the other way", which is not evidence of extra
        # information and must not pay a bonus.
        max_sim = [0.0] * len(scored)
        remaining = list(range(len(scored)))  # retrieval order, so ties favour rank
        selected: list[ScoredChunk] = []

        while remaining and len(selected) < limit:
            best_position = 0
            best_final = -math.inf
            best_mmr = 0.0
            for position, index in enumerate(remaining):
                mmr = lam * relevance[index] - (1.0 - lam) * max_sim[index]
                # Selection uses the *nudged* score, not the bare MMR term: an
                # authority prior that only reordered the winners after the fact
                # could never keep an official page in the set at all, which is
                # the one thing it exists to do.
                final = mmr + priors[index][0]
                if final > best_final:  # strict: first (best-ranked) candidate wins ties
                    best_final = final
                    best_mmr = mmr
                    best_position = position

            index = remaining.pop(best_position)
            candidate = scored[index]
            prior, decay = priors[index]
            components = dict(candidate.components)
            components.update(
                {
                    "relevance": relevance[index],
                    "diversity": max_sim[index],
                    "mmr": best_mmr,
                    "authority": prior,
                    "recency": decay,
                    "final": best_final,
                }
            )
            selected.append(replace(candidate, score=best_final, components=components))

            if vectors is not None:
                picked_vector = vectors[index]
                for other in remaining:
                    similarity = cosine(vectors[other], picked_vector)
                    if similarity > max_sim[other]:
                        max_sim[other] = similarity

        # Sorted by final rather than left in selection order: a chunk picked
        # late to break up a cluster of duplicates paid a diversity penalty, and
        # a caller truncating to fit a context window should drop the weakest
        # result, not merely the last one chosen.
        selected.sort(key=lambda s: (-s.components["final"], s.chunk.chunk_id))
        log.info(
            "reranked",
            candidates=len(scored),
            returned=len(selected),
            mmr_lambda=lam,
            diversity="on" if vectors is not None else "off",
        )
        return selected

    def _vectors(self, scored: list[ScoredChunk]) -> list[list[float]] | None:
        """Embed every candidate in one call, or `None` if the embedder is unavailable.

        `indexed_text`, matching what the dense index embedded, so the
        similarities here live in the same space as the ones that produced the
        candidates. `None` disables the diversity term only: reranking then
        degrades to relevance plus prior, which is still better than returning
        nothing because a hosted embedder timed out.
        """
        texts = [s.chunk.indexed_text for s in scored]
        try:
            vectors = self.embedder.embed(texts)
        except Exception as e:  # noqa: BLE001 - a hosted embedder is a network call
            log.error(
                "candidate embedding failed, diversity disabled",
                err=f"{type(e).__name__}: {e}"[:200],
            )
            return None
        if len(vectors) != len(texts):
            # A misaligned batch would pair every chunk with someone else's
            # vector and produce a diverse-looking ranking built on nonsense.
            log.error("embedder returned misaligned batch", want=len(texts), got=len(vectors))
            return None
        return vectors

    def _prior(self, document: Document | None, now: float) -> tuple[float, float]:
        """`(prior, decay)` for one candidate: the additive nudge and its recency factor.

        A chunk whose document did not resolve gets the neutral prior rather
        than a zero one - missing provenance is not evidence of a bad source,
        and penalising it would quietly demote every chunk the store lost track
        of.
        """
        authority = 1.0
        updated_at = 0.0
        if document is not None:
            authority = _as_authority(document.metadata.get("authority"))
            updated_at = document.updated_at
        decay = self._decay(updated_at, now)
        return self.config.authority_weight * authority * decay, decay

    def _decay(self, updated_at: float, now: float) -> float:
        """`0.5 ** (age / half_life)`, or 1.0 when recency is off or the age is unusable.

        A missing or zero timestamp means "unknown", not "written in 1970" - the
        epoch would decay to zero and bury every document whose connector did
        not supply a date. Future timestamps (clock skew, a mirror's rewritten
        mtime) clamp to age zero rather than growing the nudge above 1.0.
        """
        half_life = self.config.recency_half_life_days
        if half_life <= 0.0 or updated_at <= 0.0 or not math.isfinite(updated_at):
            return 1.0
        age_days = max(0.0, (now - updated_at) / _SECONDS_PER_DAY)
        return 0.5 ** (age_days / half_life)


def _scale_relevance(scores: list[float]) -> list[float]:
    """Scale fused scores by the best of the set, into (0, 1].

    Min-max was rejected: it pins the worst candidate at exactly 0.0, which
    deletes its relevance term and hands its fate entirely to the diversity
    penalty. RRF scores are compressed by design (rank 40 is worth about 60% of
    rank 1), and that compression is real information about how little the
    candidates differ - dividing by the maximum preserves it.
    """
    best = max(scores, default=0.0)
    if best <= 0.0 or not math.isfinite(best):
        # Everything tied, or the scores are unusable; let diversity and the
        # priors decide rather than dividing by zero.
        return [1.0] * len(scores)
    return [s / best if math.isfinite(s) else 0.0 for s in scores]


def _as_authority(value: object) -> float:
    """Coerce `metadata["authority"]` to a usable multiplier.

    It arrives from connector config and a JSON round trip, so it can be a
    string, `None`, or absent. A negative or non-finite value would invert or
    poison every comparison it touches; both fall back to neutral.
    """
    try:
        authority = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 1.0
    if not math.isfinite(authority) or authority < 0.0:
        return 1.0
    return authority
