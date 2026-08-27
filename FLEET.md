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
| (this session) | Research and skill mastery | `claude/research-skill-mastery-mwjs01` | — | both |

> The last row was added after the snapshot above and is not part of it; this
> session was not in the 14:27Z listing.

## Observed — fleet state

- All four sessions were RUNNING, created within 19 minutes of each other on 2026-08-27, all on `claude-opus-5` in `permission_mode: auto`. [src:SESSIONS-2026-08-27]
- At 14:27Z no session had pushed anything: both remotes had zero refs. [src:REPO-EMPTY-2026-08-27]
- By 15:00Z, `claude/rag-system-data-pipeline-rdkde9` had appeared on the `claude` remote at commit `1d7ce8f`, pushed 14:34:34Z, carrying 20 files — a Python package under `src/oodarag/` with `ingest/`, `scrape/`, and `util/` subpackages, plus a Makefile, `pyproject.toml`, `README.md`, and `.gitignore`. [src:SIBLING-PUSH-RAG-2026-08-27]
- That branch does not exist on the `claude-ai` remote, and `claude/blind-testing-ooda-5o3s67` and `claude/go-page-ultrathink-ooda-kqxvnc` had not been pushed to either remote. [src:BRANCHES-ABSENT-2026-08-27]
- The two pushed branches on `claude` share no ancestry: `git merge-base` exits 1, and each branch head is its own root commit. Their file listings overlap on `.gitignore` and `README.md`. [src:UNRELATED-HISTORIES-2026-08-27]
- The sessions run in separate containers and could not message each other as local peers. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]
- No tool for reading another session's transcript was available, so cross-session knowledge is limited to metadata and to whatever gets pushed. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]
- The file listing of the sibling branch was read; its code was not reviewed, so nothing here describes what that code does. [src:SIBLING-PUSH-RAG-2026-08-27]

## The merge hazard

Because both repositories started empty, each session's first commit became its
own **root commit**. The branches are therefore unrelated histories, not
divergent ones. [src:UNRELATED-HISTORIES-2026-08-27]

Three consequences, all of which bite at merge time rather than now:

- `git merge` refuses outright. Combining any two branches needs
  `--allow-unrelated-histories`, which turns every commonly-named file into a
  conflict rather than a three-way merge.
- The overlap is already real: `.gitignore` and `README.md` exist on both
  pushed branches with no common ancestor. [src:UNRELATED-HISTORIES-2026-08-27]
- Each further session that pushes a first commit adds another root, so the
  cost grows with the size of the fleet.

**Convention going forward.** The first branch merged to `main` establishes the
shared root. Every later branch rebases onto that root before merging, rather
than being merged with `--allow-unrelated-histories`. Whoever merges first
should say so, since until then there is no root to rebase onto.

**This is that first merge, and this says so.** Branch
`claude/research-skill-mastery-mwjs01` merged
`claude/review-chat-archive-zrynr4` into the pipeline history with
`--allow-unrelated-histories`. Only the two predicted files conflicted,
`.gitignore` and `README.md`, and both sides were read before resolving.
[src:UNIFIED-ROOT-2026-08-27]

That branch now carries **both** histories as ancestors, so it is the root every
later branch should rebase onto. A branch that instead merges one of the two
original roots again will reintroduce the problem this paragraph exists to
close.

**Before merging anything**, diff the file lists first:

```bash
comm -12 <(git ls-tree -r --name-only origin/<theirs> | sort) \
         <(git ls-tree -r --name-only origin/<mine>   | sort)
```

Any path in that output is a file two sessions wrote independently. Read both
versions before resolving; at this concurrency, silent clobbering is the
likeliest way work disappears.

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
