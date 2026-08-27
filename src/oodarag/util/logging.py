"""Structured logging.

Every pipeline stage logs one JSON object per event so a run can be replayed
from its log alone. Human-readable mode is the default for a terminal.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

_LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40, "silent": 100}


class Logger:
    def __init__(self, name: str, level: str | None = None, json_mode: bool | None = None) -> None:
        self.name = name
        env_level = level or os.environ.get("OODARAG_LOG_LEVEL", "info")
        self.level = _LEVELS.get(env_level.lower(), 20)
        self.json_mode = (
            json_mode
            if json_mode is not None
            else os.environ.get("OODARAG_LOG_FORMAT", "").lower() == "json"
        )

    def _emit(self, level: str, msg: str, /, **fields: Any) -> None:
        if _LEVELS[level] < self.level:
            return
        if self.json_mode:
            payload = {"ts": round(time.time(), 3), "level": level, "logger": self.name, "msg": msg}
            payload.update(fields)
            print(json.dumps(payload, default=str), file=sys.stderr, flush=True)
        else:
            extra = " ".join(f"{k}={v}" for k, v in fields.items())
            prefix = {"debug": "  ", "info": "  ", "warn": "! ", "error": "x "}[level]
            print(f"{prefix}[{self.name}] {msg}{' ' + extra if extra else ''}", file=sys.stderr, flush=True)

    def debug(self, msg: str, /, **f: Any) -> None:
        self._emit("debug", msg, **f)

    def info(self, msg: str, /, **f: Any) -> None:
        self._emit("info", msg, **f)

    def warn(self, msg: str, /, **f: Any) -> None:
        self._emit("warn", msg, **f)

    def error(self, msg: str, /, **f: Any) -> None:
        self._emit("error", msg, **f)


def get_logger(name: str) -> Logger:
    return Logger(name)
