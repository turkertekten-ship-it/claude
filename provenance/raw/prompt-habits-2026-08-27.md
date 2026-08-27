# prompt_habits run — 2026-08-27

Index built from this container's own transcripts, not the owner's history:

```
conversations: 11
messages:      966
date range:    2026-08-27T15:00:18.224Z .. 2026-08-27T15:36:46.923Z
  claude_code: 1 conversation(s)
  claude_code_subagent: 10 conversation(s)
run 2026-08-27T15:36:48+00:00: 966 msg, 0 skipped
```

## python3 tools/prompt_habits.py --worst 4
```
10 prompts scored — mean 91.4, median 95.0
of 433 user turns: 421 were tool results, 2 harness text or too short, 0 repeats
grades: A 7  B 2  C 0  D 1  F 0

habits, most expensive first (share of your prompts affected)
   30%  VAGUE_QUALITY   warn   3 prompt(s)
   10%  CONTRADICTION   error  1 prompt(s)
   60%  NO_ACCEPTANCE   info   6 prompt(s)
   50%  NO_CONTEXT      info   5 prompt(s)
   40%  NO_EXAMPLE      info   4 prompt(s)
   40%  WALL            info   4 prompt(s)
   10%  HEDGE           warn   1 prompt(s)
   10%  UNBOUNDED       warn   1 prompt(s)
   10%  VAGUE_QUANT     warn   1 prompt(s)

the one to fix: VAGUE_QUALITY — it is in 30% of what you write.
  Say what changes: fewer than 3 dependencies, passes ruff, reads at grade 9, fits one screen.

lowest scoring 4:
   62/100  2026-08-27T15:28  You are writing a provenance-grade research dossier. Inputs below are raw agent findings (
   88/100  2026-08-27T15:02  Establish who Nick Saraev actually is, from primary sources. Search and fetch: nicksaraev.
   88/100  2026-08-27T15:11  Find Nick Saraev's operating principles and mental models for building AI/automation syste
   94/100  2026-08-27T15:07  Determine whether Nick Saraev teaches, uses, or published anything called "CLEAR" (as a pr
```

The corpus is this session's own traffic — its subagent briefs and the owner's
one goal message — so the habit ranking describes this session, not the owner.
