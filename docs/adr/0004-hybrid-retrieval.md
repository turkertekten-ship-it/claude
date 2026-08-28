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
54 golden cases, `base_weight` 5.0, `rrf_k` 16), each configuration differing in
one thing:

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **44/54** | **0.8953** | 0.2413 | 0.7198 | 0.7505 |
| lexical only | **44/54** | 0.8837 | 0.2093 | **0.7677** | **0.7803** |
| dense only | 37/54 | 0.6860 | 0.1890 | 0.5853 | 0.6014 |
| no rerank | 38/54 | 0.7442 | 0.1570 | 0.5525 | 0.5899 |
| no MMR | 44/54 | 0.8953 | **0.2442** | 0.7173 | 0.7484 |

**The decision is under pressure from its own gate.** The lexical arm alone ties
hybrid on pass rate here and beats it on MRR and nDCG; hybrid keeps a 0.012 edge
on recall and a wider one on precision. What holds the decision up is the other
corpus: on the primary set hybrid is 19/20 against 18/20 for either arm alone,
and it leads on every metric.

So the arms are kept, and the honest summary is narrower than this ADR's
original claim. Hybrid is *not* reliably better than the lexical arm on this
corpus at these settings; it is better on one corpus, level on the other, and it
is insurance against a corpus where lexical matching fails - which is the case
a hosted embedder would create and this one cannot demonstrate.

**This table has now been overturned six times, and how it was wrong is the
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
