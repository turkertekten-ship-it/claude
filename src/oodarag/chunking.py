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

import re
from dataclasses import dataclass
from typing import Any

from oodarag.models import Chunk, Document
from oodarag.util.hashing import stable_id
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

    `target` is the size packing aims for, **not** the size most chunks are: a
    prose section at or under `hard_max` is emitted whole, so target governs
    only the sections above it. On the external corpus that is 31 sections of
    2,486 - though they are the big ones, and they yield about a quarter of all
    chunks, which is why sweeping target is not the no-op the section count
    suggests. The measured distribution at these defaults is median **109**
    tokens, p75 198, p90 314: a third of target, and the docstring used to
    claim the opposite.

    `hard_max` is the ceiling a chunk may not exceed even if that means
    splitting a structural unit. That became true only recently; five chunks
    exceeded it, the largest at 2.1x. See `_pack_units`.

    `min_tokens` stops the tail of a section becoming a two-word chunk that
    matches everything and means nothing. It is a floor with one deliberate
    exception: a runt whose only neighbour is large enough that merging would
    breach `hard_max` is left alone, because the ceiling wins.

    Both sizes were swept against the gate and held-out sets and the defaults
    sit on a plateau, so they are measured rather than merely inherited:

        target_tokens  |  96  160  224  320*  448  640
        gate pass /54  |  46   47   48   49    49   48
        held pass /22  |  18   19   19   19    19   18

        hard_max_tokens| 160  224  320  448  640*  960
        gate pass /54  |  48   49   49   49   49    49
        held pass /22  |  19   19   19   19   19    18

        overlap_tokens |   0   16   32   64*   96   128
        gate pass /54  |  49   49   49   49    48   48
        held pass /22  |  19   19   19   19    18   19

    Nothing was changed: every shipped value is at or tied for the best row on
    both sets. The useful finding is the flatness - retrieval is robust to
    chunk size across a 2-3x range, so the retrieval parameters tuned earlier
    are not artifacts of this particular chunking. Only the extremes move
    anything (`scripts/chunk_size_sweep.py`).
    """

    target_tokens: int = 320
    hard_max_tokens: int = 640
    overlap_tokens: int = 64
    min_tokens: int = 32
    include_context_header: bool = True
    #: Code is chunked by definition; prose by sentence window.
    code_max_tokens: int = 700


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
            # The guard here used to be `and not buffer`, which meant an
            # oversized unit was only ever handled when it was a section's
            # *first* unit - and a markdown section almost always opens with its
            # own heading line, so the buffer was never empty by the time the
            # big unit arrived. All five of the corpus's over-ceiling chunks sat
            # behind a two-token `#### Fixes`. Flush what is buffered and handle
            # the unit on its own instead (L71).
            if buffer:
                out.append((joiner.join(t for t, _, _ in buffer),
                            buffer[0][1], buffer[0][2]))
                buffer = []
                size = 0
            # A unit over the ceiling is usually not one unit at all.
            # `split_sentences` breaks on sentence punctuation or a *blank*
            # line, and a markdown bullet list and a fenced code block have
            # neither - so pydantic's 54-entry changelog list arrives here as a
            # single 1,330-token "sentence" and psutil's `>>>` example as a
            # 1,283-token one, with 133 newlines and no `. ` between them.
            #
            # Emitting those whole was the old behaviour, and it is why five
            # chunks exceeded a ceiling documented as one a chunk "may not
            # exceed" - the largest at 2.1x. It also made one retrieval unit out
            # of 54 unrelated changelog entries, so a query matching any single
            # bullet dragged in the other 53.
            #
            # Lines are the natural boundary in exactly the blocks that reach
            # here, so re-split on them rather than cutting at an arbitrary
            # point. A single line still over the ceiling - a minified file, the
            # case this branch was written for - is still emitted whole.
            lines: list[tuple[str, int]] = []
            cursor = offset
            for line in unit_text.split("\n"):
                if line.strip():
                    lines.append((line, cursor))
                cursor += len(line) + 1
            if len(lines) > 1:
                for packed, line_offset, _ in _pack_units(
                        lines, config, joiner="\n", max_tokens=ceiling):
                    out.append((packed, line_offset, index))
                continue
            out.append((unit_text, offset, index))
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


def _split_code(doc: Document, config: ChunkConfig) -> list[tuple[str, int, dict]]:
    """Code: one chunk per top-level definition, with the file's preamble kept.

    Imports and module docstrings are what tell a reader (and a reranker) what
    the file is; attaching them to the first definition keeps that signal.
    """
    language = (doc.metadata.get("language") or "").lower()
    pattern = _DEF_PATTERNS.get(language)
    text = doc.text
    if pattern is None:
        units = [(line, 0) for line in text.split("\n")]
        return [(chunk, offset, {}) for chunk, offset, _ in
                _pack_units(units, config, joiner="\n", max_tokens=config.code_max_tokens)]

    boundaries = [(m.start(), next(g for g in m.groups() if g) if m.groups() else "")
                  for m in pattern.finditer(text)]
    if not boundaries:
        units = [(line, 0) for line in text.split("\n")]
        return [(chunk, offset, {}) for chunk, offset, _ in
                _pack_units(units, config, joiner="\n", max_tokens=config.code_max_tokens)]

    pieces: list[tuple[str, int, dict]] = []
    preamble = text[: boundaries[0][0]].strip()
    for index, (start, symbol) in enumerate(boundaries):
        end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text)
        body = text[start:end].rstrip()
        if index == 0 and preamble:
            body = f"{preamble}\n\n{body}"
            start = 0
        meta = {"symbol": symbol, "language": language}
        if estimate_tokens(body) <= config.code_max_tokens:
            pieces.append((body, start, meta))
            continue
        units = [(line, 0) for line in body.split("\n")]
        for packed, _, _ in _pack_units(units, config, joiner="\n",
                                        max_tokens=config.code_max_tokens):
            pieces.append((packed, start, dict(meta)))
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
        if stripped:
            if match := _TIMESTAMP_RE.match(stripped):
                stamps[len(units)] = match.group(1)
                stripped = stripped[match.end():]
            if stripped:
                units.append((stripped, offset))
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
    # Backwards only leaves one runt unreachable: the first piece has nothing
    # before it to fold into. That is not a corner - it is *every* runt the
    # corpus has. 22 of the 153 external documents began with a chunk under
    # `min_tokens` and no document had a runt anywhere else, because the
    # backward pass already caught those. They are badge lines (`[image: Black
    # Logo]`, 4 tokens) and lead paragraphs stranded away from their section
    # (mccabe's 27-token "Ned's script to check McCabe complexity"), and either
    # way a chunk that small has almost no term statistics.
    #
    # Measured neutral on retrieval - gate 49/54 and held-out 19/22 both
    # unchanged, held-out identical to four decimals - so this is here to make
    # `min_tokens` the floor it is documented to be, not for a score.
    if (len(merged) > 1
            and estimate_tokens(merged[0][0]) < config.min_tokens
            and estimate_tokens(merged[0][0]) + estimate_tokens(merged[1][0])
            <= config.hard_max_tokens):
        text, start, meta = merged[0]
        follow_text, _follow_start, follow_meta = merged[1]
        # The runt's own offset, since it is now where the chunk begins.
        merged[1] = (f"{text}\n\n{follow_text}", start,
                     _merge_meta(meta, follow_meta))
        del merged[0]
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
