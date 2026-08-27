"""Tests for the documentation rules.

The tree is built in a TemporaryDirectory and the `KIND_FILE` signals are
constructed to match it by hand, because that is the pairing the rules actually
reason about: a signal saying "this doc exists and says this" plus a filesystem
that either does or does not contain what the doc points at. Nothing here reads
the developer's own repository, and the staleness cases set their timestamps
explicitly rather than sleeping or touching files, so the boundary can be tested
to the second.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from oodarag.reflect.detect.base import DetectContext, registry
from oodarag.reflect.detect.docs import (
    ENTRYPOINTS_HEADING,
    DocsBrokenReference,
    DocsStaleAgainstCode,
    DocsUndocumentedEntrypoint,
)
from oodarag.reflect.models import (
    ACTOR_HUMAN,
    ACTOR_MACHINE,
    KIND_COMMIT,
    KIND_FILE,
    Signal,
)

# A fixed point in time so every gap in these tests is exact.
T0 = 1_756_200_000.0
DAY = 86_400.0

DOC_EXTS = {".md", ".rst", ".txt"}
CODE_EXTS = {".py", ".toml", ".yml", ".sh", ".js"}


def file_signal(rel: str, text: str, ts: float = T0, **overrides: Any) -> Signal:
    """A `KIND_FILE` signal shaped the way the workspace walker emits them."""
    ext = "." + rel.rsplit(".", 1)[-1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
    metadata: dict[str, Any] = {
        "size": len(text),
        "mtime": round(ts, 3),
        "ext": ext,
        "line_count": len(text.splitlines()),
        "is_doc": ext in DOC_EXTS,
        "is_code": ext in CODE_EXTS,
        "is_test": "test" in rel.lower(),
        "depth": rel.count("/"),
    }
    metadata.update(overrides)
    return Signal(
        kind=KIND_FILE,
        source="workspace:files",
        text=text,
        ts=ts,
        uri=rel,
        session="workspace",
        actor=ACTOR_MACHINE,
        metadata=metadata,
    )


def commit_signal(subject: str, files: list[str], ts: float = T0) -> Signal:
    return Signal(
        kind=KIND_COMMIT,
        source="git:log",
        text=subject,
        ts=ts,
        uri="git:abc123def456",
        session="git",
        actor=ACTOR_HUMAN,
        metadata={"sha": "abc123def456", "author": "someone", "files": files},
    )


class DocsTestCase(unittest.TestCase):
    """A throwaway workspace root. The rules stat it; nothing else is touched."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.signals: list[Signal] = []

    def write(self, rel: str, text: str = "") -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")
        return path

    def add(self, rel: str, text: str, ts: float = T0, on_disk: bool = True,
            **overrides: Any) -> Signal:
        """Register a file both on disk and as an observed signal."""
        if on_disk:
            self.write(rel, text)
        sig = file_signal(rel, text, ts, **overrides)
        self.signals.append(sig)
        return sig

    def context(self, extra: list[Signal] | None = None) -> DetectContext:
        return DetectContext(
            signals=self.signals + (extra or []),
            root=self.root,
            now=T0 + 90 * DAY,
        )


# -- broken references -------------------------------------------------------


