---
provenance: enforced
---

# Fleet

Several Claude sessions run against these repositories concurrently. This file
is the roster and the rules that keep them from overwriting each other.

> This is a snapshot taken at 2026-08-27T15:04Z, not a live view. Re-run
> `mcp__Claude_Code_Remote__list_sessions` before trusting it. The fleet grew
> from 4 to 13 sessions in the 37 minutes between the first snapshot and this
> one, so a stale roster here is the normal case, not the exception.

## Roster

Ordered oldest first. Every session takes both repositories as sources except
where noted.

| Session | Title | Branch | Effort | Pushed? |
|---|---|---|---|---|
| `session_01WhTTExHdT83QPAKDFZm4fZ` | Go page review and ultrathink OODA | `claude/go-page-ultrathink-ooda-kqxvnc` | xhigh | no — `claude` only |
| `session_016cRrEmB1ZKGLpEzUQpSqhC` | Blind testing and OODA analysis | `claude/blind-testing-ooda-5o3s67` | xhigh | no |
| `session_019vCLpJgDUv8BYDRetyqzNq` | RAG system and data pipeline | `claude/rag-system-data-pipeline-rdkde9` | xhigh | **yes** — `1d7ce8f` |
| `session_01Ya1zvvkNDwhHKm2QtA4A5f` | Claude chat archive review | `claude/review-chat-archive-zrynr4` | xhigh | **yes** — `b11a6fa` |
| `session_01Y16zSaDWgURM68i51rfik2` | Daily file improvement system | `claude/daily-file-improvement-wgiluc` | xhigh | no |
| `session_01FQvAGnEvu2XY7hGtWRkMG3` | Reverse engineer chat history and system setup | `claude/reverse-engineer-chat-setup-husv9h` | xhigh | this session |
| `session_01GPgcWeschoejAkMjXJyby7` | AI system research and implementation | `claude/ai-system-research-3jpwda` | xhigh | no |
| `session_01QLk8iRamoDp6s1xEuTyd4P` | Claude code to Playground parity | `claude/code-playground-parity-xw0snj` | xhigh | no |
| `session_01DuBJPhHjftzVBGanSTQ9wo` | Ultrareview with data checkers | `claude/ultrareview-data-checkers-98ad9p` | xhigh | no |
| `session_01KaERecxQyogeT5Mde8cb1o` | Goal prompt task division | `claude/goal-prompt-task-division-0ghozd` | high | no |
| `session_01Rj2vRw3zymLrh5aPJEV6JP` | Comprehensive research and skill mastery | `claude/research-skill-mastery-mwjs01` | high | no |
| `session_01FKYZVu2ecPhHEcLJD2eWpF` | Personal skills and repos research | `claude/personal-skills-repos-research-dxmflq` | high | no |
| `session_01Vp6Nnb1YQ9xzppSDMSBEQD` | Untitled session | `claude/session-y42cyg` | xhigh | no |

The goal string each session was opened with is collected verbatim in
[profile/GOAL-CORPUS.md](profile/GOAL-CORPUS.md).

## Observed — fleet state

- The listing returned 13 sessions, all `RUNNING`, all created on 2026-08-27 between 14:07Z and 15:00Z. [src:FLEET-13-2026-08-27]
- All 13 run `claude-opus-5` in `permission_mode: auto` on environment `env_01GEni7AgBA7NiyMBecyt7K1`, and all originate from `web_claude_ai`. [src:FLEET-13-2026-08-27]
- Nine run at `effort_level: xhigh` and four at `high`. [src:FLEET-13-2026-08-27]
- The fleet grew from 4 sessions at 14:27Z to 13 at 15:04Z. [src:SESSIONS-2026-08-27] [src:FLEET-13-2026-08-27]
- Twelve of the 13 take both repositories as sources; `Go page review and ultrathink OODA` takes only `turkertekten-ship-it/claude`. [src:FLEET-13-2026-08-27]
- At 15:04Z exactly two branches existed on the `claude` remote — `claude/rag-system-data-pipeline-rdkde9` at `1d7ce8f` and `claude/review-chat-archive-zrynr4` at `b11a6fa` — so 11 of the 13 sessions had pushed nothing. [src:BRANCHES-2026-08-27T15-04Z]
- The remote `HEAD` pointed at `claude/rag-system-data-pipeline-rdkde9`. [src:BRANCHES-2026-08-27T15-04Z]
- This session's own branch, `claude/reverse-engineer-chat-setup-husv9h`, did not exist on the remote at that time. [src:BRANCHES-2026-08-27T15-04Z]
- 11 of the 13 sessions carry a goal string; it is null for `Blind testing and OODA analysis` and `Go page review and ultrathink OODA`. [src:GOALS-2026-08-27]

## Observed — the shared root

- The two pushed branches shared no ancestry, and their file listings overlapped on exactly `.gitignore` and `README.md`. [src:UNRELATED-HISTORIES-2026-08-27]
- That overlap was confirmed again at merge time and matched the prediction exactly: `git merge --allow-unrelated-histories` reported those two paths as add/add conflicts and auto-merged the other 32 files cleanly. [src:SUBSTRATE-MERGED-2026-08-27]
- The two branches were merged on `claude/reverse-engineer-chat-setup-husv9h` at commit `46adea6`, taking the pipeline branch as the root and joining the substrate onto it. Both conflicts were resolved by union; no file from either branch was dropped. [src:SUBSTRATE-MERGED-2026-08-27]

## The merge hazard

Because both repositories started empty, each session's first commit became its
own **root commit**. The branches were therefore unrelated histories, not
divergent ones. [src:UNRELATED-HISTORIES-2026-08-27]

**This is now partly resolved.** `claude/reverse-engineer-chat-setup-husv9h`
carries both pushed branches under one root [src:SUBSTRATE-MERGED-2026-08-27].
The convention that follows from it:

- **A shared root now exists.** Later branches rebase onto it rather than being
  merged with `--allow-unrelated-histories` again. Every further
  `--allow-unrelated-histories` merge adds another root and compounds the cost.
- **Eleven sessions have not pushed yet** [src:BRANCHES-2026-08-27T15-04Z].
  Each one that pushes a first commit adds a root unless it starts from the
  merged branch, so the cost grows with the size of the fleet — and the fleet
  more than tripled in 37 minutes [src:FLEET-13-2026-08-27].

**Before merging anything**, diff the file lists first:

```bash
comm -12 <(git ls-tree -r --name-only origin/<theirs> | sort) \
         <(git ls-tree -r --name-only origin/<mine>   | sort)
```

Any path in that output is a file two sessions wrote independently. Read both
versions before resolving; at this concurrency, silent clobbering is the
likeliest way work disappears. That check predicted this merge's conflicts
exactly, which is the argument for running it every time.

## Rules

**One branch per session.** Your branch is named in your own session record.
Push only there. A branch you did not create is someone else's working tree,
even when it looks abandoned.

**Push early.** Until you push, your work does not exist for the rest of the
fleet — there is no other channel through which they can see it. A long
unpushed branch is invisible work, and 11 of 13 sessions are currently in that
state [src:BRANCHES-2026-08-27T15-04Z].

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

The goal strings are different in kind: they are the owner's own typed input,
returned verbatim by the API [src:GOALS-2026-08-27]. They can be quoted as
what the owner asked for. They still are not a record of any conversation —
only of how one began.
