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

### U-7 — Whether "borris churney" designates Boris Cherny

**Unknown:** the owner's request named "borris churney". No source in this
repository records the owner confirming who that is.

**Why:** the identification rests on phonetic similarity plus the subject
matter of the request (prompts, systems, chats, OODA, workflows, subagents),
which matches Boris Cherny, creator and head of Claude Code
[src:CHERNY-IDENTITY-2026-08-27]. That is an inference, not a statement by the
owner.

**Resolves when:** the owner confirms or corrects the name.

**Action taken:** the corpus was built on Cherny material and says so in its
title, so a wrong identification is visible immediately rather than buried.

---

### U-8 — Fidelity of the tip compilation to Cherny's original posts — **CLOSED**

**Resolved 2026-08-27.** All 60 tips were checked against the 65 screenshots of
the original posts bundled in the compilation. The finding moved to
`observations.md`. Summary: roughly 35 transcribe faithfully; the remainder
fail in both directions — meaning-changing omissions, four invented bullets
written in Cherny's voice, reassigned attributions, and two mis-transcriptions.
Every numeric claim held. [src:SCREENSHOT-AUDIT-2026-08-27]

**What this closed does not cover:** the screenshots themselves are images
supplied by the same compiler, so they are not independent of him. They agree
with a separately-sourced transcription of the January thread wherever both
were checked [src:CHERNY-THREAD-MIRROR-2026-01-02], which is the best
corroboration available while `x.com` is blocked.

---

### U-9 — What Cherny actually said about prompt engineering

**Unknown:** a search result carried the headline "Head Of Anthropic's Claude
Code Says Prompt Engineering Not That Important". Whether he said that, and in
what context, is not established.

**Why:** only the headline was returned; the article was not fetched, and the
domain was not reachable [src:EGRESS-BLOCKED-2026-08-27]. A headline is a
label, and this repository does not expand labels into content.

**Resolves when:** the article or its underlying interview becomes reachable.

**Note:** it is recorded because it may sit in tension with the corpus's
emphasis on detailed specs and plan quality. That tension is unresolved, not
decided.

---

### U-10 — Cherny material published after 2026-04-16 — **PARTLY CLOSED**

**Resolved in part 2026-08-27.** One of the two leads was recovered: the
2026-05-24 post is in hand, via a mirrored X digest on GitHub after `x.com`
itself stayed blocked. Its content — that his "#1 tip" is now auto mode, as the
enabler of multi-clauding — is recorded in `observations.md`.
[src:CHERNY-X-2026-05-24]

**Still unknown:** the Threads post of 2025-12-27 cited second-hand as claiming
"259 PRs in 30 days" was not recovered; `threads.com` is blocked and no mirror
of it was found. Anything he has published after 2026-05-24 is also unchecked —
the digest that supplied the May post covers a single day.

**Why it stays open:** the recovery route was a third-party scrape, not the
source. It carries structured metadata (author id, timestamps, engagement
counts, a quoted-tweet object) consistent with a real capture, but it has not
been checked against x.com and cannot be from here.

**Resolves when:** `x.com` or `threads.com` become reachable, or an export is
placed in `archive/`.
