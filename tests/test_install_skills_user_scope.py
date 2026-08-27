#!/usr/bin/env python3
"""Tests for tools/install_skills_user_scope.py.

The failure that would actually hurt is this script deleting or overwriting a
skill the owner wrote by hand at user scope. Every destructive path is driven
here against a temporary HOME, and the cases that must be refused are asserted
as refusals rather than as absences.

Nothing here touches the real ~/.claude.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import install_skills_user_scope as inst  # noqa: E402

CASES = []


def case(name):
    def wrap(fn):
        CASES.append((name, fn))
        return fn
    return wrap


def make_skill(root: Path, name: str, body: str = "# skill\n") -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    return d


def sandbox():
    """A temp dir with a fake repo skills source and a fake HOME."""
    tmp = Path(tempfile.mkdtemp())
    src = tmp / "repo" / ".claude" / "skills"
    src.mkdir(parents=True)
    make_skill(src, "alpha")
    make_skill(src, "beta")
    make_skill(src, "ooda")  # doctrine-owned; must be excluded
    home = tmp / "home"
    (home / ".claude" / "skills").mkdir(parents=True)
    return tmp, src, home


def run(src, home, argv):
    """Invoke main() with SOURCE patched to the sandbox."""
    original = inst.SOURCE
    inst.SOURCE = src
    try:
        return inst.main(argv + ["--home", str(home)])
    finally:
        inst.SOURCE = original


@case("doctrine-owned skills are not installed by this script")
def t_excl():
    tmp, src, home = sandbox()
    try:
        names = [p.name for p in inst.discover(src)]
        assert names == ["alpha", "beta"], names
    finally:
        shutil.rmtree(tmp)


@case("a directory without SKILL.md is not a skill")
def t_notskill():
    tmp, src, home = sandbox()
    try:
        (src / "junk").mkdir()
        assert "junk" not in [p.name for p in inst.discover(src)]
    finally:
        shutil.rmtree(tmp)


@case("dry run writes nothing at all")
def t_dry():
    tmp, src, home = sandbox()
    try:
        rc = run(src, home, [])
        assert rc == 0
        assert list((home / ".claude" / "skills").iterdir()) == []
    finally:
        shutil.rmtree(tmp)


@case("--apply installs the skills and records a manifest")
def t_apply():
    tmp, src, home = sandbox()
    try:
        rc = run(src, home, ["--apply"])
        dest = home / ".claude" / "skills"
        assert rc == 0
        assert (dest / "alpha" / "SKILL.md").is_file()
        assert (dest / "beta" / "SKILL.md").is_file()
        assert not (dest / "ooda").exists(), "doctrine skill was installed"
        man = json.loads((dest / inst.MANIFEST_NAME).read_text())
        assert man["installed"] == ["alpha", "beta"], man
    finally:
        shutil.rmtree(tmp)


@case("re-running is idempotent and does not duplicate the manifest")
def t_idem():
    tmp, src, home = sandbox()
    try:
        run(src, home, ["--apply"])
        run(src, home, ["--apply"])
        dest = home / ".claude" / "skills"
        man = json.loads((dest / inst.MANIFEST_NAME).read_text())
        assert man["installed"] == ["alpha", "beta"], man
    finally:
        shutil.rmtree(tmp)


@case("a hand-written skill of the same name is refused, not overwritten")
def t_conflict():
    tmp, src, home = sandbox()
    try:
        dest = home / ".claude" / "skills"
        make_skill(dest, "alpha", "# THE OWNER WROTE THIS\n")
        rc = run(src, home, ["--apply"])
        assert rc == 1, "conflict did not set a non-zero exit"
        assert "OWNER WROTE" in (dest / "alpha" / "SKILL.md").read_text()
        assert (dest / "beta").exists(), "the non-conflicting skill was not installed"
    finally:
        shutil.rmtree(tmp)


@case("--force overwrites a conflicting skill, and only then")
def t_force():
    tmp, src, home = sandbox()
    try:
        dest = home / ".claude" / "skills"
        make_skill(dest, "alpha", "# THE OWNER WROTE THIS\n")
        run(src, home, ["--apply", "--force"])
        assert "OWNER WROTE" not in (dest / "alpha" / "SKILL.md").read_text()
    finally:
        shutil.rmtree(tmp)


@case("uninstall removes only what the manifest lists")
def t_uninstall():
    tmp, src, home = sandbox()
    try:
        dest = home / ".claude" / "skills"
        run(src, home, ["--apply"])
        make_skill(dest, "owners-own", "# not ours\n")
        rc = run(src, home, ["--uninstall", "--apply"])
        assert rc == 0
        assert not (dest / "alpha").exists()
        assert not (dest / "beta").exists()
        assert (dest / "owners-own" / "SKILL.md").is_file(), "removed a skill it did not install"
    finally:
        shutil.rmtree(tmp)


@case("uninstall dry run removes nothing")
def t_uninstall_dry():
    tmp, src, home = sandbox()
    try:
        dest = home / ".claude" / "skills"
        run(src, home, ["--apply"])
        run(src, home, ["--uninstall"])
        assert (dest / "alpha").exists(), "dry-run uninstall deleted a skill"
    finally:
        shutil.rmtree(tmp)


@case("a corrupt manifest authorises no deletion")
def t_corrupt():
    tmp, src, home = sandbox()
    try:
        dest = home / ".claude" / "skills"
        run(src, home, ["--apply"])
        (dest / inst.MANIFEST_NAME).write_text("{not json", encoding="utf-8")
        rc = run(src, home, ["--uninstall", "--apply"])
        assert rc == 1, "a corrupt manifest was treated as a delete list"
        assert (dest / "alpha").exists(), "deleted on the strength of an unreadable manifest"
    finally:
        shutil.rmtree(tmp)


@case("an empty source is reported as could-not-run, not as success")
def t_empty():
    tmp, src, home = sandbox()
    try:
        empty = tmp / "empty"
        empty.mkdir()
        rc = run(empty, home, ["--apply"])
        assert rc == 2, rc
    finally:
        shutil.rmtree(tmp)


def main() -> int:
    failed = 0
    for name, fn in CASES:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {name}\n       {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {name}\n       {type(exc).__name__}: {exc}")
        else:
            print(f"  ok   {name}")
    print()
    print("all cases passed" if not failed else f"{failed} case(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
