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

**Narrowed at 16:10Z.** Ten sibling branches have now pushed, holding 25-118
files each, and their *output* is readable. [src:FLEET-SYNC-2026-08-27] One
of them was read in full and its audit of this pipeline acted on.
[src:SIBLING-AUDIT-2026-08-27] Their reasoning remains unavailable: a diff
still shows what a session built, never what it was asked or why it chose.

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

**Checked, not assumed.** Every Markdown, text and YAML file on all twelve
sibling branches was searched for "the book", "kitap" and "imb". No match.
[src:FLEET-SYNC-2026-08-27] A second-hand lead does exist — a sibling reports
the owner's Drive holds an M&A transaction set [src:SIBLING-AUDIT-2026-08-27] —
which is consistent with an "M&A installation guide" but does not identify a
book, and is not treated as an answer.

---

### U-4 — What "imb youtube" designates — ANSWERED SECOND-HAND

**Unknown:** the `RAG system and data pipeline` goal names "imb youtube" as a
data source. The expansion of "imb" is not established.

**Why:** it appears only in that session's goal string, with no accompanying
definition, and this session did not reach the source.

**Resolves when:** the owner expands the term, or that session commits a
resolved source list.

**Answered, second-hand.** The session whose goal string contains "imb youtube"
has committed `corpus/ibm-technology/manifest.json` — a manifest of videos
attributed to the **IBM Technology** YouTube channel, built for its YouTube
connector. [src:IBM-TECHNOLOGY-CORPUS-2026-08-27] Read as a transposition,
"imb" is "ibm", and that session acted on the string that way.

**Why this is not promoted to established.** It is that session's
interpretation of its own instruction, not a statement by the owner, and the
owner has not confirmed it. It is recorded here rather than in
`observations.md` for that reason. One corroborating detail: a web search run
independently here returned the same video id, `T-D1OfcDW1M`, that the manifest
lists for the RAG explainer. [src:SEARCH-IS-A-SEPARATE-PATH-2026-08-27]

**Resolves fully when:** the owner confirms the expansion, or corrects it.

**Narrowed separately:** whatever it designates, reaching YouTube from this
container is credential-gated rather than impossible for metadata — the
consumer site is refused at CONNECT while the Data API host answers and asks
for a key, and search reaches metadata that fetch cannot. See U-7 and U-8.

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

### U-7 — Whether a valid API key reaches caption *metadata* — RESOLVED

**Was unknown:** whether `captions.list` returns track metadata for a video the
caller does not own when given a *valid* API key.

**Resolved from the API's own specification.** Google's discovery document
(revision 20260825) lists the accepted OAuth scopes per method.
`videos.list`, `search.list` and `playlistItems.list` each accept
`youtube.readonly`. `captions.list` and `captions.download` accept only
`youtube.force-ssl` and `youtubepartner` — both write-grade.
[src:YOUTUBE-SCOPES-2026-08-27]

So captions have **no read-only surface at all**. That is a property of the
API's design, not of any particular key, and it settles the question without
needing one: an API key is not a supported authentication path for either
captions method. The earlier probe result — `captions.list` returning
`API_KEY_INVALID` while `captions.download` returns "API keys are not
supported" — is consistent with this: the former validates a key before
rejecting the auth *class*, the latter rejects the class first.
[src:YOUTUBE-CAPTIONS-KEYLESS-2026-08-27]

**Still not established:** what a valid `youtube.force-ssl` OAuth token
belonging to a non-owner would get from `captions.list`. That is a different
question from the one asked here, needs an OAuth flow rather than a key, and
nothing in this pipeline depends on the answer.

**Consequence for the connector:** `caption_tracks()` is documented as
key-unsupported rather than merely untested, and remains uncalled during
ingest. Caption text comes from the export directory or not at all.

---

### U-8 — Whether YouTube ingestion is wanted at the price it carries

**Unknown:** whether the owner wants YouTube ingested at all, given that it
costs a Google Cloud project, an API key held as a secret, and a daily quota.

**Why:** the goal string naming YouTube as a source establishes that it was
named, not that the owner accepted those costs. Nothing was found stating a
preference.

**Built anyway, deliberately:** `src/oodarag/ingest/youtube.py` is complete and
tested against the API's error shapes. It needs one input — `YOUTUBE_API_KEY` —
and it works. Without one it reports `auth_required` and names the remedy. The
offline path, a directory of exported caption files, needs no key and no
network.

**Resolves when:** the owner supplies a key, or says YouTube is not wanted.

**Do not:** treat the connector's existence as evidence that YouTube data is in
the corpus. Nothing has been ingested from it.
