"""Tests for the shell-command detectors."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oodarag.reflect.detect.base import DetectContext, registry
from oodarag.reflect.detect.terminal import (
    MAKEFILE_SECTION,
    TerminalFailureSignature,
    TerminalRepeatedCommand,
    TerminalRetryLoop,
    derive_target_name,
    makefile_has_target,
    makefile_target_proposals,
)
from oodarag.reflect.models import KIND_COMMAND, Finding, Signal

# A fixed point in time so day bucketing is deterministic on any machine.
T0 = 1_756_200_000.0
DAY = 86_400.0


def cmd(text: str, *, ts: float = T0, session: str = "zsh:a", ordinal: int = 0, **meta: object):
    return Signal(
        kind=KIND_COMMAND,
        source="shell:zsh",
        text=text,
        ts=ts,
        uri=f"~/.zsh_history#L{ordinal}",
        session=session,
        ordinal=ordinal,
        metadata=dict(meta),
    )


def sequence(texts: list[str], *, session: str = "zsh:a", start: float = T0, step: float = 30.0):
    """A chronological run of commands inside one session."""
    return [
        cmd(text, ts=start + step * index, session=session, ordinal=index)
        for index, text in enumerate(texts)
    ]


class TerminalTestCase(unittest.TestCase):
    """Shared fixture: every context is rooted in a throwaway directory.

    Rooting in a tmpdir is not tidiness - `read_text` on the default root would
    read the developer's real Makefile and make the suite depend on it.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def ctx(self, signals: list[Signal]) -> DetectContext:
        return DetectContext(signals=signals, root=self.root)

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path


# -- terminal.retry_loop ------------------------------------------------------


RETRY_RUN = [
    "pytest -q tests/unit",
    "pytest -q -x tests/unit",
    "pytest -q -x --lf tests/unit",
]


