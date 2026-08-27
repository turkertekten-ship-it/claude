"""Tests for the actuator - the only part of `reflect` that writes to files.

Every test builds its workspace under `tempfile.TemporaryDirectory`. Nothing
here may read the developer's home directory, and the containment tests in
particular are written so that a regression *fails* rather than quietly writing
outside the fixture.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from oodarag.reflect.act.edits import (
    ApplyReport,
    EditApplier,
    EditResult,
    diff_bytes,
    find_anchor,
    plan_op,
    section_end,
)
from oodarag.reflect.models import EditOp, Finding, Proposal

README = (
    "# Title\n"
    "\n"
    "## Conventions\n"
    "\n"
    "- old bullet\n"
    "\n"
    "## Other\n"
    "\n"
    "tail\n"
)


def proposal(*edits: EditOp, title: str = "fix it") -> Proposal:
    finding = Finding(rule_id="test.rule", title="something", key="k")
    return Proposal(finding=finding, title=title, edits=list(edits))


class ApplierTestCase(unittest.TestCase):
    """A workspace, a backup root, and a directory that must never be written."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.root = base / "workspace"
        self.backups = base / "backups"
        self.outside = base / "outside"
        for d in (self.root, self.backups, self.outside):
            d.mkdir(parents=True)
        (self.root / "notes.md").write_text("alpha\nbeta\n", encoding="utf-8")
        (self.root / "README.md").write_text(README, encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def applier(self, dry_run: bool = False, max_bytes: int = 2_000_000) -> EditApplier:
        return EditApplier(
            root=self.root, backup_root=self.backups, dry_run=dry_run, max_bytes=max_bytes
        )

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def manifest(self, cycle_id: str) -> list[dict]:
        raw = json.loads((self.backups / cycle_id / "manifest.json").read_text("utf-8"))
        return raw["entries"]


class TestContainment(ApplierTestCase):
    def test_absolute_path_is_refused(self) -> None:
        victim = self.outside / "passwd"
        result = self.applier().apply(
            proposal(EditOp(path=str(victim), op="create", text="pwned\n")), "c1"
        )
        self.assertEqual(result.applied_count, 0)
        self.assertIn("absolute", result.results[0].reason)
        self.assertFalse(victim.exists(), "an absolute path must never be written")

    def test_dotdot_escape_is_refused(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="../escape.txt", op="create", text="pwned\n")), "c1"
        )
        self.assertEqual(result.applied_count, 0)
        self.assertIn("..", result.results[0].reason)
        self.assertFalse((self.root.parent / "escape.txt").exists())

    def test_symlinked_directory_pointing_outside_is_refused(self) -> None:
        os.symlink(self.outside, self.root / "link")
        result = self.applier().apply(
            proposal(EditOp(path="link/pwned.txt", op="create", text="pwned\n")), "c1"
        )
        self.assertEqual(result.applied_count, 0)
        self.assertIn("escapes", result.results[0].reason)
        self.assertFalse((self.outside / "pwned.txt").exists())

    def test_symlinked_file_is_never_written_through(self) -> None:
        real = self.outside / "target.md"
        real.write_text("theirs\n", encoding="utf-8")
        os.symlink(real, self.root / "linked.md")
        result = self.applier().apply(
            proposal(EditOp(path="linked.md", op="append", text="ours\n")), "c1"
        )
        self.assertEqual(result.applied_count, 0)
        self.assertIn("symlink", result.results[0].reason)
        self.assertEqual(real.read_text("utf-8"), "theirs\n")

    def test_empty_path_is_refused(self) -> None:
        result = self.applier().apply(proposal(EditOp(path="", op="append", text="x")), "c1")
        self.assertEqual(result.results[0].reason, "empty path")


