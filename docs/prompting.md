---
provenance: enforced
---

# The prompt standard

`CLAUDE.md` §6 states the rule: a prompt is a specification, and a requirement
is either written down or it is not in force. This document is the rest of it —
what the checks are, where each idea came from, and which parts are this
repository's own invention rather than anyone's published framework.

The tool is `tools/prompt_forge.py`. The procedure is
`.claude/skills/prompt-forge/SKILL.md`. This file is the reasoning behind both.

---

## The seven slots

| Slot | Settles | Absent, the model will |
|---|---|---|
| ROLE | who is answering | answer as the average of everyone who has written on the topic |
| CONTEXT | what is already true | supply the missing facts, plausibly |
| TASK | the imperative and its artifact | answer the topic instead of doing the task |
| CONSTRAINTS | what is forbidden, and the bounds | run to whatever length it stops at |
| OUTPUT | the shape of the reply | return prose that must be re-read before it is usable |
| ACCEPTANCE | how the result gets judged | produce something unfalsifiable |
| ESCAPE | what to do when it cannot be done honestly | produce something anyway |

Six of the seven are ordinary prompt craft, and versions of them appear in every
published framework anyone has written. The seventh is this repository's, and it
is the one that matters most here: a prompt with no stated failure case tells
the model that returning *something* is mandatory. That is the same failure
`tools/verify_provenance.py` catches after the fact, caught before it.

## Profiles

A missing slot costs differently depending on what the prompt is for.

| Profile | What it is for | Graded hardest on |
|---|---|---|
| `task` | a one-off ask | TASK, OUTPUT, ESCAPE |
| `build` | work that changes code | ACCEPTANCE — no test, no build |
| `research` | open-ended investigation | CONSTRAINTS — an unbounded search never ends |
| `system` | a persona or standing prompt | ROLE, CONSTRAINTS |
| `chat` | a message in a conversation | TASK; the rest advisory |
| `directive` | a standing instruction file an agent executes | everything but ROLE |

`prompt_forge.py rules --profile P` prints the grading actually in force.

---

## Where this came from

> Framing, not a claim: this section separates what was verified from what was
> only reported, because the request that produced this system rested on an
> attribution that turned out not to hold.

The owner asked for "the clear system of nick saraev" to be researched and built
in. Two separate things were found, neither of them quite that.

## Observed — what the sources actually say

- The owner's request names "the clear system of nick saraev", recorded verbatim from this session's own goal string. [src:SESSION-Y42CYG-2026-08-27]
- A search for that exact pairing returns a CLEAR prompt-engineering framework whose five components are Concise, Logical, Explicit, Adaptive and Reflective, and attributes it to Dr. Leo Lo — not to Nick Saraev. The same search returned no result indicating Saraev created it. [src:WEBSEARCH-CLEAR-2026-08-27]
- The search index lists the originating article as "The CLEAR path: A framework for enhancing information literacy through prompt engineering", on ScienceDirect under PII S0099133323000599. [src:WEBSEARCH-CLEAR-2026-08-27]
- Research subagents report that article as Leo S. Lo, *The Journal of Academic Librarianship* 49(4), 2023, article 102720, DOI 10.1016/j.acalib.2023.102720, with an open-access copy in the University of New Mexico repository — second-hand, reported by the `saraev-clear-research` workflow and not confirmed by this session. [src:SARAEV-WORKFLOW-2026-08-27]
- Across ten searches pairing his name and properties with CLEAR, the same workflow reports finding no framework, course, video, article or post of Saraev's using that name — a negative result, second-hand, and one that rests on search-index coverage rather than on reading his sites. [src:SARAEV-WORKFLOW-2026-08-27]
- Three independent third-party repositories describe a framework they call DOE — Directive, Orchestration, Execution — in the same three layers and the same order; two of them attribute it to Nick Saraev by name. These pages were fetched and read first-hand by this session. [src:DOE-FETCHES-2026-08-27]
- In that documentation, the directive layer is defined as natural-language Markdown "specifying goal, inputs, process steps, tools, edge cases, success criteria, and guardrails". [src:DOE-FETCHES-2026-08-27]
- No page belonging to Nick Saraev was read. The egress gateway answered 403 to CONNECT for nicksaraev.com, youtube.com and every other external host tried; only `raw.githubusercontent.com` and the search API were reachable. [src:EGRESS-BLOCKED-2026-08-27]
- The session's 200-call web-search budget was exhausted by the research workflow, so no further verification was possible after that point. [src:WEBSEARCH-BUDGET-2026-08-27]

