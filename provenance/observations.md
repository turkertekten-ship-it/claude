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

## Observed — the fleet at 15:04Z

- The session listing returned 13 sessions, up from 4 at 14:27Z; the fleet more than tripled in 37 minutes. [src:FLEET-13-2026-08-27]
- All 13 were `RUNNING`, all on `claude-opus-5`, `permission_mode: auto`, environment `env_01GEni7AgBA7NiyMBecyt7K1`, origin `web_claude_ai`. [src:FLEET-13-2026-08-27]
- 11 of the 13 carry a non-null goal string, up from 2 of 4 at the earlier capture. [src:GOALS-2026-08-27] [src:GOAL-COVERAGE-2026-08-27]
- At 15:04Z only two branches existed on the `claude` remote, so 11 of the 13 sessions had pushed nothing. [src:BRANCHES-2026-08-27T15-04Z]
- The remote `HEAD` pointed at `claude/rag-system-data-pipeline-rdkde9`. [src:BRANCHES-2026-08-27T15-04Z]

## Observed — the goal corpus

- The 11 goal strings are the owner's own typed input, returned verbatim by the session listing API, and are collected in `profile/GOAL-CORPUS.md`. [src:GOALS-2026-08-27]
- `ooda` and `ultrathink` (or the variant `ultrahtink`) each appear in 10 of the 11 goals. [src:GOALS-2026-08-27]
- One goal consists in full of `continue ultrathink ooda`. [src:GOALS-2026-08-27]
- Four goals scope the request to all prompts, all chats and all terminals. [src:GOALS-2026-08-27]
- Three goals ask for installed skills and repositories to be routed to and used, not merely installed. [src:GOALS-2026-08-27]
- Two goals independently prohibit fabrication, one as `never fabricate` and one as `nothing is fabricated`. [src:GOALS-2026-08-27]
- One goal asks for `outcome based blind test all`, and two sessions report blind-testing activity in their status summaries. [src:GOALS-2026-08-27] [src:FLEET-13-2026-08-27]
- One goal asks to `use workflows and sub agents`; the owner sent the same instruction directly into this session while it was running. [src:GOALS-2026-08-27] [src:USER-INSTRUCTION-WORKFLOWS-2026-08-27]
- These strings are opening lines only. They contain no follow-up turns, corrections or rejections, so they are a floor on what the owner has asked for rather than a complete record. [src:GOALS-2026-08-27]

## Observed — the sibling pipeline branch, read rather than listed

- `claude/rag-system-data-pipeline-rdkde9` holds 2,583 lines of Python across 16 modules, all of which were read in full. [src:RAG-CODE-READ-2026-08-27]
- The package declares zero runtime dependencies in `pyproject.toml`. [src:RAG-CODE-READ-2026-08-27]
- Its Makefile targets `demo`, `index`, `query`, `eval` and `loop` all invoke `oodarag.cli`, and its README references `internal/PLAN.md` and `docs/adr/0001-zero-dependency-core.md`; none of those three files existed on that branch, so those targets could not run as committed. [src:RAG-CODE-READ-2026-08-27]
- This resolves the part of U-1 that a file listing could not: what that branch contains is now established by reading it, though the session's reasoning remains unknown. [src:RAG-CODE-READ-2026-08-27]

## Observed — the merge

- The two pushed branches' file listings overlapped on exactly `.gitignore` and `README.md`, matching the prediction recorded in FLEET.md before the merge was attempted. [src:SUBSTRATE-MERGED-2026-08-27]
- `git merge --allow-unrelated-histories` reported those two paths as add/add conflicts and auto-merged the remaining 32 files with no conflict. [src:SUBSTRATE-MERGED-2026-08-27]
- Both conflicts were resolved by union and no file from either branch was dropped; the result is commit `46adea6` on `claude/reverse-engineer-chat-setup-husv9h`. [src:SUBSTRATE-MERGED-2026-08-27]

## Observed — environment

