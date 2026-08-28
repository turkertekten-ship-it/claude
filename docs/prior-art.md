---
provenance: enforced
---

# Prior art on provenance checking

Whether `tools/verify_provenance.py` reinvents something already established.
Worth knowing before extending it.

> Everything in the first section is **second-hand** — search-engine summaries
> of papers on arxiv.org, which is egress-blocked from this container. None of
> these papers was opened. Read them before relying on any characterisation
> here.

## Observed — what a search surfaced

- Four related systems appeared: `sciwrite-lint`, a local linter checking that references exist and support the claims made; `SemanticCite`, which classifies citations as supported, partially supported, unsupported, or uncertain; `PaperTrail`, a claim-evidence interface decomposing answers and sources into discrete claims; and `ProvenanceGuard`, described as a fail-closed gate for unsupported claims in MCP-based agents. [src:PROVENANCE-PRIOR-ART-2026-08-27]
- None of the underlying papers was readable from here, because arxiv.org is blocked at the proxy. [src:EGRESS-MAP-2026-08-27]

## Reading

Not an observation — an interpretation, kept out of the section above.

The approach here is not novel, and that is reassuring rather than
disappointing: an independent line of work has converged on the same shape,
including the fail-closed stance that a claim without support should block
rather than warn.

The difference is one of depth. This repository's verifier is **syntactic**: it
checks that a tag exists, resolves, and sits on every claim line in an enforced
section. It cannot tell whether the cited evidence actually supports the
sentence attached to it. That semantic step is exactly what the systems above
automate, and what the `fact-checker` subagent does here by judgement instead —
and it earns its place: it caught two claims in this repository whose tags
resolved correctly but supported slightly less than the claim made.

So the split is deliberate. The verifier is fast, deterministic, and runs on
every edit. The semantic pass is slower, fallible, and runs before publishing.
Neither replaces the other.

## What was built from this

The next step named here — checking that a claim's cited evidence contains the
numbers the claim asserts — is now implemented as `UNSUPPORTED_QUANTITY` in the
verifier. Building it taught more than reading about it would have.

### Observed — what developing the check found

- The first implementation reported 20 violations against this repository, all traceable to the check comparing against an entry's evidence *path* instead of the capture file it names; resolving the file dropped it to 17. [src:QUANTITY-CHECK-2026-08-27]
- A regex using lookarounds silently refused to match digits following a word character, missing the hour in ISO stamps like `T14:07`; bare digit runs dropped it to 3. [src:QUANTITY-CHECK-2026-08-27]
- All 3 survivors were spelled-out counts whose evidence enumerated the items without ever writing a figure; dropping spelled-out expansion left 0. [src:QUANTITY-CHECK-2026-08-27]

### Reading

Every one of those 20 was a defect in the checker, not in the documents. That is
the useful lesson: a claim-verification tool's first output is mostly a report
on its own assumptions, and shipping it without reading the findings one by one
would have meant either 20 pointless rewrites or a disabled check.

The scope is now deliberately narrow. It compares **digits to digits** and does
not expand spelled-out counts, because "the three later commits" is supported by
evidence naming three commits without ever writing "3" — flagging that would
produce findings about prose style, not about truth. Counting enumerated items
is semantic work, and semantic work stays with the `fact-checker` subagent.

A guard that is quiet enough for a hit to mean something is worth more than one
that catches everything and is therefore ignored.
