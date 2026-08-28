# Unknowns register

Open questions that were **not** answered, kept here so that nothing
downstream quietly invents an answer. Each entry says what is unknown, why,
and what would resolve it.

An empty unknowns register is a red flag, not an achievement. If you close an
entry, move the resolved fact into `observations.md` with a new source id.

---

## Status at 2026-08-28

Ten entries. Seven have moved; three cannot move from here.

| Entry | Status |
|---|---|
| U-1 sibling sessions | output known from diffs, reasoning still unreadable |
| U-2 chat history before 2026-08-27 | **blocked on the owner** — needs a data export |
| U-3 "the book" | answered from diffs; the handbook itself never in reach |
| U-4 "imb youtube" | answered second-hand as IBM Technology |
| U-5 repo split | convention holding by consensus; intent still unstated |
| U-6 Drive suggestion | **blocked on the owner** — only they know who asked |
| U-7 "borris churney" | **blocked on the owner** — one word confirms or corrects it |
| U-8 tip fidelity | **closed** — all 60 checked against screenshots |
| U-9 prompt engineering | answered second-hand; underlying talks unreachable |
| U-10 post-April material | **closed for X** through 2026-08-22; Threads still out |

The blocked entries are not blocked by effort. U-2 needs a file only the owner
can export; U-6 needs a fact only they hold; U-7 needs one word from them; and
the residue of U-1 needs a transcript no tool here exposes. Every route this
container can take has been taken — web search, the reachable documentation,
five cloned repositories, 183 mirrored digests, 65 screenshots and all 24 fleet
branches — and the honest end state is that these stay open with the exact
question written down rather than closed with a plausible answer.

---

### U-1 — Contents of the sibling sessions — **OUTPUT KNOWN, REASONING NOT**

**Moved 2026-08-28.** The fleet has grown to 14 branches on `claude` and 10 on
`claude-ai`, and every one has now been read as a diff rather than as a title.
What each session *built* is recorded in `observations.md`.
[src:FLEET-DIFFS-2026-08-28]

**Still unknown, and unchanged in principle:** a diff shows what a session
produced, never what it was asked, what it tried and discarded, or why. No
transcript-reading tool was ever exposed. The sessions' own reports about their
results — test counts, mutation-catch rates, negative findings — are each
session's claims about its own work and have not been re-run here.

**Resolves when:** a transcript export is placed in `archive/` and ingested.

**Do not:** infer their contents from their titles. That rule is what this
entry has always been for, and the branch names remain as uninformative as the
session titles were.

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

### U-3 — What "the book" refers to — **SUBSTANTIALLY ANSWERED**

**Answered 2026-08-28, from diffs rather than from the owner.** Two sibling
branches, `claude/blind-testing-ooda-5o3s67` and
`claude/go-page-ultrathink-ooda-kqxvnc`, both build a Turkish system called
`mafirm/` against a document their own files name. The blind-test report on the
first is headed "Kör sınama raporu · Uluslararası M&A Hukuku Kurulum Kitabı" —
a blind-test report on an *International M&A Law Installation Handbook*.
[src:FLEET-DIFFS-2026-08-28]

**Still unknown:** the handbook itself was never in reach of this session. What
its §2–§7 require — the sections the original goal string named — is known only
through those branches' descriptions of it, which are their claims about a
document this session has not read.

**Do not:** treat the sibling branches' account of the book as the book.

---

### U-4 — What "imb youtube" designates — **ANSWERED SECOND-HAND**

**Answered 2026-08-28, from a sibling's work rather than from the owner.** The
session whose goal string carries "imb youtube" committed
`corpus/ibm-technology/manifest.json`, a manifest of videos attributed to the
**IBM Technology** YouTube channel, built for its YouTube connector. Read as a
transposition, "imb" is "ibm", and that session acted on the string that way.
[src:IBM-MANIFEST-2026-08-28]

