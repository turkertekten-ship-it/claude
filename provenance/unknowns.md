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

## Why the ids below jump from U-6 to AIR-1

U-1 to U-6 came across with the doctrine from
`origin/claude/review-chat-archive-zrynr4` and keep their ids.

Everything this branch opened is prefixed `AIR-` (AI system Research), because
plain `U-n` is not unique across the fleet. Reading the other branches' registers
directly showed `U-7` in use for *What the Console playground actually offers*,
*Whether "borris churney" designates Boris Cherny*, *What "firms" means in this
session's goal*, and *Whether a YouTube Data API key is available*; `U-8` and
`U-10` are similarly overloaded, and one branch carries two different `U-6`
entries in a single file. [src:FLEET-UNKNOWN-ID-COLLISION-2026-08-28]

A merge of two such registers does not conflict — it appends, and two unrelated
questions end up sharing an id. The register then reads as though someone
answered a question nobody asked. Prefixing is the cheapest fix that survives a
merge, and it costs nothing to adopt.

---

### AIR-1 — What WAM Portföy actually manages

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

### AIR-2 — The exact text of the 23 July 2026 SPK valuation decision

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

**Advanced, not closed.** The decision now has a number and a bulletin — 23/07/2026
no. 45/1359, SPK bulletin 2026/38 [src:SPK-BULLETIN-45-1359-2026-08-28] — but the
operative wording is still unread. The GitHub mirror of mevzuat.spk.gov.tr that
closed AIR-4 and AIR-5 cannot close this one: its snapshot is dated 2026-06-14
and contains no document later than that, so a July decision is simply absent.
[src:SPK-MIRROR-GITHUB-2026-08-28] The corpus also carries tebliğs, rehbers and
kurul kararları but no weekly bulletins at all.

**Resolves when:** the SPK haftalık bülten 2026/38 is read directly, the mirror
is refreshed past July 2026, or counsel confirms the scope.

---

### AIR-3 — Whether any of this is wanted

**Unknown:** whether the owner wants a system of this shape at all, which of
its parts he would actually use, and what his current manual routine really is.

**Why:** the design rests on inference from a public career record, a firm
profile, and a Drive file listing. Nobody asked him what his week looks like,
what he already has, or what he has already tried and abandoned.

**Resolves when:** he says so. The design document names the specific questions
whose answers would change the build.

**Do not:** treat the adoption sequence as agreed. It is a proposal.

---

### AIR-4 — RESOLVED: VII-128.10 binds a portföy yönetim şirketi, with no size threshold

**Was unknown:** whether the requirement that primary and secondary information
systems sit inside Turkey applies to a PYŞ of WAM's size, and whether any
exception or transition regime exists.

**Resolved from the tebliğ's own text**, reached through a GitHub mirror of
mevzuat.spk.gov.tr after every Turkish host was denied at the gateway.
[src:SPK-VII-128-10-PRIMARY-2026-08-28] [src:SPK-MIRROR-GITHUB-2026-08-28]

- **MADDE 2(1)(g)** puts *sermaye piyasası kurumları* in scope, the category a
  portföy yönetim şirketi belongs to.
- **MADDE 27(1)**: "Kurum, Kuruluş ve Ortaklıkların birincil ve ikincil
  sistemlerini yurt içinde bulundurmaları zorunludur."
- **MADDE 30(3)** is the only exemption from 27(1), and it covers publicly held
  companies with no IS-audit obligation under III-62.2 — not a PYŞ.
- **MADDE 30(6)** lets the Board grant exemptions case by case, so a
  firm-specific one is possible but must be applied for.
- **MADDE 33**: in force 30/6/2025. **GEÇİCİ MADDE 1(2)**: non-crypto
  institutions had to comply with everything except 29(3) by **31/12/2025**.
- There is no size or AUM threshold anywhere in the tebliğ.

**What this settles for the design:** building rather than buying is the
compliance-correct answer here, not a budget compromise — a US-hosted system of
record is not lawfully available to this firm.

**Residual caveat, and it is small:** the text came from a third-party mirror
snapshotted 2026-06-14, not from SPK. Counsel should confirm the wording. The
question has moved from "does this bind us" to "is this copy faithful".

---

### AIR-5 — SUBSTANTIALLY RESOLVED: the fund exemption exists, in a different decision than reported

**Was unknown:** whether SPK decision 16.02.2024 no. 11/255, reported to exempt
investment funds from inflation accounting, is still in force for 2026.

**The premise was wrong.** Decision 11/255 adds *Sorumlu Yönetim İlkeleri* —
stewardship principles — to the Yatırım Fonlarına İlişkin Rehber as article 13.
It says nothing about inflation accounting. Every secondary source consulted
said otherwise, and this session repeated them.
[src:SPK-11-255-MISATTRIBUTION-2026-08-28]

**The exemption is real and comes from elsewhere**, both read from primary text:
[src:SPK-TMS29-PRIMARY-2026-08-28]

- **Decision 81/1820 of 28/12/2023(a)**: issuers and *sermaye piyasası
  kurumları* apply TMS 29 from the annual reports for periods ending 31.12.2023.
  That is the management company.
- **Decision 14/382 of 07/03/2024(A)**: "yatırım fonlarının TMS/TFRS uyarınca
  hazırlayacakları finansal tablolarında enflasyon muhasebesi uygulanmamasına" —
  investment funds do not apply inflation accounting.

**So the invariant the design rests on holds**: fund figures nominal,
management-company figures restated, never added without a flag.

**Still open, narrowly:** whether any decision after 2026-06-14 changed it. The
mirror's snapshot predates that, and SPK's own site is denied here. The
restatement basis is an explicit per-entity field with no default, so a change
is a configuration edit rather than a rewrite.

**Resolves when:** a bulletin later than June 2026 is read, or the auditor
confirms the 2026 treatment.
