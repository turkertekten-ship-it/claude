"""Split documents into retrievable chunks that still know where they came from.

Fixed-size character windows are the default in most RAG code and they are the
reason so many retrieved passages are useless: they cut mid-sentence, they
split a table from its header, and they strip the one piece of context that
makes a passage interpretable — which document and which section it is from.

Two decisions here address that:

  - **Split on structure first, pack second.** Markdown headings are a real
    outline the author already wrote. Sections become the primary boundary;
    only oversized sections get packed into overlapping sentence windows.
  - **Every chunk carries a context header.** A deterministic prefix naming the
    document title and heading path is stored with the chunk and indexed with
    it. This is the cheap form of contextual retrieval: no model call, no
    per-chunk cost, and it means a chunk reading "it depends on the chunk size"
    is retrievable as being about the thing its section was about.

Overlap is measured in sentences rather than characters so a window boundary
never lands inside a sentence.

**One strategy does not fit the corpus.** This pipeline ingests at least seven
document kinds, and they differ in the property chunking is most sensitive to:
whether the document has an internal structure worth respecting. A README has
headings. A commit message has none and is usually shorter than one chunk. An
issue comment has an author whose identity is the point. Splitting all of them
on a fixed window destroys the first, pads the second, and anonymises the third.

So chunking branches on kind, under three rules:

1. **Never split below the atomic unit.** A commit message, a single comment
   and a caption cue are atomic. Packing several together buries the small one;
   splitting one in half destroys it.
2. **Overlap only inside prose.** Overlap exists so a sentence is not cut
   mid-thought. Between one commit and the next there is no thought to cut, and
   overlap there is duplicated text inflating the index for nothing.
3. **Every chunk carries a context header, including the ones never split.** A
   whole-document chunk still has to say what document it is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from oodarag.models import Chunk, Document
from oodarag.util.hashing import stable_id
from oodarag.util.text import (
    estimate_tokens,
    split_markdown_sections,
    split_sentences,
)


@dataclass(slots=True)
class KindPolicy:
    """How one document kind is split.

    `atomic` means the document is one chunk unless it exceeds `max_tokens`,
    at which point it is split rather than truncated — losing the tail of a
    long issue comment is worse than splitting it.
    """

    target_tokens: int
    max_tokens: int
    overlap_sentences: int
    """Minimum sentences of overlap. The effective count is whichever is
    larger, this or `overlap_ratio` of the target — so a bigger chunk gets
    proportionally more overlap rather than the same single sentence."""
    atomic: bool = False
    split_on_definitions: bool = False
    label: str = ""


#: Per-kind policies. `kind` comes from a document's metadata, falling back to
#: its `source_system`. Targets differ because the natural unit differs: a
#: markdown section is larger than a clause and smaller than a commit.
KIND_POLICIES: dict[str, KindPolicy] = {
    # Prose with real structure: split on headings, overlap between sentences.
    "readme":     KindPolicy(320, 512, 1, label="markdown"),
    "file":       KindPolicy(320, 640, 0, split_on_definitions=True, label="code"),
    "web":        KindPolicy(320, 512, 1, label="markdown"),
    "skill":      KindPolicy(320, 512, 1, label="markdown"),
    # Atomic: one unit of meaning, no overlap, never packed with a neighbour.
    "commit":     KindPolicy(400, 800, 0, atomic=True, label="atomic"),
    "issue":      KindPolicy(400, 800, 0, atomic=True, label="atomic"),
    "pull_request": KindPolicy(400, 800, 0, atomic=True, label="atomic"),
    "release":    KindPolicy(400, 800, 0, atomic=True, label="atomic"),
    # A transcript's turns are its structure; overlap by one turn, not one
    # sentence, because a caption cue is already a fragment.
    "video":      KindPolicy(500, 900, 1, label="transcript"),
}

DEFAULT_POLICY = KindPolicy(320, 512, 1, label="default")


#: Suffixes whose content is prose even though the connector calls them files.
PROSE_SUFFIXES = frozenset({
    ".md", ".markdown", ".rst", ".txt", ".adoc", ".org",
})

#: Caption files. Prose, but with turn structure rather than headings, so they
#: take the transcript policy rather than the markdown one.
TRANSCRIPT_SUFFIXES = frozenset({".vtt", ".srt"})


def policy_for(doc: Document) -> KindPolicy:
    """Choose a policy from the document's kind, refined by its file type.

    `kind` alone is not enough. Both file connectors label every local or
    repository file `file`, markdown included, so routing on `kind` sends a
    README through the code strategy — no overlap, split on definitions it
    does not have. The suffix is the thing that actually distinguishes prose
    from source, so it is consulted first for anything file-shaped.
    """
    kind = str(doc.metadata.get("kind", "")).lower()

    if kind == "file" or (not kind and doc.source_system in ("file", "github")):
        suffix = _suffix_of(doc)
        if suffix in TRANSCRIPT_SUFFIXES:
            return KIND_POLICIES["video"]
        if suffix in PROSE_SUFFIXES:
            return KIND_POLICIES["readme"]
        return KIND_POLICIES["file"]

    if kind in KIND_POLICIES:
        return KIND_POLICIES[kind]
    source = (doc.source_system or "").lower()
    if source in KIND_POLICIES:
        return KIND_POLICIES[source]
    if source == "youtube":
        return KIND_POLICIES["video"]
    return DEFAULT_POLICY


def _suffix_of(doc: Document) -> str:
    """The document's file suffix, from metadata or failing that its identifiers."""
    if suffix := str(doc.metadata.get("suffix", "")).lower():
        return suffix
    for candidate in (str(doc.metadata.get("path", "")), doc.external_id, doc.uri, doc.title):
        base = candidate.rsplit("/", 1)[-1]
        if "." in base:
            return "." + base.rsplit(".", 1)[-1].lower()
    return ""


