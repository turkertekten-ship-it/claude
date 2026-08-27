---
description: Ingest conversation exports in archive/ into the searchable index and report what actually landed.
argument-hint: [optional search query to run after ingesting]
allowed-tools: Bash, Read
---

Ingest the chat archive, then report honestly on it.

```bash
python3 tools/ingest_chat_archive.py ingest --include-projects
python3 tools/ingest_chat_archive.py stats
```

`--include-projects` reads `~/.claude/projects`, where Claude Code keeps its
transcripts. On the owner's own machine that is the whole Claude Code history;
in a fresh container it is only the current session. Say which case you are in
rather than reporting the count as if it were the whole archive.

If a query was given (**$ARGUMENTS**), also run:

```bash
python3 tools/ingest_chat_archive.py search "$ARGUMENTS"
```

Then report, using only numbers the tool actually printed:

- conversations, messages, and the real date range
- how many records were skipped and why — name them; they were not repaired
- whether the archive was empty

**If the archive is empty, that is the finding.** Say so and stop. Do not
generate sample conversations, do not describe what the chats "probably"
contain, and do not summarise from session titles. An empty index is the
correct output for absent input; anything else poisons every downstream claim
because it will be read as real history.

When quoting a result, carry its message id and source file with it.
