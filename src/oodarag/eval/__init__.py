"""Evaluation: retrieval and answer quality as numbers, not impressions."""

from oodarag.eval.harness import EvalHarness, EvalReport, Golden, load_goldens
from oodarag.eval.metrics import dcg, mrr, ndcg_at_k, precision_at_k, recall_at_k

__all__ = [
    "EvalHarness", "EvalReport", "Golden", "load_goldens",
    "recall_at_k", "precision_at_k", "mrr", "ndcg_at_k", "dcg",
]
