"""Brute-force cosine similarity over stored float32 vectors.

An ANN index (HNSW, IVF, ScaNN) buys sublinear search and costs a C extension,
a build step, a tuning surface, and approximate recall you then have to
measure. At the scale this pipeline targets — one firm's documents, tens of
thousands of chunks — a full scan of a float32 matrix takes single-digit
milliseconds in numpy and tens of milliseconds in pure Python. Exact search
that is fast enough beats approximate search that needs a dependency.

Three decisions worth stating:

**Vectors are normalised once, at insert.** Cosine then reduces to a dot
product, so the query path does no per-vector square roots. A zero vector
(an empty chunk, a provider that returned nulls) is kept as zeros and scores
0.0 against everything, rather than raising a ZeroDivisionError somewhere deep
in a retrieval call.

**The numpy path must produce identical ordering, not merely similar.** numpy
sums with pairwise/SIMD accumulation and Python sums left to right, so the two
disagree in the last bits. On a corpus with duplicated boilerplate — which is
every real corpus — near-ties are common and the last bits decide the order.
Both paths therefore round to 1e-9 before sorting and tie-break on chunk id, so
installing numpy changes the speed and nothing else. That property is what
makes it safe to develop against the stdlib path and deploy against numpy.

**Dimension mismatch returns nothing rather than a truncated comparison.**
Scoring a 384-dim query against 768-dim vectors over the shared prefix produces
numbers that look like similarities and are noise. The failure mode of a silent
half-comparison is "retrieval quietly got worse"; the failure mode of an empty
result plus a warning is "retrieval is obviously broken", which someone fixes.
"""

from __future__ import annotations

import math
import os
from array import array
from collections.abc import Collection, Iterable, Sequence
from typing import TYPE_CHECKING, Any

from oodarag.util.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from oodarag.index.store import Store

log = get_logger("vector")

#: Guarded optional import. numpy is never required; if it is absent the pure
#: stdlib path runs and produces the same answers.
try:  # pragma: no cover - presence depends on the environment
    import numpy as _numpy
except ImportError:  # pragma: no cover
    _numpy = None  # type: ignore[assignment]

#: Below this many vectors the cost of materialising the matrix dominates the
#: scan, so the stdlib path is genuinely faster. Above it numpy wins by an
#: order of magnitude.
NUMPY_THRESHOLD = 256

#: Scores are rounded here before sorting so the numpy and stdlib paths cannot
#: disagree on the order of a near-tie. 1e-9 is ~7 orders of magnitude above
#: float64 accumulation noise and ~2 below anything a reranker cares about.
_ROUND = 9


def _l2_normalise(vec: Sequence[float]) -> tuple[array, float]:
    """Return (unit float32 array, original norm). A zero vector stays zero."""
    total = 0.0
    values: list[float] = []
    for x in vec:
        try:
            f = float(x)
        except (TypeError, ValueError):
            f = 0.0
        if f != f or f in (math.inf, -math.inf):
            f = 0.0
        values.append(f)
        total += f * f
    norm = math.sqrt(total)
    if norm <= 0.0:
        return array("f", [0.0] * len(values)), 0.0
    return array("f", [v / norm for v in values]), norm


