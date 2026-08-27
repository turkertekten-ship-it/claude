"""Persistence and index structures: one SQLite file, two retrieval arms.

The Store owns the durable state (documents, chunks, float32 vectors, and the
serialised indexes themselves). BM25Index and VectorIndex are in-memory
structures built from it and persisted back into it, so a restart reloads an
index instead of rebuilding one.
"""

from oodarag.index.bm25 import BM25Index, tokenize_index_text, turkish_stem
from oodarag.index.store import Blob, Store, StoreError, UpsertReport, decode_vector, encode_vector
from oodarag.index.vector import VectorIndex

__all__ = [
    "BM25Index",
    "Blob",
    "Store",
    "StoreError",
    "UpsertReport",
    "VectorIndex",
    "decode_vector",
    "encode_vector",
    "tokenize_index_text",
    "turkish_stem",
]
