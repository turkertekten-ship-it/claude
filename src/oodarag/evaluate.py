"""Measure retrieval instead of asserting it.

"Retrieval got better" is the least verifiable claim in this codebase, and the
easiest to believe. This module makes it a number by running fixed questions
with known-relevant documents against the live index.

Four metrics, because they disagree in useful ways:

  - **recall@k** — did the right document appear at all? The ceiling on every
    downstream stage: what retrieval misses, no generator can recover.
  - **MRR** — how high was the *first* right answer? What matters when a reader
    only looks at the top hit.
  - **nDCG@k** — how good is the whole ordering, discounting by log2 of rank so
    that a swap at positions 1 and 2 counts far more than one at 19 and 20.
  - **citation coverage** — did the answer actually cite retrieved chunks, and
    did it abstain when it should have? Perfect retrieval with fabricated
    citations is still a failure, and the first three metrics cannot see it.

A single number would hide the trade-off between them; a change that raises
recall while lowering MRR has made the retriever wider and blunter, and the
report should show that rather than average it away.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.generate import ExtractiveGenerator, Generator, verify_citations
from oodarag.retrieve import Retriever
from oodarag.util.logging import get_logger

log = get_logger("evaluate")


@dataclass(slots=True)
class GoldenCase:
    """One question with the documents that should answer it."""

    question: str
    relevant_doc_ids: list[str] = field(default_factory=list)
    relevant_uris: list[str] = field(default_factory=list)
    should_abstain: bool = False
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> GoldenCase:
        return cls(
            question=str(payload.get("question", "")).strip(),
            relevant_doc_ids=[str(x) for x in payload.get("relevant_doc_ids", [])],
            relevant_uris=[str(x) for x in payload.get("relevant_uris", [])],
            should_abstain=bool(payload.get("should_abstain", False)),
            notes=str(payload.get("notes", "")),
        )

    @property
    def has_expectation(self) -> bool:
        return bool(self.relevant_doc_ids or self.relevant_uris or self.should_abstain)


def load_goldens(path: str | Path) -> tuple[list[GoldenCase], list[str]]:
    """Read a JSONL golden file. Returns the cases and the lines that failed.

    Malformed lines are reported rather than skipped silently: an eval set that
    quietly shrank is worse than one that failed loudly, because the score goes
    up either way.
    """
    cases: list[GoldenCase] = []
    errors: list[str] = []
    p = Path(path)
    if not p.exists():
        return cases, [f"{p}: no such file"]

    for n, line in enumerate(p.read_text("utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            case = GoldenCase.from_dict(json.loads(line))
        except (ValueError, TypeError) as e:
            errors.append(f"{p}:{n}: {e}")
            continue
        if not case.question:
            errors.append(f"{p}:{n}: case has no question")
            continue
        if not case.has_expectation:
            errors.append(f"{p}:{n}: case states no expectation, so it cannot pass or fail")
            continue
        cases.append(case)
    return cases, errors


# ------------------------------------------------------------------- metrics


def dedupe(ids: list[str]) -> list[str]:
    """Collapse repeats, keeping first position.

    Retrieval returns *chunks*, but these metrics are about *documents*: a
    document whose chunks occupy ranks 1, 2 and 3 was retrieved once, at rank
    1. Without this collapse a document's gain is counted once per chunk and
    nDCG exceeds 1.0, which is not a rounding artefact but a wrong answer —
    the measure is defined as a ratio against the best possible ordering.
    """
    seen: set[str] = set()
    out: list[str] = []
    for ident in ids:
        if ident not in seen:
            seen.add(ident)
            out.append(ident)
    return out


def recall_at_k(retrieved_ids: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant documents present in the top k distinct results."""
    if not relevant:
        return 0.0
    top = set(dedupe(retrieved_ids)[:k])
    return len(top & relevant) / len(relevant)


def reciprocal_rank(retrieved_ids: list[str], relevant: set[str]) -> float:
    """1/rank of the first relevant document; 0 when none appears."""
    for rank, ident in enumerate(dedupe(retrieved_ids), start=1):
        if ident in relevant:
            return 1.0 / rank
    return 0.0


def dcg(gains: list[float]) -> float:
    """Discounted cumulative gain with the standard log2(rank + 1) discount."""
    return sum(g / math.log2(i + 1) for i, g in enumerate(gains, start=1))


def ndcg_at_k(retrieved_ids: list[str], relevant: set[str], k: int) -> float:
    """nDCG with binary relevance, normalized by the best possible ordering.

    Always in [0, 1]: the ideal ordering places every relevant document that
    could fit at the top, so no real ordering can beat it. A value above 1 means
    a document was double-counted, which is why the input is deduplicated first.
    """
    if not relevant:
        return 0.0
    ranked = dedupe(retrieved_ids)[:k]
    gains = [1.0 if ident in relevant else 0.0 for ident in ranked]
    ideal = [1.0] * min(len(relevant), k)
    best = dcg(ideal)
    if not best:
        return 0.0
    return min(1.0, dcg(gains) / best)


