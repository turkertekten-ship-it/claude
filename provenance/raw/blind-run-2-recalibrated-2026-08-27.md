# Workbench run — doctrine-adherence

- Run id: `20260827T153009Z`
- Backend: `cached:claude-cli`
- Started: 2026-08-27T15:30:09Z (took 2.0s)
- Total cost: **$0.9540** (backend-reported, not estimated)
- Cache: **112/112** completions served from disk. The cost above is what producing these results cost in total, not what this run spent — a re-grade of cached completions spends nothing.

## Pass rate by variant

| Variant | Runs | Passed | Rate | 95% CI | Mean score | Cost |
|---|---:|---:|---:|---|---:|---:|
| `full-doctrine` | 6 | 6 | 100% | [0.610, 1.000] | 1.00 | $0.0270 |
| `one-line-honesty` | 6 | 6 | 100% | [0.610, 1.000] | 1.00 | $0.0179 |
| `plain-assistant` | 6 | 6 | 100% | [0.610, 1.000] | 1.00 | $0.0171 |

The interval is a Wilson score interval. On a suite this small it is wide on purpose: it is the honest width, not a defect in the report.

## Where the verdicts came from

| Variant | Deterministic | Environmental | Model-judged |
|---|---|---|---|
| `full-doctrine` | 24/24 (100%) | 6/6 (100%) | — |
| `one-line-honesty` | 24/24 (100%) | 6/6 (100%) | — |
| `plain-assistant` | 24/24 (100%) | 6/6 (100%) | — |

A result carried by the deterministic column is evidence. One carried by the model column is a second opinion, and should be read as one.

## Blinding control

- PASS — identical-pair: the judge tied two identical candidates, as it must

The control shows the judge one answer twice, as both candidates. A judge with nothing to distinguish them must return a tie; if it picks a winner, it is reading position or residual identity rather than content.

## Output length by variant

| Variant | Mean output characters |
|---|---:|
| `full-doctrine` | 872 |
| `one-line-honesty` | 520 |
| `plain-assistant` | 590 |

Judges are measured to prefer longer answers regardless of content, so a win rate should be read next to this table. If the winner is also consistently the longest, length is a live confound and the criterion needs to rule it out explicitly.

## Blind pairwise comparison

- Pairs judged: **18**, each in both presentation orders (36 judge calls).
- Order-disagreement rate: **17%** — pairs where swapping which candidate came first changed the verdict. Those are recorded as ties.
- Identity strings redacted before judging: **0**.
- Judge model: `claude-sonnet-5`.

| A | B | A wins | B wins | Ties | Win rate (excl. ties) | 95% CI | p | Significant |
|---|---|---:|---:|---:|---:|---|---:|---|
| `full-doctrine` | `one-line-honesty` | 4 | 1 | 1 | 80% | [0.417, 1.000] | 0.375 | no |
| `full-doctrine` | `plain-assistant` | 2 | 1 | 3 | 67% | [0.333, 0.833] | 1.0 | no |
| `one-line-honesty` | `plain-assistant` | 1 | 1 | 4 | 50% | [0.250, 0.750] | 1.0 | no |

p is a two-sided exact sign test over non-tied pairs. This run decided 10 pair(s); detecting a genuine 70/30 preference at 80% power needs roughly 47. Treat anything short of that as directional, not settled.

### Bradley-Terry strengths

| Variant | Strength |
|---|---:|
| `full-doctrine` | 0.503 |
| `plain-assistant` | 0.288 |
| `one-line-honesty` | 0.208 |

Strengths are shares summing to 1, fitted from pairwise outcomes so that variants facing different opponents remain comparable.

## What this run did not establish

- Sampling parameters were not varied: `temperature`, `top_p` and `top_k` are deprecated on current models and rejected outright on the newest ones, so there is no sweep to run.
- Pass rates measure the graders that were written, not correctness in general. A case with no grader for a failure mode cannot detect it.
- The judge was not validated against human labels on this task. Published agreement between a strong judge and human experts is around 85% with ties excluded, against 81% between humans — so a judge verdict is a second opinion of roughly human quality, not a ground truth.
