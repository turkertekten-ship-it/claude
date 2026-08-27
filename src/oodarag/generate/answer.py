"""Answer assembly: retrieve, ground, verify, return.

The generator is swappable; the contract is not. Whichever backend produces the
prose, the answer that comes out of here has been checked against the chunks
that were actually retrieved.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from oodarag.generate.contract import build_citations, format_context, verify
from oodarag.generate.extractive import extractive_answer
from oodarag.models import Answer, ScoredChunk
from oodarag.retrieve.hybrid import HybridRetriever
from oodarag.util.logging import get_logger

log = get_logger("generate")


@dataclass
class AnswerConfig:
    top_k: int = 8
    context_tokens: int = 6000
    #: Below this citation coverage the answer is flagged, and in strict mode
    #: replaced by an abstention. Ungrounded fluency is the failure this whole
    #: pipeline exists to prevent.
    min_coverage: float = 0.5
    strict: bool = True
    #: Retrieval scores below this mean nothing was retrieved at all.
    min_top_score: float = 0.005
    #: Query-term relevance floor, measured independently of source priors.
    #: This is the gate that actually catches an out-of-corpus question: a
    #: fused score includes authority and recency, which are high for a trusted
    #: recent document regardless of whether it answers anything.
    min_relevance: float = 0.15
    generator: str = "auto"  # "auto" | "extractive" | "claude"


class AnswerGenerator:
    def __init__(self, retriever: HybridRetriever, config: AnswerConfig | None = None,
                 llm: Any = None) -> None:
        self.retriever = retriever
        self.config = config or AnswerConfig()
        self._llm = llm

    def _resolve_llm(self) -> Any | None:
        if self.config.generator == "extractive":
            return None
        if self._llm is not None:
            return self._llm
        if self.config.generator in ("auto", "claude"):
            from oodarag.generate.claude import ClaudeGenerator

            candidate = ClaudeGenerator()
            if candidate.available:
                self._llm = candidate
                return candidate
            if self.config.generator == "claude":
                log.warn("claude requested but unavailable; using extractive")
        return None

    def answer(self, question: str, *, filters: dict[str, Any] | None = None,
               top_k: int | None = None) -> Answer:
        started = time.monotonic()
        config = self.config
        results, trace = self.retriever.retrieve(
            question, top_k=top_k or config.top_k, filters=filters
        )

        if not results:
            return Answer(
                question=question, text="No indexed source matched this question.",
                abstained=True, generator="none", confidence=0.0,
                metrics={"reason": "no_results", "retrieval": trace.as_dict()},
            )

        best_relevance = max(
            (r.components.get("rerank_relevance", 0.0) for r in results), default=0.0
        )
        if results[0].score < config.min_top_score or best_relevance < config.min_relevance:
            return Answer(
                question=question,
                text=("The index contains nothing relevant to this question. "
                      f"Best query-term relevance was {best_relevance:.2f}, below the "
                      f"{config.min_relevance:.2f} floor."),
                abstained=True, generator="none", retrieved=results,
                confidence=0.0,
                metrics={"reason": "below_relevance_floor",
                         "best_relevance": round(best_relevance, 4),
                         "top_score": round(results[0].score, 4),
                         "retrieval": trace.as_dict()},
            )

        citations = build_citations(results)
        context = format_context(citations, results, max_tokens=config.context_tokens)
        idf = self.retriever.store.idf_lookup()

        llm = self._resolve_llm()
        generator_name = "extractive"
        if llm is not None:
            try:
                text = llm.generate(question, context)
                generator_name = getattr(llm, "name", "llm")
            except Exception as e:
                # A generation failure must not lose the retrieval work: fall
                # back to the grounded-by-construction path and say so.
                log.warn("llm generation failed, falling back to extractive",
                         err=str(e)[:200])
                text = extractive_answer(question, results, citations, idf=idf)
                generator_name = "extractive(llm_failed)"
        else:
            text = extractive_answer(question, results, citations, idf=idf)

        check = verify(text, citations)
        confidence = _confidence(results, check.coverage)

        abstained = False
        if config.strict and check.coverage < config.min_coverage:
            abstained = True
            text = (
                "I can't answer this from the retrieved sources with enough grounding "
                f"(citation coverage {check.coverage:.0%}, floor {config.min_coverage:.0%}). "
                "The closest material found was:\n"
                + "\n".join(f"  [{c.marker}] {c.title} - {c.uri}" for c in citations[:3])
            )
            check.citations = citations[:3]

        answer = Answer(
            question=question,
            text=check.text if not abstained else text,
            citations=check.citations,
            confidence=0.0 if abstained else confidence,
            abstained=abstained,
            generator=generator_name,
            retrieved=results,
            metrics={
                "citation_coverage": check.coverage,
                "invalid_markers": check.invalid_markers,
                "uncited_sentences": check.uncited_sentences,
                "top_score": round(results[0].score, 4),
                "best_relevance": round(best_relevance, 4),
                "retrieval": trace.as_dict(),
                "total_ms": round((time.monotonic() - started) * 1000, 2),
            },
        )
        log.info("answered", generator=generator_name, cited=len(answer.citations),
                 coverage=check.coverage, abstained=abstained,
                 ms=answer.metrics["total_ms"])
        return answer


def _confidence(results: list[ScoredChunk], coverage: float) -> float:
    """A blunt, explainable confidence.

    Three signals, none of them a probability and none pretending to be: how
    strong the best match was, how much better it was than the fifth (a flat
    distribution means nothing stood out), and how well the answer is cited.
    """
    top = results[0].score
    margin = top - results[min(4, len(results) - 1)].score
    strength = min(1.0, top / 0.6)
    separation = min(1.0, margin / 0.25) if len(results) > 1 else 0.5
    return round(0.5 * strength + 0.2 * separation + 0.3 * coverage, 4)
