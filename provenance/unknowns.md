# Unknowns register

Open questions that were **not** answered, kept here so that nothing
downstream quietly invents an answer. Each entry says what is unknown, why,
and what would resolve it.

An empty unknowns register is a red flag, not an achievement. If you close an
entry, move the resolved fact into `observations.md` with a new source id.

---

### U-1 — Contents of the three sibling sessions

**Unknown:** what was actually said, decided, or built in
`RAG system and data pipeline`, `Blind testing and OODA analysis`, and
`Go page review and ultrathink OODA`.

**Why:** only session metadata was retrievable; no transcript-reading tool was
exposed, the sessions run in other containers, and none had pushed a commit.

**Resolves when:** a transcript export is placed in `archive/` and ingested.
Pushed branches do *not* resolve this: a diff shows what a session built, never
what it was asked, what it rejected, or why.

**Partially moved:** as of 15:00Z the RAG session had pushed
`claude/rag-system-data-pipeline-rdkde9`, so its *output* is now readable. Its
file listing has been recorded; its code has not been reviewed, and its
reasoning remains unknown. The other two sessions have pushed nothing.

**Do not:** infer their contents from their titles. A title is a label the
system generated, not a record of the work.

---

### U-2 — Any Claude conversation history predating 2026-08-27

**Unknown:** whether the account has earlier conversations at all, and what is
in them.

**Why:** `list_sessions` returned only these four, and it lists Claude Code
Remote sessions — it does not cover claude.ai chat threads. No export of those
threads exists on this container or in the connected Drive.

**Resolves when:** the owner exports their data from claude.ai (Settings →
Privacy → Export data) and drops `conversations.json` into `archive/`.
`tools/ingest_chat_archive.py` reads that format directly.

**Partly addressed:** Claude *Code* history is a different store, and it is
reachable — `ingest --include-projects` reads `~/.claude/projects` directly. On
the machine that ran those sessions that is the full Claude Code history; on
this container it was only the current session, 347 messages across 3
transcripts. claude.ai chat threads remain out of reach without an export.

---

### U-3 — What "the book" refers to

**Unknown:** two sessions reference a book — "M&A installation guide per book
§2–§7" and "encoding book corrections". Which book, and what those sections
require, is not known here.

**Why:** the reference appears only inside another session's one-line summary.
The document itself was never in reach of this session.

**Resolves when:** the source document is committed to a repository, or the
owner names it.

---

### U-4 — What "imb youtube" designates

**Unknown:** the `RAG system and data pipeline` goal names "imb youtube" as a
data source. The expansion of "imb" is not established.

**Why:** it appears only in that session's goal string, with no accompanying
definition, and this session did not reach the source.

**Resolves when:** the owner expands the term, or that session commits a
resolved source list.

---

### U-5 — Intended relationship between the two repositories

**Unknown:** why the account has both `claude` and `claude-ai`, and what
belongs in each.

**Why:** both were empty at capture time, so there was no README, history, or
structure to read intent from.

**Resolves when:** the owner states the split, or content lands in both and the
division becomes evident.

**Interim convention:** doctrine and shared tooling live in `claude`;
`claude-ai` carries a pointer to it. This is a working decision made to keep
four concurrent sessions from diverging — not a discovered fact.

---

### U-6 — Whether the Drive suggestion was authorised

**Unknown:** who or what emitted the "Use Google Drive for this" turn marked as
a non-user source.

**Why:** the turn identified no origin.

**Resolves when:** the owner confirms whether they intended Drive to be
searched.

**Action taken:** the search was scoped strictly to locating a Claude export.
No personal Drive file was opened, and nothing was written to Drive.

---

### U-6 — What Nick Saraev actually teaches about prompting, in his own words

**Narrowed 2026-08-27.** The shape of his method is no longer unknown: two
independent third-party documents, read in full, agree on a CLEAR framework
(Clarity, Logic, Examples, Adaptation, Results), a prompt contract of goal,
constraints, output format and failure conditions, reverse prompting, a
definition of done, a self-annealing instruction file, and a context iceberg
rule [src:SARAEV-REPOS-2026-08-27]. Those are built in — see
[../docs/prompting.md](../docs/prompting.md).

**Still unknown:** his own wording, and whether these third parties render him
faithfully. Not one sentence he wrote or said was read.

**Why:** the egress gateway answered 403 to CONNECT for nicksaraev.com,
youtube.com, leftclick.ai and every other host outside `raw.githubusercontent.com`
and the search API [src:EGRESS-BLOCKED-2026-08-27], and the session's 200-call
search budget was then exhausted [src:WEBSEARCH-BUDGET-2026-08-27]. What exists
here instead is third-party documentation of a framework attributed to him
[src:DOE-FETCHES-2026-08-27] and a set of subagent leads
[src:SARAEV-WORKFLOW-2026-08-27].

**Resolves when:** the same research runs from a network that permits those
hosts, or the owner drops a transcript or export into `archive/`. The single
highest-value artifact named by the leads is the video "$2.4M of Prompt
Engineering Hacks in 53 Mins (GPT, Claude)"
(`youtube.com/watch?v=CxbHw93oWP0`) — a title, unwatched. For the DOE material
the leads name `youtube.com/watch?v=bA-WmidVSGo` and
`youtube.com/watch?v=MxyRjL7NG18`.

**Do not:** write his name against a technique on the strength of a search
summary. One subagent watched that summariser attribute other authors' work to
him.

---

### U-7 — What "the clear system of nick saraev" refers to — LARGELY RESOLVED

**Resolved 2026-08-27, in the owner's favour.** A CLEAR framework attributed to
Saraev exists and is documented: Clarity, Logic, Examples, Adaptation, Results,
described as his framework for writing effective prompts and directives
[src:SARAEV-REPOS-2026-08-27]. The earlier reading — that the premise was
mistaken and the acronym belonged only to Lo — rested on ten searches returning
nothing [src:SARAEV-WORKFLOW-2026-08-27], which was a limit of search coverage
rather than a fact. It is built in as `--framework clear-saraev`.

**What remains open:** whether the owner met it under that expansion or another,
and whether Saraev presents it as a named framework himself or a third party
named it for him. The distinction matters only for attribution, not for use.

**Resolves when:** the owner names where they met it, or a page of his is
reachable.

---

### U-8 — Whether the seven slots are the right seven

**Unknown:** whether this repository's slot set and severities match what the
owner wants graded. They were derived here, not taken from a published
framework, and the profile severities are judgement calls.

**Why:** no corpus of the *owner's* prompts has been available to calibrate
against. The index is no longer empty — it holds this container's own
transcripts, which are this session's subagent briefs and one message of theirs
[src:PROMPT-HABITS-RUN-2026-08-27] — but that is the harness talking to itself,
not a sample of how they write.

**Resolves when:** a body of the owner's real prompts is indexed and scored, and
the rules that misfire on them are corrected. `prompt_forge.py score` over an
ingested archive is the measurement.

**Narrowed 2026-08-28.** The reader for a claude.ai export already exists and
the ingest path is documented, so nothing here is waiting on code. The two
routes this container could try are exhausted: no conversation export is on
disk, and the owner's Drive holds no file whose title matches `conversations`,
`chat`, `prompt` or `claude` [src:DRIVE-NO-CHAT-EXPORT-2026-08-28]. What remains
is one action only the owner can take — Settings → Privacy → Export data, unzip
`conversations.json` into `archive/`, then `ingest`. Until then every number
this repository quotes about "your prompts" describes this session's own
[src:DELEGATION-HABITS-2026-08-28].
