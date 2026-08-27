"""Splitting documents into retrievable units without losing where they came from.

The strategy is structure first, prose second, and it is chosen against four
specific failure modes:

1. **A chunk that spans a heading boundary has a context header that lies.**
   Sections come from `util.text.split_markdown_sections`, and a chunk never
   crosses one. The cost is real - a document of twenty one-line sections yields
   twenty small chunks - and it is paid deliberately, because "Pricing > Free
   tier" attached to text about the enterprise tier is worse than a short chunk.

2. **A fact split across a chunk boundary is retrievable from neither side.**
   Sentences are packed up to `target_tokens` with `overlap_tokens` of the tail
   carried into the next chunk, so a boundary that lands mid-argument still
   leaves the argument intact in one of the two chunks.

3. **A truncated code example is worse than a long one.** A fenced block is
   atomic. If a single fence exceeds `max_tokens` it becomes its own oversized
   chunk rather than being cut - someone will copy whatever the retriever
   returns, and half a function is a bug delivered with a citation.

4. **Provenance has to survive to the byte range.** `char_start`/`char_end` are
   real offsets into `doc.text`, and the invariant
   `doc.text[c.char_start:c.char_end] == c.text` holds exactly. That is why a
   chunk's text is always a *slice* of the document and never a re-join of the
   pieces it was packed from: the moment the text is reassembled, the offsets
   become approximate and nothing downstream can check them.

Everything here is deterministic - no model call, no randomness - so re-chunking
an unchanged document produces byte-identical chunks with identical ids, which
is what makes the content-hash embedding cache worth having.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from oodarag.models import Chunk, Document
from oodarag.util.hashing import stable_id
from oodarag.util.logging import get_logger
from oodarag.util.text import estimate_tokens, split_markdown_sections, split_sentences

log = get_logger("chunk")

#: Mirrors the fence rule in `util.text.split_markdown_sections`. The two must
#: agree: if this module saw a fence the section splitter did not, fence state
#: and section boundaries would disagree and a heading inside a code block would
#: split a chunk in half.
_FENCE = "```"

#: Per-segment cap for the context header. The header is embedded and indexed
#: with every chunk, so an unbounded one eats the budget it exists to protect.
_HEADER_SEGMENT_CHARS = 96


@dataclass(slots=True)
class ChunkConfig:
    target_tokens: int = 320
    overlap_tokens: int = 64
    min_tokens: int = 48
    max_tokens: int = 640
    respect_code_fences: bool = True


@dataclass(slots=True)
class _Unit:
    """An atom of text that must not be split: one sentence, or one code fence.

    Offsets are absolute into `doc.text` from the moment a unit is created, so
    no later step ever has to add a base offset and get it wrong.
    """

    start: int
    end: int
    tokens: int
    code: bool = False


class Chunker:
    """Packs a `Document` into `Chunk`s.

    Per-document failures are counted into `failed`/`errors` instead of raised:
    `chunk_all` over a 4,000-document corpus must not lose 3,999 chunks to one
    document with pathological structure.
    """

    def __init__(self, config: ChunkConfig | None = None) -> None:
        self.config = config or ChunkConfig()
        # Overlap has to stay strictly under the target or packing cannot make
        # forward progress: a chunk would carry over its own entire content and
        # the packer would emit the same span forever.
        self._overlap = max(0, min(self.config.overlap_tokens, self.config.target_tokens - 1))
        self.failed = 0
        self.errors: list[str] = []

    def chunk(self, doc: Document) -> list[Chunk]:
        text = doc.text
        if not text.strip():
            return []

        groups: list[tuple[int, list[str], list[_Unit]]] = []
        for index, (path, body, offset) in enumerate(split_markdown_sections(text)):
            start = _body_start(text, offset, body)
            if start < 0:
                log.warn("section offsets unrecoverable, skipped", doc=doc.doc_id, section=index)
                continue
            units = self._units(text, start, start + len(body))
            for group in self._merge_thin(self._pack(units), text):
                groups.append((index, path, group))

        total = len(groups)
        chunks: list[Chunk] = []
        for ordinal, (section, path, group) in enumerate(groups):
            start = min(u.start for u in group)
            end = max(u.end for u in group)
            body_text = text[start:end]
            chunks.append(
                Chunk(
                    chunk_id=stable_id(doc.doc_id, str(ordinal)),
                    doc_id=doc.doc_id,
                    ordinal=ordinal,
                    text=body_text,
                    context_header=build_context_header(doc, path, ordinal, total),
                    metadata={
                        "heading_path": list(path),
                        "section": section,
                        "has_code": any(u.code for u in group),
                        "oversized": estimate_tokens(body_text) > self.config.max_tokens,
                        "source_system": doc.source_system,
                        "uri": doc.uri,
                    },
                    char_start=start,
                    char_end=end,
                )
            )
        log.debug("chunked document", doc=doc.doc_id, sections=len(groups), chunks=len(chunks))
        return chunks

    def chunk_all(self, docs: Iterable[Document]) -> list[Chunk]:
        out: list[Chunk] = []
        seen = failed = 0
        for doc in docs:
            seen += 1
            try:
                out.extend(self.chunk(doc))
            except Exception as e:
                failed += 1
                self.failed += 1
                self.errors.append(f"{doc.doc_id}: {type(e).__name__}: {e}")
                log.error("chunking failed", doc=doc.doc_id, err=f"{type(e).__name__}: {e}"[:200])
        log.info("chunked batch", docs=seen, chunks=len(out), failed=failed)
        return out

    # ------------------------------------------------------------------ internals

    def _is_fence(self, line: str) -> bool:
        return self.config.respect_code_fences and line.startswith(_FENCE)

    def _units(self, text: str, start: int, end: int) -> list[_Unit]:
        """Cut one section into atoms, alternating fenced blocks and prose runs."""
        lines = text[start:end].split("\n")
        offsets: list[int] = []
        cursor = start
        for line in lines:
            offsets.append(cursor)
            cursor += len(line) + 1  # exact: the section is a slice joined by "\n"

        units: list[_Unit] = []
        index = 0
        while index < len(lines):
            if self._is_fence(lines[index]):
                close = index + 1
                while close < len(lines) and not self._is_fence(lines[close]):
                    close += 1
                # An unterminated fence swallows the rest of the section. That is
                # the right call: the alternative is guessing where the author
                # meant it to end and splitting code at that guess.
                last = min(close, len(lines) - 1)
                units.append(_unit(text, offsets[index], offsets[last] + len(lines[last]), True))
                index = last + 1
                continue
            run = index
            while run < len(lines) and not self._is_fence(lines[run]):
                run += 1
            units.extend(self._prose_units(text, offsets[index], offsets[run - 1] + len(lines[run - 1])))
            index = run
        return units

    def _prose_units(self, text: str, start: int, end: int) -> list[_Unit]:
        segment = text[start:end]
        units: list[_Unit] = []
        cursor = 0
        for sentence in split_sentences(segment):
            found = segment.find(sentence, cursor)
            if found < 0:
                # Unreachable: `split_sentences` only ever strips. Dropping the
                # sentence beats emitting an offset that does not point at it.
                continue
            cursor = found + len(sentence)
            unit = _unit(text, start + found, start + found + len(sentence))
            if unit.tokens > self.config.max_tokens:
                units.extend(self._split_lines(text, unit))
            else:
                units.append(unit)
        return units

    def _split_lines(self, text: str, unit: _Unit) -> list[_Unit]:
        """Fallback for prose with no sentence boundary at all - a long bullet
        list or a markdown table is one "sentence" and would otherwise be one
        oversized chunk. Lines are the next-best seam that never lands mid-word."""
        out: list[_Unit] = []
        cursor = unit.start
        for line in text[unit.start : unit.end].split("\n"):
            stripped = line.strip()
            if stripped:
                begin = cursor + (len(line) - len(line.lstrip()))
                out.append(_unit(text, begin, begin + len(stripped)))
            cursor += len(line) + 1
        return out or [unit]

    def _pack(self, units: list[_Unit]) -> list[list[_Unit]]:
        """Greedy fill to `target_tokens`, with `overlap_tokens` carried forward."""
        packed: list[list[_Unit]] = []
        current: list[_Unit] = []
        tokens = 0
        for unit in units:
            oversized = unit.tokens > self.config.max_tokens
            if current and (oversized or tokens + unit.tokens > self.config.target_tokens):
                packed.append(current)
                # No overlap around an oversized atom: carrying part of a giant
                # code block into its neighbour only makes the neighbour worse.
                current = [] if oversized else self._carry_over(current)
                tokens = sum(u.tokens for u in current)
            current.append(unit)
            tokens += unit.tokens
            if oversized or tokens >= self.config.max_tokens:
                packed.append(current)
                current = []
                tokens = 0
        if current:
            packed.append(current)
        return packed

    def _carry_over(self, group: list[_Unit]) -> list[_Unit]:
        if self._overlap <= 0 or len(group) < 2:
            return []
        carried: list[_Unit] = []
        budget = self._overlap
        # `group[1:]`: at least one unit is always left behind, which is what
        # guarantees the packer advances rather than re-emitting the same span.
        for unit in reversed(group[1:]):
            if unit.tokens > budget:
                break
            carried.insert(0, unit)
            budget -= unit.tokens
        return carried

    def _merge_thin(self, groups: list[list[_Unit]], text: str) -> list[list[_Unit]]:
        """Fold an undersized group back into its predecessor.

        A trailing two-sentence stub is a chunk that can win a retrieval slot on
        one lucky term and then answer nothing. The first group of a section has
        no predecessor and stays as it is: a genuinely short section is a short
        chunk, and merging it across the heading boundary would break the header.
        """
        out: list[list[_Unit]] = []
        for group in groups:
            if out and _span_tokens(text, group) < self.config.min_tokens:
                merged = out[-1] + group
                if _span_tokens(text, merged) <= self.config.max_tokens:
                    out[-1] = merged
                    continue
            out.append(group)
        return out


def build_context_header(doc: Document, heading_path: list[str], ordinal: int, total: int) -> str:
    """`"<title> > <h1> > <h2> (part 3/9)"` - the contextual-retrieval prefix.

    Deterministic by construction: no model call, so re-chunking an unchanged
    document cannot change a chunk's id or its embedding cache key. `ordinal` is
    0-based (it is `Chunk.ordinal`) and displayed 1-based, because "part 0/9" is
    not a thing anyone reading a citation expects. The part suffix is omitted
    for single-chunk documents, where it is pure noise.
    """
    total = max(total, ordinal + 1)
    segments: list[str] = []
    seen: set[str] = set()
    for raw in (doc.title, *heading_path):
        segment = " ".join(str(raw).split())
        if not segment:
            continue
        key = segment.casefold()
        if key in seen:
            continue  # the H1 usually repeats the title; saying it twice helps nobody
        seen.add(key)
        if len(segment) > _HEADER_SEGMENT_CHARS:
            segment = segment[:_HEADER_SEGMENT_CHARS].rsplit(" ", 1)[0] + "..."
        segments.append(segment)
    header = " > ".join(segments)
    if total > 1:
        header = f"{header} (part {ordinal + 1}/{total})".strip()
    return header


def _unit(text: str, start: int, end: int, code: bool = False) -> _Unit:
    return _Unit(start=start, end=end, tokens=estimate_tokens(text[start:end]), code=code)


def _span_tokens(text: str, units: list[_Unit]) -> int:
    """Tokens of the span a group covers, not the sum of its units.

    Overlap makes a group's unit list contain repeats; summing would double-count
    them and shrink chunks below the target for no reason.
    """
    return estimate_tokens(text[min(u.start for u in units) : max(u.end for u in units)])


def _body_start(text: str, offset: int, body: str) -> int:
    """Realign a section offset onto the first character of its body.

    `split_markdown_sections` strips the body it returns but reports the offset
    of the line it started on, so the two disagree by the leading whitespace. The
    verification is not paranoia: `Document.text` is not guaranteed to have been
    through `util.text.clean` (nothing stops a caller building one by hand), and
    a wrong offset here is a citation pointing at the wrong bytes.
    """
    tail = text[offset:]
    start = offset + (len(tail) - len(tail.lstrip()))
    if text[start : start + len(body)] == body:
        return start
    return text.find(body, offset)
