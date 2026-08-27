# CLAUDE.md

Operating instructions for agents working in this repository.

## What this project is

`oodarag` - an OODA-driven, end-to-end RAG pipeline that runs on the Python
standard library alone. See `README.md` for the shape and `docs/ARCHITECTURE.md`
for the detail. `internal/PLAN.md` tracks what is built and what is next.

## Non-negotiables

1. **Zero required runtime dependencies.** The core must run on a bare Python
   3.11. numpy, hosted embedders and hosted LLMs are optional accelerators
   behind interfaces, never load-bearing. If you reach for a dependency, the
   answer is usually a smaller design. (ADR 0001)
2. **Provenance is load-bearing.** Every chunk carries the URI it came from, and
   citations are verified against retrieved chunks rather than generated. Cite
   what was actually read, pinned to an immutable identifier where one exists.
3. **Everything network-facing is bounded.** Requests, bytes, depth, wall-clock.
   Budgets bound *work*, not just accepted output. (LEARNINGS L5)
4. **Degrade, don't die.** Blocked egress, a missing key, a truncated API
   response reduce what the pipeline can do and say so. They never crash it, and
   they never silently shrink the corpus.
5. **Secrets are redacted at the connector boundary**, before text can reach an
   index file. An index is a file that gets copied around.

## How to work here

**Probe before you plan.** Run `ooda preflight` first. Reachability is an input
to the design, not something to discover at minute 40. Read
`internal/CAPABILITY-PROTOCOL.md` - it is the doctrine, not a suggestion, and
`internal/LEARNINGS.md` for what has already been paid for once.

**Test against evidence the code cannot fabricate.** Derived or observed
expectations, never values copied from a passing run. Assert that each failure
path actually fires. See `tests/test_crawler_blind.py` for the pattern.

**Run the suite before you commit.** `make test`. It is stdlib `unittest` and
needs no network for anything except the live cross-checks, which skip cleanly.

**Write the learning down.** A surprise that cost time goes in
`internal/LEARNINGS.md` with its evidence. A decision with a trade-off goes in
`docs/adr/`. Otherwise it gets paid for again next session.

## Commands

```bash
make test      # full suite
make demo      # ingest -> index -> query -> eval, end to end
make lint      # compile-check every module
PYTHONPATH=src python3 -m oodarag.cli preflight   # capability report
```

## Conventions

- Comments explain *why*, and are load-bearing where behaviour is non-obvious
  (a spec deviation, a failure mode being defended against). No comment that
  restates the line below it.
- Dataclasses for anything crossing a stage boundary.
- Every connector implements `oodarag.ingest.base.Connector` and does exactly
  one thing: yield `RawDocument`s and keep a cursor. It never chunks, embeds or
  indexes.
- Log one structured event per stage, with counts. A run should be reconstructible
  from its log.
