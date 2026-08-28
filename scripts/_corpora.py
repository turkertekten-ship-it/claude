"""The two evaluation corpora, defined once.

Every sweep in this directory builds its own index, so each one carries a copy
of what "the primary corpus" means - and two of them had drifted. `**/*.md`
rooted at the repository is recursive, so it swallows `corpus/external/pypi`:
`base_weight_sweep.py` and `expansion_ab.py` were running the *primary* golden
set against 341 documents, the repository plus the entire external corpus,
while every other script used 84 (L67). Both scripts produced recorded
conclusions from that mixture.

A corpus definition is part of a measurement's result. Keeping one copy is the
only way two scripts can be compared, so import from here rather than
redeclaring - `tests/test_documented_numbers.py` checks that nothing redeclares.
"""

from __future__ import annotations

#: (root, patterns, goldens) for each corpus.
EXTERNAL = ("corpus/external/pypi", ("**/*.md",), "evals/goldens-external.jsonl")
PRIMARY = (
    ".",
    ("src/**/*.py", "tests/**/*.py", "docs/**/*.md", "internal/**/*.md", "*.md",
     "corpus/reference/**/*.md"),
    "evals/goldens.jsonl",
)
CORPORA = {"external": EXTERNAL, "primary": PRIMARY}
