"""Build an answer out of sentences that were actually retrieved.

No generation. Every sentence in the output is copied verbatim from a retrieved
chunk and carries the marker of the chunk it came from, which means the
verification step in ``verify.py`` can only ever pass — and if it fails, the
bug is in this module rather than in a model.

That is a deliberate choice about where to sit on the quality/defensibility
curve. Extractive answers read worse than generated ones. They also cannot
invent a number, which is the only property that matters when the reader is a
CFO deciding whether to act on it.

**Abstention is a feature.** With thin evidence this returns nothing and says
why. A fund CFO would rather get silence than a confident fabrication, and the
policy engine has a rule that fires when the abstention rate or the citation
coverage moves.
"""

from __future__ import annotations

from oodarag.answer.guards import refuse
from oodarag.models import Answer, Citation, ScoredChunk
from oodarag.util.text import split_sentences, tokenize_all


class ExtractiveAnswerer:
    """Selects and orders sentences from retrieved chunks.

    ``min_score`` and ``min_overlap`` are the abstention thresholds. They are
    set so that the honest failure — returning nothing on a question the corpus
    does not cover — happens more readily than the dishonest one.
    """

    def __init__(self, *, max_sentences: int = 5, min_score: float = 0.0,
                 min_overlap: float = 0.12, max_chars: int = 1200) -> None:
        self.max_sentences = max_sentences
        self.min_score = min_score
        self.min_overlap = min_overlap
        self.max_chars = max_chars

    def answer(self, question: str, scored: list[ScoredChunk]) -> Answer:
        q_terms = set(tokenize_all(question))
        if not scored:
            return self._abstain(question, "nothing was retrieved for this question")
        if not q_terms:
            return self._abstain(question, "the question contained no searchable terms")

        top = scored[0].score
        if top < self.min_score:
            return self._abstain(
                question,
                f"the best match scored {top:.4f}, below the {self.min_score:.4f} floor",
            )

        # One marker per chunk, assigned in retrieval order so [1] is the best hit.
        markers = {s.chunk.chunk_id: i + 1 for i, s in enumerate(scored)}
        candidates: list[tuple[float, int, ScoredChunk, str]] = []

        for rank, s in enumerate(scored):
            for pos, sentence in enumerate(split_sentences(s.chunk.text)):
                text = sentence.strip()
                if len(text) < 30:
                    continue
                terms = set(tokenize_all(text))
                if not terms:
                    continue
                overlap = len(q_terms & terms) / len(q_terms)
                if overlap < self.min_overlap:
                    continue
                # Retrieval rank dominates; sentence position breaks ties toward
                # the top of a chunk, where the claim usually is.
                weight = overlap * (1.0 / (1 + rank)) * (1.0 / (1 + 0.1 * pos))
                candidates.append((weight, rank, s, text))

        if not candidates:
            return self._abstain(
                question,
                "the retrieved passages contain none of the question's key terms",
            )

        candidates.sort(key=lambda c: -c[0])
        chosen = candidates[: self.max_sentences]
        # Present in retrieval order, so the answer reads as an argument rather
        # than a ranked list.
        chosen.sort(key=lambda c: (c[1], -c[0]))

        parts: list[str] = []
        citations: list[Citation] = []
        used = 0
        for i, (weight, _rank, s, text) in enumerate(chosen):
            # The best sentence always goes in, however long it is. Dropping it
            # for exceeding the budget empties the answer and the caller reads
            # that as an abstention — "no evidence" when the truth is "evidence
            # too long", which is a different and much worse claim. Truncating
            # is not an option either: the quote has to stay verbatim or
            # citation verification fails on the system's own output.
            if i and used + len(text) > self.max_chars:
                break
            marker = markers[s.chunk.chunk_id]
            parts.append(f"{text} [{marker}]")
            used += len(text)
            citations.append(Citation(
                marker=marker,
                chunk_id=s.chunk.chunk_id,
                doc_id=s.chunk.doc_id,
                title=s.citation_title,
                uri=s.citation_uri,
                quote=text,
                score=round(float(s.score), 6),
            ))

        if not parts:
            return self._abstain(question, "no passage fitted within the length budget")

        # The guards run on the SELECTED sentences, not on the whole retrieved
        # set: what matters is whether the answer about to be returned actually
        # answers, and that is only knowable once it exists.
        objection = refuse(question, scored, [t for _w, _r, _s, t in chosen])
        if objection:
            return self._abstain(question, objection)

        best_overlap = chosen[0][0]
        confidence = _confidence(top, best_overlap, len(citations))
        return Answer(
            question=question,
            text=" ".join(parts),
            citations=citations,
            confidence=confidence,
            abstained=False,
            generator="extractive",
            retrieved=scored,
            metrics={"candidates": len(candidates), "top_score": round(float(top), 6)},
        )

    def _abstain(self, question: str, why: str) -> Answer:
        return Answer(
            question=question,
            text=f"Abstained: {why}.",
            citations=[],
            confidence=0.0,
            abstained=True,
            generator="extractive",
            metrics={"abstain_reason": why},
        )


def _confidence(top_score: float, best_overlap: float, n_citations: int) -> float:
    """A number with a stated meaning, not a vibe.

    It is the product of three observable quantities, each in [0, 1]: how well
    the best chunk scored, how much of the question the best sentence covered,
    and how much corroboration there is. It is NOT a probability that the answer
    is correct, and nothing downstream should treat it as one — the policy
    engine keys on verified-citation coverage instead, which is measurable.
    """
    score_term = min(1.0, max(0.0, float(top_score) * 8))  # RRF scores run small
    overlap_term = min(1.0, max(0.0, float(best_overlap) * 2))
    support_term = min(1.0, n_citations / 3.0)
    return round(score_term * 0.4 + overlap_term * 0.4 + support_term * 0.2, 4)
