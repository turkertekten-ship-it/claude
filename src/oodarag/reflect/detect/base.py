"""The detector contract and registry.

A detector is a named rule with two halves: `detect` turns signals into
`Finding`s (what is wrong), and `propose` turns a finding into `Proposal`s (what
to do about it). Both halves live in one class on purpose - splitting them
across files is how rule engines end up with fixes that no longer match the
condition that triggered them.

Detectors are pure with respect to the filesystem: they read, they never write.
Writing is `reflect.act`'s job and happens only after `reflect.decide` has
ranked, gated and budgeted the proposals. A detector that edited a file
directly would bypass the risk tiers, the backup, and the journal - which is to
say, all of the safety.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.reflect.models import Finding, Proposal, Signal
from oodarag.util.logging import get_logger

log = get_logger("reflect.detect")

_WORD_RE = re.compile(r"[a-z0-9_]+(?:[.\-/][a-z0-9_]+)*")


@dataclass(slots=True)
class DetectContext:
    """Everything a rule may look at, and nothing it may change.

    The indexes are built once and shared across every detector because the
    grouping work (by kind, by session, by day) is identical for all of them and
    quadratic if each rule re-does it over a week of history.
    """

    signals: list[Signal] = field(default_factory=list)
    root: Path = field(default_factory=Path.cwd)
    now: float = 0.0
    window_start: float = 0.0
    config: dict[str, Any] = field(default_factory=dict)
    _by_kind: dict[str, list[Signal]] = field(default_factory=dict, repr=False)
    _by_session: dict[str, list[Signal]] = field(default_factory=dict, repr=False)
    _text_cache: dict[str, str | None] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sig in self.signals:
            self._by_kind.setdefault(sig.kind, []).append(sig)
            self._by_session.setdefault(sig.session or sig.day, []).append(sig)
        for group in self._by_session.values():
            group.sort(key=lambda s: (s.ts, s.ordinal))

    # -- signal access -------------------------------------------------------

    def by_kind(self, *kinds: str) -> list[Signal]:
        out: list[Signal] = []
        for k in kinds:
            out.extend(self._by_kind.get(k, ()))
        out.sort(key=lambda s: (s.ts, s.ordinal))
        return out

    def by_source(self, prefix: str) -> list[Signal]:
        return [s for s in self.signals if s.source.startswith(prefix)]

    def sessions(self, *kinds: str) -> dict[str, list[Signal]]:
        """Session id -> chronological signals, optionally filtered by kind."""
        if not kinds:
            return dict(self._by_session)
        wanted = set(kinds)
        return {
            key: [s for s in group if s.kind in wanted]
            for key, group in self._by_session.items()
            if any(s.kind in wanted for s in group)
        }

    # -- filesystem access (read-only) --------------------------------------

    def resolve(self, relpath: str) -> Path:
        return (self.root / relpath).resolve()

    def within_root(self, path: Path) -> bool:
        """Guard against a rule proposing an edit outside the workspace."""
        try:
            path.resolve().relative_to(self.root.resolve())
            return True
        except (ValueError, OSError):
            return False

    def exists(self, relpath: str) -> bool:
        try:
            return (self.root / relpath).exists()
        except OSError:
            return False

    def read_text(self, relpath: str) -> str | None:
        """Cached read of a workspace file; None when absent or unreadable."""
        if relpath in self._text_cache:
            return self._text_cache[relpath]
        value: str | None = None
        try:
            path = self.root / relpath
            if path.is_file():
                value = path.read_text("utf-8", "replace")
        except (OSError, ValueError):
            value = None
        self._text_cache[relpath] = value
        return value

    def rel(self, path: Path | str) -> str:
        try:
            return str(Path(path).resolve().relative_to(self.root.resolve()))
        except (ValueError, OSError):
            return str(path)

    def setting(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)


class Detector(ABC):
    """A named rule. Subclass, set `rule_id`, implement `detect`."""

    #: Stable dotted id, e.g. "friction.repeated_instruction". It keys the
    #: learned prior in the journal, so renaming a rule resets its reputation.
    rule_id: str = "rule"

    #: One line shown as the section header in the nightly report.
    title: str = "Unnamed rule"

    #: Default severity for findings this rule emits; individual findings override.
    severity: str = "medium"

    #: Signal kinds this rule reads. The loop skips rules whose kinds are absent.
    consumes: tuple[str, ...] = ()

    #: Cap on findings per cycle. A rule that fires 400 times is noise, and the
    #: top few are almost always the informative ones.
    max_findings: int = 25

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        """Yield findings. Must not write to disk."""

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        """Turn a finding into concrete fixes. Default: observation only."""
        return ()

    # -- guarded entry points ------------------------------------------------

    def run(self, ctx: DetectContext) -> list[Finding]:
        """Detect with containment and caps. Never raises."""
        try:
            found = list(self.detect(ctx))
        except Exception as e:
            log.error("detector failed", rule=self.rule_id, err=str(e)[:300])
            return []
        for f in found:
            if not f.rule_id:
                f.rule_id = self.rule_id
        found.sort(key=lambda f: (-f.severity_rank, -f.confidence, f.title))
        if len(found) > self.max_findings:
            log.debug("findings capped", rule=self.rule_id, kept=self.max_findings, saw=len(found))
            found = found[: self.max_findings]
        return found

    def run_propose(self, finding: Finding, ctx: DetectContext) -> list[Proposal]:
        try:
            proposals = list(self.propose(finding, ctx))
        except Exception as e:
            log.error("propose failed", rule=self.rule_id, err=str(e)[:300])
            return []
        return [p for p in proposals if self._edits_are_contained(p, ctx)]

    def _edits_are_contained(self, proposal: Proposal, ctx: DetectContext) -> bool:
        """Reject a proposal touching anything outside the workspace root.

        Enforced here, at the boundary every proposal crosses, rather than in
        the actuator alone - a rule with a path bug should fail loudly at the
        rule, not quietly produce an unapplied edit every night.
        """
        for edit in proposal.edits:
            if Path(edit.path).is_absolute() or ".." in Path(edit.path).parts:
                log.warn("proposal escaped root", rule=self.rule_id, path=edit.path)
                return False
        return True


# -- registry ----------------------------------------------------------------

_REGISTRY: dict[str, type[Detector]] = {}


def register(cls: type[Detector]) -> type[Detector]:
    """Class decorator. Import-time registration keeps the loop free of a
    hand-maintained list that drifts from the modules that actually exist."""
    if cls.rule_id in _REGISTRY and _REGISTRY[cls.rule_id] is not cls:
        raise ValueError(f"duplicate rule_id: {cls.rule_id}")
    _REGISTRY[cls.rule_id] = cls
    return cls


def registry() -> dict[str, type[Detector]]:
    return dict(_REGISTRY)


def build_detectors(
    config: dict[str, Any] | None = None,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> list[Detector]:
    """Instantiate every registered rule, minus anything switched off.

    `enabled` is an allow-list when present; `disabled` always wins. Both accept
    a bare prefix ("friction") so a family of rules can be silenced at once.
    """
    config = config or {}
    disabled = disabled or []
    out: list[Detector] = []
    for rule_id, cls in sorted(_REGISTRY.items()):
        if enabled and not any(rule_id == e or rule_id.startswith(e + ".") for e in enabled):
            continue
        if any(rule_id == d or rule_id.startswith(d + ".") for d in disabled):
            continue
        out.append(cls(config.get(rule_id, {})))
    return out


# -- shared helpers ----------------------------------------------------------


def words(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def normalize_phrase(text: str, max_words: int = 40) -> str:
    """A comparable form of an instruction: lowercased content words, order kept.

    Used to tell "run make test before you commit" from "please run make test
    first" - the same instruction, and it should count as a repeat.
    """
    from oodarag.util.text import STOPWORDS

    toks = [w for w in words(text) if w not in STOPWORDS and len(w) > 1]
    return " ".join(toks[:max_words])
