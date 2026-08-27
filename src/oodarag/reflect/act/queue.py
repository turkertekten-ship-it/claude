"""The proposals waiting for a person, and the state that makes waiting safe.

Anything the loop is not allowed to do on its own has to survive until a human
looks at it, which on a laptop means surviving a reboot, a `Ctrl-C` in the
middle of a write, and a fortnight of being ignored. That is why this is a file
and not a list on the `ReflectLoop` object.

Three properties are load-bearing.

**Identity is the proposal fingerprint, so a queue cannot grow by repetition.**
The same finding re-derived on five consecutive nights is one row that has been
seen five times, not five rows. A queue that duplicates is a queue nobody reads,
and the loop's own escalation (`priors.nag_factor`) is counted from exactly this
number, so getting it wrong would also distort tomorrow's ranking.

**Lookup by prefix is strict.** People type eight characters, and eight
characters of a hash do collide eventually. Every other operation here is
reversible; `accept` is not - it hands a diff to the actuator with the user's
authority attached. So an ambiguous prefix raises with the candidates named
rather than picking the first match, because the failure mode of guessing is
applying an edit the user never read.

**A decision outranks the file it is stored in.** Writes go through a temp file
and `os.replace`, and a queue file that cannot be parsed is replaced with an
empty one and a warning instead of raising: a corrupt queue must cost you the
pending suggestions, never the nightly run. The verdicts themselves are not at
risk - `accept`/`dismiss` are also recorded in the journal, which is append-only.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from oodarag.reflect.models import EditOp, Evidence, Finding, Proposal
from oodarag.util.logging import get_logger

log = get_logger("reflect.queue")

#: Bumped only for a change that older readers cannot understand. Unknown
#: versions are read anyway - the entry shape is additive, and refusing to read
#: a queue written by a newer build would lose a user's accept.
SCHEMA_VERSION = 1

#: The handle length shown in the report and typed on the command line.
PREFIX_LEN = 8

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_DISMISSED = "dismissed"

DAY_S = 86_400.0


class ReviewQueue:
    """Proposals awaiting a human verdict, persisted as one JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    # -- persistence ---------------------------------------------------------

    def _load(self) -> dict[str, dict[str, Any]]:
        """Read the queue fresh. Never raises; a broken file reads as empty.

        Re-read on every call rather than cached in the instance: the loop holds
        a `ReviewQueue` for the length of a cycle while the CLI writes to the
        same file from another process, and re-reading a few kilobytes is much
        cheaper than reasoning about which copy is stale.
        """
        try:
            raw = self.path.read_text("utf-8")
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as e:
            log.warn("queue unreadable, treating as empty", path=str(self.path), err=str(e)[:200])
            return {}
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            log.warn("queue corrupt, starting clean", path=str(self.path), err=str(e)[:200])
            return {}

        # A bare list is accepted so a hand-edited or older file still loads.
        records = data.get("entries") if isinstance(data, dict) else data
        if not isinstance(records, list):
            log.warn("queue has no entries list, starting clean", path=str(self.path))
            return {}

        entries: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict):
                continue
            fingerprint = str(record.get("fingerprint") or "")
            if not fingerprint or not isinstance(record.get("proposal"), dict):
                # An entry we cannot rebuild a proposal from is worse than no
                # entry: it would show in the queue and fail on accept.
                continue
            entries[fingerprint] = record
        return entries

    def _save(self, entries: dict[str, dict[str, Any]]) -> bool:
        payload = {
            "version": SCHEMA_VERSION,
            "updated_at": round(time.time(), 3),
            "entries": [entries[fp] for fp in sorted(entries)],
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        except OSError as e:
            log.error("queue directory unwritable", path=str(self.path), err=str(e)[:200])
            return False
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False, default=str)
            os.replace(tmp, self.path)
            return True
        except (OSError, ValueError, TypeError) as e:
            log.error("queue write failed", path=str(self.path), err=str(e)[:200])
            try:
                os.unlink(tmp)
            except OSError:
                pass
            return False

    # -- writing -------------------------------------------------------------

    def put(self, proposals: list[Proposal], cycle_id: str = "") -> int:
        """Upsert tonight's proposals. Returns how many rows are new.

        Re-queuing something already here bumps `times_seen` and `last_cycle`
        instead of adding a row, and deliberately leaves `status` alone: a
        proposal the user accepted last night must not revert to pending just
        because the detector found it again before the actuator got to it.
        """
        if not proposals:
            return 0
        entries = self._load()
        now = time.time()
        added = 0
        for proposal in proposals:
            try:
                fingerprint = proposal.fingerprint
                body = proposal.as_dict()
            except (AttributeError, TypeError, ValueError) as e:
                log.warn("skipping unqueueable proposal", err=str(e)[:200])
                continue
            existing = entries.get(fingerprint)
            if existing is None:
                entries[fingerprint] = {
                    "fingerprint": fingerprint,
                    "status": STATUS_PENDING,
                    "times_seen": 1,
                    "first_seen": round(now, 3),
                    "last_seen": round(now, 3),
                    "first_cycle": cycle_id,
                    "last_cycle": cycle_id,
                    "decided_at": 0.0,
                    "note": "",
                    "proposal": body,
                }
                added += 1
                continue
            existing["times_seen"] = int(existing.get("times_seen") or 0) + 1
            existing["last_seen"] = round(now, 3)
            existing["last_cycle"] = cycle_id
            # The body is refreshed because the score and the rationale move
            # between nights while the fingerprint - and so the user's verdict -
            # does not.
            existing["proposal"] = body
        self._save(entries)
        log.debug("queued", added=added, total=len(entries))
        return added

    def accept(self, fingerprint_prefix: str) -> dict[str, Any] | None:
        """Mark a proposal for application on the next run. Returns the entry."""
        return self._decide(fingerprint_prefix, STATUS_ACCEPTED, "")

    def dismiss(self, fingerprint_prefix: str, note: str = "") -> dict[str, Any] | None:
        """Decline a proposal. The caller records the outcome in the journal,
        which is what actually stops it being proposed again."""
        return self._decide(fingerprint_prefix, STATUS_DISMISSED, note)

    def _decide(self, prefix: str, status: str, note: str) -> dict[str, Any] | None:
        entries = self._load()
        key = _resolve(entries, prefix)
        if key is None:
            return None
        entry = entries[key]
        entry["status"] = status
        entry["decided_at"] = round(time.time(), 3)
        if note:
            entry["note"] = note[:500]
        self._save(entries)
        log.info("queue verdict", fingerprint=key[:PREFIX_LEN], status=status)
        return copy.deepcopy(entry)

    def drop(self, fingerprint: str) -> None:
        """Remove an entry outright - used once an accepted proposal has run.

        Takes a full fingerprint. A prefix is tolerated, but an ambiguous one
        removes nothing and warns: unlike `accept`, doing nothing here is safe,
        and the entry will be re-queued by the next cycle anyway.
        """
        entries = self._load()
        try:
            key = _resolve(entries, fingerprint)
        except ValueError as e:
            log.warn("ambiguous fingerprint, dropping nothing", err=str(e)[:200])
            return
        if key is None:
            return
        del entries[key]
        self._save(entries)

    def prune(self, max_age_days: float = 30.0) -> int:
        """Drop entries nobody acted on. Returns how many went.

        Pending rows age from when they were last proposed, so anything the loop
        still believes in is kept alive by being re-queued; only suggestions that
        have stopped recurring *and* were never answered expire. Dismissed rows
        age from the verdict, because the journal - not this file - is what keeps
        a dismissal honoured. Accepted rows never expire: someone said yes, and
        silently discarding consent is the one outcome a review queue may not
        produce.
        """
        if max_age_days <= 0:
            return 0
        entries = self._load()
        cutoff = time.time() - max_age_days * DAY_S
        stale: list[str] = []
        for fingerprint, entry in entries.items():
            status = entry.get("status", STATUS_PENDING)
            if status == STATUS_ACCEPTED:
                continue
            if status == STATUS_DISMISSED:
                age_from = _as_float(entry.get("decided_at")) or _as_float(entry.get("last_seen"))
            else:
                age_from = _as_float(entry.get("last_seen"))
            if age_from and age_from < cutoff:
                stale.append(fingerprint)
        for fingerprint in stale:
            del entries[fingerprint]
        if stale:
            self._save(entries)
            log.info("queue pruned", dropped=len(stale), kept=len(entries))
        return len(stale)

    # -- reading -------------------------------------------------------------

    def items(self) -> list[dict[str, Any]]:
        """Every entry, most worth looking at first.

        Ranked by the proposal's own score so the queue and the nightly report
        agree on what matters; ties fall back to the fingerprint so two reads of
        an unchanged file are byte-identical.
        """
        entries = self._load()
        rows = [copy.deepcopy(entries[fp]) for fp in entries]
        rows.sort(key=lambda e: (-_score_of(e), -int(e.get("times_seen") or 0), e["fingerprint"]))
        return rows

    def get(self, fingerprint_prefix: str) -> dict[str, Any] | None:
        """Look up one entry by full fingerprint or by a prefix (8 chars is the
        handle shown to users). Raises ValueError when a prefix is ambiguous."""
        entries = self._load()
        key = _resolve(entries, fingerprint_prefix)
        return copy.deepcopy(entries[key]) if key else None

    def pending(self) -> list[dict[str, Any]]:
        return [e for e in self.items() if e.get("status", STATUS_PENDING) == STATUS_PENDING]

    def accepted(self) -> list[dict[str, Any]]:
        return [e for e in self.items() if e.get("status") == STATUS_ACCEPTED]

    def dismissed(self) -> list[dict[str, Any]]:
        return [e for e in self.items() if e.get("status") == STATUS_DISMISSED]

    def __len__(self) -> int:
        return len(self._load())


