# Observations

What this project has actually been measured to be. Every line resolves to an id
in `sources.yaml`. Nothing here is inferred from a filename, a branch name, or
another session's report.

Read this before working here. Read `unknowns.md` immediately after — the two
files are only useful together, because the second one is what stops the first
from reading as a complete picture.

---

## The tree, as measured

`oodarag` at S-1 is 16 Python files, 2,583 lines, under `src/oodarag/`
`[src:S-6]`. Four areas have working code:

| Area | Modules | What is there |
|---|---|---|
| `util` | `http`, `text`, `hashing`, `ratelimit`, `logging` | urllib client with retry/backoff, `Retry-After` and ETag handling, byte caps; text normalization, tokenization, markdown section splitting, secret redaction; stable content hashing; token bucket; structured logging `[src:S-1]` |
| `scrape` | `html`, `robots`, `crawler` | tolerant stdlib HTML tree builder, boilerplate removal, markdown rendering; RFC 9309 robots policy; BFS crawler with content/canonical dedupe and page/fetch/byte/depth/time budgets `[src:S-1]` |
| `ingest` | `base`, `github`, `web` | connector contract with content-hash incrementality and atomic cursor persistence; GitHub connector across repo/readme/files/issues/commits/releases with head-sha and blob-sha short circuits; web connector over the crawler `[src:S-1]` |
| `models` | `models` | `RawDocument -> Document -> Chunk -> ScoredChunk -> Answer` with provenance carried forward `[src:S-1]` |

`make lint` (`compileall -q src`) exits 0 at S-1 `[src:S-5]`.

## The gap between the README and the tree

This is the finding that mattered most at S-1, and it is why the checkers in
`tools/` exist.

The README describes a nine-stage pipeline and a feature table covering hybrid
dense + BM25 retrieval fused with RRF, an eval harness reporting recall@k, MRR
and nDCG, contextual chunk headers, and an OODA loop that decides when to
re-fetch `[src:S-1]`. **None of those five had code at S-1** — no chunker, no
embedder, no index, no retriever, no eval harness, no loop, no CLI `[src:S-6]`.

Measured consequences, not inferred ones:

* `make test` exits **2** with `ImportError: Start directory is not importable:
  'tests'` — there was no `tests/` directory `[src:S-3]`.
* `python3 -m oodarag.cli` exits **1** with `ModuleNotFoundError` `[src:S-4]`.
  `pyproject.toml` declared `ooda = "oodarag.cli:main"` as a console script, so
  `pip install` followed by `ooda` produced that same error `[src:S-1]`.
* Five Makefile targets — `demo`, `index`, `query`, `eval` and `loop` — invoked
  that missing module, so each of them failed the same way `[src:S-1]`. The
  other five (`help`, `install`, `test`, `lint`, `clean`) did not.
* Four paths were referenced by name and did not exist: `internal/PLAN.md`
  (README), `docs/adr/0001-zero-dependency-core.md` (`pyproject.toml`,
  `util/http.py`, `util/text.py`), `evals/goldens.jsonl` (Makefile), and `tests/`
  `[src:S-1]`.

The code that exists is careful and the prose describing it is accurate. The
prose describing the code that does not exist was written in the same voice,
which is what made the gap invisible from the README alone.

## What the doctrine repository expects here

`claude-ai`'s CLAUDE.md directs every session to this repository for doctrine and
names `CLAUDE.md`, `prompts/`, `provenance/` and `tools/`, plus
`.claude/skills/ooda/SKILL.md` and `tests/run_all.sh` `[src:S-2]`. At S-1 none of
those existed `[src:S-1]`. This branch created all of them except `prompts/`,
which was left uncreated and recorded as U-4 rather than filled with invented
content.

## What this branch changed

* `tools/` — the evidence framework and ten deterministic data checkers, run by
  `python3 -m tools.ultrareview`. The verdict vocabulary is four-valued so that
  "could not check" cannot be recorded as "checked and fine" `[src:S-7]`.
* `.claude/skills/ultrareview/` and `.claude/skills/ooda/` — the review procedure
  and the observe-first procedure it depends on.
* `tests/` — unit tests for every checker, plus `run_all.sh`.
* `docs/adr/0001-zero-dependency-core.md` — written because three files already
  cited it, and because the decision it records is evidenced by the tree.
* README, `pyproject.toml` and the Makefile — corrected so that what they claim
  matches what the checkers measure. The unbuilt stages moved to a roadmap that
  is labelled as one. The `ooda` console script was removed rather than left
  pointing at a module that does not exist, and the five Makefile targets that
  invoked it were removed with it.
* `LICENSE` — added, because `pyproject.toml` declared MIT and the tree carried
  no license text `[src:S-7]`.

## Where the branch ended

`bash tests/run_all.sh` exits 0 `[src:S-8]`. The checkers report 0 errors and 0
warnings over this repository, with 2 unverifiable items named rather than
folded into the pass `[src:S-7]`, and 0 errors and 0 warnings over `claude-ai`
when it is given its sibling `[src:S-9]`.

Two of the tool's own bugs were found by running it on itself, and both are
recorded here because they are the kind a review tool is least likely to catch
by reading:

