"""Unit tests for the task-division engine and its installer.

Every test runs against a temporary `CLAUDE_CONFIG_DIR`, so the suite never
reads or writes the real `~/.claude`.

The tests that matter most prove failure cases rather than the happy path:

- the engine can never exit non-zero, because exit 2 on `UserPromptSubmit`
  erases the user's prompt;
- one reply can never spend more than one refusal, even when the runtime
  invokes `Stop` twice concurrently — observed behaviour on 2.1.247, and the
  cause of two separate bugs;
- installing never damages settings the installer did not write.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "tools" / "task_division.py"
INSTALLER = REPO / "tools" / "install_task_division.py"

sys.path.insert(0, str(REPO / "tools"))
import task_division as td  # noqa: E402


def payload(event: str, **fields) -> str:
    body = {"hook_event_name": event, "session_id": "s-default", "cwd": "/w"}
    body.update(fields)
    return json.dumps(body)


class Harness(unittest.TestCase):
    """Base class giving every test its own config directory."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = self.tmp / ".claude"
        self.cfg.mkdir()
        self.env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.cfg))
        self.env.pop("CLAUDE_PLUGIN_DATA", None)
        self.env.pop("CLAUDE_TASK_DIVISION_MODE", None)
        self.env.pop("CLAUDE_TASK_DIVISION_DISABLE", None)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def hook(self, body: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ENGINE), "hook"],
            input=body,
            capture_output=True,
            text=True,
            env=env or self.env,
        )

    def specific(self, proc: subprocess.CompletedProcess) -> dict:
        self.assertTrue(proc.stdout.strip(), f"no output; stderr={proc.stderr}")
        return json.loads(proc.stdout)["hookSpecificOutput"]

    def installer(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(INSTALLER), *args], capture_output=True, text=True, env=self.env
        )


class TestNeverBreaksAPrompt(Harness):
    """Exit 2 on UserPromptSubmit blocks the prompt and erases it."""

    def test_every_kind_of_junk_exits_zero(self):
        for body in ("", "   ", "not json", "[1,2,3]", "null", '{"a":', "\x00\x01", "{}"):
            with self.subTest(body=body):
                proc = self.hook(body)
                self.assertEqual(proc.returncode, 0, f"{body!r} -> {proc.stderr}")

    def test_unknown_event_is_ignored_silently(self):
        proc = self.hook(payload("SomethingNobodyHasHeardOf"))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_unreadable_config_does_not_break_the_hook(self):
        (self.cfg / "task-division").mkdir(parents=True)
        (self.cfg / "task-division" / "config.json").write_text("{ broken")
        proc = self.hook(payload("UserPromptSubmit", prompt="x"))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.specific(proc)["hookEventName"], "UserPromptSubmit")


class TestUserPromptSubmit(Harness):
    def test_emits_the_directive(self):
        specific = self.specific(self.hook(payload("UserPromptSubmit", prompt="do a thing")))
        self.assertEqual(specific["hookEventName"], "UserPromptSubmit")
        flat = " ".join(specific["additionalContext"].split())
        for expected in ("numbered list of tasks", "TaskCreate", "TaskUpdate", "one-item list"):
            self.assertIn(expected, flat)

    def test_carries_the_working_directory(self):
        specific = self.specific(self.hook(payload("UserPromptSubmit", prompt="p", cwd="/srv/app")))
        self.assertIn("/srv/app", specific["additionalContext"])

    def test_deduplicates_across_overlapping_routes(self):
        body = payload("UserPromptSubmit", prompt="same prompt", session_id="dedupe-1")
        first, second = self.hook(body), self.hook(body)
        self.assertTrue(first.stdout.strip())
        self.assertEqual(second.stdout.strip(), "", "the same prompt was injected twice")

    def test_different_prompts_are_not_deduplicated(self):
        self.hook(payload("UserPromptSubmit", prompt="one", session_id="d2"))
        second = self.hook(payload("UserPromptSubmit", prompt="two", session_id="d2"))
        self.assertTrue(second.stdout.strip(), "a different prompt was wrongly suppressed")


