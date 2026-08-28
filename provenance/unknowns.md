# Unknowns register

Open questions that were **not** answered, kept here so that nothing
downstream quietly invents an answer. Each entry says what is unknown, why,
and what would resolve it.

An empty unknowns register is a red flag, not an achievement. If you close an
entry, move the resolved fact into `observations.md` with a new source id.

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
