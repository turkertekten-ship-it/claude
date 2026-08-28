# oodarag

An OODA-driven retrieval pipeline that runs on the Python standard library
alone. Zero required dependencies, verified from the import graph on every
review run rather than asserted here.

```
Observe  ->  Orient   ->  Decide   ->  Act
ingest       normalize    policy       reindex / backfill
             chunk        engine       / alert / answer
             embed
             index
```

That diagram is the design. The section below says which parts of it are code
today, because a README that describes a design in the present tense is how a
project ends up lying about itself.

## What is built

Everything below has working code today. Each row names the file that implements
it, so the table is checkable rather than decorative:

| Area | Module | What it does |
|---|---|---|
| HTTP | `util/http.py` | urllib client with token-bucket rate limiting (one bucket per client, not per host), retry honouring `Retry-After` and GitHub's `x-ratelimit-reset`, conditional GETs via ETag, an 8 MiB cap per response, and no silent POST replay on redirect |
| Text | `util/text.py` | NFKC normalization, code-aware tokenization, markdown section splitting that never splits a fenced block, and secret redaction applied at the connector boundary |
| HTML | `scrape/html.py` | a tolerant tree builder over `html.parser` with explicit recovery rules, structural plus link-density boilerplate removal, and markdown rendering that preserves headings, lists and code fences |
| Robots | `scrape/robots.py` | RFC 9309 semantics with per-host caching: longest-match wins with `Allow` taking ties (§2.2.2), fractional `Crawl-delay` honoured, and 5xx or unreachable treated as disallow-all rather than as permission |
| Crawl | `scrape/crawler.py` | breadth-first, dedupes on content hash and declared canonical as well as URL, records why each URL was skipped, honours a per-host crawl delay, and bounds pages, fetches, depth and wall-clock. Bytes are counted and reported but not bounded — the only byte limit is the client's 8 MiB per response |
| Ingest | `ingest/base.py` | the connector contract: content-hash incrementality, atomically persisted cursors, per-document failures counted rather than raised, and `unchanged_external_ids` so a source that saves bandwidth is not mistaken for one that lost documents |
| GitHub | `ingest/github.py` | repo, README, files, issues, PRs, commits and releases; head-sha short circuit, one recursive tree call, and raw-over-API blob fetches to stay inside the REST quota |
| Web | `ingest/web.py` | the crawler as a connector, with redaction and provenance stamping |
| Models | `models.py` | `RawDocument -> Document -> Chunk -> ScoredChunk -> Answer`, carrying provenance at every hop |

Plus three supporting modules the table would otherwise bury: `util/hashing.py`
(process-stable content hashes — `hash()` is salted per process and is never
used), `util/ratelimit.py` (the token bucket), and `util/logging.py`.

## Review tooling

`tools/` holds the evidence framework behind `/ultrareview`: ten deterministic
checkers that hold this repository's own prose to its own data.

```bash
PYTHONPATH=. python3 -m tools.ultrareview .      # check every claim in this repo
PYTHONPATH=. python3 -m tools.ultrareview . --list
bash tests/run_all.sh                            # compile, unit tests, checkers
```

They exist because the first version of this README described five capabilities
that had no code behind them, and nothing in the repository could tell the
difference. `provenance/observations.md` records what was actually measured;
`provenance/unknowns.md` records what is still undetermined.

The checkers are project-agnostic — point them at any repository.

## Not yet built — roadmap

Everything in this section is design, not code. It is separated out so that no
reader has to guess which half of the README they are in.

| Stage | Status | The failure mode it is meant to address |
|---|---|---|
| Chunking with contextual headers | not started; `Chunk.context_header` exists as a field, nothing populates it | chunks that lose the context that made them meaningful |
| Embedding + index | not started | — |
| Hybrid dense + BM25 retrieval fused with RRF | not started | semantic search missing exact terms |
| Reranking | not started; `Connector.authority` is carried for it | boilerplate outranking content |
| Eval harness: recall@k, MRR, nDCG, citation coverage | not started; no goldens exist | "is retrieval any good?" having no answer |
| The OODA loop that decides when to re-fetch | not started; `IngestDelta` is the input it will read | indexes going stale silently |
| CLI (`oodarag.cli`) | not started | — |

No target retrieval quality has been set; see U-3 in `provenance/unknowns.md`.

## Quick start

```bash
make lint            # compile-check every module
make test            # stdlib unittest, no dependencies required
make check           # lint, tests, and the evidence checkers
```

There is deliberately no `make demo` yet. There was one, and it invoked a module
that did not exist.

## Tests

The suite is stdlib `unittest`, no dependencies, and it drives the network-facing
code through fake transports so it runs anywhere.

```bash
PYTHONPATH=src:. python3 -m unittest discover -s tests -t .   # everything
PYTHONPATH=src:. OODARAG_LIVE=1 python3 -m unittest tests.test_oodarag_live
```

The second command is opt-in and really talks to `api.github.com` and `pypi.org`.
It is separate rather than skipped-on-failure, because a network test that
quietly passes when the network is missing is a green tick asserting something
nobody checked. What it covers, and what the sandbox it was written in could not
verify, is recorded in `provenance/observations.md`.

## Design principles

1. **Zero required dependencies.** The whole pipeline runs on the stdlib, so it
   works in CI, in an air-gapped container, and on a laptop. Accelerators and
   hosted models plug in behind interfaces. See
   `docs/adr/0001-zero-dependency-core.md` for what that costs.
2. **Provenance is load-bearing.** Every document carries the URI and commit sha
   it came from.
3. **Everything is bounded.** Every network stage has a budget on requests,
   bytes and time.
4. **Degrade, don't die.** Blocked egress, a missing API key or a truncated
   response reduce what the pipeline can do; they never make it crash.
5. **Measure, don't assert.** Applies to the pipeline's retrieval quality, and
   to this README. The second one is enforced by `tools/`.
