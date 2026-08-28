# Evaluation

> A RAG system without an evaluation harness is not engineered, it is
> demonstrated.

## Running it

```bash
ooda eval                                   # markdown report
ooda eval --json --out report.md            # machine-readable + written report
ooda eval --min-pass-rate 0.85              # CI gate: non-zero exit below the floor
ooda eval --exclude-source chat             # hold a source out of the eval index
```

## The golden set

`evals/goldens.jsonl`, one JSON object per line:

```json
{"question": "...", "expect_sources": ["crawler.py"], "expect_answer_contains": ["budget"]}
{"question": "What is the capital of France?", "expect_abstain": true}
```

`expect_sources` are substrings matched against a retrieved document's URI or
title - deliberately *not* chunk ids, which change whenever the chunker's
configuration changes. A golden set that must be rewritten every time the code
changes is a golden set nobody maintains.

**Negative cases matter as much as positive ones.** `expect_abstain` asserts the
system refuses questions the corpus cannot answer, which is the behaviour that
separates a grounded system from a merely confident one. A harness with only
positive cases cannot tell the difference.

## The metrics, and what each is for

| Metric | Question it answers |
|---|---|
| recall@k | Did the right material reach the window at all? Ceiling on everything downstream. |
| precision@k | How much of a fixed context budget was wasted? |
| hit@k | Was *anything* relevant retrieved? The blunt pass/fail. |
| MRR | How high was the first correct result? |
| nDCG@k | Full ranking quality with positional discount. Watch this when changing the reranker. |
| citation coverage | Share of claim sentences carrying a citation. Grounding of the *answer*. |
| abstention correctness | Does it refuse what it cannot answer? |
| latency | Per-case wall clock. |

One number hides regressions. Recall can hold steady while nDCG collapses,
which means the right documents are still arriving and arriving in the wrong
order - a reranker problem, not a retrieval problem.

**Retrieval metrics are computed over graded cases only** - the ones stating
`expect_sources`. An `expect_abstain` case has nothing to retrieve, so its
recall is definitionally zero, and averaging those zeros in means adding a
negative case *lowers reported recall* for a reason unrelated to retrieval.
Reported external recall@8 read 0.80 while every graded case was in fact fully
satisfied; scoping the denominator correctly reads 1.00. The report states how
many cases were graded so the denominator is never a guess.

## Contamination - the metric nobody reports

**If the corpus contains the evaluation questions, every metric above is
measuring a leak.**

Any system that indexes its own repository, notes, or session transcripts will
eventually index the questions it is evaluated on. During the construction of
this repository it happened three times (`internal/LEARNINGS.md` L10):

1. Session transcripts put the test queries in the corpus, because the session
   that tested them quoted them verbatim.
2. Writing the test that asserts those questions are unanswerable put them in
   the corpus again through the filesystem connector. Pass rate fell 95% → 74%
   with no code change.
3. Near-miss paraphrase: a test asking about the "1998 World Cup final" against
   a golden asking about the "1998 **FIFA** World Cup final" - 83% overlap, too
   different for a 90% threshold, close enough to make the question answerable.

**The tell is that contamination makes the metrics go up.** Nothing looks broken.
In the first case the top result scored a perfect 1.00 relevance - a perfect
match for a question the corpus should not have contained.

So contamination is measured before every eval run and reported with the
results, via two signals: **verbatim** (the question appears near-exactly,
catching quotation) and **overlap** (a document shares nearly all the question's
distinctive terms, catching discussion).

**The remedy is quarantine, per question.** Excluding a whole source is too
blunt - the rest of it is legitimate corpus. Excluding the specific documents
containing the specific question measures what the eval claims to measure.

Thresholds are asymmetric, because the errors are not equally costly.
Over-quarantining for a positive question costs one document of recall on one
case. Missing contamination on a *negative* question inverts the case entirely -
the system answers, the harness records a failure to abstain, and the reported
cause is wrong.

## Two corpora, and why

`evals/goldens.jsonl` runs against this repository. That is the corpus the
system is actually used on, so it is the one that matters - but it has a
structural problem: **the repository documents its own evaluation.** Every
golden question eventually appears in it, gets quarantined, and the eval
measures a progressively smaller corpus. Contamination currently affects 4 of
20 questions, holding out 14 distinct documents as 29 per-question holdouts -
a document that contaminates two questions is held out twice and is still one
document - and that number only grows.

`evals/goldens-external.jsonl` runs against `corpus/external/pypi` - 91 PyPI
project pages, fetched with robots checked, committed with provenance in
`corpus/external/pypi-manifest.json`. That corpus has no relationship to this
repository, so it cannot contain a question *about* this repository.

It is **not** contamination-free, and this file claimed it was. The detector
reports 4 of 54 questions affected, holding out 14 distinct documents as 17
holdouts. The cause is not self-reference but authorship: the golden questions
were written from these pages, so a question can reuse enough of a page's own
wording to match it. That is the case contamination detection exists for, and
the quarantine is doing its job - but "reported clean, so the numbers need no
quarantine" was false, and it was a claim about the trustworthiness of the
regression gate itself (L49).

```bash
make eval           # primary: this repository
make eval-external  # external: no self-reference
```

**The external set is the regression gate; the primary set is a smoke test.**

That was not the original intent, and the reason for the change is worth
stating. The primary corpus has become a corpus *about its own evaluation*. Its
top three results for "What stops a crawl from running forever?" are now
`retrieve/expansion.py` - whose docstring quotes that exact question as the
example it was written to fix - and `internal/LEARNINGS.md`, which discusses it.
The retriever is behaving correctly: those documents *are* the best matches for
those words. They are simply not the answer.

Every fix documented in this repository makes its primary eval slightly less
able to measure retrieval. That is not a problem to solve by writing less down;
it is a reason to gate on a corpus that cannot be affected by what gets written
here.

The external set has already earned it: it caught two abstention failures, an
nDCG implementation that reported values above 1.0, and a cross-process
determinism bug - none of which the primary set could see.

## Known limitations, kept as failing cases

`evals/goldens.jsonl` carries a case tagged `known-limitation` that does not
pass: the offline hashing embedder cannot bridge "running forever" to a corpus
that says "never terminates" and "unbounded", because the query's most
informative term appears nowhere.

It stays failing on purpose. It is the measurable argument for a pluggable
neural embedder, and tuning thresholds until it passes would be overfitting the
eval - the exact thing the eval exists to prevent.

## Using it as a regression gate

```yaml
- run: ooda index && ooda eval --min-pass-rate 0.85 --exclude-source chat
```

Set the floor just below the current rate. It should fail on a real regression
and not on noise - and because the default embedder is deterministic, there is
no noise to accommodate.
