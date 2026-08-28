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

## Second loop — the critic pass

The `prompt-critic` subagent was pointed at the three artifacts the owner would
actually rely on. It is the fifth surprise, and the sharpest:

**The skill's worked example quoted two scores nobody had measured.** It
claimed 34/100 for the raw ask and 96/100 for the forged one. The tool prints
38 and 100. Two invented numbers had been sitting inside the procedure that
teaches the rule against inventing numbers — in a repository whose first line
is that a claim is either sourced or not written down. They are now pinned to
fixtures by a test, so the document cannot drift from the tool again.

Chasing that number also found three real bugs in the linter, all of which had
been silently retiring rules:

- A contraction counted as an identifier. `while you're at it` anchored the
  reference in `fix the failing test`, so `FALSE_PREMISE` did not fire on the
  single most common phrasing of the thing it exists to catch.
- The anchor was looked for in the inline-code-stripped line, which removes
  exactly the path that would make a reference concrete.
- A markdown label hid the imperative: `**Task.** Write the parser` reported
  `NO_TASK`.

And two rules were too coarse: a markdown blockquote is a quotation rather than
an instruction, and "the only kind of" is a noun phrase rather than a hedge.

The critic's other findings were about the documents, and the two worth naming
are both failures of the same kind — an instruction with no branch for the case
where nobody is there. The travelling preamble told a model to ask a question
when a gap changes the output, with no branch for a scheduled run or a pipeline
where there is nobody to answer; it resolved to *ask and stop*, which returns
nothing. The document forbidding a model to return nothing had an unguarded
path to returning nothing in its own escape clause. The skill had the same hole
one layer down, in the procedure most likely to be run by a subagent with no
user. Both now have the non-interactive branch: take the reading cheapest to
correct, label it, deliver.

> The surprise worth keeping: every one of these was in an artifact that had
> already passed its own linter. A mechanical check catches the absence of a
> slot. It cannot catch a slot filled with something that does not survive
> being read adversarially, which is the whole reason the critic is a separate
> agent rather than another rule.

## Third loop — the premise was right after all

The stop condition for this work said the request could not be satisfied as
stated, because its premise did not hold: CLEAR was Lo's, and what third
parties attributed to Saraev was DOE, an agent architecture rather than a
prompting framework.

That was wrong, and the way it was wrong is the most instructive thing here.

The evidence for it was a negative result: ten searches pairing his name with
CLEAR returned nothing [src:SARAEV-WORKFLOW-2026-08-27]. A negative result from
one access path was allowed to stand as a fact about the world. It took one
`add_repo` call and one `git clone` to overturn: the git proxy serves anonymous
reads of public repositories, and had done so the whole time the egress gateway
was refusing every website [src:EGRESS-BLOCKED-2026-08-27]. Two independent
repositories document his method, and one of them states plainly, under its own
heading, that CLEAR is "Saraev's framework for writing effective prompts and
directives" — Clarity, Logic, Examples, Adaptation, Results
[src:SARAEV-REPOS-2026-08-27].

> The surprise: the failure was not in the research, which was careful and
> graded its sources honestly. It was in treating "we looked hard and found
> nothing" as equivalent to "there is nothing", when every search had gone
> through a single channel that a policy wall had already narrowed. The
> discipline that catches an unsourced claim did not catch an over-read
> absence.

There is a second correction inside the first. This repository had written down
the escape clause as its own house addition to prompt craft. The prompt
contract documented as his names *failure conditions* as one of four required
parts [src:SARAEV-REPOS-2026-08-27]. The requirement was not invented here; it
was arrived at, which is a weaker and more accurate claim.

Both corrections are now in `CLAUDE.md`, `docs/prompting.md`, the observations
and the unknowns register, and the first of them is rule 1 in the new Learned
rules section — appended by `tools/learn_rule.py`, which implements the
self-annealing pattern the same sources document.

## Fourth loop — measuring the thing instead of asserting it

Observe found nothing new to find: the two cloned repositories held exactly two
Saraev files between them, and the GitHub API refused search outright — a
policy denial, not a wall to climb around. That thread is closed until the
owner supplies a source or the network changes.

So the loop turned on the system itself, and found a claim sitting at its
centre with nothing under it. `docs/prompting.md` and the skill both said the
forged prompt "is the one that gets a usable answer on the first turn". Nobody
had ever run one. In a repository whose whole apparatus exists to stop exactly
that, the unsourced claim was the one asserting the apparatus works.

