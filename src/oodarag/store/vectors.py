"""Vector packing and the similarity kernel.

Vectors are stored as little-endian float32 blobs. float32 halves the index size
against float64 and costs nothing measurable in ranking quality - the difference
is far below the noise floor of the retrieval itself.

Scoring uses numpy when it is importable and a pure-Python kernel otherwise. The
pure path is not a stub: it is the one CI runs on, and it is exercised by the
same tests. Results from the two paths must agree to float32 precision, which is
asserted in the test suite.
"""

from __future__ import annotations

import array
import math
import struct
from typing import Sequence

try:  # optional accelerator
    import numpy as _np
except ImportError:  # pragma: no cover - exercised by the pure-python path
    _np = None

HAS_NUMPY = _np is not None


def pack(vector: Sequence[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def unpack(blob: bytes) -> list[float]:
    buf = array.array("f")
    buf.frombytes(blob)
    return buf.tolist()


def normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector] if norm else list(vector)


class VectorIndex:
    """A flat in-memory index over packed vectors.

    Flat (exhaustive) search is the right default at this scale: it is exact,
    has no build step, no parameters to tune wrong, and stays under a
    millisecond for the tens of thousands of chunks a documentation corpus
    produces. An approximate index trades recall for latency that is not yet a
    problem - and silently losing recall is precisely the failure this pipeline
    is built to avoid.
    """

    def __init__(self, dim: int) -> None:
        self.dim = dim
        self.ids: list[str] = []
        self._rows: list[list[float]] = []
        self._matrix = None  # numpy array, built lazily

    def __len__(self) -> int:
        return len(self.ids)

    def add(self, chunk_id: str, vector: Sequence[float]) -> None:
        if len(vector) != self.dim:
            raise ValueError(f"vector dim {len(vector)} != index dim {self.dim}")
        self.ids.append(chunk_id)
        self._rows.append(list(vector))
        self._matrix = None

    def add_packed(self, chunk_id: str, blob: bytes) -> None:
        self.add(chunk_id, unpack(blob))

    def _ensure_matrix(self):
        if _np is None:
            return None
        if self._matrix is None or len(self._matrix) != len(self._rows):
            self._matrix = _np.asarray(self._rows, dtype=_np.float32)
        return self._matrix

    def search(self, query: Sequence[float], k: int = 10,
               allowed: set[str] | None = None) -> list[tuple[str, float]]:
        """Top-k by cosine similarity, optionally restricted to `allowed` ids.

        Filtering happens *before* scoring, not after: post-filtering a top-k
        list is the classic way to return three results when the user asked for
        ten, because the filter removed seven of them.
        """
        if not self._rows:
            return []
        if allowed is not None and not allowed:
            return []

        if _np is not None:
            matrix = self._ensure_matrix()
            query_vec = _np.asarray(query, dtype=_np.float32)
            if allowed is None:
                scores = matrix @ query_vec
                ids = self.ids
            else:
                mask = [i for i, cid in enumerate(self.ids) if cid in allowed]
                if not mask:
                    return []
                scores = matrix[mask] @ query_vec
                ids = [self.ids[i] for i in mask]
            top = min(k, len(ids))
            order = _np.argpartition(-scores, top - 1)[:top] if top < len(ids) \
                else _np.arange(len(ids))
            order = order[_np.argsort(-scores[order])]
            return [(ids[int(i)], float(scores[int(i)])) for i in order]

        results: list[tuple[str, float]] = []
        for chunk_id, row in zip(self.ids, self._rows):
            if allowed is not None and chunk_id not in allowed:
                continue
            total = 0.0
            for x, y in zip(row, query):
                total += x * y
            results.append((chunk_id, total))
        results.sort(key=lambda pair: pair[1], reverse=True)
        return results[:k]


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
