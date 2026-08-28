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
  python3 tools/ingest_chat_archive.py ingest --include-projects
  python3 tools/ingest_chat_archive.py search "vector database" [--limit N]
  python3 tools/ingest_chat_archive.py stats
  python3 tools/ingest_chat_archive.py selfcheck
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
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"

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
    message_count INTEGER NOT NULL DEFAULT 0,
    cwd           TEXT,
    git_branch    TEXT
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
    cwd: str | None = None
    git_branch: str | None = None

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


def effective_role(declared: str, kinds: list[str]) -> str:
    """Separate the owner's own words from tool output.

    Claude Code writes tool *results* as records with `type: "user"` and
    `message.role: "user"` - the transcript format has no other slot for them.
    Taking that at face value files every command's output in the index as
    something the owner said, which makes the index useless for the one question
    it exists to answer: what did the owner actually ask for.

    A record whose content blocks are exclusively `tool_result` is tool output,
    and is filed as such. The text is still stored verbatim and still searchable;
    only the attribution changes.
    """
    if declared == "user" and kinds and all(k == "tool_result" for k in kinds):
        return "tool_result"
    return declared


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
        # Subagent transcripts carry their PARENT's sessionId, so the session
        # alone is not unique across files. Keying on the file too keeps one
        # transcript from overwriting another that merely shares a session.
        key = session if path.stem == session else f"{session}:{path.stem}"
        if key not in grouped:
            kind = "claude_code_subagent" if "subagents" in path.parts else "claude_code"
            grouped[key] = Conversation(
                id=f"cc:{key}", kind=kind, title=None, source_file=rel,
                cwd=record.get("cwd"), git_branch=record.get("gitBranch"),
            )
        conv = grouped[key]
        # A transcript's own fields are the only title available; never invent one.
        if conv.cwd is None:
            conv.cwd = record.get("cwd")
        if conv.git_branch is None:
            conv.git_branch = record.get("gitBranch")
        if conv.title is None and conv.cwd:
            conv.title = conv.cwd if not conv.git_branch else f"{conv.cwd} @ {conv.git_branch}"

        uuid = record.get("uuid") or f"{key}:{lineno}"
        conv.messages.append(
            Message(
                id=f"cc:{uuid}",
                seq=len(conv.messages),
                role=effective_role(message.get("role") or record["type"], kinds),
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

            # Uploaded files ride along as attachments carrying extracted_content.
            # That is conversation content the user actually supplied, so losing it
            # would make a search over the index quietly incomplete.
            for attachment in raw.get("attachments") or []:
                if not isinstance(attachment, dict):
                    continue
                extracted = attachment.get("extracted_content")
                if not extracted:
                    continue
                name = attachment.get("file_name") or "attachment"
                text = f"{text}\n[attachment:{name}]\n{extracted}" if text else \
                       f"[attachment:{name}]\n{extracted}"
                kinds.append("attachment")

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
            " (id, kind, title, source_file, started_at, ended_at, message_count, cwd, git_branch)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (conv.id, conv.kind, conv.title, conv.source_file,
             conv.started_at, conv.ended_at, len(conv.messages), conv.cwd, conv.git_branch),
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


def discover(archive: Path, projects: Path | None = None) -> list[Path]:
    """Archive files, plus every Claude Code transcript if `projects` is given.

    `projects` is normally ~/.claude/projects, where Claude Code keeps its
    transcripts on the machine that ran them. On a fresh container that holds
    only the current session; on the owner's own machine it is the whole
    Claude Code history, which is the point of the flag.
    """
    found: list[Path] = []
    if archive.exists():
        found += [p for p in archive.rglob("*")
                  if p.is_file() and p.suffix in (".json", ".jsonl")]
    if projects and projects.exists():
        found += [p for p in projects.rglob("*.jsonl") if p.is_file()]
    # Two paths can resolve to the same file (~ and an absolute root path).
    unique = {p.resolve(): p for p in found if p.name != "index.db"}
    return sorted(unique.values(), key=str)


def cmd_ingest(args) -> int:
    archive, db_path = Path(args.archive), Path(args.db)
    projects = Path(args.projects_dir).expanduser() if args.include_projects else None
    report = Report()
    paths = discover(archive, projects)

    if not paths:
        print(f"No conversation files found under {archive}/"
              + (f" or {projects}/." if projects else "."))
        print()
        print("This is not an error — it means no conversation record is")
        print("reachable from here. Nothing was indexed, and nothing was")
        print("invented to stand in for it. To populate it:")
        print()
        print("  Claude Code  re-run with --include-projects, on the machine")
        print("               whose ~/.claude/projects holds your transcripts")
        print("  claude.ai    Settings -> Privacy -> Export data, then unzip")
        print("               conversations.json into archive/")
        print()
        print("Then re-run this command.")
        return 0

    if projects:
        from_projects = sum(1 for p in paths if projects in p.resolve().parents)
        print(f"Reading {from_projects} transcript(s) from {projects} "
              f"and {len(paths) - from_projects} file(s) from {archive}.")

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
        sql = (
            "SELECT m.id, m.role, m.timestamp, m.source_file, c.id AS conv, c.title,"
            "       snippet(messages_fts, 0, '>>>', '<<<', ' ... ', 24) AS excerpt"
            "  FROM messages_fts f"
            "  JOIN messages m ON m.id = f.message_id"
            "  JOIN conversations c ON c.id = m.conversation_id"
            " WHERE messages_fts MATCH ?"
        )
        params: list = [args.query]
        if getattr(args, "role", None):
            sql += " AND m.role = ?"
            params.append(args.role)
        sql += " ORDER BY bm25(messages_fts) LIMIT ?"
        params.append(args.limit)
        rows = conn.execute(sql, params).fetchall()
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


def cmd_selfcheck(args) -> int:
    """Prove this copy does not silently discard transcripts.

    Subagent transcripts carry their PARENT's sessionId. A copy that keys
    conversations on session id alone lets each file overwrite the last, and
    still reports the full ingest count — the loss is invisible in the output.

    This builds that exact situation and checks the messages survive, so any
    copy of this tool, on any branch, can test itself in one command.
    """
    import tempfile

    session = "SELFCHECK-SESSION"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "subagents").mkdir()
        line = {"type": "user", "sessionId": session, "timestamp": "2026-01-01T00:00:00Z"}
        (root / f"{session}.jsonl").write_text(json.dumps(
            {**line, "uuid": "p1", "message": {"role": "user", "content": "parent line"}}) + "\n")
        (root / "subagents" / "agent-selfcheck.jsonl").write_text(json.dumps(
            {**line, "uuid": "c1", "message": {"role": "user", "content": "subagent line"}}) + "\n")
        # KI-2 fixture: a tool RESULT, which Claude Code also writes as a
        # user-typed record. It must not be stored as the owner speaking.
        (root / f"{session}.jsonl").write_text(
            (root / f"{session}.jsonl").read_text() + json.dumps(
                {**line, "uuid": "t1", "message": {"role": "user", "content": [
                    {"type": "tool_result", "content": "selfcheck tool output"}]}}) + "\n")

        report = Report()
        conversations: list[Conversation] = []
        for path in sorted(root.rglob("*.jsonl")):
            conversations += parse_claude_code_jsonl(path, report)

        conn = connect(root / "selfcheck.db")
        store(conn, conversations, Report())
        convs = conn.execute("SELECT COUNT(*) n FROM conversations").fetchone()["n"]
        msgs = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        as_user = conn.execute(
            "SELECT COUNT(*) n FROM messages WHERE role = 'user'").fetchone()["n"]
        conn.close()

    print(f"two transcripts sharing sessionId {session!r}, plus one tool result:")
    print(f"  conversations stored: {convs} (expected 2)")
    print(f"  messages stored:      {msgs} (expected 3)")
    print(f"  filed as the owner:   {as_user} (expected 2 — the tool result is not the owner)")

    if convs == 2 and msgs == 3 and as_user == 2:
        print("\nOK — this copy keeps both transcripts and attributes tool output correctly.")
        return 0

    if as_user > 2 and convs == 2 and msgs == 3:
        print("\nFAIL — this copy files TOOL OUTPUT AS THE OWNER SPEAKING (KI-2).")
        print()
        print("Claude Code writes tool results as `type: \"user\"` records. Taken at")
        print("face value, every command's output is indexed as something the owner")
        print("said, and a search for what they asked for returns mostly log lines.")
        print()
        print("Fix: derive the role from the content blocks in parse_claude_code_jsonl:")
        print()
        print("    role=effective_role(message.get(\"role\") or record[\"type\"], kinds),")
        print()
        print("where effective_role returns \"tool_result\" when every content block")
        print("is a tool_result. Re-ingest afterwards; stored roles do not correct")
        print("themselves.")
        return 1

    print("\nFAIL — this copy SILENTLY DISCARDS transcripts.")
    print()
    print("Every subagent transcript shares its parent's sessionId, so on a real")
    print("history this loses most of it while still reporting a full count.")
    print("Ingested indexes built with this copy are incomplete and the numbers")
    print("they reported cannot be trusted.")
    print()
    print("Fix: in parse_claude_code_jsonl, key the conversation on the session")
    print("AND the transcript file, not the session alone:")
    print()
    print('    key = session if path.stem == session else f"{session}:{path.stem}"')
    print()
    print("then group and build ids from `key`. Re-ingest afterwards; the stored")
    print("counts do not correct themselves.")
    return 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db", default=str(DEFAULT_DB), help="index database path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="read archive/ into the index")
    p_ingest.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_ingest.add_argument(
        "--include-projects", action="store_true",
        help="also index every Claude Code transcript under --projects-dir. On your "
             "own machine that is your whole Claude Code history.")
    p_ingest.add_argument("--projects-dir", default=str(CLAUDE_PROJECTS))
    p_ingest.set_defaults(func=cmd_ingest)

    p_search = sub.add_parser("search", help="full-text search the index")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument(
        "--role",
        choices=("user", "assistant", "tool_result"),
        help="restrict to one role; `user` is the owner's own words, with tool "
             "output filed separately under `tool_result`",
    )
    p_search.set_defaults(func=cmd_search)

    sub.add_parser("stats", help="index summary").set_defaults(func=cmd_stats)

    sub.add_parser(
        "selfcheck",
        help="verify this copy does not silently discard transcripts",
    ).set_defaults(func=cmd_selfcheck)

    p_show = sub.add_parser("show", help="print one conversation in full")
    p_show.add_argument("conversation_id")
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
