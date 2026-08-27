"""The nightly self-improvement loop.

Runs at the end of the day, looks at what you actually did - the prompts you
typed, the commands you ran, the files you have, the commits you made - and
improves your files from the evidence. Then it records what it did and what you
thought of it, so tomorrow's run is better than today's.

    from oodarag.reflect import ReflectLoop, ReflectConfig
    ReflectLoop(ReflectConfig(root=".", dry_run=False)).run_cycle()

Or from a shell, which is how it is actually meant to be used:

    ooda reflect run                      # dry run: show me what you would do
    ooda reflect run --apply              # do the safe ones
    ooda reflect schedule --kind systemd  # and do it every night

The orchestrator is exposed lazily (PEP 562). Importing it eagerly would drag
every source, rule and actuator into the process just to read a data class,
and - worse - would mean one broken optional module took down `ooda reflect
schedule` along with it. Cheap, dependency-free leaves are imported normally.
"""

from __future__ import annotations

import importlib
from typing import Any

from oodarag.reflect.journal import Journal
from oodarag.reflect.models import (
    CycleReport,
    EditOp,
    Evidence,
    Finding,
    Outcome,
    Proposal,
    Signal,
)

_LAZY: dict[str, str] = {
    "ReflectConfig": "oodarag.reflect.loop",
    "ReflectLoop": "oodarag.reflect.loop",
    "ScheduleSpec": "oodarag.reflect.schedule",
}

__all__ = [
    "CycleReport",
    "EditOp",
    "Evidence",
    "Finding",
    "Journal",
    "Outcome",
    "Proposal",
    "ReflectConfig",
    "ReflectLoop",
    "ScheduleSpec",
    "Signal",
]


def __getattr__(name: str) -> Any:
    module_path = _LAZY.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module_path), name)
    globals()[name] = value  # cache, so the indirection costs one lookup ever
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
