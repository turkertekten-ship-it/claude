"""Tests for the chat transcript source.

Every fixture is built inside a TemporaryDirectory: this source's whole job is
reading a home directory, so a test that touched the real one would be both
flaky and rude.
"""

from __future__ import annotations

import json
import os
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from oodarag.reflect.models import (
    ACTOR_ASSISTANT,
    ACTOR_HUMAN,
    KIND_PROMPT,
    KIND_REPLY,
    Signal,
)
from oodarag.reflect.sources.base import Budget
from oodarag.reflect.sources.transcripts import ChatTranscriptSource, default_roots

CLAUDE_TS = "2026-08-20T10:00:00.500Z"
CLAUDE_EPOCH = datetime(2026, 8, 20, 10, 0, 0, 500_000, tzinfo=UTC).timestamp()


def write_lines(path: Path, records: list[object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(r if isinstance(r, str) else json.dumps(r) for r in records)
    path.write_text(body + "\n", encoding="utf-8")
    return path


def collect(source: ChatTranscriptSource, since: float = 0.0, budget: Budget | None = None):
    return source.run(since=since, budget=budget)


class ClaudeCodeFormatTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projects"
        self.session = write_lines(
            self.root / "-home-user-claude" / "aaaa-bbbb-cccc.jsonl",
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "add a make target for the tests"},
                    "timestamp": CLAUDE_TS,
                    "sessionId": "S1",
                    "cwd": "/home/user/claude",
                    "uuid": "u1",
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "model": "claude-opus-5",
                        "content": [
                            {"type": "text", "text": "Running it now."},
                            {
                                "type": "tool_use",
                                "name": "Bash",
                                "input": {"command": "make test", "blob": "x" * 5000},
                            },
                            {"type": "tool_use", "name": "Read", "input": {"file": "a.py"}},
                            {"type": "thinking", "thinking": "internal monologue"},
                            {"type": "text", "text": "Done."},
                        ],
                    },
                    "timestamp": "2026-08-20T10:00:05Z",
                    "sessionId": "S1",
                },
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [{"type": "tool_result", "content": "y" * 4000}],
                    },
                    "timestamp": "2026-08-20T10:00:06Z",
                    "sessionId": "S1",
                },
                {
                    "type": "user",
                    "message": {"role": "user", "content": "<command-name>/clear</command-name>"},
                    "timestamp": "2026-08-20T10:00:07Z",
                    "sessionId": "S1",
                },
                {"type": "summary", "summary": "not a turn at all"},
                {
                    "type": "user",
                    "message": {"role": "user", "content": "and now update the README"},
                    "timestamp": "2026-08-20T10:00:08Z",
                    "sessionId": "S1",
                },
            ],
        )
        self.result = collect(ChatTranscriptSource(roots=[self.root]))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_emits_prompt_and_reply_only(self) -> None:
        kinds = [(s.kind, s.actor) for s in self.result.signals]
        self.assertEqual(
            kinds,
            [
                (KIND_PROMPT, ACTOR_HUMAN),
                (KIND_REPLY, ACTOR_ASSISTANT),
                (KIND_PROMPT, ACTOR_HUMAN),
            ],
        )
        self.assertEqual(self.result.errors, [])

    def test_tool_payloads_dropped_names_kept(self) -> None:
        reply = self.result.signals[1]
        self.assertEqual(reply.text, "Running it now.\nDone.")
        self.assertNotIn("make test", reply.text)
        self.assertNotIn("internal monologue", reply.text)
        self.assertEqual(reply.metadata["tools"], ["Bash", "Read"])

    def test_metadata_and_uri(self) -> None:
        first = self.result.signals[0]
        # This fixture's file is not named after its sessionId, so the key is
        # disambiguated by file. See TestSessionKeyDisambiguation for why.
        self.assertEqual(first.session, "S1:aaaa-bbbb-cccc")
        self.assertEqual(first.metadata["cwd"], "/home/user/claude")
        self.assertEqual(first.metadata["project"], "-home-user-claude")
        self.assertEqual(first.metadata["file"], str(self.session))
        self.assertEqual(first.metadata["turn"], 0)
        self.assertEqual(first.uri, f"{self.session}#L1")
        self.assertEqual(self.result.signals[1].metadata["model"], "claude-opus-5")
        self.assertEqual(self.result.signals[2].uri, f"{self.session}#L6")

    def test_timestamp_parsed_from_iso_with_z(self) -> None:
        self.assertAlmostEqual(self.result.signals[0].ts, CLAUDE_EPOCH, places=3)

    def test_synthetic_turns_are_not_emitted(self) -> None:
        texts = " ".join(s.text for s in self.result.signals)
        self.assertNotIn("command-name", texts)
        self.assertNotIn("yyyy", texts)  # the tool_result body
        self.assertEqual(len(self.result.signals), 3)

    def test_skipped_counter(self) -> None:
        source = ChatTranscriptSource(roots=[self.root])
        source.run()
        # the tool_result-only turn and the /clear envelope; the summary record
        # is not a turn at all and so is not counted.
        self.assertEqual(source.skipped, 2)

    def test_ordinals_are_monotonic_and_positional(self) -> None:
        ordinals = [s.ordinal for s in self.result.signals]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(len(set(ordinals)), len(ordinals))
        self.assertEqual(ordinals, [0, 1, 5])


class GenericFormatsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name) / "history"
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_generic_jsonl(self) -> None:
        path = write_lines(
            self.root / "chat-2026.jsonl",
            [
                {"role": "user", "content": "why is the index rebuilt", "ts": 1_756_300_000},
                {"role": "assistant", "content": "the cursor is not kept", "ts": 1_756_300_010},
                {"role": "system", "content": "you are a helpful assistant", "ts": 1_756_300_020},
            ],
        )
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertEqual(len(result.signals), 2)
        self.assertEqual(result.signals[0].session, "chat-2026")
        self.assertEqual(result.signals[0].ts, 1_756_300_000)
        self.assertEqual(result.signals[0].uri, f"{path}#L1")
        self.assertEqual(result.signals[1].kind, KIND_REPLY)

    def test_millisecond_epoch_is_rescaled(self) -> None:
        write_lines(
            self.root / "ms.jsonl", [{"role": "user", "content": "hi", "ts": 1_756_300_000_000}]
        )
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertEqual(result.signals[0].ts, 1_756_300_000)

    def test_json_document_list(self) -> None:
        path = self.root / "export.json"
        path.write_text(
            json.dumps(
                [
                    {"role": "user", "content": "rename the module", "ts": 1_756_300_000},
                    {"role": "assistant", "content": [{"type": "text", "text": "ok"}]},
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertEqual([s.text for s in result.signals], ["rename the module", "ok"])
        self.assertEqual(result.signals[0].session, "export")
        self.assertEqual([s.ordinal for s in result.signals], [0, 1])

    def test_json_document_messages_wrapper(self) -> None:
        path = self.root / "wrapped.json"
        path.write_text(
            json.dumps({"sessionId": "s", "messages": [{"role": "user", "content": "x y z"}]}),
            encoding="utf-8",
        )
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertEqual(len(result.signals), 1)
        self.assertEqual(result.signals[0].text, "x y z")
        # No timestamp anywhere: the file's mtime stands in for one.
        self.assertAlmostEqual(result.signals[0].ts, path.stat().st_mtime, places=3)


class HostileInputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projects"
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_torn_and_junk_lines_lose_only_their_turn(self) -> None:
        path = self.root / "torn.jsonl"
        write_lines(
            path,
            [
                {"role": "user", "content": "first instruction"},
                '{"role": "user", "content": "half written',
                "not json at all",
                "[1, 2, 3]",
                {"role": "user", "content": "second instruction"},
            ],
        )
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertEqual(
            [s.text for s in result.signals], ["first instruction", "second instruction"]
        )
        self.assertEqual([s.uri for s in result.signals], [f"{path}#L1", f"{path}#L5"])
        self.assertEqual(result.errors, [])

    def test_unknown_shapes_never_raise(self) -> None:
        path = self.root / "weird.jsonl"
        write_lines(
            path,
            [
                {"role": "user", "content": 12345},
                {"role": "user", "content": [1, 2, {"no_type": True}, {"text": "kept anyway"}]},
                {"role": "user", "content": {"type": "text", "text": "dict content"}},
                {"role": "user", "message": "a string where a dict was expected"},
                {"role": "user", "content": "   "},
                {"role": "user", "content": "<local-command-stdout>ok</local-command-stdout>"},
                {"role": "user", "content": "<system-reminder>ignore this</system-reminder>"},
                {"role": "user", "content": "good turn", "timestamp": "yesterday-ish"},
                [],
                None,
            ],
        )
        source = ChatTranscriptSource(roots=[self.root])
        result = source.run()
        self.assertEqual(
            [s.text for s in result.signals], ["kept anyway", "dict content", "good turn"]
        )
        # Unreadable timestamp -> the file's mtime, not a lost signal.
        self.assertAlmostEqual(result.signals[-1].ts, path.stat().st_mtime, places=3)
        self.assertGreaterEqual(source.skipped, 4)
        self.assertEqual(result.errors, [])

    def test_secrets_are_redacted_on_the_way_out(self) -> None:
        write_lines(
            self.root / "leak.jsonl",
            [{"role": "user", "content": "use sk-ant-" + "A" * 24 + " for the call"}],
        )
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertIn("<redacted:anthropic-key>", result.signals[0].text)
        self.assertNotIn("AAAA", result.signals[0].text)

    def test_binary_and_empty_files_are_ignored(self) -> None:
        (self.root / "blob.jsonl").write_bytes(b"\x00\x01\x02binary junk")
        (self.root / "empty.jsonl").write_text("", encoding="utf-8")
        result = collect(ChatTranscriptSource(roots=[self.root]))
        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])


class WindowAndBudgetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projects"
        self.root.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_since_skips_whole_stale_files(self) -> None:
        stale = write_lines(self.root / "old.jsonl", [{"role": "user", "content": "last month"}])
        os.utime(stale, (1_700_000_000, 1_700_000_000))
        write_lines(self.root / "fresh.jsonl", [{"role": "user", "content": "tonight"}])
        result = collect(ChatTranscriptSource(roots=[self.root]), since=time.time() - 3600)
        self.assertEqual([s.text for s in result.signals], ["tonight"])

    def test_since_skips_individual_old_turns(self) -> None:
        write_lines(
            self.root / "mixed.jsonl",
            [
                {"role": "user", "content": "before the window", "ts": 1_756_000_000},
                {"role": "user", "content": "inside the window", "ts": 1_756_900_000},
            ],
        )
        result = collect(ChatTranscriptSource(roots=[self.root]), since=1_756_500_000)
        self.assertEqual([s.text for s in result.signals], ["inside the window"])

    def test_max_signals_truncates(self) -> None:
        write_lines(
            self.root / "many.jsonl",
            [{"role": "user", "content": f"turn {i}"} for i in range(10)],
        )
        result = collect(ChatTranscriptSource(roots=[self.root]), budget=Budget(max_signals=3))
        self.assertEqual(len(result.signals), 3)
        self.assertTrue(result.truncated)

    def test_long_turn_is_clipped_to_budget(self) -> None:
        write_lines(self.root / "long.jsonl", [{"role": "user", "content": "z" * 5000}])
        result = collect(
            ChatTranscriptSource(roots=[self.root]), budget=Budget(max_chars_per_signal=100)
        )
        self.assertTrue(result.signals[0].text.endswith("[truncated]"))
        self.assertLess(len(result.signals[0].text), 200)

    def test_expired_budget_stops_before_reading(self) -> None:
        write_lines(self.root / "any.jsonl", [{"role": "user", "content": "never read"}])
        spent = Budget(wall_clock_s=0.001, started=time.monotonic() - 100.0)
        result = collect(ChatTranscriptSource(roots=[self.root]), budget=spent)
        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])


