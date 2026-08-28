---
name: eval-gate
description: Run the retrieval regression gate (index, then `ooda eval --exclude-source chat`) and interpret the report - pass rate, recall@k, nDCG, citation coverage, contamination and quarantine. Use before committing any change to chunking, embedding, retrieval, fusion, reranking, the generator or the golden set; when asked whether retrieval got better or worse; or when an eval case fails. Do NOT use it to make a failing case pass by tuning thresholds - that is the overfitting this gate exists to catch.
---

# Eval gate: is retrieval better or worse?

"The retrieval improved" is an opinion until it is a number. `docs/EVALUATION.md`
is the reference; this is how to run and read it.

## Run it

Always in this order — an eval against a stale index measures the old code.

```bash
cd /home/user/claude
PYTHONPATH=src python3 -m oodarag.cli index --refit
PYTHONPATH=src python3 -m oodarag.cli eval --exclude-source chat
```

- `index --refit` refits corpus statistics. Use it after any chunker or
  embedder change; plain `index` is enough for a content-only change.
- **`--exclude-source chat` is not optional.** Session transcripts contain the
  evaluation questions verbatim. Without the flag the harness scores a leak.
- Expect ~25s for `index` and ~1-2s for `eval` in this container. Nearly all of
  the index time is HTTP backoff against blocked hosts (`www.youtube.com`), not
  work — see the `preflight` skill.

Exit code is the gate: `0` if `pass_rate >= --min-pass-rate` (default `0.8`),
`1` below it. Verified: `--min-pass-rate 0.95` exits 1 at the current rate,
`--min-pass-rate 0.85` exits 0.

Other flags: `--json` (machine-readable), `--out report.md` (also writes the
markdown), `-k N` (retrieval depth), `--goldens PATH`.

## Establish a before, not just an after

A single run tells you the level, not the movement. To claim an improvement:

```bash
PYTHONPATH=src python3 -m oodarag.cli eval --exclude-source chat --out /tmp/eval-before.md
# ... make the change, re-index ...
PYTHONPATH=src python3 -m oodarag.cli eval --exclude-source chat --out /tmp/eval-after.md
diff /tmp/eval-before.md /tmp/eval-after.md
```

Write the eval reports to `/tmp`, never into the repo. The default embedder is
deterministic, so any difference is signal, not noise. "This should be better"
is a hypothesis; three changes in this project each made retrieval measurably
*worse* while every unit test stayed green.

## Reading the report

**Header** — `N/M cases passed`, index size, duration.

**Metrics table** — mean / p50 / min. One number hides regressions; read them
against each other:

| Movement | What it means |
|---|---|
| recall@k down | The right material stopped reaching the window. A retrieval problem — it is the ceiling on everything downstream. |
| recall@k flat, nDCG@k down | The right documents still arrive, in the wrong order. A **ranking** problem: reranker, fusion or authority weights. |
| precision@k down, recall flat | More of a fixed context budget wasted. Chunking or `top_k`. |
| mrr down | The first correct result sank. Usually the same cause as nDCG. |
| citation_coverage below 1.0 | Claim sentences without citations. A *grounding* regression in generation, not retrieval — chase it in `generate/`, not the retriever. |
| A negative case stops abstaining | The most serious failure here. Either the abstention floor moved or the corpus was contaminated. Check contamination before blaming the code. |

**Failing cases** are listed with what was expected and the top URIs actually
retrieved — that list is the diagnosis, so read it before theorising.

Observed snapshot at commit `3ae15dd` (2026-08-28), after `index --refit`:
**18/20 passed (90%)**, 88 documents / 510 chunks, recall@8 0.8, precision@8
0.169, hit@8 0.7, mrr 0.471, nDCG@8 0.509, citation_coverage 1.0. Treat this as
a datapoint, not a target: the repo moves, and the number to compare against is
*your own before-run on the same commit*, not a figure copied from this file.

## The contamination line

Every report carries one. Clean looks like:

```
no contamination across N questions
```

Contaminated looks like (real output):

```
CONTAMINATED: 4/20 questions appear in the corpus (chat=4, filesystem=19). Those
documents must be held out for the affected questions or the results measure the
leak, not the retriever.
Quarantined 23 contaminated document(s) across 4 question(s).
```

What it means: this pipeline indexes its own repository, so it eventually
indexes the questions it is evaluated on — through session transcripts that
quote them, and through docs and tests that discuss them. Two signals are
measured: **verbatim** (the question appears near-exactly — quotation) and
**overlap** (a document shares nearly all the question's distinctive terms —
discussion). Thresholds are asymmetric: a negative case is held to a much
lower bar, because missing contamination on a question that is supposed to be
unanswerable inverts the case entirely and reports the wrong cause.

The remedy is already applied automatically: **per-question quarantine**. The
specific documents containing a specific question are hidden from retrieval for
that question only. Excluding whole sources is too blunt — the rest of the
source is legitimate corpus.

So:

- `by_source` counts name the culprits. `chat=` is why `--exclude-source chat`
  exists. `filesystem=` is the repo discussing itself and is normal here.
- **The tell is that contamination makes the metrics go up.** A jump in pass
  rate with no plausible cause is a leak until proven otherwise — check this
  line before celebrating.
- A rise in the contaminated-question count after your change means something
  you added quotes a golden question. Rephrase what you wrote, or accept the
  quarantine; do not delete the golden.
- The line is provenance. An eval number reported without its contamination
  status is a number without a source.

## The `known-limitation` case must keep failing

`evals/goldens.jsonl` carries a case tagged `known-limitation`:

> **What stops a crawl from running forever?** — expects `crawler.py`.

It fails, on purpose, and it must stay failing. The offline hashing embedder
cannot bridge "running forever" to a corpus that says "never terminates" and
"unbounded": the query's most informative term (`forever`, idf 4.37) appears
nowhere in the corpus, and no lexical or feature-hashing method closes that gap.
A neural embedder would — which is the point. The case is the measurable
argument for a pluggable embedder.

**Do not fix it.** Specifically, do not lower the relevance floor, widen `k`,
loosen the match, add "forever" to the corpus, or edit the golden so it passes.
Every one of those makes the number go up without making retrieval better —
that is overfitting the eval, the exact failure the eval exists to prevent. If
it starts passing, find out *why* before treating it as good news.

Set the CI floor just below the current rate so a real regression fails and the
known limitation does not:

```yaml
- run: ooda index && ooda eval --min-pass-rate 0.85 --exclude-source chat
```

## Untagged failures are different

Any failing case **not** tagged `known-limitation` is a live defect or a
mis-specified golden, and it needs a cause before the work is done.

At commit `3ae15dd` there is one: **"How does the system decide to abstain from
answering?"** expects `answer.py`, and `answer.py` is not in the top 8 —
retrieval returns `LEARNINGS.md`, `eval/harness.py` and
`docs/adr/0005-consistent-text-analysis.md` instead. It carries only the
`generation` tag. Either it is a genuine ranking failure worth fixing in the
retriever, or the golden's `expect_sources` are wrong. Decide which, with
evidence — do not silently re-tag it `known-limitation` to make the gate quiet.

## Checklist before you say a change is good

1. `index --refit` then `eval --exclude-source chat`, before and after.
2. Pass rate did not fall, and no *new* case fails.
3. Contamination line did not get worse; a pass-rate rise has a cause other
   than a leak.
4. The `known-limitation` case still fails.
5. `make test` still passes — stdlib `unittest`, ~2 minutes, no network
   required (166 tests OK when last observed; the suite grows).
6. Report the actual numbers, including anything that got worse.
