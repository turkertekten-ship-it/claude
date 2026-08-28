#!/usr/bin/env python3
"""Tests for the consistency guard.

Its failure paths were first demonstrated by perturbing this repository by
hand, which is not a test. Each one is exercised here: the file-reading checks
against a fixture tree, the two that read module state by adding a rule to the
module and taking it away again.

Run: python3 tests/test_check_consistency.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "check_consistency.py"

sys.path.insert(0, str(REPO / "tools"))
import check_consistency as cc  # noqa: E402
import prompt_forge as pf  # noqa: E402
import check_output as co  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def fixture(root: Path, *, orphan: bool = False, undocumented: bool = False) -> None:
    (root / "tests").mkdir(parents=True)
    (root / "tools").mkdir()
    (root / "tests" / "run_all.sh").write_text("run python3 tests/test_known.py\n")
    (root / "tests" / "test_known.py").write_text("")
    if orphan:
        (root / "tests" / "test_orphan.py").write_text("")
    (root / "tools" / "documented.py").write_text("")
    if undocumented:
        (root / "tools" / "secret.py").write_text("")
    (root / "README.md").write_text("| `tools/documented.py` | a tool |\n")
    (root / "CLAUDE.md").write_text("  documented.py   a tool\n")


def main() -> int:
    print("a test nobody runs is caught")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixture(root, orphan=True)
        found = cc.check_tests_are_run(root)
        check("the orphan is named", any("test_orphan.py" in f for f in found), found)
        check("the running test is not", not any("test_known.py" in f for f in found), found)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixture(root)
        check("a fully wired tree is clean", cc.check_tests_are_run(root) == [],
              cc.check_tests_are_run(root))

    print("\nan undocumented tool is caught, in both documents")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixture(root, undocumented=True)
        found = cc.check_tools_are_documented(root)
        check("the README is named", any("README" in f and "secret.py" in f for f in found), found)
        check("the layout is named", any("CLAUDE.md" in f and "secret.py" in f for f in found), found)
        check("the documented tool is not flagged",
              not any("documented.py" in f for f in found), found)
        check("a private module is not required to be documented",
              not any("_" in f.split("/")[-1][:1] for f in found))

    print("\nthe module-state checks fire when a rule loses its registration")
    saved = pf.FRAMEWORKS["clear-lo"]["map"].pop("FILLER")
    try:
        found = cc.check_rules_are_mapped()
        check("an unmapped rule is caught", any("FILLER" in f for f in found), found)
        check("and the framework is named", any("clear-lo" in f for f in found), found)
    finally:
        pf.FRAMEWORKS["clear-lo"]["map"]["FILLER"] = saved
    check("restoring it clears the finding", cc.check_rules_are_mapped() == [])

    saved_template = co.RULE_TEMPLATES.pop("MAX_COUNT")
    try:
        found = cc.check_emitted_rules_have_templates()
        check("an emittable rule with no template is caught",
              any("MAX_COUNT" in f for f in found), found)
    finally:
        co.RULE_TEMPLATES["MAX_COUNT"] = saved_template
    check("restoring it clears the finding", cc.check_emitted_rules_have_templates() == [])

    print("\na hook that runs a checker must exit with its status")
    import json as _json
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".claude").mkdir(parents=True)
        settings = root / ".claude" / "settings.json"

        def hooks(command: str) -> None:
            settings.write_text(_json.dumps(
                {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": command}]}]}}
            ))

        hooks('python3 tools/verify_provenance.py 2>&1 | tail -20')
        found = cc.check_hooks_preserve_status(root)
        check("a piped checker is caught", found, found)
        check("and the event is named", any("PostToolUse" in f for f in found), found)

        hooks('out=$(python3 tools/verify_provenance.py 2>&1); status=$?; echo "$out" | tail -20; exit $status')
        check("capturing the status clears it",
              cc.check_hooks_preserve_status(root) == [], cc.check_hooks_preserve_status(root))

        hooks('python3 tools/verify_provenance.py 2>&1 | tail -3 # briefing only: not a gate')
        check("a hook that declares itself not a gate is allowed",
              cc.check_hooks_preserve_status(root) == [], cc.check_hooks_preserve_status(root))

        hooks('printf "hello" | tail -1')
        check("a pipe with no checker in it is not this rule's business",
              cc.check_hooks_preserve_status(root) == [], cc.check_hooks_preserve_status(root))

        settings.write_text("{not json")
        check("unparseable settings are reported",
              cc.check_hooks_preserve_status(root), cc.check_hooks_preserve_status(root))

    print("\nthe profile check cannot be satisfied by prose")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for doc in (".claude/skills/prompt-forge", ".claude/commands"):
            (root / doc).mkdir(parents=True)
        # Every profile name appears as a bare word, none as code.
        prose = " ".join(f"the {p} of it" for p in pf.PROFILES)
        (root / ".claude/skills/prompt-forge/SKILL.md").write_text(prose)
        (root / ".claude/commands/prompt.md").write_text(prose)
        found = cc.check_profiles_are_documented(root)
        check("bare words do not satisfy it", len(found) >= len(pf.PROFILES), found[:3])
        coded = " ".join(f"`{p}`" for p in pf.PROFILES)
        (root / ".claude/skills/prompt-forge/SKILL.md").write_text(coded)
        (root / ".claude/commands/prompt.md").write_text(coded)
        check("backticked names do", cc.check_profiles_are_documented(root) == [],
              cc.check_profiles_are_documented(root))
        pipes = "profile <" + "|".join(pf.PROFILES) + ">"
        (root / ".claude/skills/prompt-forge/SKILL.md").write_text(pipes)
        (root / ".claude/commands/prompt.md").write_text(pipes)
        check("and so does a usage line", cc.check_profiles_are_documented(root) == [],
              cc.check_profiles_are_documented(root))

    print("\nthe command line contract")
    live = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True, timeout=60)
    check("this repository is consistent", live.returncode == 0, live.stdout)
    js = subprocess.run([sys.executable, str(TOOL), "--json"],
                        capture_output=True, text=True, timeout=60)
    import json
    payload = json.loads(js.stdout)
    check("--json lists every invariant", len(payload["by_check"]) == len(cc.CHECKS), payload)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
