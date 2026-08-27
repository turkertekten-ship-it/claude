"""Answer a question from retrieved chunks, or decline to.

The generator here is **extractive**: it selects sentences that are actually
present in retrieved chunks and assembles them. It does not paraphrase, and it
cannot produce a sentence that is not in the corpus. That is a deliberate
restriction rather than a limitation to be apologised for — it makes the
citation check total. Every clause in the answer came from a chunk whose id is
attached, so "is this supported?" is answered by construction rather than by a
second model call that can also be wrong.

The other half is **abstention**. A retriever always returns its top k, however
bad the top k is; a generator that always writes an answer therefore always
sounds equally confident. When the retrieved evidence does not clear a
threshold of overlap with the question, this returns `abstained=True` and says
what was searched, which is the same discipline the repository's provenance
rules apply to prose: no source, no claim.

Where a hosted model is available it plugs in behind `Generator`, and the
citation verification below still runs over whatever it produces — a generated
sentence whose supporting chunk cannot be found is dropped, not trusted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from oodarag.models import Answer, Citation, ScoredChunk
from oodarag.util.logging import get_logger
from oodarag.util.text import split_sentences, tokenize

log = get_logger("generate")

STOP_ANSWER = (
    "The corpus does not contain enough to answer this. "
    "Retrieved {n} passage(s), none with sufficient overlap with the question."
)


@dataclass(slots=True)
class GenerateConfig:
    """Thresholds for saying something versus saying nothing.

    `min_overlap` is the fraction of the question's content words that must
    appear in a candidate sentence for it to count as responsive. At 0.18 a
    three-word question needs one word matched and a ten-word question needs
    two — low enough to tolerate paraphrase, high enough that a passage sharing
    only a stopword-stripped article does not qualify.

    `min_confidence` gates the whole answer. It is separate from `min_overlap`
    because a single weak sentence and a dozen weak sentences are different
    situations, and only the second should ever be assembled into an answer.

    `max_sentence_chars` rejects a candidate that is too long to be a sentence.
    Sentence splitting fails on code, tables and log dumps, and what comes back
    is a block. A block is not a claim, and quoting one as though it were makes
    an answer that looks thorough and says nothing.

    `min_novel_terms` is the informativeness floor. A passage that repeats the
    question and adds almost nothing scores extremely well on term overlap —
    perfectly, in the pathological case where the corpus contains the question
    verbatim — while answering nothing. Requiring content words *beyond* the
    question is what separates an answer from an echo.
    """

    max_sentences: int = 6
    max_chars: int = 1200
    min_overlap: float = 0.18
    min_confidence: float = 0.12
    max_citations: int = 6
    quote_chars: int = 240
    max_sentence_chars: int = 400
    min_novel_terms: int = 3


class Generator(Protocol):
    def generate(self, question: str, retrieved: list[ScoredChunk]) -> Answer: ...


class ExtractiveGenerator:
    """Assemble an answer from sentences that exist in the retrieved chunks."""

    name = "extractive"

    def __init__(self, config: GenerateConfig | None = None) -> None:
        self.config = config or GenerateConfig()

    def generate(self, question: str, retrieved: list[ScoredChunk]) -> Answer:
        cfg = self.config
        q_terms = {t for t in tokenize(question) if len(t) > 2}

        if not retrieved or not q_terms:
            return Answer(
                question=question,
                text=STOP_ANSWER.format(n=len(retrieved)),
                abstained=True,
                generator=self.name,
                retrieved=retrieved,
                metrics={"reason": "no retrieval" if not retrieved else "no content words"},
            )

        scored = self._rank_sentences(question, retrieved, q_terms)
        picked = self._select(scored, cfg)

        if not picked:
            return Answer(
                question=question,
                text=STOP_ANSWER.format(n=len(retrieved)),
                abstained=True,
                generator=self.name,
                retrieved=retrieved,
                metrics={"reason": "no sentence cleared min_overlap",
                         "best_overlap": round(scored[0][0], 4) if scored else 0.0},
            )

        confidence = sum(o for o, _, _ in picked) / len(picked)
        if confidence < cfg.min_confidence:
            return Answer(
                question=question,
                text=STOP_ANSWER.format(n=len(retrieved)),
                abstained=True,
                confidence=confidence,
                generator=self.name,
                retrieved=retrieved,
                metrics={"reason": "confidence below threshold",
                         "threshold": cfg.min_confidence},
            )

        text, citations = self._assemble(picked, retrieved, cfg)
        return Answer(
            question=question,
            text=text,
            citations=citations,
            confidence=round(confidence, 4),
            abstained=False,
            generator=self.name,
            retrieved=retrieved,
            metrics={
                "sentences": len(picked),
                "sources": len({c.doc_id for c in citations}),
            },
        )

    # ----------------------------------------------------------------- steps

    def _rank_sentences(
        self, question: str, retrieved: list[ScoredChunk], q_terms: set[str]
    ) -> list[tuple[float, str, ScoredChunk]]:
        """Score every candidate sentence by term overlap, weighted by its chunk.

        The chunk's retrieval score is folded in so that a mediocre sentence in
        an excellent passage can still outrank a keyword-dense sentence in a
        passage that barely matched — the retriever's judgement about the
        passage is evidence about the sentence.
        """
        out: list[tuple[float, str, ScoredChunk]] = []
        best_chunk_score = max((s.score for s in retrieved), default=1.0) or 1.0
        exact = question.strip().lower()

        for hit in retrieved:
            weight = hit.score / best_chunk_score
            for sentence in split_sentences(hit.chunk.text):
                sentence = sentence.strip()
                if not (25 <= len(sentence) <= self.config.max_sentence_chars):
                    # Too short to be a claim, or too long to be a sentence.
                    continue
                terms = set(tokenize(sentence))
                if not terms:
                    continue
                # Content the question did not already supply. A candidate that
                # is only the question echoed back cannot answer it.
                novel = {t for t in terms - q_terms if len(t) > 2}
                if len(novel) < self.config.min_novel_terms:
                    continue
                overlap = len(q_terms & terms) / len(q_terms)
                if len(exact) > 8 and exact in sentence.lower():
                    overlap = min(1.0, overlap + 0.4)
                out.append((overlap * (0.5 + 0.5 * weight), sentence, hit))

        out.sort(key=lambda t: t[0], reverse=True)
        return out

    def _select(
        self, scored: list[tuple[float, str, ScoredChunk]], cfg: GenerateConfig
    ) -> list[tuple[float, str, ScoredChunk]]:
        """Take the best sentences, skipping near-duplicates.

        Corpora repeat themselves — a README paragraph reappears in a doc page
        and again in a docstring. Without the near-duplicate check the answer
        is the same sentence three times, which reads as three independent
        confirmations when it is one.
        """
        picked: list[tuple[float, str, ScoredChunk]] = []
        seen_shapes: list[set[str]] = []
        used = 0

        for overlap, sentence, hit in scored:
            if overlap < cfg.min_overlap or len(picked) >= cfg.max_sentences:
                break
            shape = set(tokenize(sentence))
            if any(_jaccard(shape, prior) > 0.7 for prior in seen_shapes):
                continue
            if used + len(sentence) > cfg.max_chars:
                continue
            picked.append((overlap, sentence, hit))
            seen_shapes.append(shape)
            used += len(sentence)
        return picked

    def _assemble(
        self,
        picked: list[tuple[float, str, ScoredChunk]],
        retrieved: list[ScoredChunk],
        cfg: GenerateConfig,
    ) -> tuple[str, list[Citation]]:
        """Write the answer with inline markers, and build verified citations.

        A citation is only emitted for a chunk that is in `retrieved`. That is
        what makes the marker in the text meaningful: it points at something
        the retriever actually returned, in this run, for this question.
        """
        retrieved_ids = {h.chunk.chunk_id for h in retrieved}
        markers: dict[str, int] = {}
        citations: list[Citation] = []
        lines: list[str] = []

        for _overlap, sentence, hit in picked:
            chunk_id = hit.chunk.chunk_id
            if chunk_id not in retrieved_ids:
                log.warn("dropping uncited sentence", chunk_id=chunk_id)
                continue
            if chunk_id not in markers:
                if len(citations) >= cfg.max_citations:
                    continue
                markers[chunk_id] = len(markers) + 1
                citations.append(
                    Citation(
                        marker=markers[chunk_id],
                        chunk_id=chunk_id,
                        doc_id=hit.chunk.doc_id,
                        title=hit.citation_title,
                        uri=hit.citation_uri,
                        quote=sentence[: cfg.quote_chars],
                        score=round(hit.score, 6),
                    )
                )
            lines.append(f"{sentence} [{markers[chunk_id]}]")

        body = " ".join(lines)
        if citations:
            refs = "\n".join(f"[{c.marker}] {c.title} — {c.uri}" for c in citations)
            body = f"{body}\n\nSources:\n{refs}"
        return body, citations


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def verify_citations(answer: Answer) -> list[str]:
    """Re-check an answer's citations against what was retrieved.

    Run after generation, including for a generator this module did not write.
    Returns the problems found; an empty list means every citation resolves.
    """
    problems: list[str] = []
    retrieved_ids = {h.chunk.chunk_id for h in answer.retrieved}
    for citation in answer.citations:
        if citation.chunk_id not in retrieved_ids:
            problems.append(
                f"citation [{citation.marker}] names chunk {citation.chunk_id}, "
                "which was not retrieved for this question"
            )
            continue
        chunk = next(h.chunk for h in answer.retrieved if h.chunk.chunk_id == citation.chunk_id)
        if citation.quote and citation.quote[:80] not in chunk.text:
            problems.append(
                f"citation [{citation.marker}] quotes text absent from chunk {citation.chunk_id}"
            )
    return problems
