---
name: researching-before-acting
description: Runs an exhaustive research pass before starting a task, then routes the findings through an explicit OODA loop and refuses to stop while anything is open. Gathers from the web, from video, from GitHub repositories, and from installed skills; separates a blocked network from a missing credential; records every finding as a citable source. Use when a task rests on facts that have not been checked, when a source appears unreachable, when starting in an unfamiliar repository, when the honest answer might be "that does not exist", or whenever a request asks for something to be figured out thoroughly rather than quickly.
---

# Researching before acting

Most bad output is not a reasoning failure. It is a *looking* failure: the work
started before the situation was known, and everything after that was fluent
invention built on an assumption nobody checked.

This skill is the antidote in three parts. **Research the ground first.**
**Route what you find through an explicit loop.** **Do not stop while anything
is open.**

## The loop

Copy this checklist and tick it as you go. An unticked box is not a stopping
point.

```
Research pass
- [ ] 1. Enumerate what exists locally, before reading anything about it
- [ ] 2. Establish what the environment can actually reach
- [ ] 3. Gather from every reachable source: web, video, repositories, skills
- [ ] 4. Verify second-hand claims against a primary source
- [ ] 5. Orient: state the reading, and name the surprise
- [ ] 6. Decide: one action, with what would falsify it
- [ ] 7. Act, then re-observe the result
- [ ] 8. Close: what is done, what is open, what could not be reached
```

## 1. Enumerate before interpreting

List what is actually there. No conclusions in this step.

Check the obvious location, then the non-obvious ones. **Absence is a finding**:
an empty directory, a branch with no commits, a search returning nothing. Prefer
the authoritative source over an inference from a name — a file listing beats a
guess from a title.

**Never expand a label into content.** A branch called `rag-system-data-pipeline`
tells you a label exists. It tells you nothing about what was built, chosen, or
rejected. The same holds for a session title, a filename, or another agent's
one-line summary.

## 2. Establish what is reachable, and distinguish the barriers

Before planning any fetch, find out what the network permits. This is the step
most often skipped, and skipping it produces the most confidently wrong
conclusion available: *"that source is impossible"* when it is merely
unconfigured.

Four barriers look identical from inside a `try/except` and have different
remedies:

| Barrier | What it looks like | Remedy |
|---|---|---|
| Egress blocked | connection refused at CONNECT, before TLS | none in code — the host is not on the allowlist |
| Auth required | the host answered, and asked for a credential | supply a key |
| Rate limited | the host answered, and asked you to wait | wait for the window |
| Not found | the host answered; that path does not exist | fix the path |

Only the first is genuinely impossible from where you stand. Establish which one
you are facing before reporting anything as unavailable, and **never inherit
another agent's verdict** — re-probe it yourself. "The site is blocked" and
"the site is blocked but its API host is open and wants a key" are the same
observation reported at two different levels of usefulness.

When egress is an allowlist rather than a blocklist, mirrors, reader-proxies and
third-party scrapers are all equally blocked. Probing twenty of them is wasted
work. Probe one, learn the shape, and go looking for an *allowed* host that
serves the same data.

## 3. Gather widely, from what is actually reachable

Run these in parallel; they fail in different directions.

- **Web search and fetch** — for the authoritative document. Prefer the vendor's
  own docs over a blog restating them.
- **Video** — transcripts and talks carry reasoning that never reaches
  documentation. Where the site is blocked, the official API may not be; and a
  caption file exported by hand needs no network at all.
- **Repositories** — read the source rather than the README. A published
  constant, a default, or an error string settles an argument that prose leaves
  ambiguous.
- **Installed skills** — check what is already available before writing anything
  new. Duplicating an existing skill is worse than not having one, because now
  two things claim the same trigger.

Delegate breadth to subagents when the streams are independent, and remember
what comes back: **a subagent's report is second-hand.** It is another process's
claim about what it saw. Verify anything load-bearing yourself. Delegation
multiplies reach, not evidence.

## 4. Grade every claim

| Grade | Meaning | How to write it |
|---|---|---|
| Verified | you ran it and saw the output | state it plainly, with the evidence |
| Second-hand | another agent, session or document reports it | state it, marked as such, naming the reporter |
| Unknown | not established | say so; do not round it up |

Never silently promote second-hand to verified. That is the most common way an
honest process produces a dishonest artifact.

## 5. Orient — and name the surprise

Write down two things:

- **The reading.** What situation do these observations describe?
- **The surprise.** Where did reality diverge from what you assumed walking in?

If nothing surprised you, step 1 was too shallow. Go back. A loop whose
conclusion exactly matches its opening assumption has usually not looked at
anything.

## 6. Decide — with a falsifier

One decision, one sentence, plus the cheapest thing that would prove it wrong.
A decision with no falsifier is a preference. Prefer the action that produces
evidence over the action that produces output.

## 7. Act, then re-observe

Run it. Then look at what actually happened — the test output, the exit code,
the rendered result. **Running the thing is part of building it.** A module that
compiles is not a module that works, and the gap between those two is where most
defects live.

When the result contradicts the plan, that is the next Observe, not a nuisance.

## 8. Close honestly

A task is done when you can answer, without hedging:

1. What exists? (verified)
2. What does not exist, or could not be reached? (named, with the barrier)
3. What did I do about it?
4. What is still open?

If any answer needs a hedge, it is still open — say so rather than rounding up.
**Say what you did not do.** Scope dropped, checks skipped, things out of reach:
state them explicitly. An omission reads as a claim of completeness.

## Anti-patterns

- **Orienting on an empty Observe.** Interpreting before looking. This is where
  fabrication comes from — when you have not looked, the mind supplies something
  that fits the request.
- **Reporting the plan as the result.** "I reviewed the sources" when what you
  did was list their titles.
- **Inheriting a verdict.** Repeating another agent's "that is blocked" without
  re-probing it.
- **Treating a summary as the thing.** A one-line status is a claim about work,
  not the work.
- **Stopping at the first obstacle.** A blocked host is a fact to route around,
  not a reason to stop. Find the allowed host, the offline path, or the
  credential — and if none exists, say precisely that, having looked.
- **An empty open-questions list.** If the work produced none, you either solved
  everything or stopped looking. It is almost always the second.

## Tooling in this repository

```bash
make reachability                    # what this host can fetch, and why not
make skills                          # discover and lint every SKILL.md
python3 -m oodarag.cli loop --cycles 1   # one full OODA cycle over the corpus
python3 tools/verify_provenance.py       # reject unsourced claims
```

The barrier taxonomy in step 2 is implemented in `src/oodarag/net/reachability.py`
and is what `make reachability` reports.
