---
description: Score the prompts you have already written, from the chat index, and name the one habit that costs you most.
argument-hint: [optional --since ISO8601, or --profile]
allowed-tools: Bash, Read
---

Audit the owner's own prompt history: **$ARGUMENTS**

1. Make sure there is a corpus. `python3 tools/ingest_chat_archive.py stats`.
   If it is empty, run
   `python3 tools/ingest_chat_archive.py ingest --include-projects` first — and
   if there is still nothing, say exactly that and stop. An empty history is a
   finding; inventing a representative sample would be the worst thing you
   could do here, because everything downstream would read it as the owner's
   real writing.
2. `python3 tools/prompt_habits.py --worst 5 $ARGUMENTS`
3. Read the exclusion line before the numbers. Tool results outnumber real
   prompts in a Claude Code transcript by roughly forty to one, so a report
   that scored them would describe the harness wearing the owner's name. If the
   scored count looks implausibly high, that filter has failed and the report
   is wrong — say so rather than presenting it.
4. Report: the corpus size and what was excluded, the three most expensive
   habits with the share of prompts each affects, and one concrete rewrite of
   the single lowest scorer — their words, restructured, nothing invented.
5. Recommend exactly one habit to change. Not five. A list of five is a list
   nobody acts on.

The scores are only as meaningful as the corpus. On a fresh container the index
holds that session's own traffic, not the owner's history — the real history is
under `~/.claude/projects` on their own machine, and claude.ai threads need an
export. Say which of those you actually measured.
