"""The embedding seam: one protocol, the vector math behind it, and a cache.

`Embedder` is a `Protocol` rather than a base class because the implementations
that matter share no code: the built-in `HashingEmbedder` computes vectors in
this process, a hosted model would batch them over HTTP with retries and a
token budget. Structural typing means a provider satisfies the contract without
importing anything from here, so the zero-dependency core never grows a
dependency just to declare a subclass. Everything downstream depends on the
shape `(name, dim, embed, embed_one)` and nothing else - that is the seam.

Vectors are L2-normalized *at the source* rather than at comparison time. Two
reasons: cosine then collapses to a dot product, which is what makes the
exhaustive scan in `index/dense.py` affordable without an ANN library, and a
normalized vector is what gets written to the store, so the norm is paid once
per chunk at index time instead of once per chunk per query.

`EmbeddingCache` is keyed by `(model name, content hash)`, never by chunk id.
Chunk ids move when a document is re-chunked with different settings, but the
text either changed or it did not; keying on content also means the boilerplate
footer repeated across 400 pages is embedded once. The model name is part of
the key because vectors from two embedders are not comparable - mixing them
silently would produce a ranking that looks fine and is nonsense.

A cache is an optimization, so every failure mode here degrades instead of
raising: an unreadable or truncated cache file becomes an empty cache, a single
corrupt entry becomes a single recompute, and a failed write leaves the process
running with an in-memory cache. Refusing to index because a derived file went
bad would be strictly worse than recomputing it.
"""

from __future__ import annotations

import base64
import json
import math
import os
import tempfile
from array import array
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from oodarag.util.logging import get_logger

log = get_logger("embed")

#: Bumped when the on-disk cache layout changes. An unrecognised version is
#: treated as an empty cache, which costs a re-embed and never a crash.
CACHE_SCHEMA = 1


class Embedder(Protocol):
    """Anything that turns text into fixed-width, L2-normalized vectors.

    `name` must change whenever the vectors change - it keys the cache and, in
    a persisted index, it is the only record of what produced the numbers.
    """

    name: str
    dim: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Vectors for `texts`, positionally aligned with the input."""
        ...

    def embed_one(self, text: str) -> list[float]: ...


def l2_normalize(vec: list[float]) -> list[float]:
    """Scale `vec` to unit length, returning a new list."""
    total = 0.0
    for v in vec:
        total += v * v
    # A zero vector is a legitimate embedding (a chunk of pure stopwords, an
    # empty string); scaling it is undefined, so hand back zeros rather than
    # letting NaNs propagate into every score the vector touches.
    if total <= 0.0 or not math.isfinite(total):
        return [0.0] * len(vec)
    norm = math.sqrt(total)
    return [v / norm for v in vec]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity in [-1, 1]; 0.0 if either vector is all zeros.

    Norms are recomputed rather than assumed, so this stays correct for the
    callers that pass raw vectors (a reranker mixing in a hand-built profile
    vector, a test). The dot-product-only fast path belongs in `index/dense.py`,
    where the vectors are known to be normalized because the store wrote them.
    """
    if len(a) != len(b):
        # A dimension mismatch means two embedders got crossed, which no score
        # would reveal - a silent 0.0 here would hide the wiring bug for weeks.
        raise ValueError(f"cosine dimension mismatch: {len(a)} != {len(b)}")
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    # Clamped because float error can hand back 1.0000000000000002, and callers
    # that take an arccos or treat `1 - cos` as a distance break on it.
    return max(-1.0, min(1.0, dot / math.sqrt(norm_a * norm_b)))


class EmbeddingCache:
    """Content-hash keyed, so re-indexing an unchanged corpus costs no compute.

    Persists as one JSON file whose payloads are base64 of `array("f")` bytes -
    the same float32 encoding `index/store.py` uses for vectors. JSON lists of
    floats were rejected: they are roughly four times the size, parse an order
    of magnitude slower, and the round-trip through float32 is happening at the
    store boundary anyway, so keeping it here costs nothing that was not already
    spent.

    Writes are batched: `put` only touches memory and `flush` does one atomic
    replace. Flushing per `put` would rewrite the whole file O(n) times over an
    ingest. **The caller owns `flush()`** - a process that exits without calling
    it loses the run's new entries but never corrupts the ones already on disk.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        # {model: {content_hash: base64-of-float32}} - nested rather than a
        # joined key so a stale model's entries can be dropped in one delete.
        self._models: dict[str, dict[str, str]] = {}
        self._dirty = False
        self._hits = 0
        self._misses = 0
        if self.path is not None:
            self._load()

    def get(self, model: str, content_hash: str) -> list[float] | None:
        blob = self._models.get(model, {}).get(content_hash)
        if blob is None:
            self._misses += 1
            return None
        try:
            buf = array("f")
            buf.frombytes(base64.b64decode(blob, validate=True))
        except (ValueError, TypeError):
            # One truncated entry costs one recompute; it must not take the
            # other 40,000 with it. Drop it so the next flush cleans the file.
            self._models[model].pop(content_hash, None)
            self._dirty = True
            self._misses += 1
            return None
        self._hits += 1
        return buf.tolist()

    def put(self, model: str, content_hash: str, vec: list[float]) -> None:
        encoded = base64.b64encode(array("f", vec).tobytes()).decode("ascii")
        self._models.setdefault(model, {})[content_hash] = encoded
        self._dirty = True

    def flush(self) -> None:
        """Write the cache atomically. A failed write degrades to memory-only."""
        if self.path is None or not self._dirty:
            return
        payload = {"schema": CACHE_SCHEMA, "models": self._models}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh)
                os.replace(tmp, self.path)  # atomic: readers see old or new
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
        except OSError as e:
            log.warn("embedding cache flush failed", path=str(self.path), err=str(e)[:200])
            return
        self._dirty = False
        log.debug(
            "embedding cache flushed",
            path=str(self.path), entries=len(self), hits=self._hits, misses=self._misses,
        )

    def __len__(self) -> int:
        return sum(len(entries) for entries in self._models.values())

    def _load(self) -> None:
        assert self.path is not None
        try:
            raw = json.loads(self.path.read_text("utf-8"))
        except FileNotFoundError:
            return  # a cold cache is the normal first run, not a problem
        except (OSError, ValueError) as e:
            log.warn("embedding cache unreadable, starting empty", path=str(self.path), err=str(e)[:200])
            return
        if not isinstance(raw, dict) or raw.get("schema") != CACHE_SCHEMA:
            log.warn("embedding cache schema unrecognised, starting empty", path=str(self.path))
            return
        models = raw.get("models")
        if not isinstance(models, dict):
            return
        for model, entries in models.items():
            if isinstance(entries, dict):
                self._models[str(model)] = {
                    str(k): v for k, v in entries.items() if isinstance(v, str)
                }
