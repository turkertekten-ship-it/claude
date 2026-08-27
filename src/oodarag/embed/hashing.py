"""A deterministic embedding model that is not a model.

The dense arm of a hybrid retriever normally needs a hosted API or a few
hundred megabytes of PyTorch. Both are unavailable here by design (ADR 0001)
and unavailable in practice whenever egress is blocked or a key expires. So the
default embedder is the hashing trick: feature-hash the text into a fixed number
of buckets, sign each feature so collisions cancel instead of accumulating,
scale term frequencies sublinearly, and L2-normalise.

What that buys and what it costs, stated plainly:

* It has no semantics. "car" and "automobile" are orthogonal here. It is a
  fast, lexical-ish vector arm, and the reason the pipeline fuses it with BM25
  and a reranker rather than trusting it alone.
* It is exactly reproducible. Same bytes, same vector, on any machine, in any
  process, forever - because every hash is blake2b and Python's salted builtin
  ``hash()`` is never used, and because features are accumulated in sorted order
  so even floating-point summation order is pinned. An index whose vectors
  shift between runs cannot be incrementally updated; this one can.
* It degrades gracefully on morphology and typos, because character 4-grams are
  hashed alongside whole words. That matters more than usual for this corpus:
  Turkish is agglutinative, so "fonun", "fonlar", "fonlarin" share a stem that
  no whole-word model sees, and n-grams recover most of it for free.

The tokenizer here is deliberately NOT ``util.text.tokenize``. That one is
ASCII-scoped by design (it targets code identifiers and keeps ``dotted.paths``
together), which means "İstanbul" tokenizes to "stanbul" and "şirket" to
"irket". Fine for a code index, silently destructive for Turkish, so this
module uses a Unicode-aware token pattern and the i-family fold from
``chunk.splitter``.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

from oodarag.chunk.splitter import fold
from oodarag.util.hashing import blake_bucket, blake_sign
from oodarag.util.logging import get_logger
from oodarag.util.text import char_ngrams

log = get_logger("embed")

try:  # optional accelerator; the pipeline must run identically without it
    import numpy as _np
except ImportError:  # pragma: no cover - exercised by whichever env lacks numpy
    _np = None

HAS_NUMPY = _np is not None

DEFAULT_DIM = 512
DEFAULT_NGRAM = 4
MIN_DIM = 8

#: Below this many features the numpy path is pure overhead, so it is not taken.
_NUMPY_MIN_FEATURES = 512

#: Set once the numpy accumulation has been checked against the stdlib loop in
#: this process. Module-level because the guarantee is about the library, not
#: about any one embedder instance.
_NUMPY_VERIFIED = False

# Unicode-aware, but shaped like the house tokenizer: dotted/dashed/slashed
# compounds stay together so `oodarag.embed.hashing` and `III-52` survive.
_WORD_RE = re.compile(r"\w+(?:[.\-/]\w+)*")


def l2_normalize(vec: Sequence[float]) -> list[float]:
    """Scale a vector to unit length. A zero (or non-finite) vector stays zero.

    Returning zeros rather than raising is the right failure mode: an empty
    chunk is a real thing that happens, and a zero vector has cosine 0 with
    everything, which is exactly the "matches nothing" semantics wanted. Norms
    use ``math.fsum`` so the result does not depend on summation order and the
    optional numpy path can be held to bit-identical output.
    """
    norm = math.sqrt(math.fsum(v * v for v in vec))
    if norm == 0.0 or not math.isfinite(norm):
        return [0.0] * len(vec)
    return [v / norm for v in vec]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity, clamped to [-1, 1].

    Raises on a dimension mismatch instead of returning 0.0. That mismatch means
    two different vector spaces have been mixed in one index - a hosted model
    swapped for the fallback, or ``dim`` changed between runs - and silently
    scoring it as "unrelated" would turn a configuration error into mysteriously
    bad retrieval that nobody can trace. Callers that can genuinely receive
    mixed dims (the cache, the index loader) filter on dim before they get here.
    """
    if len(a) != len(b):
        raise ValueError(f"cosine on mismatched dims: {len(a)} vs {len(b)}")
    na = math.sqrt(math.fsum(x * x for x in a))
    nb = math.sqrt(math.fsum(x * x for x in b))
    if na == 0.0 or nb == 0.0 or not (math.isfinite(na) and math.isfinite(nb)):
        return 0.0
    dot = math.fsum(x * y for x, y in zip(a, b, strict=True))
    return max(-1.0, min(1.0, dot / (na * nb)))


