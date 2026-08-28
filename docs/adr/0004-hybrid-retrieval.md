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
`scripts/ablation.py` on the external corpus (266 documents, 3,166 chunks,
54 golden cases), each configuration differing in one thing:

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **41/54** | **0.8140** | 0.2006 | **0.6641** | 0.6872 |
| lexical only | 40/54 | 0.7907 | 0.1948 | 0.6484 | 0.6688 |
| dense only | 37/54 | 0.6744 | 0.1715 | 0.5853 | 0.5955 |
| no rerank | 32/54 | 0.6047 | 0.0901 | 0.5022 | 0.5204 |
| no MMR | 41/54 | 0.8256 | **0.2122** | 0.6615 | **0.6901** |

Hybrid beats *both* arms alone on pass rate for the first time - at 153
documents it was level with the lexical arm - and the arms are complementary in
the way predicted: **dense alone loses 0.14 of recall, lexical alone 0.02**.
Reranking is the single most load-bearing component (+9 cases, +0.21 recall,
+0.11 precision).

**MMR has now measured three values on three corpus sizes**: neutral at 91
documents, worth a case at 153, and at 266 neutral on pass rate and slightly
negative on every metric. It stays on, because a component whose measured worth
oscillates around zero as the corpus grows has not been resolved by this golden
set, and the third reading is no more authoritative than the two before it.

The same run on the primary corpus (84 documents, 864 chunks) says the same
thing about MMR - 18/20 either way - and rates reranking at two cases.

**This table has now been overturned four times, and how it was wrong is the
useful part.**

At 33 documents and 2,615 chunks, 90.9% of them PyPI download boilerplate,
hybrid led dense-only by 0.11 of recall - but that lead was largely the lexical
arm finding rare literal strings in a haystack of hex digests, a property of the
haystack rather than of any question. Removing the boilerplate (L26) erased the
lead entirely: dense-only then matched hybrid on pass rate and recall and beat
it on ordering, and this ADR recorded the case for the lexical arm as weak and
the decision as **deferred to a wider corpus** rather than acting on 36
questions.

Widening the corpus to 91 documents and 54 questions settled it, and settled it
the other way: dense-only is now 0.10 of recall behind. The deferral was right.
Both earlier readings were artifacts of a corpus too small and too polluted to
distinguish the arms, and `recall@8` had reached 0.982 with a median of 1.0 -
close enough to its ceiling that it could not have shown a regression either.

The third time was different in kind, and worth more than the first two. The
table was wrong in its **pass column only**: every metric matched to four
decimal places while every count was four cases stale, because later work moved
the abstention floor and added surface answerability - changes that decide
whether a case passes and never touch a retrieval metric. A partly refreshed
table is worse than a wholly stale one, because the columns that are right
vouch for the one that is wrong. It also changed a reading: at 43 and 43 the two
arms looked tied, at 47 and 44 they are not. The same table had been copied into
`internal/PLAN.md`, where it went stale in exactly the same column - so refresh
it whole, from `scripts/ablation.py`, in both places (L49).

The original coarse measurement failed the same way for the same reason: hit@8
read 26/28 for both hybrid and lexical-only because it saturates on a small
corpus. A metric at its ceiling cannot show a difference, and reading one as
"no difference" is how a component gets removed for being useless when it is
not.

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
