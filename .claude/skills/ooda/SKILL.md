---
name: ooda
description: Run an explicit Observe-Orient-Decide-Act loop on a task, recording evidence as you go. Use when a request rests on facts you have not yet checked, when starting work in an unfamiliar repository or environment, when a plan depends on what another session or system has already done, or whenever the honest answer might be "that does not exist". Produces sourced observations rather than plausible narrative.
---

# OODA

A loop that forces the situation to be examined before it is interpreted.
Its purpose here is narrow and practical: **most fabrication is Orient running
on an empty Observe.** When you have not looked, the mind supplies something
that fits the request. This procedure makes looking a separate, recorded step.

## When to run it

- The request assumes something exists ("look through my previous chats", "fix
  the failing test", "update the config") and you have not confirmed it does.
- You are starting in an unfamiliar repository, environment, or codebase.
- Your plan depends on work someone or something else has done.
- You notice yourself about to write "presumably" or "it looks like".

## The loop

### 1. Observe — enumerate, do not interpret

List what is actually there. No conclusions in this phase.

- Check the obvious location, then the non-obvious ones. Absence is a finding:
  an empty directory, a repository with zero commits, a search returning `{}`.
- Prefer the authoritative source over an inference from a name. A file listing
  beats a guess from a title; a tool's own output beats a summary of it.
- Record each capture in `provenance/sources.yaml` as you go — id, kind, time,
  the exact command, and the evidence. Bulky output goes in `provenance/raw/`.
- Note explicitly what you *could not* reach and why. That belongs in
  `provenance/unknowns.md`, not in a silence.
- **Before writing down that something is not there, try a second route.** A
  refusal is a fact about one path, not about the world. In this environment
  the egress gateway refused every website while the git proxy served public
  repositories the whole time, and ten searches concluded a framework did not
  exist that one `git clone` then found. Ask what else could hold the answer:
  a clone rather than a fetch, a file on disk rather than an API, the thing
  itself rather than an index of it.
- **A negative result carries its method.** "Ten searches found nothing" is a
  statement about search coverage. Write it that way, so the next reader knows
  what would overturn it.

Stop when you can state what exists and what does not without hedging.

### 2. Orient — interpret, and name the surprise

Now say what it means. Two things must be written down:

- **The reading.** What situation do these observations describe?
- **The surprise.** Where did reality diverge from what you assumed walking in?

If nothing surprised you, Observe was probably too shallow — go back. A loop
whose Orient exactly matches its opening assumption has usually not looked at
anything.

Distinguish sharply between:

| Grade | Meaning | How to write it |
|---|---|---|
| Verified | you ran it and saw the output | claim with `[src:ID]` |
| Second-hand | another system or session reports it | claim, marked second-hand, with the reporter named |
| Unknown | not established | an entry in `unknowns.md` |

Never silently promote second-hand to verified. That is the most common way an
honest process produces a dishonest artifact.

### 3. Decide — smallest action, and what would falsify it

State one decision, in one sentence, plus the cheapest thing that would prove
it wrong. A decision with no falsifier is a preference.

**Check whether it was already tried.** `provenance/rejected.md` records
approaches that were attempted and abandoned, with the reason each failed. An
entry is not a prohibition — constraints change — but rebuilding something that
already cost a loop, without knowing it did, is the avoidable version.

**Check the decision against the request, not only against the last loop.** The
loop asks what the previous Act opened, and what an Act opens is usually a
consequence of that Act — so a chain of honest loops walks into its own
machinery and stays there. In this repository nineteen of twenty consecutive
commits went to internal hygiene while the request had been a prompt system.
Every finding was real; the sequence still drifted. Every few loops, count what
the recent ones delivered against what was asked for, and if the answer is
mostly upkeep, spend the next one on the request.

Prefer the action that produces evidence over the action that produces output.
If the situation is genuinely ambiguous and the readings lead to materially
different work, this is where you ask — not after building the wrong thing.

### 4. Act — and capture the result

Do it. Then capture what happened as new evidence, which opens the next
Observe.

**Commit the work before you break it.** A falsifier usually means damaging
something on purpose — a bad input, a removed file, a reverted fix — and undoing
that damage with a blunt instrument takes uncommitted work with it. Commit
first, break second, restore with `git checkout --` rather than `reset --hard`. Run `python3 tools/verify_provenance.py` before you call the loop
closed; if it fails, the loop is not closed.

## Anti-patterns

- **Expanding a label into content.** A session titled "RAG system and data
  pipeline" tells you a title exists. It does not tell you what was built.
- **Treating a summary as the thing.** Another session's one-line status is its
  claim about its work, not the work.
- **Reporting the plan as the result.** "I reviewed the chats" when what you
  did was list session metadata is a fabrication, however small.
- **Empty unknowns.** If your loop produced no open questions, you either
  solved everything or you stopped looking. It is almost always the latter.

## Closing a loop

A loop is done when you can answer, in plain terms:

1. What exists? (sourced)
2. What does not exist, or could not be reached? (in `unknowns.md`)
3. What did I do about it?
4. What is still open?

If any answer needs a hedge, the loop is still open. Say so rather than
rounding it up.
