"""Chunking: the stage that decides what a "passage" is.

Retrieval quality is bounded above by chunking quality - no reranker recovers a
passage that was cut in half - so this package treats document structure as the
primary signal and length as a budget, not the other way round.
"""

from oodarag.chunk.splitter import build_context_header, chunk_document, fold, verify_spans

__all__ = ["build_context_header", "chunk_document", "fold", "verify_spans"]
