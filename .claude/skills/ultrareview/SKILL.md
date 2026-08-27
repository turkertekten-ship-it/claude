---
name: ultrareview
description: Run the final, evidence-first review of finished work. Measures the repository's claims against its own data with deterministic checkers, then fans out subagents for what measurement cannot reach, then adversarially verifies every finding before reporting. Use at the end of a body of work, when asked to ultrareview / do a final review / check nothing is fabricated, or before handing work over.
---

# ultrareview

A final review whose findings are reproducible by the person reading them.

The failure this exists to prevent is not a missed bug. It is a review that
*sounds* thorough. A confident summary of work nobody measured is worse than no
review, because it converts an open question into a settled one at no cost and
with no evidence. Everything below is arranged so that the review cannot make a
claim its reader cannot re-derive.

## The rule

> Every statement in the final report is a quoted claim, a file location, a
> command's real exit status, or a named absence. Anything else is deleted
> before the report is written.

Four consequences worth stating, because each is a place reviews go wrong:

1. **Measurement precedes reading.** Run the checkers before forming an opinion.
   Reading first produces a hypothesis, and a hypothesis turns the checkers into
   a search for confirmation.
2. **The reviewer is the likeliest fabricator in the room.** A reviewer under
   pressure to find things invents findings; a reviewer under pressure to sign
   off invents confidence. Both are fabrication. The defence is that every
   finding carries a locator and a second agent tries to knock it down.
3. **Absence of evidence must itself be evidenced.** "There is no test for the
   retry path" is a claim. It is only a fact once you say where you looked.
4. **A name is not its contents.** A file called `PLAN.md`, a branch called
   `fix-auth`, a function called `validate_input` — these tell you a label
   exists. Open it. Reviews that expand names into content are the single most
   common source of confident nonsense.

## Verdict vocabulary

Use these four words and no synonyms. They are the same four the checkers use,
so a report can mix machine and human findings without the reader having to
guess which is which.

| Verdict | Means | Not to be used for |
|---|---|---|
| `SUPPORTED` | Evidence found; it matches the claim. | A claim that merely seems plausible. |
| `UNSUPPORTED` | The search space was covered; nothing backs the claim. | A claim you did not have time to check. |
| `CONTRADICTED` | Evidence found; it says the opposite. | A claim you merely doubt. |
| `UNVERIFIABLE` | This review could not decide, and says so. | Anything you would rather round to pass. |

`UNVERIFIABLE` is mandatory and must appear in the report when it applies. A
review with no unverifiable items has usually not looked hard enough to find its
own limits. Never silently drop one — "not checked" reported as "checked and
fine" is the exact failure this skill exists to prevent.

## Phase 1 — Observe

Enumerate before interpreting. Produce an inventory, not a narrative.

```bash
git -C <repo> status --short && git -C <repo> log --oneline -15
find <repo> -path '*/.git' -prune -o -type f -print | sort
```

Read every file the work touched, end to end. Not a grep, not the first fifty
lines. You may not write a sentence about what the code does until you have read
the code that does it.

Record what you find as a flat list of observations with locators. Resist
grouping them into themes at this stage — a theme is already an interpretation,
and the wrong one costs you the whole review.

## Phase 2 — Orient: run the data checkers

This is the layer that does not depend on anyone's judgement, and it runs first.

```bash
cd <repo> && PYTHONPATH=. python3 -m tools.ultrareview . \
    --json /tmp/ultrareview.json --markdown /tmp/ultrareview.md
```

Ten checkers, each answering one question against the repository's own data:

| Checker | Question it answers |
|---|---|
| `paths` | Does every path the prose references exist? |
| `commands` | Do the commands the docs tell a reader to run actually work? |
| `symbols` | Do the advertised entry points and dotted names resolve in the source? |
| `deps` | Is the dependency story true, measured from the real import graph? |
| `numbers` | Is every confident figure in prose traceable to a literal or a datum? |
| `citations` | Does every `[src:ID]` resolve to a recorded source? |
| `coverage` | Do the capabilities the prose advertises exist in the code? |
| `consistency` | Where a fact is stated twice, do the two statements agree? |
| `tests_evidence` | Does the advertised suite exist, and does it pass right now? |
| `links` | Are the published URLs well-formed and pointing at this project? |

Read the JSON, not just the summary. Then, before going further:

* **The checkers' output is ground truth for the rest of the review.** You may
  add findings they could not reach. You may not overturn a measurement because
  a file reads as though it ought to work. If you believe a checker is wrong,
  reproduce its command yourself and fix the checker — an argument with a
  measurement is settled by measuring again, not by prose.
* **Note what was skipped.** `report.skipped` lists checkers that raised. A
  review missing a third of its checks looks complete and is not. Say so in the
  report.
* **Do not re-report machine findings as your own.** They belong in the report
  attributed to the checker that found them.

## Phase 3 — Decide: fan out on what measurement cannot reach

The checkers catch broken references, false capability claims and dead commands.
They cannot read for correctness, for a race, for an interface that is honest
about its types but wrong about its semantics. That is the subagent layer.