@dataclass(slots=True)
class ChunkConfig:
    """Sizing policy.

    `target_tokens` at 320 keeps a chunk small enough that several fit in a
    prompt alongside an answer, and large enough to hold a complete argument;
    `max_tokens` gives packing room before a hard split. `overlap_sentences`
    of 1 is the minimum that keeps a claim and its immediately preceding
    referent together, which is the case overlap exists to protect.
    """

    target_tokens: int = 320
    max_tokens: int = 512
    min_tokens: int = 40
    overlap_sentences: int = 1
    overlap_ratio: float = 0.15
    """Overlap as a fraction of `target_tokens`. Fixed-count overlap does not
    scale: one sentence is a reasonable cushion for a 60-token chunk and a
    token gesture at 320, which measured out at 6.9% — below the 10-20% band
    where overlap actually protects a claim split across a boundary. The
    sentence count is derived from this at pack time. Set to 0 to fall back to
    `overlap_sentences` alone."""
    include_header_in_text: bool = False
    per_kind: bool = True
    """Branch on document kind. Turn off to force one strategy over everything,
    which is useful for an A/B eval run and wrong the rest of the time."""

    def resolved(self, policy: KindPolicy) -> ChunkConfig:
        """This config with the policy's sizing applied where the caller was silent.

        A field the caller left at its default is the caller expressing no
        opinion, and the policy fills it. A field the caller changed is an
        instruction, and it wins: someone who passes `target_tokens=800` has
        said what they want, and quietly substituting 320 makes the parameter a
        lie. This is what lets an eval sweep vary one dimension while per-kind
        routing still handles the rest.
        """
        if not self.per_kind:
            return self
        defaults = ChunkConfig()
        chosen = lambda name, from_policy: (  # noqa: E731
            getattr(self, name)
            if getattr(self, name) != getattr(defaults, name)
            else from_policy
        )
        overlap_sentences = chosen("overlap_sentences", policy.overlap_sentences)
        return ChunkConfig(
            target_tokens=chosen("target_tokens", policy.target_tokens),
            max_tokens=chosen("max_tokens", policy.max_tokens),
            min_tokens=self.min_tokens,
            overlap_sentences=overlap_sentences,
            # An atomic kind takes no overlap even when a ratio is configured:
            # between one commit and the next there is no thought to cut.
            overlap_ratio=0.0 if policy.overlap_sentences == 0 else self.overlap_ratio,
            include_header_in_text=self.include_header_in_text,
            per_kind=True,
        )


