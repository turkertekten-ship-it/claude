---
provenance: enforced
---

# Chunking strategy for the oodarag corpus

Produced by routing [`chunking-advisor`](../../.claude/skills/chunking-advisor/SKILL.md)
at this corpus, as [SKILLS.md](../../SKILLS.md) directs and as finding **F-4**
of the [pipeline audit](../audits/2026-08-27-oodarag-rag-audit.md) calls for.
The skill supplies the decision tree; the document kinds below were read out of
the connectors rather than assumed.

> Framing, not a claim: this is a design, so it is a proposal until a chunker
> exists and an eval run scores it. Nothing here is measured.

## Observed — what the corpus actually contains

- Two connectors construct `RawDocument`: `github.py` at six call sites tagged `readme`, `file`, `issue`, `pull_request`, `commit` and `release`, and `web.py`, which passes markdown where the scraper produced it. [src:CORPUS-KINDS-2026-08-27]
- `models.py` documents `external_id` as "a GitHub path + sha, a YouTube video id, a chat session uuid", so transcripts and chat sessions are planned kinds with no connector yet. [src:CORPUS-KINDS-2026-08-27]
- `Chunk.context_header` is already defined as a prefix embedded and indexed with the body. [src:CORPUS-KINDS-2026-08-27]
- `util/text.py` already provides `split_markdown_sections`, `heading_path`, `split_sentences` and `estimate_tokens`. [src:CORPUS-KINDS-2026-08-27]
- `estimate_tokens` states in its own docstring that it approximates ~4 chars/token for English and ~3 for code, deliberately, to avoid a tokenizer dependency. [src:CORPUS-KINDS-2026-08-27]
- The owner's own Drive files are a corporate-transaction set — an executed SHA, a numbered investment/master/employment agreement series indexed `1.g`, `3.a`, `4.a`, tax workstreams, D&O insurance and a KVKK consent form — read as titles only. [src:DRIVE-OWNED-FILES-2026-08-27]

## The reading

The skill's tree branches on "what type of content?" — and this corpus answers
**"seven types at once"**, which is its *Mixed Content* leaf: document-aware
chunking, a different strategy per kind, parent-child preserved.

That matters more here than in a typical corpus, because these kinds differ in
the one property chunking is most sensitive to: **whether the document has an
internal structure worth respecting.** A README has headings. A commit message
has none and is usually shorter than one chunk. An issue thread has turns whose
authorship is the point. Splitting all seven on a fixed token window would
destroy the first, pad the second, and anonymise the third.

**The surprise:** the machinery for the hard case is already written.
`split_markdown_sections` returns a heading path with each section, and
`heading_path` resolves an arbitrary offset to its heading stack
[src:CORPUS-KINDS-2026-08-27] — which is precisely the input `context_header`
needs. Markdown, the largest and most structured slice, needs assembly rather
than new code.

## Per-kind strategy

| Kind | Split on | Target | Overlap | `context_header` carries |
|---|---|---|---|---|
| `readme`, web markdown | `split_markdown_sections`, then sentences if a section overruns | 800–1000 tok | 100 tok | title › heading path |
| `file` (code) | top-level definition; never mid-function | 500–1000 tok | 50 tok, and only between definitions | repo › path › enclosing symbol |
| `issue`, `pull_request` | one comment per chunk; split only if a comment overruns | whole comment | none | title › author › position in thread |
| `commit` | never split — one commit, one chunk | whole message | none | repo › sha › subject |
| `release` | heading if present, else whole | whole, else 800 tok | 100 tok | repo › tag › date |
| contract / deal document *(planned)* | clause, then section; never mid-clause | 300–500 tok | 100–150 tok | deal › document index (`3.a`) › clause path |
| transcript *(planned)* | speaker turn, merged to target | 500–800 tok | one turn | video › timestamp › speaker |
| chat session *(planned)* | message pair (user + reply) | whole exchange | none | conversation › timestamp › role |

Three rules cut across all of them:

1. **Never split below the atomic unit.** A commit message, a single comment
   and a Q&A exchange are atomic; padding them together buries the small one.
2. **Overlap only inside prose.** Overlap exists to stop a sentence being cut
   mid-thought. Between a commit and the next commit there is no thought to
   cut, and overlap there is duplicated text inflating the index.
3. **Every chunk gets a `context_header`, including the ones that were not
   split.** A whole-document chunk still needs to say what document it is.

## Contracts are a different problem, and they are in scope

The corpus above was read out of the connectors, which see GitHub and the web.
The owner's own documents are neither: they are executed transaction documents
indexed in a numbered series [src:DRIVE-OWNED-FILES-2026-08-27], and a sibling
session reports building an "M&A installation guide per book §2–§7". Any
pipeline meant to serve that work will meet a contract before it meets another
README.

Contracts break three assumptions the table above rests on:

1. **The unit of meaning is the clause, not the section.** A clause is what
   gets cited, negotiated and breached. The skill's Legal/Contracts branch is
   the tightest in its tree — 300–500 tokens, 100–150 overlap — because a
   clause separated from its qualifying sentence has changed meaning, not
   merely lost context.
2. **The document index is part of the address.** `3.a` is not decoration; it
   locates a document inside a closing set, and two agreements in one deal are
   told apart by that index long before they are told apart by their text. It
   belongs in `context_header`.
3. **Defined terms are non-local.** A contract defines a term once and uses it
   throughout, so a mid-document chunk can carry a capitalised term whose
   definition is forty pages away. Chunking cannot fix that. The header must at
   minimum name the agreement, so a retrieved clause is never attributed to the
   wrong one.

Two constraints follow that the rest of this document does not carry:

- **Parsing is the hard part here, not chunking.** These arrive as PDFs and as
  `.note` archives from a handwriting app [src:DRIVE-OWNED-FILES-2026-08-27],
  neither of which the current connectors read. This is where Docling is
  relevant: it is IBM Research's document converter, and it handles PDF layout,
  tables and reading order [src:DOCLING-IBM-2026-08-27]. It is also a heavy
  dependency, which collides directly with design principle 1 — so it belongs
  behind the connector interface as an optional extra, never in the core.
- **Redaction matters more here than anywhere else in this corpus.** These
  documents name private counterparties, and `redact_secrets` catches
  credentials, not names [src:AUDIT-OODARAG-2026-08-27]. Anything indexing this
  material needs a decision about personal data *before* the first ingest. An
  index is the thing that is hard to un-write.

## Two things to decide before writing the chunker

**Token counting.** `estimate_tokens` is a character heuristic
[src:CORPUS-KINDS-2026-08-27], and its error is systematic rather than random —
worst exactly on code, where the table above sets the tightest bounds. Tuning
sizes against it and later comparing to a provider's real count will show a
drift that looks like a retrieval regression. Keep the heuristic — the
zero-dependency rule is worth more than the precision — but record the bias
next to the numbers above, so a future eval swing is attributed correctly. This
is F-5 of the audit.

**Whether `context_header` counts against the target.** It is embedded with the
body, so it consumes real budget, and headers are long for deep heading paths.
Decide once, apply everywhere, and state it in the ADR — a chunker that counts
it for markdown and not for code will produce two incomparable size
distributions and no way to tell which one the eval is measuring.

## What this does not settle

The vendor steer noted in the skill applies: its framework and hosted-service
recommendations are not adopted here, and nothing above requires a dependency.
Sizes are the skill's defaults, adjusted for the atomicity rules — they are
starting points for the eval harness to move, not measurements. Re-open this
document with numbers once `recall@k` can be run.