class BrokenReferenceTest(DocsTestCase):
    def run_rule(self, config: dict[str, Any] | None = None) -> tuple[Any, list[Any]]:
        rule = DocsBrokenReference(config or {})
        return rule, rule.run(self.context())

    def test_broken_markdown_link_fires(self) -> None:
        self.add("docs/guide.md", "See the [setup notes](setup.md) before starting.\n")
        _, found = self.run_rule()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].rule_id, "docs.broken_ref")
        self.assertEqual(found[0].severity, "high")
        self.assertEqual(found[0].key, "docs/guide.md->docs/setup.md")
        self.assertEqual(found[0].metadata["target"], "docs/setup.md")
        self.assertTrue(found[0].evidence, "a finding without evidence is an opinion")
        self.assertIn("setup notes", found[0].evidence[0].quote)
        self.assertEqual(found[0].evidence[0].uri, "docs/guide.md")

    def test_link_to_an_existing_file_is_silent(self) -> None:
        self.add("docs/guide.md", "See [setup](setup.md).\n")
        self.write("docs/setup.md", "# Setup\n")
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_root_relative_reference_also_counts_as_present(self) -> None:
        # docs/README.md does not exist, but README.md at the root does, and a
        # hit on either resolution means the reference is not broken.
        self.add("docs/guide.md", "Start at [the readme](README.md).\n")
        self.write("README.md", "# Project\n")
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_external_links_are_ignored(self) -> None:
        self.add(
            "docs/guide.md",
            "[docs](https://example.com/missing.md) [http](http://x.test/a.md)\n"
            "[mail](mailto:someone@example.com) [tel](tel:+15550000)\n"
            "[abs](/etc/hosts) [anchor](#section)\n",
        )
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_anchor_is_stripped_before_the_existence_check(self) -> None:
        self.add("docs/guide.md", "[install](setup.md#installation)\n")
        self.write("docs/setup.md", "# Setup\n")
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_anchor_is_stripped_from_the_reported_target(self) -> None:
        self.add("docs/guide.md", "[install](setup.md#installation)\n")
        _, found = self.run_rule()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].metadata["target"], "docs/setup.md")
        self.assertNotIn("#", found[0].metadata["target"])

    def test_path_shaped_code_span_fires_more_quietly_than_a_link(self) -> None:
        self.add("docs/a.md", "Configuration lives in `conf/settings.toml`.\n")
        self.add("docs/b.md", "Configuration lives in [here](../conf/settings.toml).\n")
        _, found = self.run_rule()
        by_doc = {f.metadata["doc"]: f for f in found}
        self.assertEqual(set(by_doc), {"docs/a.md", "docs/b.md"})
        self.assertEqual(by_doc["docs/a.md"].metadata["ref_kind"], "code")
        self.assertLess(by_doc["docs/a.md"].confidence, by_doc["docs/b.md"].confidence)

    def test_commands_in_code_spans_are_not_paths(self) -> None:
        self.add(
            "docs/guide.md",
            "Run `make test` then `python -m oodarag.cli index`, and read `README`.\n",
        )
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_code_spans_can_be_switched_off(self) -> None:
        self.add("docs/guide.md", "See `conf/settings.toml`.\n")
        _, found = self.run_rule({"scan_code_spans": False})
        self.assertEqual(found, [])

    def test_fenced_examples_are_not_references(self) -> None:
        self.add(
            "docs/guide.md",
            "Example:\n\n```\ncp config/example.toml config/live.toml\n"
            "[a](nowhere.md)\n```\n\nThat is all.\n",
        )
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_a_reference_that_escapes_the_workspace_is_dropped(self) -> None:
        self.add("docs/guide.md", "[outside](../../secrets/notes.md)\n")
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_only_documentation_is_scanned(self) -> None:
        self.add("src/app.py", '"""See [design](design.md)."""\n')
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_the_same_missing_path_is_reported_once_per_doc(self) -> None:
        self.add("docs/guide.md", "[a](setup.md) and again [b](setup.md) and `docs/setup.md`\n")
        _, found = self.run_rule()
        self.assertEqual(len(found), 1)

    def test_findings_are_capped_per_document(self) -> None:
        body = "\n".join(f"[p{i}](missing-{i}.md)" for i in range(30))
        self.add("docs/guide.md", body)
        _, found = self.run_rule({"max_per_doc": 3})
        self.assertEqual(len(found), 3)

    def test_fingerprint_is_stable_across_nights(self) -> None:
        self.add("docs/guide.md", "[setup](setup.md)\n")
        _, first = self.run_rule()
        self.signals = []
        self.add("docs/guide.md", "Rewritten intro.\n\n[setup](setup.md)\n", ts=T0 + 3 * DAY)
        _, second = self.run_rule()
        self.assertEqual(first[0].fingerprint, second[0].fingerprint)

    def test_hostile_document_produces_nothing_and_does_not_raise(self) -> None:
        self.add(
            "docs/hostile.md",
            "[glob](src/*.py) [var]($(BUILD)/out.md) [tpl]({{ page.url }})\n"
            "[ph](<path/to/file.md>) [empty]() [spaces](a b c) [ws](   )\n"
            "`*.py` `<file>` `$(THING)` `--flag` ``\n"
            "[unclosed](oops.md\n" + "x" * 5000 + "\n[deep](" + "a/" * 300 + "b.md)\n",
        )
        _, found = self.run_rule()
        for finding in found:
            self.assertTrue(finding.evidence)
            self.assertNotIn("*", finding.metadata["target"])
            self.assertNotIn("<", finding.metadata["target"])

    def test_broken_config_falls_back_to_defaults(self) -> None:
        rule = DocsBrokenReference({"max_per_doc": "lots", "link_confidence": None})
        self.assertEqual(rule.max_per_doc, 10)
        self.assertEqual(rule.link_confidence, 0.8)