class RetryLoopTests(TerminalTestCase):
    def test_run_of_three_near_identical_commands_fires(self) -> None:
        rule = TerminalRetryLoop()
        findings = rule.run(self.ctx(sequence(RETRY_RUN)))

        self.assertEqual(len(findings), 1)
        found = findings[0]
        self.assertEqual(found.rule_id, "terminal.retry_loop")
        self.assertEqual(found.severity, "high")
        self.assertEqual(found.metadata["attempts"], 3)
        self.assertEqual(found.metadata["argv0"], "pytest")
        self.assertEqual(found.metadata["settled_command"], RETRY_RUN[-1])
        self.assertEqual(found.key, RETRY_RUN[-1])
        self.assertEqual(len(found.evidence), 3)
        self.assertIn("pytest -q tests/unit", found.evidence[0].quote)
        self.assertTrue(0.0 <= found.confidence <= 1.0)

    def test_fingerprint_is_stable_across_nights(self) -> None:
        rule = TerminalRetryLoop()
        tonight = rule.run(self.ctx(sequence(RETRY_RUN)))[0]
        tomorrow = rule.run(self.ctx(sequence(RETRY_RUN, session="zsh:b", start=T0 + DAY)))[0]
        self.assertEqual(tonight.fingerprint, tomorrow.fingerprint)

    def test_threshold_boundary(self) -> None:
        two = sequence(RETRY_RUN[:2])
        self.assertEqual(TerminalRetryLoop().run(self.ctx(two)), [])
        self.assertEqual(len(TerminalRetryLoop({"min_attempts": 2}).run(self.ctx(two))), 1)

    def test_identical_commands_are_not_a_retry_loop(self) -> None:
        # Re-running one command is waiting, not deriving; repeated_command owns it.
        findings = TerminalRetryLoop().run(self.ctx(sequence(["pytest -q tests/unit"] * 4)))
        self.assertEqual(findings, [])

    def test_a_different_program_breaks_the_run(self) -> None:
        texts = [RETRY_RUN[0], RETRY_RUN[1], "docker ps -a", RETRY_RUN[2]]
        self.assertEqual(TerminalRetryLoop().run(self.ctx(sequence(texts))), [])

    def test_incidental_commands_do_not_break_the_run(self) -> None:
        # Glancing at `git status` mid-struggle is part of the struggle.
        texts = [RETRY_RUN[0], RETRY_RUN[1], "git status", "ls", RETRY_RUN[2]]
        findings = TerminalRetryLoop().run(self.ctx(sequence(texts)))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].metadata["attempts"], 3)

    def test_dissimilar_commands_do_not_link(self) -> None:
        texts = ["pytest -q tests/unit", "pytest docs/", "pytest --collect-only -k zzz"]
        self.assertEqual(TerminalRetryLoop().run(self.ctx(sequence(texts))), [])

    def test_gap_larger_than_window_breaks_the_run(self) -> None:
        signals = sequence(RETRY_RUN, step=3600.0)  # an hour apart is not a struggle
        self.assertEqual(TerminalRetryLoop().run(self.ctx(signals)), [])
        loose = TerminalRetryLoop({"max_gap_s": 7200})
        self.assertEqual(len(loose.run(self.ctx(signals))), 1)

    def test_ignored_programs_never_produce_a_retry_loop(self) -> None:
        texts = ["vim a/one.py", "vim a/two.py", "vim a/three.py", "vim a/four.py"]
        self.assertEqual(TerminalRetryLoop().run(self.ctx(sequence(texts))), [])

    def test_evidence_is_capped_but_keeps_the_final_attempt(self) -> None:
        texts = [f"pytest -q -x --lf tests/common tests/unit_{i}" for i in range(10)]
        found = TerminalRetryLoop().run(self.ctx(sequence(texts)))[0]

        self.assertEqual(found.metadata["attempts"], 10)
        self.assertEqual(len(found.evidence), 6)
        self.assertIn("tests/unit_9", found.evidence[-1].quote)
        self.assertIn("attempt 10/10", found.evidence[-1].quote)

    def test_separate_sessions_do_not_form_one_run(self) -> None:
        signals = sequence(RETRY_RUN[:2]) + sequence(RETRY_RUN[2:], session="zsh:b", start=T0 + 60)
        self.assertEqual(TerminalRetryLoop().run(self.ctx(signals)), [])

    # -- proposals ------------------------------------------------------------

    def propose_once(self, rule, ctx: DetectContext, finding: Finding):
        proposals = rule.run_propose(finding, ctx)
        self.assertEqual(len(proposals), 1)
        return proposals[0]

    def test_proposal_creates_a_makefile_when_there_is_none(self) -> None:
        rule = TerminalRetryLoop()
        ctx = self.ctx(sequence(RETRY_RUN))
        proposal = self.propose_once(rule, ctx, rule.run(ctx)[0])

        self.assertEqual(proposal.risk, "safe")  # nothing can be lost
        edit = proposal.edits[0]
        self.assertEqual((edit.path, edit.op), ("Makefile", "create"))
        self.assertIn(MAKEFILE_SECTION, edit.text)
        self.assertIn(".PHONY: pytest-unit", edit.text)
        self.assertIn("\tpytest -q -x --lf tests/unit", edit.text)

    def test_proposal_appends_to_an_existing_makefile_for_review(self) -> None:
        self.write("Makefile", ".PHONY: build test\n\nbuild:\n\techo build\n")
        rule = TerminalRetryLoop()
        ctx = self.ctx(sequence(RETRY_RUN))
        proposal = self.propose_once(rule, ctx, rule.run(ctx)[0])

        self.assertEqual(proposal.risk, "review")  # it is the user's build file
        edit = proposal.edits[0]
        self.assertEqual(edit.op, "ensure_section")
        self.assertEqual(edit.anchor, ".PHONY: build test")
        self.assertIn("pytest-unit:", edit.text)

    def test_proposal_anchors_on_the_loops_own_section_when_present(self) -> None:
        self.write(
            "Makefile", f".PHONY: build\n\n{MAKEFILE_SECTION}\n\n.PHONY: old\nold:\n\techo\n"
        )
        rule = TerminalRetryLoop()
        ctx = self.ctx(sequence(RETRY_RUN))
        proposal = self.propose_once(rule, ctx, rule.run(ctx)[0])
        self.assertEqual(proposal.edits[0].anchor, MAKEFILE_SECTION)

    def test_existing_target_suppresses_the_proposal(self) -> None:
        self.write("Makefile", ".PHONY: pytest-unit\npytest-unit:\n\techo already here\n")
        rule = TerminalRetryLoop()
        ctx = self.ctx(sequence(RETRY_RUN))
        self.assertEqual(rule.run_propose(rule.run(ctx)[0], ctx), [])

    def test_command_already_in_the_makefile_suppresses_the_proposal(self) -> None:
        self.write("Makefile", f".PHONY: t\nt:\n\t{RETRY_RUN[-1]}\n")
        rule = TerminalRetryLoop()
        ctx = self.ctx(sequence(RETRY_RUN))
        self.assertEqual(rule.run_propose(rule.run(ctx)[0], ctx), [])


# -- terminal.repeated_command ------------------------------------------------


