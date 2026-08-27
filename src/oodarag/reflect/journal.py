"""The append-only record of every cycle, and the substrate the loop learns from.

Two files, both JSON Lines:

    cycles.jsonl    one record per run: what was observed, found, applied
    outcomes.jsonl  one record per verdict: applied, dismissed, reverted, failed

Append-only is a design choice, not laziness. A system that edits your files on
a timer is only trustworthy if "what did it do on the 14th, and why" has an
answer that cannot have been rewritten by the run on the 15th. Everything the
loop learns - which rules to trust, which suggestions to stop making - is a
fold over these two files, so the learned behaviour is always reconstructible
and always auditable. Delete the journal and the loop reverts to a naive but
correct first night; it never ends up in a state nobody can explain.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

from oodarag.reflect.models import CycleReport, Outcome
from oodarag.util.logging import get_logger

log = get_logger("reflect.journal")

#: Read caps. A year of nightly runs is ~365 cycle records, so these are far
#: above any real usage; they exist so a corrupted or maliciously large file
#: cannot turn a nightly job into an OOM.
MAX_CYCLE_RECORDS = 5_000
MAX_OUTCOME_RECORDS = 50_000


class Journal:
    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)
        self.cycles_path = self.dir / "cycles.jsonl"
        self.outcomes_path = self.dir / "outcomes.jsonl"

    # -- writing -------------------------------------------------------------

    def _append(self, path: Path, record: dict[str, Any]) -> bool:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record, ensure_ascii=False, default=str)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            return True
        except OSError as e:
            # A journal that cannot be written must not abort the run: the
            # edits already applied are more important than the record of them,
            # and the report still reaches the user.
            log.error("journal write failed", path=str(path), err=str(e)[:200])
            return False

    def record_cycle(self, report: CycleReport) -> bool:
        record = report.as_dict(include_detail=False)
        # Proposal *fingerprints* rather than bodies: the journal answers "has
        # this been suggested before", and storing every diff would make the
        # file unreadable within a fortnight.
        record["proposed"] = [p.fingerprint for p in report.proposals]
        record["rules_fired"] = sorted({f.rule_id for f in report.findings})
        return self._append(self.cycles_path, record)

    def record_outcome(self, outcome: Outcome) -> bool:
        return self._append(self.outcomes_path, outcome.as_dict())

    def record_outcomes(self, outcomes: list[Outcome]) -> int:
        return sum(1 for o in outcomes if self.record_outcome(o))

    # -- reading -------------------------------------------------------------

    def _read(self, path: Path, cap: int) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # a torn final line from a killed run
                    if len(records) >= cap:
                        break
        except OSError as e:
            log.warn("journal unreadable", path=str(path), err=str(e)[:200])
        return records

    def cycles(self, limit: int | None = None) -> list[dict[str, Any]]:
        records = self._read(self.cycles_path, MAX_CYCLE_RECORDS)
        return records[-limit:] if limit else records

    def outcomes(
        self,
        rule_id: str | None = None,
        fingerprint: str | None = None,
        since: float = 0.0,
    ) -> list[Outcome]:
        out: list[Outcome] = []
        for rec in self._read(self.outcomes_path, MAX_OUTCOME_RECORDS):
            if rule_id and rec.get("rule_id") != rule_id:
                continue
            if fingerprint and rec.get("fingerprint") != fingerprint:
                continue
            if since and float(rec.get("ts", 0.0)) < since:
                continue
            try:
                out.append(
                    Outcome(
                        fingerprint=rec["fingerprint"],
                        rule_id=rec.get("rule_id", ""),
                        verdict=rec.get("verdict", "deferred"),
                        ts=float(rec.get("ts", 0.0)),
                        cycle_id=rec.get("cycle_id", ""),
                        note=rec.get("note", ""),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return out

    # -- derived views -------------------------------------------------------

    def last_cycle(self) -> dict[str, Any] | None:
        cycles = self.cycles()
        return cycles[-1] if cycles else None

    def last_window_end(self, default_lookback_s: float = 86_400.0) -> float:
        """Where the next observation window should start.

        The previous cycle's end, so nothing is observed twice and nothing is
        missed. On a first run - or after the journal is deleted - fall back to
        a lookback rather than to zero: scanning a decade of shell history to
        produce a first report is a bad first impression.
        """
        last = self.last_cycle()
        if last and last.get("ended_at"):
            try:
                return float(last["ended_at"])
            except (TypeError, ValueError):
                pass
        return time.time() - default_lookback_s

    def times_proposed(self, fingerprint: str) -> int:
        """How many cycles have already suggested this exact fix.

        Feeds the nagging escalation: a proposal that has been queued for five
        nights running is either more important than its score says, or it
        should be dropped. Either way, repeating it silently is the one wrong
        answer.
        """
        return sum(1 for c in self.cycles() if fingerprint in (c.get("proposed") or []))

    def verdict_counts(self, rule_id: str) -> Counter[str]:
        return Counter(o.verdict for o in self.outcomes(rule_id=rule_id))

    def dismissed(self) -> set[str]:
        """Fingerprints the user has explicitly declined. Never re-proposed."""
        return {o.fingerprint for o in self.outcomes() if o.verdict == "dismissed"}

    def reverted(self) -> set[str]:
        return {o.fingerprint for o in self.outcomes() if o.verdict == "reverted"}

    def applied(self) -> set[str]:
        return {o.fingerprint for o in self.outcomes() if o.verdict == "applied"}

    def summary(self) -> dict[str, Any]:
        cycles = self.cycles()
        outcomes = self.outcomes()
        verdicts = Counter(o.verdict for o in outcomes)
        return {
            "cycles": len(cycles),
            "first_cycle": cycles[0].get("cycle_id") if cycles else None,
            "last_cycle": cycles[-1].get("cycle_id") if cycles else None,
            "outcomes": len(outcomes),
            "verdicts": dict(verdicts),
            "rules_seen": sorted({o.rule_id for o in outcomes if o.rule_id}),
        }
