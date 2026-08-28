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
bash tests/run_all.sh        # verifier + both test suites
```

## What is here

| Path | Purpose |
|---|---|
| `CLAUDE.md` | The doctrine. Read first. |
| `FLEET.md` | Which sessions run concurrently, and on which branches. |
| `provenance/` | The ledger, the observations, the unknowns, the raw captures, the loop logs. |
| `prompts/` | System prompts carrying the doctrine into a session. |
| `tools/verify_provenance.py` | The fabrication guard. |
| `tools/ingest_chat_archive.py` | Conversation-archive ingestion and search. |
| `tools/prompt_forge.py` | The prompt linter and compiler. |
| `tools/prompt_habits.py` | Scores the prompts you have already written. |
| `tools/learn_rule.py` | Appends a learned rule to the instruction file. |
| `tools/install_prompt_system.sh` | Installs the prompt system into `~/.claude`, for every terminal. |
| `tests/` | Tests for every tool here, including their failure cases. |
| `.claude/commands/` | The workflows, as slash commands. |
| `.claude/agents/` | `observer`, `fact-checker`, and `prompt-critic` subagents. |
| `.claude/` | Hooks and the OODA skill. |
| `docs/workflows.md` | How the workflows and subagents fit together. |
| `docs/prompting.md` | The prompt standard, and where each rule came from. |

## Prompts that can be checked

A prompt is a specification, and most disappointing output is a specification
failure. Three of those failures are mechanical — the artifact was never named,
the acceptance test was never stated, and nothing said what to do when the
request rests on something absent — so they are checked mechanically:

```bash
python3 tools/prompt_forge.py lint --profile task my-prompt.txt   # 0 clean, 1 findings
python3 tools/prompt_forge.py compile my-prompt.txt               # into the seven slots
bash tools/install_prompt_system.sh                               # /prompt in every terminal
```

`compile` cannot invent: every line of its output is a line you wrote, a
heading, or an explicit `<<MISSING:` marker, and the tests prove it.

One prompt at a time is the small win. The larger one is the corpus:

```bash
python3 tools/ingest_chat_archive.py ingest --include-projects
python3 tools/prompt_habits.py --worst 5
```

That scores the prompts you have actually written and names the habit that
costs most — the same rule firing on most of what you write is worth more than
polishing any single prompt. It counts what it excluded (in a Claude Code
transcript, tool results outnumber real prompts by around forty to one) so the
number it reports is about you rather than about the harness. Read
[docs/prompting.md](docs/prompting.md) for the standard and
`.claude/skills/prompt-forge/SKILL.md` for the procedure. For chats that cannot
reach this machine, paste [prompts/portable-preamble.md](prompts/portable-preamble.md).

## Searching your conversations

**Run this on your own machine.** Claude Code keeps every transcript under
`~/.claude/projects`, so that is where your history actually lives — one flag
indexes all of it:

```bash
python3 tools/ingest_chat_archive.py ingest --include-projects
python3 tools/ingest_chat_archive.py search "retrieval pipeline"
python3 tools/ingest_chat_archive.py stats
```

On the container this was built in, that directory held only this session, so
what you get here is small and what you get on your own machine is not.

Your **claude.ai** threads are separate and are not on disk anywhere. Export
them (Settings → Privacy → Export data), unzip `conversations.json` into
`archive/`, and run `ingest` again — that reader is written to the documented
export shape but has only been exercised against fixtures, so check the skip
count on the first real run.

Messages are stored verbatim and every hit carries its conversation id,
message id, timestamp, and source file, so a result can be quoted as evidence.
Records that cannot be parsed are skipped and counted, never repaired by
guesswork. `archive/` is git-ignored — the exports are the owner's data, not
repository content.

## Status

The tooling runs and is tested. The provenance ledger holds what was actually
established on 2026-08-27. The chat index holds nothing yet, and says so
rather than pretending otherwise.
