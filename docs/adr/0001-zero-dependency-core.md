# ADR 0001: The core runs on the standard library

- **Status:** Accepted
- **Date:** 2026-08-27
- **Scope:** everything under `src/oodarag/`

## Context

This pipeline has to run in three places that share one property: nothing can
be installed at the moment it is needed.

- **CI**, where a dependency resolution failure is indistinguishable from a
  test failure to everyone reading the red X.
- **An egress-filtered container**, where `pip install` does not fail fast — it
  hangs, retries, and eventually times out somewhere inside a build step that
  was supposed to take four seconds.
- **Someone else's machine**, five minutes after they cloned the repository,
  where the honest measure of the project is whether `make demo` printed an
  answer or a stack trace.

The usual RAG stack does not survive any of those. A sentence-transformer model
is a few hundred megabytes fetched from a hub at first use; a vector database is
a service to run; a tokenizer is a compiled wheel that has to match the
interpreter. Each is individually reasonable and collectively they mean the
project only works where it has already worked.

There is a second, quieter reason. A dependency is also an opinion you did not
write down. When retrieval quality moves, the question "did the model change?"
has to be answerable, and it is only answerable if the answer can be *read*.
Every scoring decision in this pipeline is a few dozen lines of arithmetic in
this repository, which is the difference between debugging retrieval and
debugging a black box that someone else version-bumped.

## Decision

**The core runs on the Python 3.11 standard library. Accelerators and hosted
models plug in behind interfaces, and are always optional.**

Concretely:

- `pyproject.toml` declares `dependencies = []`. The extras (`fast`,
  `providers`, `dev`) are conveniences and no code path requires them.
- The vector store is `sqlite3`, which ships with Python. Vectors serialize
  through `array("f", vec).tobytes()`.
- The embedder is `HashingEmbedder`: the signed hashing trick over
  `util.text.tokenize` plus character n-grams, hashed with `hashlib.blake2b`.
  No model download, no first-use latency, byte-identical across processes and
  machines.
- The generator is extractive. It answers with sentences that appear verbatim in
  retrieved chunks, so a citation is verifiable by string containment rather
  than by trusting a model.
- `numpy` is permitted in exactly one shape: a `try: import numpy / except
  ImportError:` fast path whose stdlib fallback produces the same result. The
  import may never be at module top level, and the fallback may never be a
  degraded approximation.
- The seams for the things that are genuinely better elsewhere already exist:
  `Embedder` is a `Protocol`, so a hosted embedding API is a class with two
  methods; `generate.build_prompt` exists so a hosted model can be dropped in
  without touching retrieval.

## Consequences

This decision has a bill, and the point of writing it down is that the bill is
paid by whoever adopts the pipeline, not by whoever chose the design.

### The embedder is weaker than a transformer

A hashing embedder has no learned semantics. It places `chunking` near
`chunked` because they share character n-grams, not because it knows what either
word means. Two passages that say the same thing in different words are near
each other only to the extent that they share tokens or subword fragments.

The mitigations are real but partial: the lexical arm of the retriever
(ADR 0002) covers exact terms the embedder cannot generalize, contextual headers
put the document's own vocabulary into every chunk, and the reranker's MMR term
stops one strong lexical match from filling the context window with near
duplicates. What none of that recovers is genuine paraphrase across disjoint
vocabulary. On a corpus where the questions use the users' words and the
documents use the authors' words, this is the ceiling, and it is lower than a
trained bi-encoder's.

### There is no ANN index, so retrieval is O(n) per query

`DenseIndex` is an exhaustive dot product over every vector. Measured on the
container this was built in — Python 3.11.15, Intel Xeon @ 2.80 GHz, 512
dimensions, `numpy` **not** installed, so the stdlib path is what ran:

| chunks | dense search | BM25 search | resident memory |
|---|---|---|---|
| 1,000 | 13 ms | not measured | ~25 MB † |
| 10,000 | 123 ms | 0.5 ms | 250 MB |
| 50,000 | 662 ms | not measured | ~1.2 GB † |

