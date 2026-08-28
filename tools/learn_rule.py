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
    stripped = TAG.sub("", re.sub(r"^\d+\.\s*", "", rule)).strip().lower()
    return re.sub(r"\s+", " ", stripped).rstrip(".")


ENFORCED_BY = re.compile(r"\s*\[enforced by: ([^\]]+)\]")
# A rule that cannot be enforced is not therefore homeless. Judgement and
# procedure belong in the document read at the moment they apply - the Observe
# phase of a loop, not twelfth in a list at session start - and where a rule
# was routed is recorded so it can be checked rather than assumed.
ROUTED_TO = re.compile(r"\s*\[routed to: ([^\]]+)\]")
TAG = re.compile(r"\s*\[(enforced by|routed to): [^\]]+\]")


def render(number: int, category: str, mode: str, action: str, because: str,
           enforced_by: str | None = None) -> str:
    action = action.strip().rstrip(".")
    because = because.strip().rstrip(".")
    line = f"{number}. [{category.strip()}] {mode} {action}, because {because}."
    if enforced_by:
        line += f" [enforced by: {enforced_by.strip()}]"
    return line


SUPERSEDED = re.compile(r"\s+—\s+superseded by rule \d+\.?$")


def can_supersede(path: Path, number: int) -> tuple[int, str]:
    """Whether rule `number` is there and not already replaced.

    Checked before anything is written: the first version appended the new rule
    and then discovered the target did not exist, leaving an orphan behind.
    """
    for rule in read_rules(path.read_text(encoding="utf-8")):
        m = RULE.match(rule)
        if m and int(m.group(1)) == number:
            if SUPERSEDED.search(rule):
                return 1, f"learn_rule: rule {number} is already superseded"
            return 0, ""
    return 1, f"learn_rule: no rule numbered {number} in {path}"


def prune(path: Path, dry_run: bool) -> tuple[int, str]:
    """Remove superseded rules from the always-loaded file.

    They were kept because a rule records something that went wrong, and that is
    worth knowing. But this file is loaded into every prompt, and the same
    sources that describe self-annealing also warn against stuffing the context.
    A retired rule's reason survives in the loop log and in git history, which
    is where history belongs; the live file should carry what is live.

    Numbering is left alone. A gap is a legible signal that something was
    retired, and renumbering would break the references rules make to each
    other.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    removed = [l.strip() for l in lines if RULE.match(l.strip()) and SUPERSEDED.search(l)]
    if not removed:
        return 0, "learn_rule: nothing superseded to prune."
    if dry_run:
        return 0, "learn_rule: would remove\n  " + "\n  ".join(r[:90] for r in removed)
    kept = [l for l in lines if not (RULE.match(l.strip()) and SUPERSEDED.search(l))]
    path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")
    return 0, ("learn_rule: removed %d superseded rule(s); their reasons survive in the\n"
               "loop log and in git history. Numbering is unchanged, so the gaps show\n"
               "where something was retired:\n  " % len(removed)
               + "\n  ".join(r[:90] for r in removed))


def annotate(path: Path, number: int, enforced_by: str | None = None,
             routed_to: str | None = None) -> tuple[int, str]:
    """Record which guard catches a breach of an existing rule.

    Rules written before enforcement existed for them would otherwise have to
    be hand-edited, in the one file this tool owns.
    """
    label, value = ("enforced by", enforced_by) if enforced_by else ("routed to", routed_to)
    named = value.split("(")[0].split("+")[0].strip()
    if not (REPO / named).exists():
        return 1, (f"learn_rule: names {named!r}, which does not exist.\n"
                   "A claim that a rule is enforced or routed somewhere is itself a claim.")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = RULE.match(line.strip())
        if m and int(m.group(1)) == number:
            if (ENFORCED_BY if enforced_by else ROUTED_TO).search(line):
                return 1, f"learn_rule: rule {number} already names a {label.split()[0]}"
            lines[i] = line.rstrip() + f" [{label}: {value.strip()}]"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 0, f"learn_rule: rule {number} {label} {value.strip()}"
    return 1, f"learn_rule: no rule numbered {number} in {path}"


def mark_superseded(path: Path, number: int, by: int) -> tuple[int, str]:
    """Mark a rule as replaced without deleting it.

    A rule that turns out to be wrong still records that something went wrong
    once, and the reason it was written is often the useful part. Removing it
    loses that; leaving it active is worse, because a later reader follows it.
    So it stays, marked, and the new rule says what replaced it. This was the
    missing operation: rules were append-only, so a wrong one could only be
    corrected by hand-editing the file the tool owns.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = RULE.match(line.strip())
        if m and int(m.group(1)) == number:
            if SUPERSEDED.search(line):
                return 1, f"learn_rule: rule {number} is already superseded"
            lines[i] = line.rstrip().rstrip(".") + f". — superseded by rule {by}"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return 0, f"learn_rule: rule {number} marked superseded by rule {by}"
    return 1, f"learn_rule: no rule numbered {number} in {path}"


