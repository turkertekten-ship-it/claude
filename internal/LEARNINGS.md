# Learnings

Durable findings, each with the evidence that produced it. Append; do not prune.
A learning without evidence is an opinion, and gets treated as one.

---

## L1 - Egress policy differs per path, within one session

**Evidence.** From the container, `curl https://www.youtube.com/` returns
`CONNECT tunnel failed, response 403`, and `$HTTPS_PROXY/__agentproxy/status`
lists the refusal under `recentRelayFailures`. The same session's web *search*
returns YouTube results and real video IDs. Web *fetch* on `www.ibm.com` returns
`EGRESS_BLOCKED` while search returns IBM page content.

**Rule.** Probe each path separately. "Blocked" is a property of a
(source, path) pair, never of a source alone.

**Consequence for this repo.** Sources the pipeline cannot fetch directly are
still researchable. They are captured into a committed manifest during research
and hydrated by the connector wherever egress permits - the connector code is
written for the unblocked case and degrades cleanly, rather than being written
for the blocked case and stuck there.

---

## L2 - GitHub API access is scoped per repository

**Evidence.** `GET /repos/turkertekten-ship-it/claude` -> 200.
`GET /repos/python/peps` -> 403, with a valid token that reports
`15000/15000` remaining on `/rate_limit`. Meanwhile
`raw.githubusercontent.com/python/cpython/...` -> 200.

**Rule.** Authentication, quota and authorization are three different things.
A token that authenticates and has quota may still be denied per resource, and
the denial arrives as 403 on the first real call - not at auth time. Probe the
specific resources you need (`probe_github_repo_scope`), not just the API root.

**Also.** Raw content and the REST API do not share a scope. Blocked on one does
not mean blocked on the other.

---

## L3 - GitHub signals rate limiting with 403

**Evidence.** Documented GitHub behaviour, reproduced in
`tests/test_github_offline.py::test_rate_limited_response_is_retried_after_the_reset`:
primary quota exhaustion and secondary rate limits both return **403** with
`x-ratelimit-remaining: 0`, not 429.

**Rule.** Retry 403 *only* when the headers or body say rate limit; otherwise
fail fast so a genuine permission error is not retried four times with backoff.
Honour `x-ratelimit-reset` as the wait, since the standard `Retry-After` is
often absent.

---

## L4 - The stdlib robots parser is not RFC 9309 compliant

**Evidence.** `urllib.robotparser.RobotFileParser.allowance()` returns the
first matching rule in file order. RFC 9309 section 2.2.2 requires the most
specific (longest) match, with `Allow` breaking ties. For the extremely common

```
Disallow: /docs/
Allow: /docs/public/
```

the stdlib forbids `/docs/public/guide`; every major crawler allows it.

**Rule.** Do not assume a stdlib module implements the spec it is named after.
Test against the spec's own examples. Replaced with `oodarag.scrape.robots`.

**Cost of not knowing this.** A crawler pointed at a documentation site would
have silently returned zero pages and looked like a network problem.

---

## L5 - Budgets must bound work, not output

**Evidence.** Crawling `pypi.org/project/requests/` with `max_pages=6` fetched
**163 pages, 32 MB, 77 seconds** to yield **1** document, because every
in-pattern link was a version page that deduplicated to the same canonical.
`max_pages` counted results; nothing counted requests.

**Rule.** Every bounded loop needs a budget on the *expensive* operation
(requests, bytes, wall-clock), not only on the accepted results. Deduplicated
and rejected items must not re-seed the frontier: their links are by definition
the links of the item they duplicate.

After the fix: 25 fetches, 5.5 seconds, same output.

---

## L6 - A rescue heuristic will rescue the wrong thing

**Evidence.** The HTML extractor retries with conservative pruning when
aggressive pruning leaves too little text. On a genuinely near-empty page
("far too short to index"), the retry returned the nav bar, cookie banner and
footer - 60 words of pure chrome - which then sailed past the thin-page filter
and would have entered the index as a document.

**Rule.** A fallback needs an acceptance test, not just a trigger. Here: accept
the conservative extraction only if it is both longer *and* not mostly link text
(boilerplate is overwhelmingly links; prose is not).

