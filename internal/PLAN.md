# Status

## Built and verified

| Area | State | Evidence |
|---|---|---|
| HTTP layer | done | 18 tests over real sockets: retries, `Retry-After`, ETag/304, size caps, rate limiting, circuit breaker |
| Web scraper | done | Boilerplate removal, RFC 9309 robots, bounded BFS crawl; verified against a live server's own request log |
| GitHub builder | done | Cross-checked byte-for-byte against `git cat-file` on a local clone; hermetic tests for pagination, truncation, rate limits, blob fallback |
| Filesystem / chat / YouTube connectors | done | Chat reads Claude Code JSONL; YouTube handles live captions, committed captions, and metadata-only |
| Chunking | done | Structure-aware with contextual headers; metadata describes the whole span when pieces merge |
| Embedding | done | Deterministic offline default; pluggable providers behind one interface |
| Store | done | One SQLite file: documents, chunks, float32 vectors, FTS5 with Porter stemming, IDF table, journal |
| Retrieval | done | Hybrid dense + lexical, RRF, IDF-weighted rerank, MMR |
| Generation | done | Citation contract verified against retrieved chunks; extractive default, Claude optional |
| Eval | done | recall/precision/MRR/nDCG, citation coverage, abstention, contamination detection and quarantine |
| OODA loop | done | Five journalled phases, auditable policy rules, action budget |
| External eval corpus | done | 14 PyPI pages with provenance; contamination reports clean, so no quarantine is needed |
| Incremental deletion | done | Removals propagate to the delta, prune guarded at 25% of a source, refused entirely for a failed connector |
| CLI | done | `preflight, index, query, eval, loop, status, journal, demo` |
| CI | done | Three jobs: stdlib matrix, numpy path, retrieval regression gate |

**Current measurements** (offline embedder, deterministic):
197 tests passing.
*Primary corpus* (this repository): 18/20 golden cases, 4 questions
contaminated and quarantined.
*External corpus* (14 PyPI pages, no self-reference): **20/20**, recall@8 0.80,
nDCG@8 0.78, MRR 0.78, citation coverage 1.0, contamination clean.

## Known limitations, deliberately not fixed

- **One golden case fails on purpose** (`known-limitation` tag). The offline
  hashing embedder cannot bridge "running forever" to a corpus that says "never
  terminates". Tuning thresholds until it passes would be overfitting the eval.
  It is the measurable argument for a pluggable neural embedder.
- **Quarantine is growing.** As the repository documents its own evaluation, more
  documents legitimately discuss the golden questions, so more get quarantined.
  Past a point this measures a smaller and smaller corpus. The fix is a golden
  set drawn from a corpus the repository does not describe.
- **Flat vector search** is exact and simple, and will need revisiting somewhere
  around 10^6 chunks. ADR 0002 states the trade and the trigger.
- **No cross-encoder reranker.** The heuristic reranker is transparent and cheap;
  a cross-encoder would rank better and cost latency. The harness is the place to
  decide that, and it has not been run.

## Next, in order of value

2. **A hosted embedder behind the existing interface**, measured against the
   offline baseline on the same goldens. The interface and the baseline exist;
   only the comparison is missing.
4. **Query expansion** for the semantic-gap case, as the cheaper alternative to a
   neural embedder.
5. **Multi-hop retrieval**, once single-shot recall is well characterised.
   Adding a loop over a retriever with unknown recall multiplies every failure.
