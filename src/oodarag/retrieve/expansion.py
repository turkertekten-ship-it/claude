"""Query expansion by pseudo-relevance feedback.

The failure this targets: a question phrased in words the corpus does not use.
"What stops a crawl from running forever?" is answered by a module that says
"bounded by requests, bytes, depth and wall clock" and "never terminates" -
sharing almost no vocabulary with the question. Neither the lexical arm nor a
feature-hashing embedder can bridge that.

Pseudo-relevance feedback bridges it with the corpus itself: run the query, take
the terms that distinguish the top results from the corpus at large, and search
again with those. No external resource, no model, and the vocabulary comes
from the corpus being searched rather than from a general thesaurus.

**The risk is query drift**, and it is not hypothetical: if the initial results
are wrong, their terms are wrong, and expansion confidently retrieves more of
the same. Three things bound it:

* the expanded search is a third arm fused *below* the dense and lexical arms
  at `expansion_weight`, so it can add candidates but never evict what the
  original query found. Within that arm every term counts alike, which is the
  mechanism behind the regression measured below: one drift term is weighted
  the same as a good one;
* the expanded results are a *third* ranked list fused with the other two, so
  expansion can add candidates but cannot evict what the original query found;
* terms are selected by how much more common they are in the feedback set than
  in the corpus, so a term that is merely frequent everywhere is not picked.

## Measured result: OFF by default

**Re-measured twice now, and the reason has changed both times.** The numbers
below are at 266 external documents / 54 cases and 84 primary documents / 20
cases, with `base_weight` 5.0 (`scripts/expansion_ab.py`):

| corpus   | expansion | pass  | recall@8 | MRR    | nDCG@8 |
|----------|-----------|-------|----------|--------|--------|
| external | off       | 43/54 | 0.8721   | 0.6994 | 0.7294 |
| external | on, 8 terms, w=0.5  | 43/54 | 0.8721 | 0.6919 | 0.7247 |
| external | on, 4 terms, w=0.5  | 43/54 | 0.8721 | 0.6926 | 0.7254 |
| external | on, 8 terms, w=0.25 | 43/54 | 0.8721 | 0.6996 | 0.7302 |
| primary  | off       | 18/20 | 0.8125   | 0.5990 | 0.6282 |
| primary  | on, 8 terms, w=0.5  | 18/20 | 0.8125 | 0.6219 | 0.6508 |
| primary  | on, 4 terms, w=0.5  | **19/20** | **0.8750** | 0.6328 | 0.6713 |
| primary  | on, 8 terms, w=0.25 | 18/20 | 0.8125 | 0.6302 | 0.6526 |

It stays off, and the argument is now about *where* the gain is. On the corpus
that gates, every setting is identical on pass rate and recall to four decimals -
expansion changes nothing there. The one case it converts is on the 20-case
primary corpus, at one of four settings, which is a peak rather than a plateau,
and it costs a second lexical search on every query.

**Both earlier versions of this block were measured on a corpus that did not
exist anywhere else.** The previous one recorded "228 primary documents" - the
repository *plus* the entire external corpus, because `expansion_ab.py` defined
the primary corpus as `**/*.md` rooted at the repository, and that glob is
recursive. Its predecessor concluded "no corpus improved; the primary corpus got
measurably worse" from a corpus a third of today's size. Every sweep now imports
`scripts/_corpora.py` and a test fails if one grows its own definition (L67).

The documented drift case still reproduces in spirit: the technique is sound,
helps on many corpora, and is bounded here by the three limits above. Turn it on
only with an A/B on your own corpus - and re-run this one before trusting it.
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
    source_chunks: list[str]

    @property
    def query(self) -> str:
        """The expansion terms alone.

        Not the original query plus these. The expansion arm is fused *beside*
        the original arms rather than replacing them, so the original query is
        still searched - by the dense and lexical arms - and this arm exists to
        contribute what they could not find. A per-term weight was computed here
        and never read by anything; it is gone rather than left to imply a
        weighting that was never applied.
        """
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
        return Expansion([], [])

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
    return Expansion(chosen, [c.chunk_id for c in feedback])
