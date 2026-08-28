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
| External eval corpus | done | 153 PyPI pages with provenance, release dates and a manifest, rebuildable by `scripts/build_external_corpus.py`; 5 of 54 questions contaminated, 22 documents held out as 28 holdouts |
| Incremental deletion | done | Removals propagate to the delta, prune guarded at 25% of a source, refused entirely for a failed connector |
| CLI | done | `preflight, index, query, eval, loop, status, journal, demo` |
| CI | done | Three jobs: stdlib matrix, numpy path, retrieval regression gate; floors ratcheted to 0.85 primary / 0.86 external |
| Non-negotiables | verified | All five attacked directly, not just asserted: zero-dependency walked module by module, provenance and redaction attacked with crafted inputs, degradation measured through partial and silent-empty source failures (L37-L39) |

**Current measurements** (offline embedder, deterministic).
384 tests passing - of which ten only run once the branch is pushed, because the
live GitHub cross-checks skip as a module unless the local HEAD is also the
remote head. The same tree reads 374 before a push and 384 after (L64), and CI,
which only runs pushed commits, always sees the larger number. Retrieval metrics are over graded cases only - abstention
cases have nothing to retrieve, and averaging their zeros in made adding a
negative case look like a retrieval regression.

| | primary (this repo) | external (153 PyPI pages) |
|---|---|---|
| golden cases | **18/20** | **48/54** |
| recall@8 | 0.7812 | 0.9070 |
| precision@8 | 0.2031 | 0.2471 |
| hit@8 | 0.8750 | 0.9302 |
| MRR | 0.5729 | 0.7089 |
| nDCG@8 | 0.6063 | 0.7460 |
| citation coverage | 1.00 | 1.00 |
| contamination | 4/20 questions, 10 documents (20 holdouts) | 5/54 questions, 22 documents (28 holdouts) |
| role | smoke test | **regression gate** |

Both columns are freshly indexed; the primary one is the CI configuration,
`--exclude-source chat`. **Read the primary column as a smoke test and nothing
else.** Over one session, with the retrieval code untouched, it read:

| after | pass | recall@8 |
|---|---|---|
| the cycle's first commit-ready tree | 18/20 | 0.7812 |
| adding the comments that explain the fix | 17/20 | 0.7812 |
| adding the LEARNINGS entry about those comments | 18/20 | 0.7500 |
| retiring the answer expectation and rewriting that entry | **18/20** | **0.7812** |

The last row is this table's own measurement, and writing it down changes the
corpus again. The fixed point is not reachable on a corpus that indexes the
notes about its own evaluation; the table above is a snapshot, and the external
column is the one that means anything.

The case that moved asks how the pipeline notices vectors from an older
embedding space, and required the answer to name the mechanism. Comments that
paraphrased it took the top slots and dropped the word; a learnings entry naming
it repeatedly put the word back and displaced expected sources elsewhere, which
is why the pass rate recovered while recall fell. Then the discrimination guard
failed the suite: the word had reached 17 of 83 documents. The expectation is
now removed and the case graded on retrieval alone, with the evidence in its
`notes` and in L63 - tightening it, the way `"sha"` became `"commit sha"`, was
measured and produces a case that cannot pass instead.

Without `--exclude-source chat` it is the *session transcript* that supplies the
answer. Nothing about the retriever changed across those three rows. A gate
whose value depends on what the last session wrote in markdown cannot detect a
regression in retrieval, which is what the external column is for.

What each retrieval arm is worth, on the external set (`scripts/ablation.py`):

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | 47/54 | 0.8721 | 0.2238 | 0.7304 | 0.7487 |
| lexical only | 47/54 | 0.8605 | 0.2151 | 0.7157 | 0.7313 |
| dense only | 44/54 | 0.8140 | 0.2122 | 0.6957 | 0.7163 |
| no rerank | 38/54 | 0.7209 | 0.1076 | 0.6298 | 0.6390 |
| no mmr | 46/54 | 0.8488 | 0.2384 | 0.7295 | 0.7430 |

Reranking is the most load-bearing component by a distance, and hybrid beats
either arm alone on every metric. That answers the question ADR 0004 had
deferred: at 33 documents dense-only matched hybrid, and the deferral rather
than the removal of an arm was the right call (L29).

On pass rate the two arms are level at 153 documents, while dense alone is
three cases behind; MMR, neutral at 91 documents, is now worth a case.
The pass column is sensitive to the abstention gate and the metric columns are
not, so a change to the floor moves one and leaves the other untouched.

The contamination row above was wrong in the same way, for a different reason:
it read "26 documents held out" from a report line that summed *per-question*
holdouts and called them documents. A document contaminating two questions is
held out twice and is one document. Both corpora hold out 14 distinct
documents; the harness now prints both numbers with their units.