class TestPreconditions(ApplierTestCase):
    def test_create_refuses_an_existing_file(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="notes.md", op="create", text="new\n")), "c1"
        )
        self.assertEqual(result.results[0].reason, "exists")
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\n")

    def test_create_writes_a_missing_file_and_its_parents(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="docs/deep/PLAN.md", op="create", text="# Plan")), "c1"
        )
        self.assertTrue(result.results[0].applied)
        self.assertEqual(self.read("docs/deep/PLAN.md"), "# Plan\n")

    def test_append_requires_the_file_to_exist(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="absent.md", op="append", text="x\n")), "c1"
        )
        self.assertEqual(result.results[0].reason, "file does not exist")
        self.assertFalse((self.root / "absent.md").exists())

    def test_replace_with_no_match_is_skipped(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="notes.md", op="replace", old="gamma", text="delta")), "c1"
        )
        self.assertEqual(result.results[0].reason, "old text not found")
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\n")

    def test_replace_with_two_matches_is_skipped(self) -> None:
        (self.root / "notes.md").write_text("alpha\nalpha\n", encoding="utf-8")
        result = self.applier().apply(
            proposal(EditOp(path="notes.md", op="replace", old="alpha", text="omega")), "c1"
        )
        self.assertIn("appears 2 times", result.results[0].reason)
        self.assertEqual(self.read("notes.md"), "alpha\nalpha\n")

    def test_replace_with_exactly_one_match_applies(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="notes.md", op="replace", old="beta", text="omega")), "c1"
        )
        self.assertTrue(result.results[0].applied)
        self.assertEqual(self.read("notes.md"), "alpha\nomega\n")

    def test_insert_after_requires_its_anchor(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="notes.md", op="insert_after", anchor="nope", text="x\n")), "c1"
        )
        self.assertEqual(result.results[0].reason, "anchor not found")

    def test_insert_after_uses_the_first_occurrence(self) -> None:
        (self.root / "notes.md").write_text("mark\nmiddle\nmark\n", encoding="utf-8")
        self.applier().apply(
            proposal(EditOp(path="notes.md", op="insert_after", anchor="mark", text="here")), "c1"
        )
        self.assertEqual(self.read("notes.md"), "mark\nhere\nmiddle\nmark\n")

    def test_unknown_op_is_refused_rather_than_guessed(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="notes.md", op="obliterate", text="x")), "c1"
        )
        self.assertIn("unknown op", result.results[0].reason)

    def test_a_binary_file_is_never_rewritten_as_text(self) -> None:
        (self.root / "blob.bin").write_bytes(b"\xff\xfe\x00\x01not utf8")
        result = self.applier().apply(
            proposal(EditOp(path="blob.bin", op="append", text="x\n")), "c1"
        )
        self.assertEqual(result.applied_count, 0)
        self.assertEqual((self.root / "blob.bin").read_bytes(), b"\xff\xfe\x00\x01not utf8")


class TestEnsureSection(ApplierTestCase):
    def test_text_lands_at_the_end_of_the_named_section(self) -> None:
        edit = EditOp(
            path="README.md", op="ensure_section", anchor="## Conventions", text="- new bullet\n"
        )
        result = self.applier().apply(proposal(edit), "c1")
        self.assertTrue(result.results[0].applied)
        self.assertEqual(
            self.read("README.md"),
            "# Title\n\n## Conventions\n\n- old bullet\n- new bullet\n\n## Other\n\ntail\n",
        )

    def test_a_deeper_heading_does_not_end_the_section(self) -> None:
        (self.root / "README.md").write_text(
            "## Conventions\n\n### Sub\n\nbody\n\n## Other\n", encoding="utf-8"
        )
        edit = EditOp(path="README.md", op="ensure_section", anchor="## Conventions", text="- x\n")
        self.applier().apply(proposal(edit), "c1")
        self.assertEqual(
            self.read("README.md"), "## Conventions\n\n### Sub\n\nbody\n- x\n\n## Other\n"
        )

    def test_a_missing_section_is_appended_at_eof(self) -> None:
        edit = EditOp(path="README.md", op="ensure_section", anchor="## Recipes", text="- make\n")
        self.applier().apply(proposal(edit), "c1")
        self.assertEqual(self.read("README.md"), README + "\n## Recipes\n\n- make\n")

    def test_running_it_again_changes_nothing(self) -> None:
        edit = EditOp(
            path="README.md", op="ensure_section", anchor="## Conventions", text="- new bullet\n"
        )
        self.applier().apply(proposal(edit), "c1")
        after_first = self.read("README.md")
        second = self.applier().apply(proposal(edit), "c2")
        self.assertEqual(self.read("README.md"), after_first, "the second night must be a no-op")
        self.assertFalse(second.results[0].applied)
        self.assertEqual(second.results[0].reason, "already present")

    def test_a_non_heading_anchor_appends_at_the_end_of_the_file(self) -> None:
        (self.root / "Makefile").write_text(".PHONY: test\ntest:\n\tpytest\n", encoding="utf-8")
        edit = EditOp(
            path="Makefile", op="ensure_section", anchor=".PHONY: test", text="lint:\n\truff\n"
        )
        self.applier().apply(proposal(edit), "c1")
        self.assertEqual(self.read("Makefile"), ".PHONY: test\ntest:\n\tpytest\nlint:\n\truff\n")

    def test_an_anchorless_ensure_section_is_refused(self) -> None:
        result = self.applier().apply(
            proposal(EditOp(path="README.md", op="ensure_section", text="- x\n")), "c1"
        )
        self.assertIn("anchor", result.results[0].reason)


