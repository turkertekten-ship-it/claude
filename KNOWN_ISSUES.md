---
provenance: enforced
---

# Known issues

## KI-1 — Transcript ingestion silently discarded data (fixed in `e392678`)

**Affects:** any copy of `tools/ingest_chat_archive.py` taken from commit
`e37b4c2` and not updated since.

**Check your copy in one command:**

```bash
python3 tools/ingest_chat_archive.py selfcheck
```

Exit 0 means your copy is sound. Exit 1 means it is affected and says what to
change. If the subcommand does not exist at all, your copy predates the fix and
is affected.

### What went wrong

`parse_claude_code_jsonl` keyed each conversation on `sessionId` alone. Subagent
transcripts carry their **parent's** `sessionId`, so every transcript for a
session collapsed onto one key and each file overwrote the previous one.

The damage is invisible in the output. The run reports how many messages it
*read*, not how many survived storage, so an affected copy prints a full,
healthy-looking count over a mostly-empty index.

### Observed — the actual numbers

- On this container, an affected run reported 3 conversations ingested but stored 1, with 44 of 347 messages retained. [src:PROJECTS-INGEST-2026-08-27]
- A subagent transcript and its parent transcript were confirmed to report the same `sessionId`. [src:SUBAGENT-SESSION-COLLISION-2026-08-27]
- The fix keys conversations and message ids on the session **and** the transcript file; all 347 messages then survive. [src:PROJECTS-INGEST-2026-08-27]

### If you are affected

Re-ingesting is required — stored counts do not correct themselves, and an
index built by an affected copy is incomplete no matter what it reported at the
time. Take the fix, then rebuild the index from source transcripts.

Treat any conclusion drawn from a search over an affected index as unsourced
until the search is re-run.

## Observed — spread through the fleet

- `claude/code-playground-parity-xw0snj` merged `e37b4c2` at merge commit `e7ab452`, combining it with the RAG branch's root `1d7ce8f`. [src:PARITY-MERGE-2026-08-27]
- That branch carries the affected version: its copy keys on `session` alone and has no `selfcheck` subcommand. [src:PARITY-MERGE-2026-08-27]
- It does not contain the three later commits on `claude/review-chat-archive-zrynr4`, including the fix. [src:PARITY-MERGE-2026-08-27]

### Observed — who is still affected (2026-08-28T07:52Z)

> How to reproduce: run `tools/fleet_selfcheck.sh`. It extracts each remote
> branch's copy and runs its `selfcheck`, rather than guessing from commit
> ancestry — a branch may have taken the fix by any route.

- Of 14 remote branches, 8 carry the ingester. [src:KI1-BRANCH-SCAN-2026-08-28]
- Passing: `code-playground-parity-xw0snj`, `reverse-engineer-chat-setup-husv9h`, `review-chat-archive-zrynr4`. [src:KI1-BRANCH-SCAN-2026-08-28]
- Still affected: `great-euler-6tx6y6`, `personal-skills-repos-research-dxmflq`, `research-skill-mastery-mwjs01`, `session-y42cyg`. [src:KI1-BRANCH-SCAN-2026-08-28]
- The parity branch took the fix at commit `a8f5236` after this advisory was filed. [src:KI1-BRANCH-SCAN-2026-08-28]

### Observed — how this was notified

- Sessions in this fleet run in separate containers and no peer messaging reaches them; `ListAgents` reports no reachable agents. [src:NO-TRANSCRIPT-TOOL-CONFIRMED-2026-08-27]
- The advisory is therefore filed as issue #1 on `turkertekten-ship-it/claude`, the repository every session takes as a source. It was the first issue on that repository. [src:KI1-ISSUE-2026-08-27]
- As of 15:16Z the parity branch had not moved and still lacked the fix. [src:PARITY-UNMOVED-2026-08-27]

> Three mechanisms, because no single one reaches a session that has already
> merged and moved on: `selfcheck` travels with the code and needs no notice to
> be read; this file travels with the repository; the issue is visible to anyone
> working the repository at all.