Four tasks were run twice each — once from a sloppy ask, once from the same
intent in the seven slots — and scored by a judge that saw both outputs under
neutral labels, order alternating, un-blinded only afterwards. Forged prompts
met 19 of 20 criteria; the raw asks met 13 [src:FORGE-AB-TRIAL-2026-08-27].

> The surprise is in the two results that did not fit the story. On the
> refactoring task the raw ask scored full marks — the model's default reading
> of `clean up this function` already matched the intent, and every extra word
> of forging was waste. And the *winning* arm broke a constraint it had been
> given in writing, returning 86 words against an 80-word limit. Both are
> deflating, and both are more useful than the headline: the slots do not make
> a model comply, and they are not always needed.

The claim in the documents is now the narrower one that survives: writing a
requirement down does not make it happen, it makes the failure to do it
visible, because a criterion that was written can be checked afterwards. That
is smaller than "better prompts get better answers" and it is the part that is
actually true.

The trial's own weakness is recorded with it rather than corrected for: the
tasks and both arms were written by the session that ran them, which chose
ambiguities knowing which slots would resolve them.

## Fifth loop — the half that was missing

The fourth loop's Act produced the evidence that opened this one: the winning
arm of the trial broke an 80-word limit that was written in its own prompt.

Observe went looking for what a prompt actually constrains in checkable terms
and found a small vocabulary — across every forged prompt in this repository,
five countable phrasings in total. Most constraints are prose: *touch only
`base.py`*, *do not change behaviour*.

> The surprise: the system had been built entirely on the specification side.
> It makes you write an acceptance test and then never reads it back. The
> 86-word answer had its limit sitting in the prompt the whole time, and the
> only thing that noticed was a language model asked to read carefully.

`tools/check_output.py` closes that half for the countable subset, and its
design is mostly refusals — it scopes to the constraint sections so a number
describing the input is not read as a limit on the answer, and it prints every
constraint it could not interpret rather than reporting "all clear" over them
[src:CHECK-OUTPUT-TRIAL-2026-08-27].

Writing it found two bugs in itself before it shipped: identical demands stated
in two sections were checked twice, and only the first clause of *"No bullet
points, no headings, no bold labels"* was ever evaluated — an early `continue`
had silently dropped two thirds of that sentence.

## Sixth loop — the checker was built backwards

Observe asked a simple question of the previous loop's tool: across this
repository's own forged prompts, how many constraints can actually be checked?

The answer was worse than expected and then more interesting than expected. The
exemplar in the skill — the prompt documented at 100/100 — has **zero**
countable constraints [src:CONSTRAINT-GRADES-2026-08-27].

> The surprise: that prompt is not weak. Two of its seven constraints name a
> command — `python3 -m unittest ...`, `bash tests/run_all.sh` — which is the
> strongest acceptance test there is, because something can run it and get a
> verdict. The tool built one loop ago reported them identically to "make it
> clean". Its output would have taught authors to prefer trivially countable
> constraints over runnable ones, which is the opposite of the point.

So constraints now sort into three grades: countable, runnable, and for a
reader to judge. Runnable commands are extracted and printed but never
executed — running a command lifted out of a prompt is not a linter's business.

The linter gained the same distinction from the other side.
`UNVERIFIABLE_ACCEPTANCE` fires on a stated acceptance test that names no
command, number, or exact comparison. It found two false positives on this
repository's own prompts within a minute of existing, both from the same cause:
the slot cue is loose enough to file "never promote it to verified" as an
acceptance test. The rule now requires the framing, not the vocabulary, and
both files returned to their previous scores.

Also fixed here: `check_output.py` recognised `## HEADING` and `**Bold.**`
slots but not `Constraints:` prose labels, so a prompt written that way fell
through to whole-prompt scanning and reported its own ROLE and TASK sentences
as unchecked constraints. Word-number limits ("at most two sentences") were
invisible to it as well.

## Still open

`U-6`, `U-7` and `U-8` in [unknowns.md](unknowns.md): what Saraev actually
teaches about prompting, what the owner meant by "the clear system", and
whether these seven slots are the right seven for the owner's real corpus —
which cannot be settled until that corpus, rather than this container's, is
indexed.
