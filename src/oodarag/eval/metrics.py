"""Retrieval metrics.

Each answers a different question, which is why the harness reports all of them:

* **recall@k** - did the right material make it into the window at all? This is
  the ceiling on everything downstream: a generator cannot cite what was never
  retrieved.
* **precision@k** - how much of the window was wasted on irrelevant material?
  Context is a fixed budget; junk in it displaces evidence.
* **MRR** - how high was the *first* correct result? Proxy for whether a human
  scanning the list finds the answer immediately.
* **nDCG@k** - full-ranking quality with graded relevance and positional
  discount. The one to watch when comparing rerankers.

All take `relevant` as a set of ids and `retrieved` as a ranked list.
"""

from __future__ import annotations

import math
from typing import Sequence


def recall_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0  # nothing to find: vacuously satisfied
    hits = len(set(retrieved[:k]) & relevant)
    return hits / len(relevant)


def precision_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Share of the *distinct* retrieved items that are relevant.

    Both sides of the ratio deduplicate. Counting duplicates in the denominator
    while the numerator credited each relevant item once meant a list containing
    the same chunk twice scored below one that did not - reporting a precision
    loss for a diversity problem, which is a different bug with a different fix.
    """
    window = list(dict.fromkeys(retrieved[:k]))
    if not window:
        return 0.0
    return len(set(window) & relevant) / len(window)


def hit_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    return 1.0 if set(retrieved[:k]) & relevant else 0.0


def mrr(retrieved: Sequence[str], relevant: set[str]) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def dcg(gains: Sequence[float]) -> float:
    return sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))


def ndcg_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """nDCG@k, crediting each relevant item once.

    Retrieval returns chunks, and several chunks can map to the same relevant
    document. Scoring each occurrence again makes the achieved DCG exceed the
    ideal - the metric went above 1.0, which for a *normalised* measure is a
    loud signal that it is not measuring what its name says. Only the first
    appearance of a relevant item earns gain, so this answers "how high were the
    distinct expected sources ranked", which is the question worth asking.
    """
    seen: set[str] = set()
    gains: list[float] = []
    for item in retrieved[:k]:
        if item in relevant and item not in seen:
            seen.add(item)
            gains.append(1.0)
        else:
            gains.append(0.0)
    ideal = [1.0] * min(len(relevant), k)
    denominator = dcg(ideal)
    return dcg(gains) / denominator if denominator else 0.0


def summarize(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "min": 0.0, "p50": 0.0, "max": 0.0, "n": 0}
    ordered = sorted(values)
    return {
        "mean": round(sum(ordered) / len(ordered), 4),
        "min": round(ordered[0], 4),
        "p50": round(ordered[len(ordered) // 2], 4),
        "max": round(ordered[-1], 4),
        "n": len(ordered),
    }