class TestSessionAndSubagent(Harness):
    def test_session_start_seeds_the_directive(self):
        specific = self.specific(self.hook(payload("SessionStart", session_start_reason="startup")))
        self.assertIn("divide every prompt into tasks", specific["additionalContext"].lower())

    def test_compaction_gets_its_own_recovery_wording(self):
        specific = self.specific(
            self.hook(payload("SessionStart", session_start_reason="compact", session_id="c1"))
        )
        self.assertIn("TaskList", specific["additionalContext"])

    def test_subagents_get_the_directive_too(self):
        specific = self.specific(self.hook(payload("SubagentStart", agent_type="Explore")))
        self.assertIn("done-condition", specific["additionalContext"])

    def test_precompact_never_blocks_a_compaction(self):
        specific = self.specific(self.hook(payload("PreCompact", trigger="auto")))
        self.assertNotIn("permissionDecision", specific)


class TestDivisionDetection(unittest.TestCase):
    """The truth table. A false negative blocks a reply that was fine."""

    DIVIDED = [
        "1. do a thing\n2. do another thing",
        "1) first\n2) second",
        "- [ ] one\n- [x] two",
        "| # | Task |\n|---|---|\n| 1 | go |",
        "Task #4 created successfully",
        "I used TaskCreate for each of these",
        "This is a single atomic task.",
        "That is one atomic task, so here is the one-item list.",
        # Regression: a one-item list under a heading is exactly what the
        # directive asks for on an atomic request. An earlier version refused a
        # live reply that had done the right thing.
        "**Task list:**\n1. Explain what a hash table is, in prose, two paragraphs.\n\nA hash table is...",
        "## Tasks\n1. Ship the thing\n\nbody text",
        "1. Add the flag — done when the new test passes.",
    ]
    NOT_DIVIDED = [
        "",
        "   ",
        "Sure, here is the answer to your question.",
        "The file is at src/main.py and the bug is on line 40.",
        "1. only one numbered item and nothing else",
    ]

    def test_recognises_divisions(self):
        for text in self.DIVIDED:
            with self.subTest(text=text[:30]):
                self.assertTrue(td.looks_divided(text))

    def test_does_not_invent_divisions(self):
        for text in self.NOT_DIVIDED:
            with self.subTest(text=text[:30]):
                self.assertFalse(td.looks_divided(text))

    def test_verify_command_exit_codes(self):
        divided = subprocess.run(
            [sys.executable, str(ENGINE), "verify", "1. a", "2. b"], capture_output=True, text=True
        )
        self.assertEqual(divided.returncode, 0)
        bare = subprocess.run(
            [sys.executable, str(ENGINE), "verify", "just prose"], capture_output=True, text=True
        )
        self.assertEqual(bare.returncode, 1)


