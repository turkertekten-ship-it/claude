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

---

### U-3 — What "the book" refers to

**Unknown:** two sessions reference a book — "M&A installation guide per book
§2–§7" and "encoding book corrections". Which book, and what those sections
require, is not known here.

**Why:** the reference appears only inside another session's one-line summary.
The document itself was never in reach of this session.

**Resolves when:** the source document is committed to a repository, or the
owner names it.

**Narrowed, not resolved (2026-08-27).** The owner's own Drive files are a
corporate-transaction set indexed `1.g`, `3.a`, `4.a` — a closing-checklist
numbering, not a filename habit [src:DRIVE-OWNED-FILES-2026-08-27]. That
establishes the *domain* the phrase sits in: M&A transaction documents, where
a numbered section reference like "§2–§7" is ordinary. It does not establish
which document. In that domain "the book" has at least two common referents —
a closing book or deal bible compiling the executed set, and an information
memorandum — and nothing seen here distinguishes them.

**Do not** pick one and build section scaffolding against it. A guide written
to the wrong §-numbering is worse than no guide, because it looks authoritative
and cites sections that do not exist.

---

### U-4 — What "imb youtube" designates

**Unknown:** the `RAG system and data pipeline` goal names "imb youtube" as a
data source. The expansion of "imb" is not established.

**Why:** it appears only in that session's goal string, with no accompanying
definition, and this session did not reach the source.

**Resolves when:** the owner expands the term, or that session commits a
resolved source list.

---

**Narrowed, not resolved (2026-08-27).** Two pieces of evidence bear on it.
Docling — named in a *different* sibling's summary — is IBM Research Zurich's
document-conversion toolkit, and its vision-model line is called Granite
[src:DOCLING-IBM-2026-08-27]. That makes "imb" as a transposition of **IBM**,
and "G stack" as **Granite**, the reading that fits the surrounding evidence
best. It remains a reading. Two summaries written by sessions this one could
not read are not a definition, and `www.ibm.com` and `research.ibm.com` are
both unreachable from here [src:EGRESS-2026-08-27], so the guess could not be
checked against the source even in principle.

**Third leg (2026-08-27).** An "IBM Technology" YouTube channel exists and
publishes retrieval-augmented-generation explainers, one of them presented by a
Senior Research Scientist at IBM Research [src:IBM-YOUTUBE-CHANNEL-2026-08-27].
So a channel matching the description does exist and carries exactly the
material a RAG session would want. Three independent legs now point the same
way — Docling is IBM's, Granite is IBM's, and IBM publishes RAG video.

That raises the confidence and does not change the grade. Establishing that a
plausible referent exists is not establishing that the owner meant it; the
phrase still appears only inside one goal string this session did not write.

**Do not** write IBM into a source list, a connector name, or a config default
on the strength of this. If the expansion is wrong, every artifact built on it
inherits the error silently — which is the exact failure this register exists
to prevent. Note also that even if the reading is right, the transcripts of
that channel are not reachable through the Data API — see U-7.

**Separately, and independently of what "imb" means:** the blocker recorded
against that goal has moved. `www.youtube.com` is genuinely unreachable, but
the YouTube Data API answers and only wants a key
[src:YOUTUBE-API-REACHABLE-2026-08-27]. See U-7.

---

### U-7 — Whether a YouTube Data API key is available to this account

**Unknown:** whether the owner has, or wants to create, a Google Cloud project
with the YouTube Data API v3 enabled and a key available to these sessions.

**Why:** the API is reachable from this container and returns a well-formed
"use an API key" error [src:YOUTUBE-API-REACHABLE-2026-08-27], so the key is
now the only thing between the pipeline and YouTube metadata and caption
tracks. No key is present in this environment, and none was requested.

**Resolves when:** the owner either supplies a key through the environment's
secret configuration, or says YouTube is not wanted as a source after all.

**Answered, and the answer is worse than assumed (2026-08-27).** A key does
*not* reach captions. Google's implementation guide requires OAuth 2.0 for
`captions.list`, and OAuth plus ownership of the video for
`captions.download`, which returns 403 for third-party public videos
[src:YOUTUBE-CAPTIONS-OAUTH-2026-08-27]. So:

- **Video metadata** — titles, descriptions, durations, playlists: an API key
  is sufficient, and that part of U-7 stands.
- **Transcripts of someone else's videos** — not obtainable through the Data
  API at all, by any credential the owner can hold. Ownership cannot be
  granted.

**What this closes.** A pipeline that planned to ingest transcripts from a
third-party channel through the official API should stop planning that. The
remaining honest routes are a transcript source that is not `youtube.com` (that
host is refused at CONNECT [src:EGRESS-2026-08-27]), a commercial extraction
vendor of the kind already recorded and rejected in `SKILLS.md`
[src:PLUGIN-CATALOG-2026-08-27], or the owner supplying transcripts directly.

---

### U-9 — How Docling model artifacts could reach this environment

**Unknown:** whether there is any route to the Docling model weights from a
container on this egress allowlist.

**Why:** Docling installs cleanly from PyPI, which is allowlisted, but fetches
its layout and TableFormer weights by `repo_id` from Hugging Face, which is
refused at CONNECT. `snapshot_download("ds4sd/docling-models")` was run and
raised `ProxyError: 403 Forbidden` [src:DOCLING-MODELS-BLOCKED-2026-08-27].

**Why it matters now:** a sibling session reports "docling building"
[src:SESSIONS-2026-08-27]. The pip half of that will succeed and the
conversion half cannot, so the failure will appear late and look like a Docling
bug rather than an environment policy.

**Resolves when:** either Hugging Face is added to the environment's network
policy, or the artifacts are staged from a machine that can reach it and
`DOCLING_SERVE_ARTIFACTS_PATH` is pointed at them. Docling supports fully
air-gapped operation given a pre-staged directory; nothing here can produce
that directory.

**Do not:** add Docling to a dependency list on the strength of it installing.
Installation is not capability here.

---

### U-8 — Why the pipeline README describes stages that do not exist

**Unknown:** whether the absent stages in `src/oodarag/` are simply not written
yet, or were written and not pushed.

**Why:** the README presents eight failure modes as handled, in the present
tense, while four have no module [src:AUDIT-OODARAG-2026-08-27]. It points at
`internal/PLAN.md` for the built-versus-planned split, and that file is absent
[src:AUDIT-OODARAG-2026-08-27]. That session was still RUNNING at capture time
[src:SESSIONS-2026-08-27], so unpushed work is a live possibility.

**Resolves when:** that session pushes again, or `internal/PLAN.md` lands.

**Do not:** treat the README's table as a description of the tree. It is a
description of the intent.

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
