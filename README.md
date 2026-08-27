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
python3 -m workbench run    suites/doctrine-adherence.yaml   # grade it
python3 -m workbench blind  suites/doctrine-adherence.yaml   # blind pairwise A/B
python3 -m workbench report .workbench/<run-id> # markdown + JSON report

python3 tools/parity_check.py                   # execute the parity matrix
```

`parity_check.py` is the part worth pointing at. `docs/parity.md` is a table of
claims, and a table is not evidence — so this exercises each capability against
the live backend and reports PASS, FAIL, or UNREACHABLE with the reason. It
currently records **20 passed, 0 failed, 5 unreachable**.

Its most useful result so far was a wrong one it later caught. For several
commits it recorded `CLAUDE_CODE_MAX_OUTPUT_TOKENS` as a broken platform
capability, and this README repeated that. The variable works. It enforces the
ceiling by **refusing** — `API Error: Claude's response exceeded the N output
token maximum` — rather than by truncating, and the check was waiting for a
truncation that never comes. The tokens that looked like a breach were thinking
tokens spent before the refusal fired, and the "output" being graded was the
error message. A harness that can be wrong about the platform can also be
caught being wrong; a written table cannot.

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
in `prompts/` actually stop a model inventing things? Sixty fabrication traps,
two arms, judged blind in both presentation orders, 50 decided pairs against
the ~47 that 80% power needs. The answer has two halves and both are honest:

- **Nothing separates them on refusing to invent.** Both variants passed 60 of
  60 on the deterministic fabrication guard, with zero discordant pairs. On
  these traps a plain assistant declines as reliably as the operating prompt.
- **Something separates them on how useful the refusal is.** The blind judge
  preferred the doctrine prompt 42–8 with 10 ties, p < 0.001 — and that
  preference survives the length control. It wrote the longer answers overall
  (768 characters against 585), but on the eleven pairs where the *plain
  assistant* was the longer one, and length bias therefore pushed the other
  way, the doctrine prompt still won 9–1, p = 0.021. Both strata significant,
  same direction. The judge was reading content, not word count.

Note what that does and does not license. On the thing the operating prompt was
written for — refusing to fabricate — the measured difference is **zero**. What
it buys is a more useful refusal, and only that.

Getting there cost two of this repository's own bugs, both kept on the record:
36 cached completions written by an **offline echo backend and served to a live
run as real model output**, and a keyword grader that made the plain assistant
win at p = 0.039 by **scoring vocabulary as honesty**. Reports:
[`blind-run-3-powered`](provenance/raw/blind-run-3-powered-2026-08-27.md), and
the two earlier, worse runs are kept beside it.
