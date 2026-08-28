#!/usr/bin/env python3
"""Turn "write a better prompt" into a check that either passes or fails.

A prompt is a specification. Most bad output traces back to a specification
that never said what it wanted, never said how it would be judged, and never
said what to do when the request turned out to rest on something that is not
there. Those three absences are mechanical, so this tool looks for them
mechanically rather than trusting a session to feel its way to a good prompt.

Two operations, deliberately separate:

  lint / score   audit a prompt. Reports the specific missing slot or hazard,
                 with a line number and the cheapest fix. Never rewrites.
  compile        restructure a raw prompt into the canonical slots. It moves
                 the author's own lines into sections and marks every gap as
                 `<<MISSING: ...>>`. It never invents content to fill a gap,
                 because a prompt that quietly gains requirements nobody wrote
                 is the same failure as a document that quietly gains facts.

The seven slots
  ROLE          who is answering, when that changes the answer
  CONTEXT       what is already true, so the model does not guess it
  TASK          the imperative, and the artifact it produces
  CONSTRAINTS   what is forbidden, and the bounds on effort
  OUTPUT        the shape of the reply, precisely enough to parse
  ACCEPTANCE    how the result will be judged, stated before it is produced
  ESCAPE        what to do when the request cannot be satisfied honestly

The last one is this repository's house requirement rather than a general
convention: a prompt with no escape hatch tells a model that returning
something is mandatory, and something is what it will return.

Usage
  python3 tools/prompt_forge.py lint    [--profile P] [--strict] [--json] FILE|- ...
  python3 tools/prompt_forge.py score   [--profile P] [--json] FILE|- ...
  python3 tools/prompt_forge.py compile [--profile P] [--with-report] FILE|-
  python3 tools/prompt_forge.py rules   [--profile P] [--json]

Profiles
  task (default) · build · research · system · chat
  They differ only in how severely a missing slot is graded: a system prompt
  needs a ROLE and does not need a TASK; a build prompt must say how it will
  be verified. Run `rules --profile P` to see the grading in force.

Exit
  0 clean · 1 findings · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phrases import FALSE_MEMORY  # noqa: E402

SEVERITIES = ("error", "warn", "info", "off")
WEIGHTS = {"error": 12, "warn": 6, "info": 2, "off": 0}

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")


# --------------------------------------------------------------------------
# Slots
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Slot:
    key: str
    heading: str
    cue: re.Pattern
    hint: str
    why: str


def _c(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.I)


SLOTS: tuple[Slot, ...] = (
    Slot(
        "ROLE", "ROLE",
        _c(r"\byou are\b|\bact as\b|\byou're an?\b|\byour (role|job|remit|output|task) is\b"
           r"|\bas an? (expert|senior|experienced|professional)\b|\bpersona\b|\bspeaking as\b"
           r"|(?:^|\n|[.!?]\s+)\s*you (?!must|should|can|will|may|might|need|have|do|don't|are|were|would)\w+\b"),
        "who is answering, and the one qualification that changes the answer",
        "Without a role the model picks one, and the one it picks is the average of the internet.",
    ),
    Slot(
        "CONTEXT", "CONTEXT",
        _c(r"\bcontext\b|\bbackground\b|\bcurrently\b|\bexisting\b|\bwe (have|use|are|run)\b|\bthe (repo|repository|codebase|project|file|system|stack|team)\b|\bhere (is|are)\b|\battached\b|\bgiven\b|\bversion\b"),
        "what is already true that the model must not guess at",
        "Every fact you leave out is a fact the model supplies, and it supplies it plausibly.",
    ),
    Slot(
        "TASK", "TASK",
        _c(r"(?:^|[.;:!?][\s*_)\]]*|,\s*|\band\s+|\bthen\s+|\balso\s+|\bplease\s+|\bto\s+|\bmust\s+|\bshould\s+|\bneed (?:you )?to\s+|\bwant (?:you )?to\s+|\bcan you\s+)[\s*_#>]*(?:\d+[.)]\s*|[-]\s*)?[\s*_#>]*(write|create|build|add|fix|refactor|implement|generate|draft|list|find|search|analy[sz]e|review|audit|summari[sz]e|explain|compare|design|plan|test|debug|convert|translate|extract|rewrite|update|remove|delete|install|configure|research|investigate|check|verify|compile|document|answer|classify|rank|score|evaluate|migrate|optimi[sz]e|port|deploy|produce|give|show|make|turn|map|trace|reproduce|extend|correct|name|define|measure|record|prove|resolve|close|refine|tighten|harden|validate|benchmark|instrument|split|merge|rename|parse|filter|sort)\b", ),
        "one imperative verb and the artifact it produces",
        "A topic is not a task. 'Docker' is a subject; 'write the Dockerfile' is an instruction.",
    ),
    Slot(
        "CONSTRAINTS", "CONSTRAINTS",
        _c(r"\bmust not\b|\bdo not\b|\bdon't\b|\bnever\b|\bonly\b|\bavoid\b|\blimit(ed)? to\b|\bno more than\b|\bat most\b|\bwithin \d|\bbudget\b|\bmax(imum)?\b|\bconstraints?\b|\brequired?\b|\bwithout\b|\bexclude\b|\bno (new |third[- ]party )?\w+ (allowed|permitted)\b"),
        "what is forbidden, and the bound on time, length, or scope",
        "An unbounded prompt is answered at whatever length the model happens to stop at.",
    ),
    Slot(
        "OUTPUT", "OUTPUT CONTRACT",
        _c(r"\bformat\b|\bjson\b|\byaml\b|\bcsv\b|\bmarkdown\b|\btable\b|\bbullet\b|\bnumbered\b|\bsections?\b|\bschema\b|\btemplate\b|\brespond with\b|\breturn (a|an|the|only|just)\b|\boutput (a|an|the|only|just)\b|\bplain text\b|\bone line\b|\bheadings?\b|\b\d+ (words|sentences|bullets|paragraphs|lines|items)\b|\bdiff\b|\bpatch\b"
           r"|\b(as|in) an? [\w-]{0,12} ?(list|table|block|paragraph|sentence|line|file)\b"
           r"|\bone line per\b|\ba list of\b|\bno (commentary|preamble|prose)\b"),
        "the exact shape of the reply — format, length, and sections",
        "If the shape is unstated you get prose, and prose has to be re-read by a human before it is usable.",
    ),
    Slot(
        "ACCEPTANCE", "ACCEPTANCE TEST",
        _c(r"\bdone when\b|\bsuccess (is|means|criteria)\b|\bacceptance\b|\bcriteri(a|on)\b|\bmust pass\b|\bpasses?\b|\bverif(y|ied|ication)\b|\bcheck that\b|\bprove\b|\bfalsif\w*\b|\bdefinition of done\b|\bcorrect (if|when)\b|\bit works when\b|\bso that i can\b|\bjudged? (by|on)\b"
           r"|\b(right|correct|valid|accepted|complete|done) only (if|when)\b|\bonly if\b"
           r"|\bexits? (0|zero|non-?zero)\b|\bgreen\b"),
        "the check that decides whether the answer is right, written before the answer exists",
        "A prompt with no acceptance test cannot be failed, so it cannot be improved either.",
    ),
    Slot(
        "ESCAPE", "IF YOU CANNOT",
        _c(r"\bif you (can'?t|cannot|are unable)\b|\bif (it|they|that|there) (is|are|does|do)(n'?t| not)\b"
           r"|\bif (no|none|nothing|neither|nobody)\b|\b(say|state|report) (so|exactly that|that plainly)\b"
           r"|\btell me\b|\bflag (it|them|that)\b|\bdo(n'?t| not) (guess|invent|fabricate|make up|assume)\b"
           r"|\bunknown\b|\bask (me|first|before)\b|\bstop and\b|\band stop\b|\bthen stop\b"
           r"|\brather than guess\b|\bno source\b|\bleave (it )?blank\b|\breturn nothing\b|\bexit clean\b"
           r"|\babsence is a finding\b|\breport(ing)? (presence and )?absence\b"
           r"|\b(could|can) ?not reach\b|\bwhat you (could|can) ?not\b"),
        "what to do when the request rests on something that is not there — say so, ask, or stop",
        "Absent this line the model treats producing something as mandatory, and it will.",
    ),
)

SLOT_BY_KEY = {s.key: s for s in SLOTS}

# Which slot a line is filed under when it matches more than one cue. ESCAPE
# and ACCEPTANCE come first because they are the two most often lost inside a
# sentence that also mentions a format.
CLASSIFY_ORDER = ("ESCAPE", "ACCEPTANCE", "OUTPUT", "ROLE", "CONSTRAINTS", "CONTEXT", "TASK")

PROFILES: dict[str, dict[str, str]] = {
    # A missing slot is graded by what the prompt is for. Nothing here is a
    # style preference: each severity is the cost of that absence in that
    # setting.
    "task": {
        "ROLE": "info", "CONTEXT": "warn", "TASK": "error", "CONSTRAINTS": "warn",
        "OUTPUT": "error", "ACCEPTANCE": "warn", "ESCAPE": "error",
    },
    "build": {
        "ROLE": "info", "CONTEXT": "warn", "TASK": "error", "CONSTRAINTS": "warn",
        "OUTPUT": "warn", "ACCEPTANCE": "error", "ESCAPE": "error",
    },
    "research": {
        "ROLE": "info", "CONTEXT": "warn", "TASK": "error", "CONSTRAINTS": "error",
        "OUTPUT": "warn", "ACCEPTANCE": "warn", "ESCAPE": "error",
    },
    "system": {
        "ROLE": "error", "CONTEXT": "info", "TASK": "info", "CONSTRAINTS": "error",
        "OUTPUT": "warn", "ACCEPTANCE": "info", "ESCAPE": "error",
    },
    "chat": {
        "ROLE": "off", "CONTEXT": "info", "TASK": "error", "CONSTRAINTS": "info",
        "OUTPUT": "warn", "ACCEPTANCE": "info", "ESCAPE": "warn",
    },
    # A standing instruction file for an agent to execute, rather than a
    # message to a chat. The field list is the one third-party repositories
    # document for the "directive" layer of the DOE framework they attribute to
    # Nick Saraev - goal, inputs, process steps, tools, edge cases, success
    # criteria, guardrails - which is why every one of them is an error here.
    # See docs/prompting.md for what that attribution does and does not rest on.
    # The four parts of the "prompt contract" that third-party documentation
    # attributes to Saraev: goal, constraints, output format, failure
    # conditions. Nothing else is graded as an error, because nothing else is
    # in that list. See docs/prompting.md for what the attribution rests on.
    "contract": {
        "ROLE": "off", "CONTEXT": "info", "TASK": "error", "CONSTRAINTS": "error",
        "OUTPUT": "error", "ACCEPTANCE": "warn", "ESCAPE": "error",
    },
    "directive": {
        "ROLE": "off", "CONTEXT": "error", "TASK": "error", "CONSTRAINTS": "error",
        "OUTPUT": "warn", "ACCEPTANCE": "error", "ESCAPE": "error",
    },
}
DEFAULT_PROFILE = "task"


# --------------------------------------------------------------------------
# Hazards
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Hazard:
    id: str
    title: str
    severity: str
    dimension: str
    why: str
    fix: str
    pattern: re.Pattern | None = None
    detector: object | None = None      # (lines, prose, raw) -> [(lineno, excerpt[, severity])]
    profiles: tuple[str, ...] = ("*",)


def _detect_false_premise(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """`the failing test` names something the prompt never established exists.

    The definite article does the damage: it asserts a unique referent. If the
    line carries no path, filename, number, or quoted name to anchor it, the
    model has to decide which failing test was meant, and deciding is inventing.
    """
    noun = re.compile(
        r"\bthe (failing|broken|flaky|current|existing|last|previous|other|usual|main) "
        r"(test|tests|build|job|check|script|bug|error|issue|problem|file|function|config|endpoint|page|one)\b"
        r"|\b(fix|debug|resolve|solve|reproduce|investigate|patch|address|track down) "
        r"the (bug|error|issue|crash|regression|failure)\b",
        re.I,
    )
    # An anchor is a path, an extension, a number, a quoted name, or anything in
    # backticks. Deliberately not a bare apostrophe: "while you're at it" is a
    # contraction, not an identifier, and reading it as one silently retired
    # this rule on the most common phrasing there is.
    anchor = re.compile(
        r"[/\\]|\.\w{1,5}\b|#\d+|\bline \d+|`[^`]+`|\"[^\"]+\"|'[\w./:-]{2,}'"
        r"|\bnamed\b|\bcalled\b|::"
    )
    out = []
    for i, raw in enumerate(lines, start=1):
        # The noun phrase is read with inline code stripped, so a quoted example
        # is not an assertion - but the anchor is looked for in the whole line,
        # because `tests/test_x.py` in backticks is exactly the identifier that
        # makes the reference concrete.
        m = noun.search(INLINE_CODE.sub("", raw))
        if m and not anchor.search(raw):
            out.append((i, m.group(0)))
    return out


def _detect_contradiction(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """Two instructions that cannot both be satisfied, so one is silently dropped."""
    pairs = [
        (re.compile(r"\b(brief|concise|short|terse|succinct|one paragraph|tl;?dr)\b", re.I),
         re.compile(r"\b(comprehensive|exhaustive|thorough|in[- ]depth|detailed|complete list|everything)\b", re.I),
         "brevity and exhaustiveness"),
        (re.compile(r"\bdo(n'?t| not) ask\b|\bwithout asking\b|\bno questions\b", re.I),
         re.compile(r"\bask (me|first|if|before)\b|\bcheck with me\b|\bclarify\b", re.I),
         "'do not ask' and 'ask me'"),
        (re.compile(r"\b(be creative|freely|your own judgement|improvise)\b", re.I),
         re.compile(r"\b(exactly|verbatim|strictly|do not deviate|follow the template)\b", re.I),
         "creative latitude and strict adherence"),
    ]
    out = []
    lowered = INLINE_CODE.sub("", text)
    for a, b, label in pairs:
        ma, mb = a.search(lowered), b.search(lowered)
        if not (ma and mb):
            continue
        line_a = lowered[: ma.start()].count("\n") + 1
        line_b = lowered[: mb.start()].count("\n") + 1
        near = abs(line_a - line_b) <= 4
        out.append((
            min(line_a, line_b),
            f"{label}: {ma.group(0)!r} vs {mb.group(0)!r}"
            + ("" if near else f" (lines {line_a} and {line_b}, possibly different scopes)"),
            "error" if near else "warn",
        ))
    return out


def _detect_unbounded(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """`all`, `every`, `everything` where nothing says how far that reaches.

    The word alone is not the problem - "for every branch that has commits"
    names a set precisely. The finding is a sweeping quantifier that is the
    object of an instruction and carries no qualifier, because that is the one
    the model has to size for you: "refactor all the modules", "review all my
    prompts". Four things take a hit back out:

      a qualifier      every file *changed on this branch*
      a count          all *four* artifacts
      a recurring event on every *push*
      an idiom         that changes *everything*
    """
    wide = re.compile(r"\b(all|every|everything)\b", re.I)
    qualifier = re.compile(
        r"^\s*(?:\w+[\s,]+){0,3}(that|which|who|whose|where|changed|modified|listed|"
        r"named|matching|created|mentioned|described|defined|marked|flagged|failing|"
        r"under|below|above|since|before|after|between)\b",
        re.I,
    )
    counted = re.compile(
        r"^\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b", re.I)
    possessive = re.compile(r"\b(all|every)\s+(my|your|our|their|his|her|its)\b", re.I)
    recurring = re.compile(
        r"\b(every|each)\s+(push|commit|run|release|request|time|day|week|month|hour|"
        r"minute|session|turn|iteration|cycle|build|deploy|merge|call)\b",
        re.I,
    )
    idiom = re.compile(
        r"\b(changes?|changed|means?|meant|is|was|are|were|explains?|poisons?|costs?)"
        r"\s+everything\b", re.I)
    task_verb = SLOT_BY_KEY["TASK"].cue

    out = []
    for i, raw in enumerate(lines, start=1):
        bare = INLINE_CODE.sub("", raw)
        m = wide.search(bare)
        if not m:
            continue
        if recurring.search(bare) or idiom.search(bare):
            continue
        tail = bare[m.end():]
        if qualifier.match(tail) or counted.match(tail):
            continue
        # An unsized scope is only expensive when something is being done to it.
        # "all my prompts" is an instruction's object even without a verb on the
        # line; "every downstream claim" inside a rationale is not.
        if task_verb.search(bare) or possessive.search(bare):
            out.append((i, m.group(0)))
    return out


def _detect_multi_ask(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """More asks than one reply can carry, with no order of priority."""
    verb = SLOT_BY_KEY["TASK"].cue
    hits = [i for i, raw in enumerate(lines, start=1) if verb.search(raw.strip())]
    ordered = re.search(r"\b(first|then|finally|in order|priorit|step 1|1\.)\b", text, re.I)
    if len(hits) > 6 and not ordered:
        return [(hits[0], f"{len(hits)} separate asks, no stated order")]
    return []


def _detect_no_stop(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """Open-ended verbs with no budget: the loop has no exit condition."""
    openv = re.compile(r"\b(research|explore|investigate|brainstorm|analy[sz]e|study|dig into|look into|survey)\b", re.I)
    bound = re.compile(
        r"\b(top|first|up to|at most|no more than|max(imum)?|limit(ed)?|within|budget|stop (when|after|once)|until)\b"
        r"|\b\d+\s*(sources?|results?|minutes?|hours?|pages?|examples?|items?)\b",
        re.I,
    )
    m = openv.search(INLINE_CODE.sub("", text))
    if m and not bound.search(text):
        return [(text[: m.start()].count("\n") + 1, m.group(0))]
    return []


def _detect_wall(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """One block long enough that the instructions inside it stop being separable."""
    out, start, buf = [], 1, []
    for i, raw in enumerate(lines + [""], start=1):
        if raw.strip():
            if not buf:
                start = i
            buf.append(raw)
        elif buf:
            block = " ".join(buf)
            if len(block) > 700 and not any(l.lstrip().startswith(("-", "*", "#", "1.")) for l in buf):
                out.append((start, f"{len(block)} characters, unbroken"))
            buf = []
    return out


def _detect_no_example(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """A shape was demanded and never shown."""
    wants_shape = re.compile(r"\b(json|csv|yaml|schema|format|classif\w+|extract|parse|tag|label|template)\b", re.I)
    has_example = re.compile(r"\b(e\.?g\.?|for example|for instance|like this|such as|example:)\b|```|\{\s*\"", re.I)
    m = wants_shape.search(INLINE_CODE.sub("", text))
    if m and not has_example.search(text):
        return [(text[: m.start()].count("\n") + 1, m.group(0))]
    return []


def _detect_unverifiable_acceptance(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """An acceptance test with nothing in it that could ever be run or counted.

    The slot rule only asks whether an acceptance test is *present*. "It should
    be good" satisfies that and settles nothing. A test earns its place by
    naming a handle: a command, a number, or an exact comparison — something
    that can come back false.
    """
    handle = re.compile(
        r"`[^`]{3,}`"                                  # a command or an identifier
        r"|\b\d+\b"                                     # a count or a threshold
        r"|\b(exactly|identical|matches?|equals?|parses?|passes|fails?|exits?\s+0"
        r"|green|clean|byte[- ]for[- ]byte|no \w+)\b",
        re.I,
    )
    # The slot cue is deliberately loose so that a present test is rarely
    # missed. That looseness cannot be inherited here: "never promote it to
    # verified" mentions verification without stating a test, and judging it as
    # a weak test is a false positive. This rule needs the stating, not the
    # vocabulary.
    framing = re.compile(
        r"\bacceptance\b|\bdone when\b|\bsuccess (is|means|criteria)\b|\bcriteri(a|on)\b"
        r"|\bmust pass\b|\bit works when\b|\bcorrect (if|when)\b|\bjudged? (by|on)\b"
        r"|\b(right|correct|valid|accepted|complete|done) only (if|when)\b"
        r"|\bdefinition of done\b|\bthe check that\b",
        re.I,
    )
    buckets = classify(lines)
    bucket = [line for line in buckets["ACCEPTANCE"] if line.strip()]
    stated = [line for line in bucket if framing.search(line)]
    if not stated:
        return []                                      # absence is NO_ACCEPTANCE's job
    # The handle may sit anywhere in the section, not on the line that framed
    # it: "## ACCEPTANCE TEST" states the test, and the command proving it is
    # the line below.
    if any(handle.search(line) for line in bucket):
        return []
    first = stated[0]
    lineno = next((i for i, l in enumerate(lines, start=1) if l.strip() == first.strip()), 0)
    return [(lineno, first.strip()[:70])]


def _detect_iceberg(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """A whole document pasted into the prompt, where a path would have done.

    Documented as Saraev's "context iceberg": keep the global rules and the
    current task above the waterline and let tools read the rest on demand,
    because a long context both costs more and degrades the answer. This can
    only ever be advice — in a chat window with no file access, pasting is the
    only option — so it is graded `info` and says so in the fix.
    """
    out, in_fence, start, size, count = [], False, 0, 0, 0
    for i, line in enumerate(raw.splitlines(), start=1):
        if FENCE.match(line):
            if in_fence:
                if size > 2000 or count > 60:
                    out.append((start, f"{count} lines / {size} characters pasted inline"))
                in_fence = False
            else:
                in_fence, start, size, count = True, i, 0, 0
            continue
        if in_fence:
            size += len(line) + 1
            count += 1
    return out


def _detect_pronoun_start(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
    """Opening with a pronoun that refers to nothing the model can see."""
    first = next((l for l in lines if l.strip()), "")
    m = re.match(r"\s*(it|this|that|they|them|those|these|he|she)\b", first, re.I)
    return [(1, m.group(1))] if m else []


def _phrase_detector(phrases: list[str]):
    lowered_phrases = [p.lower() for p in phrases]

    def detect(lines: list[str], text: str, raw: str) -> list[tuple[int, str]]:
        out = []
        for i, raw in enumerate(lines, start=1):
            bare = INLINE_CODE.sub("", raw).lower()
            for phrase in lowered_phrases:
                if phrase in bare:
                    out.append((i, phrase))
        return out

    return detect


HAZARDS: tuple[Hazard, ...] = (
    Hazard(
        "FALSE_MEMORY", "asserts a shared history the model has no record of", "error", "honesty",
        "The model cannot look up what it was told in another conversation. Asked to act on one, it reconstructs it.",
        "State the fact itself instead of referring to when you last said it.",
        detector=_phrase_detector(FALSE_MEMORY),
    ),
    Hazard(
        "FALSE_PREMISE", "names something as existing without identifying it", "error", "honesty",
        "The definite article asserts a unique referent. With no path, name, or number the model chooses one.",
        "Name it: a path, a test id, an error string, a line number.",
        detector=_detect_false_premise,
    ),
    Hazard(
        "PLACEHOLDER", "unfilled placeholder shipped in the prompt", "error", "precision",
        "A prompt containing TODO asks the model to decide what you had not decided.",
        "Fill it, or delete the line and let the ESCAPE clause cover the gap.",
        pattern=re.compile(r"<<MISSING:|\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|\[insert[^\]]*\]|\{\{[^}]*\}\}|\bLOREM\b", re.I),
    ),
    Hazard(
        "CONTRADICTION", "two instructions that cannot both hold", "error", "precision",
        "When instructions conflict one of them is dropped, and which one is not up to you.",
        "Keep the one that matters and delete the other, or scope each to a different section.",
        detector=_detect_contradiction,
    ),
    Hazard(
        "UNBOUNDED", "'all'/'every' with no stated extent", "warn", "bounds",
        "The reach of the word is decided by the model. Yours and its reading of 'all' rarely match.",
        "Replace with a countable bound: the ten most recent, everything under src/, the last 30 days.",
        detector=_detect_unbounded,
    ),
    Hazard(
        "NO_STOP", "open-ended verb with no budget", "warn", "bounds",
        "'Research X' has no natural end, so it ends wherever the context window does.",
        "Add a stop condition: N sources, a time box, or 'stop when two rounds add nothing new'.",
        detector=_detect_no_stop,
    ),
    Hazard(
        "MULTI_ASK", "more asks than one reply can carry", "warn", "bounds",
        "Long lists of asks are answered unevenly, and the unevenness is invisible in the reply.",
        "Split into separate prompts, or number them and say which two matter most.",
        detector=_detect_multi_ask,
    ),
    Hazard(
        "VAGUE_QUALITY", "quality word with no measurable meaning", "warn", "precision",
        "'Better', 'clean', 'professional' name a feeling. Nothing in the reply can be checked against them.",
        "Say what changes: fewer than 3 dependencies, passes ruff, reads at grade 9, fits one screen.",
        pattern=re.compile(
            r"\bbest practices?\b|\bmake it better\b|\bimprove it\b|\bhigh[- ]quality\b|\bprofessional\b"
            r"|\bmodern\b|\bclean(?: it up)?\b|\brobust\b|\buser[- ]friendly\b|\bseamless\b|\bproperly\b"
            r"|\bas appropriate\b|\bas needed\b|\betc\.?\b|\band so on\b|\boptimi[sz]e it\b|\bpolish\b",
            re.I,
        ),
    ),
    Hazard(
        "VAGUE_QUANT", "quantity the model has to pick for you", "warn", "precision",
        "'Some examples' is answered with however many the model feels like producing.",
        "Give a number, or a rule that yields one.",
        pattern=re.compile(r"(?<!how )\b(some|several|a few|many|various|a couple|a bunch of|numerous|multiple)\b", re.I),
    ),
    Hazard(
        "HEDGE", "the prompt hedges its own instruction", "warn", "precision",
        "A hedged instruction is optional, and optional instructions are the first to be dropped.",
        "Decide. If you genuinely do not know, ask for options instead of hedging the ask.",
        pattern=re.compile(
            r"\b(maybe|perhaps|i think|i guess|probably|might want to|if possible|ideally)\b"
            r"|(?<!\ba )(?<!\bthe )(?<!\bthis )(?<!\bthat )(?<!\bwhat )(?<!\bwhich )"
            r"(?<!\bany )(?<!\bsame )(?<!\bonly )(?<!\bother )(?<!\bevery )\b(sort of|kind of)\b",
            re.I),
    ),
    Hazard(
        "NO_EXAMPLE", "a shape is demanded but never shown", "info", "precision",
        "Format described in prose is reproduced approximately. Format shown is reproduced exactly.",
        "Paste one worked example of the output, even a two-line one.",
        detector=_detect_no_example,
    ),
    Hazard(
        "FILLER", "words that cost tokens and constrain nothing", "info", "economy",
        "Politeness is free in conversation and priced per token here. It also dilutes the instructions around it.",
        "Delete. Courtesy does not change the output; the instruction does.",
        pattern=re.compile(r"\b(please|kindly|thanks in advance|thank you|i would like you to|i want you to|if you (don'?t mind|could|would))\b", re.I),
    ),
    Hazard(
        "ROLE_INFLATION", "superlative role with no operative content", "info", "economy",
        "'World's best engineer' adds no constraint the next sentence does not add better.",
        "Replace with the qualification that actually changes the answer: the domain, the seniority, the audience.",
        pattern=re.compile(r"\bworld'?s (best|greatest|leading)\b|\bexpert genius\b|\b10x\b|\brockstar\b|\bninja\b|\bguru\b|\bphd[- ]level\b|\bsmartest\b|\bunparalleled\b|\belite\b", re.I),
    ),
    Hazard(
        "PRONOUN_START", "opens with a pronoun that has no antecedent", "info", "precision",
        "In a fresh context 'it' refers to nothing. The model picks the most recent plausible noun, which may be from your example.",
        "Name the thing in the first sentence.",
        detector=_detect_pronoun_start,
    ),
    Hazard(
        "UNVERIFIABLE_ACCEPTANCE", "an acceptance test nothing could fail", "warn", "verification",
        "A test that names no command, number, or exact comparison cannot come back false, so it settles nothing after the answer arrives.",
        "Name the handle: the command that must pass, the count it must hit, or the string it must match exactly.",
        detector=_detect_unverifiable_acceptance,
    ),
    Hazard(
        "ICEBERG", "a whole document pasted where a path would do", "info", "economy",
        "A long context costs tokens on every turn and degrades the answer; a file the model can read on demand costs neither until it is needed.",
        "If the model can read files, name the path and let it fetch what it needs. If it cannot — a chat window, another vendor — pasting is correct and this finding is noise.",
        detector=_detect_iceberg,
    ),
    Hazard(
        "WALL", "one block long enough to hide its own instructions", "info", "economy",
        "Instructions buried mid-paragraph are followed less reliably than instructions on their own line.",
        "Break into the seven slots, or at least into bullets.",
        detector=_detect_wall,
    ),
)

HAZARD_BY_ID = {h.id: h for h in HAZARDS}

# Rules whose words are legitimate when what they name is being forbidden.
NEGATABLE = {"VAGUE_QUALITY", "VAGUE_QUANT", "FILLER", "ROLE_INFLATION", "HEDGE"}
NEGATION = re.compile(r"\b(do not|don'?t|never|avoid|without|rather than|instead of|no more)\b[^.]*$", re.I)


# --------------------------------------------------------------------------
# Frameworks
# --------------------------------------------------------------------------

# Two different frameworks share the acronym CLEAR, by different authors, with
# three of five letters expanding differently. The tool refuses to guess which
# one you meant: `--framework` takes `clear-lo` or `clear-saraev`, never
# `clear`. Both are reporting lenses over rules this repository defined
# independently; the letters are theirs, the rules are not, and the mapping is
# this repository's reading of where each rule lands. Provenance for both, and
# what the attribution rests on, is in docs/prompting.md.
FRAMEWORKS = {
    "clear-lo": {
        "title": "CLEAR (Lo)",
        "attribution": "Lo, 'The CLEAR path', The Journal of Academic Librarianship 49(4), 2023",
        "letters": {
            "C": "Concise — eliminate what does not narrow the task",
            "L": "Logical — structure it so the relationships are visible",
            "E": "Explicit — say the format, the scope, the bounds",
            "A": "Adaptive — vary the formulation and adjust to what comes back",
            "R": "Reflective — evaluate the output and feed that back into the prompt",
        },
        "map": {
            "FILLER": "C", "ROLE_INFLATION": "C", "WALL": "C",
            "NO_ROLE": "L", "NO_CONTEXT": "L", "NO_TASK": "L",
            "CONTRADICTION": "L", "MULTI_ASK": "L", "PRONOUN_START": "L",
            "NO_OUTPUT": "E", "NO_CONSTRAINTS": "E", "UNBOUNDED": "E", "NO_STOP": "E",
            "VAGUE_QUALITY": "E", "VAGUE_QUANT": "E", "HEDGE": "E",
            "PLACEHOLDER": "E", "NO_EXAMPLE": "E",
            "NO_ACCEPTANCE": "R", "UNVERIFIABLE_ACCEPTANCE": "R",
        },
        "unmapped": ["NO_ESCAPE", "FALSE_MEMORY", "FALSE_PREMISE", "ICEBERG"],
        "unchecked": ["A"],
    },
    "clear-saraev": {
        "title": "CLEAR (Saraev)",
        "attribution": "attributed to Saraev by third-party documentation; unverified at source — docs/prompting.md",
        "letters": {
            "C": "Clarity — precise problem definition with measurable outcomes",
            "L": "Logic — structured thinking the model can follow",
            "E": "Examples — specific scenarios and edge cases",
            "A": "Adaptation — iterative refinement based on feedback",
            "R": "Results — validation that the output matches the need",
        },
        "map": {
            "NO_TASK": "C", "NO_CONSTRAINTS": "C", "UNBOUNDED": "C", "NO_STOP": "C",
            "VAGUE_QUALITY": "C", "VAGUE_QUANT": "C", "HEDGE": "C",
            "PLACEHOLDER": "C", "FALSE_PREMISE": "C",
            "NO_CONTEXT": "L", "NO_ROLE": "L", "CONTRADICTION": "L",
            "MULTI_ASK": "L", "WALL": "L", "PRONOUN_START": "L", "ICEBERG": "L",
            # "Examples: specific scenarios and edge cases" - an escape clause is
            # the edge case named in the prompt, which is why NO_ESCAPE maps here
            # under this framework and nowhere under Lo's.
            "NO_EXAMPLE": "E", "NO_ESCAPE": "E",
            "NO_OUTPUT": "R", "NO_ACCEPTANCE": "R", "UNVERIFIABLE_ACCEPTANCE": "R",
        },
        "unmapped": ["FILLER", "ROLE_INFLATION", "FALSE_MEMORY"],
        "unchecked": ["A"],
    },
}


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


@dataclass
class Finding:
    rule: str
    severity: str
    line: int
    title: str
    detail: str
    why: str
    fix: str
    dimension: str

    def as_dict(self) -> dict:
        return {
            "rule": self.rule, "severity": self.severity, "line": self.line,
            "title": self.title, "detail": self.detail, "why": self.why,
            "fix": self.fix, "dimension": self.dimension,
        }


@dataclass
class Report:
    source: str
    profile: str
    findings: list[Finding] = field(default_factory=list)
    slots_present: dict[str, bool] = field(default_factory=dict)
    words: int = 0

    @property
    def score(self) -> int:
        """100 minus one deduction per rule that fired, floored at 0.

        Per rule, not per occurrence: three vague words are one weakness, and
        a score that collapses on repetition stops discriminating between a
        sloppy prompt and a catastrophic one.
        """
        seen, total = set(), 0
        for f in self.findings:
            if f.rule not in seen:
                seen.add(f.rule)
                total += WEIGHTS[f.severity]
        return max(0, 100 - total)

    @property
    def grade(self) -> str:
        s = self.score
        return "A" if s >= 90 else "B" if s >= 80 else "C" if s >= 70 else "D" if s >= 60 else "F"

    def counts(self) -> dict[str, int]:
        out = {"error": 0, "warn": 0, "info": 0}
        for f in self.findings:
            out[f.severity] += 1
        return out


BLOCKQUOTE = re.compile(r"^\s*>")


def strip_fences(text: str) -> str:
    """Drop what the prompt is displaying rather than saying.

    A fenced block is an example, and a markdown blockquote is a quotation - a
    document that teaches prompting has to be able to show a bad prompt without
    being graded as one. `verify_provenance.py` skips blockquotes for the same
    reason. Line numbers are preserved so findings still point at the right
    line.
    """
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence or BLOCKQUOTE.match(line) else line)
    return "\n".join(out)


def analyse(text: str, profile: str = DEFAULT_PROFILE, source: str = "-") -> Report:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; known: {', '.join(sorted(PROFILES))}")

    prose = strip_fences(text)
    lines = prose.splitlines()
    report = Report(source=source, profile=profile, words=len(re.findall(r"\w+", prose)))

    # Absent slots.
    grading = PROFILES[profile]
    for slot in SLOTS:
        present = bool(slot.cue.search(prose)) or any(slot.cue.search(l) for l in lines)
        report.slots_present[slot.key] = present
        severity = grading.get(slot.key, "warn")
        if present or severity == "off":
            continue
        report.findings.append(Finding(
            rule=f"NO_{slot.key}", severity=severity, line=0,
            title=f"no {slot.heading.lower()}",
            detail=f"nothing in the prompt supplies {slot.hint}",
            why=slot.why,
            fix=f"add the {slot.heading} section: {slot.hint}",
            dimension="structure",
        ))

    # Present hazards.
    for hazard in HAZARDS:
        if hazard.profiles != ("*",) and profile not in hazard.profiles:
            continue
        hits: list[tuple[int, str]] = []
        if hazard.detector is not None:
            hits = hazard.detector(lines, prose, text)     # type: ignore[operator]
        elif hazard.pattern is not None:
            for i, raw in enumerate(lines, start=1):
                bare = INLINE_CODE.sub("", raw)
                for m in hazard.pattern.finditer(bare):
                    # "Do not polish the tone" forbids the vague word; it does
                    # not commit it. Only an instruction *to* do the vague
                    # thing is a finding.
                    if hazard.id in NEGATABLE and NEGATION.search(bare[max(0, m.start() - 40):m.start()]):
                        continue
                    hits.append((i, m.group(0)))
        for hit in hits:
            line, excerpt = hit[0], hit[1]
            severity = hit[2] if len(hit) > 2 else hazard.severity
            report.findings.append(Finding(
                rule=hazard.id, severity=severity, line=line,
                title=hazard.title, detail=str(excerpt), why=hazard.why,
                fix=hazard.fix, dimension=hazard.dimension,
            ))

    report.findings.sort(key=lambda f: (f.line, f.rule))
    return report


# --------------------------------------------------------------------------
# Compile
# --------------------------------------------------------------------------


MISSING_PREFIX = "<<MISSING:"


def classify(lines: list[str]) -> dict[str, list[str]]:
    """File each non-empty line under exactly one slot.

    Unmatched lines go to TASK rather than being dropped. Nothing is dropped,
    reworded, or merged: this is a filing operation, not a rewrite.
    """
    buckets: dict[str, list[str]] = {s.key: [] for s in SLOTS}
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        for key in CLASSIFY_ORDER:
            if SLOT_BY_KEY[key].cue.search(line):
                buckets[key].append(line)
                break
        else:
            buckets["TASK"].append(line)
    return buckets


def compile_prompt(text: str, profile: str = DEFAULT_PROFILE) -> str:
    """Rebuild the prompt in canonical slot order, marking every gap.

    Invariant, enforced by tests: every non-empty input line appears verbatim
    in the output, and every line of the output is either an input line, a
    template heading, or a `<<MISSING: ...>>` marker. The tool cannot invent a
    requirement, because it has no path by which to write one.
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}; known: {', '.join(sorted(PROFILES))}")

    buckets = classify(text.splitlines())
    grading = PROFILES[profile]
    out: list[str] = []
    for slot in SLOTS:
        severity = grading.get(slot.key, "warn")
        content = buckets[slot.key]
        if not content and severity == "off":
            continue
        out.append(f"## {slot.heading}")
        if content:
            out.extend(content)
        else:
            out.append(f"{MISSING_PREFIX} {slot.hint} >>")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


