---
provenance: enforced
---

# Observations — 2026-08-27

What was actually looked at, and what was actually found. Every line in an
`## Observed` section carries a source tag. Anything that could not be
verified lives in [unknowns.md](unknowns.md), not here.

## Observed — prior Claude sessions

- The account has exactly four sessions, all created on 2026-08-27 between 14:07Z and 14:26Z, all still RUNNING at capture time. [src:SESSIONS-2026-08-27]
- All four run `claude-opus-5` in `permission_mode: auto` on environment `env_01GEni7AgBA7NiyMBecyt7K1`, and all originate from `web_claude_ai`. [src:SESSIONS-2026-08-27]
- Three of the four (`RAG system and data pipeline`, `Blind testing and OODA analysis`, `Go page review and ultrathink OODA`) run at `effort_level: xhigh`; this session runs at `high`. [src:SESSIONS-2026-08-27]
- Each session writes to its own outcome branch, and three of the four take both repositories as sources; `Go page review and ultrathink OODA` takes only `turkertekten-ship-it/claude`. [src:SESSIONS-2026-08-27]
- A goal string is recorded for only two of the four sessions; it is null for two of the three siblings. [src:GOAL-COVERAGE-2026-08-27]
- Only session metadata was retrievable. Message bodies were not returned by the listing, and this session was given no tool that reads another session's transcript. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]
- A direct search for such a tool confirms none exists here, rather than merely not appearing in a listing. [src:NO-TRANSCRIPT-TOOL-CONFIRMED-2026-08-27]
- The sibling sessions run in separate containers and were not reachable as local peers. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]

## Observed — what the sessions report about themselves

> Framing, not a claim: these are each session's own one-line summary,
> recorded verbatim. They are that session's claims about its work, not
> findings this session reproduced.

- `RAG system and data pipeline` reports: "youtube blocked by proxy; confirmed FTS5/pip/API; building data model". [src:PROXY-YOUTUBE-BLOCKED]
- `Blind testing and OODA analysis` reports: "building M&A installation guide per book §2–§7; currently verifying §7 provenance". [src:SESSIONS-2026-08-27]
- `Go page review and ultrathink OODA` reports: "installing G stack + token libs; docling building; encoding book corrections". [src:SESSIONS-2026-08-27]

## Observed — repository state

- At 14:27Z both `turkertekten-ship-it/claude` and `turkertekten-ship-it/claude-ai` were empty: `git ls-remote` returned zero refs, and neither local clone had a commit. [src:REPO-EMPTY-2026-08-27]
- No session had pushed anything at that time, so no sibling work was available to read from the repositories. [src:REPO-EMPTY-2026-08-27]
- By 15:00Z that had changed: one sibling branch, `claude/rag-system-data-pipeline-rdkde9`, was on the `claude` remote at commit `1d7ce8f`, pushed 14:34:34Z with 20 files. [src:SIBLING-PUSH-RAG-2026-08-27]
- The other two sibling branches had still not been pushed to either remote. [src:BRANCHES-ABSENT-2026-08-27]
- The two pushed branches share no ancestry — each is its own root commit — and their file listings overlap on `.gitignore` and `README.md`. [src:UNRELATED-HISTORIES-2026-08-27]

## Observed — search for a chat archive

- No conversation archive exists on this container. The only transcript present is this session's own JSONL. [src:NO-LOCAL-ARCHIVE-2026-08-27]
- The attachment mount was empty; the user-data mount held only an empty `working` directory. [src:NO-LOCAL-ARCHIVE-2026-08-27]
- A Google Drive title search for "claude", "conversation", and "chat" returned nothing, and the 25 most recent Drive files were unrelated personal documents. [src:NO-DRIVE-ARCHIVE-2026-08-27]
- The Drive search was initiated by a turn explicitly marked as coming from a non-user source, not by the account owner; it was scoped to locating an export and stopped once none was found. [src:INJECT-DRIVE-2026-08-27]

## Observed — environment

- Python 3.11.15, Node v22.22.2, and jq 1.7 are available; the `sqlite3` command-line binary is not installed. [src:ENV-TOOLING-2026-08-27]

## Observed — chat transcripts actually indexed

- Three Claude Code transcripts exist on this container: this session's, and two subagent transcripts it spawned. Indexing them yields 347 messages across 3 conversations, spanning 14:26:20.952Z to 15:01:07.358Z, searchable with verbatim attributed excerpts. [src:PROJECTS-INGEST-2026-08-27]
- A subagent transcript carries its *parent's* sessionId, so a session id alone does not identify a transcript. [src:SUBAGENT-SESSION-COLLISION-2026-08-27]
- Keying conversations on session id alone silently discarded two of the three transcripts, storing 44 messages instead of 347; keying on session and file preserves all of them. [src:PROJECTS-INGEST-2026-08-27]