class TestTrailingNewline(ApplierTestCase):
    def test_a_file_without_a_final_newline_keeps_it_that_way(self) -> None:
        (self.root / "bare.md").write_text("line one", encoding="utf-8")
        self.applier().apply(proposal(EditOp(path="bare.md", op="append", text="line two\n")), "c1")
        self.assertEqual(self.read("bare.md"), "line one\nline two")

    def test_a_file_with_a_final_newline_keeps_it(self) -> None:
        self.applier().apply(proposal(EditOp(path="notes.md", op="append", text="gamma")), "c1")
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\ngamma\n")


class TestDryRun(ApplierTestCase):
    def test_dry_run_diffs_without_writing(self) -> None:
        edit = EditOp(path="notes.md", op="append", text="gamma\n")
        report = self.applier(dry_run=True).apply(proposal(edit), "c1")
        result = report.results[0]
        self.assertFalse(result.applied)
        self.assertEqual(result.reason, "dry run")
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\n", "dry run must not touch disk")
        self.assertFalse(self.backups.joinpath("c1").exists(), "dry run must not back anything up")
        self.assertTrue(result.diff.startswith("--- notes.md\n+++ notes.md\n"))
        self.assertIn("+gamma", result.diff)
        self.assertEqual(result.bytes_changed, len(b"gamma"))

    def test_the_dry_run_diff_is_what_a_real_run_produces(self) -> None:
        edits = [
            EditOp(path="README.md", op="ensure_section", anchor="## Conventions", text="- new\n"),
            EditOp(path="fresh.md", op="create", text="hello\n"),
        ]
        dry = self.applier(dry_run=True).apply(proposal(*edits), "c1")
        wet = self.applier(dry_run=False).apply(proposal(*edits), "c1")
        self.assertEqual(
            [r.diff for r in dry.results],
            [r.diff for r in wet.results],
            "--apply must be unsurprising: the same planner produces both diffs",
        )
        self.assertEqual(dry.total_bytes, wet.total_bytes)
        self.assertEqual(wet.applied_count, 2)