def chunk_document(doc: Document, config: ChunkConfig | None = None) -> list[Chunk]:
    """Split one document. Returns [] only for a document with no text."""
    base = config or ChunkConfig()
    policy = policy_for(doc)
    cfg = base.resolved(policy)
    text = doc.text.strip()
    if not text:
        return []

    # An atomic document is one unit of meaning. It becomes one chunk unless it
    # is genuinely too large, in which case splitting beats losing the tail.
    # `per_kind=False` disables the branch entirely, so an A/B run really does
    # compare one strategy against the other rather than a partial mix.
    atomic = base.per_kind and policy.atomic
    if atomic and estimate_tokens(text) <= policy.max_tokens:
        header = _context_header(doc, [])
        return [_make_chunk(doc, header, text, 0, len(text), 0, [], cfg)]

    sections = split_markdown_sections(text) or [([], text, 0)]
    chunks: list[Chunk] = []

    for headings, body, offset in sections:
        body = body.strip()
        if not body:
            continue
        header = _context_header(doc, headings)
        for piece, start, end in _pack(body, cfg, policy):
            chunks.append(_make_chunk(doc, header, piece, offset + start, offset + end,
                                      len(chunks), headings, cfg))

    if not chunks:  # a document that is entirely whitespace-separated fragments
        header = _context_header(doc, [])
        chunks.append(_make_chunk(doc, header, text, 0, len(text), 0, [], cfg))

    # Runts are folded only where packing is meaningful. For an atomic kind,
    # two short units are two units, and merging them buries the smaller.
    merged = chunks if atomic else _merge_runts(chunks, cfg)
    for i, c in enumerate(merged):
        c.ordinal = i
    return merged


def _make_chunk(doc: Document, header: str, text: str, start: int, end: int,
                ordinal: int, headings: list[str], cfg: ChunkConfig) -> Chunk:
    body = f"{header}\n\n{text}" if cfg.include_header_in_text else text
    return Chunk(
        chunk_id=stable_id(doc.doc_id, str(ordinal), text[:120]),
        doc_id=doc.doc_id,
        ordinal=ordinal,
        text=body,
        context_header=header,
        char_start=start,
        char_end=end,
        metadata={
            "source_system": doc.source_system,
            "uri": doc.uri,
            "title": doc.title,
            "headings": list(headings),
        },
    )


def _context_header(doc: Document, headings: list[str]) -> str:
    """The prefix indexed with every chunk.

    Kept to one line and built only from fields already on the document, so it
    is deterministic and adds no fetch, no model call and no failure mode.
    """
    parts = [doc.title.strip()] if doc.title.strip() else []
    if headings:
        parts.append(" > ".join(h.strip() for h in headings if h.strip()))
    if doc.source_system:
        parts.append(f"({doc.source_system})")
    return " — ".join(p for p in parts if p)


#: Lines that start a top-level definition, across the languages this corpus
#: actually contains. Matched at zero indentation only: a nested `def` is part
#: of its parent, and splitting there is the "mid-function" cut to avoid.
_DEFINITION_RE = re.compile(
    r"^(?:"
    r"(?:async\s+)?def\s+\w+"                 # python
    r"|class\s+\w+"                            # python, java, c++, ts
    r"|(?:export\s+)?(?:async\s+)?function\s+\w+"   # javascript, typescript
    r"|(?:export\s+)?(?:default\s+)?(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?\("
    r"|func\s+(?:\([^)]*\)\s*)?\w+"          # go
    r"|(?:pub\s+)?(?:async\s+)?fn\s+\w+"      # rust
    r"|(?:public|private|protected|static|final|\s)*[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*\{"  # java
    r"|type\s+\w+"                             # go, typescript
    r"|interface\s+\w+"                        # typescript, java
    r")",
    re.MULTILINE,
)


