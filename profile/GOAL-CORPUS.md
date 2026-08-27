---
provenance: enforced
---

# Goal corpus — 2026-08-27

The owner's own words, captured verbatim. This is the primary evidence behind
[OWNER-PROFILE.md](OWNER-PROFILE.md); nothing in that file is derived from
anything else.

> Why this file exists. The request that opened this session asked to look at
> "all my previous claude chat chats all my feedbacks". A prior session
> established that session transcripts are not readable from inside a session
> and that no conversation export exists on this container. What *is* readable
> is the `goal` string each session carries — text the owner typed, returned
> verbatim by the session listing API. That is a real, citable record of what
> the owner asks for, and it is what this file collects. It is not the chats.

## Observed — the corpus

- The session listing returned 13 sessions for this account, all created on 2026-08-27 between 14:07Z and 15:00Z, all `RUNNING` at capture time. [src:FLEET-13-2026-08-27]
- All 13 run `claude-opus-5` in `permission_mode: auto` on environment `env_01GEni7AgBA7NiyMBecyt7K1`, and all originate from `web_claude_ai`. [src:FLEET-13-2026-08-27]
- 11 of the 13 carry a non-null `goal.condition`; it is null for `Blind testing and OODA analysis` and `Go page review and ultrathink OODA`. [src:GOALS-2026-08-27]
- Each session writes to its own outcome branch; 12 of 13 take both repositories as sources, and `Go page review and ultrathink OODA` takes only `turkertekten-ship-it/claude`. [src:FLEET-13-2026-08-27]
- Nine of the 13 run at `effort_level: xhigh`; the remaining four run at `high`. [src:FLEET-13-2026-08-27]
- The goal strings are the owner's typed input, not generated labels: they carry consistent personal voice, first-person framing, and recurring spelling variants such as `ultrahtink`, `conitnue`, `chechers`, `usefull` and `capaiblities`. [src:GOALS-2026-08-27]
- The field is **mutable**. Re-issuing `/goal` replaces the string, and only the latest survives, so any single capture is a snapshot rather than a complete record. [src:GOALS-REISSUED-2026-08-27]
- Session titles, by contrast, are generated labels and none of the analysis below rests on them. [src:GOALS-2026-08-27]

## The 11 goal strings, verbatim

Ordered oldest session first. Spelling and punctuation are exactly as captured.

| # | Session title | Goal string (verbatim) |
|---|---|---|
| G1 | RAG system and data pipeline | `continue ultrathink ooda` |
| G2 | Claude chat archive review | `i need you to look through all my previous claude chats and build internal files and systems and system prompts and claude md files and so on and never fabricate ooda ultrathink` |
| G3 | Daily file improvement system | `i need a system that runs at the end of each day, that improves my files based on looking at my prompts and continuously improves all and that is applicable for all files chats and prompts and terminals ooda ultrathink` |
| G4 | Reverse engineer chat history and system setup | `i need you to look at all my previous claude chat chats all my feedbacks and so on and reverse engineer my files for me perfectly including the system prompt claude md and my rags and task agents, firms and files ooda ultrathink` |
| G5 | AI system research and implementation | `i need you to research me and where i work at what similar firms do how the ones who are successfull use and implement ai and build me the perfect system tailored for me ultrathink ooda` |
| G6 | Claude code to Playground parity | `i need you to get my claude code upto claude playground level and capaiblities in every aspect possible thorugh extenisve web and git hub search and utilize and route to and utilize all the skills and repos and outcome based blind test all ooda ultrathink` |
| G7 | Ultrareview with data checkers | `i need /ultrareview at the end when all we built is finished and for it to include data chechers make sure that everything is based on evidence and data and that nothing is fabricated ultrathink ooda` |
| G8 | Goal prompt task division | `with every prompt i give i need it divided into tasks and make sure this works for all prompts and all chats and all terminals` |
| G9 | Comprehensive research and skill mastery | `with every prompt i give you in every chat and terminal make sure to conitnue until there is nothing open and that you continue until all is done perfected utilized and figured out and learned before the task is started from extensive web, youtube and git hub repo and skill installations and for them to be perfectly used utilized and routed to ultrathink ooda` |
| G10 | Personal skills and repos research | `do web search and git hub repo and skill search and install and use and route to and utilize all git hub skills and repos that would be usefull for me ultrathink ooda derive whats usefull for me from research about me, looking into my files and all my previous claude chats ultrathink ooda` |
| G11 | Untitled session | `i need prompt engineering and prompt perfection for all my prompts in all my chats and all my terminals, for the clear system of nick saraev to be used for him to be researched learned about and all his learnings built in to my system ultrahtink ooda use workflows and sub agents` |

G4 is this session's own goal.

## Observed — a second capture, 26 minutes later

> Framing, not a claim: a re-read at 15:30Z found the corpus had changed
> underneath the first one. That is the single most important thing in this
> file — the goal field is not a static record.

