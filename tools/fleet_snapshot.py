#!/usr/bin/env python3
"""Regenerate the fleet roster in FLEET.md from live git refs.

A hand-written roster of a fleet this size is stale the moment it is written —
it went from 4 sessions to 14 in under an hour. This reads the refs that
actually exist, writes the raw capture to provenance/raw/, appends a source
entry for it, and rewrites the block in FLEET.md between the FLEET markers so
every generated line carries a tag that resolves.

Branches are the ground truth this session can reach. Session titles and status
lines come from an API that reports what each session says about itself; refs
report what it has actually done. This tool reads refs only.

For each branch other than the current one it also lists the files it shares
with the current branch — with unrelated root histories, those are the paths
that will conflict on merge.

Usage
  python3 tools/fleet_snapshot.py [--repo PATH] [--write]
Exit
  0 clean · 1 could not read a repository · 2 could not run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FLEET = REPO / "FLEET.md"
LEDGER = REPO / "provenance" / "sources.yaml"
RAW = REPO / "provenance" / "raw"
BEGIN, END = "<!-- FLEET:BEGIN -->", "<!-- FLEET:END -->"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {repo}: {result.stderr.strip()}")
    return result.stdout.strip()


def current_branch(repo: Path) -> str:
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def branches(repo: Path) -> list[tuple[str, str, str]]:
    git(repo, "fetch", "--all", "--prune")
    raw = git(
        repo, "for-each-ref", "--sort=-committerdate",
        "--format=%(refname:short)\t%(committerdate:iso-strict)\t%(subject)",
        "refs/remotes/origin",
    )
    rows = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and not parts[0].endswith("/HEAD"):
            rows.append((parts[0].removeprefix("origin/"), parts[1], parts[2]))
    return rows


def files_on(repo: Path, ref: str) -> set[str]:
    return set(git(repo, "ls-tree", "-r", "--name-only", f"origin/{ref}").splitlines())


def render(repo: Path, label: str, mine: str) -> tuple[str, str]:
    """Return (markdown block, raw capture) for one repository."""
    rows = branches(repo)
    my_files = files_on(repo, mine) if any(b == mine for b, _, _ in rows) else set()

    lines = [f"### `{label}`", "", "| Branch | Last commit | Subject |", "|---|---|---|"]
    raw = [f"# {label}: git for-each-ref refs/remotes/origin"]
    for branch, when, subject in rows:
        marker = " ←" if branch == mine else ""
        subject = subject.replace("|", "\\|")
        lines.append(f"| `{branch}`{marker} | {when} | {subject} |")
        raw.append(f"{branch}\t{when}\t{subject}")

    overlaps = []
    for branch, _, _ in rows:
        if branch == mine or not my_files:
            continue
        shared = sorted(my_files & files_on(repo, branch))
        if shared:
            overlaps.append((branch, shared))
            raw.append(f"# overlap {mine} ^ {branch}: {', '.join(shared)}")

    lines.append("")
    if not my_files:
        lines.append(f"This repository has no `{mine}` branch to compare against.")
    elif overlaps:
        lines.append("Paths written independently on two branches, which conflict on merge:")
        lines.append("")
        for branch, shared in overlaps:
            lines.append(f"- `{branch}` — " + ", ".join(f"`{f}`" for f in shared))
    else:
        lines.append("No other branch shares a file path with this one.")
    lines.append("")
    return "\n".join(lines), "\n".join(raw)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", action="append", default=None,
                        help="repository to include (repeatable); defaults to this one and a sibling clone")
    parser.add_argument("--write", action="store_true",
                        help="rewrite the FLEET.md block and append a source entry")
    args = parser.parse_args(argv[1:])

    repos = [Path(r).expanduser().resolve() for r in args.repo] if args.repo else [
        p for p in (REPO, REPO.parent / "claude-ai") if (p / ".git").exists()
    ]
    if not repos:
        print("fleet_snapshot: no git repositories to read", file=sys.stderr)
        return 2

    mine = current_branch(REPO)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    blocks, raws = [], []
    for repo in repos:
        try:
            block, raw = render(repo, repo.name, mine)
        except RuntimeError as exc:
            print(f"fleet_snapshot: {exc}", file=sys.stderr)
            return 1
        blocks.append(block)
        raws.append(raw)

    source_id = "FLEET-REFS-" + stamp.replace(":", "").replace("-", "")[:15]
    body = (
        f"> Generated by `tools/fleet_snapshot.py` at {stamp} from git refs, not\n"
        f"> from session titles. Re-run it rather than editing this block by hand.\n\n"
        + "\n".join(blocks)
        + f"\nRoster read from live refs at {stamp}. [src:{source_id}]\n"
    )

    if not args.write:
        print(body)
        print(f"(dry run — pass --write to update FLEET.md and add source {source_id})")
        return 0

    RAW.mkdir(parents=True, exist_ok=True)
    raw_path = RAW / f"fleet-refs-{stamp.replace(':', '')}.txt"
    raw_path.write_text("\n\n".join(raws) + "\n")

    with LEDGER.open("a") as handle:
        handle.write(
            f"\n  - id: {source_id}\n"
            f"    kind: repo_state\n"
            f'    collected_at: "{stamp}"\n'
            f'    method: "git fetch --all --prune; git for-each-ref refs/remotes/origin;'
            f' git ls-tree -r --name-only per branch"\n'
            f"    evidence: {raw_path.relative_to(REPO)}\n"
        )

    text = FLEET.read_text()
    if BEGIN not in text or END not in text:
        print(f"fleet_snapshot: FLEET.md has no {BEGIN} / {END} markers", file=sys.stderr)
        return 1
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    FLEET.write_text(f"{head}{BEGIN}\n{body}{END}{tail}")

    print(f"fleet_snapshot: FLEET.md updated, evidence at {raw_path.relative_to(REPO)}, "
          f"source {source_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
