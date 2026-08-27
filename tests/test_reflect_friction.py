"""Tests for the friction rules.

Signals are hand-built rather than parsed out of a fixture transcript: these
rules are a claim about *sequences of prompts*, and constructing the sequence
directly is the only way to test the claim without also testing the parser.
The only filesystem touched is a TemporaryDirectory standing in for a
workspace root - the memory-file proposals need to know whether a file exists,
and nothing else here reads disk.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oodarag.reflect.detect.base import DetectContext
from oodarag.reflect.detect.friction import (
    CONVENTIONS_HEADING,
    CORRECTIONS_HEADING,
    FrictionCorrection,
    FrictionReformulation,
    FrictionRepeatedInstruction,
    _bullet,
    already_documented,
    normalize_instruction,
    stem_token,
    strip_lead_filler,
)
from oodarag.reflect.models import (
    ACTOR_ASSISTANT,
    ACTOR_HUMAN,
    KIND_PROMPT,
    KIND_REPLY,
    Signal,
)

# A fixed point in time so day bucketing is deterministic on any machine.
T0 = 1_756_200_000.0
DAY = 86_400.0


def prompt(text: str, session: str = "s1", ts: float = T0, ordinal: int = 0,
           actor: str = ACTOR_HUMAN) -> Signal:
    return Signal(
        kind=KIND_PROMPT,
        source="chat:test",
        text=text,
        ts=ts,
        uri=f"chat://{session}#{ordinal}",
        session=session,
        ordinal=ordinal,
        actor=actor,
    )


def reply(text: str = "Sure, done.", session: str = "s1", ts: float = T0,
          ordinal: int = 0) -> Signal:
    return Signal(
        kind=KIND_REPLY,
        source="chat:test",
        text=text,
        ts=ts,
        uri=f"chat://{session}#{ordinal}",
        session=session,
        ordinal=ordinal,
        actor=ACTOR_ASSISTANT,
    )


class FrictionTestCase(unittest.TestCase):
    """Shared workspace root. Nothing here ever reads the developer's home."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def context(self, signals: list[Signal]) -> DetectContext:
        return DetectContext(signals=signals, root=self.root, now=T0 + 5 * DAY)

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path


# -- normalization -----------------------------------------------------------


class NormalizationTest(unittest.TestCase):
    def test_stemmer_collapses_inflections(self) -> None:
        self.assertEqual(stem_token("committing"), "commit")  # undoubles the "tt"
        self.assertEqual(stem_token("commits"), "commit")
        self.assertEqual(stem_token("running"), "run")
        self.assertEqual(stem_token("tests"), "test")

    def test_stemmer_leaves_risky_tokens_alone(self) -> None:
        self.assertEqual(stem_token("make"), "make")        # too short to touch
        self.assertEqual(stem_token("less"), "less")        # "ss" is not a plural
        self.assertEqual(stem_token("src/foo.py"), "src/foo.py")  # not a word
        self.assertEqual(stem_token("using"), "using")      # stem would be a stub

    def test_variants_of_one_instruction_share_a_key(self) -> None:
        first = normalize_instruction("Always run make test before committing")
        second = normalize_instruction("run make test before you commit")
        third = normalize_instruction("Please run make test before committing!")
        self.assertEqual(first, "run make test commit")
        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_negation_is_not_folded_away(self) -> None:
        never = normalize_instruction("never squash the commits")
        dont = normalize_instruction("don't squash the commits")
        always = normalize_instruction("always squash the commits")
        self.assertEqual(never, dont)  # same preference, two spellings
        self.assertNotEqual(never, always)  # opposite preference, never merged
        self.assertTrue(never.startswith("not "))

    def test_lead_filler_is_stripped_boundedly(self) -> None:
        self.assertEqual(strip_lead_filler("please always run the tests"), "run the tests")
        self.assertEqual(strip_lead_filler("use ruff"), "use ruff")  # cue words are content

    def test_empty_and_stopword_only_text_has_no_key(self) -> None:
        self.assertEqual(normalize_instruction(""), "")
        self.assertEqual(normalize_instruction("   \n\t "), "")
        self.assertEqual(normalize_instruction("the it is"), "")


