---
description: Audit the prompts in this repository (or a path you name) against the seven-slot standard, and report what to fix.
argument-hint: [path — defaults to prompts/ and .claude/]
allowed-tools: Bash, Read, Grep, Glob, Agent
---

Audit the prompts at: **$ARGUMENTS** (default: `prompts/`, `.claude/commands/`,
`.claude/agents/`, `.claude/skills/`)

1. Score first, so the worst offender is chosen by number rather than by
   impression. Match the profile to what the file is: `--profile system`
   for `prompts/*.md`, `--profile task` for `.claude/commands/*.md`, which
   instruct a session rather than establishing a persona.
   `python3 tools/prompt_forge.py score --profile system prompts/*.md`
2. For each file below a B, run
   `python3 tools/prompt_forge.py lint --profile system <file>` and read the
   findings against the file itself.
3. Judge each finding before acting on it. A linter rule is a heuristic: a
   finding that is wrong about *this* file is a bug in the rule, and the fix
   belongs in `tools/prompt_forge.py` with a test case, not in a special case
   that quietly exempts the file. State which findings you are rejecting and
   why.
4. Propose the smallest edit per real finding. Prompts in this repository are
   deliberately short — a prompt nobody reads to the end enforces nothing — so
   an edit that adds a section must earn it.
5. Re-run `bash tests/run_all.sh` before you report. The audit is accepted
   only when that suite passes and every file you edited scores higher than
   it did, measured rather than assumed.
6. If the path holds no prompts, or holds files that are documentation
   rather than prompts, say exactly that and stop. Scoring a README against
   a prompt standard produces a number that means nothing.

Report: a table of file, score before, score after, and the findings you
rejected as wrong. Do not report a score improvement you did not re-measure.
