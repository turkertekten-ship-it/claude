# claude — fleet substrate and retrieval pipeline

Two things live here, and they are built to serve each other:

1. **The doctrine** — the operating rules a fleet of Claude sessions runs
   under, the prompts that carry those rules, the record of what has actually
   been established, and the tooling that stops any of it drifting into
   invention.
2. **`oodarag`** — an OODA-driven retrieval pipeline that runs on the Python
   standard library alone. It is how the doctrine's Observe phase scales past
   what one session can read by hand.

Start with **[CLAUDE.md](CLAUDE.md)**. Then read
**[provenance/observations.md](provenance/observations.md)** — it is the only
file here that states established fact, and everything else is built on it.

## The one rule

A factual claim is either sourced or it is not written down.

Claims carry a `[src:ID]` tag resolving to `provenance/sources.yaml`. Anything
unsourced belongs in `provenance/unknowns.md` as an open question. This is
enforced, not trusted:

```bash
bash tests/run_all.sh        # verifier, every test suite, and the mirror check
```

## Two repositories, mirrored

`turkertekten-ship-it/claude` and `turkertekten-ship-it/claude-ai` carry the
same doctrine and tooling, so a session cloning either one is fully equipped.
That duplication is deliberate and its cost is checked rather than trusted —
`make mirror-check` fails on any difference, `make mirror` re-syncs, and the
check runs inside `run_all.sh` whenever the sibling repository is on disk.

## Why the pipeline exists

Most RAG code is a demo: load a folder, call an embedding API,
cosine-similarity top-5, stuff it in a prompt. That works until it meets a real
corpus, at which point the failure modes are always the same — the index is
stale, the chunks lost their context, the retriever returns the site footer,
and nobody can tell you whether last week's change made retrieval better or
worse.

`oodarag` is built around those failure modes rather than around the happy path:

| Failure mode | What this does about it |
|---|---|
| Index goes stale | Content-hash incremental ingest + an OODA loop that decides when to re-fetch |
| Chunks lose context | Contextual headers embedded with every chunk |
| Retriever returns boilerplate | Structural + link-density boilerplate removal in the scraper |
| Same page indexed 5 times | Canonical-URL and content-hash dedupe |
| Semantic search misses exact terms | Hybrid dense + BM25 retrieval fused with RRF |
| "Is retrieval any good?" | An eval harness with recall@k, MRR, nDCG and citation coverage |
| Secrets leak into the index | Redaction at the connector boundary, before anything is written |
| A crawl runs forever | Budgets on pages, fetches, bytes, depth and wall-clock |
| A source is unreachable | A typed diagnostic naming *which* barrier, not a stack trace |

## Quick start

```bash
make test          # stdlib unittest + the provenance guard, no dependencies
make demo          # end-to-end: ingest -> index -> query -> eval
make reachability  # what this container can and cannot fetch, as a table
```

## What is here

| Path | Purpose |
|---|---|
| `CLAUDE.md` | The doctrine. Read first. |
| `FLEET.md` | Which sessions run concurrently, and on which branches. |
| `provenance/` | The ledger, the observations, the unknowns, the raw captures. |
| `prompts/` | System prompts carrying the doctrine into a session. |
| `src/oodarag/` | The retrieval pipeline. |
| `tools/verify_provenance.py` | The fabrication guard. |
| `tools/verify_mirror.py` | The drift guard: both repositories must agree. |
| `corpus/` | Committed source material, including the video manifest. |
| `tools/ingest_chat_archive.py` | Conversation-archive ingestion and search. |
| `tests/` | Tests for all of the above, including their failure cases. |
| `.claude/skills/` | `ooda` and `researching-before-acting`, loaded by cloud sessions. |
| `.claude/commands/` | The workflows, as slash commands. |
| `.claude/agents/` | `observer` and `fact-checker` subagents. |
| `docs/workflows.md` | How the workflows and subagents fit together. |

## Design principles

1. **Zero required dependencies.** The whole pipeline runs on the stdlib, so it
   works in CI, in an air-gapped container, and on a laptop. Accelerators
   (numpy) and hosted models plug in behind interfaces.
2. **Provenance is load-bearing.** Every chunk carries the URI and commit sha it
   came from. Citations are verified against retrieved chunks, not generated.
3. **Everything is bounded.** Every network stage has a budget on requests,
   bytes and time.
4. **Degrade, don't die.** Blocked egress, a missing API key or a truncated API
   response reduce what the pipeline can do; they never make it crash — and the
   pipeline says which of the three it hit.
5. **Measure, don't assert.** Retrieval quality is a number in an eval report.

## Searching your conversations

The archive ships empty. To populate it with your own history:

```bash
# claude.ai: Settings -> Privacy -> Export data, unzip into archive/
# Claude Code: cp ~/.claude/projects/**/*.jsonl archive/

python3 tools/ingest_chat_archive.py ingest
python3 tools/ingest_chat_archive.py search "retrieval pipeline"
python3 tools/ingest_chat_archive.py stats
```

Messages are stored verbatim and every hit carries its conversation id,
message id, timestamp, and source file, so a result can be quoted as evidence.
Records that cannot be parsed are skipped and counted, never repaired by
guesswork. `archive/` is git-ignored — the exports are the owner's data, not
repository content.

## Status

The doctrine tooling runs and is tested. The provenance ledger holds what was
actually established, with the egress limits of this container measured rather
than assumed.

The chat index holds this session's own Claude Code transcript — 620 messages,
nothing unparseable — which is the only conversation present on this container.
It does not hold the owner's claude.ai history; that needs an export dropped
into `archive/`, and until one arrives the index answers questions about one
day of work rather than about a history.

Scope deliberately left open is in [provenance/unknowns.md](provenance/unknowns.md).
