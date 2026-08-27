---
provenance: enforced
---

# Fleet

Several Claude sessions run against these repositories concurrently. This file
is the roster and the rules that keep them from overwriting each other.

> This is a snapshot taken at 2026-08-27T15:20Z, not a live view. Re-run
> `mcp__Claude_Code_Remote__list_sessions` before trusting it. The previous
> snapshot, taken 53 minutes earlier, listed four sessions. It is kept below as
> a worked example of how fast this file goes stale.

## Roster

| Created (Z) | Title | Branch |
|---|---|---|
| 14:07 | Go page review and ultrathink OODA | `claude/go-page-ultrathink-ooda-kqxvnc` |
| 14:11 | Blind testing and OODA analysis | `claude/blind-testing-ooda-5o3s67` |
| 14:18 | RAG system and data pipeline | `claude/rag-system-data-pipeline-rdkde9` |
| 14:26 | Claude chat archive review | `claude/review-chat-archive-zrynr4` |
| 14:49 | Daily file improvement system | `claude/daily-file-improvement-wgiluc` |
| 14:50 | Reverse engineer chat history and system setup | `claude/reverse-engineer-chat-setup-husv9h` |
| 14:52 | AI system research and implementation | `claude/ai-system-research-3jpwda` |
| 14:53 | **Claude code to Playground parity** | `claude/code-playground-parity-xw0snj` |
| 14:54 | Ultrareview with data checkers | `claude/ultrareview-data-checkers-98ad9p` |
| 14:55 | Goal prompt task division | `claude/goal-prompt-task-division-0ghozd` |
| 14:57 | Comprehensive research and skill mastery | `claude/research-skill-mastery-mwjs01` |
| 14:58 | Personal skills and repos research | `claude/personal-skills-repos-research-dxmflq` |
| 15:00 | *(untitled)* | `claude/session-y42cyg` |
| 15:00 | *(untitled)* | `claude/great-euler-6tx6y6` |

## Observed — fleet state at snapshot time

- Fourteen sessions were listed at 15:20Z, thirteen RUNNING and one IDLE; ten of them were created between 14:49Z and 15:00Z. [src:SESSIONS-2026-08-27T15-20Z]
- All fourteen run `claude-opus-5` in `permission_mode: auto` on environment `env_01GEni7AgBA7NiyMBecyt7K1`, and all originate from `web_claude_ai`. [src:SESSIONS-2026-08-27T15-20Z]
- Thirteen take both repositories as sources; `Go page review and ultrathink OODA` takes only `turkertekten-ship-it/claude`. [src:SESSIONS-2026-08-27T15-20Z]
- At the earlier 14:27Z snapshot there were four sessions and neither remote had a single ref. [src:SESSIONS-2026-08-27] [src:REPO-EMPTY-2026-08-27]
- The sessions run in separate containers and could not message each other as local peers. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]
- No tool for reading another session's transcript was available, so cross-session knowledge is limited to metadata and to whatever gets pushed. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]

> The list arrives wrapped in an untrusted-content envelope, and the task
> summaries inside it are each session's claim about its own work. Branch names
> and timestamps are recorded above; the summaries are not, because a status
> line is not a finding.

## Rules

**The roster goes stale in under an hour.** Fourteen sessions replaced four in
fifty-three minutes. Re-run the listing rather than trusting this table, and
`git ls-remote` rather than trusting a branch name you read here.

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