#: A member of a class: an indented definition. Used only when a top-level
#: definition is itself too large, so an oversized class splits on its methods
#: rather than on sentences — a sentence boundary inside a method body is the
#: "mid-function" cut the whole strategy exists to avoid.
#:
#: The indentation is matched by exactly one `[ \t]+`, with no second
#: whitespace run behind an optional group. An earlier version read
#: `[ \t]+(?:decorators)?[ \t]*`, and those two runs could divide one line of
#: indentation between them in quadratically many ways: 16,000 leading spaces
#: with no definition after them took 11 seconds, growing fourfold per
#: doubling. A 400 KB file — inside what the GitHub connector accepts — would
#: have been hours of CPU for a single document, plantable by any repository
#: the pipeline ingests. Decorators are attached in `_split_members` instead,
#: by a backward line scan that cannot backtrack.
_MEMBER_RE = re.compile(
    r"^[ \t]+(?:async[ \t]+)?(?:def|class|fn)[ \t]+\w+",
    re.MULTILINE,
)

#: A decorator line, matched on its own rather than inside the member pattern.
_DECORATOR_RE = re.compile(r"^[ \t]*@[\w.]+")


def _decorator_start(body: str, start: int) -> int:
    """Walk back over any decorator lines immediately above `start`.

    A chunk beginning `@property` with the `def` it applies to in the next
    chunk describes nothing, and one beginning at the `def` with its decorators
    stranded above is just as wrong. This is a linear backward scan over lines,
    so it cannot reintroduce the backtracking the pattern above was rewritten
    to avoid.
    """
    cursor = start
    while cursor > 0:
        line_start = body.rfind("\n", 0, cursor - 1) + 1
        if not _DECORATOR_RE.match(body[line_start:cursor].rstrip("\n")):
            break
        cursor = line_start
    return cursor


def _split_members(body: str) -> list[tuple[str, int, int]]:
    """Cut an oversized definition at its member boundaries.

    Decorators stay with the member they decorate: a chunk that begins
    `@property` and ends before the `def` it applies to describes nothing.
    """
    starts: list[int] = []
    for m in _MEMBER_RE.finditer(body):
        # Rewind to the start of the decorator block, not the def line.
        start = _decorator_start(body, m.start())
        if not starts or start > starts[-1]:
            starts.append(start)
    if len(starts) < 2:
        return []
    if starts[0] > 0:
        starts.insert(0, 0)   # the class header and its attributes lead
    bounds = starts + [len(body)]
    out: list[tuple[str, int, int]] = []
    for start, end in zip(bounds, bounds[1:], strict=False):
        piece = body[start:end].strip()
        if piece:
            out.append((piece, start, end))
    return out


def _split_definitions(body: str) -> list[tuple[str, int, int]]:
    """Cut a source file at top-level definition boundaries.

    A function is the unit a reader cites and the unit an answer needs whole.
    Cutting one in half produces two chunks that each describe nothing: the
    first has a signature with no behaviour, the second behaviour with no name.

    Everything before the first definition — imports, module docstring, module
    constants — becomes its own leading chunk, because it is genuinely a
    different kind of content from the definitions that follow.
    """
    starts = [m.start() for m in _DEFINITION_RE.finditer(body)]
    if not starts:
        return []
    if starts[0] > 0:
        starts.insert(0, 0)   # the module preamble is its own unit
    bounds = starts + [len(body)]
    out: list[tuple[str, int, int]] = []
    for start, end in zip(bounds, bounds[1:], strict=False):
        piece = body[start:end].strip()
        if piece:
            out.append((piece, start, end))
    return out


