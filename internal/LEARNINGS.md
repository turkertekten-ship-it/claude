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
| structlog | 42 | **2** | not retrieved |
| responses | **14** | **5** | not retrieved |
| freezegun | 331 | 107 | not retrieved |

> **Correction (L66).** The dense column above originally read `-` for all three,
> and that was a broken probe rather than a measurement: it called
> `retriever.index`, which does not exist, so the search returned an empty list
> and every rank came back "not found". The real ranks are shown. They change the
> reading - `responses` is inside *both* arms' candidate sets and still demoted,
> which is a stronger claim than the entry made, and `freezegun` is reachable at
> a larger window rather than absent.

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

## L63 - The smallest weight was the most load-bearing

Re-running the zero-one-weight-at-a-time ablation, because every input to the
original had changed - the corpus tripled, `coverage_power` went to 2.0, recency
went live and then off, authority turned out to vary. External, 54 cases:

| weight zeroed | its value | pass | effect |
| --- | --- | --- | --- |
| coverage_weight | 0.45 | 48/54 | -1 |
| phrase_weight | 0.25 | 48/54 | -1 |
| authority_weight | 0.12 | 49/54 | **none** (L62) |
| recency_weight | 0.0 | 49/54 | none (already off) |
| **position_weight** | **0.05** | **46/54** | **-3** |

**The smallest weight costs the most when removed.** Position carries a ninth of
coverage's weight and three times its effect. Nothing about the configuration
suggested looking there.

The mechanism is a property of these corpora rather than of ranking in general:
the first chunk of a PyPI page is the package's own one-line summary, and "which
library does X?" is answered *there* - not in installation instructions, a
changelog, or contributor notes. The same holds for a source file, whose first
chunk carries the module docstring. A prior for "the top of a document states
what it is" happens to be almost exactly the question both golden sets ask.

**Swept, and 0.15 dominates on both corpora:**

| weight | 0.0 | 0.05 (was) | **0.15** | 0.3 | 0.45 |
| --- | --- | --- | --- | --- | --- |
| external pass | 46 | 49 | **49** | 49 | 48 |
| external nDCG@8 | 0.7284 | 0.7538 | **0.7944** | 0.7965 | 0.7946 |
| primary pass | 16 | 16 | **17** | 17 | 16 |
| primary MRR | 0.5350 | 0.6042 | **0.7312** | 0.7312 | 0.7438 |
| primary nDCG@8 | 0.5885 | 0.6327 | **0.7246** | 0.7175 | 0.7079 |

It is a plateau, not a peak: external holds 49/54 from 0.05 to 0.3, primary
17/20 from 0.15 to 0.3. Above that both decline, and they decline in a telling
way - ordering keeps improving on external while recall falls, which is a
position prior beginning to answer confidently from the top of the wrong
document.

**Shipped, measured through the real configs rather than the sweep harness:**

| | before | after |
| --- | --- | --- |
| external | 48/54 | **49/54** (0.907) |
| external recall@8 | 0.9070 | **0.9302** |
| external nDCG@8 | 0.7460 | **0.7888** |
| primary | 19/20 | 19/20 |
| primary nDCG@8 | 0.6463 | **0.6814** |

Every metric improves on both corpora and none regresses - the first change this
session that is not a trade. The gate margin goes from 0.039 to 0.057 above the
0.85 floor.

**Rules.**
1. **Weight magnitude is not importance.** The only way to know what a term
   contributes is to remove it. A 0.05 coefficient was doing more work than a
   0.45 one, and no amount of reading the scoring function would show that.
2. **Re-run an ablation when its inputs change, not when you suspect it.**
   Every input to this one had changed and the conclusion was four cycles old.
   The cost was one script; the result was the session's best number.
3. **A prior that matches the shape of your questions is worth more than a
   general one.** "The top of a document says what it is" is not a deep
   retrieval principle, and it answers most of what both golden sets ask.

---

## L64 - Two weights measured for the first time, and left alone on purpose

`coverage_weight` and `phrase_weight` had never been swept - only zeroed. After
the corpus tripled, `coverage_power` doubled and `position_weight` tripled, the
balance among them had shifted underneath without anyone looking.

**`phrase_weight` is at its optimum**, which is a stronger result than
"acceptable":

| phrase_weight | 0.05 | 0.15 | **0.25** | 0.40 | 0.60 |
| --- | --- | --- | --- | --- | --- |
| external nDCG@8 | .7725 | .7846 | **.7944** | .7829 | .7742 |
| primary nDCG@8 | .6986 | .7211 | **.7246** | .6796 | .6714 |

A single interior maximum on each corpus, falling away on both sides. Nothing to
do.

**`coverage_weight` is the interesting one:**

| coverage_weight | 0.20 | 0.35 | **0.45** | 0.60 | 0.80 |
| --- | --- | --- | --- | --- | --- |
| external pass | 48 | 49 | **49** | 49 | 49 |
| external nDCG@8 | **.8179** | .8000 | .7944 | .7858 | .7694 |
| primary pass | 17 | 17 | **17** | 16 | 16 |

**Ordering improves monotonically as the weight falls**, and the best ordering
in the whole sweep sits at 0.20 - where a case breaks. 0.35 keeps every case and
gains 0.006 of nDCG over the shipped 0.45.

**Left at 0.45, and the reason is robustness rather than the number.** 0.35 is
one step from the cliff at 0.20; 0.45 has margin on both sides. Six thousandths
of nDCG does not buy that margin away - the same argument that keeps
`min_relevance` off the peak of its own curve. Taking a small gain by moving to
the edge of a plateau is how a configuration becomes fragile without anybody
deciding that it should.

**What the shape says, which is worth more than the setting.** Coverage and
ordering quality are in tension here: the more the reranker weights term
coverage, the worse it orders. That is consistent with everything L48 through
L58 measured - coverage is computed from an IDF that ranks the discriminating
query term first only 29 times in 40, so leaning on it harder propagates a
partly-wrong signal. The 0.024 of nDCG between 0.45 and 0.20 is the price of
that weighting, and anything that fixed the underlying ordering would collect it.

**Rules.**
1. **Zeroing a weight and sweeping it answer different questions.** The
   ablation said both of these matter; only the sweep says whether their values
   are right, and one of them turned out to be exactly right and the other
   deliberately not optimal.
2. **Prefer the middle of a plateau to its better-scoring edge.** The edge is
   worth a rounding error and costs the margin that makes a default survive the
   next corpus change.
