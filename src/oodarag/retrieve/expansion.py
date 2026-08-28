"""Query expansion by pseudo-relevance feedback.

The failure this targets: a question phrased in words the corpus does not use.
"What stops a crawl from running forever?" is answered by a module that says
"bounded by requests, bytes, depth and wall clock" and "never terminates" -
sharing almost no vocabulary with the question. Neither the lexical arm nor a
feature-hashing embedder can bridge that.

Pseudo-relevance feedback bridges it with the corpus itself: run the query, take
the terms that distinguish the top results from the corpus at large, and search
again with those added. No external resource, no model, and the vocabulary comes
from the corpus being searched rather than from a general thesaurus.

**The risk is query drift**, and it is not hypothetical: if the initial results
are wrong, their terms are wrong, and expansion confidently retrieves more of
the same. Three things bound it:

* expansion terms are weighted below the original query, never replacing it;
* the expanded results are a *third* ranked list fused with the other two, so
  expansion can add candidates but cannot evict what the original query found;
* terms are selected by how much more common they are in the feedback set than
  in the corpus, so a term that is merely frequent everywhere is not picked.

## Measured result: OFF by default

It was implemented to fix one documented case and did not fix it. A/B on the
golden sets, everything else identical:

| corpus   | expansion | pass  | recall@8 | nDCG@8 |
|----------|-----------|-------|----------|--------|
| external | off       | 20/20 | 0.800    | 0.7815 |
| external | on        | 20/20 | 0.800    | 0.7815 |
| primary  | off       | 17/20 | 0.625    | 0.4729 |
| primary  | on        | 17/20 | 0.600    | 0.4642 |

No corpus improved; the primary corpus got measurably worse. The target case -
"What stops a crawl from running forever?" - expanded to *"neither candid
markdown below model wrong eval rather"*, drawn from the same wrong results the
unexpanded query returned. Textbook drift, and the three bounds above limited
the damage without preventing it.

The technique is sound and helps on many corpora; it does not help on this one,
where the embedder already does subword matching and the corpus is small. It is
kept, off, with the numbers above, so the next person to reach for it starts
from the measurement instead of repeating it. Turn it on only with an A/B on
your own corpus.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Sequence

from oodarag.models import Chunk
from oodarag.util.text import tokenize


@dataclass(slots=True)
class Expansion:
    terms: list[str]
    weights: dict[str, float]
    source_chunks: list[str]

    @property
    def query(self) -> str:
        return " ".join(self.terms)


def expand(
    query: str,
    feedback: Sequence[Chunk],
    idf: Callable[[str], float],
    *,
    max_terms: int = 8,
    min_lift: float = 1.5,
    corpus_frequency: Callable[[str], float] | None = None,
) -> Expansion:
    """Pick terms that distinguish the feedback set from the corpus.

    `lift` is how much more often a term occurs in the feedback chunks than its
    corpus-wide rate would predict. Selecting on raw frequency instead picks the
    corpus's most common words, which are by definition the least informative
    ones - the classic way pseudo-relevance feedback makes retrieval worse.
    """
    original = set(tokenize(query, stem_words=True))
    if not feedback:
        return Expansion([], {}, [])

    counts: Counter[str] = Counter()
    for chunk in feedback:
        counts.update(set(tokenize(chunk.indexed_text, stem_words=True)))

    scored: list[tuple[float, str]] = []
    for term, count in counts.items():
        if term in original or len(term) < 3:
            continue
        share = count / len(feedback)
        if share < 0.4:          # present in fewer than 40% of the feedback set
            continue
        weight = idf(term)
        if corpus_frequency is not None:
            expected = corpus_frequency(term)
            lift = share / expected if expected > 0 else float("inf")
            if lift < min_lift:
                continue
        # Prefer terms that are both distinctive corpus-wide and consistent
        # across the feedback set.
        scored.append((weight * math.log(1.0 + count), term))

    scored.sort(reverse=True)
    chosen = [term for _, term in scored[:max_terms]]
    total = sum(weight for weight, term in scored[:max_terms]) or 1.0
    weights = {term: weight / total for weight, term in scored[:max_terms]}
    return Expansion(chosen, weights, [c.chunk_id for c in feedback])