class RootsTest(unittest.TestCase):
    def test_available_requires_a_root(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nowhere"
            self.assertFalse(ChatTranscriptSource(roots=[missing]).available())
            missing.mkdir()
            self.assertTrue(ChatTranscriptSource(roots=[missing]).available())

    def test_unavailable_source_returns_empty_result(self) -> None:
        with TemporaryDirectory() as tmp:
            source = ChatTranscriptSource(roots=[Path(tmp) / "nowhere"])
            result = source.run()
            self.assertEqual(result.key, "chat:transcripts")
            self.assertEqual(result.signals, [])

    def test_default_roots_follow_home_and_env(self) -> None:
        with TemporaryDirectory() as tmp, TemporaryDirectory() as extra:
            env = {"HOME": tmp, "USERPROFILE": tmp, "OODARAG_CHAT_ROOTS": extra}
            with mock.patch.dict(os.environ, env, clear=False):
                roots = default_roots()
                self.assertIn(Path(tmp) / ".claude" / "projects", roots)
                self.assertIn(Path(extra), roots)
                write_lines(
                    Path(tmp) / ".claude" / "projects" / "proj" / "s.jsonl",
                    [{"role": "user", "content": "found via the default root"}],
                )
                source = ChatTranscriptSource()
                self.assertTrue(source.available())
                result = source.run()
        self.assertEqual([s.text for s in result.signals], ["found via the default root"])


if __name__ == "__main__":
    unittest.main()


class TestProvenanceFiltering(unittest.TestCase):
    """Only the user's own words may become a `prompt` signal.

    This is the asymmetry the whole feature rests on. A dropped turn costs one
    observation out of thousands. A synthetic turn treated as an instruction
    gets written into the user's conventions file as something they never said -
    and the loop then defends it, because it is evidence.
    """

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, relative: str, records: list[dict]) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")

    def turn(self, text: str, **extra) -> dict:
        record = {
            "type": "user", "userType": "external", "isSidechain": False,
            "timestamp": "2026-08-27T10:00:00Z", "sessionId": "s1",
            "message": {"role": "user", "content": text},
        }
        record.update(extra)
        return record

    def prompts(self) -> list[Signal]:
        source = ChatTranscriptSource(roots=[self.root])
        result = source.run(since=0, budget=Budget())
        return [s for s in result.signals if s.kind == KIND_PROMPT]

    def test_subagent_directories_are_not_walked(self) -> None:
        self.write("proj/real.jsonl", [self.turn("please always use tabs")])
        self.write("proj/subagents/workflows/wf1/agent-a.jsonl",
                   [self.turn("You are implementing part of the subsystem")])
        texts = [s.text for s in self.prompts()]
        self.assertEqual(texts, ["please always use tabs"])

    def test_sidechain_turns_are_dropped(self) -> None:
        self.write("proj/s.jsonl", [
            self.turn("a real instruction"),
            self.turn("an orchestrator brief", isSidechain=True),
        ])
        self.assertEqual([s.text for s in self.prompts()], ["a real instruction"])

    def test_non_external_user_type_is_dropped(self) -> None:
        self.write("proj/s.jsonl", [
            self.turn("a real instruction"),
            self.turn("injected", userType="internal"),
        ])
        self.assertEqual([s.text for s in self.prompts()], ["a real instruction"])

    def test_meta_turns_are_dropped(self) -> None:
        self.write("proj/s.jsonl", [
            self.turn("a real instruction"),
            self.turn("A session-scoped hook is now active", isMeta=True),
        ])
        self.assertEqual([s.text for s in self.prompts()], ["a real instruction"])

    def test_slash_command_arguments_survive_the_envelope(self) -> None:
        """A slash command is the most deliberate input in a session."""
        envelope = (
            "<command-name>/goal</command-name>\n"
            "<command-message>goal</command-message>\n"
            "<command-args>always run the linter before pushing</command-args>"
        )
        self.write("proj/s.jsonl", [self.turn(envelope, isMeta=True)])
        found = self.prompts()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].text, "always run the linter before pushing")
        self.assertEqual(found[0].metadata.get("command"), "/goal")

    def test_slash_command_without_arguments_is_dropped(self) -> None:
        envelope = "<command-name>/clear</command-name>\n<command-args></command-args>"
        self.write("proj/s.jsonl", [self.turn(envelope)])
        self.assertEqual(self.prompts(), [])

    def test_a_sidechain_slash_command_is_still_agent_traffic(self) -> None:
        """Who spoke outranks what the envelope contains."""
        envelope = "<command-name>/goal</command-name><command-args>do a thing</command-args>"
        self.write("proj/s.jsonl", [self.turn(envelope, isSidechain=True)])
        self.assertEqual(self.prompts(), [])


