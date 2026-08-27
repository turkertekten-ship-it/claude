"""Embedding: text to vector, with a floor under it.

The contract every stage downstream relies on is that :func:`get_embedder`
always returns something that embeds. A missing key, a blocked egress, or a
provider outage downgrades the vector space; it never stops the pipeline and it
never raises into a caller that only wanted to index a document.
"""

from oodarag.embed.hashing import HashingEmbedder, cosine, l2_normalize
from oodarag.embed.provider import Embedder, EmbeddingCache, HostedEmbedder, get_embedder

__all__ = [
    "Embedder",
    "EmbeddingCache",
    "HashingEmbedder",
    "HostedEmbedder",
    "cosine",
    "get_embedder",
    "l2_normalize",
]
