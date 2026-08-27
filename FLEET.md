---
provenance: enforced
---

# Fleet

Several Claude sessions run against these repositories concurrently. This file
is the roster and the rules that keep them from overwriting each other.

> Snapshot taken at 2026-08-27T15:11Z, not a live view. The roster grew from
> 4 to 14 in 44 minutes; re-run `mcp__Claude_Code_Remote__list_sessions` before
> trusting any of it.
>
> Every title, summary and goal below was written by the session it describes.
> They are that session's claims about itself, second-hand throughout.

## Roster

| Session | Title | Branch | Status |
|---|---|---|---|
| `…FXG7QR` | Untitled session | `claude/great-euler-6tx6y6` | RUNNING |
| `…Vp6Nnb` | Untitled session | `claude/session-y42cyg` | RUNNING |
| `…FKYZVu` | **Personal skills and repos research** (this session) | `claude/personal-skills-repos-research-dxmflq` | RUNNING |
| `…Rj2vRw` | Comprehensive research and skill mastery | `claude/research-skill-mastery-mwjs01` | RUNNING |
| `…KaEREc` | Goal prompt task division | `claude/goal-prompt-task-division-0ghozd` | IDLE |
| `…DuBJPh` | Ultrareview with data checkers | `claude/ultrareview-data-checkers-98ad9p` | RUNNING |
| `…QLk8iR` | Claude code to Playground parity | `claude/code-playground-parity-xw0snj` | RUNNING |
| `…GPgcWe` | AI system research and implementation | `claude/ai-system-research-3jpwda` | RUNNING |
| `…FQvAGn` | Reverse engineer chat history and system setup | `claude/reverse-engineer-chat-setup-husv9h` | RUNNING |
| `…Y16zSa` | Daily file improvement system | `claude/daily-file-improvement-wgiluc` | RUNNING |
| `…Ya1zvv` | Claude chat archive review | `claude/review-chat-archive-zrynr4` | RUNNING |
| `…9vCLpJ` | RAG system and data pipeline | `claude/rag-system-data-pipeline-rdkde9` | RUNNING |
| `…6cRrEm` | Blind testing and OODA analysis | `claude/blind-testing-ooda-5o3s67` | RUNNING |
| `…WhTTEx` | Go page review and ultrathink OODA | `claude/go-page-ultrathink-ooda-kqxvnc` | RUNNING |

Full ids and goal strings: `provenance/raw/sessions-2026-08-27T15-11Z.json`.

## Duplicated mandates

Three sessions besides this one were given effectively the same instruction —
find skills and repositories, install them, route to them.
[src:FLEET-OVERLAP-2026-08-27] They are not coordinated, they cannot read each
other, and each will independently search, choose and install.

One case is already concrete rather than theoretical: `…Rj2vRw` reports it is
"probing YouTube Data API", which is the probe this session ran between 15:02Z
and 15:10Z. [src:FLEET-OVERLAP-2026-08-27]

> Framing, not a claim: the practical consequence is that `.claude/skills/`
> is about to be written by four sessions with four different opinions, on
> four branches that share no ancestry.

What to do about it, in order of cost:

1. **Read `SKILLS.md` before installing anything.** It records what was already
   examined and turned down, so a rejected candidate is not silently
   re-adopted from its name.
2. **Push early.** A branch nobody can see is a branch everybody duplicates.
3. **Prefer additive layout.** One directory per skill under
   `.claude/skills/`, so two sessions adding different skills merge cleanly
   and only a genuine collision conflicts.
4. **Do not re-measure what is already in the ledger.** Egress is captured in
   `provenance/raw/egress-2026-08-27T15-10Z.json` and reproducible with
   `tools/probe_egress.py`.

## Observed — fleet state


- The fleet numbered 14 sessions at 15:11Z, not the 4 seen at 14:27Z; ten were created between 14:49Z and 15:01Z. [src:SESSIONS-2026-08-27T15-11]
- All 14 run `claude-opus-5` at effort `xhigh` in `permission_mode: auto` on one environment, and all carry `flag_settings.ultracode: true`. [src:SESSIONS-2026-08-27T15-11]
- Thirteen were RUNNING and one, "Goal prompt task division", was IDLE having reported its goal met. [src:SESSIONS-2026-08-27T15-11]
- Three sessions besides this one carry a find-install-route mandate for skills and repositories, and one of them reports probing the YouTube Data API concurrently with this session. [src:FLEET-OVERLAP-2026-08-27]

### Earlier capture — 2026-08-27T14:27Z
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
