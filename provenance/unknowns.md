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

**Update, 2026-08-27T15:02Z, session `claude/ai-system-research-3jpwda`:** in
this session the account owner asked, in his own turn, to be researched along
with where he works. That authorises a Drive read for that purpose here. It
says nothing about the earlier non-user turn, which remains unattributed; this
entry stays open on that question. [src:USER-GOAL-RESEARCH-2026-08-27]

---

### U-7 — What WAM Portföy actually manages

**Unknown:** the names, codes, sizes and portfolios of the GSYF and GYF funds
WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi A.Ş. founds and manages;
its AUM; its shareholders; and who else sits on its board.

**Why:** `wamportfoy.com` and `kap.org.tr` are both blocked by this
environment's egress proxy, so neither the firm's own site nor its primary
regulatory filing record could be read. What is established comes from search
summaries of third-party profile aggregators.
[src:EGRESS-BLOCKED-WAM-KAP-2026-08-27]

**Why it matters here:** every fund-level number in the system built on this
branch is therefore a worked example against seeded data, not a reading of the
firm's real book. Nothing downstream may present it as the latter.

**Resolves when:** the egress policy permits kap.org.tr, or the owner supplies
the fund list — a KAP export, a fund prospectus (izahname), or simply telling
the system the fund codes.

**Do not:** infer fund names from the firm's name, or fund sizes from the
firm's founding date.

---

### U-8 — The exact text of the 23 July 2026 SPK valuation decision

**Unknown:** the decision's bulletin number, its precise scope, and its
operative wording.

**Why:** it is established here only through Turkish financial press coverage
(yatirimx.com.tr, paraajansi.com.tr), which reports that exchange-traded GYF
and GSYF participation units held by investment funds must be valued at the
founder's last announced unit value rather than the exchange price, with
compliance required by 31 July 2026. The SPK bulletin itself was not retrieved.
[src:SPK-VALUATION-2026-07-23]

**Why it matters here:** this is the worked example the system uses to show
regulatory-change detection. A rule that fires on a misread of the decision is
worse than no rule, so the obligation seeded from it carries a `verify` flag
rather than being presented as settled law.

**Resolves when:** the SPK haftalık bülten for that week is read directly, or
counsel confirms the scope.

---

### U-9 — Whether any of this is wanted

**Unknown:** whether the owner wants a system of this shape at all, which of
its parts he would actually use, and what his current manual routine really is.

**Why:** the design rests on inference from a public career record, a firm
profile, and a Drive file listing. Nobody asked him what his week looks like,
what he already has, or what he has already tried and abandoned.

**Resolves when:** he says so. The design document names the specific questions
whose answers would change the build.

**Do not:** treat the adoption sequence as agreed. It is a proposal.