* **Recursive execution.** The `commands` checker runs what the docs tell a
  reader to run. This repository's docs tell a reader to run `make check`, which
  runs `tests/run_all.sh`, which runs the checkers. The recursion crosses process
  boundaries, so the guard is an environment marker rather than a call-depth
  counter — see `CheckConfig.for_subprocess`.
* **Test fixtures read as claims.** `tests/test_links.py` has to contain a
  deliberately wrong URL in order to assert that a wrong URL is caught. Reading
  that fixture as a published link made the checker loudest about the code
  proving it works. Files under `tests/` are now excluded from URL extraction.

Then the review's own judgement layer was pointed at the finished work: four
dimensions of subagent review, each finding handed to a separate agent whose
only job was to refute it. 31 findings were raised and **30 survived**
`[src:S-10]`. All 30 are fixed in the same commit, each with a regression test.
The three that mattered most were all in code written for this branch:

* `RepoIndex` matched its skip-list against the *absolute* path, so a
  repository checked out under `~/dev/build/repo`, a CI workspace at
  `/var/lib/ci/build/job`, or anything vendored inside a `node_modules`
  directory filtered out every one of its own files. The tool then read zero bytes and printed
  "0 error, 0 warn", exit 0. A silent clean bill of health for a tree it never
  opened is the worst output this tool can produce, and nothing in the suite
  noticed because `tempfile` never generates a directory named `build`.
* `os.environ[ENV_MARKER]` was set and never restored, so the *second* `run()`
  in one process believed it was nested and stopped executing commands. A caller
  looping over repositories got a real review of the first and a quietly
  degraded one of every other.
* The `links` checker read its own test fixtures as published claims. A test for
  a wrong-URL rule has to contain a wrong URL; reading it as a claim made the
  checker loudest about the code proving it works.

The rest were false positives of the same family — a tilde-fenced code block
read as prose, `localhost` reported as an unresolvable host, `example.com`
flagged despite RFC 2606 reserving it for exactly that use, a multi-target
Makefile rule (`build dist:`) reported as two missing targets, a monorepo's
cross-package import reported as an undeclared dependency — plus four false
claims in the documentation written for this branch, including a README row
asserting per-host rate limiting that `HttpClient` does not do (it holds one
bucket per client) and a crawler row claiming a byte bound that `CrawlConfig`
has no field for.

A third bug was found by measurement changing under the tool: creating `tests/` to
hold a shell script turned a failing `make test` into a *passing* one that
collected zero tests. `unittest discover` exits 0 on an empty suite. The
`tests_evidence` checker now parses the collected count and reports
`TESTS_VACUOUS` for a green run that asserted nothing.

## The web and GitHub ingest paths, exercised for the first time

At the start of this round `src/oodarag/` had **no tests at all** — 2,583 lines
across twelve modules, none of it ever executed by the suite. Everything green
until then covered `tools/`. Running the two built ingest paths against real
services found what only real execution finds.

### GitHub

The connector raised `TypeError` at the end of **every run using its default
resource set** `[src:S-11]`. `log.info("github fetch complete", repo=self.slug,
**counts)` collided with `counts["repo"]`, which exists whenever `"repo"` is in
`resources` — the default. `Connector.run` caught it and recorded `failed=1`, so
`IngestDelta.failed` was permanently non-zero. That delta is precisely the
signal the OODA loop is meant to read to decide whether a source is healthy, so
the one number the design leans on was reporting a failure that never happened.
The counts are now namespaced (`n_repo`, `n_readme`, `n_files`).

What the live run confirmed, rather than assumed:

* Every file document's citation URI pins the head commit sha, not a branch —
  40 of 40 on a cold run `[src:S-11]`.
* The head-sha short circuit is real: a second run against an unchanged head
  spends two requests instead of walking the tree `[src:S-11]`.
* The `git/blobs` fallback returns the file correctly `[src:S-11]`. The
  raw-first optimisation itself is **unverified here**: this repository is
  public and `raw.githubusercontent.com` still answered 404 through the sandbox
  proxy, so every blob came from the API. An earlier draft of this file recorded
  "one request via raw" — that was an artifact of `HttpClient` not counting its
  `allow_status` branch, fixed in this round, and the corrected cost is two
  requests. It is written down rather than deleted because a measurement that
  turned out to be an instrument error is worth more on the record than off it.
* A `ghp_`-shaped token is redacted before a `RawDocument` exists `[src:S-11]`.

One thing could **not** be verified live and is recorded rather than assumed:
GitHub returns `Link: rel="next"` as a numeric-ID path
(`/repositories/<id>/commits?page=2`), which the sandbox proxy rejects with 403.
`paginate()` parses the header correctly; following it across pages is covered
by fake-transport tests instead.

### Web

`github.com/robots.txt` answers 403 through the proxy, and `robots.py` treats a
restricted rules file as disallow-all, so a crawl of github.com correctly yields
nothing `[src:S-13]`. That is RFC 9309 working as documented.

