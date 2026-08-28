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

---

## L24 - A tokenizer that disagrees with the index invents terms the corpus can never contain

**Evidence.** "Which library dispatches in-process notifications between
objects?" retrieved `blinker.md` and then abstained on it: relevance 0.13
against a 0.15 floor.

`_TOKEN_RE` deliberately glues `snake_case`, `dotted.paths` and hyphenated words
into single tokens, because half this corpus is code and `oodarag.util.text` is
one identifier rather than three words. FTS5's `unicode61` treats `.`, `-` and
`/` as separators. So the two stages disagreed, and `_fts_query` quotes each
term, which makes `"in-process"` a *phrase* to FTS5 - it matched a document
saying "in process" perfectly well. The reranker then scored that same document
as containing neither word.

The damage came from the idf default. A term absent from the corpus gets the
maximum idf, so `in-process` scored 8.56 against `process`'s 5.43 - the ghost was
the most informative term in the query, and it could not be matched by any
document, ever. It dominated the coverage denominator and dragged answerability
from 1.0 to 0.695.

**What did not work.** Expanding compounds into their parts everywhere -
coverage, idf table, FTS query - looked like the principled repair. Measured on
the external corpus it left recall unchanged, moved precision +0.005, and cost
MRR 0.029 and nDCG 0.023. It also did not fix the case that motivated it:
blinker still scored 0.13. The atomic compound was carrying real signal, and
adding parts to both sides of the comparison mostly added noise.

**What worked.** Split a compound *only when the corpus vocabulary does not
contain it*. A compound the corpus has is a real term and keeps its identity; a
compound the corpus cannot have is not evidence of anything and is replaced by
its parts. Measured on the external corpus: recall, precision, MRR and nDCG all
unchanged to four decimal places, the wrong abstention gone, and the gate's
separation improved - the lowest-scoring answerable case rose 0.1301 to 0.1804
and misclassifications at the floor fell from 3 to 2.

**Rules.**
1. When two stages tokenize the same text differently, the disagreement does not
   show up as an error. It shows up as one stage confidently reporting that a
   term is absent, which is the strongest signal the system has.
2. Before repairing a disagreement, check which side is right. Here the whole-
   token regex was right about identifiers and wrong only about terms the corpus
   does not contain, so the fix belonged at that exact boundary and nowhere else.
3. A default assigned to "unseen" is a claim. `idf(unseen) = max` says absence is
   maximally informative; that is true of a real word and false of a token the
   tokenizer invented.
4. **A measurement whose motivating case does not move is a failed measurement**,
   whatever the aggregate did. The broad expansion moved four aggregate metrics
   and left blinker at 0.13 - that, not the nDCG loss, was the signal it was the
   wrong fix.

`GhostCompoundTest` pins it, taking the premise from SQLite itself rather than
asserting it: if FTS5 ever stops splitting on those separators, the test says so.

---

## L25 - The gate's feature is not the problem, and five candidates proved it

> **Superseded in part by L29.** The ranking below still holds - the feature in
> use beats all five candidates - but the conclusion that its failures are "a
> tail, not a design flaw" was measured on 33 documents and does not survive 91.
> The AUC falls from 0.973 to 0.886 and the gate becomes the dominant failure
> mode. Read the rule, not the verdict.

**Evidence.** Two of the four remaining external failures are the gate answering
a question the corpus cannot answer. `gate_margin.py` showed this is not a
threshold problem: the highest unanswerable case scores 0.355 against a 0.15
floor, the lowest answerable case scores 0.180, and raising the coverage
exponent widens that overlap monotonically (-0.2251 at 1.0, -0.2632 at 3.0).

So the obvious next step was a better feature. `gate_features.py` ranks
candidates by AUC - the share of (answerable, unanswerable) pairs ordered
correctly - because a pass count at a fixed floor conflates the feature with the
floor:

    rerank_relevance (in use)   0.973
    relevance x top-gap         0.973
    relevance x matched idf     0.964
    top1 - mean score           0.795
    top1 - top2 score           0.768
    max idf of matched terms    0.574

