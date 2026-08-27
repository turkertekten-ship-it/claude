---
provenance: enforced
---

# Loop log — the prompt system — 2026-08-27

One OODA loop, recorded because the doctrine asks for the surprise to be
written down rather than remembered. `session_01Vp6Nnb1YQ9xzppSDMSBEQD`, branch
`claude/session-y42cyg`. [src:SESSION-Y42CYG-2026-08-27]

## The request

> The owner's words, recorded verbatim in the session record: prompt
> engineering and prompt perfection for all their prompts, in all their chats
> and all their terminals; the "clear system of nick saraev" to be researched,
> learned about, and its learnings built in; using OODA, workflows and
> subagents. [src:SESSION-Y42CYG-2026-08-27]

## Observed

- The doctrine this work extends was not on the default branch. `claude/rag-system-data-pipeline-rdkde9` is the repository's HEAD branch and carries a RAG pipeline; the doctrine, prompts, provenance tooling and OODA skill were on `claude/review-chat-archive-zrynr4`, which advanced twice during the reading of it. [src:PROMPT-SCORES-2026-08-27]
- CLEAR is a real prompt-engineering framework — Concise, Logical, Explicit, Adaptive, Reflective — attributed to Dr. Leo Lo, with no search result connecting Nick Saraev to it. [src:WEBSEARCH-CLEAR-2026-08-27]
- What third parties do attribute to Saraev is a different framework, DOE, and its directive layer is a field list rather than a prompting method. [src:DOE-FETCHES-2026-08-27]
- Nothing he wrote could be read: the egress gateway refused every host except `raw.githubusercontent.com` and the search API. [src:EGRESS-BLOCKED-2026-08-27]
- The 200-call web-search budget was spent by the research workflow before the main session could re-verify anything independently. [src:WEBSEARCH-BUDGET-2026-08-27]

## Orient — four surprises, in the order they arrived

**The premise did not hold.** The request was to build in "the clear system of
nick saraev". The work expected to find his framework and encode it. What the
sources support is that CLEAR is Lo's [src:WEBSEARCH-CLEAR-2026-08-27] and that
the framework attached to Saraev's name is called something else
[src:DOE-FETCHES-2026-08-27]. The honest response was not to quietly build
something CLEAR-shaped and call it his, and not to refuse either: it was to
build the system, use CLEAR with its real author's name on it, take from the
Saraev material only the part that survives grading, and say plainly which is
which.

**The linter's first real subject was itself.** Pointing it at this
repository's own prompts was meant to grade four files. It found five detector
bugs instead — a role written as "You process exports", an escape clause
worded "if no export is present, say exactly that and stop", a generic
"demonstrate the failure" read as a false premise, a "Constraints:" heading
missed by a singular-only cue, and a contradiction rule firing on two words a
hundred lines apart. [src:PROMPT-SCORES-2026-08-27] Every one was a rule that
was wrong about a good file. Had the files been strangers' rather than the
house's, the temptation would have been to believe the tool.

**The corpus auditor reproduced the failure it exists to prevent.** Its first
run reported 369 of the owner's prompts and ranked their weaknesses
confidently. 421 of the 433 user turns it read were tool results — `ls` output,
API JSON, search results — because that is how a transcript stores them.
[src:PROMPT-HABITS-RUN-2026-08-27] The report was a portrait of the harness
wearing the owner's name, which is exactly the kind of confident, plausible,
wrong artifact this repository exists to make impossible. The filter now keys
on `block_types` and the exclusions are printed, not dropped.

**The deepest part of the request is the least verifiable part.** Research ran
into a policy wall and then a budget wall [src:EGRESS-BLOCKED-2026-08-27]
[src:WEBSEARCH-BUDGET-2026-08-27]. That does not make the answer "no". It makes
the answer "here is the system, here is what is sourced, and here is the one
video that would close the rest".

## Decide

> The decision, in one sentence: build the standard from rules this repository
> can defend on its own, attach an outside framework only where a source
> supports it and name the author, and leave the Saraev-specific material as
> marked leads rather than doctrine.
>
> What would falsify it: a source in Saraev's own words setting out a named
> prompting framework. That would move `U-6` and `U-7` into observations, and
> the `directive` profile's provenance note is where it would land. Nothing
> else in the system depends on the attribution, which is the point of having
> built it that way.

## Act — and what came of it

- `tools/prompt_forge.py` and `tools/prompt_habits.py` ship with tests that watch every rule reject something, and the whole suite passes. [src:PROMPT-SCORES-2026-08-27]
- Two of the repository's own command prompts were improved against the standard and re-measured with the same build: 78 to 90, and 82 to 100. [src:PROMPT-SCORES-2026-08-27]
- The system installs into `~/.claude` for every terminal, and the installer refuses to install a build whose tests fail. [src:PROMPT-SCORES-2026-08-27]

## Still open

`U-6`, `U-7` and `U-8` in [unknowns.md](unknowns.md): what Saraev actually
teaches about prompting, what the owner meant by "the clear system", and
whether these seven slots are the right seven for the owner's real corpus —
which cannot be settled until that corpus, rather than this container's, is
indexed.
