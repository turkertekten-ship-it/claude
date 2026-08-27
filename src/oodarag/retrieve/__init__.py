"""Retrieval: two arms fused by rank, then reranked by explainable features.

`HybridRetriever.retrieve` answers the question "which passages"; `rerank`
answers "in what order, and why". They are separate because the fusion stage
must stay free of judgement calls — RRF has no tunable per-corpus weights — and
every judgement call this pipeline makes about trust, freshness and redundancy
is therefore concentrated in one auditable place.
"""

from oodarag.retrieve.hybrid import ARM_DEPTH, RRF_K, HybridRetriever, RetrievalFilters
from oodarag.retrieve.rerank import (
    DEFAULT_WEIGHTS,
    RerankWeights,
    explain,
    rerank,
    rerank_report,
)

__all__ = [
    "ARM_DEPTH",
    "DEFAULT_WEIGHTS",
    "HybridRetriever",
    "RRF_K",
    "RerankWeights",
    "RetrievalFilters",
    "explain",
    "rerank",
    "rerank_report",
]
