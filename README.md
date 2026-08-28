# oodarag

An OODA-driven, end-to-end RAG pipeline that runs on the Python standard library alone.

```
Observe  ->  Orient   ->  Decide   ->  Act
ingest       normalize    policy       reindex / backfill
             chunk        engine       / alert / answer
             embed
             index
```

## Why this exists

Most RAG code is a demo: load a folder, call an embedding API, cosine-similarity
top-5, stuff it in a prompt. That works until it meets a real corpus, at which
point the failure modes are always the same - the index is stale, the chunks lost
their context, the retriever returns the site footer, and nobody can tell you
whether last week's change made retrieval better or worse.

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

## The nightly loop

Everything above describes a pipeline you point at a corpus. `oodarag reflect`
points the same machinery at **you**: it runs at the end of each day, reads what
you actually did, and improves your files from the evidence.

```bash
ooda reflect run                       # dry run - show me what you would change
ooda reflect run --apply               # make the safe changes
ooda reflect queue                     # what needs my call
ooda reflect accept 3f9a1c22           # yes, do that one
ooda reflect dismiss 8b2e0d41          # no, and stop suggesting it
ooda reflect revert 20260827-223000    # undo an entire night
ooda reflect schedule --kind systemd   # and do this every day at 22:30
```

### One abstraction: everything you produce is a Signal

A prompt typed into a chat, a command typed into a shell, a file on disk, a
commit in git - all normalize to the same five fields. Rules consume `Signal`s
and never learn where one came from, which is why a rule written against chat
prompts fires unchanged on terminal history, and why adding a source is one
class rather than a pass through every rule.

| Source | What it observes | Signal kinds |
|---|---|---|
| `chat:transcripts` | Chat sessions - what you *wanted* | `prompt`, `reply` |
| `shell:history` | zsh / bash / fish - what you actually *ran* | `command` |
| `workspace:files` | The file tree as it stands tonight | `file` |
| `git:log` | What changed, and when | `commit` |

### What it looks for

The rules exist because retyping a standing instruction, fighting the same
command four times, and linking to a file that was never written are the three
ways a project quietly rots.

| Rule family | Finds | Typical fix |
|---|---|---|
| `friction.*` | An instruction you have given in three separate sessions; a prompt you had to rephrase; a correction you have made twice | Write the convention down once, in your project memory file |
| `terminal.*` | A command retried with different flags until it worked; the same incantation typed on five different days | A Makefile target, so it is never re-derived |
| `docs.*` | A doc linking to a file that does not exist; Makefile targets the README never mentions; a doc older than the code it describes | Create the stub, document the entry point |
| `hygiene.*` | Credential-shaped strings in tracked files; modules with no test; ageing TODO clusters | Flag it - loudly, and without touching the file |

### Why it is safe to leave running

An unattended process that edits your files has to earn that, so the autonomy is
a property of the *edit*, not of how important the finding is:

- **`safe`** - cannot destroy information (creating a file nothing has yet, adding
  a delimited section the loop owns). The only tier applied without a human.
- **`review`** - edits your prose or config. Queued, never applied on its own.
- **`manual`** - source-code semantics, anything about secrets. Reported only.

On top of the tiers: **dry run by default**; every write is **backed up and
revertible by cycle id**; edits are **all-or-nothing per proposal** and
**idempotent**, so a second run at 22:30 changes nothing; nothing outside the
workspace root is ever written; and a run **refuses to touch a dirty working
tree**, because an autonomous edit mixed into your uncommitted work makes "who
changed this" unanswerable. Source files are never machine-edited at all.

### Why it gets better

Every verdict - applied, dismissed, reverted, failed - is appended to a journal,
and tomorrow's Decide stage folds it into a per-rule confidence. A rule whose
suggestions you keep taking gets more autonomy; one you keep declining fades;
one whose *edits* you revert is penalised harder than one whose *ideas* you
decline, because a bad edit is worse than a bad idea. Anything you dismiss is
never proposed again.

The journal is append-only and the learned behaviour is a pure fold over it, so
"what did it do on the 14th, and why" always has an answer, and deleting the
journal returns the loop to a naive but correct first night rather than to a
state nobody can explain.


## Status

Under active construction. See `internal/PLAN.md` for what is built and what is next.

## Commands

Everything runs from a checkout with no install step: `PYTHONPATH=src`, standard
library only. `make help` lists these too.

**Working on the repo**

| Command | Does |
|---|---|
| `make test` | The full suite on stdlib `unittest`. No dependencies, no plugins. |
| `make lint` | Compile-checks every module. |
| `make install` | Editable install with dev extras, if you would rather have the `ooda` entry point on your PATH. |
| `make clean` | Removes `.oodarag/`, `.data/` and caches. |

**The nightly loop** — see [The nightly loop](#the-nightly-loop) above

| Command | Does |
|---|---|
| `make reflect` | Tonight's review as a dry run. Changes nothing. |
| `make reflect-apply` | Runs the cycle and applies the `safe`-tier edits. |
| `make reflect-queue` | The proposals waiting on your accept or dismiss. |
| `make reflect-status` | What the loop has observed and learned so far. |
| `make reflect-rules` | Every rule and the confidence it has earned from your verdicts. |
| `make schedule` | Emits an end-of-day schedule. `KIND=systemd\|launchd\|cron\|github`, `AT=22:30`. |

The `ooda reflect` CLI has more than the Makefile exposes — `accept`, `dismiss`,
`revert <cycle-id>`, `report --list`. Run `ooda reflect --help`.

**Fetching a corpus**

`ooda ingest` runs one connector and writes what it returns as JSON Lines. It is
the half of the pipeline that exists: fetching and normalizing documents, with
indexing and retrieval still to come.

```bash
ooda ingest web https://example.com --max-pages 50 --max-depth 2
ooda ingest github owner/repo --ref main --exclude 'vendor/*'
```

Incremental by content hash, so a second run reports what actually changed and
appends only that. The output is a **delta stream, not a snapshot** — a
connector returns only new and changed documents, so rewriting the file each run
would delete everything that happened not to change. Pass `--fresh` to re-read
the whole source and replace the file.

**Retrieval** — declared, not yet built

`make index`, `make query`, `make eval`, `make demo` and `make loop` exit with a
message naming what is missing rather than a traceback. `internal/PLAN.md` has
the build order.

## Design principles

1. **Zero required dependencies.** The whole pipeline runs on the stdlib, so it
   works in CI, in an air-gapped container, and on a laptop. Accelerators
   (numpy) and hosted models (Voyage, Anthropic) plug in behind interfaces.
2. **Provenance is load-bearing.** Every chunk carries the URI and commit sha it
   came from. Citations are verified against retrieved chunks, not generated.
3. **Everything is bounded.** Every network stage has a budget on requests,
   bytes and time.
4. **Degrade, don't die.** Blocked egress, a missing API key or a truncated API
   response reduce what the pipeline can do; they never make it crash.
5. **Measure, don't assert.** Retrieval quality is a number in an eval report.
