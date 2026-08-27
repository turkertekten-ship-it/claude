#!/usr/bin/env python3
"""Ingest Claude conversation archives into a searchable local index.

This exists because "look through my previous chats" needs somewhere for those
chats to actually be. It reads two formats:

  * Claude Code transcripts — one JSON object per line, `type` of user or
    assistant, message content either a string or a list of typed blocks.
    This shape was read off a real transcript rather than assumed.
  * claude.ai data exports — `conversations.json` from Settings → Privacy →
    Export data. Field names vary between export versions, so the reader tries
    a list of candidates per field and reports anything it cannot map. That
    schema is NOT verified here; see provenance/unknowns.md U-2.

Rules it follows, which matter more than its features:

  * Message text is stored verbatim. Nothing is cleaned, summarised, or
    normalised, so a search hit can be quoted back to its source.
  * Every message keeps its conversation id, message id, timestamp, role, and
    source file. A hit that cannot be traced is not evidence.
  * Nothing is ever synthesised. Records that cannot be parsed are skipped and
    counted, never repaired by guesswork.
  * An empty archive produces an empty index and says so. It does not invent
    sample data to look finished.

Usage
  python3 tools/ingest_chat_archive.py ingest [--archive DIR] [--db PATH]
  python3 tools/ingest_chat_archive.py search "vector database" [--limit N]
  python3 tools/ingest_chat_archive.py stats
  python3 tools/ingest_chat_archive.py show <conversation-id>

Exit
  0 clean · 1 findings (parse failures) · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ARCHIVE = REPO / "archive"
DEFAULT_DB = REPO / "archive" / "index.db"

# claude.ai export field names differ across export versions; try each in turn.
CONV_ID_FIELDS = ("uuid", "id", "conversation_id")
CONV_TITLE_FIELDS = ("name", "title", "summary")
CONV_MSG_FIELDS = ("chat_messages", "messages", "conversation")
MSG_ID_FIELDS = ("uuid", "id", "message_id")
MSG_ROLE_FIELDS = ("sender", "role", "author")
MSG_TEXT_FIELDS = ("text", "content", "body")
TIME_FIELDS = ("created_at", "timestamp", "createdAt", "created")

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id            TEXT PRIMARY KEY,
    kind          TEXT NOT NULL,      -- claude_code | claude_ai
    title         TEXT,
    source_file   TEXT NOT NULL,
    started_at    TEXT,
    ended_at      TEXT,
    message_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    seq             INTEGER NOT NULL,
    role            TEXT NOT NULL,
    text            TEXT NOT NULL,
    timestamp       TEXT,
    block_types     TEXT,
    source_file     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, seq);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts
    USING fts5(text, message_id UNINDEXED, tokenize='porter unicode61');

CREATE TABLE IF NOT EXISTS ingest_runs (
    run_at        TEXT NOT NULL,
    files         INTEGER NOT NULL,
    conversations INTEGER NOT NULL,
    messages      INTEGER NOT NULL,
    skipped       INTEGER NOT NULL,
    notes         TEXT
);
"""


@dataclass
class Message:
    id: str
    seq: int
    role: str
    text: str
    timestamp: str | None
    block_types: str
    source_file: str


@dataclass
class Conversation:
    id: str
    kind: str
    title: str | None
    source_file: str
    messages: list[Message] = field(default_factory=list)

    @property
    def started_at(self) -> str | None:
        stamps = sorted(m.timestamp for m in self.messages if m.timestamp)
        return stamps[0] if stamps else None

    @property
    def ended_at(self) -> str | None:
        stamps = sorted(m.timestamp for m in self.messages if m.timestamp)
        return stamps[-1] if stamps else None


@dataclass
class Report:
    files: int = 0
    conversations: int = 0
    messages: int = 0
    skipped: int = 0
    problems: list[str] = field(default_factory=list)

    def note(self, message: str) -> None:
        self.skipped += 1
        if len(self.problems) < 50:      # keep the report readable
            self.problems.append(message)


def first_of(record: dict, names: tuple[str, ...]):
    for name in names:
        if record.get(name) not in (None, ""):
            return record[name]
    return None


def flatten_content(content) -> tuple[str, list[str]]:
    """Return (verbatim text, block types) without altering the text itself."""
    if isinstance(content, str):
        return content, ["<str>"]
    if not isinstance(content, list):
        return "", []

    parts: list[str] = []
    kinds: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type", "?")
        kinds.append(kind)
        if kind in ("text", "thinking"):
            value = block.get("text") or block.get("thinking") or ""
            if value:
                parts.append(value)
        elif kind == "tool_use":
            parts.append(f"[tool_use:{block.get('name', '?')}]")
        elif kind == "tool_result":
            inner = block.get("content")
            if isinstance(inner, str):
                parts.append(inner)
            elif isinstance(inner, list):
                for sub in inner:
                    if isinstance(sub, dict) and sub.get("type") == "text":
                        parts.append(sub.get("text", ""))
    return "\n".join(p for p in parts if p), kinds


