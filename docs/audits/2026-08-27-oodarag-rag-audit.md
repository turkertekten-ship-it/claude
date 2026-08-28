---
provenance: enforced
---

# `rag-audit` run against `src/oodarag/` — 2026-08-27

Produced by routing the newly installed [`rag-audit`](../../.claude/skills/rag-audit/SKILL.md)
skill at the pipeline, per the routing table in [SKILLS.md](../../SKILLS.md).
The skill's six audit categories are used as the frame; every finding below was
checked against the code rather than inferred from the README.

The headline: **what is built is built well, and the README describes a system
roughly twice its current size.** Nothing here is a design criticism — it is a
gap between a document that reads as finished and a tree that is halfway.

## Observed — what exists

- `src/oodarag/` contains exactly `__init__.py`, `models.py`, `ingest/`, `scrape/` and `util/`, totalling 2583 lines. [src:AUDIT-OODARAG-2026-08-27]
- The directories `chunk`, `embed`, `index`, `retrieve`, `rerank`, `eval`, `policy` and `store` are all absent. [src:AUDIT-OODARAG-2026-08-27]
- `redact_secrets` is called on every `RawDocument` construction path in both connectors, at `ingest/web.py:53` and `ingest/github.py:402,414,448,471,491`. [src:AUDIT-OODARAG-2026-08-27]
- `scrape/crawler.py` enforces `max_pages`, `max_fetches`, `max_depth` and a wall-clock budget, and records which one stopped the crawl in `report.stopped_by`. [src:AUDIT-OODARAG-2026-08-27]
- `pyproject.toml` declares the console script `ooda = "oodarag.cli:main"`, and `src/oodarag/cli.py` does not exist. [src:AUDIT-OODARAG-2026-08-27]
- `README.md` links `internal/PLAN.md` and `docs/adr/0001-zero-dependency-core.md`; neither path exists. [src:AUDIT-OODARAG-2026-08-27]
- The `Makefile` declares `demo`, `index`, `query`, `eval` and `loop` targets. [src:AUDIT-OODARAG-2026-08-27]

> **Superseded in part, 2026-08-27T17:00Z.** That session has since pushed
> three more commits, and every finding below has now been re-checked against
> them. The findings are kept as written rather than edited, because a
> rewritten audit is not a record; the disposition is in the table
> immediately below.

## Disposition after re-check

| Finding | Status | Basis |
|---|---|---|
| **F-1** — console script with no module | **Fixed** | `src/oodarag/cli.py` exists. [src:RAG-BRANCH-COMPLETE-2026-08-27] |
| **F-2** — README claims outrunning the code | **Fixed** | All eight rows now have code: `reciprocal_rank_fusion`, `recall_at_k`/`mrr`/`ndcg_at_k`, `citation_coverage` in the eval harness, and a citation contract in `generate/`. Both dangling links resolve. [src:AUDIT-RECHECK-2026-08-27] |
| **F-3** — Makefile targets that cannot succeed | **Fixed** | The stages they invoke now exist. [src:RAG-BRANCH-COMPLETE-2026-08-27] |
| **F-4** — chunking contract with no chunker | **Fixed** | `chunk_document` builds `Chunk(context_header=…)` from `heading_path`, classifying documents and splitting prose and code separately. [src:AUDIT-RECHECK-2026-08-27] |
| **F-5** — token estimator bias undocumented | **Stands** | `estimate_tokens` is unchanged and now cites the ADR, but that ADR does not record the estimator's bias. [src:AUDIT-RECHECK-2026-08-27] |

Two things worth saying plainly about that table.

**The convergence is not influence.** `chunking.py` classifies by document kind
and threads the heading path into `context_header` — the same shape as
[the chunking design](../design/chunking.md) written here. There is no evidence
that session read this audit, and none should be claimed. Two readings of the
same code and the same `Chunk` dataclass arriving at the same place is
corroboration that the design was the obvious one, not evidence that it
travelled.

**F-5 is now a one-line fix.** The heuristic itself is right and should stay —
a real tokenizer would need Hugging Face, which is unreachable here
[src:DOCLING-MODELS-BLOCKED-2026-08-27], so the zero-dependency choice is also
the only working choice. What is missing is a sentence in
`docs/adr/0001-zero-dependency-core.md` saying the error is systematic rather
than random and worst on code, where the chunk bounds are tightest. Without it,
the first eval swing after a tokenizer comparison will read as a retrieval
regression.