class BrokenReferenceProposalTest(DocsTestCase):
    def propose_for(self, doc: str, body: str) -> tuple[Any, list[Any]]:
        self.add(doc, body)
        rule = DocsBrokenReference({})
        ctx = self.context()
        found = rule.run(ctx)
        self.assertEqual(len(found), 1)
        return found[0], rule.run_propose(found[0], ctx)

    def test_a_missing_document_is_created_as_a_safe_stub(self) -> None:
        finding, proposals = self.propose_for("docs/guide.md", "[setup](setup.md)\n")
        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.risk, "safe")
        self.assertEqual([e.op for e in proposal.edits], ["create"])
        edit = proposal.edits[0]
        self.assertEqual(edit.path, "docs/setup.md")
        self.assertFalse(Path(edit.path).is_absolute())
        self.assertNotIn("..", Path(edit.path).parts)
        self.assertIn("Stub", edit.text)
        self.assertIn("docs/guide.md", edit.text)
        self.assertIs(proposal.finding, finding)

    def test_the_stub_matches_the_target_format(self) -> None:
        _, proposals = self.propose_for("notes.md", "[old plan](plans/old-plan.rst)\n")
        text = proposals[0].edits[0].text
        self.assertTrue(text.startswith("Old plan\n===="), text[:40])

    def test_a_missing_source_file_is_never_fabricated(self) -> None:
        finding, proposals = self.propose_for("docs/guide.md", "See `src/oodarag/missing.py`.\n")
        self.assertEqual(finding.metadata["target"], "src/oodarag/missing.py")
        self.assertEqual(proposals, [])

    def test_a_missing_image_is_reported_but_not_created(self) -> None:
        _, proposals = self.propose_for("docs/guide.md", "![diagram](img/flow.png)\n")
        self.assertEqual(proposals, [])

    def test_a_file_written_since_the_scan_is_not_re_created(self) -> None:
        self.add("docs/guide.md", "[setup](setup.md)\n")
        rule = DocsBrokenReference({})
        ctx = self.context()
        found = rule.run(ctx)
        self.write("docs/setup.md", "# Setup\n")
        self.assertEqual(rule.run_propose(found[0], ctx), [])


# -- undocumented entry points ----------------------------------------------


MAKEFILE = """PY ?= python3
export PYTHONPATH := src
VERSION:=0.1.0

.PHONY: help test lint deploy

help:
\t@echo "targets"

test: ## Run the full test suite
\t$(PY) -m unittest discover -s tests

lint: ## Compile-check every module
\t$(PY) -m compileall -q src

deploy:
\t./scripts/deploy.sh
"""

PYPROJECT = """[project]
name = "thing"
version = "0.1.0"

[project.scripts]
ooda = "oodarag.cli:main"
"""