def parse_claude_code_jsonl(path: Path, report: Report) -> list[Conversation]:
    """One transcript file may hold more than one sessionId; group by it."""
    grouped: dict[str, Conversation] = {}
    rel = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

    for lineno, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            report.note(f"{rel}:{lineno}: unparseable JSON ({exc.msg})")
            continue
        if not isinstance(record, dict) or record.get("type") not in ("user", "assistant"):
            continue                     # sidecar record types carry no message

        message = record.get("message") or {}
        text, kinds = flatten_content(message.get("content"))
        if not text:
            continue                     # no textual content to index

        session = record.get("sessionId") or path.stem
        conv = grouped.setdefault(
            session,
            Conversation(id=f"cc:{session}", kind="claude_code", title=None, source_file=rel),
        )
        uuid = record.get("uuid") or f"{session}:{lineno}"
        conv.messages.append(
            Message(
                id=f"cc:{uuid}",
                seq=len(conv.messages),
                role=message.get("role") or record["type"],
                text=text,
                timestamp=record.get("timestamp"),
                block_types=",".join(kinds),
                source_file=rel,
            )
        )
    return list(grouped.values())


def parse_claude_ai_export(path: Path, report: Report) -> list[Conversation]:
    rel = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
    try:
        data = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError as exc:
        report.note(f"{rel}: unparseable JSON ({exc.msg})")
        return []

    if isinstance(data, dict):
        data = data.get("conversations") or data.get("data") or [data]
    if not isinstance(data, list):
        report.note(f"{rel}: expected a list of conversations, got {type(data).__name__}")
        return []

    conversations: list[Conversation] = []
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            report.note(f"{rel}[{index}]: conversation is not an object")
            continue
        conv_id = first_of(record, CONV_ID_FIELDS)
        if not conv_id:
            report.note(f"{rel}[{index}]: no id field among {CONV_ID_FIELDS}")
            continue

        raw_messages = first_of(record, CONV_MSG_FIELDS) or []
        if not isinstance(raw_messages, list):
            report.note(f"{rel}[{index}]: message list is {type(raw_messages).__name__}")
            continue

        conv = Conversation(
            id=f"ai:{conv_id}",
            kind="claude_ai",
            title=first_of(record, CONV_TITLE_FIELDS),
            source_file=rel,
        )
        for position, raw in enumerate(raw_messages):
            if not isinstance(raw, dict):
                report.note(f"{rel}[{index}].messages[{position}]: not an object")
                continue
            text = first_of(raw, MSG_TEXT_FIELDS)
            kinds: list[str] = []
            if not isinstance(text, str):
                text, kinds = flatten_content(text if text is not None else raw.get("content"))
            if not text:
                continue
            msg_id = first_of(raw, MSG_ID_FIELDS) or f"{conv_id}:{position}"
            conv.messages.append(
                Message(
                    id=f"ai:{msg_id}",
                    seq=position,
                    role=str(first_of(raw, MSG_ROLE_FIELDS) or "unknown"),
                    text=text,
                    timestamp=first_of(raw, TIME_FIELDS),
                    block_types=",".join(kinds) or "<str>",
                    source_file=rel,
                )
            )
        conversations.append(conv)
    return conversations


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def store(conn: sqlite3.Connection, conversations: list[Conversation], report: Report) -> None:
    for conv in conversations:
        conn.execute(
            "INSERT OR REPLACE INTO conversations"
            " (id, kind, title, source_file, started_at, ended_at, message_count)"
            " VALUES (?,?,?,?,?,?,?)",
            (conv.id, conv.kind, conv.title, conv.source_file,
             conv.started_at, conv.ended_at, len(conv.messages)),
        )
        # Re-ingesting a file must not duplicate its messages.
        conn.execute("DELETE FROM messages_fts WHERE message_id IN"
                     " (SELECT id FROM messages WHERE conversation_id = ?)", (conv.id,))
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv.id,))
        for msg in conv.messages:
            conn.execute(
                "INSERT OR REPLACE INTO messages"
                " (id, conversation_id, seq, role, text, timestamp, block_types, source_file)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (msg.id, conv.id, msg.seq, msg.role, msg.text,
                 msg.timestamp, msg.block_types, msg.source_file),
            )
            conn.execute(
                "INSERT INTO messages_fts (text, message_id) VALUES (?,?)",
                (msg.text, msg.id),
            )
            report.messages += 1
        report.conversations += 1
    conn.commit()


def discover(archive: Path) -> list[Path]:
    if not archive.exists():
        return []
    files = sorted(p for p in archive.rglob("*") if p.suffix in (".json", ".jsonl") and p.is_file())
    return [p for p in files if p.name != "index.db"]


