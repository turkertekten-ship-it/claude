"""Tests for the file-hygiene rules.

`KIND_FILE` signals are hand-built rather than produced by walking a fixture
tree: these rules are a claim about *file contents and paths*, and constructing
them directly keeps the walker, the ignore matcher and the redactor out of the
assertion. Two things do touch disk, both inside a TemporaryDirectory - the
untested-module rule asks whether the test file it wants to write already
exists, and every proposal is checked for containment against a real root.

The secret rule is tested the way it runs: the text handed to it has already
been through `redact_secrets`, so the fixtures contain redaction markers and
never a credential. One test feeds a line with unredacted-looking junk beside
the marker and asserts the junk does not reach the evidence.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oodarag.reflect.detect.base import DetectContext
from oodarag.reflect.detect.hygiene import (
    SELF_MODULE_SUFFIX,
    HygieneDebtMarker,
    HygieneLeakedSecret,
    HygieneOversizedModule,
    HygieneUntestedModule,
    _class_name,
    file_signals,
    line_count,
    rel_path,
    top_level_definitions,
)
from oodarag.reflect.models import (
    ACTOR_HUMAN,
    ACTOR_MACHINE,
    KIND_COMMIT,
    KIND_FILE,
    Signal,
)

# A fixed point in time so day bucketing is deterministic on any machine.
T0 = 1_756_200_000.0
DAY = 86_400.0


def file_signal(path: str, text: str, ts: float = T0, ordinal: int = 0) -> Signal:
    """A workspace file observation, shaped the way WorkspaceFileSource shapes one."""
    name = path.rsplit("/", 1)[-1]
    ext = "." + name.rsplit(".", 1)[-1] if "." in name[1:] else ""
    return Signal(
        kind=KIND_FILE,
        source="workspace:files",
        text=text,
        ts=ts,
        uri=path,
        session="workspace",
        ordinal=ordinal,
        actor=ACTOR_MACHINE,
        metadata={
            "size": len(text),
            "ext": ext,
            "line_count": len(text.splitlines()),
            "is_code": ext in {".py", ".js", ".go"},
            "is_test": "test" in path.lower(),
            "depth": path.count("/"),
        },
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
        metadata={"sha": "abc123def456", "author": "t", "subject": subject, "files": files},
    )


def module_text(lines: int, public: int = 2) -> str:
    """A plausible module of a given length with some public definitions."""
    body = ["from __future__ import annotations", ""]
    for i in range(public):
        body.append(f"def public_{i}(value):")
        body.append("    return value")
        body.append("")
    body.append("def _private():")
    body.append("    return None")
    while len(body) < lines:
        body.append(f"CONSTANT_{len(body)} = {len(body)}")
    return "\n".join(body[:lines])


class HygieneTestCase(unittest.TestCase):
    """Shared workspace root. Nothing here ever reads the developer's home."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def context(self, signals: list[Signal]) -> DetectContext:
        return DetectContext(signals=signals, root=self.root, now=T0 + DAY)

    def write(self, relpath: str, text: str) -> Path:
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


# -- shared helpers ----------------------------------------------------------


class PathHelperTests(HygieneTestCase):
    def test_rel_path_rejects_paths_it_cannot_own(self) -> None:
        for uri in ("/etc/passwd", "../outside.py", "", "https://example.com/x.py", "git:abc"):
            with self.subTest(uri=uri):
                sig = Signal(kind=KIND_FILE, source="workspace:files", text="x", uri=uri)
                self.assertEqual(rel_path(sig), "")

    def test_rel_path_normalizes_a_relative_path(self) -> None:
        self.assertEqual(rel_path(file_signal("./src/a.py", "x")), "src/a.py")

    def test_file_signals_keeps_the_newest_observation_per_path(self) -> None:
        old = file_signal("src/a.py", "old", ts=T0)
        new = file_signal("src/a.py", "new", ts=T0 + 10)
        signals = file_signals(self.context([old, new]))
        self.assertEqual([s.text for s in signals], ["new"])

    def test_line_count_falls_back_when_metadata_lies(self) -> None:
        sig = file_signal("src/a.py", "a\nb\nc")
        sig.metadata["line_count"] = "not a number"
        self.assertEqual(line_count(sig), 3)

    def test_top_level_definitions_ignores_nested_ones(self) -> None:
        text = "class Thing:\n    def method(self):\n        pass\n\ndef top():\n    pass\n"
        found = [(d.kind, d.name) for d in top_level_definitions(text)]
        self.assertEqual(found, [("class", "Thing"), ("def", "top")])

    def test_class_name_is_derived_from_the_stem(self) -> None:
        self.assertEqual(_class_name("src/pkg/text_utils.py"), "TextUtils")