# -- rebuilding a proposal ---------------------------------------------------


def proposal_from_dict(d: dict[str, Any]) -> Proposal:
    """Rebuild a `Proposal` from `Proposal.as_dict()`.

    The queue stores the serialized proposal verbatim so that accepting
    something tonight applies exactly the edit that was described last week,
    rather than whatever the detector would produce if it were re-run against a
    workspace that has since moved on. That only holds if this is a faithful
    inverse, so it reconstructs the `Finding` and `Evidence` too - the
    fingerprint is derived from them, and a lossy round trip would quietly
    invalidate every accept, dismiss and prior keyed on it.

    Raises ValueError on anything it cannot rebuild, so a damaged entry is
    skipped by the caller instead of applying a half-formed edit.
    """
    if not isinstance(d, dict):
        raise ValueError(f"proposal record must be a dict, got {type(d).__name__}")
    raw_finding = d.get("finding")
    if not isinstance(raw_finding, dict):
        raise ValueError("proposal record has no finding")

    try:
        finding = Finding(
            rule_id=str(raw_finding.get("rule_id") or ""),
            title=str(raw_finding.get("title") or ""),
            detail=str(raw_finding.get("detail") or ""),
            severity=str(raw_finding.get("severity") or "medium"),
            confidence=_as_float(raw_finding.get("confidence"), 0.5),
            key=str(raw_finding.get("key") or ""),
            targets=[str(t) for t in _as_list(raw_finding.get("targets"))],
            evidence=[_evidence_from_dict(e) for e in _as_list(raw_finding.get("evidence"))],
            tags=[str(t) for t in _as_list(raw_finding.get("tags"))],
            metadata=dict(raw_finding.get("metadata") or {}),
        )
        proposal = Proposal(
            finding=finding,
            title=str(d.get("title") or ""),
            rationale=str(d.get("rationale") or ""),
            edits=[_edit_from_dict(e) for e in _as_list(d.get("edits"))],
            risk=str(d.get("risk") or "review"),
            impact=_as_float(d.get("impact"), 0.5),
            effort=_as_float(d.get("effort"), 0.5),
            score=_as_float(d.get("score"), 0.0),
            score_parts={k: _as_float(v) for k, v in (d.get("score_parts") or {}).items()},
        )
    except (AttributeError, TypeError) as e:
        raise ValueError(f"malformed proposal record: {e}") from e

    stored = d.get("fingerprint")
    if stored and stored != proposal.fingerprint:
        # Not fatal: the stored value is a cache of a derived property, and the
        # derivation is authoritative. It is worth a warning because the only
        # ways to reach it are a hand-edited file and a changed fingerprint
        # recipe, and both mean the user's past verdicts no longer line up.
        log.warn(
            "queued proposal fingerprint drifted",
            stored=str(stored)[:PREFIX_LEN],
            rebuilt=proposal.fingerprint[:PREFIX_LEN],
        )
    return proposal


