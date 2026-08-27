"""The evidence contract every data checker implements.

The point of this module is one rule, made structural rather than aspirational:

    A verdict may not be recorded without the evidence that produced it.

Review tools usually get this backwards. They emit a judgement ("the docs are
stale", "this claim looks wrong") and leave the reader to go and confirm it. The
reader then has to trust the tool exactly as much as they would have had to
trust an unaided guess, which is to say the tool has added confidence without
adding information. Worse, a reviewer - human or model - that is allowed to
assert without citing will eventually assert something it inferred rather than
something it observed, and that is indistinguishable from fabrication at the
point of reading.

So `Finding.__post_init__` refuses to build a finding whose verdict is
`SUPPORTED`, `UNSUPPORTED` or `CONTRADICTED` unless at least one `Evidence`
record is attached, and every `Evidence` record must name where it came from: a
file and line, a command and its exit status, or an explicit statement of the
search space that turned up nothing.

The fourth verdict, `UNVERIFIABLE`, exists for exactly the case that makes
review tools lie: the checker could not decide. It is not a pass. It is not a
failure. It is the tool saying so out loud instead of rounding to whichever one
is more convenient.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence


class Verdict(str, Enum):
    """What the evidence supports. Deliberately four-valued.

    Three-valued review (pass / fail / unknown-folded-into-pass) is how a
    checker ends up reporting a clean bill of health for a claim it never
    actually examined.
    """

    SUPPORTED = "supported"          # evidence was found and it matches the claim
    UNSUPPORTED = "unsupported"      # the search space was covered; nothing supports it
    CONTRADICTED = "contradicted"    # evidence was found and it says the opposite
    UNVERIFIABLE = "unverifiable"    # this checker cannot decide, and says so

    @property
    def is_problem(self) -> bool:
        return self in (Verdict.UNSUPPORTED, Verdict.CONTRADICTED)


class Severity(str, Enum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"error": 3, "warn": 2, "info": 1}[self.value]


class EvidenceKind(str, Enum):
    FILE = "file"          # a byte range of a file that exists
    COMMAND = "command"    # a process that was actually run, with its exit status
    ABSENCE = "absence"    # a search that was actually performed and found nothing
    VALUE = "value"        # a value computed from the two above


@dataclass(slots=True)
class Evidence:
    """One observation. Not a conclusion - the thing the conclusion rests on.

    `ABSENCE` evidence is the subtle one. "There is no such file" is only a fact
    if you say where you looked; otherwise it is a guess wearing a fact's
    clothes. `searched` is therefore required for absence evidence, and
    `__post_init__` enforces it.
    """

    kind: EvidenceKind
    summary: str
    path: str = ""
    line: int = 0
    excerpt: str = ""
    argv: tuple[str, ...] = ()
    exit_code: int | None = None
    output: str = ""
    searched: tuple[str, ...] = ()
    value: Any = None

    def __post_init__(self) -> None:
        if self.kind is EvidenceKind.FILE and not self.path:
            raise ValueError("FILE evidence must name the file it came from")
        if self.kind is EvidenceKind.COMMAND and not self.argv:
            raise ValueError("COMMAND evidence must record the argv that was run")
        if self.kind is EvidenceKind.ABSENCE and not self.searched:
            raise ValueError(
                "ABSENCE evidence must state where it looked; "
                "'not found' without a search space is a guess, not an observation"
            )

    @property
    def locator(self) -> str:
        """A clickable `file:line`, a command line, or the search space."""
        if self.kind is EvidenceKind.FILE:
            return f"{self.path}:{self.line}" if self.line else self.path
        if self.kind is EvidenceKind.COMMAND:
            return " ".join(self.argv)
        if self.kind is EvidenceKind.ABSENCE:
            return f"searched {', '.join(self.searched[:6])}"
        return self.path or "computed"

    def as_dict(self) -> dict[str, Any]:
        # `exit_code` is listed explicitly because a successful command's status
        # is evidence: dropping it as "empty" would turn "ran and passed" into
        # "ran, outcome unrecorded", which is the ambiguity this tool exists to
        # remove. Everything else is elided only when genuinely unset.
        out = {k: v for k, v in asdict(self).items() if v not in ("", (), None)}
        if self.exit_code is None:
            out.pop("exit_code", None)
        if not self.line:
            out.pop("line", None)
        out["kind"] = self.kind.value
        out["locator"] = self.locator
        return out

    # -------------------------------------------------------------- factories

    @classmethod
    def at(cls, path: str | Path, line: int, excerpt: str, summary: str = "") -> Evidence:
        text = excerpt.strip()
        return cls(
            kind=EvidenceKind.FILE,
            summary=summary or f"{path}:{line}",
            path=str(path),
            line=line,
            excerpt=text[:400],
        )

    @classmethod
    def absent(cls, summary: str, searched: Sequence[str]) -> Evidence:
        if not searched:
            raise ValueError("absent() requires a non-empty search space")
        return cls(kind=EvidenceKind.ABSENCE, summary=summary, searched=tuple(searched))

    @classmethod
    def measured(cls, summary: str, value: Any, path: str | Path = "") -> Evidence:
        return cls(kind=EvidenceKind.VALUE, summary=summary, value=value, path=str(path))

    @classmethod
    def ran(cls, argv: Sequence[str], *, cwd: str | Path | None = None,
            timeout: float = 120.0, env: dict[str, str] | None = None) -> Evidence:
        """Run a command and record what actually happened.

        The output is captured and truncated rather than summarised, because a
        summary of a failure is the reviewer's opinion of the failure. A caller
        that wants to know why `make test` fails should read the stderr this
        recorded, not a paraphrase of it.
        """
        started = time.monotonic()
        try:
            proc = subprocess.run(  # noqa: S603 - argv is caller-supplied, never a shell string
                list(argv),
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            combined = (proc.stdout or "") + (proc.stderr or "")
            code: int | None = proc.returncode
        except FileNotFoundError as e:
            combined, code = f"{type(e).__name__}: {e}", None
        except subprocess.TimeoutExpired:
            combined, code = f"timed out after {timeout}s", None
        return cls(
            kind=EvidenceKind.COMMAND,
            summary=f"`{' '.join(argv)}` exited {code}",
            argv=tuple(argv),
            exit_code=code,
            output=_tail(combined, 1200),
            value=round(time.monotonic() - started, 3),
        )


def _tail(text: str, limit: int) -> str:
    """Keep the end of long output: a traceback's cause is on its last line."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return "...(truncated)...\n" + text[-limit:]


