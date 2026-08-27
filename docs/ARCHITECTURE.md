# Architecture

```
                    ┌─────────── OODA loop ───────────┐
                    │  observe → orient → decide → act │
                    └───────┬──────────────────┬───────┘
                            │                  │
   ┌────────────┐    ┌──────▼──────┐    ┌──────▼──────┐    ┌──────────────┐
   │ connectors │───▶│  normalize  │───▶│    chunk    │───▶│    embed     │
   │            │    │  + redact   │    │ + context   │    │  (pluggable) │
   │ filesystem │    └─────────────┘    │   header    │    └──────┬───────┘
   │ github     │                       └─────────────┘           │
   │ web/scrape │                                                 ▼
   │ chat       │                                        ┌─────────────────┐
   │ youtube    │                                        │  SQLite index   │
   └────────────┘                                        │ docs · chunks   │
                                                         │ vectors · FTS5  │
                                                         └────────┬────────┘
                                                                  │
   ┌──────────────┐   ┌──────────┐   ┌─────────┐   ┌─────┐   ┌────▼─────┐
   │   answer     │◀──│ citation │◀──│ rerank  │◀──│ RRF │◀──│  dense   │
   │ + provenance │   │ contract │   │  + MMR  │   │     │◀──│ + lexical│
   └──────────────┘   └──────────┘   └─────────┘   └─────┘   └──────────┘
                                                                  │
                                                         ┌────────▼────────┐
                                                         │  eval harness   │
                                                         │ + contamination │
                                                         └─────────────────┘
```

## Module map

| Module | Responsibility |
|---|---|
| `access/probe.py` | What this environment can reach, as data the loop consumes |
| `ingest/base.py` | Connector contract: yield documents, keep a cursor, nothing else |
| `ingest/{filesystem,github,web,chat,youtube}.py` | One source each |
| `scrape/{html,robots,crawler}.py` | Boilerplate removal, RFC 9309 robots, bounded BFS crawl |
| `pipeline.py` | normalize → chunk → embed → index, idempotently |
| `chunking.py` | Structure-aware splitting with contextual headers |
| `embedding/` | Pluggable embedders; deterministic offline default |
| `store/` | One SQLite file: documents, chunks, float32 vectors, FTS5 |
| `retrieve/` | Hybrid search, RRF, MMR, transparent reranking |
| `generate/` | Answer assembly with an enforced citation contract |
| `eval/` | Retrieval metrics, golden harness, contamination detection |
| `ooda/` | The control loop and its policy rules |

## The five invariants

Everything else is negotiable; these are not.

1. **The core has no required dependencies.** Every stage runs on the Python
   standard library. Accelerators (numpy) and hosted models (Claude, Voyage) sit
   behind interfaces. The configuration CI exercises is the configuration that
   ships. (ADR 0001)

2. **Provenance survives every stage.** A `RawDocument` becomes a `Document`
   becomes a `Chunk` becomes a `ScoredChunk` becomes a `Citation`, and each
   carries the URI it came from, pinned to an immutable identifier where one
   exists. Citations are verified against retrieved chunks, never generated.

3. **Analysis is consistent across stages.** Any two stages comparing the same
   text tokenize, stem and weight it identically. Index and reranker disagreeing
   made retrieval worse than no stemming at all. (ADR 0005, LEARNINGS L11)

4. **Work is bounded, not just output.** Requests, bytes, depth, wall clock.
   Bounding only accepted results lets work run away invisibly. (LEARNINGS L5)

5. **Failure is explicit.** A blocked source, a truncated API response, an
   unembedded chunk, a contaminated eval - each is a recorded finding, not a
   log line. Empty results are always explained: blocked, filtered, deduped, or
   genuinely absent.

## Data flow in one paragraph

A connector yields `RawDocument`s, having redacted credentials and skipped
anything it has already seen (content-hash incremental). `normalize` canonicalises
the text and redacts again - defence in depth, because connectors are easy to add
and easy to forget. `chunk_document` splits on structure and prepends a
deterministic context header naming the document, heading path, symbol, speaker
or timestamp; the header is embedded and indexed with the body, which is what
keeps a chunk interpretable in isolation. Vectors go into SQLite as float32 blobs
tagged with the embedder's fingerprint; text goes into an FTS5 table with Porter
stemming. At query time both arms are pre-filtered by the same predicate, fused
by reciprocal rank, reranked on IDF-weighted features, and diversified by MMR.
The generator receives numbered evidence, and whatever it writes is verified
against that evidence before it is returned.

## Where the OODA loop sits

The loop is not a scheduler. It observes what changed and what is reachable,
orients raw counts into a situation (coverage, staleness, source health, quality),
applies policy rules that state a condition and an action, acts within a budget,
and journals every phase. The journal is the point: a cron job that re-indexes
nightly is silent about whether it needed to and whether it worked.

See `docs/OODA.md` for the phases and `docs/EVALUATION.md` for how quality is
measured - including why an eval report without a contamination status is a
number with no provenance.
