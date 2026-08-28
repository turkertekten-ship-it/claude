"""Answer assembly: retrieve, ground, verify, return.

The generator is swappable; the contract is not. Whichever backend produces the
prose, the answer that comes out of here has been checked against the chunks
that were actually retrieved.
"""

from __future__ import annotations

import statistics
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
    #: Never fired on either golden set either, for a different reason: the
    #: extractive generator emits only sentences it can cite, so citation
    #: coverage is 1.000 at the *minimum* across all 74 questions. This is
    #: unreachable in *this configuration* rather than structurally - the Claude
    #: generator can produce a sentence it cannot attribute, which is exactly
    #: what this exists to refuse. Distinguishing the two mattered: one of these
    #: guards should be labelled dead and the other should not (L65).
    min_coverage: float = 0.5
    strict: bool = True
    #: Retrieval scores below this mean nothing was retrieved at all.
    #:
    #: **Structurally unreachable on a non-empty result list, and kept anyway.**
    #: The reranker's total carries two query-independent priors that are
    #: present whatever the chunk says: `authority_weight * (1.0/1.5) = 0.080`
    #: for a chunk whose metadata omits authority, and `position_weight = 0.150`
    #: at ordinal 0. A chunk matching *nothing at all* therefore scores 0.230 -
    #: 46x this floor - and 0.089 even at ordinal 100. Measured across both
    #: golden sets: the smallest top score observed is 0.2541 (external) and
    #: 0.5099 (primary), 51x and 102x above it, and the guard has never fired.
    #:
    #: That is the failure `rerank.py` describes above `rerank_relevance`: a
    #: total with priors folded in cannot answer "is this relevant at all". The
    #: check beside this one, `min_relevance`, does the job correctly by reading
    #: relevance alone, and subsumes this entirely.
    #:
    #: Not deleted. It costs one comparison, an empty result list is handled
    #: earlier, and it becomes live again the moment the query-independent
    #: weights are zeroed - which `authority_weight` at 0.0 would do. A cheap
    #: guard that is dead under today's weights and alive under a plausible
    #: configuration is worth keeping and worth labelling (L65).
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
    #:
    #: **What no value of this floor can do.** Three of the five remaining
    #: external gate failures are this gate answering a question it should
    #: refuse, so the obvious move is to raise the floor. It does not work, and
    #: the reason is that the two distributions overlap
    #: (`scripts/abstention_floor_curve.py`, over 61 answerable and 15
    #: abstainable goldens):
    #:
    #:   should answer   min .0850  p25 .3466  median .4542  p75 .5760  max 1.0
    #:   should abstain  min .0034  p25 .0198  median .0901  p75 .3114  max .7249
    #:
    #: The medians separate cleanly, which is why a floor works at all and why
    #: 12 of 15 abstain cases are caught. The tail does not. Catching "Which
    #: package sends mail over SMTP?" at .7249 needs a floor above it, which
    #: sits past the median of the answerable cases. Catching "What is the
    #: capital of France?" at .3303 needs ~.34, and 13 answerable cases score
    #: below that.
    #:
    #: The three that get through are not random: "sends mail over SMTP",
    #: "renders Jinja templates to PDF" (.5910), "pins dependency hashes for
    #: reproducible installs" (.2481). Each is a plausible conjunction of terms
    #: the corpus really contains, asked about a package it does not. That is
    #: the hardest case for any bag-of-terms relevance and it is a feature
    #: problem, not a threshold problem - so the next attempt here should be a
    #: different signal, not another sweep of this one.
    min_relevance: float = 0.19
    #: Which statistic of the retrieved chunks' relevance the floor is applied
    #: to. "max" asks whether *any* chunk looks relevant; "mean" asks whether
    #: the retrieved set as a whole does.
    #:
    #: Ranked by AUC over 61 answerable and 15 abstainable goldens
    #: (`scripts/abstention_signals.py`), mean separates the classes better than
    #: max - 0.863 against 0.845 - which is the kind of gap L22 found worth
    #: three end-to-end cases. The reasoning: a maximum over eight chunks is a
    #: single-sample extreme, so one spuriously good chunk carries the whole
    #: decision, and an out-of-corpus question can find one of those far more
    #: easily than it can find eight.
    #:
    #: AUC is for killing candidates, not choosing between survivors, so the
    #: shipped value is decided end to end, not by the 0.018. Each statistic
    #: swept against its own floor, since they are on different scales
    #: (`scripts/relevance_statistic_ab.py`):
    #:
    #:   max   floor   0.10   0.15   0.19*  0.22   0.25   0.30
    #:   external      46/54  47/54  49/54  48/54  47/54  44/54
    #:   primary       17/20  18/20  18/20  18/20  18/20  18/20
    #:   held-out      19/22  19/22  19/22  19/22  18/22  16/22
    #:
    #:   mean  floor   0.03   0.05   0.07   0.09   0.11   0.14   0.18
    #:   external      45/54  46/54  46/54  46/54  46/54  42/54  42/54
    #:   primary       15/20  16/20  17/20  17/20  17/20  18/20  18/20
    #:   held-out      19/22  20/22  20/22  19/22  18/22  19/22  16/22
    #:
    #: **max wins where it counts and loses everywhere else**, which is why the
    #: default is not the higher-AUC option. Best max is 49/54 on the gate
    #: against mean's 46; they tie at 18/20 on primary; and mean takes held-out
    #: 20/22 against 19 - the only configuration all session to move that set
    #: off 19/22. Three cases on the gate outweigh one on a set deliberately
    #: barely gated.
    #:
    #: The 0.018 of AUC did not merely fail to pay, it pointed the wrong way.
    #: L22 recorded a 0.010 AUC gain in this same gate being worth three
    #: end-to-end cases; here 0.018 costs three. AUC does not predict end-to-end
    #: behaviour in either direction, and both facts are now on record.
    relevance_statistic: str = "max"
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

        relevances = [r.components.get("rerank_relevance", 0.0) for r in results]
        best_relevance = (
            statistics.mean(relevances) if config.relevance_statistic == "mean"
            else max(relevances, default=0.0)
        ) if relevances else 0.0
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