**Generalisation.** Any "if the good path fails, try the loose path" needs a
predicate on the loose path's output, or it converts a clean failure into a
dirty success.

---

## L7 - Test against evidence the code cannot fabricate

**Evidence.** The crawler's own `skipped["robots"]` counter proves nothing about
whether a disallowed URL was actually requested - only that the crawler thinks
it skipped one. The test server's request log proves it, because the crawler
does not write that log.

Similarly, the GitHub connector's file contents are checked against
`git cat-file blob` on a local clone: two independent readers of the same
repository, over completely different transports, must produce identical bytes.

**Rule.** Rank evidence by how independent it is of the code under test:

1. Observed by a third party (server logs, a second implementation, the git binary)
2. Derived at test time from a specification
3. Computed by the code under test  <- weakest, use only for reporting

And assert that each failure path *fired* at least once, or it is untested.

---

## L8 - A blind test is only blind if the expectation is derived

**Evidence.** The crawler blind test computes its expected URL set with a
reference BFS written from the documented rules, in the test file, with no
access to `Crawler`. When the two disagreed, three of the four disagreements
were bugs in the crawler (L5, L6, canonical identity) and one was a flaw in the
test's own site fixture - which is exactly the outcome a differential test
should produce.

**Rule.** Hardcoding expected values from a passing run bakes in current
behaviour, including its bugs. Derive expectations from the spec, or observe
them independently.

---

## L9 - Provenance must point at what was actually read

**Evidence.** PyPI serves every version page with `<link rel="canonical">`
pointing at the base project page. Using the declared canonical as the citation
URI collapsed six distinct crawled pages to one URI - a citation that would send
a reader to a page that does not contain the quoted text.

**Rule.** The citation URI is the URL fetched. A declared canonical is an
identity claim used for *deduplication*, and belongs in metadata. Pin to
immutable identifiers where they exist: the GitHub connector cites
`/blob/<commit-sha>/path`, never `/blob/main/path`, because `main` moves.

---

## L10 - A system that indexes its own repository contaminates its own eval

**Evidence.** Three separate times in one session, the golden set's negative
cases - out-of-corpus questions the system must refuse - started passing as
*answers*:

1. Indexing session transcripts put the test queries into the corpus, because
   the session in which they were tested quoted them verbatim. Retrieval found
   them, relevance scored 1.00, and "What is the capital of France?" was
   answered with confidence 0.85.
2. Writing `tests/test_pipeline_core.py` - which asserts those questions are
   unanswerable - put them into the corpus again, this time through the
   filesystem connector. Pass rate fell from 95% to 74% with no code change.
3. The near-miss case: the test says "Who won the 1998 World Cup final?" and the
   golden asks about the "1998 **FIFA** World Cup final". 83% term overlap - too
   different to match a 90% threshold, close enough to make the question
   answerable.

**Rule.** This is train/test leakage, and it arrives through a door nobody
watches. Any corpus that includes the project's own repository, tests, notes or
session logs will eventually contain the evaluation questions. Detect it, do not
assume it away:

* measure contamination *before* every eval run and report it alongside the
  results - an eval report without a contamination status is a number with no
  provenance;
* quarantine per question, not per source. Excluding the whole source throws
  away legitimate corpus; excluding the specific documents containing the
  specific question measures what the eval claims to measure;
* make the thresholds asymmetric. Over-quarantining costs one document of
  recall on one case. Missing contamination inverts the case and reports the
  wrong cause.

**Watch for the tell.** Contamination makes retrieval metrics go *up*. Nothing
looks broken. In case 1 the top result scored a perfect 1.00 relevance - it was
a perfect match for a question the corpus should not have contained.

---

## L11 - Two stages that compare the same text must analyse it identically

**Evidence.** Adding Porter stemming to the FTS5 index improved lexical recall
and made end-to-end retrieval *worse* (18/19 -> 17/19). The lexical arm, now
stemmed, ranked `answer.py` first for "how does the system decide to abstain".
The reranker, still matching raw tokens, scored that passage as containing none
of the query's terms - "abstained" is not "abstain" - and pushed the best hit
out of the results entirely.

Each half was individually correct. The combination was worse than neither.

