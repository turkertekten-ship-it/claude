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