3. **A monotone trend inside a sweep is a finding even when you do not act on
   it.** "Ordering improves as coverage's share falls" names a cost the current
   design is paying and tells the next cycle what a fix would be worth.

---

## L65 - Two guards that never fire, for two different reasons

`AnswerConfig` has two thresholds nobody had measured: `min_top_score = 0.005`
and `min_coverage = 0.5`. Across all 74 golden questions on both corpora,
**neither has ever fired.**

| | smallest observed | floor | margin |
| --- | --- | --- | --- |
| top score, external | 0.2541 | 0.005 | 51x |
| top score, primary | 0.5099 | 0.005 | 102x |
| citation coverage, both | **1.000** | 0.5 | never below |

L25 says "I could not make it fire" and "it cannot fire" are different claims,
and only the second justifies calling a safety check dead. So I computed the
bound instead of sampling for it - and the two guards turn out to be dead in
*different senses*, which is the finding.

**`min_top_score` is structurally unreachable.** The reranker's total carries
two query-independent priors present whatever the chunk says:

```
authority_weight * (1.0/1.5)  = 0.080   # metadata omits authority -> default 1.0
position_weight  * 1.0        = 0.150   # ordinal 0
                                0.230   # a chunk matching NOTHING scores this
```

46x the floor, and still 0.089 at ordinal 100. No chunk in a non-empty result
list can fall under 0.005.

This is exactly the failure `rerank.py` warns about four lines above the code
that produces the number: *"Fold them into one number and the total stops being
usable as an 'is this relevant at all' signal."* `min_top_score` reads the
total, so it cannot do its stated job; `min_relevance` beside it reads relevance
alone and subsumes it entirely.

**`min_coverage` is unreachable in this configuration, not structurally.** The
extractive generator emits only sentences it can cite, so citation coverage is
1.000 at the minimum across all 74 questions. The Claude generator can produce a
sentence it cannot attribute - which is precisely what this guard exists to
refuse. It is live under a configuration the evals do not exercise.

**Neither was deleted, and the distinction is why.** One is dead under today's
weights and becomes live the moment `authority_weight` and `position_weight` are
zeroed - a plausible configuration, and one this project has swept. The other is
dead under today's *generator* and live under one that ships in the same
repository. Both cost a comparison. What they lacked was a label, and a test that
computes the bound rather than trusting the docstring.

**Rules.**
1. **Compute a guard's bound, do not sample for it.** Seventy-four questions
   never firing is weak evidence; a floor of 0.230 against a threshold of 0.005
   settles it, and took arithmetic rather than a corpus.
2. **"Never fires" has several causes and they need different responses.**
   Structurally impossible, impossible under this configuration, and merely
   untriggered look identical in a test run and imply different actions.
3. **A guard that reads the wrong quantity is worse than a missing one**,
   because it occupies the place where the real check would go. This one has sat
   beside the check that does its job for as long as both have existed.

---

## L66 - A smaller candidate set retrieves better, and my probe had been lying

Two findings, and the second one corrects a table I wrote three cycles ago.

**The probe first.** Chasing where failing cases are lost, I had reported dense
ranks as "not found" for all three. The probe called `retriever.index` -
`HybridRetriever` has no such attribute, so `hasattr` was False, the search list
was empty, and every lookup returned None. **An absence produced by asking
nothing looks exactly like an absence produced by asking and finding nothing.**
That is L55's rule ("no failures" is also what nothing looks like) arriving in my
own diagnostic, one cycle after I wrote it down.

The real ranks, via `store.vector_index(embedder.fingerprint)`:

| expected | lexical | dense | inside k=40 |
| --- | --- | --- | --- |
| structlog | 2 | 42 | lexical only |
| responses | 5 | **14** | **both** |
| freezegun | 107 | 331 | neither |

`responses` is found by *both* arms well inside the candidate set and still does
not survive - a stronger version of the demotion claim than L58 made, on
evidence L58 did not have.

Re-measured properly over all 43 goldens with an expected source: **41 kept, 1
demoted (`responses`), 1 unreachable (`freezegun`)**. `structlog` is no longer
among them - raising `position_weight` (L63) fixed it.

**Then the window itself.** `candidate_k` had never been measured:

| candidate_k | 20 | 40 (was) | 80 | 120 | 200 |
| --- | --- | --- | --- | --- | --- |
| external pass | 49/54 | 49/54 | 49/54 | 48 | 48 |
| external recall@8 | .9302 | .9302 | **.9419** | .9186 | .8953 |
| primary pass | **18/20** | 17/20 | 16/20 | 16 | 16 |
| external latency | 85ms | 98ms | 133ms | 168ms | 233ms |

**More candidates is worse.** Through the shipped configs, halving it to 20
keeps both pass rates, improves nDCG@8 on both (0.7888 -> 0.7954 external,
0.6814 -> 0.6830 primary) and cuts latency 15% and 26%.

That is only surprising if the reranker is assumed correct. It is partly wrong
by construction - coverage rests on an IDF that ranks the discriminating query
term first in 29 of 40 goldens (L48) - so each extra candidate is another chance
to promote something the arms had correctly ranked low. Recall@8 *does* peak at
80 while the pass rate does not follow, because the documents arriving between
40 and 80 are ones the reranker then mis-orders. Two metrics disagreeing is the
signal, again (L58).

**And it closes an avenue rather than opening one.** `freezegun` sits at lexical
rank 107; reaching it needs k >= 110, which costs a case on each corpus. It is a
retrieval gap, not a windowing one, and no setting of this parameter recovers it.

**A test I wrote in this cycle was wrong in an instructive way.** To assert both
arms request the same window I counted occurrences of `k=config.candidate_k` in
the source and asserted two. There are four - two arms, the expansion arm, and
the cap on the fused list - so it failed for being wrong about the
implementation rather than for finding a defect. Replaced with a behavioural
test on `dense_hits` and `lexical_hits`. **A source-string assertion breaks on a
rename and stays silent on a behaviour change, which is the wrong way round.**

**Rules.**
1. **A diagnostic that returns nothing must prove it asked something.** Assert
   the probe's own preconditions - here, that the index it searched was
   non-empty - or an empty result will be read as a finding.
2. **Bigger candidate sets are not free recall.** They are only an improvement
   if whatever ranks them is trustworthy; against an imperfect reranker they
   are additional opportunities to be wrong, and the metric that shows it is
   the one you were not optimising.
3. **Do not assert on source text when you can assert on behaviour.**

---

## L67 - Six parameters tuned on 74 cases, and nothing held out to detect it