def _pack_definitions(body: str, cfg: ChunkConfig) -> list[tuple[str, int, int]]:
    """Group definitions up to the target, never splitting one that fits.

    Small helpers are packed together — twenty one-line functions as twenty
    chunks is noise — but a definition is only ever split when it alone
    exceeds the hard cap, and then by sentence so the cut lands at a comment
    or statement boundary rather than mid-expression.
    """
    units = _split_definitions(body)
    if not units:
        return _pack_prose(body, cfg)

    out: list[tuple[str, int, int]] = []
    buffer: list[tuple[str, int, int]] = []
    tokens = 0

    def flush() -> None:
        if not buffer:
            return
        start, end = buffer[0][1], buffer[-1][2]
        out.append((body[start:end].strip(), start, end))
        buffer.clear()

    for piece, start, end in units:
        cost = estimate_tokens(piece)
        if cost > cfg.max_tokens:
            flush()
            tokens = 0
            # A definition over the cap splits on its members first, and only
            # falls back to sentences when it has none to split on.
            members = _split_members(piece)
            if members:
                buffered: list[tuple[str, int, int]] = []
                running = 0
                for sub, s_off, e_off in members:
                    sub_cost = estimate_tokens(sub)
                    if buffered and running + sub_cost > cfg.target_tokens:
                        first, last = buffered[0], buffered[-1]
                        out.append((piece[first[1]:last[2]].strip(),
                                    start + first[1], start + last[2]))
                        buffered, running = [], 0
                    buffered.append((sub, s_off, e_off))
                    running += sub_cost
                if buffered:
                    first, last = buffered[0], buffered[-1]
                    out.append((piece[first[1]:last[2]].strip(),
                                start + first[1], start + last[2]))
            else:
                for sub, s_off, e_off in _pack_prose(piece, cfg):
                    out.append((sub, start + s_off, start + e_off))
            continue
        if buffer and tokens + cost > cfg.target_tokens:
            flush()
            tokens = 0
        buffer.append((piece, start, end))
        tokens += cost
    flush()
    return out


def _pack(body: str, cfg: ChunkConfig, policy: KindPolicy | None = None) -> list[tuple[str, int, int]]:
    """Pack a section into windows of about `target_tokens`, overlapping.

    A section that already fits is emitted whole: splitting something that fits
    only makes each half less interpretable.
    """
    if policy is not None and policy.split_on_definitions and _DEFINITION_RE.search(body):
        return _pack_definitions(body, cfg)
    return _pack_prose(body, cfg)


def _pack_prose(body: str, cfg: ChunkConfig) -> list[tuple[str, int, int]]:
    """Pack prose into overlapping sentence windows."""
    if estimate_tokens(body) <= cfg.max_tokens:
        return [(body, 0, len(body))]

    sentences = split_sentences(body)
    if not sentences:
        return [(body, 0, len(body))]

    overlap_n = _overlap_sentences(sentences, cfg)
    spans = _locate(body, sentences)
    out: list[tuple[str, int, int]] = []
    window: list[int] = []
    tokens = 0

    for i, sentence in enumerate(sentences):
        cost = estimate_tokens(sentence)
        if window and tokens + cost > cfg.target_tokens:
            out.append(_emit(body, spans, window))
            keep = window[-overlap_n:] if overlap_n else []
            window = list(keep)
            tokens = sum(estimate_tokens(sentences[j]) for j in window)
        window.append(i)
        tokens += cost
        # A single sentence longer than the hard cap is emitted alone rather
        # than being cut mid-clause; a very long sentence is still one claim.
        if tokens >= cfg.max_tokens:
            out.append(_emit(body, spans, window))
            window, tokens = [], 0

    if window:
        out.append(_emit(body, spans, window))
    return out


