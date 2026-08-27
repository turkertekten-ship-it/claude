---
description: Establish the check that will prove a task worked, before the task is started — and wire it as the gate the work has to pass.
argument-hint: [the task about to be worked]
allowed-tools: Bash, Read, Grep, Glob, Edit, Write, Agent
---

Set up the verification loop for: **$ARGUMENTS**

The corpus rule this enforces is in `.claude/skills/cherny/SKILL.md`: a task
without a runnable check has only one completion signal, "it looks done", which
makes the human the verification loop. Close it first.

Do not start the task itself. Produce the gate it will have to pass.

1. **State the claim the finished work will make**, as one testable sentence.
   Not "improve the parser" — "the parser accepts `X` and rejects `Y`". If the
   task cannot be phrased this way, say so; that is a finding about the task,
   and it usually means the request is still ambiguous.

2. **Find an existing check.** Look for the test suite, build, linter, or script
   that would exercise this claim:

   ```bash
   ls tests/ 2>/dev/null; cat Makefile 2>/dev/null | head -30
   ```

   Report what exists and, specifically, whether it covers the claim in step 1.
   A suite that passes without touching the changed behaviour is not a check.

3. **If no check covers the claim, build one.** The smallest thing that fails
   now and passes when the work is done. Run it and watch it fail — an untested
   check is not a check, and a guard nobody has seen reject something is not a
   guard.

4. **Choose the gate**, weakest that fits:
   - watched work → run the check before reporting
   - a condition that must hold across a session → a `/goal` condition
   - an unattended run → a `Stop` hook that blocks the turn until it passes
   - a result that matters more than the cost of checking → the `verifier`
     subagent, in its own context window

5. **Report** the claim, the command that tests it, the observed failing output
   from step 3, and which gate you wired. If no check is possible in this
   environment, say that plainly and name what you are substituting — do not
   proceed as though the gap is not there.

Close by running `python3 tools/verify_provenance.py`; if the write-up asserts
anything about what exists, it needs a source like everything else here.
