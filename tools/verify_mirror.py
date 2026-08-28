#!/usr/bin/env python3
"""Check that the two repositories carry the same doctrine and tooling.

The owner chose to mirror both repositories rather than keep a single home for
the rules, so that a session cloning either one is fully equipped. That choice
has a known cost: two copies drift, and drifted rules are worse than one copy
plus a pointer, because both look authoritative.

This makes the drift visible. It compares content hashes of the mirrored paths
and reports what differs, what is missing on each side, and what is extra.

Excluded deliberately:
  - `.git`, caches, and build output, which are not content.
  - `archive/`, which holds the owner's conversation exports and is
    git-ignored — it is per-checkout data, not doctrine.
`provenance/raw/` **is** mirrored, despite holding captures made in one
container. The first draft of this excluded it, on the reasoning that copying a
capture would assert the other repository had made the same observation. That
was wrong twice over: a capture is a record of when and how something was
observed, and the ledger already says so, and — decisively — `sources.yaml`
cites those files by path, so a repository holding the ledger without the
captures fails its own provenance check on every entry.

Usage
  python3 tools/verify_mirror.py [other_repo]   # defaults to ../claude-ai
Exit
  0 in sync · 1 drift found · 2 could not run
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OTHER = REPO.parent / "claude-ai"

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache",
    ".oodarag", ".data", "build", "dist", "htmlcov", "archive",
}

#: Files that are per-checkout state rather than content.
SKIP_NAMES = {"index.db", ".DS_Store"}

#: Only these trees are mirrored. Everything else is free to differ.
MIRRORED = (
    "CLAUDE.md", "FLEET.md", "README.md", "Makefile", "pyproject.toml",
    ".gitignore", "src", "tests", "tools", "docs", "prompts", "provenance",
    ".claude", "evals", "corpus",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def collect(root: Path) -> dict[str, str]:
    """Content hashes of every mirrored file, keyed by repo-relative path."""
    out: dict[str, str] = {}
    for name in MIRRORED:
        target = root / name
        if not target.exists():
            continue
        candidates = [target] if target.is_file() else sorted(target.rglob("*"))
        for path in candidates:
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name in SKIP_NAMES:
                continue
            rel = path.relative_to(root).as_posix()
            try:
                out[rel] = digest(path)
            except OSError:
                continue
    return out


def main(argv: list[str]) -> int:
    other = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_OTHER
    if not other.is_dir():
        print(f"verify_mirror: no repository at {other}", file=sys.stderr)
        return 2

    here, there = collect(REPO), collect(other)
    missing = sorted(set(here) - set(there))
    extra = sorted(set(there) - set(here))
    differing = sorted(p for p in set(here) & set(there) if here[p] != there[p])

    for path in missing:
        print(f"  missing in {other.name}: {path}")
    for path in extra:
        print(f"  only in {other.name}:   {path}")
    for path in differing:
        print(f"  differs:               {path}")

    total = len(missing) + len(extra) + len(differing)
    if total == 0:
        print(f"verify_mirror: OK — {len(here)} mirrored file(s) identical in both repositories")
        return 0
    print(f"\nverify_mirror: {total} path(s) drifted "
          f"({len(missing)} missing, {len(extra)} extra, {len(differing)} differing)",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
