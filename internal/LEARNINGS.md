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
