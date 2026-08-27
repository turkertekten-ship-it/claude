"""Ingest and lint Agent Skills.

A skill is only useful if the agent *reaches for it*, and that decision is made
almost entirely from two frontmatter fields the author rarely tests: `name` and
`description`. Everything else in a SKILL.md is invisible until routing has
already succeeded. So this module does two jobs:

  - it turns skills into documents, so a corpus can answer "do I already have
    something for this?" before a new skill gets written; and
  - it lints them against the published authoring constraints, so a skill that
    can never load — a `name` over the limit, a reserved word, a description
    written in the first person — fails a check instead of silently never
    triggering.

The lint encodes constraints that are validated by the runtime, not opinions:
a `name` outside its character set is a load error, not a style preference.
Rules that are guidance rather than validation are reported at `warn`, and the
docstring of each check says which it is.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.logging import get_logger
from oodarag.util.text import clean

log = get_logger("ingest.skills")

# Validation constraints on SKILL.md frontmatter.
NAME_MAX = 64
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
RESERVED_NAME_WORDS = ("anthropic", "claude")
DESCRIPTION_MAX = 1024

# Authoring guidance rather than validation: exceeded bodies still load.
BODY_MAX_LINES = 500
REFERENCE_TOC_LINES = 100

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
XML_TAG = re.compile(r"<[A-Za-z/][^>]*>")

FIRST_PERSON = re.compile(
    r"\b(I can|I will|I help|I'll|you can use this|use me to|this lets you)\b", re.I
)

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


@dataclass(slots=True)
class SkillFinding:
    severity: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity.upper():<5} {self.code}: {self.message}"


@dataclass(slots=True)
class Skill:
    """One parsed SKILL.md, plus where it came from."""

    name: str
    description: str
    path: Path
    body: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    scope: str = "project"

    @property
    def directory(self) -> Path:
        return self.path.parent

    @property
    def command(self) -> str:
        """The slash command that invokes it.

        For personal and project skills the command comes from the *directory*
        name, not from the frontmatter `name`; a mismatch between the two is a
        common reason an author's `/foo` does not exist.
        """
        return f"/{self.directory.name}"

    @property
    def body_lines(self) -> int:
        return len(self.body.splitlines())

    def references(self) -> list[str]:
        """Relative markdown links from the body — the progressive-disclosure edges."""
        out = []
        for target in MD_LINK.findall(self.body):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            out.append(target.split("#")[0])
        return out


def parse_skill(path: Path, scope: str = "project") -> Skill | None:
    """Read a SKILL.md. Returns None only when the file cannot be read at all."""
    try:
        raw = path.read_text("utf-8", errors="replace")
    except OSError as e:
        log.warn("skill unreadable", path=str(path), err=str(e))
        return None

    front: dict[str, Any] = {}
    body = raw
    if m := FRONT_MATTER.match(raw):
        body = raw[m.end() :]
        front = _parse_frontmatter(m.group(1))
    return Skill(
        name=str(front.get("name", "") or ""),
        description=str(front.get("description", "") or ""),
        path=path,
        body=body,
        frontmatter=front,
        scope=scope,
    )


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the frontmatter block.

    PyYAML is used when present because a description containing a colon is
    common and needs real quoting rules. The hand-rolled fallback keeps the
    module usable in the zero-dependency configuration the package promises.
    """
    try:
        import yaml

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        pass
    except Exception as e:  # malformed YAML is a finding, not a crash
        log.warn("frontmatter did not parse", err=str(e)[:200])
        return {}

    out: dict[str, Any] = {}
    key = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line[0] not in " \t" and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            out[key] = value.strip().strip("'\"")
        elif key:  # a folded continuation line
            out[key] = f"{out.get(key, '')} {line.strip()}".strip()
    return out


