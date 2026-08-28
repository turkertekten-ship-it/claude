"""Reranking.

Fusion produces a good candidate ordering from two weak signals. Reranking is
where cheap, high-precision evidence that neither retrieval arm can see gets
applied: whether the query's rare terms actually appear, whether the phrase
appears intact, how authoritative the source is, and how old it is.

The heuristic reranker below is deliberately transparent - every component is
recorded on the result - because an opaque reranker that reorders results for
reasons nobody can inspect is worse than none. A cross-encoder or LLM reranker
implements the same interface and can replace it where the latency is affordable.
"""

from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

from oodarag.models import ScoredChunk
from oodarag.util.text import expand_compounds, is_compound, tokenize


class Reranker(ABC):
    name = "reranker"

    @abstractmethod
    def rerank(self, query: str, results: list[ScoredChunk]) -> list[ScoredChunk]: ...


@dataclass
class HeuristicReranker(Reranker):
    """Feature-based reranking with an auditable score breakdown."""

    name: str = "heuristic"
    #: Maps a stemmed term to its inverse document frequency. Without it every
    #: query word counts equally and coverage stops discriminating - see
    #: SqliteStore.idf_table for what that costs.
    idf: Callable[[str], float] | None = field(default=None)
    #: Terms the corpus contains, for the answerability factor below. Leaving
    #: it None disables that factor, which is only for A/B measurement.
    vocabulary: set[str] | None = field(default=None)
    #: Absence of a term is only evidence at scale. Below this vocabulary size,
    #: a corpus is too small for "not present" to mean "not covered": a
    #: three-document corpus lacks most ordinary English words, and its IDF
    #: estimates are too noisy to distinguish a generic missing word from a
    #: distinctive one. Measured on a real corpus (1,343 chunks, ~9k terms) the
    #: factor is worth +2 golden cases; on a toy corpus it rejected a question
    #: the corpus plainly answered.
    min_vocabulary_for_answerability: int = 2000
    #: Exponent applied to IDF when weighting coverage. 1.0 is plain IDF
    #: weighting; higher values concentrate weight on the query's rare terms, so
    #: a question whose only distinctive word is missing cannot be carried by
    #: its generic ones ("how does one Python library let other packages *hook*
    #: into it" was outvoted by python/library/package).
    #:
    #: Measured, and left at 1.0 - the evidence is genuinely mixed:
    #:
    #:   corpus    power  pass   recall  prec    MRR     nDCG
    #:   external  1.0    32/36  0.9286  0.2946  0.8741  0.8633
    #:   external  2.0    33/36  0.9643  0.3080  0.8676  0.8653
    #:   external  3.0    33/36  0.9643  0.3036  0.8861  0.8782
    #:   primary   1.0    17/20  0.7812  0.1953  0.5573  0.5911
    #:   primary   2.0    18/20  0.7500  0.2109  0.5698  0.5832
    #:   primary   3.0    18/20  0.7500  0.2031  0.5631  0.5797
    #:
    #: Pass rate and precision improve on both corpora; primary recall falls by
    #: 0.031 and primary nDCG dips. Recall is documented here as the ceiling on
    #: everything downstream, and trading it for pass rate on one corpus is the
    #: local optimisation the eval exists to prevent - so the default does not
    #: move on evidence this mixed. Raise it only with an A/B on your own corpus.
    coverage_power: float = 1.0
    coverage_weight: float = 0.45
    phrase_weight: float = 0.25
    authority_weight: float = 0.12
    recency_weight: float = 0.08
    position_weight: float = 0.05
    base_weight: float = 1.0
    half_life_days: float = 365.0

    def _query_set(self, query_terms: list[str]) -> set[str]:
        """Query terms for coverage, with unmatchable compounds broken up.

        `tokenize` keeps `snake_case`, `dotted.paths` and hyphenated words whole
        so that identifiers survive, which is right for a corpus that is half
        code. FTS5's unicode61 splits on those separators, so a quoted
        "in-process" reaches the lexical arm as a two-word phrase and matches a
        document saying "in process". The reranker then scored that same
        document as containing neither, and - because a term the corpus has
        never contained gets the maximum idf - the ghost term dominated both the
        coverage denominator and answerability. "Which library dispatches
        in-process notifications between objects?" was retrieved and then
        abstained on, at relevance 0.13 against a 0.15 floor.

        Only compounds absent from the corpus are split. A compound the corpus
        does contain is a real term and keeps its atomic identity.
        """
        vocabulary = self.vocabulary
        if not vocabulary:
            return set(query_terms)
        expanded: set[str] = set()
        for term in query_terms:
            if term in vocabulary or not is_compound(term):
                expanded.add(term)
                continue
            parts = [p for p in expand_compounds([term], stem_words=True) if p != term]
            expanded.update(parts or [term])
        return expanded

    def _answerability(self, query_terms: set[str]) -> float:
        """How much of the query's information the corpus contains at all.

        A property of the query and the corpus, not of any chunk - so it scales
        every candidate identically and cannot reorder them. It gates answering
        without touching ranking.

        It exists because fractional coverage hides *which* part matched: "what
        is the boiling point of mercury" matched the word "point" in a corpus of
        Python package pages, took a third of its coverage from that one
        incidental word, and was answered with confidence 0.76. Neither
        "boiling" nor "mercury" occurs anywhere in that corpus, and that is the
        whole answer to whether the question can be answered from it.

        An earlier attempt asked instead whether the query's single most
        informative term was present. That reduced to `max(query_set, key=idf)`,
        which picks an arbitrary element when terms tie - and since Python
        randomises string hashing per process, set iteration order varies
        between runs, so the same question abstained or answered depending on
        the run. Four runs returned three different key terms. It broke this
        pipeline's determinism (ADR 0001) silently: the eval moved by one case
        and looked like noise.
        """
        if not self.vocabulary or not query_terms or self.idf is None:
            return 1.0
        if len(self.vocabulary) < self.min_vocabulary_for_answerability:
            return 1.0
        total = sum(self.idf(term) for term in query_terms)
        if total <= 0:
            return 1.0
        known = sum(self.idf(term) for term in query_terms if term in self.vocabulary)
        return known / total

    def rerank(self, query: str, results: list[ScoredChunk]) -> list[ScoredChunk]:
        # Stemmed, to match the FTS5 index. Raw-token coverage scores a passage
        # saying "abstained" as containing none of a query for "abstain", and
        # so demotes the exact passages the lexical arm ranked first.
        query_terms = tokenize(query, stem_words=True)
        query_set = self._query_set(query_terms)
        # Computed once per query, not per chunk.
        answerability = self._answerability(query_set)
        # Content tokens only. Measuring the phrase over every token lets a run
        # of stopwords score: "what is the" is three of the seven words in
        # "what is the boiling point of mercury", which scored 0.43 and carried
        # an out-of-corpus question past the abstention floor on its own.
        # Stopword adjacency is not evidence of anything.
        phrase_terms = tokenize(query, stem_words=True)
        now = time.time()

        for result in results:
            chunk = result.chunk
            haystack_terms = tokenize(chunk.indexed_text, stem_words=True)
            haystack = " ".join(haystack_terms)
            chunk_terms = set(haystack_terms)

            if not query_set:
                coverage = 0.0
            elif self.idf is None:
                coverage = len(query_set & chunk_terms) / len(query_set)
            else:
                # Weighted by informativeness: matching a term that appears
                # everywhere is not evidence, matching a rare one is.
                power = self.coverage_power
                total_weight = sum(self.idf(t) ** power for t in query_set)
                matched_weight = sum(self.idf(t) ** power
                                     for t in query_set & chunk_terms)
                coverage = matched_weight / total_weight if total_weight else 0.0
            # Exact phrase match is rare and highly diagnostic; partial credit
            # for a long shared prefix keeps it from being all-or-nothing.
            phrase_score = _longest_common_run(phrase_terms, haystack)

            authority = float(chunk.metadata.get("authority", 1.0))
            authority_score = max(0.0, min(1.5, authority)) / 1.5

            updated = float(chunk.metadata.get("updated_at") or 0.0)
            if updated:
                age_days = max(0.0, (now - updated) / 86400.0)
                recency = math.exp(-age_days / self.half_life_days)
            else:
                recency = 0.5  # unknown age is neither fresh nor stale

            # Earlier chunks of a document are usually its thesis; later chunks
            # are detail. A weak preference, not a strong one.
            position = 1.0 / (1.0 + 0.15 * chunk.ordinal)

            adjustment = (
                self.coverage_weight * coverage
                + self.phrase_weight * phrase_score
                + self.authority_weight * authority_score
                + self.recency_weight * recency
                + self.position_weight * position
            )
            # The query's single most informative term decides whether the
            # corpus covers the question at all. Without this, a query whose
            # defining terms are absent still scored a third of its coverage
            # from one incidental common word - "what is the boiling point of
            # mercury" matched "point" in a corpus of Python package pages and
            # was answered with confidence 0.76. Fractional coverage hides
            # *which* third matched, and that is the part that matters.

            # Relevance is kept separate from the priors on purpose. Authority,
            # recency and position are query-independent: they raise a chunk's
            # score whether or not it has anything to do with the question. Fold
            # them into one number and the total stops being usable as an
            # "is this relevant at all" signal - an irrelevant chunk from a
            # trusted, recent source outscores the abstention floor and the
            # system answers confidently from nothing. Ordering uses the total;
            # the abstention gate uses `rerank_relevance` alone.
            relevance = (0.6 * coverage + 0.4 * phrase_score) * answerability

            result.components.update({
                "rerank_relevance": relevance,
                "rerank_answerability": answerability,
                "rerank_coverage": coverage,
                "rerank_phrase": phrase_score,
                "rerank_authority": authority_score,
                "rerank_recency": recency,
                "rerank_position": position,
                "rerank_adjustment": adjustment,
                "pre_rerank_score": result.score,
            })
            result.score = self.base_weight * result.score + adjustment

        results.sort(key=lambda r: r.score, reverse=True)
        return results


def _longest_common_run(words: list[str], haystack: str, min_run: int = 2) -> float:
    """Fraction of the query's content terms present as one contiguous run.

    A cheap proximity signal: a chunk containing "reciprocal rank fusion"
    should outrank one merely containing all three words scattered apart.

    `words` must already have stopwords removed and be stemmed the same way as
    `haystack`, and a run shorter than `min_run` scores zero - a single shared
    word is coverage, which is measured separately and weighted by how
    informative the word is. Counting it here too would double-count it, and
    counting an unweighted single word would let the most common term in the
    corpus stand in for a match.
    """
    if len(words) < min_run:
        return 0.0
    # Padded on both sides so a run cannot match the tail of a longer token:
    # without this, ["rank", "fusion"] scores a full 1.0 against
    # "prank fusion", contributing 0.4 to relevance on a chunk that does not
    # contain the phrase at all. Stemming makes such collisions more likely,
    # not less.
    padded_haystack = f" {haystack} "
    for length in range(len(words), min_run - 1, -1):
        for start in range(0, len(words) - length + 1):
            if f" {' '.join(words[start:start + length])} " in padded_haystack:
                return length / len(words)
    return 0.0
