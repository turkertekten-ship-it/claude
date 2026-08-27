"""Retrieval quality as a number you can argue with.

This module exists so that a retrieval change is settled by measurement rather
than by argument. Every metric is computed here from first principles, in a few
lines each, with the formula on screen: the point of an eval harness is that
somebody tuning `rrf_k` at midnight can check the arithmetic themselves instead
of trusting a library they have never read. Nothing here is imported from
anywhere - there is no dependency to install and no version of a metric library
to disagree about.

Four decisions shape the numbers.

**Relevance is judged at document level, matching on URI or doc id.** A golden
labels the *documents* that ought to answer the question, because chunk ids are
derived from the chunker's configuration: labelling chunks would invalidate the
entire golden set every time `target_tokens` moved, which is precisely the
change an eval is supposed to be able to measure. URIs are matched by path
suffix as well as by equality, because the offline corpus is addressed as
`file:///abs/path/evals/corpus/x.md` and an absolute path is a property of the
machine, not of the corpus.

**Retrieval metrics are averaged only over goldens that carry labels.** A
golden with `should_abstain=True` has no relevant documents by construction;
scoring it as recall 0.0 would drag every retrieval number down in proportion
to how many honesty cases the golden set contains, which would penalise adding
them. Those goldens are graded on whether the pipeline actually abstained, and
`render()` prints both denominators so the split is never a surprise.

**Citation coverage counts only answers that asserted something.** An
abstention carries no citations, so "all of its citations resolve" is vacuously
true; including abstentions in the denominator would let a pipeline that
abstains on everything score a perfect 1.0 on honesty.

**False abstention is reported next to abstention, always.** Raising
`min_confidence` improves the apparent quality of whatever answers survive - it
is the cheapest way to make an eval look better and the easiest to mistake for
progress. `false_abstention_rate` is the share of *answerable* goldens the
pipeline declined anyway, so the trade is visible in the same table as the win.

A question that raises is counted, not fatal: `evaluate` records the exception
in that question's row and carries on, because an eval that dies on question
three tells you less than one that finishes and reports three failures.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from oodarag.models import Answer, ScoredChunk
from oodarag.util.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - the annotation is all that is needed
    # Imported for typing only. `evaluate` uses nothing but `.ask()`, so a test
    # double never has to construct a real Pipeline (and importing it eagerly
    # would drag the store, the indexes and an embedder into every eval import).
    from oodarag.pipeline import Pipeline

log = get_logger("eval")

#: Rows printed in the "worst questions" section of `render()`. Three, because a
#: report nobody reads is a report that does nothing: the failures worth staring
#: at are the bottom few, and a full dump of 200 questions gets skimmed.
_WORST_N = 3

#: Terminal width the table is laid out for.
_QUESTION_COL = 58


@dataclass(slots=True)
class Golden:
    """One labelled question.

    `relevant_uris` and `relevant_doc_ids` are alternative spellings of the same
    label and are unioned, never intersected: a URI is what a human can write by
    hand, a doc id is what a script can extract from an existing index, and a
    golden set assembled from both should not require its author to keep the two
    in sync.
    """

    question: str
    relevant_uris: list[str] = field(default_factory=list)
    relevant_doc_ids: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    should_abstain: bool = False

    @property
    def targets(self) -> int:
        """How many distinct documents this question is expected to surface."""
        return len(self.relevant_uris) + len(self.relevant_doc_ids)

    @property
    def labelled(self) -> bool:
        return self.targets > 0


@dataclass(slots=True)
class EvalReport:
    n: int = 0
    recall_at_k: float = 0.0
    mrr: float = 0.0
    ndcg_at_k: float = 0.0
    citation_coverage: float = 0.0
    abstention_rate: float = 0.0
    false_abstention_rate: float = 0.0
    per_question: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "recall_at_k": round(self.recall_at_k, 4),
            "mrr": round(self.mrr, 4),
            "ndcg_at_k": round(self.ndcg_at_k, 4),
            "citation_coverage": round(self.citation_coverage, 4),
            "abstention_rate": round(self.abstention_rate, 4),
            "false_abstention_rate": round(self.false_abstention_rate, 4),
            "per_question": self.per_question,
        }

    def render(self) -> str:
        """An aligned terminal table plus the worst questions by reciprocal rank.

        Every metric prints the denominator it was averaged over. Without it,
        `recall@k 1.000` over the two labelled goldens in a set of forty reads
        exactly like `recall@k 1.000` over all forty.
        """
        k = self._k()
        labelled = [r for r in self.per_question if r.get("targets", 0) and not r.get("error")]
        # Every denominator excludes rows that errored, because the averages
        # excluded them too: a printed denominator that disagrees with the one
        # actually divided by is worse than printing none at all.
        answerable = [r for r in self.per_question
                      if not r.get("should_abstain") and not r.get("error")]
        asked = [r for r in self.per_question if not r.get("error")]
        answered = [r for r in asked if not r.get("abstained")]
        failed = [r for r in self.per_question if r.get("error")]

        rows = [
            (f"recall@{k}", self.recall_at_k, f"{len(labelled)} labelled"),
            ("MRR", self.mrr, f"{len(labelled)} labelled"),
            (f"nDCG@{k}", self.ndcg_at_k, f"{len(labelled)} labelled"),
            ("citation coverage", self.citation_coverage, f"{len(answered)} answered"),
            ("abstention rate", self.abstention_rate, f"{len(asked)} asked"),
            ("false abstention", self.false_abstention_rate, f"{len(answerable)} answerable"),
        ]

        out: list[str] = []
        out.append(f"eval: {self.n} goldens  "
                   f"({len(labelled)} labelled, "
                   f"{sum(1 for r in self.per_question if r.get('should_abstain'))}"
                   f" expected abstentions"
                   f"{f', {len(failed)} failed' if failed else ''})")
        out.append("")
        out.append(f"  {'metric':<20}{'value':>8}   {'averaged over':<16}")
        out.append(f"  {'-' * 20}{'-' * 8}   {'-' * 16}{'-' * 10}")
        for name, value, over in rows:
            out.append(f"  {name:<20}{value:>8.3f}   {over:<16}{_bar(value)}")

        misses = [r for r in self.per_question if r.get("must_include_missing")]
        if misses:
            out.append("")
            out.append(f"  must_include misses: {len(misses)}")
            for row in misses[:_WORST_N]:
                missing = ", ".join(str(m) for m in row["must_include_missing"])
                out.append(f"    - {_clip(row['question'], _QUESTION_COL)}  [{missing}]")

        graded = sorted(labelled, key=lambda r: (r.get("rr", 0.0), r.get("recall", 0.0)))
        if graded:
            out.append("")
            out.append(f"  worst {min(_WORST_N, len(graded))} by MRR")
            out.append(f"    {'rr':>5} {'rec':>5} {'ndcg':>5}  {'flags':<6} question")
            for row in graded[:_WORST_N]:
                out.append(
                    f"    {row.get('rr', 0.0):>5.2f} {row.get('recall', 0.0):>5.2f} "
                    f"{row.get('ndcg', 0.0):>5.2f}  {_flags(row):<6} "
                    f"{_clip(row['question'], _QUESTION_COL)}"
                )

        if failed:
            out.append("")
            out.append(f"  failed: {len(failed)}")
            for row in failed[:_WORST_N]:
                out.append(f"    - {_clip(row['question'], _QUESTION_COL)}: {row['error']}")
        return "\n".join(out)

    def _k(self) -> int:
        """The k the report was computed at, recovered from the rows."""
        for row in self.per_question:
            if (k := row.get("k")) is not None:
                return int(k)
        return 0


# --------------------------------------------------------------------- metrics
#
# Each function takes a relevance vector - `relevance[i]` is True when the
# result at rank i+1 was relevant - and nothing else. They are module level and
# pure so the arithmetic can be tested without a pipeline, an index or a corpus.


def reciprocal_rank(relevance: Sequence[bool]) -> float:
    """1 / rank of the first relevant result; 0.0 if there is none.

        RR = 1 / rank_first_relevant
    """
    for i, hit in enumerate(relevance, start=1):
        if hit:
            return 1.0 / i
    return 0.0


def recall_at_k(found_targets: int, total_targets: int) -> float:
    """Share of the labelled documents that appeared anywhere in the top k.

        recall@k = |relevant ∩ retrieved@k| / |relevant|

    Counted over *documents*, not chunks: a document that contributes four
    chunks to the top k is one document found, and dividing chunk hits by a
    document-level label count would happily exceed 1.0.
    """
    if total_targets <= 0:
        return 0.0
    return min(1.0, found_targets / total_targets)


def dcg(relevance: Sequence[bool]) -> float:
    """Discounted cumulative gain with binary gains and the log2 discount.

        DCG = Σ_{i=1..k} gain_i / log2(i + 1)      gain_i ∈ {0, 1}

    Rank 1 is worth 1/log2(2) = 1.0, rank 2 is worth 1/log2(3) ≈ 0.63, rank 8
    is worth ≈ 0.33.
    """
    return sum(1.0 / math.log2(i + 1) for i, hit in enumerate(relevance, start=1) if hit)


def ndcg_at_k(relevance: Sequence[bool], total_targets: int, k: int) -> float:
    """DCG divided by the DCG of the best ranking that was achievable.

        nDCG@k = DCG@k / IDCG@k

    The ideal ranking puts `ideal_n` relevant results in positions 1..ideal_n,
    where `ideal_n = min(k, max(labelled_documents, relevant_hits))`. Using the
    label count alone would cap nDCG below 1.0 whenever one labelled document
    supplied two retrieved chunks; using the hit count alone would score a run
    that found one of three labelled documents at rank 1 as a perfect 1.0. The
    max of the two is the honest reading: the best achievable ranking has at
    least one slot per labelled document and at least as many as we actually
    found.
    """
    hits = sum(1 for hit in relevance if hit)
    ideal_n = min(k, max(total_targets, hits))
    if ideal_n <= 0:
        return 0.0
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_n + 1))
    return dcg(relevance[:k]) / idcg if idcg > 0 else 0.0


# --------------------------------------------------------------------- loading


def load_goldens(path: str | Path) -> list[Golden]:
    """Read a JSONL golden set.

    Malformed lines are counted and skipped rather than raised. A golden set is
    hand-edited, so a trailing comma on line 14 is a routine event; losing the
    other 17 questions to it is not an acceptable response. Blank lines and
    `#` comment lines are allowed so the file can be annotated in place.
    """
    p = Path(path)
    goldens: list[Golden] = []
    bad = 0
    try:
        raw = p.read_text("utf-8")
    except OSError as e:
        log.error("golden set unreadable", path=str(p), err=f"{type(e).__name__}: {e}")
        return []

    for lineno, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise TypeError("golden must be a JSON object")
            question = str(payload["question"]).strip()
            if not question:
                raise ValueError("empty question")
            goldens.append(
                Golden(
                    question=question,
                    relevant_uris=[str(u) for u in payload.get("relevant_uris", [])],
                    relevant_doc_ids=[str(d) for d in payload.get("relevant_doc_ids", [])],
                    must_include=[str(s) for s in payload.get("must_include", [])],
                    should_abstain=bool(payload.get("should_abstain", False)),
                )
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            bad += 1
            log.warn("skipped malformed golden", path=str(p), line=lineno,
                     err=f"{type(e).__name__}: {e}"[:160])

    log.info("loaded goldens", path=str(p), loaded=len(goldens), skipped=bad)
    return goldens


# -------------------------------------------------------------------- matching


def _normalize_uri(uri: str) -> str:
    """Comparable form of a URI: no `file://` scheme, no trailing slash, folded.

    Case folding is safe here and suffix matching is what makes the offline
    corpus addressable at all - a golden written by a human says
    `evals/corpus/bm25-scoring.md`, while the indexed document says
    `file:///home/someone/claude/evals/corpus/bm25-scoring.md`.
    """
    value = uri.strip().replace("\\", "/")
    if value.lower().startswith("file://"):
        value = value[len("file://"):]
    return value.rstrip("/").casefold()


def uri_matches(retrieved_uri: str, target: str) -> bool:
    """True when a retrieved URI is the target, or lives at that path suffix."""
    got, want = _normalize_uri(retrieved_uri), _normalize_uri(target)
    if not got or not want:
        return False
    return got == want or got.endswith("/" + want)


def _matched_targets(hit: ScoredChunk, golden: Golden) -> set[str]:
    """Which of the golden's labels this one retrieved chunk satisfies."""
    matched: set[str] = set()
    doc_id = hit.chunk.doc_id
    for target in golden.relevant_doc_ids:
        if target == doc_id:
            matched.add(f"doc:{target}")
    uri = hit.citation_uri
    for target in golden.relevant_uris:
        if uri_matches(uri, target):
            matched.add(f"uri:{target}")
    return matched


