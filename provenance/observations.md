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
