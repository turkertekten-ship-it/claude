"""Ranking and gating: what is worth doing tonight, and what is allowed.

Exposed lazily (PEP 562) for the same reason as `reflect.sources`: importing the
pure conflict rules must not drag in the policy engine and its journal-backed
priors, and one broken module here should cost that module rather than the run.
"""

from __future__ import annotations

import importlib
from typing import Any

from oodarag.reflect.decide.conflicts import EXCLUSIVE_OPS, resolve_edit_conflicts

_LAZY: dict[str, str] = {
    "Decision": "oodarag.reflect.decide.policy",
    "PolicyConfig": "oodarag.reflect.decide.policy",
    "PolicyEngine": "oodarag.reflect.decide.policy",
    "RulePriors": "oodarag.reflect.decide.priors",
}

__all__ = [
    "EXCLUSIVE_OPS",
    "Decision",
    "PolicyConfig",
    "PolicyEngine",
    "RulePriors",
    "resolve_edit_conflicts",
]


def __getattr__(name: str) -> Any:
    module_path = _LAZY.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module_path), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