Over this session I changed six defaults, each on a measurement: `coverage_power`
1.0 -> 2.0, `gate_coverage_power` None -> 1.0, `position_weight` 0.05 -> 0.15,
`candidate_k` 40 -> 20, `recency_weight` 0.08 -> 0.0, plus re-confirming
`min_relevance`. Every one was justified by a sweep over the same 74 golden
questions.

**Six knobs against 74 cases is enough to fit noise, and I had nothing held out
to tell the difference.** Every "measured improvement" in this session shares
that weakness, and no amount of care within a sweep detects it.

**The held-out set.** 111 of the 153 corpus documents are referenced by no
existing golden. `evals/goldens-heldout.jsonl` is 22 questions - 18 positive, 4
negative - whose expected sources are drawn only from those, written from
general knowledge of what each package does rather than from reading its page,
so their phrasing is not derived from the text they have to retrieve. One
question trips the contamination detector and is quarantined automatically.

**The result: the tuning transfers.**

| | before tuning | shipped |
| --- | --- | --- |
| **held-out** pass | 18/22 | **19/22** |
| **held-out** recall@8 | 0.8889 | **0.9444** |
| **held-out** nDCG@8 | 0.7771 | **0.8029** |
| external (tuned on) pass | 46/54 | 49/54 |
| external (tuned on) nDCG@8 | 0.7353 | 0.7938 |

Better on every metric on cases the parameters never saw. And **the gain is
smaller on held-out than on the tuned set** - +0.026 of nDCG against +0.059,
+4.5% of pass rate against +6.5%. That gap is the fitting: roughly half of the
measured improvement on the tuned set does not transfer, and the rest is real.

That is the most useful number this session produced about its own method. It
does not say the tuning was wrong; it says a measured gain on a tuned set should
be read at roughly half its face value until something independent confirms it.

**Kept out of the gate on purpose.** CI runs it with `--min-pass-rate 0.6`,
loose enough to catch only catastrophe. A tight floor would make it one more
thing to tune against and destroy the property that makes it worth having - the
same reason the evaluation harness itself deserved adversarial attention (L28).
Its value is entirely in never having been optimised for.

**Rules.**
1. **Count your knobs against your cases before trusting a sweep.** Six against
   seventy-four should have prompted this at the third parameter, not the sixth.
2. **A held-out set has to be built before you want it and never scored
   against.** Its only property is independence, and one tuning decision made on
   it spends that permanently.
3. **Discount a tuned-set gain by what a held-out set does not reproduce.** Here
   that factor was about a half, measured rather than assumed - and it is the
   right lens for re-reading every improvement recorded above.

---

## L68 - The non-negotiables re-checked, and one apparent hole that is a design