# -- 1. debt markers ---------------------------------------------------------


class DebtMarkerTests(HygieneTestCase):
    def test_reports_one_row_per_file_with_line_numbered_evidence(self) -> None:
        text = "x = 1\n# TODO: rename this\ny = 2\n# FIXME: and this\n"
        findings = HygieneDebtMarker().run(self.context([file_signal("src/pkg/a.py", text)]))
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.key, "src/pkg/a.py")
        self.assertEqual(finding.metadata["count"], 2)
        self.assertEqual(finding.metadata["markers"], {"TODO": 1, "FIXME": 1})
        self.assertEqual(finding.severity, "low")
        self.assertEqual(len(finding.evidence), 2)
        self.assertTrue(finding.evidence[0].quote.startswith("src/pkg/a.py:2: "))
        self.assertIn("rename this", finding.evidence[0].quote)

    def test_a_loud_file_is_escalated_and_quotes_are_capped(self) -> None:
        text = "\n".join(f"# TODO: item {i}" for i in range(7))
        findings = HygieneDebtMarker().run(self.context([file_signal("src/pkg/a.py", text)]))
        self.assertEqual(findings[0].severity, "medium")
        self.assertTrue(findings[0].metadata["loud"])
        self.assertEqual(len(findings[0].evidence), 3)
        self.assertEqual(findings[0].metadata["count"], 7)

    def test_thresholds_and_markers_come_from_config(self) -> None:
        text = "# TODO: a\n# NOTE: b\n"
        rule = HygieneDebtMarker({"loud_threshold": 1, "markers": ["NOTE"]})
        findings = rule.run(self.context([file_signal("src/pkg/a.py", text)]))
        self.assertEqual(findings[0].metadata["markers"], {"NOTE": 1})
        self.assertEqual(findings[0].severity, "medium")

    def test_tests_and_this_rules_own_source_are_exempt(self) -> None:
        signals = [
            file_signal("tests/test_a.py", "# TODO: cover the error path\n"),
            file_signal("src/" + SELF_MODULE_SUFFIX, "# TODO: not my own vocabulary\n"),
        ]
        self.assertEqual(HygieneDebtMarker().run(self.context(signals)), [])

    def test_the_exemption_is_config_overridable(self) -> None:
        signals = [file_signal("tests/test_a.py", "# TODO: cover the error path\n")]
        rule = HygieneDebtMarker({"exclude_prefixes": ["vendor/"], "exclude_self": False})
        self.assertEqual(len(rule.run(self.context(signals))), 1)

    def test_the_word_in_prose_is_not_a_marker(self) -> None:
        # A README describing what this rule looks for is the canonical case:
        # the words are there, the deferral is not, and the finding it would
        # produce could never be resolved.
        text = "| `hygiene.debt_marker` | TODO/FIXME/XXX markers, one row per file |\n"
        self.assertEqual(
            HygieneDebtMarker().run(self.context([file_signal("README.md", text)])), []
        )

    def test_punctuation_or_a_comment_opener_makes_it_a_marker(self) -> None:
        for line in ("TODO: rename", "TODO(alice): rename", "# TODO rename", "// FIXME rename"):
            with self.subTest(line=line):
                findings = HygieneDebtMarker().run(
                    self.context([file_signal("src/a.py", line + "\n")])
                )
                self.assertEqual(len(findings), 1)

    def test_prose_and_partial_words_are_not_markers(self) -> None:
        text = "The todo list is long.\nTODOS are not markers.\nxTODOx neither.\ndebug()\n"
        self.assertEqual(
            HygieneDebtMarker().run(self.context([file_signal("docs/notes.md", text)])), []
        )

    def test_a_line_with_two_markers_counts_once(self) -> None:
        text = "# TODO/FIXME: one deferral, two words\n"
        findings = HygieneDebtMarker().run(self.context([file_signal("src/a.py", text)]))
        self.assertEqual(findings[0].metadata["count"], 1)

    def test_hostile_paths_are_dropped_rather_than_reported(self) -> None:
        hostile = [
            file_signal("/etc/shadow", "# TODO: absolute"),
            file_signal("../../elsewhere.py", "# TODO: escape"),
            file_signal("", "# TODO: nameless"),
        ]
        self.assertEqual(HygieneDebtMarker().run(self.context(hostile)), [])

    def test_the_rule_proposes_nothing(self) -> None:
        rule = HygieneDebtMarker()
        ctx = self.context([file_signal("src/a.py", "# TODO: x\n")])
        finding = rule.run(ctx)[0]
        self.assertEqual(rule.run_propose(finding, ctx), [])