class TestApplyAndBackup(ApplierTestCase):
    def test_a_real_apply_writes_and_backs_up(self) -> None:
        report = self.applier().apply(
            proposal(EditOp(path="notes.md", op="append", text="gamma\n")), "cycle-1"
        )
        self.assertEqual(report.applied_count, 1)
        self.assertEqual(report.failed_count, 0)
        self.assertEqual(report.backup_dir, str(self.backups / "cycle-1"))
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\ngamma\n")
        backup = self.backups / "cycle-1" / "notes.md"
        self.assertEqual(backup.read_text("utf-8"), "alpha\nbeta\n")

    def test_the_manifest_records_what_revert_needs(self) -> None:
        edits = [
            EditOp(path="notes.md", op="append", text="gamma\n"),
            EditOp(path="new/file.md", op="create", text="fresh\n"),
        ]
        self.applier().apply(proposal(*edits), "cycle-1")
        entries = {e["path"]: e for e in self.manifest("cycle-1")}
        self.assertTrue(entries["notes.md"]["existed_before"])
        self.assertEqual(len(entries["notes.md"]["sha256"]), 64)
        created = entries[str(Path("new/file.md"))]
        self.assertFalse(created["existed_before"], "a create must record that there was no file")
        self.assertEqual(created["sha256"], "")

    def test_the_first_backup_of_a_cycle_wins(self) -> None:
        applier = self.applier()
        applier.apply(proposal(EditOp(path="notes.md", op="append", text="one\n")), "cycle-1")
        applier.apply(proposal(EditOp(path="notes.md", op="append", text="two\n")), "cycle-1")
        backup = self.backups / "cycle-1" / "notes.md"
        self.assertEqual(backup.read_text("utf-8"), "alpha\nbeta\n")
        self.assertEqual(len(self.manifest("cycle-1")), 1)

    def test_apply_all_reports_every_proposal(self) -> None:
        report = self.applier().apply_all(
            [
                proposal(EditOp(path="notes.md", op="append", text="gamma\n")),
                proposal(EditOp(path="nope.md", op="append", text="x\n")),
            ],
            "cycle-1",
        )
        self.assertEqual(report.applied_count, 1)
        self.assertEqual(report.failed_count, 1)
        self.assertEqual(report.paths, ["notes.md", "nope.md"])
        self.assertIn("results", report.as_dict())

    def test_file_mode_survives_an_edit(self) -> None:
        script = self.root / "run.sh"
        script.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
        script.chmod(0o755)
        self.applier().apply(proposal(EditOp(path="run.sh", op="append", text="echo bye\n")), "c1")
        self.assertEqual(script.stat().st_mode & 0o777, 0o755)


class TestAllOrNothing(ApplierTestCase):
    def test_a_bad_second_op_prevents_the_first(self) -> None:
        (self.root / "notes.md").write_text("alpha\nalpha\n", encoding="utf-8")
        edits = [
            EditOp(path="README.md", op="append", text="appended\n"),
            EditOp(path="notes.md", op="replace", old="alpha", text="omega"),
        ]
        report = self.applier().apply(proposal(*edits), "cycle-1")
        self.assertEqual(report.applied_count, 0)
        self.assertEqual(self.read("README.md"), README, "the valid op must not land alone")
        self.assertEqual(self.read("notes.md"), "alpha\nalpha\n")
        self.assertIn("blocked by notes.md", report.results[0].reason)
        self.assertIn("appears 2 times", report.results[1].reason)
        self.assertFalse((self.backups / "cycle-1").exists(), "nothing applied, nothing backed up")

    def test_ops_are_planned_against_each_other(self) -> None:
        edits = [
            EditOp(path="stack.md", op="create", text="one\n"),
            EditOp(path="stack.md", op="append", text="two\n"),
        ]
        report = self.applier().apply(proposal(*edits), "cycle-1")
        self.assertEqual(report.applied_count, 2)
        self.assertEqual(self.read("stack.md"), "one\ntwo\n")

    def test_an_already_satisfied_op_does_not_block_its_siblings(self) -> None:
        edits = [
            EditOp(path="README.md", op="ensure_section", anchor="## Conventions",
                   text="- old bullet\n"),
            EditOp(path="notes.md", op="append", text="gamma\n"),
        ]
        report = self.applier().apply(proposal(*edits), "cycle-1")
        self.assertEqual(report.results[0].reason, "already present")
        self.assertTrue(report.results[1].applied)
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\ngamma\n")


class TestLimits(ApplierTestCase):
    def test_a_file_over_the_size_cap_is_left_alone(self) -> None:
        (self.root / "huge.md").write_text("x" * 500, encoding="utf-8")
        report = self.applier(max_bytes=100).apply(
            proposal(EditOp(path="huge.md", op="append", text="more\n")), "c1"
        )
        self.assertIn("larger than 100 bytes", report.results[0].reason)
        self.assertEqual(len(self.read("huge.md")), 500)

    def test_an_edit_that_would_blow_past_the_cap_is_refused(self) -> None:
        report = self.applier(max_bytes=100).apply(
            proposal(EditOp(path="big.md", op="create", text="y" * 500)), "c1"
        )
        self.assertIn("would exceed 100 bytes", report.results[0].reason)
        self.assertFalse((self.root / "big.md").exists())


