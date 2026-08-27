# oodarag

An OODA-driven, end-to-end RAG pipeline that runs on the Python standard library alone.

```
Observe  ->  Orient   ->  Decide   ->  Act
ingest       normalize    policy       reindex / backfill
             chunk        engine       / alert / answer
             embed
             index
```

## Why this exists

Most RAG code is a demo: load a folder, call an embedding API, cosine-similarity
top-5, stuff it in a prompt. That works until it meets a real corpus, at which
point the failure modes are always the same - the index is stale, the chunks lost
their context, the retriever returns the site footer, and nobody can tell you
whether last week's change made retrieval better or worse.

`oodarag` is built around those failure modes rather than around the happy path:

| Failure mode | What this does about it |
|---|---|
| Index goes stale | Content-hash incremental ingest + an OODA loop that decides when to re-fetch |
| Chunks lose context | Contextual headers embedded with every chunk |
| Retriever returns boilerplate | Structural + link-density boilerplate removal in the scraper |
| Same page indexed 5 times | Canonical-URL and content-hash dedupe |
| Semantic search misses exact terms | Hybrid dense + BM25 retrieval fused with RRF |
| "Is retrieval any good?" | An eval harness with recall@k, MRR, nDCG and citation coverage |
| Secrets leak into the index | Redaction at the connector boundary, before anything is written |
| A crawl runs forever | Budgets on pages, fetches, bytes, depth and wall-clock |

## Status

Under active construction. See `internal/PLAN.md` for what is built and what is next.

## Quick start

```bash
make test          # stdlib unittest, no dependencies required
make demo          # end-to-end: ingest -> index -> query -> eval
```

## Design principles

1. **Zero required dependencies.** The whole pipeline runs on the stdlib, so it
   works in CI, in an air-gapped container, and on a laptop. Accelerators
   (numpy) and hosted models (Voyage, Anthropic) plug in behind interfaces.
2. **Provenance is load-bearing.** Every chunk carries the URI and commit sha it
   came from. Citations are verified against retrieved chunks, not generated.
3. **Everything is bounded.** Every network stage has a budget on requests,
   bytes and time.
4. **Degrade, don't die.** Blocked egress, a missing API key or a truncated API
   response reduce what the pipeline can do; they never make it crash.
5. **Measure, don't assert.** Retrieval quality is a number in an eval report.

## Session tooling

Beyond the pipeline, this repository carries tooling for the Claude Code
sessions that work on it.

**Task division.** Every submitted prompt is divided into an explicit numbered
task list before any work begins, enforced by a `UserPromptSubmit` hook rather
than by remembering to do it:

```bash
python3 tools/install_task_division.py          # every project on this machine
python3 tools/install_task_division.py --check  # 0 installed, 1 not installed
```

See `docs/task-division.md` for the mechanism, the scope it covers, and how to
switch it off.
