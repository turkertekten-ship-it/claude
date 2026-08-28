"""Structured logging.

Every pipeline stage logs one JSON object per event so a run can be replayed
from its log alone. Human-readable mode is the default for a terminal.

Three rules keep that promise true rather than aspirational.

Everything goes to stderr. `ooda ... --json` writes its result document to
stdout for a caller to pipe into `jq`, so a single log line on stdout would
corrupt it. There is deliberately no code path here that can reach stdout.

An event is one line, and one line is one write. Field values come from the
outside world - a URL, a page title, `str(exc)` from a remote error - and a
newline inside one of them would forge a log line that a reader cannot tell
from a real event. JSON mode escapes it; text mode escapes it by hand. The
record is also written with a single `write` call rather than `print`'s two,
so two threads cannot split one event across two lines.

A log call never raises. `json.dumps` refuses more than callers expect - a
non-string dict key, a reference cycle, a NaN - and the call sites here are
usually already handling a failure. Serialization trouble degrades to a line
carrying the fields in repr form; a logger that can end a nightly run at 3am is
worse than no logger at all.

`OODARAG_LOG_LEVEL` (debug/info/warn/error/silent) and `OODARAG_LOG_FORMAT`
(`json`) are read when a Logger is constructed. Modules build theirs at import
time, so the environment has to be set before the process starts - which is the
only point at which a nightly job's environment is under anyone's control.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

_LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40, "silent": 100}
_DEFAULT_LEVEL = _LEVELS["info"]

_PREFIXES = {"debug": "  ", "info": "  ", "warn": "! ", "error": "x "}

#: Keys the envelope owns. A caller field of the same name is renamed rather
#: than allowed to win: a record whose "level" reads "info" because some call
#: site passed level="info" as data is a lie no replay can detect.
_RESERVED = frozenset({"ts", "level", "logger", "msg"})


def _safe_repr(value: Any) -> str:
    try:
        return repr(value)
    except Exception:  # a broken __repr__ is not a reason to lose the event
        return "<unrepresentable>"


def _safe_str(value: Any) -> str:
    try:
        text = str(value)
    except Exception:
        return "<unrepresentable>"
    # Text mode has no quoting, so a newline in a value is not content, it is
    # structure: it would end the event and start a forged one. Backslashes are
    # left alone - unambiguity is worth less here than a readable path.
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


class Logger:
    def __init__(self, name: str, level: str | None = None, json_mode: bool | None = None) -> None:
        self.name = name
        # An unset variable and an empty one mean the same thing; an unknown
        # name is a typo in a shell profile, not a reason to fail a run.
        env_level = (level or os.environ.get("OODARAG_LOG_LEVEL") or "info").strip()
        self.level = _LEVELS.get(env_level.lower(), _DEFAULT_LEVEL)
        self.json_mode = (
            json_mode
            if json_mode is not None
            else os.environ.get("OODARAG_LOG_FORMAT", "").strip().lower() == "json"
        )

    def _emit(self, level: str, msg: str, fields: dict[str, Any]) -> None:
        if _LEVELS[level] < self.level:
            return
        if self.json_mode:
            line = self._json_line(level, msg, fields)
        else:
            line = self._text_line(level, msg, fields)
        stream = sys.stderr  # resolved per call: tests and CLIs both rebind it
        stream.write(line + "\n")
        stream.flush()

    def _json_line(self, level: str, msg: str, fields: dict[str, Any]) -> str:
        payload: dict[str, Any] = {
            "ts": round(time.time(), 3),
            "level": level,
            "logger": self.name,
            "msg": msg if isinstance(msg, str) else _safe_repr(msg),
        }
        for key, value in fields.items():
            payload[f"field_{key}" if key in _RESERVED else key] = value
        try:
            # allow_nan=False: NaN/Infinity are Python's dialect of JSON, not
            # JSON, and one unparsable line costs a reader the whole run.
            return json.dumps(payload, default=_safe_repr, allow_nan=False)
        except (TypeError, ValueError, RecursionError):
            # A cycle, an unstringifiable dict key, or a non-finite float. The
            # envelope is known-good, so only the caller's fields are flattened.
            flat = {k: v if k in _RESERVED else _safe_repr(v) for k, v in payload.items()}
            return json.dumps(flat, default=_safe_repr, allow_nan=False)

    def _text_line(self, level: str, msg: str, fields: dict[str, Any]) -> str:
        extra = " ".join(f"{k}={_safe_str(v)}" for k, v in fields.items())
        return f"{_PREFIXES[level]}[{self.name}] {msg}{' ' + extra if extra else ''}"

    # `msg` is positional-only so that a call site logging a field named "msg"
    # gets a record instead of a TypeError raised from inside the logger, on the
    # very error path it was trying to report. Envelope collisions are resolved
    # by renaming the field, never by crashing or by letting the field win.
    def debug(self, msg: str, /, **f: Any) -> None:
        self._emit("debug", msg, f)

    def info(self, msg: str, /, **f: Any) -> None:
        self._emit("info", msg, f)

    def warn(self, msg: str, /, **f: Any) -> None:
        self._emit("warn", msg, f)

    def error(self, msg: str, /, **f: Any) -> None:
        self._emit("error", msg, f)


def get_logger(name: str) -> Logger:
    return Logger(name)