## Findings

### F-1 — `pip install .` produces a console script that cannot run · blocking

`[project.scripts]` maps `ooda` to `oodarag.cli:main`, but there is no
`cli.py`. [src:AUDIT-OODARAG-2026-08-27] Packaging succeeds, the `ooda`
executable is written to `bin/`, and the first invocation dies with
`ModuleNotFoundError: No module named 'oodarag.cli'`. This is the first thing a
new user does, and it fails before any of the good work is visible.

*Fix:* either add a `cli.py` whose `main()` currently prints the implemented
subcommands, or comment out the `[project.scripts]` block until it exists.
The second is one line and honest.

### F-2 — the README's failure-mode table presents planned work as delivered · high

The table maps eight named failure modes to what the pipeline "does about it",
in the present tense. Four of the eight have code:
boilerplate stripping, content-hash dedupe, redaction, and crawl budgets.
The other four — the OODA staleness policy, contextual chunking, hybrid
dense+BM25 with RRF, and the recall@k / MRR / nDCG eval harness — have no
module at all. [src:AUDIT-OODARAG-2026-08-27]

The `Status` section does say "under active construction", but it points at
`internal/PLAN.md` for the split, and that file is absent
[src:AUDIT-OODARAG-2026-08-27] — so a reader has no way to tell which half they
are looking at. For a repository whose first design principle is that
provenance is load-bearing, a capability table that does not distinguish built
from intended is the one document most worth fixing.

*Fix:* add a status column to the table — a two-character marker per row is
enough — and either write `internal/PLAN.md` or stop linking it.

### F-3 — `make demo`, `query`, `eval` and `loop` cannot succeed · high

All four targets are declared [src:AUDIT-OODARAG-2026-08-27] and all four need
modules that do not exist. `make demo` is offered in the README's Quick start,
directly beneath `make test`, which does work.

*Fix:* have the unimplemented targets exit non-zero with the stage they are
waiting on, rather than failing with a traceback.

### F-4 — chunking has a contract but no implementation · medium

`Chunk.context_header` is defined and documented as the contextual-retrieval
prefix, embedded and indexed with the body. That is the right design and it is
the correct answer to the "chunks lose context" failure mode. But no chunker
constructs a `Chunk`. [src:AUDIT-OODARAG-2026-08-27]

The pieces are already sitting in `util/text.py`:
`split_markdown_sections` returns heading paths with offsets, and
`heading_path` resolves an offset to its heading stack — which is exactly the
input a `context_header` needs. This is the shortest path to a working
retrieval spine.

*Route:* [`chunking-advisor`](../../.claude/skills/chunking-advisor/SKILL.md)
before writing the chunker — the corpus mixes prose, code and (per
`models.py`) transcripts, and those should not share one strategy.

### F-5 — `estimate_tokens` is a heuristic that the eval harness will inherit · low

`estimate_tokens` approximates ~4 chars/token and says in its own docstring
that it is deliberately an estimate, to avoid a tokenizer dependency. That
trade is defensible and consistent with design principle 1. It becomes a
problem only when chunk sizes are tuned against it and then compared to a
provider's real token count — the drift is systematic, not random, and worst
on code.

*Fix:* not now. Record it as a known bias in the ADR when the eval harness
lands, so a future retrieval regression is not misattributed.

## What passed

Three of the README's claims were checked and hold:

- **Redaction really is at the connector boundary**, not bolted on downstream — every path that builds a `RawDocument` goes through it. [src:AUDIT-OODARAG-2026-08-27]
- **Crawls really are bounded**, on four independent axes, and the crawler reports which budget stopped it rather than silently truncating. [src:AUDIT-OODARAG-2026-08-27]
- **Provenance really is carried in the data model** — `doc_id` and `content_hash` flow from `RawDocument` through `Document` to `Chunk`.

The audit skill's remaining categories — embedding configuration, vector store
setup, retrieval pipeline, generation configuration — could not be assessed,
because none of those stages exists yet. [src:AUDIT-OODARAG-2026-08-27] That is
an absence, not a pass. Re-run this audit when the retrieval spine lands.
