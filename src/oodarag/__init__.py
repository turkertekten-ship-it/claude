"""oodarag - an OODA-driven, end-to-end retrieval-augmented generation pipeline.

The package is deliberately dependency-free: every stage (ingest, normalize,
chunk, embed, index, retrieve, rerank, generate, evaluate) runs on the Python
standard library alone, so the pipeline is reproducible in CI, in an air-gapped
container, and on a laptop without a GPU. Optional accelerators and hosted
model providers plug in behind the same interfaces.
"""

__version__ = "0.1.0"

from oodarag.models import Answer, Chunk, Document, RawDocument, ScoredChunk

__all__ = ["Answer", "Chunk", "Document", "RawDocument", "ScoredChunk", "__version__"]
