"""The framework's own invariants.

These tests exist for one reason: the anti-fabrication rule is only real if it
is enforced at construction time. If `Finding` ever starts accepting a verdict
with no evidence, every report the tool has ever produced becomes unfalsifiable
and nothing else in the suite would notice.
"""

from __future__ import annotations

import unittest

from tools.evidence import (
    Claim,
    Evidence,
    EvidenceKind,
    Finding,
    Report,
    Severity,
    Verdict,
)


def claim(text: str = "the pipeline is fast") -> Claim:
    return Claim(text=text, path="README.md", line=7)


class TestEvidenceInvariants(unittest.TestCase):
    def test_absence_requires_a_search_space(self):
        with self.assertRaises(ValueError):
            Evidence.absent("no such file", [])
        ok = Evidence.absent("no such file", ["/repo"])
        self.assertEqual(ok.kind, EvidenceKind.ABSENCE)
        self.assertIn("/repo", ok.locator)

    def test_file_evidence_requires_a_path(self):
        with self.assertRaises(ValueError):
            Evidence(kind=EvidenceKind.FILE, summary="somewhere")

    def test_command_evidence_requires_argv(self):
        with self.assertRaises(ValueError):
            Evidence(kind=EvidenceKind.COMMAND, summary="it failed")

    def test_ran_records_real_exit_code(self):
        good = Evidence.ran(["python3", "-c", "print('hi')"])
        self.assertEqual(good.exit_code, 0)
        bad = Evidence.ran(["python3", "-c", "import sys; sys.exit(3)"])
        self.assertEqual(bad.exit_code, 3)

    def test_ran_survives_a_missing_binary(self):
        missing = Evidence.ran(["definitely-not-a-real-binary-xyz"])
        self.assertIsNone(missing.exit_code)
        self.assertIn("FileNotFoundError", missing.output)

    def test_ran_truncation_keeps_the_end(self):
        noisy = Evidence.ran(["python3", "-c", "print('x' * 5000); print('THE_CAUSE')"])
        self.assertIn("THE_CAUSE", noisy.output)
        self.assertIn("truncated", noisy.output)

    def test_locator_is_clickable_for_file_evidence(self):
        self.assertEqual(Evidence.at("src/a.py", 12, "x = 1").locator, "src/a.py:12")


class TestFindingRequiresEvidence(unittest.TestCase):
    def test_verdict_without_evidence_is_refused(self):
        for verdict in (Verdict.SUPPORTED, Verdict.UNSUPPORTED, Verdict.CONTRADICTED):
            with self.subTest(verdict=verdict):
                with self.assertRaises(ValueError):
                    Finding(checker="t", code="C", verdict=verdict,
                            severity=Severity.ERROR, claim=claim())

    def test_unverifiable_requires_a_reason(self):
        with self.assertRaises(ValueError):
            Finding(checker="t", code="C", verdict=Verdict.UNVERIFIABLE,
                    severity=Severity.INFO, claim=claim())
        ok = Finding(checker="t", code="C", verdict=Verdict.UNVERIFIABLE,
                     severity=Severity.INFO, claim=claim(), detail="network disabled")
        self.assertFalse(ok.is_problem)

    def test_evidenced_finding_is_accepted(self):
        f = Finding(checker="t", code="C", verdict=Verdict.CONTRADICTED,
                    severity=Severity.ERROR, claim=claim(),
                    evidence=[Evidence.at("README.md", 7, "the pipeline is fast")])
        self.assertTrue(f.is_problem)
        self.assertEqual(f.as_dict()["locator"], "README.md:7")


class TestReport(unittest.TestCase):
    def _report(self) -> Report:
        r = Report(root="/repo")
        r.add(Finding(checker="a", code="BROKEN", verdict=Verdict.CONTRADICTED,
                      severity=Severity.ERROR, claim=claim("make test works"),
                      evidence=[Evidence.ran(["python3", "-c", "import sys; sys.exit(2)"])]))
        r.add(Finding(checker="b", code="VAGUE", verdict=Verdict.UNSUPPORTED,
                      severity=Severity.WARN, claim=claim("handles 8 MiB"),
                      evidence=[Evidence.absent("no literal found", ["src/"])]))
        r.add(Finding(checker="c", code="NONET", verdict=Verdict.UNVERIFIABLE,
                      severity=Severity.INFO, claim=claim("the link resolves"),
                      detail="network disabled"))
        return r

    def test_exit_code_is_driven_by_errors_only(self):
        r = self._report()
        self.assertEqual(r.exit_code, 1)
        clean = Report(root="/repo")
        clean.add(Finding(checker="c", code="NONET", verdict=Verdict.UNVERIFIABLE,
                          severity=Severity.INFO, claim=claim(), detail="network disabled"))
        self.assertEqual(clean.exit_code, 0, "unverifiable must not fail a run")

    def test_unverifiable_is_never_counted_as_a_problem(self):
        r = self._report()
        self.assertEqual(len(r.problems), 2)
        self.assertEqual(len(r.unverifiable), 1)

    def test_markdown_always_surfaces_unverifiable(self):
        md = self._report().to_markdown()
        self.assertIn("unverifiable", md)
        self.assertIn("network disabled", md)
        self.assertIn("cannot be mistaken for", md)

    def test_json_roundtrips(self):
        import json

        payload = json.loads(self._report().to_json())
        self.assertEqual(payload["problem_count"], 2)
        self.assertEqual(payload["counts"]["unverifiable"], 1)
        self.assertTrue(all("evidence" in f for f in payload["findings"]))


if __name__ == "__main__":
    unittest.main()


class TestExitCodeZeroSurvives(unittest.TestCase):
    """A successful command's exit status is evidence.

    Regression: the dict builder elided falsey values, and `0 in ("", (), None, 0)`
    is True - so every passing command was serialised with its outcome missing.
    """

    def test_zero_exit_code_is_serialised(self):
        e = Evidence.ran(["python3", "-c", "pass"])
        self.assertEqual(e.exit_code, 0)
        self.assertIn("exit_code", e.as_dict())
        self.assertEqual(e.as_dict()["exit_code"], 0)

    def test_missing_binary_has_no_exit_code_key(self):
        e = Evidence.ran(["definitely-not-a-real-binary-xyz"])
        self.assertNotIn("exit_code", e.as_dict())


class TestValueEvidenceNamesItsSource(unittest.TestCase):
    """A computed number with no source looks rigorous and points at nothing."""

    def test_measured_without_a_source_is_refused(self):
        with self.assertRaises(ValueError):
            Evidence.measured("47 files scanned", value=47)

    def test_a_path_satisfies_it(self):
        e = Evidence.measured("47 files", value=47, path="src/")
        self.assertEqual(e.locator, "src/")

    def test_derived_from_satisfies_it(self):
        e = Evidence.measured("47 files", value=47, derived_from=["a.py", "b.py"])
        self.assertIn("a.py", e.locator)

    def test_a_sourceless_value_cannot_prop_up_a_verdict(self):
        # Without the invariant this constructs cleanly, and a CONTRADICTED
        # finding ends up resting on a number from nowhere.
        with self.assertRaises(ValueError):
            Finding(checker="t", code="C", verdict=Verdict.CONTRADICTED,
                    severity=Severity.ERROR, claim=claim(),
                    evidence=[Evidence.measured("it is 3x slower", value=3)])
