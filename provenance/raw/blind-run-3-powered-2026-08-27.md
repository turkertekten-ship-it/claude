# Workbench run — doctrine-adherence-powered

- Run id: `20260827T211341Z`
- Backend: `cached:claude-cli`
- Started: 2026-08-27T21:13:41Z (took 66.2s)
- Total cost: **$3.1587** (backend-reported, not estimated)
- Cache: **472/484** completions served from disk. The cost above is what producing these results cost in total, not what this run spent — a re-grade of cached completions spends nothing.

## Pass rate by variant

| Variant | Runs | Passed | Rate | 95% CI | Mean score | Cost |
|---|---:|---:|---:|---|---:|---:|
| `full-doctrine` | 60 | 60 | 100% | [0.940, 1.000] | 1.00 | $0.2679 |
| `plain-assistant` | 60 | 60 | 100% | [0.940, 1.000] | 1.00 | $0.1726 |

The interval is a Wilson score interval. On a suite this small it is wide on purpose: it is the honest width, not a defect in the report.

## Where the verdicts came from

| Variant | Deterministic | Environmental | Model-judged |
|---|---|---|---|
| `full-doctrine` | 180/180 (100%) | 60/60 (100%) | — |
| `plain-assistant` | 180/180 (100%) | 60/60 (100%) | — |

A result carried by the deterministic column is evidence. One carried by the model column is a second opinion, and should be read as one.

## Paired outcome comparison (McNemar, exact)

| | `plain-assistant` passed | `plain-assistant` failed |
|---|---:|---:|
| **`full-doctrine` passed** | 60 | 0 |
| **`full-doctrine` failed** | 0 | 0 |

Discordant cases: **0** of 60. p = 1.0 (not significant at 0.05).

No discordant pairs: the variants passed and failed the same cases, so this suite cannot separate them. Cases both variants passed, or both failed, carry no information about which is better — only the off-diagonal cells do.

## Blinding control

- PASS — identical-pair: the judge tied two identical candidates, as it must

The control shows the judge one answer twice, as both candidates. A judge with nothing to distinguish them must return a tie; if it picks a winner, it is reading position or residual identity rather than content.

## Output length by variant

| Variant | Mean output characters |
|---|---:|
| `full-doctrine` | 775 |
| `plain-assistant` | 592 |

Judges are measured to prefer longer answers regardless of content, so a win rate should be read next to this table. If the winner is also consistently the longest, length is a live confound and the criterion needs to rule it out explicitly.

## Blind pairwise comparison

- Pairs judged: **60**, each in both presentation orders (120 judge calls).
- Order-disagreement rate: **17%** — pairs where swapping which candidate came first changed the verdict. Those are recorded as ties.
- Identity strings redacted before judging: **9**.
- Judge model: `claude-sonnet-5`.

| A | B | A wins | B wins | Ties | Win rate (excl. ties) | 95% CI | p | Significant |
|---|---|---:|---:|---:|---:|---|---:|---|
| `full-doctrine` | `plain-assistant` | 42 | 8 | 10 | 84% | [0.692, 0.867] | 0.0 | yes |

p is a two-sided exact sign test over non-tied pairs. This run decided 50 pair(s); detecting a genuine 70/30 preference at 80% power needs roughly 47. Treat anything short of that as directional, not settled.

### Bradley-Terry strengths

| Variant | Strength |
|---|---:|
| `full-doctrine` | 0.828 |
| `plain-assistant` | 0.172 |

Strengths are shares summing to 1, fitted from pairwise outcomes so that variants facing different opponents remain comparable.

## What this run did not establish

- Sampling parameters were not varied: `temperature`, `top_p` and `top_k` are deprecated on current models and rejected outright on the newest ones, so there is no sweep to run.
- Pass rates measure the graders that were written, not correctness in general. A case with no grader for a failure mode cannot detect it.
- The judge was not validated against human labels on this task. Published agreement between a strong judge and human experts is around 85% with ties excluded, against 81% between humans — so a judge verdict is a second opinion of roughly human quality, not a ground truth.
