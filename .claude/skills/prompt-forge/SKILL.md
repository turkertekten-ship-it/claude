---
name: prompt-forge
description: Turn a rough ask into a prompt that can be checked - seven slots, a linter, and an adversarial reading pass. Use when writing or rewriting any prompt (a chat message, a system prompt, a subagent brief, a slash command), when a prompt produced the wrong thing and you are about to retry, when someone asks to "improve", "perfect", or "engineer" a prompt, or before delegating work to another agent. Produces a prompt whose gaps are marked rather than guessed.
---

# Prompt forge

A prompt is a specification, and most disappointing output is a specification
failure rather than a model failure. The specification usually failed in one of
three ways: it never named the artifact, it never said how the result would be
judged, or it never said what to do when the request turned out to rest on
something that is not there.

Those three are mechanical, so this procedure checks them mechanically. The
part that cannot be mechanised — deciding *which* reading of an ambiguous ask
is the right one — is the part you do by hand, and the whole point of the
checks is to leave you time for it.

## The seven slots

| Slot | What it settles | Absent, the model will |
|---|---|---|
| **ROLE** | who is answering | answer as the average of everyone who has written on the topic |
| **CONTEXT** | what is already true | supply the missing facts, plausibly |
| **TASK** | the imperative and its artifact | answer the topic instead of doing the task |
| **CONSTRAINTS** | what is forbidden, and the bounds | run to whatever length it stops at |
| **OUTPUT** | the shape of the reply | return prose you have to re-read before you can use |
| **ACCEPTANCE** | how the result gets judged | produce something unfalsifiable |
| **ESCAPE** | what to do when it cannot be done honestly | produce something anyway |

The last slot is the house requirement. A prompt with no escape hatch tells the
model that returning *something* is mandatory — and something is what comes
back. One sentence fixes it: *if the file is not there, say so and stop.*

## The loop

Run it as an OODA loop. The failure this prevents is polishing the wording of a
prompt whose ambiguity was never located.

### 1. Observe — what does the prompt actually say?

Read the raw ask and run the linter over it before interpreting anything:

```bash
python3 tools/prompt_forge.py lint --profile task raw.txt      # in this repo
prompt-forge lint --profile task raw.txt                       # if installed
```

Write down which slots are absent and which hazards fired. Do not fix anything
yet. The inventory is the observation; guessing at intent is the next phase and
it belongs there.

Profiles: `task` (default) · `build` (an acceptance test is mandatory) ·
`research` (bounds are mandatory) · `system` (a role is mandatory) · `chat`
(lightest) · `directive` (a standing instruction file an agent executes:
context, constraints and acceptance all mandatory) · `contract` (the four parts
of the prompt contract documented as Saraev's: goal, constraints, output
format, failure conditions). `rules --profile P` prints the grading in force,
and it is the authority — this list is prose and can fall behind it.

### 2. Orient — find the readings, name the surprise

For each gap, ask the question that matters: **is there more than one reading
under which the work would be materially different?** That is the only kind of
ambiguity worth spending a turn on. "Improve the docs" has at least three
readings — reorganise, rewrite, expand — and they produce three different
diffs. "Use British spelling" has one.

Delegate the attack to the `prompt-critic` subagent. An author is the worst
reader of their own prompt, because they read the intention rather than the
text. The critic returns the divergent readings and the one sentence that
collapses each. Its report is second-hand: keep the readings you can see in the
text yourself.

Name the surprise. If the critic found nothing you had not already seen, the
prompt was read charitably rather than adversarially.

### 3. Decide — one reading, and what would falsify it

A **gap** is an absent slot. Fill each with exactly one of three moves, and
never a fourth. (Hazard findings — a vague word, a filler phrase — are not gaps;
they are edits. Rewrite the phrase.)

1. **Get the evidence.** The gap is a fact you can check — read the file, run
   the command, list the directory. Most CONTEXT gaps close this way.
2. **Ask.** The readings diverge and the wrong one wastes the work. One
   question, with the options named, beats a paragraph of hedging. If nobody is
   there to answer — a scheduled run, a subagent, a pipeline — this move is
   unavailable: take the reading cheapest to correct, label it in the prompt as
   an assumption, and go on. A question into an empty room returns nothing.