BULLET = {"error": "!!", "warn": " !", "info": " ."}


def render(report: Report, verbose: bool = True) -> str:
    counts = report.counts()
    head = (f"{report.source}  [{report.profile}]  score {report.score}/100 ({report.grade})  "
            f"{report.words} words  "
            f"{counts['error']} error / {counts['warn']} warn / {counts['info']} info")
    lines = [head, "-" * len(head)]

    present = [k for k, v in report.slots_present.items() if v]
    absent = [k for k, v in report.slots_present.items() if not v]
    lines.append(f"slots present: {', '.join(present) if present else 'none'}")
    lines.append(f"slots absent:  {', '.join(absent) if absent else 'none'}")
    lines.append("")

    if not report.findings:
        lines.append("no findings.")
        return "\n".join(lines)

    for f in report.findings:
        where = f"line {f.line}" if f.line else "prompt"
        lines.append(f"{BULLET[f.severity]} {f.rule:<15} {where:<9} {f.title}")
        lines.append(f"     {f.detail}")
        if verbose:
            lines.append(f"     why: {f.why}")
            lines.append(f"     fix: {f.fix}")
        lines.append("")
    return "\n".join(lines).rstrip()


def read_source(name: str) -> tuple[str, str]:
    if name == "-":
        return sys.stdin.read(), "<stdin>"
    path = Path(name)
    if not path.exists():
        raise FileNotFoundError(name)
    return path.read_text(encoding="utf-8", errors="replace"), str(path)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def cmd_lint(args) -> int:
    worst, payload = 0, []
    for name in args.files:
        text, label = read_source(name)
        report = analyse(text, args.profile, label)
        payload.append({
            "source": label, "profile": report.profile, "score": report.score,
            "grade": report.grade, "words": report.words,
            "slots_present": report.slots_present,
            "findings": [f.as_dict() for f in report.findings],
        })
        if not args.json:
            print(render(report, verbose=not args.quiet))
            print()
        counts = report.counts()
        if counts["error"] or counts["warn"] or (args.strict and counts["info"]):
            worst = 1
    if args.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2))
    return worst


