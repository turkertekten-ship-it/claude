# ADR 0002: Dense and BM25, fused by rank

- **Status:** Accepted
- **Date:** 2026-08-27
- **Scope:** `oodarag/retrieve.py`, `oodarag/index/bm25.py`, `oodarag/index/dense.py`

## Context

The two families of retrieval fail in opposite directions, and both failures
are the kind a user notices immediately.

**Dense retrieval misses exact identifiers.** An embedding is a summary; a
summary is where detail goes to die. `k1`, `ECONNRESET`, `0.75`,
`replace_document_chunks`, `v2.3.1` — these are tokens whose whole meaning is
their exact spelling, and a vector space built to place *similar* things
together is built to place them together too. The user who searched for an
error code and got four pages about error handling in general does not conclude
that the ranking is subtly off. They conclude the search is broken, and they
are right: they gave the system the most specific possible query and it threw
the specificity away. This pipeline's embedder (ADR 0001) is a hashing
embedder, which makes the problem sharper, not milder — it has no learned
notion of "this token is rare and therefore load-bearing".

**Lexical retrieval misses paraphrase.** BM25 matches strings. A question
asking "why is meaning-based search alone not enough?" against a document that
says "pure dense retrieval fails on exact identifiers" shares almost no content
tokens with its own answer. Every user who does not already know the corpus's
vocabulary is asking that kind of question, which is to say: every new user.

Neither failure is fixable inside the other arm. Tuning BM25's `k1` and `b` does
not teach it synonyms, and no amount of embedding dimensionality makes a
hashing embedder respect an exact string.

## Decision

**Run both arms on every query and fuse them by rank, using Reciprocal Rank
Fusion.**

```
score(chunk) = Σ_arm  weight_arm / (rrf_k + rank_arm(chunk))
```

with `rrf_k = 60` and both weights at 1.0 by default (`RetrievalConfig`).

The mechanics that matter:

- **Both arms are over-fetched, then cut.** Each is asked for `candidates` (40)
  results to produce `k` (8). Fusion can only rank what it was handed, and a
  chunk both arms place tenth is usually a better answer than one a single arm
  places first — it cannot win if the arms were only asked for eight.
- **Rank in, rank out.** The fused score never touches an arm's raw score. Raw
  scores ride along in `ScoredChunk.components` for debugging and are read by
  nothing that ranks.
- **A missing arm contributes nothing, and says so.** When only one arm returns
  a chunk, `components["<arm>_rank"]` is `MISSING_RANK` (0.0, out of band
  because real ranks are 1-based) and that arm adds no term to the sum. It would
  be easy to write a plausible 0.0 *score* instead; that is a lie the dense arm
  tells convincingly, since a cosine of 0.0 is a real value meaning "orthogonal"
  rather than "never saw this chunk".

### What was measured

On the seed corpus (9 documents, 48 chunks), 15 labelled goldens, k=8:

| arm | MRR | hit@1 | hit@8 |
|---|---|---|---|
| BM25 only | 1.000 | 1.000 | 1.000 |
| dense only | 0.967 | 0.933 | 1.000 |
| RRF fusion | 1.000 | 1.000 | 1.000 |

**Hybrid does not win on this corpus, and the honest reading is that the corpus
cannot show a win.** Nine hand-written documents whose goldens were written
against them are close to the best case for lexical matching: the questions use
the documents' own vocabulary. Any design argument resting on this table alone
would be an argument that hybrid retrieval is unnecessary.

The discrimination shows up on paraphrases the goldens do not contain. Rank of
the correct document, same index:

| query | BM25 | dense | RRF |
|---|---|---|---|
| "Why is meaning-based search alone not enough?" | #4 | #2 | #3 |
| "How do I merge two result lists that score things differently?" | #1 | #2 | #1 |
| "What do I do when someone pastes an error code into the search box?" | #8 | #2 | #3 |

That is the actual shape of the benefit, and it is worth stating precisely
because it is not the shape people advertise: **RRF does not take the better
arm's rank. It lands between them.** It is a variance reducer, not a maximizer.
The BM25 column swings between #1 and #8 depending on whether the user happened
to use the document's words; the fused column stays between #1 and #3. What is
being bought is the elimination of the bad tail, paid for by giving up a little
of the best case.

## Consequences

**Fusion only pays on the query classes each arm was built for.** This is the
consequence that took longest to see, and it was invisible in aggregate.
Measured over the golden set as a whole, hybrid retrieval scores *below* BM25
alone (0.842 against 0.886 MRR) — the documented weakest-link effect of
unweighted RRF, where an equal vote from a weaker arm drags good hits down.
Read on its own, that number says the second index is dead weight.

Measured per query class it reverses. The dense arm here is a
character-n-gram hashing embedder, so its home class is degraded input, and
the golden set's clean questions never exercised it:

| typos per query | BM25 | dense | hybrid | best arm |
|---|---|---|---|---|
| 0 | **0.886** | 0.764 | 0.842 | BM25 |
| 4 | 0.688 | 0.674 | **0.723** | fusion beats both |
| 6 | 0.474 | 0.511 | **0.583** | fusion beats both |

From four typos onward fusion beats *both* arms, which is real fusion gain
rather than a weighted average of two rankings. The dense arm overtakes BM25 at
six. So the honest statement of this decision's value is conditional: equal
weights cost about 0.04 MRR on clean queries and buy 0.03 to 0.11 on noisy
ones. For a corpus of clean, well-spelled queries over well-written documents,
BM25 alone would be the better engineering choice and this ADR would not
survive its own evidence.