3. **Write an escape clause.** The gap cannot be closed now: say in the prompt
   what to do when the assumption fails. This is what converts an unknown into
   an instruction instead of into an invention.

Inventing a plausible requirement is not a fourth move. A prompt that quietly
grows requirements nobody wrote produces work nobody asked for, and the growth
is invisible in the output.

### 4. Act — compile, re-lint, ship

```bash
python3 tools/prompt_forge.py compile --profile build raw.txt > forged.md
```

`compile` files your own lines under the seven headings and marks every gap as
`<<MISSING: ...>>`. It cannot write content, by construction — the tests prove
every line of its output is either a line you wrote, a heading, or a marker.
Fill the markers yourself, using the three moves above, then re-lint until it
exits 0:

```bash
python3 tools/prompt_forge.py lint --profile build forged.md   # 0 = clean
```

**`clean` means exit 0: no error and no warn findings.** Info findings are
advisory, and the tool ignores them unless you pass `--strict` — which is worth
doing for a prompt that will be reused rather than sent once.

## Worked example

Raw, as it arrived:

> fix the failing test and clean up the module while you're at it

Linted: `FALSE_PREMISE` (which failing test?), `VAGUE_QUALITY` (`clean up`),
`NO_OUTPUT`, `NO_ACCEPTANCE`, `NO_ESCAPE`, and three more for the context,
constraints and role it never states. **Score 38/100.**

The divergent readings: `clean up` could mean reformat, restructure, or delete
dead code — three different diffs, and two of them are not what anyone wanted.

Forged:

> **Role.** You are working in this Python 3.11 repository.
> **Context.** `tests/test_ingest.py::test_dedupe` fails with `KeyError: 'uri'`
> after commit `1d7ce8f`. The module under test is `src/oodarag/ingest/base.py`.
> **Task.** Make that test pass.
> **Constraints.** Touch only `base.py`. Do not change the test. No new
> dependencies.
> **Output.** A unified diff, then two sentences on the root cause.
> **Acceptance.** `python3 -m unittest tests.test_ingest -v` passes, and
> `bash tests/run_all.sh` stays green.
> **If you cannot.** If the failure does not reproduce, stop and report what
> you actually saw rather than changing code to fit the description.

**Score 100/100.** The second prompt is longer. Whether that buys anything is a
question this repository now has one measurement of rather than an opinion: in
a blind trial of four tasks, prompts written this way met 19 of 20 stated
criteria against the raw asks' 13 [src:FORGE-AB-TRIAL-2026-08-27]. On one of
the four the raw ask scored full marks and the forging bought nothing. See
`docs/prompting.md` for what that trial does and does not establish — it is
four tasks, run once.

Both numbers are pinned in `tests/test_prompt_forge.py` against the fixtures in
`tests/fixtures/prompts/`, because they were wrong once: this section quoted 34
and 96, which nobody had measured. A document in this repository asserting an
unmeasured number is the failure the provenance guard exists to catch, and it
does not become acceptable for being a small one.

## Anti-patterns

- **Polishing tone instead of removing ambiguity.** Rewriting for elegance
  changes nothing about what comes back. Locating the two readings does.
- **Role inflation.** "You are the world's best engineer" adds no constraint.
  "You are reviewing this for a reader who has never seen the codebase" does.
- **Stacking politeness.** Every filler word dilutes the instructions it sits
  between. The linter grades this as `info` because it costs little each time —
  and it recurs in every prompt you ever send.
- **Assuming shared history.** Phrases of the `as we discussed` family point at
  a conversation the model cannot retrieve. It will reconstruct one.
- **Perfecting a prompt for work that should not be delegated.** If you cannot
  state the acceptance test, you do not yet know what you want. Find that out
  first; no amount of prompt engineering substitutes for it.

## Closing a forge pass

Done when you can answer:

1. Which slot was missing, and how did you fill it — evidence, question, or
   escape clause?
2. Which competing reading did you close off, and which sentence closed it?
3. Does `prompt_forge lint` exit 0 at the profile this prompt will run under?
4. What is still unknown, and does the prompt now say what to do about it?

If any answer needs a hedge, the prompt is not finished. Say so rather than
rounding it up.
