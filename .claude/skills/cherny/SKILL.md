---
name: cherny
description: Apply the Boris Cherny practice set for driving Claude Code — close the verification loop before starting, plan before coding, run uncorrelated context windows for review, keep CLAUDE.md pruned, and ship small squashed PRs. Use when setting up how a task will be worked, when a session is producing plausible-looking output nobody has checked, when deciding whether to plan or just do it, when choosing between a skill, a command, a subagent and a hook, or when a task is large enough to parallelize.
---

# The Cherny practice set

The sourced corpus this comes from is `docs/cherny-practice.md`; every claim
there carries a `[src:]` tag. This file is the procedure. Where the two differ,
the corpus is the record and this is the habit.

## The one rule everything else serves

**Give Claude a way to verify its work before you give it the work.**

A task without a check has one completion signal: it looks done. That makes the
human the verification loop, and every mistake then waits to be noticed. A task
with a check closes its own loop — do, run the check, read the result, iterate.

So the first question on any task is not "what is the plan", it is **"what
command will tell us this worked, and does it exist yet?"** If the answer is
"nothing", building the check *is* the first task.

Pick the weakest gate that fits, and escalate only as autonomy grows:

| Gate | Use when |
|---|---|
| Ask for the check in the prompt | ordinary work you are watching |
| A `/goal` condition | the session should keep going until a condition holds |
| A `Stop` hook running the check as a script | unattended runs; it blocks the turn from ending |
| A second opinion from a fresh subagent | the result matters more than the effort of checking it |

Then report accordingly: **show the evidence, do not assert success.** Paste the
command and its output. "Tests pass" without the output is an assertion.

## Before writing code

- Plan first when the approach is uncertain, the change spans files, or the code
  is unfamiliar. Iterate on the plan until it is right — a good plan usually
  one-shots the implementation.
- **Skip the plan when you could describe the diff in one sentence.** Planning a
  typo fix is overhead, not rigor.
- When something goes sideways mid-task, go back and re-plan. Do not keep
  pushing a plan that has already failed once.
- Be specific. Name the file, the scenario, the constraint, and what "fixed"
  looks like. Point at an existing pattern to follow rather than describing one.
  Generic instructions land maybe a third of the time; specific ones are worth
  a multiple of that, and cost less than the course-correction they avoid.
- Ask for more thinking when the trade-offs are genuinely hard. The documented
  escalation is `think` → `think hard` → `megathink` → `think harder` →
  `ultrathink`.

## Use separate context windows to check work

More tokens on a problem gives a better result; *uncorrelated* context windows
give a better result still. An agent that did not write the code is measurably
better at finding its bugs than the one that did — the same way a colleague
reviews your PR better than you re-reading it.

- Delegate wide reads (sweeps, surveys, "where is X handled") to a subagent so
  the findings come back without the file dumps.
- Delegate review to an agent that sees the diff and the criteria, not the
  reasoning that produced it.
- Give the reviewer a bounded remit: flag what breaks correctness or a stated
  requirement, and treat the rest as optional. A reviewer asked to find gaps
  will always find some, and chasing all of them produces over-engineering.
- A subagent's report is second-hand. Verify anything load-bearing yourself
  before you write it down as fact.

## Anything measurable can become a loop

For a property you can measure — CPU, memory, CI time, frame rate, latency,
bundle size — the shape is always the same: *iterate on X with a profiler and a
dataset until it hits Y*. Name the metric, name the target, hand over the tool
that measures it, and let the agent run until the number moves.

This is the verification rule applied to performance instead of correctness,
and it is worth reaching for more often than people do: the profiler is already
the check, so the loop costs almost nothing to close.

## Large multi-step work gets a checklist, not a bigger prompt

For migrations, "fix all 100 lint errors", or any exhaustive sweep: have the
tool write the full work list to a Markdown file first — filenames and line
numbers — then work down it one item at a time, verifying each and checking it
off before moving on.

The checklist is doing two jobs: it survives a context reset, and it converts
"did we get them all?" from a judgement into a count.

## Course-correct early rather than steering at the end

Interrupt as soon as the approach looks wrong — an interrupt preserves context,
so the work so far stays available to redirect. If two corrections on the same
point have not landed, the context is now polluted with failed approaches;
clear it and restart with a prompt that incorporates what you learned. A clean
session with a better prompt beats a long session carrying its own mistakes.

## Choosing where a rule should live

| Put it in | When |
|---|---|
| `CLAUDE.md` | a fact that must hold in every session — build commands, conventions, layout |
| `.claude/rules/*.md` with `paths:` | it only applies to certain files; it loads when they are touched |
| A skill | it is a procedure rather than a fact; the body costs nothing until used |
| A command in `.claude/commands/` | an inner-loop workflow run many times a day |
| A subagent in `.claude/agents/` | it needs its own context window or a restricted toolset |
| A hook | it must happen every time regardless of what the model decides |

The dividing line that matters: `CLAUDE.md` is *advisory* — it arrives as a user
message and shapes behaviour without enforcing it. A hook is *deterministic*. If
something must never happen, it is a hook or a permission rule, not a sentence.

## Keeping CLAUDE.md alive without letting it rot

Two forces pull against each other, and both are right:

- **Add:** whenever a correction is given, fold it back in so the mistake does
  not recur. Ending a correction with "update CLAUDE.md so this does not happen
  again" is the single highest-leverage habit in the corpus.
- **Prune:** for each line ask *"would removing this cause a mistake?"* If not,
  cut it. A bloated file gets ignored wholesale, so adding without pruning
  eventually destroys the file's authority.

Resolve the tension by routing, not by compromising: facts stay, procedures
become skills, file-specific rules become path-scoped rules. Target under 200
lines. If one instruction keeps getting skipped, emphasise *that line only* —
`IMPORTANT` or `YOU MUST` on the one line that needs it. Emphasising everything
emphasises nothing.

Two habits that make this cheap rather than a chore:

- Capture in the moment, not in a review pass. Press `#` mid-session to fold an
  instruction into the right file as you hit it, and include the change in the
  same commit so the team gets it too.
- Treat the file as a prompt, not a config. It goes into every request, so it
  deserves the same tuning any frequently-used prompt would get — iterate on
  the wording until the mistake rate actually drops, rather than appending and
  hoping.

## Shipping

- Small, single-purpose PRs. A median around 100–120 lines stays reviewable at
  any rate of output.
- Squash-merge so each PR is one commit: clean history, easy revert, sane
  bisect.
- Check configuration into git — settings, commands, agents, hooks, skills. The
  whole team gets the improvement, and it compounds.

## Parallelism

Isolate parallel work so sessions cannot overwrite each other — worktrees, or
separate checkouts. For large mechanical changesets, fan out to worktree agents
rather than doing them in series.

Parallelism multiplies output, not correctness. Every parallel stream still owes
its own verification loop; five unchecked sessions produce five times the
unchecked work.

## What this practice set does not license

- It does not license trusting output because the model is good. "Look only at
  the final result" is a habit that presupposes the check exists.
- It does not license inventing a source. Verification is the whole point of the
  corpus, and an unverifiable claim fails it by definition.
- It does not license adopting a practice the environment cannot support. If
  there is no browser, "verify in a browser" is not available — say so and pick
  a check that is.
