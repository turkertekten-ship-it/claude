"""Maximal marginal relevance.

Top-k by relevance alone reliably returns the same passage five times: a
well-written document says the important thing in the introduction, the summary
and the conclusion, and all three are excellent matches. The generator then gets
one fact repeated five times and no supporting context, in a fixed context
budget that could have held five different facts.

MMR fixes the objective: at each step pick the candidate that maximises

    lambda * relevance - (1 - lambda) * max_similarity_to_already_selected

lambda = 1 is pure relevance; lambda = 0 is pure diversity. Around 0.7 keeps the
best result first while pushing near-duplicates down.
"""

from __future__ import annotations

from typing import Callable, Sequence


def mmr_select(
    candidates: list[tuple[str, float]],
    similarity: Callable[[str, str], float],
    k: int = 8,
    lambda_: float = 0.7,
) -> list[str]:
    if not candidates:
        return []
    remaining = list(candidates)
    selected: list[str] = []
    # The most relevant candidate is always chosen first: diversity is a
    # tie-breaker among good results, never a reason to demote the best one.
    first_id, _ = max(remaining, key=lambda pair: pair[1])
    selected.append(first_id)
    remaining = [pair for pair in remaining if pair[0] != first_id]

    while remaining and len(selected) < k:
        best_id, best_score = None, float("-inf")
        for candidate_id, relevance in remaining:
            redundancy = max((similarity(candidate_id, chosen) for chosen in selected), default=0.0)
            score = lambda_ * relevance - (1.0 - lambda_) * redundancy
            if score > best_score:
                best_id, best_score = candidate_id, score
        if best_id is None:
            break
        selected.append(best_id)
        remaining = [pair for pair in remaining if pair[0] != best_id]
    return selected


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """Token-set overlap: a similarity that needs no vectors, so MMR still works
    when a candidate has no embedding yet."""
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)