### What that means for the request

**CLEAR is real, and it is Lo's.** It is built in as a reporting lens:

```bash
python3 tools/prompt_forge.py rules  --framework clear     # the mapping
python3 tools/prompt_forge.py score  --framework clear FILE
```

The letters are his; the rules under them are this repository's, and the mapping
is this repository's reading of where each rule lands. Two of his five —
Adaptive and Reflective — describe how you work across attempts rather than what
a single prompt contains. Adaptive gets no static check at all, and the tool
prints `n/a` for it rather than a score, because reporting 100/100 for something
never examined is the same move as reporting a plan as a result.

**The Saraev material is a lead, not a source.** What can be established is that
third parties document a DOE framework and attribute it to him. What cannot be
established from here is anything in his own words: his sites were unreachable.
So his name appears in this repository in exactly two places — the `directive`
profile, whose required field list is taken from that third-party documentation,
and this section, which says where that came from and how thin it is.

Nothing has been written down as his teaching. The `provenance/unknowns.md`
entries U-6 and U-7 hold the open questions, and they are what closes if his
actual material becomes reachable.

### Leads held back, and where they are

The research workflow returned a large, carefully graded body of material
[src:SARAEV-WORKFLOW-2026-08-27]. Its own summary of the gap is the useful part:
what it could source of his method is a **business and scoping** method — how to
decide what is worth automating, how to package and price it — and on prompting
technique specifically it verified nothing in his own words. Those business
rules are real leads with URLs, and they are outside what a prompt linter has
any business encoding, so they stay in `provenance/raw/` and are not doctrine
here.

The prompting material it found traces to one artifact: a video on his channel
titled "$2.4M of Prompt Engineering Hacks in 53 Mins (GPT, Claude)"
(`youtube.com/watch?v=CxbHw93oWP0`). Nobody watched it. Every technique
circulating from it reached the workflow through a machine summary of it, and
the summariser was independently caught inventing attributions, so not one of
those techniques is written down here as his.

Worth noting for whoever closes this: several of those unverified leads —
explicit output formats, information density over length, few-shot examples —
would land on rules this repository already has (`NO_OUTPUT`, `FILLER` and
`WALL`, `NO_EXAMPLE`). That convergence is not evidence for either side. The
rules were not derived from him, and they do not become his when a summary of a
video happens to agree with them.

---

## What the linter cannot check

Stated plainly, because a guard whose limits are unstated gets trusted past
them:

- **Whether the prompt asks for the right thing.** A perfectly specified request
  for the wrong artifact scores 100.
- **Whether the acceptance test is any good.** The rule sees that one is
  present, not that it discriminates. `prompt-critic` is the pass that reads for
  that, and it is a subagent rather than a rule for exactly this reason.
- **Adaptation across attempts.** One prompt at one moment is all a static
  reading has.
- **Whether a claimed technique works.** Every rule rationale in the tool is
  stated as this repository's standard, never as a finding about model behaviour
  — because that would be a factual claim, and it would need a source.

A finding that is wrong about a particular prompt is a bug in the rule. Fix the
rule and add the case to `tests/test_prompt_forge.py`; exempting the file
quietly retires the rule for everyone.

## Prompts that leave this machine

Hooks, the verifier, and the linter exist here and nowhere else. For a chat
window, another vendor's assistant, or a terminal without this repository,
`prompts/portable-preamble.md` carries the parts that survive being pasted, and
`tools/install_prompt_system.sh` puts the commands into `~/.claude` so every
terminal on this machine has them.
