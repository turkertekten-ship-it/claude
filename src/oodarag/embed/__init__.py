"""Embedding: the seam where a hosted model replaces the built-in one.

`HashingEmbedder` is the zero-dependency default; anything matching the
`Embedder` protocol can take its place without touching another stage.
"""

from __future__ import annotations

from oodarag.embed.base import Embedder, EmbeddingCache, cosine, l2_normalize
from oodarag.embed.hashing import HashingEmbedder

__all__ = ["Embedder", "EmbeddingCache", "HashingEmbedder", "cosine", "l2_normalize"]
