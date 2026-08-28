"""One place that turns a source's date into a timestamp.

Four connectors and the reranker all needed this, and two of them had grown
their own copy. Date parsing that differs between stages is the same shape as
tokenizing that differs between stages (L24): nothing errors, one side simply
reports a date the other cannot see.

Deliberately narrow. It accepts what the sources this project reads actually
send - ISO-8601 with or without a trailing `Z`, and numeric timestamps as
numbers or strings - and returns None for everything else rather than guessing.
None means "the source did not say", which is a different claim from "it changed
now", and conflating those is what made every document in a run equally fresh
(L44).
"""

from __future__ import annotations

import datetime
from typing import Any


def to_timestamp(value: Any) -> float | None:
    """A POSIX timestamp, or None when the value does not carry a date."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        # bool is an int subclass; a flag is not a date.
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    try:
        # `fromisoformat` handles the trailing Z from Python 3.11, the floor
        # this project targets. A naive datetime is read as UTC rather than as
        # local time: the sources are APIs, and their naive stamps are UTC.
        parsed = datetime.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.timestamp()