**Rule.** Analysis must be consistent across every stage that compares the same
text: index, query, rerank, and any fallback path. Approximate agreement is not
agreement, which is why `util/stemming.py` implements the actual Porter
algorithm rather than a suffix-stripping approximation - FTS5 runs Porter, so
matching it exactly is the requirement.

**Second-order finding.** With stemming consistent, the eval got worse again -
because "recommended" now matched a query about ibuprofen dosage, and raw term
coverage weighted that ubiquitous word the same as "ibuprofen". The fix was to
weight coverage by IDF: matching a term that appears everywhere is not evidence.
Stemming raises recall and lowers precision, and a gate built on unweighted
coverage cannot absorb that.

**Meta-finding.** Each of these was caught by the eval harness and by nothing
else. There was no failing test, no exception, and no log line - just a number
that moved. A retrieval change without a measurement is a guess.

---

## L12 - A relevance signal must not be satisfiable by stopwords

**Evidence.** An independent end-to-end run asked "What is the boiling point of
mercury?" - a question the corpus cannot answer - and got a confident answer
(0.68) assembled from passages about journals and connectors.

The abstention gate reads `relevance = 0.6 * coverage + 0.4 * phrase`. Coverage
was correctly low (0.181, IDF-weighted: "boil" and "mercuri" are absent, "point"
is common). But `phrase` scored **0.429**, because it measured the longest
contiguous run of the query's tokens *including stopwords*: "what is the" is
three of the seven words in "what is the boiling point of mercury". That
contributed 0.17 on its own - more than the entire 0.15 floor.

**Rule.** Every component of a relevance score has to be evidence. A run of
stopwords is not evidence of anything; neither is a single shared common word,
which coverage already measures and weights by informativeness. The phrase
signal now uses stemmed content tokens with a minimum run of two.

**Why the earlier fixes did not catch it.** L11 made coverage IDF-weighted, and
coverage behaved correctly here. The bug was in the *other* term of the same sum
- one that had never been weighted at all, and that no golden case exercised
because every negative case until now shared no common word with the corpus.

**Generalisation.** When you fix a scoring component, check its siblings for the
same class of defect. A weighted term and an unweighted term in one sum means
the unweighted one now dominates the cases the weighting was meant to fix.

---

## L13 - A silent no-op is worse than a loud failure

**Evidence.** A batch of source edits applied with `str.replace` silently did
nothing, because the anchor text had moved. The module compiled, the suite
passed, and the feature was simply absent - surfacing three steps later as an
`AttributeError` on an attribute that was never added.

**Rule.** Any find-and-modify step must assert it found something. The fix is
one line - check the occurrence count before replacing and fail loudly when it
is not what was expected - and it paid for itself immediately: a later batch
aborted on a bad anchor *before* writing, leaving the tree untouched instead of
half-patched.

**Generalisation.** This is not about editing. Any operation that can quietly do
nothing - a regex that matches nothing, a filter that excludes everything, a
delete that removes no rows - needs to verify it acted.

---

## L14 - An adversarial pass finds what a test suite cannot

**Evidence.** An independent review of a codebase with 156 passing tests found
**15 confirmed defects**, each reproduced by running it. None of them threw an
exception. Every one returned a plausible wrong answer:

| Defect | Symptom |
|---|---|
| FTS5 `'delete'` given empty values | Deleted text stayed retrievable, and rowid reuse made it resolve **under a different document's citation** |
| `\b` before an underscore-prefixed keyword | `GITHUB_TOKEN=...` was written to the index unredacted |
| Relevant set built from the retrieved list | `recall@k` was pinned at 1.0 - the metric documented as the ceiling on everything downstream |
| `_normalize` leaving double spaces | Any golden question containing a comma was invisible to the verbatim contamination check |
| Refit baseline rewritten every run | Corpus growth measured against the last *run*, so the embedder could never refit |
| `source_health` overwritten per cycle | A quarantine did not survive a restart; an intermittent source could never reach the threshold |
| Fence detection by `split("```")` parity | Prose *mentioning* a fence flipped parity and the whitespace collapse ran inside real code |

