"""Extractive answering - no language model required.

This exists for two reasons, and neither is "we couldn't get an API key".

**It keeps the pipeline whole.** Every other stage runs offline; if the final
stage needed a hosted model, the end-to-end test would need one too, and the
system could not be evaluated in CI or in an air-gapped container.

**It is the grounding floor.** An extractive answer quotes retrieved text
verbatim, so it cannot hallucinate - by construction, not by instruction. It
reads worse than a generated answer, and it is the baseline an LLM answer has to
beat on the eval harness to justify its cost.
"""

from __future__ import annotations

from oodarag.generate.contract import Citation
from oodarag.models import ScoredChunk
import re

from oodarag.util.text import split_sentences, tokenize

# Lines that are source code rather than explanation. An extractive answer that
# opens with an import block is technically "grounded" and useless to read, so
# code-shaped sentences are penalised - not excluded, because a question about
# code is legitimately answered by code.
_CODE_START_RE = re.compile(
    r"^\s*(?:import|from|def|class|return|elif|else|for|while|try|except|finally|"
    r"with|yield|assert|raise|await|async|const|let|var|function|export|package|"
    r"public|private|#|//|/\*|@|\}|\{|\)|\]|<|\$)", re.I)
_SYMBOL_RE = re.compile(r"[(){}\[\]=<>;:|&^~%\\/_*+-]")


def _code_likeness(sentence: str) -> float:
    """0 = prose, 1 = definitely code."""
    if not sentence:
        return 0.0
    score = 0.6 if _CODE_START_RE.match(sentence) else 0.0
    symbols = len(_SYMBOL_RE.findall(sentence)) / max(1, len(sentence))
    score += min(0.4, symbols * 2.0)
    return min(1.0, score)


def extractive_answer(question: str, results: list[ScoredChunk],
                      citations: list[Citation], max_sentences: int = 5,
                      idf=None) -> str:
    """Compose an answer from the sentences that best match the question.

    Sentence selection is IDF-weighted for the same reason retrieval is: a
    sentence sharing the question's rare terms is answering it, one sharing only
    its common words is not.
    """
    if not results:
        return ""
    query_terms = set(tokenize(question, stem_words=True))
    weight = idf or (lambda term: 1.0)
    scored: list[tuple[float, str, int]] = []

    for result, citation in zip(results, citations):
        chunk_weight = max(result.score, 0.0001)
        for sentence in split_sentences(result.chunk.text):
            words = sentence.split()
            if not 4 <= len(words) <= 60:
                continue
            terms = set(tokenize(sentence, stem_words=True))
            if not terms:
                continue
            shared = query_terms & terms
            if not shared:
                continue
            total_weight = sum(weight(t) for t in query_terms) or 1.0
            overlap = sum(weight(t) for t in shared) / total_weight
            # Density rewards a sentence that is *about* the query rather than
            # one that merely happens to be long enough to contain the terms.
            density = len(shared) / len(terms)
            readability = 1.0 - 0.7 * _code_likeness(sentence)
            scored.append(((overlap * 0.7 + density * 0.3 + chunk_weight * 0.05) * readability,
                           sentence.strip(), citation.marker))

    if not scored:
        # Nothing matched at the sentence level: fall back to the top chunk's
        # opening, which is at least the most relevant passage retrieved.
        best, citation = results[0], citations[0]
        opening = " ".join(split_sentences(best.chunk.text)[:2])
        return f"{opening} [{citation.marker}]"

    scored.sort(key=lambda item: item[0], reverse=True)
    seen: set[str] = set()
    lines: list[str] = []
    for _, sentence, marker in scored:
        key = " ".join(sorted(tokenize(sentence)))[:120]
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"{sentence} [{marker}]")
        if len(lines) >= max_sentences:
            break
    return " ".join(lines)
