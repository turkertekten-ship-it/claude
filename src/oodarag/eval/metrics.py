"""Retrieval and answer metrics. Pure functions, no state, no dependencies.

The README's stated reason for this project's existence is the question "did
last week's change make retrieval better or worse". That question has no answer
without these, which is why an unmeasured system is treated here as a finding
rather than a neutral state.

Every function takes ranked ids and a set of relevant ids and returns a float in
[0, 1]. Empty inputs return 0.0 rather than raising: a metric that raises on an
empty result set turns "retrieval found nothing" into a crash, and losing that
distinction is exactly how a silent regression survives.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def recall_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    rel = set(relevant)
    if not rel:
        return 0.0
    return len(rel & set(ranked[:k])) / len(rel)


def precision_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    if k <= 0 or not ranked:
        return 0.0
    rel = set(relevant)
    window = ranked[:k]
    return len(rel & set(window)) / len(window)


def mrr(ranked: Sequence[str], relevant: Iterable[str]) -> float:
    """Reciprocal rank of the FIRST relevant hit. Rewards getting it right first."""
    rel = set(relevant)
    for i, item in enumerate(ranked, start=1):
        if item in rel:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Binary-gain nDCG. Unlike recall it cares where in the list a hit landed."""
    rel = set(relevant)
    if not rel:
        return 0.0
    dcg = sum(1.0 / math.log2(i + 1) for i, item in enumerate(ranked[:k], start=1)
              if item in rel)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(rel), k) + 1))
    return dcg / ideal if ideal else 0.0


def citation_coverage(n_covered: int, n_sentences: int) -> float:
    return n_covered / n_sentences if n_sentences else 0.0


def abstention_rate(abstained: Sequence[bool]) -> float:
    return sum(1 for a in abstained if a) / len(abstained) if abstained else 0.0


def calibration_error(confidences: Sequence[float], correct: Sequence[bool],
                      bins: int = 5) -> float:
    """Expected calibration error: mean gap between stated and realised accuracy.

    A system claiming 0.9 confidence and being right half the time is more
    dangerous than one that says 0.5, because the number is what a reader
    delegates their judgement to. This is the check that catches that.
    """
    if not confidences or len(confidences) != len(correct):
        return 0.0
    n = len(confidences)
    total = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(confidences)
               if (lo <= c < hi) or (b == bins - 1 and c == 1.0)]
        if not idx:
            continue
        avg_conf = sum(confidences[i] for i in idx) / len(idx)
        acc = sum(1 for i in idx if correct[i]) / len(idx)
        total += (len(idx) / n) * abs(avg_conf - acc)
    return total