- Python 3.11.15, Node v22.22.2, and jq 1.7 are available; the `sqlite3` command-line binary is not installed. [src:ENV-TOOLING-2026-08-27]
- The container reports 4 CPUs, which caps this session's workflow fan-out at 2 concurrent subagents. [src:ENV-CONCURRENCY-2026-08-27]
- PyYAML 6.0.1 imports and Python's bundled sqlite3 (3.45.1) creates an FTS5 virtual table successfully. [src:ENV-CONCURRENCY-2026-08-27] [src:ENV-SQLITE-FTS5-2026-08-27]

## Observed — tooling built by the substrate session

- `tools/ingest_chat_archive.py` was run against a copy of that session's own transcript: 127 messages across 1 conversation, spanning 14:26:20.952Z to 14:49:46.659Z, with 2 unparseable records skipped and named rather than repaired. [src:INGEST-VALIDATED-2026-08-27]
- The claude.ai export reader was exercised only against synthetic fixtures under `tests/`, never against a real export. [src:INGEST-VALIDATED-2026-08-27]
- All three hook commands in `.claude/settings.json` were executed directly and exited cleanly; they were not observed firing inside a live session. [src:HOOKS-VALIDATED-2026-08-27]

## Observed — chat transcripts actually indexed

- Three Claude Code transcripts exist on this container: this session's, and two subagent transcripts it spawned. Indexing them yields 347 messages across 3 conversations, spanning 14:26:20.952Z to 15:01:07.358Z, searchable with verbatim attributed excerpts. [src:PROJECTS-INGEST-2026-08-27]
- A subagent transcript carries its *parent's* sessionId, so a session id alone does not identify a transcript. [src:SUBAGENT-SESSION-COLLISION-2026-08-27]
- Keying conversations on session id alone silently discarded two of the three transcripts, storing 44 messages instead of 347; keying on session and file preserves all of them. [src:PROJECTS-INGEST-2026-08-27]

## Observed — the chat archive on this branch

- The chat index now holds real data rather than shipping empty: 144 messages across 1 conversation, spanning 14:50:16.588Z to 15:13:44.637Z, with 0 records skipped. [src:ARCHIVE-INGESTED-2026-08-27]
- That one conversation is this session's own transcript. No other session's transcript exists on this container, so the index covers one of 13 sessions. [src:ARCHIVE-INGESTED-2026-08-27]
- Subagent and workflow-journal transcripts were deliberately excluded after a first pass indexed them as 9 further "conversations"; machine-to-machine traffic is not one of the owner's chats. [src:ARCHIVE-INGESTED-2026-08-27]
- Searching the populated index exposed a defect that only real data could reveal: Claude Code files tool *results* as `type: "user"` records, so command output was being indexed as the owner speaking. Two of the first three hits for "reverse engineer" were Bash output. [src:ROLE-ATTRIBUTION-BUG-2026-08-27]
- The ingester now derives the role from the content blocks and search takes a `--role` filter; after the fix, `search "ooda" --role user` returns only the owner's own goal text, and a regression case covering it passes. [src:ROLE-ATTRIBUTION-BUG-2026-08-27]

## Observed — user-scope installation

- `tools/install_user_scope.py` plans 9 writes under `~/.claude` — a managed block in CLAUDE.md plus the OODA skill, 2 agents and 5 commands — and its dry run creates nothing. [src:INSTALLER-VALIDATED-2026-08-27]
- All 18 installer test cases pass, including that hand-written owner content survives an install, survives a re-run, and survives an uninstall. [src:INSTALLER-VALIDATED-2026-08-27]
- The installer has not been run with `--apply` against this container's real `~/.claude`, so its effect on a live session is untested here; only its file handling is. [src:INSTALLER-VALIDATED-2026-08-27]
- It reaches Claude Code sessions on one machine. It does not reach claude.ai web conversations, which do not read `~/.claude/`; that half of the request needs a manual paste into a Project's custom instructions. [src:INSTALLER-VALIDATED-2026-08-27]

