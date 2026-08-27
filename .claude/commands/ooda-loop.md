---
description: Run one complete OODA loop on a task, producing sourced evidence, a named surprise, a falsifiable decision, and a verified result.
argument-hint: [the task]
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent, TaskCreate, TaskUpdate
---

Run one full OODA loop on: **$ARGUMENTS**

Follow `.claude/skills/ooda/SKILL.md`. Produce all four artifacts — a loop
missing one of them has not run.

**Observe.** Enumerate what exists before deciding what it means. Use the
`observer` subagent for breadth, then verify what matters yourself. Record
captures in `provenance/sources.yaml` and absences in
`provenance/unknowns.md`.

**Orient.** Write the reading, and write the surprise: where reality diverged
from what you assumed walking in. If nothing surprised you, Observe was too
shallow — go back. Grade every claim verified, second-hand, or unknown, and do
not let a grade drift upward.

**Decide.** One decision, one sentence, plus the cheapest thing that would
prove it wrong. A decision with no falsifier is a preference. If the readings
genuinely diverge and lead to materially different work, ask now rather than
after building.

**Act.** Do it. Capture the result as new evidence. Run
`bash tests/run_all.sh` before calling the loop closed.

Close by answering plainly: what exists, what does not, what you did, what is
still open. If any answer needs a hedge, say the loop is still open rather than
rounding it up.