# -- rule 1: repeated instruction --------------------------------------------

REPEATED = [
    prompt("Always run make test before committing", session="a", ts=T0),
    prompt("run make test before you commit", session="b", ts=T0 + DAY),
    prompt("Please run make test before committing", session="c", ts=T0 + 2 * DAY),
]


class RepeatedInstructionTest(FrictionTestCase):
    def test_fires_across_three_sessions(self) -> None:
        found = list(FrictionRepeatedInstruction().detect(self.context(REPEATED)))

        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.rule_id, "friction.repeated_instruction")
        self.assertEqual(finding.severity, "high")
        self.assertEqual(finding.key, "run make test commit")
        self.assertEqual(finding.targets, ["CLAUDE.md"])
        self.assertEqual(finding.metadata["sessions"], 3)
        self.assertEqual(finding.metadata["days"], 3)
        self.assertGreaterEqual(finding.confidence, 0.5)
        self.assertLessEqual(finding.confidence, 1.0)
        # One quote per session, and they carry their provenance.
        self.assertEqual(len(finding.evidence), 3)
        self.assertEqual({e.session for e in finding.evidence}, {"a", "b", "c"})
        self.assertTrue(all(e.uri.startswith("chat://") for e in finding.evidence))

    def test_fingerprint_is_stable_across_nights(self) -> None:
        """Tomorrow's run sees different sessions and must produce the same id."""
        tomorrow = [
            prompt("run make test before you commit", session="x", ts=T0 + 10 * DAY),
            prompt("always run make test before committing", session="y", ts=T0 + 11 * DAY),
            prompt("make sure you run make test before committing", session="z",
                   ts=T0 + 12 * DAY),
        ]
        today = list(FrictionRepeatedInstruction().detect(self.context(REPEATED)))[0]
        later = list(FrictionRepeatedInstruction().detect(self.context(tomorrow)))[0]
        self.assertEqual(today.fingerprint, later.fingerprint)

    def test_below_threshold_is_silent(self) -> None:
        self.assertEqual(list(FrictionRepeatedInstruction().detect(self.context(REPEATED[:2]))), [])

    def test_repeats_inside_one_session_are_not_a_convention(self) -> None:
        """Three times in one sitting is reformulation, not a standing preference."""
        same_session = [
            prompt("always run make test before committing", session="a", ts=T0, ordinal=i)
            for i in range(4)
        ]
        self.assertEqual(list(FrictionRepeatedInstruction().detect(self.context(same_session))), [])

    def test_threshold_is_configurable(self) -> None:
        rule = FrictionRepeatedInstruction({"min_sessions": 2})
        self.assertEqual(len(list(rule.detect(self.context(REPEATED[:2])))), 1)

    def test_non_instructions_are_ignored(self) -> None:
        chatter = []
        for idx, session in enumerate("abc"):
            chatter += [
                prompt("what does the retrieval layer do here?", session=session,
                       ts=T0 + idx * DAY),
                prompt("thanks", session=session, ts=T0 + idx * DAY, ordinal=1),
                prompt("/compact", session=session, ts=T0 + idx * DAY, ordinal=2),
                prompt("```python\nprint(1)\n```", session=session, ts=T0 + idx * DAY, ordinal=3),
            ]
        self.assertEqual(list(FrictionRepeatedInstruction().detect(self.context(chatter))), [])

    def test_assistant_turns_never_count_as_instructions(self) -> None:
        echoed = [
            prompt("always run make test before committing", session=s, ts=T0 + i * DAY,
                   actor=ACTOR_ASSISTANT)
            for i, s in enumerate("abc")
        ]
        self.assertEqual(list(FrictionRepeatedInstruction().detect(self.context(echoed))), [])

    def test_findings_are_capped(self) -> None:
        rule = FrictionRepeatedInstruction()
        rule.max_findings = 2
        signals = []
        for n in range(6):
            for i, session in enumerate("abc"):
                signals.append(
                    prompt(f"always keep module{n} under one hundred lines",
                           session=f"{session}{n}", ts=T0 + i * DAY)
                )
        self.assertEqual(len(list(rule.detect(self.context(signals)))), 6)
        self.assertEqual(len(rule.run(self.context(signals))), 2)


