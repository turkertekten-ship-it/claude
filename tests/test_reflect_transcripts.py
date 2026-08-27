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

from oodarag.reflect.models import ACTOR_ASSISTANT, ACTOR_HUMAN, KIND_PROMPT, KIND_REPLY
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
        self.assertEqual(first.session, "S1")
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