Against `pypi.org`, which does serve robots.txt, a real crawl ran end to end:
three pages stopped by `max_pages` with 114 URLs still queued, live
rules obeyed (`/help/` allowed, `/simple/` denied), and extraction that kept the
heading structure while dropping the cookie banner and skip-links `[src:S-12]`.

Two bugs in `html.py`, the second of them introduced while fixing the first:

* **Navigation links were being discarded.** Links were collected from the tree
  *after* aggressive pruning, so every `<nav>` and `<footer>` link had already
  been deleted. The comment directly above that code claimed the opposite — "a
  crawler needs the nav it just discarded in order to find the next page". On a
  documentation site, whose link structure is almost entirely navigation, the
  crawler would have found almost nothing. Extraction is now two-stage: drop
  what is never content, collect links, then drop the boilerplate.
* **That fix broke `link_density`.** The metric divides link text by body text,
  and suddenly the numerator spanned the whole document while the denominator
  was still the body — so it read 0.47 on a page whose body contained no links
  at all, and 1.00 on the PyPI homepage. Since its docstring defines a high
  value as "boilerplate removal failed", the metric reported failure exactly
  when removal had succeeded. `ExtractedPage` now carries `body_links`
  separately from `links`, and the corrected figure for that homepage is 0.195
  `[src:S-12]`.

The second one is worth recording for its own sake: it was found only because
the first fix was measured rather than assumed, and it would have been invisible
in any test that checked link *counts* instead of the derived metric.

### Two open items closed

`make lint` had been reported UNVERIFIABLE on every run because its recipe runs
`compileall`, which the commands checker refused to execute since it writes
bytecode into the tree under review and ignores `PYTHONDONTWRITEBYTECODE`. The
run environment now sets `PYTHONPYCACHEPREFIX` outside the tree, so the command
is executed and passes.

The `links` checker's module docstring promised "HEAD (falling back to GET)" and
the code never fell back, so `https://api.github.com` — which answers 400 to HEAD
and 200 to GET — was reported as a dead link. The fallback now exists, and only
404 and 410 count as dead: a refused method, a demand for credentials, a rate
limit or a 5xx is a fact about the server at that moment, not about the
documentation `[src:S-14]`.

## What the first tests found

`src/oodarag` went from **no tests at all** to 383 of them `[src:S-15]`. Writing
them surfaced 29 bugs `[src:S-17]`, and the pattern across them is worth stating
because it is not the pattern anyone expects.

Almost none were logic errors in the happy path. The code is careful there. They
clustered in three places instead:

**Optimisations that lost data.** Every saving in this pipeline works by *not*
transferring something, and each one had found a different way to make "I did
not send it" indistinguishable from "it is gone".

* The GitHub head-sha short circuit — the connector's headline cost saving —
  made a warm run report every file in the corpus as removed and drop every
  stored hash. Measured against the real API: 6 of 6 files proposed for
  deletion, 0 hashes kept `[src:S-16]`. The saving proposed wiping the index and
  then paid for a full re-ingest.
* A 304 from a conditional GET did the same thing to the crawler whenever a
  client was shared between runs — which is the documented way to share a rate
  limit.
* The blob-sha map recorded a file's sha *before* fetching its bytes, so one
  transient error meant that file was never fetched again.
* `next_cursor` advanced the head sha even when the tree walk had failed, which
  poisons the cursor permanently: the next run takes the short circuit and skips
  the files that commit added, forever, with no error anywhere.

The first two share one cause and now share one fix:
`Connector.unchanged_external_ids`, which lets a source say "still there, still
the same" about a document it deliberately did not send.

**Standards implemented from memory rather than from the text.** `robots.py`
names RFC 9309 as its contract and delegated to `RobotFileParser.can_fetch`,
which returns the *first* matching rule. §2.2.2 requires the *longest* match to
win. So `Disallow: /docs/` followed by `Allow: /docs/public/` was read backwards
and the explicitly-published subtree was the one thing refused. `Crawl-delay:
0.5` was silently discarded because the stdlib accepts only integers — on a
module whose docstring opens by explaining that impolite crawling gets you
blocked.

**Failure paths that were never taken.** `_decompress` caught `OSError` and
`zlib.error` but not the `EOFError` a truncated gzip stream actually raises, so
one reset connection killed a whole crawl. `TokenBucket.acquire(n)` hung for
ever when `n` exceeded capacity — no exception, no log line. `extract()` raised
`RecursionError` on a page with a few hundred unclosed tags, which is precisely
the broken page the module promises to survive; its stated principle is
"degrade, don't die", and that was the one input that made it die.

Two more were mine, introduced during this round and caught by measuring rather
than assuming: collecting links after the aggressive prune deleted every
navigation link before the crawler saw them, and the fix for it silently
inverted `link_density` so the metric reported failure exactly when boilerplate
removal had succeeded. Both are described above under the web section.

### What is still not verified

One item, and it is by design rather than unfinished: link reachability is not
checked unless `--network` is passed, because a result that depends on the
network is not reproducible and an unreachable host inside a sandbox is not
evidence of a broken link. Run with `--network` it reports 0 errors and 0
warnings, with three links undetermined — two hosts the sandbox proxy blocks and
one that refuses a bare-origin request `[src:S-14]`.
