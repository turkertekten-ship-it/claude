"""Contamination detection for the golden set.

The failure this catches is subtle and, once seen, obvious: if the corpus
contains the evaluation questions, the evaluation measures nothing. It is
train/test leakage, arriving through a door nobody watches.

It is not hypothetical here. This pipeline indexes session transcripts, and a
session in which someone *tested* the system contains the test questions
verbatim. The retriever then finds them - correctly, by every internal measure -
and a negative case designed to prove the system abstains on out-of-corpus
questions instead proves it answers them confidently. Retrieval scores go *up*.
Nothing looks broken.

So contamination is measured before the eval runs, and reported alongside the
results. An eval report that does not state its contamination status is a number
without a provenance.

Two signals, because they fail differently:

* **verbatim** - the question appears in a document, near-exactly. Catches the
  transcript case, where the question was quoted.
* **overlap** - a document shares most of the question's distinctive terms in a
  short span. Catches paraphrase, where the question was discussed rather than
  quoted.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import tokenize, tokenize_all


@dataclass(slots=True)
class Contamination:
    question: str
    doc_id: str
    uri: str
    source_system: str
    kind: str            # "verbatim" | "overlap"
    score: float
    excerpt: str = ""
    #: True when this finding actually invalidates the case. A positive golden
    #: whose terms all appear in the corpus is not contaminated - that is the
    #: corpus containing the answer, which is the entire point. Only a verbatim
    #: copy of the question, or any match at all against a case that is supposed
    #: to be out-of-corpus, breaks the measurement.
    fatal: bool = True


@dataclass
class ContaminationReport:
    findings: list[Contamination] = field(default_factory=list)
    questions_checked: int = 0
    clean: bool = True
    #: Source systems implicated, with counts - the actionable summary, since
    #: the remedy is almost always "exclude this source from the eval index".
    by_source: dict[str, int] = field(default_factory=dict)

    @property
    def fatal_findings(self) -> list["Contamination"]:
        return [f for f in self.findings if f.fatal]

    def as_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "questions_checked": self.questions_checked,
            "contaminated_questions": len({f.question for f in self.fatal_findings}),
            "informational_findings": len(self.findings) - len(self.fatal_findings),
            "by_source": self.by_source,
            "findings": [asdict(f) for f in self.fatal_findings[:25]],
        }

    def summary(self) -> str:
        if self.clean:
            return f"no contamination across {self.questions_checked} questions"
        affected = len({f.question for f in self.fatal_findings})
        sources = ", ".join(f"{name}={count}" for name, count in sorted(self.by_source.items()))
        return (f"CONTAMINATED: {affected}/{self.questions_checked} questions appear in the "
                f"corpus ({sources}). Those documents must be held out for the affected "
                f"questions or the results measure the leak, not the retriever.")


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def detect(store: SqliteStore, questions: list[str], *,
           negative_questions: set[str] | None = None,
           verbatim_threshold: float = 0.85,
           overlap_threshold: float = 0.9,
           negative_verbatim_threshold: float = 0.5,
           negative_overlap_threshold: float = 0.7,
           max_docs_scanned: int = 5000) -> ContaminationReport:
    """Check whether any question appears in the indexed corpus.

    `negative_questions` are the ones expected to be unanswerable. Any corpus
    match against those is fatal; for the rest only a verbatim quotation is.

    The thresholds are deliberately asymmetric, because the two errors are not
    equally costly. Over-quarantining a document for a positive question costs
    one document of recall on one case. *Missing* contamination on a negative
    question silently inverts the case - the system answers, the eval records a
    failure to abstain, and the reported cause is wrong. Paraphrase is the
    realistic shape of this: a test asserting "Who won the 1998 World Cup
    final?" is unanswerable contaminates a golden that asks about the "1998
    FIFA World Cup final" at 83% overlap, which a 90% threshold sails past.
    """
    negatives = negative_questions or set()
    report = ContaminationReport(questions_checked=len(questions))
    if not questions:
        return report

    documents = store.all_documents()[:max_docs_scanned]
    prepared = [
        (doc, _normalize(doc.text), set(tokenize(doc.text)))
        for doc in documents
    ]

    for question in questions:
        is_negative = question in negatives
        verbatim_floor = (negative_verbatim_threshold if is_negative
                          else verbatim_threshold)
        overlap_floor = (negative_overlap_threshold if is_negative
                         else overlap_threshold)
        q_norm = _normalize(question)
        q_terms = set(tokenize(question))
        q_words = _normalize(" ".join(tokenize_all(question))).split()
        if not q_words:
            continue

        for doc, doc_norm, doc_terms in prepared:
            excerpt = ""
            # 1. verbatim: the whole question, or a long contiguous run of it.
            longest = _longest_run(q_words, doc_norm)
            if longest >= verbatim_floor:
                position = doc_norm.find(" ".join(q_words[: max(2, int(len(q_words) * longest))]))
                if position >= 0:
                    excerpt = doc.text[max(0, position - 60):position + 160]
                report.findings.append(Contamination(
                    question=question, doc_id=doc.doc_id, uri=doc.uri,
                    source_system=doc.source_system, kind="verbatim",
                    score=round(longest, 3), excerpt=excerpt.strip(), fatal=True,
                ))
                report.by_source[doc.source_system] = \
                    report.by_source.get(doc.source_system, 0) + 1
                continue
            # 2. overlap: nearly every distinctive term of the question present.
            if q_terms and len(q_terms & doc_terms) / len(q_terms) >= overlap_floor:
                fatal = is_negative
                report.findings.append(Contamination(
                    question=question, doc_id=doc.doc_id, uri=doc.uri,
                    source_system=doc.source_system, kind="overlap",
                    score=round(len(q_terms & doc_terms) / len(q_terms), 3), fatal=fatal,
                ))
                if fatal:
                    report.by_source[doc.source_system] = \
                        report.by_source.get(doc.source_system, 0) + 1

    report.clean = not report.fatal_findings
    return report


def _longest_run(words: list[str], haystack: str) -> float:
    """Longest contiguous run of `words` present in `haystack`, as a fraction."""
    for length in range(len(words), 1, -1):
        for start in range(0, len(words) - length + 1):
            if " ".join(words[start:start + length]) in haystack:
                return length / len(words)
    return 0.0