# -- rule 1 + 3: the shared memory-file proposal ------------------------------


class MemoryProposalTest(FrictionTestCase):
    def finding(self):
        return list(FrictionRepeatedInstruction().detect(self.context(REPEATED)))[0]

    def test_creates_the_memory_file_when_it_is_absent(self) -> None:
        ctx = self.context(REPEATED)
        rule = FrictionRepeatedInstruction()
        proposals = list(rule.propose(self.finding(), ctx))

        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.risk, "safe")  # nothing exists, nothing can be lost
        self.assertEqual(len(proposal.edits), 1)
        edit = proposal.edits[0]
        self.assertEqual(edit.op, "create")
        self.assertEqual(edit.path, "CLAUDE.md")
        self.assertIn(CONVENTIONS_HEADING, edit.text)
        self.assertIn("- Run make test before you commit.", edit.text)
        self.assertEqual(edit.anchor, "")

    def test_ensures_a_section_when_the_file_exists(self) -> None:
        self.write("CLAUDE.md", "# Project memory\n\nHand written notes.\n")
        ctx = self.context(REPEATED)
        proposal = list(FrictionRepeatedInstruction().propose(self.finding(), ctx))[0]

        self.assertEqual(proposal.risk, "review")  # it is the user's prose now
        edit = proposal.edits[0]
        self.assertEqual(edit.op, "ensure_section")
        self.assertEqual(edit.anchor, CONVENTIONS_HEADING)
        self.assertIn("Run make test before you commit.", edit.text)
        self.assertNotIn("# Project memory", edit.text)

    def test_verbatim_duplicate_is_not_proposed_again(self) -> None:
        self.write(
            "CLAUDE.md",
            f"# Project memory\n\n{CONVENTIONS_HEADING}\n\n- Run make test before you commit.\n",
        )
        ctx = self.context(REPEATED)
        self.assertEqual(list(FrictionRepeatedInstruction().propose(self.finding(), ctx)), [])

    def test_the_users_own_phrasing_also_suppresses(self) -> None:
        """Already written by hand, in other words: still already documented."""
        self.write("CLAUDE.md", "# Rules\n\n* Always run make test before committing.\n")
        ctx = self.context(REPEATED)
        self.assertEqual(list(FrictionRepeatedInstruction().propose(self.finding(), ctx)), [])

    def test_already_documented_is_conservative_about_junk(self) -> None:
        self.assertTrue(already_documented("anything", ""))
        self.assertFalse(already_documented("", "use ruff for linting"))

    def test_a_memory_file_outside_the_workspace_is_refused(self) -> None:
        ctx = self.context(REPEATED)
        for escape in ("../evil.md", "/etc/passwd"):
            rule = FrictionRepeatedInstruction({"memory_file": escape})
            self.assertEqual(list(rule.propose(self.finding(), ctx)), [], escape)

    def test_the_memory_file_is_configurable(self) -> None:
        rule = FrictionRepeatedInstruction({"memory_file": "docs/conventions.md"})
        proposal = list(rule.propose(self.finding(), self.context(REPEATED)))[0]
        self.assertEqual(proposal.edits[0].path, "docs/conventions.md")

    def test_credentials_are_never_automated(self) -> None:
        signals = []
        for idx, session in enumerate("abc"):
            signals.append(
                prompt("always read the api key from .env, never from the source",
                       session=session, ts=T0 + idx * DAY)
            )
        ctx = self.context(signals)
        rule = FrictionRepeatedInstruction()
        finding = list(rule.detect(ctx))[0]
        proposal = list(rule.propose(finding, ctx))[0]
        self.assertEqual(proposal.risk, "manual")

    def test_proposal_paths_stay_relative(self) -> None:
        ctx = self.context(REPEATED)
        rule = FrictionRepeatedInstruction()
        # run_propose is the guarded entry point the loop actually calls.
        proposals = rule.run_propose(self.finding(), ctx)
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].paths, ["CLAUDE.md"])


