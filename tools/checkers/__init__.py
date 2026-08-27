"""The bundled data checkers.

Importing this module registers every checker. A checker whose module fails to
import is recorded in `IMPORT_FAILURES` rather than allowed to vanish: a review
that quietly ran nine checks instead of ten reads exactly like one that ran ten,
which is the failure mode this whole package exists to prevent.

See CONTRACT.md for what a checker must satisfy.
"""

from __future__ import annotations

import importlib

#: Checkers that ship with the tool. Order is irrelevant - the runner sorts.
BUILTIN = (
    "citations",
    "commands",
    "consistency",
    "coverage",
    "deps",
    "links",
    "numbers",
    "paths",
    "symbols",
    "tests_evidence",
)

#: module name -> why it could not be loaded. Surfaced in `Report.skipped`.
IMPORT_FAILURES: dict[str, str] = {}

for _name in BUILTIN:
    try:
        importlib.import_module(f"tools.checkers.{_name}")
    except Exception as _e:  # noqa: BLE001 - the reason is the payload
        IMPORT_FAILURES[_name] = f"{type(_e).__name__}: {_e}"

__all__ = ["BUILTIN", "IMPORT_FAILURES"]