class HashingEmbedder:
    """Feature-hashing embedder. Stdlib only, deterministic, no training.

    ``word_weight`` and ``ngram_weight`` set how much of the vector is whole
    words versus character n-grams. The default leans on words and treats
    n-grams as a robustness layer: at equal weight the n-grams swamp the signal
    (a 10-character word contributes 11 n-grams and 1 word) and every long word
    starts to look like every other long word.
    """

    __slots__ = ("dim", "ngram", "word_weight", "ngram_weight", "salt", "max_tokens", "_numpy")

    def __init__(
        self,
        dim: int = DEFAULT_DIM,
        *,
        ngram: int = DEFAULT_NGRAM,
        word_weight: float = 1.0,
        ngram_weight: float = 0.45,
        salt: str = "",
        max_tokens: int = 8192,
        use_numpy: bool | None = None,
    ) -> None:
        requested = int(dim)
        self.dim = max(MIN_DIM, requested)
        if self.dim != requested:
            # Clamp rather than raise: this is usually a config file, and a
            # pipeline that refuses to start over a bad tuning knob is a
            # pipeline that stops being run.
            log.warn("embedding dim clamped", requested=requested, using=self.dim)
        self.ngram = max(2, int(ngram))
        self.word_weight = float(word_weight)
        self.ngram_weight = float(ngram_weight)
        self.salt = str(salt)
        self.max_tokens = max(1, int(max_tokens))
        self._numpy = HAS_NUMPY if use_numpy is None else bool(use_numpy and HAS_NUMPY)

    @property
    def name(self) -> str:
        """Identifies the vector space, not just the class.

        Two HashingEmbedders with different dims, n-gram sizes or salts produce
        incomparable vectors, so anything that persists a vector persists this
        string next to it.
        """
        tail = f"-{self.salt}" if self.salt else ""
        return f"hash-{self.dim}d-{self.ngram}g{tail}"

    @property
    def space(self) -> str:
        return self.name

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        counts = self._features(text or "")
        if not counts:
            return [0.0] * self.dim
        return l2_normalize(self._accumulate(counts))

    # ------------------------------------------------------------- internals

    def _features(self, text: str) -> dict[str, float]:
        """Raw feature counts, namespaced so a word can never collide with an n-gram.

        Truncation at ``max_tokens`` is deterministic (a prefix, not a sample):
        embedding a whole book into 512 buckets saturates them anyway, and the
        cap is what stops one pathological document from stalling a run.
        """
        counts: dict[str, float] = {}
        seen = 0
        for m in _WORD_RE.finditer(text):
            token = fold(m.group(0))
            if not token:
                continue
            seen += 1
            if seen > self.max_tokens:
                log.warn("embedding input truncated", tokens=self.max_tokens, chars=len(text))
                break
            key = "w:" + token
            counts[key] = counts.get(key, 0.0) + 1.0
            if self.ngram_weight:
                for gram in char_ngrams(token, self.ngram):
                    key = "g:" + gram
                    counts[key] = counts.get(key, 0.0) + 1.0
        return counts

    def _weight(self, feature: str, count: float) -> float:
        """Sublinear tf: the tenth occurrence of a word says far less than the first."""
        base = self.word_weight if feature[0] == "w" else self.ngram_weight
        return base * (1.0 + math.log(count))

    def _accumulate(self, counts: dict[str, float]) -> list[float]:
        # Sorted, not insertion-ordered: dict order is already deterministic for
        # identical input, but sorting removes the dependency entirely, so a
        # future change to feature extraction order cannot silently move every
        # vector by an ulp and invalidate a persisted index.
        features = sorted(counts)
        if self._numpy and len(features) >= _NUMPY_MIN_FEATURES:
            vec = self._accumulate_numpy(features, counts)
            if vec is not None:
                return vec
        vec = [0.0] * self.dim
        for feature in features:
            idx = blake_bucket(feature, self.dim, self.salt)
            vec[idx] += blake_sign(feature) * self._weight(feature, counts[feature])
        return vec

    def _accumulate_numpy(
        self, features: list[str], counts: dict[str, float]
    ) -> list[float] | None:
        """The optional accelerated path, held to bit-identical output.

        ``np.add.at`` is unbuffered and applies its updates in index order, so it
        reproduces the Python loop's floating-point summation exactly. That is an
        assumption about a third-party library, and an assumption that is wrong
        by one ulp still poisons an index built half on one machine and half on
        another - so the first use in each process verifies it against the
        stdlib path and disables numpy permanently if it disagrees. Cheap
        insurance: one extra computation per process.
        """
        if _np is None:  # pragma: no cover - guarded by caller
            return None
        try:
            idx = _np.fromiter(
                (blake_bucket(f, self.dim, self.salt) for f in features),
                dtype=_np.int64,
                count=len(features),
            )
            val = _np.fromiter(
                (blake_sign(f) * self._weight(f, counts[f]) for f in features),
                dtype=_np.float64,
                count=len(features),
            )
            arr = _np.zeros(self.dim, dtype=_np.float64)
            _np.add.at(arr, idx, val)
            vec: list[float] = arr.tolist()
        except Exception as e:  # numpy present but unhappy: never fatal
            log.warn("numpy embedding path failed, using stdlib", err=str(e)[:160])
            self._numpy = False
            return None
        global _NUMPY_VERIFIED
        if not _NUMPY_VERIFIED:
            reference = [0.0] * self.dim
            for feature in features:
                reference[blake_bucket(feature, self.dim, self.salt)] += (
                    blake_sign(feature) * self._weight(feature, counts[feature])
                )
            if reference != vec:
                log.error("numpy path diverged from stdlib, disabling it")
                self._numpy = False
                return None
            _NUMPY_VERIFIED = True
        return vec

