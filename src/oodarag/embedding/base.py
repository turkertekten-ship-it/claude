"""The embedder interface.

Two methods, deliberately: documents and queries are embedded differently by
some providers (asymmetric models use distinct instruction prefixes), and a
pipeline that cannot express that difference silently loses accuracy on every
query.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

Vector = list[float]


class Embedder(ABC):
    name: str = "embedder"
    dim: int = 0

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        """Embed passages for indexing."""

    def embed_query(self, text: str) -> Vector:
        """Embed a query. Defaults to the document path for symmetric models."""
        return self.embed_documents([text])[0]

    def fit(self, corpus: Sequence[str]) -> None:
        """Optional: learn corpus statistics. No-op for hosted models."""
        return None

    @property
    def fingerprint(self) -> str:
        """Identity of this embedder's vector space.

        Vectors from different models, dimensions or corpus statistics are not
        comparable. The fingerprint is stored alongside every vector so a
        configuration change is detected instead of silently returning garbage
        similarity scores against a half-migrated index.
        """
        return f"{self.name}:{self.dim}"

    def state(self) -> dict:
        return {}

    def load_state(self, state: dict) -> None:
        return None