# -- 2. leaked secrets -------------------------------------------------------


class LeakedSecretTests(HygieneTestCase):
    def test_a_redaction_marker_is_the_evidence_of_a_leak(self) -> None:
        # What a real signal looks like: the source redacted the token on the
        # way out, so the marker is all the rule ever sees.
        text = 'HOST = "example.com"\nGITHUB_TOKEN = "<redacted:github-token>"\n'
        findings = HygieneLeakedSecret().run(self.context([file_signal("deploy/.env", text)]))
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.severity, "critical")
        self.assertEqual(finding.key, "deploy/.env")
        self.assertEqual(finding.metadata["action"], "rotate-and-remove")
        self.assertEqual(finding.metadata["kinds"], ["github-token"])
        self.assertEqual(finding.metadata["lines"], [2])
        self.assertEqual(finding.evidence[0].quote, "deploy/.env:2: <redacted:github-token>")

    def test_evidence_never_carries_what_sits_beside_the_marker(self) -> None:
        # The redactor replaces what it matched and nothing else, so the rest of
        # the line may still hold something nobody wants written to a report.
        text = 'key = "<redacted:api-key>"  # rotated from AKIAOLDLEFTOVERVALUE\n'
        findings = HygieneLeakedSecret().run(self.context([file_signal("conf/app.ini", text)]))
        quote = findings[0].evidence[0].quote
        self.assertIn("conf/app.ini:1:", quote)
        self.assertIn("<redacted:api-key>", quote)
        self.assertNotIn("AKIAOLDLEFTOVERVALUE", quote)
        self.assertNotIn("rotated", quote)

    def test_the_bare_marker_counts_too(self) -> None:
        findings = HygieneLeakedSecret().run(
            self.context([file_signal("conf/app.ini", "password = <redacted>\n")])
        )
        self.assertEqual(findings[0].metadata["kinds"], ["unspecified"])

    def test_the_word_redacted_alone_is_not_a_marker(self) -> None:
        text = "This value is redacted in the report; see docs/redacted.md.\n"
        self.assertEqual(
            HygieneLeakedSecret().run(self.context([file_signal("docs/a.md", text)])), []
        )

    def test_fixture_paths_are_skipped_but_counted(self) -> None:
        signals = [
            file_signal("deploy/.env", 'TOKEN = "<redacted:github-token>"\n'),
            file_signal(
                "tests/fixtures/creds.env",
                'A = "<redacted:api-key>"\nB = "<redacted:slack-token>"\n',
            ),
            file_signal("docs/example.env", 'C = "<redacted>"\n'),
        ]
        findings = HygieneLeakedSecret().run(self.context(signals))
        self.assertEqual([f.key for f in findings], ["deploy/.env"])
        self.assertEqual(findings[0].metadata["fixture_files_skipped"], 2)
        self.assertEqual(findings[0].metadata["fixture_matches_skipped"], 3)

    def test_a_tree_of_nothing_but_fixtures_reports_nothing(self) -> None:
        signals = [file_signal("tests/fixtures/creds.env", 'A = "<redacted:api-key>"\n')]
        self.assertEqual(HygieneLeakedSecret().run(self.context(signals)), [])

    def test_fixture_markers_are_config_overridable(self) -> None:
        signals = [file_signal("tests/fixtures/creds.env", 'A = "<redacted:api-key>"\n')]
        rule = HygieneLeakedSecret({"fixture_markers": ["golden/"]})
        self.assertEqual(len(rule.run(self.context(signals))), 1)

    def test_a_file_that_merely_defines_the_markers_is_not_a_leak(self) -> None:
        # The source records whether redaction actually fired. False means the
        # markers were in the file to begin with - the redactor's own source,
        # its tests, a README quoting one - which is a description of a secret
        # and not the trace of one.
        sig = file_signal("src/util/text.py", 'REPLACEMENT = "<redacted:github-token>"\n')
        sig.metadata["redacted"] = False
        self.assertEqual(HygieneLeakedSecret().run(self.context([sig])), [])

    def test_a_file_the_redactor_actually_scrubbed_is_a_leak(self) -> None:
        sig = file_signal("deploy/.env", 'T = "<redacted:github-token>"\n')
        sig.metadata["redacted"] = True
        self.assertEqual(len(HygieneLeakedSecret().run(self.context([sig]))), 1)

    def test_a_signal_without_the_flag_falls_back_to_the_marker(self) -> None:
        # An older source, or one that never redacts, leaves the rule on its own
        # evidence rather than silencing it.
        sig = file_signal("deploy/.env", 'T = "<redacted:github-token>"\n')
        sig.metadata.pop("redacted", None)
        self.assertEqual(len(HygieneLeakedSecret().run(self.context([sig]))), 1)

    def test_it_never_proposes_an_edit(self) -> None:
        rule = HygieneLeakedSecret()
        ctx = self.context([file_signal("deploy/.env", 'T = "<redacted:github-token>"\n')])
        finding = rule.run(ctx)[0]
        self.assertEqual(rule.run_propose(finding, ctx), [])

    def test_many_hits_are_quoted_within_the_cap(self) -> None:
        text = "\n".join(f'K{i} = "<redacted:api-key>"' for i in range(9))
        findings = HygieneLeakedSecret().run(self.context([file_signal("conf/app.ini", text)]))
        self.assertEqual(findings[0].metadata["count"], 9)
        self.assertEqual(len(findings[0].evidence), 3)
        self.assertLessEqual(findings[0].confidence, 0.95)


