---
provenance: enforced
---

# Fleet

Several Claude sessions run against these repositories concurrently. This file
is the roster and the rules that keep them from overwriting each other.

> This is a snapshot taken at 2026-08-27T14:27Z, not a live view. Re-run
> `mcp__Claude_Code_Remote__list_sessions` before trusting it.

## Roster

| Session | Title | Branch | Effort | Sources |
|---|---|---|---|---|
| `session_01Ya1zvvkNDwhHKm2QtA4A5f` | Claude chat archive review | `claude/review-chat-archive-zrynr4` | high | both |
| `session_019vCLpJgDUv8BYDRetyqzNq` | RAG system and data pipeline | `claude/rag-system-data-pipeline-rdkde9` | xhigh | both |
| `session_016cRrEmB1ZKGLpEzUQpSqhC` | Blind testing and OODA analysis | `claude/blind-testing-ooda-5o3s67` | xhigh | both |
| `session_01WhTTExHdT83QPAKDFZm4fZ` | Go page review and ultrathink OODA | `claude/go-page-ultrathink-ooda-kqxvnc` | xhigh | `claude` only |

## Observed — fleet state at snapshot time

- All four sessions were RUNNING, created within 19 minutes of each other on 2026-08-27, all on `claude-opus-5` in `permission_mode: auto`. [src:SESSIONS-2026-08-27]
- No session had pushed a commit: both remotes had zero refs. [src:REPO-EMPTY-2026-08-27]
- The sessions run in separate containers and could not message each other as local peers. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]
- No tool for reading another session's transcript was available, so cross-session knowledge is limited to metadata and to whatever gets pushed. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]

## Rules

**One branch per session.** Your branch is named in your own session record.
Push only there. A branch you did not create is someone else's working tree,
even when it looks abandoned.

**Push early.** Until you push, your work does not exist for the rest of the
fleet — there is no other channel through which they can see it. A long
unpushed branch is invisible work.

**Read before you build on it.** Another session's branch counts as known only
once it is pushed *and* you have read the diff. Its title and status line are
not a substitute.

**Doctrine has one home.** Shared rules and tooling live in
`turkertekten-ship-it/claude`. `claude-ai` points here rather than keeping a
second copy, so the rules cannot fork.

**Merge deliberately.** When two branches touch the same file, read both sides
before resolving. Concurrency at this density makes silent clobbering the
likeliest failure.

## Reading the roster honestly

A title is a generated label. "RAG system and data pipeline" establishes that a
session carries that name — nothing about what it built, chose, or concluded.
The same holds for the status summaries: they are each session's claim about
its own work. Cite them as second-hand, or verify them yourself.
