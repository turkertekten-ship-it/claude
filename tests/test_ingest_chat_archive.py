#!/usr/bin/env python3
"""Tests for the chat-archive ingester.

The cases that matter are the honesty ones: an empty archive must stay empty,
malformed records must be skipped and counted rather than repaired, and stored
text must come back byte-identical so a search hit can be quoted as evidence.

Fixtures here are synthetic ON PURPOSE and live only under tests/. They are
never written to the live index.

Run: python3 tests/test_ingest_chat_archive.py
"""

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import ingest_chat_archive as ica  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail="") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


class Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def write_cc_transcript(path: Path) -> str:
    verbatim = "Keep   this  text\n\texactly as-is — em dash, tabs and all."
    rows = [
        {"type": "user", "uuid": "u1", "sessionId": "S1", "timestamp": "2026-01-01T00:00:00Z",
         "message": {"role": "user", "content": verbatim}},
        {"type": "assistant", "uuid": "a1", "sessionId": "S1", "timestamp": "2026-01-01T00:00:05Z",
         "message": {"role": "assistant", "content": [
             {"type": "thinking", "thinking": "internal reasoning"},
             {"type": "text", "text": "answer about vector databases"},
             {"type": "tool_use", "name": "Bash"},
         ]}},
        # Claude Code files tool OUTPUT as a user-typed record. Taken at face
        # value this lands command output in the index as something the owner
        # said, which is exactly what the index must not do.
        {"type": "user", "uuid": "u_tool", "sessionId": "S1",
         "timestamp": "2026-01-01T00:00:04Z",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "content": "rebuilt in 3.2s; tabs preserved exactly"},
         ]}},
        # Sidecar record types carry no message and must be ignored, not skipped.
        {"type": "attachment", "uuid": "x1", "sessionId": "S1"},
        {"type": "user", "uuid": "u2", "sessionId": "S2", "timestamp": "2026-01-02T00:00:00Z",
         "message": {"role": "user", "content": "second session entirely"}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n{ broken json\n")
    return verbatim


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        archive = tmp / "archive"
        archive.mkdir()
        db = tmp / "index.db"

        print("empty-archive cases")
        rc = ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        check("empty archive exits 0", rc == 0, rc)
        check("empty archive creates no index", not db.exists())

        print("claude code transcript cases")
        verbatim = write_cc_transcript(archive / "t.jsonl")
        report = ica.Report()
        convs = ica.parse_claude_code_jsonl(archive / "t.jsonl", report)
        check("sessions are split into separate conversations", len(convs) == 2, len(convs))
        check("malformed line is skipped", report.skipped == 1, report.skipped)
        check("skip is explained", bool(report.problems), report.problems)

        by_id = {c.id: c for c in convs}
        s1 = by_id["cc:S1"]
        check("sidecar records are not indexed as messages", len(s1.messages) == 3, len(s1.messages))
        check("text is stored verbatim", s1.messages[0].text == verbatim, repr(s1.messages[0].text))
        check("block types are recorded",
              s1.messages[1].block_types == "thinking,text,tool_use", s1.messages[1].block_types)

        by_role = {m.id: m.role for m in s1.messages}
        check("tool output is not filed as the owner speaking",
              by_role["cc:u_tool"] == "tool_result", by_role["cc:u_tool"])
        check("a genuine user message keeps the user role",
              by_role["cc:u1"] == "user", by_role["cc:u1"])
        check("tool output is still stored verbatim and searchable",
              "rebuilt in 3.2s" in s1.messages[2].text, s1.messages[2].text)
        check("thinking and text are both captured",
              "internal reasoning" in s1.messages[1].text
              and "vector databases" in s1.messages[1].text)
        check("timestamps bound the conversation",
              s1.started_at == "2026-01-01T00:00:00Z" and s1.ended_at == "2026-01-01T00:00:05Z")
        check("provenance is retained on every message",
              all(m.source_file and m.id for m in s1.messages))

        print("claude.ai export cases")
        (archive / "conversations.json").write_text(json.dumps([
            {"uuid": "C1", "name": "Titled chat", "chat_messages": [
                {"uuid": "m1", "sender": "human", "text": "exported question",
                 "created_at": "2026-02-01T00:00:00Z"},
                {"uuid": "m2", "sender": "assistant", "text": "exported answer",
                 "created_at": "2026-02-01T00:00:09Z"},
            ]},
            {"name": "no id at all", "chat_messages": []},
            "not an object",
        ]))
        report2 = ica.Report()
        exported = ica.parse_claude_ai_export(archive / "conversations.json", report2)
        check("well-formed export conversation is read", len(exported) == 1, len(exported))
        check("conversation title is kept", exported[0].title == "Titled chat")
        check("idless and non-object records are skipped", report2.skipped == 2, report2.skipped)

        print("index and search cases")
        rc = ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        check("parse failures make ingest exit 1", rc == 1, rc)
        conn = ica.connect(db)
        total = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        check("all readable messages are indexed", total == 6, total)

        hits = conn.execute(
            "SELECT m.text FROM messages_fts f JOIN messages m ON m.id = f.message_id"
            " WHERE messages_fts MATCH 'vector'").fetchall()
        check("full-text search finds a message", len(hits) == 1, len(hits))
        check("search returns the verbatim stored text",
              "vector databases" in hits[0]["text"])
        conn.close()

        print("idempotence cases")
        ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        conn = ica.connect(db)
        again = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        fts = conn.execute("SELECT COUNT(*) n FROM messages_fts").fetchone()["n"]
        check("re-ingesting does not duplicate messages", again == 6, again)
        check("re-ingesting does not duplicate the search index", fts == 6, fts)
        conn.close()

        print("role-filter cases")
        # 'tabs' appears in the owner's real message AND in the tool output, so
        # the filter has to keep one and drop the other rather than match nothing.
        conn = ica.connect(db)
        unfiltered = conn.execute(
            "SELECT COUNT(*) n FROM messages_fts f JOIN messages m ON m.id = f.message_id"
            " WHERE messages_fts MATCH 'tabs'").fetchone()["n"]
        as_user = conn.execute(
            "SELECT m.id FROM messages_fts f JOIN messages m ON m.id = f.message_id"
            " WHERE messages_fts MATCH 'tabs' AND m.role = 'user'").fetchall()
        conn.close()
        check("the term matches both the owner and the tool output",
              unfiltered == 2, unfiltered)
        check("filtering to the owner keeps exactly the real message",
              [r["id"] for r in as_user] == ["cc:u1"], [r["id"] for r in as_user])
        rc = ica.cmd_search(Args(db=str(db), query="tabs", limit=10, role="user"))
        check("search accepts a role filter and exits clean", rc == 0, rc)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
