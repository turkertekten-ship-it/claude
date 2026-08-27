# oodarag build plan

What is built, what "built" was allowed to mean, and what an honest reader
should still distrust. The interface every stage was written against is
`internal/CONTRACTS.md`, which is frozen.

Status was determined on 2026-08-27 by reading the `src/` tree and running
`make demo`, `make eval`, `make loop` and `make test` (77 tests, 1 skipped,
green). It is not a plan for what someone intends to write.

**How to read the status column.**

| | |
|---|---|
| **Done** | The module exists, `make demo` exercises it end to end, and the "done means" column is true. |
| **Next** | Partly there. Something specific and named is missing. |
| **Later** | Deliberately not started. The seam it would plug into exists. |

Done is about the code path running, not about it being well tested. Test
coverage is tracked separately below because conflating the two is how a
green plan ends up describing an untested pipeline.

## Stages

| Stage | Module | Status | "Done" means |
|---|---|---|---|
| **ingest** | `ingest/base.py`, `files.py`, `web.py`, `github.py` | Done | A connector yields `RawDocument`s, persists a cursor, and reports `new/changed/unchanged/failed` in an `IngestDelta`. Incrementality is content-hash based. One bad document is counted, never raised. |
| **normalize** | `normalize.py` | Done | Cleans text, redacts secrets a second time, drops thin documents, dedupes on `content_hash` and on `metadata["canonical"]`, carries `authority` through. Counts every drop in a `NormalizeReport`. |
| **chunk** | `chunk.py` | Done | Splits on markdown structure, packs to `target_tokens` with overlap, never splits a fenced code block, and stamps every chunk with a `context_header` and real `char_start`/`char_end` offsets into `doc.text`. |
| **embed** | `embed/base.py`, `embed/hashing.py` | Done | `HashingEmbedder` produces byte-identical L2-normalized vectors across processes, with no model download. `EmbeddingCache` is keyed by content hash, so re-indexing an unchanged corpus embeds nothing. |
| **index** | `index/store.py`, `bm25.py`, `dense.py` | Done | One sqlite file in WAL mode holds documents, chunks and vectors behind a `schema_version`. BM25 and dense both build from the store and are refilled in place, never rebound. |
| **retrieve** | `retrieve.py` | Done | Both arms over-fetch `candidates`, RRF fuses by rank, and every `ScoredChunk` carries `bm25_rank`, `dense_rank`, `bm25`, `dense`, `rrf` and a populated `document`. See `docs/adr/0002-hybrid-retrieval.md`. |
| **rerank** | `rerank.py` | Done | MMR diversity plus an authority nudge, writing `components["mmr"]`, `["authority"]`, `["final"]`. The reranker is fed a pool deeper than `k` so diversity can actually change the result. |
| **generate** | `generate.py` | Done | Extractive answers built only from sentences present verbatim in retrieved chunks; every citation re-verified by substring containment against the chunk body; abstains below `min_confidence` rather than guessing. |
| **evaluate** | `evals/harness.py` | Done | `recall@k`, `MRR`, `nDCG@k`, citation coverage, abstention rate and false-abstention rate, computed from first principles, over `evals/goldens.jsonl`. Malformed golden lines are skipped and counted. |
| **loop** | `ooda/loop.py` | Done | Observe / orient / decide / act are separate methods; `decide` is a pure function of the orientation; `act` is the only phase that mutates; `--dry-run` runs everything but `act`. |
| **cli** | `cli.py` | Done | `demo`, `index`, `query`, `eval`, `loop`, `stats`, one per Makefile target. `main(argv)` returns an exit code on every path and never lets a traceback reach the terminal. `demo` runs offline from `evals/corpus/`. |

Two things in the tree are adjacent to the pipeline rather than stages of it:
`scrape/` (HTML extraction, robots, the bounded crawler) sits under the web
connector, and `access/probe.py` is a capability probe, not a retrieval stage.
Neither is on the `RawDocument -> Answer` path.

## What is not started, and why that is fine

| | Status | Note |
|---|---|---|
| Hosted-model generation | Later | The seam is written and unused: `generate.build_prompt` produces the prompt a hosted model would need. Wiring it is a class, not a refactor. |
| ANN index | Later | `DenseIndex` is exhaustive. Replacing it means one class with `add` and `search`. The corpus size where this stops being optional is in `docs/adr/0001-zero-dependency-core.md`. |
| Cross-encoder rerank | Later | `Reranker` already owns the final ordering, so a cross-encoder slots in behind the same call. Needs a trained model, which ADR 0001 puts out of scope for the core. |
| Deletion propagation | **Next** | See known gaps 3. |
| Source-filtered query | **Next** | See known gaps 4. |

