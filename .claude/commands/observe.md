---
description: Run the Observe phase of an OODA loop — enumerate what actually exists, record it as sourced evidence, and name what could not be reached.
argument-hint: [what to inventory, e.g. "the two repos and the fleet"]
allowed-tools: Bash, Read, Grep, Glob, Agent, TaskCreate, TaskUpdate
---

Inventory this, without interpreting it: **$ARGUMENTS**

Read `.claude/skills/ooda/SKILL.md` first, then work the Observe phase only.

1. Delegate the sweep to the `observer` subagent. Give it the target and tell
   it to report presence *and* absence, each with the command that established
   it. Absence is a finding of equal weight.
2. Take its inventory back and verify anything load-bearing yourself. A
   subagent's report is second-hand until you have re-run the command.
3. Write each capture into `provenance/sources.yaml`: id, kind, `collected_at`,
   the exact method, and the evidence. Bulky output goes verbatim into
   `provenance/raw/`.
4. Add sourced lines to `provenance/observations.md` under an `## Observed`
   heading, and add anything you could not reach to `provenance/unknowns.md`
   with what would resolve it.
5. Run `python3 tools/verify_provenance.py`. Non-zero means you are not done.

Stop at the inventory. Do not recommend, plan, or conclude — that is Orient,
and it is a separate step. If you find yourself writing "this suggests", delete
it and hand back the inventory.
