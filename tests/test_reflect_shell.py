"""Tests for the shell-history signal source."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from oodarag.reflect.models import ACTOR_HUMAN, KIND_COMMAND, day_key
from oodarag.reflect.sources.base import Budget
from oodarag.reflect.sources.shell import ShellHistorySource

# Fixed points in time so day grouping is deterministic on any machine.
T0 = 1_756_200_000.0
MTIME = 1_756_300_000.0

ZSH_HISTORY = """: 1756200000:0;git status
: 1756200060:12;pytest -q
: notanumber:0;echo hi
: 1756200200:3;for f in *.py; do \\
  echo $f; done
q
# a comment nobody ran
"""

FISH_HISTORY = """- cmd: git push
  when: 1756200000
- cmd: vim notes.md
  when: 1756200100
  paths:
    - notes.md
- cmd: ls
- cmd: 
- cmd: x
"""


class ShellHistoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    # -- fixtures ------------------------------------------------------------

    def write(self, name: str, text: str, mtime: float = MTIME) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        os.utime(path, (mtime, mtime))
        return path

    def signals(self, paths: list[Path], since: float = 0.0, **config: object) -> list:
        source = ShellHistorySource(paths=paths, config=config)
        result = source.run(since=since)
        self.assertEqual(result.errors, [])
        return result.signals

    # -- zsh -----------------------------------------------------------------

    def test_zsh_extended_format(self) -> None:
        path = self.write(".zsh_history", ZSH_HISTORY)
        sigs = self.signals([path])

        self.assertEqual([s.text for s in sigs][:3], ["git status", "pytest -q", "echo hi"])
        self.assertEqual(len(sigs), 4)  # "q" and the comment line are dropped

        first = sigs[0]
        self.assertEqual(first.kind, KIND_COMMAND)
        self.assertEqual(first.actor, ACTOR_HUMAN)
        self.assertEqual(first.source, "shell:history")
        self.assertEqual(first.ts, T0)
        self.assertEqual(first.ordinal, 0)
        self.assertEqual(first.metadata["shell"], "zsh")
        self.assertEqual(first.metadata["argv0"], "git")
        self.assertEqual(first.metadata["history_file"], str(path))
        self.assertEqual(first.metadata["elapsed_s"], 0.0)
        self.assertIs(first.metadata["ts_estimated"], False)
        self.assertTrue(first.uri.startswith(str(path)))

        self.assertEqual(sigs[1].metadata["elapsed_s"], 12.0)

    def test_zsh_malformed_metadata_keeps_the_command(self) -> None:
        """": notanumber:0;echo hi" must not kill the file or the command."""
        path = self.write(".zsh_history", ZSH_HISTORY)
        broken = [s for s in self.signals([path]) if s.text == "echo hi"]

        self.assertEqual(len(broken), 1)
        self.assertEqual(broken[0].ts, MTIME)  # falls back to the file's mtime
        self.assertIs(broken[0].metadata["ts_estimated"], True)

    def test_zsh_backslash_continuation_is_joined(self) -> None:
        path = self.write(".zsh_history", ZSH_HISTORY)
        joined = [s for s in self.signals([path]) if s.text.startswith("for f in")]

        self.assertEqual(len(joined), 1)
        self.assertIn("\n", joined[0].text)
        self.assertIn("echo $f; done", joined[0].text)
        self.assertEqual(joined[0].ts, T0 + 200)
        self.assertEqual(joined[0].metadata["argv0"], "for")

    def test_zsh_plain_lines_when_extended_history_is_off(self) -> None:
        path = self.write(".zsh_history", "ls -la\ncd /tmp\n")
        sigs = self.signals([path])

        self.assertEqual([s.text for s in sigs], ["ls -la", "cd /tmp"])
        self.assertTrue(all(s.metadata["ts_estimated"] for s in sigs))
        self.assertTrue(all(s.ts == MTIME for s in sigs))

    # -- bash ----------------------------------------------------------------

    def test_plain_bash_tails_and_estimates_timestamps(self) -> None:
        path = self.write(".bash_history", "".join(f"echo {i}\n" for i in range(20)))
        sigs = self.signals([path], tail_lines=5)

        self.assertEqual([s.text for s in sigs], [f"echo {i}" for i in range(15, 20)])
        # ordinal stays the position in the file, not the position in the tail
        self.assertEqual([s.ordinal for s in sigs], list(range(15, 20)))
        self.assertTrue(all(s.ts == MTIME for s in sigs))
        self.assertTrue(all(s.metadata["ts_estimated"] is True for s in sigs))
        self.assertEqual({s.session for s in sigs}, {f"bash:{day_key(MTIME)}"})

    def test_bash_timestamp_comments(self) -> None:
        text = (
            "#1756200000\n"
            "make test\n"
            "#1756200100\n"
            'git commit -m "wip"\n'
            "# not a timestamp\n"
            "ls\n"
        )
        path = self.write(".bash_history", text)
        # tail_lines is deliberately tiny: a file that carries its own clock is
        # never tailed, because `since` can filter it exactly.
        sigs = self.signals([path], tail_lines=1)

        self.assertEqual([s.text for s in sigs], ["make test", 'git commit -m "wip"', "ls"])
        self.assertEqual(sigs[0].ts, T0)
        self.assertEqual(sigs[1].ts, T0 + 100)
        self.assertIs(sigs[0].metadata["ts_estimated"], False)
        # the third command has no marker of its own, so it is estimated
        self.assertEqual(sigs[2].ts, MTIME)
        self.assertIs(sigs[2].metadata["ts_estimated"], True)
        self.assertEqual(sigs[0].session, f"bash:{day_key(T0)}")

    # -- fish ----------------------------------------------------------------

    def test_fish_format(self) -> None:
        path = self.write(".local/share/fish/fish_history", FISH_HISTORY)
        sigs = self.signals([path])

        self.assertEqual([s.text for s in sigs], ["git push", "vim notes.md", "ls"])
        self.assertEqual(sigs[0].ts, T0)
        self.assertEqual(sigs[1].ts, T0 + 100)
        self.assertEqual(sigs[1].metadata["shell"], "fish")
        self.assertEqual(sigs[1].metadata["argv0"], "vim")
        # a record with no "when:" still counts, with an estimated stamp
        self.assertEqual(sigs[2].ts, MTIME)
        self.assertIs(sigs[2].metadata["ts_estimated"], True)

    # -- windowing and grouping ---------------------------------------------

    def test_since_filters_timestamped_commands(self) -> None:
        path = self.write(".zsh_history", ZSH_HISTORY)
        sigs = self.signals([path], since=T0 + 100)

        # git status (T0) and pytest (T0+60) fall outside the window; the
        # malformed line survives because mtime is inside it.
        self.assertEqual(sorted(s.metadata["argv0"] for s in sigs), ["echo", "for"])

    def test_since_skips_a_whole_untimed_file_that_is_too_old(self) -> None:
        path = self.write(".bash_history", "ls\ncd /tmp\n", mtime=T0)
        self.assertEqual(self.signals([path], since=T0 + 1000), [])
        self.assertEqual(len(self.signals([path], since=T0 - 1000)), 2)

    def test_session_groups_by_shell_and_local_day(self) -> None:
        later = T0 + 2 * 86_400
        text = f": {int(T0)}:0;ls\n: {int(T0) + 60}:0;pwd\n: {int(later)}:0;make\n"
        path = self.write(".zsh_history", text)
        sigs = self.signals([path])

        self.assertEqual(sigs[0].session, sigs[1].session)
        self.assertEqual(sigs[0].session, f"zsh:{day_key(T0)}")
        self.assertNotEqual(sigs[2].session, sigs[0].session)
        self.assertEqual(sigs[2].session, f"zsh:{day_key(later)}")

    # -- discovery and availability -----------------------------------------

    def test_available(self) -> None:
        missing = self.root / "nope" / ".bash_history"
        self.assertFalse(ShellHistorySource(paths=[missing]).available())
        path = self.write(".bash_history", "ls\n")
        self.assertTrue(ShellHistorySource(paths=[path]).available())
        # a missing path alongside a real one is skipped, not fatal
        self.assertEqual(len(self.signals([missing, path])), 1)

    def test_discovery_honours_home_and_histfile(self) -> None:
        self.write(".bash_history", "ls\n")
        custom = self.write("custom_hist", ": 1756200000:0;make\n")
        old_home = os.environ.get("HOME")
        old_hist = os.environ.get("HISTFILE")
        os.environ["HOME"] = str(self.root)
        os.environ["HISTFILE"] = str(custom)
        try:
            source = ShellHistorySource()
            found = {p.name for p in source.candidates()}
            self.assertIn("custom_hist", found)
            self.assertIn(".bash_history", found)
            self.assertTrue(source.available())
            texts = {s.text for s in source.run().signals}
            self.assertEqual(texts, {"ls", "make"})
        finally:
            _restore("HOME", old_home)
            _restore("HISTFILE", old_hist)

    def test_the_same_file_twice_is_read_once(self) -> None:
        path = self.write(".zsh_history", ": 1756200000:0;ls\n")
        self.assertEqual(len(self.signals([path, path])), 1)

    # -- hostile input -------------------------------------------------------

    def test_binary_and_unreadable_paths_degrade_to_nothing(self) -> None:
        binary = self.root / ".bash_history"
        binary.write_bytes(b"ls -la\n\x00\x00\x01\x02binary junk\n")
        directory = self.root / "adirectory"
        directory.mkdir()
        source = ShellHistorySource(paths=[binary, directory])
        result = source.run()

        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_continuation_bomb_is_capped(self) -> None:
        path = self.write(".bash_history", "".join("x\\\n" for _ in range(500)))
        sigs = self.signals([path])

        self.assertTrue(sigs)
        # 500 escaped lines must not fold into one 500-line "command"
        self.assertTrue(all(s.text.count("\n") < 64 for s in sigs))

    def test_secrets_are_redacted_by_the_base_class(self) -> None:
        path = self.write(".bash_history", "export API_KEY=abcd1234efgh5678ijkl\n")
        text = self.signals([path])[0].text

        self.assertNotIn("abcd1234efgh5678ijkl", text)
        self.assertIn("<redacted>", text)

    # -- budgets -------------------------------------------------------------

    def test_signal_budget_truncates(self) -> None:
        path = self.write(".zsh_history", ZSH_HISTORY)
        result = ShellHistorySource(paths=[path]).run(budget=Budget(max_signals=2))

        self.assertEqual(len(result.signals), 2)
        self.assertTrue(result.truncated)

    def test_expired_budget_yields_nothing(self) -> None:
        path = self.write(".zsh_history", ZSH_HISTORY)
        result = ShellHistorySource(paths=[path]).run(budget=Budget(wall_clock_s=1e-9))

        self.assertEqual(result.signals, [])
        self.assertEqual(result.errors, [])

    def test_long_command_is_truncated_per_signal(self) -> None:
        path = self.write(".bash_history", "echo " + "a" * 5_000 + "\n")
        result = ShellHistorySource(paths=[path]).run(budget=Budget(max_chars_per_signal=100))

        self.assertEqual(len(result.signals), 1)
        self.assertTrue(result.signals[0].text.endswith("[truncated]"))


def _restore(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
