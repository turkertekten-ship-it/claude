# The cost of the self-annealing section — 2026-08-27

```
4 rule(s), 121 words, 6% of CLAUDE.md
  within budget, no contradictions or near-duplicates found
```

## Projected growth, at this repository's mean rule length

| rules | section words | share of the file |
|---|---|---|
| 4 | 121 | 6% |
| 10 | 302 | 15% |
| 50 | 1512 | 46% |
| 200 | 6050 | 78% |

Mean rule length 30 words. Four rules were appended in one session,
and the appending is now automated by check_output.py --suggest-rule.

## The two collisions that set the thresholds

Both real collisions this repository has produced sit at exactly 0.50 word
overlap: a contradiction (Never/Always on the same action in the same
category) and a restatement (the same rule written twice in different words).
The four genuine rules produce no finding at that threshold. A threshold set
above the real cases would be a check that has never caught anything.