## Observed — the fleet moved while this branch was working

- Between 15:04Z and 15:25Z the `claude` remote went from 2 branches to 11, and `claude-ai` from 0 to 5. [src:SIBLING-MERGES-2026-08-27T1525Z]
- Both branches this one was built from had advanced in that window: the pipeline branch by one commit and the substrate branch by four. [src:SIBLING-MERGES-2026-08-27T1525Z]
- Both were merged here. The substrate merge produced 8 conflicts, every one resolved by reading both sides rather than taking a side; the pipeline merge was clean. [src:SIBLING-MERGES-2026-08-27T1525Z]
- After both merges the inherited blind-test suites pass in this tree: 72 tests, OK, 1 skipped. [src:SIBLING-MERGES-2026-08-27T1525Z]
- All five branches on the `claude-ai` remote share one root commit, `a21b4f48`, so the unrelated-histories hazard does not apply there — the fleet converged. This session branched from that root rather than adding a sixth. [src:CLAUDE-AI-SHARED-ROOT-2026-08-27]

## Observed — the goal corpus is mutable

- A second capture at 15:30Z found 14 sessions, and four of them carried a different goal than at 15:04Z; two of those four had been null before. [src:GOALS-REISSUED-2026-08-27]
- Re-issuing `/goal` replaces the string in place, so only the latest survives and any single reading of the field is a snapshot. [src:GOALS-REISSUED-2026-08-27]
- Three of the four re-issues were `continue ultrathink ooda`; four sessions now carry that exact string. [src:GOALS-REISSUED-2026-08-27]
- The fourth was a correction rather than a new task: `this is not even close to being enough dont stop do all ... run at least 20 of these cycles`. It is the only line in the corpus that reacts to delivered work instead of requesting it. [src:GOALS-REISSUED-2026-08-27]
- A fourteenth session asks for `borris churney` material to be installed and utilised across all prompts, systems and chats, using workflows and subagents — the second goal to name an external figure whose work should be absorbed. [src:GOALS-REISSUED-2026-08-27]
- On this evidence P5 (continue until nothing is open) and P9 (use workflows and subagents) were both upgraded from Moderate to Strong in `profile/OWNER-PROFILE.md`. [src:GOALS-REISSUED-2026-08-27]

## Observed — the pipeline's first integration run

- The independently-built modules compose: a cross-module run of normalize, chunk, embed, store, index, retrieve, rerank and generate completed end to end, with chunk offsets round-tripping against the source text and every citation resolving to a retrieved chunk. [src:BM25-SILENT-ZERO-2026-08-27]
- That run also exposed a defect no unit test would have caught: the lexical retrieval arm returned nothing, silently, while the dense arm kept answering. [src:BM25-SILENT-ZERO-2026-08-27]
- The cause was an IDF clamped at zero, which on a small corpus zeroes every term because every term is in more than half the documents. It was fixed to the Lucene/Robertson non-negative form. [src:BM25-SILENT-ZERO-2026-08-27]
- The regression suite was watched failing against the reverted implementation and passing against the fixed one, rather than only passing. [src:BM25-SILENT-ZERO-2026-08-27]

## Observed — the pipeline end to end

- The full chain runs offline against the seed corpus: 9 documents ingested to 40 chunks and 40 vectors, 18 goldens answered, no network. [src:PIPELINE-E2E-2026-08-27]
- Answers carry 3-5 verified citations each, and a question the corpus does not cover abstains with zero citations rather than answering. [src:PIPELINE-E2E-2026-08-27]
- Both retrieval arms contribute on every answerable question, which is what the BM25 fix restored. [src:PIPELINE-E2E-2026-08-27] [src:BM25-SILENT-ZERO-2026-08-27]
- The harness reports recall@8=1.000, MRR=1.000, nDCG@8=0.885, citation coverage=1.000, abstention 0.167, false abstention 0.000. [src:PIPELINE-E2E-2026-08-27]
- Those numbers measure self-consistency, not retrieval quality: the corpus and the golden set were written together by one agent, so perfect recall largely establishes that documents written to be retrievable are retrieved. [src:PIPELINE-E2E-2026-08-27]

