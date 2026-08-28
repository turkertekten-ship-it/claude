"""Why an extractive answerer should refuse, when a score cannot tell it to.

Measured, not assumed. Running the golden set over this corpus showed that the
obvious lexical signals do NOT separate answerable questions from unanswerable
ones: IDF-weighted term coverage bottoms out at 0.61 on questions the corpus
does answer and reaches 0.85 on one it does not, and the fused retrieval score
is constant at the top rank and carries no information at all. Any threshold
that made the twenty goldens pass would be fitted to twenty examples and would
generalise to nothing.

So instead of one tuned number, three guards, each resting on something true
about this system rather than on a distribution:

**Topic.** If few of a question's informative terms appear anywhere in what was
retrieved, the corpus is not about this. Plain presence, not IDF-weighted: an
IDF computed over five retrieved chunks is not corpus IDF, and measuring showed
it scoring real answerable questions at 0.38-0.41 — it would have cost genuine
answers to buy a cleaner metric. Measured plain coverage on this corpus runs
0.75-1.00 for answerable questions and 0.56 for the off-topic one; the threshold
sits at 0.60, below the answerable floor with margin, so the guard fires only on
the clearly off-topic.

**Answer type.** A question demanding a figure — "how many", "how much", "the
exact value" — cannot be answered by prose containing no figure. This is the
guard that catches the dangerous case: a question about a real fund, retrieving
real passages about that fund, none of which contain the number asked for.

**Redaction class.** Addresses, phone numbers, national IDs, IBANs and emails
are stripped at the connector boundary by ``redact.py``. A question asking for
one is unanswerable *by construction*, and saying so is more honest than
searching for something the pipeline guarantees is absent.

Each guard returns a reason or ``None``. A reason is a refusal.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from oodarag.models import ScoredChunk
from oodarag.util.text import tokenize_all

#: Share of a question's content terms that must appear somewhere in the
#: retrieved text. Measured floor for answerable questions on this corpus: 0.75.
#: Set at 0.60 so the guard keeps a real margin and never trades a genuine
#: answer for a tidier abstention rate — a false non-abstention is still caught
#: downstream by citation verification, while a false abstention is a lost answer.
MIN_TOPIC_COVERAGE = 0.60

_QUANTITY = re.compile(
    r"\b(how many|how much|how long|exact(?:ly)?|net asset value|nav\b|"
    r"what (?:is|was|are|were) the (?:value|amount|size|total|number|price|figure)|"
    r"kaç|ne kadar|tutarı|değeri nedir)\b",
    re.IGNORECASE,
)

_REDACTED_CLASS = re.compile(
    r"\b(home address|postal address|residential address|mobile number|"
    r"phone number|telephone number|e-?mail address|national id|"
    r"identity number|tckn|passport number|iban|bank account|credit card|"
    r"ev adresi|telefon numarası|kimlik numarası)\b",
    re.IGNORECASE,
)

#: A year or a citation marker is not an answer to "how much". Stripping them
#: before looking for a figure is what separates "the passage states the number"
#: from "the passage happens to mention 2026".
_NOT_A_FIGURE = re.compile(r"\b(?:19|20)\d{2}\b|\[\d+\]|\bU-\d+\b|\b[IVX]+-\d+")
_DIGIT = re.compile(r"\d")


def topic_coverage(question: str, retrieved: Sequence[ScoredChunk]) -> float:
    """Fraction of the question's content terms present anywhere in the retrieved text."""
    terms = [t for t in set(tokenize_all(question)) if len(t) > 2]
    if not terms or not retrieved:
        return 0.0
    blob: set[str] = set()
    for s in retrieved:
        blob |= set(tokenize_all(s.chunk.text))
    return sum(1 for t in terms if t in blob) / len(terms)


def off_topic(question: str, retrieved: Sequence[ScoredChunk]) -> str | None:
    cov = topic_coverage(question, retrieved)
    if cov < MIN_TOPIC_COVERAGE:
        return (f"the retrieved passages cover only {cov:.0%} of the question's "
                "informative terms — this corpus is not about it")
    return None


def asks_for_a_figure(question: str) -> bool:
    return bool(_QUANTITY.search(question or ""))


def missing_figure(question: str, sentences: Sequence[str]) -> str | None:
    """A question demanding a number, answered by prose without one.

    The case this exists for: asking the exact NAV of a real fund. Retrieval
    returns genuine passages about that fund, every citation verifies, and the
    answer still does not contain the figure — which reads as an answer and is
    not one.
    """
    if not asks_for_a_figure(question):
        return None
    if any(_DIGIT.search(_NOT_A_FIGURE.sub(" ", s)) for s in sentences):
        return None
    return ("the question asks for a figure and no retrieved passage contains "
            "one — the corpus discusses the subject without stating the number")


def asks_for_redacted_class(question: str) -> str | None:
    m = _REDACTED_CLASS.search(question or "")
    if not m:
        return None
    return (f"'{m.group(0)}' belongs to a class of identifier that is stripped at "
            "ingest by the redaction layer, so it cannot be present in the index "
            "and no amount of retrieval will find it")


def refuse(question: str, retrieved: Sequence[ScoredChunk],
           sentences: Sequence[str]) -> str | None:
    """The first guard that objects, or None. Order is cheapest-first."""
    return (asks_for_redacted_class(question)
            or off_topic(question, retrieved)
            or missing_figure(question, sentences))
