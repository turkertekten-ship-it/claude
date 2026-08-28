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

import datetime
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


def _as_number(value: Any, *, default: float) -> float:
    """A metadata value as a float, or the default. Never raises.

    Metadata is whatever a connector chose to write, which is whatever the
    upstream API returned. `float()` on it is a crash waiting for the first
    source that stores a string.
    """
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _as_timestamp(value: Any) -> float:
    """A metadata date as a POSIX timestamp, or 0.0 for "unknown".

    This was written after `float(chunk.metadata.get("updated_at") or 0.0)`
    raised ValueError on `"2026-01-02T00:00:00Z"` - the shape the GitHub
    connector stores for an issue. **That crash is not reachable through the
    pipeline**, and saying so matters more than the fix: the store overwrites a
    chunk's `updated_at` with the document's, which is always a float, so the
    reranker never meets the string. The demonstration used a chunk built by
    hand, which proves what the function does and not what the system does.

    The parse stays because metadata is whatever a connector chose to write and
    a scorer should not raise on it, but it is a guard rather than a repair.

    0.0 means unknown, which the caller reads as "neither fresh nor stale" -
    the right answer for a date nobody can parse.
    """
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        pass
    try:
        # `fromisoformat` handles the trailing Z from Python 3.11 on, which is
        # the floor this project targets.
        return datetime.datetime.fromisoformat(text).timestamp()
    except ValueError:
        return 0.0


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
    #: Measured, and left at 1.0. Re-measured after the external corpus turned
    #: out to be 90.9% site template (L26); the first table was taken on that
    #: corpus and its conclusion did not survive cleaning it, which is the
    #: reason this one names the corpus it was taken on.
    #:
    #:   corpus    power  pass   recall  prec    MRR     nDCG
    #:   external  1.0    44/54  0.9186  0.2355  0.7729  0.7965
    #:   external  2.0    45/54  0.9186  0.2529  0.7502  0.7791
    #:   external  3.0    45/54  0.9070  0.2529  0.7223  0.7588
    #:   primary   1.0    17/20  0.8125  0.2109  0.5573  0.6032
    #:   primary   2.0    18/20  0.7500  0.2109  0.5677  0.5823
    #:   primary   3.0    18/20  0.7500  0.2031  0.5214  0.5494
    #:
    #: Raising the exponent buys a case on each corpus and costs ordering
    #: quality on both - external nDCG falls 0.7965 to 0.7791, primary recall
    #: falls 0.06. Ordering is what the downstream stages read, so 1.0 stays.
    #: Reproduce with `scripts/ablation.py --sweep-coverage-power 1.0 2.0 3.0`,
    #: and re-measure on your own corpus before moving it: this sweep has now
    #: been run on three versions of the external corpus and pointed a
    #: different way on each (L26, L29).
    #: Unstemmed corpus vocabulary, for the surface check below. Optional: the
    #: reranker works without it and simply does not apply the factor.
    surface_vocabulary: set[str] | None = field(default=None)
    #: Multiply answerability by the share of the query's idf mass whose
    #: *surface form* the corpus holds. On: measured at +3 golden cases with
    #: every retrieval metric unchanged to four decimal places. See the table in
    #: `_surface_factor`. A reranker built without a `surface_vocabulary` simply
    #: does not apply it.
    use_surface_answerability: bool = True
    coverage_power: float = 1.0
    coverage_weight: float = 0.45
    phrase_weight: float = 0.25
    #: Invisible to both eval gates, for the same reason as `recency_weight`
    #: below: each corpus is a single filesystem source at authority 1.0, so the
    #: factor is a constant across every candidate and cannot reorder anything.
    #: Measured by zeroing each weight in turn - coverage, phrase and position
    #: all move the metrics on both corpora; authority and recency move neither.
    #: Between them that is 0.20 of the reranker's weight carried by unit tests
    #: alone (L43).
    authority_weight: float = 0.12
    #: Neither eval gate can see this. Both corpora are written in one pass, so
    #: their documents share a timestamp - spread 0.00 days external, 0.91 days
    #: primary - and a factor identical across every candidate cannot reorder
    #: anything. Measured: switching recency off entirely leaves both sets at
    #: 48/54 and 18/20 with every metric unchanged, and moving the clock five
    #: years forward does nothing either.
    #:
    #: So this weight is carried by unit tests alone, and a regression in it
    #: would not show up in the regression gate. Recorded rather than removed:
    #: the factor is right for a corpus of mixed ages, which is what a crawl or
    #: a chat archive produces, and those are not what the gates run on.
    recency_weight: float = 0.08
    position_weight: float = 0.05
    base_weight: float = 1.0
    half_life_days: float = 365.0
    #: Source of "now" for the recency factor. Injectable so a run can be made
    #: reproducible: with the wall clock, two runs of the same query over the
    #: same index return the same *ranking* but scores that differ by around
    #: 1e-8, because a document's age is recomputed against a clock that moved
    #: between them. That is correct behaviour and it makes a score impossible
    #: to assert exactly, so an eval cannot tell a real score regression from
    #: the seconds it took to get there. Freeze it and the whole pipeline is
    #: bit-reproducible.
    clock: Callable[[], float] = time.time

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

    def _surface_factor(self, query: str) -> float:
        """How much of the query the corpus holds *unstemmed*.

        Answerability treats a query term absent from the vocabulary as proof
        the corpus never discussed it. Stemming conflates, so the proof is
        weaker than it reads: "mercury" and "mercurial" share the stem
        `mercuri`, and a corpus mentioning the version control system reported
        the chemical element as known. "What is the boiling point of mercury?"
        was answered with confidence 0.83 on that basis.

        Weighted by the idf of each term's stem, because that is what says how
        much of the question a term carries. Returns 1.0 - no opinion - when
        there is no surface vocabulary or the query has no content terms.

        Measured end to end, everything else held constant:

            corpus    surface  pass   recall  prec    MRR     nDCG
            external  off      44/54  0.9186  0.2355  0.7729  0.7965
            external  on       47/54  0.9186  0.2355  0.7729  0.7965
            primary   off      17/20  0.8125  0.2109  0.5594  0.6041
            primary   on       17/20  0.8125  0.2109  0.5594  0.6041

        Three cases gained, none lost, and **every retrieval metric identical to
        four decimal places** - which is the property to check rather than
        assume: the factor is a function of the query and the corpus, not of any
        chunk, so it scales every candidate equally and cannot reorder them. It
        gates without touching ranking, exactly as `_answerability` does.

        The cases it fixes are "What is the boiling point of mercury?" (the
        conflation above), "Which library pins dependency hashes for
        reproducible installs?" and "Which package reads and writes spreadsheet
        files?" - all three questions the corpus cannot answer and was answering.

        Ranked as a gate feature by AUC over 473 pairs it scored 0.896 against
        0.886 for relevance alone: about five pairs, which read as noise. The end
        to end measurement is worth three cases. AUC ranks pairs; what decides a
        case is whether it crosses a fixed floor, and those are not the same
        question.
        """
        if not self.use_surface_answerability or not self.surface_vocabulary:
            return 1.0
        # The same reasoning as `min_vocabulary_for_answerability`, and needed
        # more sharply here: a small corpus lacks most *surface forms* of the
        # words it does discuss, so this factor would gate almost everything.
        # Turning it on without this guard failed a suite test that answers from
        # a five-document corpus - relevance 0.06 against a 0.15 floor.
        if len(self.surface_vocabulary) < self.min_vocabulary_for_answerability:
            return 1.0
        raw = tokenize(query)
        stems = tokenize(query, stem_words=True)
        if not raw or len(raw) != len(stems):
            return 1.0
        total = sum(self.idf(stem) for stem in stems)
        if total <= 0:
            return 1.0
        known = sum(idf for surface, idf in
                    ((r, self.idf(s)) for r, s in zip(raw, stems))
                    if surface in self.surface_vocabulary)
        return known / total

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
        answerability = self._answerability(query_set) * self._surface_factor(query)
        # Content tokens only. Measuring the phrase over every token lets a run
        # of stopwords score: "what is the" is three of the seven words in
        # "what is the boiling point of mercury", which scored 0.43 and carried
        # an out-of-corpus question past the abstention floor on its own.
        # Stopword adjacency is not evidence of anything.
        phrase_terms = tokenize(query, stem_words=True)
        now = self.clock()

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

            authority = _as_number(chunk.metadata.get("authority"), default=1.0)
            authority_score = max(0.0, min(1.5, authority)) / 1.5

            updated = _as_timestamp(chunk.metadata.get("updated_at"))
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
