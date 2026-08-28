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

## Seventh loop — closing the circuit

Observe asked a question with a one-line answer: does anything connect the
checker to the learned-rules file? Nothing did. `grep` found no reference in
either direction.

> The surprise is what that means about the previous two loops. The pattern
> this repository documents as Saraev's self-annealing loop ends with a step
> that updates the instruction file "to warn future instances"
> [src:SARAEV-REPOS-2026-08-27]. Both halves had been built — a checker that
> catches a violation, a tool that records a rule — and the step between them
> was left to a human retyping. A loop documented in `docs/prompting.md` as
> built in had a gap in the middle of it, and nothing noticed because each
> half worked.

`check_output.py --suggest-rule` emits, per failure, the exact `learn_rule.py`
command that records it, with the measurement in the `because` and nothing
else — a reason that speculated about *why* an answer went wrong would be
invention appended to the file every future prompt loads.

The falsifier was end-to-end rather than notional: the emitted command was run,
the rule landed, and running it again was refused rather than duplicated. Rule
4 in this repository's Learned rules arrived that way, from the trial's own
86-word overrun.

## Eighth loop — two things built from one source, fighting

Observe asked what the mechanism automated one loop ago actually costs. Four
rules, 121 words, 6% of `CLAUDE.md`. At the measured mean rule length, fifty
rules would be 45% of the file and two hundred would be 76%
[src:RULES-BUDGET-2026-08-27].

> The surprise: two things built in this session from the same source pull
> against each other. The **iceberg technique** says do not stuff the context —
> keep the rules and the task above the waterline and let tools fetch the rest.
> **Self-annealing** appends a rule to the always-loaded file on every failure,
> and the seventh loop automated the appending. One of them is a context
> budget; the other is an unbounded context producer, and neither knew about
> the other.

`learn_rule.py review` gives the section a budget and runs inside
`tests/run_all.sh`, so the pressure is mechanical rather than remembered. It
also flags rules that contradict each other — the same category, opposite mode,
overlapping action — and rules that restate one already there, which the exact
duplicate check could never catch.

It deletes nothing. A rule exists because something went wrong once, and
pruning it silently loses that; retiring one is an edit somebody makes on
purpose, which is why the tool reports and stops.

Both thresholds were set from measurement rather than taste. The two collisions
this repository has actually produced sit at exactly 0.50 word overlap, and the
four genuine rules produce no finding there [src:RULES-BUDGET-2026-08-27]. A
threshold chosen above the real cases would have been a check that never caught
anything.

## Ninth loop — the copy that actually runs

The owner asked for this to work in every terminal. What runs in a terminal is
the installed copy under `~/.claude`, and Observe found that nothing kept it in
step with the repository: `grep` found no staleness check, and the two were
identical only because this session re-ran the installer by hand after each of
eight loops.

> The surprise is that this is the repository's own thesis, one level up. Its
> opening argument is that a rule living only in prose gets skipped under
> pressure. The currency of the installed copy was living in a habit, and a
> user has no such habit. A stale `/prompt` in another terminal would have been
> running rules from before four of these loops — including before the linter
> bug fixes — while looking exactly the same.

`--check` compares every installed file against what the installer would write
now, applying the same path rewrite so the markdown copies are not reported as
false differences. It is in `tests/run_all.sh`, and a machine with nothing
installed exits 0 rather than failing a fresh clone.

Writing it produced two defects worth naming, both caught by running the
falsifiers rather than by reading the code. The check ran after the `mkdir`
loop, so a read-only check created directories on a machine that had nothing
installed. And moving it earlier put it above its own helper functions, so the
markdown comparison silently did nothing while the summary still reported "in
sync" — a check that quietly checked less than it claimed, which is worse than
no check at all.

## Tenth loop — what the installer did to a machine that was not this one

Observe started with the delivery path nobody had exercised: a fresh clone of
the pushed branch, running `tests/run_all.sh` cold. It passed all ten checks,
which was the expected and uninteresting answer.

The interesting question came out of it. Every install this session had run
into a container whose `~/.claude` held nothing of the owner's. What happens on
a machine where it does?

