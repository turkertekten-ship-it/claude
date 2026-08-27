"""The contract between what the observer redacted and what the rules conclude.

`sources/base` stamps `metadata["redacted"]` with whether `redact_secrets`
actually changed the text. Exactly one rule may act on that flag, and getting
the blast radius wrong is silent in both directions: too narrow and
`hygiene.leaked_secret` reports the redaction module itself as a leak every
night; too wide and `hygiene.debt_marker` skips every file in the repository and
simply reports nothing, forever, with no error anywhere.

Both directions have happened during development, which is why they are pinned
here rather than left to the rules' own tests.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from oodarag.reflect.detect.base import DetectContext, build_detectors
from oodarag.reflect.models import KIND_FILE, Finding, Signal

MARKER_TEXT = 'REDACTIONS = {"github": "<redacted:github-token>"}\n'
DEBT_TEXT = "def f():\n    # TODO: handle the empty case\n    return 1\n"


class RedactionContractTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def signal(self, rel: str, text: str, redacted: bool | None) -> Signal:
        meta: dict = {"is_doc": False, "is_code": True, "ext": ".py",
                      "line_count": text.count("\n")}
        if redacted is not None:
            meta["redacted"] = redacted
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return Signal(kind=KIND_FILE, source="workspace:files", text=text, uri=rel,
                      session="workspace", metadata=meta)

    def findings(self, rule: str, signals: list[Signal]) -> list[Finding]:
        ctx = DetectContext(signals=signals, root=self.root, now=time.time())
        out: list[Finding] = []
        for detector in build_detectors(enabled=[rule]):
            out.extend(detector.run(ctx))
        return out


class TestLeakedSecretTrustsTheObserver(RedactionContractTestCase):
    def test_a_file_that_defines_the_markers_is_not_a_leak(self) -> None:
        """The redaction module contains the marker text and holds no secret."""
        signal = self.signal("src/pkg/redact.py", MARKER_TEXT, redacted=False)
        self.assertEqual(self.findings("hygiene.leaked_secret", [signal]), [])

    def test_a_file_that_was_actually_redacted_is_a_leak(self) -> None:
        signal = self.signal("src/pkg/config.py", MARKER_TEXT, redacted=True)
        found = self.findings("hygiene.leaked_secret", [signal])
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, "critical")
        self.assertNotIn("ghp_", found[0].detail, "the secret must never be echoed")

    def test_absent_metadata_falls_back_to_matching(self) -> None:
        """Hand-built signals, and any future source that forgets to stamp it."""
        signal = self.signal("src/pkg/config.py", MARKER_TEXT, redacted=None)
        self.assertEqual(len(self.findings("hygiene.leaked_secret", [signal])), 1)


class TestTheGuardIsScopedToThatOneRule(RedactionContractTestCase):
    def test_debt_markers_are_found_in_unredacted_files(self) -> None:
        """The regression: this guard once suppressed every file for this rule.

        Almost no file is ever redacted, so applying the credential guard here
        turns the rule off across the whole repository while still reporting
        success.
        """
        signal = self.signal("src/pkg/engine.py", DEBT_TEXT, redacted=False)
        found = self.findings("hygiene.debt_marker", [signal])
        self.assertEqual(len(found), 1, "a TODO in an unredacted file is still a TODO")

    def test_other_hygiene_rules_ignore_the_flag_entirely(self) -> None:
        big = "".join(f"x = {n}\n" for n in range(800))
        signal = self.signal("src/pkg/huge.py", big, redacted=False)
        self.assertEqual(len(self.findings("hygiene.oversized_module", [signal])), 1)


if __name__ == "__main__":
    unittest.main()