**Why this is not promoted to established:** it is one session's reading of its
own instruction, not the owner's word. Another sibling reached the same
conclusion independently, which raises confidence without changing its kind.

**Worth noting for its own sake:** that manifest refuses to attach summaries to
videos whose captions it could never fetch, on the stated grounds that doing so
"would produce a citation that looks verbatim and is not". That is the same rule
this repository enforces, arrived at separately. [src:IBM-MANIFEST-2026-08-28]

**Resolves fully when:** the owner confirms the expansion, or corrects it.

---

### U-5 — Intended relationship between the two repositories — **CONVENTION HOLDING, INTENT STILL UNSTATED**

**Unknown:** why the account has both `claude` and `claude-ai`, and what belongs
in each.

**Why it stays open:** the owner has still not stated the split. Nothing has
changed about that.

**What the fleet now shows.** Nine of the ten branches on `claude-ai` each add a
single commit editing only `CLAUDE.md` — the interim pointer convention,
followed independently by nine sessions that never coordinated.
[src:FLEET-DIFFS-2026-08-28]

One does not: `claude-ai`'s `rag-system-data-pipeline-rdkde9` roots at an
unrelated commit and installs a **second, self-contained operating doctrine**
there, with its own protocol documents, skills and workflows.
[src:FLEET-DIFFS-2026-08-28]

> So the convention is being followed by consensus and broken by one branch.
> That is evidence about what sessions *do*, not about what the owner wants,
> and it is not promoted into an answer. Nine sessions agreeing is nine
> sessions making the same interim decision this file already recorded.

**Resolves when:** the owner states the split.

**Interim convention, unchanged:** doctrine and shared tooling live in `claude`;
`claude-ai` points at them.

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

### U-9 — What Cherny said about prompt engineering — **ANSWERED, SECOND-HAND**

**Answered 2026-08-28.** The headline was not a distortion, but it was also not
a contradiction of this corpus. His position, as reported: prompt engineering is
largely not important, "people tend to overthink it a little bit", and
over-specifying is unnecessary — coupled with "I don't prompt Claude anymore. I
have loops running that prompt Claude and figuring out what to do. My job is to
write loops." [src:CHERNY-LOOPS-2026-08-28] [src:LOOP-ENGINEERING-KB-2026-08-28]

**Why it does not contradict the corpus:** the same reporting has him
prescribing the empirical method this corpus already carries — give the model a
task that is too hard, give it tools to verify the work, see where it struggles,
then fix that with better prompting, a skill, or an MCP. The claim is that
polishing prompts is the wrong lever, not that specificity is worthless.

**Still unknown:** the exact wording and its context. Every source for it is a
transcript or article this session could not fetch; the talks it traces to are
on YouTube and unreachable. The tension flagged when this entry was opened is
resolved only to the standard of second-hand reporting.

---

### U-10 — Cherny material published after 2026-04-16 — **CLOSED for X, open for Threads**

**Resolved 2026-08-28.** A sweep of 183 mirrored X digests on GitHub recovered
13 of his posts spanning 2026-03-13 to **2026-08-22** — five days before this
capture. The corpus is no longer stale, and the recovered material is recorded
in `observations.md` and the corpus. [src:CHERNY-X-SWEEP-2026-08-28]

**Still open, narrowly:** the Threads post of 2025-12-27 claiming 259 PRs in 30
days was not recovered. `threads.com` is blocked, no mirror of it was found, and
a tertiary source quotes it as verbatim without this session being able to check
that. [src:LOOP-ENGINEERING-KB-2026-08-28]

**Grading, unchanged:** everything recovered came through third-party scrapes
mirrored on GitHub, not from x.com. The records carry per-post ids, timestamps
and engagement counts consistent with real captures, and the two independent
mirrors agree with the bundled screenshots wherever all three were compared —
but none of it has been checked against the source.

**Resolves fully when:** `x.com` or `threads.com` become reachable.
