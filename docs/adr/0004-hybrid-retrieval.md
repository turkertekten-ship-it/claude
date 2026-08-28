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
`scripts/ablation.py` on the external corpus (153 documents, 1,802 chunks,
54 golden cases), each configuration differing in one thing:

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **49/54** | **0.9302** | 0.2471 | **0.7643** | **0.7958** |
| lexical only | **49/54** | 0.9186 | 0.2442 | 0.7581 | 0.7839 |
| dense only | 42/54 | 0.7209 | 0.2122 | 0.6860 | 0.6831 |
| no rerank | 39/54 | 0.6977 | 0.1134 | 0.6196 | 0.6258 |
| no MMR | **49/54** | **0.9302** | **0.2587** | 0.7620 | 0.7945 |

The decision stands, and the case for it is narrower than it was. **Hybrid no
longer beats either arm alone on pass rate** - it ties lexical-only at 49/54,
and leads only on recall (+0.012), MRR (+0.006) and nDCG (+0.012). The pass
column reads the abstention gate and the metric columns do not, so the two need
not move together; what carries the decision now is ordering and recall, not
cases.

The arms are no longer close to complementary in the way first predicted:
**dense alone is 0.21 of recall behind**, up from 0.10, while lexical alone
gives up 0.012. Reranking remains the single most load-bearing component
(+10 cases, +0.23 recall, +0.13 precision).

**MMR has now reversed a fourth time - on this corpus.** On external it is back
to costing more than it buys: identical pass rate, identical recall, +0.0013 of
nDCG, for **-0.0116 of precision**. On the primary corpus, run in the same
sweep, it earns a case and 0.0625 of recall (19/20 and 0.8750 with, 18/20 and
0.8125 without) and gains precision as well.

So MMR is not simply neutral, harmful or helpful: it is corpus-dependent, and the same
is true of the arms' balance (L58 found the two corpora wanting opposite
`base_weight` values). Quoting the external row alone - the habit this table
encourages, since external is the gate - would have recorded "MMR costs
precision for nothing" as a general fact about the component. It is a fact about
one corpus.

### The `candidate_k` hypothesis, measured

Both reversals were first written up here with one explanation: `candidate_k`
was halved 40 -> 20 this session, so the weaker arm has fewer chances to land a
hit and MMR has less redundancy to remove. `scripts/candidate_k_arms.py` sweeps
k with each arm disabled, on the external corpus:

| configuration | k=10 | k=20 | k=40 | k=80 |
|---|---|---|---|---|
| hybrid | 46/54 r0.872 p0.253 | **49/54** r0.930 p0.247 | 49/54 r0.930 p0.247 | 49/54 **r0.942** p0.235 |
| dense only | 39/54 r0.663 p0.203 | 42/54 r0.721 p0.212 | **44/54 r0.814** p0.209 | 43/54 r0.814 p0.203 |
| lexical only | 48/54 r0.907 p0.244 | **49/54** r0.919 p0.244 | 49/54 r0.919 p0.227 | 48/54 r0.895 p0.218 |
| no MMR | 46/54 r0.872 p0.253 | 49/54 r0.930 **p0.259** | 49/54 r0.930 **p0.262** | 49/54 r0.942 **p0.244** |

**One hypothesis, two answers.**

*For the dense arm it holds exactly.* Dense-only goes 39, 42, **44**, 43 as k
rises, and at k=40 it reads 44/54 with recall 0.814 - the number this ADR
recorded before `candidate_k` was halved, to three decimals. The arm never got
worse; the window in front of it got smaller. Hybrid meanwhile is flat at 49/54
for k=20, 40 and 80, which is why the original `candidate_k` sweep - run on the
hybrid configuration alone - correctly saw nothing. A parameter can be neutral
for the whole and decisive for a part.

*For MMR it is false, in the direction that matters.* If MMR were starved of
redundancy at k=20, more candidates would restore its value. Instead its cost
**grows** with k:

    k              |   10     20     40     80
    MMR on pass    |   +0     +0     +0     +0
    MMR on recall  | +0.000 +0.000 +0.000 +0.000
    MMR on prec@8  | +0.000 -0.012 -0.015 -0.009

Across an 8x range of candidate set size, MMR changes the pass rate and recall
of this corpus **not at all**, and only ever costs precision. Whatever reversed
it, `candidate_k` is not it - most likely the reranker changes earlier this
session, which already order the top of the list by coverage and position, but
that is unmeasured and is deliberately not written down as a second story to
replace the first.

A last thing this table says that the ablation could not: **lexical-only beats
hybrid at k=10** (48/54 against 46/54). The dense arm is not merely weaker
there, it is actively costing cases when the window is tight.

For the primary corpus (84 documents, 868 chunks, 20 cases), same run:

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **19/20** | **0.8750** | **0.2422** | **0.6219** | **0.6483** |
| lexical only | **19/20** | 0.8438 | 0.2188 | 0.6036 | 0.6316 |
| dense only | 18/20 | 0.7812 | 0.2188 | 0.5755 | 0.5896 |
| no rerank | 16/20 | 0.7500 | 0.1797 | 0.5714 | 0.5450 |
| no MMR | 18/20 | 0.8125 | 0.2266 | 0.6172 | 0.6313 |

**This table has now been wrong four times, and how it was wrong is the useful
part.**

The fourth time cost nothing because it was found by re-running the command
rather than by trusting the file: six retrieval parameters and two chunking
defects had changed underneath it since the numbers above were last taken, and
every row moved. Two readings inverted - hybrid's pass-rate lead over lexical
disappeared, and MMR went from earning a case to costing precision for nothing.
A decision record whose measurements are stale argues for its decision with
evidence that no longer exists.

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
