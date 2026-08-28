# Unknowns register

Open questions that were **not** answered, kept here so that nothing
downstream quietly invents an answer. Each entry says what is unknown, why,
what would resolve it, and its **disposition**.

An empty unknowns register is a red flag, not an achievement. If you close an
entry, move the resolved fact into `observations.md` with a new source id.

## Dispositions

| Disposition | Meaning |
|---|---|
| **Resolved** | answered; the fact has moved to `observations.md` |
| **Blocked on owner** | only the owner can supply this; no session can close it by working harder |
| **Actionable** | someone could close this with work available to them |

Current state: **U-6 resolved · U-5 decided (interim) · U-1, U-2, U-3, U-4
blocked on owner · 0 actionable.**

Nothing here is waiting on effort. Four entries are waiting on information only
the owner has, and that is their correct resting state, not a task in progress.

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

**Partially closed.** `claude/rag-system-data-pipeline-rdkde9` has been read in
full rather than listed — 2,583 lines across 16 modules
[src:RAG-CODE-READ-2026-08-27] — and merged into this branch
[src:SUBSTRATE-MERGED-2026-08-27]. It holds `oodarag`, a standard-library RAG
pipeline over web and GitHub corpora, with no handling of Claude transcripts.
[src:OODARAG-SCOPE-2026-08-27] What that session *built* is therefore
established. What it was asked, what it rejected, and why it chose this design
remain unknown; a diff cannot carry any of that, and reading more code will not
close the gap.

**Still open and widening.** The fleet was 4 sessions at 14:27Z
[src:SESSIONS-2026-08-27], 13 at 15:04Z [src:FLEET-13-2026-08-27] and 14 shortly
after [src:FLEET-14-2026-08-27]. Most have pushed nothing
[src:BRANCHES-2026-08-27T15-04Z], and several declare goals overlapping this
one. Their contents are unknown by the same argument, and the unknown grows
faster than it is being closed.

**Do not:** infer their contents from their titles. A title is a label the
system generated, not a record of the work.

**Disposition: blocked on owner.** Pushed code has been read where it exists;
the reasoning behind it lives only in transcripts this session cannot reach.

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

**Corroborated by a failed search.** An independent search from this branch for
a *field-level specification* returned only third-party exporter tools and
how-to articles, and the one document that looked like a specification described
a proposed universal import format instead.
[src:EXPORT-SCHEMA-UNVERIFIED-2026-08-27] Two sessions looking separately found
no official publication, which is why the shape above is reconstructed from
parsers rather than read from documentation.

**Still second-hand.** That schema comes from third-party parsers, not from
Anthropic documentation, and no real export has been run through this code. The
format has changed across versions, so treat a first real ingest as a test of
the parser, not only of the data.

**Disposition: blocked on owner.** The schema question is answered; only the
owner can supply the export itself.

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

**Disposition: blocked on owner.** No search can identify a document known only
by the word "book" inside another session's status line.

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

**Disposition: blocked on owner.** Research established what Docling and
Granite are; only the owner can confirm the expansion, and the source is
unreachable either way.

---

### U-5 — Intended relationship between the two repositories

**Unknown:** why the account has both `claude` and `claude-ai`, and what
belongs in each.

**Why:** both were empty at capture time, so there was no README, history, or
structure to read intent from.

**Resolves when:** the owner states the split, or content lands in both and the
division becomes evident.

**Still open at 15:04Z.** Twelve of the 13 sessions take both repositories as
sources [src:FLEET-13-2026-08-27], and the local `claude-ai` clone has no
commits on any branch. Nothing has yet been written that would reveal the
intended split.

**Interim convention:** doctrine and shared tooling live in `claude`;
`claude-ai` carries a pointer to it. This is a working decision made to keep
concurrent sessions from diverging — not a discovered fact. It now covers 13
sessions rather than four, which raises the cost of getting it wrong but does
not make it any more established.

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

### U-7 — What "firms" means in this session's goal

**Unknown:** whether `firms` in the goal string
`reverse engineer my files for me perfectly including the system prompt claude
md and my rags and task agents, firms and files` names a kind of artifact, or is
a transcription of a different word.