def lint_skill(skill: Skill) -> list[SkillFinding]:
    """Check one skill against the authoring constraints.

    `error` marks something the runtime itself rejects or that stops the skill
    from ever being selected. `warn` marks published guidance. `info` marks a
    smell worth a second look.
    """
    findings: list[SkillFinding] = []
    add = lambda sev, code, msg: findings.append(SkillFinding(sev, code, msg))  # noqa: E731

    # --- name -------------------------------------------------------------
    if not skill.name:
        add("error", "name-missing", "frontmatter has no `name` field")
    else:
        if len(skill.name) > NAME_MAX:
            add("error", "name-too-long",
                f"`name` is {len(skill.name)} characters, over the {NAME_MAX} limit")
        if not NAME_PATTERN.match(skill.name):
            add("error", "name-charset",
                f"`name` must be lowercase letters, numbers and hyphens only: {skill.name!r}")
        for word in RESERVED_NAME_WORDS:
            if word in skill.name.lower():
                add("error", "name-reserved",
                    f"`name` contains the reserved word {word!r}")
        if XML_TAG.search(skill.name):
            add("error", "name-xml", "`name` may not contain XML tags")
        if skill.scope in ("project", "personal") and skill.name != skill.directory.name:
            add("info", "name-not-command",
                f"`name` is {skill.name!r} but the command comes from the directory, "
                f"so this is {skill.command}")

    # --- description ------------------------------------------------------
    if not skill.description.strip():
        add("error", "description-missing",
            "frontmatter has no `description`; without it the skill is never routed to")
    else:
        if len(skill.description) > DESCRIPTION_MAX:
            add("error", "description-too-long",
                f"`description` is {len(skill.description)} characters, "
                f"over the {DESCRIPTION_MAX} limit")
        if XML_TAG.search(skill.description):
            add("error", "description-xml", "`description` may not contain XML tags")
        if FIRST_PERSON.search(skill.description):
            add("warn", "description-person",
                "`description` is written in the first or second person; it is injected "
                "into the system prompt and should be third person")
        if not re.search(r"\b(use (this )?when|when the user|triggers? on|use for)\b",
                         skill.description, re.I):
            add("warn", "description-no-trigger",
                "`description` does not say *when* to use the skill, only what it does")

    # --- body -------------------------------------------------------------
    if skill.body_lines > BODY_MAX_LINES:
        add("warn", "body-too-long",
            f"body is {skill.body_lines} lines, over the {BODY_MAX_LINES}-line guidance; "
            "split it into referenced files")
    if not skill.body.strip():
        add("error", "body-empty", "the skill has frontmatter but no instructions")

    # --- references -------------------------------------------------------
    for target in skill.references():
        resolved = (skill.directory / target).resolve()
        if not resolved.exists():
            add("error", "reference-missing", f"body links to {target!r}, which does not exist")
            continue
        if resolved.suffix.lower() == ".md":
            findings.extend(_lint_reference(skill, resolved, target))

    if "\\" in "".join(skill.references()):
        add("error", "windows-path", "references use backslashes; paths must use forward slashes")

    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))


def _lint_reference(skill: Skill, resolved: Path, target: str) -> list[SkillFinding]:
    """Check a referenced file for depth and for a table of contents.

    A reference that itself references another file is the documented cause of
    partial reads: the second hop tends to be previewed rather than read.
    """
    out: list[SkillFinding] = []
    try:
        text = resolved.read_text("utf-8", errors="replace")
    except OSError:
        return out
    nested = [
        t for t in MD_LINK.findall(text)
        if not t.startswith(("http://", "https://", "#", "mailto:"))
        and t.lower().endswith(".md")
    ]
    if nested:
        out.append(SkillFinding(
            "warn", "reference-depth",
            f"{target} links onward to {nested[0]!r}; keep references one level deep",
        ))
    lines = text.splitlines()
    if len(lines) > REFERENCE_TOC_LINES and not re.search(
        r"^##?\s*(contents|table of contents)", text, re.I | re.M
    ):
        out.append(SkillFinding(
            "warn", "reference-no-toc",
            f"{target} is {len(lines)} lines with no table of contents",
        ))
    return out


def discover_skills(roots: list[str | Path]) -> list[Skill]:
    """Find every SKILL.md under the given roots.

    Both layouts are accepted: `<root>/<name>/SKILL.md` (a skills directory)
    and a nested `.claude/skills/<name>/SKILL.md` anywhere below the root.
    """
    found: dict[Path, Skill] = {}
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        if base.is_file() and base.name == "SKILL.md":
            candidates = [base]
        else:
            candidates = sorted(base.rglob("SKILL.md"))
        for path in candidates:
            resolved = path.resolve()
            if resolved in found:
                continue  # a symlinked skill reachable from two roots loads once
            scope = _scope_for(resolved)
            if skill := parse_skill(resolved, scope):
                found[resolved] = skill
    return list(found.values())


def _scope_for(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    if "plugins" in parts:
        return "plugin"
    if "synced" in parts:
        return "synced"
    home = str(Path.home()).lower()
    if str(path).lower().startswith(f"{home}/.claude/skills"):
        return "personal"
    return "project"


class SkillConnector(Connector):
    """Index the skills available to a session, lint findings included.

    The lint result is carried in the document metadata rather than only
    printed, so "which of my skills can never trigger?" is a retrieval query
    rather than a separate report nobody runs.
    """

    authority = 1.2  # a skill in the repo is a first-party instruction

    def __init__(self, roots: list[str | Path], *, key: str = "skills") -> None:
        self.roots = roots
        self.key = key

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        for skill in discover_skills(self.roots):
            findings = lint_skill(skill)
            errors = [str(f) for f in findings if f.severity == "error"]
            warnings = [str(f) for f in findings if f.severity == "warn"]
            body = "\n".join([
                f"# Skill: {skill.name or skill.directory.name}",
                f"Command: {skill.command}",
                f"Scope: {skill.scope}",
                "",
                "## Description",
                clean(skill.description) or "(none)",
                "",
                "## Instructions",
                skill.body.strip(),
            ])
            yield RawDocument(
                source_system="skill",
                external_id=str(skill.path),
                uri=skill.path.as_uri(),
                title=skill.name or skill.directory.name,
                text=body,
                metadata={
                    "kind": "skill",
                    "scope": skill.scope,
                    "command": skill.command,
                    "body_lines": skill.body_lines,
                    "references": skill.references(),
                    "lint_errors": errors,
                    "lint_warnings": warnings,
                    "loadable": not errors,
                },
            )