# -- rule 2: reformulation ---------------------------------------------------

REFORMULATED = [
    prompt("can you summarize the design doc for the retrieval layer",
           session="s1", ts=T0, ordinal=0),
    prompt("summarize the design doc for the retrieval layer please",
           session="s1", ts=T0 + 60, ordinal=1),
    prompt("summarize the retrieval layer design doc in three bullets",
           session="s1", ts=T0 + 200, ordinal=2),
]


class ReformulationTest(FrictionTestCase):
    def test_fires_once_per_run_not_once_per_pair(self) -> None:
        found = list(FrictionReformulation().detect(self.context(REFORMULATED)))

        self.assertEqual(len(found), 1)  # two similar pairs, one problem
        finding = found[0]
        self.assertEqual(finding.rule_id, "friction.reformulation")
        self.assertEqual(finding.severity, "medium")
        self.assertEqual(finding.metadata["attempts"], 3)
        self.assertEqual(finding.metadata["restatements"], 2)
        self.assertEqual(finding.metadata["session"], "s1")
        self.assertEqual(finding.metadata["span_s"], 200.0)
        self.assertGreaterEqual(finding.metadata["similarity"], 0.6)
        self.assertEqual(len(finding.evidence), 3)
        # Keyed on the phrasing that finally landed, so it survives to tomorrow.
        self.assertEqual(finding.key, normalize_instruction(REFORMULATED[-1].text))

    def test_confidence_rises_with_the_number_of_restatements(self) -> None:
        rule = FrictionReformulation()
        short = list(rule.detect(self.context(REFORMULATED[:2])))[0]
        longer = list(rule.detect(self.context(REFORMULATED)))[0]
        self.assertGreater(longer.confidence, short.confidence)
        self.assertLessEqual(longer.confidence, 1.0)

    def test_dissimilar_prompts_do_not_fire(self) -> None:
        unrelated = [
            prompt("summarize the design doc for the retrieval layer", ts=T0, ordinal=0),
            prompt("now add a systemd unit for the nightly job", ts=T0 + 60, ordinal=1),
        ]
        self.assertEqual(list(FrictionReformulation().detect(self.context(unrelated))), [])

    def test_similar_prompts_far_apart_in_time_do_not_fire(self) -> None:
        far = [
            REFORMULATED[0],
            prompt(REFORMULATED[1].text, session="s1", ts=T0 + 4 * 3600, ordinal=1),
        ]
        self.assertEqual(list(FrictionReformulation().detect(self.context(far))), [])

    def test_similar_prompts_in_different_sessions_do_not_fire(self) -> None:
        split = [
            prompt(REFORMULATED[0].text, session="s1", ts=T0, ordinal=0),
            prompt(REFORMULATED[1].text, session="s2", ts=T0 + 60, ordinal=0),
        ]
        self.assertEqual(list(FrictionReformulation().detect(self.context(split))), [])

    def test_thresholds_are_configurable(self) -> None:
        strict = FrictionReformulation({"sim_threshold": 0.99})
        self.assertEqual(list(strict.detect(self.context(REFORMULATED))), [])
        narrow = FrictionReformulation({"window_s": 30})
        self.assertEqual(list(narrow.detect(self.context(REFORMULATED))), [])

    def test_a_single_retry_is_observation_only(self) -> None:
        ctx = self.context(REFORMULATED[:2])
        rule = FrictionReformulation()
        finding = list(rule.detect(ctx))[0]
        self.assertEqual(list(rule.propose(finding, ctx)), [])

    def test_three_attempts_propose_the_accepted_phrasing(self) -> None:
        ctx = self.context(REFORMULATED)
        rule = FrictionReformulation()
        finding = list(rule.detect(ctx))[0]
        proposals = list(rule.propose(finding, ctx))

        self.assertEqual(len(proposals), 1)
        # A guess about intent is never applied unattended, even into a file
        # that does not exist yet.
        self.assertEqual(proposals[0].risk, "review")
        self.assertIn("three bullets", proposals[0].edits[0].text)


