"""A prompt workbench for Claude Code.

The Anthropic Console Workbench lets you hold a prompt still and vary one
thing at a time: the model, the parameters, the wording. Then it lets you
score the results. A terminal agent has none of that by default -- it has one
conversation, one configuration, and no memory of what the previous wording
scored.

This package supplies the missing half, with three commitments that the
console version does not make:

1.  **Deterministic graders run first.** A model is only asked to judge what
    no exact match, regex, schema check or shell command could settle. Every
    grader reports which kind it was, so a result can be read for how much of
    it rests on a judgement call.
2.  **Comparisons are blind.** A judge never learns which variant produced
    which candidate, and every pair is judged twice with the positions
    swapped. A win that does not survive the swap is recorded as a tie.
3.  **Costs are reported, never estimated.** The figures come from the
    backend's own accounting. This package contains no price table, because a
    price table is a fact that goes stale silently.

Entry point: ``python3 -m workbench``.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
