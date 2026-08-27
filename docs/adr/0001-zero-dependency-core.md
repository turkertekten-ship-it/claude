# ADR 0001 - The core has no required dependencies

**Status:** accepted

## Context

The obvious build is `sentence-transformers` + FAISS or a hosted vector database
+ an embedding API. That is four heavy dependencies, a model download, a network
call per query, and an API key before anything runs.

## Decision

The core pipeline runs on the Python standard library. numpy, hosted embedders
and hosted LLMs are optional extras behind interfaces.

## Consequences

**What this buys.** The pipeline runs in CI with no secrets, inside an
egress-filtered container, and on a laptop with no GPU - and it is the *same*
pipeline in each, not a mock. Vectors are byte-identical on every machine, so an
eval difference is a real regression rather than model drift. A new contributor
runs `make test` and it works.

**What it costs.** The default embedder is feature hashing, not a learned model.
It will lose to a good neural embedder on paraphrase, and the eval harness shows
exactly where: see the `semantic-gap` case in `evals/goldens.jsonl`, where the
query's most informative term ("forever") appears nowhere in a corpus that says
"never terminates".

That cost is the point. The offline embedder is the baseline a hosted one has to
*beat on the harness* to justify its dependency, its key and its per-query
latency. Without a runnable baseline that comparison never gets made.

**Where the line is.** An optional extra may improve a stage. It may not become
required for a stage to function. `store/vectors.py` uses numpy when importable
and a pure-Python kernel otherwise; both are exercised by the same tests.