## Observed — tooling built here

- `tools/ingest_chat_archive.py` was run against a copy of this session's own transcript: 127 messages across 1 conversation, spanning 14:26:20.952Z to 14:49:46.659Z, with 2 unparseable records skipped and named rather than repaired. [src:INGEST-VALIDATED-2026-08-27]
- The claude.ai export reader was exercised only against synthetic fixtures under `tests/`, never against a real export. [src:INGEST-VALIDATED-2026-08-27]
- All three hook commands in `.claude/settings.json` were executed directly and exited cleanly; they were not observed firing inside a live session. [src:HOOKS-VALIDATED-2026-08-27]

## Conclusion

The honest answer to "look through all my previous claude chats" is bounded:
three sibling sessions exist and their titles, models, branches and
self-reported summaries are known, with a goal string on record for one of the
three [src:SESSIONS-2026-08-27], but their
conversation contents were not reachable by any means available here
[src:NO-TRANSCRIPT-ACCESS-2026-08-27], and no exported archive exists on disk
[src:NO-LOCAL-ARCHIVE-2026-08-27] or in Drive [src:NO-DRIVE-ARCHIVE-2026-08-27].

One sibling has since pushed code [src:SIBLING-PUSH-RAG-2026-08-27], which
makes *that branch's output* readable — but a diff is not a transcript, and
reading it would establish what was built, never what was discussed or decided.

Everything downstream of this file is built on that record alone. The chat
contents were not reconstructed, summarised, or guessed at.

## Observed — the prompt system built here

- `tools/prompt_forge.py` scores this repository's own prompts: `base-operator.md` 94, `builder.md` 94, `researcher.md` 92, `archive-ingest.md` 90, `portable-preamble.md` 98, `prompt-smith.md` 100, all at the `system` profile. [src:PROMPT-SCORES-2026-08-27]
- Two command prompts were edited after the linter found real gaps in them, and re-measured with the same build of the linter: `fleet-sync.md` 78 to 90, `ingest-chats.md` 82 to 100. [src:PROMPT-SCORES-2026-08-27]
- `bash tests/run_all.sh` passes with the prompt suite added: the verifier, both existing suites, and `tests/test_prompt_forge.py`. [src:PROMPT-SCORES-2026-08-27]
- Turning the linter on this repository's own prompts is what surfaced its detector bugs: a role written as "You process exports", an escape clause worded "if no export is present, say exactly that and stop", a generic "demonstrate the failure" read as a false premise, a "Constraints:" heading missed by a singular-only cue, and a contradiction rule firing on two words a hundred lines apart. [src:PROMPT-SCORES-2026-08-27]

## Observed — the CLEAR and Saraev research

> Framing, not a claim: the detail, the grading of each source, and what does
> not follow from it are in [../docs/prompting.md](../docs/prompting.md). Only
> the load-bearing findings are repeated here.

- The CLEAR prompt-engineering framework — Concise, Logical, Explicit, Adaptive, Reflective — is attributed by search results to Dr. Leo Lo, and no search result indicated Nick Saraev created it. [src:WEBSEARCH-CLEAR-2026-08-27]
- That search-level absence was superseded. A cloned public repository documents a second, different CLEAR framework and attributes it to Saraev by name: Clarity, Logic, Examples, Adaptation, Results, introduced as "Saraev's framework for writing effective prompts and directives". [src:SARAEV-REPOS-2026-08-27]
- The two frameworks share an acronym and differ in three letters of five, so they are not variants of one framework. [src:SARAEV-REPOS-2026-08-27]
- A second, independent repository reconstructs his course *AI Agents Full Course 2026* from its subtitles and documents a "prompt contract" of goal, constraints, output format and failure conditions, plus "reverse prompting", a "definition of done", a self-modifying instruction file with a growing learned-rules section, and a "context iceberg" rule. [src:SARAEV-REPOS-2026-08-27]
- Both repositories were reachable by `git clone` through the session's git proxy at a time when the egress gateway refused every website tried, including his own. [src:SARAEV-REPOS-2026-08-27] [src:EGRESS-BLOCKED-2026-08-27]
- Three third-party repositories, read first-hand, document a DOE framework (Directive, Orchestration, Execution) and two attribute it to Nick Saraev by name; its directive layer specifies "goal, inputs, process steps, tools, edge cases, success criteria, and guardrails". [src:DOE-FETCHES-2026-08-27]
- Nothing written by Saraev himself was read: the egress gateway refused every host except `raw.githubusercontent.com` and the search API. [src:EGRESS-BLOCKED-2026-08-27]
- The 200-call web-search budget was exhausted by the research workflow, ending verification for this session. [src:WEBSEARCH-BUDGET-2026-08-27]
- The research workflow's own findings are recorded verbatim and marked second-hand; one of its agents demonstrated the search summariser attributing other authors' work to Saraev, which is why none of its claims were promoted. [src:SARAEV-WORKFLOW-2026-08-27]

