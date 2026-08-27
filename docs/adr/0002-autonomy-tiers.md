# 0002 - Autonomy is a property of the edit, not of the finding

**Status:** Accepted
**Date:** 2026-08-27

## Context

The `reflect` loop runs unattended and writes to the user's files. That is the
feature; it is also the entire risk. Some gate has to decide what it may do on
its own at 22:30 and what has to wait for a person.

The obvious gate is importance. Findings already carry a severity, so the loop
could simply act on the ones that matter most and queue the rest. That is
exactly backwards, and it took building it to see why.

Consider two findings the loop actually produces on a real repository:

- **Trivial:** the README links to `internal/PLAN.md`, which was never written.
  The fix is to create a file nothing currently occupies.
- **Critical:** a tracked file contains something credential-shaped. The fix is
  to remove it, rotate it, and rewrite history.

Severity says act on the second and defer the first. But the first cannot
destroy information - there is no file there to damage - while the second is
the single most dangerous edit in the system: an automated rewrite of a file
containing a live secret is how that secret gets committed a second time, in a
diff, at night, with nobody watching.

Importance says how much the user should *care*. It says nothing about what
happens if the loop is *wrong*.

## Decision

**Autonomy is decided by the risk of the edit, independently of the severity of
the finding.** Every `Proposal` carries a `risk` tier that describes what its
`EditOp`s could destroy:

| Tier | Means | Handling |
|---|---|---|
| `safe` | Cannot destroy information: creating a file that does not exist, adding a delimited section the loop itself owns | Applied without a human |
| `review` | Edits the user's own prose or configuration - README, Makefile, memory file | Queued, never applied unattended |
| `manual` | Source-code semantics, or anything touching a credential | Reported only; no edit is ever generated |

Severity and risk are consumed by different lists. Severity orders what the
report shows first. Risk decides which list a proposal lands in at all. A
trivial `safe` fix and a critical `manual` finding do not compete, because they
are never ranked against each other.

Source files are never machine-edited, at any tier. The loop improves the
material *around* the code - the docs, the conventions, the entry points - and
reports on the code itself.

## Consequences

**What this buys.** The blast radius of a wrong rule is bounded by construction
rather than by the rule author's judgement. A new detector can be written
carelessly and the worst it can do unattended is create a file nobody asked for,
which `ooda reflect revert` removes. Reviewing a new rule means checking one
field.

Because the tiers are about destruction rather than importance, they compose
with the other guarantees without special cases: dry-run by default, backup
before every write, all-or-nothing per proposal, idempotent operations, nothing
written outside the workspace root, and a refusal to touch a dirty working tree.

**What this costs.** The genuinely valuable fixes are mostly `review`, so the
loop's unattended output is modest - stubs and delimited sections - and the
queue is where the real value accumulates. That is the correct trade and it is
also the reason the queue has to be pleasant to work through: `ooda reflect
queue`, then `accept` or `dismiss` on an eight-character id. A system whose good
suggestions all need a human is only as good as the ten seconds that takes.

**What would change this.** Per-rule promotion. A rule with a long journal of
accepted, never-reverted proposals has earned more than a rule shipped
yesterday, and `decide.priors` already computes exactly that number. Promotion
is deliberately not implemented yet: it should be based on evidence from real
use, and there is none.

## Alternatives considered

**Gate on severity, with a confidence threshold.** The pairing above is the
counterexample. It also makes every new rule a security review, because a rule
author choosing a severity is implicitly choosing an autonomy level.

**Require confirmation for everything.** Honest, and it makes the loop a
notification system. The `safe` tier exists so that the boring, unambiguous
maintenance actually gets done - that being the work people never get to.

**Apply everything, rely on git to undo it.** Assumes a clean repository, a
user who reads diffs, and that the workspace is version-controlled at all. The
first is why a dirty tree blocks a run; the last is why backups are kept
independently of git.
