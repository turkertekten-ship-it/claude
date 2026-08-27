---
name: ooda
description: The observe-orient-decide-act procedure this project works by. Use when starting on an unfamiliar repository, when a task's scope is not yet established, or whenever you are about to decide something before you have enumerated what exists. Referenced by CLAUDE.md as the standing procedure for "observe before you orient".
---

# OODA

Four phases, in order, with a rule about what you are allowed to write down in
each. The ordering is the whole content: the common failure is not skipping a
phase, it is doing them in the wrong order and calling the result observation.

## Observe — enumerate, do not interpret

List what exists. Files, commits, branches, targets, exit codes.

```bash
git status --short; git log --oneline -15; git branch -a
find . -path ./.git -prune -o -type f -print | sort
```

The rule for this phase: **write nothing that contains the word "so", "which
means", or "therefore".** Those words mark the transition to Orient, and doing
it here is what produces a review of a repository nobody read.

Two failures to guard against specifically:

* **Expanding a name into content.** `PLAN.md` tells you a file with that name
  exists. It does not tell you there is a plan in it. Open it.
* **Accepting a summary as an observation.** Another session's report of its own
  work is a lead, not a fact. Mark it as second-hand and name the reporter.

## Orient — say what the enumeration means

Now interpret, and only against what Observe actually recorded. Every
interpretation cites the observation it rests on.

The useful question here is not "what is this?" but "what would have to be true
for this to be what it looks like?" — then go and check that thing. A README
describing a pipeline implies a module that runs it; if no such module is in the
inventory, the orientation is "documentation describes unbuilt work", not
"pipeline exists".

Separate what you measured from what you inferred. Keep the two in different
sentences; the inference is the part that will be wrong.

## Decide — commit, and record what would change your mind

State the decision, the alternatives rejected, and the evidence behind it. Record
the open questions you are deciding *around* rather than deciding — in this
project those go in `provenance/unknowns.md` with an id, so a later session
inherits the question instead of silently re-answering it from imagination.

A decision with no stated falsifier is a preference. Write down what observation
would reverse it.

## Act — do it, then measure the result

Make the change. Then run the thing: the suite, the command, the checker. The
loop closes on a measurement, not on the edit.

`/ultrareview` is the Act-phase gate for a finished body of work: it re-runs
Observe as data and refuses to sign off on anything it could not measure.

## Why the loop, rather than a plan

A plan assumes the first orientation was right. The loop assumes it was not, and
makes re-observing after acting the cheapest step rather than an admission. On
an unfamiliar repository the first orientation is usually wrong in a way that is
invisible until something is measured — which is exactly why Act ends with a
measurement and hands back to Observe.
