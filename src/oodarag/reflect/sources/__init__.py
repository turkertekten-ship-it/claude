"""Observers. Each turns one system the user touches into `Signal`s.

Adding a source is the whole extension story for coverage: implement
`SignalSource.collect`, and every rule in `reflect.detect` starts working on
that system without being told it exists.

Concrete sources are exposed lazily (PEP 562) so that importing one does not
import them all. A machine with no shell history, or a source module that fails
to import after an edit, must cost you that source and nothing else - the loop
runs unattended, and "one observer is unavailable tonight" is a normal Tuesday,
not a reason to skip the run.
"""

from __future__ import annotations

import importlib
from typing import Any

from oodarag.reflect.sources.base import Budget, SignalSource, SourceResult

_LAZY: dict[str, str] = {
    "ChatTranscriptSource": "oodarag.reflect.sources.transcripts",
    "ShellHistorySource": "oodarag.reflect.sources.shell",
    "WorkspaceFileSource": "oodarag.reflect.sources.workspace",
    "GitHistorySource": "oodarag.reflect.sources.workspace",
}

__all__ = [
    "Budget",
    "ChatTranscriptSource",
    "GitHistorySource",
    "ShellHistorySource",
    "SignalSource",
    "SourceResult",
    "WorkspaceFileSource",
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
