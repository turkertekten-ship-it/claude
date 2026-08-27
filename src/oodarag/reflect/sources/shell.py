"""Terminal history as a signal source.

A chat log records what the user *asked for*; the shell records what they
actually did, including the four attempts before the one that worked. That is
the material most friction rules need, and it is nearly free to read - every
shell already keeps it, whether or not anyone meant it to be observed.

The hard part is time. Only some formats record when a command ran: zsh's
extended history does, fish does, bash does it only when `HISTTIMEFORMAT` was
exported. A plain `~/.bash_history` is an ordered list of commands with no clock
at all, and a nightly loop that filters on "since the last run" has two bad
options for such a file - drop it every night, or re-emit all of it every night.
Neither is acceptable, so this source takes a third: read only the tail, stamp
those commands with the file's mtime, and mark them `ts_estimated` so a rule
that reasons about *when* can tell a measured timestamp from a guessed one.

Sessions are synthetic for the same reason. A history file carries no session
id, so signals are grouped by shell and local day ("zsh:2026-08-27"). Same-day
adjacency is the grouping the retry-loop rules actually want; anything finer
would be invented precision.

Redaction belongs to the base class - `SignalSource.run` passes every signal
through `redact_secrets` - which matters more here than anywhere else, because
history is exactly where `export API_KEY=...` lives.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oodarag.reflect.models import ACTOR_HUMAN, KIND_COMMAND, Signal, day_key
from oodarag.reflect.sources.base import (
    Budget,
    SignalSource,
    as_metadata,
    home_candidates,
    iter_existing,
    safe_read_text,
)
from oodarag.util.logging import get_logger

log = get_logger("reflect.source.shell")

#: How many commands to keep from a history file that carries no timestamps.
DEFAULT_TAIL_LINES = 500

#: Per-file read cap. Long-lived history files reach tens of megabytes and none
#: of the interesting part is at the start.
DEFAULT_MAX_FILE_BYTES = 4_000_000

#: A file where every line ends in a backslash would otherwise fold into one
#: enormous "command"; nothing a human types is 64 lines of continuation.
MAX_CONTINUATION_LINES = 64

_BUDGET_CHECK_EVERY = 200

_ZSH_META_RE = re.compile(r"^:\s*(\d+):(\d+);([\s\S]*)$")
_ZSH_SNIFF_RE = re.compile(r"^:\s*\d+:\d+;")
_BASH_TS_RE = re.compile(r"^#(\d{6,})$")
_FISH_CMD_RE = re.compile(r"^- +cmd:[ \t]?([\s\S]*)$")
_FISH_WHEN_RE = re.compile(r"^\s+when:\s*(\S+)")

#: Filename fragment -> shell. Checked in order, so "fish_history" is not read
#: as a bash file just because "bash" appears later in the list.
_NAME_HINTS: tuple[tuple[str, str], ...] = (
    ("fish", "fish"),
    ("zsh", "zsh"),
    ("zhistory", "zsh"),
    ("bash", "bash"),
)


@dataclass(slots=True)
class _Entry:
    """One command as it appears in a history file, before it becomes a Signal."""

    text: str
    lineno: int
    ts: float | None = None
    elapsed: float | None = None


class ShellHistorySource(SignalSource):
    """Bash, zsh and fish history files as `KIND_COMMAND` signals."""

    key = "shell:history"
    kinds = (KIND_COMMAND,)

    def __init__(
        self,
        paths: list[Path] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.config = config or {}
        self.tail_lines = _positive_int(self.config.get("tail_lines"), DEFAULT_TAIL_LINES)
        self.max_file_bytes = _positive_int(
            self.config.get("max_file_bytes"), DEFAULT_MAX_FILE_BYTES
        )
        # None means "discover"; an explicit list (including an empty one) is a
        # deliberate override, which is how tests stay off the real home dir.
        self._override = [Path(p) for p in paths] if paths is not None else None

    # -- discovery -----------------------------------------------------------

    def candidates(self) -> list[Path]:
        if self._override is not None:
            return list(self._override)
        out: list[Path] = []
        # $HISTFILE first: when it is set it is the file the user's shell is
        # really writing, and it often points somewhere the defaults never look.
        hist = os.environ.get("HISTFILE", "").strip()
        if hist:
            out.append(Path(hist).expanduser())
        out.extend(
            home_candidates(
                ".bash_history",
                ".zsh_history",
                ".zhistory",
                ".local/share/fish/fish_history",
            )
        )
        xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        if xdg:
            out.append(Path(xdg).expanduser() / "fish" / "fish_history")
        return out

    def available(self) -> bool:
        return next(iter_existing(self.candidates()), None) is not None

    # -- collection ----------------------------------------------------------

    def collect(self, since: float, budget: Budget) -> Iterator[Signal]:
        seen: set[str] = set()
        for path in iter_existing(self.candidates()):
            if budget.expired():
                return
            try:
                marker = str(path.resolve())
            except OSError:
                marker = str(path)
            if marker in seen:  # $HISTFILE frequently *is* ~/.zsh_history
                continue
            seen.add(marker)
            yield from self._collect_file(path, since, budget)

    def _collect_file(self, path: Path, since: float, budget: Budget) -> Iterator[Signal]:
        text = _read_tail(path, self.max_file_bytes)
        if not text:
            return
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = time.time()

        shell, fmt = _classify(path, text)
        entries = _PARSERS[fmt](text)
        timed = any(e.ts is not None for e in entries)
        offset = 0
        if not timed:
            # Nothing in this file can be newer than the file itself, so a stale
            # file is skipped whole rather than re-emitted and thrown away.
            if since and mtime < since:
                log.debug("history older than window", path=str(path), shell=shell)
                return
            if len(entries) > self.tail_lines:
                offset = len(entries) - self.tail_lines
                entries = entries[offset:]

        emitted = 0
        for index, entry in enumerate(entries):
            if emitted % _BUDGET_CHECK_EVERY == 0 and budget.expired():
                return
            if entry.ts is not None and since and entry.ts < since:
                continue
            ts = entry.ts if entry.ts is not None else mtime
            yield Signal(
                kind=KIND_COMMAND,
                source=self.key,
                text=entry.text,
                ts=ts,
                uri=f"{path}#L{entry.lineno}",
                session=f"{shell}:{day_key(ts)}",
                ordinal=offset + index,
                actor=ACTOR_HUMAN,
                metadata=as_metadata(
                    shell=shell,
                    argv0=_argv0(entry.text),
                    history_file=str(path),
                    ts_estimated=entry.ts is None,
                    elapsed_s=entry.elapsed,
                ),
            )
            emitted += 1


# -- parsers -----------------------------------------------------------------


def _parse_zsh(text: str) -> list[_Entry]:
    """zsh extended history: ``: <start>:<elapsed>;<command>``, or plain lines."""
    entries: list[_Entry] = []
    for lineno, line in _logical_lines(text):
        ts: float | None = None
        elapsed: float | None = None
        body = line
        if line.startswith(":"):
            match = _ZSH_META_RE.match(line)
            if match:
                ts = _parse_ts(match.group(1))
                elapsed = _parse_ts(match.group(2), allow_zero=True)
                body = match.group(3)
            elif ";" in line:
                # A metadata prefix we cannot read - a corrupt clock value, or a
                # write interleaved by two shells. Keep the command and drop the
                # claim about when it ran; a lost observation is worse than an
                # estimated timestamp.
                body = line.split(";", 1)[1]
        body = body.strip()
        if not _accept(body):
            continue
        entries.append(_Entry(text=body, lineno=lineno, ts=ts, elapsed=elapsed))
    return entries


def _parse_bash(text: str) -> list[_Entry]:
    """bash history: one command per line, optionally preceded by ``#<unix-ts>``."""
    entries: list[_Entry] = []
    pending: float | None = None
    for lineno, line in _logical_lines(text):
        body = line.strip()
        match = _BASH_TS_RE.match(body)
        if match:
            pending = _parse_ts(match.group(1))
            continue
        if not _accept(body):
            continue
        entries.append(_Entry(text=body, lineno=lineno, ts=pending))
        pending = None
    return entries


