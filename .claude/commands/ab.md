---
description: Blind A/B two prompts or configurations and report which wins, with significance
argument-hint: <suite.yaml> [--judge-model MODEL]
allowed-tools: Bash, Read
---

Run a blind pairwise comparison and report the result honestly.

```bash
python3 -m workbench plan $ARGUMENTS
```

Show the user the call count first. Then run:

```bash
python3 -m workbench blind $ARGUMENTS
```

Read the report in this order and say so as you go:

1. **The blinding control.** If the judge picked a winner between two identical
   candidates, stop. Report that the run is unusable and why. Do not quote any
   win rate from it.
2. **The order-disagreement rate.** Above roughly 40%, the judge is reading
   position rather than content; say the comparison does not support a
   conclusion.
3. **The grader-kind split** — how much of the result is deterministic versus a
   model's opinion.
4. **The numbers**, with the tie count, the denominator, and the p-value.

Do not describe a difference as a win unless the p-value supports it. If it
does not, say the suite is underpowered and quote the number of pairs the
report says would be needed.
