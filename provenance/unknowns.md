# Open questions

Questions this session could not answer from evidence, recorded so a later
session inherits the question instead of quietly answering it from imagination.

An entry leaves this file in one of two ways: the owner states the answer and it
becomes a sourced observation, or evidence turns up that settles it. It never
leaves because someone found it inconvenient.

---

### U-1 — What is `oodarag` ultimately meant to do?

The README describes a nine-stage pipeline (ingest, normalize, chunk, embed,
index, retrieve, rerank, generate, evaluate) `[src:S-1]`. Four stages have code:
`util`, `ingest`, `scrape`, and the `models` that flow between them `[src:S-6]`.
The remaining five exist only as prose. Whether they are intended, deferred, or
aspirational is not recorded anywhere in the tree.

**Blocks:** knowing whether the missing stages are a gap to fill or a claim to retract.

### U-2 — What corpus is this pipeline for?

Two connectors exist: GitHub and web crawl `[src:S-1]`. The README's failure-mode
table mentions transcripts and chat, and `models.py` names "a YouTube video id, a
chat session uuid" in a docstring `[src:S-1]`. No such connector exists. Whether
those are planned sources or illustrative examples is undetermined.

### U-3 — Is there an intended retrieval quality target?

The README asserts an eval harness reporting recall@k, MRR, nDCG and citation
coverage `[src:S-1]`. No thresholds, goldens or target numbers appear anywhere,
and `evals/goldens.jsonl` — referenced by the Makefile's `eval` target — does not
exist `[src:S-1]`. Without a target, "is retrieval any good" has no answer even
once the harness is built.

### U-4 — What belongs in `prompts/`?

`turkertekten-ship-it/claude-ai`'s CLAUDE.md names `prompts/` as one of four
directories holding this project's doctrine `[src:S-2]`. No such directory exists
here `[src:S-1]`. This session created the other three (`provenance/`, `tools/`,
and the `CLAUDE.md` reference) because their contents were determined by work
actually done; `prompts/` was not invented, because nothing in either repository
indicates what would go in it.

**Resolved by:** the owner stating what `prompts/` is for, or removing the reference.

### U-5 — How is work divided between `claude` and `claude-ai`?

`claude-ai`'s CLAUDE.md states that shared doctrine and tooling stay in `claude`
and that `claude-ai` points at them, and explicitly records the division itself
as undecided `[src:S-2]`. Both repositories were near-empty when that was
written: `claude-ai` contains one file, `claude` contains a Python package
`[src:S-1]`. There is no history, issue, or README from which the intended split
can be established, so nothing has been invented to fill it.

The interim convention is unchanged: doctrine and tooling here, a pointer there.

**Resolved by:** the owner stating the intended division. Until then, work that
could go in either repository goes here, where the tooling is.

### U-6 — Is `docs/adr/0001-zero-dependency-core.md` the start of an ADR series?

Three source files reference that ADR by number `[src:S-1]`. This session wrote
it, because the decision it records is evidenced by the tree (an empty
`dependencies` list and an import graph that is stdlib-only). Whether further
ADRs are wanted, and under what numbering, is not established.
