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

## Observed — the Boris Cherny corpus

- The material requested as "borris churney" was identified as Boris Cherny (`@bcherny`), creator and head of Claude Code at Anthropic; the identification is an inference and is registered as open in [unknowns.md](unknowns.md) U-7. [src:CHERNY-IDENTITY-2026-08-27]
- Most sources about him were unreachable from this container: `x.com`, `anthropic.com`, `ycombinator.com`, `substack.com`, `medium.com` and the tip-compilation sites all failed at the egress proxy. Only `code.claude.com`, `docs.claude.com`, `raw.githubusercontent.com` and `api.github.com` answered. [src:EGRESS-BLOCKED-2026-08-27]
- One primary source was reached and read in full: an unpublished draft dated 2025-04-13 in Cherny's own blog repository, `bcherny/bcherny.github.io`, in which he writes "I created Claude Code as a research project". [src:CHERNY-OWN-DRAFT-2025-04-13]
- That draft is unfinished — eight subsections, including all five under its "Multi-Claude" heading, are headings with no body. Nothing was inferred from them. [src:CHERNY-OWN-DRAFT-2025-04-13]
- A third-party GitHub compilation supplied 60 further tips across seven dated collections from 2026-01-03 to 2026-04-16, transcribed from his X threads. It is secondary, and its fidelity is established for exactly one tip. [src:CHERNY-TIPS-REPO-2026-08-27]
- That one fidelity check, against a screenshot of the original post bundled in the compilation, found the transcription faithful in substance but abridged: it dropped two of the post's three paragraphs. [src:CHERNY-TWEET13-SCREENSHOT-2026-08-27]
- His advice on permissions reverses across the corpus: the 2025 draft recommends `--dangerously-skip-permissions` as "safe yolo mode", the 2026-01-03 tips say not to use it, and the 2026-04-16 tips describe a classifier-backed auto mode as the safer replacement. [src:CHERNY-PERMISSIONS-REVERSAL-2026-08-27]
- Two search summaries disagreed about whether he runs parallel work in separate checkouts or in git worktrees; the compilation resolves it as both — checkouts personally, worktrees for most of his team. [src:CHERNY-SEARCH-SETUP-2026-08-27] [src:CHERNY-TIPS-REPO-2026-08-27]
- The corpus's central claim — give Claude a runnable way to verify its work — is independently stated by Anthropic's own best-practices documentation, which this session fetched directly rather than through the compilation. [src:DOCS-BESTPRACTICES-2026-08-27]
- The deterministic-gate form of that practice already existed in this repository before the corpus was collected: a `PostToolUse` hook runs the provenance verifier on every write, and a `Stop` hook runs the full suite. [src:REPO-STATE-VERIFY-HOOKS-2026-08-27]

## Observed — inherited state of the code on this branch

- `oodarag.cli` does not exist, so the `demo`, `index`, `query`, `eval` and `loop` targets advertised in the Makefile all fail; `internal/PLAN.md`, referenced by `README.md`, is also absent. This session did not repair it and changed nothing under `src/`. [src:OODARAG-NO-CLI-2026-08-27]

## Observed — what auditing this work found

- Two subagents audited this session's own output; between them they found a miscount, a misattributed term, an arithmetic error, a gloss contradicted by the corpus's own sources, two second-hand claims written as fact, and four quotations the ledger could not check. Each was re-derived here before being acted on, and all held. [src:AUDIT-SUBAGENTS-2026-08-27]
- The test suite could not see any of the installed layer: deleting three files named in `CLAUDE.md` and replacing a skill with invalid YAML still produced "ALL CHECKS PASSED" and exit 0. [src:AUDIT-SUBAGENTS-2026-08-27]
- `make test` passed vacuously, running unittest discovery over test scripts that define no `TestCase` subclass. [src:AUDIT-SUBAGENTS-2026-08-27]
- The fabrication guard crashed rather than reporting when a violation lay outside the repository root, so it failed at the moment it found something. [src:AUDIT-SUBAGENTS-2026-08-27]
- The document auditor separately confirmed clean what it was asked to attack hardest: the 60-tip count, every PR statistic, both screenshot quotations, and the absence of any invented content under the draft's empty headings. [src:AUDIT-SUBAGENTS-2026-08-27]

## Observed — the tip compilation, fully audited

- All 60 tips were compared against the 65 bundled screenshots of the original posts. Roughly 35 transcribe faithfully; the rest fail in both directions. [src:SCREENSHOT-AUDIT-2026-08-27]
- The compilation invents. Four bullets in the 2026-03-30 collection appear in no post while reading as Cherny's words, and the entire squash-merge rationale in the 2026-03-25 file is the compiler's commentary on a four-word statement. [src:SCREENSHOT-AUDIT-2026-08-27]
- It reassigns attribution: "our version of @danshipper's Compounding Engineering" became "Boris's version", "We call this test time compute" became "Boris calls this", and first-person-plural was repeatedly rewritten as third-person about "the team". [src:SCREENSHOT-AUDIT-2026-08-27]
- It mis-transcribes: the shell aliases `za, zb, zc` were rendered `2a, 2b, 2c`, and the handle `@amorriscode` as `@amorisscode`. [src:SCREENSHOT-AUDIT-2026-08-27]
- Every numeric claim survived the audit exactly, including all eight PR statistics and the "200% this year" figure. [src:SCREENSHOT-AUDIT-2026-08-27]
- The claim that his advice on `--dangerously-skip-permissions` reversed between 2025 and 2026 was **wrong and is retracted**. Tips 10 and 12 of the same January 2026 thread state the conditional practice in full: not as a default, yes inside a sandbox for long-running work — which is what the 2025 draft also says. [src:CHERNY-PERMISSIONS-CONDITIONAL-2026-08-27]
- The error arose because two apparently independent citations both resolved to the same lossy compilation. [src:SCREENSHOT-AUDIT-2026-08-27]

## Observed — material recovered past the egress block

- The 2026-05-24 post recorded as unreachable was recovered from a mirrored X digest on GitHub: he states "These days my #1 tip is: use auto mode", framing it as "the key building block for multi-clauding". [src:CHERNY-X-2026-05-24]
- An independent transcription of the 2026-01-02 thread, carrying all 23 posts with per-post timestamps, was recovered the same way and preserves text the compilation drops. [src:CHERNY-THREAD-MIRROR-2026-01-02]
- Both recoveries came through `raw.githubusercontent.com`, which is reachable while every host actually serving the posts is not. Third-party mirrors on GitHub are the only route to this material from this container. [src:CHERNY-X-2026-05-24] [src:CHERNY-THREAD-MIRROR-2026-01-02]
