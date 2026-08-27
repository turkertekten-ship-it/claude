"""Reciprocal rank fusion.

Combining a dense list with a lexical list means combining two scores that are
not on the same scale and never will be: cosine similarity lives in [-1, 1] and
is roughly linear; BM25 is unbounded and corpus-dependent. Normalising them into
a weighted sum requires calibration that drifts every time the corpus changes.

RRF sidesteps the problem by discarding the scores and using only the ranks:

    score(d) = sum over lists of  weight / (k + rank(d))

`k` (60 by convention, from the original TREC work) damps the top-rank advantage
so a document ranked 1st in one list and absent from the other does not
automatically beat a document ranked 3rd in both - which is exactly the
behaviour you want from a hybrid retriever, since agreement across two different
retrieval mechanisms is the strongest signal available.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RankedList:
    name: str
    results: list[tuple[str, float]]
    weight: float = 1.0


def reciprocal_rank_fusion(
    lists: list[RankedList], k: int = 60, top_k: int = 50,
) -> list[tuple[str, float, dict[str, float]]]:
    """Fuse ranked lists. Returns (id, fused_score, per-list contributions)."""
    fused: dict[str, float] = {}
    components: dict[str, dict[str, float]] = {}
    for ranked in lists:
        for rank, (item_id, raw_score) in enumerate(ranked.results, start=1):
            contribution = ranked.weight / (k + rank)
            fused[item_id] = fused.get(item_id, 0.0) + contribution
            entry = components.setdefault(item_id, {})
            entry[f"{ranked.name}_rank"] = float(rank)
            entry[f"{ranked.name}_score"] = float(raw_score)
            entry[f"{ranked.name}_rrf"] = contribution
    ordered = sorted(fused.items(), key=lambda pair: pair[1], reverse=True)
    return [(item_id, score, components.get(item_id, {})) for item_id, score in ordered[:top_k]]
