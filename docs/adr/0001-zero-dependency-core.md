# ADR 0001 — The core runs on the standard library alone

**Status:** accepted

## Context

A retrieval pipeline naturally reaches for three dependencies: an HTTP client
(`requests`), an array library (`numpy`), and a vector store or embedding
service. Each is individually reasonable and together they decide where the
pipeline can run.

The environments this has to work in are not generous. A filtered container
where egress is an allowlist. CI with no credentials. A laptop with no GPU. In
each of those, a dependency is not a convenience — it is a thing that can be
missing, and a pipeline that cannot start is worth less than one that starts
degraded.

## Decision

The core requires nothing outside the standard library. Every stage — ingest,
normalize, chunk, embed, index, retrieve, rerank, generate, evaluate — runs on
Python 3.11 alone.

Accelerators and hosted providers plug in behind interfaces (`Embedder`,
`Generator`, `Connector`) and are strictly optional.

## What this costs, stated plainly

- **Embeddings are weaker.** The hashing trick captures term overlap and some
  morphology, not meaning. `car` and `automobile` stay far apart. This is
  tolerable only because the dense arm is fused with BM25 rather than used
  alone; on its own it would be a bad retriever.
- **Dense search is a brute-force scan.** No ANN index. Exact, no tuning
  parameters, and linear in corpus size — right at this scale, wrong at a much
  larger one.
- **Scoring is pure Python.** Roughly an order of magnitude slower than a
  vectorised equivalent. `pip install oodarag[fast]` adds numpy behind the same
  interface.

## What it buys

- `make test` and `make demo` run in any container with Python, including one
  with no network at all. The zero-dependency claim is exercised by the default
  path rather than asserted in a README.
- No credential is required to evaluate whether the pipeline works.
- A dependency cannot break the build by changing, being yanked, or being
  unreachable from behind a proxy.

## Known bias: token counts are estimated, not measured

`estimate_tokens` approximates roughly four characters per token for English
and three for code, deliberately, so that no tokenizer dependency is needed.
Chunk sizes are tuned against it and the eval harness inherits it.

The drift this introduces is **systematic rather than random**, and worst on
code, where identifiers and punctuation tokenise far more finely than the
ratio assumes. Two consequences worth writing down before they cause a
misdiagnosis:

- A chunk targeted at 320 estimated tokens may be materially larger in a real
  tokenizer's count. If chunks are later sized against a model's context
  budget, size from the model's own counter, not from this.
- A retrieval regression that appears after switching to a real tokenizer is
  most likely this bias surfacing, not the retriever getting worse. Compare
  chunk-size distributions before concluding anything about ranking.

Recorded here rather than fixed, because the fix is a tokenizer dependency and
that is the trade this ADR exists to refuse. `Embedder` and the chunker both
take the counter as a seam, so a project that already has a tokenizer can
supply it.

## Consequences

Two rules follow, and both are load-bearing:

1. **A new dependency in the core needs its own ADR.** The optional extras are
   the pressure valve.
2. **Every interface must have a working stdlib implementation.** An interface
   whose only implementation needs a network is not an interface, it is a
   dependency with extra steps.

## Alternatives considered

- **`requests` for HTTP.** It would buy connection pooling and a nicer API. It
  would not buy per-host rate limiting, `Retry-After` handling, conditional
  requests, response-size caps or content-type gating — all of which had to be
  written anyway. `urllib` also reads proxy configuration from the environment,
  which is how this runs inside a filtered container with no special casing.
- **A hosted embedding API.** Better vectors, at the cost of a credential and
  egress on the default path. Available behind `Embedder` for anyone who has
  both.
- **A vector database.** Better scaling, at the cost of a service to run. A
  SQLite file is copyable, diffable, and inspectable with one import, which
  matters more at this size.
