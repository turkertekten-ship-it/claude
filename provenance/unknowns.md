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

**Resolves when:** the sessions push their branches (then read the diffs), or a
transcript export is placed in `archive/` and ingested.

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

### U-7 — What the Console playground actually offers in its UI

**Unknown:** which affordances the current playground exposes — whether it has
a variables panel, saved prompts, a tool-definition editor, a batch submitter,
or a token counter.

**Why:** `platform.claude.com/playground` returns the Console login page when
fetched unauthenticated, and the Help Center article the release note points at
is on a domain this container's egress proxy blocks. The release note's claim
that it "supports every Messages API parameter" is a statement about
parameters, not about controls.

**Resolves when:** someone signed in to the Console describes or screenshots it,
or the Help Center becomes reachable.

**Consequence:** the parity matrix in `docs/parity.md` marks the playground
column from the release notes and the API reference, not from the UI. Rows
about what the playground can do are therefore claims about the API it builds
requests for.

---

### U-8 — Whether the MT-Bench figures match the canonical paper

**Unknown:** whether the judge-consistency, verbosity and self-preference
numbers used to justify the blind-comparison design match arXiv 2306.05685 as
published.

**Why:** `arxiv.org` is blocked by this container's egress proxy. Two
independent GitHub full-text mirrors agreed exactly, and the behaviour they
describe matches the FastChat implementation, which is corroboration but not a
reading of the canonical PDF.

**Resolves when:** the paper is fetched from an unblocked network.

**Consequence:** the design does not depend on the exact values. It depends on
the direction — that position bias is large enough to matter — and on the
paper's stated prescription, which the implementation follows. Treat the
numbers as motivation, not as calibration constants.

---

### U-9 — Whether the doctrine prompt's measured effect generalises

**Unknown:** whether the result of `suites/doctrine-adherence.yaml` holds
beyond its six cases, one model, and single sample per cell.

**Why:** six cases is a small suite by construction. The report computes how
many decided pairs would be needed to detect a genuine 70/30 preference at 80%
power, and the suite does not have them.

**Resolves when:** the suite is extended, `repeats` is raised above 1, or the
same variants are run against a second model family.

**Do not:** quote a win rate from that run as though the question were settled.
The report says what it did not establish; that section is the result too.

---

### U-10 — RESOLVED: the operating prompt does not measurably reduce fabrication

Answered on 2026-08-27 by `suites/hard-traps.yaml`. Moved to
`observations.md` under "the hard traps". Kept here as a pointer because the
question was open long enough to be cited.

**The answer:** on traps hard enough to make both arms fail, no measurable
difference. What remains open is narrower: twelve decided pairs cannot exclude
a small effect, and the traps are this session's own construction rather than a
published benchmark.