@dataclass(slots=True)
class Claim:
    """An assertion found in the repository, with where it was asserted.

    A claim is always quoted verbatim from a file. The checkers never restate a
    claim in their own words, because a restated claim is a claim about a claim,
    and the reader can no longer tell which one was checked.
    """

    text: str
    path: str
    line: int
    kind: str = "prose"
    context: str = ""

    @property
    def locator(self) -> str:
        return f"{self.path}:{self.line}"

    def as_dict(self) -> dict[str, Any]:
        return {"text": self.text, "path": self.path, "line": self.line, "kind": self.kind}


@dataclass(slots=True)
class Finding:
    """A verdict on one claim, plus the evidence that produced it."""

    checker: str
    code: str
    verdict: Verdict
    severity: Severity
    claim: Claim
    evidence: list[Evidence] = field(default_factory=list)
    detail: str = ""
    remedy: str = ""

    def __post_init__(self) -> None:
        if self.verdict is not Verdict.UNVERIFIABLE and not self.evidence:
            raise ValueError(
                f"{self.checker}/{self.code}: verdict {self.verdict.value!r} recorded with no "
                "evidence. Either attach the observation it rests on, or record it as "
                "UNVERIFIABLE and say why."
            )
        if self.verdict is Verdict.UNVERIFIABLE and not self.detail:
            raise ValueError(
                f"{self.checker}/{self.code}: UNVERIFIABLE requires `detail` naming what "
                "stopped the check from deciding"
            )

    @property
    def is_problem(self) -> bool:
        return self.verdict.is_problem

    def as_dict(self) -> dict[str, Any]:
        return {
            "checker": self.checker,
            "code": self.code,
            "verdict": self.verdict.value,
            "severity": self.severity.value,
            "claim": self.claim.as_dict(),
            "locator": self.claim.locator,
            "detail": self.detail,
            "remedy": self.remedy,
            "evidence": [e.as_dict() for e in self.evidence],
        }