class UndocumentedEntrypointTest(DocsTestCase):
    def run_rule(self, config: dict[str, Any] | None = None) -> tuple[Any, list[Any]]:
        rule = DocsUndocumentedEntrypoint(config or {})
        return rule, rule.run(self.context())

    def test_missing_targets_are_grouped_into_one_finding(self) -> None:
        self.add("Makefile", MAKEFILE)
        self.add("README.md", "# Thing\n\nRun `make test` to check your work.\n")
        _, found = self.run_rule()
        self.assertEqual(len(found), 1, "one finding, not one per target")
        finding = found[0]
        self.assertEqual(finding.key, "readme-entrypoints")
        names = [e["name"] for e in finding.metadata["missing"]]
        self.assertEqual(sorted(names), ["deploy", "lint"])
        self.assertTrue(finding.evidence)
        self.assertEqual(finding.targets, ["README.md"])

    def test_phony_help_and_assignments_are_not_targets(self) -> None:
        self.add("Makefile", MAKEFILE)
        self.add("README.md", "# Thing\n")
        _, found = self.run_rule()
        names = {e["name"] for e in found[0].metadata["missing"]}
        self.assertEqual(names, {"test", "lint", "deploy"})
        for noise in ("PY", "PYTHONPATH", "VERSION", "PHONY", "help"):
            self.assertNotIn(noise, names)

    def test_a_word_that_merely_contains_the_target_does_not_document_it(self) -> None:
        self.add("Makefile", "test: ## Run tests\n\t@true\n")
        self.add("README.md", "# Thing\n\nThe latest contest protest.\n")
        _, found = self.run_rule()
        self.assertEqual([e["name"] for e in found[0].metadata["missing"]], ["test"])

    def test_console_scripts_count_as_entry_points(self) -> None:
        self.add("pyproject.toml", PYPROJECT)
        self.add("README.md", "# Thing\n")
        _, found = self.run_rule()
        entries = found[0].metadata["missing"]
        self.assertEqual([e["name"] for e in entries], ["ooda"])
        self.assertEqual(entries[0]["kind"], "script")

    def test_a_fully_documented_project_is_silent(self) -> None:
        self.add("Makefile", MAKEFILE)
        self.add("pyproject.toml", PYPROJECT)
        self.add("README.md", "# Thing\n\nmake test, make lint, make deploy, and `ooda query`.\n")
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_nothing_to_document_is_silent(self) -> None:
        self.add("README.md", "# Thing\n")
        _, found = self.run_rule()
        self.assertEqual(found, [])

    def test_a_malformed_pyproject_costs_only_its_own_entries(self) -> None:
        self.add("Makefile", MAKEFILE)
        self.add("pyproject.toml", "[project\nname = broken \x00\n[[[")
        self.add("README.md", "# Thing\n")
        _, found = self.run_rule()
        self.assertEqual(len(found), 1)
        names = {e["name"] for e in found[0].metadata["missing"]}
        self.assertEqual(names, {"test", "lint", "deploy"})

    def test_files_are_read_from_disk_when_no_signal_carries_them(self) -> None:
        # The walker skips ignored and oversized files; the rule still needs to
        # be able to read the Makefile it is reasoning about.
        self.write("Makefile", MAKEFILE)
        self.write("README.md", "# Thing\n")
        self.signals.append(file_signal("src/app.py", "x = 1\n"))
        _, found = self.run_rule()
        self.assertEqual(len(found), 1)

    def test_the_file_names_are_configurable(self) -> None:
        self.add("build/Makefile", MAKEFILE)
        self.add("docs/index.md", "# Thing\n")
        _, found = self.run_rule({"makefile": "build/Makefile", "readme": "docs/index.md"})
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].targets, ["docs/index.md"])

    def test_a_threshold_can_silence_small_gaps(self) -> None:
        self.add("Makefile", "test: ## Run tests\n\t@true\n")
        self.add("README.md", "# Thing\n")
        _, found = self.run_rule({"min_missing": 2})
        self.assertEqual(found, [])


class EntrypointProposalTest(DocsTestCase):
    def propose(self, config: dict[str, Any] | None = None) -> list[Any]:
        rule = DocsUndocumentedEntrypoint(config or {})
        ctx = self.context()
        found = rule.run(ctx)
        self.assertEqual(len(found), 1)
        return rule.run_propose(found[0], ctx)

    def test_an_existing_readme_is_only_ever_appended_to_under_review(self) -> None:
        self.add("Makefile", MAKEFILE)
        self.add("README.md", "# Thing\n\nSome prose the loop must not touch.\n")
        proposals = self.propose()
        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.risk, "review")
        edit = proposal.edits[0]
        self.assertEqual(edit.op, "ensure_section")
        self.assertEqual(edit.path, "README.md")
        self.assertEqual(edit.anchor, ENTRYPOINTS_HEADING)
        self.assertIn("`make lint`", edit.text)
        self.assertIn("Compile-check every module", edit.text)
        self.assertIn("`make deploy`", edit.text)  # no ## comment, still listed

    def test_an_absent_readme_is_created_safely(self) -> None:
        self.add("Makefile", MAKEFILE)
        proposals = self.propose()
        self.assertEqual(proposals[0].risk, "safe")
        edit = proposals[0].edits[0]
        self.assertEqual(edit.op, "create")
        self.assertIn(ENTRYPOINTS_HEADING, edit.text)
        self.assertIn("`make test`", edit.text)

    def test_the_listing_is_capped(self) -> None:
        many = "\n".join(f"t{i}: ## does thing {i}\n\t@true" for i in range(20))
        self.add("Makefile", many)
        self.add("README.md", "# Thing\n")
        proposals = self.propose({"max_listed": 4})
        self.assertEqual(proposals[0].edits[0].text.count("\n"), 4)

    def test_proposal_paths_stay_inside_the_workspace(self) -> None:
        self.add("Makefile", MAKEFILE)
        self.add("README.md", "# Thing\n")
        for proposal in self.propose():
            for edit in proposal.edits:
                self.assertFalse(Path(edit.path).is_absolute())
                self.assertNotIn("..", Path(edit.path).parts)


