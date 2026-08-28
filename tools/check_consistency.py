#!/usr/bin/env python3
"""Check that the repository's lists still agree with each other.

Three times in this session, two lists stayed in step only because somebody was
paying attention: the installed copy against the repository, the installer's
targets against its own test list, and the tool's profiles against the prose
documenting them. Each was correct when checked and guarded by nothing.

A list that must match another list is a rule, and this repository's position on
rules is that they get enforced rather than remembered. These are the pairs:

  1. every tests/test_*.py is run by tests/run_all.sh
  2. every tool is named in README.md and in the CLAUDE.md layout
  3. every prompt_forge profile is named in the skill and the /prompt command
  4. every rule check_output can emit has a learn_rule template
  5. every declared hazard and slot is mapped or explicitly unmapped in each
     framework

A test nobody runs is the worst of these, because it reports nothing and looks
like coverage.

Usage
  python3 tools/check_consistency.py [--json]
Exit
  0 consistent · 1 drift found · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

PRIVATE = ("_",)


def tools_of(root: Path = REPO) -> list[Path]:
    return sorted(
        p for p in list(root.glob("tools/*.py")) + list(root.glob("tools/*.sh"))
        if not p.name.startswith(PRIVATE)
    )


def check_tests_are_run(root: Path = REPO) -> list[str]:
    runner = (root / "tests" / "run_all.sh").read_text()
    return [
        f"tests/{p.name} is never run: add it to tests/run_all.sh"
        for p in sorted(root.glob("tests/test_*.py"))
        if p.name not in runner
    ]


def check_tools_are_documented(root: Path = REPO) -> list[str]:
    readme = (root / "README.md").read_text()
    doctrine = (root / "CLAUDE.md").read_text()
    out = []
    for path in tools_of(root):
        if path.name not in readme:
            out.append(f"tools/{path.name} is not in the README table")
        if path.name not in doctrine:
            out.append(f"tools/{path.name} is not in the CLAUDE.md layout")
    return out


def check_profiles_are_documented(root: Path = REPO) -> list[str]:
    """A profile has to be named as code, not merely appear as a word.

    The first version of this check looked for the bare string, which "task",
    "chat" and "contract" satisfy in any prose about prompts — an invariant
    that could not fail, which is the defect `UNVERIFIABLE_ACCEPTANCE` exists to
    catch, committed here.
    """
    import prompt_forge as pf
    out = []
    for doc in (".claude/skills/prompt-forge/SKILL.md", ".claude/commands/prompt.md"):
        path = root / doc
        if not path.exists():
            out.append(f"{doc} is missing")
            continue
        text = path.read_text()
        for profile in sorted(pf.PROFILES):
            # Named as code, or as one alternative in a `<a|b|c>` usage line.
            named = (f"`{profile}`" in text
                     or re.search(rf"[<|]{profile}[|>]", text) is not None)
            if not named:
                out.append(f"profile {profile!r} is not named as code in {doc}")
    return out


def check_emitted_rules_have_templates(root: Path = REPO) -> list[str]:
    import check_output as co
    source = (root / "tools" / "check_output.py").read_text()
    emitted = set(re.findall(r'add\("([A-Z_]+)"', source))
    return [
        f"check_output can emit {rule} but learn_rule has no template for it"
        for rule in sorted(emitted - set(co.RULE_TEMPLATES))
    ]


def check_rules_are_mapped(root: Path = REPO) -> list[str]:
    import prompt_forge as pf
    every = {h.id for h in pf.HAZARDS} | {f"NO_{s.key}" for s in pf.SLOTS}
    out = []
    for name, framework in pf.FRAMEWORKS.items():
        accounted = set(framework["map"]) | set(framework["unmapped"])
        for rule in sorted(every - accounted):
            out.append(f"{rule} is neither mapped nor declared unmapped under {name}")
    return out


CHECKS = {
    "tests are run": check_tests_are_run,
    "tools are documented": check_tools_are_documented,
    "profiles are documented": check_profiles_are_documented,
    "emitted rules have templates": check_emitted_rules_have_templates,
    "rules are mapped": check_rules_are_mapped,
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="check_consistency",
        description="Check the repository's lists against each other. 0 consistent, 1 drift, 2 could not run.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    results: dict[str, list[str]] = {}
    try:
        for name, fn in CHECKS.items():
            results[name] = fn()
    except (OSError, ImportError) as exc:
        print(f"check_consistency: could not run: {exc}", file=sys.stderr)
        return 2

    findings = [f for group in results.values() for f in group]
    if args.json:
        print(json.dumps({"findings": findings, "by_check": results}, indent=2))
        return 1 if findings else 0

    for name, group in results.items():
        print(f"  {'FAIL' if group else 'ok  '} {name}")
        for finding in group:
            print(f"       {finding}")
    if findings:
        print(f"\ncheck_consistency: {len(findings)} drift(s)", file=sys.stderr)
        return 1
    print(f"\ncheck_consistency: {len(CHECKS)} invariant(s) hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
