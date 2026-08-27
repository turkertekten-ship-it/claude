"""A feature-based reranker: no model, and every number it produces is auditable.

A cross-encoder reranker is better at this job and cannot be used here. It
needs a model file or an API call, it cannot explain itself, and when it demotes
the one passage that answered the question there is nothing to inspect. This
module trades that ceiling for a property that matters more in a regulated
setting: for any ranked result, `components` says exactly why it ranked there,
and the weights that produced it are five numbers in one dataclass.

The five features, and the failure each one exists to fix:

* **Exact phrase.** Fusion is a bag-of-words vote. A query for
  `nitelikli yatırımcı` scores a chunk containing both words far apart the same
  as one containing the phrase. The longest contiguous run of query tokens found
  in the chunk, as a fraction of the query, restores the word order that BM25
  threw away.

* **Lexical coverage.** The dense arm will happily return a chunk that is
  topically adjacent and mentions none of the asked-about terms. Coverage —
  what fraction of the query's content terms actually appear, surface form or
  Turkish stem — is the cheapest available check that a passage is about the
  question rather than about the neighbourhood of the question.

* **Source authority.** A rule about a filing deadline that cites a blog over
  the Resmî Gazete is wrong even when the blog is right, because the citation is
  what an auditor follows. Authority comes from the caller (typically
  `FirmProfile.authority_map`), and an unmapped source gets a deliberately
  mediocre default rather than a good one.

* **Recency decay.** Regulation is superseded. An exponential half-life is used
  instead of a cut-off because a cliff at N days makes a document worthless the
  morning after it crosses it, which is never what the reader meant. 180 days is
  a default, not a finding; a corpus of statutes wants a much longer one.

* **Near-duplicate penalty (MMR).** The single most common bad result set is
  eight chunks that are the same paragraph from eight mirrors of one page.
  Greedy maximal-marginal-relevance selection subtracts each candidate's
  similarity to what has already been picked, so the eighth slot goes to a
  passage that says something new.

Weights are a `RerankWeights` instance and are normalised, so `relevance` is
always in [0, 1] and a components dump is comparable across queries. Nothing
here mutates its input: the returned `ScoredChunk`s are copies, so a caller can
diff pre- and post-rerank orderings.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from oodarag.index.bm25 import tokenize_index_text, turkish_stem
from oodarag.models import ScoredChunk
from oodarag.util.logging import get_logger
from oodarag.util.text import STOPWORDS, clean

log = get_logger("rerank")

#: How hard a near-duplicate is punished. At 0.35 a chunk that is a verbatim
#: copy of one already selected needs a 0.35 relevance lead to survive, which
#: is large; a chunk that merely overlaps half its vocabulary loses 0.17.
DIVERSITY = 0.35

#: What an unmapped source is worth. Deliberately mediocre: a source nobody
#: graded should not outrank one someone graded highly, nor be treated as junk.
DEFAULT_AUTHORITY = 0.5

#: A document with no usable timestamp scores neutral rather than stale. Missing
#: metadata is not evidence of age, and treating it as such quietly buries every
#: source whose connector does not emit dates.
NEUTRAL_RECENCY = 0.5

#: Cap on query length for the phrase scan, which is O(len^2) in windows.
_MAX_PHRASE_TOKENS = 24


@dataclass(slots=True, frozen=True)
class RerankWeights:
    """Relative pull of each feature. Normalised at use, so only ratios matter."""

    base: float = 1.0
    phrase: float = 0.6
    coverage: float = 0.8
    authority: float = 0.5
    recency: float = 0.4

    @property
    def total(self) -> float:
        return self.base + self.phrase + self.coverage + self.authority + self.recency


DEFAULT_WEIGHTS = RerankWeights()


def _content_terms(tokens: Sequence[str]) -> set[str]:
    """Surface tokens plus their stems, stopwords and single characters dropped."""
    out: set[str] = set()
    for token in tokens:
        if len(token) <= 1 or token in STOPWORDS:
            continue
        out.add(token)
        out.add(turkish_stem(token))
    return out


def _longest_phrase(qtokens: Sequence[str], haystack: str) -> int:
    """Longest run of consecutive query tokens present in the chunk, in tokens."""
    n = len(qtokens)
    for size in range(n, 1, -1):
        for start in range(0, n - size + 1):
            if f" {' '.join(qtokens[start : start + size])} " in haystack:
                return size
    return 0


def _timestamp(scored: ScoredChunk) -> float | None:
    """Best available age signal, in epoch seconds, or None."""
    doc = scored.document
    if doc is not None:
        for value in (doc.updated_at, doc.created_at):
            try:
                ts = float(value)
            except (TypeError, ValueError):
                continue
            if ts > 0:
                return ts
    for key in ("updated_at", "published_at", "fetched_at", "timestamp"):
        raw = scored.chunk.metadata.get(key)
        try:
            ts = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if ts > 0:
            return ts
    return None


def _source_of(scored: ScoredChunk) -> str:
    if scored.document is not None and scored.document.source_system:
        return scored.document.source_system
    meta_source = scored.chunk.metadata.get("source_system") or scored.chunk.metadata.get("source")
    return str(meta_source) if meta_source else ""


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter) if inter else 0.0


def rerank(
    query: str,
    scored: Sequence[ScoredChunk],
    authority: Mapping[str, float] | None = None,
    now: float | None = None,
    half_life_days: float = 180.0,
    *,
    weights: RerankWeights | None = None,
    diversity: float = DIVERSITY,
    default_authority: float = DEFAULT_AUTHORITY,
    k: int | None = None,
) -> list[ScoredChunk]:
    """Reorder fused results by explainable features. Returns copies.

    `half_life_days <= 0` disables recency decay entirely (every candidate
    scores 1.0), which is the right setting for a corpus of statutes where age
    carries no signal. `authority` maps a document's `source_system` to a weight
    in [0, 1]; anything outside that range is clamped rather than allowed to
    dominate the sum.

    The returned `ScoredChunk.score` is the post-rerank score. The fused score
    it replaces is preserved in `components["pre_rerank"]`, and every feature
    that contributed is written alongside it.
    """
    if not scored:
        return []
    weights = weights or DEFAULT_WEIGHTS
    total_weight = weights.total or 1.0
    now = time.time() if now is None else float(now)
    decay_enabled = half_life_days > 0
    qtokens_all = tokenize_index_text(clean(query or ""))
    qtokens = qtokens_all[:_MAX_PHRASE_TOKENS]
    qterms = _content_terms(qtokens_all)
    if not qtokens:
        log.warn("rerank got an empty query; features degrade to the fused order")

    scores = [float(s.score) for s in scored]
    lo, hi = min(scores), max(scores)
    span = hi - lo

    features: list[dict[str, float]] = []
    termsets: list[set[str]] = []
    for candidate in scored:
        tokens = tokenize_index_text(candidate.chunk.indexed_text)
        haystack = f" {' '.join(tokens)} "
        terms = _content_terms(tokens)
        termsets.append(terms)

        if not qtokens:
            phrase = 0.0
        elif len(qtokens) == 1:
            phrase = 1.0 if qtokens[0] in tokens else 0.0
        else:
            phrase = _longest_phrase(qtokens, haystack) / len(qtokens)

        coverage = (len(qterms & terms) / len(qterms)) if qterms else 0.0

        raw_auth = (authority or {}).get(_source_of(candidate), default_authority)
        try:
            auth = min(1.0, max(0.0, float(raw_auth)))
        except (TypeError, ValueError):
            auth = default_authority

        ts = _timestamp(candidate)
        if ts is None:
            age_days = -1.0
            recency = 1.0 if not decay_enabled else NEUTRAL_RECENCY
        else:
            age_days = max(0.0, (now - ts) / 86400.0)
            recency = 1.0 if not decay_enabled else math.pow(0.5, age_days / half_life_days)

        # A constant fused score carries no ranking information, so it must not
        # be min-maxed into an arbitrary spread; flatten it to 1.0 instead.
        base = 1.0 if span <= 0 else (float(candidate.score) - lo) / span

        relevance = (
            weights.base * base
            + weights.phrase * phrase
            + weights.coverage * coverage
            + weights.authority * auth
            + weights.recency * recency
        ) / total_weight

        features.append(
            {
                "pre_rerank": round(float(candidate.score), 9),
                "rerank_base": round(base, 6),
                "phrase": round(phrase, 6),
                "coverage": round(coverage, 6),
                "authority": round(auth, 6),
                "recency": round(recency, 6),
                "age_days": round(age_days, 3),
                "relevance": round(relevance, 6),
            }
        )

    order = _mmr_select(scored, features, termsets, diversity)
    limit = len(order) if k is None else max(1, int(k))

    out: list[ScoredChunk] = []
    for rank, (idx, final, penalty) in enumerate(order[:limit], start=1):
        components = dict(scored[idx].components)
        components.update(features[idx])
        components["duplicate_penalty"] = round(penalty, 6)
        components["rerank_score"] = round(final, 6)
        components["rerank_rank"] = float(rank)
        out.append(replace(scored[idx], score=round(final, 6), components=components))
    return out


def _mmr_select(
    scored: Sequence[ScoredChunk],
    features: Sequence[Mapping[str, float]],
    termsets: Sequence[set[str]],
    diversity: float,
) -> list[tuple[int, float, float]]:
    """Greedy maximal marginal relevance. Returns (index, final score, penalty).

    Greedy, not optimal: the optimal diverse subset is NP-hard and the greedy
    approximation is what every published MMR implementation does. Selection is
    O(n^2) in candidates, which for the fifty-odd a fusion produces is free.
    """
    diversity = max(0.0, float(diversity))
    hashes = [s.chunk.content_hash for s in scored]
    remaining = set(range(len(scored)))
    chosen: list[tuple[int, float, float]] = []
    chosen_idx: list[int] = []

    while remaining:
        best: tuple[int, float, float] | None = None
        for idx in remaining:
            penalty = 0.0
            if chosen_idx and diversity > 0.0:
                sims = []
                for prev in chosen_idx:
                    # Byte-identical chunks are the mirror-site case and get no
                    # benefit of the doubt from a token-overlap estimate.
                    sims.append(
                        1.0 if hashes[idx] and hashes[idx] == hashes[prev]
                        else _jaccard(termsets[idx], termsets[prev])
                    )
                penalty = max(sims)
            final = float(features[idx]["relevance"]) - diversity * penalty
            key = (round(final, 9), -idx)
            if best is None or key > (round(best[1], 9), -best[0]):
                best = (idx, final, penalty)
        assert best is not None  # remaining is non-empty
        chosen.append(best)
        chosen_idx.append(best[0])
        remaining.discard(best[0])
    return chosen


def explain(scored: Sequence[ScoredChunk], top: int = 10) -> str:
    """A fixed-width dump of the score breakdown. For a `--explain` flag and for
    the moment someone asks why the obvious answer came fourth."""
    if not scored:
        return "no results"
    cols = (
        ("rrf", "rrf"), ("bm25", "bm25"), ("dense", "dense"), ("phrase", "phrase"),
        ("coverage", "cover"), ("authority", "auth"), ("recency", "recency"),
        ("duplicate_penalty", "dup-pen"), ("rerank_score", "final"),
    )
    header = f"{'#':>2}  {'chunk':<26} " + " ".join(f"{label:>9}" for _, label in cols) + "  source"
    lines = [header, "-" * len(header)]
    for rank, s in enumerate(scored[:top], start=1):
        cells = " ".join(f"{s.components.get(key, 0.0):>9.4f}" for key, _ in cols)
        source = (s.document.source_system if s.document else "?") or "?"
        lines.append(f"{rank:>2}  {s.chunk.chunk_id[:26]:<26} {cells}  {source}")
    return "\n".join(lines)


def rerank_report(scored: Sequence[ScoredChunk]) -> dict[str, Any]:
    """Aggregate feature statistics for one result set — the shape an eval
    harness wants when it is asking "is the reranker doing anything?"."""
    if not scored:
        return {"results": 0}
    def mean(key: str) -> float:
        vals = [s.components.get(key, 0.0) for s in scored]
        return round(sum(vals) / len(vals), 4)
    return {
        "results": len(scored),
        "mean_coverage": mean("coverage"),
        "mean_phrase": mean("phrase"),
        "mean_authority": mean("authority"),
        "mean_recency": mean("recency"),
        "mean_duplicate_penalty": mean("duplicate_penalty"),
        "sources": sorted({(s.document.source_system if s.document else "?") for s in scored}),
    }