## Observed — every advertised entry point runs

- `make demo`, `make test` and `make loop` all run offline on this container; the README's targets are no longer aspirational. [src:CLI-VERIFIED-2026-08-27]
- The demo answers with citations that resolve to corpus files, and refuses a question the corpus does not cover rather than producing a plausible sentence. [src:CLI-VERIFIED-2026-08-27]
- One OODA cycle produces the four-block report the design called for, and its single decision carries a stated reason and an expected value. [src:CLI-VERIFIED-2026-08-27]
- `python3 -m oodarag.cli` fails without `PYTHONPATH=src`, which is why the Makefile is the documented entry point. [src:CLI-VERIFIED-2026-08-27]

## Observed — claims recovered by the orphan advisory

- The ADR's dense-search latency table reproduces independently: 1,000 chunks at 15.0 ms/query against its stated 13 ms, 10,000 at 128.7 ms against its 123 ms. The subagent measured rather than invented. [src:ADR-PERF-REPRODUCED-2026-08-27]
- The `selfcheck` subcommand was validated by the substrate session before this branch extended it. [src:SELFCHECK-VALIDATED-2026-08-27]
- The goal recorded for the substrate session at 14:26Z asked to look through previous chats and build internal files, systems and system prompts, and to never fabricate. [src:USER-GOAL-2026-08-27]
- One ledger source is legitimately orphaned: `FLEET-REFS-20260827T150640` backs a FLEET.md roster that a later regeneration replaced, and the current roster cites the newer snapshot. [src:CLAUDE-AI-SHARED-ROOT-2026-08-27]

## Observed — the golden set does not discriminate

- Scored alone on the same index, BM25 reaches MRR=1.000 and the dense arm 0.967, both at recall@8=1.000 over the 15 answerable goldens. [src:SINGLE-ARM-EVAL-2026-08-27]
- The hybrid pipeline's MRR=1.000 is therefore attributable entirely to the lexical arm; fusion contributes nothing measurable on this set. [src:SINGLE-ARM-EVAL-2026-08-27]
- It follows that the set cannot detect a regression in the embedder, the dense index, or RRF fusion — a change breaking fusion outright would still report MRR=1.000. [src:SINGLE-ARM-EVAL-2026-08-27]

## Observed — the golden set, made able to discriminate

- 8 paraphrase goldens were added, worded to avoid the corpus's own vocabulary so term overlap alone cannot rank the right document first. [src:PARAPHRASE-GOLDENS-2026-08-27]
- On those 8, MRR is BM25 0.671, dense 0.385, hybrid 0.546 — a spread of 0.29, against 0.03 on the original 15. The set can now detect a regression in the embedder or in fusion. [src:PARAPHRASE-GOLDENS-2026-08-27]
- On paraphrase questions the fused result is worse than its own lexical arm alone: 0.546 against 0.671. Equal-weight RRF drags good lexical hits down when the other arm is much weaker. [src:PARAPHRASE-GOLDENS-2026-08-27]
- That is the ceiling `docs/adr/0001-zero-dependency-core.md` predicted in prose — a hashing embedder cannot recover paraphrase across disjoint vocabulary — now measured. [src:PARAPHRASE-GOLDENS-2026-08-27]
- It was deliberately not fixed by re-weighting, because tuning weights against the same questions that revealed the problem is the overfitting the harness exists to expose. [src:PARAPHRASE-GOLDENS-2026-08-27]

## Observed — the store suite, and a leak it found

- A subagent wrote 48 store tests but was cut off by a session limit before running them; 47 passed as written and one used a pytest-mock API absent from stdlib unittest.mock. [src:STORE-LEAK-2026-08-27]
- Repaired to use stdlib mock, that test failed for a real reason: `Store.__init__` raised `SchemaVersionError` without closing the connection it had opened, leaking a handle the caller could not reach. [src:STORE-LEAK-2026-08-27]
- With the leak fixed, all 48 pass and the full pipeline suite is 125 tests, OK, 1 skipped. [src:STORE-LEAK-2026-08-27]