## Observed — the prompt corpus on this container

- Indexing this container's transcripts yields 966 messages across 11 conversations; of 433 user-role turns, 421 are tool results rather than typed prompts. [src:PROMPT-HABITS-RUN-2026-08-27]
- After excluding tool results, harness text and repeats, 10 prompts remained to score, and they are this session's own subagent briefs plus the owner's single goal message — not a sample of the owner's writing. [src:PROMPT-HABITS-RUN-2026-08-27]
- The ratio matters for the tool's design: an auditor that did not filter on `block_types` would have reported 369 "prompts" and described the harness under the owner's name. [src:PROMPT-HABITS-RUN-2026-08-27]

## Observed — whether the standard earns its cost

- A blind-judged A/B trial over four tasks found forged prompts meeting 19 of 20 fixed criteria against the raw asks' 13. [src:FORGE-AB-TRIAL-2026-08-27]
- The forged arm won three tasks and tied one, and on the tied task the raw ask scored full marks, so the forging bought nothing there. [src:FORGE-AB-TRIAL-2026-08-27]
- Stating a constraint did not guarantee it was met: the forged summary exceeded the 80-word limit it was given, at 86 words. [src:FORGE-AB-TRIAL-2026-08-27]
- The trial's tasks and both arms were written by the same session that ran it, so the design favours the forged arm; this is recorded with the result rather than corrected for. [src:FORGE-AB-TRIAL-2026-08-27]

## Observed — checking answers, not just prompts

- Run against the A/B trial's stored answers, `tools/check_output.py` reports the winning arm's 86 words against its prompt's written 80-word limit, and the losing arm's five paragraphs, ninety words and bold label. [src:CHECK-OUTPUT-TRIAL-2026-08-27]
- It reproduces mechanically what the model judge found by reading, and additionally flags the bold label the judge folded into a prose note. [src:CHECK-OUTPUT-TRIAL-2026-08-27]
- Of the six constraints that prompt states, five are countable and one is not; the uncountable one is listed rather than passed over. [src:CHECK-OUTPUT-TRIAL-2026-08-27]

## Observed — what a good prompt's constraints are actually made of

- The exemplar prompt in `.claude/skills/prompt-forge/SKILL.md`, documented at 100/100, has zero countable constraints; two of its seven name a command and are runnable, and five are prose for a reader to judge. [src:CONSTRAINT-GRADES-2026-08-27]
- `tests/fixtures/prompts/clean_task.md` has one countable constraint, one runnable, and eight for a reader. [src:CONSTRAINT-GRADES-2026-08-27]
- The first version of `check_output.py` reported the runnable constraints identically to unverifiable prose, which would have steered authors away from naming a command — the strongest form of acceptance test available. [src:CONSTRAINT-GRADES-2026-08-27]

## Observed — what the self-annealing section costs

- Four learned rules were appended in one session; they are 121 words, 6% of `CLAUDE.md`. [src:RULES-BUDGET-2026-08-27]
- At the measured mean rule length, fifty rules would be about 45% of the file and two hundred about 76% — arithmetic on the measured mean, not an observed file. [src:RULES-BUDGET-2026-08-27]
- Both collisions this repository has actually produced — one contradiction, one restatement — sit at exactly 0.50 word overlap, and the four genuine rules produce no finding at that threshold. [src:RULES-BUDGET-2026-08-27]

## Observed — the paths that touch the owner's own machine

- `git check-ignore -v archive/index.db` resolves to `.gitignore:3:archive/`, so the chat index built by the documented `ingest --include-projects` command cannot be committed; `*.db` covers it a second time. [src:RULES-BUDGET-2026-08-27]
- The installer's four `~/.local/bin` shims were written with an unguarded redirect, so a file already at one of those names — `check-output` is an ordinary name for a personal script — would have been overwritten and then removed by `--uninstall`, one loop after the same defect was fixed for every other target. [src:RULES-BUDGET-2026-08-27]