# -- 3. untested modules -----------------------------------------------------


class UntestedModuleTests(HygieneTestCase):
    def module(self, path: str = "src/pkg/thing.py", lines: int = 60) -> Signal:
        return file_signal(path, module_text(lines))

    def test_a_module_no_test_names_is_reported_once(self) -> None:
        signals = [self.module(), file_signal("src/pkg/other.py", module_text(40))]
        findings = HygieneUntestedModule().run(self.context(signals))
        keys = [f.key for f in findings]
        self.assertEqual(sorted(keys), ["src/pkg/other.py", "src/pkg/thing.py"])
        finding = next(f for f in findings if f.key == "src/pkg/thing.py")
        self.assertEqual(finding.metadata["import_path"], "pkg.thing")
        self.assertEqual(finding.metadata["suggested_test"], "tests/test_thing.py")
        self.assertEqual(finding.metadata["line_count"], 60)
        self.assertIn("def public_0", finding.metadata["public_names"])
        self.assertTrue(finding.evidence)
        self.assertIn("no test mentions", finding.evidence[0].quote)

    def test_a_test_that_imports_the_module_suppresses_it(self) -> None:
        signals = [
            self.module(),
            file_signal("tests/test_thing.py", "from pkg.thing import public_0\n"),
        ]
        self.assertEqual(HygieneUntestedModule().run(self.context(signals)), [])

    def test_prose_naming_the_stem_does_not_suppress_it(self) -> None:
        """A comment is not a test, and the bare stem is far too loose a match.

        This rule previously suppressed on any word-boundary hit anywhere in any
        test file. On this repository the HTML scraper read as covered because
        an unrelated HTTP test contained a "text/html" content type, and the web
        connector because its stem is an ordinary English word - so the rule
        fell silent about exactly the modules it exists to find, with nothing to
        show that it had.

        Note the shape of this docstring: naming a module in its qualified form
        would itself suppress the finding for that module, since prose in a test
        file is still a mention. That is a real limit of the heuristic, so the
        examples above are deliberately written without a path.
        """
        signals = [
            self.module(),
            file_signal("tests/test_bundle.py", "# exercises the thing module end to end\n"),
        ]
        self.assertEqual(len(HygieneUntestedModule().run(self.context(signals))), 1)

    def test_an_unrelated_path_sharing_the_stem_does_not_suppress_it(self) -> None:
        """The case that was really happening: a content type is not a module."""
        signals = [
            self.module(),
            file_signal("tests/test_other.py", 'headers = {"content-type": "text/thing"}\n'),
        ]
        self.assertEqual(len(HygieneUntestedModule().run(self.context(signals))), 1)

    def test_a_qualified_reference_does_suppress_it(self) -> None:
        for reference in ("pkg.thing", "pkg/thing", "src/pkg/thing.py"):
            with self.subTest(reference=reference):
                signals = [
                    self.module(),
                    file_signal("tests/test_bundle.py", f"# covers {reference}\n"),
                ]
                self.assertEqual(HygieneUntestedModule().run(self.context(signals)), [])

    def test_a_stem_inside_a_longer_word_does_not_suppress_it(self) -> None:
        signals = [
            self.module(),
            file_signal("tests/test_bundle.py", "# covers everything_thingy in one go\n"),
        ]
        self.assertEqual(len(HygieneUntestedModule().run(self.context(signals))), 1)

    def test_dunder_init_tests_and_tiny_modules_are_not_candidates(self) -> None:
        signals = [
            file_signal("src/pkg/__init__.py", module_text(60)),
            file_signal("tests/helpers.py", module_text(60)),
            file_signal("src/pkg/tiny.py", "x = 1\ny = 2\n"),
        ]
        self.assertEqual(HygieneUntestedModule().run(self.context(signals)), [])

    def test_size_carries_the_confidence(self) -> None:
        small = HygieneUntestedModule().run(
            self.context([file_signal("src/pkg/small.py", module_text(25))])
        )[0]
        large = HygieneUntestedModule().run(
            self.context([file_signal("src/pkg/large.py", module_text(500))])
        )[0]
        self.assertLess(small.confidence, large.confidence)
        self.assertLessEqual(large.confidence, 0.85)
        self.assertEqual(large.metadata["line_count"], 500)

    def test_recent_commits_raise_confidence_and_add_evidence(self) -> None:
        quiet = HygieneUntestedModule().run(self.context([self.module()]))[0]
        churned = HygieneUntestedModule().run(
            self.context(
                [self.module(), commit_signal("rework the thing loader", ["src/pkg/thing.py"])]
            )
        )[0]
        self.assertGreater(churned.confidence, quiet.confidence)
        self.assertEqual(churned.metadata["recent_commits"], 1)
        self.assertEqual(len(churned.evidence), 2)
        self.assertIn("rework the thing loader", churned.evidence[1].quote)

    def test_a_flat_layout_still_gets_examined(self) -> None:
        findings = HygieneUntestedModule().run(
            self.context([file_signal("pkg/thing.py", module_text(60))])
        )
        self.assertEqual(findings[0].metadata["import_path"], "pkg.thing")

    def test_two_modules_sharing_a_stem_do_not_fight_over_one_test_path(self) -> None:
        rule = HygieneUntestedModule()
        ctx = self.context(
            [
                file_signal("src/pkg/ingest/base.py", module_text(60)),
                file_signal("src/pkg/sources/base.py", module_text(60)),
            ]
        )
        findings = rule.run(ctx)
        self.assertEqual(len(findings), 2)
        paths = sorted(f.metadata["suggested_test"] for f in findings)
        self.assertEqual(paths, ["tests/test_ingest_base.py", "tests/test_sources_base.py"])
        edits = sorted(p.edits[0].path for f in findings for p in rule.run_propose(f, ctx))
        self.assertEqual(edits, paths)  # two creates, two destinations

    def test_the_skeleton_proposal_is_a_reviewable_create(self) -> None:
        rule = HygieneUntestedModule()
        ctx = self.context([self.module()])
        finding = rule.run(ctx)[0]
        proposals = rule.run_propose(finding, ctx)
        self.assertEqual(len(proposals), 1)
        proposal = proposals[0]
        self.assertEqual(proposal.risk, "review")
        self.assertEqual(len(proposal.edits), 1)
        edit = proposal.edits[0]
        self.assertEqual(edit.op, "create")
        self.assertEqual(edit.path, "tests/test_thing.py")
        self.assertFalse(Path(edit.path).is_absolute())
        self.assertNotIn("..", Path(edit.path).parts)
        self.assertIn('MODULE = "pkg.thing"', edit.text)
        self.assertIn("importlib.import_module(MODULE)", edit.text)
        self.assertIn("class ThingImportTest(unittest.TestCase)", edit.text)
        self.assertIn("TODO", edit.text)
        self.assertIn("#   - def public_0", edit.text)
        self.assertIn("from __future__ import annotations", edit.text)

    def test_the_skeleton_is_valid_python(self) -> None:
        rule = HygieneUntestedModule()
        ctx = self.context([self.module()])
        text = rule.run_propose(rule.run(ctx)[0], ctx)[0].edits[0].text
        compile(text, "tests/test_thing.py", "exec")  # a broken skeleton is worse than none

    def test_no_proposal_when_the_test_path_is_already_taken(self) -> None:
        self.write("tests/test_thing.py", "# somebody's file\n")
        rule = HygieneUntestedModule()
        ctx = self.context([self.module()])
        finding = rule.run(ctx)[0]
        self.assertEqual(rule.run_propose(finding, ctx), [])
        self.assertEqual(finding.key, "src/pkg/thing.py")  # the finding still stands

    def test_a_module_without_a_dotted_import_path_is_reported_not_proposed(self) -> None:
        rule = HygieneUntestedModule()
        ctx = self.context([file_signal("src/pkg/my-mod.py", module_text(60))])
        finding = rule.run(ctx)[0]
        self.assertEqual(finding.metadata["import_path"], "")
        self.assertEqual(rule.run_propose(finding, ctx), [])

    def test_thresholds_are_config(self) -> None:
        signals = [file_signal("src/pkg/tiny.py", module_text(10))]
        rule = HygieneUntestedModule({"min_lines": 5, "test_dir": "t"})
        findings = rule.run(self.context(signals))
        self.assertEqual(findings[0].metadata["suggested_test"], "t/test_tiny.py")

    def test_a_huge_test_corpus_is_truncated_rather_than_held(self) -> None:
        big = file_signal("tests/test_big.py", "thing\n" * 5_000)
        rule = HygieneUntestedModule({"max_test_chars": 10})
        # The corpus is cut before the mention is read, so the module is
        # reported: truncation must fail towards saying something, not towards
        # silently pretending coverage exists.
        findings = rule.run(self.context([self.module(), big]))
        self.assertEqual([f.key for f in findings], ["src/pkg/thing.py"])