Twenty cycles of change later - redaction moved to the boundary type, front
matter added, the corpus rebuilt and dated, six defaults retuned - the five
stated guarantees were due to be run rather than read (L47's rule). All five
hold, and the interesting part is a check that *looks* like a failure.

| non-negotiable | check | result |
| --- | --- | --- |
| 1. zero required deps | import every module on bare 3.11 | all import, no third party loaded |
| 2. provenance load-bearing | 1810 chunks, orphans and missing URIs | 0 and 0 |
| 3. everything bounded | budget parameters per network module | http 10, crawler 9, builder 2 |
| 4. degrade, don't die | fetch a blocked host | `PolicyDeniedError`, handled |
| 5. secrets redacted | see below | holds |

**The apparent hole.** Eight committed corpus files contain text the redactor
matches. Looking at what, rather than counting:

```
pyjwt         eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...   the canonical example JWT
environs      https://sloria:secret@localhost           a README example
asyncpg       password='password'                        a docs example
itsdangerous  token = auth_s.dumps({"id": 5, ...})       a variable named token
```

Not one is a credential. They are public documentation examples, and the last is
a false positive on an assignment.

**And they are supposed to be there.** The corpus is a faithful copy of what was
fetched; the manifest hashes that text; redacting it would falsify the
provenance this project treats as load-bearing, and would also destroy the best
test material available for the redactor. Non-negotiable 5 is about *the index* -
"before text can reach an index file" - and the index is clean.

Measured end to end: **12 redactable lines in the committed corpus, 0 appearing
verbatim in the built index, exactly 12 `<redacted` markers in it.** A perfect
correspondence, on text nobody wrote as a fixture.

Both halves are now tests, and the first exists because of L57's lesson: the
assertion "no credential shapes reach the index" passes trivially if the corpus
stops containing any, and a vacuous pass looks exactly like a working redactor.
So one test asserts the corpus still contains at least five such lines, and the
other asserts none of them reach the index.

**Mutation testing then said the test had no teeth, and mutation testing was
wrong twice before it was right.** Removing the redaction from
`RawDocument.__post_init__`: survived. Removing it from the filesystem connector
as well: survived. That looked like a vacuous test - until a grep for every call
site found a **third** layer, `pipeline.py:92`, `redact_secrets(clean(raw.text))`.

| removed | result |
| --- | --- |
| boundary only | survived |
| connector only | survived |
| pipeline only | survived |
| **all three** | **caught** |

So redaction is three-deep, each layer independently sufficient, and the test
asserts the *invariant* rather than any one mechanism - which is the correct
shape for a safety guarantee and the reason no single mutation moves it.

**Two of the three earlier "survived" results were my own harness lying.** A
pattern with the wrong indentation, and an `assert` on a short string guarding a
`str.replace` of a longer one: `replace` does nothing quietly, the suite runs on
unmutated code, and the harness prints SURVIVED. That is a false negative in the
one tool whose job is finding false negatives - L55's rule, for the third time
this session, in my own scratch script. The harness now compares the file before
and after and refuses to report anything if the text did not change.

The redundancy has a measured cost: `redact_secrets` is ~277ms over the corpus,
so three passes is roughly 10% of an 8s index build. Worth it for a guarantee
about credentials, and worth knowing rather than discovering.

**Rules.**
1. **When a check looks like a violation, read what it matched before believing
   it.** Eight files "containing secrets" were eight files containing a JWT from
   a specification and the word `password` in an example.
2. **State which artifact a guarantee is about.** "Redacted at the connector
   boundary" and "no credential shapes anywhere in the repository" are different
   promises, and only one of them is compatible with keeping a faithful copy of
   what was fetched.
3. **Pair an absence assertion with a presence assertion.** "Nothing leaked"
   needs "and there was something to leak", or the test measures the corpus
   rather than the code.

---

## L69 - An empty index and a total quality collapse produce identical reports

The commit that added the held-out set turned CI red, and the report looked
alarming: **22 of 22 cases failing, every metric 0.0, "unexpected abstention"**
on each one. That reads as the retriever having stopped working entirely.

It was a workflow mistake. I had added the held-out eval as a step *before* the
step that builds the index it evaluates - the external `index` command runs
inside the "Evaluate against the external corpus" step, further down. So the
eval ran against an index that did not exist.

**The two are indistinguishable in the output**, and that is the defect worth
fixing. `none of ['tqdm'] retrieved; got []` is exactly what a missing index and
a broken retriever both produce, and nothing in the report says which. The
latency gave it away - 0.07ms per query, no work done - and only because I
happened to look.

`cmd_eval` now refuses: it checks the chunk count first and exits **2** with
`refusing to evaluate: ... holds no chunks. Run 'index' first`. Two rather than
one on purpose - **1 is the exit code for a quality regression**, and a missing
prerequisite reported as a regression is the same conflation one level up. All
three mutations are caught, including "exit 1 instead of 2".

This is the project's own rule about empty results arriving in the tool that
reports on everything else: *empty is blocked, filtered, deduplicated or
genuinely absent - say which.* The eval harness had been unable to say.

**Two smaller things from the same half hour, both mine.** Checking the new exit
code I wrote `cmd ... | tail -2` then `echo $?`, which reports `tail`'s status
and printed a confident `exit code: 0` for a command that had exited 2. And the
CI step I added created this failure precisely because a barely-gated
observational step still runs in a sequence, and I had thought about the floor
rather than the ordering.

**Rules.**
1. **Distinguish "the input was missing" from "the answer was wrong" in the
   output, not just in the exit code.** They are the same shape - nothing came
   back - and only one of them means what the report says.
2. **Use a distinct exit code for a broken precondition.** Sharing one with a
   quality failure guarantees the two get confused by whoever reads CI next,
   which was me, ten minutes later.
3. **`$?` after a pipeline is the last command's status.** Two of this
   session's confident measurements have been of the wrong object; this one
   claimed a fresh exit code that was `tail`'s.

---

## L70 - A guard that only fires as a section's first unit never fires

`_pack_units` had a branch for a unit bigger than the ceiling: emit it whole
rather than cut it at an arbitrary point. The guard was
`if unit_tokens > ceiling and not buffer`.

`not buffer` is the whole bug. A markdown section opens with its own heading
line, so by the time the oversized unit arrives the buffer already holds a
two-token `#### Fixes` and the branch is skipped. Every one of the five
over-ceiling chunks in the external corpus sat behind such a heading. The
largest was 1,332 estimated tokens against a `hard_max_tokens` of 640 - 2.1x a
ceiling whose docstring said a chunk "may not exceed" it.

**What was actually in them.** Not minified files, which is what the branch was
written for. `split_sentences` breaks on sentence punctuation or a blank line,
and a markdown bullet list has neither: pydantic's 54-entry changelog list came
through as one 1,330-token "sentence" with 40 newlines and zero occurrences of
`. `, and psutil's `>>>` example block as a 1,283-token one with 133 newlines.
So one retrieval unit held 54 unrelated changelog entries, and a query matching
any single bullet dragged in the other 53.

The fix is two changes, and the first is the one that mattered: drop `not
buffer` and flush what is buffered, then re-split the oversized unit on line
boundaries - the natural boundary in exactly the blocks that reach here - with
a genuinely unsplittable single line still emitted whole. External corpus:
5 over-ceiling chunks -> 0.

**It measured as nothing, and that is the honest result.** Gate 49/54 and
held-out 19/22, every metric identical to four decimals. Checked rather than
assumed: `pydantic`, `psutil` and `autopep8` are the expected answer to zero of
the 76 golden questions across both sets. So this is *unmeasurable here*, not
*ineffective* - the distinction the protocol asks for, and the reason to record
it as a correctness fix rather than dress it up as an improvement.

**Rules.**
1. **A guard conditioned on "nothing else has happened yet" fires only on
   synthetic input.** Real documents have preambles, headings and front matter.
2. **A fallback needs its output checked, not just its trigger.** "Emit it
   whole" fired correctly for years and produced a 1,332-token chunk; nothing
   looked at what came out.
3. **A splitter named for one structure returns garbage on another.**
   `split_sentences` is a sentence splitter and a bullet list is not sentences;
   the repair belongs where the bound is enforced, not in the splitter.

---

## L71 - The regression test passed against the bug

Having fixed L70 I wrote the regression test for it, ran the mutation harness,
and it reported **SURVIVED** for restoring the exact `and not buffer` guard.
The test could not catch the bug it was named after.

The fixture was `#### Fixes\n{items}`. `_SENT_RE` breaks on a blank line, and a
single newline is not one - so the heading and the list arrived as *one* unit,
the buffer was empty, and the pre-fix guard handled it correctly. The real file
has a blank line after the heading, which is precisely what makes the heading
its own unit. My test comment claimed "the heading here is what makes this a
regression test"; the heading was there and did nothing.

One character of whitespace separated a test that pins the fix from a test that
would have gone green forever on broken code.

**Also in this cycle, the same shape twice.** The first patch I wrote for L70
changed only the branch body and left `not buffer` alone. Re-running the probe
showed the external corpus unchanged at 1,827 chunks and 5 violations - and
because the protocol says *unchanged is ineffective, already correct or
unmeasurable - say which*, I went looking instead of moving on. The answer was
"the code never ran".

**Rules.**
1. **Copy the fixture's shape from the input that produced the bug**, whitespace
   included. A fixture written from memory tests the code you imagined.
2. **Mutation-test a regression test against the specific line it exists to
   pin**, not against a general mutant. "The suite catches something" is not
   "this test catches this".
3. **Re-measure after every patch, including the obvious one.** Two patches this
   cycle looked right and did nothing; both were caught by re-running a probe
   that took four seconds.

---

## L72 - 165 features per bucket, and relieving the crowding made it worse

`HashingEmbedder` projects tokens and character 4-grams into `dim` buckets by
signed feature hashing. Its docstring says signed hashing makes collisions
"cancel in expectation instead of accumulating into a systematic bias" - which
is true of the expectation and silent about the variance, and nobody had ever
measured the load it was talking about.

The external corpus has **126,791 distinct features** and `dim` is 768:
**165 features per bucket**, with not one bucket empty at any dimension tried
up to 12,288. Every coordinate of every document vector is a signed sum of
about 165 unrelated features. That looks like an obvious, unexamined ceiling on
the dense arm, and the prediction was that raising `dim` would help.

It does not, and the shape of the non-result is the point:

    dim            |  256   768*  1536  3072  6144
    features/bucket|  495   165    83    41    21
    gate pass /54  |   48    49    48    48    49
    gate MRR       | .7566 .7643 .7566 .7461 .7674
    gate nDCG@8    | .7831 .7958 .7841 .7766 .7981
    held pass /22  |   19    19    19    19    19
    index time     | 3.2s  3.4s  3.5s  3.8s  5.1s

**I wrote this entry up with the first four rows and had to correct it.** With
`6144` still running, the table read as a clean monotone decline and I recorded
"768 is the peak and every larger dimension is worse". Then 6144 came in at the
top of the table. Down, down, down, up is not a trend; it is noise at a
resolution of one case in 54, and the four-row version had a mechanism ready to
explain it.

**What this establishes.** The collision-load argument is falsified: relieving
crowding 24-fold moves gate pass by one case in a direction that does not hold,
and held-out sits at exactly 19/22 across the whole 24x range. **Dimension is
not a lever here**, and 6144 costs 50% more index time and eight times the
vector storage for it. It also does not establish that 768 is optimal in any
deep sense: every other retrieval parameter in this project was tuned *at* 768,
so part of what any peak here measures is the rest of the system being fitted
to it.

The hypothesis the four-row table invited - that collisions act as an accidental
smoothing, since character n-grams exist to blur "chunking" into "chunked" - is
exactly the kind of story a noisy monotone trend attracts. It may still be true;
this measurement neither supports nor refutes it, and testing it would mean
varying `ngram_size` and `use_ngrams` against `dim`, which has not been done.

**Rules.**
1. **A load factor nobody has measured is not evidence of a bottleneck, and
   measuring it is not either.** 165:1 is a real number and pointed the wrong
   way; only the sweep settled it.
2. **Do not read a trend off a partial sweep.** Three points fell in a line, I
   named the peak and reached for a mechanism, and the fourth point landed
   above the peak. Wait for the last row, especially the slow one - it is slow
   because it is the extreme, which is where a trend is confirmed or broken.
3. **Non-monotone is the tell for noise.** Where a parameter has a real effect
   the effect has a direction; alternating 48/49/48/48/49 is a ruler that
   cannot resolve what is being asked of it.
4. **A parameter that looks untouched may still be load-bearing through
   everything tuned around it.** "Best in the sweep" and "optimal" come apart
   when the sweep moves one knob and six others were fitted at its current
   value - say which one you measured.

---

## L73 - The decision record argued from evidence that no longer existed

ADR 0004 decides for hybrid retrieval and backs it with an ablation table. The
table already carried an unusual amount of self-knowledge - it opens "this table
has now been wrong three times" and explains each. It was wrong a fourth time,
and I found it only because the dense-dimension sweep (L72) made me look at what
the arms were currently worth.

Six retrieval parameters and two chunking defects had changed underneath it.
Every row moved, and two readings inverted:

| configuration | was | now |
|---|---|---|
| hybrid | 47/54, recall 0.872 | 49/54, recall 0.9302 |
| lexical only | 47/54, recall 0.861 | 49/54, recall 0.9186 |
| dense only | 44/54, recall 0.814 | 42/54, recall 0.7209 |
| no rerank | 38/54 | 39/54 |
| no MMR | 46/54, prec 0.238 | 49/54, prec **0.2587** |

The ADR's headline sentence - "hybrid beats either arm alone on pass rate,
recall, MRR and nDCG" - is now false in its first clause: hybrid ties
lexical-only at 49/54 and leads only on the metric columns. And MMR, which the
previous refresh had found "worth a case and 0.023 of recall", now costs 0.0116
of precision on external and buys 0.0013 of nDCG.

**The part I nearly got wrong.** I wrote "MMR has reversed a fourth time and is
back to costing more than it buys" from the external table, which is the gate
and therefore the table one reads. The same run's primary-corpus table has MMR
earning a case *and* recall *and* precision (19/20 and 0.8750 against 18/20 and
0.8125). MMR is not harmful; it is corpus-dependent, exactly as `base_weight`
turned out to be (L58). Publishing the external row alone would have recorded a
fact about one corpus as a fact about the component.

The likely mechanism for both reversals is one parameter: `candidate_k` was
halved to 20 this session. Less redundancy reaches MMR, and the weaker arm has
fewer candidates in which to land a hit. That is a hypothesis - it has not been
measured, and it is now the obvious next question.

**Rules.**
1. **A measurement that justifies a decision has a shelf life, and a decision
   record is where staleness does the most damage** - the numbers are there
   precisely so the decision is not re-argued, so nobody re-checks them.
2. **Re-run the ablation after changing anything it ablates.** Six parameter
   changes each looked local; together they moved every row of the table that
   justifies the architecture.
3. **When two corpora are measured, quote both or quote neither.** The gate
   corpus is the one in front of you, and a component's behaviour there is not
   the component's behaviour.

---

## L74 - One hypothesis, two reversals, and it only explained one

L73 recorded two inversions in ADR 0004's ablation and offered a single cause
for both: `candidate_k` had been halved 40 -> 20, so the weaker arm had fewer
chances and MMR had less redundancy to remove. It was a tidy story that fit both
facts, which is exactly the kind that deserves a measurement rather than a
paragraph. `scripts/candidate_k_arms.py` sweeps k with each arm disabled:

| configuration | k=10 | k=20 | k=40 | k=80 |
|---|---|---|---|---|
| hybrid | 46/54 r0.872 | 49/54 r0.930 | 49/54 r0.930 | 49/54 r0.942 |
| dense only | 39/54 r0.663 | 42/54 r0.721 | **44/54 r0.814** | 43/54 r0.814 |
| lexical only | **48/54** r0.907 | 49/54 r0.919 | 49/54 r0.919 | 48/54 r0.895 |
| no MMR | 46/54 p0.253 | 49/54 p0.259 | 49/54 p0.262 | 49/54 p0.244 |

**Confirmed for the dense arm, by a number I could not have fabricated.** At
k=40 dense-only reads 44/54 with recall 0.814 - the value the ADR recorded
before the halving, to three decimals, arrived at from a fresh index. The arm
never degraded; its window shrank.

**Falsified for MMR, in the direction that matters.** Starvation predicts that
more candidates restore MMR's value. Its cost *grows* with k instead: pass +0
and recall +0.000 at every k from 10 to 80, precision -0.000, -0.012, -0.015,
-0.009. Over an 8x range of candidate set size MMR does nothing for this corpus
except cost precision. I could have left the tidy story in the ADR and nobody
would have checked it, because it was plausible and covered everything.

**And the shape of why the original sweep missed this.** `candidate_k` 40 -> 20
was measured on the *hybrid* configuration: same pass rates, better nDCG, 15-26%
faster - a clean win, correctly measured. Hybrid is flat at 49/54 for k=20, 40
and 80. The change cost the dense arm two cases and 0.09 of recall, and no
measurement of the whole could see it. The same sweep also shows lexical-only
*beating* hybrid at k=10, 48/54 to 46/54.

**Rules.**
1. **A hypothesis that explains two things at once is one hypothesis with two
   chances to be wrong.** Test it against each separately; here it was right
   about one and backwards about the other.
2. **Measure the parts, not only the whole.** A parameter can be neutral for the
   composed system and decisive for a component inside it, and the composed
   measurement is the one you will naturally run.
3. **Predict the direction before you sweep.** "More candidates restores MMR"
   was falsifiable and false; without stating it first, the growing cost would
   have read as noise rather than as a refutation.
4. **When the falsification leaves a gap, leave it open.** The real cause of the
   MMR reversal is unmeasured. Writing a second plausible story in place of the
   first is how the first one got there.

---

## L75 - The mechanism was real and the named cause was wrong

L74 left a gap deliberately: MMR is worth a case on the primary corpus and a
precision cost on the external one, and the `candidate_k` story that would have
explained it had just been falsified. Rather than write a second plausible
story, the thing to do was measure the mechanism MMR's own docstring already
claims - "a well-written document says the important thing in the introduction,
the summary and the conclusion, and all three are excellent matches."

That is within-document repetition, and it is directly observable. Over each
corpus's goldens, on the top 8 that relevance alone returns - the list MMR would
be replacing, which bounds what it can improve, and deliberately not the same as
MMR's choice set of ~20 reranked candidates:

                                     external   primary
    mean pairwise token overlap        0.0480    0.0790
    median                             0.0435    0.0772
    share of pairs same document       0.1085    0.1214
    distinct documents / results       0.7986    0.7312

**Direction confirmed, cause refuted.** The corpus where MMR pays is 1.6-1.8x
more redundant, so redundancy is the mechanism. But same-document pairs are
almost equally common in both - 0.121 against 0.109, a 12% relative difference
carrying a 65% difference in overlap. The extra redundancy is *across*
documents, not within them: a repository whose README, ARCHITECTURE, PLAN and
LEARNINGS all discuss chunking, against 153 PyPI pages that each describe a
different package. The docstring's story is a real phenomenon that is not what
distinguishes these two corpora.

**And the ruler says how much any of this can matter.** Both overlaps are tiny.
At lambda 0.7 the redundancy term is `0.3 * max_similarity`, so MMR's largest
possible influence is about 0.024 on primary and 0.014 on external - a
tie-breaker in both directions. That is consistent with a component that has now
been measured as neutral, then worth a case, then a precision cost: it has never
been doing very much, and which way the noise falls is what has been changing.

**Rules.**
1. **When a component's docstring names a mechanism, that is a hypothesis with
   an address.** Measuring the named quantity is cheaper than inventing a new
   explanation, and it can confirm the effect while refuting the story.
2. **A confirmed direction is not a confirmed cause.** Primary is more
   redundant, as predicted; the predicted *kind* of redundancy accounts for
   almost none of the difference.
3. **Compute the maximum the mechanism could contribute before arguing about
   its sign.** One multiplication showed MMR's ceiling here is ~0.02, which
   explains three contradictory readings across three corpora better than any of
   the individual explanations did.

---

## L76 - Four parameters swept, four plateaus, one pattern

`rrf_k` was the last untouched retrieval parameter: 60, the value from the
original RRF paper, inherited rather than chosen. It sets how sharply rank 1
beats rank 10 - 1.15x at 60, 5.5x at 1.

The prediction, stated before the sweep: it would measure flat, for the reason
`base_weight` did (L58) - the reranker's adjustment outweighs the fused score
34.5x, so fusion is largely a candidate generator and its constant has little
left to decide. Mostly right, with one exception worth having:

    rrf_k             1      5      20     60*    200
    external pass     48/54  49/54  49/54  49/54  49/54
    external nDCG@8   .7683  .7993  .7899  .7958  .7996
    held-out pass     19/22  19/22  19/22  19/22  19/22
    primary pass      17/20  18/20  18/20  18/20  18/20
    primary nDCG@8    .6865  .7013  .7353  .7230  .7211

Above the degenerate value the pass rate is flat on both corpora across a 40x
range, held-out does not move at all, and primary's recall@8 is 0.8750 for every
value tried. `rrf_k=1` costs exactly one case on each. The ordering metrics move
about 0.03, non-monotonically, and the two corpora peak in opposite places -
external at 200 and 5, primary at 20.

**Four sweeps this session, all the same shape.** `target_tokens`,
`hard_max_tokens`, `overlap_tokens`, the embedder's `dim`, and now `rrf_k`: each
sits on a plateau, each moves only at an extreme, and each has ordering metrics
that wobble non-monotonically inside the plateau. Held-out has read 19/22 for
every configuration of every one of them.

That is a finding about the system, not five null results. **The reranker
decides the ordering, and everything upstream of it is a candidate generator**
whose parameters matter only when set badly enough to lose the answer entirely.
It also means the six retrieval parameters tuned earlier are not fragile
artifacts of one chunking or one embedding space - they are robust across
2x-40x variation in everything feeding them.

The corollary is where the remaining headroom is. Ablation says reranking is
worth +10 cases; dense-only 42/54 against hybrid 49/54; and every knob outside
the reranker is flat. The next real improvement is in the reranker or in the
corpus, not in another sweep of a fusion or windowing constant.

**Rules.**
1. **When the nth sweep of a component finds a plateau, stop sweeping that
   component and write down why they are all flat.** Five plateaus is evidence
   about where the decisions are being made.
2. **A plateau is a robustness result, not a wasted measurement.** It is what
   licenses trusting earlier tuning that was done at one point on it.
3. **State the prediction before the sweep even when you expect nothing.**
   "Flat, because the reranker dominates" survived four of five values and
   failed at `rrf_k=1`, which is more informative than "flat" would have been.

---

## L77 - The floor is not the problem, and I nearly reported that it was

L76 concluded that the retrieval parameters are all on plateaus and the
remaining headroom is elsewhere. Looking at where, the five external gate
failures split 3:2 - three are the abstention gate *answering* an out-of-corpus
question, only two are retrieval misses. So the gate, not retrieval, is where
the gate corpus is losing.

Three wrong turns on the way to the actual finding, each caught by a cheap check.

**First, "answerability is a constant".** Probing four questions, every returned
chunk had `rerank_answerability` 1.0, including "What is the capital of France?"
- the exact dead-feature pattern of L30. Measured over 61 questions it takes 13
distinct values; it is per-question, so eight identical values in one question's
results is what a working feature looks like here. Four questions was not a
sample, it was an anecdote.

**Second, hand-built inputs.** I wrote five out-of-corpus questions myself and
measured against them. The golden sets already carry 15 `expect_abstain` cases,
built the same way as everything else (L31). Swapping them in moved the median
of the abstain distribution from 0.3114 to 0.0901 - my invented questions were
*harder* than the real ones and would have overstated the problem.

**Third, and the one that would have shipped a wrong recommendation.** My curve
scored floors by "abstain cases caught plus answer cases past the floor", and
made 0.10 look better than the shipped 0.19 (68 against 67). It is not a
contradiction, it is a different measurement: a case can clear the floor and
still fail because retrieval returned the wrong document, so "answers past the
floor" over-counts. The shipped value was chosen on end-to-end pass rate, which
is what the project gates on. Two curves over one decision, analysed differently
(L24's shape, in the tooling).

**The finding that survived all three.** Over 61 answerable and 15 abstainable
goldens:

    should answer   min .0850  p25 .3466  median .4542  p75 .5760  max 1.0
    should abstain  min .0034  p25 .0198  median .0901  p75 .3114  max .7249

The medians separate, which is why a floor works at all and catches 12 of 15.
The tail does not, and **no value of the floor fixes the three failures**:
catching the worst at .7249 needs a floor past the median of the answerable
cases; catching "capital of France" at .3303 needs ~.34, below which 13
answerable cases sit.

The three that get through are the hardest possible cases for a bag-of-terms
score: "sends mail over SMTP", "renders Jinja templates to PDF", "pins
dependency hashes for reproducible installs" - each a plausible conjunction of
terms the corpus genuinely contains, asked about a package it does not have.

**Rules.**
1. **A per-item feature that is identical within an item is not a constant.**
   Check the axis the feature varies along before calling it dead.
2. **When your new curve disagrees with an existing one, find what each
   measures before believing either.** Mine isolated a component and read as a
   verdict on the whole.
3. **Distinguish "this threshold is mistuned" from "this feature cannot make
   this decision".** Only the second is worth acting on, and the quartiles say
   which - overlapping tails with separated medians means tune no further.

---

## L78 - A better AUC that costs three cases, in the gate where a better AUC once bought three

L77 concluded the abstention floor is a feature problem, not a threshold
problem, so the next move was a different signal. Rather than invent one, rank
everything the pipeline already computes, by AUC over 61 answerable and 15
abstainable goldens (`scripts/abstention_signals.py`):

    mean relevance over 8           0.863
    rerank_relevance (incumbent)    0.845
    relevance of the top chunk      0.844
    top fused score                 0.825
    answerability                   0.814
    max coverage                    0.805
    max phrase                      0.707
    absolute margin top-2           0.593
    relative margin (top-2)/top     0.519
    recency (known saturated)       0.502

**The controls say the ruler works.** `recency` lands at 0.502, a coin flip,
which is exactly what L43 says a saturated feature must score. Term
co-occurrence, re-run at 153 documents, still gives TPR-FPR 0.159 - L51 holds
after the widening that overturned three other measurements. And the margin
hypothesis I had formed from four questions dies at 0.593.

**Then the winner lost.** Mean relevance beats the incumbent by 0.018 AUC. Swept
end to end, each statistic against its own floor since they are on different
scales:

                external      primary     held-out
    best max    49/54         18/20       19/22
    best mean   46/54         18/20       20/22

Mean is better on the held-out set - the only configuration all session to move
it off 19/22 - ties on primary, and loses the gate by three cases. `max` stays.

**The part worth the entry.** L22 records a 0.010 AUC gain *in this same gate*
being worth three end-to-end cases, and drew the rule that when AUC and the
shipping metric disagree, the shipping metric wins. Here 0.018 of AUC costs
three cases. Both are true, and together they say something stronger than either
alone: AUC does not predict end-to-end behaviour **in either direction**. It
remains good for what L22 used it for - killing a candidate cheaply, as it did
for margin and co-occurrence here - and worthless for ranking survivors.

The option is kept rather than reverted, with a test asserting the two settings
decide differently on a real retrieval with a floor derived from it (three
mutations caught, including mean and max swapped). A measured alternative that
lost is worth more as executable code than as a paragraph, and the held-out
result means a different corpus could reasonably choose it.

**Rules.**
1. **A proxy metric that once predicted the real one is not thereby a
   predictor.** Two samples, opposite directions, same gate.
2. **Put a known-dead signal in the ranking as a control.** `recency` at 0.502
   is what told me the AUC computation was sound before I acted on the top row.
3. **When a candidate wins the proxy, that is the beginning of the
   measurement.** The 0.018 bought a full end-to-end sweep, which is the only
   thing that decided anything.

---

## L79 - A signal can be worth keeping without adding separation

The gate's relevance is `(0.6 * gate_coverage + 0.4 * phrase) * answerability`.
That split was a bare constant in the expression - not a config field, never
swept - and it is the only free parameter inside the feature L77 identified as
the abstention bottleneck.

**Sweeping it needed one thing exposed first.** Relevance feeds only the gate,
never the ordering, so every split retrieves the same set and each candidate is
arithmetic on recorded components. Except `gate_coverage` was not recorded:
`rerank_coverage` is the *ranking* coverage at `coverage_power` 2.0, and the
gate uses `gate_coverage_power` 1.0 (0.5504 against 0.5998 on one chunk). The
abstention decision was the one quantity in the pipeline that could not be
inspected after the fact. Adding `rerank_gate_coverage` made the whole sweep a
single retrieval pass, and the reconstruction was checked against the shipped
number to nine places before any of it was believed.

    coverage weight  0.0    0.2    0.4    0.5    0.6*   0.7    0.8    0.9    1.0
    AUC              .737   .835   .839   .842   .845   .846   .851   .851   .851

I predicted an interior optimum, since the 0.6/0.4 mix beats either component
alone. Wrong: monotone in coverage, flat from 0.8, best at the endpoint.

**Then end to end it lost anyway**, each weight against its own floor:

    weight 0.4  best 49/54 at floor 0.19  (primary 18/20, held-out 19/22)
    weight 0.0  best 48/54 at floor 0.32  (primary 18/20, held-out 19/22)

I extended the phrase-free range to 0.60 before believing that, because the
first sweep ended at 0.32 with the curve still rising - the truncation error of
L72. It does peak at 0.32 and falls monotonically after: 48, 46, 45, 44, 41, 35.

**The mechanism is in the failure split, not the totals.** At the shipped floor
the phrase term holds over-answers to 3 where dropping it gives 6. Phrase-free
needs floor 0.32 to get back to 3, and by then it has traded an over-refusal for
it. AUC is right that the phrase run adds no separation; what it adds is a
*lower usable operating point*, where fewer positives are lost to catch the same
negatives. Those are different properties and only one of them is what AUC
measures.

**Third disagreement, second in a row.** L22: +0.010 AUC worth three cases.
L78: +0.018 AUC costing three. Now +0.006 costing one. The rule from L78 - that
AUC predicts end-to-end behaviour in neither direction - is now three samples
deep and has stopped being a surprise.

**Rules.**
1. **"Adds no separation" and "is not worth keeping" are different claims.**
   A term that shifts where the threshold can sit earns its place without
   improving any ranking statistic.
2. **A quantity a decision reads must be recorded**, even when a similarly named
   one already is. Two coverages differing by a power made the gate's own input
   unobservable and its only parameter unsweepable.
3. **Extend a sweep whose curve is still moving at the edge**, before comparing
   its best cell with anything. This one happened to peak at the boundary; the
   check cost four minutes and the alternative was a comparison against an
   unknown.

---

## L80 - The same always-False probe, twice in one session

Query expansion was the last parameter in `RetrievalConfig` with no measurement
under it - every other tuned value carries a sweep table, and `use_expansion`
carried an "off" inherited from a corpus a third the current size. It was also
the obvious tool for the two remaining external retrieval failures, which are
vocabulary mismatches ("control what the clock returns" against freezegun's own
wording).

**Measured, it is inert on the gate corpus and live on the other.** External:
identical pass and recall for every arm, with 4, 8 and 12 terms byte-identical.
Primary: 8 terms gains 0.016 of nDCG, 4 terms *costs a case*. Fourth time this
session the two corpora have wanted different things, after `base_weight` (L58),
MMR (L75) and the abstention floor.

**Then my probe lied to me, in a way I had already been caught by.** To explain
the split I counted how many expansion candidates reach the top 8, testing
`"expansion_rrf" in result.components`. The arm is registered as `"expanded"`,
so the key is `expanded_rrf` and the test was always False. The probe printed
"0 reaching the top 8" for both corpora at every candidate_k, which reads
exactly like a finding - and would have supported the tidy story I had already
formed, that expansion is truncated away by the halved `candidate_k`. It is the
same defect as L58's `hasattr(r, "index")`, which produced a column of dashes I
published before catching. Twice in one session, both times a membership test
against a name I did not verify, both times producing a plausible zero.

What tipped it off was arithmetic, not suspicion: primary's metrics moved when
expansion was on, and a component contributing literally nothing cannot move a
metric. The contradiction was in the data I already had.

**With the right key, the real mechanism.** Expansion voted for 26% of external
top-8 slots and 31-41% of primary's, touching 43 of 54 and 17 of 20 queries. But
across 74 queries at k=20 and k=40 it introduced **zero** chunks the other arms
had not already found. It is a re-ranker of the existing candidate set, never a
recall mechanism - which is why recall@8 is unchanged to four decimals wherever
it is enabled, and why it cannot fix the failures it was reached for: freezegun
is at lexical rank 107 and dense 331, outside the candidate set, and a component
that only reweights candidates cannot promote one that is not among them.

The code comment says expansion "can add candidates but never evict". True of
the design and misleading about the effect: on this corpus it never adds either.

**Rules.**
1. **A membership test against a string you did not verify is a coin flip that
   always lands the same way.** Print the available keys once before writing
   `"x" in components`; it costs one line and I have now paid for it twice.
2. **A zero that agrees with your current hypothesis deserves more scrutiny
   than one that contradicts it.** Both my zeros were confirmations, which is
   why neither got checked.
3. **Cross-check a "contributes nothing" against any metric that moved.** The
   refutation was already in the table above the probe.
4. **"Can add" and "does add" are different claims**, and only the second tells
   you whether a component can fix a recall gap.

---

## L81 - The convenient explanation was mine, and it was wrong

Two external cases fail for retrieval rather than abstention, and L80 had just
shown query expansion structurally cannot reach them. The remaining story was
attractive: `embedding/hashing.py` says of itself "it will not match a good
neural embedder on paraphrase", the questions are visibly paraphrases
("control what the clock returns" against freezegun's "travel through time by
mocking the datetime module"), so the failures are the documented price of the
zero-dependency core rather than a defect. Tidy, exculpatory, and citing an ADR.

**Measured, it is false.** Share of the question's terms the answer document
contains:

    cases that pass    min 0.200  p25 0.571  median 0.714  max 1.000
    the two that fail  0.500 and 0.667

Both failures sit above the passing p25, and six passing cases have lower
overlap than either - bcrypt passes on 0.200 against freezegun's 0.500. How much
of the question the answer contains does not decide anything, so "paraphrase"
was a description of how the questions read, not of why they fail.

**What the same data says instead.** The missing terms are `clock`, `control`,
`fake`, `network`, `repli` - and what remains is high-frequency vocabulary for a
corpus of Python packages. Measuring the document frequency of the *rarest*
shared term, which is the best hook a term-matching retriever has for picking
one document out of 153:

    cases that pass    min 1  p25 3  median 5  max 103
    the two that fail  13 and 48

Their best hook is 2.6x and 9.6x commoner than the median passing case's. That
is a real and much stronger signal - and still not sufficient, because one
passing case survives a hook in 103 of 153 documents. A rare term helps and is
not required; the reranker can carry a case without one.

**Why this was worth the twenty minutes.** The falsified story would have closed
the investigation with an ADR reference and no code change, and it would have
been believed - it is the kind of explanation that sounds like engineering
maturity. The measurement that killed it was five lines of set arithmetic over
files already on disk.

**Rules.**
1. **Be most suspicious of the explanation that excuses you.** "This is the
   documented limitation of a design we chose deliberately" needs the same
   evidence as "this is a bug", and is far less likely to get it.
2. **A property you can see in the input is not thereby the cause.** These
   questions *are* paraphrases; the passing ones are too, and more so.
3. **When the first measurement refutes the hypothesis, the second is usually
   in the same data.** The missing-terms list that disproved the paraphrase
   story is what pointed at term rarity.
