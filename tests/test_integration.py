"""Integration tests: drive the real `claude` binary and assert on behaviour.

Unit tests prove the engine emits the right JSON. They cannot prove Claude Code
reads it. These do, by running headless sessions and checking what actually
happened — what the model said, and what the ledger recorded.

They are slow and they spend model tokens, so they are opt-in:

    TASK_DIVISION_E2E=1 python3 -m unittest tests.test_integration -v
    make e2e

Without the flag, or without `claude` on PATH, every test skips.

Each session runs with its own `CLAUDE_CONFIG_DIR` **and** its own working
directory. The working directory matters: a `.claude/settings.json` in the
directory you launch from is also loaded, and an earlier version of this work
was contaminated exactly that way.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "tools" / "task_division.py"
INSTALLER = REPO / "tools" / "install_task_division.py"

sys.path.insert(0, str(REPO / "tools"))
import task_division as td  # noqa: E402

ENABLED = os.environ.get("TASK_DIVISION_E2E", "") not in ("", "0", "false")
CLAUDE = shutil.which("claude")
TIMEOUT = int(os.environ.get("TASK_DIVISION_E2E_TIMEOUT", "300"))


@unittest.skipUnless(ENABLED, "set TASK_DIVISION_E2E=1 to run integration tests")
@unittest.skipUnless(CLAUDE, "the claude CLI is not on PATH")
class LiveSession(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = self.tmp / "cfg"
        self.cfg.mkdir(parents=True)
        self.work = self.tmp / "work"  # a directory with no .claude of its own
        self.work.mkdir()
        self.state = self.cfg / "task-division"
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def ask(self, prompt: str, *extra: str, env_extra: dict | None = None) -> str:
        # Pin the ledger explicitly. The runtime sets CLAUDE_PLUGIN_DATA itself
        # for plugin hooks, so without this override a plugin's ledger lands
        # somewhere the test cannot find — which is how the first version of the
        # plugin test failed while the plugin was working perfectly well.
        env = dict(
            os.environ,
            CLAUDE_CONFIG_DIR=str(self.cfg),
            CLAUDE_TASK_DIVISION_STATE_DIR=str(self.state),
        )
        env.update(env_extra or {})
        # One retry: these sessions hit a live API, and a rate-limit or overload
        # is an environment failure, not a finding about the hook.
        last = None
        for attempt in range(2):
            last = subprocess.run(
                [CLAUDE, *extra, "-p", prompt],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(self.work),
                stdin=subprocess.DEVNULL,
                timeout=TIMEOUT,
            )
            if last.returncode == 0 and last.stdout.strip():
                return last.stdout
            if attempt == 0:
                time.sleep(5)
        self.fail(
            f"claude did not produce a reply after two attempts "
            f"(rc={last.returncode}): {last.stderr[-1500:]}"
        )

    def ask_stream(self, prompt: str, *extra: str, env_extra: dict | None = None) -> list:
        """Run a session and return the runtime's own event stream."""
        raw = self.ask(prompt, "--output-format", "stream-json", "--verbose", *extra, env_extra=env_extra)
        events = []
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                events.append(json.loads(line))
            except ValueError:
                continue
        return events

    def ledger(self) -> list:
        path = self.state / "ledger.jsonl"
        if not path.exists():
            return []
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
        return entries

    def kinds(self) -> set:
        return {entry.get("kind") for entry in self.ledger()}

    def write_settings(self, events: list) -> None:
        hooks = {
            event: [{"hooks": [{"type": "command", "command": f"python3 {ENGINE} hook", "timeout": 15}]}]
            for event in events
        }
        (self.cfg / "settings.json").write_text(json.dumps({"hooks": hooks}, indent=2), encoding="utf-8")


