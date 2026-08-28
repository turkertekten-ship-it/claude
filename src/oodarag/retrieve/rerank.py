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
from typing import Any, Callable

from oodarag.models import ScoredChunk
from oodarag.util.dates import to_timestamp
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

    It delegates to `util.dates.to_timestamp` so that a date this scorer can
    read is exactly a date the connectors can write. Two stages that parse the
    same field differently is the shape of L24: nothing errors, one side simply
    sees a date the other cannot.

    0.0 means unknown, which the caller reads as "neither fresh nor stale" -
    the right answer for a date nobody can parse.
    """
    return to_timestamp(value) or 0.0


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
    #: The exponent on IDF in the coverage factor, for *ranking*. The gate uses
    #: `gate_coverage_power` below, and the two must not be conflated: sharpening
    #: this number is free for a relative ordering and silently recalibrates a
    #: fixed abstention floor.
    #:
    #: Was 1.0. Raised to 2.0 after the corpus widened to 153 documents (L50),
    #: which reversed the measurement it had been held at 1.0 by
    #: (`scripts/gate_power_sweep.py`, external / 54 cases):
    #:
    #:   rank power   1.0     1.5     2.0     2.5     3.0
    #:   pass (gate shared)  47/54  47/54  47/54  43/54  42/54
    #:   pass (gate at 1.0)  47/54  48/54  49/54  48/54  47/54
    #:   recall@8            0.8721 0.9070 0.9302 0.9070 0.8953
    #:   nDCG@8              0.7487 0.7476 0.7538 0.7395 0.7328
    #:
    #: At 91 documents the best cell was rank 2.5 for +1 case, and it cost 0.039
    #: MRR, 0.022 nDCG and 0.031 of primary recall - a trade, and it was declined
    #: as an overfit. At 153 the optimum moved to 2.0 and stopped being a trade:
    #: +2 cases, +0.058 recall, nDCG *up* on both corpora, primary unchanged on
    #: pass, recall and MRR. The only cost is 0.018 of external MRR.
    #:
    #: **Re-verified after this session's chunking fixes** (1,810 -> 1,802
    #: chunks, the five over-ceiling ones split), and the external curve that
    #: chose 2.0 is gone: external is now flat at 49/54 and recall 0.9302 for
    #: every power from 1.0 to 3.0, with MRR declining monotonically as the
    #: power rises (.7741 .7696 .7643 .7539 .7411). Read alone, external now
    #: says 1.0.
    #:
    #: Primary says the opposite, and it is what holds the default
    #: (`scripts/reranker_reverify.py`, 2,537 chunks / 20 cases):
    #:
    #:   power      1.0     1.5     2.0     2.5     3.0
    #:   pass       18/20   18/20   18/20   18/20   18/20
    #:   MRR        0.6766  0.6766  0.7078  0.7078  0.7078
    #:   nDCG@8     0.6988  0.6981  0.7212  0.7212  0.7212
    #:
    #: 2.0 is the lowest power on primary's upper step, and taking it costs
    #: external 0.010 MRR; taking 1.0 instead would cost primary 0.031 MRR and
    #: 0.022 nDCG to buy that back. So the value stands and its justification
    #: does not - the external peak that chose it no longer exists, and the
    #: default now rests on primary alone. Fifth time the two corpora have
    #: wanted opposite things (L58 base_weight, L75 MMR, the abstention floor,
    #: L80 expansion).
    #:
    #: This does not repair the register mismatch L48 measured - IDF still ranks
    #: the discriminating query term first in only 29 of 40 goldens. Sharpening
    #: a partly-wrong ordering works here because the gate no longer moves with
    #: it, not because the ordering got better.
    coverage_power: float = 2.0
    #: The power the *abstention gate* weights coverage by. None means "the same
    #: as `coverage_power`", which is what shipped before this field existed and
    #: is no longer the default.
    #:
    #: They are separable because they answer different questions. Ranking asks
    #: which of these candidates is best; the gate asks whether the best one is
    #: good enough to answer from at all, against a fixed floor. Raising
    #: `coverage_power` sharpens the first and silently recalibrates the second,
    #: because `relevance` is computed from the same number.
    #:
    #: Held at 1.0 while the ranker runs at 2.0. The recovery from decoupling
    #: grows with the sharpening, which is the mechanism rather than one cell of
    #: a grid - at 153 documents, gate shared vs gate at 1.0: 47 vs 47 at rank
    #: 1.0, 47 vs 48 at 1.5, 47 vs 49 at 2.0, 43 vs 48 at 2.5, 42 vs 47 at 3.0.
    #: Without it, rank 2.0 would be worth nothing and rank 2.5 would cost four
    #: cases.
    gate_coverage_power: float | None = 1.0
    #: How the abstention gate's relevance splits between coverage and the
    #: phrase run:  `(1 - w) * gate_coverage + w * phrase`, times answerability.
    #: This was a bare 0.6/0.4 in the expression and had never been swept, which
    #: made it the one free parameter inside the feature L77 identified as the
    #: gate's bottleneck.
    #:
    #: Swept by AUC over 61 answerable and 15 abstainable goldens
    #: (`scripts/gate_split_sweep.py`), from a single retrieval pass, since
    #: relevance feeds only the gate and never the ordering:
    #:
    #:   coverage weight  0.0    0.2    0.4    0.5    0.6*   0.7    0.8    0.9    1.0
    #:   AUC              .737   .835   .839   .842   .845   .846   .851   .851   .851
    #:
    #: Monotone in coverage and flat from 0.8 up - not the non-monotone wobble
    #: that means noise (L72). The prediction going in was that the optimum
    #: would be interior, because the 0.6/0.4 mix beats either component alone;
    #: it is at the endpoint instead.
    #:
    #: **And AUC was wrong again.** Each weight swept against its own floor,
    #: since dropping the phrase term shifts both distributions upward
    #: (`scripts/gate_phrase_ab.py`, extended to floor 0.60 because the
    #: phrase-free curve was still rising at the end of the first range):
    #:
    #:   weight 0.4  floor  0.15   0.19*  0.22   0.25   0.28   0.32
    #:   external           47/54  49/54  48/54  47/54  45/54  44/54
    #:   held-out           19/22  19/22  19/22  18/22  17/22  16/22
    #:
    #:   weight 0.0  floor  0.15   0.22   0.28   0.32   0.36   0.40   0.50
    #:   external           46/54  46/54  46/54  48/54  46/54  45/54  41/54
    #:   held-out           19/22  19/22  19/22  19/22  19/22  18/22  16/22
    #:
    #: Best phrase-free is 48/54 at floor 0.32 against the shipped 49/54 at
    #: 0.19, tying on primary and held-out. The +0.006 of AUC bought a lost
    #: case, which is the third time AUC and the shipping metric have disagreed
    #: in this gate and the second running where AUC pointed at a change the
    #: pass rate rejected (L22, L78, L79).
    #:
    #: The mechanism is visible in the failure split rather than the totals. At
    #: the shipped floor the phrase term holds over-answers to 3 where dropping
    #: it gives 6; phrase-free needs floor 0.32 to get back to 3, and by then it
    #: has traded an over-refusal for it. The phrase run is not adding
    #: separation - AUC is right about that - it is letting the gate catch the
    #: same negatives from a *lower* floor, where fewer positives are lost.
    #: A signal can be worth keeping for where it puts the operating point.
    gate_phrase_weight: float = 0.4
    #: Swept on the current corpus and defaults, external / primary:
    #:
    #:   coverage_weight   0.20   0.35   0.45   0.60   0.80
    #:   external pass     48     49     49     49     49
    #:   external nDCG@8   .8179  .8000  .7944  .7858  .7694
    #:   primary pass      17     17     17     16     16
    #:
    #: **Ordering improves as this weight falls, and the pass rate breaks below
    #: 0.35.** 0.20 has the best nDCG in the sweep and loses a case; 0.35 keeps
    #: the case and gains 0.006 of nDCG over 0.45.
    #:
    #: Kept at 0.45 anyway. 0.35 sits one step from the cliff at 0.20 while 0.45
    #: has margin on both sides, and 0.006 of nDCG does not buy that away - the
    #: same reason `min_relevance` is not set to the peak of its own curve. The
    #: trade is real and worth knowing: something that lowered coverage's share
    #: without losing the case at 0.20 would be worth 0.024 of nDCG.
    coverage_weight: float = 0.45
    #: 0.25 is the optimum on both corpora, not merely acceptable on them:
    #:
    #:   phrase_weight     0.05   0.15   0.25   0.40   0.60
    #:   external nDCG@8   .7725  .7846  .7944  .7829  .7742
    #:   primary nDCG@8    .6986  .7211  .7246  .6796  .6714
    #:
    #: A single interior maximum on each, falling away symmetrically. An exact
    #: phrase match is rare and highly diagnostic, and weighting it past a
    #: quarter starts preferring a long shared prefix over actually covering the
    #: question.
    phrase_weight: float = 0.25
    #: Weak rather than inert, and the distinction took a measurement.
    #:
    #: It was recorded as inert on the grounds that "each corpus is a single
    #: filesystem source at authority 1.0". That is still true of the external
    #: corpus and **false of the primary one**, which carries four levels: 1.2
    #: for this repository, 1.0 for reference material, 0.9 for chat, 0.68 for
    #: a transcript-less video.
    #:
    #: It varies and it still does not discriminate, because the variation is
    #: not *inside the sets that get compared*. Over the 20 primary goldens:
    #:
    #:   every result shares one authority   7 of 20 queries
    #:   exactly two distinct values        11 of 20
    #:   median spread within a result set  0.20
    #:
    #: and 83 of 97 documents sit at the same level. Swept 0.0 to 0.3, recall@8
    #: is identical at every setting and pass rate never leaves 19/20; MRR and
    #: nDCG wobble in the third decimal.
    #:
    #: Left at 0.12. Unlike `recency_weight` below there is nothing to switch
    #: off - this prior is not wrong for the corpus, it simply has almost
    #: nothing to say about it, and tuning it against a 20-case set where no
    #: metric moves would be fitting noise. It becomes real on a corpus that
    #: mixes sources of genuinely different trust *within the same answers*.
    authority_weight: float = 0.12
    #: **0.0, and that is a measurement rather than a default.**
    #:
    #: This was 0.08 and unmeasurable for the life of the project: every
    #: document in both corpora shared an age, so the factor was a constant and
    #: could not reorder anything (L43, L50). The external corpus now carries
    #: each PyPI page's real release date as committed front matter, spanning
    #: **5.5 years**, and the factor spans 0.0042-1.0000 instead of
    #: 0.999182-0.999348 - a 6000x wider signal, worth 0.0797 of score at the
    #: old weight instead of 0.000013.
    #:
    #: Swept the first time it could be (external, 54 cases, dates live):
    #:
    #:   recency_weight  0.0    0.02   0.04   0.06   0.08   0.12   0.16
    #:   pass            49/54  47     47     47     47     45     45
    #:   recall@8        0.9302 0.8837 0.8837 0.8837 0.9070 0.8605 0.8605
    #:   nDCG@8          0.7538 0.7414 0.7373 0.7341 0.7390 0.7233 0.7143
    #:
    #: Zero dominates on every metric, and the factor was **harmless while dead
    #: and harmful once alive**. The reason is not subtle: recency is a prior
    #: for corpora whose documents *supersede* one another - news, changelogs,
    #: versioned docs, a chat archive - where a later document is more likely to
    #: be the answer. A corpus of package descriptions has no such property. How
    #: recently `pydantic` shipped a release says nothing about whether it
    #: answers a question about `relativedelta`.
    #:
    #: So it is off by default and this table is the argument for turning it on:
    #: raise it for a superseding corpus, and measure, because a prior that
    #: suits the wrong corpus is noise injected into every query. The primary
    #: corpus is unaffected either way - its files still share one checkout age.
    recency_weight: float = 0.0
    #: Earlier chunks of a document are usually its thesis; later ones are
    #: detail. **0.15, raised from 0.05 after the smallest weight turned out to
    #: be the most load-bearing.**
    #:
    #: Zeroing each weight in turn on the current corpus and defaults, external:
    #:
    #:   zeroed            coverage(.45)  phrase(.25)  authority(.12)  position(.05)
    #:   pass              48/54          48/54        49/54           **46/54**
    #:
    #: Position costs three cases when removed - more than coverage, which
    #: carries nine times its weight. Weight magnitude is not importance: the
    #: first chunk of a PyPI page is the package's own summary, and "which
    #: library does X?" is answered there rather than in installation notes or
    #: a changelog. That is a property of the corpus, and the same holds for
    #: source files, whose first chunk carries the module docstring.
    #:
    #: Swept on both, and re-measured after this session's chunking fixes
    #: (`scripts/reranker_reverify.py`; `pass / recall@8 / MRR / nDCG@8`):
    #:
    #:   weight     0.0                    0.05                   0.15
    #:   external   46 .8837 .6857 .7254   49 .9535 .7231 .7684   49 .9302 .7643 .7958
    #:   primary    16 .7812 .5521 .6008   17 .8750 .6036 .6588   18 .8750 .7078 .7212
    #:
    #:   weight     0.3                    0.5
    #:   external   49 .9186 .7969 .8087   49 .9302 .7930 .8068
    #:   primary    17 .7812 .7000 .6829   17 .8438 .7318 .7168
    #:
    #: 0.15 survives on both: joint-best on external pass, and on primary the
    #: outright peak on pass and nDCG and joint-best on recall. Unlike
    #: `coverage_power` above, this one is a peak rather than a plateau, and it
    #: sharpened - primary used to hold 17/20 from 0.15 to 0.3 and now tops out
    #: at 0.15 alone.
    #:
    #: Above 0.15, external ordering keeps climbing (MRR .7969 at 0.3 against
    #: .7643 here) while recall falls, on both corpora. That is a position
    #: prior beginning to answer from the top of the wrong document, and the
    #: held-out set is where the cost surfaces: 19/22 everywhere except 0.5,
    #: which drops to 18/22 while looking like an improvement on external
    #: ordering alone.
    position_weight: float = 0.15
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
                coverage = gate_coverage = 0.0
            elif self.idf is None:
                coverage = gate_coverage = len(query_set & chunk_terms) / len(query_set)
            else:
                # Weighted by informativeness: matching a term that appears
                # everywhere is not evidence, matching a rare one is.
                matched = query_set & chunk_terms

                def _weighted(power: float) -> float:
                    total = sum(self.idf(t) ** power for t in query_set)
                    return (sum(self.idf(t) ** power for t in matched) / total
                            if total else 0.0)

                coverage = _weighted(self.coverage_power)
                gate_coverage = (coverage if self.gate_coverage_power is None
                                 else _weighted(self.gate_coverage_power))
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
            relevance = ((1.0 - self.gate_phrase_weight) * gate_coverage
                         + self.gate_phrase_weight * phrase_score) * answerability

            result.components.update({
                "rerank_relevance": relevance,
                # The gate's own coverage, which is *not* `rerank_coverage`:
                # ranking uses `coverage_power` 2.0 and the gate uses
                # `gate_coverage_power` 1.0, so the two differ (0.5505 against
                # 0.5998 on one measured chunk). Recording only the ranking one
                # left the abstention decision the single quantity in the
                # pipeline that could not be inspected after the fact, and made
                # the coverage/phrase split below unsweepable without re-running
                # retrieval for every candidate value.
                "rerank_gate_coverage": gate_coverage,
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
