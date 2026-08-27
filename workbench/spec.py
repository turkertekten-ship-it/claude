"""Suite files: what to run, against what, and how to score it.

A suite is one YAML file holding three lists -- variants, cases, graders --
plus the defaults they inherit from. It is the unit that gets committed,
diffed and re-run, so the loader is strict: an unknown key is an error, not a
shrug. A typo in ``temprature`` that silently does nothing is worse than a
crash, because the run still produces numbers.

Shape::

    name: doctrine-adherence
    description: Does the operator prompt actually stop unsourced claims?

    defaults:
      model: claude-haiku-4-5
      effort: medium
      mode: text

    vars:                       # suite-wide, overridden per case
      repo: turkertekten-ship-it/claude

    variants:
      - id: with-doctrine
        system_file: prompts/base-operator.md
      - id: without-doctrine
        system: You are a helpful assistant.

    cases:
      - id: unsourced-claim
        vars: {topic: the repository layout}
        prompt: |
          State one fact about {{topic}} in {{repo}}.
        graders:
          - {type: regex, pattern: '\\[src:[A-Z0-9-]+\\]'}
          - {type: not_contains, value: 'as we discussed'}
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import SpecError

try:  # PyYAML is present in this environment, but the failure should be legible.
    import yaml
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SpecError(
        "PyYAML is required to read suite files: python3 -m pip install pyyaml"
    ) from exc


#: Modes a variant can run in.
#:
#: ``text``  - no tools, one turn. The prompt-engineering case: the output is
#:             the artifact, and graders read it directly.
#: ``agent`` - tools enabled, run inside a scratch directory seeded from a
#:             fixture. The artifact is the resulting *directory*, and graders
#:             run against it. This is the outcome-based mode, and it is the
#:             one thing a browser playground structurally cannot do.
MODES = ("text", "agent")

_VARIANT_KEYS = {
    "id", "system", "system_file", "model", "effort", "mode", "tools",
    "append_system", "json_schema", "vars", "prompt_prefix", "prompt_suffix",
    "max_budget_usd", "fixture", "setup", "note",
}
_CASE_KEYS = {
    "id", "prompt", "prompt_file", "vars", "graders", "weight", "note",
    "fixture", "skip",
}
_SUITE_KEYS = {
    "name", "description", "defaults", "vars", "variants", "cases",
    "graders", "judge", "blind", "repeats",
}
_DEFAULT_KEYS = {
    "model", "effort", "mode", "tools", "system", "system_file",
    "append_system", "json_schema", "max_budget_usd", "fixture",
}


def _reject_unknown(where: str, got: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(got) - allowed)
    if unknown:
        raise SpecError(
            f"{where}: unknown key(s) {', '.join(unknown)}. "
            f"Allowed: {', '.join(sorted(allowed))}."
        )


@dataclass(frozen=True)
class Grader:
    """One check. ``type`` selects the implementation in :mod:`workbench.graders`."""

    type: str
    config: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    #: A grader may be marked non-blocking: it is scored and reported but does
    #: not decide pass/fail. Useful for metrics you want tracked before you are
    #: willing to gate on them.
    advisory: bool = False

    @property
    def label(self) -> str:
        for key in ("name", "pattern", "value", "path", "command"):
            if key in self.config:
                return f"{self.type}({str(self.config[key])[:40]})"
        return self.type


@dataclass(frozen=True)
class Variant:
    """One configuration under test -- the thing whose effect we want to measure."""

    id: str
    system: str | None = None
    model: str | None = None
    effort: str | None = None
    mode: str = "text"
    tools: str | None = None
    append_system: str | None = None
    json_schema: dict[str, Any] | None = None
    vars: dict[str, Any] = field(default_factory=dict)
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    max_budget_usd: float | None = None
    fixture: str | None = None
    setup: list[str] = field(default_factory=list)
    note: str = ""


@dataclass(frozen=True)
class Case:
    """One input, plus the checks its output must survive."""

    id: str
    prompt: str
    vars: dict[str, Any] = field(default_factory=dict)
    graders: tuple[Grader, ...] = ()
    weight: float = 1.0
    fixture: str | None = None
    skip: str = ""
    note: str = ""


@dataclass(frozen=True)
class Suite:
    """A whole suite file, resolved and validated."""

    name: str
    description: str
    variants: tuple[Variant, ...]
    cases: tuple[Case, ...]
    vars: dict[str, Any] = field(default_factory=dict)
    judge: dict[str, Any] = field(default_factory=dict)
    blind: dict[str, Any] = field(default_factory=dict)
    repeats: int = 1
    path: Path | None = None

    def variant(self, variant_id: str) -> Variant:
        for v in self.variants:
            if v.id == variant_id:
                return v
        raise SpecError(f"no variant with id {variant_id!r}")

    def case(self, case_id: str) -> Case:
        for c in self.cases:
            if c.id == case_id:
                return c
        raise SpecError(f"no case with id {case_id!r}")


def _load_grader(raw: Any, where: str) -> Grader:
    if isinstance(raw, str):
        # Shorthand: `- json_valid` for a grader that needs no configuration.
        return Grader(type=raw)
    if not isinstance(raw, dict):
        raise SpecError(f"{where}: a grader must be a mapping or a bare type name")
    config = dict(raw)
    gtype = config.pop("type", None)
    if not gtype:
        raise SpecError(f"{where}: grader is missing `type`")
    weight = float(config.pop("weight", 1.0))
    advisory = bool(config.pop("advisory", False))
    return Grader(type=str(gtype), config=config, weight=weight, advisory=advisory)


def _read_file(base: Path, rel: str, where: str) -> str:
    candidate = (base / rel).resolve()
    if not candidate.is_file():
        raise SpecError(f"{where}: file not found: {rel} (looked in {base})")
    return candidate.read_text(encoding="utf-8")


def load_suite(path: str | Path) -> Suite:
    """Read, validate and resolve a suite file.

    ``system_file`` and ``prompt_file`` are resolved relative to the suite
    file's directory, so a suite is relocatable as a unit.
    """
    suite_path = Path(path).resolve()
    if not suite_path.is_file():
        raise SpecError(f"suite file not found: {suite_path}")
    try:
        raw = yaml.safe_load(suite_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SpecError(f"{suite_path}: not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise SpecError(f"{suite_path}: top level must be a mapping")

    _reject_unknown(str(suite_path), raw, _SUITE_KEYS)
    base = suite_path.parent

    defaults = raw.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise SpecError(f"{suite_path}: `defaults` must be a mapping")
    _reject_unknown(f"{suite_path}: defaults", defaults, _DEFAULT_KEYS)

    suite_vars = raw.get("vars") or {}
    if not isinstance(suite_vars, dict):
        raise SpecError(f"{suite_path}: `vars` must be a mapping")

    shared_graders = [
        _load_grader(g, f"{suite_path}: graders[{i}]")
        for i, g in enumerate(raw.get("graders") or [])
    ]

    raw_variants = raw.get("variants")
    if not raw_variants:
        raise SpecError(f"{suite_path}: at least one variant is required")
    variants: list[Variant] = []
    seen_variant_ids: set[str] = set()
    for i, rv in enumerate(raw_variants):
        where = f"{suite_path}: variants[{i}]"
        if not isinstance(rv, dict):
            raise SpecError(f"{where}: must be a mapping")
        _reject_unknown(where, rv, _VARIANT_KEYS)
        merged = {**defaults, **rv}
        vid = merged.get("id")
        if not vid:
            raise SpecError(f"{where}: missing `id`")
        if vid in seen_variant_ids:
            raise SpecError(f"{where}: duplicate variant id {vid!r}")
        seen_variant_ids.add(str(vid))

        system = merged.get("system")
        if merged.get("system_file"):
            if system:
                raise SpecError(f"{where}: set `system` or `system_file`, not both")
            system = _read_file(base, str(merged["system_file"]), where)

        mode = str(merged.get("mode", "text"))
        if mode not in MODES:
            raise SpecError(f"{where}: mode must be one of {', '.join(MODES)}")

        variants.append(
            Variant(
                id=str(vid),
                system=system,
                model=merged.get("model"),
                effort=merged.get("effort"),
                mode=mode,
                tools=merged.get("tools"),
                append_system=merged.get("append_system"),
                json_schema=merged.get("json_schema"),
                vars=dict(merged.get("vars") or {}),
                prompt_prefix=str(merged.get("prompt_prefix", "")),
                prompt_suffix=str(merged.get("prompt_suffix", "")),
                max_budget_usd=merged.get("max_budget_usd"),
                fixture=merged.get("fixture"),
                setup=list(merged.get("setup") or []),
                note=str(merged.get("note", "")),
            )
        )

    raw_cases = raw.get("cases")
    if not raw_cases:
        raise SpecError(f"{suite_path}: at least one case is required")
    cases: list[Case] = []
    seen_case_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        where = f"{suite_path}: cases[{i}]"
        if not isinstance(rc, dict):
            raise SpecError(f"{where}: must be a mapping")
        _reject_unknown(where, rc, _CASE_KEYS)
        cid = rc.get("id")
        if not cid:
            raise SpecError(f"{where}: missing `id`")
        if cid in seen_case_ids:
            raise SpecError(f"{where}: duplicate case id {cid!r}")
        seen_case_ids.add(str(cid))

        prompt = rc.get("prompt")
        if rc.get("prompt_file"):
            if prompt:
                raise SpecError(f"{where}: set `prompt` or `prompt_file`, not both")
            prompt = _read_file(base, str(rc["prompt_file"]), where)
        if not prompt:
            raise SpecError(f"{where}: missing `prompt` or `prompt_file`")

        case_graders = [
            _load_grader(g, f"{where}: graders[{j}]")
            for j, g in enumerate(rc.get("graders") or [])
        ]
        cases.append(
            Case(
                id=str(cid),
                prompt=str(prompt),
                vars=dict(rc.get("vars") or {}),
                graders=tuple(copy.deepcopy(shared_graders) + case_graders),
                weight=float(rc.get("weight", 1.0)),
                fixture=rc.get("fixture"),
                skip=str(rc.get("skip", "")),
                note=str(rc.get("note", "")),
            )
        )

    repeats = int(raw.get("repeats", 1))
    if repeats < 1:
        raise SpecError(f"{suite_path}: `repeats` must be >= 1")

    return Suite(
        name=str(raw.get("name") or suite_path.stem),
        description=str(raw.get("description", "")),
        variants=tuple(variants),
        cases=tuple(cases),
        vars=suite_vars,
        judge=dict(raw.get("judge") or {}),
        blind=dict(raw.get("blind") or {}),
        repeats=repeats,
        path=suite_path,
    )
