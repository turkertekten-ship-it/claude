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
    #: Retrieval scores below this mean nothing was retrieved at all. Read off
    #: the total score, so it is scale-dependent like everything else that was -
    #: currently 200x below the smallest score any golden query produces, which
    #: is the margin a "nothing at all" floor should have (L69).
    min_top_score: float = 0.005
    #: Query-term relevance floor, measured independently of source priors.
    #: This is the gate that actually catches an out-of-corpus question: a
    #: fused score includes authority and recency, which are high for a trusted
    #: recent document regardless of whether it answers anything.
    #:
    #: Swept in steps of 0.01 over both corpora (`scripts/floor_sweep.py`),
    #: re-run at 153 external documents after the corpus widened (L50):
    #:
    #:   floor          0.10-0.13  0.15-0.17  0.18  0.19  0.20-0.23  0.24-0.25  0.28+
    #:   external       44/54      45/54      46    47    46         45         43 down
    #:   primary        17/20      17-18/20   18    18    18         18         18
    #:   combined       61/74      62-63/74   64    65    64         63         declining
    #:   over-answered   6          5          4     3     3          2          2
    #:   over-refused    0          1          1     1     2          4          6 up
    #:
    #: **0.19 is kept, and the reasoning for it is not the reasoning it had.**
    #: On the 91-document corpus the curve had two plateaus and 0.19 was the
    #: midpoint of the upper one, chosen over a lone peak at 0.20 on the grounds
    #: that picking a peak fits the threshold to 74 questions. On 153 documents
    #: the curve is unimodal and 0.19 *is* its mode, with 0.18 and 0.20 one case
    #: below on either side and a smooth decline outward. "Pick the plateau, not
    #: the peak" was advice about a spike in a flat region; the mode of a smooth
    #: single-peaked curve is a different object and is the right estimate.
    #:
    #: The shoulders are not noise either. Raising to 0.20 does not buy what a
    #: higher floor is supposed to buy - over-answering stays at 3 all the way
    #: to 0.23 - and adds an over-refusal. The safety argument that once favoured
    #: a higher floor does not apply on this corpus.
    #:
    #: **The table this replaced would have argued for the wrong value.** It
    #: recorded 0.20 at 49/54, the best cell in it; today 0.20 measures 46/54.
    #: A reader trusting it would have raised the floor and lost a case, which
    #: is what a stale measurement inside a decision does rather than merely
    #: mislead (L52).
    #:
    #: Re-sweep when the corpus changes - this number is a property of the
    #: corpus, not of the algorithm. It has now been re-swept twice for exactly
    #: that reason, and moved neither time.
    #: The abstention floor, applied to `rerank_relevance * arm agreement`.
    #:
    #: This number was moved twice in one session and the moves were noise. The
    #: arc is worth keeping because it is what a golden set too small to resolve
    #: a knob looks like from the inside:
    #:
    #:     0.08   chosen on 54 cases, 266 pages - both corpora flat there (L71)
    #:     0.03   corrected on 54 cases, 349 pages - 0.08 began over-refusing (L72)
    #:     0.08   restored on 79 cases, 349 pages - the knob is nearly flat (L74)
    #:
    #: With 25 more golden cases the combined pass count reads 81, 83, 82, 81,
    #: 81, 82, 81, 82, 82, 82, 81 of 99 across floors 0.01 to 0.11 - a one-case
    #: wobble over an eleven-fold range. The external corpus is indifferent
    #: everywhere in that band and the primary one reaches its best only at 0.08
    #: and above, so 0.08 maximises the worse of the two rather than the sum of
    #: one. Sweeping it is `scripts/floor_sweep.py`.
    min_relevance: float = 0.08
    #: A strong match is answered even when the arms disagree about it.
    #:
    #: Multiplying relevance by agreement refuses on *either* cause, and the
    #: failure decomposition at 79 golden cases showed the cost: seven of
    #: sixteen failures were answerable questions refused with agreement at
    #: 12%, one of them carrying relevance 0.56 - a good match thrown away
    #: because the two arms happened to pick different neighbours (L79).
    #:
    #: Swept over both corpora, this rescue never costs a correct refusal
    #: anywhere at or above 0.35 and removes three wrong ones:
    #:
    #:     rescue      none  0.60  0.50  0.40  0.35  0.30  0.20  0.15
    #:     correct       10    10    10    10    10     9     7     7
    #:     wrong          8     7     6     5     5     5     1     0
    #:
    #: Lower values score better on net and buy it by refusing fewer
    #: unanswerable questions, which is the gate's whole job; 0.40 sits in the
    #: region where the trade is one-directional.
    min_relevance_rescue: float = 0.40
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
        agreement = _arm_agreement(results)
        gate_signal = best_relevance * agreement
        weak = (gate_signal < config.min_relevance
                and best_relevance < config.min_relevance_rescue)
        if results[0].score < config.min_top_score or weak:
            return Answer(
                question=question,
                text=("The index contains nothing relevant to this question. "
                      f"Best query-term relevance was {best_relevance:.2f} across "
                      f"{agreement:.0%} arm agreement, giving {gate_signal:.2f} - "
                      f"below the {config.min_relevance:.2f} floor."),
                abstained=True, generator="none", retrieved=results,
                confidence=0.0,
                metrics={"reason": "below_relevance_floor",
                         "best_relevance": round(best_relevance, 4),
                         "arm_agreement": round(agreement, 4),
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


#: Below this many results the agreement share is too coarse to estimate.
_AGREEMENT_MIN_WINDOW = 5


def _arm_agreement(results: list[ScoredChunk]) -> float:
    """Share of the window that *both* retrieval arms found.

    A question the corpus answers tends to look answerable to a lexical search
    and to a dense one at the same time; a question that merely shares
    vocabulary with the corpus splits them. Measured over 43 answerable and 11
    unanswerable golden cases, `relevance x agreement` separates the two at
    **AUC 0.850**, against 0.763 for relevance alone and 0.78 or below for every
    other candidate tried across four sessions (L71).

    It is free: the ranks are already in the fusion components.

    **1.0 when only one arm ran**, which is not a detail. Disabling an arm makes
    every result single-sourced, so a naive share would be 0.0 and the gate
    would refuse everything - the same shape as the `use_rerank` defect that
    once silently disabled the gate's only input. A configuration flag must
    degrade behaviour, not switch off an unrelated safety check.
    """
    if len(results) < _AGREEMENT_MIN_WINDOW:
        # A share estimated from three results is not a share. On a corpus
        # smaller than the window both arms return nearly everything, and what
        # little they disagree on swings the fraction by a third at a time - a
        # synthetic three-document index scored 33% and had its answerable
        # question refused. Below the minimum the factor is neutral, so the gate
        # falls back to relevance alone rather than to noise (L71).
        return 1.0
    saw_dense = any("dense_rank" in r.components for r in results)
    saw_lexical = any("lexical_rank" in r.components for r in results)
    if not (saw_dense and saw_lexical):
        return 1.0
    both = sum(1 for r in results
               if "dense_rank" in r.components and "lexical_rank" in r.components)
    return both / len(results)


def _confidence(results: list[ScoredChunk], coverage: float) -> float:
    """A blunt, explainable confidence.

    Three signals, none of them a probability and none pretending to be: how
    strong the best match was, how much better it was than the fifth (a flat
    distribution means nothing stood out), and how well the answer is cited.

    **Every term is bounded 0..1 by construction**, which is the repair rather
    than a nicety. The first two used to be read off `ScoredChunk.score`, whose
    scale is set by `HeuristicReranker.base_weight`: when that moved 1.0 -> 5.0
    every top score landed above the 0.6 the strength term divided by, so
    strength was pinned at 1.0 for **all 48** answered goldens, 32 of them
    reported >= 0.99, and the measure's ability to separate right answers from
    wrong ones collapsed from AUC 0.665 to **0.519** - a coin flip (L69).

    `rerank_relevance` cannot do that: it is a coverage-times-answerability
    product in [0, 1] regardless of any weight. Measured over 35 right and 13
    wrong answers on the external corpus (`scripts/confidence_ab.py`):

        current, from the total score            AUC 0.519
        relevance only                           AUC 0.703
        relevance, relevance margin, coverage    AUC 0.665   <- this
        relevance, margin as share of top        AUC 0.673

    The relevance-based forms are indistinguishable from one another at this
    sample size and all of them beat the incumbent by a wide margin. This one is
    chosen because it is the only one whose every input is scale-free *and*
    keeps the three signals the docstring promises, so the next weight change
    cannot silently retire it.
    """
    relevance = [r.components.get("rerank_relevance", 0.0) for r in results]
    top = max(relevance, default=0.0)
    margin = top - relevance[min(4, len(relevance) - 1)] if relevance else 0.0
    strength = min(1.0, top / 0.5)
    separation = min(1.0, margin / 0.25) if len(results) > 1 else 0.5
    return round(0.5 * strength + 0.2 * separation + 0.3 * coverage, 4)
