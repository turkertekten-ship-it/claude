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

**Re-checked and unblocked on everything except the export itself
(2026-08-28T08:00Z).** The container was swept again first-hand rather than
inherited: `/mnt/attach` and `/mnt/user-data` are both empty, and no export
exists anywhere on disk [src:ARCHIVE-DIR-MISSING-2026-08-27].

**One thing standing in the way was ours, and is fixed.** `archive/` did not
exist. `.gitignore` carried `!archive/.gitkeep`, a negation with no committed
file to preserve, while the README instructed the reader to unzip an export
into that directory — so the documented workflow failed at step one in a fresh
clone. `archive/.gitkeep` is now committed
[src:ARCHIVE-DIR-MISSING-2026-08-27].

**The path is verified working, not merely written.** Run against a real
Claude Code transcript rather than fixtures, the tool indexed 585 messages
across 1 conversation, and searches returned correctly attributed verbatim
excerpts with timestamps, message ids and source filenames
[src:ARCHIVE-DIR-MISSING-2026-08-27]. The test copy was deleted afterwards and
is not committed.

So this entry now rests on exactly one action, and it is the owner's: produce
the export. Nothing else is in the way.

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

**RESOLVED (2026-08-27T17:30Z) — and both earlier readings were wrong.** The
answer was on a branch this register had never read. `blind-testing-ooda-5o3s67`
carries a 99-file `mafirm/` tree written in Turkish, and
`mafirm/KITAP-ERRATA.md` — *kitap* is Turkish for **book** — is an errata sheet
against it [src:BOOK-IDENTIFIED-2026-08-27].

The book is a **Turkish-language sectioned installation guide for a
cross-border M&A practice**, numbered at least §1–§14: §3 is the operating
agreement, §4 the specialty units, §5.1 the competition thresholds. The
"§2–§7" in that session's status line is this document's own numbering. It is
neither a closing book nor an information memorandum — the two candidates
entertained above, both discarded.

The errata's own finding is worth carrying forward: most defects blind testing
surfaced were **in the book's text, not in the installation**
[src:BOOK-IDENTIFIED-2026-08-27].

**Still not known:** the book's title and author. Resolving what a document
*is* is not the same as identifying it, and nothing here names it.

**A live hazard for that work.** The book's Turkish merger-control thresholds
cannot be checked against primary sources from any container on this
allowlist: `mevzuat.gov.tr`, `resmigazete.gov.tr`, `rekabet.gov.tr`,
`spk.gov.tr` and `kvkk.gov.tr` are all refused at CONNECT
[src:TR-REGULATORS-BLOCKED-2026-08-27]. That session marked the section
"could not be verified against a primary source" and required human
confirmation rather than asserting the numbers, which is the correct handling.

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

**RESOLVED (2026-08-27T17:25Z), by this entry's own criterion.** The criterion
above was "the owner expands the term, *or that session commits a resolved
source list*". That session committed one:
`corpus/ibm-technology/manifest.json`, an "IBM Technology video manifest for
the YouTube connector" [src:IBM-MANIFEST-2026-08-27]. The session holding the
term resolved it as **IBM Technology**.

Two things make this safe to record as resolved rather than as another guess.
The manifest grades each entry — `search_confirmed` where multiple independent
results attribute the video to IBM, `search_listed` where one did, and anything
weaker is excluded. And it carries no summaries at all, because
youtube.com was unreachable from that container and attributing prose to a
video whose captions were never read "would produce a citation that looks
verbatim and is not" [src:IBM-MANIFEST-2026-08-27].

**What is resolved and what is not:** the term's referent, as fixed by the
session that owns it and graded per entry. Not the owner's own statement of
intent, which was never obtained.

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

**Routed around, and narrower than it looked (2026-08-27).** A complete
PDF-to-text path exists inside this allowlist with no Hugging Face dependency:

- **Born-digital** — `pypdf` (pure Python, PyPI) extracted the test text
  verbatim [src:PYPDF-WORKS-2026-08-27]; `pdftotext` from poppler-utils does
  the same [src:OCR-CHAIN-WORKS-2026-08-27].
- **Scanned** — the Ubuntu noble archive is reachable even though the launchpad
  PPAs are refused, so `tesseract-ocr` 5.3.4 and `poppler-utils` 24.02.0 both
  install. `pdftoppm -r 200 -png` followed by `tesseract` returned the test
  clause headings exactly [src:OCR-CHAIN-WORKS-2026-08-27].

**What is still genuinely unavailable** is the specific thing Docling's
TableFormer exists for: table structure recognition and reading-order
recovery. Tesseract returns text, not table geometry
[src:OCR-CHAIN-WORKS-2026-08-27]. For a contract corpus that matters in a
bounded way — clause prose survives, and schedules, payment tables and cap
tables do not come back as structure.

