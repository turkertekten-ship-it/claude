"""Numbers in the living documentation must match what the repository holds.

Six documented numbers were wrong at once, found by re-running the commands
that produced them rather than reading them (L49): an ablation table stale in
its pass column in two files, a quarantine count copied without its unit in
three, and "fourteen PyPI project pages" for a corpus that has held 91 since
the widening.

Hand-fixing the same number in a third file is the signal to stop hand-fixing
it. These assert the claims that are free to check - corpus size and golden-set
size - against the files themselves.

Deliberately *not* covered, and why: the ablation table's pass rates need a
built index and a full sweep, which is minutes, and the contamination counts
need an index too. Those are refreshed by running `scripts/ablation.py` and the
eval; this file cannot make that cheap and does not pretend to.

`internal/LEARNINGS.md` is excluded on purpose. Those entries describe a moment
and their numbers are correct as history - "fourteen pages" is right there and
wrong in `docs/EVALUATION.md`, which describes the present.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Documents that describe the present. LEARNINGS and the ADRs' historical
#: passages are not in scope - see the module docstring.
LIVING_DOCS = ("docs/EVALUATION.md", "internal/PLAN.md",
               "docs/adr/0004-hybrid-retrieval.md", "README.md")


def _text(rel: str) -> str:
    path = ROOT / rel
    return path.read_text("utf-8") if path.exists() else ""


#: Spelled-out counts, because the defect this file exists for was written in
#: words: "fourteen PyPI project pages" for a corpus of 91. A digits-only
#: pattern missed the exact case it was added to catch, which mutation testing
#: found and no amount of re-reading would have.
WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
}
_COUNT = r"(\d+|" + "|".join(WORD_NUMBERS) + r")"


def _as_int(token: str) -> int:
    return int(token) if token.isdigit() else WORD_NUMBERS[token.lower()]


def _external_corpus_size() -> int:
    return len(list((ROOT / "corpus/external/pypi").glob("*.md")))


def _golden_count(rel: str) -> int:
    lines = (ROOT / rel).read_text("utf-8").splitlines()
    return sum(1 for line in lines
               if line.strip() and not line.lstrip().startswith("#"))


class DocumentedNumbersTest(unittest.TestCase):
    def test_every_pypi_page_count_matches_the_corpus_on_disk(self):
        actual = _external_corpus_size()
        self.assertGreater(actual, 0, "the external corpus is missing")
        found = 0
        for rel in LIVING_DOCS:
            for claim in re.findall(_COUNT + r" PyPI", _text(rel), re.I):
                found += 1
                self.assertEqual(_as_int(claim), actual,
                                 f"{rel} claims {claim} PyPI pages; there are {actual}")
        self.assertGreater(found, 0, "no claim was checked, so this test proves nothing")

    def test_every_golden_case_count_matches_the_golden_files(self):
        external = _golden_count("evals/goldens-external.jsonl")
        primary = _golden_count("evals/goldens.jsonl")
        sizes = {external, primary}
        found = 0
        for rel in LIVING_DOCS:
            text = _text(rel)
            for claim in re.findall(_COUNT + r" golden cases", text, re.I):
                found += 1
                self.assertEqual(_as_int(claim), external,
                                 f"{rel} claims {claim} external golden cases; "
                                 f"there are {external}")
            # "4 of 54 questions", "4 of 20 questions" - the second number is
            # the size of the set, and must be one of the two sets that exist.
            for _, total in re.findall(_COUNT + r" of " + _COUNT + r" questions", text, re.I):
                found += 1
                self.assertIn(_as_int(total), sizes,
                              f"{rel} refers to a golden set of {total} questions; "
                              f"the sets hold {sorted(sizes)}")
        self.assertGreater(found, 0, "no claim was checked, so this test proves nothing")

    def test_the_manifest_lists_the_documents_that_are_actually_there(self):
        import json

        manifest = json.loads((ROOT / "corpus/external/pypi-manifest.json")
                              .read_text("utf-8"))
        names = {d["name"] for d in manifest["documents"]}
        on_disk = {p.stem for p in (ROOT / "corpus/external/pypi").glob("*.md")}
        self.assertEqual(names, on_disk,
                         "the manifest and the corpus directory disagree, so "
                         "provenance does not cover what is indexed")


if __name__ == "__main__":
    unittest.main()