def _by_framework(report: Report, key: str) -> dict[str, int | None]:
    """Per-component scores under one framework.

    A component with no static check scores None, not 100 — reporting a perfect
    score for something never examined is the same move as reporting a plan as
    a result.
    """
    fw = FRAMEWORKS[key]
    out: dict[str, int | None] = {
        letter: (None if letter in fw["unchecked"] else 100)
        for letter in fw["letters"]
    }
    seen = set()
    for f in report.findings:
        letter = fw["map"].get(f.rule)
        if letter is None or f.rule in seen:
            continue
        seen.add(f.rule)
        current = out[letter]
        if current is not None:
            out[letter] = max(0, current - WEIGHTS[f.severity] * 2)
    return out


def cmd_score(args) -> int:
    rows, worst = [], 0
    for name in args.files:
        text, label = read_source(name)
        report = analyse(text, args.profile, label)
        rows.append((label, report))
        if report.score < args.min_score:
            worst = 1

    if args.framework and not args.json:
        fw = FRAMEWORKS[args.framework]
        for label, r in rows:
            print(f"{label}  [{r.profile}]  {r.score}/100 ({r.grade})  — {fw['title']}")
            for letter, score in _by_framework(r, args.framework).items():
                shown = "n/a    " if score is None else f"{score:>3}/100"
                mark = "  (not statically checkable)" if score is None else ""
                print(f"  {letter}  {shown}  {fw['letters'][letter]}{mark}")
            unmapped = sorted({f.rule for f in r.findings} & set(fw["unmapped"]))
            if unmapped:
                print(f"  outside this framework: {', '.join(unmapped)}")
            print(f"  {fw['attribution']}")
            print()
        return worst

    if args.json:
        print(json.dumps([
            {"source": l, "score": r.score, "grade": r.grade, "profile": r.profile,
             "dimensions": _by_dimension(r),
             **({"framework": args.framework,
                 "components": _by_framework(r, args.framework),
                 "attribution": FRAMEWORKS[args.framework]["attribution"]}
                if args.framework else {})}
            for l, r in rows
        ], indent=2))
    else:
        width = max((len(l) for l, _ in rows), default=6)
        for label, r in rows:
            dims = _by_dimension(r)
            worst_dim = min(dims, key=dims.get) if dims else "-"
            print(f"{label:<{width}}  {r.score:>3}/100  {r.grade}  weakest: {worst_dim}")
    return worst


