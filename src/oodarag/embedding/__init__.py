"""Embedding providers behind one interface."""

from oodarag.embedding.base import Embedder
from oodarag.embedding.hashing import HashingEmbedder

__all__ = ["Embedder", "HashingEmbedder", "get_embedder"]


def get_embedder(name: str = "hashing", **kwargs) -> Embedder:
    """Resolve an embedder by name.

    Defaults to `hashing`, which needs no network, no key and no model
    download. That is not a toy fallback: it is the only configuration in which
    the whole pipeline is reproducible in CI and inside an air-gapped container,
    so it is the one the tests and the eval baseline run on.
    """
    name = (name or "hashing").lower()
    if name in ("hashing", "local", "offline"):
        return HashingEmbedder(**kwargs)
    if name in ("voyage", "voyageai"):
        from oodarag.embedding.providers import VoyageEmbedder

        return VoyageEmbedder(**kwargs)
    if name in ("openai", "openai-compatible", "compat"):
        from oodarag.embedding.providers import OpenAICompatibleEmbedder

        return OpenAICompatibleEmbedder(**kwargs)
    raise ValueError(f"unknown embedder: {name!r}")
