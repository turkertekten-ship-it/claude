#!/usr/bin/env python3
"""Install this repository's vendored skills into ~/.claude/skills/.

Why this exists
  The owner's most-repeated request is that rules apply across all prompts,
  all chats and all terminals. A skill committed to `.claude/skills/` in this
  repository reaches sessions opened *in this repository* and nothing else. A
  skill in `~/.claude/skills/` is picked up by every Claude Code session on the
  machine, whatever directory it starts in.

  `tools/install_user_scope.py` on a sibling branch does this for the doctrine
  — the OODA skill, the subagents, the commands. This does it for the skills
  vendored from outside the account, which that installer does not carry. The
  two are complementary and neither is a substitute for the other.

What it deliberately does not do
  It does not reach claude.ai web conversations. Those do not read
  `~/.claude/`, and no script here can change that; that half needs the skill
  pasted into a Project's custom instructions by hand.

  It also does not survive this container. `~/.claude` is not persistent
  storage, so a fresh session starts without it and must run this again. That
  is why this ships as a committed script rather than as a one-time action.

Safety
  Dry run is the default; nothing is written without `--apply`. Each installed
  skill directory is recorded in a manifest, and `--uninstall` removes only
  what the manifest lists — never a directory this script did not create.
  A skill directory the owner wrote by hand is never overwritten unless
  `--force` is passed, and the reason is reported rather than silently skipped.

Usage
  python3 tools/install_skills_user_scope.py              # show the plan
  python3 tools/install_skills_user_scope.py --apply      # do it
  python3 tools/install_skills_user_scope.py --uninstall --apply
Exit
  0 clean · 1 nothing installed / conflicts found · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / ".claude" / "skills"
MANIFEST_NAME = ".installed-by-oodarag.json"

# Skills that belong to this repository's doctrine and are installed by the
# sibling doctrine installer instead. Listing them here keeps the two scripts
# from fighting over the same directory.
DOCTRINE_SKILLS = {"ooda"}


def user_skills_dir(home: Path) -> Path:
    return home / ".claude" / "skills"


def discover(source: Path) -> list[Path]:
    """Skill directories in this repository, excluding doctrine-owned ones."""
    if not source.is_dir():
        return []
    out = []
    for child in sorted(source.iterdir()):
        if not child.is_dir() or child.name in DOCTRINE_SKILLS:
            continue
        if not (child / "SKILL.md").is_file():
            continue
        out.append(child)
    return out


def read_manifest(dest: Path) -> dict:
    path = dest / MANIFEST_NAME
    if not path.is_file():
        return {"installed": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A corrupt manifest must not authorise deleting anything.
        return {"installed": []}
    if not isinstance(data.get("installed"), list):
        return {"installed": []}
    return data


def write_manifest(dest: Path, names: list[str]) -> None:
    payload = {
        "installed": sorted(names),
        "note": (
            "Written by tools/install_skills_user_scope.py. --uninstall removes "
            "only the directories listed here."
        ),
    }
    (dest / MANIFEST_NAME).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def plan_install(skills: list[Path], dest: Path, force: bool) -> tuple[list, list]:
    """Return (to_install, conflicts). A conflict is a directory we did not install."""
    known = set(read_manifest(dest)["installed"])
    to_install, conflicts = [], []
    for skill in skills:
        target = dest / skill.name
        if target.exists() and skill.name not in known and not force:
            conflicts.append(skill.name)
        else:
            to_install.append(skill)
    return to_install, conflicts


def do_install(skills: list[Path], dest: Path, apply: bool, force: bool) -> int:
    to_install, conflicts = plan_install(skills, dest, force)

    for name in conflicts:
        print(f"  CONFLICT  {name} exists at user scope and was not installed by this script")
    for skill in to_install:
        verb = "install" if apply else "would install"
        print(f"  {verb:>14}  {skill.name}")

    if not apply:
        print()
        print(f"dry run — nothing written. Re-run with --apply to install into {dest}")
        if conflicts:
            print("  conflicts above would be skipped; --force overwrites them")
        return 0 if to_install or not conflicts else 1

    if not to_install:
        print()
        print("nothing to install")
        return 1 if conflicts else 0

    dest.mkdir(parents=True, exist_ok=True)
    installed = set(read_manifest(dest)["installed"])
    for skill in to_install:
        target = dest / skill.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill, target)
        installed.add(skill.name)
    write_manifest(dest, sorted(installed))

    print()
    print(f"installed {len(to_install)} skill(s) into {dest}")
    print("  these reach every Claude Code session on this machine")
    print("  they do NOT reach claude.ai web conversations, which do not read ~/.claude/")
    print("  ~/.claude is not persistent: a fresh container must run this again")
    return 1 if conflicts else 0


def do_uninstall(dest: Path, apply: bool) -> int:
    names = read_manifest(dest)["installed"]
    if not names:
        print("nothing recorded as installed by this script")
        return 1
    for name in names:
        target = dest / name
        verb = "remove" if apply else "would remove"
        state = "" if target.exists() else "  (already gone)"
        print(f"  {verb:>14}  {name}{state}")
    if not apply:
        print()
        print("dry run — nothing removed. Re-run with --apply")
        return 0
    for name in names:
        target = dest / name
        if target.exists():
            shutil.rmtree(target)
    manifest = dest / MANIFEST_NAME
    if manifest.exists():
        manifest.unlink()
    print()
    print(f"removed {len(names)} skill(s) from {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry run)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite a user-scope skill this script did not install")
    ap.add_argument("--uninstall", action="store_true",
                    help="remove only what the manifest records")
    ap.add_argument("--home", default="", help="override HOME (for tests)")
    args = ap.parse_args(argv)

    home = Path(args.home) if args.home else Path.home()
    dest = user_skills_dir(home)

    if args.uninstall:
        return do_uninstall(dest, args.apply)

    skills = discover(SOURCE)
    if not skills:
        print(f"install_skills_user_scope: no skills found under {SOURCE}", file=sys.stderr)
        return 2
    print(f"source: {SOURCE}")
    print(f"target: {dest}")
    print()
    return do_install(skills, dest, args.apply, args.force)


if __name__ == "__main__":
    sys.exit(main())
