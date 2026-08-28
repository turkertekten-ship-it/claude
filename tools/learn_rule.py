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


# The section grows by one rule per correction and nothing ever removes one.
# That is deliberate - a rule exists because something went wrong, and silent
# pruning loses the reason - but unbounded growth turns the always-loaded file
# into mostly accumulated corrections. Measured on this repository: at 50 rules
# the section is 45% of CLAUDE.md, at 200 it is 76%. The same source that
# documents self-annealing also warns against stuffing the context; these
# defaults are where the two meet.
DEFAULT_MAX_WORDS = 500
DEFAULT_MAX_SHARE = 25          # per cent of the file

# Both thresholds were set from measurement rather than taste: the two real
# collisions this repository has produced - one contradiction, one restatement -
# both sit at exactly 0.50 word overlap, and the four genuine rules produce no
# finding at that level. A threshold chosen above the real cases would be a
# check that has never caught anything.
CONTRADICTION = 0.5
NEAR_DUPLICATE = 0.5


def parts_of(rule: str) -> tuple[str, str, set[str]]:
    m = RULE.match(rule)
    if not m:
        return "", "", set()
    body = m.group("body").split(", because")[0]
    words = {w for w in re.findall(r"[a-z]+", body.lower()) if len(w) > 3}
    return m.group("category").lower(), m.group("mode").lower(), words


def overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def review(path: Path, max_words: int, max_share: int) -> tuple[int, list[str]]:
    """Report on the section without changing it. 0 clean, 1 findings."""
    text = path.read_text(encoding="utf-8")
    rules = read_rules(text)
    lines: list[str] = []
    findings = 0

    total_words = len(text.split())
    section_words = sum(len(r.split()) for r in rules)
    share = round(100 * section_words / total_words) if total_words else 0
    lines.append(f"{len(rules)} rule(s), {section_words} words, {share}% of {path.name}")

    if section_words > max_words or share > max_share:
        findings += 1
        lines.append(f"  OVER BUDGET: {section_words} words / {share}% "
                     f"exceeds {max_words} words / {max_share}%")
        lines.append("  Nothing here will delete a rule for you. Merge the ones that say the")
        lines.append("  same thing, and retire any whose `because` no longer describes a risk")
        lines.append("  this repository still runs — by editing the file, deliberately.")

    parsed = [(i, r, *parts_of(r)) for i, r in enumerate(rules)]
    for i, (_, rule_a, cat_a, mode_a, words_a) in enumerate(parsed):
        for _, rule_b, cat_b, mode_b, words_b in parsed[i + 1:]:
            if not words_a or not words_b:
                continue
            similarity = overlap(words_a, words_b)
            if cat_a == cat_b and mode_a != mode_b and similarity >= CONTRADICTION:
                findings += 1
                lines.append(f"  CONTRADICTION ({round(100*similarity)}% overlap, same category):")
                lines.append(f"    {rule_a}")
                lines.append(f"    {rule_b}")
            elif mode_a == mode_b and similarity >= NEAR_DUPLICATE:
                findings += 1
                lines.append(f"  NEAR-DUPLICATE ({round(100*similarity)}% overlap):")
                lines.append(f"    {rule_a}")
                lines.append(f"    {rule_b}")

    if not findings:
        lines.append("  within budget, no contradictions or near-duplicates found")
    return (1 if findings else 0), lines


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

    rev = sub.add_parser("review", help="report size, contradictions and near-duplicates")
    rev.add_argument("--file", default=str(DEFAULT_FILE))
    rev.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    rev.add_argument("--max-share", type=int, default=DEFAULT_MAX_SHARE)

    args = parser.parse_args(argv[1:])
    path = Path(args.file).expanduser()

    if args.command == "review":
        if not path.exists():
            print(f"learn_rule: no such file: {path}", file=sys.stderr)
            return 2
        code, lines = review(path, args.max_words, args.max_share)
        print("\n".join(lines))
        return code

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
