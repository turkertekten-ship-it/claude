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

## KI-2 — Tool output indexed as the owner speaking (fixed on `claude/reverse-engineer-chat-setup-husv9h`)

**Affects:** any copy of `tools/ingest_chat_archive.py` whose
`parse_claude_code_jsonl` reads the role straight off the record, i.e. every
copy taken before this fix — including copies that already carry the KI-1 fix.

**Check your copy with the same command as KI-1:**

```bash
python3 tools/ingest_chat_archive.py selfcheck
```

The check now covers both defects. Exit 1 naming `TOOL OUTPUT AS THE OWNER`
means you are affected by KI-2; exit 1 naming `SILENTLY DISCARDS` means KI-1.
A copy whose selfcheck reports only two expected counts rather than three
predates this fix.

### What went wrong

Claude Code has no separate record type for tool results. It writes them as
`type: "user"` with `message.role: "user"`, and the ingester took that field at
face value. Every command's output — every `git status`, every test run, every
file listing — was therefore stored as something the owner said.

The damage is subtler than KI-1's. Nothing is lost and no count is wrong. What
breaks is the one question the index exists to answer: search it for what the
owner asked for and you get mostly log lines back, with the few real messages
buried among them.

### Observed — the actual numbers

- A search of the populated index for `reverse engineer` returned three hits all labelled `user`, of which two were Bash output and none was typed by the owner. [src:ROLE-ATTRIBUTION-BUG-2026-08-27]
- After the fix, `search "ooda" --role user` returned 2 hits, both the owner's own goal text. [src:ROLE-ATTRIBUTION-BUG-2026-08-27]
- The detector was watched failing against a copy with only the role derivation reverted, confirming it is independent of the KI-1 check rather than masked by it. [src:ROLE-ATTRIBUTION-BUG-2026-08-27]

### If you are affected

`effective_role` derives the role from the content blocks: a record whose blocks
are exclusively `tool_result` is filed as `tool_result` rather than `user`. The
text is still stored verbatim and still searchable — only the attribution
changes — and `search` gains a `--role` filter so the owner's own words can be
isolated.

Re-ingest afterwards. Stored roles do not correct themselves.

## Observed — spread through the fleet

- `claude/code-playground-parity-xw0snj` merged `e37b4c2` at merge commit `e7ab452`, combining it with the RAG branch's root `1d7ce8f`. [src:PARITY-MERGE-2026-08-27]
- That branch carries the affected version: its copy keys on `session` alone and has no `selfcheck` subcommand. [src:PARITY-MERGE-2026-08-27]
- It does not contain the three later commits on `claude/review-chat-archive-zrynr4`, including the fix. [src:PARITY-MERGE-2026-08-27]

### Observed — who is still affected (2026-08-28T08:05Z)

> How to reproduce: `python3 tools/fleet_probe.py`. It imports each remote
> branch's copy and runs two transcripts sharing a sessionId through its
> parser, checking both survive. Behaviour is the oracle — see the correction
> below for why the copy's own `selfcheck` subcommand is not.

- Of 14 remote branches, 7 carry the ingester. [src:KI1-PROBE-SCAN-2026-08-28]
- Sound: `code-playground-parity-xw0snj`, `reverse-engineer-chat-setup-husv9h`, `review-chat-archive-zrynr4`, `session-y42cyg`. [src:KI1-PROBE-SCAN-2026-08-28]
- Affected: `great-euler-6tx6y6`, `personal-skills-repos-research-dxmflq`, `research-skill-mastery-mwjs01`. [src:KI1-PROBE-SCAN-2026-08-28]

### Fixing an affected copy

> One command, and it declines to act when it is unsure:
> `python3 tools/fix_ki1.py tools/ingest_chat_archive.py --write`

- The fixer does nothing when the copy is already sound, refuses to write unless the patched source demonstrably keeps both transcripts, keeps a `.ki1.bak`, and prints the change rather than guessing when the code has drifted. Verified against a copy taken from `great-euler-6tx6y6`, including that a second run is a no-op. [src:KI1-FIXER-VERIFIED-2026-08-28]

### Correction — an earlier scan was wrong

- A first scan reported `session-y42cyg` as affected. It is not: it carries the keying fix but predates the `selfcheck` subcommand, so asking for `selfcheck` returned "invalid choice" and the script read that as failure. [src:KI1-PROBE-SCAN-2026-08-28]

> "Has no detector" is not "is defective". The script that made that mistake
> has been removed rather than left to mislead, and the correction is posted on
> issue #1 where the wrong list was published.

### Observed — how this was notified

- Sessions in this fleet run in separate containers and no peer messaging reaches them; `ListAgents` reports no reachable agents. [src:NO-TRANSCRIPT-TOOL-CONFIRMED-2026-08-27]
- The advisory is therefore filed as issue #1 on `turkertekten-ship-it/claude`, the repository every session takes as a source. It was the first issue on that repository. [src:KI1-ISSUE-2026-08-27]
- As of 15:16Z the parity branch had not moved and still lacked the fix. [src:PARITY-UNMOVED-2026-08-27]

> Three mechanisms, because no single one reaches a session that has already
> merged and moved on: `selfcheck` travels with the code and needs no notice to
> be read; this file travels with the repository; the issue is visible to anyone
> working the repository at all.
