"""Act: draft, record, and never send.

Every executor here writes to disk. None of them emails an LP, files with a
regulator, or posts to KAP. That is not a missing feature, it is the design:
drafting is what a system can be trusted with, and sending is a decision a
person makes with their name on it. A system that files automatically has to be
right every time; one that drafts only has to be useful.

The decision journal is append-only JSONL. It is the artefact that turns "the
system flagged it" into a record an inspector can follow: which rule, which
facts, which thresholds, at what time, in which cycle.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from oodarag.ooda.policy import Action, journal_line
from oodarag.util.logging import get_logger

log = get_logger("act")


class DecisionJournal:
    """Append-only audit trail. One JSON object per line, never rewritten."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, actions: list[Action], *, cycle: str) -> int:
        if not actions:
            return 0
        at = time.time()
        with self.path.open("a", encoding="utf-8") as fh:
            for action in actions:
                fh.write(journal_line(action, cycle=cycle, at=at) + "\n")
        return len(actions)

    def read(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                log.warn("unreadable journal line skipped", path=str(self.path))
        return rows[-limit:] if limit else rows


@dataclass
class Brief:
    """The Monday-morning page."""

    as_of: date
    firm: str
    actions: list[Action] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    provenance_note: str = ""

    @property
    def escalations(self) -> list[Action]:
        return [a for a in self.actions if a.kind == "escalate"]

    @property
    def alerts(self) -> list[Action]:
        return [a for a in self.actions if a.kind == "alert"]

    @property
    def digest(self) -> list[Action]:
        return [a for a in self.actions if a.kind == "digest"]


_PERCENT_FACTS = frozenset({"nominal_move", "real_move", "inflation", "coverage"})


def _fmt(key: str, value: Any) -> str:
    """Render a fact for a human.

    Percentages are shown to two places. The underlying Decimal keeps full
    precision in the journal — this is presentation only, and the journal is
    what an auditor reads.
    """
    if key in _PERCENT_FACTS:
        try:
            return f"{Decimal(str(value)):.2%}"
        except (InvalidOperation, ValueError, TypeError):
            return str(value)
    return str(value)


def render_brief(brief: Brief) -> str:
    """Markdown, in the order a reader should meet it: what must be done, what
    is wrong, then everything else."""
    L = [f"# {brief.firm} — {brief.as_of.isoformat()}", ""]

    if not brief.actions:
        L.extend(["Nothing fired this cycle.", "",
                  "> A quiet brief is a result, not an absence. It means every rule "
                  "ran and none of their conditions held.", ""])

    def section(title: str, items: list[Action], empty: str) -> None:
        L.append(f"## {title}")
        L.append("")
        if not items:
            L.extend([empty, ""])
            return
        for a in items:
            flag = "  ⚠ UNVERIFIED BASIS" if a.unverified_basis else ""
            L.append(f"- **{a.rule_id}** · {a.target}{flag}")
            L.append(f"  {a.reason}")
            if a.requires_signoff:
                L.append(f"  *sign-off: {a.requires_signoff}*")
            for k in ("due", "business_days_left", "nominal_move", "real_move",
                      "inflation", "coverage", "age_days"):
                if k in a.facts:
                    L.append(f"  · {k}: {_fmt(k, a.facts[k])}")
        L.append("")

    section("Needs a decision today", brief.escalations,
            "Nothing requires sign-off.")
    section("Wrong, or about to be", brief.alerts, "No alerts.")
    section("For the week", brief.digest, "Nothing accumulated.")

    if brief.notes:
        L.extend(["## Notes", ""] + [f"- {n}" for n in brief.notes] + [""])

    L.extend(["---", ""])
    L.append(brief.provenance_note or (
        "Every figure above is computed deterministically and carries its basis. "
        "Obligations marked UNVERIFIED came from research that could not reach a "
        "primary source: they are a starting calendar, not legal deadlines."))
    L.append("")
    L.append("*Drafted, not sent. Nothing here has been filed with anyone.*")
    return "\n".join(L)