# -- staleness ---------------------------------------------------------------


class StaleAgainstCodeTest(DocsTestCase):
    def run_rule(self, config: dict[str, Any] | None = None,
                 extra: list[Signal] | None = None) -> tuple[Any, list[Any], DetectContext]:
        rule = DocsStaleAgainstCode(config or {})
        ctx = self.context(extra)
        return rule, rule.run(ctx), ctx

    def test_a_doc_far_behind_its_neighbours_is_reported(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 45 * DAY)
        _, found, _ = self.run_rule()
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.rule_id, "docs.stale")
        self.assertEqual(finding.severity, "low")
        self.assertEqual(finding.key, "src/pkg/notes.md")
        self.assertEqual(finding.metadata["newest_code"], "src/pkg/engine.py")
        self.assertEqual(finding.metadata["gap_days"], 45.0)
        self.assertGreaterEqual(len(finding.evidence), 2)
        self.assertIn("src/pkg/engine.py", finding.evidence[1].quote)

    def test_exactly_at_the_threshold_is_not_yet_stale(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 30 * DAY)
        _, found, _ = self.run_rule()
        self.assertEqual(found, [])

    def test_one_second_past_the_threshold_is_stale(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 30 * DAY + 1)
        _, found, _ = self.run_rule()
        self.assertEqual(len(found), 1)

    def test_the_threshold_is_configurable(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 10 * DAY)
        _, silent, _ = self.run_rule()
        self.assertEqual(silent, [])
        _, found, _ = self.run_rule({"stale_days": 7})
        self.assertEqual(len(found), 1)

    def test_a_doc_newer_than_its_code_is_silent(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0 + 45 * DAY)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0)
        _, found, _ = self.run_rule()
        self.assertEqual(found, [])

    def test_a_readme_speaks_for_the_subtree_below_it(self) -> None:
        self.add("src/README.md", "# Source\n", ts=T0)
        self.add("src/pkg/deep/engine.py", "x = 1\n", ts=T0 + 60 * DAY)
        _, found, _ = self.run_rule()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].key, "src/README.md")

    def test_an_unrelated_directory_does_not_pair(self) -> None:
        self.add("docs/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 60 * DAY)
        _, found, _ = self.run_rule()
        self.assertEqual(found, [])

    def test_a_commit_that_touched_the_file_is_added_as_evidence(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 45 * DAY)
        commit = commit_signal("rewrite the engine", ["src/pkg/engine.py"], ts=T0 + 45 * DAY)
        _, found, _ = self.run_rule(extra=[commit])
        quotes = [e.quote for e in found[0].evidence]
        self.assertEqual(len(found[0].evidence), 3)
        self.assertIn("rewrite the engine", quotes[2])

    def test_staleness_never_proposes_an_edit(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 200 * DAY)
        rule, found, ctx = self.run_rule()
        self.assertEqual(len(found), 1)
        self.assertEqual(rule.run_propose(found[0], ctx), [])

    def test_files_without_a_usable_timestamp_are_skipped(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=0.0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 45 * DAY)
        _, found, _ = self.run_rule()
        self.assertEqual(found, [])

    def test_confidence_stays_modest_however_large_the_gap(self) -> None:
        self.add("src/pkg/notes.md", "# Notes\n", ts=T0)
        self.add("src/pkg/engine.py", "x = 1\n", ts=T0 + 3000 * DAY)
        _, found, _ = self.run_rule()
        self.assertLessEqual(found[0].confidence, 0.6)


class RegistrationTest(unittest.TestCase):
    def test_every_rule_is_registered_under_its_id(self) -> None:
        known = registry()
        for rule_id, cls in (
            ("docs.broken_ref", DocsBrokenReference),
            ("docs.undocumented_entrypoint", DocsUndocumentedEntrypoint),
            ("docs.stale", DocsStaleAgainstCode),
        ):
            self.assertIs(known.get(rule_id), cls)
            self.assertIn(KIND_FILE, cls.consumes)


if __name__ == "__main__":
    unittest.main()