## Observed — invariant suites written after the agents were cut off

- The workflow's three test agents and two audit agents all failed on a session limit, so those suites were written by hand instead. [src:INVARIANT-SUITES-2026-08-27]
- Three suites cover the invariants CLAUDE.md actually names — citation verification and abstention, `decide()` purity and dry-run side-effect freedom, and chunk offsets and fence atomicity — rather than aiming at coverage. [src:INVARIANT-SUITES-2026-08-27]
- The dry-run case was strengthened after passing suspiciously fast: it now asserts the pipeline is non-empty before comparing, so an ingest that silently did nothing cannot make it trivially true. [src:INVARIANT-SUITES-2026-08-27]

## Observed — the closing audits

- Zero third-party imports across `src/`: an AST walk against `sys.stdlib_module_names` found 0 offenders, both numpy import sites are inside `try/except ImportError`, and `pyproject` declares no runtime dependencies. [src:AUDITS-RUN-BY-HAND-2026-08-27]
- All 35 objects named in `internal/CONTRACTS.md` exist with every specified attribute; ten modules written independently against that spec did not drift at the seams. [src:AUDITS-RUN-BY-HAND-2026-08-27]
- Both audits were assigned to workflow agents killed by a session limit and were run by hand instead. [src:AUDITS-RUN-BY-HAND-2026-08-27]
- One claim is untested here: the numpy fast path cannot be compared against the stdlib fallback because numpy is not installed on this container. Both paths share one sort, so divergence is unlikely, but unlikely is not tested. [src:AUDITS-RUN-BY-HAND-2026-08-27]

## Observed — the eval baseline, now with headroom

- On the 26-golden set the pipeline scores recall@8 0.957, MRR 0.848, nDCG@8 0.785, citation coverage 1.000, abstention 0.192, false abstention 0.087. [src:EVAL-BASELINE-26-2026-08-27]
- Every metric fell against the 18-golden baseline, which is the improvement: the old set was saturated and could not detect a regression, and this one has headroom and two answerable questions it currently gets wrong. [src:EVAL-BASELINE-26-2026-08-27]
- `false_abstention` rising from 0.000 to 0.087 is the trade becoming visible: on harder questions the generator refuses rather than guessing. [src:EVAL-BASELINE-26-2026-08-27]

## Observed — fusion measured per query class, correcting an earlier finding

> Correction, not an addition: two entries above (the golden-set discrimination
> finding and the 26-golden baseline) concluded that the dense arm contributes
> nothing and fusion is strictly worse than its lexical arm. That conclusion was
> drawn from a golden set with no query class on which the dense arm could win,
> so it could only ever have reached one answer. The lines below supersede it.

- Scored per query class, MRR by typos-per-query (BM25 / dense / hybrid): 0 → 0.886 / 0.764 / 0.842; 4 → 0.688 / 0.674 / 0.723; 6 → 0.474 / 0.511 / 0.583. [src:FUSION-PER-CLASS-2026-08-27]
- The dense arm overtakes BM25 at 6 typos per query, and from 4 onward the fused ranking beats *both* arms — genuine fusion gain, not a weighted average. [src:FUSION-PER-CLASS-2026-08-27]
- The hashing embedder's character n-grams are precisely typo-robustness, so degraded input is its home class; the corpus's clean questions never exercised it. [src:FUSION-PER-CLASS-2026-08-27]
- Sweeping `lexical_weight` on clean queries is monotone and never crosses BM25-alone (1.0 → 0.546, 3.0 → 0.661, 5.0 → 0.664, against 0.671), so re-weighting is not the fix and the 1.0/1.0 default stands. [src:FUSION-PER-CLASS-2026-08-27]
- Equal weights cost about 0.04 MRR on clean queries and buy 0.03 to 0.11 on noisy ones. [src:FUSION-PER-CLASS-2026-08-27]
- The prompt to measure per class rather than in aggregate came from a GitHub project whose README benchmarks that way and asserts a fusion invariant in CI. [src:GITHUB-PRACTICE-SURVEY-2026-08-27]

