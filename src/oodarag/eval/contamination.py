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
from oodarag.util.text import tokenize


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
    """Lowercase, strip punctuation, and collapse the resulting whitespace.

    The collapse is not cosmetic. Replacing a punctuation run with a space
    leaves the space that was already beside it, so "work, exactly" becomes
    "work  exactly" - while the question side, built from tokens, has single
    spaces. The two sides then never match, and a question quoted verbatim in
    the corpus is reported clean. Any golden question containing a comma was
    invisible to the verbatim check.
    """
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def detect(store: SqliteStore, questions: list[str], *,
           negative_questions: set[str] | None = None,
           verbatim_threshold: float = 0.85,
           overlap_threshold: float = 0.9,
           negative_verbatim_threshold: float = 0.5,
           negative_overlap_threshold: float = 0.6,
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

    # Weighted by informativeness, for the same reason retrieval relevance is:
    # a document sharing a question's rare terms is discussing that question; one
    # sharing only its common words is not.
    idf = store.idf_lookup()
    documents = store.all_documents()[:max_docs_scanned]
    prepared = [
        (doc, " ".join(tokenize(doc.text, stem_words=True)),
         set(tokenize(doc.text, stem_words=True)))
        for doc in documents
    ]

    for question in questions:
        is_negative = question in negatives
        verbatim_floor = (negative_verbatim_threshold if is_negative
                          else verbatim_threshold)
        overlap_floor = (negative_overlap_threshold if is_negative
                         else overlap_threshold)
        q_norm = _normalize(question)
        q_terms = set(tokenize(question, stem_words=True))
        # Content tokens, stemmed - the same analysis the document side gets.
        # Counting stopwords lets "who won the" score 0.5 against an unrelated
        # document and quarantine it from a negative case, which removes real
        # corpus from the eval and makes the contamination signal cry wolf.
        q_words = tokenize(question, stem_words=True)
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
                # Fatal only for a question the corpus is supposed to be unable
                # to answer. On a positive golden, a document matching the
                # question's terms *is the answer* - quarantining it would
                # remove the very source the case expects and turn a passing
                # case into a failing one. Report it, do not act on it.
                report.findings.append(Contamination(
                    question=question, doc_id=doc.doc_id, uri=doc.uri,
                    source_system=doc.source_system, kind="verbatim",
                    score=round(longest, 3), excerpt=excerpt.strip(),
                    fatal=is_negative,
                ))
                if is_negative:
                    report.by_source[doc.source_system] = \
                        report.by_source.get(doc.source_system, 0) + 1
                continue
            # 2. overlap: nearly every distinctive term of the question present.
            if not q_terms:
                continue
            total_weight = sum(idf(t) for t in q_terms) or 1.0
            weighted = sum(idf(t) for t in q_terms & doc_terms) / total_weight
            if weighted >= overlap_floor:
                fatal = is_negative
                report.findings.append(Contamination(
                    question=question, doc_id=doc.doc_id, uri=doc.uri,
                    source_system=doc.source_system, kind="overlap",
                    score=round(weighted, 3), fatal=fatal,
                ))
                if fatal:
                    report.by_source[doc.source_system] = \
                        report.by_source.get(doc.source_system, 0) + 1

    report.clean = not report.fatal_findings
    return report


def _longest_run(words: list[str], haystack: str, min_run: int = 2) -> float:
    """Longest contiguous run of `words` present in `haystack`, as a fraction.

    `words` and `haystack` must both be stemmed content tokens, and the run is
    padded so it cannot match the tail of a longer token.
    """
    if len(words) < min_run:
        return 0.0
    padded = f" {haystack} "
    for length in range(len(words), min_run - 1, -1):
        for start in range(0, len(words) - length + 1):
            if f" {' '.join(words[start:start + length])} " in padded:
                return length / len(words)
    return 0.0
