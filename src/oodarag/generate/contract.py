"""The citation contract.

A RAG answer is only worth more than a plain model answer if its claims are
traceable. That property has to be *checked*, not requested: a model told to
cite will sometimes cite a source that does not say what it is credited with,
or invent a marker number that indexes nothing.

So citations are verified after generation, against the chunks that were
actually retrieved:

* every `[n]` marker must index a retrieved chunk - unknown markers are dropped
  from the answer text rather than left to look authoritative;
* coverage (the share of substantive sentences carrying a citation) is measured
  and returned, so a caller can reject a weakly-grounded answer;
* below `min_coverage` in strict mode the generator abstains, because "I don't
  have enough grounded material to answer" is a correct answer and a confident
  ungrounded one is not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from oodarag.models import Citation, ScoredChunk
from oodarag.util.text import split_sentences, summarize

_MARKER_RE = re.compile(r"\[(\d{1,2})\]")
# Sentences that carry no claim do not need a citation: a heading, a lead-in
# line ending in a colon, a bullet marker, a very short fragment.
_NON_CLAIM_RE = re.compile(r"^\s*(?:[-*#>]|\d+[.)])\s*|:\s*$")


@dataclass(slots=True)
class CitationCheck:
    citations: list[Citation]
    coverage: float
    uncited_sentences: list[str]
    invalid_markers: list[int]
    text: str

    @property
    def grounded(self) -> bool:
        return bool(self.citations) and not self.invalid_markers


def build_citations(results: list[ScoredChunk]) -> list[Citation]:
    """Assign stable 1-based markers to retrieved chunks."""
    return [
        Citation(
            marker=i,
            chunk_id=result.chunk.chunk_id,
            doc_id=result.chunk.doc_id,
            title=result.citation_title,
            uri=result.chunk.metadata.get("deep_link") or result.citation_uri,
            quote=summarize(result.chunk.text, 220),
            score=round(result.score, 4),
        )
        for i, result in enumerate(results, start=1)
    ]


def verify(text: str, available: list[Citation]) -> CitationCheck:
    """Check an answer's markers against the citations actually available."""
    valid = {c.marker: c for c in available}
    used: list[int] = []
    invalid: list[int] = []

    for match in _MARKER_RE.finditer(text):
        marker = int(match.group(1))
        if marker in valid:
            if marker not in used:
                used.append(marker)
        elif marker not in invalid:
            invalid.append(marker)

    # A marker pointing at nothing is worse than no marker: it looks like
    # evidence. Remove it from the text rather than shipping it.
    cleaned = text
    for marker in invalid:
        cleaned = cleaned.replace(f"[{marker}]", "")
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    sentences = _attach_trailing_markers(split_sentences(cleaned))
    claims = [s for s in sentences
              if len(s.split()) >= 5 and not _NON_CLAIM_RE.match(s)]
    cited = [s for s in claims if _MARKER_RE.search(s)]
    coverage = len(cited) / len(claims) if claims else (1.0 if cleaned else 0.0)

    return CitationCheck(
        citations=[valid[m] for m in used],
        coverage=round(coverage, 4),
        uncited_sentences=[s for s in claims if not _MARKER_RE.search(s)][:5],
        invalid_markers=invalid,
        text=cleaned,
    )


_MARKER_ONLY_RE = re.compile(r"^[\s\[\]\d,;.]*$")


def _attach_trailing_markers(sentences: list[str]) -> list[str]:
    """Re-join fragments that are nothing but citation markers.

    Sentence splitting breaks after terminal punctuation, and `[` opens a new
    sentence - so "Claim about chunking. [1]" splits into a claim with no
    citation and a fragment that is only a citation. Coverage then reads 0% for
    a perfectly cited answer, and strict mode abstains on it.

    This is the conventional placement for a trailing citation, so it has to be
    handled rather than styled around: an LLM will produce it whatever the
    prompt says.
    """
    joined: list[str] = []
    for sentence in sentences:
        stripped = sentence.strip()
        if joined and stripped and _MARKER_ONLY_RE.match(stripped) and "[" in stripped:
            joined[-1] = f"{joined[-1]} {stripped}"
            continue
        joined.append(sentence)
    return joined


def format_context(citations: list[Citation], results: list[ScoredChunk],
                   max_tokens: int = 6000) -> str:
    """Render retrieved chunks as a numbered evidence block.

    Each entry carries its marker, title and URI so the model can cite without
    inventing identifiers, and so a human reading the prompt can audit it.
    """
    from oodarag.util.text import estimate_tokens

    blocks: list[str] = []
    spent = 0
    for citation, result in zip(citations, results):
        body = result.chunk.indexed_text
        entry = (f"[{citation.marker}] {citation.title}\n"
                 f"    source: {citation.uri}\n"
                 f"{body}")
        cost = estimate_tokens(entry)
        if spent + cost > max_tokens and blocks:
            break
        blocks.append(entry)
        spent += cost
    return "\n\n---\n\n".join(blocks)