def cmd_ingest(args) -> int:
    archive, db_path = Path(args.archive), Path(args.db)
    report = Report()
    paths = discover(archive)

    if not paths:
        print(f"No archive files found under {archive}/.")
        print()
        print("This is not an error — it means no conversation export has been")
        print("placed there yet. Nothing was indexed, and nothing was invented")
        print("to stand in for it. To populate it:")
        print()
        print("  claude.ai   Settings -> Privacy -> Export data, then unzip")
        print("              conversations.json into archive/")
        print("  Claude Code copy ~/.claude/projects/**/*.jsonl into archive/")
        print()
        print("Then re-run this command.")
        return 0

    conn = connect(db_path)
    for path in paths:
        report.files += 1
        if path.suffix == ".jsonl":
            parsed = parse_claude_code_jsonl(path, report)
        elif path.name.startswith("conversations") or path.suffix == ".json":
            parsed = parse_claude_ai_export(path, report)
        else:
            continue
        store(conn, parsed, report)

    conn.execute(
        "INSERT INTO ingest_runs (run_at, files, conversations, messages, skipped, notes)"
        " VALUES (?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), report.files,
         report.conversations, report.messages, report.skipped,
         "; ".join(report.problems[:10]) or None),
    )
    conn.commit()

    print(f"Indexed {report.messages} message(s) across {report.conversations} "
          f"conversation(s) from {report.files} file(s) -> {db_path}")
    if report.skipped:
        print(f"\nSkipped {report.skipped} record(s) that could not be parsed. "
              f"They were not repaired or guessed at:")
        for problem in report.problems:
            print(f"  - {problem}")
        return 1
    return 0


def cmd_search(args) -> int:
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"No index at {db_path}. Run `ingest` first.", file=sys.stderr)
        return 2
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT m.id, m.role, m.timestamp, m.source_file, c.id AS conv, c.title,"
            "       snippet(messages_fts, 0, '>>>', '<<<', ' ... ', 24) AS excerpt"
            "  FROM messages_fts f"
            "  JOIN messages m ON m.id = f.message_id"
            "  JOIN conversations c ON c.id = m.conversation_id"
            " WHERE messages_fts MATCH ?"
            " ORDER BY bm25(messages_fts) LIMIT ?",
            (args.query, args.limit),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"Bad FTS query {args.query!r}: {exc}", file=sys.stderr)
        return 2

    if not rows:
        print(f"No matches for {args.query!r} in {db_path}.")
        return 0

    for row in rows:
        title = row["title"] or row["conv"]
        print(f"\n[{row['timestamp'] or 'no timestamp'}] {row['role']} — {title}")
        print(f"  {row['excerpt']}")
        print(f"  message={row['id']}  file={row['source_file']}")
    print(f"\n{len(rows)} match(es).")
    return 0


def cmd_stats(args) -> int:
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"No index at {db_path}. Run `ingest` first.")
        return 0
    conn = connect(db_path)
    convs = conn.execute("SELECT COUNT(*) n FROM conversations").fetchone()["n"]
    msgs = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
    print(f"conversations: {convs}")
    print(f"messages:      {msgs}")
    if msgs:
        span = conn.execute(
            "SELECT MIN(timestamp) lo, MAX(timestamp) hi FROM messages WHERE timestamp IS NOT NULL"
        ).fetchone()
        print(f"date range:    {span['lo']} .. {span['hi']}")
        for row in conn.execute("SELECT kind, COUNT(*) n FROM conversations GROUP BY kind"):
            print(f"  {row['kind']}: {row['n']} conversation(s)")
    for row in conn.execute("SELECT * FROM ingest_runs ORDER BY run_at DESC LIMIT 3"):
        print(f"run {row['run_at']}: {row['messages']} msg, {row['skipped']} skipped")
    return 0


def cmd_show(args) -> int:
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"No index at {db_path}. Run `ingest` first.", file=sys.stderr)
        return 2
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT role, timestamp, text FROM messages WHERE conversation_id = ? ORDER BY seq",
        (args.conversation_id,),
    ).fetchall()
    if not rows:
        print(f"No conversation {args.conversation_id!r} in the index.", file=sys.stderr)
        return 1
    for row in rows:
        print(f"\n--- {row['role']} @ {row['timestamp'] or 'no timestamp'} ---")
        print(row["text"])
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", default=str(DEFAULT_DB), help="index database path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="read archive/ into the index")
    p_ingest.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_ingest.set_defaults(func=cmd_ingest)

    p_search = sub.add_parser("search", help="full-text search the index")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.set_defaults(func=cmd_search)

    sub.add_parser("stats", help="index summary").set_defaults(func=cmd_stats)

    p_show = sub.add_parser("show", help="print one conversation in full")
    p_show.add_argument("conversation_id")
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
