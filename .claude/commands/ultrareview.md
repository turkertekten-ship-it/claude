---
description: The closing gate. Re-verify every claim and every check before work is called finished — provenance, tests, the pipeline eval, and the diff itself.
argument-hint: [optional scope, e.g. "the retrieval change" or a path]
allowed-tools: Bash, Read, Grep, Glob, Agent
---

Run the closing review over: **$ARGUMENTS** (default: everything changed on this
branch).

This gate exists because a review that only reads the code has not checked the
claims. Work is finished when the data checkers pass, not when the diff looks
convincing.

## 1. Run the checkers, and paste what they actually printed

```bash
python3 tools/verify_provenance.py     # 0 clean · 1 violations · 2 could not run
bash tests/run_all.sh                  # verifier + tool suites + pipeline suite
make test                              # the oodarag suite, offline
make demo                              # end-to-end, offline
```

Report the real output. A summary of a command you did not run is the exact
failure this repository is built to prevent.

## 2. Audit the claims, not just the code

Dispatch the `fact-checker` subagent over every document the work touched, then
verify anything load-bearing yourself — its report is second-hand.

Check specifically:

- Every `[src:ID]` resolves, and the source **supports the specific claim**. A
  resolving tag on an unrelated fact is still a fabrication.
- Nothing was promoted from second-hand to verified between draft and final.
- No name or title was expanded into content.
- Every README and doc claim matches code that exists. A promise the code has
  not kept is corrected, or moved to `internal/PLAN.md` under "Next".
- The unknowns register is not empty, and nothing that got quietly answered is
  still sitting in it.

## 3. Verify by outcome, not by inspection

For each behavioural claim, name the command that demonstrates it and run it.
For a guard, show it rejecting something. For a retrieval change, show the eval
delta before and after — `make eval` on both sides, not an argument about why it
should be better.

If a claim has no runnable demonstration, say so plainly rather than grading it
as verified.

## 4. Read your own diff adversarially

`git diff` the whole branch. Ask what a reviewer would reject: a widened scope,
a new dependency, a weakened test, a deleted claim that should have been fixed
instead, a secret that reached a file.

## 5. Report

Four things, in plain terms:

1. **What was done**, with the command output that shows it.
2. **What was deliberately not done**, and why. Scope dropped is reported, not
   omitted.
3. **What is still open**, as open — not rounded up to done.
4. **The checker results**, verbatim.

If any of the four needs a hedge, the work is not finished. Say that instead of
closing the gate.
