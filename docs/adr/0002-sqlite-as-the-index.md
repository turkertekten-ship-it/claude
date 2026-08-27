# ADR 0002 - SQLite is the whole index

**Status:** accepted

## Context

Retrieval needs a document store, a chunk store, a vector index and a lexical
index. The usual answer is three systems: Postgres, a vector database, and
Elasticsearch or equivalent.

## Decision

One SQLite file holds all four: `documents`, `chunks`, `embeddings` (float32
blobs), and an FTS5 virtual table for BM25. Vector search is exhaustive over a
flat in-memory index built from the same file.

## Consequences

**Why it fits.** The index is one file - copyable, attachable to a CI artifact,
deletable. FTS5 ships with the standard library's SQLite, so real BM25 costs no
dependency and no second system to keep in sync with the first. Updates are
transactional, so a crash mid-index leaves the previous consistent state rather
than a half-migrated one that returns wrong results silently.

**Why flat vector search.** Exhaustive search is exact, has no build step and no
parameters to tune wrong, and stays sub-millisecond at the tens of thousands of
chunks a documentation corpus produces. An ANN index trades recall for latency
that is not yet a problem, and silently losing recall is the failure this
pipeline exists to prevent. Revisit at ~10^6 chunks, with the eval harness
measuring what the change costs.

**Where it will break.** Concurrent writers (SQLite serialises them; WAL helps
readers, not writers), corpora too large to hold vectors in memory, and
distributed deployment. All three are real limits, and none of them apply to the
corpus sizes this targets.

**One migration hazard, already hit.** `CREATE VIRTUAL TABLE IF NOT EXISTS` will
not notice a changed tokenizer, so an index built under the old one keeps it
silently and half the corpus stems while the other half does not. The store
carries a schema version and rebuilds the FTS table from `chunks` when it bumps.
