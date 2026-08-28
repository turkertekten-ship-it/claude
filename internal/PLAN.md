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
| External eval corpus | done | 266 PyPI pages with provenance, release dates and a manifest, rebuildable by `scripts/build_external_corpus.py`; 5 of 54 questions contaminated, 31 documents held out as 36 holdouts |
| Incremental deletion | done | Removals propagate to the delta, prune guarded at 25% of a source, refused entirely for a failed connector |
| CLI | done | `preflight, index, query, eval, loop, status, journal, demo` |
| CI | done | Three jobs: stdlib matrix, numpy path, retrieval regression gate; floors 0.85 primary, 0.79 external (rebased for a corpus 74% larger, then ratcheted for base_weight 5.0; L66, L67) |
| Non-negotiables | verified | All five attacked directly, not just asserted: zero-dependency walked module by module, provenance and redaction attacked with crafted inputs, degradation measured through partial and silent-empty source failures (L37-L39) |

**Current measurements** (offline embedder, deterministic).
385 tests passing - of which ten only run once the branch is pushed, because the
live GitHub cross-checks skip as a module unless the local HEAD is also the
remote head. The same tree reads 375 before a push and 385 after (L64), and CI,
which only runs pushed commits, always sees the larger number. Retrieval metrics are over graded cases only - abstention
cases have nothing to retrieve, and averaging their zeros in made adding a
negative case look like a retrieval regression.

| | primary (this repo) | external (266 PyPI pages) |
|---|---|---|
| golden cases | **19/20** | **44/54** |
| recall@8 | 0.8750 | 0.8953 |
| precision@8 | 0.2500 | 0.2413 |
| hit@8 | 0.9375 | 0.9302 |
| MRR | 0.6510 | 0.7198 |
| nDCG@8 | 0.6734 | 0.7505 |
| citation coverage | 1.00 | 1.00 |
| contamination | 4/20 questions, 10 documents (20 holdouts) | 5/54 questions, 31 documents (36 holdouts) |
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

What each retrieval arm is worth, on the external set (`scripts/ablation.py`,
266 documents, 3,166 chunks, `base_weight` 5.0, `rrf_k` 16, priors rescaled -
the whole table re-run, never a column):

| configuration | pass | recall@8 | prec@8 | MRR | nDCG@8 |
|---|---|---|---|---|---|
| hybrid | **44/54** | **0.8953** | 0.2413 | 0.7198 | 0.7505 |
| lexical only | **44/54** | 0.8837 | 0.2093 | **0.7677** | **0.7803** |
| dense only | 37/54 | 0.6860 | 0.1890 | 0.5853 | 0.6014 |
| no rerank | 38/54 | 0.7442 | 0.1570 | 0.5525 | 0.5899 |
| no mmr | 44/54 | 0.8953 | **0.2442** | 0.7173 | 0.7484 |

**The dense arm is on notice again.** On the gate corpus the lexical arm alone
now ties hybrid on pass rate and *beats* it on MRR and nDCG - one configuration
ago hybrid beat both arms on every metric. The primary corpus still says hybrid
(19/20 against 18/20 for either arm alone), which is the only reason the arm
survives this reading. ADR 0004 has now been overturned six times and this is
the second time the dense arm has been the thing overturned.

Reranking is worth six cases and MMR none on the external set, one on primary.
Both numbers have moved every time something upstream did; an ablation measures
a component *in a configuration*, never a component.

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

   **Measure it in hybrid, not alone, and expect the arm to outrun the system.**
   Widening the offline embedder from 192 to 3072 buckets buys the dense arm
   twelve cases and the pipeline none, because RRF publishes the average of the
   two arms' opinions rather than the better one (L65). A hosted embedder that
   disappoints in hybrid is evidence about the fusion before it is evidence
   about the model.

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

3. **Widen the corpus again.** Done twice more and it keeps paying: 33 to 91
   overturned three recorded conclusions (L29), 91 to 153 settled two more, and
   153 to 266 cost the same retriever **seven cases** - 48/54 to 41/54, recall
   0.9070 to 0.8140 - without a line of retrieval code changing (L66). Each
   widening has revealed that the previous corpus was flattering the retriever,
   which is the argument for doing it again rather than against. Of 128 packages
   requested this time, 113 were added, one was already held, and 14 were
   skipped with their reasons reported: five behind an anti-bot interstitial
   (a per-run cost rather than a blocker) and nine whose pages carry under 40
   words once the site template is removed. `ooda preflight` still has `web_pypi`
   **ok** while wikipedia, youtube, ibm.com and arxiv are refused CONNECT, so
   PyPI remains the only reachable source.

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

- **Retuning `candidate_k`, `mmr_lambda` or `coverage_weight`.** Swept over both
  corpora and confirmed on plateaus (L33), then re-swept after `base_weight` and
  `rrf_k` moved, because a constant confirmed under a different configuration is
  a stale constant (L68). `rrf_k` did move, 60 to 16. `candidate_k` stays at 40
  and **its recorded rationale is now false**: "a deeper pool is worse, because
  it gives the reranker more chances to promote the wrong document" held when
  the reranker decided almost the whole ordering. With the fused score carrying
  five times the weight, 30 through 80 are level and 80 is a single high sample
  between two lower ones - a peak to leave alone, not a plateau to move to.

- **Term co-occurrence as a gate signal.** Measured and refuted: the terms of the
  worst unanswerable case do co-occur, and three answerable cases have none
  (L32).

- **Query expansion.** Built and measured three times, off each time for a
  different reason - the current one being that it is *neutral* on the corpus
  that gates: identical pass rate and recall at every setting, and the one case
  it converts is on the 20-case smoke corpus at one of four settings (L67). The
  table is in `retrieve/expansion.py`.

- **Raising the embedder's `dim`, or moving the *arm* weights off 1.0** (the
  reranker's `base_weight` did move, to 5.0 - L67). Both
  swept over both corpora (`scripts/embedder_sweep.py`, L65). 768 is where
  hybrid pass rate is maximal; 1536 and up cost 1.5x to 4.6x query latency to
  lose a case. The weights are not a dial: past a ratio of
  `(rrf_k + candidate_k) / (rrf_k + 1)` - 1.64 at the old `rrf_k`, 3.29 now - the lighter arm is dropped
  entirely, and `lexical_weight=0.6` measures identical to `0.0`. The one
  tempting setting, 0.75, is a peak on the external corpus and costs a case on
  the primary one.

- **Retuning the chunk sizes.** Swept over both corpora at last, from 96 to 640
  tokens (`scripts/chunk_sweep.py`, L63). 320 sits on a plateau that runs to
  480 on the corpus that gates, the two corpora disagree in direction, and 96
  costs 72% more chunks to lose four cases. The sweep's finding was elsewhere:
  `hard_max_tokens` was not a ceiling (chunks ran to 2.1x it), the index could
  not tell that the chunker had changed, and the context header - never costed
  before - is 13.1% on top of the external corpus's body tokens and buys two
  cases and 4.7 recall points.
