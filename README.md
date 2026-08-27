# claude — fleet substrate

Operating rules, prompts, provenance, and tooling for a fleet of Claude
sessions working on one owner's behalf.

Start with **[CLAUDE.md](CLAUDE.md)**. Then read
**[provenance/observations.md](provenance/observations.md)** — it is the only
file here that states established fact, and everything else is built on it.

## The one rule

A factual claim is either sourced or it is not written down.

Claims carry a `[src:ID]` tag resolving to `provenance/sources.yaml`. Anything
unsourced belongs in `provenance/unknowns.md` as an open question. This is
enforced, not trusted:

```bash
bash tests/run_all.sh        # verifier + both test suites
```

## What is here

| Path | Purpose |
|---|---|
| `CLAUDE.md` | The doctrine. Read first. |
| `FLEET.md` | Which sessions run concurrently, and on which branches. |
| `provenance/` | The ledger, the observations, the unknowns, the raw captures. |
| `prompts/` | System prompts carrying the doctrine into a session. |
| `tools/verify_provenance.py` | The fabrication guard. |
| `tools/ingest_chat_archive.py` | Conversation-archive ingestion and search. |
| `tests/` | Tests for both tools, including their failure cases. |
| `.claude/commands/` | The workflows, as slash commands. |
| `.claude/agents/` | `observer` and `fact-checker` subagents. |
| `.claude/` | Hooks and the OODA skill. |
| `docs/workflows.md` | How the workflows and subagents fit together. |

## Searching your conversations

**Run this on your own machine.** Claude Code keeps every transcript under
`~/.claude/projects`, so that is where your history actually lives — one flag
indexes all of it:

```bash
python3 tools/ingest_chat_archive.py ingest --include-projects
python3 tools/ingest_chat_archive.py search "retrieval pipeline"
python3 tools/ingest_chat_archive.py stats
```

On the container this was built in, that directory held only this session, so
what you get here is small and what you get on your own machine is not.

Your **claude.ai** threads are separate and are not on disk anywhere. Export
them (Settings → Privacy → Export data), unzip `conversations.json` into
`archive/`, and run `ingest` again — that reader is written to the documented
export shape but has only been exercised against fixtures, so check the skip
count on the first real run.

Messages are stored verbatim and every hit carries its conversation id,
message id, timestamp, and source file, so a result can be quoted as evidence.
Records that cannot be parsed are skipped and counted, never repaired by
guesswork. `archive/` is git-ignored — the exports are the owner's data, not
repository content.

## Status

The tooling runs and is tested. The provenance ledger holds what was actually
established on 2026-08-27. The chat index holds nothing yet, and says so
rather than pretending otherwise.
