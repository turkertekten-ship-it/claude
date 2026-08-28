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
20 questions and quarantines 25 documents, and that number only grows.

`evals/goldens-external.jsonl` runs against `corpus/external/pypi` - fourteen
PyPI project pages, fetched with robots checked, committed with provenance in
`corpus/external/pypi-manifest.json`. That corpus has no relationship to this
repository and cannot contain the questions asked of it. Contamination there is
reported clean, so the numbers need no quarantine to be trustworthy.

```bash
make eval           # primary: this repository
make eval-external  # external: no self-reference
```

**Run both before believing a retrieval change.** The external set caught two
abstention failures the primary set could not see, because the primary corpus
contained the very words that made those questions look answerable.

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
