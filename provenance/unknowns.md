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

**Partially moved:** the RAG branch has been read, not just listed — it holds
`oodarag`, a standard-library RAG pipeline over web and GitHub corpora, with no
handling of Claude transcripts. [src:OODARAG-SCOPE-2026-08-27] What that session
was *asked*, what it rejected, and why it chose this design remain unknown; a
diff cannot carry any of that.

**Still open and widening:** the fleet is now fourteen sessions.
[src:FLEET-14-2026-08-27] Most have pushed nothing, and several declare goals
overlapping this one. Their contents are unknown by the same argument.

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

**Schema question now closed.** The export shape was established from public
sources rather than guessed: conversations carry `uuid`, `name`, `created_at`,
`updated_at`, `chat_messages[]`; messages carry `uuid`, `sender`, `created_at`,
a flat `text`, a `content[]` block list, and `attachments[]` with `file_name`
and `extracted_content`. [src:CLAUDE-EXPORT-SCHEMA-2026-08-27] The parser was
tested against that shape and one real gap was found and fixed — attachment
bodies were being dropped. [src:EXPORT-PARSER-TESTED-2026-08-27]

**Still second-hand.** That schema comes from third-party parsers, not from
Anthropic documentation, and no real export has been run through this code. The
format has changed across versions, so treat a first real ingest as a test of
the parser, not only of the data.

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

**What research established.** A sibling session reported verifying a
"Docling/Granite IBM hypothesis". Those are real IBM projects: Docling was
initiated by IBM Research Zurich and is now hosted in the LF AI & Data
Foundation — 65.7k stars, MIT, converting PDF/DOCX/PPTX/XLSX/HTML/EPUB into
Markdown and JSON — and GraniteDocling is its vision-language model.
[src:DOCLING-IBM-2026-08-27]

**What research did NOT establish.** That "imb" means IBM. It is a plausible
transposition, and the sibling's hypothesis points the same way, but the owner
has not said so and a plausible reading is not a fact. Nothing in this
repository depends on the expansion.

**Also unreachable:** `www.youtube.com` is blocked at the proxy for both curl
and WebFetch, so no YouTube source can be read here regardless of what "imb"
means. [src:EGRESS-MAP-2026-08-27] This confirms first-hand what the RAG
session had reported second-hand.

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