Give each agent one dimension, the inventory from Phase 1, and the checker
report so it does not re-litigate what is already measured. Require a locator on
every finding.

```javascript
export const meta = {
  name: 'ultrareview-judgement',
  description: 'Review dimensions no checker can reach, then refute each finding',
  phases: [{ title: 'Review' }, { title: 'Verify' }],
}

const DIMENSIONS = [
  { key: 'correctness',  ask: 'Logic that is wrong for a reachable input. Give the input.' },
  { key: 'claims',       ask: 'Prose asserting behaviour the code does not have. Quote both.' },
  { key: 'evidence',     ask: 'Numbers, benchmarks, or capabilities stated with no traceable source.' },
  { key: 'boundaries',   ask: 'Error paths, budgets and limits: what happens at and past each edge.' },
  { key: 'tests',        ask: 'What the suite asserts vs what it appears to assert. Name untested branches.' },
  { key: 'consistency',  ask: 'Two parts of the work that cannot both be true.' },
]

const FINDINGS = {
  type: 'object', required: ['findings'],
  properties: { findings: { type: 'array', items: {
    type: 'object',
    required: ['file', 'line', 'claim', 'verdict', 'evidence', 'failure_scenario'],
    properties: {
      file: { type: 'string' }, line: { type: 'integer' },
      claim: { type: 'string', description: 'verbatim quote from the file' },
      verdict: { enum: ['SUPPORTED','UNSUPPORTED','CONTRADICTED','UNVERIFIABLE'] },
      evidence: { type: 'string', description: 'file:line or command+exit code' },
      failure_scenario: { type: 'string', description: 'concrete input -> wrong output' },
      severity: { enum: ['error','warn','info'] },
    } } } },
}

phase('Review')
const reviewed = await pipeline(
  DIMENSIONS,
  d => agent(`Review <scope> for: ${d.ask}
Already measured by the deterministic checkers — do NOT re-report these:
<paste the checker findings>
Quote every claim verbatim with file:line. If you cannot point at it, do not report it.`,
    { label: `review:${d.key}`, phase: 'Review', schema: FINDINGS }),
  r => parallel((r?.findings ?? []).map(f => () =>
    agent(`Try to REFUTE this finding. Read the code yourself; do not take it on trust.
${JSON.stringify(f)}
Default to refuted=true when uncertain. A finding that survives must survive on evidence.`,
      { label: `verify:${f.file}:${f.line}`, phase: 'Verify',
        schema: { type: 'object', required: ['refuted', 'why'],
          properties: { refuted: { type: 'boolean' }, why: { type: 'string' } } } })
      .then(v => ({ ...f, refuted: v?.refuted !== false, why: v?.why ?? 'verifier returned nothing' }))))
)

const survived = reviewed.flat().filter(Boolean).filter(f => !f.refuted)
log(`${reviewed.flat().length} raised, ${survived.length} survived refutation`)
return { survived }
```

Scale the fan-out to the work: a handful of dimensions for a small change, the
full set plus a second refutation round for a body of work being handed over.

## Phase 4 — Act: verify, then report

**Refute before you report.** Every surviving finding gets a second agent whose
job is to knock it down, defaulting to refuted when uncertain. A finding that
cannot survive a hostile read was never a finding. This is not ceremony: it is
the step that removes the plausible-but-wrong items, which are the ones that
cost a reader the most time.

**Then check your own report against the same rule.** Before sending, walk every
sentence and ask: is this a quote, a locator, a measured exit code, or a named
absence? If it is none of those, cut it or go and measure it. Summary sentences
smuggle in fabrication more often than finding bodies do, because nobody expects
a summary to need a citation.

**Report format.** Lead with what is broken now, with locators. Then unsupported
claims. Then unverifiable items, explicitly labelled. Then what was checked and
found sound — briefly, because a reader needs to know the search space to
interpret the silence. State the checkers that were skipped and why.

State plainly whether the work is finished. "Finished" means: the deterministic
checkers exit zero, the test suite passes on the current tree with its real
output shown, every surviving finding is either fixed or reported as a known
limitation, and every unverifiable item is named. Anything short of that is
reported as short of that.

## Fabrication tells

Things that are almost always unbacked. Check each against the tree, never
against memory:

* A path, module or command named in prose but never opened during the work.
* A number with a unit — throughput, size, cost, percentage — with no literal
  behind it.
* A capability described in a feature table where the corresponding code is a
  docstring.
* A test count, coverage figure or benchmark quoted without the command that
  produced it.
* "Should work", "now handles", "is now safe" — a state claim with no run behind it.
* A summary from another agent, repeated as fact. Second-hand stays second-hand:
  mark it as reported, name the reporter, and verify before relying on it.
* A citation whose id resolves to nothing.
* A version, date or author copied from a template.

## What this skill will not do

It will not sign off work it could not measure. If the suite cannot run, the
network is blocked, or a claim depends on a system this session cannot reach,
that is an `UNVERIFIABLE` line in the report — not a smaller claim quietly
substituted for the one that was asked about.