def _overlap_sentences(sentences: list[str], cfg: ChunkConfig) -> int:
    """How many trailing sentences to carry into the next window.

    Derived from `overlap_ratio` rather than fixed, because a fixed count does
    not scale with chunk size: one average sentence is a real cushion at 60
    tokens and a gesture at 320. Capped at a third of the target so overlap can
    never dominate the window it is protecting.
    """
    if cfg.overlap_ratio <= 0:
        return max(0, cfg.overlap_sentences)
    sample = sentences[: min(len(sentences), 24)]
    avg = max(1.0, sum(estimate_tokens(s) for s in sample) / len(sample))
    budget = cfg.target_tokens * cfg.overlap_ratio
    derived = int(round(budget / avg))
    ceiling = max(1, int(cfg.target_tokens / (3 * avg)))
    return max(cfg.overlap_sentences, min(derived, ceiling))


def _locate(body: str, sentences: list[str]) -> list[tuple[int, int]]:
    """Character spans of each sentence, so a chunk can cite a byte range."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for s in sentences:
        idx = body.find(s, cursor)
        if idx < 0:  # normalization moved it; fall back to sequential spans
            idx = cursor
        spans.append((idx, idx + len(s)))
        cursor = idx + len(s)
    return spans


def _emit(body: str, spans: list[tuple[int, int]], window: list[int]) -> tuple[str, int, int]:
    start = spans[window[0]][0]
    end = spans[window[-1]][1]
    return body[start:end].strip(), start, end


def _merge_runts(chunks: list[Chunk], cfg: ChunkConfig) -> list[Chunk]:
    """Fold a too-small chunk into its neighbour, generalising the header.

    Short chunks are a retrieval hazard out of proportion to their size: a
    two-word heading scores well on a two-word query and displaces the passage
    that actually answers it.

    Merging across a section boundary has a trap, though. The context header is
    the thing that makes a chunk interpretable, so a merged chunk that keeps the
    *first* section's heading now asserts that heading over text belonging to
    the second — a confident, wrong label, which is worse than a vague one. So
    the merged header is recomputed from the **common prefix** of the two
    heading paths: merging "Budgets > Pages" with "Budgets > Bytes" yields
    "Budgets", and merging two unrelated top-level sections yields just the
    document title. The chunk stays interpretable and claims nothing false.
    """
    if len(chunks) < 2:
        return chunks
    out: list[Chunk] = []
    for chunk in chunks:
        if (
            out
            and estimate_tokens(chunk.text) < cfg.min_tokens
            and out[-1].doc_id == chunk.doc_id
            and estimate_tokens(out[-1].text) + estimate_tokens(chunk.text) <= cfg.max_tokens
        ):
            prev = out[-1]
            prev.text = f"{prev.text}\n\n{chunk.text}".strip()
            prev.char_end = max(prev.char_end, chunk.char_end)
            shared = _common_prefix(
                list(prev.metadata.get("headings", [])),
                list(chunk.metadata.get("headings", [])),
            )
            prev.metadata["headings"] = shared
            prev.context_header = _rebuild_header(prev, shared)
            continue
        out.append(chunk)
    return out


def _common_prefix(a: list[str], b: list[str]) -> list[str]:
    """The heading path both chunks genuinely sit under."""
    shared: list[str] = []
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        shared.append(x)
    return shared


def _rebuild_header(chunk: Chunk, headings: list[str]) -> str:
    """Recompose a context header from the parts still true of the chunk."""
    title = str(chunk.metadata.get("title", "")).strip()
    source = str(chunk.metadata.get("source_system", "")).strip()
    parts = [title] if title else []
    if headings:
        parts.append(" > ".join(h.strip() for h in headings if h.strip()))
    if source:
        parts.append(f"({source})")
    return " — ".join(p for p in parts if p)


def chunk_documents(docs: list[Document], config: ChunkConfig | None = None) -> list[Chunk]:
    cfg = config or ChunkConfig()
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, cfg))
    return out
