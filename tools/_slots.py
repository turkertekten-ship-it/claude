#!/usr/bin/env python3
"""How a prompt labels its slots, in one place.

A slot heading appears three ways in real prompts - `## CONSTRAINTS`,
`**Constraints.**`, and `Constraints:` - and both the linter and the output
checker have to recognise all three. Two copies of this parser would drift.
"""

from __future__ import annotations

import re


# A slot gets labelled three ways in real prompts: a markdown heading
# (`## CONSTRAINTS`), a bold label (`**Constraints.**`), or plain prose
# (`Constraints: no third-party actions`). One regex covering all three kept
# breaking one of them, so this is a function with the cases named.
SLOT_WORDS = re.compile(
    r"^(CONSTRAINTS?|OUTPUT(?:\s+CONTRACT)?|ACCEPTANCE(?:\s+TESTS?)?|SUCCESS\s+CRITERIA"
    r"|ROLE|CONTEXT|BACKGROUND|TASK|IF\s+YOU\s+CANNOT|ESCAPE)",
    re.I,
)
MARKER = re.compile(r"^(#{1,6}\s+|\*\*|-\s+\*\*)")


def slot_of(line: str) -> tuple[str, str] | None:
    """(slot name, rest of the line) if this line labels a slot, else None."""
    stripped = line.strip()
    marked = bool(MARKER.match(stripped))
    core = MARKER.sub("", stripped, count=1)
    m = SLOT_WORDS.match(core)
    if not m:
        return None
    rest = core[m.end():]
    # A prose label has to be punctuated, or every sentence starting with the
    # word "Context" would open a section.
    if not marked and not rest.lstrip("*").startswith((":", ".")):
        return None
    return m.group(1).upper(), rest.lstrip("*:. ").strip()


