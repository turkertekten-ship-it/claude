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
in. The first pass concluded the premise did not hold. **That conclusion was
wrong, and the correction is the most useful thing in this document.** There
are two different frameworks called CLEAR, by two different authors, and three
of their five letters expand differently. The owner was pointing at the second
one; the first pass only found the first.

## Observed — what the sources actually say

- The owner's request names "the clear system of nick saraev", recorded verbatim from this session's own goal string. [src:SESSION-Y42CYG-2026-08-27]
- A search for that exact pairing returns a CLEAR prompt-engineering framework whose five components are Concise, Logical, Explicit, Adaptive and Reflective, and attributes it to Dr. Leo Lo — not to Nick Saraev. The same search returned no result indicating Saraev created it. [src:WEBSEARCH-CLEAR-2026-08-27]
- The search index lists the originating article as "The CLEAR path: A framework for enhancing information literacy through prompt engineering", on ScienceDirect under PII S0099133323000599. [src:WEBSEARCH-CLEAR-2026-08-27]
- Research subagents report that article as Leo S. Lo, *The Journal of Academic Librarianship* 49(4), 2023, article 102720, DOI 10.1016/j.acalib.2023.102720, with an open-access copy in the University of New Mexico repository — second-hand, reported by the `saraev-clear-research` workflow and not confirmed by this session. [src:SARAEV-WORKFLOW-2026-08-27]
- Across ten searches pairing his name and properties with CLEAR, the research workflow reported finding no framework of Saraev's using that name. [src:SARAEV-WORKFLOW-2026-08-27]
- **That negative result was a limit of search coverage, not a fact.** A public repository cloned through the git proxy documents a CLEAR framework and attributes it to Saraev explicitly, under the heading "The CLEAR Framework (Effective AI Communication)" and the line "Saraev's framework for writing effective prompts and directives": Clarity, Logic, Examples, Adaptation, Results. [src:SARAEV-REPOS-2026-08-27]
- That expansion differs from Lo's in three letters of five: Clarity against Concise, Examples against Explicit, Results against Reflective. The two frameworks share an acronym and are not the same framework. [src:SARAEV-REPOS-2026-08-27]
- A second repository, independent of the first, carries a Chinese-language reconstruction built from the subtitles of his course *AI Agents Full Course 2026* (`EsTrWCV0Ph4`). It documents a "prompt contract" — break a vague requirement into goal, constraints, output format and failure conditions before starting — and its companion "reverse prompting", in which the model first asks five clarifying questions and then generates the contract. [src:SARAEV-REPOS-2026-08-27]
- The same source documents a "definition of done" as the thing most people leave out of an agent loop, a self-modifying instruction file whose "learned rules" section grows when the user corrects the agent, and a "context iceberg" rule against pasting a whole codebase into a prompt. [src:SARAEV-REPOS-2026-08-27]
- Three independent third-party repositories describe a framework they call DOE — Directive, Orchestration, Execution — in the same three layers and the same order; two of them attribute it to Nick Saraev by name. These pages were fetched and read first-hand by this session. [src:DOE-FETCHES-2026-08-27]
- In that documentation, the directive layer is defined as natural-language Markdown "specifying goal, inputs, process steps, tools, edge cases, success criteria, and guardrails". [src:DOE-FETCHES-2026-08-27]
- No page belonging to Nick Saraev was read. The egress gateway answered 403 to CONNECT for nicksaraev.com, youtube.com and every other external host tried; only `raw.githubusercontent.com` and the search API were reachable. [src:EGRESS-BLOCKED-2026-08-27]
- The session's 200-call web-search budget was exhausted by the research workflow, so no further verification was possible after that point. [src:WEBSEARCH-BUDGET-2026-08-27]

### What that means for the request

**Both CLEARs are built in, and the tool will not let you conflate them.**
`--framework` takes `clear-lo` or `clear-saraev` and refuses a bare `clear`,
because two frameworks answer to that name:

```bash
python3 tools/prompt_forge.py rules --framework clear-saraev    # the mapping
python3 tools/prompt_forge.py score --framework clear-lo FILE
```

The letters are their authors'; the rules under them are this repository's, and
each mapping is this repository's reading of where a rule lands. Both
frameworks have one component a static reading cannot check — Lo's Adaptive and
Saraev's Adaptation both describe iterating across attempts rather than what one
prompt contains — and the tool prints `n/a` for it rather than a score, because
reporting 100/100 for something never examined is the same move as reporting a
plan as a result.

One difference is worth naming: under Saraev's expansion, **E is "Examples —
specific scenarios and edge cases", so the escape clause maps to it.** Under
Lo's it maps nowhere. This repository had called the escape clause its own
house addition. On the evidence now available that was overclaiming: a
documented prompt contract of his names *failure conditions* as one of its four
required parts. The requirement is the same one; the house did not invent it,
it arrived at it.

**What is built in, and what it rests on:**

| Built in | From | Grade |
|---|---|---|
| `--framework clear-lo` | Lo's five components | attributed, author named, paper indexed |
| `--framework clear-saraev` | Clarity/Logic/Examples/Adaptation/Results | third-party documentation, read first-hand, unverified at source |
| `--profile contract` | goal · constraints · output format · failure conditions | as above |
| `--profile directive` | the DOE directive field list | as above |
| `tools/learn_rule.py` | the self-annealing "learned rules" section | as above |
| reverse prompting in `/prompt` | five clarifying questions, then the contract | as above |
| the `ICEBERG` rule | the context iceberg: a path beats a pasted document | as above |

