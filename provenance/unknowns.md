# Unknowns register

Open questions that were **not** answered, kept here so that nothing
downstream quietly invents an answer. Each entry says what is unknown, why,
and what would resolve it.

An empty unknowns register is a red flag, not an achievement. If you close an
entry, move the resolved fact into `observations.md` with a new source id.

---

### U-1 — RESOLVED: the three sibling branches were pushed and read

**Answered** 2026-08-28. All three sessions the entry named have pushed, and
their diffs have been read. [src:SIBLING-BRANCHES-READ-2026-08-28]

- `RAG system and data pipeline` built an end-to-end retrieval system on the
  shared `oodarag` root: a runnable capability prober, a citation contract that
  checks answers against retrieved chunks, a contamination detector, a literal
  OODA loop, and an IBM Technology video manifest whose entries ingest as
  metadata-only because youtube.com was unreachable.
- `Blind testing and OODA analysis` installed a Turkish M&A legal practice from
  a book, then blind-tested the installation, then patched it while keeping the
  unpatched original. Its own root commit is unrelated to this branch's.
- `Go page review and ultrathink OODA` is a second, independent installation of
  the same book, with gate hooks, an audit script and a limits declaration.

**What that does not license.** The detailed reading was delegated and is
second-hand; what this session verified itself is listed in the source entry.
Those branches' test counts are their own reports of their own runs and were
not reproduced here. The entry's own warning still applies in a new form: a
delegate's summary of a diff is not the diff.

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

### U-3 — RESOLVED: the book is identified, though its text is not held here

**Answered** 2026-08-28. Two sibling branches install the same document and both
name it: *Uluslararası M&A Hukuku · Kurulum Kitabı*, Arel Barzilay, Sürüm 1.0
(`go-page`, `mafirm/KURULUM.md`), also given as "RePie Arel M&A Avukat Claude
Kurulum Kitabı", Sürüm 1.0, 27 Ağustos 2026 (`blind-testing`, `README.md`).
Nineteen sections, §0–§19. [src:BOOK-IDENTIFIED-2026-08-28]

The two title strings reconcile rather than conflict: blind-testing's own
heading uses go-page's title and its body gives the longer form.

**Still not held:** the book's text is committed nowhere. The nearest thing is
`mafirm/KITAP-ERRATA.md`, which is corrections *for* it. So the earlier session
summaries — "M&A installation guide per book §2–§7", "encoding book
corrections" — now resolve to a named document with a known structure, and its
contents remain unread by this session.

### U-4 — Advanced, not closed: "imb" was read as IBM, never defined

**Unknown still:** what "imb youtube" designates, as a statement rather than an
inference.

**What is now established:** the session whose goal string contains the phrase
built `corpus/ibm-technology/manifest.json` — a manifest of IBM Technology
YouTube videos, with each entry's channel attribution graded
`search_confirmed` or `search_listed`, and youtube.com recorded as unreachable
so no captions were fetched. The string "imb" appears nowhere on that branch,
and no commit states an expansion. [src:IMB-IBM-BEHAVIOUR-2026-08-28]

**Why it stays open:** acting on a reading is not stating one. That session
evidently read "imb" as "IBM"; it did not record that it had. The distinction
matters here more than usual, because the whole point of this register is that
a plausible expansion adopted silently is indistinguishable from a fact.

**Resolves when:** the owner expands the term.

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

### U-7 — Substantially answered from the playground's own client code

**What is now established.** The UI is still behind authentication and nobody
here has seen it, but `platform.claude.com` serves the playground's JavaScript
to a logged-out browser, and it names what the app implements: a tool-definition
editor, a simple/advanced field split, cache-breakpoint placement, templates,
and full run inspection. There is no variable templating and no evals —
negative evidence agreeing with the sunset note — and saved prompts exist only
as browser-local versioned history. [src:PLAYGROUND-CLIENT-CODE-2026-08-28]

**Still unknown:** whether a token counter, a comparison mode, or a code-export
control exists. Those were absent from the logged-out bundle, which is not the
same as absent from the product.

**The distinction that keeps this open rather than closed:** shipped code is
evidence of implementation, not of presentation. A control can exist in a store
and never reach a screen.

**Resolves when:** someone signed in describes or screenshots it, or the Help
Center article becomes reachable.

### U-8 — RESOLVED: the figures match the canonical paper

**Answered** 2026-08-28. The paper's arXiv LaTeX source was retrieved
byte-identical from three unrelated repositories and cross-checked against two
independent PDF extractions. Every figure this repository quotes matches.
[src:MT-BENCH-CANONICAL-2026-08-28]