## Observed — egress, probed first-hand

- `api.github.com` returns 200, `raw.githubusercontent.com` 301 and `pypi.org` 200; `www.youtube.com` returns 000 and both `www.elastic.co` and `howborisusesclaudecode.com` are refused by the egress proxy. [src:GITHUB-PRACTICE-SURVEY-2026-08-27]
- A sibling session had reported YouTube as blocked; that report was second-hand and is now verified directly. [src:GITHUB-PRACTICE-SURVEY-2026-08-27] [src:PROXY-YOUTUBE-BLOCKED]

## Observed — the config layer audited against collected practice

- `.claude/settings.json` carried hooks but no permissions block and no env, so every make target and every tool invocation prompted; a wildcard allowlist and `PYTHONPATH=src` were added. [src:GITHUB-PRACTICE-SURVEY-2026-08-27]
- CLAUDE.md was 288 lines against a collected budget of 200; it is now 208, with every named rule verified present after the rewrite. [src:CLAUDEMD-TRIMMED-2026-08-27]
- The subagent format already matched the convention used by the largest public collections — name, description written as a trigger, a minimal tool set, and a model — so no change was needed there. [src:GITHUB-PRACTICE-SURVEY-2026-08-27]
- `rerank` now has unit tests, including the control that proves the diversity case measures diversity rather than incidental reordering. [src:RERANK-TESTED-2026-08-27]
- All eleven pipeline stages now have unit tests, up from two when the plan was written. [src:COVERAGE-CLOSED-2026-08-27] [src:CLI-CONTRACT-TESTED-2026-08-27]
- The CLI returns a non-zero code with a diagnosis and no traceback on every failure path driven — no arguments, unknown subcommand, missing question, and a non-existent index. [src:CLI-CONTRACT-TESTED-2026-08-27]
- Complete coverage is not evidence of retrieval quality: the corpus is nine documents and the golden set 26 questions, so the pipeline is well specified and only thinly evaluated. [src:CLI-CONTRACT-TESTED-2026-08-27]
- The eval harness's arithmetic was checked against hand-computed textbook values for RR, recall@k, DCG, nDCG and URI matching, so the retrieval numbers reported elsewhere in this file are sound as arithmetic. [src:COVERAGE-CLOSED-2026-08-27]
- One assertion failed first and was wrong rather than finding a bug: content-free input embeds to a zero vector by design, and cosine returns 0.0 for it rather than dividing by zero. [src:COVERAGE-CLOSED-2026-08-27]

## Conclusion

The request that opened this session asked to look at "all my previous claude
chat chats all my feedbacks". Here is exactly how far that got.

**Reachable, and used.** The owner's own words survive in the `goal` string of
each session, returned verbatim by the listing API. Eleven of those exist
[src:GOALS-2026-08-27], and they are the evidence base for
`profile/OWNER-PROFILE.md`. Two sibling branches had been pushed, and both were
read in full rather than listed [src:RAG-CODE-READ-2026-08-27].

**Not reachable, and not invented.** The conversations themselves. No
transcript-reading tool was exposed to the earlier session
[src:NO-TRANSCRIPT-ACCESS-2026-08-27], no export exists on this container
[src:NO-LOCAL-ARCHIVE-2026-08-27] or in the connected Drive
[src:NO-DRIVE-ARCHIVE-2026-08-27], and eleven of the thirteen sessions have
pushed nothing at all [src:BRANCHES-2026-08-27T15-04Z].

A goal string is where a conversation started. The corrections, the rejected
suggestions, and the reasoning — the part of a chat archive actually worth
mining — remain out of reach, and remain open as U-2. Nothing downstream of
this file treats a goal string as though it were a transcript.