class TestStopEnforcement(Harness):
    LONG = "x" * 900

    def test_denies_a_substantial_undivided_reply(self):
        specific = self.specific(
            self.hook(payload("Stop", session_id="e1", last_assistant_message=self.LONG))
        )
        self.assertEqual(specific["permissionDecision"], "deny")
        self.assertIn("numbered list of tasks", specific["permissionDecisionReason"])

    def test_allows_a_divided_reply(self):
        proc = self.hook(
            payload("Stop", session_id="e2", last_assistant_message="1. a\n2. b\n" + self.LONG)
        )
        self.assertEqual(proc.stdout.strip(), "")

    def test_never_challenges_a_short_reply(self):
        proc = self.hook(payload("Stop", session_id="e3", last_assistant_message="Yes, on line 40."))
        self.assertEqual(proc.stdout.strip(), "")

    def test_ignores_a_mid_turn_stop(self):
        proc = self.hook(
            payload("Stop", session_id="e4", last_assistant_message=self.LONG, stop_reason="tool_use")
        )
        self.assertEqual(proc.stdout.strip(), "")

    def test_one_reply_spends_one_refusal_even_when_stop_fires_twice(self):
        """Observed on 2.1.247: Stop is invoked twice per turn, concurrently."""
        body = payload("Stop", session_id="race", last_assistant_message=self.LONG)
        procs = [
            subprocess.Popen(
                [sys.executable, str(ENGINE), "hook"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                env=self.env,
            )
            for _ in range(2)
        ]
        outputs = [proc.communicate(body)[0] for proc in procs]
        self.assertTrue(all('"deny"' in out for out in outputs), "the two decisions disagreed")
        spent = (self.cfg / "task-division" / "sessions" / "race.denials").read_text().strip()
        self.assertEqual(spent, "1", f"one reply spent {spent} refusals")

    def test_refusal_budget_runs_out(self):
        ceiling = td.DEFAULT_CONFIG["max_denials_per_session"]
        denials = 0
        for index in range(ceiling + 2):
            proc = self.hook(
                payload("Stop", session_id="budget", last_assistant_message=self.LONG + str(index))
            )
            if proc.stdout.strip() and '"deny"' in proc.stdout:
                denials += 1
        self.assertEqual(denials, ceiling, "the refusal budget did not run out")

    def test_warn_mode_advises_without_refusing(self):
        env = dict(self.env, CLAUDE_TASK_DIVISION_MODE="warn")
        specific = self.specific(
            self.hook(payload("Stop", session_id="w1", last_assistant_message=self.LONG), env=env)
        )
        self.assertNotIn("permissionDecision", specific)
        self.assertIn("systemMessage", specific)

    def test_off_mode_is_completely_silent(self):
        for key in ("CLAUDE_TASK_DIVISION_MODE", "CLAUDE_TASK_DIVISION_DISABLE"):
            with self.subTest(key=key):
                env = dict(self.env, **{key: "off" if "MODE" in key else "1"})
                proc = self.hook(payload("Stop", session_id="o1", last_assistant_message=self.LONG), env=env)
                self.assertEqual(proc.stdout.strip(), "")
                proc = self.hook(payload("UserPromptSubmit", prompt="p"), env=env)
                self.assertEqual(proc.stdout.strip(), "")


class TestTaskShape(Harness):
    def test_flags_a_task_with_no_done_condition(self):
        specific = self.specific(
            self.hook(payload("TaskCreated", task_title="Fix it", task_description=""))
        )
        self.assertIn("done-condition", specific["systemMessage"])
        self.assertNotIn("permissionDecision", specific, "advisory by default, not a denial")

    def test_accepts_a_well_formed_task(self):
        proc = self.hook(
            payload(
                "TaskCreated",
                task_title="Add retry logic to the uploader",
                task_description="Retries three times with backoff; done when the flaky upload test passes.",
            )
        )
        self.assertEqual(proc.stdout.strip(), "")

    def test_strict_mode_denies_a_vacuous_task(self):
        (self.cfg / "task-division").mkdir(parents=True, exist_ok=True)
        (self.cfg / "task-division" / "config.json").write_text(
            json.dumps({"mode": "enforce", "enforce_task_quality": True})
        )
        specific = self.specific(
            self.hook(payload("TaskCreated", task_title="stuff", task_description=""))
        )
        self.assertEqual(specific["permissionDecision"], "deny")

    def test_completion_without_notes_is_flagged(self):
        specific = self.specific(self.hook(payload("TaskCompleted", task_id="7", completion_notes="")))
        self.assertIn("systemMessage", specific)


class TestConfigAndLedger(Harness):
    def test_config_round_trips(self):
        written = subprocess.run(
            [sys.executable, str(ENGINE), "config", "mode=warn", "min_response_chars=800"],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(written.returncode, 0, written.stderr)
        loaded = json.loads(
            subprocess.run(
                [sys.executable, str(ENGINE), "config"], capture_output=True, text=True, env=self.env
            ).stdout
        )
        self.assertEqual(loaded["mode"], "warn")
        self.assertEqual(loaded["min_response_chars"], 800)

    def test_config_rejects_unknown_keys(self):
        proc = subprocess.run(
            [sys.executable, str(ENGINE), "config", "nonsense=1"],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(proc.returncode, 2)

    def test_ledger_records_what_happened(self):
        self.hook(payload("UserPromptSubmit", prompt="ledger test", session_id="L1"))
        ledger = self.cfg / "task-division" / "ledger.jsonl"
        self.assertTrue(ledger.exists())
        kinds = [json.loads(line)["kind"] for line in ledger.read_text().splitlines()]
        self.assertIn("inject", kinds)

    def test_selftest_is_repeatable(self):
        for attempt in range(2):
            proc = subprocess.run(
                [sys.executable, str(ENGINE), "selftest"], capture_output=True, text=True, env=self.env
            )
            self.assertEqual(proc.returncode, 0, f"attempt {attempt}: {proc.stdout}{proc.stderr}")


class TestInstallerRoutes(Harness):
    def setUp(self):
        super().setUp()
        self.project = self.tmp / "project"
        (self.project / ".claude").mkdir(parents=True)

    def args(self, *extra: str) -> list:
        return ["--home", str(self.cfg), "--project", str(self.project), *extra]

    def settings(self, name: str = "settings.json") -> dict:
        return json.loads((self.cfg / name).read_text())

    def test_user_route_registers_every_event(self):
        proc = self.installer(*self.args("--route", "user"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        hooks = self.settings()["hooks"]
        for event in td.HANDLED:
            self.assertIn(event, hooks, f"{event} not registered")
        self.assertTrue((self.cfg / "hooks" / "task_division.py").exists())
        self.assertIn("Divide every prompt", (self.cfg / "CLAUDE.md").read_text())

    def test_project_and_local_routes(self):
        self.installer(*self.args("--route", "project", "--route", "local"))
        for name in ("settings.json", "settings.local.json"):
            data = json.loads((self.project / ".claude" / name).read_text())
            self.assertIn("UserPromptSubmit", data["hooks"])
        self.assertTrue((self.project / ".claude" / "hooks" / "task_division.py").exists())

    def test_project_route_is_portable_across_clones(self):
        """A committed settings.json must not hard-code this machine's paths."""
        self.installer(*self.args("--route", "project"))
        data = json.loads((self.project / ".claude" / "settings.json").read_text())
        command = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PROJECT_DIR}", command)
        self.assertNotIn(str(self.project), command)

    def test_plugin_route_registers_the_marketplace_without_enabling(self):
        self.installer(*self.args("--route", "plugin"))
        data = json.loads((self.project / ".claude" / "settings.json").read_text())
        self.assertIn("turkertekten-tools", data["extraKnownMarketplaces"])
        self.assertNotIn(
            "enabledPlugins", data, "enabling the plugin here would double-fire every hook"
        )

    def test_skills_dir_route_builds_a_loadable_plugin(self):
        self.installer(*self.args("--route", "skills-dir"))
        root = self.cfg / "skills" / "task-division"
        manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "task-division")
        self.assertTrue((root / "hooks" / "hooks.json").exists())
        self.assertTrue((root / "skills" / "divide" / "SKILL.md").exists())
        self.assertTrue((root / "scripts" / "task_division.py").exists())

    def test_plugin_route_writes_plugin_and_marketplace(self):
        self.installer(*self.args("--route", "plugin"))
        root = self.project / "plugins" / "task-division"
        hooks = json.loads((root / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", hooks["Stop"][0]["hooks"][0]["command"])
        market = json.loads((self.project / ".claude-plugin" / "marketplace.json").read_text())
        self.assertEqual(market["plugins"][0]["name"], "task-division")

    def test_installed_engine_runs_standalone(self):
        self.installer(*self.args("--route", "user"))
        copied = self.cfg / "hooks" / "task_division.py"
        proc = subprocess.run(
            [sys.executable, str(copied), "hook"],
            input=payload("UserPromptSubmit", prompt="p", session_id="standalone"),
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")

    def test_check_reports_missing_then_installed(self):
        self.assertEqual(self.installer(*self.args("--route", "all", "--check")).returncode, 1)
        self.installer(*self.args("--route", "all"))
        self.assertEqual(self.installer(*self.args("--route", "all", "--check")).returncode, 0)

    def test_dry_run_writes_nothing(self):
        self.installer(*self.args("--route", "all", "--dry-run"))
        self.assertFalse((self.cfg / "settings.json").exists())
        self.assertFalse((self.cfg / "hooks").exists())


class TestInstallerSafety(Harness):
    def setUp(self):
        super().setUp()
        self.project = self.tmp / "project"
        (self.project / ".claude").mkdir(parents=True)
        self.seeded = {
            "model": "opus",
            "permissions": {"allow": ["Bash(git status:*)"]},
            "hooks": {
                "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo unrelated"}]}],
                "PostToolUse": [{"hooks": [{"type": "command", "command": "echo fmt"}]}],
            },
        }
        (self.cfg / "settings.json").write_text(json.dumps(self.seeded, indent=2))
        (self.cfg / "CLAUDE.md").write_text("# my notes\n\nkeep me\n")

    def args(self, *extra: str) -> list:
        return ["--home", str(self.cfg), "--project", str(self.project), "--route", "user", *extra]

    def data(self) -> dict:
        return json.loads((self.cfg / "settings.json").read_text())

    def ours(self, event: str = "UserPromptSubmit") -> list:
        return [e for e in self.data()["hooks"][event] if "task_division.py" in json.dumps(e)]

    def test_preserves_unrelated_settings_and_hooks(self):
        self.installer(*self.args())
        data = self.data()
        self.assertEqual(data["model"], "opus")
        self.assertEqual(data["permissions"]["allow"], ["Bash(git status:*)"])
        self.assertIn("PostToolUse", data["hooks"])
        self.assertTrue(any("unrelated" in json.dumps(e) for e in data["hooks"]["UserPromptSubmit"]))
        self.assertIn("keep me", (self.cfg / "CLAUDE.md").read_text())

    def test_is_idempotent_across_repeated_installs(self):
        for _ in range(3):
            self.installer(*self.args())
        self.assertEqual(len(self.ours()), 1)
        self.assertEqual(len(self.data()["hooks"]["UserPromptSubmit"]), 2)
        self.assertEqual((self.cfg / "CLAUDE.md").read_text().count("BEGIN claude-task-division"), 1)

    def test_upgrades_a_v1_installation_in_place(self):
        legacy = dict(self.seeded)
        legacy["hooks"] = dict(legacy["hooks"])
        legacy["hooks"]["UserPromptSubmit"] = legacy["hooks"]["UserPromptSubmit"] + [
            {"hooks": [{"type": "command", "command": "python3 /old/task_division_hook.py"}]}
        ]
        (self.cfg / "settings.json").write_text(json.dumps(legacy, indent=2))
        self.installer(*self.args())
        blob = json.dumps(self.data())
        self.assertNotIn("task_division_hook.py", blob, "the v1 entry survived the upgrade")
        self.assertEqual(len(self.ours()), 1)

    def test_uninstall_restores_the_original_files(self):
        before_settings, before_memory = self.data(), (self.cfg / "CLAUDE.md").read_text()
        self.installer(*self.args())
        self.installer(*self.args("--uninstall"))
        self.assertEqual(self.data(), before_settings)
        self.assertEqual((self.cfg / "CLAUDE.md").read_text(), before_memory)
        self.assertFalse((self.cfg / "hooks" / "task_division.py").exists())

    def test_backs_up_before_writing(self):
        self.installer(*self.args())
        backups = list((self.cfg / "backups").glob("settings.json.*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertNotIn("task_division", backups[0].read_text())

    def test_refuses_to_clobber_unparseable_settings(self):
        (self.cfg / "settings.json").write_text("{ not json ")
        proc = self.installer(*self.args())
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual((self.cfg / "settings.json").read_text(), "{ not json ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