class TestRevert(ApplierTestCase):
    def apply_a_cycle(self) -> ApplyReport:
        edits = [
            EditOp(path="notes.md", op="append", text="gamma\n"),
            EditOp(path="internal/PLAN.md", op="create", text="# Plan\n"),
        ]
        return self.applier().apply(proposal(*edits), "cycle-1")

    def test_revert_restores_originals_and_removes_creations(self) -> None:
        self.apply_a_cycle()
        self.assertTrue((self.root / "internal" / "PLAN.md").exists())
        report = self.applier().revert("cycle-1")
        self.assertEqual(report.applied_count, 2)
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\n")
        self.assertFalse(
            (self.root / "internal" / "PLAN.md").exists(),
            "a created file must be deleted, not blanked",
        )

    def test_revert_twice_is_a_no_op(self) -> None:
        self.apply_a_cycle()
        self.applier().revert("cycle-1")
        again = self.applier().revert("cycle-1")
        self.assertEqual(again.applied_count, 0)
        reasons = sorted(r.reason for r in again.results)
        self.assertEqual(reasons, ["already absent", "already matches backup"])
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\n")

    def test_revert_of_an_unknown_cycle_is_quiet(self) -> None:
        report = self.applier().revert("never-ran")
        self.assertEqual(report.results, [])

    def test_a_tampered_manifest_cannot_reach_outside_the_root(self) -> None:
        self.apply_a_cycle()
        path = self.backups / "cycle-1" / "manifest.json"
        payload = json.loads(path.read_text("utf-8"))
        payload["entries"] = [
            {"path": "../../escape.md", "op": "append", "existed_before": True,
             "sha256": "", "backup": "notes.md"}
        ]
        path.write_text(json.dumps(payload), encoding="utf-8")
        report = self.applier().revert("cycle-1")
        self.assertEqual(report.applied_count, 0)
        self.assertIn("..", report.results[0].reason)
        self.assertFalse((self.root.parent / "escape.md").exists())

    def test_a_corrupt_manifest_degrades_to_nothing_to_do(self) -> None:
        self.apply_a_cycle()
        (self.backups / "cycle-1" / "manifest.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(self.applier().revert("cycle-1").results, [])

    def test_revert_honours_dry_run(self) -> None:
        self.apply_a_cycle()
        report = self.applier(dry_run=True).revert("cycle-1")
        self.assertEqual(report.applied_count, 0)
        self.assertEqual(self.read("notes.md"), "alpha\nbeta\ngamma\n")
        self.assertTrue(any(r.diff for r in report.results))


class TestPureHelpers(unittest.TestCase):
    def test_plan_op_touches_no_disk(self) -> None:
        status, text, reason = plan_op(EditOp(path="x", op="create", text="hi"), None)
        self.assertEqual((status, text, reason), ("ok", "hi\n", ""))

    def test_find_anchor_prefers_a_whole_line(self) -> None:
        lines = [".PHONY: test-integration\n", ".PHONY: test\n"]
        self.assertEqual(find_anchor(lines, ".PHONY: test"), 1)

    def test_find_anchor_falls_back_to_containment(self) -> None:
        self.assertEqual(find_anchor(["## Conventions <!-- x -->\n"], "## Conventions"), 0)

    def test_a_fenced_comment_is_not_a_heading(self) -> None:
        lines = ["## S\n", "```sh\n", "# not a heading\n", "```\n", "body\n"]
        self.assertEqual(section_end(lines, 0), len(lines))

    def test_diff_bytes_counts_both_sides_of_a_change(self) -> None:
        diff = "--- a\n+++ a\n@@ -1 +1 @@\n-old\n+new\n"
        self.assertEqual(diff_bytes(diff), 6)

    def test_edit_result_is_serialisable(self) -> None:
        self.assertEqual(EditResult(path="a", op="append").as_dict()["applied"], False)


if __name__ == "__main__":
    unittest.main()
