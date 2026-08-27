---
provenance: enforced
---

# Owner profile — standing preferences

What the owner asks for, derived only from their own words in
[GOAL-CORPUS.md](GOAL-CORPUS.md). Every preference below names the goals it
came from and how strongly they support it.

> How to read this. A preference here is an **inference**, not an observation.
> The observations are the verbatim strings in the goal corpus; the inference is
> the claim that a repeated phrasing represents a standing preference rather
> than a one-off. Each row carries a confidence grade so a weak inference cannot
> be quietly used as if it were a strong one.

## Observed — the derivation basis

- The profile is derived from 11 goal strings issued by the owner across 11 distinct sessions on 2026-08-27. [src:GOALS-2026-08-27]
- No session transcript, conversation export, or follow-up turn was available to this session; the goal strings are the entire evidence base. [src:GOALS-2026-08-27]
- The two sessions with a null goal contribute only behavioural corroboration through their status summaries, which are second-hand. [src:FLEET-13-2026-08-27]
- Two prior sessions independently pushed work to `turkertekten-ship-it/claude`, and both branches were read directly rather than inferred from their titles. [src:BRANCHES-2026-08-27T15-04Z]

## Confidence grades

| Grade | Meaning |
|---|---|
| **Strong** | Stated in 3 or more independent goals |
| **Moderate** | Stated in 2 goals, or in 1 goal and corroborated by observed behaviour |
| **Single** | Stated once. Real, but do not treat it as a general law |

## The profile

| # | Standing preference | Grade | From |
|---|---|---|---|
| P1 | Run an explicit OODA loop, and think hard before acting | **Strong** | 10 of 11 goals |
| P2 | Never fabricate; everything rests on evidence and data | **Moderate** | G2, G7 |
| P3 | Verify by outcome-based blind testing, not by inspection | **Moderate** | G6, plus behaviour in two sessions |
| P4 | Apply it everywhere — all prompts, all chats, all terminals | **Strong** | G3, G8, G9, G11 |
| P5 | Continue until nothing is open | **Moderate** | G9, G7, G4 |
| P6 | Divide every prompt into tasks | **Single** | G8 |
| P7 | Research before building, from web, YouTube and GitHub | **Strong** | G6, G9, G10 |
| P8 | Route to and actually use installed skills and repos | **Strong** | G6, G9, G10 |
| P9 | Use workflows and subagents | **Moderate** | G11, plus a direct instruction to this session |
| P10 | Build from the owner's own material, tailored to them | **Strong** | G4, G5, G10 |
| P11 | Improve the files continuously, on a daily cycle | **Single** | G3 |
| P12 | Finish with a review gate that checks the data | **Single** | G7 |

---

## P1 — OODA and deliberate thinking · Strong

`ooda` appears in 10 of 11 goals and `ultrathink`/`ultrahtink` in the same 10.
G1 in its entirety is `continue ultrathink ooda` — when the owner had nothing
else to say, this is what they said. [src:GOALS-2026-08-27]

**Standing directive.** Work in explicit Observe → Orient → Decide → Act loops
and reason at depth before acting. The procedure is
[`.claude/skills/ooda/SKILL.md`](../.claude/skills/ooda/SKILL.md).

## P2 — Never fabricate · Moderate

G2 says `never fabricate`. G7 says `make sure that everything is based on
evidence and data and that nothing is fabricated`. Two sessions reached for the
same prohibition independently. [src:GOALS-2026-08-27]

**Standing directive.** A factual claim is either sourced or it is not written
down. This is already the repository's enforced rule; the goal corpus confirms
it came from the owner rather than from a session's own invention.

## P3 — Outcome-based blind testing · Moderate

G6 asks for `outcome based blind test all`. Two sessions report blind-test
activity in their status lines — 85 blind tests in one, 32 of 32 green in
another. [src:GOALS-2026-08-27] [src:FLEET-13-2026-08-27]

**Standing directive.** Verify by running the thing and checking the outcome,
not by reading the diff and finding it convincing. A guard is real once it has
been watched rejecting something.

## P4 — Everywhere, not just here · Strong

Four goals set scope explicitly and identically: `all my prompts in all my chats
and all my terminals` (G11), `all prompts and all chats and all terminals` (G8),
`in every chat and terminal` (G9), `applicable for all files chats and prompts
and terminals` (G3). [src:GOALS-2026-08-27]

**Standing directive.** Configuration intended to change behaviour generally
belongs at user scope (`~/.claude/`), not only in one repository. A rule that
lives in one project's `CLAUDE.md` does not reach the other twelve sessions.
This is the most-repeated request in the corpus and the easiest to under-deliver
on, because a repository is the convenient place to put things.

