# claude — fleet substrate

Operating rules, prompts, provenance, and tooling for a fleet of Claude
sessions working on one owner's behalf — plus `oodarag`, the retrieval pipeline
those sessions build against.

Start with **[CLAUDE.md](CLAUDE.md)**. Then read
**[provenance/observations.md](provenance/observations.md)** — it is the only
file here that states established fact, and everything else is built on it.

## The one rule

A factual claim is either sourced or it is not written down.

Claims carry a `[src:ID]` tag resolving to `provenance/sources.yaml`. Anything
unsourced belongs in `provenance/unknowns.md` as an open question. This is
enforced, not trusted:

```bash
bash tests/run_all.sh        # verifier + tool suites + the pipeline suite
```

## What is here

### The substrate — how sessions work

| Path | Purpose |
|---|---|
| `CLAUDE.md` | The doctrine. Read first. |
| `FLEET.md` | Which sessions run concurrently, and on which branches. |
| `profile/` | The owner's standing preferences, and the evidence they came from. |
| `provenance/` | The ledger, the observations, the unknowns, the raw captures. |
| `prompts/` | System prompts carrying the doctrine into a session. |
| `tools/verify_provenance.py` | The fabrication guard. |
| `tools/ingest_chat_archive.py` | Conversation-archive ingestion and search. |
| `tools/install_user_scope.py` | Installs the doctrine into `~/.claude/`, so it reaches every terminal. |
| `.claude/commands/` | The workflows, as slash commands. |
| `.claude/agents/` | The subagent definitions. |
| `.claude/` | Hooks and the OODA skill. |
| `docs/workflows.md` | How the workflows and subagents fit together. |

### oodarag — the retrieval pipeline

An OODA-driven, end-to-end RAG pipeline that runs on the Python standard
library alone.

```
Observe  ->  Orient   ->  Decide   ->  Act
ingest       normalize    policy       reindex / backfill
             chunk        engine       / alert / answer
             embed
             index
```

| Path | Purpose |
|---|---|
| `src/oodarag/` | The pipeline: ingest, normalize, chunk, embed, index, retrieve, rerank, generate, evaluate, loop. |
| `internal/CONTRACTS.md` | The frozen interface spec every module is built against. |
| `internal/PLAN.md` | What is built, what is next, and what to still distrust. |
| `docs/adr/` | The decisions, with their costs stated. |
| `evals/` | The golden set and the offline seed corpus. |

It is built around the failure modes of real corpora rather than the happy path:

| Failure mode | What this does about it |
|---|---|
| Index goes stale | Content-hash incremental ingest, plus an OODA loop that decides when to re-fetch |
| Chunks lose context | Contextual headers embedded with every chunk |
| Retriever returns boilerplate | Structural and link-density boilerplate removal in the scraper |
| Same page indexed 5 times | Canonical-URL and content-hash dedupe |
| Semantic search misses exact terms | Hybrid dense + BM25 retrieval fused with RRF |
| "Is retrieval any good?" | An eval harness with recall@k, MRR, nDCG and citation coverage |
| Secrets leak into the index | Redaction at the connector boundary, before anything is written |
| A crawl runs forever | Budgets on pages, fetches, bytes, depth and wall-clock |

Design principles: zero required dependencies, provenance is load-bearing,
everything is bounded, degrade rather than die, measure rather than assert.

```bash
make test          # stdlib unittest, no dependencies required
make demo          # end-to-end, offline: ingest -> index -> query -> eval
```

## Searching your conversations

The archive ships empty of claude.ai exports. To populate it:

```bash
# claude.ai: Settings -> Privacy -> Export data, unzip into archive/
# Claude Code: cp ~/.claude/projects/**/*.jsonl archive/

python3 tools/ingest_chat_archive.py ingest
python3 tools/ingest_chat_archive.py search "retrieval pipeline"
python3 tools/ingest_chat_archive.py search "ooda" --role user   # your words only
python3 tools/ingest_chat_archive.py stats
```

Messages are stored verbatim and every hit carries its conversation id,
message id, timestamp, and source file, so a result can be quoted as evidence.

`--role user` matters more than it looks. Claude Code files tool *output* as
user-typed records, so without the distinction a search for what you asked for
returns mostly command output. Tool results are indexed under `tool_result` and
stay searchable; they are just no longer attributed to you.
Records that cannot be parsed are skipped and counted, never repaired by
guesswork. `archive/` is git-ignored — the exports are the owner's data, not
repository content.

## What the owner asked for

[`profile/OWNER-PROFILE.md`](profile/OWNER-PROFILE.md) reconstructs the owner's
standing preferences from [`profile/GOAL-CORPUS.md`](profile/GOAL-CORPUS.md) —
the verbatim goal strings across their concurrent sessions. Every preference
carries the goals it was derived from and a confidence grade, so a weak
inference cannot later be used as though it were a strong one.

That corpus is not the conversation history. It is the opening line of each
session, which is what was actually reachable. The gap is recorded as U-2 in
[`provenance/unknowns.md`](provenance/unknowns.md) rather than papered over.

## Status

The substrate tooling runs and is tested. The provenance ledger holds what was
actually established on 2026-08-27. See `internal/PLAN.md` for the pipeline's
per-stage status and its known gaps.
