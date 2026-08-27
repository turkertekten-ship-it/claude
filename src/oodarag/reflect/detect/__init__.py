"""Rules.

Importing this package is what populates the registry: every rule module is
imported here for its `@register` side effects, so `build_detectors()` returns
the rules that actually exist rather than a hand-maintained list that drifts
from them.

Each import is guarded individually. A rule module with a syntax error or a bad
import should cost you that rule and be loudly reported - not silently disable
every other rule, and not abort a nightly run that would otherwise have found
nine useful things. `load_errors()` exposes what failed so the cycle report can
say so out loud instead of quietly returning fewer findings.
"""

from __future__ import annotations

import importlib

from oodarag.reflect.detect.base import (
    DetectContext,
    Detector,
    build_detectors,
    register,
    registry,
)
from oodarag.util.logging import get_logger

log = get_logger("reflect.detect")

#: Rule modules, in report order. Adding a rule family means adding one name.
RULE_MODULES = ("friction", "terminal", "docs", "hygiene")

_LOAD_ERRORS: dict[str, str] = {}


def _load_rules() -> None:
    for name in RULE_MODULES:
        try:
            importlib.import_module(f"oodarag.reflect.detect.{name}")
        except Exception as e:  # noqa: BLE001 - a bad rule must not sink the run
            _LOAD_ERRORS[name] = f"{type(e).__name__}: {e}"
            log.error("rule module failed to load", module=name, err=str(e)[:300])


def load_errors() -> dict[str, str]:
    """Rule modules that could not be imported, for the report to surface."""
    return dict(_LOAD_ERRORS)


_load_rules()

__all__ = [
    "DetectContext",
    "Detector",
    "RULE_MODULES",
    "build_detectors",
    "load_errors",
    "register",
    "registry",
]
