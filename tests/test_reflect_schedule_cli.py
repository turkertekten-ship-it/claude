"""Tests for the scheduling generators and the command line surface.

The scheduling code is the part of this system nobody looks at again: it gets
run once, pasted into a unit file, and forgotten. So the tests pin the things
that would otherwise fail silently at 22:30 six weeks later - the catch-up flag
that decides whether a closed laptop skips the day, and the GitHub expression
escaping that decides whether the workflow parses at all.
"""

from __future__ import annotations

import io
import contextlib
import tempfile
import time
import unittest
from pathlib import Path

from oodarag.cli import EXIT_ERROR, EXIT_NOT_BUILT, EXIT_OK, build_parser, main, parse_since
from oodarag.reflect.schedule import (
    ScheduleSpec,
    cron_line,
    github_workflow,
    install_hint,
    launchd_plist,
    render,
    systemd_units,
)


class TestScheduleSpec(unittest.TestCase):
    def spec(self, at: str = "22:30", apply: bool = False) -> ScheduleSpec:
        return ScheduleSpec.parse(Path("/srv/project"), at, apply=apply)

    def test_parses_time(self) -> None:
        spec = self.spec("07:05")
        self.assertEqual((spec.hour, spec.minute), (7, 5))

    def test_rejects_malformed_and_out_of_range(self) -> None:
        for bad in ("garbage", "25:00", "12:99", "", "12"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.spec(bad)

    def test_command_carries_root_pythonpath_and_apply(self) -> None:
        self.assertNotIn("--apply", self.spec().command)
        applying = self.spec(apply=True).command
        self.assertIn("--apply", applying)
        self.assertIn("/srv/project/src", applying)
        self.assertIn("oodarag.cli reflect run", applying)


class TestScheduleBackends(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = ScheduleSpec.parse(Path("/srv/project"), "22:30")

    def test_cron_line_shape_and_warning(self) -> None:
        line = cron_line(self.spec)
        self.assertIn("30 22 * * *", line)
        # The one thing a user must know about cron here.
        self.assertIn("does not catch up", line)

    def test_systemd_timer_persists_missed_runs(self) -> None:
        units = systemd_units(self.spec)
        timer = units["oodarag-reflect.timer"]
        self.assertIn("OnCalendar=*-*-* 22:30:00", timer)
        self.assertIn("Persistent=true", timer, "a closed laptop must still run the loop")
        self.assertIn("WantedBy=timers.target", timer)
        self.assertIn("ExecStart=", units["oodarag-reflect.service"])

    def test_launchd_plist_is_wellformed(self) -> None:
        from xml.etree import ElementTree

        plist = launchd_plist(self.spec)
        ElementTree.fromstring(plist)  # raises if the plist is not valid XML
        self.assertIn("<key>StartCalendarInterval</key>", plist)
        self.assertIn("<integer>22</integer>", plist)

    def test_github_workflow_escapes_expressions_and_is_dry_by_default(self) -> None:
        text = github_workflow(self.spec)
        # An f-string that leaked its braces would emit ${{{{ }}}} and never parse.
        self.assertIn("${{ inputs.apply == true }}", text)
        self.assertNotIn("${{{{", text)
        self.assertIn("cron: '30 22 * * *'", text)
        self.assertIn("default: false", text)
        self.assertIn("fetch-depth: 0", text)

    def test_render_dispatches_and_rejects_unknown(self) -> None:
        self.assertIn("crontab-entry", render("cron", self.spec))
        self.assertIn(".github/workflows/nightly-reflect.yml", render("github", self.spec))
        self.assertEqual(len(render("systemd", self.spec)), 2)
        with self.assertRaises(ValueError):
            render("upstart", self.spec)

    def test_install_hint_names_the_files(self) -> None:
        hint = install_hint("systemd", self.spec, [Path("/tmp/oodarag-reflect.timer")])
        self.assertIn("systemctl --user enable --now", hint)


class TestParseSince(unittest.TestCase):
    def test_relative_units(self) -> None:
        now = time.time()
        self.assertAlmostEqual(parse_since("36h"), now - 36 * 3600, delta=5)
        self.assertAlmostEqual(parse_since("2d"), now - 2 * 86400, delta=5)
        self.assertAlmostEqual(parse_since("30m"), now - 1800, delta=5)
        self.assertAlmostEqual(parse_since("1w"), now - 604800, delta=5)

    def test_absolute_and_sentinels(self) -> None:
        self.assertIsNone(parse_since(None), "None means 'carry on from last cycle'")
        self.assertIsNone(parse_since(""))
        self.assertEqual(parse_since("all"), 0.0)
        self.assertEqual(parse_since("1756240000"), 1756240000.0)
        self.assertAlmostEqual(
            parse_since("2026-08-01"), time.mktime(time.strptime("2026-08-01", "%Y-%m-%d")))

    def test_garbage_is_rejected_with_a_useful_message(self) -> None:
        import argparse

        with self.assertRaises(argparse.ArgumentTypeError) as caught:
            parse_since("last tuesday")
        self.assertIn("36h", str(caught.exception))


class TestParser(unittest.TestCase):
    def test_reflect_subcommands_exist(self) -> None:
        parser = build_parser()
        for sub in ("run", "status", "report", "queue", "accept", "dismiss", "revert",
                    "rules", "schedule"):
            with self.subTest(sub=sub):
                args = parser.parse_args(["reflect", sub] + (["x"] if sub in
                                         ("accept", "dismiss", "revert") else []))
                self.assertTrue(callable(args.func))

    def test_run_defaults_to_dry(self) -> None:
        args = build_parser().parse_args(["reflect", "run"])
        self.assertFalse(args.apply, "the default must never write")

    def test_repeatable_rule_flags_accumulate(self) -> None:
        args = build_parser().parse_args(
            ["reflect", "run", "--rule", "friction", "--rule", "docs", "--skip-rule", "hygiene"])
        self.assertEqual(args.rule, ["friction", "docs"])
        self.assertEqual(args.skip_rule, ["hygiene"])


class TestNotBuiltCommands(unittest.TestCase):
    def test_stubs_exit_two_without_a_traceback(self) -> None:
        for command in ("index", "query", "eval", "demo", "loop"):
            with self.subTest(command=command):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = main([command])
                self.assertEqual(code, EXIT_NOT_BUILT)
                self.assertIn("not built yet", err.getvalue())


class TestScheduleCommand(unittest.TestCase):
    def test_prints_without_writing_by_default(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["reflect", "schedule", "--kind", "cron", "--at", "23:15"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("15 23 * * *", out.getvalue())
        self.assertIn("--write", err.getvalue())

    def test_write_creates_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["reflect", "schedule", "--kind", "systemd",
                             "--root", tmp, "--write", tmp])
            self.assertEqual(code, EXIT_OK)
            self.assertTrue((Path(tmp) / "oodarag-reflect.timer").exists())
            self.assertTrue((Path(tmp) / "oodarag-reflect.service").exists())

    def test_github_backend_writes_to_its_own_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["reflect", "schedule", "--kind", "github",
                             "--root", tmp, "--write", tmp])
            self.assertEqual(code, EXIT_OK)
            self.assertTrue((Path(tmp) / ".github/workflows/nightly-reflect.yml").exists())

    def test_bad_time_is_an_error_not_a_traceback(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(["reflect", "schedule", "--at", "nope"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("HH:MM", err.getvalue())


if __name__ == "__main__":
    unittest.main()