**Rule.** A suite proves the cases someone thought of. It cannot prove the
absence of cases nobody thought of, and a green suite is actively misleading
about that. Budget for a pass whose explicit goal is to break the thing, with
two constraints that did the work here: **prove every finding by running it**,
and **rank by whether a wrong answer reaches a user**, not by how odd the code
looks.

**Corollary, from fixing them.** Three of the fifteen were siblings of bugs
already fixed - the same class in the next function along (unweighted matching
in `contamination` after `rerank` was fixed; a token-boundary collision in the
very code that had just been corrected). When you fix a defect, search for its
class, not its instance.

**The honest footnote.** Fixing #3 moved reported `recall@8` from 0.84 to 0.65.
Nothing got worse; the number started meaning something.

---

## L15 - Detection without propagation is not a feature

**Evidence.** The connector contract detected removed documents correctly and
had done since it was written: after a file was deleted from a source, the
cursor recorded `removed_last_run: ['secret.md']`. Nothing downstream could see
it, because `IngestDelta` did not carry the field. The document stayed in the
index, stayed embedded, and stayed citable - an answer could quote text that no
longer existed at a URI that no longer resolved.

The gap survived because every visible signal said it was handled: the code that
computes removals is there, it is commented, and `internal/PLAN.md` listed
deletion as "next" rather than "missing", which reads as a decision rather than
an omission.

**Rule.** A value that is computed and not consumed is dead code wearing a
feature's clothes. When a plan says a capability is "deliberately deferred",
check that the deferral is actually enforced somewhere - and that what exists is
either wired up or clearly marked unreachable.

**On the fix.** Pruning is guarded rather than automatic, for the reason the
original deferral gave: a source returning almost nothing is usually an expired
token or a truncated listing, not a bulk deletion. A removal set above 25% of a
source is refused and reported, a connector that failed contributes no removals
at all, and the prune is scoped by source system because two sources can
legitimately use the same external id. The loop decides it at priority 85 -
below index integrity, above freshness, because a citation to deleted text is
wrong rather than merely stale.

---

## L16 - A normalised metric above 1.0 is the metric telling you it is broken

**Evidence.** After the recall fix (L14, defect 3), the external eval reported
**nDCG@8 = 1.4575**. nDCG is normalised by construction; it cannot exceed 1.

The cause: retrieval returns *chunks*, and several chunks map to the same
expected *document*. Every occurrence earned gain, while the ideal DCG counted
the document once - so achieved DCG exceeded ideal. Only the first appearance of
a relevant item should score.

**Rule.** Know each metric's range and assert it. A value outside the range is
free evidence that the implementation and the definition have diverged, and it
costs one line to check. The bug had been reported as a plausible-looking 0.62
on the primary corpus; it took a corpus where documents were chunked more
heavily to push it past 1.0 and become visible.

---

## L17 - `max()` over a set is not deterministic across processes

**Evidence.** An abstention gate asked whether the query's most informative term
appeared, via `max(query_set, key=idf)`. When several terms tie on IDF - common,
since every term absent from the corpus receives the same default - `max`
returns whichever tied element it meets first. Set iteration order for strings
depends on hash randomisation, which Python varies **per process**.

Four runs of the same question:

```
order= ['point','mercuri','boil']  max_on_tie= point
order= ['boil','mercuri','point']  max_on_tie= boil
order= ['point','boil','mercuri']  max_on_tie= point
order= ['boil','mercuri','point']  max_on_tie= boil
```

"point" is in the corpus; "boil" and "mercuri" are not. So the same question
abstained or answered depending on which run you were in, and the golden set
moved by one case between identical invocations - indistinguishable from noise.

**Rule.** Never let an ordering decision fall out of a set. Iterate a sorted
sequence, break ties explicitly, or - better - reformulate so no arbitrary
choice is needed. The fix here replaced "is the single best term present" with
"how much of the query's IDF mass does the corpus contain at all", which has no
tie to break and is a property of the query rather than of any one chunk.

**Where this hides.** It only bites when values tie, so it survives every test
written with distinct values, and it is invisible within a single process.

---

## L18 - Evaluate on a corpus that has never heard of you