## Verification: what actually exercises each stage

| Stage | Unit tests | Exercised end to end by |
|---|---|---|
| ingest (github, crawler) | `test_github_offline.py` (13), `test_github_blind.py` (10), `test_crawler_blind.py` (17), `test_robots.py` (14), `test_html_extract.py` (15), `test_http_client.py` (14) | `make demo`, `make loop` |
| ingest (files) | none | `make demo`, `make index` |
| chunk | incidental, via `test_bm25_small_corpus.py` | `make demo` |
| index / bm25 | `test_bm25_small_corpus.py` (5) | `make demo`, `make eval` |
| normalize, embed, store, retrieve, rerank, generate, evaluate, loop, cli | **none** | `make demo`, `make eval`, `make loop` |

77 tests pass. Read the right-hand column before taking comfort from that
number: the majority of them cover the network edge — HTTP, robots, HTML
extraction, GitHub — because that is where this pipeline talks to something it
does not control. The retrieval core downstream of ingestion has one regression
test and an end-to-end demo.

## Known gaps

Things an honest reader should still distrust, worst first.

**1. The eval numbers are not evidence of retrieval quality.** `make eval`
reports recall@8 = 1.000, MRR = 1.000, nDCG@8 = 0.885 over 18 goldens. The
corpus is nine hand-written documents and the goldens were written against
those documents, so the questions use the corpus's own vocabulary — close to the
best case for lexical matching. Measured on the same index, BM25 alone also
scores MRR 1.000. A 1.000 on this set means the harness works, not that
retrieval does. Treat it as a regression baseline and nothing more; the number
that would mean something comes from a corpus nobody wrote the questions
against.

**2. Nine of the eleven stages have no unit tests.** Normalize, embed, store,
retrieve, rerank, generate, evaluate, loop and cli are covered only by the
end-to-end demo, which asserts nothing — it prints. A bug that degrades ranking
without breaking it produces a demo that looks identical. The one regression
test that exists (`test_bm25_small_corpus.py`) exists because exactly that
happened: a clamped IDF silenced the whole lexical arm on a small corpus, the
dense arm kept answering, and every number stayed plausible.

**3. Deletions never propagate.** `Connector.run` records vanished documents in
`cursor["removed_last_run"]` and `Store.delete_document` is implemented, but
nothing reads the first or calls the second. A document deleted at its source
stays indexed, retrievable and citable indefinitely. This is a deliberate
staging decision — a transient empty response from a source must never be able
to wipe an index — but the second half, an explicit downstream action that acts
on the recorded list, is not written. Until it is, the index is append-and-update
only.

**4. `source_filter` is implemented but unreachable.** `HybridRetriever.retrieve`
accepts it; `Pipeline.ask` does not pass it and the CLI has no flag for it. "Ask
this question against the docs only" is not currently possible through any
supported entry point.

**5. The embedder has no learned semantics, and the eval cannot see it.** The
hashing embedder matches tokens and character n-grams. Genuine paraphrase across
disjoint vocabulary is its ceiling (ADR 0001), and because the goldens share
vocabulary with the corpus, the golden set does not measure the thing most
likely to be weak in production. The paraphrase probes recorded in ADR 0002 are
a sharper instrument and are not automated.

**6. Token counts are estimates and have not been calibrated.**
`util.text.estimate_tokens` is `max(words, chars // 4)`. It has not been checked
against any real tokenizer here. Every budget built on it — chunk sizing, the
generation context budget — is soft. Anyone attaching a hosted model with a hard
context limit must re-check it against that model's tokenizer, especially for
code and non-Latin scripts.

**7. The loop's `act` phase is narrower than it looks.** `reingest`, `backfill`
and `reindex` really do mutate. `retune` deliberately only proposes — a loop that
edits retrieval knobs invalidates the eval numbers used to judge the edit — and
`alert` writes a log line with no delivery channel behind it. A cycle report
showing an alert means nobody was told.

**8. Only the files connector has been run against real data offline.** The web
and GitHub connectors are covered by blind and offline tests against fixtures
and a local HTTP server. They have not been pointed at a large live source in
this repository, so their budget and rate-limit behaviour under real conditions
is untested rather than verified.

**9. `.oodarag/` is created relative to the working directory.** Every entry
point defaults to `--root .oodarag`, so running from a different directory
silently starts a second, empty index rather than failing. `ooda stats` and
`ooda query` refuse to create one and say where they looked, which turns the
silent case into a diagnosis, but the default is still cwd-relative.
