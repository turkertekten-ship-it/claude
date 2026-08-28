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
        # Sidecar record types carry no message and must be ignored, not skipped.
        {"type": "attachment", "uuid": "x1", "sessionId": "S1"},
        {"type": "user", "uuid": "u2", "sessionId": "S2", "timestamp": "2026-01-02T00:00:00Z",
         "message": {"role": "user", "content": "second session entirely"}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n{ broken json\n")
    return verbatim


def subagent_transcript_cases() -> None:
    """Two transcripts sharing a session id must both survive storage.

    Subagent transcripts carry their PARENT's sessionId. Keying a conversation
    on the session alone collapses every transcript of a session onto one id,
    and each file overwrites the last. The loss is silent: the run reports what
    it READ, not what survived, so an affected copy prints a healthy count over
    a mostly-empty index.

    Reported against this repository as KI-1 (issue #1), reproduced here before
    fixing: 12 messages on disk, "Indexed 12 message(s) across 2
    conversation(s)", 5 stored.
    """
    print("subagent transcript cases")
    import sqlite3

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        archive = root / "archive"
        archive.mkdir()
        session = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

        def record(text: str, i: int) -> str:
            return json.dumps({
                "sessionId": session, "uuid": f"t{i}", "type": "user",
                "timestamp": f"2026-01-01T00:00:{i:02d}Z",
                "message": {"role": "user", "content": text},
            })

        (archive / f"{session}.jsonl").write_text(
            "\n".join(record(f"parent {i}", i) for i in range(5)), encoding="utf-8")
        (archive / "11111111-2222-3333-4444-555555555555.jsonl").write_text(
            "\n".join(record(f"subagent {i}", i + 50) for i in range(7)), encoding="utf-8")

        db = root / "index.db"
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        connection = sqlite3.connect(db)
        try:
            messages = connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            conversations = connection.execute(
                "SELECT COUNT(*) FROM conversations").fetchone()[0]
            subagent_kept = connection.execute(
                "SELECT COUNT(*) FROM messages WHERE text LIKE 'subagent%'").fetchone()[0]
        finally:
            connection.close()

    check("every message on disk is stored, not just the ones read",
          messages == 12, f"stored {messages} of 12")
    check("the two transcripts stay two conversations",
          conversations == 2, f"got {conversations}")
    check("the subagent transcript is not overwritten by its parent",
          subagent_kept == 7, f"kept {subagent_kept} of 7")


def selfcheck_cases() -> None:
    """The selfcheck must pass a sound copy and fail one with the defect.

    A guard nobody has watched reject is a hope. This reinstates exactly the
    one line the fix changed, in a copy of the tool, and requires the check to
    catch it.
    """
    print("selfcheck cases")
    import shutil
    import subprocess

    tool = REPO / "tools" / "ingest_chat_archive.py"
    ok = subprocess.run([sys.executable, str(tool), "selfcheck"],
                        capture_output=True, text=True)
    check("selfcheck passes on this copy", ok.returncode == 0, ok.stderr[:160])

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(tool.parent, root / "tools")
        broken = root / "tools" / tool.name
        source = broken.read_text(encoding="utf-8")
        # Only the assignment, matched with its indentation. The same text also
        # appears inside the diagnostic the check prints, and blanket-replacing
        # it would silently gut the very message this test asserts on -- which
        # is what happened on the first attempt.
        defect = ('\n        key = session if path.stem == session '
                  'else f"{session}:{path.stem}"\n')
        assert defect in source, "the fix line moved; update this test"
        broken.write_text(source.replace(defect, "\n        key = session\n"),
                          encoding="utf-8")
        bad = subprocess.run([sys.executable, str(broken), "selfcheck"],
                             capture_output=True, text=True)
    check("selfcheck FAILS a copy with only the fix line reverted",
          bad.returncode == 1, f"exit {bad.returncode}")
    check("and it names the change that fixes it",
          "path.stem" in bad.stderr, bad.stderr[:160])


def message_identity_cases() -> None:
    """A message belongs to one conversation, and search counts it once.

    The messages primary key was the record uuid alone, while store() clears
    stale rows by conversation_id. So the same uuid arriving under a second
    conversation MOVED the row: the first conversation kept its message_count
    and lost the message, and messages_fts accumulated a duplicate per move --
    one message, two search hits. Reproduced before fixica.
    """
    print("message identity")
    import tempfile

    def conv(cid: str, mid: str):
        c = ica.Conversation(id=cid, kind="claude_code", title=None, source_file="f.jsonl")
        c.messages.append(ica.Message(id=mid, seq=0, role="user",
                                      text="the same message body", timestamp=None,
                                      block_types="text", source_file="f.jsonl"))
        return c

    with tempfile.TemporaryDirectory() as tmp:
        conn = ica.connect(Path(tmp) / "t.db")
        report = ica.Report()
        ica.store(conn, [conv("cc:A", "cc:A:u1")], report)
        ica.store(conn, [conv("cc:B", "cc:B:u1")], report)
        rows = conn.execute("SELECT id, conversation_id FROM messages").fetchall()
        check("both conversations keep their own message", len(rows) == 2, str(len(rows)))
        counts = dict(conn.execute("SELECT id, message_count FROM conversations").fetchall())
        check("neither conversation claims a message it lost",
              counts == {"cc:A": 1, "cc:B": 1}, str(counts))
        hits = conn.execute("SELECT count(*) FROM messages_fts WHERE messages_fts "
                            "MATCH 'same'").fetchone()[0]
        check("search returns one hit per message", hits == 2, str(hits))

        ica.store(conn, [conv("cc:A", "cc:A:u1")], report)
        hits = conn.execute("SELECT count(*) FROM messages_fts WHERE messages_fts "
                            "MATCH 'same'").fetchone()[0]
        check("re-ingesting a conversation does not duplicate it", hits == 2, str(hits))


def main() -> int:
    subagent_transcript_cases()
    selfcheck_cases()
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
        # `cc:S1:t`, not `cc:S1`: the transcript file is t.jsonl and its stem
        # does not match the session id, so the conversation is keyed on both.
        # That is the fix for KI-1 -- a subagent transcript carries its parent's
        # sessionId, and keying on the session alone let one file overwrite
        # another. A compound key here is the visible cost of that.
        s1 = by_id["cc:S1:t"]
        check("sidecar records are not indexed as messages", len(s1.messages) == 2, len(s1.messages))
        check("text is stored verbatim", s1.messages[0].text == verbatim, repr(s1.messages[0].text))
        check("block types are recorded",
              s1.messages[1].block_types == "thinking,text,tool_use", s1.messages[1].block_types)
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
        check("all readable messages are indexed", total == 5, total)

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
        check("re-ingesting does not duplicate messages", again == 5, again)
        check("re-ingesting does not duplicate the search index", fts == 5, fts)
        conn.close()

    message_identity_cases()

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
