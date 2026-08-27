"""A signed hashing-trick embedder: lexical semantics at zero install cost.

Be clear about what this is. It is a deterministic projection of a weighted
bag of lexical features into a fixed-width vector - a strong baseline that
retrieves well on technical corpora, ships in the standard library, needs no
model download, no GPU, and no network. It is **not** a transformer: it has no
idea that "car" and "automobile" mean the same thing, and it never will. What
it does capture is exact term overlap, subword overlap, and term frequency,
which is most of what a hybrid retriever's dense arm contributes on a corpus of
docs and code. When a hosted model is worth its latency, it plugs in at the
`Embedder` protocol in `base.py` and nothing else in the pipeline changes.

**Why signed.** The plain hashing trick maps every feature to a bucket and adds
its weight. Collisions are then always constructive: two unrelated features
sharing a bucket inflate it, and with 512 buckets over a corpus vocabulary that
inflation is not rare noise, it is a systematic upward bias concentrated in
whichever buckets happen to be crowded. Multiplying each feature by a
deterministic +/-1 sign (`util.hashing.blake_sign`) makes the collision error
zero-mean: colliding features cancel as often as they reinforce, so the
expected dot product between two documents is the true feature-space dot
product plus noise, rather than the true value plus a bias. That is the whole
reason the sign exists, and it is why `dim` can stay small.

**Features.** Sublinear term frequency (`1 + log(tf)`) over `util.text.tokenize`
at weight 1.0, plus `util.text.char_ngrams` of each token at
`NGRAM_WEIGHT`. The n-grams are what put "chunking" and "chunked" near each
other without a learned model - they share `^chu`, `chun` and `hunk`. There is
deliberately no IDF: an embedder must be able to vectorise a query before the
corpus exists, and the lexical arm (`index/bm25.py`) already carries the corpus
statistics. Sublinear TF because a word repeated forty times in a chunk is not
forty times more about that word.

**Determinism is a hard requirement**, not a nice-to-have: vectors written to
the index by one process are compared against query vectors computed by
another, and a rebuild must reproduce the old numbers exactly or the index
silently rots. Every bucket and sign therefore comes from blake2b via
`util.hashing`. Python's builtin `hash()` is salted per process
(`PYTHONHASHSEED`) and would make the same text embed differently in two runs -
it must never appear here.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from oodarag.embed.base import EmbeddingCache, l2_normalize
from oodarag.util.hashing import blake_bucket, blake_sign, content_hash
from oodarag.util.logging import get_logger
from oodarag.util.text import char_ngrams, tokenize

log = get_logger("embed")

DEFAULT_SALT = "oodarag"

#: Weight of one n-gram relative to one whole token. High enough that a
#: morphological variant scores well clear of an unrelated chunk, low enough
#: that chunks sharing only prefixes never outrank chunks sharing real terms:
#: an exact term match still scores several times a subword-only match.
NGRAM_WEIGHT = 0.35


class HashingEmbedder:
    """Signed-hashing-trick embedder: deterministic, dependency-free, no model download."""

    def __init__(
        self,
        dim: int = 512,
        *,
        ngram: int = 4,
        use_ngrams: bool = True,
        salt: str = DEFAULT_SALT,
        cache: EmbeddingCache | None = None,
    ) -> None:
        if dim < 8:
            raise ValueError(f"dim must be at least 8, got {dim}")
        if ngram < 2:
            raise ValueError(f"ngram must be at least 2, got {ngram}")
        self.dim = dim
        self.ngram = ngram
        self.use_ngrams = use_ngrams
        self.salt = salt
        self.cache = cache
        #: Distinct from the bucket salt so the two draws stay independent even
        #: if blake2b's digest_size ever stops separating them for us.
        self._sign_salt = f"{salt}:sign"
        #: Texts that failed to vectorise this run. Counted, never raised.
        self.failed = 0
        self.name = self._build_name()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Vectors for `texts`, always positionally aligned with the input.

        Alignment is the contract that matters: callers zip the result against
        chunk ids, so a text that fails to vectorise yields a zero vector (which
        scores 0.0 against everything and simply never retrieves) instead of a
        shorter list that would silently attach every subsequent vector to the
        wrong chunk.
        """
        out: list[list[float]] = []
        for text in texts:
            digest = content_hash(text) if self.cache is not None else ""
            if self.cache is not None:
                hit = self.cache.get(self.name, digest)
                # The dim check is belt and braces: `name` encodes dim, so a
                # mismatch means a hand-edited cache file, not a config change.
                if hit is not None and len(hit) == self.dim:
                    out.append(hit)
                    continue
            try:
                vec = self._vector(text)
            except Exception as e:
                self.failed += 1
                log.warn("embedding failed, using zero vector", err=f"{type(e).__name__}: {e}"[:200])
                out.append([0.0] * self.dim)
                continue  # a failure is never cached - the next run retries it
            if self.cache is not None:
                self.cache.put(self.name, digest, vec)
            out.append(vec)
        return out

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        counts = Counter(tokenize(text))
        for token, tf in counts.items():
            weight = 1.0 + math.log(tf)  # sublinear: tf=1 -> 1.0, tf=40 -> 4.7
            self._accumulate(vec, token, weight)
            if not self.use_ngrams:
                continue
            # Every n-gram carries the same weight, deliberately. Scaling a
            # token's n-grams by 1/sqrt(k) to stop a 40-character dotted path
            # outweighing 37 real words was tried and rejected: it shrinks the
            # subword arm to a third of the collision noise floor, and
            # "how does chunking work" then scores 0.028 against a chunk about
            # chunkers and 0.026 against one about photosynthesis - i.e. the
            # arm stops working at all. Flat weighting gives 0.129 vs 0.036.
            # Long tokens do get more mass, but only as sqrt(k), because their
            # n-grams land in k different buckets.
            share = NGRAM_WEIGHT * weight
            for gram in char_ngrams(token, self.ngram):
                # Namespaced: an interior n-gram like "hunk" is a different
                # feature from the word "hunk", and conflating them would let a
                # short word absorb an unrelated word's subword mass.
                self._accumulate(vec, f"#{gram}", share)
        # Zero vectors survive normalization as zeros, which is the right answer
        # for a chunk that tokenizes to nothing.
        return l2_normalize(vec)

    def _accumulate(self, vec: list[float], feature: str, weight: float) -> None:
        bucket = blake_bucket(feature, self.dim, self.salt)
        vec[bucket] += blake_sign(feature, self._sign_salt) * weight

    def _build_name(self) -> str:
        """Identity of the vectors this instance produces - it keys the cache.

        Every constructor argument that changes a vector has to show up here,
        or a cache written with one configuration is served to another.
        """
        parts = [f"hash-{self.dim}", f"n{self.ngram}" if self.use_ngrams else "plain"]
        if self.salt != DEFAULT_SALT:
            parts.append("s" + content_hash(self.salt)[:6])
        return "-".join(parts)
