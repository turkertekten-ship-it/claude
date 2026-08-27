"""Reading the user's own words back out of chat transcripts.

This is the source the rest of the loop leans on hardest. Shell history records
what was run and git records what changed, but only a transcript records what
the user *wanted* - and nearly every finding worth surfacing ("you re-explained
the test command four nights running", "you corrected the same assumption
twice") is a statement about intent rather than about mechanics.

Two things make that harder than tailing a log file.

The first is that "transcript format" is not a format. Claude Code writes one
JSON object per line with keys that have moved between versions; other tools
write a flat list of ``{"role", "content"}`` dicts; a `content` field is
sometimes a string and sometimes a list of typed blocks. So every file is
sniffed rather than assumed, and every shape that is not recognized costs one
turn, never the file and never the run. Half-written final lines are the normal
state of a session that is still open, not an exceptional one.

The second is that most lines in a modern transcript are not speech. Tool
inputs, tool results, ``<command-name>`` envelopes and injected
``<system-reminder>`` blocks outnumber real instructions by an order of
magnitude and are far longer than them. Left in the text, they drown the one
sentence the user actually typed in anything a detector goes on to measure -
term frequencies, repeated phrasings, similarity between turns. So tool calls
survive only as names in ``metadata["tools"]``, their payloads are dropped on
the floor, and envelope turns are counted in `self.skipped` rather than
emitted: a sudden jump in that count is the earliest warning that a new
transcript version has outrun this parser.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from oodarag.reflect.models import (
    ACTOR_ASSISTANT,
    ACTOR_HUMAN,
    KIND_PROMPT,
    KIND_REPLY,
    Signal,
)
from oodarag.reflect.sources.base import (
    Budget,
    SignalSource,
    as_metadata,
    iter_existing,
    safe_read_text,
)
from oodarag.util.logging import get_logger

log = get_logger("reflect.transcripts")

#: Where transcripts live when nobody says otherwise. `history` is included
#: because older Claude Code builds wrote there and a machine may hold both.
DEFAULT_RELATIVE_ROOTS = (".claude/projects", ".claude/history")

#: Colon-separated extra roots, for people who keep transcripts elsewhere.
ROOTS_ENV = "OODARAG_CHAT_ROOTS"

#: Per-file read cap. A long-running session file can reach tens of megabytes;
#: reading the head of one is worth more than reading none of it.
MAX_FILE_BYTES = 8_000_000

#: Ceiling on files considered in one run, so a home directory that has
#: accumulated years of sessions cannot turn the nightly job into a full scan.
MAX_FILES = 5_000

_TRANSCRIPT_GLOBS = ("*.jsonl", "*.ndjson", "*.json")

_USER_ROLES = frozenset({"user", "human"})
_ASSISTANT_ROLES = frozenset({"assistant", "model", "ai", "bot"})

#: Keys a timestamp has hidden behind, in the transcripts seen so far.
_TS_KEYS = ("timestamp", "ts", "time", "created_at", "createdAt", "date")

#: Block types whose body is machine chatter, never instruction.
_OPAQUE_BLOCKS = frozenset(
    {"tool_result", "thinking", "redacted_thinking", "image", "document", "search_result"}
)
_TOOL_CALL_BLOCKS = frozenset({"tool_use", "server_tool_use", "mcp_tool_use"})

_ENVELOPE_PREFIXES = ("<command-name>", "<local-command", "<system-reminder>")

# A turn that is *only* a tag block - "<command-message>...</command-message>",
# "<local-command-stdout></local-command-stdout>" - is the client talking to
# itself. Pasted HTML gets caught by this too, which is a trade worth making:
# a lost paste is one missing signal, a kept envelope skews every phrase count.
_TAG_ONLY_RE = re.compile(r"^<[^>\s]+(?:\s[^>]*)?>.*</[^>]+>$", re.DOTALL)

_NUMERIC_RE = re.compile(r"^\d+(?:\.\d+)?$")
_ISO_HEAD_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})")


def default_roots() -> list[Path]:
    """Standard transcript locations plus anything named in $OODARAG_CHAT_ROOTS."""
    roots = [Path.home() / rel for rel in DEFAULT_RELATIVE_ROOTS]
    for piece in os.environ.get(ROOTS_ENV, "").split(os.pathsep):
        piece = piece.strip()
        if piece:
            roots.append(Path(piece).expanduser())
    return roots


class ChatTranscriptSource(SignalSource):
    """Turn chat session files into `KIND_PROMPT` / `KIND_REPLY` signals.

    `skipped` counts turns dropped as synthetic - empty after text extraction,
    or a client envelope. It is reset per `collect` and read by the loop for
    observability; nothing downstream depends on its value.
    """

    key = "chat:transcripts"
    kinds = (KIND_PROMPT, KIND_REPLY)

    def __init__(self, roots: list[Path] | None = None) -> None:
        self.roots = [Path(r).expanduser() for r in roots] if roots is not None else default_roots()
        self.skipped = 0

    def available(self) -> bool:
        return next(iter_existing(self.roots), None) is not None

    def collect(self, since: float, budget: Budget) -> Iterator[Signal]:
        self.skipped = 0
        emitted = 0
        files = 0
        for path, mtime in self._iter_files(since):
            # Between files rather than between turns: a budget check per line
            # costs more than it saves, and one file is a bounded unit of work.
            if budget.expired() or emitted >= budget.max_signals:
                log.debug("transcript scan cut short", files=files, signals=emitted)
                return
            files += 1
            for sig in self._read_file(path, since, mtime, budget):
                yield sig
                emitted += 1
        log.debug("transcripts read", files=files, signals=emitted, skipped=self.skipped)

    # -- file discovery ------------------------------------------------------

    def _iter_files(self, since: float) -> Iterator[tuple[Path, float]]:
        """Candidate files, oldest first, already filtered by `since`.

        Dropping a whole file on its mtime is the cheapest filter available
        here: a session that was last written before the window opened cannot
        contain a turn inside it.
        """
        found: list[tuple[Path, float]] = []
        seen: set[Path] = set()
        for root in iter_existing(self.roots):
            for path in self._walk(root):
                if path in seen:
                    continue
                seen.add(path)
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                if since and mtime < since:
                    continue
                found.append((path, mtime))
                if len(found) >= MAX_FILES:
                    log.warn("transcript file cap hit", cap=MAX_FILES)
                    break
            if len(found) >= MAX_FILES:
                break
        found.sort(key=lambda pair: (pair[1], str(pair[0])))
        yield from found

    def _walk(self, root: Path) -> Iterator[Path]:
        try:
            if root.is_file():
                yield root
                return
            for pattern in _TRANSCRIPT_GLOBS:
                yield from sorted(root.rglob(pattern))
        except OSError as e:
            log.warn("transcript root unreadable", root=str(root), err=str(e)[:200])

    def _project_for(self, path: Path) -> str:
        """The per-project directory a session file sits in, if it sits in one."""
        parent = path.parent
        if any(parent == root for root in self.roots):
            return ""
        return parent.name

    # -- per-file parsing ----------------------------------------------------

    def _read_file(
        self, path: Path, since: float, mtime: float, budget: Budget
    ) -> Iterator[Signal]:
        text = safe_read_text(path, max_bytes=min(budget.max_bytes, MAX_FILE_BYTES))
        if not text.strip():
            return
        project = self._project_for(path)
        for index, (record, lineno) in enumerate(_iter_records(text)):
            try:
                sig = self._to_signal(record, path, lineno, index, mtime, project)
            except (AttributeError, TypeError, ValueError) as e:
                # An unrecognized record shape: lose the turn, keep the file.
                log.debug("transcript turn unparsed", uri=f"{path}#L{lineno}", err=str(e)[:120])
                continue
            if sig is None or (since and sig.ts < since):
                continue
            yield sig

    def _to_signal(
        self,
        rec: dict[str, Any],
        path: Path,
        lineno: int,
        index: int,
        mtime: float,
        project: str,
    ) -> Signal | None:
        message = rec.get("message")
        message = message if isinstance(message, dict) else None
        role, content = _role_and_content(rec, message)
        if role in _USER_ROLES:
            kind, actor = KIND_PROMPT, ACTOR_HUMAN
        elif role in _ASSISTANT_ROLES:
            kind, actor = KIND_REPLY, ACTOR_ASSISTANT
        else:
            return None  # summaries, system records, progress events

        text, tools = _extract_text(content)
        text = text.strip()
        if not text or _is_envelope(text):
            self.skipped += 1
            return None

        ts = _record_ts(rec, message)
        meta = as_metadata(
            cwd=_first_str(rec.get("cwd"), rec.get("workingDirectory")),
            model=_first_str(message.get("model") if message else None, rec.get("model")),
            file=str(path),
            project=project,
            tools=tools,
        )
        meta["turn"] = index
        return Signal(
            kind=kind,
            source=self.key,
            text=text,
            ts=ts if ts is not None else mtime,
            uri=f"{path}#L{lineno}",
            session=_session_of(rec, path),
            # Position in the file, so gaps left by dropped envelopes stay
            # visible and the order of what survived is still the real order.
            ordinal=index,
            actor=actor,
            metadata=meta,
        )


# -- record extraction -------------------------------------------------------


def _iter_records(text: str) -> Iterator[tuple[dict[str, Any], int]]:
    """Yield (record, line number) for whichever of the three layouts this is."""
    document = _load_document(text)
    if document is not None:
        # A pretty-printed document has no line per message worth pointing at,
        # so every turn anchors to the top of the file and metadata["turn"]
        # carries the position instead.
        for rec in document:
            yield rec, 1
        return
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue  # a torn final line from a session still being written
        if isinstance(rec, dict):
            yield rec, lineno


def _load_document(text: str) -> list[dict[str, Any]] | None:
    """Parse a whole-file JSON list of messages, or None if this is not one."""
    if not text[:64].lstrip().startswith(("[", "{")):
        return None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError, RecursionError):
        return None  # almost always JSONL, whose second line is "extra data"
    if isinstance(data, dict):
        for key in ("messages", "conversation", "turns", "history"):
            value = data.get(key)
            if isinstance(value, list):
                data = value
                break
        else:
            return None
    if not isinstance(data, list):
        return None
    return [rec for rec in data if isinstance(rec, dict)]


def _role_and_content(rec: dict[str, Any], message: dict[str, Any] | None) -> tuple[str, Any]:
    role = ""
    content: Any = None
    if message is not None:
        role = _first_str(message.get("role"))
        content = message.get("content")
    if not role:
        role = _first_str(rec.get("role"), rec.get("type"), rec.get("sender"))
    if content is None:
        content = rec.get("content", rec.get("text"))
    return role.lower(), content


def _extract_text(content: Any) -> tuple[str, list[str]]:
    """The human-readable half of a content field, plus the tool names in it.

    Tool inputs and results are discarded rather than summarized: a detector
    comparing two prompts wants the instruction, and a 40 KB diff pasted into a
    tool_result would dominate every similarity it computes.
    """
    if isinstance(content, str):
        return content, []
    if isinstance(content, dict):
        content = [content]
    if not isinstance(content, list):
        return "", []
    parts: list[str] = []
    tools: set[str] = set()
    for block in content:
        if isinstance(block, str):
            parts.append(block)
            continue
        if not isinstance(block, dict):
            continue
        btype = _first_str(block.get("type"))
        if btype in _TOOL_CALL_BLOCKS:
            name = _first_str(block.get("name"))
            if name:
                tools.add(name)
            continue
        if btype in _OPAQUE_BLOCKS:
            continue
        value = block.get("text")
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(p for p in parts if p.strip()), sorted(tools)


def _is_envelope(text: str) -> bool:
    """Whether a turn is the client talking to itself rather than the user."""
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.startswith(_ENVELOPE_PREFIXES):
        return True
    return stripped.startswith("<") and bool(_TAG_ONLY_RE.match(stripped))


def _session_of(rec: dict[str, Any], path: Path) -> str:
    session = _first_str(
        rec.get("sessionId"),
        rec.get("session_id"),
        rec.get("session"),
        rec.get("conversationId"),
        rec.get("conversation_id"),
    )
    return session or path.stem


# -- timestamps --------------------------------------------------------------


def _record_ts(rec: dict[str, Any], message: dict[str, Any] | None) -> float | None:
    for holder in (rec, message):
        if not isinstance(holder, dict):
            continue
        for key in _TS_KEYS:
            if key in holder:
                value = _parse_ts(holder[key])
                if value is not None:
                    return value
    return None


def _parse_ts(value: Any) -> float | None:
    """Unix seconds from whatever the writer thought a timestamp was.

    A timestamp this cannot read is not an error worth losing a turn over - the
    caller falls back to the file's mtime, which is wrong by minutes rather
    than by the whole signal.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return _from_epoch(float(value))
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if _NUMERIC_RE.match(raw):
        return _from_epoch(float(raw))
    iso = raw[:-1] + "+00:00" if raw.endswith(("Z", "z")) else raw
    try:
        parsed = datetime.fromisoformat(iso)
    except ValueError:
        parsed = _parse_ts_head(raw)
        if parsed is None:
            return None
    try:
        return parsed.timestamp()
    except (OSError, OverflowError, ValueError):
        return None


def _parse_ts_head(raw: str) -> datetime | None:
    """Last resort: the date and second of an ISO-ish string, offsets ignored.

    Reached by things `fromisoformat` refuses - nanosecond fractions, a comma
    decimal separator, a trailing " UTC". Losing the sub-second part costs
    nothing here; every window in this loop is measured in hours.
    """
    match = _ISO_HEAD_RE.match(raw)
    if not match:
        return None
    try:
        parsed = datetime.strptime(f"{match.group(1)}T{match.group(2)}", "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
    # Naive strings are read as local time, except where the original carried a
    # UTC marker that the strict parser choked on for unrelated reasons.
    if raw.endswith(("Z", "z")) or "+00:00" in raw or raw.endswith("UTC"):
        return parsed.replace(tzinfo=UTC)
    return parsed


def _from_epoch(value: float) -> float | None:
    if value <= 0:
        return None
    while value > 4e10:  # milliseconds, or microseconds, rather than seconds
        value /= 1000.0
    return value


def _first_str(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""
