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
bash tests/run_all.sh        # verifier + every test suite
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
| `workbench/` | The prompt workbench: variants, sweeps, graders, blind A/B. |
| `docs/parity.md` | Console Workbench → Claude Code parity matrix, sourced. |
| `src/oodarag/` | An OODA-driven RAG pipeline on the standard library alone. |
| `tests/` | Tests for all of the above, including their failure cases. |
| `.claude/` | Hooks, skills, slash commands, subagent definitions. |

## The workbench

`workbench/` closes the gap between a terminal coding agent and the Console
Workbench: prompt variants with `{{variables}}`, parameter sweeps, a grader
stack that tries deterministic checks before it asks a model anything, and
**blind outcome-based A/B testing** — candidates are stripped of identity and
shown to a judge in both orders, and a win only counts when both orders agree.

```bash
python3 -m workbench doctor                     # what this environment can do
python3 -m workbench run    suites/example.yaml # run a suite, grade it
python3 -m workbench blind  suites/example.yaml # blind pairwise A/B
python3 -m workbench report .workbench/<run-id> # markdown + JSON report
```

It runs on whatever backend the environment actually has, and says which one
it picked. See [docs/workbench.md](docs/workbench.md).

## Searching your conversations

The archive ships empty, because no conversation export existed when this was
built. To populate it:

```bash
# claude.ai: Settings -> Privacy -> Export data, unzip into archive/
# Claude Code: cp ~/.claude/projects/**/*.jsonl archive/

python3 tools/ingest_chat_archive.py ingest
python3 tools/ingest_chat_archive.py search "retrieval pipeline"
python3 tools/ingest_chat_archive.py stats
```

Messages are stored verbatim and every hit carries its conversation id,
message id, timestamp, and source file, so a result can be quoted as evidence.
Records that cannot be parsed are skipped and counted, never repaired by
guesswork. `archive/` is git-ignored — the exports are the owner's data, not
repository content.

## oodarag

`src/oodarag/` is a zero-dependency ingest and scraping core (HTTP client with
retry and rate limiting, robots-aware crawler, boilerplate-stripping HTML
extraction, GitHub connector). It arrived on a sibling session's branch and is
carried here unchanged; its own design notes are in its module docstrings.

## Status

The tooling runs and is tested. The provenance ledger holds what was actually
established on 2026-08-27. The chat index holds nothing yet, and says so
rather than pretending otherwise.

The workbench has been run against a real question — does the operating prompt
in `prompts/` actually stop a model inventing things? — and the honest answer
is **not shown**. Three variants passed the deterministic layer identically;
the blind comparison favoured the doctrine prompt directionally but at
p = 0.375 over ten decided pairs, with the winning variant also writing the
longest answers. The full report is in
[`provenance/raw/blind-run-2-recalibrated-2026-08-27.md`](provenance/raw/blind-run-2-recalibrated-2026-08-27.md),
and the run that came before it — the one where a miscalibrated grader failed
every variant including the correct answers — is kept beside it.