# -- rule 3: correction ------------------------------------------------------


def corrected_session(text: str, session: str = "s1", ts: float = T0) -> list[Signal]:
    return [
        prompt("format the project", session=session, ts=ts, ordinal=0),
        reply("Running black over the tree.", session=session, ts=ts + 10, ordinal=1),
        prompt(text, session=session, ts=ts + 20, ordinal=2),
    ]


class CorrectionTest(FrictionTestCase):
    def test_fires_on_a_prompt_that_repairs_the_previous_reply(self) -> None:
        signals = corrected_session("No, that's wrong. Use ruff for linting, not black.")
        found = list(FrictionCorrection().detect(self.context(signals)))

        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.rule_id, "friction.correction")
        # The marker and the complaint are dropped; the preference is kept.
        self.assertEqual(finding.metadata["instruction"], "Use ruff for linting, not black")
        self.assertEqual(finding.key, "use ruff lint black")
        self.assertTrue(finding.metadata["opened_with_marker"])
        self.assertEqual(finding.severity, "medium")  # one correction, so far
        # The corrected reply is quoted alongside the correction itself.
        self.assertEqual(len(finding.evidence), 2)
        self.assertIn("corrected reply:", finding.evidence[-1].quote)

    def test_marker_prefixes_are_stripped_from_the_instruction(self) -> None:
        rule = FrictionCorrection()
        cases = {
            "no, use tabs in the Makefile": "use tabs in the Makefile",
            "Nope. Use tabs in the Makefile.": "Use tabs in the Makefile",
            "actually, use tabs in the Makefile": "use tabs in the Makefile",
            "That's not what I asked - use tabs in the Makefile": "use tabs in the Makefile",
        }
        for text, expected in cases.items():
            self.assertEqual(rule.instruction_from(text), expected, text)

    def test_a_prompt_with_no_reply_before_it_is_not_a_correction(self) -> None:
        signals = [prompt("No, use ruff for linting, not black.", ts=T0, ordinal=0)]
        self.assertEqual(list(FrictionCorrection().detect(self.context(signals))), [])

    def test_a_prompt_with_no_marker_is_not_a_correction(self) -> None:
        signals = corrected_session("Now update the README to match.")
        self.assertEqual(list(FrictionCorrection().detect(self.context(signals))), [])

    def test_pure_annoyance_carries_no_preference(self) -> None:
        """A bare "no, that's wrong" is a mood, not an instruction to record."""
        signals = corrected_session("no, that's wrong")
        self.assertEqual(list(FrictionCorrection().detect(self.context(signals))), [])

    def test_repeats_raise_severity_and_confidence(self) -> None:
        once = corrected_session("No, use ruff for linting, not black.", session="s1", ts=T0)
        twice = once + corrected_session(
            "Nope. Use ruff for linting, not black.", session="s2", ts=T0 + DAY
        )
        rule = FrictionCorrection()
        single = list(rule.detect(self.context(once)))[0]
        repeated = list(rule.detect(self.context(twice)))[0]

        self.assertEqual(repeated.metadata["occurrences"], 2)
        self.assertEqual(repeated.metadata["sessions"], 2)
        self.assertEqual(repeated.severity, "high")
        self.assertGreater(repeated.confidence, single.confidence)
        self.assertEqual(repeated.key, single.key)  # one preference, not two

    def test_late_markers_are_not_corrections(self) -> None:
        essay = (
            "Here is the plan for the migration, which is long and detailed and "
            "describes each of the steps in order before it finally gets around to "
            "mentioning that something is wrong with the old approach."
        )
        signals = corrected_session(essay)
        self.assertEqual(list(FrictionCorrection().detect(self.context(signals))), [])

    def test_proposal_goes_under_the_corrections_heading(self) -> None:
        signals = corrected_session("No, that's wrong. Use ruff for linting, not black.")
        ctx = self.context(signals)
        rule = FrictionCorrection()
        finding = list(rule.detect(ctx))[0]

        created = list(rule.propose(finding, ctx))
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].risk, "safe")
        self.assertEqual(created[0].edits[0].op, "create")
        self.assertIn(CORRECTIONS_HEADING, created[0].edits[0].text)
        self.assertIn("- Use ruff for linting, not black.", created[0].edits[0].text)

        self.write("CLAUDE.md", "# Project memory\n")
        existing_ctx = self.context(signals)
        reviewed = list(rule.propose(finding, existing_ctx))[0]
        self.assertEqual(reviewed.risk, "review")
        self.assertEqual(reviewed.edits[0].op, "ensure_section")
        self.assertEqual(reviewed.edits[0].anchor, CORRECTIONS_HEADING)

    def test_already_documented_correction_is_not_reproposed(self) -> None:
        signals = corrected_session("No, that's wrong. Use ruff for linting, not black.")
        self.write(
            "CLAUDE.md",
            f"# Project memory\n\n{CORRECTIONS_HEADING}\n\n- Use ruff for linting, not black.\n",
        )
        ctx = self.context(signals)
        rule = FrictionCorrection()
        finding = list(rule.detect(ctx))[0]
        self.assertEqual(list(rule.propose(finding, ctx)), [])


