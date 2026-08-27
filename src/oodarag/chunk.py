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
"""

from __future__ import annotations

from dataclasses import dataclass

from oodarag.models import Chunk, Document
from oodarag.util.hashing import stable_id
from oodarag.util.text import (
    estimate_tokens,
    split_markdown_sections,
    split_sentences,
)


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
    include_header_in_text: bool = False


def chunk_document(doc: Document, config: ChunkConfig | None = None) -> list[Chunk]:
    """Split one document. Returns [] only for a document with no text."""
    cfg = config or ChunkConfig()
    text = doc.text.strip()
    if not text:
        return []

    sections = split_markdown_sections(text) or [([], text, 0)]
    chunks: list[Chunk] = []

    for headings, body, offset in sections:
        body = body.strip()
        if not body:
            continue
        header = _context_header(doc, headings)
        for piece, start, end in _pack(body, cfg):
            chunks.append(_make_chunk(doc, header, piece, offset + start, offset + end,
                                      len(chunks), headings, cfg))

    if not chunks:  # a document that is entirely whitespace-separated fragments
        header = _context_header(doc, [])
        chunks.append(_make_chunk(doc, header, text, 0, len(text), 0, [], cfg))

    merged = _merge_runts(chunks, cfg)
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


def _pack(body: str, cfg: ChunkConfig) -> list[tuple[str, int, int]]:
    """Pack a section into windows of about `target_tokens`, overlapping.

    A section that already fits is emitted whole: splitting something that fits
    only makes each half less interpretable.
    """
    if estimate_tokens(body) <= cfg.max_tokens:
        return [(body, 0, len(body))]

    sentences = split_sentences(body)
    if not sentences:
        return [(body, 0, len(body))]

    spans = _locate(body, sentences)
    out: list[tuple[str, int, int]] = []
    window: list[int] = []
    tokens = 0

    for i, sentence in enumerate(sentences):
        cost = estimate_tokens(sentence)
        if window and tokens + cost > cfg.target_tokens:
            out.append(_emit(body, spans, window))
            keep = window[-cfg.overlap_sentences :] if cfg.overlap_sentences else []
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
