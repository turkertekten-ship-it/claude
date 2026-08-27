---
name: workbench
description: Compare prompt or configuration variants and score them, instead of judging a change by reading it. Use when asked whether one prompt, system message, model or effort level is better than another; when a change to a prompt needs evidence before it is adopted; when someone asks for an A/B test, an eval, a blind test, or a regression check on prompt behaviour; or when you are about to claim a rewrite is an improvement. Produces graded runs and blind pairwise comparisons with significance, not impressions.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Workbench

The trap this exists to defuse: you rewrite a prompt, read both versions, and
conclude the new one is better. You wrote it, so of course it reads better. A
model judge shown both is no help either if it can tell which one is the new
one — and it usually can, from a label, a model name, or simply from being
shown the new one second.

So: never assert one variant is better than another from reading them. Measure.

## Before anything else

```bash
python3 -m workbench doctor
```

It reports which backends exist here, whether `claude plugin eval` is
available, and — importantly — what cannot be controlled. Sampling parameters
are not on that list of controls, and that is not a defect in this tool:
`temperature`, `top_p` and `top_k` are deprecated on current models and
rejected outright on the newest, and the CLI exposes no flag for them. Do not
build a suite around varying them, and correct anyone who asks you to.

## The loop

**1. Write a suite.** One YAML file: the variants, the cases, the graders.
Start from `suites/doctrine-adherence.yaml`, which is a working example rather
than a toy.

**2. Inspect before spending.**

```bash
python3 -m workbench plan suites/mine.yaml
```

Prints the exact request each variant would send and the number of calls it
would make. Nothing is sent.

**3. Run it.**

```bash
python3 -m workbench run   suites/mine.yaml            # grade only
python3 -m workbench blind suites/mine.yaml --judge-model claude-sonnet-5
```

`blind` adds the pairwise comparison. Give the judge a model from a **different
family** than the variants under test: a judge is measured to favour its own
family's output, and the report will warn you if you forget.

**4. Read the report in this order.**

- **The blinding control first.** The judge was shown one answer twice, as both
  candidates. If it picked a winner between two identical texts, it is reading
  position or leaked identity, and nothing else in the report is safe to quote.
- **The order-disagreement rate.** Pairs where swapping which candidate came
  first changed the verdict. High means the judge is reading layout.
- **The grader-kind split.** A result carried by deterministic graders is
  evidence. One carried by the model column is a second opinion.
- **Then the numbers.**

## Writing graders

Reach for them in this order, and stop at the first that settles the case:

1. **Deterministic** — `equals`, `contains`, `regex`, `json_schema`,
   `json_path`, `word_count`. Free, instant, identical every time.
2. **Environmental** — `command`, `file_exists`, `file_contains`, `cost_under`,
   `latency_under`. `command` is the important one: it hands the output to a
   real checker (a linter, a test runner, `tools/grade_no_fabrication.py`) and
   takes that program's exit code as the verdict. This is what makes a suite
   outcome-based rather than a matter of taste.
3. **`judge`** — only for what genuinely cannot be checked any other way.

`python3 -m workbench graders` lists them all with their kinds.

## Agent mode

A variant with `mode: agent` runs with tools inside a scratch directory seeded
from a fixture. The artifact is then the **directory**, and `file_exists`,
`file_contains` and `command` graders run against it. Use this when the
question is "did it do the job", not "did it say the right thing".

## Reporting a result honestly

- Quote the win rate **and** its denominator. Wins over all pairs and wins over
  decided pairs are different numbers.
- Quote the tie count and the p-value. A 4–2 split is p = 0.69: that is noise,
  and calling it a win is the single most common way this kind of report
  misleads.
- If the intervals overlap, say "no separation at this sample size" and quote
  how many pairs would be needed. The report computes it.
- Say what the suite could not test.

## When to use `claude plugin eval` instead

It ships with Claude Code and grades things this package does not: which tools
fired, in what order, and what files a run created, with a with-plugin /
without-plugin ablation. If the question is "does my plugin trigger correctly",
use it. `python3 -m workbench export-eval suites/mine.yaml` translates a suite
across and tells you which graders had no equivalent.

Use the workbench when the question is "which of these N prompts is better",
which is the comparison `claude plugin eval` does not make.