**Re-weighting is not the fix, and was tested rather than assumed.** Sweeping
`lexical_weight` from 1.0 to 5.0 on clean queries is monotone and never crosses
BM25-alone (1.0 → 0.546, 3.0 → 0.661, 5.0 → 0.664, against 0.671 for BM25 by
itself). Weighting the dense arm down only asymptotically approaches ignoring
it, while destroying the noisy-query gain that justifies having it. The
1.0 / 1.0 default therefore stands as a deliberate choice, not an untuned one.

**The invariant is guarded in the suite, in both directions.**
`tests/test_fusion_invariant.py` asserts that fusion beats its best single arm
on noisy queries, that the dense arm still wins its home class, and that the
clean-query deficit stays bounded. The last of those pins a number this ADR
admits is a loss, so it cannot quietly grow into a reason the whole approach
stops being worth it.

**Two indexes to keep in sync.** `BM25Index` and `DenseIndex` are both derived
from the store, and a write that updates one without the other produces answers
from a corpus that no longer exists — stale but plausible, the hardest kind of
wrong to notice. The pipeline handles this by never rebuilding on write: an
ingest marks the indexes stale and `ask()` rebuilds both, together, on demand.
`Pipeline.stats()` reports `bm25_chunks` and `dense_vectors` alongside the
store's own counts so a divergence is visible rather than inferred. The two
arms are also refilled through `.build()` rather than rebound, so the retriever
holding references to them can never end up querying a discarded index.

**More memory, and the dense arm is the expensive half.** The corpus is
resident twice: an inverted index (posting lists, cheap — see the measurements
in ADR 0001) plus a full vector per chunk (~25 KB each on the stdlib path).
Removing the dense arm would roughly eliminate the memory ceiling; that is the
real cost of keeping it, and it is why ADR 0001's size thresholds are dominated
by the dense side.

**One more knob, and knobs are where retrieval systems go to die.**
`RetrievalConfig` now carries `rrf_k`, `dense_weight` and `lexical_weight` on
top of `k` and `candidates`. The mitigation is procedural rather than technical:
retrieval changes are settled by `make eval` before and after, one knob at a
time. A change that moves no metric does not ship, however principled it sounds.

**Every hit can be attributed.** `components` carries `bm25_rank`, `dense_rank`,
`bm25`, `dense` and `rrf` for every returned chunk, which `ooda query --verbose`
prints as one line per citation. "Which arm found this?" is answerable without a
debugger, and a change that quietly kills one arm shows up as a column of `-`
rather than as a slightly worse number three weeks later.

**The fused score is ordinal and cannot be thresholded.** It says this chunk
beat that one; it does not say either is any good. RRF at rank 1 in one arm is
about 1/61 ≈ 0.016 whether the corpus is perfect or worthless. Anything needing
a confidence — the generator's abstention floor, most obviously — must compute
it from evidence rather than from this number, and `ExtractiveGenerator` does
exactly that.

## Alternatives considered

**Normalize the scores, then add them.** Rejected, and this is the alternative
worth being specific about, because it is the one that looks obviously fine.

Over the 15 labelled goldens on the seed corpus, the two arms' scores ranged:

- BM25: 0.51 to 24.36
- cosine: −0.046 to 0.533

These are not two scales; they are two different kinds of quantity. BM25 is an
unbounded sum over query terms whose magnitude depends on the query's length,
the corpus's IDF distribution and the average document length. Cosine is a
bounded geometric quantity on [−1, 1]. Min-max normalizing each per query makes
the top hit of both arms exactly 1.0 — including the query where the dense arm
returned nothing relevant at all, which is precisely when you need it to
contribute least.

The deeper objection is drift. Any normalization is fitted to a corpus:
`avgdl` moves as documents are added, the IDF distribution shifts as the
vocabulary grows, and the constants that made the blend behave stop being the
right constants. Nothing fails. The weights silently stop meaning what they
meant, retrieval quality erodes over months, and the eval that would have caught
it was run before the corpus tripled. Ranks have no such parameter: rank 3 is
rank 3 in a corpus of 40 chunks and in a corpus of 4 million.

**Dense only.** Simplest, one index, half the memory. Rejected on the exact
identifier case — see the "error code" row above, where the dense arm is
respectable (#2) but the system as a whole has thrown away the strongest signal
the user gave it. On a corpus that is half code and half prose, which is what
this pipeline targets, exact tokens are not an edge case.

**Lexical only.** Cheapest by a wide margin: BM25 search stays under a
millisecond at 10,000 chunks against the dense arm's 123 ms, needs no embedder
and no vector storage, and on the seed corpus it *wins outright*. Rejected on
the paraphrase rows: its rank of the correct document swings from #1 to #8
depending on vocabulary the user cannot be expected to guess. If the dense arm
is ever removed for cost reasons, that swing is what is being accepted, and the
paraphrase probes above are the test that will show it.

**Learned fusion, or a cross-encoder reranker.** Better than both, and both
require a trained model — out of scope under ADR 0001. The seam is already
there: `Reranker` takes an `Embedder` and rewrites `components["final"]`, so a
cross-encoder slots in behind the same call without retrieval knowing.
