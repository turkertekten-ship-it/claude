---
provenance: enforced
---

# Learnings

Surprises that cost time, with the evidence. `internal/CAPABILITY-PROTOCOL.md`
routes here; the file did not exist until something was actually learned worth
putting in it.

> The bar for an entry: it changed how the work was done, and the next session
> would otherwise pay for it again. A restatement of the doctrine is not a
> learning.

## L-1 — A session's goal string is mutable, and a replacement is feedback

**Cost:** an entire preference analysis built on what turned out to be a
snapshot. Re-reading the same field 26 minutes later changed two confidence
grades.

**What to do differently:** sample the field repeatedly, not once. Sampling once
gives opening lines; sampling repeatedly catches corrections, which are worth
more per word than any opening line.

## Observed — L-1

- Four of fourteen sessions carried a different `goal.condition` at 15:30Z than at 15:04Z; re-issuing `/goal` replaces the string in place and only the latest survives. [src:GOALS-REISSUED-2026-08-27]
- One replacement was a correction rather than a new task, and is the only text in the corpus reacting to delivered work instead of requesting it. [src:GOALS-REISSUED-2026-08-27]

---

## L-2 — Two defects were invisible to reading and obvious to running

**Cost:** both would have shipped. Neither was a coding error — one came from a
specification written in this repository, and the other from taking a data
format at face value.

**What to do differently:** run the thing on real data and read what it printed,
including the log lines nobody asked for. Both defects announced themselves in a
counter — `lexical=0` in one case, a role label in the other — that a passing
test suite would never have surfaced. This is what "outcome-based blind test"
buys, concretely.

## Observed — L-2

- The BM25 IDF was clamped at zero, so on a small corpus every term zeroed and the lexical arm returned nothing while the dense arm kept answering. The eval still produced numbers. [src:BM25-SILENT-ZERO-2026-08-27]
- Claude Code writes tool results as `type: "user"` records, so command output was indexed as the owner speaking; two of the first three search hits were Bash output. [src:ROLE-ATTRIBUTION-BUG-2026-08-27]

---

## L-3 — A frozen interface contract makes parallel agents safe to merge

**Cost:** none, which is the point. This is recorded because the cheap version
fails badly.

**What to do differently:** write the contract before fanning out, and spend real
effort on it. Agents working from the same prose brief drift at the seams;
agents working from named signatures with defaults do not. The contract is also
what makes a mismatch a *fixable* disagreement rather than an argument about
whose module is right — the contract wins.

## Observed — L-3

- Ten agents implemented separate modules against `internal/CONTRACTS.md` with no communication between them, and the chain ran end to end on the first integration attempt. [src:PIPELINE-E2E-2026-08-27]

---

## L-4 — At this concurrency, remote state you read is already stale

**Cost:** a merge planned against two branch heads, both of which had moved by
the time the merge ran.

**What to do differently:** fetch immediately before merging, not when planning
it, and always diff the file lists first. Also: read the sibling's work before
assuming it competes with yours. It turned out to be complementary — they
hardened the layer this branch inherited while this branch built the layer above
it — and treating it as a conflict would have wasted both.

## Observed — L-4

- The fleet grew from 4 sessions to 14 within roughly one hour. [src:SESSIONS-2026-08-27] [src:FLEET-13-2026-08-27]
- Between 15:04Z and 15:25Z the `claude` remote went from 2 branches to 11, and both branches this one was built from advanced underneath it. [src:SIBLING-MERGES-2026-08-27T1525Z]
- Diffing the two file lists before merging predicted the conflicting paths exactly, both times it was run. [src:SUBSTRATE-MERGED-2026-08-27]

---

## L-5 — A careless range replacement silently deletes prose

**Cost:** three sourced observations from another session were dropped and only
noticed later, during a merge, by grepping for their source ids.

**What to do differently:** a `partition`/slice edit that spans from one heading
to another takes everything in between, including sections added since the code
was written. Anchor edits on the exact text being replaced, and after any
structural edit to a provenance file, check that every source id in the ledger
is still cited somewhere. The verifier catches an unresolvable tag; it does not
catch a claim that quietly vanished — that asymmetry is worth remembering, since
it means the guard is one-directional.

## Observed — L-5

- A range replacement spanning two headings removed the section between them, dropping three sourced lines from another session's observations. [src:SECTION-DROP-2026-08-27]
- `verify_provenance` did not flag it: it checks that cited ids resolve, not that declared ids are still cited. The loss surfaced only by grepping for the two ids during a later merge. [src:SECTION-DROP-2026-08-27]

---

## L-6 — Fan-out is capped by CPUs, not by ambition

**Cost:** two workflows launched concurrently competed for the same two slots
and slowed each other down.

**What to do differently:** check `nproc` before deciding how wide to go. Beyond
the cap, more agents means more queueing, not more throughput — and two
workflows running at once is strictly worse than the same agents in one, because
neither can see the other's queue.

## Observed — L-6

- The container reports 4 CPUs, which caps workflow fan-out at 2 concurrent subagents. [src:ENV-CONCURRENCY-2026-08-27]
