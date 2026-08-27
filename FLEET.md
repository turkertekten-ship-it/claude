---
provenance: enforced
---

# Fleet

Several Claude sessions run against these repositories concurrently. This file
is the roster and the rules that keep them from overwriting each other.

> This is a snapshot taken at 2026-08-27T14:27Z, not a live view. Re-run
> `mcp__Claude_Code_Remote__list_sessions` before trusting it.
>
> It is also **known stale**: a re-fetch at 16:10Z found 13 branches on
> `claude` and 7 on `claude-ai`, against the 4 sessions listed below.
> [src:FLEET-SYNC-2026-08-27] The roster below is kept as the original capture
> rather than edited, so the gap between it and the branch list stays visible.
> The branches are the authoritative list; the session table is not.

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

## Observed — the fleet at 16:10Z

- `claude` carries 13 branches and `claude-ai` carries 7, against a roster of 4 sessions. Ten sibling branches hold between 25 and 118 files each. [src:FLEET-SYNC-2026-08-27]
- `claude/personal-skills-repos-research-dxmflq` vendored four skills into `.claude/skills/` — `chunking-advisor`, `doc-coauthoring`, `mcp-builder` and `rag-audit` — and wrote a `SKILLS.md` routing table. [src:FLEET-SYNC-2026-08-27]
- That branch also contains an audit of `src/oodarag/`, run before the retrieval spine existed, whose blocking findings were a console script with no `cli.py`, a README presenting planned work as delivered, four Makefile targets that could not succeed, and a chunking contract with no implementation. [src:SIBLING-AUDIT-2026-08-27]
- All twelve sibling branches were searched for the strings behind U-3 and U-4; neither "the book" nor "imb" appears in any Markdown, text or YAML file on any of them. [src:FLEET-SYNC-2026-08-27]

## Observed — the same pipeline built twice

- `claude/rag-system-data-pipeline-rdkde9`, the branch this session's code descends from, has independently completed the same pipeline: chunking, embedding, storage, retrieval, generation, evaluation and an OODA loop, plus a YouTube connector, an egress prober and a contamination check. [src:PIPELINE-DIVERGENCE-2026-08-27]
- The two implementations do not share a module layout. Where this branch has `retrieve.py`, `evaluate.py` and `net/reachability.py`, that branch has `retrieve/fusion.py`, `eval/metrics.py` and `access/probe.py`; twenty-six files exist on both branches with divergent content, including `cli.py`, `pipeline.py`, `models.py`, `README.md` and `docs/adr/0001-zero-dependency-core.md`. [src:PIPELINE-DIVERGENCE-2026-08-27]
- Both branches independently found and fixed the same defect in the standard library's robots.txt parser, and both independently built contamination detection for their eval harness. [src:PIPELINE-DIVERGENCE-2026-08-27]

## Duplication is a separate failure from clobbering

> This section is a reading of the observations above, not a finding. It is
> kept out of an `## Observed` heading for that reason.

The rules in this file — one branch per session, push early, read before you
build on it — are aimed at *clobbering*: two sessions overwriting one file.
They worked. Nothing was overwritten.

What happened instead was *duplication*, which those rules do not address at
all. Two sessions each spent a session building the same seven stages, neither
aware of the other, and both were following the convention correctly the whole
time.

The gap is timing rather than rules. "Read before you build on it" is
satisfied by one sync at the start of a session — and at that moment the
sibling branch either does not exist or holds nothing worth reading. The
branches that would have changed the plan appear *during* the work. A fleet
sync at each phase boundary, rather than once at the beginning, would have
surfaced this after the first stage instead of after the seventh.

**Suggested convention, not yet agreed by anyone else:** re-run `/fleet-sync`
when a phase completes, not only when a session starts. It costs one fetch and
a file listing.

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

**Two sessions performed that merge independently, and neither knew.** Branch
`claude/research-skill-mastery-mwjs01` merged
`claude/review-chat-archive-zrynr4` into the pipeline history with
`--allow-unrelated-histories`; only the two predicted files conflicted, and
both sides were read before resolving. [src:UNIFIED-ROOT-2026-08-27] Branch
`claude/personal-skills-repos-research-dxmflq` carries a commit titled "Unify
the fleet's two unrelated roots on this session's branch" doing the same thing.
[src:FLEET-SYNC-2026-08-27]

So "whoever merges first should say so" did not work as a coordination rule: by
the time either session could have said it, both had already acted. **The
convention needs a claim made before the merge, not after it.** Until one of
these branches lands on a default branch, there are now two candidate roots and
a later branch can still pick the wrong one.

Whichever is adopted, the branch that adopts it carries **both** original
histories as ancestors, and every later branch should rebase onto that rather
than merging an original root again.

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