**And it corrected the framing, not the numbers.** Two qualifiers were missing:
the consistency figures come from a deliberately hard setup rather than being
general swap-consistency rates, and Claude-v1's 23.8% is partly a *name* bias
that renaming moves to 56.2%. `docs/parity.md` now carries both — which is why
"the numbers were right" was not a sufficient answer to this entry.

### U-9 — RESOLVED: powered, replicated on a second family, still null

The power half is answered. `suites/fabrication-powered.yaml` extended the
suite to 40 cases, raised `repeats` to 3, and pre-registered a paired,
family-clustered analysis before the run. The interval spans zero
[src:POWERED-FAB-2026-08-28], and still spans zero after every failing run was
audited by hand [src:POWERED-FAB-AUDIT-2026-08-28]. Moved to
`observations.md` under "the adequately powered test, pre-registered".

The stratified half of that analysis was reported before it had actually run;
repaired, both strata span zero — tuned −0.0256 [−0.1000, +0.0400] and
held-out −0.0952 [−0.2667, +0.0000], p = 0.25 on fourteen cases.
[src:STRATIFICATION-NEVER-RAN-2026-08-28]

The transfer half is answered too. The same forty traps and the same two arms
ran on a second model family: -0.0917, 95% CI [-0.2045, +0.0000], sign test
p = 0.1250, with the operating prompt at 120/120 and a plain assistant at
109/120 [src:SONNET-VALID-2026-08-28]. Negative again, interval containing zero
again. The first attempt at that run was void — one arm answered with attempted
tool calls in 47 of 120 runs — and is kept as
[src:SONNET-RUN-VOID-2026-08-28] because the void is the more useful artifact.

**What this now rests on:** the prompt does not buy its trap score by declining
everything. On forty questions where declining would be wrong, both arms
answered 80 of 80 [src:NO-OVER-REFUSAL-2026-08-28]. Before that control existed,
every fabrication result here was compatible with a prompt that simply refuses.

**Still unknown, and narrower:** why so few cases discriminate. Thirty-six of
forty were ties on the second family, and four discordant cases against zero
floors the two-sided sign test at p = 0.125 — the experiment is limited by how
many cases separate the arms, not by how many were run.

**Resolves when:** a suite is built whose cases discriminate more often, or the
existing traps are made harder. More repeats will not do it.

**Do not:** report any of these point estimates as an effect. Eight runs have
produced a negative point estimate and eight intervals have contained zero;
quoting the point without the interval turns a null into a finding, which is
the specific failure this file exists to prevent.

---

### U-10 — RESOLVED: the operating prompt does not measurably reduce fabrication

Answered on 2026-08-27 by `suites/hard-traps.yaml`. Moved to
`observations.md` under "the hard traps". Kept here as a pointer because the
question was open long enough to be cited.

**The answer:** on traps hard enough to make both arms fail, no measurable
difference. What remains open is narrower: twelve decided pairs cannot exclude
a small effect, and the traps are this session's own construction rather than a
published benchmark.

---

### U-11 — What "parity" should mean, now that its target is withdrawn

**Asked and left to me.** The owner was offered three choices — accept the
seventeen executable acceptance criteria as the definition, name what they miss,
narrow to the API surface, or aim past the playground entirely — and expressed
no preference on any of them. Also offered: whether to accept the fabrication
null or fund harder traps, and whether to leave the two credential-blocked rows
documented or supply a key. No preference on those either.

**So these are my decisions, not the owner's, and they are recorded here rather
than in `observations.md` because "the owner declined to choose" is not evidence
that the choice was right.**

1. `tools/acceptance_check.py` is the working definition of done: 15 pass,
   0 fail, 2 blocked. The two blocked rows are a withdrawn product and a
   missing credential.
2. The fabrication question is answered as far as this instrument can answer
   it. Eight runs, two model families, every interval containing zero. No
   further spend on it.
3. The two API-form rows stay BLOCKED and documented rather than deleted,
   because deleting them would make the matrix green by hiding a real
   difference.

**Resolves when:** the owner states what they actually wanted, at which point
any of the three may turn out to be wrong. Each is cheap to revisit: the
criteria are a file, the suites still run, and a key would move two rows.

**Do not:** describe the goal as "satisfied" without naming which definition
was used. Under (1) it is met; under a reading that requires the retired UI it
cannot be met by anyone.
