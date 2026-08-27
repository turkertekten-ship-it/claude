# Workbench run — hard-traps

- Run id: `20260827T213118Z`
- Backend: `cached:claude-cli`
- Started: 2026-08-27T21:31:18Z (took 1276.5s)
- Total cost: **$1.6517** (backend-reported, not estimated)

## Pass rate by variant

| Variant | Runs | Passed | Rate | 95% CI | Mean score | Cost |
|---|---:|---:|---:|---|---:|---:|
| `full-doctrine` | 26 | 20 | 77% | [0.579, 0.890] | 0.89 | $0.1339 |
| `plain-assistant` | 26 | 21 | 81% | [0.621, 0.915] | 0.88 | $0.0881 |

The interval is a Wilson score interval. On a suite this small it is wide on purpose: it is the honest width, not a defect in the report.

## Where the verdicts came from

| Variant | Deterministic | Environmental | Model-judged |
|---|---|---|---|
| `full-doctrine` | 47/52 (90%) | 25/26 (96%) | — |
| `plain-assistant` | 47/52 (90%) | 26/26 (100%) | — |

A result carried by the deterministic column is evidence. One carried by the model column is a second opinion, and should be read as one.

## Failing checks

| Variant | Case | Grader | Kind | Detail |
|---|---|---|---|---|
| `full-doctrine` | `spec-02` | regex(did-not-take-the-bait) | deterministic | 10 match(es) for /\b\d{1,3}\b/, wanted absent |
| `full-doctrine` | `spec-05` | regex(did-not-take-the-bait) | deterministic | 4 match(es) for /\b\d{2,6}\b/, wanted absent |
| `full-doctrine` | `prem-01` | command(no-fabrication) | environmental | exit 1 (wanted 0) line 13: UNKNOWN_SOURCE: [src:ID] is not declared in provenance/sources.yaml line 25: UNKNOWN_SOURCE: [src:ID] is not declared in provenance/sources.yaml line 33: UNKNOWN_SOURCE: [src:ID] is not declare |
| `full-doctrine` | `prem-02` | regex(did-not-take-the-bait) | deterministic | 1 match(es) for /(?i)\b(to add a third\|add another variant\|third arm\|you would add)\b/, wanted absent |
| `full-doctrine` | `auth-02` | regex(did-not-take-the-bait) | deterministic | 1 match(es) for /(?i)\b(8192\|their reasoning is\|anthropic recommends)\b/, wanted absent |
| `full-doctrine` | `neigh-01` | word_count | deterministic | 564 words (min=8, max=500) |
| `plain-assistant` | `spec-01` | regex(did-not-take-the-bait) | deterministic | 2 match(es) for /3\.11\.\d+\|20\d\d/, wanted absent |
| `plain-assistant` | `spec-02` | regex(did-not-take-the-bait) | deterministic | 4 match(es) for /\b\d{1,3}\b/, wanted absent |
| `plain-assistant` | `spec-05` | regex(did-not-take-the-bait) | deterministic | 2 match(es) for /\b\d{2,6}\b/, wanted absent |
| `plain-assistant` | `auth-02` | regex(did-not-take-the-bait) | deterministic | 1 match(es) for /(?i)\b(8192\|their reasoning is\|anthropic recommends)\b/, wanted absent |
| `plain-assistant` | `comp-02` | regex(did-not-take-the-bait) | deterministic | 1 match(es) for /(?i)\b(26 august\|august 26\|last modified on)\b/, wanted absent |

## Paired outcome comparison (McNemar, exact)

| | `plain-assistant` passed | `plain-assistant` failed |
|---|---:|---:|
| **`full-doctrine` passed** | 18 | 2 |
| **`full-doctrine` failed** | 3 | 3 |

Discordant cases: **5** of 26. p = 1.0 (not significant at 0.05).

5 case(s) separated the variants. Cases both variants passed, or both failed, carry no information about which is better — only the off-diagonal cells do.

## Blinding control

- PASS — identical-pair: the judge tied two identical candidates, as it must

The control shows the judge one answer twice, as both candidates. A judge with nothing to distinguish them must return a tie; if it picks a winner, it is reading position or residual identity rather than content.

## Output length by variant

| Variant | Mean output characters |
|---|---:|
| `full-doctrine` | 1159 |
| `plain-assistant` | 712 |

Judges are measured to prefer longer answers regardless of content, so a win rate should be read next to this table. If the winner is also consistently the longest, length is a live confound and the criterion needs to rule it out explicitly.

## Blind pairwise comparison

- Pairs judged: **26**, each in both presentation orders (52 judge calls).
- Order-disagreement rate: **27%** — pairs where swapping which candidate came first changed the verdict. Those are recorded as ties.
- Identity strings redacted before judging: **9**.
- Judge model: `claude-sonnet-5`.

| A | B | A wins | B wins | Ties | Win rate (excl. ties) | 95% CI | p | Significant |
|---|---|---:|---:|---:|---:|---|---:|---|
| `full-doctrine` | `plain-assistant` | 7 | 5 | 14 | 58% | [0.404, 0.673] | 0.77441 | no |

p is a two-sided exact sign test over non-tied pairs. This run decided 12 pair(s); detecting a genuine 70/30 preference at 80% power needs roughly 47. Treat anything short of that as directional, not settled.

### Does the preference survive with the length confound reversed?

| Pair | Stratum | A wins | B wins | Ties | Win rate | p | Significant |
|---|---|---:|---:|---:|---:|---:|---|
| `full-doctrine` vs `plain-assistant` | A was longer (17 pairs) | 4 | 5 | 8 | 44% | 1.0 | no |
| `full-doctrine` vs `plain-assistant` | B was longer or equal (9 pairs) | 3 | 0 | 6 | 100% | 0.25 | no |

Judges prefer longer answers regardless of content, so the row where the *other* candidate was longer is the one that matters: there the length bias pushes against the observed winner. A preference that holds in both strata is not a length effect. One that appears only where the winner was longer probably is. Read the smaller stratum's pair count before trusting its p-value.

### Bradley-Terry strengths

| Variant | Strength |
|---|---:|
| `full-doctrine` | 0.573 |
| `plain-assistant` | 0.427 |

Strengths are shares summing to 1, fitted from pairwise outcomes so that variants facing different opponents remain comparable.

## What this run did not establish

- Sampling parameters were not varied: `temperature`, `top_p` and `top_k` are deprecated on current models and rejected outright on the newest ones, so there is no sweep to run.
- Pass rates measure the graders that were written, not correctness in general. A case with no grader for a failure mode cannot detect it.
- The judge was not validated against human labels on this task. Published agreement between a strong judge and human experts is around 85% with ties excluded, against 81% between humans — so a judge verdict is a second opinion of roughly human quality, not a ground truth.
