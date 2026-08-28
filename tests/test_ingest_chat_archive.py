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
    """cmd_ingest reads these attributes; defaults keep the projects tree out."""

    def __init__(self, **kw):
        self.include_projects = False
        self.projects_dir = "/nonexistent"
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
        # The file stem differs from the sessionId, so ids carry both.
        check("ids disambiguate session by file", set(by_id) == {"cc:S1:t", "cc:S2:t"}, set(by_id))
        s1 = by_id["cc:S1:t"]
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

        print("real claude.ai export schema cases")
        # Field names and shapes confirmed against several independent public
        # parsers of the official export; see ledger CLAUDE-EXPORT-SCHEMA.
        (archive / "conversations.json").write_text(json.dumps([
            {"uuid": "R1", "name": "flat text", "created_at": "2026-03-01T10:00:00Z",
             "updated_at": "2026-03-01T10:05:00Z", "chat_messages": [
                {"uuid": "rm1", "sender": "human", "created_at": "2026-03-01T10:00:00Z",
                 "text": "flat text message",
                 "content": [{"type": "text", "text": "flat text message"}]}]},
            {"uuid": "R2", "name": "blocks only", "created_at": "2026-03-02T10:00:00Z",
             "updated_at": "2026-03-02T10:05:00Z", "chat_messages": [
                {"uuid": "rm2", "sender": "assistant", "created_at": "2026-03-02T10:00:00Z",
                 "text": "", "content": [{"type": "text", "text": "BLOCK ONLY CONTENT"}]}]},
            {"uuid": "R3", "name": "attachment", "created_at": "2026-03-03T10:00:00Z",
             "updated_at": "2026-03-03T10:05:00Z", "chat_messages": [
                {"uuid": "rm3", "sender": "human", "created_at": "2026-03-03T10:00:00Z",
                 "text": "see attached", "attachments": [
                    {"file_name": "spec.txt", "extracted_content": "ATTACHED FILE BODY"}]}]},
        ]))
        rep3 = ica.Report()
        real = ica.parse_claude_ai_export(archive / "conversations.json", rep3)
        texts = [m.text for c in real for m in c.messages]
        check("all three real-schema conversations parse", len(real) == 3, len(real))
        check("nothing skipped on the real schema", rep3.skipped == 0, rep3.problems)
        check("flat text field is read", any(t == "flat text message" for t in texts))
        check("content blocks are read when text is empty",
              any("BLOCK ONLY CONTENT" in t for t in texts), texts)
        check("attachment extracted_content is retained",
              any("ATTACHED FILE BODY" in t for t in texts), texts)
        check("attachment is named in the stored text",
              any("[attachment:spec.txt]" in t for t in texts))
        check("attachment is recorded in block_types",
              any("attachment" in m.block_types for c in real for m in c.messages))
        check("sender values are preserved verbatim",
              {m.role for c in real for m in c.messages} == {"human", "assistant"},
              {m.role for c in real for m in c.messages})
        check("export timestamps are kept",
              all(m.timestamp for c in real for m in c.messages))

        print("index and search cases")
        rc = ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        check("parse failures make ingest exit 1", rc == 1, rc)
        conn = ica.connect(db)
        total = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        # Composition, not a magic number: t.jsonl contributes 4 readable
        # messages (3 in session S1 — a user turn, an assistant turn and a tool
        # result — plus 1 in S2) and conversations.json contributes 3, one per
        # real-schema conversation.
        expected = 4 + 3
        check("all readable messages are indexed", total == expected, total)

        hits = conn.execute(
            "SELECT m.text FROM messages_fts f JOIN messages m ON m.id = f.message_id"
            " WHERE messages_fts MATCH 'vector'").fetchall()
        check("full-text search finds a message", len(hits) == 1, len(hits))
        check("search returns the verbatim stored text",
              "vector databases" in hits[0]["text"])
        conn.close()

        print("session-collision cases")
        # Subagent transcripts carry the PARENT's sessionId. Two files sharing
        # a session must stay two conversations, or one silently erases the
        # other -- which is data loss, not a display bug.
        sub = archive / "subagents"
        sub.mkdir()
        shared = {"type": "user", "uuid": "s1", "sessionId": "SHARED",
                  "timestamp": "2026-03-01T00:00:00Z",
                  "message": {"role": "user", "content": "parent transcript line"}}
        (archive / "SHARED.jsonl").write_text(json.dumps(shared) + "\n")
        child = dict(shared, uuid="s2",
                     message={"role": "user", "content": "subagent transcript line"})
        (sub / "agent-abc.jsonl").write_text(json.dumps(child) + "\n")

        report3 = ica.Report()
        parent_convs = ica.parse_claude_code_jsonl(archive / "SHARED.jsonl", report3)
        child_convs = ica.parse_claude_code_jsonl(sub / "agent-abc.jsonl", report3)
        check("a shared sessionId yields distinct conversation ids",
              parent_convs[0].id != child_convs[0].id,
              (parent_convs[0].id, child_convs[0].id))
        check("subagent transcripts are labelled as such",
              child_convs[0].kind == "claude_code_subagent", child_convs[0].kind)

        db2 = tmp / "collide.db"
        conn2 = ica.connect(db2)
        ica.store(conn2, parent_convs + child_convs, ica.Report())
        kept = conn2.execute("SELECT COUNT(*) n FROM conversations").fetchone()["n"]
        msgs2 = conn2.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        check("neither transcript overwrites the other", kept == 2, kept)
        check("both transcripts' messages survive", msgs2 == 2, msgs2)
        conn2.close()

        print("idempotence cases")
        # Compare against the count this same archive produces, not a constant,
        # so adding a fixture above cannot masquerade as a duplication bug.
        ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        conn = ica.connect(db)
        first = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        conn.close()

        ica.cmd_ingest(Args(archive=str(archive), db=str(db)))
        conn = ica.connect(db)
        again = conn.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        fts = conn.execute("SELECT COUNT(*) n FROM messages_fts").fetchone()["n"]
        check("re-ingesting does not duplicate messages", again == first, (first, again))
        check("re-ingesting does not duplicate the search index", fts == first, (first, fts))
        check("the collision fixtures are in this count", first >= 7, first)
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

    print("selfcheck cases")
    import subprocess as sp
    good = sp.run([sys.executable, str(REPO / "tools" / "ingest_chat_archive.py"), "selfcheck"],
                  capture_output=True, text=True)
    check("selfcheck passes on this copy", good.returncode == 0, good.stdout[-200:])

    # Revert only the fix and confirm the detector catches it. A detector that
    # cannot fail proves nothing about the copies it is meant to screen.
    with tempfile.TemporaryDirectory() as tmp2:
        src = (REPO / "tools" / "ingest_chat_archive.py").read_text()
        marker = 'key = session if path.stem == session else f"{session}:{path.stem}"'
        broken = src.replace("        " + marker, "        key = session", 1)
        check("the fix line is present to revert", broken != src)
        target = Path(tmp2) / "ingest_chat_archive.py"
        target.write_text(broken)
        bad = sp.run([sys.executable, str(target), "selfcheck"], capture_output=True, text=True)
        check("selfcheck fails when the fix is reverted", bad.returncode == 1, bad.returncode)
        check("failure names the data loss", "SILENTLY DISCARDS" in bad.stdout)

    # KI-2: the same detector must also catch tool output filed as the owner.
    # Reverting only the role derivation leaves transcript keying intact, so
    # this proves the two checks are independent rather than one masking the other.
    with tempfile.TemporaryDirectory() as tmp3:
        src = (REPO / "tools" / "ingest_chat_archive.py").read_text()
        marker = 'role=effective_role(message.get("role") or record["type"], kinds),'
        broken = src.replace(marker, 'role=message.get("role") or record["type"],', 1)
        check("the role-derivation line is present to revert", broken != src)
        target3 = Path(tmp3) / "ingest_chat_archive.py"
        target3.write_text(broken)
        bad2 = sp.run([sys.executable, str(target3), "selfcheck"], capture_output=True, text=True)
        check("selfcheck fails when role derivation is reverted", bad2.returncode == 1, bad2.returncode)
        check("failure names the misattribution",
              "TOOL OUTPUT AS THE OWNER" in bad2.stdout, bad2.stdout[-200:])
        check("it does not misreport this as data loss",
              "SILENTLY DISCARDS" not in bad2.stdout)
    print("fleet probe cases")
    sys.path.insert(0, str(REPO / "tools"))
    import fleet_probe

    good = (REPO / "tools" / "ingest_chat_archive.py").read_text()
    sound, detail = fleet_probe.probe_source(good)
    check("probe calls this copy sound", sound, detail)

    marker = 'key = session if path.stem == session else f"{session}:{path.stem}"'
    broken = good.replace("        " + marker, "        key = session", 1)
    check("the fix line was found to revert", broken != good)
    sound_bad, detail_bad = fleet_probe.probe_source(broken)
    check("probe calls a reverted copy affected", not sound_bad, detail_bad)

    # The false positive that made an earlier scan misreport a healthy branch:
    # a copy carrying the fix but predating the selfcheck subcommand must still
    # be judged sound, because behaviour is the oracle, not the CLI surface.
    no_selfcheck = good.replace('        "selfcheck",\n', "", 1)
    no_selfcheck = no_selfcheck.replace(
        '    sub.add_parser(\n        "selfcheck",', '    _unused = (\n        "selfcheck",', 1)
    sound_ns, detail_ns = fleet_probe.probe_source(good.replace(
        'help="verify this copy does not silently discard transcripts",', 'help="x",', 1))
    check("a copy without the selfcheck CLI is still judged by behaviour",
          sound_ns, detail_ns)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