**The feature in use won.** Nothing beat it, and combining it with the top-gap
changed nothing at all. The hypothesis that motivated the sweep - that a question
made entirely of ordinary words ("what keeps two processes from writing the same
file at once") matches many moderately-rare words while identifying nothing - is
refuted: match specificity is 0.574, near a coin flip.

**Rule.** Before replacing a component, measure the one you have on the same
scale as its replacements. AUC 0.973 over 224 pairs is roughly six misordered
pairs; that is a tail, not a design flaw, and the two failing cases are it. A
lexical-semantic scorer cannot distinguish "the corpus discusses these words"
from "the corpus answers this question" - closing that gap needs a judge that
reads, or a corpus large enough that the near-misses stop being near. Neither is
a scoring change, so no further scoring change should be attempted for it.

**On the sweep itself.** Eight unanswerable cases is a small sample and AUC will
happily rank noise. It was used to *reject* candidates, which is what a small
sample can support; nothing was adopted on it.

---

## L26 - The regression gate was 90.9% site template

**Evidence.** `blinker.md` is 5,269 bytes. About 350 of them describe blinker;
the rest is PyPI's download table, wheel filenames, SHA256 and BLAKE2b digests,
Sigstore transparency entries and the full release history back to 2010.
Measured across the whole external corpus - the one this project relies on
*because* it is uncontaminated - **90.9% of it was that furniture**.
`coverage.md` was 252KB of which 1,962 bytes described the project;
`cffi.md` 90KB of which 653.

`scrape/html.py` is not at fault, and this was checked rather than assumed:
run against the live page it turns 75,768 bytes of HTML into 5,205, and the
sections it keeps sit inside the page's main content area. No single-page
extractor can tell them from the article.

**Why it mattered more than wasted space.** IDF is computed over that text. The
word `file` - in every page's "Download files", "File details" and "File
hashes" - had an IDF of 0.08, so a corpus of hex digests and upload dates set
the scale deciding what counts as a rare term. Every downstream stage reads that
scale: the reranker's coverage, the abstention gate's answerability, the
extractive generator.

**The fix.** Cross-document repetition is the signal one page cannot see. A
heading present in at least half the documents from one host is that host's
template (`scrape/boilerplate.py`). On this corpus the separation is wide: the
eight template headings are in 67-100% of pages, and the next-most-common
heading, "Contributing", is in 27%.

**Measured, external corpus, everything else held constant:**

    corpus         chunks  pass   recall  prec    MRR     nDCG   latency
    as committed    2,615  32/36  0.9286  0.2946  0.8741  0.8633   112ms
    template off      253  33/36  0.9821  0.2812  0.8793  0.8833    42ms

Recall rose 0.054, nDCG 0.020, one more case passed, the index shrank tenfold
and queries got 2.7x faster. Precision fell 0.013. Two of the four standing
failures were boilerplate dilution: `pluggy` now retrieves, and `blinker` moved
from "not retrieved" to "retrieved but gated".

**A rejected variant, recorded because it was tempting.** A second trigger -
"a heading repeated many times inside one document is template" - caught the
real furniture (172 repeats) but also ate changelogs, which repeat "Fixed" 37
times and "Changed" 35. There is no threshold between 37 and 172 that is
anything but a number fitted to this corpus, and the rule contradicted the
premise: the signal a single page cannot see is repetition *across* pages.
Dropped.

**Rules.**
1. Look at the corpus. Not a sample of one document - the byte counts. A
   250KB page describing a Python library is a fact about the extractor, and it
   was sitting in `wc -c` for the whole time the retrieval scores were being
   tuned.
2. Boilerplate is defined by repetition across a site, not by position in a
   page. An extractor that only sees one document cannot apply the definition,
   so the filter belongs to corpus construction.
3. **A conclusion measured on a corpus is a conclusion about that corpus.**
   Cleaning this one reversed the coverage_power finding recorded in L23's
   neighbourhood (the exponent widened the gate's overlap monotonically before,
   and narrows it after) and inverted ADR 0004's arm comparison. Every
   measurement table in this repository now names the corpus it was taken on.

---

## L27 - The corpus was rewritten and the embedder never noticed

**Evidence.** After removing the template, the same corpus and the same code
gave `recall@8 = 1.0` through the incremental index and `0.9821` rebuilt from
scratch. Identical inputs, different answers, nothing logged.

`_should_refit` compared document *counts*. Rewriting all 33 documents deleted
90.9% of their text and left the count at 33, so growth was 0.0 and no refit
fired: the embedder stayed fitted on a term distribution that no longer existed.

This is the reasoning `idf_table` already applies to itself, in a comment
directly above the code - *"Keyed on a content digest, not just the count.
Re-indexing a document with reworded text of the same chunk count leaves the
count identical while every term changes"* - which had never been carried across
to the fit that the same corpus feeds.

The rule was also asymmetric. `(total - fitted) / fitted > 0.25` fires on 25%
growth and never on shrinkage, and a corpus that loses a quarter of its text has
moved exactly as far as one that gains a quarter.

**The fix.** Record the corpus volume at each fit alongside the count, and refit
when either moves more than 25% in either direction. Verified end to end by
replaying the actual scenario from git: index the pre-cleaning corpus, swap in
the cleaned one, and compare against a fresh build. Before, the two paths
disagreed and no refit fired; after, they agree exactly. Reverting the fix makes
the check fail again, so the check can see the bug it is there for.

**Note the direction.** The stale index scored *better* - 1.0 against 0.9821.
The fix does not improve the metric; it makes the metric mean something. A
number that depends on the history of the index rather than on its contents is
not a measurement.

**Rules.**
1. When a cache is invalidated on a content digest, ask what *else* was derived
   from that content. Here it was the thing the digest was invented to protect.
2. A threshold on change should be symmetric unless there is a stated reason it
   is not. "Grew by a quarter" and "shrank by a quarter" are the same distance.
3. Build the same thing twice, once incrementally and once from scratch, and
   compare. Any difference is a bug, and it is a class of bug no unit test on
   either path alone can find.

---

## L28 - What an adversarial review found that 249 passing tests did not

An independent reviewer was given the retrieval and evaluation path and asked
for defects that produce wrong results silently, with a reproduction for each.
The suite was green throughout. Six of its seven findings held up; the seventh
did not, which is the second lesson here.

**Held up, in severity order.**

1. *The reranker's corpus statistics were captured once.* `HybridRetriever`
   took `store.idf_lookup()` and `store.vocabulary()` in its constructor. The
   first closes over a dict, the second returns a set - neither ever saw a later
   index run. A retriever built before indexing kept an **empty** vocabulary for
   life, and `_answerability` returns 1.0 on an empty vocabulary because that is
   the guard for a corpus too small to judge absence. `ooda loop` builds its
   generator before the ACT phase indexes, so this was every loop run: the gate
   stopped abstaining and nothing said so.
2. *Porter step 4 removed two suffixes.* "ion" sat outside the loop as an
   unconditional rule, so "additionally" lost "al" and then "ion" - "addit"
   against SQLite's "addition". Measured against SQLite's own tokenizer through
   `fts5vocab` over 5,145 word types, disagreement was 18 types; it is now 8.
   The `if suffix in ("ion",)` guard inside the loop was unreachable, because
   "ion" was not in the list it iterated.
3. *The IDF cache was keyed on corpus content but not on the analyser.* The
   table's terms are the analyser's output. Change the stemmer and an index
   serves the old term space while queries arrive in the new one - so every
   query term reads as absent, and absent means maximum weight. The FTS table
   has guarded against this with a schema version all along.
4. *Contamination excerpts were sliced out of the wrong string.* The offset
   indexed the stemmed token text and then sliced the raw document, so the
   evidence field of a report whose purpose is to justify quarantining a
   document showed unrelated text. It also re-searched for the question's
   *first* words, though the matched run may start anywhere.
5. *`Expansion.weights` was computed and never read*, while the module docstring
   described expansion terms "weighted below the original query". The weighting
   did not exist.
6. Three small ones: a `uri_prefix` filter whose `%` and `_` acted as wildcards,
   a precision metric that deduplicated its numerator but not its denominator,
   and a scan budget applied by slicing a fully materialised document list.

**Did not hold up.** The report said `dense_weight` was a control that changes
nothing - 0 of 56 queries affected by setting it to 0 or to 50 - because the
reranker's adjustment swamps the fused score. Re-measured on the current code:
`dense_weight=0` changes the returned list on **34 of 36** queries and
`dense_weight=50` changes the **top-1** result on 15 of 36. A weaker version is
true and worth knowing - `dense_weight=0` changes top-1 on 0 of 36, so the dense
arm's fusion weight moves the tail and never the head on this corpus - but the
finding as stated is wrong.

**Rules.**
1. A green suite is evidence about the paths it exercises. Every defect above
   was in a path with tests; none of the tests asked the question that exposed
   it. Adversarial review is not redundant with testing, and the two find
   different things.
**How much the first one cost, measured after the fact.** `ooda loop` builds its
generator before the ACT phase indexes anything, so the empty-vocabulary case was
every loop run rather than an edge case. Running one cycle against an empty index
over the 91-document corpus, with the fix and without:

    with the fix       47/54  (0.8704)
    fix reverted       38/54  (0.7037)

Nine cases. The loop's own quality rule fired an `alert` action in the degraded
run, so the system did notice - it just had no way to say why, and the number it
reported was the only visible symptom of a retriever whose gate had been silently
switched off. A defect that only shows up in the autonomous path is a defect that
shows up when nobody is watching.

2. **Verify a finding before acting on it, including one that arrives with a
   reproduction.** The reproduction can be correct and the conclusion wrong, or
   the code can have moved underneath it. Re-running the measurement cost
   minutes; changing the fusion weights on a false premise would have cost a
   regression nobody could explain.
3. The three most severe findings are all one shape: **a value derived from the
   corpus, cached, and not invalidated when its input changed.** The reranker's
   vocabulary, the IDF table's analyser, the embedder's fit (L27). Where this
   codebase holds derived state, that is where to look next.

---

## L29 - Widening the corpus overturned three conclusions, including one from this file

The external corpus went from 33 documents to 91, and the golden set from 36
questions to 54, using `scripts/build_external_corpus.py` - which did not exist
before, so the artifact every retrieval number is measured against could not be
rebuilt. That is now fixed and the builder uses the pipeline's own parts, so a
defect in extraction shows up in the corpus rather than being papered over by a
separate scraper.

**What it overturned.**

1. *ADR 0004's arm comparison, for the second time.* At 33 dirty documents
   hybrid led dense-only by 0.11 of recall; cleaned (L26), dense-only matched
   hybrid and led on ordering, and the ADR recorded the case for the lexical arm
   as weak and **deferred** the decision rather than removing an arm on 36
   questions. At 91 documents hybrid leads again by 0.10 of recall. The
   deferral was right, and both small-corpus readings were artifacts.

2. *L25, in this file.* It concluded that the abstention gate's feature was
   already the best available and that its failures were "a tail, not a design
   flaw" - AUC 0.973, roughly six misordered pairs. On 91 documents the same
   measurement gives **0.886** over 473 pairs, the overlap between answerable
   and unanswerable widens from -0.21 to -0.45, and six of eleven remaining
   failures are the gate answering something it cannot answer. The feature is
   still the best of the six candidates and is no longer good enough. **L25's
   rule stands; its conclusion does not.**

3. *Metric saturation.* Cleaning the corpus had pushed `recall@8` to 0.982 with
   a median of 1.0, which L26 flagged as a ceiling it could no longer measure
   from. It now reads 0.919 with a minimum of 0.0.

**Three defects the widening exposed, each silent.**

- *A 200 that is not a success.* pypi.org serves a Fastly anti-bot interstitial
  with HTTP 200, a normal content-type and a few kilobytes of markup. Indexed,
  it is a document that answers nothing - and a site serving the same one for
  many URLs contributes identical text repeatedly, the worst possible input to a
  term-frequency statistic. `scrape/html.interstitial_reason` names it.
  Intermittent: one URL returned it twice while five others succeeded seconds
  apart, then returned content ten times in a row minutes later.
- *Writing `page.text` where the corpus needs `page.markdown`.* The template
  filter works on headings and `text` has none, so it was a silent no-op: 60
  documents were added carrying every byte of their boilerplate, one of them
  305KB, while the report said "0.0% removed". It said so honestly. Nobody
  looked. The builder now prints fetched-versus-stored words per page, because a
  page whose two numbers are equal and a page with no template on it must not
  look alike.
- *A thinness guard on the wrong side of the filter.* `MIN_WORDS` was checked
  against the fetched text, so pages that were 40 words of prose and 17,000
  words of download table passed it and landed as eight-word documents. Checked
  against the stored text, three of them are correctly refused.

**A stemming collision, which is nobody's bug.** "What is the boiling point of
mercury?" is answered at 0.825 because `mercury` and `mercurial` both stem to
`mercuri`, and one document mentions Mercurial the version control system.
SQLite's Porter agrees, so this is the algorithm working as specified.
Answerability's premise - "a term absent from the vocabulary proves the corpus
never discussed it" - is weaker than it reads: absent *after conflation* is not
absent.

**Rules.**
1. A conclusion drawn on a small corpus is a hypothesis about a large one. Two
   of the three reversals above were recorded as settled findings at the time,
   with tables.
2. **Deferring beats acting when the measurement cannot support the action.**
   Removing the lexical arm on 36 questions would have been wrong, and the
   evidence for removing it looked exactly as good as the evidence for keeping
   it does now.
3. When a corpus grows, the questions written for the old one may no longer be
   questions. "How do Python programs talk to a web server?" had two plausible
   answers at 33 documents and ten at 91; it was replaced, with its reasoning
   recorded, rather than quietly widened to ten expected sources.

---

## L30 - The stemmed vocabulary was the wrong place to ask "does the corpus know this word?"

**Evidence.** L29 left the abstention gate as the dominant failure mode: six of
eleven external failures were the gate answering a question the corpus cannot
answer, and its feature's AUC had fallen from 0.973 on 33 documents to 0.886 on
91.

`gate_features.py` ranked two new candidates against the four already rejected:

    relevance x surface            0.896
    rerank_relevance (in use)      0.886
    relevance x top-gap            0.886
    surface answerability          0.877
    relevance x matched idf        0.865
    top1 - top2 score              0.799
    top1 - mean score              0.776
    document coverage              0.742
    chunk minus document coverage  0.609
    max idf of matched terms       0.555

Two things came out of that table, and the second is the useful one.

**The document-coverage hypothesis is dead.** "Which package renders Jinja
templates to PDF?" scores highest of all unanswerable cases because jinja,
template and render are all present and pdf is only ever elsewhere - so the
obvious signal was "a *document* covers the query while no *chunk* does". It
ranks 0.609, barely above a coin flip, and plain document coverage is worse than
what is already in use. `pdf` is in the corpus; the query's terms are simply
never together. Confirmed by inspection, not just by the number.

**Answerability was asking the wrong vocabulary.** It treats a query term absent
from the corpus vocabulary as proof the corpus never discussed the thing. That
vocabulary is stemmed, and stemming conflates: `mercury` and `mercurial` share
`mercuri`, so one page mentioning the version control system made the chemical
element read as known, and "What is the boiling point of mercury?" was answered
at 0.83. SQLite's Porter agrees with ours, so the stemmer is right and the
*question being asked of it* was wrong. **Absent after conflation is not
absent.** The store now keeps an unstemmed vocabulary and the gate multiplies in
the share of the query's idf mass whose surface form the corpus actually holds.

**Measured end to end, everything else held constant:**

    corpus    surface  pass   recall  prec    MRR     nDCG
    external  off      44/54  0.9186  0.2355  0.7729  0.7965
    external  on       47/54  0.9186  0.2355  0.7729  0.7965
    primary   off      17/20  0.8125  0.2109  0.5594  0.6041
    primary   on       17/20  0.8125  0.2109  0.5594  0.6041

Three cases gained, none lost, and **every retrieval metric identical to four
decimal places** - the property to check rather than assume, and asserted by a
test: the factor is a function of the query and the corpus, not of any chunk, so
it scales every candidate equally and cannot reorder them.

**Rules.**
1. **AUC ranks pairs; a case is decided by whether it crosses a fixed floor.**
   The winning candidate beat the incumbent by 0.010, about five pairs of 473,
   which reads as noise - and was worth three cases end to end. Rank candidates
   by AUC to decide what to *try*; decide what to *ship* on the metric the
   system is judged by.
2. When a derived structure answers a question badly, check whether it is the
   question you meant to ask. Nothing was wrong with the stemmer, the
   vocabulary, or the code that consulted it. The premise attached to the answer
   was wrong.
3. **A guard that exists for one feature usually applies to its sibling.**
   Switching this on without `min_vocabulary_for_answerability` made a
   five-document corpus abstain from everything - relevance 0.06 against a 0.15
   floor - and the suite caught it. A small corpus lacks most *surface forms* of
   the words it does discuss, even more sharply than it lacks stems.
4. A feature computed and never applied passes every test written about the
   feature. The mutation that removed the multiply from `rerank()` passed four
   of five new tests; only an end-to-end one caught it. This is the third time
   this session (L23, L28).

---

## L31 - I broke the regression gate with a commit whose message contained the number

**Evidence.** The corpus-widening commit (L29) took the external pass rate from
33/36 to 44/54. CI's external gate is `--min-pass-rate 0.85`; 44/54 is 0.8148.
The run went red. The commit message states "44/54" in a table.

Nothing was wrong with the change, the gate, or the number. I had all three and
did not put them together, because I was measuring *retrieval quality* - recall,
nDCG, saturation - and the gate measures *pass rate*, which I had watched fall on
purpose and stopped thinking of as a threshold. The next commit took it to 47/54
and CI recovered, so the red was transient by luck of sequencing rather than by
design.

**What makes this more than carelessness.** Deliberately making an evaluation
harder and leaving its floor alone guarantees a failure that is expected, and an
expected failure is the kind people learn to scroll past. The floor is part of
the change: either it moves with the corpus, or the change waits for the work
that restores the margin, or the commit says why red is correct for now. Any of
those is fine. Silence is not.

The floor stays at 0.85. At 47/54 = 0.870 it tolerates exactly one more failing
case, which is the tightness it is for.

**Rules.**
1. A threshold in CI is a number in the repository like any other. When a change
   moves the quantity the threshold guards, check the threshold in the same
   breath - the arithmetic takes seconds and was already sitting in the commit
   message.
2. **Check CI on your own push before starting the next thing.** The gate exists
   to tell you something, and it can only do that if someone reads it. Two
   further commits went out before I looked.
3. Deliberately raising the difficulty of a measurement is a legitimate and
   valuable act; it is also the moment the old thresholds stop meaning what they
   meant.

---

## L32 - The floor was set against a corpus that no longer exists, and my sweep had a substring bug

**Evidence.** `min_relevance = 0.15` decides whether a question is answered or
refused. Swept in steps of 0.01 over both corpora it turns out to sit in a
two-sample *dip*: 0.10-0.14 and 0.17-0.21 both score better, and 0.15-0.16 is
the worst region in the range. It was chosen against a 33-document corpus. This
is L31's rule again, on a second threshold - a number set against an old
difficulty stops meaning what it meant - and the two were found within an hour
of each other, which suggests looking for the third.

Moved to **0.19**, the middle of the 0.17-0.21 plateau. External 47/54 to 48/54,
primary 17/20 to 18/20.

**0.20 scores one case higher and was declined.** It is a single sample with
0.19 and 0.21 both below it. Picking the peak of a swept curve fits the
threshold to 74 questions; the plateau is the part of the curve that carries
information about the corpus rather than about the golden set.

**The sweep's first table was wrong, and the way it was wrong is the lesson.**
Failure modes were counted with `"expected abstention" in failure`. The string
for the opposite failure is `"unexpected abstention"`, which **contains** it, so
every wrongly-refused case was also counted as wrongly-answered. The table then
said that *raising* the abstention floor *increased* over-answering, which
cannot happen. That impossibility is what exposed it - not a test, and not
review.

Corrected, the table is monotonic and decides something the pass count could
not. Two plateaus reach 48/54 with different mixes: the low one over-answers
three times and never wrongly refuses; the high one over-answers twice and
wrongly refuses three times. Over-answering is the dangerous direction here -
returning a weak match is how a RAG system confidently cites an irrelevant page -
so the higher plateau is better than its equal pass rate suggests.

**Rules.**
1. **A measurement that violates a monotonic expectation is a bug in the
   measurement** until proved otherwise. Raising a threshold cannot increase the
   failures that threshold suppresses.
2. Substring tests on human-readable status strings are a trap when one status
   is the negation of another and shares its spelling. `startswith`, an enum, or
   a structured field; never `in`.
3. Report the failure *mix*, not just the count. Two settings with the same pass
   rate can be differently safe, and which direction is safe is a property of the
   system rather than of the metric.

---

## L33 - Auditing the other constants, and finding nothing

L31 and L32 each found a threshold set against a 33-document corpus and stale on
the 91-document one, within an hour of each other. Two of anything suggests a
third, so `scripts/constant_sweep.py` sweeps any retrieval constant over both
corpora and prints pass counts, failure mixes, recall and nDCG side by side.

**Six constants swept. Four confirmed, none moved.**

    constant                          swept over        verdict
    candidate_k = 40                  20,40,80,120,200  keep
    mmr_lambda = 0.7                  0.5 - 1.0         keep, wide plateau
    rrf_k = 60                        10 - 200          keep, flat throughout
    coverage_weight = 0.45            0.35 - 0.65       keep, best recall
    min_vocabulary_for_answerability  0, 2000, 20000    keep, inactive by design
    min_relevance = 0.15              0.10 - 0.30       **moved to 0.19** (L32)

`candidate_k` is the interesting one. The intuition was that a 4.5x larger
corpus needs a deeper candidate pool, and the opposite is true: 20 scores better
than 40 on the external set (49/54, recall 0.9535) and worse on the primary one
(17/20, recall 0.7500), while 80 and above are worse on both. A deeper pool
gives the reranker and MMR more chances to promote the wrong document. 40 is the
balance and stays, on evidence rather than inertia.

`min_vocabulary_for_answerability` is inactive at both corpus sizes - 0 and 2000
give identical results because both corpora have more than 2,000 terms - and
20000 costs five external cases by disabling answerability entirely. It is a
guard for small corpora, correctly set, and the sweep confirms it is not
silently doing something else.

**The audit also found the ratchet that was missing.** Both CI floors were left
where they were after the pass rates improved, which lets a gain erode silently.
Primary 0.80 to 0.85 and external 0.85 to 0.86, each set so exactly one
regression is tolerated - the tightness the external floor had before the corpus
grew and diluted it.

**Rules.**
1. A negative audit is a result. Four constants confirmed on plateaus is worth
   the hour, because the alternative is suspecting all of them for ever.
2. **Ratchet a threshold after an improvement, in the same change.** L31 is
   about a floor left too high for a corpus that got harder; this is the same
   mistake pointing the other way, and it is the quieter of the two because
   nothing goes red.
3. Sweeping is cheap enough to be routine once the harness exists. The first
   sweep of `min_relevance` took an afternoon of hand-rolled scripts; the fifth
   took one command.

---

## L34 - The rule about permanent failures was written down and not implemented here

**Evidence.** Probing nine documentation hosts for a corpus source, the log
showed this three times per blocked host:

    ! [http] transport retry url=https://docs.python.org/... err=<urlopen error
      Tunnel connection failed: 403 Forbidden> attempt=1 wait=1.06
    ! [http] transport retry ... attempt=2 wait=2.43
    ! [http] transport retry ... attempt=3 wait=3.25

A proxy answering CONNECT with 403 is stating a rule, not reporting a fault, and
the rule will still be there in four seconds. Measured: ~7s per blocked host
before, **0.25s** after - and the cost was paid again by every code path that
touched the host.

The rule - *"a permanent failure is not a transient one; policy denials, blocked
egress and missing permissions do not pass, so detect them once and stop paying
for them"* - has been in this repository's protocol from early on. The HTTP
client was the one place it was not implemented. It was written down, agreed,
propagated to a user-level memory, and not applied to the code sitting directly
under it.

**What it had cost, indirectly.** `ooda preflight` pins `attempts=1` for its
probes, which is how the capability report stayed fast. That trade means a
genuine blip is reported as **blocked** - a false blocker, precisely what the
capability protocol exists to prevent. With denials failing fast on their own,
the probe now retries once and the report is unchanged at 2.07s.

**A second substring trap, in the code that reads the first one's output.** The
probe classified denials with `"403" in str(e)`, which also matches a URL
containing 403, a byte count of 403, and a port number - and it reports
"blocked" to a human deciding whether a source is reachable. Now a type,
`PolicyDeniedError`. This is L32's bug in a different file, found the same day,
which is the argument for treating "substring test on a status string" as a
smell rather than an incident.

**Rules.**
1. **A rule in the protocol is not a rule in the code.** When you write a
   learning down, grep for the places it should already apply. This one names
   its own targets: retry loops, backoff, circuit breakers.
2. A denial must not trip a circuit breaker built for flakiness. Conflating them
   makes "three consecutive transport failures" mean two different things, and
   the breaker's cooldown then hides a permanent condition behind a timer.
3. Narrowing an exception type is only safe if the new type is a subclass -
   `PolicyDeniedError` extends `TransportError`, so every existing handler still
   catches it. There is a test asserting exactly that.

---

## L35 - Auditing the code against the learnings, as L34 said to

L34's first rule was that writing a learning down is not applying it, and that a
good learning names its own targets. This is that grep, run over the rules that
name something greppable.

**"Substring test on a status string" (L32, L34): clean.** Two instances were
already fixed the same day; the sweep found no third. That closes it as an
incident rather than leaving it as a suspicion.

**"Bound the expensive operation" (L5): one unbounded loop, latent.**
`TokenBucket.acquire` waits in a `while True` with no wall-clock bound, which is
correct - a caller asking to be rate limited is asking to wait - but only
because the loop can end. `_tokens` is capped at `capacity`, so a request larger
than the capacity is never satisfiable and the caller sleeps in five-second
steps for ever, silently. Reproduced: `TokenBucket(rate_per_sec=2).acquire(5)`
does not return.

Latent today, because the only caller asks for one token from a bucket of at
least one. It was a hang waiting for the first weighted request - a
"cost this endpoint three tokens" change is the obvious next edit to a rate
limiter. Now refused with a message that says why, since an unsatisfiable
request is a caller bug rather than a long wait.

**"An operation that can silently do nothing" (L13): one asymmetry, mine.**
`_invalidate_idf` dropped the IDF table on every corpus write. When
`surface_vocabulary` was added two cycles ago it went into the same table, over
the same input, and was not added to that drop. Both validate against the corpus
signature so neither is actually stale - but the asymmetry is the trap: the next
reader sees "the derived cache is cleared here" and does not check whether
theirs is in the list. Renamed `_invalidate_derived` with the keys as a named
constant, and the test asserts against the `meta` table rather than the
constant, so adding a cache without listing it fails.

**A test that detects a hang must not detect it by hanging.** The first version
of the token-bucket test called `acquire` directly: with the guard removed the
test run hung until the CI job timed out. Moved into a thread with a two-second
join, it now fails in 2.1s. A slow confusing failure in place of a fast clear
one is worth fixing even when both are technically red.

**Rules.**
1. A rule that names greppable targets should be grepped for on the day it is
   written. Two of these three findings are older than the rule that found them.
2. **Adding a second cache over an input means revisiting everything that
   invalidates the first.** This is L20's shape for the fourth time in this
   codebase, and the first time I introduced it myself.
3. A `while True` needs a written argument for why it terminates, in the
   docstring, next to the loop. Writing that argument is what exposed this one.

---

## L36 - The Observe phase acts, the docstring denied it, and I nearly deleted a live rule over it

**Evidence.** `OodaLoop.observe` began: *"Gather evidence. Nothing is changed
here except the journal."* The next statement is `self.pipeline.run(...)`, which
ingests documents, writes chunks, refits the embedder and writes vectors. In a
loop whose entire structure is the separation of looking from acting, that is
not a small inaccuracy.

The consequence is real and was measured. Three chunks were written without
vectors; by the time Decide ran, `embedding_coverage` read **1.0** and the
decided action was `run_eval`. With **no connectors at all**, the same thing:
three missing vectors became zero during Observe. So the policy rules that look
like they govern ingestion do not - Observe has already brought about the
situation Decide is shown.

**The mistake I nearly made.** On that evidence I concluded the priority-100
`embed_missing` rule was unreachable and was ready to delete it as dead policy.
It is not dead. It fires when a connector *raises*, leaving chunks without
vectors that the ingest never got to - which is exactly the case a repair rule
is for. I had tested four scenarios, all of them healthy, and generalised from
them.

Deleting it would have removed a safety rule that fires only when something has
already gone wrong, which is the worst possible thing to prove absent by testing
the happy path. Both halves are now pinned: `embed_missing` must appear when a
connector raises, and must not appear when the loop is healthy. Deleting the
rule fails the first; a threshold that fires on a healthy corpus fails the
second and the two convergence tests with it.

**Rules.**
1. **A rule that only fires when something is broken cannot be shown dead by
   exercising the paths where nothing is broken.** Enumerate the conditions from
   the rule's own text and construct each one, rather than sampling scenarios
   and generalising.
2. When a docstring states an invariant, check the code under it before
   trusting the invariant elsewhere - this one had been read and believed while
   reasoning about which rules could fire.
3. "Observe changes nothing" is worth wanting but was never true here, and the
   honest repair was to say what Observe does and why, not to restructure the
   loop to match the sentence. For this system the sources' current contents
   *are* the observation, and there is no way to see them without fetching.

---

## L37 - The citation verifier was rewriting the code it was quoting

**Evidence.** Provenance is this project's second non-negotiable: citations are
verified against retrieved chunks rather than generated. The verifier that
enforces it recognised markers with `\[(\d{1,2})\]`, which is also the syntax of
an array subscript - on a corpus that is half source code.

Three failures, all demonstrated:

    text in                                    text out
    "sys.argv[1] reads the flag."              counted as a citation of chunk 1
    "The loop reads chunks[7] ... [1]."        "The loop reads chunks ... [1]."
    "values[12] = compute(x)"  (in a fence)    "values = compute(x)"
    "the crawl [999999999999]"                 unchanged, shipped as evidence

The middle two are the serious ones. An answer that presents `values = compute(x)`
as a quotation from a document containing `values[12] = compute(x)` has altered
its evidence - and it did so *because* of the code whose comment reads "a marker
pointing at nothing is worse than no marker: it looks like evidence. Remove it
from the text rather than shipping it."

The first inflates grounding: a sentence quoting code read as cited when it
cited nothing. The last is that same comment failing on its own terms - a marker
too long for the two-digit cap was neither recognised nor removed, so the only
markers that shipped unexamined were the ones furthest from pointing at
anything.

**The fix has two halves, and one is not enough.** A lookbehind separates a
marker from a subscript: a real marker follows whitespace or punctuation, a
subscript follows an identifier or a closing bracket. That handles `argv[1]` and
`chunks[7]`. It cannot handle `x = [12]`, a list literal that follows a space
exactly like a marker - so fenced code is skipped outright, where quoted source
lives and no marker belongs. Digits are unbounded now, so an out-of-range marker
is detected and stripped rather than passing through.

Costs nothing: 48/54 and 18/20, citation coverage 1.0 on both, unchanged.

**Rules.**
1. **A syntax borrowed from the corpus will collide with the corpus.** Square
   brackets round digits are citation markers in prose and subscripts in code,
   and this system indexes both. The collision was in the design, not in an
   edge case.
2. Text that is *quoted* must be inviolable to any cleaning step. A verifier
   that edits evidence to make it verifiable has inverted its own purpose.
3. Read a bound in a pattern as a claim about the data. `\d{1,2}` claims there
   are never more than 99 citations *and* that anything longer is not a marker -
   the second half was silently false, and false in the direction of shipping
   the bad case.

---

## L38 - Attacking the redactor: five leaks closed, two "improvements" reverted on measurement

**Evidence.** Secrets are redacted at the connector boundary - non-negotiable 5,
because an index is a file that gets copied around. Attacking `redact_secrets`
with eleven credential shapes, five got through:

    Authorization: Basic YWRtaW46aHVudGVyMg==            leaked
    https://user:s3cr3tpass@github.com/org/repo.git      leaked
    postgres://admin:hunter2hunter@db:5432/app           leaked
    aws_secret_access_key = wJalrXUtnFEMI/K7MDENG...     leaked
    eyJhbGciOi....eyJzdWIiOiIxIn0.abcdefgh               leaked
    password: hunter2                                    leaked

The URL one matters most for this system specifically: the GitHub connector
handles clone URLs and every chunk stores a provenance URI, so a credential
there lands in the index **and** in every citation quoting that chunk. The user
is kept and only the password replaced - the user is provenance, the password is
the secret.

**Two attempted fixes were reverted, on evidence.** Redaction runs over every
ingested document, source code included, so it has two failure directions:

    change                              secrets caught   source files rewritten
    baseline                            6 of 11          3 of 51
    keyword allowed a suffix            +aws             14 of 51
    value floor lowered 8 -> 4          +short password  (with above) 14 of 51
    both reverted, specific patterns    11 of 11         4 of 51

The suffix form catches `aws_secret_access_key = ...` and also
`unit_tokens = estimate_tokens(...)`, `max_tokens=self.max_tokens` and
`def _idf(self, token: str)`. Excluding code punctuation from the value does not
help, because the value simply ends before the bracket. Telling an identifier
from a credential generically is a losing game, so the keyword rule stays narrow
and `aws_secret_access_key` is named specifically, where precision costs nothing.

`password: hunter2` is still not caught: seven characters against an eight
character floor, and lowering the floor catches `token: str)`. That is now a
**test asserting the leak**, so a future widening has to confront the trade
rather than discover it.

The remaining false positives are 4 of 91 corpus files and 4 of 51 source files
against a baseline of 3 and 3. The extra corpus file is `pyjwt.md`, where the
JWT rule correctly fires on a JWT in the project's own documentation - a
redactor cannot tell an example credential from a live one and should not try.

**Rules.**
1. **A redactor has two failure directions and they are not symmetric, but
   neither is free.** "False positives are cheap" is true right up until the
   thing being rewritten is the corpus the system exists to search.
2. Prefer a specific pattern to a widened general one. Every widening of the
   keyword rule bought one credential shape and cost several files.
3. **Write a test for the leak you decided not to close.** An accepted cost that
   is not written down is indistinguishable from an oversight, and the next
   person to widen the floor will not know it was ever considered.

---

## L39 - Verifying the non-negotiables, and two claims that were true but unchecked

The five non-negotiables in CLAUDE.md are the project's own statement of what
must not break. Four had been attacked by this point; this closes the other two
and finds that both hold - with an untested path each.

**Zero required runtime dependencies (1): holds.** Three third-party imports in
51 modules - numpy twice, anthropic once - all inside functions, and every
module imports on a bare interpreter.

CI enforces this by having no install step, and its comment calls a green build
"evidence of that claim". It is evidence for the paths the suite exercises. A
module no test imports could carry a top-level `import numpy` and CI would stay
green: `ingest/youtube.py` is such a module, and adding one there was invisible
until a test walked the package rather than sampling it. Two tests now do -
import every module, and refuse any third-party import at module scope. Both
name the file and line.

**Degrade, don't die, and never silently shrink the corpus (4): holds.** The
dangerous shape is a *partial* failure, because the documents an interrupted
listing never reached look exactly like documents deleted upstream. Measured:

    scenario                      failed  removed  documents  pruned
    yields 3 of 8, then raises    1       0        8 -> 8     0
    raises immediately            1       0        8 -> 8     0
    succeeds, returns nothing     0       8        8 -> 8     0 (guard refused)

The first two are correct because `ingest/base.py` computes removals only when
the run completed. The third is the one with no upstream defence at all - a
source that succeeds and returns nothing is indistinguishable from a source
whose contents were deleted - and the 25% fraction guard is the only thing
between an expired token and an empty index. It refused at 100% and said so.

Only the *total* failure had a test. The partial one, which is the realistic
shape, did not; nor did the silent-empty case end to end. All three are pinned
now, and each mutation - removals computed on a failed run, the fraction guard
disabled, the error cleared before reporting - fails exactly one of them.

**Rules.**
1. **"A green build is evidence of that claim" is worth reading twice.** It is
   evidence for whatever the build exercises, and a claim about *every* module
   needs something that walks every module.
2. When a guard has no upstream defence, test it at the extreme rather than near
   the threshold. The silent-empty case sends 100% of a source to the guard, and
   that is the number worth asserting.
3. A property that holds by construction still needs a test, or the next
   refactor removes the construction. `removed = ... if completed else []` is one
   line, and it is the whole of "a failure never shrinks the corpus".

---

## L40 - Sweeping the docstrings for claims, and finding one the chunker did not keep

Three separate defects this session started from a docstring asserting something
the code did not do (L36, L37, L39). Rather than keep stumbling on them, this is
the sweep: grep the source for absolute claims - never, always, cannot, only -
and check the ones that are load-bearing and cheap to test.

Most held, and two were already tested: "never silently replay a POST" has
`test_post_is_not_replayed_across_a_redirect`, and the prune guard's promises
have theirs.

**One did not.** `_pack`'s docstring says *"Overlap is applied in whole units, so
a chunk never starts mid-sentence."* True of sentences and silent about code
fences, which the chunker does not model at all. Measured on the 91-document
corpus: **20 of 1,148 chunks carry an odd number of fence markers** - a long
fenced block lands in two chunks, the first ending inside the fence and the
second opening with the orphaned tail and a closing marker that opens nothing.

It reaches the user, because the extractive generator quotes chunk text
verbatim: an unclosed fence renders everything after it as code, and a stray
closing one renders the prose before it as code. Balancing the markers fixes it
without moving a boundary, so retrieval is untouched - 48/54, recall 0.9186,
nDCG 0.7965, identical.

**The test I wrote for it could not fail in the way that mattered.** Which end
is missing decides where the marker goes, and my assertion only checked that the
count came out even. Appending to a chunk that *opens* with a dangling marker
also makes the count even - and wraps the prose in a code block. The mutation
passed. The assertion now checks the prose ends up outside the fence, which is
the actual claim.

**Rules.**
1. A docstring claim is scoped by the vocabulary it uses. "Never starts
   mid-sentence" is true and says nothing about a document whose structure is
   not sentences - the gap was in what the sentence did not mention.
2. **When a repair has two directions, an assertion about the symptom cannot
   tell them apart.** Balancing a count is satisfied by both the right fix and
   the wrong one; only asserting where the content ends up separates them.
3. Measure the claim on the corpus, not on a fixture. Three fixture cases passed
   while 20 real chunks were broken, and the corpus test is what regresses if
   the packing changes.

---

## L41 - The harness checked the corpus for leaks and never checked the goldens

**Evidence.** Every number in this file comes from the eval harness, so it is
the one component whose defects are invisible - a wrong measurement does not
look wrong, it looks like a result. Attacking it turned up one gap, in the
place the harness was already thinking hardest.

`Golden.expect_sources` entries are **substrings**, matched against a document's
uri and title. That is deliberate and documented: `"pluggy"` rather than a full
path. It also means an expectation can be satisfied by documents it was never
meant to name, and every uri in a filesystem corpus shares a directory:

    "pypi"    matches 91 of 91 documents
    "claude"  matches 91 of 91
    "s"       matches 91 of 91

A golden expecting any of those passes with recall 1.0 whatever retrieval
returns. That is a test that cannot fail, inside the instrument every other
measurement is taken with - and this session has spent a lot of effort on tests
that cannot fail in ordinary code, while the harness went unexamined.

The mirror case is quieter: an expectation matching *nothing* makes a case that
can never pass, which reads for ever as a retrieval failure rather than as a
broken golden.

**The current golden set is clean** - all 54 expectations match exactly one
document each, checked before writing any code, so nothing measured this session
is affected. The guard is for the next golden, and there is a test that runs it
against the real set so a too-broad one surfaces where it is written.

Contamination detection already asks *does the corpus give the answer away*.
This asks the other half - *does the expectation pick anything out* - and both
are reported, never silently corrected. Rewriting a golden because it looks too
broad is how an eval starts agreeing with the system.

**The same check on the answer side found a live one.** `expect_answer_contains`
is also a substring, searched in the generated answer - which is assembled from
the corpus, so a term the corpus repeats will appear in almost any answer:

    'sha'          appears in 31 of 81 primary documents (38%)
    'fingerprint'  14 of 81 (17%)
    '9309'          5 of 81 (6%)
    'commit sha'    5 of 81 (6%)
    'Mozilla'       4 of 91 external (4%)

`"sha"` is satisfied by "shared", "shape" and "share" as readily as by a commit
sha, in a corpus where more than a third of documents contain one of them. The
golden using it now says `"commit sha"` - which is what the connector actually
documents, since an unchanged `head_sha` is what skips the file walk. That is
making a golden **stricter**, which is the opposite of the failure mode where an
eval is loosened until it agrees; the case still passes at 18/20.

**Rules.**
1. **Attack the measuring instrument, and attack it early.** A defect there does
   not produce a failure, it produces a number, and every conclusion downstream
   inherits it. This one was reached after forty learnings about everything else.
2. Substring matching is convenient at the point of writing and unbounded at the
   point of evaluation. If a config accepts substrings, something has to check
   what they actually match against real data.
3. A validity check has two directions here too - too broad and too narrow - and
   the too-narrow one is worse for being plausible: an impossible golden looks
   exactly like a system that keeps failing one case.

---

## L42 - "Not deterministic across processes", and the correction that mattered

**Evidence.** ADR 0001 calls this pipeline deterministic, so the claim was
measured: run the same three queries over the same index in four subprocesses
with `PYTHONHASHSEED` set to 0, 1, 42 and 999, and digest the whole result.

Four different digests. The first reading was "end-to-end retrieval is not
deterministic across processes", which is what the digests say and is wrong
about why.

Comparing the components rather than the digest: the chunk ids matched, the
order matched, coverage, relevance, the abstention decision and
`best_relevance` all matched to fifteen digits. Only the raw scores differed,
by a **constant** 7.185e-09 across every result. A constant offset is not what
hash-order non-determinism looks like.

**The decisive test was running the same seed twice.** Same delta. It is
`time.time()` in the recency factor: a document's age is recomputed against a
clock that moved between the two runs. The embedder was never implicated - it
uses BLAKE2 rather than Python's `hash()`, and its vectors, idf state and
fingerprint are byte-identical across seeds.

**What changed as a result.** The clock is now injectable. With it frozen, the
whole pipeline is bit-reproducible across hash seeds - four seeds, one digest -
and an eval can assert a score exactly instead of only a ranking. Against the
wall clock it cannot: two runs of the same eval differ in the last decimal, so
a real score regression is indistinguishable from the seconds it took to get
there.

The fixture for the clock test needed fixing too. `_doc` sets no `updated_at`,
and the recency factor only applies to a chunk that carries an age - with none
it returns a constant and the clock cannot matter. The test passed for the wrong
reason until the documents were given a date.

**Rules.**
1. **A digest tells you *that* something differs, never *what*.** Comparing the
   components took one extra run and turned a wrong conclusion into a correct
   one. Digest to detect, decompose to diagnose.
2. When something varies across processes, **run it twice in the same process
   before blaming the process.** Hash seeds are the interesting explanation and
   the clock is the boring one; the boring one was right.
3. A constant delta across every element is a signal in itself. Hash-order
   effects are erratic; a fixed offset points at something shared, and here it
   pointed straight at the clock.

---

## L43 - A scoring component the regression gate cannot see

**Evidence.** Having made the recency clock injectable (L42), the obvious next
move was to freeze it in the eval so the gate stopped measuring the calendar.
Measured first, and the measurement said not to bother - then said something
more interesting.

    corpus    documents with a date   age spread
    external  91 of 91                0.00 days
    primary   81 of 81                0.91 days

Both corpora are written in one pass, so their documents share a timestamp, and
a factor identical across every candidate cannot reorder anything. Confirmed
three ways: recency switched off entirely leaves external at 48/54 and primary
at 18/20 with every metric unchanged to four decimals, and moving the clock five
years forward changes nothing at all.

So the eval was never time-dependent and the fix was unnecessary. What the
measurement did establish is that **`recency_weight = 0.08` is carried by unit
tests alone**: 8% of the reranker's score, on by default, and provably invisible
to both regression gates. A regression in it would not show up anywhere the
project looks.

Recorded rather than removed. The factor is right for a corpus of mixed ages -
a crawl, a chat archive, a repository's commit history - and those are simply
not what the gates run on. What it needed was tests that actually fire: a
fresher document must outrank an identical stale one, that ordering must
disappear when the weight is zero (or the first test proves nothing about
recency), and an undated document must read as neither fresh nor stale rather
than as infinitely old, which would bury every document from a source that
carries no timestamps.

**Then the same question, asked of every weight.** Zeroing each in turn:

    weight              external              primary
    coverage_weight     49/54  moves          16/20  moves
    phrase_weight       48/54  moves          17/20  moves
    position_weight     48/54  moves          18/20  moves
    authority_weight    48/54  NO EFFECT      18/20  NO EFFECT
    recency_weight      48/54  NO EFFECT      18/20  NO EFFECT

Authority is inert for the same structural reason: each corpus is a single
filesystem source at authority 1.0, so the factor is constant across every
candidate. Between them, **0.20 of the reranker's weight - a fifth of the
score - is invisible to both regression gates.**

Authority had no test at all. It now has three: a trusted source must outrank an
identical untrusted one, that ordering must vanish with the weight at zero, and
the value must be clamped - a connector is free to report any number, and
without a ceiling a source claiming authority 1000 outranks every relevant
document from every other source, which is relevance ceasing to matter.

**Rules.**
1. **Measure the effect before building the fix**, even when the fix is
   obviously correct. This one was correct, unnecessary, and the measurement
   that showed it unnecessary is the only reason the real gap was found.
2. **Ask the question of every sibling, not just the one you tripped over.**
   Recency was found by accident; authority was found by spending five more
   minutes asking the same question of the other four weights, and it was the
   one with no tests at all.
3. A component that no gate can see is not tested by the gate being green.
   Uniform inputs make a weighted factor a constant, and a constant multiplied
   through every candidate is indistinguishable from the feature being absent.
4. When a test shows a component working, add the one that shows the component
   *causing* it. "The fresher document ranked first" is satisfied by insertion
   order; it means something only alongside "and it does not, with the weight
   at zero".

---

## L44 - The connectors knew the real dates and had nowhere to put them

**Evidence.** L43 found the recency factor inert on both eval corpora, because
every document in a run shares a timestamp. Chasing *why* they share one:

`Document.from_raw` set `updated_at = raw.fetched_at`, for every connector,
unconditionally. `fetched_at` is when we asked. So a GitHub issue last touched
in January, fetched a moment ago, was scored as **brand new** - measured,
recency 0.99999998 - and every document ingested in the same run got the same
date, which is exactly the uniformity that made the factor a constant.

The connectors were not missing the information. GitHub's API returns
`"updated_at": "2026-01-02T00:00:00Z"`, the connector reads it and puts it in
metadata, where nothing scores it. It had nowhere else to go.

`RawDocument.source_updated_at` is that place: what the source says about its own
content, distinct from when we fetched it, and **None when the source does not
say** - which is a different claim from "it changed now". Measured end to end
through the connector's real output: the same issue now scores recency 0.520.

**A false claim I made along the way, and the correction.** Getting here, I found
that `float(chunk.metadata.get("updated_at") or 0.0)` raises ValueError on the
ISO string the connector stores, and wrote that retrieving any GitHub issue
crashes the reranker. **It does not.** The store overwrites a chunk's
`updated_at` with the document's, which is always a float, so the reranker never
meets the string. My demonstration built the chunk by hand - it showed what the
function does, not what the system does, which is the mistake L36 records about
concluding from constructed scenarios. The defensive parse stayed, correctly
labelled as a guard rather than a repair.

**Rules.**
1. **When a value is uniform, ask where it comes from before concluding the
   feature is useless.** The uniformity was the symptom; the cause was a field
   assignment three modules away, and the fix makes the feature work rather than
   documenting it as unmeasurable.
2. "We fetched this at T" and "the source changed this at T" are different
   facts. Storing one in the other's field is provenance that lies, and it lies
   in the direction that makes everything look fresh.
3. A hand-built input proves what a function does. Only an input the system
   actually produces proves what the system does - and I have now made this
   mistake in both directions in one session: concluding a rule was dead from
   scenarios that were too narrow (L36), and concluding a crash was live from a
   scenario the pipeline cannot produce.

---

## L45 - GitHub issues were one of seven, and there were two parsers

**Evidence.** L44 wired `source_updated_at` for GitHub *issues*. L43's own rule
says to ask the question of every sibling before closing a cycle, so I did.
Six more sites read a real date from their source and filed it in metadata,
where nothing scores it:

| document kind | field the source states |
| --- | --- |
| GitHub repo | `pushed_at` |
| GitHub commit | `commit.author.date` |
| GitHub release | `published_at` |
| web page | `<time datetime>`, `article:published_time`, `dc.date` |
| YouTube video | manifest `published` |
| chat session | the timestamp of its **last** turn |

So the fix I had just measured as working covered one seventh of the surface.
The recency factor stayed a constant for six of seven document kinds, and no
test would have said so.

**Two parsers, quietly disagreeing.** Wiring them turned up a second problem.
`rerank._as_timestamp` parsed ISO dates one way; `github._iso_to_timestamp`,
which I had added in the previous cycle, parsed them another. They differed on
naive timestamps: the reranker's `datetime.fromisoformat(text).timestamp()`
reads a stamp with no offset as **local time**, the connector's as UTC. Under
`TZ=Asia/Kolkata` that is a five-and-a-half hour disagreement about the same
string, and nothing errors - one stage simply sees a date the other cannot.
This is L24 (tokenizing that differed between indexing and querying) in a new
field. Both now delegate to one `util.dates.to_timestamp`, and a test asserts
that every shape the parser accepts is a date the scorer can read.

**Measured.** Primary 18/20, external 48/54 - **unchanged**, before and after.
A correct fix the evals cannot measure is a gap in the evals, not evidence of
value, so it is recorded as such rather than claimed as an improvement.

**Correction, made in the next cycle: the reason I first gave for "unchanged"
was wrong.** I wrote that both eval corpora are built by the filesystem
connector, "which has no source date, so neither corpus can see this change at
all." It has one. `FilesystemConnector` was passing `path.stat().st_mtime` as
`fetched_at`, and `Document.from_raw` falls back to `fetched_at`, so every
document in both corpora already carried its own per-file date. Measured on the
built indexes:

| corpus | docs | distinct dates | span | recency factor |
| --- | --- | --- | --- | --- |
| primary | 96 | 94 | 0.94 days | 0.994773 - 0.999980 |
| external | 91 | 34 | 0.030 days | 0.999182 - 0.999348 |

So the factor is **saturated, not constant** - a distinction that matters
because they have different causes and only one of them is a bug. At
`recency_weight = 0.08` the whole spread is worth 4.2e-04 of score on the
primary corpus, against a coverage term weighted 0.45 over [0, 1]: about a
thousandth of the discriminating range, enough to break an exact tie and
nothing else.

The cause is not the connector, it is the corpora. Both are files whose ages
span under a day - the repository's entire git history is 0.9 days long (`git
log` over 187 files: 28 distinct commit dates, 0.9-day span), and the external
pages were scraped into files in one run. There is no age signal in either
corpus to find. Saying "the connector has no date" pointed at a fixable bug;
the truth points at a corpus that cannot exercise the feature, which is the
L28 rule - suspect the ruler before the thing.

**The eighth sibling.** Checking that claim turned up the site I had missed
while enumerating the family. `fetched_at=path.stat().st_mtime` is not a
missing date, it is a date in the wrong field: it makes `Document.created_at`,
which is `fetched_at`, claim the file was ingested at its mtime. `updated_at`
came out right only because two errors cancelled - the wrong field, and a
fallback that reads it. Now `source_updated_at=stat.st_mtime` and `fetched_at`
is the read time, asserted with `os.utime` against a 2024 date so the
expectation is derived rather than observed. Both evals: still 18/20 and 48/54,
because `updated_at` is the same number by either route.

Thirteen mutations were applied and all thirteen were caught - each connector
dropping its date, chat dating a session by its first turn instead of its last,
the parser reading naive stamps as local time, an offset parsed away instead of
applied, a boolean flag counting as a date, and the reranker going back to
parsing dates its own way.

**Rules.**
1. **A fix applied to one member of a family is a survey, not a fix.** Before
   closing the cycle, enumerate the siblings and check each. Seven sites, one
   wired: the measurement that said "it works" was true and almost entirely
   beside the point.
2. **When two stages parse the same field, they must share the parser, not
   agree by inspection.** A second copy is a divergence that has not happened
   yet. The divergence here was invisible in UTC and five hours wide elsewhere.
3. **"Unchanged" is a result worth reporting with its reason.** Empty is always
   blocked, filtered, deduplicated or genuinely absent; unchanged is always
   ineffective, already-correct or *unmeasurable by this eval*. Saying which
   costs a sentence and stops the next cycle re-deriving it.
4. **And the reason has to be checked, not assumed.** I gave one above, in the
   same breath as writing rule 3, and it was wrong - a plausible mechanism I
   never measured. Checking it took one query against the built index and
   turned up both the real cause and the sibling I had missed. An explanation
   for a null result is a claim like any other.
5. **Saturated is not constant.** A factor pinned at 0.999 across a corpus and
   a factor that is literally one value look identical in a pass rate and have
   different fixes: one needs a corpus with range, the other needs code. Report
   the spread, not the impression.

---

## L46 - The ranker and the abstention gate were sharing one knob

**Observation.** Six external cases fail. Tracing the two most diagnosable ones
showed they have the *same* cause pulling in opposite directions.

"How should a password be stored so the stored form cannot be reversed?" is not
a retrieval failure at all - `bcrypt.md` comes back at **rank 0**, which is the
best answer this corpus contains. Its `rerank_relevance` is 0.1168, under the
0.19 floor, so the system abstains. The query has five content terms and the
chunk matches one of them - but that one is `password`, IDF 4.60, and the other
four are question scaffolding.

"How does one Python library let other packages hook into it?" fails the other
way: every PyPI page contains `python`, `library` and `packages`, so coverage is
high for all of them (hypothesis 0.626, httpx 0.588) and the one discriminating
term, `hook`, cannot lift `pluggy` above them.

**Hypothesis, and it was wrong.** Sharpen `coverage_power` so rare terms
dominate. Measured on the external corpus:

| power | pass | recall@8 | MRR | nDCG@8 |
| --- | --- | --- | --- | --- |
| 1.0 | 48/54 | 0.9186 | 0.7729 | 0.7965 |
| 2.0 | 47/54 | 0.9186 | 0.7502 | 0.7791 |
| 2.5 | 47/54 | **0.9419** | 0.7336 | 0.7750 |
| 3.0 | 44/54 | 0.9070 | 0.7223 | 0.7588 |
| 4.0 | 43/54 | 0.9070 | 0.7083 | 0.7526 |

Monotonically worse on pass rate. But **recall@8 peaks at 2.5**, above every
other row - retrieval got better while the pass rate got worse, which is not
something a single quality knob should be able to do.

**The cause.** `relevance = (0.6 * coverage + 0.4 * phrase) * answerability`,
and `coverage` is the power-weighted number. Ranking and the abstention gate
read the same quantity, so sharpening for ranking silently rescales what the
fixed 0.19 floor is comparing against. One knob, two jobs, opposite directions.

**Decoupled and measured.** `gate_coverage_power` lets the gate keep its own
exponent:

| rank power | gate shared | gate at 1.0 | recall@8 |
| --- | --- | --- | --- |
| 1.0 | 48/54 | 48/54 | 0.9186 |
| 2.0 | 47/54 | 48/54 | 0.9186 |
| 2.5 | 47/54 | **49/54** | 0.9419 |
| 3.0 | 44/54 | 47/54 | 0.9070 |

The recovery *grows* with the sharpening - +1, +2, +3 - which is the mechanism
showing itself rather than one lucky cell in a grid.

**What did not change: the defaults.** 49/54 is the best external number this
project has measured, and it is not shipped. Rank power 2.5 costs 0.039 external
MRR and 0.031 primary recall (0.8125 -> 0.7812), and on the primary corpus
decoupling changes nothing at any power. Tuning a global default on one corpus's
pass rate against another corpus's recall is the overfit already recorded twice
here. The control ships available and off, with the table on it.

**Rules.**
1. **When two consumers read one number, sharpening it for one recalibrates the
   other.** A ranking signal reused as a gate threshold is the common case: the
   ranking is relative and the gate is absolute, so any monotone rescaling is
   free for the first and a silent retune for the second.
2. **Two metrics moving in opposite directions is a structural finding, not
   noise to average away.** Recall up and pass rate down was the whole diagnosis;
   a single headline number would have hidden it and the sweep would have ended
   at "1.0 is best".
3. **A measured improvement is not automatically a shipped one.** State what it
   costs on the corpus it was not tuned on, then decide.

---

## L47 - Non-negotiable 5 had three holes, and I found them by checking it

**How it surfaced.** Not from a bug report. Between cycles I re-ran the five
non-negotiables as checks rather than reading them, and one of them was a
one-line grep:

```
$ grep -c "redact_secrets" src/oodarag/ingest/*.py
chat.py:3  filesystem.py:2  github.py:6  web.py:2  youtube.py:0
```

**Hole 1: a connector that never called it.** The YouTube connector redacts
nothing. Its text comes from a captions file, a *curated notes file* - an
arbitrary local markdown document - and a manifest summary. A notes file is
exactly where a pasted key lives.

**Hole 2: titles, missed by every connector.** All seven redact the body and
none redact the title, and a title is not decoration: `chunking._context_header`
puts it at the front of `Chunk.indexed_text`, so it is embedded, indexed and
searchable. The chat connector builds its title from the user's own first
message; a commit title is a commit's subject line. Both are ordinary places for
a token to sit.

**Hole 3: metadata, and it explains the wording of the rule.** The web connector
does `text=redact_secrets(...)` and then, three lines down,
`"description": ... or summarize(page.text, 200)` - `page.text`, the copy it did
*not* redact. Reproduced: a credential on a crawled page reached
`metadata["description"]` in full while the body beside it was clean. Nothing
embeds a description. The rule says "before text can reach an index file", not
"before it can be embedded", and this is the case that distinguishes them.

**The fix is structural, not another convention.** `RawDocument.__post_init__`
redacts `text`, `title`, `uri` and every string inside `metadata`, recursively.
`RawDocument` is the one type every connector must construct, so a connector
written next year inherits the guarantee instead of having to remember it - and
what was being kept by seven files each remembering is now kept by one.

**Measured.** Both evals unchanged (18/20, 48/54). The double pass - connectors
still redact, and `redact_secrets` is idempotent for every pattern it carries -
costs 277 ms over 144 documents and 1.05 MiB, against an 8.3 s primary index.
No false positives: a commit sha, a content hash, a canonical URL, a dotted
path and an underscored path all come through untouched, checked explicitly
because a redactor loose on structured data would break provenance silently.

**Mutation testing found two gaps in my own tests, then a third thing.** Eight
mutations, six caught immediately. The two survivors: nothing asserted that a
secret *inside a list* was redacted (`headings` is a list lifted off the page),
and my false-positive fixture had no value containing an underscore, so a
redactor that mangled underscores passed. Both are now covered.

The third: the tuple branch survived every mutation because no connector writes
a tuple. Deleting it would have left a tuple falling through to "return
unchanged" - a leak. Preserving tuple-ness would have been a fiction, since
metadata is JSON in the store and a tuple round-trips as a list. It now
redacts and returns a list, with the reason in a comment, and the test asserts
the type change on purpose.

**Rules.**
1. **Re-run your non-negotiables as checks, not as reading.** Five stated
   guarantees, one of them false in three places, and the cheapest check was a
   `grep -c`. A principle nobody has executed lately is a hope.
2. **A guarantee kept by convention is kept by the least careful caller.**
   Move it to the type every caller must construct, and it holds for callers
   who have not been written yet.
3. **Ask what the rule's own words range over.** "Before it reaches an index
   file" covers metadata; "before it is embedded" does not, and the code had
   been written to the second reading of a rule that says the first (L27 -
   read a claim for what it does not range over).
4. **A branch that survives every mutation is untested, and the fix is not
   always a test.** Ask first whether the branch should exist. Here neither
   "delete" nor "test as written" was right: the branch was needed for safety
   and wrong in what it preserved.

---

## L48 - IDF measures rarity in the corpus, and the question is in a different register

**The case.** "How should a password be stored so the stored form cannot be
reversed?" is one of the six external failures, and it is not a retrieval
failure: `bcrypt.md` comes back at **rank 0**. The abstention floor throws it
away. The arithmetic reproduces exactly:

| query stem | IDF | documents containing it (of 91) |
| --- | --- | --- |
| revers | 5.79 | ~0 |
| cannot | 4.79 | ~1 |
| password | **4.60** | ~1 |
| store | 4.37 | ~1 |
| form | 4.07 | ~2 |

`4.5999 / 23.6204 = 0.1947` coverage, `0.6 x 0.1947 = 0.1168` relevance, against
a 0.19 floor. The one term that identifies the answer carries **19.5%** of the
query's weight; four scaffolding words carry 80.5%.

**Why IDF cannot help here.** The coverage factor weights by IDF on the stated
theory that "matching a term that appears everywhere is not evidence, matching a
rare one is". That theory needs terms that appear everywhere. These do not
appear everywhere - they appear almost nowhere. A PyPI project page is not
written in the register a question is written in, so `cannot`, `reversed`, `my`,
`let` and `lose` are *rare in this corpus* and score above `password`, `hook`
and `schema`.

**Measured, not asserted** (`scripts/idf_discrimination.py`). Over the 40
goldens with an expected source and at least one discriminating query term -
where "discriminating" is derived from the corpus as "appears in the expected
document and in at most 20% of documents" - IDF's top-ranked query term is the
discriminating one in **28 of 40 (70%)**. The twelve failures are all register
mismatches:

```
let    (4.30) beats hook           <- the pluggy eval failure
revers (5.79) beats password       <- the bcrypt eval failure
my     (4.69) beats execut, measur
lose   (6.64) beats databas, schema
program(4.37) beats schema
```

**Two of the six external eval failures are in that list.** The mechanism is
confirmed end to end rather than hypothesised.

**It also explains L46.** Sharpening `coverage_power` made the pass rate
monotonically worse (48 -> 43), which was recorded there as a fact without a
cause. This is the cause: if the IDF ordering is right only 70% of the time,
raising the exponent amplifies a partly *anti*-informative ordering. Two
findings from different cycles turn out to be one.

**A fix derived from the mechanism, and falsified**
(`scripts/idf_ceiling_sweep.py`). If no single rare-in-corpus word should
dominate a query, clipping the weight should recover the cases:

| ceiling | none | 6.0 | 5.5 | 5.0 | 4.5 | 4.0 | 3.5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pass | 48/54 | 48 | 48 | 48 | 48 | 47 | 45 |

Flat, then worse. Clipping compresses *magnitudes* and leaves the *ordering*
alone, and the ordering is the defect: capped at 5.0, `revers` is 5.0 against
`password` at 4.60 - still the wrong way round. Nothing was shipped.

**Is the mismatch just small N? Untestable by subsampling, and the reason is
worth recording.** If "cannot" scores as rare only because it appears in 1 of 91
pages, then at larger N its document frequency should rise, its IDF fall, and
the ranking correct itself with no code change. That is cheap to check by
subsampling the corpus we have - except it is not.

Measured both ways, and neither works:

* **Variable question set.** Rate falls 100% (n=20) to 72.5% (n=91) - but each
  row scores a *different* set of goldens, because only questions whose target
  document survived the subsample can be counted. The trend is an artifact of
  which targets survived, not of N. This is the same defect as comparing two
  stages that analyse data differently (L24), committed inside my own probe.
* **Fixed question set.** Holding the goldens to those answerable in the
  smallest corpus fixes the confound and leaves **five cases**. 100% at n=20,
  80% at n=91. Nothing is concluded from five.

The trap is structural: shrinking a corpus removes the documents the goldens
point at, so corpus size and question coverage cannot be varied independently
by subsampling. Testing this needs *new* documents, not fewer.

`pypi.org` is reachable (probed: robots.txt and a project page, both 200), so
that fetch is available - but widening the corpus predictably drops the external
pass rate past the 0.85 CI gate, which is L23's exact failure. That is a
deliberate decision about the gate, not a measurement to slip in.

**The obvious next fix is blocked by leakage, which is worth knowing before
building it.** If the defect is that IDF cannot tell a rare content word from a
rare function word, the natural correction is a second frequency signal: a term
appearing in *many questions* and few documents is scaffolding ("cannot",
"let", "my"), while one appearing in few of both is discriminating ("password",
"hook"). The 74 golden questions across both sets are exactly such a sample.

They are also the test set. Weighting retrieval by statistics computed over the
goldens is training on what the goldens are supposed to measure - the same
contamination this project already quarantines documents to avoid, arriving
through the term table instead of the corpus. The eval would improve and mean
less.

A real fix needs question-register frequencies from a source that is not the
evaluation set: a held-out question pool, or an ordinary-English frequency list.
The second is the usual answer and costs a dependency or a network fetch, which
is ADR 0001's territory rather than a tuning decision. Recorded so the next
cycle reaches that fork knowingly rather than building the leaky version first.

**Rules.**
1. **A term-weighting scheme inherits the register of the text it was fitted
   on.** IDF over documents answers "rare in these documents", and a query
   written by a person asking a question is not a sample from that
   distribution. On a specialised corpus the two diverge enough to invert the
   ranking on 30% of queries.
2. **Diagnose before fixing, and keep them separate when the fix fails.** The
   diagnosis here is measured and survives; the first fix derived from it does
   not. Recording the falsified fix is what stops the next cycle spending an
   hour on the same idea.
3. **When one cause explains two previously separate findings, prefer it.** The
   monotone `coverage_power` result had been written down as a fact with no
   mechanism. It had one, in another cycle's notes.

---

## L49 - A table wrong in one column, and a number that lost its unit

Two documentation defects found by re-running the commands that produced the
numbers, rather than reading them.

**The ablation table in `internal/PLAN.md` was wrong in its pass column only.**
Re-running `scripts/ablation.py --corpus external`, every metric matched to four
decimal places - recall@8 0.9186, MRR 0.7729, nDCG 0.7965 - and every pass count
was four cases stale:

| configuration | recorded | actual |
| --- | --- | --- |
| hybrid | 44/54 | 48/54 |
| lexical only | 43/54 | 47/54 |
| dense only | 43/54 | 44/54 |
| no rerank | 40/54 | 40/54 |

The mechanism is clean: later work moved the abstention floor and added surface
answerability. Neither touches a *retrieval* metric, and both change whether a
case passes. So a partial refresh was invisible - and the stale column changed a
conclusion, not just a number. At 43 and 43 the two arms read as tied; at 47 and
44 lexical alone is one case off hybrid while dense alone is four off.

**A partly refreshed table is worse than a stale one**, because the columns that
are right vouch for the one that is wrong.

**The contamination row had lost its unit.** It read "26 documents held out".
The harness was printing two counts of one operation under near-identical
labels: the run log said `documents=14` and the report said "Quarantined 29
contaminated document(s) across 4 question(s)". Both are correct and they answer
different questions - 14 distinct documents, held out 29 times, because a
document contaminating two questions is held out twice and is still one
document. The report's phrasing implied the first and printed the second, and
whoever wrote the plan copied it as a document count.

This is L28's class again: a defect in the instrument does not produce a
failure, it produces a number, and everything downstream inherits it. The report
now prints "14 distinct document(s) as 29 per-question holdout(s), across 4
question(s)", and a test asserts the two counts differ when a document
contaminates two questions and coincide when none does. Both mutations of the
counters are caught.

**The same defect was in three more places, found by applying the rule once.**
`docs/adr/0004-hybrid-retrieval.md` carries a copy of the same ablation table
and had gone stale in exactly the same column - and its prose drew a conclusion
from it, crediting reranking with "+4 cases" where the current numbers say +8.
`docs/EVALUATION.md` had two more: "fourteen PyPI project pages" for a corpus
that has held 91 since the widening, and the quarantine count copied with the
wrong unit again.

Its third claim was the one that mattered: *"Contamination there is reported
clean, so the numbers need no quarantine to be trustworthy."* The external set
is the regression gate, and it is **not** clean - 4 of 54 questions, 14
documents held out. The cause is not self-reference, which the corpus genuinely
cannot have, but authorship: the goldens were written from those pages, so a
question can reuse enough of a page's wording to match it. The detector is
working; the sentence claiming it had nothing to find was false, and it was a
claim about whether the gate's own numbers can be trusted.

**Rules.**
1. **Re-run the command, do not read the table.** The cost was one minute per
   table and every one was wrong - two in `PLAN.md`, one in an ADR, three in
   `EVALUATION.md`.
2. **A measurement copied into a second document goes stale in both.** The same
   ablation table lived in `internal/PLAN.md` and in ADR 0004 and drifted
   identically. Refresh every copy from the script, or keep one copy.
3. **A claim that a check found nothing ages worse than a number.** "Reported
   clean" was true when written and became false silently, and unlike a stale
   count it reads as reassurance rather than as data. Re-run the check that
   produced it, not just the metrics beside it.
4. **Refresh a living table; do not rewrite a dated record.** The same
   "fourteen pages" figure appears in this file and is correct there, because
   these entries describe a moment. `EVALUATION.md` describes the present.

**Hand-fixing the same number in a third file was the signal to stop.**
`tests/test_documented_numbers.py` now asserts the claims that are free to
check - the external corpus size, the golden-set sizes, and that the provenance
manifest lists exactly the documents on disk - against the files themselves.
The expensive ones are left out and said to be left out: the ablation pass
rates and the contamination counts both need a built index, and a test that
pretends to cover them would be worse than the gap.

**Its first version missed the exact defect it was written for.** The regex was
`(\d+) PyPI`, and the defect was "**fourteen** PyPI project pages" - spelled
out in words. Every mutation I tried was caught except the one that mattered,
and only because I mutated the *original* defect rather than a paraphrase of
it. The test now reads spelled-out numbers, and four variants of that mutation
are caught.

That is the whole argument for mutation testing in one case: the test passed,
covered the file, named the right claim, and could not have caught the bug it
was written for. Re-reading it would not have shown that. **Mutate the original
defect verbatim, not a convenient re-spelling of it.**
5. **Refresh a measurement table whole, never a column.** Different columns have
   different sensitivities, so a change can move one and leave the rest exactly
   right - which is the state that looks most trustworthy and is not.
6. **A count needs its unit in the sentence that prints it.** "29 documents"
   and "29 per-question holdouts over 14 documents" are the same number and
   different facts; only one of them survives being copied somewhere else.

---

## L50 - The corpus widened 91 to 153, and it settled two open questions

**The small-N hypothesis is falsified.** L48 measured IDF ranking the
discriminating query term first in only 28 of 40 goldens, because a function
word like `cannot` appears in ~1 of 91 PyPI pages and so scores as rare. The
obvious question was whether that is an artifact of corpus size. The previous
cycle established that subsampling cannot answer it - shrinking a corpus removes
the documents the goldens point at, so the question set and N cannot be varied
independently.

Real documents can. At 153 documents, on the same 40-question set:

| corpus | discriminating-term-first |
| --- | --- |
| 91 | 28/40 (70.0%) |
| 153 | 29/40 (72.5%) |

**Sixty-eight percent more documents bought one case.** The mismatch is not
about sample size, and adding more PyPI pages never will fix it: the function
words are absent from *that register* at any N, so every page added is more of
the same distribution. This closes the cheapest of the three paths L48 left open.

**It overturned a recorded conclusion, which is what widening is for.** ADR 0004
said MMR "is close to neutral on this corpus" - 48/54 with and without at 91
documents. At 153 it is worth a case and 0.023 of recall. Reranking went from +8
cases to +9. The third time that table has moved under a widening.

**And it exposed a real defect, not a stale golden.** "What is the capital of
France?" is a negative case, and the system now answers it with confidence
0.758. The cause, traced rather than guessed:

* `chardet.md` contains the word **France**, inside a French sentence used to
  demonstrate encoding detection;
* `idna.md` contains the word **capital**, as in "capital letters".

Two content terms, each matched once, in unrelated senses, in different
documents. Coverage over a two-term query is 0.5 for a chunk holding either one,
relevance is 0.3, and the 0.19 floor is cleared. Before the widening neither
term existed in the corpus, answerability collapsed the score, and it abstained
correctly - for the right reason, but only by luck of vocabulary.

**The short-query weakness is the general form.** A fixed relevance floor is much
easier to clear for a two-term query than a five-term one, because coverage is a
*fraction*: one incidental match is half of two terms and a fifth of five. And a
signal that would separate this case exists and is unused - **no single document
contains both `capit` and `franc`**, whereas for genuinely answerable questions
the discriminating terms co-occur. Co-occurrence is per-corpus; coverage is
per-chunk; nothing currently reads the first.

**Decided, not discovered (L23).** Pass rate 48/54 -> **47/54 = 0.870**, against
a CI floor of 0.85. The floor is not moved and the widening is kept: the corpus
is harder and more honest, every metric has more room (recall 0.919 -> 0.872,
nDCG 0.797 -> 0.744), and the case that was lost was lost to a defect worth
finding. The margin is now 0.020 rather than 0.039, and that is the cost.

**Rules.**
1. **When a hypothesis needs more data, get more data - do not simulate it by
   removing some.** Subsampling changes two things at once here, and the answer
   took 62 real pages and one measurement.
2. **Widening a corpus is not a neutral operation on a golden set.** Eleven
   abstention cases assert what the corpus *cannot* answer, so every document
   added is a chance to invalidate one. Two broke here, and only one of the two
   was the system's fault - which is exactly the distinction to make before
   editing either the corpus or the goldens.
3. **A negative case that passes because a word happens to be absent is passing
   by luck.** It looked like a working abstention gate for as long as the
   vocabulary happened not to collide.

---

## L51 - Three cheap fixes falsified, all pointing the same way

L48 diagnosed the coverage weighting: IDF measures rarity in a corpus of PyPI
prose, a question is written in another register, and the ranking inverts on 30%
of queries. Three corrections followed from that diagnosis. All three were
measured. All three failed, and the pattern in *how* they failed is the finding.

**1. Clip the IDF weight** so no single rare-in-corpus word dominates. Flat at
48/54 from no cap down to 5.0, then worse. Clipping compresses magnitudes and
the defect is ordering (L48).

**2. Widen the corpus**, in case rarity is a small-N artifact. 91 to 153
documents moved discrimination 28/40 to 29/40. The function words are absent
from that register at any N (L50).

**3. Require the query's discriminating terms to co-occur** in one document -
motivated by "What is the capital of France?", where `capit` is in idna.md
("capital letters") and `franc` in chardet.md (a French sample string) and no
document holds both. Measured over all 54 goldens at six rarity cutoffs:

| content-term cutoff | best threshold | TPR-FPR | answerable median | negative median |
| --- | --- | --- | --- | --- |
| df <= 33% | 0.60 | 0.159 | 1.00 | 1.00 |
| df <= 10% | 0.65 | 0.112 | 1.00 | 1.00 |
| df <= 3% | 0.50 | 0.000 | 1.00 | 1.00 |

No separation. The France case is real and does not generalise: most of the
negatives are ordinary English - "Who won the 1998 FIFA World Cup final?",
"Which package sends mail over SMTP?" - whose terms do co-occur somewhere in a
large enough body of developer prose. Nothing was built.

**What the three failures have in common.** Each tried to separate *relevant*
from *irrelevant* using a statistic over term occurrence, and each failed on the
same class of case: a query whose words are individually present and collectively
meaningless in this corpus. "Capital letters" and a French sample string are a
perfect lexical match for "capital" and "France" and have nothing to do with the
question. No amount of counting where terms appear recovers that, because the
information needed is what the terms *mean* here - which is what an embedder is
for, and the hosted ones are unreachable from this environment.

That is a convergent result rather than three separate dead ends, and it is
worth more than any of the three individually: the remaining failures on this
corpus are not reachable by cheaper term statistics.

**Rules.**
1. **When several independent fixes fail on the same subset, stop proposing
   fixes of that kind.** Three attempts from one diagnosis is enough evidence
   that the diagnosis, while correct, does not imply a lexical remedy.
2. **A mechanism that explains one case is a hypothesis, not a feature.**
   Co-occurrence explains the France case exactly and separates nothing over 54.
   The measurement that would have justified building it took twenty lines and
   ran before any code was written.

---

## L52 - A stale number in a decision record keeps a feature switched off

L49 was about stale numbers in reports: a table wrong in one column, a count
that had lost its unit. This is the same defect one level up, and it costs more.

`retrieve/expansion.py` implements pseudo-relevance feedback and is **off by
default**, on the strength of a measurement block in its own docstring:

> | external | off | 20/20 | 0.800 | 0.7815 |
> | primary  | on  | 17/20 | 0.600 | 0.4642 |
>
> No corpus improved; the primary corpus got measurably worse.

"External 20/20" dates it: the external set has held 54 cases for a long time,
and the corpus has gone 33 to 91 to 153 documents since. Re-run today
(`scripts/expansion_ab.py`):

| corpus | expansion | pass | recall@8 | MRR | nDCG@8 |
| --- | --- | --- | --- | --- | --- |
| external | off | 47/54 | 0.8721 | 0.7304 | 0.7487 |
| external | on | 47/54 | **0.8837** | 0.7246 | 0.7485 |
| primary | off | 16/20 | 0.7812 | 0.6354 | 0.6442 |
| primary | on | 16/20 | **0.8125** | **0.6375** | **0.6582** |

**Both of the old claims are false now.** Primary does not get worse - it
improves on every metric. And a corpus does improve: recall rises on both.

**It still stays off, and the new reason is the interesting part.** The pass
rate does not move on either corpus, at any of four settings (4, 8, 12 terms;
weight 0.25 and 0.5). The recall gain is real and *inframarginal* - it lands on
cases that already passed or still fail, and converts none. Measured cost: 20%
of query latency, 99.0 ms to 118.8 ms mean. Better recall for no additional
answered question, at a fifth more latency, is not a default.

So the decision is unchanged and every reason for it is different. That is the
point: had the numbers stayed stale, the feature would have remained off for a
reason that was no longer true, and the next person to reach for it would have
read a table telling them not to bother.

**Why this is worse than L49.** A stale number in a report misleads whoever
reads it. A stale number in a decision record *acts*: it holds a switch in a
position nobody has re-justified. The docstring was doing its job - "kept, off,
with the numbers above, so the next person starts from the measurement instead
of repeating it" - and that is exactly the mechanism that made it load-bearing
once it aged.

**Rules.**
1. **A measurement that justifies a default has a shelf life.** Re-run it when
   the thing it was measured on changes - the corpus, the golden set, the
   analyser. Anything that says "we tried this and it did not work" is a
   candidate to re-try, and the older it is the better a candidate.
2. **Record what a decision would take to reverse.** "Off because it does not
   help" ages badly; "off because the pass rate does not move at four settings
   and it costs 20% latency" tells the next person exactly which number to
   watch.
3. **Re-measuring can leave the decision alone and still be worth the time.**
   Same switch, entirely different justification, and the difference between
   those two states is whether anyone can trust the switch.

---

## L53 - The stale table did not just mislead, it argued for the wrong value

L52's rule - a measurement that justifies a default has a shelf life - names its
own next target. `AnswerConfig.min_relevance` is the abstention floor, and its
docstring ends: *"Re-sweep when the corpus changes - this number is a property
of the corpus, not of the algorithm."* The corpus had just changed by 68%, so I
re-swept it. That instruction was written by a previous cycle and worked.

**The value did not move. Everything justifying it did.**

| floor | 0.10-0.13 | 0.15-0.17 | 0.18 | **0.19** | 0.20-0.23 | 0.24-0.25 |
| --- | --- | --- | --- | --- | --- | --- |
| external | 44/54 | 45/54 | 46 | **47** | 46 | 45 |
| combined | 61/74 | 62-63/74 | 64 | **65** | 64 | 63 |
| over-answered | 6 | 5 | 4 | **3** | 3 | 2 |
| over-refused | 0 | 1 | 1 | **1** | 2 | 4 |

On 91 documents the curve had **two plateaus**, 0.19 was the midpoint of the
upper one, and a lone peak at 0.20 was deliberately rejected with the reasoning
that picking a peak fits the threshold to 74 questions. On 153 documents the
curve is **unimodal and 0.19 is its mode**, with 0.18 and 0.20 one case below on
either side.

So the old advice - pick the plateau, not the peak - no longer applies, because
there is no longer a plateau to pick. That advice was about a spike in a flat
region; the mode of a smooth single-peaked curve is a different object. Same
number, opposite argument.

**And the old table actively argued for the wrong value.** Its best cell was
0.20 at 49/54. Today 0.20 measures 46/54. A reader trusting the documented sweep
would have raised the floor and lost a case - which is the difference between a
stale number in a report and a stale number in a decision: the first misleads,
the second recommends.

**A second thing the re-sweep killed.** The original rationale for preferring a
higher floor was that it cuts over-answering, the failure this project treats as
dangerous. On the current corpus over-answering sits at 3 from 0.19 all the way
to 0.23 - raising the floor buys none of what it was supposed to buy, and costs
an over-refusal. The safety argument is simply not available here any more.

**Rules.**
1. **Write the re-run trigger into the docstring.** "Re-sweep when the corpus
   changes" is the only reason this got re-measured, two cycles and one corpus
   later. A measurement that says what would invalidate it is a measurement that
   gets renewed.
2. **When a value survives a re-measurement, check whether its argument did.**
   Twice now the number has stayed and the reasoning has been replaced. A
   default defended by an argument that no longer holds is undefended, and looks
   identical to a well-chosen one.
3. **A stale decision table is worse than no table**, because it converts a
   reader's diligence into a wrong move. Anyone following this one would have
   changed the floor on the strength of a cell that had gone stale.

---

## L54 - The corpus widening reversed a decision I had made this session

Two cycles ago I measured `gate_coverage_power`, found the best external number
this project had produced, and **declined to ship it**: rank power 2.5 with the
gate held at 1.0 gave 49/54, and it cost 0.039 external MRR, 0.022 nDCG and
0.031 of primary recall. Tuning a global default on one corpus's pass rate
against another corpus's recall is the overfit already recorded twice here, so
it shipped available and off.

That was right on the evidence available. The evidence changed.

Applying L52's rule - a measurement that justifies a default has a shelf life -
to my own decision, I re-ran the sweep at 153 documents. **The optimum moved
from 2.5 to 2.0, and stopped being a trade.**

| | rank 1.0 (was) | rank 2.0 (now) |
| --- | --- | --- |
| external pass | 47/54 | **49/54** |
| external recall@8 | 0.8721 | **0.9302** |
| external nDCG@8 | 0.7487 | **0.7538** |
| external MRR | 0.7304 | 0.7122 |
| primary pass | 16/20 | 16/20 |
| primary recall@8 | 0.7812 | 0.7812 |
| primary nDCG@8 | 0.6442 | **0.6558** |

At 91 documents this idea cost nDCG on both corpora and recall on primary. At
153 nDCG rises on both, primary is unchanged on pass, recall and MRR, and the
only cost is 0.018 of external MRR. The reason it was declined no longer exists.

**Shipped, and measured end to end through the real configs** rather than the
sweep harness: primary **18/20 -> 19/20**, external **47/54 -> 48/54**. Both
corpora gain a case. External recall 0.8721 -> 0.9070, primary 0.8125 -> 0.8438.

**What did not happen.** This does not repair the register mismatch of L48: IDF
still ranks the discriminating query term first in only 29 of 40 goldens.
Sharpening a partly-wrong ordering helps here *because the gate no longer moves
with it*, not because the ordering improved. The three falsified fixes of L51
stay falsified.

**The sequence is the lesson.** A corpus widening (L50) invalidated a
measurement (L52's expansion table), which suggested re-running a second one
(L53's abstention floor), which suggested re-running a third - and the third
reversed a decision made four cycles earlier in the same session. None of these
were found by review. Each was found by re-running a command whose output was
already written down.

**Rules.**
1. **Re-measure your own recent decisions after the data changes, not just old
   ones.** I trusted a number I had produced myself two hours earlier because it
   felt current. Its corpus was 40% smaller.
2. **"Declined as an overfit" is a conclusion about a dataset, not about an
   idea.** Record what would reverse it. Here the note said the cost was 0.031
   of primary recall; when that cost went to zero, the decision was obvious.
3. **One stale measurement is rarely alone.** Widening the corpus aged four
   documented conclusions at once, and they were only found because the first
   one prompted a sweep of the others.

---

## L55 - A cancelled build reports zero failures

Checking CI on the commit that widened the corpus - the one carrying the gate
risk, where the external pass rate fell to 0.870 against an 0.85 floor - I asked
the API for failed jobs and got:

    {"failed_jobs":0,"message":"No failed jobs found in this workflow run"}

and moved on. That run had been **cancelled**, not passed.

`.github/workflows/ci.yml` sets `concurrency: cancel-in-progress: true`, so
pushing a second commit kills the first commit's run. A cancelled run has no
failed jobs, so every check phrased as *"were there failures?"* answers no -
identically to a green run. The question was wrong, not the answer.

The widening was verified in the end, by three later runs that contain it, so
nothing was actually shipped unverified. The method was still unsound, and it
was unsound in the direction that matters: it can only ever produce a false
*pass*.

**Two things follow, and they are different.**

*For reading a result:* assert `conclusion == "success"`. "No failures" is a
weaker claim that a cancelled, skipped or never-started run also satisfies. This
is the L-series rule about operations that can silently do nothing, applied to
the thing that reports on all the others - and I had spent this whole session
insisting on verifying CI before claiming green, using a query that could not
distinguish green from cancelled.

*For the repository:* with `cancel-in-progress`, only the branch tip is
guaranteed verified. A per-commit greenness discipline is not enforceable under
that setting, and pretending otherwise is worse than knowing it. The setting is
kept - re-running superseded commits is not worth the minutes - and the
workflow now says plainly what its run history does and does not mean.

**Rules.**
1. **Verify the positive, not the absence of the negative.** "No failures", "no
   errors logged", "nothing was rejected" are all satisfied by *nothing having
   happened*. Ask for the success, and get a state, not a count of problems.
2. **The check on your checks deserves the same scrutiny as the checks.** L28
   said attack the measuring instrument first; this is the instrument that
   reports whether every other instrument ran.
3. **A tooling default can quietly void a discipline.** Nobody chose "only the
   tip gets verified" - it arrived with a sensible cost-saving default, and it
   silently changed what a green history means.

---

## L56 - The +1 I shipped was a +2 and a -1, and the -1 is measurable to the word

L54 shipped `coverage_power` 2.0 with the gate pinned at 1.0 and reported the
external set going 47/54 to 48/54. That is true and it hides the shape of it.
Comparing the failure lists rather than the counts:

* **fixed:** `pluggy` ("let other packages hook into it") and `tomli` ("reads
  TOML configuration files")
* **broken:** `structlog` ("treats every event as a dictionary passed through a
  chain of functions")

Two fixed, one broken, net one. A pass rate cannot show that, and the broken one
is the more instructive.

**structlog is not a semantic gap.** Its page says *"Everything is about
functions that take and return dictionaries"*, and it contains six of the query's
ten terms including every one that identifies it: `log`, `event`, `dictionari`,
`function`, `everi`, `librari`. It should be trivially retrievable. Traced:

| term | IDF | IDF² | in structlog | documents containing it |
| --- | --- | --- | --- | --- |
| chain | **6.00** | **35.97** | **no** | **3** - black, responses, orjson |
| treat | 4.22 | 17.85 | no | 14 |
| everi | 3.90 | 15.24 | yes | 25 |
| event | 3.80 | 14.44 | yes | 17 |
| dictionari | 3.75 | 14.08 | yes | 17 |
| through | 3.66 | 13.41 | no | 35 |

`chain` is the single highest-weighted term in the query. It occurs in three
documents out of 153, none of them about chaining functions - `black`,
`responses`, `orjson`. It is a word from the question's register that the corpus
happens to use three times, incidentally.

At power 1 it carried 4.5% of the query's weight and structlog's coverage was
0.523. At power 2 it carries **27%**, and coverage falls to **0.442**. Squaring
IDF squares the influence of the term the corpus understands least.

**This is L48 stated more sharply, and worse than I had it.** The problem is not
only that IDF misranks query terms - it is that a term which is *rare and
irrelevant* is indistinguishable from one that is *rare and discriminating*, and
every mechanism that trusts rarity harder makes the confusion cost more. IDF
cannot separate `password` from `chain`; sharpening multiplies whichever it got
wrong.

**Was shipping it still right?** Yes, and the reasoning is worth keeping
explicit. +2/-1 on the gate corpus, +1 case on primary, recall 0.8721 -> 0.9070,
nDCG up on both, one metric down 0.018. The trade is favourable and the loss is
a single case with a fully understood cause. But "48/54, up one" was an
incomplete description of it, and I wrote that before decomposing.

**Rules.**
1. **Diff the failure lists, not the pass counts.** Net +1 was two different
   changes. The count is the summary; the set is the result.
2. **An exponent on a weight is an exponent on the weight's errors.** Any
   transform that concentrates influence concentrates misplaced influence too,
   and the cases it breaks are the ones where the weight was wrong - which is
   exactly where you cannot see it from an aggregate.
3. **Report a shipped change by what it did to the members, at least once.** The
   aggregate justifies the decision; the decomposition tells you what you now
   own.

---

## L57 - I measured the wrong unit and it named the wrong fix

Chasing L56's structlog failure, I computed coverage per *document* and found
something striking: `black.md` matches **all ten** query terms, coverage 1.000,
while structlog ranks 11th. Black's PyPI page is long prose about code
formatting and contains every ordinary English word in the question. The obvious
reading is that coverage rewards long documents, and the obvious fix is the one
BM25 already has - length normalisation.

**The reranker does not score documents. It scores chunks.** Recomputing at the
unit the code actually uses:

| coverage@p2 | chunk vocab | document | terms matched |
| --- | --- | --- | --- |
| 0.409 | 144 | h11 | 5/10 |
| 0.407 | 139 | black | 3/10 |
| **0.220** | 59 | **structlog** | **4/10** |

structlog's best chunk matches *more* terms than black's and scores half as
much, so the story is not length. Decomposed: black's chunk matches `chain`
(35.97) and `treat` (17.85) - 53.8 between them - while structlog's matches
`event` (14.44) and `dictionari` (14.08) - 28.5. **The two heaviest terms in the
query are both words from the question's register that are irrelevant to the
answer, and together they outweigh the answer's actual signature.**

Length is real but secondary: the top 50 chunks by coverage have median
vocabulary 78 against a corpus median of 36. So I swept a BM25-style penalty,
`coverage / (1 - b + b·|chunk|/median)`:

| b | 0.00 | 0.25 | 0.50 | 0.75 | 1.00 |
| --- | --- | --- | --- | --- | --- |
| structlog rank | 15 | 15 | 17 | 14 | 16 |
| top result | h11 | black | black | regex | regex |

Flat. The top document churns without ever becoming the right one. **Falsified -
the fourth fix from this diagnosis to be measured and rejected**, after IDF
clipping, corpus widening and co-occurrence.

**The thing worth keeping is the sequence.** The document-level number was not
wrong; it was about the wrong object, and it pointed confidently at a fix that
does nothing. Had I implemented length normalisation on that evidence it would
have passed review - it is a real technique, addressing a real effect that the
measurement genuinely showed - and bought nothing.

This is the same rule this project has recorded about comparing stages that
analyse data differently (L24), turned inward: **a diagnostic must compute over
the same unit as the code it is diagnosing.** Documents and chunks are both
defensible things to measure and only one of them is what the reranker sees.

**Rules.**
1. **Diagnose at the granularity the code operates on.** Not the one that is
   convenient to compute, and not the one the corpus is stored in.
2. **A measurement can be correct, striking, and about the wrong object.**
   "Black matches all ten terms" is true and irrelevant, and it was more
   persuasive than the number that mattered.
3. **Four falsified fixes from one diagnosis is information.** Clipping,
   widening, co-occurrence and length normalisation all fail on the same cases.
   The diagnosis keeps being confirmed and keeps not implying a lexical remedy.

---

## L58 - The fusion decides 3% of the ordering, and on one corpus that is right

Four lexical fixes had been falsified against the same three cases, so instead
of proposing a fifth I decomposed where those cases are actually lost. The
answer was not where I had been looking.

| expected | dense rank | lexical rank | final rank |
| --- | --- | --- | --- |
| structlog | - | **2** | not retrieved |
| responses | - | **5** | not retrieved |
| freezegun | - | - | not retrieved |

**The lexical arm ranks `structlog` second for its own question, and it does not
survive to the output.** Two of the three "retrieval failures" are not retrieval
failures. The reranker demotes what the index found.

**Measured cause.** Final score is `base_weight * fused + adjustment`, with
`base_weight = 1.0`. Over 432 results from the 54 golden queries:

| | median | range | spread |
| --- | --- | --- | --- |
| fused RRF score | 0.0159 | 0.0119-0.0328 | 0.0209 |
| reranker adjustment | 0.3616 | 0.1895-0.9099 | **0.7204** |

The reranker's spread is **34.5x** the fused score's. Reciprocal Rank Fusion
decides about 3% of the ordering; the two arms function as a candidate generator
and the heuristic reranker does the ranking. That also explains why removing the
reranker is catastrophic (38/54) - it leaves a signal with a 0.02 spread - and
why the reranker's known flaws (L48, L56, L57) are so consequential.

**Rebalancing was the obvious fix, and the corpora want opposite things.**

| base_weight | 1 | 5 | 20 | 35 | 80 |
| --- | --- | --- | --- | --- | --- |
| external | **49/54** | 47 | 46 | 43 | 45 |
| primary | 16/20 | 16 | 17 | **18** | 18 |
| primary recall@8 | 0.7812 | 0.7812 | 0.8750 | 0.8750 | 0.8750 |

On the external corpus the current value is the best available and every
increase costs cases. On the primary corpus it is the *worst* value, and raising
it buys two cases and 0.094 of recall. The reranker dominating the ordering is
correct on one corpus and wrong on the other.

That is explicable rather than mysterious. The external corpus is short prose
where English term coverage discriminates well; the primary corpus is source
code, where the lexical arm matching identifiers is worth more than a coverage
heuristic built for sentences. One global constant cannot be right for both, and
the shipped value favours the corpus the regression gate runs on - which is the
defensible choice, but it was never a choice anyone made.

**Nothing was changed**, and this is the fifth fix measured and rejected for
these cases. It is also the first one that failed for an interesting reason
rather than by doing nothing.

**Correction, made immediately after: the override is not systematic.** The
framing above - "the reranker demotes what the index found" - describes the two
cases truthfully and implies a pattern that does not exist. Measured across the
43 goldens with an expected source:

* 36 have the expected document in the **lexical top 3**
* **35 of those survive to the final top 8**
* **one is demoted out of it: structlog**

The reranker respects a strong lexical hit in 35 of 36 opportunities. `responses`
is not a counter-example either; it sits at lexical rank 5, outside what anyone
would call a strong hit.

So the natural targeted fix - guarantee that the arms' top hits cannot be
demoted - would be a rule introduced to rescue exactly one case, which is the
thing L51 warns about: a mechanism that explains one case is a hypothesis, not a
feature. Not built.

The 34.5x scale imbalance is still real, still unexamined until now, and still
the reason `base_weight` matters more on one corpus than the other. What is *not*
true is that it is systematically costing correct results on the gate corpus. One
case in thirty-six is the cost, and the sweep shows raising `base_weight` to
recover it loses three others.

**Rules.**
1. **When several fixes fail, stop fixing and decompose.** Four attempts at
   "retrieval cannot find these documents" when the index ranked one of them
   second. The decomposition took one script and reframed the problem.
0. **Then check whether the reframing is a pattern or an anecdote.** I wrote up
   "the reranker demotes what the index found" from two examples and it is one
   in thirty-six. The measurement that would have qualified it cost one script,
   and I ran it only because the fix it implied felt too narrow to build.
2. **Check the scales of things you add together.** Two terms combined with
   weight 1.0 are only balanced if their ranges are comparable. Here one had
   34.5x the spread of the other, so the smaller was decorative - and no test,
   metric or review would show it, because both components were individually
   correct.
3. **A single global constant across two corpora is a compromise even when
   nobody negotiated one.** Ours favours the gate corpus, which is right; the
   point is that the trade existed unexamined and the other corpus was paying
   for it.

---

## L59 - Nobody had checked whether the confidence number means anything

Every answer carries a `confidence`, and a caller's only cheap way to decide
whether to trust a RAG answer is that number. It has never been measured against
whether the answer was right.

Measured over the 54 external goldens (see the caveat below):

| | n | min | median | max |
| --- | --- | --- | --- | --- |
| answered, expected source cited | 36 | 0.665 | **0.940** | 1.000 |
| answered, wrong or unanswerable | 11 | 0.682 | **0.722** | **1.000** |

**The ranges overlap across 0.318 of a 0.335 span - 95%.** No threshold
separates them. The medians differ usefully (0.940 vs 0.722) and the best
available cut sits at 0.74 with TPR-FPR of 0.490, so the signal is real: it is
informative *by tendency* and useless *as a gate*, and the docstring says
nothing about which of those it is.

**The part that matters is the maximum.** Three wrong answers are reported at
confidence **1.000**:

```
1.000  Which package sends mail over SMTP?        cites packaging.md, environs.md
1.000  Which package renders Jinja templates to PDF?  cites jinja2.md
1.000  What is relativedelta used for?            cites arrow.md, greenlet.md
```

The third is the clearest: a real question with a real answer in the corpus
(`python-dateutil` documents `relativedelta`), answered from `arrow` and
`greenlet`, at the top of the scale. A caller filtering on "confidence == 1.0"
would keep exactly this.

**Caveat, stated because it changes what the numbers compare to.** This
measurement calls the generator directly and therefore *skips the eval harness's
per-question quarantine of contaminated documents*. Two of the three cases above
are not among the eval's six failures, and the quarantine is the likely reason.
The calibration result stands - it is about what the system reports when it
answers - but these are not the same population as the eval's pass/fail, and
reading them as such would be the wrong-unit error of L57 again.

**Why confidence saturates.** It is built from citation coverage and retrieval
score, both of which are high whenever the extractive generator finds text to
quote. Quoting successfully is not evidence of answering correctly, and nothing
in the number is derived from whether the retrieved chunk addresses the question
- that information exists, in `rerank_relevance`, and the abstention gate uses
it while the reported confidence does not.

**Rules.**
1. **A number a caller will act on deserves a calibration measurement, once.**
   This one took a twenty-line script and had never been run in fifty-eight
   recorded learnings, all of which were about retrieval quality rather than
   about what the system tells you regarding it.
2. **Report the overlap, not the difference in means.** "Correct answers score
   higher on average" is true here and would have been a fair summary; the
   ranges overlap 95%, which is the fact a caller needs.
3. **A confidence that cannot be wrong at 1.0 is a different contract from one
   that can.** Whichever one you have, say so where the field is defined.

---

## L60 - The confidence breaks a rule the codebase states, and it costs nothing here

L59 found the reported confidence badly calibrated. Reading how it is built
turned up a documented inconsistency:

`_confidence` uses `results[0].score` - the *total*. And `rerank.py` says of
that number, in a comment above the line that produces it:

> Authority, recency and position are query-independent: they raise a chunk's
> score whether or not it has anything to do with the question. Fold them into
> one number and the total stops being usable as an "is this relevant at all"
> signal ... Ordering uses the total; the abstention gate uses
> `rerank_relevance` alone.

The abstention gate obeys that rule. The confidence reported to the caller
breaks it, using exactly the number the comment says is unusable for judging
relevance. That looked like a bug with an obvious fix.

**Measured, and the fix is not supported** (`scripts/confidence_ab.py`, AUC over
all right/wrong pairs of the 47 answered goldens):

| formulation | AUC | best TPR-FPR |
| --- | --- | --- |
| **current** (0.5·top/0.6 + 0.2·sep + 0.3·cov) | **0.665** | 0.490 |
| relevance only | 0.657 | 0.442 |
| swap top → relevance | 0.634 | 0.497 |
| current × relevance | 0.629 | **0.525** |
| half top, half relevance | 0.641 | 0.490 |

The current form has the best AUC. One alternative has a better threshold
separation and a worse AUC, which is L22's split again - and here there is no
shipping metric to break the tie, because nothing gates on confidence. With 11
wrong answers, none of these differences is distinguishable from noise.

**Why the inconsistency costs nothing.** L43 measured authority and recency as
*inert on both corpora*: authority is constant because each corpus is a single
source at 1.0, and recency is saturated because every document is the same age.
So `top` is `relevance + phrase + a constant` here. Folding in priors that do
not vary changes nothing - which is precisely why the violated rule has no
victim, and precisely why it will have one on a corpus with mixed sources or
real age spread. That is the corpus the priors exist for.

**So: not changed, and now written down where the field is defined** - the
inconsistency, the measurement showing it is currently harmless, and the
condition under which it stops being harmless.

**Rules.**
1. **A rule stated in a comment is worth grepping for violations of.** This one
   named its own targets - "the total", "authority, recency and position" - and
   the violation was one file away, in the number users actually see.
2. **"It violates our stated principle" is a reason to measure, not to change.**
   The principle is right, the violation is real, and on this data the fix makes
   things very slightly worse. Ship the measurement, not the tidiness.
3. **An inert component makes a real defect invisible.** The bug and the reason
   it does not bite have the same cause, so the corpus that would expose it is
   the one where the feature finally works.

---

## L61 - The recency factor was harmless while dead and harmful once alive

L43 measured `recency_weight` as inert on both corpora: every document shared an
age, so the factor was a constant and could not reorder anything. L50 refined
that to *saturated* rather than constant. Neither could say whether the feature
was any good, because nothing could exercise it.

**PyPI stamps every project page with its release date**, in a `<time datetime>`
that `scrape/html.extract` already reads - and the corpus builder fetched it and
threw it away. The same defect as connectors reading a real date and filing it
where nothing scores it (L44/L45), this time in the tooling.

**The carrier matters and nearly went wrong.** The obvious move is to set each
file's mtime. Git does not preserve mtimes, so a fresh clone stamps every file
with the checkout time: recency would be live in a working tree and dead in CI,
and the two would measure different corpora. That is L34 built in deliberately.
The date is committed instead, as markdown front matter, which required
`util.text.split_front_matter` and teaching the filesystem connector to strip a
`---` block rather than index `date` and `source` as prose.

**Backfilled 151 of 153 pages** - two carry no date on the page and fall back to
the mtime, reported rather than silently defaulted.

| | before | after |
| --- | --- | --- |
| corpus age span | 0.03 days | **1,999 days (5.5 years)** |
| recency factor | 0.999182-0.999348 | **0.0042-1.0000** |
| spread | 1.65e-04 | 0.9958, **6000x** |
| worth, at weight 0.08 | 0.000013 of score | 0.0797 of score |

**Then it could be swept for the first time, and zero dominates:**

| recency_weight | 0.0 | 0.02 | 0.04 | 0.06 | 0.08 | 0.12 | 0.16 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pass | **49/54** | 47 | 47 | 47 | 47 | 45 | 45 |
| recall@8 | **0.9302** | 0.8837 | 0.8837 | 0.8837 | 0.9070 | 0.8605 | 0.8605 |
| nDCG@8 | **0.7538** | 0.7414 | 0.7373 | 0.7341 | 0.7390 | 0.7233 | 0.7143 |

Every non-zero weight is worse on every metric. The feature did not merely fail
to help - it was **harmless while dead and harmful once alive**, and for four
cycles it had been recorded as a neutral thing that simply could not be measured.

**Why it is wrong here, and where it would be right.** Recency is a prior for
corpora whose documents *supersede* one another: news, changelogs, versioned
docs, a chat archive. A later document is then more likely to be the answer. A
corpus of package descriptions has no such property - how recently `pydantic`
shipped says nothing about whether it answers a question about `relativedelta`.
The prior is not broken; it is applied to a corpus that does not satisfy its
assumption.

So it ships at 0.0 with the table as the argument for turning it on. A prior
that suits the wrong corpus is noise injected into every query.

**A determinism property came free.** With no scoring term reading the wall
clock, the same index and query now give bit-identical scores whenever they run
- stronger than the injectable clock was introduced to approximate. Pinned, and
the older test that asserted the clock *does* move the score now passes
`recency_weight` explicitly, so it keeps testing what it was written for.

**Rules.**
1. **"Inert" is not "harmless", it is "unmeasured".** Four cycles recorded this
   factor as unmeasurable and left it on. The first measurement said switch it
   off. An untested default is a claim, and the claim was wrong.
2. **Ask what carries a value into version control before choosing where to put
   it.** An mtime is a perfectly good date that CI cannot see.
3. **A prior encodes an assumption about the corpus. Write the assumption down
   next to the weight**, because the weight is meaningless to anyone who does
   not know which corpora it suits.

---

## L62 - A feature can vary across the corpus and still never discriminate

Having made `recency_weight` measurable and found it harmful (L61), the sibling
question is `authority_weight` - the other prior L43 recorded as inert, on the
grounds that "every document came from one source with the same trust level".

**That claim is stale.** The primary corpus carries four authority levels:

```
{1.2: 83, 1.0: 1, 0.68: 8, 0.9: 5}      # 97 documents
```

1.2 for this repository, 1.0 for reference material, 0.9 for chat transcripts,
0.68 for a video with no transcript. It varies, and has for a while.

**It varies and still does not discriminate.** Swept 0.0 to 0.3 on the corpus
where it varies: **recall@8 is identical at every setting**, pass rate never
leaves 19/20, MRR and nDCG wobble in the third decimal.

The reason is not that the input is constant - it is that the variation is not
*inside the sets that get compared*:

| | |
| --- | --- |
| queries where every result shares one authority | **7 of 20** |
| queries with exactly two distinct values | 11 of 20 |
| median spread within a result set | 0.20 |
| corpus share at the most common level | 83/97 = **86%** |

A ranking feature only ever acts on differences *within* a candidate set. Global
variance is the wrong statistic: 86% of documents at one level means most
comparisons are between two documents of equal authority, and the factor cancels.

**This refines L43 and L50 into something more useful.** The progression was
"constant, therefore inert" (L43), then "saturated, not constant" (L50), and now
"varying, and still inert". All three describe a feature that cannot reorder
anything, and only the first is about the input being uniform. The question to
ask is not *does this feature's input vary across my data* but **does it vary
between the items my system actually compares**.

**Decision: left at 0.12.** Unlike recency there is nothing to switch off - the
prior is not wrong for this corpus, it simply has almost nothing to say about
it. Tuning it against a 20-case set where no metric moves would be fitting
noise. The note on the field now says what would make it real: a corpus mixing
sources of genuinely different trust *within the same answers*.

**Rules.**
1. **Measure a ranking feature's spread within the candidate set, not across
   the corpus.** They are different numbers and only one of them predicts
   whether the feature does anything.
2. **A stale justification survives longer than a stale number**, because
   nothing recomputes it. "Single source, one trust level" was true when
   written and had been false for many cycles, and it was still being cited as
   the reason not to look.
3. **"Weak" and "inert" deserve different words and different decisions.**
   Recency was harmful and got switched off; authority is merely quiet and was
   left alone. Collapsing both into "does not move the metrics" would have
   invited the same action for opposite situations.

---

## L63 - The most upstream number in the pipeline had never been measured

Every constant this repository has swept sits downstream of the chunk:
`candidate_k`, `mmr_lambda`, `rrf_k`, the coverage weights, the abstention
floor, the base weights, recency, authority (L33, L44, L61, L62). The chunker's
own sizes - `target_tokens=320`, `hard_max_tokens=640`, `overlap_tokens=64` -
had never been swept at all, which makes them the largest untested claim in the
tree by L61's rule. Everything downstream was tuned against whatever they
happened to produce.

`scripts/chunk_sweep.py` sweeps them, holding the shipped ratios (hard_max 2x,
overlap 0.2x) so the knob means "chunk granularity" rather than silently
becoming a hard_max sweep at the top of the range:

| target | external pass | recall@8 | nDCG@8 | chunks | primary pass | recall@8 | chunks |
|---|---|---|---|---|---|---|---|
| 96 | 45/54 | 0.8953 | 0.7256 | 3141 | 18/20 | 0.8125 | 2091 |
| 160 | 47/54 | 0.9070 | 0.7389 | 2254 | 18/20 | 0.8125 | 1361 |
| 240 | 48/54 | 0.9070 | 0.7443 | 1928 | 17/20 | 0.7812 | 1018 |
| **320** | **49/54** | **0.9302** | **0.7538** | **1822** | **17/20** | **0.7812** | **840** |
| 480 | 49/54 | 0.9302 | 0.7552 | 1770 | 18/20 | 0.7812 | 659 |
| 640 | 49/54 | 0.9302 | 0.7448 | 1748 | 18/20 | 0.7812 | 597 |

**Decision: left at 320**, on a plateau that runs to 480 on the corpus that
gates. The two corpora disagree in direction - external wants bigger chunks and
primary's recall is best at its smallest setting - and only the external one
moves pass rate, so this is a plateau to sit on rather than a peak to chase.
Smaller is not free either: 96 costs 72% more chunks, vectors and index bytes to
lose four cases.

**The sweep's real finding was in a column nobody asked for.** Chunk size p50
barely moved on the external corpus - 103 tokens at target 96, 126 at target
640 - because PyPI pages split into sections far below any of these ceilings.
The knob looked nearly inert. The `max` column said otherwise: **1357 tokens at
every single setting**, against a documented ceiling of 640.

### `hard_max_tokens` was not a ceiling

`ChunkConfig` said it was *"the ceiling a chunk may not exceed even if that
means splitting a structural unit"*. `_pack_units` had a branch that emitted an
over-ceiling unit whole rather than cutting it "at an arbitrary point". Measured
on the shipped config:

| | external (153 pages) | primary |
|---|---|---|
| chunks over `hard_max` | 8 of 1810 (0.44%) | 18 of 829 (2.17%) |
| largest | **1357 tokens, 2.1x the ceiling** | 714 |
| what they are | changelog bullet lists | oversized definitions |

The mechanism is that `split_sentences` returns *one unit* for text with no
terminal punctuation - a changelog, a table, a fenced example - so a 1,332-token
"sentence" is not a long sentence, it is the splitter failing to see structure it
does not model. Lines are the structure such text does have. Packing now
subdivides by lines, then by word windows for a line that is still too big (a
minified file), and never cuts mid-word.

**This is L40's defect again, and L40's sweep could not have caught it.** That
sweep grepped the source for *never, always, cannot, only*. This claim is
phrased "may not exceed". The vocabulary was the limit, not the claims.

Retrieval is untouched by the fix - the external gate reads 48/54, recall 0.907,
nDCG 0.746 before and after, from a rebuilt index - and the tail now tracks the
knob it is supposed to (max 237 at target 96, 1267 at 640) instead of sitting at
1357 regardless.

### Two different numbers are both called "the chunk size"

The ceiling is spent on the chunk *body*. `Chunk.token_estimate` measures
`indexed_text`, which is body **plus** the context header - which is why a 640
ceiling reports 667. The header had never been costed either:

| | external | primary |
|---|---|---|
| header, median | 19 tokens | 18 tokens |
| share of what is embedded, median | 14.2% | 6.0% |
| on top of all body text | **13.1%** | 7.1% |
| in chunks with a body under 64 tokens | 29% | 30% |

So contextual retrieval - commitment 2 of the chunker's docstring, argued for
and never measured - costs 13% of the external corpus's embedded tokens. It
earns them, and not in the way the docstring claims:

| | pass | recall@8 | MRR | nDCG@8 |
|---|---|---|---|---|
| header on (shipped) | **49/54** | **0.9302** | 0.7122 | 0.7538 |
| header off | 47/54 | 0.8837 | **0.7322** | **0.7586** |

Two cases and 4.7 recall points for 13% more tokens - and *worse* ordering among
what it finds. The header pulls documents into the window that would otherwise
be missed, and adds noise to the ranking of the ones already there. On the
primary corpus it changes nothing but precision. Kept, now on evidence.

### The index had no idea the chunker had changed

`IndexPipeline` guards the embedding space: change the model, the dimension or
the corpus statistics and every affected vector is recomputed rather than
silently compared across incompatible spaces. One stage upstream there was
nothing. Chunking is not a function of the document, so an unchanged document
meant an unchanged chunk:

```
first index:                     153 docs, 1822 chunks
re-index, 5x smaller chunker:      0 docs,    0 chunks written   <- reported success
```

Every measurement taken that way describes a chunker that is not in the tree.
`reindex_all()` existed for exactly this and its docstring says so - *"used
after a chunking-config change, which the incremental path cannot detect"* - but
nothing detected it, so somebody had to remember. **I did not remember**: the
first gate run of this cycle went straight through the stale path, and it agreed
with the rebuilt one only by luck.

The pipeline now stores a chunker fingerprint - the sizes *and* the module
source, because subdividing an oversized unit moves boundaries with every number
held constant - and rebuilds chunks when it changes. Idempotence survives: an
unchanged chunker still writes zero.

### Writing this entry cost a golden case, then gave it back, then killed it

The primary corpus went 18/20 to 17/20 during this cycle. It was not the
chunker: on the *same* corpus, old and new chunkers both give 17/20 with
identical metrics to four decimals. It was the prose. The case is the one that
asks how the pipeline notices vectors left over from an older embedding space,
and its answer had to contain the word the mechanism is named after. The new
comments written to explain this cycle's fix took the top slots from the code
they describe - and they paraphrase the mechanism instead of naming it, so the
answer no longer carried the word. Recall did not move; the expected sources
were still retrieved. Only the wording of the answer built from them changed.

Then writing *this entry*, which uses that word a dozen times, put it back into
the corpus and the case passed again. Three measurements over one session,
retrieval code untouched throughout:

| corpus state | pass | recall@8 |
|---|---|---|
| before this cycle's edits | 18/20 | 0.7812 |
| plus the comments explaining the fix | 17/20 | 0.7812 |
| plus this learnings entry | 18/20 | 0.7500 |
| plus the golden's retired expectation and this rewrite | 18/20 | 0.7812 |

The pass rate came back and recall went *down*: the new prose supplied the
missing keyword for one question and displaced expected sources for others. A
number that moves in both directions from writing documentation is not measuring
the retriever. The external gate, which does not describe this repository, read
48/54 and recall 0.907 before and after all of it.

**Then the repository's own guard failed the suite**, which is the part that
matters. `check_discrimination` reports an expectation that no longer selects
anything, and the word had reached **17 of 83 documents (20.5%)**, past its 20%
threshold. Three of those seventeen were mine; the other fourteen were there
already. The word is repository vocabulary now.

The precedent was to tighten, the way `"sha"` became `"commit sha"` at 6%. It
does not work here. Every tighter form - the two identifiers and the possessive
phrase - sits under 5% of documents *and* appears in none of the extractive
answers, so each trades a case that passes without discriminating for a case
that cannot pass. The counterfactual is decisive: excluding both expected
documents from retrieval, the answer *still* contains the word, because this
file now discusses it at length.

**So the expectation was removed rather than tightened**, with the evidence in
the golden's `notes`; that case is graded on retrieval alone from here. An
answer expectation works only when it names a rare literal - an RFC number, a
commit sha - never when it is a word the code is written in. Removing an
expectation to make a case pass is eval-fitting; removing one measured not to
discriminate, and recording why, is maintenance. The difference is entirely in
whether the measurement came first.

### And the corpus was reading over my shoulder

Excluding the chat source turns that case from a pass into a failure, so the
transcript is where the passing answer came from. There is exactly one chat
document in this index:

```
title: Session: /goal goal ultrathinl continue ooda
chars: 8899   occurrences of "fingerprint": 8
```

That is *this session*, indexed while it ran. The eval's answer to "how does the
pipeline detect a stale embedding space?" was my own conversation about writing
the answer, and the corpus grew every time I typed. The local number is 18/20
and the honest one is 17/20 - CI is right to pass `--exclude-source chat`, and
the eval on a developer's machine is measuring something no other machine has.

**Rules.**
1. **Sweep the most upstream knob first.** Everything downstream was tuned
   against whatever it produced, so its value is baked into every conclusion
   that came after. It is also the knob nobody sweeps, because unlike a
   retrieval constant it costs a full re-index.
2. **Read the max, not the median, when checking a bound.** The p50 said this
   knob was nearly inert on the external corpus and the max said the ceiling was
   broken by 2.1x. A bound is a claim about the tail; the middle of the
   distribution cannot report on it.
3. **A ceiling with an "emit it whole" branch is a target with a comment.**
   Every escape hatch in a bound is the bound's real value.
4. **Guard every stage whose output is cached, not only the stage that bit you
   last.** The embedding-space check was built after being burned; chunks sit
   above vectors and had no equivalent, and the fix for that had been written
   already - as a method nothing called automatically.
5. **In a corpus that indexes its own notes, writing the note changes the
   measurement** - and the session transcript lands in it before the note does.
   Separate the corpus change from the code change before attributing a
   regression: the control run here (same corpus, both chunkers) is what
   stopped a paragraph of prose being recorded as a chunker regression.
6. **An expectation about answer *text* must name a rare literal.** An RFC
   number and "commit sha" survive; a word the code is written in gets adopted
   by the corpus and stops separating a right answer from a wrong one. Check it
   by counterfactual - remove the expected sources and see whether the answer
   still contains the term - not by how the case is currently scoring.

---

## L64 - The offsets said where the chunk came from, and 45% of them were wrong

L63 filed this as the next cycle's lead: `char_start` failed to locate its own
chunk for 206 of 831 primary chunks. Split by kind, it is not a general drift -
it is one stage:

| | located by `char_start` |
|---|---|
| code | **333 of 606 (55.0%)** |
| prose | 1818 of 1822 (99.8%) |

**Three mechanisms, all the same shape: something moved and the offset did
not.**

1. `_split_code` built its line units as `[(line, 0) for line in ...]` and then
   discarded the offsets the packer returned, filing every piece at the
   enclosing definition's start. A definition too large for one chunk therefore
   produced pieces that all claimed the same position - one of them 3,151
   characters from where its text actually is - and the two branches for files
   with no recognised definitions filed *everything* at 0.
2. `chunk_document` strips each piece before storing it, which moves where the
   text begins by however much whitespace came off. For a packed code body that
   is a whole indent, so even a correct piece offset pointed just before the
   text rather than at it.
3. `_split_transcript` filed each cue at the start of its *line*, while the unit
   text had the leading whitespace and the `[00:04:12]` marker removed. The
   offset pointed at the timestamp, not at the words the chunk contains.

Fixing all three: **code 55.0% -> 100%**, prose unchanged at 99.8%. The four
remaining prose chunks are ones where `_balance_fences` prepends a synthetic
fence marker, so their text genuinely does not exist in the document - explained,
not broken.

**Nothing in the fix changes what is retrieved, and that is checkable rather
than assumed.** Chunked over a frozen snapshot of the tree, before and after:
606 chunks both times, all 606 chunk ids equal, all 606 lengths equal, 273
offsets different. Splitting and rejoining on the same separator is lossless, so
carrying real offsets is invisible to everything downstream. The external gate
reads 48/54, recall 0.907, nDCG 0.746 before and after.

**Why this lived so long: nothing reads the field.** `char_start` is computed,
stored, selected back and never consumed - no citation, no deep link, no
snippet. A field with no reader gets no test and no bug report, so the error had
no way to surface; it was wrong in every index this project has ever built. That
is the cheap moment to fix it, and the expensive moment is the first feature
that trusts it.

**The property test had to be written to the data, not to the wish.** The first
version asserted that the document at `char_start` begins with the chunk's first
24 characters, and it failed on *correct* prose: chunk text is a reconstruction -
units joined with a space where the document had a blank line - so only a
whitespace-collapsed prefix is locatable. The strict version would have reported
a bug in the one path that never had one. Against the old chunker the test now
fails with `pieces share an offset: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`.

**And the suite grew by ten tests with no code change.** 367 at the start of the
session, 372 after this work, 382 for the *same commit* an hour later. The live
GitHub cross-checks skip as a module unless the local HEAD is also the remote
head - `push first`, says the skip message - so pushing the branch is what
enabled them. A test count is a property of the environment as much as of the
tree, and CI, which only ever runs pushed commits, runs a larger suite than a
working copy does.

**Rules.**
1. **A field nobody reads is not a field nobody can get wrong - it is a field
   nobody can notice being wrong.** Test provenance where it is written, because
   there is no reader to complain.
2. **An offset argument of `0` is a lie the type checker accepts.** Every one of
   the three defects passed a syntactically fine number that meant "I do not
   know where this is".
3. **Every transformation after an offset is computed moves what it points at** -
   a strip, a marker removed, a prefix added. The offset is part of the
   transformation, not a fact recorded before it.
4. **Write the property test to what the data can be, not to what would be
   tidy.** Chunk text is a reconstruction; asserting a verbatim slice reports
   bugs in code that is correct, which is how a good property gets thrown away.
5. **The size of a test suite is an environment measurement.** Ten tests here
   turn on whether the branch has been pushed.

---

## L65 - The dense arm was starved, fixing it changed nothing, and the weights that would have fixed that are a cliff

L63 swept the chunker because it was the most upstream unmeasured number.
`dim = 768` is the next one: every embedding this project has produced has been
hashed into 768 buckets, and the load factor says what that means - **129,072
distinct features on the external corpus, 168 per bucket**; 85,112 and 111 per
bucket on the primary one. Signed hashing makes collisions cancel in
expectation. It does not make them free.

`scripts/embedder_sweep.py`, external corpus:

| dim | hybrid | recall@8 | dense only | recall@8 | ms/query | index MB |
|---|---|---|---|---|---|---|
| 192 | 48/54 | 0.8953 | 34/54 | 0.5349 | 56 | 4.5 |
| 384 | 49/54 | 0.9302 | 40/54 | 0.7093 | 70 | 8.3 |
| **768** | **49/54** | **0.9302** | **44/54** | **0.8023** | **95** | **12.6** |
| 1536 | 48/54 | 0.9070 | 43/54 | 0.8140 | 144 | 17.2 |
| 3072 | 48/54 | 0.9070 | 46/54 | 0.8605 | 239 | 28.2 |
| 6144 | 48/54 | 0.9070 | 46/54 | 0.8488 | 441 | 49.5 |

**The dense arm is collision-limited and the system is not.** Widening from 192
to 3072 buys the dense arm **twelve cases** (34 -> 46) and 0.33 recall. Hybrid
over the same range: 48, 49, 49, 48, 48, 48. The pipeline is not embedding-space
limited at 768; something downstream is.

**Decomposed to the one case that moves.** *"How does one Python library let
other packages hook into it?"*, expecting `pluggy`:

| dim | pluggy's rank, hybrid | pluggy's rank, dense only |
|---|---|---|
| 192 | 12 | not in top 30 |
| 384 | 7 | not in top 30 |
| 768 | **8** | not in top 30 |
| 1536 | 12 | not in top 30 |
| 3072 | 9 | **5** |
| 6144 | 9 | 6 |

At 3072 the dense arm has learned to find the right document and puts it fifth.
Hybrid publishes it ninth, one place outside the window. Isolating the stage, at
dim 3072:

```
dense only              rank 5      lexical only           rank 13
dense only, no rerank   rank 9      hybrid, no rerank      rank 10
                        hybrid (shipped)  rank 9
```

Fusion is the ceiling. RRF combines a rank-5 opinion with a rank-13 opinion and
publishes rank 9 - the average, not the maximum - and the reranker, which
promotes the document from 9 to 5 when it is alone with the dense arm, cannot
reach past the fused ordering to do it.

### So turn the weights up. They do not turn.

Raising `dense_weight` or lowering `lexical_weight` should let the better arm
through. Measured instead:

| ratio | lexical_weight | pass | recall@8 | nDCG@8 |
|---|---|---|---|---|
| 1.00 | 1.0 | 49/54 | 0.9302 | 0.7538 |
| 1.11 | 0.9 | 49/54 | 0.9302 | 0.7570 |
| 1.33 | 0.75 | 49/54 | 0.9302 | 0.7628 |
| 1.54 | 0.65 | 47/54 | 0.9070 | 0.7657 |
| **1.67** | **0.6** | **44/54** | **0.8023** | **0.6972** |
| 2.00 | 0.5 | 44/54 | 0.8023 | 0.6972 |
| inf | **0.0** | **44/54** | **0.8023** | **0.6972** |

**A weight of 0.6 and a weight of zero are the same system**, to four decimal
places on three metrics. The arithmetic says exactly where that happens before
the experiment does: every RRF contribution from a list of `n` candidates lies
between `weight/(k+1)` and `weight/(k+n)`, so one arm's whole range spans

    (k + n) / (k + 1) = (60 + 40) / 61 = 1.64

and past that ratio every document the heavy arm returns outscores every
document only the light arm returns. The predicted cliff is 1.64; the measured
one is between 1.54 and 1.67. The knob is continuous in its type and a switch in
its behaviour, and its cliff is set by two constants - `rrf_k` and `candidate_k` -
that live nowhere near it.

**Decisions: `dim` stays 768, both weights stay 1.0.** 768 is where hybrid pass
rate is maximal and the dense arm is worth having as a fallback; 1536 upward
costs 1.5x to 4.6x the query latency to lose a case. `lexical_weight=0.75` is
tempting - same pass rate, better nDCG on the external set - and it costs a case
on the primary one, so it is a peak on one corpus, which this repository has
recorded as a mistake three times already.

**The consequence for the plan item that is blocked on a key.** "A hosted
embedder, measured against the offline baseline" assumes a better embedder makes
the system better. This cycle is the measurement of that assumption's mechanism,
and it says a twelve-case improvement in the dense arm reached the output as
nothing. A hosted embedder must be evaluated in hybrid, not alone, and if it
looks disappointing there, the fusion - not the model - is the thing to examine.

**Rules.**
1. **Improving a component is not improving a system.** Report the arm you
   changed *and* the output; either alone is half the finding, and the half that
   flatters the change is the one you will report by accident.
2. **A knob mediated by a rank transform inherits that transform's range.**
   Compute the range before treating the knob as continuous - it is two
   divisions, and it predicted the cliff to within one sample here.
3. **When two constants set a third knob's usable range, that relationship
   belongs next to both, or in a test that recomputes it.** A pinned 1.64 goes
   stale the first time anybody sweeps `rrf_k`.
4. **Read the cost column before the quality column.** 6144 buckets is 4.6x the
   latency and 3.9x the index for one case fewer.

---

## L66 - Widening the corpus took seven cases off the gate, and none of them back

PLAN item 3 has said "widen the corpus again" since L29, on the grounds that
every previous widening overturned something. This one widened the external
corpus from **153 to 266 PyPI pages** - 128 packages requested, 113 added, one
already held, 14 skipped and reported (five behind an anti-bot interstitial,
nine with under 40 words once the site template comes off).

**With no retrieval code changed at all:**

| | 153 documents | 266 documents |
|---|---|---|
| pass | **48/54** | **41/54** |
| recall@8 | 0.9070 | 0.8140 |
| MRR | 0.7089 | 0.6641 |
| nDCG@8 | 0.7460 | 0.6872 |

The previous corpus was flattering the retriever by 13% of the cases. That is
the third time widening has said so, and the reason to do it a fourth time.

**Decomposed before diagnosed**, because "seven cases" is not one thing:

* **Three are retrieval misses** - `pluggy`, `blinker` and `bcrypt` no longer
  reach the window, displaced by pages that merely share vocabulary (`docker`,
  `psycopg2-binary`, `keyring`).
* **Four are the abstention gate** letting an unanswerable question through. A
  bigger corpus does not only add answers, it adds *higher-scoring junk*, and
  the floor that refused it at 153 documents does not at 266.

**And checked for the artefact first.** Quarantine grew from 22 documents to 31,
and quarantine excludes documents from their own question - if it had started
holding out an expected document, the case could not pass whatever retrieval
did. It has not: every held-out document belongs to a negative case, which is
the design. The seven failures are real.

**The floor does not scale, and raising it does not help.** Re-swept over the
widened corpus, the combined pass count across both corpora is flat within noise
over a 2.7x range of thresholds:

| floor | 0.15 | 0.20 | 0.25 | 0.30 | 0.35 | 0.40 |
|---|---|---|---|---|---|---|
| external | 42/54 | 41/54 | 43/54 | 43/54 | 44/54 | 42/54 |
| wrongly answered | 6 | 6 | 4 | 3 | 1 | 0 |
| wrongly refused | 0 | 2 | 2 | 5 | 6 | 10 |
| both corpora | 60/74 | 59/74 | 61/74 | 60/74 | 61/74 | 59/74 |

Every threshold buys a refusal by selling an answer, one for one, which is what
a threshold looks like when the two populations it separates have moved together.
Left at 0.19. The gate's problem is not where its line is drawn.

**The ablation moved again too.** Re-run whole (`scripts/ablation.py`, 266
documents, 3,166 chunks): hybrid 41/54, lexical only 40/54, dense only 37/54, no
rerank 32/54, no MMR 41/54. Two conclusions change with the corpus:

1. **Hybrid beats both arms on pass rate for the first time.** At 153 it was
   level with the lexical arm; the second arm now pays for itself.
2. **MMR has measured three different values on three corpus sizes** - neutral
   at 91, worth a case at 153, neutral-and-slightly-negative at 266. Left on. A
   component that oscillates around zero as the corpus grows has not been
   resolved by this golden set, and the third reading is not more authoritative
   than the two before it.

**The CI floor was rebased 0.86 -> 0.74**, and that deserves stating plainly
because it looks like moving the goalposts. A pass-rate floor is a ratchet
against *regression*: it encodes "we were here, do not go back". It is
calibrated against a corpus, and replacing the corpus retires it - the same
retriever now reads 41/54 where it read 48/54, and neither number is a
regression. So the floor is re-derived on the new corpus with the tightness it
always had: 41/54 = 0.759 passes, 40/54 = 0.741 passes, 39/54 = 0.722 fails, so
one regression is tolerated and two are not. The alternative - keeping 0.86 -
would fail CI on every commit until someone tuned retrieval to a number that no
longer exists.

`make eval-external` was carrying `--min-pass-rate 0.95`, which nothing has met
since the 33-document corpus. A target nobody runs is a claim nobody checks; it
now matches CI.

**Rules.**
1. **A ratchet is calibrated against a corpus. Changing the corpus retires the
   ratchet** - re-derive it, and say so in the same breath. Keeping it is
   theatre and quietly deleting it is worse.
2. **Widen the corpus to find out how good your retriever is not.** Three
   widenings, three overturned conclusions, and every one of them made the
   instrument harder to fool.
3. **Decompose a drop before diagnosing it.** Four of these seven cases are an
   abstention threshold and three are retrieval; a fix aimed at either would
   have been measured against the other and looked like it failed.
4. **Check that the harness cannot have caused the failure before believing
   it.** Quarantine holds documents out per question and grew by nine here; had
   it caught an expected document, the case would have been unpassable and the
   cause invisible in the report.
5. **A threshold separating two populations that grow together does not scale
   with the corpus.** The floor sweep trades one-for-one across a 2.7x range,
   which says the answer is not a better threshold.

---

## L67 - Two sweeps were measuring a corpus that exists nowhere else

Chasing why `bcrypt` stopped being retrieved on the widened corpus led into
`scripts/base_weight_sweep.py`, which had already measured that mechanism (L58).
Its output began:

```
## primary: 341 documents, 20 cases
```

The primary corpus is **84** documents. The script defined it as `**/*.md`
rooted at the repository, and that glob is recursive, so it swallowed all 266
pages of `corpus/external/pypi`. It was running the *primary* golden set - 20
questions about this repository - against the repository diluted 4:1 with PyPI
package pages. `expansion_ab.py` had the same definition and the same defect;
its own decision record says "228 primary documents", which is the same
arithmetic one corpus-size ago. Every other script used the six-pattern
definition and 84 documents.

**Both scripts had produced recorded conclusions.**

### What the corrected runs say

`base_weight` decides how much the fused retrieval score counts against the
reranker's own adjustment. L58 measured the two on scales 34.5x apart, predicted
that raising it would recover cases the arms had ranked highly, and **falsified
that prediction**: on the corpus of the day the external set was best at 1.0 and
the primary set wanted 35, so it shipped as a compromise "that happens to favour
the corpus the gate runs on".

Corrected, and at 266 documents:

| base_weight | 1 | 2 | 3 | **4** | **5** | **6** | 8 | 12 | 16 |
|---|---|---|---|---|---|---|---|---|---|
| external | 41/54 | 41/54 | 41/54 | **43/54** | **43/54** | **43/54** | 41/54 | 40/54 | 40/54 |
| recall@8 | .8140 | .8140 | .8140 | .8605 | **.8721** | **.8721** | .8372 | .8256 | .8256 |
| primary | 18/20 | 18/20 | 18/20 | 18/20 | 18/20 | 18/20 | 18/20 | 19/20 | 18/20 |

Three samples wide, +2 cases and +0.058 recall on the corpus that gates, and
free on the other - whose pass rate does not move anywhere between 1 and 8 and
whose nDCG improves. **Shipped at 5.0.** The old primary column (16/20 at
base_weight 1, rising to 18 at 35) was the mixture talking; the real primary
corpus reads 18/20 at 1 and never goes below it.

So L58's hypothesis was right and its corpus was too small to show it. The
falsification stands as a record of what 153 documents could support, which is
why it is worth keeping rather than editing.

Downstream of the change, on the external gate: **41/54 -> 43/54**, recall
0.8140 -> 0.8721, nDCG 0.6872 -> 0.7294. The primary gate holds 18/20 with
recall 0.7812 -> 0.8125. The CI floor is ratcheted 0.74 -> 0.77 to hold it.

**Query expansion** was the other conclusion drawn from the mixture: "off by
default, because it made retrieval worse", later corrected to "off because the
gain is inframarginal". Corrected and re-measured, it is *neutral* - identical
pass rate and recall to four decimals at every setting on the gate corpus - and
converts one case on the 20-case primary corpus at one of four settings. Still
off, now for the third distinct reason, and this time the reason is that there
is nothing on the gate corpus to switch on for.

**MMR moved again too**, without being touched: worth a case at 153 documents,
neutral-to-negative at 266, worth a case again at 266 once `base_weight` became
5.0. A diversification step is a function of the ordering handed to it, so its
measured worth is really a measurement of everything upstream.

### The fix

`scripts/_corpora.py` holds one definition, every sweep imports it, and
`tests/test_documented_numbers.py` fails if a script grows its own or if the
primary definition matches an external page. The check is worth its keep: the
pre-fix definition matches 341 files, 266 of them external corpus pages.

**Rules.**
1. **A corpus definition is part of a measurement's result.** Two scripts with
   different definitions are two experiments, and only the printed document
   count says so - which is why every sweep here now prints it.
2. **`**/*.md` rooted at a repository is recursive and will find your test
   fixtures.** The corpus you evaluate against is the one the glob matched, not
   the one you meant.
3. **Re-run a falsification when its corpus changes.** L58 predicted an effect,
   failed to find it, and was right - the prediction needed 266 documents and
   a corrected corpus to show up. A negative result is dated evidence, not a
   closed question.
4. **When a shared constant moves, every measurement that depended on it is
   stale** - the ablation, MMR's worth and the expansion A/B all had to be
   re-run after `base_weight` changed, and each was measured at the old value
   an hour earlier.

---

## L68 - Every constant confirmed under the old configuration was a stale constant

L67 changed `base_weight` from 1.0 to 5.0 and ended with the rule that every
measurement depending on a moved constant is stale. This is that rule applied to
the rest of the retrieval constants, all of which were "swept over both corpora
and confirmed on plateaus" (L33) - at `base_weight` 1.0, on a corpus of 153
documents.

**`rrf_k` moved, 60 to 16.** 60 is the constant from the original TREC work,
carried unexamined. Re-swept at 266 documents with `base_weight` 5.0, 12-20 is a
plateau on *both* corpora simultaneously:

| rrf_k | 8 | 12 | 16 | 20 | 25 | 30 | 45 | 60 |
|---|---|---|---|---|---|---|---|---|
| external | 43/54 | 43/54 | **43/54** | 43/54 | 42/54 | 42/54 | 42/54 | 43/54 |
| recall@8 | .8837 | .8837 | **.8837** | .8837 | .8605 | .8605 | .8605 | .8721 |
| primary | 18/20 | 19/20 | **19/20** | 19/20 | 19/20 | 19/20 | 18/20 | 18/20 |

Less damping suits a fused score that now carries five times the weight it used
to. It also widens the arm-weight cliff from 1.64 to 3.29 (L65), which is a side
effect rather than a reason.

**`candidate_k` stayed at 40 and its recorded rationale did not.** L33 recorded
"a deeper candidate pool is *worse*, because it gives the reranker more chances
to promote the wrong document". Under the new fusion, 30 through 80 are level
and 80 is a single high sample (44/54) between 60 and 120 (43 and 42) - a peak,
so nothing moves, but the *reason* the old value survives is now the opposite of
the recorded one.

### Raising one side of a sum retires the other side

Two tests started failing on the `base_weight` change, and they were right to:

```
FAIL: test_a_trusted_source_outranks_an_identical_untrusted_one
FAIL: test_a_fresher_document_outranks_an_identical_stale_one
```

`authority` and `recency` are *tie-breakers*: what matters is their size
relative to the score whose ties they break. Multiplying the fused term by five
without touching them cut their influence by the same factor, and the property
they exist for - a trusted or fresher document outranking an otherwise identical
one - stopped holding. Nothing in the configuration says these numbers are
coupled; two tests did.

Rescaled to match, and the cost measured rather than assumed:

| | authority 0.12 | 0.6 | position 0.05 | 0.25 |
|---|---|---|---|---|
| external | 43/54 | 43/54 | 43/54 | **44/54** |
| primary | 19/20 | 19/20 | 19/20 | 19/20, nDCG .6157 -> **.6734** |

Authority is free, exactly as L62 predicted for a feature that does not vary
within candidate sets - it changes nothing on either corpus and restores the
tie-break. Position buys a case.

**And `position_weight` was left at 0.25 rather than 0.8, where it measures
better.** The external corpus improves monotonically all the way up - 46/54 and
recall 0.9186 at 0.8, with no plateau anywhere - while the primary corpus loses
recall past 0.35. A knob that only ever wants to go up on one corpus is
measuring that corpus's shape: PyPI pages open with the description that answers
the question, so "prefer the first chunk" keeps paying. That is a fact about the
pages. 0.25 is the principled value - the old weight times the change in
`base_weight` - and it is where the two corpora still agree.

**Recency's conclusion survived the rescale and its scale did not.** Re-swept at
the new `base_weight`: 0.0 reads 44/54, then 43, 43, 41, 38 at 0.1, 0.2, 0.4 and
0.8. Off is still best and still degrades monotonically (L61), but the *value*
that delivers the documented behaviour moved from 0.08 to 0.8, and the test that
pins that behaviour had 0.08 hardcoded. The authority test now passes `None` and
reads the shipped default, so it cannot pin a value the reranker has left.

### Where the session's changes leave the gate

| | before this session | now |
|---|---|---|
| external corpus | 153 pages | **266 pages** |
| external pass | 48/54 | **44/54** |
| external recall@8 | 0.9070 | 0.8953 |
| primary pass | 18/20 | **19/20** |
| primary recall@8 | 0.7812 | **0.8750** |

The external column looks like a loss and is not: on the *same* 266-page corpus
the retriever went 41/54 to 44/54 and recall 0.8140 to 0.8953. The 48/54 was
measured on a corpus 43% smaller that flattered it (L66). The floor is ratcheted
0.77 to 0.79.

**The primary floor was deliberately not ratcheted** to match its 19/20. That
corpus's pass rate moves by a case when a session writes documentation, in both
directions, with no retrieval change at all (L63) - so a tight floor there would
fail CI on prose. Only the corpus that cannot describe this repository gets a
tight ratchet.

**Rules.**
1. **A constant confirmed under a configuration is confirmed *for* that
   configuration.** Four constants were on documented plateaus; one moved, and
   two of the other three changed value or rationale.
2. **When a knob scales one term of a sum, every other term's meaning changed.**
   The priors were not touched and were retired anyway. Ask what a number is
   relative to before deciding it is unaffected.
3. **A test that hardcodes a default will pin the value the code has left.**
   `weight=None` and read the shipped default: then the test measures the
   system rather than a copy of it.
4. **A knob that improves monotonically on one corpus with no plateau is
   measuring that corpus.** Stop at the principled value and write down what the
   ramp was telling you.

---

## L69 - The reported confidence became a constant, and the code that broke it was mine

L68's own rule 2 says a knob that scales one term of a sum changes what every
other term means. It found the two tie-breaker priors that way. It missed one,
two files downstream, and the miss was visible in the first query I ran
afterwards:

```
$ ooda query "What is the capital of France?"
... confidence=1.0  generator=extractive  coverage=1.0
```

Confidence 1.0 for a question a corpus of PyPI pages cannot answer.

**`_confidence` divides by constants that assume a score scale.** It reads
`ScoredChunk.score`, whose size is set by `HeuristicReranker.base_weight`:

    strength   = min(1, top / 0.6)
    separation = min(1, (top - fifth) / 0.25)

At `base_weight` 1.0 the top score sat around 0.2-0.4 and both terms varied. At
5.0 the smallest top score over 48 answered goldens is **1.146**, so strength is
pinned at 1.0 for every case. Measured:

| | before the rescale | after |
|---|---|---|
| confidence range | 0.30 - 1.00 | 0.87 - 1.00 |
| cases reporting >= 0.99 | a handful | **32 of 48** |
| AUC, right vs wrong answers | 0.665 | **0.519** |

An 0.519 AUC is a coin flip. The number was still being printed, still being
stored in the journal, and no test noticed, because every test that asserts
confidence asserts a floor it still clears.

**The fix is not a recalibration.** Re-tuning 0.6 and 0.25 to the new scale
would work until the next weight change, which is the same bug on a timer.
`rerank_relevance` is a coverage-times-answerability product, bounded 0..1 by
construction whatever any weight does, and the gate has always used it for
exactly that reason. Measured over 35 right and 13 wrong answers
(`scripts/confidence_ab.py`):

| formulation | AUC | best TPR-FPR |
|---|---|---|
| current, from the total score | 0.519 | 0.097 |
| relevance only | 0.703 | 0.435 |
| swap top -> relevance, keep the raw margin | 0.691 | 0.455 |
| **relevance, relevance margin, coverage** | **0.665** | **0.455** |
| relevance, margin as a share of top, coverage | 0.673 | 0.426 |

The relevance-based forms are indistinguishable from one another at this sample
size and all of them beat the incumbent by 0.15 of AUC. **Shipped: relevance,
relevance margin, coverage** - the only one whose every input is scale-free
*and* keeps the three signals the docstring promises. Confidence now spans
0.508 to 1.000 over 33 distinct values, and the capital of France reports 0.70.

**L60 predicted this and aimed at the wrong trigger.** It found the same
inconsistency - the gate uses relevance, the reported confidence uses the total -
measured it inert, and wrote that it "would bite on a corpus with mixed
authority or real age spread, which is exactly what the priors were built for".
It bit on neither. It bit because someone changed a weight in a different file.

**Rules.**
1. **A constant that divides a score is a claim about that score's scale.**
   Grep for the divisors when a scoring weight moves: `/ 0.6` two modules away
   is not something a test failure will find for you.
2. **Prefer a bounded input to a calibrated constant.** `rerank_relevance` is
   0..1 by construction; anything built on it survives a rescale, and the
   alternative is a recalibration due every time a weight moves.
3. **A signal nobody gates on gets no test that can fail.** Confidence is
   printed, journalled and returned to callers, and its collapse to a constant
   was invisible to 387 tests. Assert the *spread* of a reported number, not
   just its floor.
4. **When a prediction names the trigger, the trigger is the weakest part of
   it.** L60 was right that the inconsistency would bite and wrong about what
   would set it off, which cost nothing here only because the fix is the same
   either way.

---

## L70 - The audit that found nothing, and what "nothing" measured

L69's first rule is to grep for the divisors when a scoring weight moves. Doing
that across the tree: `min_top_score` is scale-dependent and has 200x of margin,
`authority/1.5`, `df/total`, the IDF normaliser and `_code_likeness` are all
bounded by construction, and nothing thresholds the reported confidence - it is
printed and journalled and gates nothing, which is exactly why it could rot.

That leaves the reranker's own two weights, swept at `base_weight` 1.0 and never
since. Both are flat now - 44/54 and 19/20 at every setting, nDCG wobbling in
the third decimal - so nothing moved. **The flatness is the finding.** Measured
on the same index, one knob, two configurations:

| coverage_weight | 0.25 | 0.45 (shipped) | 0.8 |
|---|---|---|---|
| old: `base_weight` 1, `rrf_k` 60, old priors | **44/54** | 41/54 | 40/54 |
| now: `base_weight` 5, `rrf_k` 16 | 44/54 | 44/54 | 44/54 |

A knob with a four-case span became inert. This session moved the ordering's
centre of gravity off the lexical re-scorer and onto the fusion, and that is
what it looks like from the inside: `rrf_k`, previously never examined, became
worth two cases; `coverage_weight` and `phrase_weight`, previously worth four,
became worth none.

**And the uncomfortable half.** The old configuration reaches 44/54 too, by
dropping `coverage_weight` to 0.25 - one knob, not three. Two different routes
to the same pass rate, and a session that reports only the route it took has
credited the wrong cause. The shipped route is still the better one, on evidence
rather than on ownership:

|  | pass | recall@8 | nDCG@8 | neighbours |
|---|---|---|---|---|
| old config, `coverage_weight` 0.25 | 44/54 | 0.8837 | 0.7188 | 41/54 and 40/54 |
| shipped | 44/54 | **0.8953** | **0.7505** | **44/54 either side** |

Better on both metric columns, and sitting in a region where its neighbours
score the same rather than three cases worse. A configuration whose neighbours
agree with it is one whose next corpus change is less likely to move it - which
is the property this repository has been buying, one sweep at a time, for
sixty-odd learnings.

**Rules.**
1. **Report the routes you did not take.** A gain reachable by a knob you did
   not touch is a fact about the system, and omitting it credits your change
   with someone else's effect.
2. **Prefer the flat neighbourhood to the equal peak.** Two settings with the
   same pass rate are not equivalent if one of them is surrounded by worse ones:
   flatness is robustness against the next corpus.
3. **An audit that finds nothing has still measured something** - here, that the
   knobs a previous session tuned no longer do anything, which is the clearest
   statement available of what this session actually changed.
