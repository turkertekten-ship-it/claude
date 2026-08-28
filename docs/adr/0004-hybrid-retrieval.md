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
`scripts/ablation.py` on the external corpus (33 documents, 2,615 chunks,
36 golden cases), each configuration differing in one thing:

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **32/36** | **0.929** | 0.295 | 0.874 | **0.863** |
| lexical only | 31/36 | 0.893 | 0.272 | **0.878** | 0.850 |
| dense only | 31/36 | 0.821 | **0.339** | 0.780 | 0.785 |
| no rerank | 31/36 | 0.857 | 0.165 | 0.798 | 0.792 |
| no MMR | 32/36 | 0.911 | 0.304 | 0.874 | 0.863 |

Hybrid beats either arm alone on pass rate and recall, which is the claim. The
arms are complementary in the way predicted but not symmetric: **dense is more
precise, lexical has better recall**, and dense alone loses 0.11 of recall.

Reranking is worth +1 case, +0.07 recall and +0.13 precision. MMR is worth
+0.02 recall - small here, larger on the primary corpus (0.75 to 0.81), because
that corpus has more near-duplicate chunks per document.

A coarser measurement said something different: hit@8 was 26/28 for both hybrid
and lexical-only, because hit@8 saturates on a corpus this size. A metric at
ceiling cannot show a difference, and reading one as "no difference" is how a
component gets removed for being useless when it is not.

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
