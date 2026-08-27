# 0001 - The core runs on the standard library alone

**Status:** Accepted
**Date:** 2026-08-27

## Context

`oodarag` has two halves that pull in opposite directions.

The retrieval pipeline is the kind of code that normally arrives with a
dependency tree: a tokenizer, a vector store, an embedding client, a YAML
parser, a HTTP library. Each is individually reasonable and collectively they
are the reason a RAG project that worked in March does not import in September.

The nightly `reflect` loop makes that worse, because of *when* it runs. It runs
unattended at 22:30 on a laptop, from a systemd timer or a launchd agent, in
whatever environment that machine happens to have. A job like that fails in a
particular way: not loudly, but by printing an `ImportError` into a log nobody
reads, for weeks, until someone notices the reports stopped. A dependency that
is merely *usually* present is worse than no feature at all, because it degrades
into silence rather than into an error anyone sees.

## Decision

**The core of both halves runs on the Python standard library, with no required
third-party packages.** `dependencies = []` in `pyproject.toml` is a load-bearing
line, not an accident of a young project.

Accelerators and hosted models are allowed, but only ever *behind an interface
that already has a working stdlib implementation*:

- `numpy` (`[fast]`) vectorises scoring for large corpora. Without it, scoring
  is a slower loop that returns the same ranking.
- `requests` (`[providers]`) is offered for people who prefer it. Without it,
  `urllib` does the same job.
- Hosted embedding and generation providers plug in behind the same call sites
  as the local, deterministic ones.

The rule for any future dependency: if its absence changes an *answer* rather
than a *speed*, it does not go in the core.

## Consequences

**What this buys.**

- The pipeline runs in CI, in an air-gapped container, on a fresh laptop, and
  inside a scheduled job, with `PYTHONPATH=src` and nothing else. No install
  step means no install step to break at 22:30.
- Tests run on `unittest` with no plugins, so `make test` cannot be broken by a
  resolver.
- The nightly loop degrades along one axis only - "this source was unavailable
  tonight" - rather than failing to start.

**What this costs, honestly.**

- Text handling is more code than it would be with a library, and token counts
  are estimates. `util.text.estimate_tokens` is deliberately approximate; every
  budget in the pipeline is a soft budget with headroom precisely so that an
  estimate is sufficient.
- The embedder is a hashing-trick model rather than a learned one. It is
  deterministic and cheap; it is not competitive with a real embedding model,
  which is why the interface exists for swapping one in.
- Some things stay a deliberate subset. The `.gitignore` matcher in
  `reflect.sources.workspace` handles the common patterns rather than the full
  specification, and says so where it is defined.

**What would reverse this.** A required dependency becomes acceptable if the
project ever ships a binary artifact where the environment is pinned by us
rather than discovered at runtime. Until then, the constraint stays.

## Alternatives considered

**Vendor the dependencies into the tree.** Solves the availability problem and
creates a worse one: vendored code is code we now maintain and must patch for
CVEs, without the review that the core gets.

**Depend on a small, stable set and pin exactly.** Pinning makes today
reproducible and makes next year's security update somebody's afternoon. It
also does nothing for the case that actually motivated this decision - the
scheduled job running in an environment we did not create.

**Make the loop a shell script to dodge the packaging question.** Moves the
problem rather than solving it: the loop needs to parse three history formats
and several transcript shapes, and a shell script that does that is a
dependency on `jq`, `awk` and the local `sed` dialect wearing a disguise.
