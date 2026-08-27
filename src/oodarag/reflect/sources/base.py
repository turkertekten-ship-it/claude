"""The signal-source contract.

A source's only job is to turn one system - a chat log, a shell history file, a
directory tree, a git repository - into `Signal`s. It does not interpret them.
That separation is the reason a rule written against chat prompts also fires on
terminal history: rules never see a source, only signals.

Three things are enforced here rather than left to each source, because a
source that forgets one of them is a source that leaks or hangs:

1. **Redaction.** Every signal's text passes through `redact_secrets` on the way
   out. Shell history and chat logs are the two places on a machine most likely
   to contain a live token pasted in a hurry, and this loop writes reports to
   disk and diffs to a review queue.
2. **Budgets.** Every source runs under a cap on signals, bytes and wall-clock.
   A nightly job that walks a home directory must not still be walking it at
   dawn.
3. **Containment.** A source that raises returns an empty result with the error
   recorded. One unreadable history file must not cost you the night's run.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.reflect.models import Signal
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("reflect.source")


@dataclass(slots=True)
class Budget:
    """Hard caps for one source run.

    Wall-clock is measured from construction with a monotonic clock, so a clock
    adjustment in the middle of the night cannot make a budget infinite.
    """

    max_signals: int = 20_000
    max_bytes: int = 32_000_000
    max_chars_per_signal: int = 20_000
    wall_clock_s: float = 120.0
    started: float = field(default_factory=time.monotonic)

    def expired(self) -> bool:
        return self.wall_clock_s > 0 and (time.monotonic() - self.started) > self.wall_clock_s

    def child(self, wall_clock_s: float | None = None) -> Budget:
        """A fresh budget for one sub-run, so one slow source cannot eat the rest."""
        return Budget(
            max_signals=self.max_signals,
            max_bytes=self.max_bytes,
            max_chars_per_signal=self.max_chars_per_signal,
            wall_clock_s=self.wall_clock_s if wall_clock_s is None else wall_clock_s,
        )


@dataclass(slots=True)
class SourceResult:
    key: str
    signals: list[Signal] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    truncated: bool = False
    duration_s: float = 0.0

    def __len__(self) -> int:
        return len(self.signals)


class SignalSource(ABC):
    """Base class for everything that observes.

    Subclasses implement `collect`; `run` wraps it with the guarantees above.
    """

    #: Stable identifier, e.g. "chat:claude-code" or "shell:zsh". Appears on
    #: every signal and in the report, so it must not drift between nights.
    key: str = "source"

    #: Signal kinds this source can emit. Purely declarative - used by the loop
    #: to skip sources no enabled rule cares about.
    kinds: tuple[str, ...] = ()

    def available(self) -> bool:
        """Whether this source can run here at all (files present, tool installed)."""
        return True

    @abstractmethod
    def collect(self, since: float, budget: Budget) -> Iterator[Signal]:
        """Yield signals observed at or after `since` (unix seconds).

        `since` is advisory for sources that cannot filter cheaply; `run`
        enforces it. Yield lazily: budgets are checked between yields, so a
        generator can be cut off mid-walk, while a list cannot.
        """

    def run(self, since: float = 0.0, budget: Budget | None = None) -> SourceResult:
        budget = budget or Budget()
        started = time.monotonic()
        result = SourceResult(key=self.key)
        bytes_seen = 0

        if not self.available():
            result.duration_s = round(time.monotonic() - started, 3)
            log.debug("source unavailable", key=self.key)
            return result

        try:
            for sig in self.collect(since, budget):
                if len(result.signals) >= budget.max_signals or bytes_seen >= budget.max_bytes:
                    result.truncated = True
                    break
                if budget.expired():
                    result.truncated = True
                    log.warn("source hit wall-clock budget", key=self.key)
                    break
                if sig.ts and since and sig.ts < since:
                    continue
                text = sig.text or ""
                if len(text) > budget.max_chars_per_signal:
                    text = text[: budget.max_chars_per_signal] + "\n...[truncated]"
                redacted = redact_secrets(text)
                # Whether redaction actually fired is the authoritative answer to
                # "did this file hold a credential", and only the observer can
                # know it. A rule that infers it later by matching the marker
                # text cannot tell a redacted secret from a file that *defines*
                # the markers - the redaction module itself, its tests, a README
                # quoting one - and reports a critical finding against each.
                sig.metadata["redacted"] = redacted != text
                sig.text = redacted
                if not sig.source:
                    sig.source = self.key
                bytes_seen += len(sig.text)
                result.signals.append(sig)
        except Exception as e:  # the source itself failed
            result.errors.append(f"{self.key}: {type(e).__name__}: {e}")
            log.error("source failed", key=self.key, err=str(e)[:300])

        result.duration_s = round(time.monotonic() - started, 3)
        log.debug(
            "source run", key=self.key, signals=len(result.signals),
            truncated=result.truncated, secs=result.duration_s,
        )
        return result


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    """Read a text file, or return "" for anything that is not readable text.

    Sources walk directories full of binaries, sockets, broken symlinks and
    files owned by other users. Every one of those is a normal condition here,
    not an error worth a traceback.
    """
    try:
        if not path.is_file():
            return ""
        if path.stat().st_size > max_bytes:
            with path.open("rb") as fh:
                raw = fh.read(max_bytes)
        else:
            raw = path.read_bytes()
    except (OSError, ValueError):
        return ""
    if b"\x00" in raw[:8000]:  # NUL in the head is the cheapest binary test
        return ""
    return raw.decode("utf-8", "replace")


def session_from_path(path: Path, fallback: str = "") -> str:
    """A session key derived from a file name (chat logs are one file per session)."""
    return path.stem or fallback


def iter_existing(paths: list[Path]) -> Iterator[Path]:
    for p in paths:
        try:
            if p.exists():
                yield p
        except OSError:
            continue


def home_candidates(*relative: str) -> list[Path]:
    """Expand a set of home-relative paths, honouring $HOME overrides in tests."""
    home = Path.home()
    return [home / r for r in relative]


def as_metadata(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v not in (None, "", [])}
