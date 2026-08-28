#!/usr/bin/env python3
"""Structural checks on the doctrine layer itself.

The provenance verifier checks what documents *claim*. Nothing checked that the
documents, skills, agents and commands still *exist* and still parse — so
deleting a file named in CLAUDE.md, or breaking a skill's frontmatter, left the
whole suite green. That gap was found by pointing a verification subagent at
the repository and asking it what the checks did not cover.

Every case here fails loudly when a piece of the layer goes missing or
malformed.

Run: python3 tests/test_layer_integrity.py
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}" + (f" - {detail}" if detail else ""))
        FAILURES.append(name)


# Paths that look like references but are not files in this repository:
# other people's repositories, URLs, and locations described rather than used.
EXTERNAL = re.compile(
    r"^(https?:|claude\.ai|code\.claude\.com|docs\.claude\.com|~/|/etc/|/Library/|C:)"
    r"|^[\w.-]+/[\w.-]+$"          # owner/repo
    r"|^_drafts/|^_posts/"          # paths inside Cherny's repository
)

# Referenced in prose as where a thing *would* live, not as a file that exists.
DESCRIBED_NOT_REQUIRED = {
    ".mcp.json",   # named as Cherny's shared config, not a file of this repo
    "archive/",
    ".claude/rules/",
    ".claude/settings.local.json",
    "CLAUDE.local.md",
    "provenance/raw/",
    ".claude/commands/",
    ".claude/agents/",
    ".claude/skills/",
    "src/",
    "tools/",
    "tests/",
    "prompts/",
}

BACKTICKED = re.compile(r"`([^`\s]+\.(?:md|py|sh|json|yaml|yml))`")


def referenced_paths(text: str) -> set[str]:
    """Backticked things that look like files in this repository."""
    out = set()
    for raw in BACKTICKED.findall(text):
        if EXTERNAL.search(raw) or raw in DESCRIBED_NOT_REQUIRED or "*" in raw:
            continue
        out.add(raw)
    return out


def _on_a_remote_branch(ref: str) -> bool:
    """True if the path exists on some fetched branch of this repository.

    A fleet document legitimately talks about files that live on a sibling's
    branch and not in this checkout. Those are real, checkable references — so
    they are resolved against the remote refs rather than waved through by an
    exception list, which would stop the check noticing a genuine typo.
    """
    try:
        branches = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        ).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return False
    for br in branches:
        probe = subprocess.run(
            ["git", "cat-file", "-e", f"{br}:{ref}"],
            cwd=REPO, capture_output=True, timeout=30,
        )
        if probe.returncode == 0:
            return True
    return False


def unresolved(refs: set[str], src: Path) -> list[str]:
    """A reference resolves if it names a file from the repo root, from the
    directory of the document that mentions it — `base-operator.md` inside
    prompts/README.md means prompts/base-operator.md — or, for a document about
    the fleet, from any fetched branch of this repository."""
    bad = []
    for ref in refs:
        if (REPO / ref).exists() or (src.parent / ref).exists():
            continue
        if _on_a_remote_branch(ref):
            print(f"       (note: {ref} is absent here but present on a sibling branch)")
            continue
        bad.append(ref)
    return sorted(bad)


def frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return meta if isinstance(meta, dict) else None


print("referenced files exist")
DOCS = [
    "CLAUDE.md",
    "FLEET.md",
    "docs/workflows.md",
    "docs/cherny-practice.md",
    "prompts/README.md",
    "prompts/cherny-operator.md",
    ".claude/skills/cherny/SKILL.md",
    ".claude/skills/ooda/SKILL.md",
]
for rel in DOCS:
    src = REPO / rel
    if not src.exists():
        check(f"{rel} exists", False, "the document itself is missing")
        continue
    missing = unresolved(referenced_paths(src.read_text()), src)
    check(f"{rel} references only files that exist", not missing, f"missing: {missing}")

print()
print("subagents are well formed")
for agent in sorted((REPO / ".claude" / "agents").glob("*.md")):
    meta = frontmatter(agent)
    rel = agent.relative_to(REPO)
    if meta is None:
        check(f"{rel} has parseable frontmatter", False, "absent or invalid YAML")
        continue
    check(f"{rel} declares name and description", {"name", "description"} <= set(meta))
    check(f"{rel} name matches its filename", meta.get("name") == agent.stem, str(meta.get("name")))

print()
print("skills are well formed")
for skill in sorted((REPO / ".claude" / "skills").glob("*/SKILL.md")):
    meta = frontmatter(skill)
    rel = skill.relative_to(REPO)
    if meta is None:
        check(f"{rel} has parseable frontmatter", False, "absent or invalid YAML")
        continue
    check(f"{rel} declares a description", bool(meta.get("description")))
    if "name" in meta:
        check(f"{rel} name matches its directory", meta["name"] == skill.parent.name, str(meta["name"]))
    # The docs put the ceiling at 500 lines; past that a skill is reference
    # material that should be split, not a procedure.
    lines = len(skill.read_text().splitlines())
    check(f"{rel} is under 500 lines", lines < 500, f"{lines} lines")

print()
print("slash commands are well formed")
for cmd in sorted((REPO / ".claude" / "commands").glob("*.md")):
    meta = frontmatter(cmd)
    rel = cmd.relative_to(REPO)
    if meta is None:
        check(f"{rel} has parseable frontmatter", False, "absent or invalid YAML")
        continue
    check(f"{rel} declares a description", bool(meta.get("description")))

print()
print("every command named in CLAUDE.md is defined")
claude_md = (REPO / "CLAUDE.md").read_text()
table = re.findall(r"^\| `/([a-z-]+)", claude_md, re.M)
for name in sorted(set(table)):
    defined = (REPO / ".claude" / "commands" / f"{name}.md").exists() or (
        REPO / ".claude" / "skills" / name / "SKILL.md"
    ).exists()
    check(f"/{name} is defined", defined, "named in CLAUDE.md but no file defines it")

print()
print("every subagent named in CLAUDE.md exists")
for name in sorted(set(re.findall(r"`(observer|fact-checker|verifier)`", claude_md))):
    check(f"{name} agent exists", (REPO / ".claude" / "agents" / f"{name}.md").exists())

print()
print("the ledger's file evidence resolves")
ledger = yaml.safe_load((REPO / "provenance" / "sources.yaml").read_text()) or {}
for entry in ledger.get("sources") or []:
    ev = entry.get("evidence")
    if isinstance(ev, str) and ev.startswith("provenance/"):
        check(f"{entry['id']} evidence exists", (REPO / ev.strip()).exists(), ev)

print()
if FAILURES:
    print(f"{len(FAILURES)} case(s) failed")
    sys.exit(1)
print("all cases passed")