def _by_dimension(report: Report) -> dict[str, int]:
    """Per-dimension scores, so a prompt can be told where it is weak.

    Dimensions are this repository's own axes, not an outside framework's.
    """
    dims = ("structure", "precision", "bounds", "honesty", "economy", "verification")
    out = {d: 100 for d in dims}
    seen = set()
    for f in report.findings:
        if (f.dimension, f.rule) in seen:
            continue
        seen.add((f.dimension, f.rule))
        out[f.dimension] = max(0, out[f.dimension] - WEIGHTS[f.severity] * 2)
    return out


def cmd_compile(args) -> int:
    text, label = read_source(args.file)
    out = compile_prompt(text, args.profile)
    print(out, end="")
    if args.with_report:
        report = analyse(text, args.profile, label)
        print(render(report), file=sys.stderr)
        return 1 if report.counts()["error"] else 0
    return 0


def cmd_rules(args) -> int:
    grading = PROFILES[args.profile]
    if args.json:
        print(json.dumps({
            "profile": args.profile,
            "slots": [
                {"id": f"NO_{s.key}", "slot": s.key, "heading": s.heading,
                 "severity": grading.get(s.key, "warn"), "hint": s.hint, "why": s.why}
                for s in SLOTS
            ],
            "hazards": [
                {"id": h.id, "severity": h.severity, "dimension": h.dimension,
                 "title": h.title, "why": h.why, "fix": h.fix}
                for h in HAZARDS
            ],
        }, indent=2))
        return 0
    if args.framework:
        fw = FRAMEWORKS[args.framework]
        print(f"{fw['title']} components, and the rules this repository maps to each")
        print(f"{fw['attribution']}\n")
        for letter, meaning in fw["letters"].items():
            mapped = sorted(r for r, l in fw["map"].items() if l == letter)
            note = "  — no static check; this is a property of how you iterate" \
                if letter in fw["unchecked"] else ""
            print(f"  {letter}  {meaning}{note}")
            print(f"     {', '.join(mapped) if mapped else 'no rule maps here'}")
        print(f"\n  outside it: {', '.join(fw['unmapped'])}")
        return 0
    print(f"profile: {args.profile}\n")
    print("slots (a finding when absent)")
    for s in SLOTS:
        print(f"  {'NO_' + s.key:<15} {grading.get(s.key, 'warn'):<6} {s.hint}")
    print("\nhazards (a finding when present)")
    for h in HAZARDS:
        print(f"  {h.id:<15} {h.severity:<6} {h.title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt_forge",
        description="Audit and restructure prompts. 0 clean, 1 findings, 2 could not run.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_profile(p):
        p.add_argument("--profile", default=DEFAULT_PROFILE, choices=sorted(PROFILES),
                       help="how strictly each slot is graded (default: task)")

    lint = sub.add_parser("lint", help="audit one or more prompts")
    add_profile(lint)
    lint.add_argument("files", nargs="+", help="prompt files, or - for stdin")
    lint.add_argument("--json", action="store_true")
    lint.add_argument("--strict", action="store_true", help="info-level findings also fail")
    lint.add_argument("--quiet", action="store_true", help="one line per finding")
    lint.set_defaults(func=cmd_lint)

    score = sub.add_parser("score", help="one score per prompt")
    add_profile(score)
    score.add_argument("files", nargs="+")
    score.add_argument("--json", action="store_true")
    score.add_argument("--min-score", type=int, default=0, help="fail below this score")
    score.add_argument("--framework", choices=sorted(FRAMEWORKS), default=None,
                       help="also report per-component scores under a named framework. "
                            "Two frameworks share the acronym CLEAR and expand it "
                            "differently, so name the one you mean")
    score.set_defaults(func=cmd_score)

    comp = sub.add_parser("compile", help="restructure a prompt into the seven slots")
    add_profile(comp)
    comp.add_argument("file", help="prompt file, or - for stdin")
    comp.add_argument("--with-report", action="store_true", help="also write the audit to stderr")
    comp.set_defaults(func=cmd_compile)

    rules = sub.add_parser("rules", help="list the rules in force")
    add_profile(rules)
    rules.add_argument("--json", action="store_true")
    rules.add_argument("--framework", choices=sorted(FRAMEWORKS), default=None,
                       help="show the mapping to a named framework's components")
    rules.set_defaults(func=cmd_rules)
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"prompt_forge: no such file: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"prompt_forge: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
