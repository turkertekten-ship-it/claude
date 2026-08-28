"""The evaluation harness.

Without this, "the retrieval got better" is an opinion. The harness turns it
into a number that a change either improves or does not, and a regression gate
CI can fail on.

A golden case states what *should* be retrieved, expressed as substrings of a
document URI or title rather than chunk ids - chunk ids change every time the
chunker's configuration changes, and a golden set that has to be rewritten
whenever the code changes is a golden set nobody maintains.

Negative cases matter as much as positive ones. `expect_abstain` cases assert
the system *refuses* out-of-corpus questions, which is the behaviour that
separates a grounded system from a confident one.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from oodarag.eval.metrics import hit_at_k, mrr, ndcg_at_k, recall_at_k, summarize
from oodarag.eval.contamination import ContaminationReport, detect
from oodarag.eval.discrimination import DiscriminationReport
from oodarag.eval.discrimination import check as check_discrimination
from oodarag.generate.answer import AnswerGenerator
from oodarag.util.logging import get_logger

log = get_logger("eval")


@dataclass(slots=True)
class Golden:
    question: str
    #: Substrings; a retrieved document matches if any appears in its uri or title.
    expect_sources: list[str] = field(default_factory=list)
    #: Substrings that should appear in the answer text (case-insensitive).
    expect_answer_contains: list[str] = field(default_factory=list)
    #: True for out-of-corpus questions the system must refuse.
    expect_abstain: bool = False
    filters: dict[str, Any] | None = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    question: str
    passed: bool
    recall: float = 0.0
    precision: float = 0.0
    hit: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    citation_coverage: float = 0.0
    abstained: bool = False
    latency_ms: float = 0.0
    failures: list[str] = field(default_factory=list)
    retrieved_uris: list[str] = field(default_factory=list)
    #: True when the golden states expected sources. Retrieval metrics are
    #: meaningless for a case that expects an abstention - there is nothing to
    #: retrieve - and averaging their zeros in means every negative case added
    #: to the set mechanically lowers reported recall.
    graded: bool = False


@dataclass
class EvalReport:
    cases: list[CaseResult] = field(default_factory=list)
    k: int = 8
    duration_s: float = 0.0
    index_stats: dict[str, Any] = field(default_factory=dict)
    contamination: ContaminationReport | None = None
    discrimination: DiscriminationReport | None = None
    excluded_sources: tuple[str, ...] = ()
    #: question -> document ids hidden from retrieval for that question only.
    quarantined: dict[str, list[str]] = field(default_factory=dict)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def pass_rate(self) -> float:
        return round(self.passed / len(self.cases), 4) if self.cases else 0.0

    def aggregate(self) -> dict[str, Any]:
        # Retrieval metrics over the cases that state a retrieval expectation,
        # and citation coverage over the cases that were meant to be answered.
        # Mixing abstention cases into either turns "we added more negative
        # cases" into "retrieval got worse".
        retrieval_cases = [c for c in self.cases if c.graded]
        positive = [c for c in self.cases if c.graded and not c.abstained]
        return {
            "cases": len(self.cases),
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            f"recall@{self.k}": summarize([c.recall for c in retrieval_cases]),
            f"precision@{self.k}": summarize([c.precision for c in retrieval_cases]),
            f"hit@{self.k}": summarize([c.hit for c in retrieval_cases]),
            "mrr": summarize([c.mrr for c in retrieval_cases]),
            f"ndcg@{self.k}": summarize([c.ndcg for c in retrieval_cases]),
            "citation_coverage": summarize([c.citation_coverage for c in positive]),
            "latency_ms": summarize([c.latency_ms for c in self.cases]),
            "duration_s": round(self.duration_s, 2),
        }

    def failures(self) -> list[CaseResult]:
        return [c for c in self.cases if not c.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "aggregate": self.aggregate(),
            "index": self.index_stats,
            "excluded_sources": list(self.excluded_sources),
            "quarantined": self.quarantined,
            "contamination": self.contamination.as_dict() if self.contamination else None,
            "discrimination": (self.discrimination.as_dict()
                               if self.discrimination else None),
            "cases": [asdict(c) for c in self.cases],
        }

    def to_markdown(self) -> str:
        agg = self.aggregate()
        lines = [
            "# Retrieval evaluation",
            "",
            f"**{self.passed}/{len(self.cases)} cases passed** ({self.pass_rate:.0%})  ",
            (f"Retrieval metrics over {sum(1 for c in self.cases if c.graded)} graded "
             f"cases; {sum(1 for c in self.cases if not c.graded)} abstention cases "
             f"are excluded from them.  "),
            f"Index: {self.index_stats.get('documents', '?')} documents, "
            f"{self.index_stats.get('chunks', '?')} chunks  ",
            f"Duration: {agg['duration_s']}s",
            "",
            (f"Excluded sources: {', '.join(self.excluded_sources)}  "
             if self.excluded_sources else ""),
            (self.contamination.summary() if self.contamination else ""),
            (self.discrimination.summary() if self.discrimination else ""),
            # Two different counts, because they answer different questions and
            # had been reported under near-identical labels: the run log printed
            # the distinct-document count and this line printed the sum of
            # per-question holdouts, so one run said "14" and "29" about the
            # same operation. A document that contaminates two questions is held
            # out twice and is one document. `internal/PLAN.md` had recorded the
            # holdout total as a document count.
            (f"Quarantined {len({d for ds in self.quarantined.values() for d in ds})} "
             f"distinct document(s) as "
             f"{sum(len(d) for d in self.quarantined.values())} per-question "
             f"holdout(s), across {len(self.quarantined)} question(s)."
             if self.quarantined else ""),
            "",
            "| Metric | mean | p50 | min |",
            "|---|---|---|---|",
        ]
        for key in (f"recall@{self.k}", f"precision@{self.k}", f"hit@{self.k}",
                    "mrr", f"ndcg@{self.k}", "citation_coverage", "latency_ms"):
            stat = agg[key]
            lines.append(f"| {key} | {stat['mean']} | {stat['p50']} | {stat['min']} |")
        if failures := self.failures():
            lines += ["", "## Failing cases", ""]
            for case in failures:
                lines.append(f"- **{case.question}**")
                for failure in case.failures:
                    lines.append(f"  - {failure}")
        return "\n".join(lines) + "\n"


def load_goldens(path: str | Path) -> list[Golden]:
    """Read a JSONL golden set. Blank lines and `#` comments are ignored."""
    goldens: list[Golden] = []
    for line_number, line in enumerate(Path(path).read_text("utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            goldens.append(Golden(**json.loads(stripped)))
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"{path}:{line_number}: {e}") from e
    return goldens


class EvalHarness:
    def __init__(self, generator: AnswerGenerator, k: int = 8,
                 exclude_sources: tuple[str, ...] = (),
                 quarantine_contaminated: bool = True) -> None:
        self.generator = generator
        self.k = k
        #: Hide, per question, the documents that contain that question. Any
        #: system indexing its own repository will eventually index the test
        #: asserting a question is unanswerable - which makes it answerable and
        #: silently inverts the result. Excluding whole sources is too blunt
        #: (the rest of that source is legitimate corpus); quarantining the
        #: specific contaminated documents for the specific affected question
        #: measures what the eval claims to measure.
        self.quarantine_contaminated = quarantine_contaminated
        #: Source systems held out of the eval index. Sources that record the
        #: evaluation itself - session transcripts above all - contaminate the
        #: golden set and must be excluded or the numbers are meaningless.
        self.exclude_sources = exclude_sources

    def run(self, goldens: list[Golden]) -> EvalReport:
        report = EvalReport(k=self.k, excluded_sources=self.exclude_sources)
        store = self.generator.retriever.store
        report.index_stats = store.stats()
        report.contamination = detect(
            store, [g.question for g in goldens],
            negative_questions={g.question for g in goldens if g.expect_abstain},
            expected_sources={g.question: g.expect_sources for g in goldens
                              if g.expect_sources},
        )
        # The other half of "is this golden set measuring anything?".
        # Contamination asks whether the corpus gives the answer away;
        # this asks whether the expectation picks a document out at all.
        report.discrimination = check_discrimination(store, goldens)
        if not report.discrimination.clean:
            log.warn("golden expectations do not discriminate",
                     summary=report.discrimination.summary()[:220])

        quarantine: dict[str, set[str]] = {}
        if not report.contamination.clean:
            log.warn("golden set contamination detected",
                     summary=report.contamination.summary()[:220])
            if self.quarantine_contaminated:
                for finding in report.contamination.fatal_findings:
                    quarantine.setdefault(finding.question, set()).add(finding.doc_id)
                log.info("quarantining contaminated documents",
                         questions=len(quarantine),
                         documents=len({d for s in quarantine.values() for d in s}))
        report.quarantined = {q: sorted(d) for q, d in quarantine.items()}
        started = time.monotonic()

        for golden in goldens:
            case_started = time.monotonic()
            filters = dict(golden.filters or {})
            if self.exclude_sources:
                filters["exclude_source_system"] = list(self.exclude_sources)
            if contaminated := quarantine.get(golden.question):
                filters["exclude_doc_ids"] = sorted(contaminated)
            answer = self.generator.answer(
                golden.question, filters=filters or None, top_k=self.k
            )
            latency = (time.monotonic() - case_started) * 1000

            uris = [
                f"{r.citation_uri} {r.citation_title}" for r in answer.retrieved
            ]
            # Graded by *document*, not chunk: a golden that names chunk ids
            # breaks on every chunker change.
            #
            # Each retrieved position is mapped to the expected source it
            # satisfies, or to a unique sentinel. Building the relevant set from
            # the *retrieved* list instead - which is what this did - makes the
            # relevant set a subset of the retrieved set by construction, so
            # recall is 1.0 whenever anything matched and 1.0 again (via the
            # empty-set guard) when nothing did. The metric documented as "the
            # ceiling on everything downstream" reported a constant.
            expected = [e.lower() for e in golden.expect_sources]
            ranked = []
            for i, blob in enumerate(uris):
                lowered = blob.lower()
                match = next((e for e in expected if e in lowered), None)
                ranked.append(match if match is not None else f"\x00miss{i}")
            relevant_positions = set(expected)

            case = CaseResult(
                question=golden.question,
                passed=True,
                abstained=answer.abstained,
                latency_ms=round(latency, 2),
                citation_coverage=float(answer.metrics.get("citation_coverage", 0.0)),
                retrieved_uris=[r.citation_uri for r in answer.retrieved[:self.k]],
            )
            if golden.expect_sources:
                case.graded = True
                case.recall = recall_at_k(ranked, relevant_positions, self.k)
                # Precision counts filled slots, not distinct sources: two
                # chunks from one expected document are two useful results.
                filled = sum(1 for r in ranked[:self.k] if r in relevant_positions)
                case.precision = filled / min(self.k, len(ranked)) if ranked else 0.0
                case.hit = hit_at_k(ranked, relevant_positions, self.k)
                case.mrr = mrr(ranked, relevant_positions)
                case.ndcg = ndcg_at_k(ranked, relevant_positions, self.k)
                if not set(ranked[:self.k]) & relevant_positions:
                    case.failures.append(
                        f"none of {golden.expect_sources} retrieved; "
                        f"got {case.retrieved_uris[:3]}"
                    )

            if golden.expect_abstain and not answer.abstained:
                case.failures.append(
                    f"expected abstention, answered with confidence {answer.confidence}"
                )
            if not golden.expect_abstain and answer.abstained:
                case.failures.append(f"unexpected abstention: {answer.text[:120]}")

            lowered = answer.text.lower()
            for expected in golden.expect_answer_contains:
                if expected.lower() not in lowered:
                    case.failures.append(f"answer missing {expected!r}")

            case.passed = not case.failures
            report.cases.append(case)

        report.duration_s = time.monotonic() - started
        log.info("eval complete", cases=len(report.cases), passed=report.passed,
                 rate=report.pass_rate, secs=round(report.duration_s, 2))
        return report