> The surprise, and the worst defect found in ten loops: the installer
> **silently overwrote** a command the owner had written, and `--uninstall`
> then **deleted it permanently**, because the path was on its list and the
> list never recorded who wrote what. Neither could be seen from inside a
> container where that directory was empty. The standing instruction this
> session runs under says to look at a target before overwriting it, and the
> tool that installs the doctrine did not.

The installer now keeps a manifest of what it wrote. It refuses a target it did
not install and that does not already match what it would write, naming the
file; `--force` copies the owner's version aside first. `--uninstall` removes
only files in the manifest whose content is still what was installed — a file
edited since is left with a note, because the edit is the owner's work.

Two smaller things came out of the falsifiers: a refusal was exiting 2 ("could
not run") when it is a finding, and the first version of the edit-preserving
uninstall checked only manifest membership, so a file we installed and the
owner then rewrote was still deleted.

## Eleventh loop — the fix that was only as complete as the search

The tenth loop's real lesson was not about installers: it was that this
container hides a class of defect that only exists on the owner's machine.
Observe went looking for others of that class along the two paths that touch
their own data.

The first came back clean, which is worth recording: `git check-ignore`
resolves `archive/index.db` to the `archive/` rule, so the chat index the
documented command builds cannot be committed, and `*.db` covers it again.

The second did not.

> The surprise is what it says about the previous loop rather than about the
> code. The installer's four `~/.local/bin` shims were still written with a
> bare redirect. The fix for "never overwrite a file you did not write" had
> been applied to the markdown copies and the tool copies — the two places
> being looked at — and not to the third, in the same commit, alongside a
> seventeen-case test suite asserting the fix was complete. Not one of those
> cases installed over a foreign *binary*. Thoroughness about the parts you
> considered reads exactly like thoroughness.

The shims are guarded now, and the more useful change is the test that made
that mechanical: it enumerates every target, and asserts its own list is the
same length as the installer's `TARGETS` array. Adding a target without adding
a case now fails the suite — verified by adding one and watching it fail.

## Twelfth loop — the lists that only agreed because someone was looking

Loop eleven's fix was a test that asserts its own list matches the installer's.
Observe generalised that: where else must a list match another list, with
nothing checking?

Five pairs, all correct at the time of looking, none guarded — every test file
against `run_all.sh`, every tool against the README and the layout, every
profile against the two documents naming them, every rule the checker can emit
against the templates that record it, every rule against both framework
mappings. Correct by attention, three loops running.

`tools/check_consistency.py` holds all five, and runs in the suite.

> The surprise came twice, from the guard catching itself. Its first run failed
> on `check_consistency.py` not being in the README — a tool I had written
> ninety seconds earlier. Its second failure was `test_check_consistency.py`
> not being in `run_all.sh`: the test written *for* the guard, caught by the
> guard, for exactly the defect the guard exists to prevent. A test nobody runs
> reports nothing and looks like coverage.

One of the five was worthless as first written. "Every profile is named in the
documentation" was a substring search, and `task`, `chat` and `contract` occur
in any prose about prompts — an invariant that could not fail, which is the
defect `UNVERIFIABLE_ACCEPTANCE` exists to catch, committed inside the tool that
enforces it. It now requires the name as code or as an alternative in a usage
line, and the test proves bare prose no longer satisfies it.

## Thirteenth loop — running the machine on the owner's own prompt

Three loops had gone on the system's own hygiene. Observe turned back to the
only real user prompt in reach — the goal string that started this — and asked
what the finished machine says about it.

Two answers, and the second is the useful one.

**It scores 38/100, exactly as it did at loop zero**, after roughly fifteen rule
changes. Every one of those changes was a narrowing that removed a false
positive, and none of them weakened the verdict on a genuinely under-specified
prompt. That is the failure mode of iterative rule-tuning — drifting permissive
one exemption at a time — not happening, and it is worth having measured rather
than assumed.

**Then the forged version was written, and the linter rejected it.** Two of the
three findings were bugs in the tool, both exposed only by writing a prompt in
the format the system itself recommends:

- `Extend the system`, `Correct the rule`, `Name the artifact` were not
  recognised as tasks. The verb list had been assembled from the kinds of
  request that had happened to come up.
- `UNVERIFIABLE_ACCEPTANCE` fired on a well-formed acceptance test. It looked
  for the handle on the line that framed the test, and in the slot format this
  system recommends the framing word is the heading while the command proving
  it is the line below. The rule was punishing its own house style.

> The surprise: twelve loops of guarding produced a system that failed on the
> first real prompt written the way it tells people to write. Fixture prompts
> and subagent briefs had exercised everything except the shape the
> documentation actually recommends.

`prompts/forged/standing-prompt-system.md` is the result, at 100/100 against 38
for the raw ask. Its slots are filled from what was built and not corrected over
thirteen loops rather than from a reconstruction of the owner's intent, and its
escape clause says exactly that.

## Fourteenth loop — the tool rewarding its own ceremony

Loop thirteen ended on the observation that the system had never been tested in
the shape it recommends. `compile` produces exactly that shape, so Observe ran
the round trip over every fixture: compile a prompt, empty the markers, score
both.

Two fixtures scored **higher** compiled than raw. `worked_raw.md` went from 38
to 62 with not one word of content added.

> The surprise: the presence checks were satisfied by the heading. `compile`
> writes `## ACCEPTANCE TEST` over a gap, and the linter read the label as the
> thing. So the tool paid 24 points for structure alone — in a repository whose
> own skill says that padding a prompt with ceremonial sections makes it worse,
> and whose linter has a rule against unfalsifiable acceptance tests. It was
> rewarding the exact behaviour it argues against, and no fixture caught it
> because no fixture had ever been compiled and re-scored.

Slot presence is now judged on content, with the label stripped before the cue
runs. An empty skeleton now scores *below* the raw ask, which is right: it says
the same thing and has unfilled structure to fill. The property is a test —
compiling must never raise a score, checked over every fixture.

Fixing it required the slot-label parser in two tools, so it moved to
`tools/_slots.py` on the `_phrases.py` precedent. That immediately broke every
terminal but this one: the installer did not ship the new module, and the
repository kept working only because the file is on disk here. The installer's
tool list was a sixth list nobody checked, and `check_consistency.py` now
derives that invariant from the source — every private module an installed tool
imports must itself be shipped.

Three guards caught this loop's own mistakes in sequence: the installer's
self-verification refused to install a linter that crashed on import, the
target-count assertion from loop eleven noticed a target added without a test,
and the consistency check named the missing module.

## Fifteenth loop — three defects behind one property

Loop fourteen found its bug by testing a property rather than an example, so
Observe asked what other properties should hold. The sharpest: **filling a gap
must never lower the score**, or the tool punishes doing what it just asked for.

Monotonicity held. What it exposed was two steps where filling a slot changed
nothing, and behind those, three defects.

**A statement of fact satisfied the acceptance slot.** The cue matched any
mention of passing, verifying or green, so "the suite currently passes" — a
fact about today, sitting in a CONTEXT section — was read as the test on the
answer. `NO_ACCEPTANCE` therefore never fired on any prompt with decent
context. That is the damaging direction of error: a false *present* lets a
prompt through, where a false absent merely nags.

**Cues broke across line wraps.** Eighty-six of these alternatives are phrases,
every prompt in this repository is wrapped at eighty columns, and
`accepted only when` straddling a break was simply not seen. A slot could be
reported absent because of where the text happened to wrap.

**`^` was never a line anchor.** The cues compiled without `re.MULTILINE`, so
"an imperative at the start of a line" only ever matched the start of the whole
prompt. It had been working by accident, through the alternative that fires
after a full stop.

> The surprise: the second and third had been true for the entire session. Every
> score in every loop was computed with slot detection that depended on where
> lines happened to break. The numbers moved only slightly when it was fixed,
> which is luck rather than vindication.

Fixing the first two collided with loop fourteen's fix: a heading supplies no
slot, but the format this system recommends puts the framing in the heading
(`## ACCEPTANCE TEST`) and the substance on the line below, so together they
rejected a well-formed acceptance test. A labelled section now supplies its slot
when it has content under it — neither half alone.

Four properties are now tests: filling a slot never lowers the score, a fact is
not a test, a line break does not hide a slot, and structure alone earns
nothing.

## Still open

`U-6`, `U-7` and `U-8` in [unknowns.md](unknowns.md): what Saraev actually
teaches about prompting, what the owner meant by "the clear system", and
whether these seven slots are the right seven for the owner's real corpus —
which cannot be settled until that corpus, rather than this container's, is
indexed.
