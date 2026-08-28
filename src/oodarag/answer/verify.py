"""Check that a citation's quote actually occurs in the chunk it cites.

This is the difference between "the model said so" and "the source says so",
and it is the single control that decides whether anything this system produces
can survive an audit.

It is not paranoia. Purpose-built commercial legal-research systems — vendors
whose entire product is retrieval over primary law — were measured hallucinating
in the high teens and low thirties of a percent
[src:DELEGATED-RECON-2026-08-27]. Anything assembled here will be worse. The
design response is not to try harder at generation; it is to make every asserted
span checkable against the retrieved text, drop the ones that fail, and abstain
rather than hedge when nothing survives.

Verification is on normalised whitespace only. Case and punctuation are NOT
normalised away: a quote that differs from its source in a digit, a negation or
a currency is a different claim, and matching it loosely would defeat the check.
"""

from __future__ import annotations

import re

from oodarag.models import Answer, Citation, ScoredChunk
from oodarag.util.logging import get_logger

log = get_logger("verify")

_WS = re.compile(r"\s+")
_MARKERS_ONLY = re.compile(r"^(?:\s*\[\d+\])+\s*$")


def normalise(text: str) -> str:
    """Collapse whitespace. Nothing else — see the module docstring."""
    return _WS.sub(" ", text or "").strip()


def quote_supported(quote: str, haystack: str) -> bool:
    q = normalise(quote)
    return bool(q) and q in normalise(haystack)


def verify_citations(answer: Answer, retrieved: list[ScoredChunk]) -> Answer:
    """Drop unsupported citations; abstain if none survive.

    A citation must name a chunk that was actually retrieved AND quote text that
    actually occurs in it. Citing a real chunk with an invented quote is the
    failure mode that looks most convincing, so both halves are checked.
    """
    by_id = {s.chunk.chunk_id: s for s in retrieved}
    kept: list[Citation] = []
    dropped: list[str] = []

    for c in answer.citations:
        scored = by_id.get(c.chunk_id)
        if scored is None:
            dropped.append(f"{c.chunk_id}: not in the retrieved set")
            continue
        if not quote_supported(c.quote, scored.chunk.text):
            dropped.append(f"{c.chunk_id}: quote not found in the chunk")
            continue
        kept.append(c)

    answer.citations = kept
    answer.metrics["citations_dropped"] = len(dropped)
    if dropped:
        answer.metrics["drop_reasons"] = dropped[:10]
        log.warn("citations dropped", n=len(dropped), first=dropped[0])

    answer.metrics["citation_coverage"] = round(coverage(answer), 4)

    if not kept and not answer.abstained:
        answer.abstained = True
        answer.confidence = 0.0
        answer.text = (
            "Abstained: nothing in the retrieved sources supports an answer. "
            f"{len(dropped)} citation(s) failed verification."
        )
    elif dropped:
        # Losing a citation costs confidence proportionally, never silently.
        total = len(kept) + len(dropped)
        answer.confidence = round(answer.confidence * (len(kept) / total), 4)
    return answer


def coverage(answer: Answer) -> float:
    """Fraction of the answer's sentences carrying a surviving citation marker.

    Sentences are counted by their marker, not by a parser: a sentence that ends
    up with no ``[n]`` after verification is uncovered, which is exactly what
    this number is for.
    """
    if answer.abstained:
        return 0.0
    raw = [s for s in re.split(r"(?<=[.!?])\s+", answer.text or "") if s.strip()]
    # A marker written after the terminal period — "…rate is 37 percent. [1]" —
    # splits into a fragment of its own. Left alone it counts as an uncited
    # sentence and halves the score of a perfectly cited answer, so a fragment
    # that is nothing but markers is folded back into the sentence it belongs to.
    sentences: list[str] = []
    for part in raw:
        if _MARKERS_ONLY.match(part) and sentences:
            sentences[-1] += " " + part
        else:
            sentences.append(part)
    if not sentences:
        return 0.0
    live = {c.marker for c in answer.citations}
    covered = sum(1 for s in sentences
                  if any(f"[{m}]" in s for m in live))
    return covered / len(sentences)