"Unverified at source" means exactly this: two independent third parties, read
first-hand, agree on the shape of his method — and no page or video of his own
was reachable, so none of it is quotable as his wording. `youtube.com` and
`nicksaraev.com` are still refused by this container's gateway.

Nothing has been written down as his teaching. The `provenance/unknowns.md`
entries U-6 and U-7 hold the open questions, and they are what closes if his
actual material becomes reachable.

### Leads still held back

Not everything found is built in. Two categories stay out:

**His business method.** The research workflow sourced a substantial set of
rules about what is worth automating, how to package it and how to price it
[src:SARAEV-WORKFLOW-2026-08-27]. Those are real, and they are outside what a
prompt linter has any business encoding. They stay in `provenance/raw/`.

**Techniques that reached us only through a machine summary.** A video titled
"$2.4M of Prompt Engineering Hacks in 53 Mins" (`youtube.com/watch?v=CxbHw93oWP0`)
is where his prompting material is said to live. Nobody watched it. Everything
circulating from it arrived through a summariser that was independently caught
inventing attributions, so none of it is written down as his. That is a
different evidence grade from the two repositories above, which are documents
read in full.

**The lesson recorded in `CLAUDE.md` under Learned rules:** a negative result
from search coverage is not a finding. Ten searches said there was no Saraev
CLEAR; one `git clone` found it. The gateway that blocked every website served
public repositories the whole time.

---

## Does forging a prompt actually help?

The repository asserted that it did before it had any reason to. That claim is
now replaced by one trial, with its limits stated.

Four tasks, each attempted twice — once from a realistic sloppy ask, once from
the same intent written into the seven slots. A separate judge scored both
outputs against five criteria fixed in advance, saw them under neutral labels
with the order alternating, and was not told which arm was which until after
scoring.

## Observed — the A/B trial

- Across four tasks and twenty criteria, the forged prompts met 19 and the raw asks met 13. The forged arm won three tasks and tied one; it never lost. [src:FORGE-AB-TRIAL-2026-08-27]
- On the refactoring task the raw ask scored 5 of 5: the model's default reading of "clean up this function" matched the intent exactly, and the forging bought nothing. [src:FORGE-AB-TRIAL-2026-08-27]
- The largest gap was the test-writing task, 2 against 5, where the raw arm chose pytest and wrote happy-path tests — the two decisions the asker cared about, both unstated in the raw ask and both guessed wrong. [src:FORGE-AB-TRIAL-2026-08-27]
- A stated constraint was still missed: the forged summary was given an 80-word limit and returned 86 words. [src:FORGE-AB-TRIAL-2026-08-27]

### What the trial does not establish

> Framing, not a claim. Four tasks, one run each, one judge each: no
> repetition, no variance estimate, an indication rather than a measurement.
> The tasks and both arms were written by the same session, which chose
> ambiguities knowing which slots would resolve them — that favours the forged
> arm by construction, and the tied task is the only evidence that the effect
> is not total. Part of the result is near-tautological, since stating a
> requirement makes it likelier to be met; the number that is not tautological
> is the raw arm's 13 of 20, because that is how often the default guess was
> already right, and it is what the extra words are being bought against.

The honest form of the claim is therefore narrower than the one this repository
started with. Writing the slots does not make the model comply — the 86-word
summary is the counter-example sitting inside the winning arm. It makes
non-compliance **visible**, because a criterion that was written down is a
criterion that can be checked afterwards. That is the whole mechanism, and it
is smaller and more durable than "better prompts get better answers".

## The other half: checking the answer

An acceptance test that nobody reads back is decoration. `tools/check_output.py`
takes the forged prompt and the answer it produced, and counts what can be
counted: limits on words, lines, sentences and paragraphs; one-paragraph and
one-code-block demands; forbidden tokens; JSON validity; a missing preamble.

Two design decisions are worth stating, because both are refusals:

- **It scopes to the constraint sections.** A prompt written in the seven slots
  gets its CONSTRAINTS, OUTPUT CONTRACT and ACCEPTANCE TEST read, and nothing
  else — otherwise "the module has 400 lines" in the CONTEXT becomes a limit on
  the answer. A prompt without slot headings is scanned whole, and the report
  says so.
- **It lists what it could not interpret.** Most of what a prompt constrains is
  prose no machine can check. A checker reporting "all clear" over the parts it
  silently skipped would be worse than no checker, so the unchecked constraints
  are printed alongside the ones that passed.

Run against this repository's own trial data it finds the 86-word overrun that
the model judge found by reading [src:CHECK-OUTPUT-TRIAL-2026-08-27]. That is
the whole argument for it: the constraint was written down, and until now
nothing counted it.

## What the linter cannot check

Stated plainly, because a guard whose limits are unstated gets trusted past
them:

- **Whether the prompt asks for the right thing.** A perfectly specified request
  for the wrong artifact scores 100.
- **Whether the acceptance test is any good.** The rule sees that one is
  present, not that it discriminates. `prompt-critic` is the pass that reads for
  that, and it is a subagent rather than a rule for exactly this reason.
- **Adaptation across attempts.** One prompt at one moment is all a static
  reading has. Both CLEAR frameworks have a component for it, and both score
  `n/a` here rather than pretending otherwise.
- **Whether pasting was the right call.** `ICEBERG` fires on a large pasted
  block, but a chat window with no file access has no alternative. That is why
  it is `info` and why its fix says when to ignore it.
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