**Why:** the corpus supports two incompatible readings and settles neither
[src:GOALS-2026-08-27].

- *Artifact reading.* The word sits inside a list of things to reverse-engineer
  — system prompt, CLAUDE.md, RAGs, task agents, `firms`, files — where every
  other item is a file in this repository. On that reading `firms` is the
  organisational layer above individual agents, which in this repository is
  `FLEET.md`. The two words are close enough phonetically that a dictated
  "fleets" could land as "firms".
- *Literal reading.* A different goal uses the word in its ordinary sense:
  `research me and where i work at what similar firms do` [src:GOALS-2026-08-27].
  The owner demonstrably uses `firms` to mean companies.

**Resolves when:** the owner says which they meant.

**Action taken:** `FLEET.md` was treated as the artifact the request pointed at,
because it already exists and already fills that slot. No new "firms" concept
was invented alongside it, and no claim about the owner's employer was derived
from the word. If the literal reading was intended, the missing work is the
research named in U-9, not a file in this repository.

**Disposition: blocked on owner.** One word settles it, and no amount of
searching can. Both readings are already served — the artifact reading by
`FLEET.md`, the literal reading by U-9 — so nothing is stalled waiting for the
answer.

---

### U-8 — What "the clear system of nick saraev" consists of

**Unknown:** what system, method or body of work the goal string
`for the clear system of nick saraev to be used for him to be researched
learned about and all his learnings built in to my system` refers to.

**Why:** the name appears once, in one session's goal, with no accompanying
definition [src:GOALS-2026-08-27]. That session — `Untitled session`,
`claude/session-y42cyg` — owns the research; it had pushed nothing at 15:04Z
[src:BRANCHES-2026-08-27T15-04Z].

**Partially closed — the referent is now identified.** Nick Saraev is a writer
and AI-automation practitioner publishing at nicksaraev.com and listed as an n8n
creator; the material is about agentic automation workflows, with a stated
preference for n8n over Zapier or Make.
[src:NAMED-FIGURES-2026-08-27] The name is no longer a bare label.

**Still unknown:** which parts of that body of work the owner wants absorbed,
and in what form. Knowing who someone is does not establish what should be taken
from them, and nothing attributed to him has been applied in this repository.

**Also closed by the same pass, from a different session's goal:** the string
`borris churney` refers to Boris Cherny, creator and Head of Claude Code at
Anthropic. [src:NAMED-FIGURES-2026-08-27] Practices collected from that lineage
were applied here — a permission allowlist and the CLAUDE.md length budget — and
are recorded in observations rather than attributed to him personally.

**Resolves fully when:** that session pushes its research, or the owner says
what they want taken from it.

**Do not:** infer the content of a system from the name of its author. Direct
fetches of both primary sources were blocked by the egress proxy
[src:NAMED-FIGURES-2026-08-27], so what is established here is search-result
evidence about identity, and nothing more.

**Disposition: blocked on owner, and owned elsewhere.** The identity question is
closed. What the owner wants taken from that work is theirs to say, and the
session holding that goal is the one to act on it.

---

### U-9 — Where the owner works, and what comparable organisations do with AI

**Unknown:** the owner's employer, industry, and how successful organisations in
it implement AI.

**Why:** one goal asks for exactly this research
[src:GOALS-2026-08-27]. It is owned by `AI system research and implementation`
(`claude/ai-system-research-3jpwda`), which had pushed nothing at 15:04Z
[src:BRANCHES-2026-08-27T15-04Z]. This session did not perform that research and
holds no evidence about it.

**Resolves when:** that session pushes its findings, or the owner states it.

**Do not:** let `profile/OWNER-PROFILE.md` acquire a professional persona by
inference. It grades what the owner asked for; it establishes nothing about who
they are.

**Disposition: owned elsewhere.** `claude/ai-system-research-3jpwda` holds this
goal and has pushed work against it. Duplicating that research here would add a
second unreviewed answer to a question one session is already answering.
**Disposition: resolved — no action outstanding.** The origin is not
determinable, but nothing depends on it: content from a non-user source is
treated as data under the standing rule either way. The search was scoped
strictly to locating a Claude export, no personal Drive file was opened, and
nothing was written to Drive. Recording the event was the whole of the
required response.