class VectorIndex:
    """Exact cosine search over an in-memory float32 matrix.

    Not thread-safe for concurrent mutation; concurrent *searches* are fine.
    The pipeline's shape is one indexer then many readers, so a lock on every
    search would cost more than it protects.
    """

    __slots__ = ("dim", "_ids", "_pos", "_vecs", "_matrix", "_dirty", "_np", "_threshold",
                 "rejected_dim", "rejected_zero")

    def __init__(
        self,
        dim: int | None = None,
        *,
        use_numpy: bool | None = None,
        numpy_threshold: int = NUMPY_THRESHOLD,
        numpy_module: Any = None,
    ) -> None:
        self.dim = dim
        self._ids: list[str] = []
        self._pos: dict[str, int] = {}
        self._vecs: list[array] = []
        self._matrix: Any = None
        self._dirty = True
        self._threshold = max(1, int(numpy_threshold))
        self.rejected_dim = 0
        self.rejected_zero = 0
        # OODARAG_NO_NUMPY exists so a bug report can be reproduced on the
        # stdlib path without uninstalling anything.
        forced_off = os.environ.get("OODARAG_NO_NUMPY", "").strip().lower() in {"1", "true", "yes"}
        module = numpy_module if numpy_module is not None else _numpy
        if use_numpy is False or forced_off:
            self._np = None
        elif use_numpy is True:
            self._np = module  # may be None; _use_numpy() handles that
            if module is None:
                log.warn("numpy requested but not importable; using the stdlib path")
        else:
            self._np = module

    # ------------------------------------------------------------ building

    def add(self, chunk_id: str, vec: Sequence[float]) -> bool:
        """Insert or replace one vector. False means it was rejected, and the
        reason is in `rejected_dim` / `rejected_zero` plus a log line."""
        if not vec:
            self.rejected_zero += 1
            return False
        if self.dim is None:
            self.dim = len(vec)
        if len(vec) != self.dim:
            self.rejected_dim += 1
            log.warn("vector rejected, wrong dimension", chunk_id=chunk_id,
                     got=len(vec), want=self.dim)
            return False
        unit, norm = _l2_normalise(vec)
        if norm <= 0.0:
            self.rejected_zero += 1
            log.warn("vector is all zeros; it will never be retrieved", chunk_id=chunk_id)
        idx = self._pos.get(chunk_id)
        if idx is None:
            self._pos[chunk_id] = len(self._ids)
            self._ids.append(chunk_id)
            self._vecs.append(unit)
        else:
            self._vecs[idx] = unit
        self._dirty = True
        return True

    def add_many(self, pairs: Iterable[tuple[str, Sequence[float]]]) -> int:
        return sum(1 for cid, vec in pairs if self.add(cid, vec))

    def build_from_store(self, store: Store) -> VectorIndex:
        """Load every vector that still has a live chunk behind it."""
        self._ids.clear()
        self._pos.clear()
        self._vecs.clear()
        self._matrix = None
        self._dirty = True
        added = self.add_many(store.iter_vectors())
        log.info("vector index built", vectors=added, dim=self.dim,
                 rejected_dim=self.rejected_dim)
        return self

    @classmethod
    def from_store(cls, store: Store, **kwargs: Any) -> VectorIndex:
        return cls(**kwargs).build_from_store(store)

    def remove(self, chunk_id: str) -> bool:
        """Swap-pop removal: O(1), and it reorders ids, which nothing depends on
        because every result carries its chunk id."""
        idx = self._pos.pop(chunk_id, None)
        if idx is None:
            return False
        last = len(self._ids) - 1
        if idx != last:
            self._ids[idx] = self._ids[last]
            self._vecs[idx] = self._vecs[last]
            self._pos[self._ids[idx]] = idx
        self._ids.pop()
        self._vecs.pop()
        self._dirty = True
        return True

    # ----------------------------------------------------------- searching

    def _use_numpy(self) -> Any:
        if self._np is None or len(self._ids) < self._threshold:
            return None
        return self._np

    def _matrix_for(self, np: Any) -> Any:
        if self._matrix is not None and not self._dirty:
            return self._matrix
        try:
            buf = b"".join(v.tobytes() for v in self._vecs)
            flat = np.frombuffer(buf, dtype=np.float32)
            self._matrix = flat.reshape(len(self._vecs), self.dim or 0).astype(np.float64)
            self._dirty = False
        except Exception as e:  # any numpy surprise falls back, never raises
            log.warn("numpy matrix build failed, using the stdlib path", err=str(e)[:200])
            self._matrix = None
            self._np = None
        return self._matrix

    def search(
        self, vec: Sequence[float], k: int = 20, allowed: Collection[str] | None = None
    ) -> list[tuple[str, float]]:
        """Top-k `(chunk_id, cosine)`, highest first.

        Returns `[]` — never raises — for an empty index, an empty query
        vector, a zero query vector, or a query whose dimension does not match
        the index.
        """
        if not self._ids or k <= 0 or not vec:
            return []
        if self.dim is not None and len(vec) != self.dim:
            log.warn("query vector rejected, wrong dimension", got=len(vec), want=self.dim)
            return []
        query, norm = _l2_normalise(vec)
        if norm <= 0.0:
            log.warn("query vector is all zeros; no dense results")
            return []

        np = self._use_numpy()
        matrix = self._matrix_for(np) if np is not None else None
        if matrix is not None:
            try:
                raw = matrix.dot(np.array(list(query), dtype=np.float64)).tolist()
            except Exception as e:
                log.warn("numpy search failed, using the stdlib path", err=str(e)[:200])
                raw = self._scores_stdlib(query)
        else:
            raw = self._scores_stdlib(query)

        scored: list[tuple[str, float]] = []
        for idx, score in enumerate(raw):
            chunk_id = self._ids[idx]
            if allowed is not None and chunk_id not in allowed:
                continue
            # Clamp: float32 round-off puts a vector's similarity with itself at
            # 1.0000000000000002, and a cosine above 1 in a report reads as a bug.
            clamped = 1.0 if score > 1.0 else (-1.0 if score < -1.0 else score)
            scored.append((chunk_id, round(clamped, _ROUND)))
        scored.sort(key=lambda kv: (-kv[1], kv[0]))
        return scored[:k]

    def _scores_stdlib(self, query: array) -> list[float]:
        q = list(query)
        return [sum(a * b for a, b in zip(vec, q, strict=False)) for vec in self._vecs]

    # ----------------------------------------------------------- reporting

    def __len__(self) -> int:
        return len(self._ids)

    def __contains__(self, chunk_id: str) -> bool:
        return chunk_id in self._pos

    def get(self, chunk_id: str) -> array | None:
        idx = self._pos.get(chunk_id)
        return self._vecs[idx] if idx is not None else None

    @property
    def numpy_available(self) -> bool:
        return self._np is not None

    def stats(self) -> dict[str, Any]:
        return {
            "vectors": len(self._ids),
            "dim": self.dim,
            "numpy": self._use_numpy() is not None,
            "numpy_available": self._np is not None,
            "numpy_threshold": self._threshold,
            "rejected_dim": self.rejected_dim,
            "rejected_zero": self.rejected_zero,
        }

    def __repr__(self) -> str:
        return f"<VectorIndex n={len(self._ids)} dim={self.dim}>"