def _parse_fish(text: str) -> list[_Entry]:
    """fish history: a YAML-ish record stream, ``- cmd:`` then ``  when:``."""
    entries: list[_Entry] = []
    current: _Entry | None = None
    for lineno, raw in enumerate(text.split("\n"), start=1):
        match = _FISH_CMD_RE.match(raw)
        if match:
            if current is not None:
                entries.append(current)
            # Kept exactly as written: fish escapes embedded newlines as "\n",
            # and un-escaping that would corrupt every command that legitimately
            # contains a backslash-n, which is most `printf` lines.
            current = _Entry(text=match.group(1).strip(), lineno=lineno)
            continue
        if current is None:
            continue
        when = _FISH_WHEN_RE.match(raw)
        if when:
            current.ts = _parse_ts(when.group(1))
        # "  paths:" and its indented items describe the command rather than
        # being commands, so everything else in a record is ignored.
    if current is not None:
        entries.append(current)
    return [e for e in entries if _accept(e.text)]


_PARSERS = {"zsh": _parse_zsh, "bash": _parse_bash, "fish": _parse_fish}


# -- helpers -----------------------------------------------------------------


def _logical_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield (1-based line number, text), joining backslash continuations.

    Both zsh and bash store a multi-line command by escaping the newline, so
    reading physical lines would split one command into fragments that no rule
    can match.
    """
    lines = text.split("\n")
    index = 0
    total = len(lines)
    while index < total:
        start = index
        parts = [lines[index]]
        while (
            parts[-1].endswith("\\")
            and index + 1 < total
            and len(parts) < MAX_CONTINUATION_LINES
        ):
            parts[-1] = parts[-1][:-1]
            index += 1
            parts.append(lines[index])
        yield start + 1, "\n".join(parts)
        index += 1


def _accept(text: str) -> bool:
    """Blank lines, comment-only lines and one-character commands carry nothing."""
    return len(text) >= 2 and not text.startswith("#")


def _argv0(text: str) -> str:
    head = text.strip().split(None, 1)[0] if text.strip() else ""
    return head[:80]


def _parse_ts(raw: str, allow_zero: bool = False) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0 or (value == 0 and not allow_zero):
        return None
    return value


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _classify(path: Path, text: str) -> tuple[str, str]:
    """(shell label, parser name) for a history file."""
    name = path.name.lower()
    for fragment, shell in _NAME_HINTS:
        if fragment in name:
            return shell, shell
    # $HISTFILE may be called anything, so fall back to what the bytes look
    # like. A zsh file with EXTENDED_HISTORY off is indistinguishable from a
    # bash one and is parsed as bash - identical results, weaker label.
    fmt = _sniff(text)
    return fmt, fmt


def _sniff(text: str) -> str:
    for line in text.split("\n", 200)[:200]:
        if _FISH_CMD_RE.match(line):
            return "fish"
        if _ZSH_SNIFF_RE.match(line):
            return "zsh"
    return "bash"


def _read_tail(path: Path, max_bytes: int) -> str:
    """Read at most `max_bytes` from the END of a history file.

    History files are append-ordered, so a cap applied from the front would hand
    the loop last year's commands and silently hide today's.
    """
    try:
        size = path.stat().st_size
        if size <= max_bytes:
            return safe_read_text(path, max_bytes)
        with path.open("rb") as fh:
            fh.seek(size - max_bytes)
            raw = fh.read(max_bytes)
    except (OSError, ValueError):
        return ""
    if b"\x00" in raw[:8000]:  # same cheap binary test the base class uses
        return ""
    text = raw.decode("utf-8", "replace")
    # The seek almost certainly landed mid-line; that fragment is not a command.
    return text.split("\n", 1)[1] if "\n" in text else ""
