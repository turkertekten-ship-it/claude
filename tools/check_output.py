#!/usr/bin/env python3
"""Check an answer against the constraints its own prompt stated.

The prompt standard makes you write an acceptance test. Nothing until now read
it back. That gap is not theoretical: in this repository's own A/B trial the
winning arm was given an 80-word limit and returned 86 words, and the limit was
in the prompt the whole time [src:FORGE-AB-TRIAL-2026-08-27].

**What this does not do.** It does not verify an answer. Most of what a prompt
constrains is prose no machine can check - "touch only `base.py`", "do not
change behaviour". Across this repository's own forged prompts only a handful
of constraints are countable at all. So the tool checks the countable subset,
and then lists every constraint sentence it could not interpret, because a
checker that reported "all clear" over the parts it silently skipped would be
worse than no checker.

Scope: if the prompt uses the slot headings, only the constraint, output and
acceptance sections are read - a number in the CONTEXT section describes the
input, not the answer. Without headings the whole prompt is scanned and the
report says so.

Usage
  python3 tools/check_output.py PROMPT OUTPUT [--json] [--quiet]
  cat answer.txt | python3 tools/check_output.py PROMPT -
Exit
  0 every checkable constraint held · 1 one or more failed · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")
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


CHECKED_SECTIONS = ("CONSTRAINT", "OUTPUT", "ACCEPTANCE")

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}
NUMBER = r"(\d+|" + "|".join(WORD_NUMBERS) + r")"


def as_number(token: str) -> int:
    return int(token) if token.isdigit() else WORD_NUMBERS[token]


UNITS = {
    "word": lambda t: len(t.split()),
    "words": lambda t: len(t.split()),
    "line": lambda t: len([l for l in t.splitlines() if l.strip()]),
    "lines": lambda t: len([l for l in t.splitlines() if l.strip()]),
    "sentence": lambda t: len([s for s in re.split(r"[.!?]+(?:\s|$)", t) if s.strip()]),
    "sentences": lambda t: len([s for s in re.split(r"[.!?]+(?:\s|$)", t) if s.strip()]),
    "paragraph": lambda t: len([p for p in re.split(r"\n\s*\n", t.strip()) if p.strip()]),
    "paragraphs": lambda t: len([p for p in re.split(r"\n\s*\n", t.strip()) if p.strip()]),
    "character": len,
    "characters": len,
}


@dataclass
class Check:
    rule: str
    demand: str
    ok: bool
    detail: str


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)
    runnable: list[tuple[str, str]] = field(default_factory=list)
    unchecked: list[str] = field(default_factory=list)
    scoped: bool = True

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]


def sentences_of(text: str) -> list[str]:
    parts = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*# ").strip()
        if not line:
            continue
        parts.extend(s.strip() for s in re.split(r"(?<=[.;])\s+", line) if s.strip())
    return parts


def constraint_text(prompt: str) -> tuple[str, bool]:
    """The sections whose statements are about the answer, if they are marked."""
    lines = prompt.splitlines()
    if not any(slot_of(l) for l in lines):
        return prompt, False
    kept, keeping = [], False
    for line in lines:
        slot = slot_of(line)
        if slot:
            name, rest = slot
            keeping = any(name.startswith(s) for s in CHECKED_SECTIONS)
            if keeping and rest:
                kept.append(rest)
            continue
        if keeping:
            kept.append(line)
    return "\n".join(kept), True


def strip_fences(text: str) -> str:
    out, inside = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        out.append(line)
    return "\n".join(out)


def fenced_blocks(text: str) -> int:
    return sum(1 for line in text.splitlines() if FENCE.match(line)) // 2


def body_of(output: str) -> str:
    """A single fenced block is the answer; the fence is packaging."""
    if fenced_blocks(output) == 1 and output.strip().startswith(("```", "~~~")):
        return strip_fences(output)
    return output


def check(prompt: str, output: str) -> Report:
    """Every matcher runs against every constraint sentence.

    Not first-match-wins: "No bullet points, no headings, no bold labels" is one
    sentence carrying three constraints, and an early `continue` silently
    checked only the first of them. Identical demands stated twice — once in
    CONSTRAINTS and again in the OUTPUT CONTRACT — collapse to one check.
    """
    scope, scoped = constraint_text(prompt)
    report = Report(scoped=scoped)
    body = body_of(output)
    seen: set[tuple[str, str]] = set()

    def add(rule: str, demand: str, ok: bool, detail: str) -> bool:
        if (rule, demand) in seen:
            return True
        seen.add((rule, demand))
        report.checks.append(Check(rule, demand, ok, detail))
        return True

    def counts(sentence: str, low: str) -> bool:
        fired = False
        m = re.search(r"\b(?:under|below|at most|no more than|fewer than|less than|"
                      r"maximum of|max(?:imum)?|up to|within)\s+" + NUMBER + r"\s+(\w+)", low)
        if m and m.group(2) in UNITS:
            limit, unit = as_number(m.group(1)), m.group(2)
            actual = UNITS[unit](body)
            fired = add("MAX_COUNT", f"at most {limit} {unit}", actual <= limit, f"{actual} {unit}")
        m = re.search(r"\bexactly\s+" + NUMBER + r"\s+(\w+)", low)
        if m and m.group(2) in UNITS:
            want, unit = as_number(m.group(1)), m.group(2)
            actual = UNITS[unit](body)
            fired = add("EXACT_COUNT", f"exactly {want} {unit}", actual == want, f"{actual} {unit}") or fired
        return fired

    def structure(sentence: str, low: str) -> bool:
        fired = False
        if re.search(r"\bone paragraph\b|\ba single paragraph\b", low):
            actual = UNITS["paragraphs"](body)
            fired = add("ONE_PARAGRAPH", "one paragraph", actual == 1, f"{actual} paragraphs")
        if re.search(r"\bno (?:bullet|bullets|bullet points|lists?|numbered lists?)\b", low):
            bad = [l for l in body.splitlines() if re.match(r"\s*(?:[-*+]\s|\d+[.)]\s)", l)]
            fired = add("NO_LISTS", "no list markup", not bad, f"{len(bad)} list line(s)") or fired
        if re.search(r"\bno (?:headings?|headers?)\b", low):
            bad = [l for l in body.splitlines() if re.match(r"\s*#{1,6}\s", l)]
            fired = add("NO_HEADINGS", "no headings", not bad, f"{len(bad)} heading(s)") or fired
        if re.search(r"\bno bold labels?\b|\bno bold\b", low):
            bad = [l for l in body.splitlines() if re.match(r"\s*\*\*", l)]
            fired = add("NO_BOLD_LABELS", "no bold labels", not bad,
                        f"{len(bad)} bold-led line(s)") or fired
        m = re.search(r"\b(?:in\s+)?one\s+(?:\w+\s+)?code block\b", low)
        if m:
            actual = fenced_blocks(output)
            fired = add("ONE_CODE_BLOCK", "one code block", actual == 1,
                        f"{actual} fenced block(s)") or fired
        if re.search(r"\bno preamble\b", low):
            first = next((l for l in body.splitlines() if l.strip()), "")
            bad = bool(re.match(r"\s*(here(?:'s| is| are)|sure|certainly|i(?:'ll| will| have)|"
                                r"below is|this is (?:a|the) (?:summary|answer))\b", first, re.I))
            fired = add("NO_PREAMBLE", "no preamble", not bad, f"opens {first[:44]!r}") or fired
        return fired

    def forbidden(sentence: str, low: str) -> bool:
        fired = False
        if re.search(r"\bno exclamation\b", low):
            fired = add("NO_EXCLAMATION", "no exclamation marks", "!" not in body,
                        f"{body.count('!')} found")
        if re.search(r"\bno emoji\b", low):
            found = [c for c in body if ord(c) > 0x2500 and c.isprintable() and not c.isalnum()]
            fired = add("NO_EMOJI", "no emoji", not found, f"{len(found)} found") or fired
        for m in re.finditer(r"\bno [\"'`]?(please|sorry|apolog\w*)[\"'`]?\b", low):
            word = m.group(1)[:6]
            hits = len(re.findall(word, body, re.I))
            fired = add("FORBIDDEN_WORD", f"no {m.group(1)!r}", hits == 0,
                        f"{hits} occurrence(s)") or fired
        return fired

    COMMAND = re.compile(r"`([^`]{4,120})`")
    RUNNABLE_VERB = re.compile(
        r"\b(pass(?:es|ed)?|fail(?:s|ed)?|green|exits?\s+0|succeeds?|returns?|parses?|"
        r"compiles?|runs?|is clean|reports?)\b", re.I)

    def runnable(sentence: str, low: str) -> bool:
        """A constraint naming a command is verifiable by running it.

        This tool does not run it - executing a command lifted out of a prompt
        is not something a linter should do - so it reports the command and
        says it was not run. That is a different answer from "cannot be
        checked", and the difference is the whole point.
        """
        if not RUNNABLE_VERB.search(low):
            return False
        commands = [c for c in COMMAND.findall(sentence) if re.search(r"[ /.]", c)]
        if not commands:
            return False
        for command in commands:
            entry = (command, sentence)
            if entry not in report.runnable:
                report.runnable.append(entry)
        return True

    def formats(sentence: str, low: str) -> bool:
        if re.search(r"\b(?:as|valid|in)\s+json\b", low):
            probe = strip_fences(output).strip() if fenced_blocks(output) else output.strip()
            try:
                json.loads(probe)
                return add("VALID_JSON", "valid JSON", True, "parses")
            except json.JSONDecodeError as exc:
                return add("VALID_JSON", "valid JSON", False, f"does not parse: {exc.msg}")
        return False

    for sentence in sentences_of(scope):
        low = sentence.lower()
        fired = False
        for matcher in (counts, structure, forbidden, formats, runnable):
            fired = matcher(sentence, low) or fired
        if not fired:
            report.unchecked.append(sentence)

    return report


def render(report: Report, quiet: bool = False) -> str:
    lines = []
    passed = [c for c in report.checks if c.ok]
    lines.append(f"{len(passed)}/{len(report.checks)} countable constraint(s) held, "
                 f"{len(report.runnable)} runnable but not run here, "
                 f"{len(report.unchecked)} for a reader to judge")
    if not report.scoped:
        lines.append("note: the prompt has no slot headings, so the whole of it was scanned "
                     "for constraints — a number describing the input may be read as a limit")
    lines.append("")
    for c in report.checks:
        mark = "ok  " if c.ok else "FAIL"
        lines.append(f"  {mark} {c.rule:<16} {c.demand:<28} {c.detail}")
    if report.runnable:
        lines.append("")
        lines.append("  runnable — this tool does not execute commands; run these yourself:")
        for command, sentence in report.runnable:
            lines.append(f"    $ {command}")
            lines.append(f"      to satisfy: {sentence[:88]}")
    if report.unchecked and not quiet:
        lines.append("")
        lines.append("  for a reader to judge — no command named, nothing countable:")
        for sentence in report.unchecked:
            lines.append(f"    · {sentence[:96]}")
    return "\n".join(lines)


# Catch -> Diagnose -> Rewrite. The pattern this repository documents as
# Saraev's self-annealing loop ends by updating the instruction file "to warn
# future instances". Detection and learning were built as separate tools and
# never connected, so a correction the checker found was still spent unless
# somebody retyped it. These are the retyping.
RULE_TEMPLATES = {
    "MAX_COUNT": ("output", "exceed a stated limit on length"),
    "EXACT_COUNT": ("output", "miss a stated exact count"),
    "ONE_PARAGRAPH": ("format", "break a one-paragraph instruction into several"),
    "NO_LISTS": ("format", "use list markup when the prompt forbids it"),
    "NO_HEADINGS": ("format", "add headings when the prompt forbids them"),
    "NO_BOLD_LABELS": ("format", "open lines with bold labels when the prompt forbids them"),
    "ONE_CODE_BLOCK": ("format", "return more than one code block when one was asked for"),
    "VALID_JSON": ("format", "return JSON that does not parse"),
    "NO_EXCLAMATION": ("tone", "use exclamation marks when the prompt forbids them"),
    "NO_EMOJI": ("tone", "use emoji when the prompt forbids them"),
    "FORBIDDEN_WORD": ("tone", "use a word the prompt forbids"),
    "NO_PREAMBLE": ("format", "open with a preamble when the prompt forbids one"),
}


def suggested_rules(report: Report) -> list[str]:
    """One ready-to-run `learn_rule.py add` per failure.

    The `--because` carries the measurement and nothing else. A reason that
    speculates about why the answer went wrong would be exactly the invention
    this repository exists to prevent, and it would be appended to the file
    every future prompt loads.
    """
    out = []
    for check in report.failed:
        category, action = RULE_TEMPLATES.get(
            check.rule, ("output", f"violate a stated {check.rule.lower().replace('_', ' ')} constraint")
        )
        because = f"an answer to a prompt demanding {check.demand} came back with {check.detail}"
        out.append(
            "python3 tools/learn_rule.py add"
            f" --category {shlex.quote(category)}"
            f" --never {shlex.quote(action)}"
            f" --because {shlex.quote(because)}"
        )
    return out


def read(name: str) -> str:
    if name == "-":
        return sys.stdin.read()
    path = Path(name)
    if not path.exists():
        raise FileNotFoundError(name)
    return path.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="check_output",
        description="Check an answer against the constraints its prompt stated. "
                    "0 all held, 1 a failure, 2 could not run.",
    )
    parser.add_argument("prompt")
    parser.add_argument("output", help="the answer, or - for stdin")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="omit the unchecked list")
    parser.add_argument("--suggest-rule", action="store_true",
                        help="for each failure, print the learn_rule command that would "
                             "record it, so the correction is not spent on one answer")
    args = parser.parse_args(argv[1:])

    try:
        report = check(read(args.prompt), read(args.output))
    except FileNotFoundError as exc:
        print(f"check_output: no such file: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "scoped": report.scoped,
            **({"suggested_rules": suggested_rules(report)} if args.suggest_rule else {}),
            "checks": [vars(c) for c in report.checks],
            "runnable": [{"command": c, "sentence": s} for c, s in report.runnable],
            "unchecked": report.unchecked,
        }, indent=2))
    else:
        print(render(report, args.quiet))
        if args.suggest_rule:
            rules = suggested_rules(report)
            print()
            if rules:
                print("  to keep this from being spent on one answer, record it:")
                for line in rules:
                    print(f"    {line}")
            else:
                print("  nothing failed, so there is nothing to record.")
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