**Evidence.** The primary corpus is this repository, which documents its own
evaluation. Contamination reached 4 of 20 questions and 25 quarantined
documents, and grows with every commit - the eval measures a smaller corpus each
time. A second golden set was built over fourteen PyPI project pages, which have
no relationship to this project.

The external set immediately caught **two abstention failures the primary set
could not see**: "what is the boiling point of mercury" and "what is the capital
of France" were both answered confidently. The primary corpus could not detect
them, because by then it *contained* those exact phrases - written into the
learnings file, the golden set and the tests while fixing earlier versions of
the same bug.

**Rule.** If a system is evaluated on material it also authors, keep a second
corpus it cannot influence. It does not need to be large - fourteen pages was
enough - only independent. Report both, and treat a disagreement between them as
the interesting result rather than an inconvenience.

**Also.** The external set found the nDCG overflow (L16) that the primary set had
been quietly under-reporting, because its documents chunk more heavily. A second
corpus is a second sampling of the failure space, not just a second score.

---

## L19 - A negative result is a result, if you write down the number

**Evidence.** Pseudo-relevance feedback was implemented specifically to fix one
documented failure - a question phrased in words the corpus does not use ("what
stops a crawl from running *forever*" against a module that says "bounded by
requests, bytes, depth" and "never terminates"). It did not fix it, and it made
the primary corpus worse:

| corpus   | expansion | pass  | recall@8 | nDCG@8 |
|----------|-----------|-------|----------|--------|
| external | off       | 20/20 | 0.800    | 0.7815 |
| external | on        | 20/20 | 0.800    | 0.7815 |
| primary  | off       | 17/20 | 0.625    | 0.4729 |
| primary  | on        | 17/20 | 0.600    | 0.4642 |

The target question expanded to *"neither candid markdown below model wrong eval
rather"* - terms harvested from the same wrong results the unexpanded query had
returned. Textbook query drift. The three mitigations built in (lower weight, a
separate fused arm, lift-based term selection) limited the damage without
preventing it.

**Rule.** Pre-register the decision rule *before* measuring - here, "keep only
if neither corpus regresses and at least one improves" - and then honour it.
Without that, a result this close is easy to argue into acceptance, because the
pass rate did not move and only two second-order metrics fell.

**On what to do with the code.** It is kept, off by default, with the table
above in its module docstring and tests pinning the default. The technique is
sound and helps on many corpora; it does not help on this one, where the
embedder already does subword matching and the corpus is small. Deleting it
would mean the next person implements it and repeats the experiment; keeping it
undocumented would mean someone enables it and quietly loses recall.

**A detail worth keeping.** The feedback set for the target question included
`retrieve/expansion.py` - the module written to fix that question became a top
result for it, and then supplied its own vocabulary as expansion terms. A
self-referential corpus contaminates more than its evaluation.

---

## L20 - Check the denominator, not just the numerator

**Evidence.** Reported external recall@8 was 0.80, and it looked like retrieval
headroom worth chasing. Inspecting the cases individually showed every graded
case fully satisfied: all 16 retrieved every expected source, most at rank 1.

The metric was averaging over all 20 cases, four of which are `expect_abstain` -
questions with nothing to retrieve, whose recall is definitionally zero.
16 × 1.0 ÷ 20 = 0.80. **Adding a negative case to the golden set lowered
reported recall**, with no change to retrieval at all.

Correctly scoped, the same runs read: recall@8 1.00, hit@8 1.00, MRR 0.97,
nDCG@8 0.98.

**Rule.** When a metric looks off, check what it is averaged over before
investigating what it measures. A denominator that silently includes cases the
metric does not apply to is invisible in the aggregate and obvious in the
per-case output - which is why the harness now reports the graded count next to
the numbers.

**Note the direction.** L14 found a recall bug that made the number too high
(0.84 → 0.65 after fixing). This one made it too low (0.80 → 1.00). Both were
denominator errors, both were honesty fixes, and the fact that they moved in
opposite directions is the point: an unexamined metric is not biased in a
convenient direction, it is simply unknown.

---

## L21 - A cursor that outlives its index produces a silently partial corpus

**Evidence.** Deleting an index and re-running the ingest produced **19
documents out of 33**, reporting zero errors. Incremental ingest decides
"unchanged, skip" from the cursor alone; the cursor lived in a JSON file beside
the index, survived the deletion, and reported every document it knew about as
unchanged. Nothing re-added them.

The only visible symptom was the eval score halving - recall@8 fell from 0.93 to
0.41 - which reads as a retrieval regression, not a missing corpus.

**Rule.** The cursor is not the authority on what the index contains; the index
is. Two changes: cursors now live inside the index by default, so they cannot be
deleted separately from the data they describe (L15 established this for the
library and the CLI was still using a file); and before each run the pipeline
reconciles - anything the cursor claims that the store does not have is dropped
from the cursor and re-fetched.

**Generalisation.** Any cache that records "I have already handled X" must be
invalidated by the disappearance of X, not only by a change to it. Optimisations
that skip work need a way to notice the work has been undone.

---

## L22 - A corpus that documents its own evaluation eventually cannot evaluate

**Evidence.** L10 recorded contamination as something to detect and quarantine.
It does not stay bounded. All three current failures on the primary golden set
are now self-reference artefacts:

- the top result for "What stops a crawl from running forever?" is
  `retrieve/expansion.py`, whose docstring quotes that exact question as the
  example it was written to fix;
- the top results for "How does the system decide to abstain?" are the ADR, the
  learnings file and the regression tests written *about* the abstention logic;
- "What is the boiling point of mercury?" is answered, because that phrase now
  appears in the learnings file, two test files, a module docstring and the
  golden set itself.

The retriever is right every time - those documents genuinely are the best
lexical and semantic matches for those words. They are simply not the answer.
Quarantine now removes 26 documents across 4 questions and rises with every
commit.

**Rule.** Writing things down makes a self-indexing corpus a worse evaluation
target, and writing less down is not the answer. Gate on a corpus that cannot be
affected by what you write. The primary set is kept as a smoke test and as a
live demonstration of contamination - it is genuinely useful for that - and the
external set is the regression gate.

**The general shape:** when the measurement and the thing measured share a
substrate, the measurement decays. Budget for an independent one early, while
the corpus is still small enough that building it is cheap.

---

## L23 - A flag must degrade the thing it names, and a saturated metric hides that it didn't

**Evidence.** `scripts/ablation.py` was written to answer "what is each retrieval
arm actually worth?". Its first run said `use_rerank=False` answered **8 of 36**
external golden cases, against 32 for the full hybrid - while recall stayed at
0.857. The retriever was finding the right chunks and then refusing to answer.

The cause: the abstention gate reads `rerank_relevance`, a feature only the
reranker computes. Making the reranker call conditional on `use_rerank` left
that feature at zero, so the gate abstained on nearly everything. A flag named
for ranking had quietly disabled an unrelated safety check.

The first fix restored the pre-rerank list *order* and looked correct. It was
not: MMR and the score floor both read `result.score`, which still held the
reranked value, so the arm came out byte-identical to full hybrid. Only
restoring `score` from `pre_rerank_score` made the flag mean anything -
`no rerank` then measured 31/36, recall 0.857, precision 0.165, nDCG 0.792
against hybrid's 32/36, 0.929, 0.295, 0.863.

**Why it survived so long.** The metric in use was hit@8, which read **26/28 for
both hybrid and lexical-only**. On a corpus this size, eight slots are enough for
almost anything to land somewhere in the list, so the metric was pinned at its
ceiling and could not express the difference. nDCG and precision, which care
where in the list a result lands, separated the arms immediately.

**Rules.**
1. A configuration flag must change the behaviour it names and nothing else.
   Prove it: assert the flagged run differs from the unflagged one. A flag whose
   two settings produce identical output is either dead or wired to the wrong
   thing, and both look like success.
2. When a feature computed by one stage is consumed by another, the consumer
   owns the requirement. Compute the feature unconditionally and let the flag
   govern only its use.
3. Before trusting a comparison, check the metric is not saturated. If two arms
   you expect to differ score the same, suspect the ruler before the arms.

Both failure modes are pinned by `RerankCouplingTest`, and both were confirmed
by mutation: re-introducing the conditional rerank fails 3 of its 3 tests;
re-introducing the order-only fix fails 2 of 3.
