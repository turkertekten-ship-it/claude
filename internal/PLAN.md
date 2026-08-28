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
| External eval corpus | done | 33 PyPI pages with provenance and a manifest; 1 of 36 questions contaminated, 2 documents quarantined |
| Incremental deletion | done | Removals propagate to the delta, prune guarded at 25% of a source, refused entirely for a failed connector |
| CLI | done | `preflight, index, query, eval, loop, status, journal, demo` |
| CI | done | Three jobs: stdlib matrix, numpy path, retrieval regression gate |

**Current measurements** (offline embedder, deterministic).
227 tests passing. Retrieval metrics are over graded cases only - abstention
cases have nothing to retrieve, and averaging their zeros in made adding a
negative case look like a retrieval regression.

| | primary (this repo) | external (33 PyPI pages) |
|---|---|---|
| golden cases | 17/20 | **33/36** |
| recall@8 | 0.8125 | 0.9821 |
| precision@8 | 0.2031 | 0.2812 |
| hit@8 | 0.8750 | 1.0000 |
| MRR | 0.5766 | 0.8793 |
| nDCG@8 | 0.6126 | 0.8833 |
| citation coverage | 1.00 | 1.00 |
| contamination | 4/20 questions, 26 documents held out | 1/36 questions, 2 documents |
| role | smoke test | **regression gate** |

What each retrieval arm is worth, on the external set (`scripts/ablation.py`):

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | 33/36 | 0.9821 | 0.2812 | 0.8793 | 0.8833 |
| lexical only | 32/36 | 0.9464 | 0.2679 | 0.8735 | 0.8707 |
| dense only | 33/36 | 0.9821 | 0.2991 | 0.8839 | 0.9008 |
| no rerank | 32/36 | 0.8929 | 0.1518 | 0.8333 | 0.8169 |
| no mmr | 33/36 | 0.9821 | 0.3125 | 0.8786 | 0.8880 |

Reranking is clearly load-bearing. **The case for the lexical arm is not**: on
this corpus dense-only matches hybrid on pass rate and recall and beats it on
precision, MRR and nDCG. That is a reversal - before the corpus was cleaned
(L26) hybrid led dense-only by 0.11 of recall - and ADR 0004 now records it as
deferred rather than settled, because 36 questions over 33 documents cannot
settle it either way.

Two metrics here are at or near their ceiling and can no longer show a
regression: hit@8 reads 1.0, and recall@8 reads 0.9821 with a median of 1.0.
That is the same trap as L23, and it is the strongest argument for item 2
below.

The gap between the columns is the self-reference problem, not a difference in
difficulty: the primary corpus contains the questions, so its best matches are
the documents written *about* the answer rather than the answer. All three of
its current failures are that artefact. See docs/EVALUATION.md.

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

1. **A hosted embedder behind the existing interface**, measured against the
   offline baseline on the same goldens. The interface and the baseline exist;
   only the comparison is missing, and it is currently **blocked**: no
   `ANTHROPIC_API_KEY` or `VOYAGE_API_KEY` is reachable from this environment.
   `ooda preflight` reports this, so the block is visible rather than inferred.
   This is the measurable argument for the one golden case that fails on
   purpose - the offline embedder cannot bridge "running forever" to a corpus
   that says "never terminates".

2. **A golden set drawn from a corpus this repository does not describe.** The
   external set is that, and it is why it is the regression gate. The primary
   set's quarantine is at 26 documents across 4 questions and rises with every
   commit (L22). Widening the external corpus is worth more than any scoring
   change, because it is the only lever on the failures that remain. This is
   actionable now: `ooda preflight` has `web_pypi` **ok** (HTTP 200) while
   wikipedia, youtube, ibm.com and arxiv are refused CONNECT by the proxy, so
   PyPI is the reachable source and the corpus can grow without a new egress
   path.

3. **Multi-hop retrieval**, once single-shot recall is well characterised.
   Adding a loop over a retriever with unknown recall multiplies every failure.
   Single-shot recall is now characterised on the external set (0.9286), so the
   precondition is close to met.

## Deliberately not next

- **Tuning the abstention gate.** Five candidate features were ranked against
  the one in use and none beat it: AUC 0.973 for `rerank_relevance` against
  0.77-0.80 for score-shape signals and 0.574 for match specificity
  (`scripts/gate_features.py`, L25). The two remaining gate failures are the
  tail of a feature that is already the best available, not a design flaw.
  Separating "the corpus discusses these words" from "the corpus answers this
  question" needs a judge that reads or a larger corpus - neither is a scoring
  change.

- **Raising `coverage_power`.** Measured on both corpora and left at 1.0. It
  trades primary recall for pass rate on one corpus, and it widens the gate's
  overlap monotonically (`scripts/gate_margin.py`). The table is in
  `retrieve/rerank.py`.

- **Query expansion.** Built, measured, and off by default because it made
  retrieval worse. The table is in `retrieve/expansion.py`.