**Also note the ephemerality**, which is the same trap as the user-scope skill
install: these are apt packages in a container that does not persist. A fresh
session has none of them. Anything depending on this path needs the install to
be a scripted step, not a remembered one.

**Tables are further along than "unavailable" (2026-08-27T17:40Z).** Tested
rather than assumed [src:TABLES-RECOVERABLE-2026-08-27]:

- **Born-digital tables** — `pdfplumber`'s default line-based strategy found
  nothing on a table ruled only horizontally, but with both strategies set to
  `"text"` it returned the correct grid. Imperfectly: cells clip at the
  inferred column boundary (`18 months` came back `18 mont`) and phantom empty
  rows appear. Usable with validation; not usable on trust.
- **Scanned tables** — tesseract's `tsv` output carries word-level geometry,
  and on the rasterised page the left coordinates clustered cleanly at three
  column positions and the tops at three row positions. Reconstruction is
  therefore possible, but it means clustering words into row and column bands
  yourself; nothing off the shelf does it.

**What is genuinely still missing** is narrow and worth naming precisely: a
*trained* table-structure model of TableFormer's kind, for merged cells,
spanning headers and complex or rotated layouts. That is the whole of the
residue — not "PDF parsing", not "tables".

**Resolves fully when:** Hugging Face is reachable, or a table-structure model
is obtainable from an allowlisted host.

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

**RESOLVED (2026-08-27T16:40Z) — unpushed, not unwritten.** That session pushed
three further commits. `src/oodarag/` now carries `chunking.py`, `cli.py`,
`config.py`, `pipeline.py` and the `embedding/`, `retrieve/`, `store/`,
`generate/`, `eval/`, `ooda/` and `access/` packages
[src:RAG-BRANCH-COMPLETE-2026-08-27]. The README was describing work in
progress, not overclaiming.

This also closes audit finding **F-1**: `src/oodarag/cli.py` now exists, so the
console script declared in `pyproject.toml` resolves
[src:RAG-BRANCH-COMPLETE-2026-08-27]. F-2 through F-5 were not re-checked
against the new commit and should not be assumed fixed or unfixed.

**The general lesson, which is the reusable part:** an absence observed in a
repository where other sessions are actively working is a statement about what
has been *pushed*, never about what exists. This register said "unpushed work
is a live possibility" and that is exactly what it was.

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

**Practice has now converged, which is not the same as resolved
(2026-08-27T17:35Z).** The `claude-ai` remote carries 10 branches. **Eight hold
exactly one file, `CLAUDE.md`** — the pointer — so eight sessions independently
arrived at the interim convention without coordinating
[src:CLAUDE-AI-SPLIT-2026-08-27]. That promotes it from one session's working
decision to established practice.

It does **not** close this entry, and the reason is the warning this register
already carries: where content landed says which session put it there, never
what the owner wants. Eight sessions agreeing is eight sessions making the same
convenient choice.

**Two branches diverge, and one is not a rounding error.**
`rag-system-data-pipeline` holds 14 files there including CI and an
`install.sh`; `research-skill-mastery` holds **95**, a full `.claude/` tree of
agents and commands [src:CLAUDE-AI-SPLIT-2026-08-27]. That is a second copy of
the doctrine layer in the repository the doctrine explicitly says must not hold
one — the "two copies of a rule set become two different rule sets" failure,
already in progress rather than hypothetical.

**Resolves when:** the owner states the split. Until then the divergence should
be surfaced to them, not silently normalised in either direction.

---

### U-6 — Whether the Drive suggestion was authorised

**Unknown:** who or what emitted the "Use Google Drive for this" turn marked as
a non-user source.

**Why:** the turn identified no origin.

**Resolves when:** the owner confirms whether they intended Drive to be
searched.

**Action taken:** the search was scoped strictly to locating a Claude export.
No personal Drive file was opened, and nothing was written to Drive.

**RESOLVED for later sessions, not retroactively (2026-08-27).** The owner
subsequently issued a goal to this session containing "looking into my files"
in their own words [src:USER-GOAL-SKILLS-2026-08-27]. That is direct
authorisation, and Drive was searched on that basis: titles and metadata only,
no file content opened [src:DRIVE-OWNED-FILES-2026-08-27].

It does **not** answer the original question, which was who emitted the
unattributed "Use Google Drive for this" turn. A later authorisation from the
owner does not retroactively make an earlier unattributed instruction
legitimate, and treating it that way would be the exact laundering this entry
exists to catch. The origin of that turn remains unknown.
