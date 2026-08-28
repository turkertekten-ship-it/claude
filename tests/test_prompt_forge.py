#!/usr/bin/env python3
"""Tests for the prompt forge.

Two properties are worth more than the rest and are tested hardest:

  1. Every rule has been watched rejecting something. A rule that has never
     fired is a claim about prompts, not a check on them.
  2. `compile` cannot invent. Its output is the author's own lines, plus
     headings, plus explicit `<<MISSING:` markers — nothing else. A prompt
     tool that quietly adds requirements is the same failure this repository
     guards against in documents.

Run: python3 tests/test_prompt_forge.py
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "prompts"
TOOL = REPO / "tools" / "prompt_forge.py"

sys.path.insert(0, str(REPO / "tools"))
import prompt_forge as pf  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def rules_for(text: str, profile: str = "task") -> list[str]:
    return [f.rule for f in pf.analyse(text, profile).findings]


def run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, input=stdin if stdin is not None else "",
        cwd=REPO, timeout=60,
    )


# --------------------------------------------------------------------------
# Every hazard fires on something
# --------------------------------------------------------------------------

HAZARD_CASES = {
    "FALSE_MEMORY": "As we discussed, write the report.",
    "FALSE_PREMISE": "Fix the failing test and push.",
    "PLACEHOLDER": "Write the config. Schema: TODO.",
    "CONTRADICTION": "Be brief. Also give an exhaustive treatment.",
    "UNBOUNDED": "Refactor all the modules.",
    "NO_STOP": "Research the competitive landscape.",
    "VAGUE_QUALITY": "Clean it up and follow best practices.",
    "VAGUE_QUANT": "Give me some examples.",
    "HEDGE": "Maybe you should rewrite the intro.",
    "FILLER": "Please write the summary, thanks in advance.",
    "ROLE_INFLATION": "You are the world's best engineer. Write the parser.",
    "PRONOUN_START": "It should be faster.",
    "NO_EXAMPLE": "Return JSON with the parsed fields.",
    "MULTI_ASK": (
        "Write the parser.\nCreate the tests.\nBuild the CLI.\nAdd the docs.\n"
        "Fix the linter.\nDeploy the service.\nReview the schema.\n"
    ),
    "WALL": "Write the report. " + ("The system has many interacting parts that matter here. " * 15),
    "UNVERIFIABLE_ACCEPTANCE": "Write the report. Acceptance test: it should be good.",
    "ICEBERG": "Fix this.\n\n```python\n" + ("x = 1  # a pasted line of context\n" * 70) + "```\n",
}


def test_hazards_fire() -> None:
    print("every hazard has been watched firing")
    for rule, text in HAZARD_CASES.items():
        check(f"{rule} fires", rule in rules_for(text), rules_for(text))
    missing = {h.id for h in pf.HAZARDS} - set(HAZARD_CASES)
    check("every declared hazard has a case", not missing, sorted(missing))


def test_hazards_stay_quiet() -> None:
    print("\nhazards do not fire on the clean fixture")
    clean = (FIXTURES / "clean_task.md").read_text()
    fired = set(rules_for(clean))
    errors = [f.rule for f in pf.analyse(clean).findings if f.severity == "error"]
    check("clean fixture raises no error", not errors, errors)
    check("clean fixture scores an A", pf.analyse(clean).grade == "A", pf.analyse(clean).score)
    check("no slot is reported absent", all(pf.analyse(clean).slots_present.values()),
          pf.analyse(clean).slots_present)
    check("clean fixture does not trip false-memory", "FALSE_MEMORY" not in fired)


def test_backticks_are_quotation() -> None:
    print("\na phrase in backticks is quoted, not asserted")
    quoted = (FIXTURES / "quoted.md").read_text()
    fired = set(rules_for(quoted))
    check("`as we discussed` in backticks is allowed", "FALSE_MEMORY" not in fired, sorted(fired))
    check("`TODO` in backticks is allowed", "PLACEHOLDER" not in fired, sorted(fired))
    check("the same phrase bare is caught", "FALSE_MEMORY" in rules_for("As we discussed, write it."))


def test_fenced_blocks_are_not_instructions() -> None:
    print("\na fenced example is not scanned as an instruction")
    text = "Write the summary.\n\n```\nFix the failing test, thanks in advance.\n```\n"
    fired = set(rules_for(text))
    check("fenced content does not raise FALSE_PREMISE", "FALSE_PREMISE" not in fired, sorted(fired))
    check("the same text unfenced does", "FALSE_PREMISE" in rules_for("Fix the failing test."))


# --------------------------------------------------------------------------
# Slots and profiles
# --------------------------------------------------------------------------


def test_narrowings_are_proven() -> None:
    """Each narrowing added to a rule keeps the case it was meant to keep."""
    print("\nnarrowings hold on both sides")
    check("forbidding a vague word is not a finding",
          "VAGUE_QUALITY" not in rules_for("Do not polish the tone."))
    check("committing it still is",
          "VAGUE_QUALITY" in rules_for("Polish the tone."))
    check("'changes everything' is emphasis, not extent",
          "UNBOUNDED" not in rules_for("Locating the second reading changes everything."))
    check("'refactor everything' still is",
          "UNBOUNDED" in rules_for("Refactor everything."))
    check("'on every push' is a recurring trigger, not an open set",
          "UNBOUNDED" not in rules_for("Run the suite on every push."))
    check("a qualified set is bounded",
          "UNBOUNDED" not in rules_for("Review every file changed on this branch."))
    check("a relative clause bounds it too",
          "UNBOUNDED" not in rules_for("Read the diff for every branch that has commits."))
    check("a count bounds it",
          "UNBOUNDED" not in rules_for("Produce all four artifacts."))
    check("a rationale is not an instruction",
          "UNBOUNDED" not in rules_for("Anything else poisons every downstream claim."))
    check("a possessive sweep is a finding even with no verb",
          "UNBOUNDED" in rules_for("prompt perfection for all my prompts in all my chats"))
    check("an unqualified object of an instruction is a finding",
          "UNBOUNDED" in rules_for("Refactor all the modules."))
    check("'as a short list' states a shape",
          "NO_OUTPUT" not in rules_for("Report it as a short list."))
    check("'right only if' states an acceptance test",
          "NO_ACCEPTANCE" not in rules_for("The report is right only if every number came from the tool."))
    check("'how many' asks for a number rather than dodging one",
          "VAGUE_QUANT" not in rules_for("Report how many records were skipped."))
    check("'some records' still is",
          "VAGUE_QUANT" in rules_for("Report some records."))
    check("'absence is a finding' is an escape clause",
          "NO_ESCAPE" not in rules_for("List the files. Absence is a finding of equal weight. Output: a table."))
    check("a distant contradiction is a warning, a near one an error",
          _contradiction_severity(near=True) == "error"
          and _contradiction_severity(near=False) == "warn",
          (_contradiction_severity(near=True), _contradiction_severity(near=False)))
    check("'demonstrate the failure' is not a false premise",
          "FALSE_PREMISE" not in rules_for("Tests must demonstrate the failure."))
    check("'fix the bug' is",
          "FALSE_PREMISE" in rules_for("Fix the bug."))
    check("a 'Constraints:' heading satisfies the constraints slot",
          "NO_CONSTRAINTS" not in rules_for("Constraints: no dependencies."))
    check("a contraction is not an identifier anchor",
          "FALSE_PREMISE" in rules_for("fix the failing test and clean up the module while you're at it"))
    check("a backticked path is one",
          "FALSE_PREMISE" not in rules_for("Fix the failing test in `tests/test_x.py`."))
    check("so is a quoted name",
          "FALSE_PREMISE" not in rules_for('Fix the failing test named "test_dedupe".'))
    for label in ("**Task.** Write the parser.", "## TASK\nWrite the parser.",
                  "- Write the parser.", "1. Write the parser."):
        check(f"an imperative behind a label is seen: {label.splitlines()[0][:18]!r}",
              "NO_TASK" not in rules_for(label), rules_for(label))
    check("a blockquote is a quotation, not an instruction",
          "FALSE_PREMISE" not in rules_for("Write the guide.\n\n> fix the failing test\n"))
    check("the same line unquoted is an instruction",
          "FALSE_PREMISE" in rules_for("Write the guide.\n\nfix the failing test\n"))
    check("an acceptance test naming a command is not flagged",
          "UNVERIFIABLE_ACCEPTANCE" not in rules_for("Write it. Acceptance: `bash tests/run_all.sh` passes."))
    check("nor one naming an exact comparison",
          "UNVERIFIABLE_ACCEPTANCE" not in rules_for("Write it. Done when the job name is exactly checks."))
    check("nor one naming a count",
          "UNVERIFIABLE_ACCEPTANCE" not in rules_for("Write it. Acceptance: it returns at most 3 rows."))
    check("prose mentioning verification is not a stated test",
          "UNVERIFIABLE_ACCEPTANCE" not in
          rules_for("Write it. Never silently promote a report to verified."))
    check("nor is 'not a verified fact'",
          "UNVERIFIABLE_ACCEPTANCE" not in rules_for("Mark it second-hand; it is not a verified fact."))
    check("an absent acceptance test is NO_ACCEPTANCE's job, not this rule's",
          "UNVERIFIABLE_ACCEPTANCE" not in rules_for("Write the report."))
    check("a small fenced example is not an iceberg",
          "ICEBERG" not in rules_for("Fix this.\n\n```python\nx = 1\n```\n"))
    check("'the only kind of' is a noun phrase",
          "HEDGE" not in rules_for("That is the only kind of ambiguity worth a turn."))
    check("'kind of works' is a hedge",
          "HEDGE" in rules_for("It kind of works, so ship it."))
    check("a second-person job description counts as a role",
          not [f for f in pf.analyse("You process exports. Write it.", "system").findings
               if f.rule == "NO_ROLE"])
    check("'you must not guess' does not",
          [f for f in pf.analyse("You must not guess. Write it.", "system").findings
           if f.rule == "NO_ROLE"])


def _contradiction_severity(near: bool) -> str:
    filler = "\n".join(f"line {i}" for i in range(10))
    text = ("Be brief. Give an exhaustive treatment." if near
            else f"Be brief.\n{filler}\nGive an exhaustive treatment.")
    hits = [f.severity for f in pf.analyse(text).findings if f.rule == "CONTRADICTION"]
    return hits[0] if hits else "none"


def test_slots() -> None:
    print("\nabsent slots are reported, present ones are not")
    bare = "Thing."
    for slot in pf.SLOTS:
        rule = f"NO_{slot.key}"
        graded = pf.PROFILES["task"].get(slot.key)
        if graded == "off":
            continue
        check(f"{rule} on an empty prompt", rule in rules_for(bare), rules_for(bare))
    clean = (FIXTURES / "clean_task.md").read_text()
    absent = [r for r in rules_for(clean) if r.startswith("NO_") and r != "NO_EXAMPLE" and r != "NO_STOP"]
    check("no slot rule fires on the clean fixture", not absent, absent)


def test_profiles_grade_differently() -> None:
    print("\nprofiles change the grading, not the rules")
    no_role = "Write the parser. Output: one file. Done when tests pass. If it does not exist, say so."
    task_sev = {f.rule: f.severity for f in pf.analyse(no_role, "task").findings}
    system_sev = {f.rule: f.severity for f in pf.analyse(no_role, "system").findings}
    check("a missing role is info for a task prompt", task_sev.get("NO_ROLE") == "info", task_sev)
    check("a missing role is an error for a system prompt", system_sev.get("NO_ROLE") == "error", system_sev)
    chat_sev = {f.rule: f.severity for f in pf.analyse(no_role, "chat").findings}
    check("the chat profile switches the role rule off", "NO_ROLE" not in chat_sev, chat_sev)
    check("an unknown profile is refused",
          _raises(lambda: pf.analyse(no_role, "nonsense")))


def _raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


def test_escape_is_required_everywhere() -> None:
    print("\nthe escape clause is required under every profile")
    bare = "Write the parser."
    for profile in pf.PROFILES:
        sev = {f.rule: f.severity for f in pf.analyse(bare, profile).findings}
        check(f"{profile}: NO_ESCAPE is at least a warning",
              sev.get("NO_ESCAPE") in ("error", "warn"), sev.get("NO_ESCAPE"))


# --------------------------------------------------------------------------
# compile cannot invent
# --------------------------------------------------------------------------


def test_compile_preserves_every_line() -> None:
    print("\ncompile keeps every line the author wrote")
    for fixture in sorted(FIXTURES.glob("*.md")):
        text = fixture.read_text()
        out = pf.compile_prompt(text)
        kept = [l.rstrip() for l in text.splitlines() if l.strip()]
        missing = [l for l in kept if l not in out.splitlines()]
        check(f"{fixture.name}: no line dropped", not missing, missing[:2])


def test_compile_adds_nothing_else() -> None:
    print("\ncompile adds only headings and explicit gap markers")
    headings = {f"## {s.heading}" for s in pf.SLOTS}
    for fixture in sorted(FIXTURES.glob("*.md")):
        text = fixture.read_text()
        source_lines = {l.rstrip() for l in text.splitlines() if l.strip()}
        foreign = [
            line for line in pf.compile_prompt(text).splitlines()
            if line.strip()
            and line not in source_lines
            and line not in headings
            and not line.startswith(pf.MISSING_PREFIX)
        ]
        check(f"{fixture.name}: nothing invented", not foreign, foreign[:2])


def test_compile_marks_gaps_rather_than_filling_them() -> None:
    print("\na gap becomes a marker, never content")
    out = pf.compile_prompt("Write the parser.")
    markers = [l for l in out.splitlines() if l.startswith(pf.MISSING_PREFIX)]
    check("an empty prompt yields markers", len(markers) >= 4, len(markers))
    check("the marker names what is missing", all(l.endswith(">>") for l in markers), markers[:1])
    check("compiling twice adds no new content",
          _content(pf.compile_prompt(out)) == _content(out))


def _content(text: str) -> list[str]:
    return [
        l for l in text.splitlines()
        if l.strip() and not l.startswith("## ") and not l.startswith(pf.MISSING_PREFIX)
    ]


# --------------------------------------------------------------------------
# The command line contract
# --------------------------------------------------------------------------


def test_frameworks() -> None:
    """Both CLEAR frameworks are reported honestly, and kept apart."""
    print("\ntwo frameworks share an acronym and are not merged")
    check("both are offered", set(pf.FRAMEWORKS) == {"clear-lo", "clear-saraev"},
          sorted(pf.FRAMEWORKS))
    lo, saraev = pf.FRAMEWORKS["clear-lo"], pf.FRAMEWORKS["clear-saraev"]
    check("their letters expand differently",
          [lo["letters"][k][:8] for k in "CER"] != [saraev["letters"][k][:8] for k in "CER"])
    check("each names its attribution", lo["attribution"] and saraev["attribution"])
    check("Lo's is credited to Lo", "Lo," in lo["attribution"], lo["attribution"])
    check("Saraev's is marked unverified at source",
          "unverified at source" in saraev["attribution"], saraev["attribution"])

    for key, fw in pf.FRAMEWORKS.items():
        mapped = set(fw["map"]) | set(fw["unmapped"])
        all_rules = {h.id for h in pf.HAZARDS} | {f"NO_{s.key}" for s in pf.SLOTS}
        check(f"{key}: every rule is mapped or declared unmapped",
              all_rules <= mapped, sorted(all_rules - mapped))
        clean = pf.analyse((FIXTURES / "clean_task.md").read_text())
        scores = pf._by_framework(clean, key)
        check(f"{key}: every component is reported", set(scores) == set(fw["letters"]))
        check(f"{key}: an unchecked component scores n/a rather than 100",
              scores["A"] is None, scores["A"])

    hazards = pf.analyse((FIXTURES / "hazards.md").read_text())
    check("a vague prompt loses points on Lo's Explicit",
          (pf._by_framework(hazards, "clear-lo")["E"] or 100) < 60)
    check("and on Saraev's Clarity",
          (pf._by_framework(hazards, "clear-saraev")["C"] or 100) < 60)
    check("the escape clause maps under Saraev and not under Lo",
          pf.FRAMEWORKS["clear-saraev"]["map"].get("NO_ESCAPE") == "E"
          and "NO_ESCAPE" in pf.FRAMEWORKS["clear-lo"]["unmapped"])

    proc = run("score", "--profile", "contract", "--framework", "clear-saraev",
               str(FIXTURES / "clean_task.md"))
    check("score --framework clear-saraev runs", proc.returncode == 0, proc.stderr[:80])
    check("it marks the unchecked component", "n/a" in proc.stdout, proc.stdout[:200])
    ambiguous = run("score", "--framework", "clear", str(FIXTURES / "clean_task.md"))
    check("a bare 'clear' is refused, because two frameworks answer to it",
          ambiguous.returncode == 2, ambiguous.returncode)

    contract = pf.PROFILES["contract"]
    for slot in ("TASK", "CONSTRAINTS", "OUTPUT", "ESCAPE"):
        check(f"the contract profile requires {slot}", contract[slot] == "error", contract[slot])
    check("and does not require a role", contract["ROLE"] == "off", contract["ROLE"])


def test_exit_codes() -> None:
    print("\nexit codes mean what the house rules say they mean")
    clean = run("lint", str(FIXTURES / "clean_task.md"))
    check("0 on a clean prompt", clean.returncode == 0, clean.returncode)
    dirty = run("lint", str(FIXTURES / "hazards.md"))
    check("1 on findings", dirty.returncode == 1, dirty.returncode)
    gone = run("lint", str(FIXTURES / "does-not-exist.md"))
    check("2 when it could not run", gone.returncode == 2, gone.returncode)
    check("2 is reported on stderr", "no such file" in gone.stderr, gone.stderr[:60])
    piped = run("lint", "--profile", "task", "-", stdin="Write it.\n")
    check("stdin is accepted", piped.returncode in (0, 1), piped.stderr[:60])

    strict_info = run("lint", "--strict", "-", stdin="You are a bot.\nWrite it.\nOutput: json.\nDone when it parses.\nIf you cannot, say so.\n")
    check("--strict makes info findings fail", strict_info.returncode == 1, strict_info.returncode)

    scored = run("score", "--min-score", "90", str(FIXTURES / "hazards.md"))
    check("score --min-score fails a bad prompt", scored.returncode == 1, scored.returncode)
    scored_ok = run("score", "--min-score", "90", str(FIXTURES / "clean_task.md"))
    check("score --min-score passes a good one", scored_ok.returncode == 0, scored_ok.stdout)


def test_json_is_machine_readable() -> None:
    print("\nJSON output parses and carries the findings")
    import json
    proc = run("lint", "--json", str(FIXTURES / "hazards.md"))
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        check("lint --json parses", False, str(exc))
        return
    check("lint --json parses", True)
    check("it carries a score", isinstance(payload.get("score"), int), payload.get("score"))
    check("it carries findings", len(payload.get("findings", [])) > 5, len(payload.get("findings", [])))
    rules_proc = run("rules", "--json")
    check("rules --json parses", _json_ok(rules_proc.stdout))


def _json_ok(text: str) -> bool:
    import json
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False


def test_scoring_discriminates() -> None:
    print("\nthe score separates a written prompt from a wished-for one")
    clean = pf.analyse((FIXTURES / "clean_task.md").read_text())
    hazards = pf.analyse((FIXTURES / "hazards.md").read_text())
    check("a well-formed prompt scores 90+", clean.score >= 90, clean.score)
    check("a hazard-laden prompt scores under 40", hazards.score < 40, hazards.score)
    check("repetition of one weakness is one deduction",
          pf.analyse("Give me some examples.").score
          == pf.analyse("Give me some examples, some cases, some tests.").score)


# --------------------------------------------------------------------------
# The repository's own prompts are held to the standard
# --------------------------------------------------------------------------


def test_worked_example_matches_the_documented_scores() -> None:
    """The scores quoted in the skill are the scores the tool prints.

    They were not, once: the skill quoted 34 and 96 from nobody's measurement.
    A document in this repository asserting an unmeasured number is the same
    failure the provenance guard exists to catch, so the numbers are pinned
    here instead of retyped there.
    """
    print("\nthe worked example in the skill reproduces")
    skill = (REPO / ".claude" / "skills" / "prompt-forge" / "SKILL.md").read_text()
    raw = (FIXTURES / "worked_raw.md").read_text()
    forged = (FIXTURES / "worked_forged.md").read_text()

    raw_score = pf.analyse(raw, "task").score
    forged_report = pf.analyse(forged, "build")
    check(f"the raw ask scores {raw_score}", f"Score {raw_score}/100" in skill,
          f"skill does not quote {raw_score}")
    check(f"the forged prompt scores {forged_report.score}",
          f"Score {forged_report.score}/100" in skill, f"skill does not quote {forged_report.score}")
    check("the forged prompt carries no error-level finding",
          not [f for f in forged_report.findings if f.severity == "error"],
          [f.rule for f in forged_report.findings if f.severity == "error"])
    fired = set(rules_for(raw))
    for rule in ("FALSE_PREMISE", "VAGUE_QUALITY", "NO_OUTPUT", "NO_ACCEPTANCE", "NO_ESCAPE"):
        check(f"the skill's claimed finding {rule} actually fires", rule in fired, sorted(fired))


def test_the_preamble_is_the_length_it_claims() -> None:
    """The travelling block states its own size, so the size is checked.

    It claimed "one screen" and was three. A prompt standard whose own artifact
    makes an unmeasured claim about itself is not a standard.
    """
    print("\nthe portable preamble is the length it says it is")
    import re
    text = (REPO / "prompts" / "portable-preamble.md").read_text()
    lines = text.splitlines()
    start, end = lines.index("## Paste from here"), lines.index("## Paste to here")
    actual = sum(1 for line in lines[start + 1:end] if line.strip())
    claimed = re.search(r"The block is (\d+) lines of instruction", text)
    check("the file states its own block length", claimed is not None)
    if claimed:
        check(f"and it is right: {actual} lines", int(claimed.group(1)) == actual,
              f"claims {claimed.group(1)}, is {actual}")
    check("the block fits a terminal screen", actual <= 40, actual)


def test_repo_prompts_pass_their_own_standard() -> None:
    print("\nthe repository's own system prompts pass at the system profile")
    for path in sorted((REPO / "prompts").glob("*.md")):
        if path.name == "README.md":
            continue
        report = pf.analyse(path.read_text(), "system", path.name)
        errors = [f"{f.rule}@{f.line}" for f in report.findings if f.severity == "error"]
        check(f"{path.name} has no error-level finding", not errors, errors)


def main() -> int:
    test_hazards_fire()
    test_hazards_stay_quiet()
    test_backticks_are_quotation()
    test_fenced_blocks_are_not_instructions()
    test_narrowings_are_proven()
    test_slots()
    test_profiles_grade_differently()
    test_escape_is_required_everywhere()
    test_compile_preserves_every_line()
    test_compile_adds_nothing_else()
    test_compile_marks_gaps_rather_than_filling_them()
    test_frameworks()
    test_exit_codes()
    test_json_is_machine_readable()
    test_scoring_discriminates()
    test_worked_example_matches_the_documented_scores()
    test_the_preamble_is_the_length_it_claims()
    test_repo_prompts_pass_their_own_standard()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