† scaled from the 10,000-chunk measurement, which is the only one taken. The
search timings are all measured, 20 queries each.

Two things are visible there and only one of them is the one people expect.

The latency is linear, as advertised. The **memory** is the sharper limit: a
512-dimension vector held as a Python list of floats costs about 25 KB, roughly
six times the 4 KB the same numbers occupy in the sqlite blob, because every
float is a boxed object. The lexical arm is not the problem — an inverted index
only touches the posting lists for terms actually in the query, which is why
BM25 stays under a millisecond while the dense arm crosses a tenth of a second.

### The token estimator is an estimate

`util.text.estimate_tokens` counts words and characters and takes the larger of
`words` and `len(text) // 4`. It is not a tokenizer and it has not been
calibrated against one here. It is used for chunk sizing and for the context
budget in `build_prompt`, both of which are soft budgets with headroom for
exactly this reason. Anyone who wires this into a hosted model with a hard
context limit must re-check the budget against that model's real tokenizer
before trusting it, especially on code and on non-Latin scripts, where the
four-characters-per-token assumption is at its worst.

### Where the costs stop being acceptable

Stated as a threshold so it can be checked rather than argued:

- **Under ~1,000 chunks** (the seed corpus is 48): every cost above is
  invisible. The stdlib core is simply the right answer.
- **1,000–10,000 chunks:** comfortable. Dense search stays inside the ~100 ms
  that reads as instant, memory stays in the hundreds of megabytes. Install the
  `fast` extra when it starts to feel slow; the numpy path changes nothing about
  the results.
- **10,000–50,000 chunks:** the point of review. Latency is now visible in an
  interactive loop and memory is the binding constraint. Keep the stdlib core
  for batch and eval work; expect to want a real ANN index for anything
  interactive.
- **Above ~50,000 chunks:** the exhaustive dense arm is the wrong tool.
  Sub-second-per-query and gigabyte-scale resident memory are not a tuning
  problem, they are the design showing its edge. Swap `DenseIndex` for an ANN
  index behind the same two methods (`add`, `search`) and keep everything else.
- **Independently of size:** if answer quality is limited by paraphrase rather
  than by ranking, replace the `Embedder` rather than adding hardware. The
  interface exists for that, and no other stage needs to know.

Note the shape of every one of those escapes: a class with the same two or three
methods. That is what "the core runs on the stdlib" is buying — not a promise
that the stdlib is enough forever, but that the thing you outgrow is one object
and not the architecture.

## Alternatives considered

**Depend on `sentence-transformers` and a vector database.** Better retrieval
out of the box, and the standard answer. Rejected because it moves the failure
from "answers are mediocre" to "nothing runs", and the second failure is the one
that kills adoption. It also makes the eval harness dishonest: numbers produced
against a model that downloads itself at first use cannot be reproduced by
someone whose network blocks the hub.

**Vendor the dependencies into the repository.** Keeps the install offline.
Rejected because vendored code is code you now maintain without having written
it, and a vendored transformer still needs its weights.

**Make the dependencies optional but the good paths dependent on them** — a
stdlib fallback that exists only so the import does not fail. Rejected as the
worst of both: the fallback path never gets exercised, so it rots, and the first
person to hit it discovers the "zero-dependency" claim was decorative. The rule
that numpy may only appear where the stdlib produces the *same* result is what
keeps this from happening quietly. It is also why the fallback does not rot: in
the container this was built in numpy is absent, so `make test`, `make eval` and
the numbers in the table above are all the stdlib path — the fast path is the
one that goes unexercised, which is the safer way round.

**Require a hosted model for generation.** Fluent answers, and a network
dependency on the one stage where being wrong is most expensive. Rejected as the
default, kept as a seam: `build_prompt` is written and unused by the extractive
generator, which is the honest way to leave a door open.