# -- hostile input -----------------------------------------------------------


class HostileInputTest(FrictionTestCase):
    """Nothing in a transcript is trustworthy, and none of it may abort the run."""

    def hostile_signals(self) -> list[Signal]:
        junk = [
            prompt("", session="h", ts=T0, ordinal=0),
            prompt("   \n\n\t  ", session="h", ts=T0, ordinal=1),
            prompt("\x00\x01\x02", session="h", ts=T0, ordinal=2),
            prompt("always " * 4000, session="h", ts=T0, ordinal=3),
            prompt("no, " + "x" * 20_000, session="h", ts=T0, ordinal=4),
            reply("", session="h", ts=T0, ordinal=5),
            prompt("no, ???!!! ***", session="h", ts=T0, ordinal=6),
            prompt("```\nnot code but pasted anyway\n```", session="h", ts=T0, ordinal=7),
            # No session and no timestamp: the source could not tell us either.
            Signal(kind=KIND_PROMPT, source="chat:test", text="?" * 300, ts=0.0),
            Signal(kind=KIND_REPLY, source="chat:test", text="ok", ts=0.0),
        ]
        # One real, findable instruction buried in the junk, so the assertions
        # below are about a rule that fired rather than about silence.
        real = [
            prompt("always use ruff for linting", session=s, ts=T0 + i * DAY, ordinal=9)
            for i, s in enumerate(("h", "i", "j"))
        ]
        return junk + real

    def test_every_rule_survives_hostile_input(self) -> None:
        ctx = self.context(self.hostile_signals())
        fired = 0
        for rule in (FrictionRepeatedInstruction(), FrictionReformulation(), FrictionCorrection()):
            findings = list(rule.detect(ctx))  # detect(), not run(): no safety net
            fired += len(findings)
            for finding in findings:
                self.assertTrue(finding.evidence, f"{rule.rule_id} produced an opinion")
                self.assertTrue(0.0 <= finding.confidence <= 1.0)
                for proposal in rule.run_propose(finding, ctx):
                    for edit in proposal.edits:
                        self.assertFalse(Path(edit.path).is_absolute())
                        self.assertNotIn("..", Path(edit.path).parts)
        self.assertEqual(fired, 1)  # the buried instruction, and nothing the junk implied

    def test_an_oversized_instruction_is_not_written_to_the_memory_file(self) -> None:
        """A finding can be worth reporting and still be too long to be a bullet."""
        essay = "always " + " ".join(f"consideration{i}" for i in range(80))
        signals = [
            prompt(essay, session=s, ts=T0 + i * DAY) for i, s in enumerate("abc")
        ]
        rule = FrictionRepeatedInstruction({"max_words": 200})
        ctx = self.context(signals)
        finding = list(rule.detect(ctx))[0]
        self.assertEqual(list(rule.propose(finding, ctx)), [])

    def test_broken_config_falls_back_to_defaults(self) -> None:
        """Rule config is hand-written JSON; a quoted or bogus threshold is normal."""
        rule = FrictionRepeatedInstruction({"min_sessions": "3", "max_words": None,
                                            "memory_file": "  "})
        self.assertEqual(rule.min_sessions, 3)
        self.assertEqual(rule.max_words, 60)
        self.assertEqual(rule.memory_file, "CLAUDE.md")
        self.assertEqual(len(list(rule.detect(self.context(REPEATED)))), 1)

    def test_an_unreadable_memory_file_is_treated_as_absent(self) -> None:
        (self.root / "CLAUDE.md").mkdir()  # a directory where a file was expected
        ctx = self.context(REPEATED)
        rule = FrictionRepeatedInstruction()
        finding = list(rule.detect(ctx))[0]
        proposal = list(rule.propose(finding, ctx))[0]
        self.assertEqual(proposal.edits[0].op, "create")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class TestCorrectionMeaningIsPreserved(unittest.TestCase):
    """A correction must never be written down as its own opposite.

    These are regression tests for the worst bug this subsystem can have. The
    marker list is used for two different jobs - deciding that a prompt is a
    correction, and trimming the throat-clearing off the front of it - and the
    words that do the first job are not all safe for the second. "don't" marks a
    correction and is also the entire meaning of it.
    """

    def setUp(self) -> None:
        self.rule = FrictionCorrection()

    def instruction(self, text: str) -> str:
        return self.rule.instruction_from(text)

    def test_negation_survives_extraction(self) -> None:
        cases = [
            ("nope, don't force push. Use --force-with-lease instead.", "don't force push"),
            ("wrong, do not commit the lockfile", "do not commit"),
            ("no, never push to main - use a feature branch", "never push to main"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                got = self.instruction(raw).lower()
                self.assertIn(expected, got)

    def test_the_inverted_form_is_never_produced(self) -> None:
        got = self.instruction("nope, don't force push. Use --force-with-lease instead.")
        self.assertFalse(
            got.lower().startswith("force push"),
            f"the instruction was inverted: {got!r}",
        )

    def test_imperative_verbs_that_are_also_markers_survive(self) -> None:
        """'stop', 'revert' and 'undo' are the instruction, not a preamble."""
        for raw, expected in [
            ("actually, stop using pytest fixtures here", "stop using"),
            ("no, revert that migration", "revert that migration"),
            ("actually undo the rename", "undo the rename"),
        ]:
            with self.subTest(raw=raw):
                self.assertIn(expected, self.instruction(raw).lower())

    def test_discourse_markers_are_still_stripped(self) -> None:
        """The split must not cost us the trimming it was there to do."""
        got = self.instruction("no, that's wrong. Use ruff for linting.")
        # instruction_from returns the bare clause; _bullet is what punctuates it.
        self.assertEqual(got, "Use ruff for linting")
        self.assertNotIn("wrong", got.lower())
        self.assertEqual(_bullet(got), "- Use ruff for linting.")

    def test_a_correction_is_still_recognised_by_a_non_strippable_marker(self) -> None:
        self.assertIsNotNone(self.rule.marker_in("don't force push to main"))
        self.assertIsNotNone(self.rule.marker_in("stop reformatting the imports"))

    def test_clause_boundaries_survive_the_rejoin(self) -> None:
        """A dash separator is consumed by the splitter; the pause must come back."""
        self.assertEqual(
            _bullet(self.instruction("no, never push to main - use a feature branch")),
            "- Never push to main, use a feature branch.",
        )
        self.assertEqual(
            _bullet(self.instruction("nope, don't force push. Use --force-with-lease instead.")),
            "- Don't force push. Use --force-with-lease instead.",
        )

    def test_a_configured_marker_list_still_protects_negation(self) -> None:
        rule = FrictionCorrection({"markers": ["no,", "don't", "stop"]})
        self.assertIn("don't deploy", rule.instruction_from("no, don't deploy on fridays").lower())