def _flatten(text: str) -> str:
    """Whitespace-collapsed, case-folded text for containment checks.

    Both halves matter, and both were paid for. Case, because the corpus writes
    `BM25` and an extracted sentence can open with `bm25`; failing a golden over
    a capital letter trains whoever maintains the set to write weaker
    assertions. Whitespace, because answers are quoted verbatim from source
    files that are hard-wrapped at 79 columns - a two-word `must_include` such
    as "dot product" fails against a real, correct answer whenever the source
    happened to wrap between the two words. The assertion is about the words the
    answer used, not about where a text editor broke the line.
    """
    return " ".join(text.split()).casefold()


def _missing_strings(answer_text: str, must_include: Sequence[str]) -> list[str]:
    """The required strings the answer does not contain."""
    haystack = _flatten(answer_text)
    return [s for s in must_include if s.strip() and _flatten(s) not in haystack]


# ------------------------------------------------------------------- evaluate


def evaluate(pipeline: Pipeline, goldens: Sequence[Golden], k: int = 8) -> EvalReport:
    """Run every golden through the pipeline and score the result.

    The pipeline is only ever asked for `.ask(question, k=k)`, so anything with
    that method can be evaluated - which is what keeps the harness usable in a
    unit test with a scripted stand-in and no index on disk.
    """
    report = EvalReport(n=len(goldens))
    started = time.monotonic()

    recalls: list[float] = []
    rrs: list[float] = []
    ndcgs: list[float] = []
    coverages: list[float] = []
    abstained_flags: list[float] = []
    false_abstentions: list[float] = []

    for golden in goldens:
        row: dict[str, Any] = {
            "question": golden.question,
            "k": k,
            "targets": golden.targets,
            "should_abstain": golden.should_abstain,
        }
        try:
            answer = pipeline.ask(golden.question, k=k)
        except Exception as e:  # one bad question must not end the run
            row["error"] = f"{type(e).__name__}: {e}"[:200]
            log.error("question failed", question=golden.question[:80], err=row["error"])
            report.per_question.append(row)
            continue

        _score_one(answer, golden, k, row)

        if golden.labelled:
            recalls.append(row["recall"])
            rrs.append(row["rr"])
            ndcgs.append(row["ndcg"])
        if not answer.abstained:
            coverages.append(row["citations_ok"])
        abstained_flags.append(1.0 if answer.abstained else 0.0)
        if not golden.should_abstain:
            false_abstentions.append(1.0 if answer.abstained else 0.0)

        report.per_question.append(row)

    report.recall_at_k = _mean(recalls)
    report.mrr = _mean(rrs)
    report.ndcg_at_k = _mean(ndcgs)
    report.citation_coverage = _mean(coverages)
    report.abstention_rate = _mean(abstained_flags)
    report.false_abstention_rate = _mean(false_abstentions)

    log.info(
        "eval complete",
        n=report.n,
        recall=round(report.recall_at_k, 3),
        mrr=round(report.mrr, 3),
        ndcg=round(report.ndcg_at_k, 3),
        citations=round(report.citation_coverage, 3),
        abstained=round(report.abstention_rate, 3),
        false_abstained=round(report.false_abstention_rate, 3),
        secs=round(time.monotonic() - started, 2),
    )
    return report