@dataclass
class Report:
    """Everything one review run observed."""

    root: str
    findings: list[Finding] = field(default_factory=list)
    checkers_run: list[str] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    duration_s: float = 0.0

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def extend(self, findings: Iterable[Finding]) -> None:
        for f in findings:
            self.add(f)

    # ------------------------------------------------------------------ views

    @property
    def problems(self) -> list[Finding]:
        return [f for f in self.findings if f.is_problem]

    @property
    def unverifiable(self) -> list[Finding]:
        return [f for f in self.findings if f.verdict is Verdict.UNVERIFIABLE]

    def by_severity(self, severity: Severity) -> list[Finding]:
        return [f for f in self.problems if f.severity is severity]

    def counts(self) -> dict[str, int]:
        out = {v.value: 0 for v in Verdict}
        for f in self.findings:
            out[f.verdict.value] += 1
        return out

    @property
    def exit_code(self) -> int:
        """0 only when nothing is unsupported or contradicted at error severity.

        UNVERIFIABLE never fails the run - a checker that could not look is not
        the same as a repository that is wrong - but it is always printed, so it
        cannot quietly become a pass.
        """
        return 1 if self.by_severity(Severity.ERROR) else 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "started_at": self.started_at,
            "duration_s": round(self.duration_s, 3),
            "checkers_run": self.checkers_run,
            "skipped": self.skipped,
            "counts": self.counts(),
            "problem_count": len(self.problems),
            "findings": [f.as_dict() for f in self.findings],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        lines: list[str] = ["# ultrareview evidence report", ""]
        counts = self.counts()
        lines.append(f"Root: `{self.root}`")
        lines.append(
            f"Checkers: {len(self.checkers_run)} run"
            + (f", {len(self.skipped)} skipped" if self.skipped else "")
        )
        lines.append(
            "Verdicts: "
            + ", ".join(f"{k} {v}" for k, v in counts.items() if v)
            + f" (in {self.duration_s:.2f}s)"
        )
        lines.append("")

        for severity in (Severity.ERROR, Severity.WARN, Severity.INFO):
            group = self.by_severity(severity)
            if not group:
                continue
            lines.append(f"## {severity.value} ({len(group)})")
            lines.append("")
            for f in group:
                lines.append(f"### `{f.claim.locator}` - {f.code}")
                lines.append("")
                lines.append(f"- **Claim**: {f.claim.text.strip()[:300]}")
                lines.append(f"- **Verdict**: {f.verdict.value}")
                if f.detail:
                    lines.append(f"- **Detail**: {f.detail}")
                for e in f.evidence:
                    lines.append(f"- **Evidence** ({e.kind.value}) `{e.locator}`: {e.summary}")
                    if e.output:
                        excerpt = e.output.strip().splitlines()[-3:]
                        for row in excerpt:
                            lines.append(f"      {row}")
                if f.remedy:
                    lines.append(f"- **Remedy**: {f.remedy}")
                lines.append("")

        if self.unverifiable:
            lines.append(f"## unverifiable ({len(self.unverifiable)})")
            lines.append("")
            lines.append(
                "These were not checked. They are listed so that "
                "'not checked' cannot be mistaken for 'checked and fine'."
            )
            lines.append("")
            for f in self.unverifiable:
                lines.append(f"- `{f.claim.locator}` {f.code}: {f.detail}")
            lines.append("")

        if not self.problems and not self.unverifiable:
            lines.append("No unsupported or contradicted claims found.")
            lines.append("")
        return "\n".join(lines)
