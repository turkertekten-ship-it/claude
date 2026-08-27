"""Two retrieval arms, fused by rank rather than by score.

Lexical and dense retrieval fail in opposite directions, which is the entire
argument for running both. BM25 cannot match `katılma payı` against a chunk
that says `fon birimi`, and an embedding cannot reliably find `III-52.1` or
`WQQ` — a rare literal string is noise to a model that never saw it in
training but is a perfect signal to an inverted index. A pipeline that answers
regulatory questions needs both, and it needs to be able to say which arm found
the passage.

**Why Reciprocal Rank Fusion and not a weighted sum of scores.** BM25 scores
are unbounded and depend on corpus statistics; cosine similarities sit in a
narrow band near the top of their range and depend on the embedding model.
Normalising them onto a common scale requires per-query min-max, which is
unstable exactly when it matters (a query with one strong hit and nine weak
ones min-maxes the noise up to 1.0). RRF throws the magnitudes away and keeps
the ranks: ``sum over arms of 1 / (k + rank)``, k=60. It needs no calibration,
survives an arm being empty, and is why a new embedding model can be swapped in
without retuning a fusion weight.

The cost is that RRF discards how *confident* an arm was, so the raw scores and
both ranks are carried in ``ScoredChunk.components`` untouched. That is not
decoration: the single most common retrieval bug is one arm silently returning
nothing — a missing API key, an index that was never built, a filter that
matched no documents — and from a fused score alone that is indistinguishable
from the arm having voted and lost.

Every failure here degrades instead of raising. No embedder, an embedder that
throws, an unbuilt vector index, a corrupt BM25 blob: the affected arm
contributes nothing, a warning is logged, and the other arm answers.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from oodarag.index.bm25 import BM25Index
from oodarag.index.store import Store
from oodarag.index.vector import VectorIndex
from oodarag.models import Document, ScoredChunk
from oodarag.util.logging import get_logger
from oodarag.util.text import clean

log = get_logger("retrieve")

#: The constant from Cormack et al. 2009. Larger flattens the contribution of
#: rank position (all arms count nearly equally); smaller makes rank 1 dominate.
#: 60 is the published default and there is no evidence in this corpus to move it.
RRF_K = 60.0

#: How deep each arm goes before fusion. Fusing top-8 lists loses documents that
#: rank 9th in both arms and would have fused to the top; going deeper than this
#: mostly costs time.
ARM_DEPTH = 50

Embedder = Callable[[str], Sequence[float]]


@dataclass(slots=True)
class RetrievalFilters:
    """Restrictions applied *before* scoring, as a set of eligible chunk ids.

    Filtering after retrieval is the obvious implementation and the wrong one:
    ask for the top 8 chunks from `spk` and post-filtering may hand back two,
    because the other six came from elsewhere. Pushing the filter into both arms
    means k results are k results.
    """

    source_system: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    doc_ids: tuple[str, ...] = ()
    updated_after: float | None = None
    updated_before: float | None = None
    #: Convenience recency window; resolved against `now` at retrieval time.
    within_days: float | None = None

    @property
    def is_empty(self) -> bool:
        return not (
            self.source_system
            or self.metadata
            or self.doc_ids
            or self.updated_after is not None
            or self.updated_before is not None
            or self.within_days is not None
        )

    @classmethod
    def coerce(cls, obj: RetrievalFilters | Mapping[str, Any] | None) -> RetrievalFilters | None:
        """Accept a dataclass, a plain dict, or None.

        A dict is what a CLI flag or a JSON request body produces. Unrecognised
        keys are logged and dropped rather than raising: a typo in a filter name
        should narrow nothing and say so, not take down a query.
        """
        if obj is None:
            return None
        if isinstance(obj, cls):
            return obj
        if not isinstance(obj, Mapping):
            log.warn("filters ignored, not a mapping", got=type(obj).__name__)
            return None
        aliases = {
            "source": "source_system",
            "sources": "source_system",
            "source_systems": "source_system",
            "since": "updated_after",
            "until": "updated_before",
            "recency_days": "within_days",
            "days": "within_days",
            "doc_id": "doc_ids",
        }
        out = cls()
        unknown: list[str] = []
        for raw_key, value in obj.items():
            key = aliases.get(str(raw_key), str(raw_key))
            if value is None:
                continue
            if key == "source_system":
                out.source_system = (value,) if isinstance(value, str) else tuple(value)
            elif key == "doc_ids":
                out.doc_ids = (value,) if isinstance(value, str) else tuple(value)
            elif key == "metadata" and isinstance(value, Mapping):
                out.metadata = dict(value)
            elif key in ("updated_after", "updated_before", "within_days"):
                try:
                    setattr(out, key, float(value))
                except (TypeError, ValueError):
                    log.warn("filter ignored, not a number", key=key, value=repr(value)[:60])
            else:
                unknown.append(str(raw_key))
        if unknown:
            log.warn("unknown filter keys ignored", keys=sorted(unknown))
        return out


def _resolve_embedder(embedder: Any) -> Embedder | None:
    """Duck-type whatever the caller passed into a `str -> vector` callable.

    The embedding layer is a sibling module owned elsewhere, so this binds to a
    shape rather than to a class: `embed_query(text)`, `embed([texts])`, or a
    plain callable. Anything else is refused loudly at construction, which is a
    better place to find out than inside a query.
    """
    if embedder is None:
        return None
    for attr in ("embed_query", "embed_one"):
        fn = getattr(embedder, attr, None)
        if callable(fn):
            return fn  # type: ignore[no-any-return]
    batch = getattr(embedder, "embed", None)
    if callable(batch):

        def _one(text: str) -> Sequence[float]:
            out = batch([text])
            return out[0] if out else []

        return _one
    if callable(embedder):
        return embedder  # type: ignore[no-any-return]
    log.warn("embedder ignored, no usable interface", got=type(embedder).__name__)
    return None


class HybridRetriever:
    """BM25 + dense cosine, fused with RRF, filtered before scoring."""

    __slots__ = ("store", "bm25", "vector", "rrf_k", "arm_depth",
                 "bm25_weight", "dense_weight", "_embed")

    def __init__(
        self,
        store: Store,
        *,
        bm25: BM25Index | None = None,
        vector: VectorIndex | None = None,
        embedder: Any = None,
        rrf_k: float = RRF_K,
        arm_depth: int = ARM_DEPTH,
        bm25_weight: float = 1.0,
        dense_weight: float = 1.0,
    ) -> None:
        self.store = store
        self.bm25 = bm25
        self.vector = vector
        self.rrf_k = float(rrf_k)
        self.arm_depth = max(1, int(arm_depth))
        self.bm25_weight = float(bm25_weight)
        self.dense_weight = float(dense_weight)
        self._embed = _resolve_embedder(embedder)

    @classmethod
    def from_store(cls, store: Store, *, embedder: Any = None, **kwargs: Any) -> HybridRetriever:
        """Load or rebuild both arms from the store. The normal entry point.

        The vector arm is built from whatever vectors the store holds; if it
        holds none — the embedder was never run, or ran and failed — the arm is
        simply empty and every result comes from BM25. That is a degraded mode
        worth having, not an error worth raising.
        """
        try:
            bm25 = BM25Index.ensure(store)
        except Exception as e:
            log.error("bm25 arm unavailable", err=str(e)[:200])
            bm25 = None
        try:
            vector = VectorIndex.from_store(store)
        except Exception as e:
            log.error("dense arm unavailable", err=str(e)[:200])
            vector = None
        return cls(store, bm25=bm25, vector=vector, embedder=embedder, **kwargs)

    # ------------------------------------------------------------ querying

    def retrieve(
        self,
        query: str,
        k: int = 8,
        filters: RetrievalFilters | Mapping[str, Any] | None = None,
        *,
        now: float | None = None,
    ) -> list[ScoredChunk]:
        """Top-k chunks with their parent documents and a full score breakdown."""
        text = clean(query or "")
        if not text:
            log.warn("empty query")
            return []
        k = max(1, int(k))

        allowed = self._eligible(filters, now=now)
        if allowed is not None and not allowed:
            log.warn("filters matched no documents", query=text[:80])
            return []

        bm25_hits = self._bm25_arm(text, allowed)
        dense_hits = self._dense_arm(text, allowed)
        if not bm25_hits and not dense_hits:
            log.warn("no hits from either arm", query=text[:80],
                     bm25=self.bm25 is not None, dense=self.vector is not None)
            return []

        fused = self._fuse(bm25_hits, dense_hits)
        return self._materialise(fused, k)

    def _eligible(
        self,
        filters: RetrievalFilters | Mapping[str, Any] | None,
        *,
        now: float | None,
    ) -> set[str] | None:
        """The chunk ids a filter permits, or None for "no restriction"."""
        parsed = RetrievalFilters.coerce(filters)
        if parsed is None or parsed.is_empty:
            return None
        updated_after = parsed.updated_after
        if parsed.within_days is not None:
            window = (now if now is not None else time.time()) - parsed.within_days * 86400.0
            updated_after = window if updated_after is None else max(updated_after, window)
        try:
            return self.store.find_chunk_ids(
                source_system=parsed.source_system or None,
                doc_ids=parsed.doc_ids or None,
                metadata=parsed.metadata or None,
                updated_after=updated_after,
                updated_before=parsed.updated_before,
            )
        except Exception as e:
            # A broken filter must not silently widen the search to everything;
            # returning an empty set makes the query fail closed.
            log.error("filter evaluation failed; returning no results", err=str(e)[:200])
            return set()

    def _bm25_arm(self, text: str, allowed: set[str] | None) -> list[tuple[str, float]]:
        if self.bm25 is None or not len(self.bm25):
            return []
        try:
            return self.bm25.search(text, k=self.arm_depth, allowed=allowed)
        except Exception as e:
            log.error("bm25 arm failed", err=str(e)[:200])
            return []

    def _dense_arm(self, text: str, allowed: set[str] | None) -> list[tuple[str, float]]:
        if self.vector is None or not len(self.vector) or self._embed is None:
            return []
        try:
            qvec = self._embed(text)
        except Exception as e:
            # A hosted embedder with no key, no egress, or a rate limit lands
            # here. The lexical arm still answers.
            log.warn("query embedding failed, dense arm skipped", err=str(e)[:200])
            return []
        if not qvec:
            log.warn("embedder returned nothing, dense arm skipped")
            return []
        try:
            return self.vector.search(qvec, k=self.arm_depth, allowed=allowed)
        except Exception as e:
            log.error("dense arm failed", err=str(e)[:200])
            return []

    def _fuse(
        self, bm25_hits: Sequence[tuple[str, float]], dense_hits: Sequence[tuple[str, float]]
    ) -> list[tuple[str, dict[str, float]]]:
        """RRF over the two ranked lists.

        Ranks are 1-based, so `rank_bm25 == 0.0` in the components means "this
        chunk was not in the BM25 list at all" and never "it ranked first".
        """
        parts: dict[str, dict[str, float]] = {}
        for arm, hits, weight in (
            ("bm25", bm25_hits, self.bm25_weight),
            ("dense", dense_hits, self.dense_weight),
        ):
            for rank, (chunk_id, score) in enumerate(hits, start=1):
                comp = parts.setdefault(
                    chunk_id,
                    {"bm25": 0.0, "dense": 0.0, "rrf": 0.0, "rank_bm25": 0.0, "rank_dense": 0.0},
                )
                comp[arm] = float(score)
                comp[f"rank_{arm}"] = float(rank)
                comp["rrf"] += weight / (self.rrf_k + rank)
        ranked = sorted(
            ((cid, comp) for cid, comp in parts.items()),
            key=lambda kv: (-round(kv[1]["rrf"], 9), kv[0]),
        )
        return ranked

    def _materialise(
        self, fused: Sequence[tuple[str, dict[str, float]]], k: int
    ) -> list[ScoredChunk]:
        """Turn fused ids into ScoredChunks, skipping ids the store no longer has.

        An index built before a delete will happily return chunk ids that are
        gone. Backfilling from the next candidates keeps `retrieve(k=8)`
        honest instead of returning six results and no explanation.
        """
        wanted = [cid for cid, _ in fused[: k * 3]] or [cid for cid, _ in fused]
        chunks = self.store.get_chunks(wanted)
        missing = [cid for cid in wanted if cid not in chunks]
        if missing:
            log.warn("index references chunks the store has dropped; reindex is due",
                     count=len(missing), example=missing[0])

        doc_ids = {chunks[cid].doc_id for cid in wanted if cid in chunks}
        try:
            documents: dict[str, Document] = self.store.get_documents(doc_ids)
        except Exception as e:
            log.warn("parent documents could not be loaded", err=str(e)[:200])
            documents = {}

        out: list[ScoredChunk] = []
        for chunk_id, components in fused:
            chunk = chunks.get(chunk_id)
            if chunk is None:
                continue
            out.append(
                ScoredChunk(
                    chunk=chunk,
                    score=round(components["rrf"], 9),
                    components=dict(components),
                    document=documents.get(chunk.doc_id),
                )
            )
            if len(out) >= k:
                break
        return out

    # ----------------------------------------------------------- reporting

    def stats(self) -> dict[str, Any]:
        return {
            "bm25": self.bm25.stats() if self.bm25 is not None else None,
            "vector": self.vector.stats() if self.vector is not None else None,
            "embedder": self._embed is not None,
            "rrf_k": self.rrf_k,
            "arm_depth": self.arm_depth,
        }

    def __repr__(self) -> str:
        n_bm25 = len(self.bm25) if self.bm25 is not None else 0
        n_vec = len(self.vector) if self.vector is not None else 0
        return f"<HybridRetriever bm25={n_bm25} dense={n_vec} embedder={self._embed is not None}>"
