#!/usr/bin/env python3
"""Tests for the installer's staleness check.

What runs in every other terminal is the installed copy, not this repository.
Until this check existed, the two stayed in step only because somebody
remembered to re-run the installer — which is the failure mode this repository
exists to guard against, one level up.

Every case runs against a temporary prefix, so the real ~/.claude is untouched.

Run: python3 tests/test_install_check.py
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALLER = REPO / "tools" / "install_prompt_system.sh"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run(*args: str, prefix: Path, bindir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(INSTALLER), *args, "--prefix", str(prefix), "--bin-dir", str(bindir)],
        capture_output=True, text=True, cwd=REPO, timeout=300,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        prefix, bindir = Path(tmp) / "claude", Path(tmp) / "bin"

        print("a machine with nothing installed is not 'stale'")
        fresh = run("--check", prefix=prefix, bindir=bindir)
        check("exit 0", fresh.returncode == 0, fresh.stdout[-200:])
        check("and it says what to run", "Run: bash tools" in fresh.stdout, fresh.stdout[:120])
        check("a read-only check writes nothing", not prefix.exists() and not bindir.exists(),
              f"{prefix.exists()=} {bindir.exists()=}")

        print("\ninstalling, then checking")
        install = run(prefix=prefix, bindir=bindir)
        check("install exits 0", install.returncode == 0, install.stdout[-300:])
        after = run("--check", prefix=prefix, bindir=bindir)
        check("a fresh install is in sync", after.returncode == 0, after.stdout[-200:])
        check("every file is compared, markdown included",
              after.stdout.count("same") >= 10, after.stdout)

        print("\ndrift is caught, in either kind of file")
        tool = prefix / "tools" / "prompt_forge.py"
        tool.write_text(tool.read_text() + "\n# drift\n")
        drifted = run("--check", prefix=prefix, bindir=bindir)
        check("a drifted tool fails", drifted.returncode == 1, drifted.returncode)
        check("and is named", "DRIFTED  tools/prompt_forge.py" in drifted.stdout, drifted.stdout)

        doc = prefix / "commands" / "prompt.md"
        doc.write_text(doc.read_text() + "\nextra\n")
        both = run("--check", prefix=prefix, bindir=bindir)
        check("a drifted command is caught too",
              "DRIFTED  commands/prompt.md" in both.stdout, both.stdout)
        check("the count is reported", "2 file(s) differ" in both.stdout, both.stdout[-300:])

        (prefix / "tools" / "learn_rule.py").unlink()
        missing = run("--check", prefix=prefix, bindir=bindir)
        check("a missing file is caught", "MISSING  tools/learn_rule.py" in missing.stdout,
              missing.stdout)

        print("\nreinstalling repairs it")
        run(prefix=prefix, bindir=bindir)
        repaired = run("--check", prefix=prefix, bindir=bindir)
        check("back in sync", repaired.returncode == 0, repaired.stdout[-200:])

        print("\nthe rewrite is part of the comparison, not a false difference")
        installed_cmd = (prefix / "commands" / "prompt.md").read_text()
        source_cmd = (REPO / ".claude" / "commands" / "prompt.md").read_text()
        check("the installed copy differs from source by the rewrite",
              installed_cmd != source_cmd)
        check("and the check still calls it the same",
              "same     commands/prompt.md" in repaired.stdout, repaired.stdout)

    print("\nit will not clobber a file it did not write")
    with tempfile.TemporaryDirectory() as tmp:
        prefix, bindir = Path(tmp) / "claude", Path(tmp) / "bin"
        (prefix / "commands").mkdir(parents=True)
        mine = prefix / "commands" / "prompt.md"
        original = "---\ndescription: The owner's own command.\n---\nDo the usual thing.\n"
        mine.write_text(original)

        refused = run(prefix=prefix, bindir=bindir)
        check("install refuses", refused.returncode == 1, refused.returncode)
        check("and names the file", "REFUSING to overwrite" in refused.stderr, refused.stderr[:200])
        check("the owner's file is untouched", mine.read_text() == original, mine.read_text()[:80])

        forced = run("--force", prefix=prefix, bindir=bindir)
        check("--force installs", forced.returncode == 0, forced.stdout[-200:])
        backups = list((prefix / "commands").glob("prompt.md.replaced-*"))
        check("the original was copied aside", backups, list((prefix / "commands").iterdir()))
        check("and the copy is the original",
              backups and backups[0].read_text() == original, backups)
        check("the installed copy is ours", "seven slots" in mine.read_text())

        again = run(prefix=prefix, bindir=bindir)
        check("re-installing over our own files is not a conflict", again.returncode == 0,
              again.stderr[:200])
        check("a manifest records what was installed",
              (prefix / ".prompt-system-manifest").exists())

        print("\nuninstall removes only its own, unmodified files")
        stranger = prefix / "commands" / "prompt-audit.md"
        stranger.write_text("a file the owner replaced after installation\n")
        edited = prefix / "agents" / "prompt-critic.md"
        edited.write_text(edited.read_text() + "\nmy own note\n")
        foreign = prefix / "agents" / "unrelated.md"
        foreign.write_text("nothing to do with this repository\n")

        removed = run("--uninstall", prefix=prefix, bindir=bindir)
        check("uninstall exits 0", removed.returncode == 0, removed.stdout[-200:])
        check("a replaced file is kept", stranger.exists() and "owner replaced" in stranger.read_text())
        check("an edited file is kept", edited.exists() and "my own note" in edited.read_text())
        check("an unrelated file is untouched", foreign.exists())
        check("our own unmodified files are gone",
              not (prefix / "tools" / "prompt_forge.py").exists())
        check("the manifest is gone", not (prefix / ".prompt-system-manifest").exists())
        check("and it reports what it kept", "left alone" in removed.stdout, removed.stdout[-160:])

    print("\nevery target is guarded, not only the ones anyone thought of")
    # The list below is enumerated, so it can fall behind the installer. This
    # asserts it has not: the previous loop guarded the files it was looking at,
    # left the shims unguarded, and shipped a test suite that agreed with it.
    script = INSTALLER.read_text()
    declared = re.search(r"TARGETS=\((.*?)\n\)", script, re.S)
    target_count = len([l for l in declared.group(1).splitlines() if l.strip()]) if declared else -1
    targets = [
        "commands/prompt.md", "commands/prompt-audit.md", "commands/prompt-habits.md",
        "agents/prompt-critic.md", "skills/prompt-forge/SKILL.md",
        "tools/prompt_forge.py", "tools/prompt_habits.py", "tools/learn_rule.py",
        "tools/check_output.py", "tools/_phrases.py", "tools/_slots.py",
    ]
    shims = ["prompt-forge", "prompt-habits", "learn-rule", "check-output"]
    check("the test list covers every declared target",
          target_count == len(targets) + len(shims),
          f"installer declares {target_count}, this test covers {len(targets) + len(shims)}")
    for rel in targets + shims:
        with tempfile.TemporaryDirectory() as tmp:
            prefix, bindir = Path(tmp) / "claude", Path(tmp) / "bin"
            is_shim = rel in shims
            target = (bindir / rel) if is_shim else (prefix / rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            mine = f"the owner's own {rel}\n"
            target.write_text(mine)
            r = run(prefix=prefix, bindir=bindir)
            check(f"refuses to clobber {rel}",
                  r.returncode == 1 and target.read_text() == mine,
                  f"exit={r.returncode} content_changed={target.read_text() != mine}")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