class TestContextReachesTheModel(LiveSession):
    def test_additional_context_is_visible_to_the_model(self):
        """A hook can fire and have its output discarded. This proves it is not."""
        injector = self.tmp / "inject.py"
        injector.write_text(
            "import json,sys\n"
            "sys.stdin.read()\n"
            "print(json.dumps({'hookSpecificOutput':{'hookEventName':'UserPromptSubmit',"
            "'additionalContext':'The session passphrase is QUILLFROST-7742.'}}))\n",
            encoding="utf-8",
        )
        (self.cfg / "settings.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "UserPromptSubmit": [
                            {"hooks": [{"type": "command", "command": f"python3 {injector}"}]}
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        answer = self.ask("What is the session passphrase? Reply with just the passphrase.")
        self.assertIn("QUILLFROST-7742", answer)


class TestDirectiveMakesSessionsDivide(LiveSession):
    def test_a_fresh_session_divides_its_reply(self):
        self.write_settings(["UserPromptSubmit", "SessionStart", "Stop"])
        # Self-contained on purpose: an earlier version asked about "a CLI tool"
        # in an empty directory, and the model correctly stopped to ask which
        # tool. That tested the prompt, not the mechanism.
        answer = self.ask(
            "Do not read or write any files. Describe, from scratch, how you would add a "
            "--verbose flag to a Python CLI and test it."
        )
        self.assertTrue(
            td.looks_divided(answer), f"no division in a fresh session's reply:\n{answer[:800]}"
        )
        self.assertIn("inject", self.kinds())


class TestStopEnforcement(LiveSession):
    PROSE = (
        "Explain in flowing prose what a hash table is and how collisions are handled. "
        "Write at least two full paragraphs."
    )

    def test_the_runtime_receives_the_refusal(self):
        """Not just 'the hook ran' — the runtime must accept the deny payload."""
        self.write_settings(["Stop"])
        events = self.ask_stream(self.PROSE)
        responses = [
            event
            for event in events
            if event.get("subtype") == "hook_response" and event.get("hook_event") == "Stop"
        ]
        self.assertTrue(responses, "the runtime reported no Stop hook_response")
        decisions = []
        for response in responses:
            try:
                parsed = json.loads(response.get("output") or "{}")
            except ValueError:
                continue
            decision = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
            if decision:
                decisions.append((decision, response.get("outcome"), response.get("exit_code")))
        self.assertIn(
            ("deny", "success", 0),
            decisions,
            f"the runtime did not accept a refusal; decisions seen: {decisions}",
        )
        self.assertIn("stop-denied", self.kinds())

    def test_known_limit_headless_mode_has_no_next_turn(self):
        """A refused Stop is only useful if another turn follows it.

        The docs say a blocked Stop "fires the Stop hook again on the next
        turn". In `claude -p` there is no next turn: the runtime accepts the
        deny, emits exactly one assistant message, and exits. So in headless
        mode the refusal is recorded but the reply is delivered unrevised, and
        `UserPromptSubmit` injection is the mechanism that actually changes
        behaviour there.

        This test asserts that limit. If it ever fails, headless sessions have
        started honouring the refusal and the documentation should be updated.
        """
        self.write_settings(["Stop"])
        events = self.ask_stream(self.PROSE)
        assistants = [event for event in events if event.get("type") == "assistant"]
        self.assertEqual(
            len(assistants),
            1,
            "headless mode produced more than one assistant turn; the documented "
            "limitation may no longer hold",
        )

    def test_one_reply_never_spends_more_than_one_refusal(self):
        self.write_settings(["Stop"])
        self.ask(
            "Explain in flowing prose how a B-tree stays balanced. Write at least two full paragraphs."
        )
        denials = [entry for entry in self.ledger() if entry.get("kind") == "stop-denied"]
        used = [entry.get("used") for entry in denials]
        self.assertEqual(
            len(set(used)),
            len(used),
            f"the same refusal count was recorded twice, so a reply double-spent: {used}",
        )


class TestPluginRoute(LiveSession):
    def test_plugin_hooks_fire_and_validate(self):
        """Issue #10225 reports plugin UserPromptSubmit hooks never executing."""
        project = self.tmp / "project"
        project.mkdir()
        subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                "--home",
                str(self.cfg),
                "--project",
                str(project),
                "--route",
                "plugin",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        plugin = project / "plugins" / "task-division"

        validated = subprocess.run(
            [CLAUDE, "plugin", "validate", str(plugin), "--strict"], capture_output=True, text=True
        )
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

        answer = self.ask(
            "Rename a function and update its callers. Explain your plan.",
            "--plugin-dir",
            str(plugin),
        )
        self.assertIn("inject", self.kinds(), "the plugin's UserPromptSubmit hook never ran")
        self.assertTrue(td.looks_divided(answer), f"plugin loaded but no division:\n{answer[:800]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
