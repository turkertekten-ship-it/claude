"""Tests for the task-division prompt hook and its installer.

Two properties matter more than the rest, and both are proved by watching the
failure case rather than by reading the code:

- the hook cannot cost anyone a prompt (exit 2 erases it), so it must exit 0 on
  anything it is handed, including nothing at all;
- the installer edits a file the user owns, so it must preserve everything it
  did not put there, and must put its own entry there exactly once.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "tools" / "task_division_hook.py"
INSTALLER = REPO / "tools" / "install_task_division.py"

PAYLOAD = json.dumps(
    {
        "session_id": "abc123",
        "transcript_path": "/tmp/t.jsonl",
        "cwd": "/home/user/project",
        "permission_mode": "default",
        "hook_event_name": "UserPromptSubmit",
        "prompt": "add retry logic to the uploader",
    }
)


def run_hook(stdin: str = "", env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )


def run_installer(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INSTALLER), *args],
        capture_output=True,
        text=True,
    )


class TestHookOutput(unittest.TestCase):
    def test_emits_the_documented_userpromptsubmit_shape(self):
        proc = run_hook(PAYLOAD)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        specific = payload["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
        self.assertIn("additionalContext", specific)

    def test_context_asks_for_a_numbered_division_and_task_tracking(self):
        context = json.loads(run_hook(PAYLOAD).stdout)["hookSpecificOutput"]["additionalContext"]
        # Compared unwrapped: the directive is hard-wrapped for readability, and
        # a line break falling mid-phrase is not a change in meaning.
        flat = " ".join(context.split())
        for expected in (
            "numbered list of tasks",
            "TaskCreate",
            "TaskUpdate",
            "one-item list",
            "Never skip the division silently",
        ):
            self.assertIn(expected, flat)

    def test_context_carries_the_working_directory(self):
        context = json.loads(run_hook(PAYLOAD).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("/home/user/project", context)

    def test_selftest_passes(self):
        proc = subprocess.run(
            [sys.executable, str(HOOK), "--selftest"], capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestHookNeverBlocksAPrompt(unittest.TestCase):
    """Exit code 2 on UserPromptSubmit blocks the prompt and erases it."""

    def test_survives_anything_on_stdin(self):
        for stdin in ("", "   ", "not json", "[1,2,3]", "null", '{"prompt": null}', "\x00\x01"):
            with self.subTest(stdin=stdin):
                proc = run_hook(stdin)
                self.assertEqual(proc.returncode, 0, f"{stdin!r} -> {proc.stderr}")
                self.assertNotEqual(proc.returncode, 2)

    def test_still_emits_valid_json_when_stdin_is_junk(self):
        payload = json.loads(run_hook("not json").stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")

    def test_disable_switch_is_silent_and_clean(self):
        import os

        env = dict(os.environ, CLAUDE_TASK_DIVISION_DISABLE="1")
        proc = run_hook(PAYLOAD, env=env)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


class TestInstaller(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = self.tmp / ".claude"
        self.cfg.mkdir()
        self.settings = self.cfg / "settings.json"
        self.memory = self.cfg / "CLAUDE.md"
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def seed(self):
        self.settings.write_text(
            json.dumps(
                {
                    "model": "opus",
                    "permissions": {"allow": ["Bash(git status:*)"]},
                    "hooks": {
                        "UserPromptSubmit": [
                            {"hooks": [{"type": "command", "command": "echo unrelated"}]}
                        ],
                        "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}],
                    },
                },
                indent=2,
            )
            + "\n"
        )
        self.memory.write_text("# my notes\n\nkeep me\n")

    def entries(self):
        return json.loads(self.settings.read_text())["hooks"]["UserPromptSubmit"]

    def ours(self):
        return [e for e in self.entries() if "task_division_hook.py" in json.dumps(e)]

    def test_installs_into_an_empty_config_dir(self):
        proc = run_installer("--home", str(self.cfg))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.cfg / "hooks" / "task_division_hook.py").exists())
        self.assertEqual(len(self.ours()), 1)
        self.assertIn("Divide every prompt into tasks", self.memory.read_text())

    def test_installed_copy_runs_standalone(self):
        run_installer("--home", str(self.cfg))
        copied = self.cfg / "hooks" / "task_division_hook.py"
        proc = subprocess.run(
            [sys.executable, str(copied)], input=PAYLOAD, capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            json.loads(proc.stdout)["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit"
        )

    def test_command_in_settings_points_at_the_installed_copy(self):
        run_installer("--home", str(self.cfg))
        command = self.ours()[0]["hooks"][0]["command"]
        self.assertIn(str(self.cfg / "hooks" / "task_division_hook.py"), command)

    def test_preserves_unrelated_settings_and_hooks(self):
        self.seed()
        run_installer("--home", str(self.cfg))
        data = json.loads(self.settings.read_text())
        self.assertEqual(data["model"], "opus")
        self.assertEqual(data["permissions"]["allow"], ["Bash(git status:*)"])
        self.assertIn("Stop", data["hooks"])
        self.assertTrue(any("unrelated" in json.dumps(e) for e in self.entries()))
        self.assertIn("keep me", self.memory.read_text())

    def test_is_idempotent(self):
        self.seed()
        for _ in range(3):
            run_installer("--home", str(self.cfg))
        self.assertEqual(len(self.ours()), 1)
        self.assertEqual(len(self.entries()), 2)
        self.assertEqual(self.memory.read_text().count("BEGIN claude-task-division"), 1)

    def test_check_reports_missing_then_installed(self):
        self.assertEqual(run_installer("--home", str(self.cfg), "--check").returncode, 1)
        run_installer("--home", str(self.cfg))
        self.assertEqual(run_installer("--home", str(self.cfg), "--check").returncode, 0)

    def test_uninstall_restores_the_original_files(self):
        self.seed()
        before_settings = json.loads(self.settings.read_text())
        before_memory = self.memory.read_text()
        run_installer("--home", str(self.cfg))
        run_installer("--home", str(self.cfg), "--uninstall")
        self.assertEqual(json.loads(self.settings.read_text()), before_settings)
        self.assertEqual(self.memory.read_text(), before_memory)
        self.assertFalse((self.cfg / "hooks" / "task_division_hook.py").exists())

    def test_backs_up_before_writing(self):
        self.seed()
        run_installer("--home", str(self.cfg))
        backups = list((self.cfg / "backups").glob("settings.json.*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertNotIn("task_division_hook", backups[0].read_text())

    def test_refuses_to_clobber_unparseable_settings(self):
        self.settings.write_text("{ this is not json ")
        proc = run_installer("--home", str(self.cfg))
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.settings.read_text(), "{ this is not json ")

    def test_dry_run_writes_nothing(self):
        self.seed()
        before = self.settings.read_text()
        proc = run_installer("--home", str(self.cfg), "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.settings.read_text(), before)
        self.assertFalse((self.cfg / "hooks").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
