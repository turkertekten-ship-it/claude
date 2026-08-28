"""Structure-aware chunking.

Chunking is where most RAG systems quietly lose. Split on a fixed character
count and you cut a function in half, orphan a table from its header, and strip
every passage of the context that told you what it was about. The retriever then
does its job perfectly on text that no longer means anything.

Three commitments here:

1. **Split on structure first, size second.** Markdown headings, code
   definitions, transcript timestamps and chat turns are natural boundaries that
   the author already put there. Size limits pack *within* those boundaries.

2. **Every chunk carries a context header.** A short deterministic prefix -
   document title, heading path, file path and symbol, speaker and timestamp -
   is embedded and indexed *with* the body. This is contextual retrieval: it is
   what stops "it depends on the chunk size" being retrieved with no idea what
   "it" refers to. Deterministic, so it costs nothing and is reproducible; an
   LLM-generated variant can be layered on top for corpora that justify it.

3. **Overlap is sentence-aligned, not character-aligned.** Overlapping by raw
   characters produces chunks that begin mid-word.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import Any

from oodarag.models import Chunk, Document
from oodarag.util.hashing import content_hash, stable_id
from oodarag.util.text import (
    estimate_tokens,
    split_markdown_sections,
    split_sentences,
    summarize,
)

# Top-level definitions across the languages this corpus actually contains.
_DEF_PATTERNS = {
    "python": re.compile(r"^(?:async\s+)?(?:def|class)\s+(\w+)", re.M),
    "javascript": re.compile(
        r"^(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+)|"
        r"const\s+(\w+)\s*=\s*(?:async\s*)?\()", re.M),
    "typescript": re.compile(
        r"^(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+)|"
        r"interface\s+(\w+)|type\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()", re.M),
    "go": re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)", re.M),
    "rust": re.compile(r"^(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|impl|trait)\s+(\w+)", re.M),
    "java": re.compile(r"^\s*(?:public|private|protected).*?\s(\w+)\s*\(", re.M),
    "ruby": re.compile(r"^\s*(?:def|class|module)\s+(\w+)", re.M),
}
_TIMESTAMP_RE = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*", re.M)
_SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z .'-]{1,30}):\s")

CODE_LANGUAGES = frozenset(_DEF_PATTERNS) | {
    "c", "cpp", "csharp", "php", "swift", "kotlin", "scala", "bash", "sql", "lua", "r", "julia",
}


@dataclass(slots=True)
class ChunkConfig:
    """Sizes are in estimated tokens (see util.text.estimate_tokens).

    `target_tokens` is what most chunks will be. `hard_max_tokens` bounds a
    chunk's *body*: a structural unit larger than it is subdivided - by lines,
    then by word windows - so the bound holds even for text the sentence
    splitter cannot divide, which is where it used to leak (L63).

    Two things sit outside that bound on purpose, and both were found by
    reading a chunk size without asking what it measured:

    * the context header is added after packing and costs a median 19 tokens,
      13% on top of the external corpus's body text, so `Chunk.token_estimate`
      - which measures what is actually embedded - runs above this ceiling by
      roughly a header;
    * code is packed against `code_max_tokens`, deliberately the larger of the
      two, because a definition is worth keeping whole.

    `min_tokens` stops the tail of a section becoming a two-word chunk that
    matches everything and means nothing.
    """

    target_tokens: int = 320
    hard_max_tokens: int = 640
    overlap_tokens: int = 64
    min_tokens: int = 32
    include_context_header: bool = True
    #: Code is chunked by definition; prose by sentence window.
    code_max_tokens: int = 700


def chunker_fingerprint(config: ChunkConfig | None = None) -> str:
    """Identity of the chunking that produced a chunk: its sizes and its code.

    Chunks are upstream of vectors, and the index already refuses to compare
    vectors across embedding spaces. It had no equivalent for chunks, so a
    store re-indexed after a chunking change kept every old chunk - the
    documents had not changed, and nothing else was consulted. Measured: a
    corpus re-indexed with a 5x smaller chunker rewrote **0 of 1,822** chunks
    and reported success (L63).

    The module's own source is part of the identity because the sizes are not
    the whole algorithm: subdividing an oversized unit moves boundaries with
    every number held constant. That errs towards re-chunking - editing a
    comment here costs one re-index - and the error in the other direction is
    every measurement afterwards being taken against chunks that no longer
    correspond to any version of the code.
    """
    config = config or ChunkConfig()
    sizes = ";".join(f"{field}={getattr(config, field)}"
                     for field in sorted(ChunkConfig.__dataclass_fields__))
    try:
        source = pathlib.Path(__file__).read_text("utf-8")
    except OSError:
        # Packaged without its source (a zipapp): the sizes still change the
        # fingerprint, and a code change without a size change goes unnoticed.
        # Degrade rather than refuse to index.
        source = ""
    return content_hash(sizes, source)


_FENCE = "`" * 3


def _balance_fences(text: str) -> str:
    """Close a code fence the split left open, and open one it left dangling.

    Packing works in prose or code units and knows nothing about fences, so a
    long fenced block lands in two chunks: the first ends inside the fence, the
    second begins with the orphaned tail and a closing marker that opens nothing.
    Measured on the 91-document external corpus, 20 of 1,148 chunks carry an odd
    number of markers.

    It matters because the extractive generator quotes chunk text verbatim into
    answers. An unclosed fence renders everything after it as code; a stray
    closing one renders the answer's prose as code from that point back.

    Only the markers are added - no boundary moves, so retrieval is unaffected
    and a chunk stays exactly the text it was, made independently renderable.
    """
    if _FENCE not in text:
        return text
    lines = text.splitlines()
    markers = [i for i, line in enumerate(lines) if line.strip().startswith(_FENCE)]
    if len(markers) % 2 == 0:
        return text
    # An odd count means one end is missing. Which end is decided by where the
    # first marker sits relative to the text before it: a chunk opening with a
    # marker inherited an already-open fence.
    first = markers[0]
    if not any(lines[i].strip() for i in range(first)):
        return f"{_FENCE}\n{text}"
    return f"{text}\n{_FENCE}"


def chunk_document(doc: Document, config: ChunkConfig | None = None) -> list[Chunk]:
    """Split one document into retrievable chunks."""
    config = config or ChunkConfig()
    kind = _classify(doc)
    if kind == "code":
        pieces = _split_code(doc, config)
    elif kind == "transcript":
        pieces = _split_transcript(doc, config)
    elif kind == "chat":
        pieces = _split_chat(doc, config)
    else:
        pieces = _split_prose(doc, config)

    # Merge undersized pieces *before* building chunks, so a merged chunk's
    # metadata and context header describe everything it actually contains.
    # Merging finished Chunk objects instead keeps only the first piece's
    # metadata, which produces a chunk labelled `symbol: alpha` whose body also
    # holds `beta` and `Gamma` - provenance that quietly lies.
    pieces = _merge_runt_pieces(pieces, config)

    chunks: list[Chunk] = []
    for ordinal, (text, start, meta) in enumerate(pieces):
        # The strip moves where the chunk begins, so the offset moves with it.
        # Without this the span points at the whitespace before the text - by a
        # whole indent for a packed code body, which is most of them (L64).
        start += len(text) - len(text.lstrip())
        text = _balance_fences(text.strip())
        if not text:
            continue
        header = _context_header(doc, meta) if config.include_context_header else ""
        chunks.append(
            Chunk(
                chunk_id=stable_id(doc.doc_id, str(ordinal), text[:200]),
                doc_id=doc.doc_id,
                ordinal=ordinal,
                text=text,
                context_header=header,
                char_start=start,
                char_end=start + len(text),
                metadata={
                    "source_system": doc.source_system,
                    "uri": doc.uri,
                    "title": doc.title,
                    "kind": kind,
                    # The identity of the text `char_start` and `char_end`
                    # index. Those offsets address the *normalised* document,
                    # not the file it came from - front matter is stripped,
                    # whitespace normalised, secrets replaced - so a span is
                    # only a precise reference when it travels with the hash of
                    # the text it refers to (L78).
                    "doc_hash": doc.content_hash,
                    "authority": doc.metadata.get("authority", 1.0),
                    **meta,
                },
            )
        )
    for ordinal, chunk in enumerate(chunks):
        chunk.ordinal = ordinal
    return chunks


# ------------------------------------------------------------------ classification


def _classify(doc: Document) -> str:
    meta = doc.metadata
    if meta.get("kind") in ("chat_turn", "chat_session") or doc.source_system == "chat":
        return "chat"
    if meta.get("kind") == "transcript" or doc.source_system == "youtube":
        return "transcript"
    language = (meta.get("language") or "").lower()
    if language in CODE_LANGUAGES and not meta.get("is_doc"):
        return "code"
    return "prose"


def _context_header(doc: Document, meta: dict[str, Any]) -> str:
    """A compact 'where am I' line, embedded with the chunk body."""
    parts: list[str] = [doc.title]
    if paths := meta.get("heading_paths"):
        # A merged chunk spans several sections; name the leaf of each so the
        # header describes the whole span rather than only where it began.
        leaves = [p[-1] for p in paths if p]
        root = " > ".join(paths[0][:-1]) if paths[0][:-1] else ""
        joined = "; ".join(dict.fromkeys(leaves))
        parts.append(f"{root} > {joined}" if root else joined)
    elif path := meta.get("heading_path"):
        parts.append(" > ".join(path))
    if symbols := meta.get("symbols"):
        parts.append(f"definitions: {', '.join(symbols)}")
    elif symbol := meta.get("symbol"):
        parts.append(f"definition: {symbol}")
    if speaker := meta.get("speaker"):
        parts.append(f"speaker: {speaker}")
    if timestamp := meta.get("timestamp"):
        parts.append(f"at {timestamp}")
    if role := meta.get("role"):
        parts.append(f"role: {role}")
    line = " | ".join(p for p in parts if p)
    return f"[{doc.source_system}] {line}"


# ------------------------------------------------------------------- strategies


def _pack_units(
    units: list[tuple[str, int]],
    config: ChunkConfig,
    joiner: str = " ",
    max_tokens: int | None = None,
) -> list[tuple[str, int, int]]:
    """Greedily pack (text, offset) units into target-sized chunks with overlap.

    Overlap is applied in whole units, so a chunk never starts mid-sentence.

    Returns `(text, char_offset, first_unit_index)`. The unit index is not
    decoration: a transcript chunk's timestamp is the timestamp of the cue it
    starts at, and estimating that from word counts drifts within a few chunks
    and then saturates on the last cue in the document - publishing a `?t=`
    deep link that lands at the end of the video whatever passage was cited.
    """
    ceiling = max_tokens or config.hard_max_tokens
    out: list[tuple[str, int, int]] = []
    buffer: list[tuple[str, int, int]] = []
    size = 0

    for index, (unit_text, offset) in enumerate(units):
        unit_tokens = estimate_tokens(unit_text)
        if unit_tokens > ceiling:
            # A unit larger than the ceiling on its own. Emitting it whole - as
            # this did - is how `hard_max_tokens` stopped being a ceiling: 8 of
            # 1,810 external chunks ran to 2.1x it, the largest a 1,332-token
            # changelog list that the sentence splitter sees as one sentence
            # (L63). Subdivide instead, and flush first so the pieces are not
            # silently prefixed with the previous chunk's tail.
            if buffer:
                out.append((joiner.join(t for t, _, _ in buffer), buffer[0][1], buffer[0][2]))
                buffer = []
                size = 0
            out.extend(_subdivide(unit_text, offset, index, config, ceiling))
            continue
        if size + unit_tokens > config.target_tokens and buffer:
            out.append((joiner.join(t for t, _, _ in buffer), buffer[0][1], buffer[0][2]))
            carry: list[tuple[str, int, int]] = []
            carried = 0
            for carried_text, off, idx in reversed(buffer):
                tokens = estimate_tokens(carried_text)
                if carried + tokens > config.overlap_tokens:
                    break
                carry.insert(0, (carried_text, off, idx))
                carried += tokens
            buffer = carry
            size = carried
        buffer.append((unit_text, offset, index))
        size += unit_tokens

    if buffer:
        out.append((joiner.join(t for t, _, _ in buffer), buffer[0][1], buffer[0][2]))
    return out


def _subdivide(unit_text: str, offset: int, index: int,
               config: ChunkConfig, ceiling: int) -> list[tuple[str, int, int]]:
    """Last resort for one unit that is bigger than the ceiling by itself.

    A "sentence" of 1,332 tokens is not a sentence; it is the splitter failing
    to see structure it does not model - a changelog bullet list, a fenced
    example, a table, none of which end in a full stop. Lines are the structure
    such text does have, so split there first, and fall back to word windows
    only when a single line is still over the ceiling (a minified file). Never
    cuts mid-word, so a chunk still reads as text rather than as a fragment.

    Offsets stay absolute: every piece reports where it starts in the document,
    because a citation that points at the wrong span is worse than a long chunk.
    """
    pieces: list[tuple[str, int, int]] = []

    def emit(start: int, end: int) -> None:
        raw = unit_text[start:end]
        lead = len(raw) - len(raw.lstrip())
        text = raw.strip()
        if text:
            pieces.append((text, offset + start + lead, index))

    lines = unit_text.splitlines(keepends=True) or [unit_text]
    buffer_start: int | None = None
    buffer_end = 0
    size = 0
    cursor = 0
    for line in lines:
        start, cursor = cursor, cursor + len(line)
        tokens = estimate_tokens(line)
        if tokens > ceiling:
            if buffer_start is not None:
                emit(buffer_start, buffer_end)
                buffer_start, size = None, 0
            _window_words(unit_text, start, cursor, offset, index, config, pieces)
            continue
        if size + tokens > config.target_tokens and buffer_start is not None:
            emit(buffer_start, buffer_end)
            buffer_start, size = None, 0
        if buffer_start is None:
            buffer_start = start
        buffer_end = cursor
        size += tokens
    if buffer_start is not None:
        emit(buffer_start, buffer_end)
    return pieces


def _window_words(unit_text: str, start: int, end: int, offset: int, index: int,
                  config: ChunkConfig, pieces: list[tuple[str, int, int]]) -> None:
    """Split one over-ceiling line into target-sized windows on word boundaries."""
    line = unit_text[start:end]
    window_start = 0
    size = 0
    cursor = 0
    for match in re.finditer(r"\S+\s*", line):
        size += estimate_tokens(match.group())
        cursor = match.end()
        if size >= config.target_tokens:
            text = line[window_start:cursor].strip()
            if text:
                lead = len(line[window_start:cursor]) - len(line[window_start:cursor].lstrip())
                pieces.append((text, offset + start + window_start + lead, index))
            window_start, size = cursor, 0
    tail = line[window_start:].strip()
    if tail:
        lead = len(line[window_start:]) - len(line[window_start:].lstrip())
        pieces.append((tail, offset + start + window_start + lead, index))


def _split_prose(doc: Document, config: ChunkConfig) -> list[tuple[str, int, dict]]:
    """Markdown/prose: sections by heading, then sentence-window packing."""
    pieces: list[tuple[str, int, dict]] = []
    for heading_path, body, section_offset in split_markdown_sections(doc.text):
        meta = {"heading_path": heading_path} if heading_path else {}
        if estimate_tokens(body) <= config.hard_max_tokens:
            pieces.append((body, section_offset, meta))
            continue
        units: list[tuple[str, int]] = []
        cursor = section_offset
        for sentence in split_sentences(body):
            index = doc.text.find(sentence, cursor)
            units.append((sentence, index if index >= 0 else cursor))
            cursor = (index if index >= 0 else cursor) + len(sentence)
        for packed_text, offset, _ in _pack_units(units, config):
            pieces.append((packed_text, offset, dict(meta)))
    return pieces or [(doc.text, 0, {})]


def _line_units(text: str, base: int) -> list[tuple[str, int]]:
    """Lines paired with where each one actually starts in the document.

    The offsets used to be `0` for every line, and the packed pieces' offsets
    were then thrown away in favour of the enclosing definition's start. Every
    piece of a split definition therefore claimed the same `char_start` - 202 of
    606 code chunks pointed somewhere they were not, one by 3,151 characters
    (L64). Splitting and rejoining on "\n" is lossless, so carrying the real
    offsets changes no chunk text and no chunk id.
    """
    units: list[tuple[str, int]] = []
    cursor = base
    for line in text.split("\n"):
        units.append((line, cursor))
        cursor += len(line) + 1
    return units


def _split_code(doc: Document, config: ChunkConfig) -> list[tuple[str, int, dict]]:
    """Code: one chunk per top-level definition, with the file's preamble kept.

    Imports and module docstrings are what tell a reader (and a reranker) what
    the file is; attaching them to the first definition keeps that signal.
    """
    language = (doc.metadata.get("language") or "").lower()
    pattern = _DEF_PATTERNS.get(language)
    text = doc.text
    boundaries = [(m.start(), next(g for g in m.groups() if g) if m.groups() else "")
                  for m in pattern.finditer(text)] if pattern else []
    if not boundaries:
        return [(chunk, offset, {}) for chunk, offset, _ in
                _pack_units(_line_units(text, 0), config, joiner="\n",
                            max_tokens=config.code_max_tokens)]

    pieces: list[tuple[str, int, dict]] = []
    raw_preamble = text[: boundaries[0][0]]
    preamble = raw_preamble.strip()
    for index, (start, symbol) in enumerate(boundaries):
        end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text)
        body = text[start:end].rstrip()
        units = _line_units(body, start)
        if index == 0 and preamble:
            # The preamble is joined on to the first definition, so the chunk's
            # text spans a gap in the document. Its lines still carry their own
            # offsets; the blank line between the two is filed at the end of the
            # preamble, which is where it would be if it were real.
            lead = len(raw_preamble) - len(raw_preamble.lstrip())
            gap = lead + len(preamble)
            units = _line_units(preamble, lead) + [("", gap)] + units
            body = f"{preamble}\n\n{body}"
            start = lead
        meta = {"symbol": symbol, "language": language}
        if estimate_tokens(body) <= config.code_max_tokens:
            pieces.append((body, start, meta))
            continue
        for packed, offset, _ in _pack_units(units, config, joiner="\n",
                                             max_tokens=config.code_max_tokens):
            pieces.append((packed, offset, dict(meta)))
    return pieces


def _split_transcript(doc: Document, config: ChunkConfig) -> list[tuple[str, int, dict]]:
    """Transcripts: pack cues into windows, keeping the first timestamp.

    A citation into a video is only useful if it can be turned into a
    `?t=` deep link, so the timestamp travels with the chunk.
    """
    lines = doc.text.split("\n")
    units: list[tuple[str, int]] = []
    stamps: dict[int, str] = {}
    offset = 0
    for line in lines:
        stripped = line.strip()
        # Where the cue's *text* starts, not where its line does: the leading
        # whitespace and the timestamp marker are removed from the unit, so an
        # offset that ignores them points at "[00:04:12] " rather than at the
        # words the chunk actually contains (L64).
        start = offset + len(line) - len(line.lstrip())
        if stripped:
            if match := _TIMESTAMP_RE.match(stripped):
                stamps[len(units)] = match.group(1)
                start += match.end()
                stripped = stripped[match.end():]
            if stripped:
                units.append((stripped, start))
        offset += len(line) + 1

    pieces: list[tuple[str, int, dict]] = []
    for packed_text, start, first_unit in _pack_units(units, config):
        # The exact cue this chunk starts at, reported by the packer.
        timestamp = stamps.get(first_unit) or _nearest_stamp(stamps, first_unit)
        meta: dict[str, Any] = {}
        if timestamp:
            meta["timestamp"] = timestamp
            meta["deep_link"] = _deep_link(doc.uri, timestamp)
        pieces.append((packed_text, start, meta))
    return pieces


def _nearest_stamp(stamps: dict[int, str], index: int) -> str:
    candidates = [i for i in stamps if i <= index]
    return stamps[max(candidates)] if candidates else ""


def _deep_link(uri: str, timestamp: str) -> str:
    parts = [int(p) for p in timestamp.split(":")]
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    if "youtube.com" in uri or "youtu.be" in uri:
        joiner = "&" if "?" in uri else "?"
        return f"{uri}{joiner}t={seconds}"
    return uri


def _split_chat(doc: Document, config: ChunkConfig) -> list[tuple[str, int, dict]]:
    """Chat transcripts: keep turns intact, pack consecutive turns into windows.

    A single turn is rarely self-contained - the answer is in the reply and the
    question is in the turn before - so a window of turns retrieves better than
    a turn alone.
    """
    turns = re.split(r"\n(?=(?:user|assistant|system|tool)\b\s*[:>])", doc.text, flags=re.I)
    units: list[tuple[str, int]] = []
    offset = 0
    roles: dict[int, str] = {}
    for turn in turns:
        cleaned = turn.strip()
        if cleaned:
            if match := re.match(r"^(user|assistant|system|tool)\b\s*[:>]", cleaned, re.I):
                roles[len(units)] = match.group(1).lower()
            units.append((cleaned, offset))
        offset += len(turn) + 1

    pieces: list[tuple[str, int, dict]] = []
    for packed_text, start, first_unit in _pack_units(units, config, joiner="\n\n"):
        # Role of the turn the window opens with, by unit index rather than by
        # chunk position - the two diverge as soon as any chunk holds more than
        # one turn, which is the normal case.
        meta = {"role": roles[first_unit]} if first_unit in roles else {}
        pieces.append((packed_text, start, meta))
    return pieces


def _merge_runt_pieces(pieces: list[tuple[str, int, dict]],
                       config: ChunkConfig) -> list[tuple[str, int, dict]]:
    """Fold undersized pieces into their neighbour, combining their metadata.

    A 12-token chunk has almost no term statistics: it either matches nothing or
    matches everything, and either way it wastes a retrieval slot. But a merged
    chunk spans more than one structural unit, so its metadata has to say so -
    otherwise the context header names one heading or one function while the
    body holds three, and every downstream consumer of that metadata is wrong.
    """
    if len(pieces) < 2:
        return pieces
    merged: list[tuple[str, int, dict]] = []
    for text, start, meta in pieces:
        if (merged
                and estimate_tokens(text) < config.min_tokens
                and estimate_tokens(merged[-1][0]) + estimate_tokens(text)
                <= config.hard_max_tokens):
            previous_text, previous_start, previous_meta = merged[-1]
            merged[-1] = (f"{previous_text}\n\n{text}", previous_start,
                          _merge_meta(previous_meta, meta))
            continue
        merged.append((text, start, dict(meta)))
    return merged


def _merge_meta(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Combine two pieces' metadata so the result describes the merged span."""
    out = dict(first)
    for key, plural in (("symbol", "symbols"), ("heading_path", "heading_paths")):
        values = list(first.get(plural) or ([first[key]] if first.get(key) else []))
        for candidate in (second.get(plural) or ([second[key]] if second.get(key) else [])):
            if candidate not in values:
                values.append(candidate)
        if values:
            out[plural] = values
            out[key] = values[0]
    for key, value in second.items():
        # Keep the earliest timestamp: a merged transcript window starts where
        # its first cue started.
        if key not in out and key not in ("symbols", "heading_paths"):
            out[key] = value
    return out


def chunk_documents(docs: list[Document], config: ChunkConfig | None = None) -> list[Chunk]:
    config = config or ChunkConfig()
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, config))
    return out


def summarize_chunking(chunks: list[Chunk]) -> dict[str, Any]:
    """Distribution stats - the fastest way to see a chunker misbehaving."""
    if not chunks:
        return {"chunks": 0}
    sizes = sorted(c.token_estimate for c in chunks)
    kinds: dict[str, int] = {}
    for chunk in chunks:
        kind = chunk.metadata.get("kind", "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "chunks": len(chunks),
        "docs": len({c.doc_id for c in chunks}),
        "tokens_min": sizes[0],
        "tokens_p50": sizes[len(sizes) // 2],
        "tokens_p95": sizes[int(len(sizes) * 0.95)],
        "tokens_max": sizes[-1],
        "tokens_mean": round(sum(sizes) / len(sizes), 1),
        "by_kind": kinds,
    }
