# ADR 0005 - One text analysis, used by every stage

**Status:** accepted

## Context

Adding Porter stemming to the FTS5 index improved lexical recall and made
end-to-end retrieval measurably *worse* (18/19 golden cases to 17/19).

The stemmed lexical arm correctly ranked `answer.py` first for "how does the
system decide to abstain". The reranker, still matching raw tokens, scored that
passage as containing none of the query's terms - "abstained" is not "abstain" -
and pushed the best hit out of the results entirely.

Each half was correct in isolation. The combination was worse than neither.

## Decision

Every stage that compares the same text analyses it identically: the FTS index,
the query, the reranker, the pure-Python BM25 fallback, and extractive sentence
selection. `util/stemming.py` implements the actual Porter algorithm rather than
a suffix-stripping approximation, because SQLite's FTS5 `porter` tokenizer runs
Porter and matching it exactly is the requirement, not a nicety.

## Consequences

**Approximate agreement is not agreement.** A heuristic stemmer would diverge on
irregular cases, and divergence is precisely the failure being fixed.

**Stemming trades precision for recall, and the gate has to absorb it.** With
analysis consistent, the eval got worse again - "recommended" now matched a query
about ibuprofen dosage. The fix was IDF-weighted coverage. A gate built on
unweighted term counts cannot survive higher recall.

**One place deliberately does not stem.** The FTS5 `MATCH` expression is built
from unstemmed tokens, because the porter tokenizer stems both sides of the match
itself; pre-stemming would double-stem the query. The exception is commented at
the call site.

**None of this was visible without measurement.** No test failed, no exception
was raised, no log line appeared. A number moved. A retrieval change without an
eval is a guess.