class RepeatedCommandTests(TerminalTestCase):
    def spread(self, text: str, runs: int, days: int) -> list[Signal]:
        """`runs` copies of one command, dealt round-robin across `days` days."""
        out: list[Signal] = []
        for index in range(runs):
            day = index % days
            out.append(
                cmd(
                    text,
                    ts=T0 + DAY * day + 60 * index,
                    session=f"zsh:{day}",
                    ordinal=index,
                )
            )
        return out

    def test_five_runs_over_two_days_fires(self) -> None:
        signals = self.spread("docker compose up -d", runs=5, days=2)
        findings = TerminalRepeatedCommand().run(self.ctx(signals))

        self.assertEqual(len(findings), 1)
        found = findings[0]
        self.assertEqual(found.key, "docker compose up -d")
        self.assertEqual(found.metadata["runs"], 5)
        self.assertEqual(found.metadata["days"], 2)
        self.assertEqual(found.severity, "medium")
        # One quote per day: five quotes from two days is the same quote five times.
        self.assertEqual(len(found.evidence), 2)

    def test_run_count_boundary(self) -> None:
        four = self.spread("docker compose up -d", runs=4, days=2)
        self.assertEqual(TerminalRepeatedCommand().run(self.ctx(four)), [])
        self.assertEqual(len(TerminalRepeatedCommand({"min_runs": 4}).run(self.ctx(four))), 1)

    def test_day_count_boundary(self) -> None:
        one_day = self.spread("docker compose up -d", runs=6, days=1)
        self.assertEqual(TerminalRepeatedCommand().run(self.ctx(one_day)), [])
        self.assertEqual(len(TerminalRepeatedCommand({"min_days": 1}).run(self.ctx(one_day))), 1)

    def test_ignore_list_excludes_cheap_commands(self) -> None:
        rule = TerminalRepeatedCommand()
        for text in ("ls -la", "cd ../other", "git status", "git log --oneline"):
            with self.subTest(text=text):
                self.assertEqual(rule.run(self.ctx(self.spread(text, runs=8, days=3))), [])

    def test_ignore_list_is_configurable(self) -> None:
        signals = self.spread("git status", runs=6, days=2)
        self.assertEqual(len(TerminalRepeatedCommand({"ignore": []}).run(self.ctx(signals))), 1)
        # `git` alone silences every subcommand, including interesting ones.
        rule = TerminalRepeatedCommand({"ignore": ["git"]})
        self.assertEqual(rule.run(self.ctx(self.spread("git push --force", 6, 2))), [])

    def test_whitespace_is_normalized_before_grouping(self) -> None:
        signals = self.spread("docker compose up -d", runs=3, days=2)
        signals += [
            cmd("docker   compose  up  -d ", ts=T0 + DAY * 2 + i, session="zsh:2", ordinal=i)
            for i in range(2)
        ]
        found = TerminalRepeatedCommand().run(self.ctx(signals))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].metadata["runs"], 5)

    def test_proposal_wraps_the_command_in_a_target(self) -> None:
        rule = TerminalRepeatedCommand()
        ctx = self.ctx(self.spread("docker compose up -d", runs=5, days=2))
        proposals = rule.run_propose(rule.run(ctx)[0], ctx)

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].risk, "safe")
        self.assertIn(".PHONY: docker-compose", proposals[0].edits[0].text)

    def test_make_commands_are_never_wrapped_in_make_targets(self) -> None:
        rule = TerminalRepeatedCommand()
        ctx = self.ctx(self.spread("make test", runs=6, days=2))
        findings = rule.run(ctx)
        self.assertEqual(len(findings), 1)  # still worth observing
        self.assertEqual(rule.run_propose(findings[0], ctx), [])


# -- terminal.failure_signature ----------------------------------------------


