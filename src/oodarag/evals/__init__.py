"""Evaluation: the golden set, and the harness that turns it into numbers.

The package is separate from the pipeline stages on purpose. Nothing in
`oodarag/` imports it, so the harness can depend on the whole pipeline without
any stage depending on the harness - and a retrieval change can never quietly
adjust the thing that grades it.

The offline seed corpus and `goldens.jsonl` live in `evals/` at the repository
root rather than inside the package: they are data a reader is meant to open,
edit and argue with, not code shipped in a wheel.
"""

from oodarag.evals.harness import EvalReport, Golden, evaluate, load_goldens

__all__ = ["EvalReport", "Golden", "evaluate", "load_goldens"]
