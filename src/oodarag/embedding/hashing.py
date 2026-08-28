"""A deterministic, dependency-free embedder.

This is a signed feature-hashing (hashing trick) projection of a BM25-weighted
sparse vector into a dense space:

    tokens + character n-grams
      -> sublinear term frequency, weighted by inverse document frequency
      -> hashed into `dim` buckets with a per-feature sign
      -> L2 normalised

It is not a learned model and it will not match a good neural embedder on
paraphrase. What it does give, which matters more for the *pipeline*, is:

* **no network, no key, no download** - CI, air-gapped containers and laptops
  all behave identically;
* **exact determinism** - the same text produces the same vector on every
  machine forever, so eval numbers are comparable across runs and a retrieval
  regression is a real regression rather than model drift;
* **honest baseline** - swapping in a hosted embedder must *beat* this on the
  eval harness to justify its cost and its dependency.

Two design details do most of the work:

*Signed hashing.* Each feature gets a deterministic +1/-1 sign, so collisions
cancel in expectation instead of accumulating into a systematic bias. In
expectation - the variance still grows with load, and the load is high: the
153-document external corpus has 126,791 distinct features (tokens plus 4-grams)
in 768 buckets, so **165 features per bucket** and not one bucket empty. That
reads like an obvious ceiling and is not one. Swept 256 -> 6144, a 24x change in
crowding, gate pass rate goes 48, 49, 48, 48, 49 and the held-out set sits at
19/22 for every value: non-monotone and one case wide, which is noise rather
than a trend (L72). 6144 costs 50% more index time and 8x the vector storage to
buy it. The default stays at 768, and the honest reason is that dimension is not
a lever here - not that 768 was found optimal, since every other retrieval
parameter was tuned at it. `scripts/embed_dim_sweep.py`.

*Character n-grams.* Subword features give robustness to morphology and typos
("chunking" near "chunked") without a learned vocabulary, and they are what
keep code identifiers retrievable.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

from oodarag.embedding.base import Embedder, Vector
from oodarag.util.hashing import blake_bucket, blake_sign
from oodarag.util.text import char_ngrams, tokenize

_NGRAM_WEIGHT = 0.35  # subword features support word features, they do not replace them


class HashingEmbedder(Embedder):
    name = "hashing"

    def __init__(self, dim: int = 768, ngram_size: int = 4, use_ngrams: bool = True) -> None:
        self.dim = dim
        self.ngram_size = ngram_size
        self.use_ngrams = use_ngrams
        self._df: Counter[str] = Counter()
        self._docs = 0

    # ------------------------------------------------------------------ fitting

    def fit(self, corpus: Sequence[str]) -> None:
        """Learn document frequencies.

        Without this every term is weighted equally and the vector is dominated
        by whatever words are most common in the corpus - which is to say, by
        the words that carry the least information.
        """
        self._df = Counter()
        self._docs = 0
        for text in corpus:
            self._docs += 1
            for token in set(tokenize(text)):
                self._df[token] += 1

    @property
    def fitted(self) -> bool:
        return self._docs > 0

    def _idf(self, token: str) -> float:
        if not self._docs:
            return 1.0
        df = self._df.get(token, 0)
        # BM25 IDF, floored: a term in every document contributes nothing, but
        # never goes negative and flips the sign of a legitimate match.
        return max(0.05, math.log(1.0 + (self._docs - df + 0.5) / (df + 0.5)))

    # ---------------------------------------------------------------- embedding

    def _vector(self, text: str) -> Vector:
        tokens = tokenize(text)
        if not tokens:
            return [0.0] * self.dim
        counts = Counter(tokens)
        vector = [0.0] * self.dim

        for token, count in counts.items():
            weight = (1.0 + math.log(count)) * self._idf(token)
            index = blake_bucket(token, self.dim, salt="w")
            vector[index] += weight * blake_sign(token, salt="w")
            if not self.use_ngrams:
                continue
            ngram_weight = weight * _NGRAM_WEIGHT
            for gram in char_ngrams(token, self.ngram_size):
                gram_index = blake_bucket(gram, self.dim, salt="g")
                vector[gram_index] += ngram_weight * blake_sign(gram, salt="g")

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0.0:
            return vector
        return [v / norm for v in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> Vector:
        return self._vector(text)

    # ------------------------------------------------------------------- state

    @property
    def fingerprint(self) -> str:
        # Corpus statistics change the vector space, so they are part of its
        # identity: an index built before a refit is not comparable to one built
        # after, and must be detected rather than silently mixed.
        return f"{self.name}:{self.dim}:n{self.ngram_size if self.use_ngrams else 0}:d{self._docs}"

    def state(self) -> dict:
        return {
            "dim": self.dim,
            "ngram_size": self.ngram_size,
            "use_ngrams": self.use_ngrams,
            "docs": self._docs,
            # Only terms seen more than once: singletons are half the vocabulary
            # and contribute a near-constant IDF.
            "df": {t: c for t, c in self._df.items() if c > 1},
        }

    def load_state(self, state: dict) -> None:
        self.dim = state.get("dim", self.dim)
        self.ngram_size = state.get("ngram_size", self.ngram_size)
        self.use_ngrams = state.get("use_ngrams", self.use_ngrams)
        self._docs = state.get("docs", 0)
        self._df = Counter(state.get("df", {}))


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity. Vectors from this embedder are already normalised, so
    this reduces to a dot product - but never assume that of a foreign vector."""
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / math.sqrt(norm_a * norm_b)