class FailureSignatureTests(TerminalTestCase):
    def test_exit_status_failures_fire_at_the_threshold(self) -> None:
        rule = TerminalFailureSignature()
        one = [cmd("npm run build", ts=T0, ordinal=0, exit=1)]
        self.assertEqual(rule.run(self.ctx(one)), [])

        two = one + [cmd("npm run build", ts=T0 + DAY, session="zsh:b", ordinal=1, exit=2)]
        findings = rule.run(self.ctx(two))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].key, "npm run build")
        self.assertEqual(findings[0].metadata["exit_failures"], 2)
        self.assertEqual(findings[0].metadata["exit_codes"], [1, 2])
        self.assertEqual(findings[0].metadata["mode"], "exit status")
        self.assertTrue(all("exit" in e.quote for e in findings[0].evidence))

    def test_successful_commands_are_not_failures(self) -> None:
        signals = [cmd("npm run build", ts=T0 + i, ordinal=i, exit=0) for i in range(4)]
        self.assertEqual(TerminalFailureSignature().run(self.ctx(signals)), [])

    def test_min_failures_is_configurable(self) -> None:
        signals = [cmd("npm run build", ts=T0, ordinal=0, exit=1)]
        rule = TerminalFailureSignature({"min_failures": 1})
        self.assertEqual(len(rule.run(self.ctx(signals))), 1)

    def test_sudo_retry_is_the_textual_proxy(self) -> None:
        signals = sequence(["docker ps -a", "sudo docker ps -a", "echo done"])
        findings = TerminalFailureSignature().run(self.ctx(signals))

        self.assertEqual(len(findings), 1)
        found = findings[0]
        self.assertEqual(found.key, "docker ps -a")
        self.assertEqual(found.metadata["reasons"], ["sudo"])
        self.assertEqual(found.metadata["mode"], "repair behaviour")
        self.assertIn("re-run as root", found.evidence[-1].quote)

    def test_sudo_flags_do_not_hide_the_retry(self) -> None:
        signals = sequence(["make install", "sudo -E make install"])
        self.assertEqual(len(TerminalFailureSignature().run(self.ctx(signals))), 1)

    def test_undo_command_is_the_textual_proxy(self) -> None:
        signals = sequence(["git rebase -i main", "git reset --hard HEAD@{1}"])
        findings = TerminalFailureSignature().run(self.ctx(signals))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].metadata["reasons"], ["undo"])
        self.assertIn("then undone by", findings[0].evidence[-1].quote)

    def test_unrelated_follow_up_is_not_a_failure(self) -> None:
        signals = sequence(["git rebase -i main", "git push"])
        self.assertEqual(TerminalFailureSignature().run(self.ctx(signals)), [])

    def test_similar_program_is_not_an_undo_marker(self) -> None:
        # Token-prefix matching, so `killall` is not `kill`.
        signals = sequence(["docker ps -a", "killall docker"])
        self.assertEqual(TerminalFailureSignature().run(self.ctx(signals)), [])

    def test_a_recorded_exit_status_disables_the_proxy(self) -> None:
        signals = [
            cmd("docker ps -a", ts=T0, ordinal=0, exit=0),
            cmd("sudo docker ps -a", ts=T0 + 5, ordinal=1, exit=0),
        ]
        self.assertEqual(TerminalFailureSignature().run(self.ctx(signals)), [])

    def test_a_late_follow_up_is_not_a_repair(self) -> None:
        signals = sequence(["docker ps -a", "sudo docker ps -a"], step=4000.0)
        self.assertEqual(TerminalFailureSignature().run(self.ctx(signals)), [])

    def test_the_rule_proposes_nothing(self) -> None:
        rule = TerminalFailureSignature()
        ctx = self.ctx(sequence(["docker ps -a", "sudo docker ps -a"]))
        self.assertEqual(rule.run_propose(rule.run(ctx)[0], ctx), [])


# -- shared machinery ---------------------------------------------------------


