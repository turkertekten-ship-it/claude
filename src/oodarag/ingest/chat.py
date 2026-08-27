"""Chat transcript connector.

Claude Code writes every session to JSONL under `~/.claude/projects/`. Those
transcripts are the highest-signal corpus most engineers never index: they
contain the decisions, the dead ends, the reasons a thing was built the way it
was, and the specific errors that were hit and fixed. None of that is in the
code, and most of it never reaches a document.

Three judgement calls shape what gets indexed, and each of them is about signal
rather than convenience:

**Tool result bodies are excluded by default.** A single `cat` of a large file
can be more text than the entire conversation around it, and it is text that
already exists in the repository - indexing it duplicates the corpus and buries
the reasoning. The *fact* that a tool ran, and which one, is kept: that is the
part that is not recoverable from anywhere else.

**Reasoning blocks are excluded by default.** They are the model's working, not
a conclusion, and they can restate discarded options confidently enough to be
retrieved as if they were decisions. Opt in with `include_thinking=True`.

**Redaction is not optional.** Transcripts routinely contain pasted credentials,
so every turn goes through `redact_secrets` before it becomes a document.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.logging import get_logger
from oodarag.util.text import clean, redact_secrets, summarize

log = get_logger("ingest.chat")

# Line types that carry conversation. Everything else in the JSONL is harness
# bookkeeping (attachments, mode switches, queue operations) and is not content.
CONVERSATION_TYPES = frozenset({"user", "assistant"})


class ChatTranscriptConnector(Connector):
    def __init__(
        self,
        root: str | Path | None = None,
        *,
        include_thinking: bool = False,
        include_tool_results: bool = False,
        max_tool_result_chars: int = 400,
        min_turns: int = 2,
        authority: float = 0.9,
        key: str | None = None,
    ) -> None:
        default_root = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
        self.root = Path(root) if root else default_root / "projects"
        self.include_thinking = include_thinking
        self.include_tool_results = include_tool_results
        self.max_tool_result_chars = max_tool_result_chars
        self.min_turns = min_turns
        self.authority = authority
        self.key = key or f"chat:{self.root}"
        self.stats: dict[str, Any] = {}

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        if not self.root.exists():
            log.warn("no transcript directory", path=str(self.root))
            self.stats = {"sessions": 0, "reason": "root missing"}
            return
        sessions = 0
        skipped = 0
        for path in sorted(self.root.rglob("*.jsonl")):
            document = self._session_document(path)
            if document is None:
                skipped += 1
                continue
            sessions += 1
            yield document
        self.stats = {"sessions": sessions, "skipped": skipped}
        log.info("chat transcripts read", sessions=sessions, skipped=skipped)

    def _session_document(self, path: Path) -> RawDocument | None:
        turns: list[str] = []
        tools: dict[str, int] = {}
        session_id = path.stem
        cwd = ""
        first_ts = ""
        last_ts = ""
        first_user_message = ""

        try:
            raw_lines = path.read_text("utf-8", errors="replace").splitlines()
        except OSError as e:
            log.warn("unreadable transcript", path=str(path), err=str(e)[:120])
            return None

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # a partially written last line is normal on a live session
            if entry.get("type") not in CONVERSATION_TYPES:
                continue
            cwd = entry.get("cwd") or cwd
            timestamp = entry.get("timestamp", "")
            first_ts = first_ts or timestamp
            last_ts = timestamp or last_ts

            message = entry.get("message") or {}
            role = message.get("role") or entry.get("type")
            rendered = self._render_content(message.get("content"), tools)
            if not rendered:
                continue
            if role == "user" and not first_user_message:
                first_user_message = rendered
            turns.append(f"{role}: {rendered}")

        if len(turns) < self.min_turns:
            return None

        body = "\n\n".join(turns)
        title = summarize(_strip_harness_markup(first_user_message), 90) or session_id
        return RawDocument(
            source_system="chat",
            external_id=f"session:{session_id}",
            uri=path.as_uri(),
            title=f"Session: {title}",
            text=redact_secrets(body),
            metadata={
                "kind": "chat_session",
                "session_id": session_id,
                "cwd": cwd,
                "turns": len(turns),
                "started_at": first_ts,
                "ended_at": last_ts,
                "tools_used": sorted(tools, key=lambda t: -tools[t])[:15],
                "tool_call_count": sum(tools.values()),
                "authority": self.authority,
                "project": path.parent.name,
            },
        )

    def _render_content(self, content: Any, tools: dict[str, int]) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return clean(content)

        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                parts.append(clean(block.get("text", "")))
            elif block_type == "thinking":
                if self.include_thinking:
                    parts.append(clean(block.get("thinking", "")))
            elif block_type == "tool_use":
                name = block.get("name", "tool")
                tools[name] = tools.get(name, 0) + 1
                # The intent behind a call is signal; its full arguments are not.
                description = (block.get("input") or {}).get("description") or ""
                parts.append(f"[used {name}{': ' + clean(description) if description else ''}]")
            elif block_type == "tool_result":
                if not self.include_tool_results:
                    continue
                payload = block.get("content")
                text = payload if isinstance(payload, str) else json.dumps(payload, default=str)
                parts.append(f"[result] {clean(text)[:self.max_tool_result_chars]}")
        return "\n".join(p for p in parts if p)

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["stats"] = self.stats
        return cursor


def _strip_harness_markup(text: str) -> str:
    """Drop the slash-command and hook wrappers so a title reads like a title."""
    import re

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
