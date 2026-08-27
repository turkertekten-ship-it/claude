"""Deterministic embeddings with no model, no service and no dependencies.

The pipeline promises to run with zero required dependencies, which rules out
both a hosted embedding API and numpy. What remains is the hashing trick: map
every token to a fixed bucket with a deterministic sign, sum, and normalize.

This is genuinely weaker than a learned model — it captures term overlap and
some morphology, not meaning; `car` and `automobile` stay far apart. It is used
here because the *dense arm of a hybrid retriever* does not have to be good on
its own to be useful: fused with BM25, it recovers paraphrase-by-shared-subword
and it never returns nothing. Where a real embedding model is available, it
plugs in behind `Embedder` and the rest of the pipeline does not change.

Signed buckets matter: without the sign, hash collisions accumulate and every
vector drifts towards the same dense blob. With a sign drawn from the same
digest, collisions cancel rather than accumulate and the expected value of any
output column is zero — the property that makes the trick usable at a few
hundred dimensions at all. This is the signed variant of feature hashing
(Weinberger, Dasgupta, Langford, Smola & Attenberg, ICML 2009), which is also
what scikit-learn's `FeatureHasher` does by default.

Hashing is `blake2b` from `hashlib`, never the builtin `hash()`: string hashing
in CPython is salted per process, so an index built in one run would not match
a query vector computed in the next.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from oodarag.util.hashing import blake_bucket, blake_sign
from oodarag.util.text import char_ngrams, tokenize

Vector = list[float]


class Embedder(Protocol):
    """Anything that turns text into a fixed-width vector."""

    dim: int

    def embed(self, text: str) -> Vector: ...
    def embed_batch(self, texts: list[str]) -> list[Vector]: ...


@dataclass
class HashingEmbedder:
    """Signed hashing-trick embeddings over words and character n-grams.

    `dim` at 512 is a power of two on purpose: bucketing is a plain modulo, so
    a non-power-of-two spreads tokens unevenly across the columns.

    512 is also where the Johnson-Lindenstrauss bound points for this corpus
    size. The bound gives the dimension needed to preserve pairwise distances
    within 1 +- eps as `D >= 4 ln(n) / (eps^2/2 - eps^3/3)`, and it depends on
    the number of *documents*, not the vocabulary. For a few thousand chunks at
    a tolerable eps = 0.3 that is roughly 800; at eps = 0.5, roughly 400. The
    bound is explicitly conservative, so 512 sits sensibly between the two.
    Raising it costs scoring time linearly.

    `ngram_weight` below 1 reflects that a subword match is real evidence but
    weaker than a whole-word match; it is what lets `retrieval` and `retriever`
    land near each other without letting `ret` dominate.
    """

    dim: int = 512
    use_ngrams: bool = True
    ngram_size: int = 4
    ngram_weight: float = 0.35
    sublinear_tf: bool = True

    def embed(self, text: str) -> Vector:
        vec = [0.0] * self.dim
        tokens = tokenize(text)
        if not tokens:
            return vec

        counts: dict[str, int] = {}
        for tok in tokens:
            counts[tok] = counts.get(tok, 0) + 1

        for token, count in counts.items():
            # Sublinear scaling: the tenth occurrence of a word says much less
            # than the second, and without damping one repeated term can define
            # the whole vector.
            weight = (1.0 + math.log(count)) if self.sublinear_tf else float(count)
            vec[blake_bucket(token, self.dim)] += weight * blake_sign(token)

            if self.use_ngrams and len(token) > self.ngram_size:
                sub = self.ngram_weight * weight
                for gram in char_ngrams(token, self.ngram_size):
                    vec[blake_bucket(gram, self.dim, salt="n")] += sub * blake_sign(gram, salt="n")

        return l2_normalize(vec)

    def embed_batch(self, texts: list[str]) -> list[Vector]:
        return [self.embed(t) for t in texts]


def l2_normalize(vec: Vector) -> Vector:
    """Normalize in place-ish, so cosine similarity is a plain dot product."""
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


def cosine(a: Vector, b: Vector) -> float:
    """Cosine similarity. Assumes normalized input; falls back when it is not."""
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    if abs(na - 1.0) < 1e-6 and abs(nb - 1.0) < 1e-6:
        return dot(a, b)
    return dot(a, b) / (na * nb)


def pack(vec: Vector) -> bytes:
    """Serialize for SQLite storage as float32, halving the row size."""
    import struct

    return struct.pack(f"<{len(vec)}f", *vec)


def unpack(blob: bytes) -> Vector:
    import struct

    return list(struct.unpack(f"<{len(blob) // 4}f", blob))