**Caveat this profile will not hide:** this repository is a repository. Making a
rule apply across every chat and terminal needs it installed into user-scope
config, and that install is a separate act from committing a file here.

## P5 — Continue until nothing is open · Moderate

G9: `make sure to conitnue until there is nothing open and that you continue
until all is done perfected utilized and figured out`. G7 scopes its review to
`when all we built is finished`. G4 asks for files reverse-engineered
`perfectly`. [src:GOALS-2026-08-27]

**Standing directive.** Do not stop at the first deliverable. Before finishing,
enumerate what is still open and either close it or say plainly that it is open
and why. An honest list of remaining gaps satisfies this; silence does not.

## P6 — Divide every prompt into tasks · Single

G8: `with every prompt i give i need it divided into tasks and make sure this
works for all prompts and all chats and all terminals`. [src:GOALS-2026-08-27]

**Standing directive.** Decompose a request into named tasks before working it,
and report against that decomposition. A separate session is building this as a
general mechanism; this repository's obligation is to be consistent with it, not
to duplicate it.

## P7 — Research before building · Strong

G9: `learned before the task is started from extensive web, youtube and git hub
repo and skill installations`. G10: `do web search and git hub repo and skill
search`. G6: `thorugh extenisve web and git hub search`. [src:GOALS-2026-08-27]

**Standing directive.** Establish what already exists before writing something
new. The ordering in G9 is explicit — learning comes *before* the task is
started, not as a justification produced afterwards.

## P8 — Route to what is installed · Strong

The word `route` recurs in three goals: `utilize and route to and utilize all
the skills and repos` (G6), `perfectly used utilized and routed to` (G9),
`route to and utilize all git hub skills and repos` (G10).
[src:GOALS-2026-08-27]

**Standing directive.** Installing a capability is not using it. When a skill,
command or tool exists for a job, dispatch to it rather than re-implementing the
job inline. The repeated pairing of "install" with "use", "utilize" and "route
to" reads as a complaint about capabilities that were installed and then sat
unused.

## P9 — Workflows and subagents · Moderate

G11: `use workflows and sub agents`. The owner also sent this instruction
directly into this session while it was running, in the same words.
[src:GOALS-2026-08-27] [src:USER-INSTRUCTION-WORKFLOWS-2026-08-27]

**Standing directive.** Fan work out across parallel agents where the work
genuinely decomposes, rather than doing everything in one context. Note the
constraint that comes with it: a subagent's report is second-hand, so anything
load-bearing gets verified before it is written down.

## P10 — Tailored to the owner, from the owner's material · Strong

G5: `research me and where i work at what similar firms do ... build me the
perfect system tailored for me`. G10: `derive whats usefull for me from research
about me, looking into my files and all my previous claude chats`. G4:
`reverse engineer my files for me perfectly`. [src:GOALS-2026-08-27]

**Standing directive.** Build from what the owner actually has and actually
asks for, evidenced. This file is the artifact of that directive; the point of
grading each preference is so a future session can tell derived preference from
invented persona.

## P11 — Daily improvement cycle · Single

G3: `a system that runs at the end of each day, that improves my files based on
looking at my prompts and continuously improves all`. [src:GOALS-2026-08-27]

**Standing directive.** Treat the file set as something that gets revised on a
cycle from accumulated prompts, not written once. A separate session is building
this; this repository's obligation is to keep its files in a shape that such a
loop can revise — sourced, dated and separable.

## P12 — A closing review gate · Single

G7: `i need /ultrareview at the end when all we built is finished and for it to
include data chechers make sure that everything is based on evidence and data`.
[src:GOALS-2026-08-27]

**Standing directive.** Work ends with a verification pass over the claims, not
just over the code. `tools/verify_provenance.py` and `tests/run_all.sh` are this
repository's data checkers, and
[`.claude/commands/ultrareview.md`](../.claude/commands/ultrareview.md) is the
gate that runs them.

---

## Deliberately not inferred

Things the corpus touches but does not establish. They belong in
[../provenance/unknowns.md](../provenance/unknowns.md), not in a persona.

- **What "firms" means in G4.** G4 lists `task agents, firms and files` among
  artifacts to reverse-engineer. G5 uses the same word literally, as companies:
  `where i work at what similar firms do`. The two readings are incompatible and
  the corpus does not settle it. See U-7.
- **Where the owner works, and what their industry does with AI.** G5 asks for
  this to be researched. It was not researched here, and nothing in this profile
  assumes an answer.
- **What "the clear system of nick saraev" consists of.** Named once, in G11, as
  material to research. Not researched here; the name is recorded, not expanded.
- **Whether these 11 goals represent the owner's full preferences.** They are
  opening lines. The corrections, rejections and follow-ups that make up most of
  a real conversation were not reachable. A preference absent from this file may
  simply never have been typed into a goal box.
