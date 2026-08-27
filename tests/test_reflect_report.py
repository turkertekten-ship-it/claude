"""Tests for what the user actually sees: the review queue and the briefing.

Two failures here are worse than a crash, because both are silent. A prefix
lookup that guesses applies an edit the user never read - so the ambiguous case
is asserted to raise, and to name its candidates. A round trip through the queue
that changes a fingerprint invalidates every accept, dismiss and learned prior
keyed on it, without anything appearing to go wrong - so the round trip is
asserted byte for byte.

The report tests are mostly about restraint: a briefing that prints a skeleton on
a quiet night trains people to skim past the headings, including on the night one
of them matters. Everything is built in a temp directory; nothing reads a real
journal, queue or home directory.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from oodarag.reflect.act.queue import ReviewQueue, proposal_from_dict
from oodarag.reflect.act.report import (
    MAX_DIFF_LINES,
    MAX_OBSERVATIONS_PER_RULE,
    render_json,
    render_markdown,
    write_report,
)
from oodarag.reflect.models import CycleReport, EditOp, Evidence, Finding, Proposal

DAY_S = 86_400.0


# -- fixtures ----------------------------------------------------------------


@dataclass
class FakeEditResult:
    """Duck-typed stand-in for `act.edits.EditResult`."""

    path: str
    applied: bool = True
    reason: str = ""
    diff: str = ""


@dataclass
class FakeApplyReport:
    results: list[FakeEditResult] = field(default_factory=list)


def make_proposal(
    key: str = "k",
    *,
    rule_id: str = "docs.missing_target",
    risk: str = "review",
    paths: tuple[str, ...] = ("README.md",),
    quotes: tuple[str, ...] = ("how do I run the tests again",),
    score: float = 0.42,
) -> Proposal:
    finding = Finding(
        rule_id=rule_id,
        title=f"finding {key}",
        detail=f"detail for {key}",
        severity="high",
        confidence=0.75,
        key=key,
        targets=list(paths),
        evidence=[
            Evidence(quote=q, uri=f"chat://{key}/{i}", ts=1_800_000_000.0 + i, source="chat")
            for i, q in enumerate(quotes)
        ],
        tags=["docs", "friction"],
        metadata={"count": 4, "nested": {"a": 1}},
    )
    return Proposal(
        finding=finding,
        title=f"fix {key}",
        rationale=f"because of {key}",
        edits=[EditOp(path=p, op="append", text=f"text {key}\n", note="n") for p in paths],
        risk=risk,
        impact=0.8,
        effort=0.2,
        score=score,
        score_parts={"severity": 0.75, "score": score},
    )


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    @property
    def queue_path(self) -> Path:
        return self.root / "state" / "queue.json"


# -- round-tripping ----------------------------------------------------------


class TestProposalRoundTrip(TempCase):
    def test_dict_round_trip_preserves_the_fingerprint(self) -> None:
        original = make_proposal("round", paths=("README.md", "docs/guide.md"))
        rebuilt = proposal_from_dict(original.as_dict())
        self.assertEqual(rebuilt.fingerprint, original.fingerprint)
        self.assertEqual(rebuilt.finding.fingerprint, original.finding.fingerprint)

    def test_round_trip_preserves_every_field_the_actuator_reads(self) -> None:
        original = make_proposal("full", paths=("a.md", "b.md"))
        rebuilt = proposal_from_dict(original.as_dict())
        self.assertEqual(rebuilt.as_dict(), original.as_dict())
        self.assertEqual([e.path for e in rebuilt.edits], ["a.md", "b.md"])
        self.assertEqual([e.text for e in rebuilt.edits], ["text full\n", "text full\n"])
        self.assertEqual(rebuilt.finding.metadata, {"count": 4, "nested": {"a": 1}})
        self.assertEqual(rebuilt.finding.evidence[0].uri, "chat://full/0")

    def test_round_trip_survives_the_queue_file(self) -> None:
        original = make_proposal("via-disk")
        queue = ReviewQueue(self.queue_path)
        queue.put([original], "cycle-1")
        entry = queue.get(original.fingerprint[:8])
        assert entry is not None
        self.assertEqual(proposal_from_dict(entry["proposal"]).fingerprint, original.fingerprint)

    def test_a_malformed_record_raises_rather_than_half_building(self) -> None:
        for bad in ({}, {"finding": "not a dict"}, [], "nope", {"finding": {}, "edits": [{}]}):
            with self.assertRaises(ValueError):
                proposal_from_dict(bad)  # type: ignore[arg-type]

    def test_unknown_extra_keys_do_not_break_rebuilding(self) -> None:
        payload = make_proposal("extra").as_dict()
        payload["invented_by_a_newer_build"] = {"x": 1}
        payload["finding"]["also_new"] = [1, 2]
        self.assertEqual(proposal_from_dict(payload).title, "fix extra")


# -- queue mechanics ---------------------------------------------------------


class TestReviewQueue(TempCase):
    def test_put_is_an_upsert_that_bumps_times_seen(self) -> None:
        queue = ReviewQueue(self.queue_path)
        proposal = make_proposal("nag")
        self.assertEqual(queue.put([proposal], "cycle-1"), 1)
        self.assertEqual(queue.put([proposal], "cycle-2"), 0, "a re-queue is not a new row")

        items = queue.items()
        self.assertEqual(len(items), 1, "the same proposal must never duplicate")
        self.assertEqual(items[0]["times_seen"], 2)
        self.assertEqual(items[0]["first_cycle"], "cycle-1")
        self.assertEqual(items[0]["last_cycle"], "cycle-2")

    def test_put_refreshes_the_body_but_keeps_a_human_verdict(self) -> None:
        queue = ReviewQueue(self.queue_path)
        proposal = make_proposal("verdict")
        queue.put([proposal], "cycle-1")
        queue.accept(proposal.fingerprint)

        proposal.score = 0.99  # re-scored by tonight's priors
        queue.put([proposal], "cycle-2")

        entry = queue.get(proposal.fingerprint)
        assert entry is not None
        self.assertEqual(entry["status"], "accepted", "re-proposing must not undo an accept")
        self.assertAlmostEqual(entry["proposal"]["score"], 0.99)
        self.assertEqual([e["fingerprint"] for e in queue.accepted()], [proposal.fingerprint])

    def test_pending_and_accepted_are_disjoint_views(self) -> None:
        queue = ReviewQueue(self.queue_path)
        keep, take, drop = (make_proposal(k) for k in ("keep", "take", "drop"))
        queue.put([keep, take, drop], "cycle-1")
        self.assertEqual(len(queue.pending()), 3)

        queue.accept(take.fingerprint)
        queue.dismiss(drop.fingerprint, note="not how we do it here")

        self.assertEqual([e["fingerprint"] for e in queue.pending()], [keep.fingerprint])
        self.assertEqual([e["fingerprint"] for e in queue.accepted()], [take.fingerprint])
        dismissed = queue.dismissed()
        self.assertEqual(dismissed[0]["note"], "not how we do it here")
        self.assertGreater(dismissed[0]["decided_at"], 0.0)

    def test_verdicts_on_a_missing_entry_return_none(self) -> None:
        queue = ReviewQueue(self.queue_path)
        queue.put([make_proposal("only")], "cycle-1")
        self.assertIsNone(queue.accept("deadbeef"))
        self.assertIsNone(queue.dismiss("deadbeef"))
        self.assertIsNone(queue.get("deadbeef"))
        self.assertIsNone(queue.get(""))

    def test_drop_removes_an_applied_entry(self) -> None:
        queue = ReviewQueue(self.queue_path)
        proposal = make_proposal("done")
        queue.put([proposal, make_proposal("other")], "cycle-1")
        queue.drop(proposal.fingerprint)
        self.assertEqual(len(queue.items()), 1)
        queue.drop(proposal.fingerprint)  # dropping twice is not an error
        self.assertEqual(len(queue.items()), 1)

    def test_items_are_ranked_by_score_so_the_report_and_queue_agree(self) -> None:
        queue = ReviewQueue(self.queue_path)
        queue.put(
            [make_proposal("low", score=0.1), make_proposal("high", score=0.9)],
            "cycle-1",
        )
        self.assertEqual([e["proposal"]["title"] for e in queue.items()], ["fix high", "fix low"])

    def test_returned_entries_are_copies(self) -> None:
        queue = ReviewQueue(self.queue_path)
        proposal = make_proposal("copy")
        queue.put([proposal], "cycle-1")
        entry = queue.get(proposal.fingerprint)
        assert entry is not None
        entry["status"] = "accepted"
        entry["proposal"]["edits"][0]["text"] = "sabotage"

        fresh = queue.get(proposal.fingerprint)
        assert fresh is not None
        self.assertEqual(fresh["status"], "pending")
        self.assertEqual(fresh["proposal"]["edits"][0]["text"], "text copy\n")


class TestPrefixLookup(TempCase):
    def seed(self, *fingerprints: str) -> ReviewQueue:
        """Write the file by hand: real fingerprints never collide on demand."""
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        body = make_proposal("seed").as_dict()
        self.queue_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "entries": [
                        {
                            "fingerprint": fp,
                            "status": "pending",
                            "times_seen": 1,
                            "first_seen": time.time(),
                            "last_seen": time.time(),
                            "proposal": dict(body, fingerprint=fp),
                        }
                        for fp in fingerprints
                    ],
                },
                indent=2,
            ),
            "utf-8",
        )
        return ReviewQueue(self.queue_path)

    def test_an_eight_char_prefix_resolves(self) -> None:
        queue = self.seed("abcdef1200000000", "99998888aaaabbbb")
        entry = queue.get("abcdef12")
        assert entry is not None
        self.assertEqual(entry["fingerprint"], "abcdef1200000000")

    def test_an_ambiguous_prefix_raises_and_names_the_candidates(self) -> None:
        queue = self.seed("abcdef1200000000", "abcdef1299999999")
        with self.assertRaises(ValueError) as caught:
            queue.get("abcdef12")
        message = str(caught.exception)
        self.assertIn("abcdef1200", message)
        self.assertIn("abcdef1299", message)
        for action in (queue.accept, queue.dismiss):
            with self.assertRaises(ValueError):
                action("abcdef12")

    def test_an_exact_fingerprint_is_never_ambiguous(self) -> None:
        queue = self.seed("abcdef12", "abcdef1299999999")
        entry = queue.get("abcdef12")
        assert entry is not None
        self.assertEqual(entry["fingerprint"], "abcdef12")

    def test_an_ambiguous_drop_removes_nothing(self) -> None:
        queue = self.seed("abcdef1200000000", "abcdef1299999999")
        queue.drop("abcdef12")
        self.assertEqual(len(queue.items()), 2, "guessing here would delete a real decision")


class TestPruneAndCorruption(TempCase):
    def age(self, fingerprint: str, days: float) -> None:
        data = json.loads(self.queue_path.read_text("utf-8"))
        for entry in data["entries"]:
            if entry["fingerprint"] == fingerprint:
                entry["last_seen"] = time.time() - days * DAY_S
                if entry.get("decided_at"):
                    entry["decided_at"] = time.time() - days * DAY_S
        self.queue_path.write_text(json.dumps(data), "utf-8")

    def test_prune_drops_only_stale_untouched_entries(self) -> None:
        queue = ReviewQueue(self.queue_path)
        old, fresh, accepted = (make_proposal(k) for k in ("old", "fresh", "accepted"))
        queue.put([old, fresh, accepted], "cycle-1")
        queue.accept(accepted.fingerprint)
        self.age(old.fingerprint, 45)
        self.age(accepted.fingerprint, 45)

        self.assertEqual(queue.prune(max_age_days=30.0), 1)
        remaining = {e["fingerprint"] for e in queue.items()}
        self.assertEqual(remaining, {fresh.fingerprint, accepted.fingerprint})
        self.assertEqual(queue.prune(max_age_days=30.0), 0, "prune is idempotent")

    def test_prune_with_no_age_limit_keeps_everything(self) -> None:
        queue = ReviewQueue(self.queue_path)
        proposal = make_proposal("kept")
        queue.put([proposal], "cycle-1")
        self.age(proposal.fingerprint, 4000)
        self.assertEqual(queue.prune(max_age_days=0.0), 0)
        self.assertEqual(len(queue.items()), 1)

    def test_a_corrupt_file_reads_as_empty_and_then_heals(self) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue_path.write_text("{not json at all", "utf-8")
        queue = ReviewQueue(self.queue_path)
        self.assertEqual(queue.items(), [])
        self.assertEqual(queue.pending(), [])
        self.assertIsNone(queue.get("abcdef12"))

        proposal = make_proposal("after-corruption")
        self.assertEqual(queue.put([proposal], "cycle-1"), 1)
        self.assertEqual(len(ReviewQueue(self.queue_path).items()), 1)

    def test_hostile_shapes_are_ignored_entry_by_entry(self) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue_path.write_text(
            json.dumps(
                {
                    "entries": [
                        "a bare string",
                        {"no_fingerprint": True},
                        {"fingerprint": "cafe0001", "proposal": "not a dict"},
                        {"fingerprint": "cafe0002", "proposal": {"title": "survivor"}},
                    ]
                }
            ),
            "utf-8",
        )
        items = ReviewQueue(self.queue_path).items()
        self.assertEqual([e["fingerprint"] for e in items], ["cafe0002"])

    def test_a_missing_file_is_an_empty_queue_not_an_error(self) -> None:
        queue = ReviewQueue(self.root / "never" / "written" / "queue.json")
        self.assertEqual(queue.items(), [])
        self.assertEqual(len(queue), 0)
        self.assertIsNone(queue.accept("abcdef12"))

    def test_a_top_level_list_is_still_readable(self) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue_path.write_text(
            json.dumps([{"fingerprint": "cafe0003", "proposal": {"title": "legacy"}}]), "utf-8"
        )
        self.assertEqual(len(ReviewQueue(self.queue_path).items()), 1)


# -- the briefing ------------------------------------------------------------


def applied_report(*results: FakeEditResult) -> FakeApplyReport:
    return FakeApplyReport(results=list(results))


class TestEmptyReport(TempCase):
    def test_a_quiet_night_is_three_lines(self) -> None:
        markdown = render_markdown(CycleReport(cycle_id="20260827-020000"), None, [], {})
        lines = markdown.splitlines()
        self.assertEqual(len(lines), 3, f"expected a three-line report, got:\n{markdown}")
        self.assertTrue(lines[0].startswith("# Nightly review - "))
        self.assertIn("0 signals observed", lines[2])
        self.assertNotIn("##", markdown)
        self.assertNotIn("None", markdown)

    def test_every_section_is_omitted_when_it_has_nothing_to_say(self) -> None:
        report = CycleReport(cycle_id="c", dry_run=False)
        report.proposals = [make_proposal("q")]
        report.queued = [report.proposals[0].fingerprint]
        markdown = render_markdown(report, None, [], {})

        self.assertIn("## Awaiting your call", markdown)
        for absent in ("## Applied", "## Observations", "## What the loop learned", "## Errors"):
            self.assertNotIn(absent, markdown)


class TestPopulatedReport(TempCase):
    def build(self) -> tuple[CycleReport, FakeApplyReport, Proposal, Proposal]:
        done = make_proposal("done", risk="safe", paths=("Makefile",))
        waiting = make_proposal(
            "waiting", paths=("README.md",), quotes=("how do I run the tests again", "and again")
        )
        report = CycleReport(cycle_id="20260827-020000", dry_run=False)
        report.signals = 128
        orphan = Finding(
            rule_id="hygiene.stale",
            title="orphan note",
            key="o",
            severity="low",
            targets=["notes/old.md"],
        )
        report.findings = [done.finding, waiting.finding, orphan]
        report.proposals = [done, waiting]
        report.applied = [done.fingerprint]
        report.queued = [waiting.fingerprint]
        applied = applied_report(
            FakeEditResult(
                path="Makefile",
                applied=True,
                diff="--- a/Makefile\n+++ b/Makefile\n+test:\n+\tpython -m unittest\n",
            )
        )
        return report, applied, done, waiting

    def test_it_leads_with_a_verdict_then_what_changed(self) -> None:
        report, applied, _, _ = self.build()
        markdown = render_markdown(report, applied, [], {})
        self.assertIn("128 signals observed, 3 findings, 1 applied, 1 awaiting your call.",
                      markdown)
        self.assertLess(markdown.index("## Applied"), markdown.index("## Awaiting your call"))
        self.assertLess(markdown.index("## Awaiting your call"), markdown.index("## Observations"))

    def test_applied_changes_carry_their_diff_in_a_collapsed_block(self) -> None:
        report, applied, done, _ = self.build()
        markdown = render_markdown(report, applied, [], {})
        self.assertIn("<details><summary><code>Makefile</code></summary>", markdown)
        self.assertIn("```diff", markdown)
        self.assertIn("+\tpython -m unittest", markdown)
        self.assertIn("</details>", markdown)
        self.assertIn(done.fingerprint[:8], markdown)
        self.assertIn("ooda reflect revert 20260827-020000", markdown)

    def test_queued_items_carry_evidence_and_the_exact_commands(self) -> None:
        report, applied, _, waiting = self.build()
        markdown = render_markdown(report, applied, [], {})
        short = waiting.fingerprint[:8]
        self.assertIn(f"`ooda reflect accept {short}`", markdown)
        self.assertIn(f"`ooda reflect dismiss {short}`", markdown)
        self.assertIn("> how do I run the tests again", markdown)
        self.assertIn("because of waiting", markdown)

    def test_findings_without_a_proposal_appear_as_observations(self) -> None:
        report, applied, _, _ = self.build()
        markdown = render_markdown(report, applied, [], {})
        observations = markdown.split("## Observations", 1)[1]
        self.assertIn("**hygiene.stale**", observations)
        self.assertIn("orphan note", observations)
        self.assertNotIn("finding done", observations, "a proposed finding is not an observation")

    def test_a_dry_run_says_so_instead_of_claiming_it_changed_files(self) -> None:
        report, applied, _, _ = self.build()
        report.dry_run = True
        markdown = render_markdown(report, applied, [], {})
        self.assertIn("Dry run", markdown)
        self.assertIn("## Would apply (dry run)", markdown)
        self.assertNotIn("## Applied", markdown)
        self.assertNotIn("ooda reflect revert", markdown)


class TestNothingIsDroppedSilently(TempCase):
    def test_decision_notes_and_priors_reach_the_reader(self) -> None:
        report = CycleReport(cycle_id="c")
        markdown = render_markdown(
            report,
            None,
            ["a1b2c3d4 (docs.missing) queued: its risk tier is review"],
            {"docs.missing": {"confidence": 0.8125, "verdicts": {"applied": 3, "dismissed": 1}}},
        )
        self.assertIn("## What the loop learned", markdown)
        self.assertIn("its risk tier is review", markdown)
        self.assertIn("0.81", markdown)
        self.assertIn("applied 3", markdown)

    def test_a_rule_with_no_history_still_shows_its_starting_confidence(self) -> None:
        markdown = render_markdown(
            CycleReport(cycle_id="c"), None, [], {"new.rule": {"confidence": 0.5, "verdicts": {}}}
        )
        self.assertIn("no history yet", markdown)

    def test_errors_and_failed_edits_are_surfaced_together(self) -> None:
        report = CycleReport(cycle_id="c")
        report.errors = ["shell:zsh: truncated at budget"]
        applied = applied_report(
            FakeEditResult(path="README.md", applied=False, reason="anchor no longer present"),
            FakeEditResult(path="Makefile", applied=True, diff="--- a\n+++ b\n+x\n"),
        )
        markdown = render_markdown(report, applied, [], {})
        self.assertIn("## Errors", markdown)
        self.assertIn("truncated at budget", markdown)
        self.assertIn("anchor no longer present", markdown)
        self.assertNotIn("Makefile", markdown.split("## Errors", 1)[1])


class TestNothingFallsBetweenSections(TempCase):
    """The actuator reports a dry run as `applied=False`, so a proposal the loop
    would have applied is in neither `report.applied` nor `report.queued`. That
    is the default mode, so a report that lost those rows would be wrong on most
    nights."""

    def dry_run_report(self) -> tuple[CycleReport, Proposal, FakeApplyReport]:
        planned = make_proposal("planned", risk="safe", paths=("Makefile",))
        report = CycleReport(cycle_id="c", dry_run=True)
        report.proposals = [planned]
        report.applied = []
        report.queued = []
        applied = applied_report(
            FakeEditResult(path="Makefile", applied=False, reason="dry run", diff="+test:\n")
        )
        return report, planned, applied

    def test_a_dry_runs_planned_edits_are_shown_not_lost(self) -> None:
        report, planned, applied = self.dry_run_report()
        markdown = render_markdown(report, applied, [], {})
        self.assertIn("## Would apply (dry run)", markdown)
        self.assertIn(planned.fingerprint[:8], markdown)
        self.assertIn("+test:", markdown)

    def test_a_dry_run_is_not_reported_as_an_error(self) -> None:
        report, _, applied = self.dry_run_report()
        self.assertNotIn("## Errors", render_markdown(report, applied, [], {}))

    def test_an_edit_that_failed_is_named_with_its_proposal(self) -> None:
        failed = make_proposal("failed", risk="safe", paths=("README.md",))
        report = CycleReport(cycle_id="c", dry_run=False)
        report.proposals = [failed]
        applied = applied_report(
            FakeEditResult(path="README.md", applied=False, reason="anchor no longer present")
        )
        markdown = render_markdown(report, applied, [], {})
        errors = markdown.split("## Errors", 1)[1]
        self.assertIn(failed.fingerprint[:8], errors)
        self.assertIn("fix failed did not apply: anchor no longer present", errors)
        self.assertEqual(errors.count("anchor no longer present"), 1, "said once, not twice")
        self.assertNotIn("## Applied", markdown, "a failed edit did not change anything")


class TestHostileAndOversizedInput(TempCase):
    def test_a_diff_containing_a_code_fence_does_not_break_out(self) -> None:
        proposal = make_proposal("fenced", paths=("README.md",))
        report = CycleReport(cycle_id="c", dry_run=False)
        report.proposals = [proposal]
        report.applied = [proposal.fingerprint]
        diff = "--- a/README.md\n+++ b/README.md\n+```sh\n+make test\n+```\n"
        markdown = render_markdown(report, applied_report(
            FakeEditResult(path="README.md", diff=diff)), [], {})
        self.assertIn("````diff", markdown, "the fence must outgrow the backticks inside it")
        self.assertIn("+make test", markdown)

    def test_a_giant_diff_is_clipped(self) -> None:
        proposal = make_proposal("giant", paths=("big.txt",))
        report = CycleReport(cycle_id="c", dry_run=False)
        report.proposals = [proposal]
        report.applied = [proposal.fingerprint]
        diff = "\n".join(f"+line {i}" for i in range(MAX_DIFF_LINES * 5))
        markdown = render_markdown(report, applied_report(
            FakeEditResult(path="big.txt", diff=diff)), [], {})
        self.assertIn("Diff truncated", markdown)
        self.assertLess(markdown.count("+line "), MAX_DIFF_LINES + 5)

    def test_multiline_and_overlong_text_is_flattened(self) -> None:
        proposal = make_proposal("messy")
        proposal.title = "a title\nwith a newline and " + "x" * 500
        proposal.finding.evidence[0].quote = "quoted\nover\nlines " + "y" * 500
        report = CycleReport(cycle_id="c")
        report.proposals = [proposal]
        report.queued = [proposal.fingerprint]
        markdown = render_markdown(report, None, [], {})
        for line in markdown.splitlines():
            self.assertLess(len(line), 460, f"a runaway line got through: {line[:80]}")
        self.assertNotIn("with a newline\n", markdown)

    def test_a_proposal_with_no_recorded_diff_is_still_listed(self) -> None:
        proposal = make_proposal("nodiff", paths=("x.md",))
        report = CycleReport(cycle_id="c", dry_run=False)
        report.proposals = [proposal]
        report.applied = [proposal.fingerprint]
        markdown = render_markdown(report, applied_report(), [], {})
        self.assertIn("x.md", markdown)
        self.assertIn("no diff recorded", markdown)

    def test_only_the_first_few_observations_per_rule_are_printed(self) -> None:
        report = CycleReport(cycle_id="c")
        report.findings = [
            Finding(rule_id="noisy.rule", title=f"observation {i}", key=str(i))
            for i in range(MAX_OBSERVATIONS_PER_RULE + 7)
        ]
        markdown = render_markdown(report, None, [], {})
        self.assertIn("...and 7 more from this rule", markdown)
        self.assertEqual(markdown.count("- [medium]"), MAX_OBSERVATIONS_PER_RULE)


class TestWriteReport(TempCase):
    def test_it_writes_the_cycle_file_and_refreshes_latest(self) -> None:
        reports = self.root / "reports"
        report = CycleReport(cycle_id="20260827-020000")
        path = write_report(reports, report, "# hello\n")
        self.assertEqual(path, reports / "20260827-020000.md")
        self.assertEqual(path.read_text("utf-8"), "# hello\n")

        latest = reports / "latest.md"
        self.assertTrue(latest.exists())
        self.assertFalse(latest.is_symlink(), "latest.md must be a copy, not a symlink")
        self.assertEqual(latest.read_text("utf-8"), path.read_text("utf-8"))

    def test_latest_follows_the_newest_cycle(self) -> None:
        reports = self.root / "reports"
        write_report(reports, CycleReport(cycle_id="20260826-020000"), "# older\n")
        write_report(reports, CycleReport(cycle_id="20260827-020000"), "# newer\n")
        self.assertEqual((reports / "latest.md").read_text("utf-8"), "# newer\n")
        self.assertTrue((reports / "20260826-020000.md").exists(), "history is kept")

    def test_a_hostile_cycle_id_cannot_escape_the_reports_directory(self) -> None:
        reports = self.root / "reports"
        path = write_report(reports, CycleReport(cycle_id="../../etc/passwd"), "# nope\n")
        self.assertEqual(path.parent, reports)
        self.assertFalse((self.root.parent / "etc").exists())
        self.assertTrue(path.exists())

    def test_an_unwritable_directory_is_logged_not_raised(self) -> None:
        blocker = self.root / "blocked"
        blocker.write_text("I am a file, not a directory", "utf-8")
        path = write_report(blocker, CycleReport(cycle_id="c"), "# hi\n")
        self.assertFalse(path.exists(), "nothing was written, and nothing blew up")


class TestRenderJson(TempCase):
    def test_it_is_parseable_and_carries_the_extras(self) -> None:
        proposal = make_proposal("json")
        report = CycleReport(cycle_id="c", dry_run=False)
        report.proposals = [proposal]
        report.queued = [proposal.fingerprint]
        payload = json.loads(
            render_json(
                report,
                applied_report(FakeEditResult(path="Makefile", applied=True, diff="+x")),
                ["a note that must not vanish"],
                {"docs.missing_target": {"confidence": 0.5}},
            )
        )
        self.assertEqual(payload["cycle_id"], "c")
        self.assertEqual(payload["decision_notes"], ["a note that must not vanish"])
        self.assertIn("docs.missing_target", payload["priors"])
        self.assertEqual(payload["changed_files"][0]["path"], "Makefile")
        self.assertEqual(payload["proposals"][0]["fingerprint"], proposal.fingerprint)

    def test_report_only_call_still_works(self) -> None:
        payload = json.loads(render_json(CycleReport(cycle_id="c")))
        self.assertEqual(payload["decision_notes"], [])
        self.assertEqual(payload["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
