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

**What it is worth depends on the corpus, and the paragraph above is only part
of the reason.** MMR earns a case on the primary corpus (19/20 against 18/20,
recall 0.8750 against 0.8125) and costs 0.0116 of precision on the external one
for no cases and no recall, across an 8x range of `candidate_k` (ADR 0004, L74).

Measured rather than guessed at, over each corpus's goldens on the top 8 that
relevance alone returns (`scripts/redundancy_probe.py`). Note what that is and
is not: MMR chooses k from the *whole* reranked candidate list, about 20 items,
so this is not its choice set. It is the list MMR would be replacing, which is
the thing that bounds what MMR can improve - if these 8 are already diverse,
every substitution trades relevance for no diversity, which is the precision
cost observed:

                                 external   primary
    mean pairwise token overlap    0.0480    0.0790
    median                         0.0435    0.0772
    share of pairs same document   0.1085    0.1214
    distinct documents / results   0.7986    0.7312

The direction fits: the corpus where MMR pays is 1.6-1.8x more redundant. But
the *cause* is not the one this docstring names. Same-document pairs are nearly
equally common in both (0.121 against 0.109), so the extra redundancy is not a
document repeating itself in its introduction and conclusion - it is separate
documents covering the same ground, which is what a repository of README,
ARCHITECTURE, PLAN and LEARNINGS files is.

Note also how small both numbers are. At lambda 0.7 the redundancy term is
0.3 * max_similarity, so at most about 0.024 on the primary corpus and 0.014 on
the external one. MMR is a tie-breaker at this scale in both directions, which
is consistent with it moving one case at most either way.
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