- A fourteenth session had appeared, carrying a twelfth distinct goal: `install use and utilize all of the borris churney material you can find and use it for all my prompts systems and chats ooda use workflows and subagents`. [src:GOALS-REISSUED-2026-08-27]
- Four of the fourteen sessions carried a *different* goal at 15:30Z than at 15:04Z, and two of those had been null at the first capture. [src:GOALS-REISSUED-2026-08-27]
- Three of those four re-issues were `continue ultrathink ooda`, bringing the number of sessions currently carrying that exact string to four. [src:GOALS-REISSUED-2026-08-27]
- The fourth re-issue was not a new task but a **correction**, and it is quoted in full below. [src:GOALS-REISSUED-2026-08-27]
- One session's goal was marked `met: true` — the only one so far. [src:GOALS-REISSUED-2026-08-27]

## G13 — the correction

Issued to `Goal prompt task division`, replacing G8:

> `ultrathink continue ooda this is not even close to being enough dont stop do
> all and research more from web and git hub install add to files route and
> utilize your research more and run at least 20 of these cycles ultrathink ooda`

This is follow-up feedback of exactly the kind the first capture concluded was
unreachable — the owner reading a result, judging it insufficient, and saying
so. It is worth more per word than any opening line in the table above, because
it is the only line in the corpus that reacts to delivered work rather than
requesting it.

Three things it establishes that no opening goal did:
`this is not even close to being enough` and `dont stop do all` — the first
deliverable is not the finish line. `research more from web and git hub install
add to files route and utilize your research more` — research is expected to
land in files and be routed to, not merely reported. `run at least 20 of these
cycles` — the owner counts iterations, and treats a single pass as a starting
point.

## Observed — term frequencies across the 11 goals

> Method, not a claim: counted by literal substring match over the strings in
> the table above, misspellings included.

- `ooda` appears in 10 of 11 goals; the one exception is G8. [src:GOALS-2026-08-27]
- `ultrathink` or `ultrahtink` appears in 10 of 11 goals; the one exception is G8. [src:GOALS-2026-08-27]
- G1 consists of nothing but `continue ultrathink ooda` — three words, two of which are these two terms. [src:GOALS-2026-08-27]
- `all` appears in 9 of 11 goals, most often quantifying scope: `all my prompts`, `all my chats`, `all my terminals`, `all the skills and repos`, `all my previous claude chats`. [src:GOALS-2026-08-27]
- `every` appears in 3 goals, always as `with every prompt` or `in every chat and terminal`. [src:GOALS-2026-08-27]
- `route`, in the sense of dispatching to an installed capability, appears in 3 goals (G6, G9, G10). [src:GOALS-2026-08-27]
- `fabricate` appears in 2 goals (G2, G7), both times as a prohibition. [src:GOALS-2026-08-27]
- `blind test` appears in 1 goal (G6), as `outcome based blind test all`. [src:GOALS-2026-08-27]
- `workflows and sub agents` appears in 1 goal (G11). [src:GOALS-2026-08-27]
- `terminals` appears in 4 goals, always paired with `chats` and `prompts`. [src:GOALS-2026-08-27]

## Observed — corroboration from session activity

> Framing, not a claim: each line below is another session's own one-line
> status summary, recorded verbatim. They are that session's claims about its
> own work. They corroborate the goal strings; they do not independently verify
> anything.

- `Blind testing and OODA analysis` reports `running 85 blind tests on DocX audit system; baseline 56 failed`, and it carries no goal string — the blind-testing practice appears in its behaviour rather than in its goal. [src:FLEET-13-2026-08-27]
- `RAG system and data pipeline` reports `crawler blind tests green (32/32); patching GitHub connector for hermetic testing`. [src:FLEET-13-2026-08-27]
- `Ultrareview with data checkers` reports `Python RAG repo analysis: found 10+ README/docs claims vs. missing files; building test framework`. [src:FLEET-13-2026-08-27]
- `Claude code to Playground parity` reports `4 research agents sweeping web/GitHub; testing backend execution`. [src:FLEET-13-2026-08-27]
- `Go page review and ultrathink OODA` reports `implementing §12+§14 gates & self-tests; 2 subagents building in parallel`. [src:FLEET-13-2026-08-27]
- `Daily file improvement system` reports `building nightly OODA loop; contracts frozen, fanning agents to 10 modules`. [src:FLEET-13-2026-08-27]

## What this corpus is not

It is not the conversation history. A goal string is one line the owner typed,
and the field holds only the most recent one. It does not contain the ordinary
follow-up turns, the rejected suggestions, or the reasoning — which is where
most of the useful signal in a real chat archive lives.

The one exception is a re-issued goal, and G13 shows why it matters: when the
owner replaces a goal, the replacement is feedback on what was delivered. That
makes repeated capture worth doing. Sampling this field once gives opening
lines; sampling it repeatedly catches corrections. Neither is a transcript.

The register for that material remains open as U-2 in
[../provenance/unknowns.md](../provenance/unknowns.md), and it resolves the same
way it always did: an export from claude.ai dropped into `archive/` and ingested
with `tools/ingest_chat_archive.py`.
