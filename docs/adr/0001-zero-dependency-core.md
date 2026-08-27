# ADR 0001 — The core runs on the standard library alone

**Status:** accepted
**Date:** 2026-08-27

## Context

Three files cite this ADR by number — `pyproject.toml`, `src/oodarag/util/http.py`
and `src/oodarag/util/text.py` — and it did not exist. This document records the
decision those files were already relying on. It is written from the tree rather
than from intent: everything below is a property the code actually has, and
`python3 -m tools.ultrareview . --only deps` re-derives it from the import graph.

A retrieval pipeline reaches for dependencies early and hard: `requests` for
HTTP, `beautifulsoup4` for HTML, `numpy` for vectors, a tokenizer, a client for
whichever embedding API is in fashion. Each is individually reasonable. Together
they decide where the pipeline can run.

## Decision

The core has no required dependencies. Every stage runs on CPython's standard
library. Accelerators and hosted models plug in behind interfaces, as extras.

`[project] dependencies` is empty. `[project.optional-dependencies]` carries
`fast` (numpy), `providers` (requests) and `dev` (pytest, ruff).

## Consequences

**What this buys.** The pipeline runs in CI without a resolver step, in an
air-gapped container, and on a laptop with nothing installed. A reviewer can read
the whole data path without also reading four libraries' semantics. The install
surface is a real security property, not a stylistic one: there is no transitive
dependency tree to audit or to be compromised through.

**What it costs, concretely.**

* No connection pooling. `util/http.py` builds on `urllib`, so each request pays
  a fresh handshake. At the crawler's default 2 requests/second this is not the
  bottleneck; at a hundred it would be.
* HTML parsing is ours. `scrape/html.py` is a tolerant tree builder over
  `html.parser`, roughly 510 lines including boilerplate removal. That is code we
  own and must keep correct against malformed real-world HTML — the recovery
  rules in `_TreeBuilder` exist because of specific failure shapes, and they are
  the part most likely to need extending.
* Token counts are estimates. `util/text.estimate_tokens` approximates ~4
  characters per token rather than importing a real tokenizer. Every budget that
  consumes it is therefore a soft budget and is documented as one.
* Vector maths, when the retrieval stages are built, will be pure Python by
  default. `numpy` behind the `fast` extra is the intended escape hatch, and it
  must stay an optional import inside a function — an unguarded module-level
  import would make the extra required in practice while claiming to be optional.
  The `deps` checker enforces exactly this.

**How the decision is enforced.** `tools/checkers/deps.py` walks every import in
the tree with `ast`, classifies each as stdlib, first-party, declared or
undeclared, and contradicts any prose claiming zero dependencies if an unguarded
third-party import exists. The claim is therefore checked on every run rather
than trusted.

## Alternatives rejected

* **`requests` for HTTP.** It would have bought connection pooling and a nicer
  API. It would not have bought per-host rate limiting, `Retry-After` handling,
  conditional GETs, or response-size caps — all of which `util/http.py` needs and
  implements regardless. The dependency's value here was smaller than it looks.
* **A parser dependency for HTML.** Genuinely better than what we have at
  handling pathological markup. Rejected because it is the dependency most likely
  to be unavailable in the constrained environments this is meant to run in, and
  because boilerplate removal — the part that actually determines corpus quality —
  would have been ours to write either way.
* **Vendoring.** Rejected: it keeps the install surface small while making
  upgrades and auditing worse than either alternative.

## Reversal condition

If the retrieval stages land and pure-Python scoring is measured to be the
bottleneck on a corpus this project actually targets, `numpy` moves from `fast`
to required and this ADR is superseded. The trigger is a measurement, not an
impression.
