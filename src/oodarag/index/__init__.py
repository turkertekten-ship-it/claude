"""The index: one durable SQLite file plus two ranking structures over it.

The split is deliberate. `Store` owns everything that must survive a process -
documents, chunks, vectors - and is the only module in the pipeline permitted
durable state. `BM25Index` and `DenseIndex` own everything cheap to recompute:
term statistics and a vector matrix, both rebuilt from `Store.iter_chunks()`
and `Store.iter_vectors()` at startup.

Persisting those two structures instead would buy a second or two of startup and
cost a whole class of bug - an inverted list that disagrees with the rows it was
built from, which does not fail, it just quietly ranks wrong. Rebuilding from
the store makes disagreement impossible by construction.

Two arms rather than one because they fail differently: BM25 finds the exact
error string and the rare identifier a dense model has never seen, dense finds
the paraphrase that shares no words with the question. `retrieve.py` fuses them.
"""

from __future__ import annotations

from oodarag.index.bm25 import BM25Index, BM25Params
from oodarag.index.dense import DenseIndex
from oodarag.index.store import Store

__all__ = ["BM25Index", "BM25Params", "DenseIndex", "Store"]
