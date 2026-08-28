#!/usr/bin/env python3
"""Append a learned rule to the instruction file, in a checked format.

The pattern this implements is documented by third parties as Nick Saraev's
self-annealing instruction file: the always-loaded prompt carries a growing
"learned rules" section, and every time the owner corrects the agent, a rule is
appended rather than the correction being spent on one turn and forgotten.
See docs/prompting.md for what that attribution rests on.

Why a tool rather than a note in a skill: a rule appended by hand drifts in
format, duplicates one already there, and — the failure that matters — arrives
without the *because*. A rule with no reason cannot be reviewed later, because
nothing in it says what it was protecting against. This refuses to write one.

The format, as documented:

    N. [category] Always|Never <do X>, because <Y>.

Usage
  python3 tools/learn_rule.py add --category tests --never "skip run_all.sh" \\
      --because "a guard nobody ran is a guard that does not exist"
  python3 tools/learn_rule.py list
  python3 tools/learn_rule.py add ... --file ~/.claude/CLAUDE.md --dry-run
Exit
  0 written (or listed) · 1 refused · 2 could not run
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_FILE = REPO / "CLAUDE.md"
SECTION = "## Learned rules"
PREAMBLE = (
    "Rules appended when a correction landed, newest last. Each one is here\n"
    "because something went wrong once; the `because` is what lets a later\n"
    "reader decide whether it still applies. Written by `tools/learn_rule.py`.\n"
)
RULE = re.compile(r"^(\d+)\.\s+\[(?P<category>[^\]]+)\]\s+(?P<mode>Always|Never)\s+(?P<body>.+)$")


def read_rules(text: str) -> list[str]:
    if SECTION not in text:
        return []
    tail = text.split(SECTION, 1)[1]
    # The section ends at the next heading of the same or higher level.
    end = re.search(r"^#{1,2} ", tail, re.M)
    body = tail[: end.start()] if end else tail
    return [line.strip() for line in body.splitlines() if RULE.match(line.strip())]


def normalise(rule: str) -> str:
    """Compare rules by their content, not their numbering or spacing."""
    stripped = re.sub(r"^\d+\.\s*", "", rule).strip().lower()
    return re.sub(r"\s+", " ", stripped).rstrip(".")


def render(number: int, category: str, mode: str, action: str, because: str) -> str:
    action = action.strip().rstrip(".")
    because = because.strip().rstrip(".")
    return f"{number}. [{category.strip()}] {mode} {action}, because {because}."


def add_rule(path: Path, category: str, mode: str, action: str, because: str,
             dry_run: bool) -> tuple[int, str]:
    if not path.exists():
        return 2, f"learn_rule: no such file: {path}"
    text = path.read_text(encoding="utf-8")
    existing = read_rules(text)
    candidate = render(len(existing) + 1, category, mode, action, because)

    for rule in existing:
        if normalise(rule) == normalise(candidate):
            return 1, f"learn_rule: already recorded, unchanged:\n  {rule}"

    if dry_run:
        return 0, f"learn_rule: would append to {path}:\n  {candidate}"

    if SECTION in text:
        lines = text.splitlines()
        # Append after the last existing rule, or after the section's preamble.
        insert_at = None
        in_section = False
        for i, line in enumerate(lines):
            if line.strip() == SECTION:
                in_section = True
                insert_at = i + 1
                continue
            if in_section:
                if re.match(r"^#{1,2} ", line):
                    break
                if RULE.match(line.strip()) or line.strip():
                    insert_at = i + 1
        lines.insert(insert_at, candidate)
        new_text = "\n".join(lines).rstrip() + "\n"
    else:
        new_text = text.rstrip() + f"\n\n---\n\n{SECTION}\n\n{PREAMBLE}\n{candidate}\n"

    path.write_text(new_text, encoding="utf-8")
    return 0, f"learn_rule: appended to {path} ({date.today().isoformat()}):\n  {candidate}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="learn_rule",
        description="Append a learned rule to an instruction file. 0 written, 1 refused, 2 could not run.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="append one rule")
    add.add_argument("--file", default=str(DEFAULT_FILE))
    add.add_argument("--category", required=True, help="one word: tests, git, style, tone...")
    group = add.add_mutually_exclusive_group(required=True)
    group.add_argument("--always", metavar="ACTION", help="what to do from now on")
    group.add_argument("--never", metavar="ACTION", help="what to stop doing")
    add.add_argument("--because", required=True,
                     help="what went wrong, so a later reader can judge whether it still applies")
    add.add_argument("--dry-run", action="store_true")

    listing = sub.add_parser("list", help="print the rules already recorded")
    listing.add_argument("--file", default=str(DEFAULT_FILE))

    args = parser.parse_args(argv[1:])
    path = Path(args.file).expanduser()

    if args.command == "list":
        if not path.exists():
            print(f"learn_rule: no such file: {path}", file=sys.stderr)
            return 2
        rules = read_rules(path.read_text(encoding="utf-8"))
        if not rules:
            print(f"learn_rule: {path} has no learned rules yet.")
            print("That is the honest state of a file nobody has corrected, not an error.")
            return 0
        print(f"{len(rules)} learned rule(s) in {path}:")
        for rule in rules:
            print(f"  {rule}")
        return 0

    if not args.because.strip():
        print("learn_rule: --because may not be empty. A rule with no reason cannot be",
              file=sys.stderr)
        print("reviewed later, because nothing in it says what it was protecting against.",
              file=sys.stderr)
        return 1

    mode = "Always" if args.always else "Never"
    action = args.always or args.never
    code, message = add_rule(path, args.category, mode, action, args.because, args.dry_run)
    print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
