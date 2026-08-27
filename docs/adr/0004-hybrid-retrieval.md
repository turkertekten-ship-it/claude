# ADR 0004 - Hybrid retrieval fused by rank, not score

**Status:** accepted

## Context

Dense retrieval misses exact tokens - error codes, flags, function names,
versions - because embedding blurs them. Lexical retrieval misses paraphrase.
Combining them requires reconciling cosine similarity in [-1, 1] with unbounded,
corpus-dependent BM25 scores.

## Decision

Run both arms over the same pre-filtered candidate set, fuse with Reciprocal
Rank Fusion, rerank on transparent IDF-weighted features, then diversify with
MMR.

## Consequences

**Rank, not score.** Normalising two incomparable scales into a weighted sum
needs calibration that drifts every time the corpus changes. RRF discards the
magnitudes and uses only positions, so agreement across two different retrieval
mechanisms - the strongest available signal - wins over a single first place.

**Pre-filter, never post-filter.** Both arms take the same allowed-id set.
Filtering a top-k list afterwards is how a request for ten results returns three.

**The reranker is transparent on purpose.** Every component is recorded on the
result. A reranker that reorders for reasons nobody can inspect is worse than
none, and the score breakdown is what made two real bugs findable:

- Relevance had to be separated from source priors. Authority and recency are
  query-independent, so an irrelevant chunk from a trusted recent source cleared
  the abstention floor and out-of-corpus questions were answered confidently.
  Ordering uses the total; the abstention gate uses relevance alone.
- Coverage had to be IDF-weighted. Unweighted, "recommended" satisfied a quarter
  of a query about ibuprofen dosage. Matching a term that appears everywhere is
  not evidence.

**MMR is a tie-breaker, not a re-ranking.** The most relevant result is always
selected first; diversity only decides among the rest. A well-written document
states its thesis in the introduction, the summary and the conclusion, and all
three match - filling a fixed context budget with one fact stated three times.