# -- 4. oversized modules ----------------------------------------------------


class OversizedModuleTests(HygieneTestCase):
    def test_the_threshold_is_a_boundary_not_a_range(self) -> None:
        at_limit = file_signal("src/pkg/a.py", module_text(600))
        self.assertEqual(HygieneOversizedModule().run(self.context([at_limit])), [])
        over = file_signal("src/pkg/a.py", module_text(601))
        findings = HygieneOversizedModule().run(self.context([over]))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].metadata["line_count"], 601)
        self.assertEqual(findings[0].metadata["over_by"], 1)

    def test_the_definition_count_travels_with_the_finding(self) -> None:
        text = module_text(700, public=4)
        findings = HygieneOversizedModule().run(self.context([file_signal("src/a.py", text)]))
        finding = findings[0]
        self.assertEqual(finding.metadata["top_level_definitions"], 5)  # 4 public + 1 private
        self.assertEqual(finding.metadata["defs"], 5)
        self.assertEqual(finding.metadata["classes"], 0)
        self.assertEqual(finding.severity, "low")
        self.assertTrue(finding.evidence)
        self.assertIn("100 over 600", finding.evidence[0].quote)
        self.assertIn("src/a.py:3: def public_0", finding.evidence[1].quote)

    def test_data_files_are_not_modules(self) -> None:
        long_data = "\n".join(f"- item {i}" for i in range(900))
        signals = [
            file_signal("data/big.yaml", long_data),
            file_signal("docs/big.md", long_data),
            file_signal("package-lock.json", long_data),
        ]
        self.assertEqual(HygieneOversizedModule().run(self.context(signals)), [])

    def test_max_lines_is_config(self) -> None:
        rule = HygieneOversizedModule({"max_lines": 10})
        findings = rule.run(self.context([file_signal("src/a.py", module_text(40))]))
        self.assertEqual(findings[0].metadata["max_lines"], 10)
        self.assertGreaterEqual(findings[0].confidence, 0.4)
        self.assertLessEqual(findings[0].confidence, 0.9)

    def test_it_proposes_nothing(self) -> None:
        rule = HygieneOversizedModule()
        ctx = self.context([file_signal("src/a.py", module_text(900))])
        self.assertEqual(rule.run_propose(rule.run(ctx)[0], ctx), [])


