#!/usr/bin/env python3
"""Tests for the user-scope installer.

The installer writes into the owner's real ~/.claude/, so the case that matters
is not "does it copy files" but "can it destroy something the owner wrote".
Every case below is about that: the block is spliced, never smeared; existing
content survives; re-running does not accumulate copies; and a dry run is
genuinely inert.

Run: python3 tests/test_install_user_scope.py
"""

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import install_user_scope as ius  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail="") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def main() -> int:
    real_home = ius.HOME_CLAUDE
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / ".claude"
        ius.HOME_CLAUDE = fake
        try:
            target = fake / "CLAUDE.md"

            print("dry-run cases")
            rc = ius.main([])
            check("dry run exits 0", rc == 0, rc)
            check("dry run writes nothing at all", not fake.exists())

            print("first-install cases")
            rc = ius.main(["--apply"])
            check("apply exits 0", rc == 0, rc)
            check("CLAUDE.md is created", target.exists())
            body = target.read_text()
            check("the managed block is delimited", ius.BEGIN in body and ius.END in body)
            check("the doctrine is actually in it", "Never fabricate" in body)
            check("the ooda skill is installed", (fake / "skills/ooda/SKILL.md").exists())
            check("commands are installed", (fake / "commands/ultrareview.md").exists())

            print("idempotence cases")
            ius.main(["--apply"])
            body2 = target.read_text()
            check("re-running does not duplicate the block",
                  body2.count(ius.BEGIN) == 1, body2.count(ius.BEGIN))
            check("re-running is a no-op on content", body2 == body)

            print("owner-content cases")
            # The failure that would actually hurt: the owner's own rules, written
            # by hand, silently replaced by ours.
            owner = "# My own rules\n\nAlways deploy on Fridays.\n"
            target.write_text(owner)
            ius.main(["--apply"])
            merged = target.read_text()
            check("owner's own content survives an install",
                  "Always deploy on Fridays." in merged)
            check("owner's content stays above our block",
                  merged.index("Always deploy on Fridays.") < merged.index(ius.BEGIN))
            check("our block is appended exactly once",
                  merged.count(ius.BEGIN) == 1, merged.count(ius.BEGIN))

            print("update cases")
            # An edit inside our block must be replaced; an edit outside must not.
            tampered = merged.replace("Never fabricate", "Never fabricate (edited)")
            target.write_text(tampered + "\n# Trailing note of mine\n")
            ius.main(["--apply"])
            after = target.read_text()
            check("edits inside the block are overwritten",
                  "(edited)" not in after)
            check("content after the block survives",
                  "# Trailing note of mine" in after)
            check("content before the block survives",
                  "Always deploy on Fridays." in after)

            print("uninstall cases")
            rc = ius.main(["--uninstall", "--apply"])
            final = target.read_text()
            check("uninstall exits 0 when it removed something", rc == 0, rc)
            check("the block is gone", ius.BEGIN not in final)
            check("the owner keeps everything they wrote",
                  "Always deploy on Fridays." in final and "# Trailing note of mine" in final)
            rc = ius.main(["--uninstall", "--apply"])
            check("uninstalling twice reports nothing to do", rc == 1, rc)
        finally:
            ius.HOME_CLAUDE = real_home

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