class TargetNamingTests(unittest.TestCase):
    def test_names_are_sanitized_to_a_safe_alphabet(self) -> None:
        cases = {
            "pytest -q tests/unit": "pytest-unit",
            "./scripts/Deploy.sh --prod": "deploy-prod",
            "docker compose up -d": "docker-compose",
            "sudo docker compose up": "docker-compose",
            "FOO=1 python3.11 -m pip install -e .": "python3-pip",
            "npm run build:css": "npm-run",
            "cargo build --release": "cargo-build",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                name = derive_target_name(command)
                self.assertEqual(name, expected)
                self.assertRegex(name, r"^[a-z0-9-]+$")

    def test_unnameable_commands_yield_nothing(self) -> None:
        for command in ("", "   ", "!!!", "/"):
            with self.subTest(command=command):
                self.assertEqual(derive_target_name(command), "")

    def test_names_are_length_capped(self) -> None:
        name = derive_target_name("pytest " + "x" * 200)
        self.assertLessEqual(len(name), 40)
        self.assertRegex(name, r"^[a-z0-9-]+$")

    def test_target_detection_ignores_variable_assignments(self) -> None:
        self.assertTrue(makefile_has_target("build:\n\techo\n", "build"))
        self.assertTrue(makefile_has_target("build ::\n\techo\n", "build"))
        self.assertFalse(makefile_has_target("build := yes\n", "build"))
        self.assertFalse(makefile_has_target("build ::= yes\n", "build"))
        self.assertFalse(makefile_has_target(".PHONY: build\n", "build"))
        self.assertFalse(makefile_has_target("", "build"))


class MakefileProposalTests(TerminalTestCase):
    def finding(self, key: str = "cmd") -> Finding:
        return Finding(rule_id="terminal.retry_loop", title="t", key=key)

    def propose(self, command: str, **kwargs: object):
        return makefile_target_proposals(
            self.finding(command),
            self.ctx([]),
            command=command,
            makefile=str(kwargs.pop("makefile", "Makefile")),
            title="t",
            rationale="r",
            **kwargs,
        )

    def ctx(self, signals: list[Signal]) -> DetectContext:
        return DetectContext(signals=signals, root=self.root)

    def test_dollar_signs_are_escaped_for_make(self) -> None:
        proposals = self.propose("for f in *.py; do echo $f; done")
        self.assertEqual(len(proposals), 1)
        self.assertIn("echo $$f", proposals[0].edits[0].text)

    def test_commands_containing_a_hash_are_refused(self) -> None:
        # make eats `#` even inside a recipe, so the target would not mean this.
        self.assertEqual(self.propose("git commit -m fix#12"), [])

    def test_credential_shaped_commands_are_manual(self) -> None:
        proposals = self.propose("deploy --token=<redacted:github-token> prod")
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].risk, "manual")
        self.assertIn("credential", proposals[0].rationale)

    def test_paths_outside_the_workspace_are_refused(self) -> None:
        for makefile in ("/etc/Makefile", "../Makefile", ""):
            with self.subTest(makefile=makefile):
                self.assertEqual(self.propose("pytest -q tests", makefile=makefile), [])

    def test_proposal_paths_stay_relative(self) -> None:
        proposal = self.propose("pytest -q tests/unit")[0]
        self.assertEqual(proposal.paths, ["Makefile"])
        self.assertFalse(Path(proposal.edits[0].path).is_absolute())


class HostileInputTests(TerminalTestCase):
    """Nothing typed into a shell can abort the night's run."""

    def ctx(self, signals: list[Signal]) -> DetectContext:
        return DetectContext(signals=signals, root=self.root)

    def test_malformed_commands_do_not_raise(self) -> None:
        texts = [
            'echo "unbalanced quote',
            "",
            "   ",
            "\x00\x07binary",
            "é" * 5000,
            "pytest -q 'also unbalanced",
            "pytest -q 'also unbalanced x",
        ]
        signals = sequence(texts) + [
            cmd("weird exit", ts=T0 + 500, ordinal=99, exit="not-a-number"),
            cmd("bool exit", ts=T0 + 501, ordinal=100, exit=True),
        ]
        ctx = self.ctx(signals)
        for rule in (TerminalRetryLoop(), TerminalRepeatedCommand(), TerminalFailureSignature()):
            with self.subTest(rule=rule.rule_id):
                for found in rule.run(ctx):
                    self.assertTrue(found.evidence, "a finding without evidence is an opinion")
                    for proposal in rule.run_propose(found, ctx):
                        self.assertFalse(Path(proposal.edits[0].path).is_absolute())

    def test_garbage_config_falls_back_to_defaults(self) -> None:
        rule = TerminalRetryLoop({"min_attempts": "three", "sim_threshold": None, "makefile": 7})
        self.assertEqual(rule.min_attempts, 3)
        self.assertEqual(rule.sim_threshold, 0.6)
        self.assertEqual(rule.makefile, "Makefile")
        self.assertEqual(len(rule.run(self.ctx(sequence(RETRY_RUN)))), 1)

    def test_control_characters_never_reach_a_recipe(self) -> None:
        rule = TerminalRepeatedCommand({"min_days": 1, "min_runs": 2})
        signals = [cmd("run\x07bell now", ts=T0 + i, ordinal=i) for i in range(3)]
        ctx = self.ctx(signals)
        findings = rule.run(ctx)
        self.assertEqual(len(findings), 1)
        self.assertEqual(rule.run_propose(findings[0], ctx), [])


class RegistrationTests(unittest.TestCase):
    def test_all_three_rules_are_registered(self) -> None:
        known = registry()
        for rule_id in (
            "terminal.retry_loop",
            "terminal.repeated_command",
            "terminal.failure_signature",
        ):
            with self.subTest(rule_id=rule_id):
                self.assertIn(rule_id, known)
                self.assertEqual(known[rule_id].consumes, (KIND_COMMAND,))


if __name__ == "__main__":
    unittest.main()