def _evidence_from_dict(d: Any) -> Evidence:
    if not isinstance(d, dict):
        raise ValueError("evidence record must be a dict")
    return Evidence(
        quote=str(d.get("quote") or ""),
        uri=str(d.get("uri") or ""),
        ts=_as_float(d.get("ts")),
        session=str(d.get("session") or ""),
        source=str(d.get("source") or ""),
    )


def _edit_from_dict(d: Any) -> EditOp:
    if not isinstance(d, dict):
        raise ValueError("edit record must be a dict")
    path = str(d.get("path") or "")
    op = str(d.get("op") or "")
    if not path or not op:
        raise ValueError("edit record needs both a path and an op")
    return EditOp(
        path=path,
        op=op,
        text=str(d.get("text") or ""),
        anchor=str(d.get("anchor") or ""),
        old=str(d.get("old") or ""),
        note=str(d.get("note") or ""),
    )


# -- helpers -----------------------------------------------------------------


def _resolve(entries: dict[str, dict[str, Any]], prefix: str) -> str | None:
    """Full fingerprint for a prefix, or None. Raises on an ambiguous prefix."""
    key = (prefix or "").strip().lower()
    if not key:
        return None
    if key in entries:
        return key  # an exact hit is never ambiguous, whatever else shares its head
    matches = sorted(fp for fp in entries if fp.startswith(key))
    if not matches:
        return None
    if len(matches) > 1:
        shown = ", ".join(m[: PREFIX_LEN + 4] for m in matches[:6])
        more = "" if len(matches) <= 6 else f" (and {len(matches) - 6} more)"
        raise ValueError(
            f"{prefix!r} matches {len(matches)} queued proposals: {shown}{more}. "
            f"Use more characters."
        )
    return matches[0]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _score_of(entry: dict[str, Any]) -> float:
    proposal = entry.get("proposal")
    return _as_float(proposal.get("score")) if isinstance(proposal, dict) else 0.0