**The ablation table was previously wrong in its pass column only** - every metric
matched to four decimal places while every count was four cases stale, because
later work moved the abstention floor and added surface answerability, neither
of which touches a retrieval metric. A partly refreshed table is worse than a
stale one: the accurate columns vouch for the inaccurate one. Re-run it with
`PYTHONPATH=src python3 scripts/ablation.py --corpus external` and replace the
whole table, never a column.

Nothing here is saturated any more. recall@8 was 0.9821 with a median of 1.0 on
the 33-document corpus; it now reads 0.9186 with a minimum of 0.0.

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

2. **The abstention gate**, still, though less of it. The unstemmed surface
   check is in and worth +3 cases at no measured cost (L30); the document
   coverage idea was measured and is dead (AUC 0.609, barely above a coin
   flip). Three of the seven remaining failures are still the gate:

   - "Which tool publishes a package to a private PyPI mirror?" (0.658) and
     "Which package renders Jinja templates to PDF?" (0.602) are near-misses
     where every query term is in the corpus and only their *combination* is
     absent. No single-chunk or single-document coverage measure separates
     these, because the terms genuinely are there.
   - "What keeps two processes from writing the same file at once?" (0.768) is a
     question made entirely of ordinary words, which is the case
     `gate_features.py` showed match specificity cannot detect (AUC 0.555).

   **Term co-occurrence was tried and is dead.** The idea was that a question
   whose informative terms never appear together is unattested. Measured
   directly against the index: `pdf` and `jinja` *do* co-occur in one chunk, so
   the signal misses the very case it was designed for - while the answerable
   `bcrypt`, `orjson` and `watchdog` questions have zero co-occurrence among
   their top-idf terms and would all be wrongly refused. A well-phrased question
   does not reuse the document's words, which is the same semantic gap that
   causes the remaining retrieval failures.

   The limit is now measured rather than asserted. The worst unanswerable case
   scores 0.595 with answerability 1.0 and surface 1.0 - every word genuinely in
   the corpus - while the answerable cases that fail score 0.147 and 0.148. That
   is a 4x overlap, not a margin, and both directions are "the corpus contains
   these words". Separating them is a judgement about meaning, which is item 1,
   and item 1 is blocked on a key.

3. **Widen the corpus again.** 33 to 91 documents overturned three recorded
   conclusions and de-saturated every metric (L29); 91 to 153 settled two more
   and levelled the retrieval arms on pass rate. There is no reason to think
   153 is where that stops. `scripts/build_external_corpus.py --list` does it,
   and `ooda preflight` has `web_pypi` **ok** while wikipedia, youtube, ibm.com
   and arxiv are refused CONNECT, so PyPI remains the reachable source. Two
   pages of 63 were refused by an anti-bot interstitial, which is a per-run
   cost rather than a blocker.

4. **Multi-hop retrieval**, once single-shot recall is well characterised.
   Adding a loop over a retriever with unknown recall multiplies every failure.
   Single-shot recall on the external set is 0.9070.

5. **Give `char_start` a reader.** Fixed and pinned in L64 - code chunks went
   from 55% to 100% located, with chunk ids and lengths byte-identical - but the
   field is still written and never consumed. It is now correct enough to build
   on: a citation that quotes the exact span, or a snippet that shows a match in
   its document rather than the whole chunk. Until something reads it, the
   property test is the only thing keeping it honest.

## Deliberately not next

- **Raising `coverage_power`.** Measured on three versions of the external
  corpus and left at 1.0 each time, for a different reason each time - which is
  itself the finding. It currently buys a case and costs ordering quality on
  both corpora. The table is in `retrieve/rerank.py`.

- **Retuning `candidate_k`, `mmr_lambda`, `rrf_k` or `coverage_weight`.** All
  four swept over both corpora and confirmed on plateaus at their current values
  (L33, `scripts/constant_sweep.py`). `candidate_k` is the one worth knowing
  about: a deeper candidate pool is *worse*, not better, because it gives the
  reranker more chances to promote the wrong document.

- **Term co-occurrence as a gate signal.** Measured and refuted: the terms of the
  worst unanswerable case do co-occur, and three answerable cases have none
  (L32).

- **Query expansion.** Built, measured, and off by default because it made
  retrieval worse. The table is in `retrieve/expansion.py`.

- **Retuning the chunk sizes.** Swept over both corpora at last, from 96 to 640
  tokens (`scripts/chunk_sweep.py`, L63). 320 sits on a plateau that runs to
  480 on the corpus that gates, the two corpora disagree in direction, and 96
  costs 72% more chunks to lose four cases. The sweep's finding was elsewhere:
  `hard_max_tokens` was not a ceiling (chunks ran to 2.1x it), the index could
  not tell that the chunker had changed, and the context header - never costed
  before - is 13.1% on top of the external corpus's body tokens and buys two
  cases and 4.7 recall points.
