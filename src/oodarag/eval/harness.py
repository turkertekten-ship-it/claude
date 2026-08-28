"""Run the golden questions and say whether retrieval got better or worse.

Two things make this more than a scorecard.

**Abstention cases are first-class.** A golden set with no unanswerable
questions cannot distinguish a system that knows things from one that bluffs,
so `should_abstain` is a scored outcome and a wrong non-abstention counts
against the run. That is the metric that would catch this system starting to
invent.

**Regression is a comparison, not a number.** A report on its own tells you
almost nothing; a report against a saved baseline tells you whether the change
you just made helped. `compare` fails on a material drop and passes silently
otherwise, so it can sit in a check.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from oodarag.answer.extractive import ExtractiveAnswerer
from oodarag.answer.verify import coverage, verify_citations
from oodarag.eval import metrics
from oodarag.util.logging import get_logger

log = get_logger("eval")

DEFAULT_GOLDENS = Path("evals/goldens.jsonl")


@dataclass(slots=True)
class Golden:
    question: str
    expected_doc_ids: list[str] = field(default_factory=list)
    expected_answer_substrings: list[str] = field(default_factory=list)
    should_abstain: bool = False
    note: str = ""


@dataclass(slots=True)
class CaseResult:
    question: str
    should_abstain: bool
    abstained: bool
    recall_at_5: float
    mrr: float
    ndcg_at_5: float
    citation_coverage: float
    confidence: float
    substrings_found: int
    substrings_expected: int
    passed: bool
    why: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvalReport:
    cases: list[CaseResult] = field(default_factory=list)
    aggregate: dict[str, float] = field(default_factory=dict)
    corpus: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    def as_dict(self) -> dict[str, Any]:
        return {"aggregate": self.aggregate, "corpus": self.corpus,
                "cases": [c.as_dict() for c in self.cases]}

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, ensure_ascii=False, sort_keys=True)

    def to_markdown(self) -> str:
        lines = ["# Retrieval evaluation", "",
                 f"**{self.passed}/{len(self.cases)} cases passed**", ""]
        for k in sorted(self.aggregate):
            lines.append(f"- {k}: {self.aggregate[k]:.4f}")
        lines += ["", "| ok | question | abstain (want/got) | recall@5 | MRR | cites |",
                  "|---|---|---|---|---|---|"]
        for c in self.cases:
            mark = "yes" if c.passed else "NO"
            q = c.question if len(c.question) <= 54 else c.question[:51] + "..."
            lines.append(
                f"| {mark} | {q} | {int(c.should_abstain)}/{int(c.abstained)} | "
                f"{c.recall_at_5:.2f} | {c.mrr:.2f} | {c.citation_coverage:.2f} |")
        failures = [c for c in self.cases if not c.passed]
        if failures:
            lines += ["", "## Failures", ""]
            for c in failures:
                lines.append(f"- **{c.question}** — {c.why}")
        return "\n".join(lines)


class EvalHarness:
    """Runs the golden set against a retriever and an answerer."""

    def __init__(self, retriever: Any, answerer: ExtractiveAnswerer | None = None,
                 *, k: int = 5) -> None:
        self.retriever = retriever
        self.answerer = answerer or ExtractiveAnswerer()
        self.k = k

    @staticmethod
    def load(path: Path | str = DEFAULT_GOLDENS) -> list[Golden]:
        p = Path(path)
        if not p.exists():
            log.error("golden set missing; nothing to evaluate", path=str(p))
            return []
        out: list[Golden] = []
        for n, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                raw = json.loads(line)
                out.append(Golden(
                    question=raw["question"],
                    expected_doc_ids=list(raw.get("expected_doc_ids", [])),
                    expected_answer_substrings=list(raw.get("expected_answer_substrings", [])),
                    should_abstain=bool(raw.get("should_abstain", False)),
                    note=str(raw.get("note", "")),
                ))
            except (json.JSONDecodeError, KeyError) as e:
                log.warn("golden line skipped", line_no=n, err=str(e)[:120])
        return out

    def run(self, goldens: list[Golden]) -> EvalReport:
        report = EvalReport()
        confidences: list[float] = []
        correct: list[bool] = []

        for g in goldens:
            scored = self.retriever.retrieve(g.question, k=self.k)
            # Document-level relevance: a golden names documents, not chunk ids,
            # because chunk ids move whenever the splitter changes and a golden
            # set that breaks on a refactor stops being run.
            ranked_docs: list[str] = []
            for s in scored:
                did = _doc_key(s)
                if did not in ranked_docs:
                    ranked_docs.append(did)

            answer = verify_citations(self.answerer.answer(g.question, scored), scored)

            found = sum(1 for sub in g.expected_answer_substrings
                        if sub.lower() in (answer.text or "").lower())
            rec = metrics.recall_at_k(ranked_docs, g.expected_doc_ids, self.k)
            case = CaseResult(
                question=g.question,
                should_abstain=g.should_abstain,
                abstained=answer.abstained,
                recall_at_5=rec,
                mrr=metrics.mrr(ranked_docs, g.expected_doc_ids),
                ndcg_at_5=metrics.ndcg_at_k(ranked_docs, g.expected_doc_ids, self.k),
                citation_coverage=coverage(answer),
                confidence=answer.confidence,
                substrings_found=found,
                substrings_expected=len(g.expected_answer_substrings),
                passed=True,
            )

            # A wrong abstention decision fails the case outright: bluffing on an
            # unanswerable question is the failure this set exists to catch.
            if g.should_abstain and not answer.abstained:
                case.passed, case.why = False, "answered a question it should have refused"
            elif not g.should_abstain and answer.abstained:
                case.passed, case.why = False, f"abstained: {answer.metrics.get('abstain_reason', '?')}"
            elif g.expected_doc_ids and rec == 0.0:
                case.passed, case.why = False, "no expected document in the top k"
            elif g.expected_answer_substrings and found == 0:
                case.passed, case.why = False, "none of the expected substrings appeared"

            report.cases.append(case)
            confidences.append(answer.confidence)
            correct.append(case.passed)

        n = len(report.cases) or 1
        report.aggregate = {
            "pass_rate": report.passed / n,
            "recall_at_5": sum(c.recall_at_5 for c in report.cases) / n,
            "mrr": sum(c.mrr for c in report.cases) / n,
            "ndcg_at_5": sum(c.ndcg_at_5 for c in report.cases) / n,
            "citation_coverage": sum(c.citation_coverage for c in report.cases) / n,
            "abstention_rate": metrics.abstention_rate([c.abstained for c in report.cases]),
            "calibration_error": metrics.calibration_error(confidences, correct),
        }
        return report


def compare(current: EvalReport, baseline: dict[str, Any], *,
            tolerance: float = 0.05) -> list[str]:
    """Material drops against a saved baseline. Empty means no regression.

    Tolerance is one-sided on purpose: improvement never fails a check, and a
    drop inside the tolerance is noise rather than news. The metrics compared
    are the ones a change can plausibly break.
    """
    drops: list[str] = []
    base = baseline.get("aggregate", {})
    for key in ("pass_rate", "recall_at_5", "mrr", "ndcg_at_5", "citation_coverage"):
        if key not in base:
            continue
        was, now = float(base[key]), float(current.aggregate.get(key, 0.0))
        if now < was - tolerance:
            drops.append(f"{key}: {was:.4f} -> {now:.4f} (drop {was - now:.4f})")
    # A jump in abstention is a regression even though the number goes up.
    if "abstention_rate" in base:
        was, now = float(base["abstention_rate"]), float(current.aggregate["abstention_rate"])
        if now > was + tolerance:
            drops.append(f"abstention_rate: {was:.4f} -> {now:.4f} (system got quieter)")
    return drops


def _doc_key(scored: Any) -> str:
    """A stable, human-readable document key for goldens to name.

    Prefers the source path in metadata over the hashed doc_id, so a golden set
    can be written by a person and survives a re-index.
    """
    doc = getattr(scored, "document", None)
    if doc is not None:
        meta = getattr(doc, "metadata", {}) or {}
        if meta.get("path"):
            return str(meta["path"])
        if getattr(doc, "uri", ""):
            return str(doc.uri)
    return scored.chunk.doc_id