def add_rule(path: Path, category: str, mode: str, action: str, because: str,
             dry_run: bool, enforced_by: str | None = None) -> tuple[int, str]:
    if not path.exists():
        return 2, f"learn_rule: no such file: {path}"
    if enforced_by:
        named = enforced_by.split("(")[0].split("+")[0].strip()
        if not (REPO / named).exists():
            return 1, (f"learn_rule: --enforced-by names {named!r}, which does not exist.\n"
                       "A claim that something is enforced is itself a claim.")
    text = path.read_text(encoding="utf-8")
    existing = read_rules(text)
    candidate = render(len(existing) + 1, category, mode, action, because, enforced_by)

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
        lines.append("  `learn_rule.py prune` removes superseded rules, whose reasons survive")
        lines.append("  in the loop log and in git history. Beyond that, nothing here deletes a")
        lines.append("  live rule for you: merge the ones that say the same thing, and retire any")
        lines.append("  whose `because` no longer describes a risk this repository still runs.")

    live = [r for r in rules if not SUPERSEDED.search(r)]
    enforced = [r for r in live if ENFORCED_BY.search(r)]
    routed = [r for r in live if ROUTED_TO.search(r) and not ENFORCED_BY.search(r)]
    loose = len(live) - len(enforced) - len(routed)
    if live:
        lines.append(f"  {len(live)} live: {len(enforced)} enforced by a guard, "
                     f"{len(routed)} routed to where they are read, "
                     f"{loose} in this list only")
        if loose:
            lines.append("  a rule in this list only is read at session start and nowhere else,")
            lines.append("  which is the weakest place a rule can live")
    retired = [r for r in rules if SUPERSEDED.search(r)]
    if retired:
        lines.append(f"  {len(retired)} superseded, kept for their reasons and still costing context")
    parsed = [(i, r, *parts_of(r)) for i, r in enumerate(rules) if not SUPERSEDED.search(r)]
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
    add.add_argument("--enforced-by", default=None,
                     help="the guard that catches a breach, if there is one. Named files must "
                          "exist. A rule with none is advisory, and the review says how many are")
    add.add_argument("--dry-run", action="store_true")

    sup = sub.add_parser("supersede", help="replace a rule that turned out to be wrong")
    sup.add_argument("number", type=int, help="the rule number being replaced")
    sup.add_argument("--file", default=str(DEFAULT_FILE))
    sup.add_argument("--category", required=True)
    supgroup = sup.add_mutually_exclusive_group(required=True)
    supgroup.add_argument("--always", metavar="ACTION")
    supgroup.add_argument("--never", metavar="ACTION")
    sup.add_argument("--because", required=True)
    sup.add_argument("--dry-run", action="store_true")

    ann = sub.add_parser("annotate", help="name the guard that enforces an existing rule")
    ann.add_argument("number", type=int)
    ann.add_argument("--file", default=str(DEFAULT_FILE))
    anngroup = ann.add_mutually_exclusive_group(required=True)
    anngroup.add_argument("--enforced-by", help="the guard that catches a breach")
    anngroup.add_argument("--routed-to", help="the document read when the rule applies")

    pr = sub.add_parser("prune", help="remove superseded rules from the loaded file")
    pr.add_argument("--file", default=str(DEFAULT_FILE))
    pr.add_argument("--dry-run", action="store_true")

    listing = sub.add_parser("list", help="print the rules already recorded")
    listing.add_argument("--file", default=str(DEFAULT_FILE))

    rev = sub.add_parser("review", help="report size, contradictions and near-duplicates")
    rev.add_argument("--file", default=str(DEFAULT_FILE))
    rev.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    rev.add_argument("--max-share", type=int, default=DEFAULT_MAX_SHARE)

    args = parser.parse_args(argv[1:])
    path = Path(args.file).expanduser()

    if args.command == "prune":
        if not path.exists():
            print(f"learn_rule: no such file: {path}", file=sys.stderr)
            return 2
        code, message = prune(path, args.dry_run)
        print(message, file=sys.stderr if code else sys.stdout)
        return code

    if args.command == "annotate":
        if not path.exists():
            print(f"learn_rule: no such file: {path}", file=sys.stderr)
            return 2
        code, message = annotate(path, args.number, args.enforced_by, args.routed_to)
        print(message, file=sys.stderr if code else sys.stdout)
        return code

    if args.command == "supersede":
        if not path.exists():
            print(f"learn_rule: no such file: {path}", file=sys.stderr)
            return 2
        code, message = can_supersede(path, args.number)
        if code:
            print(message, file=sys.stderr)
            return code
        existing = read_rules(path.read_text(encoding="utf-8"))
        new_number = len(existing) + 1
        mode = "Always" if args.always else "Never"
        code, message = add_rule(path, args.category, mode, args.always or args.never,
                                 args.because, args.dry_run)
        if code:
            print(message, file=sys.stderr)
            return code
        print(message)
        if args.dry_run:
            print(f"learn_rule: would mark rule {args.number} superseded by rule {new_number}")
            return 0
        code, message = mark_superseded(path, args.number, new_number)
        print(message, file=sys.stderr if code else sys.stdout)
        return code

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
    code, message = add_rule(path, args.category, mode, action, args.because, args.dry_run,
                             getattr(args, "enforced_by", None))
    print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
