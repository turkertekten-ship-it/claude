"""Structure-aware chunking: turn a Document into retrievable Chunks.

Chunking is where most RAG systems quietly lose. The cheap approach - slide a
fixed character window over the text - is fast to write and produces two
failure modes that are invisible until a user reads an answer:

1. A window ends mid-sentence, mid-table-row or mid-code-block. The retrieved
   passage is then syntactically broken, and a generator asked to quote it
   either truncates a number or invents the missing half.
2. A window has no idea where it sits. "It depends on the chunk size" retrieves
   beautifully for a query about chunk size and tells the reader nothing,
   because "it" was defined three windows earlier.

So this module breaks on *structure* first and on length second. The boundary
preference order is: section heading, then paragraph, then sentence, then line,
and only as a last resort a raw character cut. Every chunk carries a
deterministic context header (:func:`build_context_header`) that restates where
it came from, which is the cheap half of contextual retrieval - the half that
does not need a model call and therefore cannot drift between runs.

Two invariants are load-bearing and are checked by :func:`verify_spans`:

* ``doc.text[chunk.char_start:chunk.char_end]`` is the chunk's source region.
  A citation is only worth printing if it can be traced back to a byte range,
  so no transformation is applied to a chunk that would break that mapping.
  (The single exception is CRLF folding, which changes the rendering but not
  the range; see :func:`_render`.)
* Chunking is a pure function of the document text. Same bytes in, same chunk
  ids out, on any machine, in any process. An index that reshuffles itself
  between runs cannot be diffed, cached, or trusted.

What this module deliberately does NOT do: normalize, clean, or redact. Those
change the text and would invalidate the offsets. They belong upstream, at
Document construction, where the offsets are established.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from oodarag.models import Chunk, Document
from oodarag.util.hashing import stable_id
from oodarag.util.logging import get_logger
from oodarag.util.text import (
    estimate_tokens,
    heading_path,
    split_markdown_sections,
    truncate_tokens,
)

log = get_logger("chunk")

#: Matches the ~4 chars/token assumption in :func:`oodarag.util.text.estimate_tokens`.
#: Used only for O(1) budget arithmetic so packing does not re-measure a growing
#: slice on every piece; the authoritative count is still ``estimate_tokens``.
CHARS_PER_TOKEN = 4

#: Once a chunk holds this fraction of its budget, a paragraph/section boundary
#: is taken immediately rather than packing to the brim. Slightly shorter chunks
#: that end on a real boundary beat maximally-full chunks that end mid-thought;
#: retrieval quality is dominated by whether the passage is self-contained.
SOFT_BREAK_RATIO = 0.62

#: How far over target a merge is allowed to push a chunk. Absorbing a runt is
#: worth some overshoot - a 12-token chunk is noise in the index, it matches
#: everything weakly and nothing well - but not unbounded overshoot.
MERGE_HEADROOM = 1.5

MAX_TITLE_TOKENS = 32
MAX_PATH_TOKENS = 40

# Opening fence: up to three leading spaces, then >=3 backticks or tildes.
# NOTE: util.text.split_markdown_sections only tracks ``` fences, so a heading
# line inside a ~~~ fence will already have split the section before we see it.
# We cannot fix that without editing that module; we merely refuse to make it
# worse by splitting further inside whatever we are handed.
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")

# Sentence boundary WITH an offset, and without the ASCII-uppercase lookahead
# used elsewhere in the codebase: a Turkish sentence starts "İstanbul..." or
# "Şirket...", neither of which is [A-Z], and gating on ASCII would silently
# turn every Turkish paragraph into one unsplittable blob.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?…])[ \t]*\n?[ \t]*(?=\S)")

# The i-family, collapsed. See fold().
_I_FAMILY = {ord("I"): "i", ord("ı"): "i", ord("İ"): "i"}


def fold(s: str) -> str:
    """Case-fold for *comparison only*, in a way that survives Turkish.

    ``str.lower()`` is wrong here in both directions: ``"I".lower()`` is ``"i"``,
    which a Turkish reader reads as a different letter from ``"I"`` (whose
    lowercase is ``"ı"``), and ``"İ".lower()`` yields two codepoints (``i`` plus
    a combining dot) that then fail to compare equal to a plain ``i``.

    Rather than pick a locale - the corpus is mixed Turkish and English, so
    either choice is wrong for half of it - we collapse the whole i-family
    (I, ı, İ, i) onto one letter. That deliberately conflates Turkish "ılık" and
    "ilik"; the tradeoff is accepted because the alternative is failing to match
    a heading a user typed in ASCII against the same heading written properly.
    Nothing user-visible is ever produced by this function.
    """
    folded = unicodedata.normalize("NFKC", s).translate(_I_FAMILY)
    return folded.replace("̇", "").casefold().strip()


def _flatten(s: str) -> str:
    """Collapse any whitespace to single spaces. Case is never touched."""
    return " ".join((s or "").split())


@dataclass(slots=True, frozen=True)
class _Piece:
    """The smallest span the packer is allowed to cut at.

    ``level`` records how good the boundary *before* this piece is: 0 for a
    block (paragraph / fence / heading) boundary, 1 for a sentence or table row,
    2 for a bare line, 3 for a forced character cut. Lower is better, and the
    packer uses it to prefer ending a chunk on a real structural seam.
    """

    start: int
    end: int
    tokens: int
    level: int
    fence: bool = False
    table: bool = False


@dataclass(slots=True)
class _Span:
    """A provisional chunk: a half-open range of doc.text plus what we know about it."""

    start: int
    end: int
    headings: list[str]
    tokens: int
    fence: bool = False
    table: bool = False
    merged: int = 1
    cross_section: bool = False


# --------------------------------------------------------------------- blocks


def _iter_lines(text: str, start: int, end: int) -> Iterator[tuple[int, int]]:
    """Yield (start, end) for each line in [start, end), newline included."""
    i = start
    while i < end:
        nl = text.find("\n", i, end)
        if nl == -1:
            yield i, end
            return
        yield i, nl + 1
        i = nl + 1


def _closes_fence(stripped: str, marker: str) -> bool:
    return bool(stripped) and stripped[0] == marker[0] and set(stripped) == {marker[0]}


def _blocks(text: str, start: int, end: int) -> list[tuple[int, int, bool]]:
    """Split a span into (start, end, is_fence) blocks.

    A fenced block is emitted whole and is never subdivided further - half a
    code block retrieves as garbage and reads to a generator as a syntax error,
    which is strictly worse than one oversized chunk. An unterminated fence
    swallows the rest of the span, which is the conservative reading: we cannot
    know the author meant to close it, and guessing splits the block.
    """
    out: list[tuple[int, int, bool]] = []
    cur_start: int | None = None
    cur_end = start
    in_fence = False
    marker = "`"
    for ls, le in _iter_lines(text, start, end):
        line = text[ls:le]
        stripped = line.strip()
        if in_fence:
            cur_end = le
            if _closes_fence(stripped, marker):
                out.append((cur_start if cur_start is not None else ls, cur_end, True))
                cur_start, in_fence = None, False
            continue
        if (m := _FENCE_OPEN_RE.match(line)) is not None:
            if cur_start is not None:
                out.append((cur_start, cur_end, False))
            in_fence = True
            marker = m.group(1)
            cur_start, cur_end = ls, le
            continue
        if not stripped:
            if cur_start is not None:
                out.append((cur_start, cur_end, False))
                cur_start = None
            continue
        if cur_start is None:
            cur_start = ls
        cur_end = le
    if cur_start is not None:
        out.append((cur_start, cur_end, in_fence))
    return out


def _char_cuts(text: str, start: int, end: int, target_chars: int) -> list[int]:
    """Last-resort cuts through a span with no usable boundary in it.

    This is the 200k-character-single-line case: a minified blob, a base64
    payload, a CSV row with no spaces. There is no honest boundary, so we cut on
    length - but never in the middle of a combining sequence, or a decomposed
    "İ" would arrive in the next chunk as a naked dot.
    """
    cuts = [start]
    pos = start
    while end - pos > target_chars:
        nxt = pos + target_chars
        while nxt < end and unicodedata.combining(text[nxt]):
            nxt += 1
        if nxt >= end or nxt <= pos:
            break
        cuts.append(nxt)
        pos = nxt
    return cuts


def _split_long(text: str, start: int, end: int, level: int, target_tokens: int) -> list[_Piece]:
    """Break an oversized non-fence span down: lines, then raw characters."""
    target_chars = max(1, target_tokens * CHARS_PER_TOKEN)
    pieces: list[_Piece] = []
    for i, (ls, le) in enumerate(_iter_lines(text, start, end)):
        line_level = level if i == 0 else 2
        if estimate_tokens(text[ls:le]) <= target_tokens:
            pieces.append(_Piece(ls, le, estimate_tokens(text[ls:le]), line_level))
            continue
        cuts = _char_cuts(text, ls, le, target_chars)
        for j, cs in enumerate(cuts):
            ce = cuts[j + 1] if j + 1 < len(cuts) else le
            pieces.append(_Piece(cs, ce, estimate_tokens(text[cs:ce]), line_level if j == 0 else 3))
    return pieces


def _pieces(text: str, start: int, end: int, target_tokens: int) -> list[_Piece]:
    """Decompose a section into cuttable pieces, finest granularity last."""
    pieces: list[_Piece] = []
    for bstart, bend, is_fence in _blocks(text, start, end):
        if is_fence:
            pieces.append(_Piece(bstart, bend, estimate_tokens(text[bstart:bend]), 0, fence=True))
            continue
        lines = list(_iter_lines(text, bstart, bend))
        # A pipe anywhere in the block means we are probably inside a markdown
        # table. Treat every line as atomic: a half row is not merely ugly, it
        # re-parses as a *different* table with the columns shifted.
        if any("|" in text[ls:le] for ls, le in lines):
            for i, (ls, le) in enumerate(lines):
                pieces.append(_Piece(ls, le, estimate_tokens(text[ls:le]), 0 if i == 0 else 1,
                                     table=True))
            continue
        seg_starts = [bstart]
        for m in _SENT_SPLIT_RE.finditer(text, bstart, bend):
            if m.end() > seg_starts[-1]:
                seg_starts.append(m.end())
        for i, ss in enumerate(seg_starts):
            se = seg_starts[i + 1] if i + 1 < len(seg_starts) else bend
            level = 0 if i == 0 else 1
            tokens = estimate_tokens(text[ss:se])
            if tokens <= target_tokens:
                pieces.append(_Piece(ss, se, tokens, level))
            else:
                pieces.extend(_split_long(text, ss, se, level, target_tokens))
    return pieces


# ---------------------------------------------------------------------- pack


def _pack(
    text: str, pieces: list[_Piece], target_tokens: int, overlap_tokens: int
) -> list[tuple[int, int, bool, bool]]:
    """Greedily group pieces into chunk spans, then extend each start backwards
    to create overlap.

    Overlap is expressed as a *wider span*, not as a copied prefix. That keeps
    ``text[start:end]`` exact for every chunk even though adjacent chunks now
    share a region - which is the only formulation under which a citation into
    an overlapping chunk still resolves to a real byte range.
    """
    if not pieces:
        return []
    target_chars = max(1, target_tokens * CHARS_PER_TOKEN)
    soft_tokens = max(1, int(target_tokens * SOFT_BREAK_RATIO))
    groups: list[tuple[int, int]] = []
    first = 0
    cur_tokens = 0
    for i, p in enumerate(pieces):
        if i > first:
            too_big = (
                cur_tokens + p.tokens > target_tokens
                or p.end - pieces[first].start > target_chars
            )
            if too_big or (p.level == 0 and cur_tokens >= soft_tokens):
                groups.append((first, i - 1))
                first, cur_tokens = i, 0
        cur_tokens += p.tokens
    groups.append((first, len(pieces) - 1))

    out: list[tuple[int, int, bool, bool]] = []
    for gi, (a, b) in enumerate(groups):
        start = pieces[a].start
        if overlap_tokens and gi > 0:
            floor = groups[gi - 1][0]
            acc = 0
            j = a - 1
            # Never consume the whole previous group (that would make chunk k a
            # superset of chunk k-1), and never reach back into a fence: the
            # prefix would be a code block missing its opening line.
            while j > floor:
                q = pieces[j]
                if q.fence or acc + q.tokens > overlap_tokens:
                    break
                acc += q.tokens
                start = q.start
                j -= 1
        out.append((
            start,
            pieces[b].end,
            any(pieces[k].fence for k in range(a, b + 1)),
            any(pieces[k].table for k in range(a, b + 1)),
        ))
    return out


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _merge_runts(text: str, spans: list[_Span], min_tokens: int, target_tokens: int) -> list[_Span]:
    """Absorb below-threshold chunks into a neighbour, forward-first.

    A single left-to-right pass is enough and, unlike repeated global passes, it
    stays linear: a growing accumulator stops absorbing the moment it clears
    ``min_tokens``, so no span is measured more than a bounded number of times.
    A trailing runt has no successor, so it is folded backwards afterwards.
    """
    if len(spans) < 2 or min_tokens <= 0:
        return spans
    limit = int(target_tokens * MERGE_HEADROOM)
    out: list[_Span] = []
    for span in spans:
        if out:
            prev = out[-1]
            if prev.tokens < min_tokens:
                merged_tokens = estimate_tokens(text[prev.start : span.end])
                if merged_tokens <= limit:
                    out[-1] = _merge(text, prev, span, merged_tokens)
                    continue
        out.append(span)
    if len(out) > 1 and out[-1].tokens < min_tokens:
        prev, last = out[-2], out[-1]
        merged_tokens = estimate_tokens(text[prev.start : last.end])
        if merged_tokens <= limit:
            out[-2:] = [_merge(text, prev, last, merged_tokens)]
    return out


def _merge(text: str, a: _Span, b: _Span, tokens: int) -> _Span:
    cross = a.headings != b.headings
    return _Span(
        start=a.start,
        end=max(a.end, b.end),
        # A merged chunk spans two heading paths, so neither is the whole truth.
        # We keep the chain in effect where the chunk *starts* - which is what a
        # reader scrolling to char_start would see, and which is exactly
        # ``a.headings``, since a span's headings come from the section holding
        # its start offset. ``cross_section`` in the metadata is the flag that
        # says the body reaches past them.
        headings=a.headings,
        tokens=tokens,
        fence=a.fence or b.fence,
        table=a.table or b.table,
        merged=a.merged + b.merged,
        cross_section=a.cross_section or b.cross_section or cross,
    )


def _render(text: str, start: int, end: int) -> str:
    """The chunk body as indexed.

    CRLF is folded to LF: leaving carriage returns in would put a ``\\r`` inside
    every character n-gram of the embedder and inside every quoted citation, for
    no gain. It shortens the rendered string relative to the source range, which
    is why ``char_end`` is documented as the end of the source *region* rather
    than as ``char_start + len(text)``.
    """
    return text[start:end].replace("\r\n", "\n").replace("\r", "\n")


# --------------------------------------------------------------------- public


def build_context_header(
    doc: Document, headings: Sequence[str], ordinal: int, total: int
) -> str:
    """The contextual-retrieval prefix prepended to a chunk before indexing.

    Deliberately template-based rather than model-generated. A generated header
    costs an LLM call per chunk, cannot be reproduced, and - the part that
    actually bites - changes between runs, so every chunk's content hash changes
    and the entire embedding cache is invalidated by a re-run that changed
    nothing. A template gives up some fluency and buys a stable index.

    ``ordinal`` is 0-based (it is ``Chunk.ordinal``) and is rendered 1-based.
    The position line is omitted for a single-chunk document, where "Part 1 of 1"
    is pure noise. Note the tradeoff it does carry: because ``total`` appears in
    the header, editing a document enough to change its chunk count re-embeds all
    of its chunks. That is acceptable because such an edit shifts chunk
    boundaries anyway; a *smaller* edit does not change the count.

    Never changes the case of anything it is given: see :func:`fold` for why
    lowercasing a Turkish heading is a real, visible bug.
    """
    title = _flatten(doc.title) or _flatten(doc.uri) or doc.doc_id or "(untitled)"
    lines = [f"Document: {truncate_tokens(title, MAX_TITLE_TOKENS)}"]

    folded_title = fold(title)
    path: list[str] = []
    for h in headings or ():
        flat = _flatten(str(h))
        if not flat or fold(flat) == folded_title:
            continue  # the first heading is usually the title again
        if path and fold(path[-1]) == fold(flat):
            continue
        path.append(flat)
    if path:
        lines.append(f"Section: {truncate_tokens(' > '.join(path), MAX_PATH_TOKENS)}")

    if source := _flatten(getattr(doc, "source_system", "")):
        lines.append(f"Source: {source}")

    try:
        ordinal_i, total_i = int(ordinal), int(total)
    except (TypeError, ValueError):
        ordinal_i, total_i = 0, 0
    if total_i > 1 and 0 <= ordinal_i < total_i:
        lines.append(f"Part {ordinal_i + 1} of {total_i}")
    return "\n".join(lines)


def chunk_document(
    doc: Document,
    target_tokens: int = 450,
    overlap_tokens: int = 60,
    min_tokens: int = 40,
) -> list[Chunk]:
    """Split a document into overlapping, structure-aligned chunks.

    Degenerate inputs are the point of most of this code, not an afterthought:
    empty text yields no chunks rather than one empty one; a document that is
    nothing but headings collapses into a handful of merged chunks instead of a
    hundred four-token ones; a single 200k-character line with no whitespace in
    it is cut on length because there is nothing else to cut on; CRLF is folded
    in the rendered text while the offsets stay pinned to the original bytes.
    """
    text = getattr(doc, "text", "") or ""
    if not text.strip():
        return []

    target_tokens = max(16, int(target_tokens))
    # An overlap at or above the target would make consecutive chunks identical
    # (or worse, make the window never advance), so it is capped at half.
    overlap_tokens = max(0, min(int(overlap_tokens), target_tokens // 2))
    min_tokens = max(0, min(int(min_tokens), target_tokens))

    sections = split_markdown_sections(text)
    if not sections:  # defensive: only reachable if the helper changes shape
        sections = [(heading_path(text, 0), text, 0)]
    starts = [off for _, _, off in sections]

    spans: list[_Span] = []
    for i, (headings, _body, off) in enumerate(sections):
        sec_end = starts[i + 1] if i + 1 < len(starts) else len(text)
        for start, end, fence, table in _pack(
            text, _pieces(text, off, sec_end, target_tokens), target_tokens, overlap_tokens
        ):
            start, end = _trim(text, start, end)
            if end <= start:
                continue
            spans.append(
                _Span(start, end, list(headings), estimate_tokens(text[start:end]), fence, table)
            )

    spans = _merge_runts(text, spans, min_tokens, target_tokens)
    if not spans:
        return []

    total = len(spans)
    chunks: list[Chunk] = []
    for ordinal, span in enumerate(spans):
        body = _render(text, span.start, span.end)
        if not body.strip():
            continue
        header = build_context_header(doc, span.headings, ordinal, total)
        metadata: dict[str, Any] = {
            "doc_title": doc.title,
            "source_system": doc.source_system,
            "uri": doc.uri,
            "headings": list(span.headings),
            "has_code": span.fence,
            "has_table": span.table,
        }
        if span.merged > 1:
            metadata["merged_from"] = span.merged
        if span.cross_section:
            metadata["cross_section"] = True
        chunks.append(
            Chunk(
                # Content-sensitive, so an edited chunk cannot silently reuse the
                # id of the text it replaced. The index therefore deletes by
                # doc_id and re-inserts rather than updating in place.
                chunk_id=stable_id(doc.doc_id, str(ordinal), body),
                doc_id=doc.doc_id,
                ordinal=ordinal,
                text=body,
                context_header=header,
                metadata=metadata,
                char_start=span.start,
                char_end=span.end,
            )
        )
    if len(chunks) != total:  # a chunk rendered blank: worth knowing, not fatal
        log.warn("dropped blank chunks", doc_id=doc.doc_id, expected=total, kept=len(chunks))
    return chunks


def verify_spans(doc: Document, chunks: Sequence[Chunk]) -> list[str]:
    """Check the provenance invariant. Returns a list of problems, empty if clean.

    This exists because "the offsets are honest" is the kind of claim that is
    true when written and false three refactors later, and because a citation
    system whose ranges have silently drifted is worse than one with no ranges
    at all: it prints a quote that looks sourced and is not.
    """
    problems: list[str] = []
    text = doc.text or ""
    for i, c in enumerate(chunks):
        if c.ordinal != i:
            problems.append(f"chunk {c.chunk_id}: ordinal {c.ordinal} at position {i}")
        if not (0 <= c.char_start <= c.char_end <= len(text)):
            problems.append(f"chunk {c.chunk_id}: span {c.char_start}:{c.char_end} out of bounds")
            continue
        if _render(text, c.char_start, c.char_end) != c.text:
            problems.append(f"chunk {c.chunk_id}: text does not match its source range")
        if i and chunks[i - 1].char_start > c.char_start:
            problems.append(f"chunk {c.chunk_id}: starts before its predecessor")
    return problems
