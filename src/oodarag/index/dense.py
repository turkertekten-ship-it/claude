"""Exhaustive dense retrieval: one dot product per chunk, and why that is enough.

Vectors arrive L2-normalized - `embed/base.py` normalizes at the source and the
store persists them that way - so cosine similarity is already just a dot
product. Recomputing norms per query per chunk would be work whose answer is
known to be 1.0. The invariant is deliberately trusted rather than re-enforced
here: renormalizing on `add` would hide the one bug worth catching, an embedder
wired in that does not normalize, whose symptom is scores wandering outside
[-1, 1] instead of a ranking that is quietly wrong.

An approximate-nearest-neighbour index (faiss, hnswlib, annoy) was rejected
twice over. It is a compiled third-party dependency, which the project does not
take. And it is *approximate*: at the scale this pipeline targets - tens of
thousands of chunks - a brute-force scan is a few hundred million float
multiplies, which numpy does in milliseconds and pure Python does in well under
a second, so ANN would trade the one thing that matters (never missing the
single chunk that answers the question) for a speedup nobody would notice. ANN
earns its keep in the millions; below that it is a recall regression with a
benchmark attached.

The numpy path is one matmul against a matrix built once and cached until the
next `add`. It exists for the largest corpora and must agree with the stdlib
path exactly, so three things are pinned: both paths produce scores through the
*same* ranking code, the matrix is float64 rather than float32 (halving the
memory would also change the arithmetic, and identical results are worth more
here than the bytes), and ties are broken by `chunk_id`. That last one is not
theoretical - duplicate boilerplate embeds to bit-identical vectors, so exact
ties are routine, and without a total order the top-k would depend on which
path ran, i.e. on whether the machine happened to have numpy installed.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from operator import mul
from typing import Any

from oodarag.util.logging import get_logger

log = get_logger("dense")

try:  # optional, via `pip install oodarag[fast]`
    import numpy as _np
except ImportError:  # the stdlib path below is the reference implementation
    _np = None  # type: ignore[assignment]

#: Escape hatch so the test suite can prove the two paths agree on a machine
#: that has numpy, and so a numpy build that misbehaves can be sidestepped
#: without uninstalling it.
_FORCE_STDLIB = os.environ.get("OODARAG_NO_NUMPY", "") not in ("", "0")


class DenseIndex:
    """In-memory exhaustive vector index over L2-normalized embeddings."""

    def __init__(self, dim: int) -> None:
        if dim <= 0:
            raise ValueError(f"dense index dim must be positive, got {dim}")
        self.dim = dim
        #: Vectors refused during `build` (dimension mismatch), counted so a
        #: rebuild reports the damage instead of dying on the first bad row.
        self.rejected = 0
        #: Repeat `chunk_id`s ignored (see `add`).
        self.skipped_duplicate = 0
        self._ids: list[str] = []
        self._vectors: list[list[float]] = []
        self._positions: dict[str, int] = {}
        self._matrix: Any = None

    def __len__(self) -> int:
        return len(self._ids)

    @property
    def backend(self) -> str:
        return "numpy" if _np is not None and not _FORCE_STDLIB else "stdlib"

    def add(self, chunk_id: str, vector: Sequence[float]) -> None:
        """Add one vector under `chunk_id`.

        A dimension mismatch raises: it means two embedders got crossed, and
        every score computed afterwards would be arithmetic on unrelated
        coordinate systems - a bug no ranking would ever look wrong enough to
        reveal. A repeat `chunk_id` is ignored and counted instead, because the
        damage there is bounded and known: the same chunk would otherwise be
        returned twice and counted twice by rank fusion downstream.
        """
        if len(vector) != self.dim:
            raise ValueError(
                f"dense index dimension mismatch for {chunk_id}: "
                f"index dim {self.dim} != vector dim {len(vector)}"
            )
        if chunk_id in self._positions:
            self.skipped_duplicate += 1
            log.debug("duplicate chunk_id ignored", chunk_id=chunk_id)
            return
        self._positions[chunk_id] = len(self._ids)
        self._ids.append(chunk_id)
        self._vectors.append([float(v) for v in vector])
        self._matrix = None  # cached matrix no longer covers every row

    def build(self, pairs: Iterable[tuple[str, Sequence[float]]]) -> DenseIndex:
        """Replace the index contents with `pairs`. Returns self.

        A vector left over from a superseded embedder has the wrong width and
        must not abort a rebuild of the other forty thousand; those are counted
        into `rejected` and reported once at the end.
        """
        self._reset()
        for chunk_id, vector in pairs:
            try:
                self.add(chunk_id, vector)
            except ValueError as e:
                self.rejected += 1
                if self.rejected <= 3:  # one line per corpus, not per row
                    log.warn("vector rejected", chunk_id=chunk_id, err=str(e))
        if self.rejected:
            log.warn("dense build rejected vectors", count=self.rejected, dim=self.dim)
        log.info(
            "dense built",
            vectors=len(self._ids),
            dim=self.dim,
            backend=self.backend,
            duplicates=self.skipped_duplicate,
        )
        return self

    def search(self, vector: Sequence[float], k: int = 20) -> list[tuple[str, float]]:
        """Top-`k` `(chunk_id, similarity)` pairs, highest similarity first.

        An empty index and a non-positive `k` return `[]`. A query vector of the
        wrong width raises, for the same reason `add` does: it is a wiring bug
        that no score could ever expose. The width is checked before the
        emptiness test on purpose, so an index that happens to be empty does not
        swallow the mismatch and let it surface a thousand chunks later.
        """
        if len(vector) != self.dim:
            raise ValueError(
                f"dense query dimension mismatch: index dim {self.dim} != vector dim {len(vector)}"
            )
        if k <= 0 or not self._ids:
            return []

        query = [float(v) for v in vector]
        scores = self._score_numpy(query) if self.backend == "numpy" else self._score_stdlib(query)
        # Both paths land here: the ranking is written once so the two cannot
        # drift apart. Ties break on chunk_id ascending, which is what makes the
        # numpy and stdlib results identical for the identical vectors that
        # duplicated content produces.
        ranked = sorted(
            zip(self._ids, scores, strict=True),
            key=lambda pair: (-pair[1], pair[0]),
        )
        return ranked[:k]

    def _score_stdlib(self, query: list[float]) -> list[float]:
        # map + operator.mul rather than a generator expression with a zip: the
        # inner loop runs dim times per chunk, and this keeps it in C.
        return [sum(map(mul, vec, query)) for vec in self._vectors]

    def _score_numpy(self, query: list[float]) -> list[float]:
        if self._matrix is None:
            # Built once and reused across queries; `add` drops it. float64
            # matches the Python floats the stdlib path works in, so the two
            # differ only in summation order, never in precision.
            self._matrix = _np.asarray(self._vectors, dtype=_np.float64)
        return self._matrix.dot(_np.asarray(query, dtype=_np.float64)).tolist()

    def _reset(self) -> None:
        self._ids = []
        self._vectors = []
        self._positions = {}
        self._matrix = None
        self.rejected = 0
        self.skipped_duplicate = 0

    def __repr__(self) -> str:
        return f"DenseIndex(vectors={len(self._ids)}, dim={self.dim}, backend={self.backend})"
