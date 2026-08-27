"""A skill lint is only worth having if it rejects a skill that cannot load."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.ingest.skills import (  # noqa: E402
    DESCRIPTION_MAX,
    NAME_MAX,
    SkillConnector,
    discover_skills,
    lint_skill,
    parse_skill,
)

GOOD = """---
name: researching-sources
description: Gathers and cross-checks sources before a claim is written down. Use when a task rests on facts that have not been checked, or when starting work in an unfamiliar repository.
---

# Researching sources

1. Enumerate what exists.
2. Record each capture.
3. Name what could not be reached.
"""


def skill_dir(root: Path, name: str, body: str) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(body, "utf-8")
    return d / "SKILL.md"


class SkillLintCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def codes(self, body: str, name: str = "researching-sources") -> set[str]:
        skill = parse_skill(skill_dir(self.root, name, body))
        assert skill is not None
        return {f.code for f in lint_skill(skill)}

    def errors(self, body: str, name: str = "researching-sources") -> set[str]:
        skill = parse_skill(skill_dir(self.root, name, body))
        assert skill is not None
        return {f.code for f in lint_skill(skill) if f.severity == "error"}


class TestAcceptsAGoodSkill(SkillLintCase):
    def test_a_well_formed_skill_produces_no_findings(self) -> None:
        self.assertEqual(self.codes(GOOD), set())

    def test_frontmatter_is_parsed_including_a_description_with_punctuation(self) -> None:
        skill = parse_skill(skill_dir(self.root, "researching-sources", GOOD))
        assert skill is not None
        self.assertEqual(skill.name, "researching-sources")
        self.assertIn("cross-checks", skill.description)
        self.assertEqual(skill.command, "/researching-sources")


class TestRejectsWhatCannotLoad(SkillLintCase):
    def test_uppercase_in_name_is_an_error(self) -> None:
        body = GOOD.replace("name: researching-sources", "name: Researching_Sources")
        self.assertIn("name-charset", self.errors(body))

    def test_reserved_word_in_name_is_an_error(self) -> None:
        body = GOOD.replace("name: researching-sources", "name: claude-researcher")
        self.assertIn("name-reserved", self.errors(body))

    def test_over_length_name_is_an_error(self) -> None:
        body = GOOD.replace("name: researching-sources", f"name: {'a' * (NAME_MAX + 1)}")
        self.assertIn("name-too-long", self.errors(body))

    def test_missing_description_is_an_error_because_it_can_never_be_routed_to(self) -> None:
        body = "---\nname: researching-sources\n---\n\n# Body\n\nSteps.\n"
        self.assertIn("description-missing", self.errors(body))

    def test_over_length_description_is_an_error(self) -> None:
        body = GOOD.replace(
            "description: Gathers and cross-checks sources before a claim is written down. "
            "Use when a task rests on facts that have not been checked, or when starting "
            "work in an unfamiliar repository.",
            "description: " + "x" * (DESCRIPTION_MAX + 10),
        )
        self.assertIn("description-too-long", self.errors(body))

    def test_a_body_with_no_instructions_is_an_error(self) -> None:
        body = GOOD.split("# Researching sources")[0]
        self.assertIn("body-empty", self.errors(body))

    def test_a_reference_to_a_missing_file_is_an_error(self) -> None:
        body = GOOD + "\nDetail: see [reference.md](reference.md)\n"
        self.assertIn("reference-missing", self.errors(body))


class TestGuidanceIsWarnedNotFailed(SkillLintCase):
    def test_first_person_description_is_a_warning(self) -> None:
        body = GOOD.replace("description: Gathers", "description: I can help you gather")
        codes = self.codes(body)
        self.assertIn("description-person", codes)
        self.assertNotIn("description-person", self.errors(body))

    def test_description_without_a_trigger_is_a_warning(self) -> None:
        body = GOOD.replace(
            "Use when a task rests on facts that have not been checked, or when starting "
            "work in an unfamiliar repository.",
            "It is quite thorough.",
        )
        self.assertIn("description-no-trigger", self.codes(body))

    def test_an_over_long_body_is_a_warning_not_an_error(self) -> None:
        body = GOOD + "\n" + "\n".join(f"line {i}" for i in range(600))
        self.assertIn("body-too-long", self.codes(body))
        self.assertEqual(self.errors(body), set())

    def test_a_reference_that_references_onward_is_flagged(self) -> None:
        d = self.root / "researching-sources"
        d.mkdir(parents=True, exist_ok=True)
        (d / "deep.md").write_text("more here", "utf-8")
        (d / "reference.md").write_text("See [deep.md](deep.md)", "utf-8")
        body = GOOD + "\nDetail: see [reference.md](reference.md)\n"
        self.assertIn("reference-depth", self.codes(body))

    def test_a_long_reference_without_a_table_of_contents_is_flagged(self) -> None:
        d = self.root / "researching-sources"
        d.mkdir(parents=True, exist_ok=True)
        (d / "reference.md").write_text("\n".join(f"line {i}" for i in range(150)), "utf-8")
        body = GOOD + "\nDetail: see [reference.md](reference.md)\n"
        self.assertIn("reference-no-toc", self.codes(body))


class TestDiscoveryAndIngest(SkillLintCase):
    def test_discovers_nested_skill_directories(self) -> None:
        skill_dir(self.root / ".claude" / "skills", "researching-sources", GOOD)
        found = discover_skills([self.root])
        self.assertEqual(len(found), 1)

    def test_the_same_skill_reachable_twice_is_loaded_once(self) -> None:
        skill_dir(self.root, "researching-sources", GOOD)
        found = discover_skills([self.root, self.root, str(self.root)])
        self.assertEqual(len(found), 1)

    def test_a_missing_root_is_skipped_rather_than_raising(self) -> None:
        self.assertEqual(discover_skills(["/nonexistent"]), [])

    def test_connector_carries_the_lint_result_into_metadata(self) -> None:
        skill_dir(self.root, "researching-sources", GOOD)
        broken = GOOD.replace("name: researching-sources", "name: BadName")
        skill_dir(self.root, "broken-one", broken)
        docs = list(SkillConnector([self.root]).fetch({}))
        self.assertEqual(len(docs), 2)
        loadable = {d.title: d.metadata["loadable"] for d in docs}
        self.assertTrue(loadable["researching-sources"])
        self.assertFalse(loadable["BadName"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
