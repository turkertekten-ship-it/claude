# Approaches tried and rejected

What was attempted, what happened, and why it was not kept — so that the next
session does not rebuild it. A rule says what to do; this says what was already
tried and did not work, which a rule cannot express.

> The shape is borrowed from the `learnings/_TEMPLATE.md` in a repository that
> documents the DOE framework: "captures approaches that were tested but not
> selected, and why. Prevents re-discovering dead ends."
> [src:DOE-TEMPLATES-2026-08-28]

Each entry names the problem, the approach, the result, and the evidence. An
entry is not a prohibition — an approach can be right later, under different
constraints. It is a record of what it cost last time.

---

## Keeping a written claim from going stale

**Current approach:** register the number with the command that produced it in
`provenance/measurements.yaml`, and re-run it in the suite
(`tools/verify_measurements.py`). Chosen because it compares exactly and cannot
misread a sentence.

### Rejected: a prose guard for undated claims about mutable state

**Tried:** 2026-08-27, loop seventeen. **Result:** failed, backed out.

An `UNDATED_STATE` rule for `verify_provenance.py`: an assertion about state
that changes must carry a date. It took four rounds of narrowing —
conditionals ("if the archive is empty"), generic examples ("a repository with
no commits"), descriptions of possible output, past-completed framings ("both
repositories started empty") — and still misjudged four of nine cases,
including reading "the index is **no** longer empty" as an emptiness claim.

**Why it failed:** it tried to recognise a semantic category rather than a
closed set of idioms. Detecting an assertion in English needs tense, reference
and conditionals to be read correctly, which a pattern cannot do. Rule 9 states
the general form. The `FALSE_MEMORY` guard is the contrast that works: thirteen
fixed phrases, no false positive across the repository.

---

## Finding which lessons never reached a document

**Current approach:** read the loop log. There is no mechanical substitute.

### Rejected: keyword-matching the loop log against the documents

**Tried:** 2026-08-28, loop twenty-three. **Result:** unreliable, discarded.

A probe searched the documents for phrases summarising each named surprise, to
find lessons that had not been routed anywhere readable. It reported two
lessons as missing; reading showed one was a false positive, because the probe
looked for the summariser's phrasing rather than the rule's.

**Why it failed:** the same defect as the entry above, committed inside a check
written to audit rule coverage. A loop log is prose, and prose is read.

---

## How to add an entry

When an approach is abandoned, record it here before the reasoning is lost:
the problem it addressed, what was tried, when, the result, and the specific
reason it failed. The reason is the part that transfers — "it did not work" is
not an entry.