def detect_contamination(question: str, texts: list[str]) -> str:
    """Return the source of a near-verbatim copy of the question, or "".

    An evaluation whose questions are inside the corpus measures nothing. The
    question retrieves itself, every metric improves, and the abstention cases
    — the ones that check the retriever declines when it should — quietly stop
    working. It is the most flattering way for an eval to be wrong, so it is
    checked rather than assumed absent.

    The check is deliberately crude: an exact substring match on a normalized
    form. It catches the real case (a golden file, or a captured report from a
    previous run, indexed alongside the corpus) without flagging a document
    that merely discusses the same subject.
    """
    needle = " ".join(question.lower().split()).rstrip("?").strip()
    if len(needle) < 25:
        return ""
    for text in texts:
        if needle in " ".join(text.lower().split()):
            return text[:120]
    return ""


@dataclass(slots=True)
class CaseResult:
    question: str
    recall: float
    mrr: float
    ndcg: float
    abstained: bool
    expected_abstain: bool
    citation_problems: list[str] = field(default_factory=list)
    retrieved: list[str] = field(default_factory=list)
    latency_s: float = 0.0
    contaminated_by: str = ""

    @property
    def passed(self) -> bool:
        """A case passes on the expectation it actually stated.

        A contaminated case never passes, whatever its metrics say: its score
        is measuring the leak, not the retriever.
        """
        if self.contaminated_by:
            return False
        if self.expected_abstain:
            return self.abstained and not self.citation_problems
        return self.recall > 0.0 and not self.citation_problems


@dataclass(slots=True)
class EvalReport:
    k: int
    cases: list[CaseResult] = field(default_factory=list)
    load_errors: list[str] = field(default_factory=list)

    def _mean(self, attr: str) -> float:
        scored = [c for c in self.cases if not c.expected_abstain]
        if not scored:
            return 0.0
        return sum(getattr(c, attr) for c in scored) / len(scored)

    @property
    def summary(self) -> dict[str, Any]:
        total = len(self.cases)
        passed = sum(1 for c in self.cases if c.passed)
        problems = sum(len(c.citation_problems) for c in self.cases)
        return {
            "cases": total,
            "passed": passed,
            "failed": total - passed,
            f"recall@{self.k}": round(self._mean("recall"), 4),
            "mrr": round(self._mean("mrr"), 4),
            f"ndcg@{self.k}": round(self._mean("ndcg"), 4),
            "citation_problems": problems,
            "contaminated": sum(1 for c in self.cases if c.contaminated_by),
            "abstentions": sum(1 for c in self.cases if c.abstained),
            "load_errors": len(self.load_errors),
            "mean_latency_s": round(
                sum(c.latency_s for c in self.cases) / total, 4
            ) if total else 0.0,
        }

    def render(self) -> str:
        lines = [f"{'RESULT':<7} {'RECALL':>6} {'MRR':>6} {'NDCG':>6}  QUESTION"]
        lines.append("-" * 78)
        for c in self.cases:
            verdict = "pass" if c.passed else "FAIL"
            lines.append(
                f"{verdict:<7} {c.recall:>6.3f} {c.mrr:>6.3f} {c.ndcg:>6.3f}  "
                f"{c.question[:44]}"
            )
            if c.contaminated_by:
                lines.append(
                    f"        ! the corpus contains this question verbatim: "
                    f"{c.contaminated_by[:70]!r}"
                )
            for problem in c.citation_problems:
                lines.append(f"        ! {problem}")
        lines.append("-" * 78)
        for key, value in self.summary.items():
            lines.append(f"{key:>20}: {value}")
        for err in self.load_errors:
            lines.append(f"  load error: {err}")
        return "\n".join(lines)

    @property
    def exit_code(self) -> int:
        """0 when every case passed and the file loaded; 1 otherwise."""
        if self.load_errors:
            return 1
        return 0 if all(c.passed for c in self.cases) else 1


def evaluate(
    retriever: Retriever,
    goldens: list[GoldenCase],
    *,
    k: int = 8,
    generator: Generator | None = None,
    load_errors: list[str] | None = None,
) -> EvalReport:
    """Run every golden case against the live index."""
    gen = generator or ExtractiveGenerator()
    report = EvalReport(k=k, load_errors=list(load_errors or []))

    for case in goldens:
        started = time.monotonic()
        hits = retriever.search(case.question, k)
        answer = gen.generate(case.question, hits)
        elapsed = time.monotonic() - started

        # Match on whichever identifier the case supplied. URIs are the more
        # durable key across a re-ingest, since doc_ids depend on the connector
        # key while a URI is a property of the source.
        if case.relevant_uris:
            retrieved_ids = [h.citation_uri for h in hits]
            relevant = set(case.relevant_uris)
        else:
            retrieved_ids = [h.chunk.doc_id for h in hits]
            relevant = set(case.relevant_doc_ids)

        report.cases.append(
            CaseResult(
                contaminated_by=detect_contamination(
                    case.question, [h.chunk.text for h in hits]
                ),
                question=case.question,
                recall=recall_at_k(retrieved_ids, relevant, k),
                mrr=reciprocal_rank(retrieved_ids, relevant),
                ndcg=ndcg_at_k(retrieved_ids, relevant, k),
                abstained=answer.abstained,
                expected_abstain=case.should_abstain,
                citation_problems=verify_citations(answer),
                retrieved=dedupe(retrieved_ids)[:k],
                latency_s=elapsed,
            )
        )

    log.info("evaluation complete", **report.summary)
    return report