class TestSessionKeyDisambiguation(unittest.TestCase):
    """Two transcript files can claim the same session id.

    A subagent transcript records its *parent's* sessionId. Keyed on the id
    alone, several files collapse into one conversation - and the sequence rules
    then read adjacency across a boundary that does not exist:
    `friction.reformulation` comparing a prompt in one file against a prompt in
    another, `friction.correction` treating a prompt as repairing a reply it
    never saw. Both yield confident findings about a conversation that never
    happened.

    Reported against a sibling tool in this repository as issue #1, where the
    same pattern caused each file to overwrite the last in storage. This source
    stores nothing, so the symptom differs, but the key was equally wrong.
    """

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, session_id: str, prompts: list[str]) -> None:
        records = []
        for text in prompts:
            records.append({
                "type": "user", "userType": "external", "isSidechain": False,
                "sessionId": session_id, "timestamp": "2026-08-27T10:00:00Z",
                "message": {"role": "user", "content": text},
            })
        (self.root / name).write_text(
            "\n".join(json.dumps(r) for r in records), encoding="utf-8")

    def sessions(self) -> dict[str, list[str]]:
        result = ChatTranscriptSource(roots=[self.root]).run(since=0, budget=Budget())
        out: dict[str, list[str]] = {}
        for sig in result.signals:
            out.setdefault(sig.session, []).append(sig.text)
        return out

    def test_two_files_sharing_a_session_id_stay_separate(self) -> None:
        self.write("parent.jsonl", "S1", ["first conversation"])
        self.write("child.jsonl", "S1", ["second conversation"])
        sessions = self.sessions()
        self.assertEqual(len(sessions), 2, f"collapsed into: {sorted(sessions)}")
        self.assertEqual(sorted(sessions), ["S1:child", "S1:parent"])

    def test_a_file_named_after_its_session_keeps_the_bare_id(self) -> None:
        """The common case: Claude Code names the file for the session."""
        self.write("S1.jsonl", "S1", ["only conversation"])
        self.assertEqual(sorted(self.sessions()), ["S1"])

    def test_a_record_without_a_session_id_falls_back_to_the_file(self) -> None:
        (self.root / "loose.jsonl").write_text(
            json.dumps({"role": "user", "content": "no session id here"}), encoding="utf-8")
        self.assertEqual(sorted(self.sessions()), ["loose"])