def _score_one(answer: Answer, golden: Golden, k: int, row: dict[str, Any]) -> None:
    """Fill one per-question row in place. Every metric for this question is here."""
    ranked = list(answer.retrieved)[:k]
    relevance = [bool(_matched_targets(hit, golden)) for hit in ranked]
    found: set[str] = set()
    for hit in ranked:
        found |= _matched_targets(hit, golden)

    row["retrieved"] = len(ranked)
    row["hit_ranks"] = [i for i, hit in enumerate(relevance, start=1) if hit]
    row["recall"] = round(recall_at_k(len(found), golden.targets), 4)
    row["rr"] = round(reciprocal_rank(relevance), 4)
    row["ndcg"] = round(ndcg_at_k(relevance, golden.targets, k), 4)
    row["abstained"] = answer.abstained
    row["confidence"] = round(float(answer.confidence), 4)
    row["citations"] = len(answer.citations)

    # Resolution is checked against everything the pipeline retrieved, not just
    # the top k this report grades at: a citation pointing past rank k is still
    # a citation that resolves, and calling it a fabrication would be wrong.
    retrieved_ids = {hit.chunk.chunk_id for hit in answer.retrieved}
    resolves = bool(answer.citations) and all(
        c.chunk_id in retrieved_ids for c in answer.citations
    )
    row["citations_ok"] = 1.0 if resolves else 0.0
    row["unresolved_citations"] = [
        c.chunk_id for c in answer.citations if c.chunk_id not in retrieved_ids
    ]

    missing = _missing_strings(answer.text, golden.must_include)
    if missing:
        row["must_include_missing"] = missing
    # An abstention is a *correct* outcome when the golden expects one, and a
    # failure when it does not. Naming that as its own field keeps the judgement
    # in the report rather than in the head of whoever reads the table.
    row["abstention_correct"] = answer.abstained == golden.should_abstain


def _mean(values: Sequence[float]) -> float:
    """Mean of a possibly empty sample; an empty sample is 0.0, not a crash.

    0.0 rather than `None` because every consumer (the OODA loop's quality
    score, a CI threshold) needs a number, and "no labelled questions" should
    read as "no evidence of quality" rather than as a passing grade.
    """
    return sum(values) / len(values) if values else 0.0


def _bar(value: float, width: int = 10) -> str:
    """A 0..1 value as a fixed-width bar, so the table can be scanned not read."""
    filled = max(0, min(width, int(round(value * width))))
    return "#" * filled + "." * (width - filled)


def _clip(text: str, width: int) -> str:
    flat = " ".join(str(text).split())
    return flat if len(flat) <= width else flat[: width - 3] + "..."


def _flags(row: dict[str, Any]) -> str:
    """Compact per-question status: A abstained, M must_include miss, C citations."""
    marks = ""
    marks += "A" if row.get("abstained") else "-"
    marks += "M" if row.get("must_include_missing") else "-"
    marks += "C" if row.get("citations_ok") == 0.0 and not row.get("abstained") else "-"
    return marks