# -- cross-rule properties ---------------------------------------------------


class RuleContractTests(HygieneTestCase):
    def all_rules(self) -> list[object]:
        return [
            HygieneDebtMarker(),
            HygieneLeakedSecret(),
            HygieneUntestedModule(),
            HygieneOversizedModule(),
        ]

    def signals(self) -> list[Signal]:
        return [
            file_signal("src/pkg/thing.py", "# TODO: split this\n" + module_text(700)),
            file_signal("deploy/.env", 'TOKEN = "<redacted:github-token>"\n'),
        ]

    def test_every_finding_carries_evidence_a_key_and_a_sane_confidence(self) -> None:
        ctx = self.context(self.signals())
        seen = 0
        for rule in self.all_rules():
            for finding in rule.run(ctx):
                seen += 1
                with self.subTest(rule=rule.rule_id, key=finding.key):
                    self.assertTrue(finding.evidence)
                    self.assertTrue(finding.key)
                    self.assertTrue(finding.fingerprint)
                    self.assertGreaterEqual(finding.confidence, 0.0)
                    self.assertLessEqual(finding.confidence, 1.0)
        self.assertGreaterEqual(seen, 4)

    def test_fingerprints_are_stable_across_two_nights(self) -> None:
        first = self.context(self.signals())
        second = self.context([file_signal(s.uri, s.text, ts=T0 + DAY) for s in self.signals()])
        for rule in self.all_rules():
            with self.subTest(rule=rule.rule_id):
                self.assertEqual(
                    [f.fingerprint for f in rule.run(first)],
                    [f.fingerprint for f in rule.run(second)],
                )

    def test_no_rule_raises_on_hostile_input(self) -> None:
        hostile = [
            file_signal("src/a.py", "\x00\x01 binary-ish � TODO <redacted:api-key>"),
            file_signal("src/b.py", "TODO" * 10_000),
            file_signal("weird/‮evil.py", "# FIXME: right-to-left override"),
            Signal(kind=KIND_FILE, source="workspace:files", text="", uri="src/c.py"),
        ]
        ctx = self.context(hostile)
        for rule in self.all_rules():
            with self.subTest(rule=rule.rule_id):
                for finding in rule.run(ctx):
                    self.assertEqual(rule.run_propose(finding, ctx), rule.run_propose(finding, ctx))


if __name__ == "__main__":
    unittest.main()
