# Workbench run — hard-traps-heldout

- Run id: `20260827T223803Z`
- Backend: `cached:claude-cli`
- Started: 2026-08-27T22:38:03Z (took 991.6s)
- Total cost: **$1.4341** (backend-reported, not estimated)
- Cache: **8/284** completions served from disk. The cost above is what producing these results cost in total, not what this run spent — a re-grade of cached completions spends nothing.

## Pass rate by variant

| Variant | Runs | Passed | Rate | 95% CI | Mean score | Cost |
|---|---:|---:|---:|---|---:|---:|
| `doctrine-v1` | 14 | 14 | 100% | [0.785, 1.000] | 1.00 | $0.3535 |
| `doctrine-v2` | 14 | 14 | 100% | [0.785, 1.000] | 1.00 | $0.3431 |

The interval is a Wilson score interval. On a suite this small it is wide on purpose: it is the honest width, not a defect in the report.

## Where the verdicts came from

| Variant | Deterministic | Environmental | Model-judged |
|---|---|---|---|
| `doctrine-v1` | 14/14 (100%) | 14/14 (100%) | 14/14 (100%) |
| `doctrine-v2` | 14/14 (100%) | 14/14 (100%) | 14/14 (100%) |

A result carried by the deterministic column is evidence. One carried by the model column is a second opinion, and should be read as one.

## Paired outcome comparison (McNemar, exact)

| | `doctrine-v2` passed | `doctrine-v2` failed |
|---|---:|---:|
| **`doctrine-v1` passed** | 14 | 0 |
| **`doctrine-v1` failed** | 0 | 0 |

Discordant cases: **0** of 14. p = 1.0 (not significant at 0.05).

No discordant pairs: the variants passed and failed the same cases, so this suite cannot separate them. Cases both variants passed, or both failed, carry no information about which is better — only the off-diagonal cells do.

## Blinding control

- PASS — identical-pair: the judge tied two identical candidates, as it must

The control shows the judge one answer twice, as both candidates. A judge with nothing to distinguish them must return a tie; if it picks a winner, it is reading position or residual identity rather than content.

## Output length by variant

| Variant | Mean output characters |
|---|---:|
| `doctrine-v1` | 930 |
| `doctrine-v2` | 657 |

Judges are measured to prefer longer answers regardless of content, so a win rate should be read next to this table. If the winner is also consistently the longest, length is a live confound and the criterion needs to rule it out explicitly.

## Blind pairwise comparison

- Pairs judged: **14**, each in both presentation orders (28 judge calls).
- Order-disagreement rate: **36%** — pairs where swapping which candidate came first changed the verdict. Those are recorded as ties.
- Identity strings redacted before judging: **0**.
- Judge model: `claude-sonnet-5`.

| A | B | A wins | B wins | Ties | Win rate (excl. ties) | 95% CI | p | Significant |
|---|---|---:|---:|---:|---:|---|---:|---|
| `doctrine-v1` | `doctrine-v2` | 2 | 1 | 11 | 67% | [0.429, 0.643] | 1.0 | no |

p is a two-sided exact sign test over non-tied pairs. This run decided 3 pair(s); detecting a genuine 70/30 preference at 80% power needs roughly 47. Treat anything short of that as directional, not settled.

### Does the preference survive with the length confound reversed?

| Pair | Stratum | A wins | B wins | Ties | Win rate | p | Significant |
|---|---|---:|---:|---:|---:|---:|---|
| `doctrine-v1` vs `doctrine-v2` | A was longer (13 pairs) | 1 | 1 | 11 | 50% | 1.0 | no |
| `doctrine-v1` vs `doctrine-v2` | B was longer or equal (1 pairs) | 1 | 0 | 0 | 100% | 1.0 | no |

Judges prefer longer answers regardless of content, so the row where the *other* candidate was longer is the one that matters: there the length bias pushes against the observed winner. A preference that holds in both strata is not a length effect. One that appears only where the winner was longer probably is. Read the smaller stratum's pair count before trusting its p-value.

### Bradley-Terry strengths

| Variant | Strength |
|---|---:|
| `doctrine-v1` | 0.606 |
| `doctrine-v2` | 0.394 |

Strengths are shares summing to 1, fitted from pairwise outcomes so that variants facing different opponents remain comparable.

## What this run did not establish

- Sampling parameters were not varied: `temperature`, `top_p` and `top_k` are deprecated on current models and rejected outright on the newest ones, so there is no sweep to run.
- Pass rates measure the graders that were written, not correctness in general. A case with no grader for a failure mode cannot detect it.
- The judge was not validated against human labels on this task. Published agreement between a strong judge and human experts is around 85% with ties excluded, against 81% between humans — so a judge verdict is a second opinion of roughly human quality, not a ground truth.
 it.
- The judge was not validated against human labels on this task. Published agreement between a strong judge and human experts is around 85% with ties excluded, against 81% between humans — so a judge verdict is a second opinion of roughly human quality, not a ground truth.
