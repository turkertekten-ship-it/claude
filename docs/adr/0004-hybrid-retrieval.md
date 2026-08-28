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

## Measured

The argument above is an argument. These are the numbers, from
`scripts/ablation.py` on the external corpus (33 documents, 253 chunks,
36 golden cases), each configuration differing in one thing:

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **33/36** | **0.982** | 0.281 | 0.879 | 0.883 |
| lexical only | 32/36 | 0.946 | 0.268 | 0.874 | 0.871 |
| dense only | **33/36** | **0.982** | 0.299 | **0.884** | **0.901** |
| no rerank | 32/36 | 0.893 | 0.152 | 0.833 | 0.817 |
| no MMR | **33/36** | **0.982** | **0.313** | 0.879 | 0.888 |

**This table no longer says what it used to, and the honest reading is that the
case for the lexical arm is now weak.** On the corpus as it stands, dense alone
matches hybrid on pass rate and recall and beats it on precision, MRR and nDCG.
Lexical alone is the worst of the three. Reranking remains clearly load-bearing
(+1 case, +0.09 recall, +0.13 precision); MMR costs precision and buys nothing
measurable here.

The previous table, taken before the corpus was cleaned (L26), showed hybrid
ahead of dense-only by 0.11 of recall. That corpus was 90.9% PyPI download
boilerplate, and the lexical arm's apparent advantage was largely its ability to
find a rare literal string in a haystack of hex digests - a property of the
haystack, not of the queries anyone asks. Removing the boilerplate removed the
advantage.

What this ADR should be judged on has therefore not been measured yet: whether
the two arms fail in uncorrelated ways on questions a person would ask, over a
corpus big enough for it to matter. 36 questions over 33 documents cannot settle
it, and `recall@8` on this corpus is now 0.982 with a median of 1.0 - close
enough to its ceiling that it can no longer show a regression. **Hybrid stays
for now because removing an arm on 36 questions would be the same mistake in the
other direction, and the decision is deferred to a wider corpus** (PLAN, "next").

A coarser measurement said something different again: hit@8 was 26/28 for both
hybrid and lexical-only, because hit@8 saturates on a corpus this size. A metric
at ceiling cannot show a difference, and reading one as "no difference" is how a
component gets removed for being useless when it is not. That is now true of
recall@8 here too.

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
