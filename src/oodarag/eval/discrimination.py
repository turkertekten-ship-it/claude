"""Does a golden's expected source actually pick anything out?

`Golden.expect_sources` entries are substrings, matched against a document's uri
and title. That is convenient - "pluggy" rather than a full path - and it means
an entry can be satisfied by documents it was never meant to name. Every uri in
a filesystem corpus shares a directory, so an expectation of `"pypi"` matches
all 91 documents and the case passes with recall 1.0 no matter what retrieval
returns.

That is a test that cannot fail, living inside the instrument every other
measurement is taken with - the worst place for one. Contamination detection
already asks whether the corpus gives the answer away; this asks the other half,
whether the expectation distinguishes anything.

Reported, never silently corrected: a golden set is an asset, and rewriting one
because it looks too broad is how an eval starts agreeing with the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from oodarag.store.sqlite_store import SqliteStore

#: An expectation matching more than this share of the corpus is not selecting
#: a document, it is selecting the corpus. Deliberately loose: a golden may name
#: two or three sources legitimately, and on a 91-document corpus this allows
#: eighteen before complaining.
MAX_MATCH_SHARE = 0.2


@dataclass
class Finding:
    question: str
    expectation: str
    matched: int
    total: int
    #: "source" for an expected document, "answer" for expected answer text.
    kind: str = "source"
    examples: list[str] = field(default_factory=list)

    @property
    def share(self) -> float:
        return self.matched / self.total if self.total else 0.0

    def describe(self) -> str:
        if not self.matched:
            return (f"{self.kind} expectation {self.expectation!r} matches no "
                    f"document in the corpus, so the case can never pass: "
                    f"{self.question}")
        return (f"{self.kind} expectation {self.expectation!r} matches "
                f"{self.matched} of {self.total} documents ({self.share:.0%}), "
                f"so the case passes without discriminating: {self.question}")


@dataclass
class DiscriminationReport:
    findings: list[Finding] = field(default_factory=list)
    documents: int = 0

    @property
    def clean(self) -> bool:
        return not self.findings

    def summary(self) -> str:
        if self.clean:
            return ""
        return (f"NON-DISCRIMINATING: {len(self.findings)} golden expectation(s) "
                f"do not select a document. " +
                " ".join(f.describe() for f in self.findings[:3]))

    def as_dict(self) -> dict:
        return {
            "clean": self.clean,
            "documents": self.documents,
            "findings": [
                {"question": f.question, "expectation": f.expectation,
                 "kind": f.kind, "matched": f.matched,
                 "share": round(f.share, 4), "examples": f.examples}
                for f in self.findings
            ],
        }


def check(store: SqliteStore, goldens) -> DiscriminationReport:
    """Report expectations that match nothing, or nearly everything."""
    documents = store.all_documents()
    report = DiscriminationReport(documents=len(documents))
    if not documents:
        return report
    blobs = [((d.uri or "") + " " + (d.title or "")).lower() for d in documents]
    names = [d.title or d.uri for d in documents]

    # Answer expectations are searched in the generated answer, but the answer
    # is assembled from the corpus - so a term the corpus repeats everywhere
    # will turn up in almost any answer. `"sha"` appears in 38% of this
    # repository's documents, matching "shared", "shape" and "share" as readily
    # as a commit sha, and any answer citing a third of the corpus satisfies it.
    bodies = [(d.text or "").lower() for d in documents]

    for golden in goldens:
        for expectation in getattr(golden, "expect_sources", None) or []:
            needle = expectation.lower()
            hits = [i for i, blob in enumerate(blobs) if needle in blob]
            report.findings.extend(_finding(golden, expectation, hits, names,
                                            len(documents), "source"))
        for expectation in getattr(golden, "expect_answer_contains", None) or []:
            needle = expectation.lower()
            hits = [i for i, body in enumerate(bodies) if needle in body]
            report.findings.extend(_finding(golden, expectation, hits, names,
                                            len(documents), "answer"))
    return report


def _finding(golden, expectation: str, hits: list[int], names: list[str],
             total: int, kind: str) -> list[Finding]:
    """Empty when the expectation is discriminating, one finding when it is not.

    A list rather than an optional so the caller reads as a filter; both
    failure directions - matching nothing, matching nearly everything - produce
    the same shape.
    """
    share = len(hits) / total if total else 0.0
    if hits and share <= MAX_MATCH_SHARE:
        return []
    return [Finding(question=golden.question, expectation=expectation,
                    matched=len(hits), total=total, kind=kind,
                    examples=[names[i] for i in hits[:5]])]
