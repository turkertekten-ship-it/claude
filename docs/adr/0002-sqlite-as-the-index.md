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
parameters to tune wrong. An ANN index trades recall for latency, and silently
losing recall is the failure this pipeline exists to prevent.

**The latency claim here was an estimate and it was wrong** - "sub-millisecond
at the tens of thousands of chunks a documentation corpus produces", revisit at
~10^6. Measured on the pure-Python path with `scripts/latency_scaling.py`
(L82), the dense scan is **linear at ~0.027 ms per chunk** while every other
stage is flat, because every other stage is bounded by `candidate_k` or `top_k`
rather than by the corpus:

| documents | chunks | total | dense | lexical | rerank | mmr |
|---|---|---|---|---|---|---|
| 90 | 733 | 45.9 | 18.7 | 0.9 | 14.9 | 9.8 |
| 175 | 1,983 | 87.3 | 52.5 | 1.8 | 17.6 | 11.3 |
| 260 | 3,225 | 122.5 | 88.6 | 2.5 | 16.6 | 11.1 |
| 349 | 4,220 | 150.1 | 114.9 | 3.2 | 17.3 | 10.9 |

So the real shape is `total ≈ 30 ms + 0.027 ms × chunks`, and the triggers
follow from a latency budget rather than from a round number:

| budget | chunks | documents at this corpus's 12 chunks each |
|---|---|---|
| 250 ms | ~8,000 | ~700 |
| 1 s | ~36,000 | ~3,000 |
| 10 s | ~370,000 | ~31,000 |

At 10^6 chunks a query takes **27 seconds**, so the original revisit trigger was
two orders of magnitude past the point of usefulness. **Revisit at ~35,000
chunks** on this path, with the eval harness measuring what an ANN index costs
in recall. numpy - the documented optional accelerator, absent from the
environment these numbers came from - moves the constant and not the shape.

**Where it will break.** Concurrent writers (SQLite serialises them; WAL helps
readers, not writers), corpora too large to hold vectors in memory, and
distributed deployment. All three are real limits, and none of them apply to the
corpus sizes this targets.

**One migration hazard, already hit.** `CREATE VIRTUAL TABLE IF NOT EXISTS` will
not notice a changed tokenizer, so an index built under the old one keeps it
silently and half the corpus stems while the other half does not. The store
carries a schema version and rebuilds the FTS table from `chunks` when it bumps.
