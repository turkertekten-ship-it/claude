"""Reranking.

Fusion produces a good candidate ordering from two weak signals. Reranking is
where cheap, high-precision evidence that neither retrieval arm can see gets
applied: whether the query's rare terms actually appear, whether the phrase
appears intact, how authoritative the source is, and how old it is.

The heuristic reranker below is deliberately transparent - every component is
recorded on the result - because an opaque reranker that reorders results for
reasons nobody can inspect is worse than none. A cross-encoder or LLM reranker
implements the same interface and can replace it where the latency is affordable.
"""

from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

from oodarag.models import ScoredChunk
from oodarag.util.text import tokenize, tokenize_all


class Reranker(ABC):
    name = "reranker"

    @abstractmethod
    def rerank(self, query: str, results: list[ScoredChunk]) -> list[ScoredChunk]: ...


@dataclass
class HeuristicReranker(Reranker):
    """Feature-based reranking with an auditable score breakdown."""

    name: str = "heuristic"
    #: Maps a stemmed term to its inverse document frequency. Without it every
    #: query word counts equally and coverage stops discriminating - see
    #: SqliteStore.idf_table for what that costs.
    idf: Callable[[str], float] | None = field(default=None)
    coverage_weight: float = 0.45
    phrase_weight: float = 0.25
    authority_weight: float = 0.12
    recency_weight: float = 0.08
    position_weight: float = 0.05
    base_weight: float = 1.0
    half_life_days: float = 365.0

    def rerank(self, query: str, results: list[ScoredChunk]) -> list[ScoredChunk]:
        # Stemmed, to match the FTS5 index. Raw-token coverage scores a passage
        # saying "abstained" as containing none of a query for "abstain", and
        # so demotes the exact passages the lexical arm ranked first.
        query_terms = tokenize(query, stem_words=True)
        query_set = set(query_terms)
        phrase = " ".join(tokenize_all(query))
        now = time.time()

        for result in results:
            chunk = result.chunk
            haystack = chunk.indexed_text.lower()
            chunk_terms = set(tokenize(haystack, stem_words=True))

            if not query_set:
                coverage = 0.0
            elif self.idf is None:
                coverage = len(query_set & chunk_terms) / len(query_set)
            else:
                # Weighted by informativeness: matching a term that appears
                # everywhere is not evidence, matching a rare one is.
                total_weight = sum(self.idf(t) for t in query_set)
                matched_weight = sum(self.idf(t) for t in query_set & chunk_terms)
                coverage = matched_weight / total_weight if total_weight else 0.0
            # Exact phrase match is rare and highly diagnostic; partial credit
            # for a long shared prefix keeps it from being all-or-nothing.
            if phrase and phrase in haystack:
                phrase_score = 1.0
            else:
                phrase_score = _longest_common_run(phrase, haystack)

            authority = float(chunk.metadata.get("authority", 1.0))
            authority_score = max(0.0, min(1.5, authority)) / 1.5

            updated = float(chunk.metadata.get("updated_at") or 0.0)
            if updated:
                age_days = max(0.0, (now - updated) / 86400.0)
                recency = math.exp(-age_days / self.half_life_days)
            else:
                recency = 0.5  # unknown age is neither fresh nor stale

            # Earlier chunks of a document are usually its thesis; later chunks
            # are detail. A weak preference, not a strong one.
            position = 1.0 / (1.0 + 0.15 * chunk.ordinal)

            adjustment = (
                self.coverage_weight * coverage
                + self.phrase_weight * phrase_score
                + self.authority_weight * authority_score
                + self.recency_weight * recency
                + self.position_weight * position
            )
            # Relevance is kept separate from the priors on purpose. Authority,
            # recency and position are query-independent: they raise a chunk's
            # score whether or not it has anything to do with the question. Fold
            # them into one number and the total stops being usable as an
            # "is this relevant at all" signal - an irrelevant chunk from a
            # trusted, recent source outscores the abstention floor and the
            # system answers confidently from nothing. Ordering uses the total;
            # the abstention gate uses `rerank_relevance` alone.
            relevance = 0.6 * coverage + 0.4 * phrase_score

            result.components.update({
                "rerank_relevance": relevance,
                "rerank_coverage": coverage,
                "rerank_phrase": phrase_score,
                "rerank_authority": authority_score,
                "rerank_recency": recency,
                "rerank_position": position,
                "rerank_adjustment": adjustment,
                "pre_rerank_score": result.score,
            })
            result.score = self.base_weight * result.score + adjustment

        results.sort(key=lambda r: r.score, reverse=True)
        return results


def _longest_common_run(phrase: str, haystack: str) -> float:
    """Fraction of the query phrase present as one contiguous run.

    Cheap proxy for proximity: a chunk containing "reciprocal rank fusion"
    should outrank one that merely contains all three words scattered apart.
    """
    words = phrase.split()
    if not words:
        return 0.0
    for length in range(len(words), 1, -1):
        for start in range(0, len(words) - length + 1):
            if " ".join(words[start:start + length]) in haystack:
                return length / len(words)
    return 0.0
