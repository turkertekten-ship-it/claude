"""The one module in the loop that writes to the user's files.

Everything upstream of here is advisory. A source that misreads a history file
produces a bad signal; a detector with a bug produces a bad finding; a policy
that mis-scores produces a bad ranking - and all of it stays words on a screen.
This module is where the words become bytes on someone's disk, at night, with
nobody watching, so this is where the paranoia lives. Each guarantee below is
re-checked *here*, at the last possible moment, rather than trusted to have held
somewhere further up the chain: a detector already refuses to emit an edit that
escapes the workspace, and that is not a reason for the actuator to assume it.

Five invariants, in the order a write meets them:

1. **Containment.** The target resolves inside `root` or it is not written.
   Absolute paths, `..`, and symlinks that lead out of the tree are rejected by
   name. A rule with a path bug must not be able to reach `/etc`.
2. **Preconditions.** Every op states a condition it can be checked against
   before anything is opened for writing - `create` needs an absent file,
   `replace` needs its `old` to be unambiguous. The file may well have changed
   since the proposal was written, and the right response to that is to skip,
   never to force.
3. **All-or-nothing, per proposal.** Preconditions for *every* op are evaluated
   against a simulated file tree first. If one fails, none are applied. A
   half-applied proposal is worse than an unapplied one: it is a state nobody
   designed and nobody reviewed.
4. **Backup before write.** The original is copied under
   `backup_root/<cycle_id>/` with a manifest, so `revert` is a mechanical
   operation over a record rather than an attempt to reconstruct intent.
5. **Atomic write.** A temp file in the same directory, then `os.replace`. A
   crash - or a laptop lid - must never leave a source file half written.

Dry run is the default, and the diff a dry run prints is produced by exactly the
planning code a real run then applies. That is the whole point: `--apply` is
never allowed to be a surprise, because if the diff was wrong, nothing had been
written yet.
"""

from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from oodarag.reflect.models import EditOp, Proposal
from oodarag.util.logging import get_logger

log = get_logger("reflect.act")

#: Per-cycle backup index. The name is reserved: a workspace file called
#: `manifest.json` at the root is backed up as `manifest.json.orig`, because a
#: backup that overwrites the index describing it is not a backup.
MANIFEST_NAME = "manifest.json"

#: Refuse to rewrite anything larger. Every op here is line- or
#: substring-oriented, so a 40 MB file is not a document this module
#: understands, and holding two copies of it in memory to diff them is how a
#: nightly job gets OOM-killed instead of finishing.
DEFAULT_MAX_BYTES = 2_000_000

#: Mode for files the loop creates. `mkstemp` makes 0600, which would leave a
#: freshly created README readable only by its owner - a confusing artefact of
#: how it was written rather than a decision anyone made.
NEW_FILE_MODE = 0o644

#: A cycle id is generated internally and then used as a directory name.
#: "Generated internally" is also how most of the directory traversals in the
#: wild were described, so it is squeezed through this on the way to a path.
_CYCLE_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")

_STATUS_OK = "ok"      # would change the file
_STATUS_NOOP = "noop"  # already in the desired state; not a failure
_STATUS_FAIL = "fail"  # precondition violated; blocks the whole proposal


# -- text helpers -------------------------------------------------------------


def _ensure_final_newline(text: str) -> str:
    if not text or text.endswith("\n"):
        return text
    return text + "\n"


def _preserve_trailing_newline(original: str, updated: str) -> str:
    """Keep the file's own final-newline convention across an edit.

    A file that ended with a newline still does; one that did not, still does
    not. Both directions matter - the first because `"\\n".join(lines)` quietly
    eating a trailing newline is the single most common way an automated edit
    shows up as noise in someone's diff, the second because adding one is the
    same noise with the sign flipped. An empty or brand-new file counts as
    "ends with a newline", since that is what a text file normally does.
    """
    if not updated:
        return updated
    ends = original.endswith("\n") or not original
    if ends and not updated.endswith("\n"):
        return updated + "\n"
    if not ends and updated.endswith("\n"):
        return updated[:-1]
    return updated


def _heading_level(line: str) -> int:
    """ATX heading depth (`## Foo` -> 2), or 0 for a line that is not one."""
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return 0
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if hashes > 6:
        return 0
    rest = stripped[hashes:]
    if rest and not rest[0].isspace():
        return 0  # "#tag" and "#!/bin/sh" are not headings
    return hashes


def find_anchor(lines: list[str], anchor: str) -> int | None:
    """Index of the line an anchor names, or None.

    Two passes, and the order is the point: a whole-line match first, so an
    anchor like `.PHONY: test` cannot land on `.PHONY: test-integration`, and
    only then a containment match, so an anchor that was written from memory
    ("## Conventions" against "## Conventions <!-- generated -->") still finds
    its heading instead of silently appending a second one.
    """
    needle = anchor.strip()
    if not needle:
        return None
    for i, line in enumerate(lines):
        if line.strip() == needle:
            return i
    for i, line in enumerate(lines):
        if needle in line:
            return i
    return None


def section_end(lines: list[str], start: int) -> int:
    """Index just past the last line belonging to the section opened at `start`.

    The section runs to the next heading of the same or a higher level, or to
    EOF. Fenced code blocks are skipped, because a `# comment` inside a shell
    example is not a heading and a loop that thinks it is will insert text into
    the middle of somebody's snippet.

    An anchor that is not a heading at all (a `.PHONY:` line, a delimiter
    comment) opens a region with no syntactic end, so it runs to EOF - which is
    also the only sane place to add another entry to that kind of list.
    """
    level = _heading_level(lines[start]) if start < len(lines) else 0
    if level == 0:
        return len(lines)
    fenced = False
    for i in range(start + 1, len(lines)):
        stripped = lines[i].lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fenced = not fenced
            continue
        if fenced:
            continue
        found = _heading_level(lines[i])
        if found and found <= level:
            return i
    return len(lines)


def unified_diff(rel: str, old: str, new: str) -> str:
    """The diff a human reviews, and the only thing a dry run produces.

    Line ends are dropped before diffing rather than kept: a file with no final
    newline otherwise splices its last line onto the next diff line, and a
    review artefact that renders wrong on exactly the files most likely to be
    hand-edited is not worth the fidelity it buys.
    """
    lines = difflib.unified_diff(
        old.splitlines(), new.splitlines(), fromfile=rel, tofile=rel, lineterm=""
    )
    text = "\n".join(lines)
    return text + "\n" if text else ""


def diff_bytes(diff: str) -> int:
    """The size of the change, not the change in size.

    A replacement of equal length changes zero bytes by subtraction and is
    plainly not nothing, so this counts the bytes on the added and removed lines
    instead. It is reported for skipped and dry-run edits too: the question it
    answers is "how big is this edit", which has the same answer either way.
    """
    total = 0
    for line in diff.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        if line.startswith(("+", "-")):
            total += len(line[1:].encode("utf-8", "replace"))
    return total


def _sha256_path(path: Path) -> str:
    """A real digest of the file's bytes, so `sha256sum` on the backup agrees."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for block in iter(lambda: fh.read(65_536), b""):
                h.update(block)
    except OSError:
        return ""
    return h.hexdigest()


def _safe_cycle_id(cycle_id: str) -> str:
    cleaned = _CYCLE_SAFE_RE.sub("_", (cycle_id or "").strip()).strip("._-")
    return cleaned or "unknown"


# -- results ------------------------------------------------------------------


@dataclass(slots=True)
class EditResult:
    """What became of one `EditOp`.

    `reason` is populated whenever `applied` is false, and it is written to be
    read by a person at breakfast: "exists", "old text appears 3 times",
    "blocked by an earlier edit in this proposal". A silent skip is the failure
    mode that makes a nightly loop untrustworthy - it looks identical to a loop
    that had nothing to do.
    """

    path: str
    op: str
    applied: bool = False
    reason: str = ""
    diff: str = ""
    bytes_changed: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ApplyReport:
    """Everything one call to the actuator did, or would have done."""

    cycle_id: str
    results: list[EditResult] = field(default_factory=list)
    backup_dir: str = ""

    @property
    def applied_count(self) -> int:
        return sum(1 for r in self.results if r.applied)

    @property
    def failed_count(self) -> int:
        """Everything that did not land - failed, skipped, or merely a dry run.

        Deliberately not three counters. The caller that cares about the
        difference reads `reason`; the caller that does not care wants one
        number meaning "not done".
        """
        return sum(1 for r in self.results if not r.applied)

    @property
    def total_bytes(self) -> int:
        return sum(r.bytes_changed for r in self.results)

    @property
    def paths(self) -> list[str]:
        seen: list[str] = []
        for r in self.results:
            if r.path not in seen:
                seen.append(r.path)
        return seen

    def as_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "backup_dir": self.backup_dir,
            "applied": self.applied_count,
            "failed": self.failed_count,
            "bytes_changed": self.total_bytes,
            "results": [r.as_dict() for r in self.results],
        }


@dataclass(slots=True)
class _Planned:
    """One op, resolved and simulated, before anything has been written."""

    op: EditOp
    target: Path
    rel: str
    before: str | None
    after: str
    status: str
    reason: str = ""
    diff: str = ""
    bytes_changed: int = 0


# -- the operations -----------------------------------------------------------


def _op_append(current: str, addition: str) -> str:
    body = current
    if body and not body.endswith("\n"):
        body += "\n"  # never glue onto a last line that has no newline
    return _preserve_trailing_newline(current, body + addition)


def _op_insert_after(current: str, anchor: str, addition: str) -> tuple[str, str, str]:
    lines = current.splitlines(keepends=True)
    idx = find_anchor(lines, anchor)
    if idx is None:
        return (_STATUS_FAIL, "", "anchor not found")
    if not lines[idx].endswith("\n"):
        lines[idx] += "\n"
    lines.insert(idx + 1, _ensure_final_newline(addition))
    return (_STATUS_OK, _preserve_trailing_newline(current, "".join(lines)), "")


def _op_ensure_section(current: str, anchor: str, addition: str) -> tuple[str, str, str]:
    """Append to a section the loop owns, creating the section if need be.

    Idempotency is load-bearing here in a way it is not for the other ops: this
    is the op every "write it down so you stop re-explaining it" rule reaches
    for, and it is re-proposed every single night until the underlying habit
    changes. A version of this that appended unconditionally would turn a memory
    file into a hundred copies of one bullet inside a fortnight, which is
    exactly the failure that makes people delete the tool.
    """
    if addition and addition in current:
        return (_STATUS_NOOP, current, "already present")
    block = _ensure_final_newline(addition)
    lines = current.splitlines(keepends=True)
    idx = find_anchor(lines, anchor)
    if idx is None:
        body = current
        if body and not body.endswith("\n"):
            body += "\n"
        if body and not body.endswith("\n\n"):
            body += "\n"  # a heading gets a blank line above it
        merged = body + anchor.rstrip("\n") + "\n\n" + block
        return (_STATUS_OK, _preserve_trailing_newline(current, merged), "")
    end = section_end(lines, idx)
    # The end of a section means after its last line of content, not after the
    # blank lines that separate it from whatever comes next - otherwise every
    # addition lands flush against the following heading.
    while end > idx + 1 and not lines[end - 1].strip():
        end -= 1
    if end > 0 and not lines[end - 1].endswith("\n"):
        lines[end - 1] += "\n"
    lines.insert(end, block)
    return (_STATUS_OK, _preserve_trailing_newline(current, "".join(lines)), "")


def plan_op(op: EditOp, before: str | None) -> tuple[str, str, str]:
    """Simulate one op against `before` (None = the file is absent).

    Returns `(status, text, reason)`. Pure: it reads no filesystem and writes
    nothing, which is what lets the dry-run diff be the same object the real run
    later commits rather than a second implementation that drifts from it.
    """
    kind = op.op
    if kind == "create":
        if before is not None:
            return (_STATUS_FAIL, "", "exists")
        return (_STATUS_OK, _ensure_final_newline(op.text), "")

    if before is None:
        return (_STATUS_FAIL, "", "file does not exist")

    if kind == "append":
        return (_STATUS_OK, _op_append(before, op.text), "")

    if kind == "replace":
        if not op.old:
            return (_STATUS_FAIL, "", "replace needs `old`")
        count = before.count(op.old)
        if count == 0:
            return (_STATUS_FAIL, "", "old text not found")
        if count > 1:
            # Ambiguity is not resolvable from here, and guessing which of three
            # matches the rule meant is how an automated edit lands in the wrong
            # function at 3am.
            return (_STATUS_FAIL, "", f"old text appears {count} times, expected exactly once")
        updated = before.replace(op.old, op.text, 1)
        return (_STATUS_OK, _preserve_trailing_newline(before, updated), "")

    if kind == "insert_after":
        if not op.anchor:
            return (_STATUS_FAIL, "", "insert_after needs an `anchor`")
        return _op_insert_after(before, op.anchor, op.text)

    if kind == "ensure_section":
        if not op.anchor:
            return (_STATUS_FAIL, "", "ensure_section needs an `anchor`")
        return _op_ensure_section(before, op.anchor, op.text)

    return (_STATUS_FAIL, "", f"unknown op: {kind}")


# -- the actuator -------------------------------------------------------------


class EditApplier:
    """Applies proposals to a workspace, or shows what it would apply.

    `dry_run` is the default and is honoured by `revert` as well: a class whose
    safety depends on remembering to pass a flag is a class that will one day be
    constructed without it.
    """

    def __init__(
        self,
        root: Path | str,
        backup_root: Path | str,
        dry_run: bool = True,
        max_bytes: int = DEFAULT_MAX_BYTES,
    ) -> None:
        self.root = Path(root).resolve()
        self.backup_root = Path(backup_root)
        self.dry_run = dry_run
        self.max_bytes = max_bytes

    # -- containment ---------------------------------------------------------

    def _resolve(self, relpath: str) -> tuple[Path, str, str]:
        """`(target, rel, error)`. A non-empty error means: do not write this.

        Resolution happens before the containment test, not after, because the
        interesting attack is not a literal `../../etc` - the detector base
        already rejects those - but a directory inside the workspace that is a
        symlink to somewhere outside it. Only a resolved path can answer that.
        """
        raw = (relpath or "").strip()
        if not raw:
            return (self.root, "", "empty path")
        candidate = Path(raw)
        if candidate.is_absolute():
            return (self.root, raw, "absolute paths are never applied")
        if ".." in candidate.parts:
            return (self.root, raw, "path contains '..'")
        unresolved = self.root / candidate
        try:
            if unresolved.is_symlink():
                # Replacing a symlink atomically replaces the *link* with a
                # regular file, which silently changes something the user set up
                # on purpose. Following it instead would edit a file the
                # proposal never named. Neither is ours to choose.
                return (self.root, raw, "target is a symlink")
            target = unresolved.resolve()
            rel = target.relative_to(self.root)
        except (OSError, RuntimeError, ValueError):
            return (self.root, raw, "path escapes the workspace root")
        return (target, str(rel), "")

    def _load(self, target: Path) -> tuple[str | None, str]:
        """`(text, error)`. `(None, "")` means the file is simply not there."""
        try:
            if not target.exists():
                return (None, "")
            if not target.is_file():
                return (None, "not a regular file")
            size = target.stat().st_size
            if size > self.max_bytes:
                return (None, f"file is larger than {self.max_bytes} bytes")
            raw = target.read_bytes()
        except (OSError, ValueError) as e:
            return (None, f"unreadable: {type(e).__name__}")
        try:
            # Strict, unlike every read elsewhere in the subsystem. A source
            # that mangles one character produces a slightly wrong signal; a
            # writer that decodes with "replace" and writes the result back
            # destroys the bytes it could not understand.
            return (raw.decode("utf-8"), "")
        except UnicodeDecodeError:
            return (None, "not utf-8 text")

    # -- planning ------------------------------------------------------------

    def _plan(self, proposal: Proposal) -> list[_Planned]:
        """Simulate the whole proposal against an overlay of the real tree.

        The overlay is what makes a proposal that creates a file and then
        appends to it verifiable: the second op is checked against what the
        first would have produced, not against a disk state that no longer
        applies by the time it runs.
        """
        overlay: dict[Path, str] = {}
        planned: list[_Planned] = []
        for op in proposal.edits:
            target, rel, err = self._resolve(op.path)
            if err:
                log.warn("edit rejected", path=op.path, op=op.op, reason=err)
                planned.append(
                    _Planned(op, target, rel, None, "", _STATUS_FAIL, err)
                )
                continue
            if target in overlay:
                before: str | None = overlay[target]
                read_err = ""
            else:
                before, read_err = self._load(target)
            if read_err:
                planned.append(_Planned(op, target, rel, None, "", _STATUS_FAIL, read_err))
                continue
            status, after, reason = plan_op(op, before)
            if status == _STATUS_OK and len(after.encode("utf-8")) > self.max_bytes:
                status, reason = _STATUS_FAIL, f"result would exceed {self.max_bytes} bytes"
            if status == _STATUS_OK and after == before:
                status, reason = _STATUS_NOOP, "no change"
            entry = _Planned(op, target, rel, before, after, status, reason)
            if status == _STATUS_OK:
                entry.diff = unified_diff(op.path, before or "", after)
                entry.bytes_changed = diff_bytes(entry.diff)
                overlay[target] = after
            planned.append(entry)
        return planned

    # -- applying ------------------------------------------------------------

    def apply(self, proposal: Proposal, cycle_id: str) -> ApplyReport:
        return self.apply_all([proposal], cycle_id)

    def apply_all(self, proposals: list[Proposal], cycle_id: str) -> ApplyReport:
        """Apply each proposal independently; one bad proposal costs only itself.

        The backup manifest is shared across the cycle and merged with whatever
        an earlier call already wrote, so `apply` twice and `apply_all` once
        leave the same recoverable state behind.
        """
        cycle_dir = self.backup_root / _safe_cycle_id(cycle_id)
        report = ApplyReport(cycle_id=cycle_id, backup_dir=str(cycle_dir))
        manifest = self._load_manifest(cycle_dir)
        index = {str(e.get("path")) for e in manifest}
        for proposal in proposals:
            report.results.extend(self._apply_one(proposal, cycle_dir, manifest, index))
        log.info(
            "edits done",
            cycle=cycle_id,
            applied=report.applied_count,
            failed=report.failed_count,
            dry_run=self.dry_run,
        )
        return report

    def _apply_one(
        self,
        proposal: Proposal,
        cycle_dir: Path,
        manifest: list[dict[str, Any]],
        index: set[str],
    ) -> list[EditResult]:
        planned = self._plan(proposal)
        if not planned:
            return []
        blocker = next((p for p in planned if p.status == _STATUS_FAIL), None)
        if blocker is not None:
            log.warn(
                "proposal not applied",
                title=proposal.title[:80],
                path=blocker.op.path,
                reason=blocker.reason,
            )
            return [self._blocked_result(p, blocker) for p in planned]
        if self.dry_run:
            return [
                EditResult(
                    path=p.op.path,
                    op=p.op.op,
                    applied=False,
                    reason=p.reason or "dry run",
                    diff=p.diff,
                    bytes_changed=p.bytes_changed,
                )
                for p in planned
            ]
        return self._commit(planned, cycle_dir, manifest, index)

    @staticmethod
    def _blocked_result(entry: _Planned, blocker: _Planned) -> EditResult:
        if entry is blocker or entry.status == _STATUS_FAIL:
            reason = entry.reason
        else:
            reason = f"blocked by {blocker.op.path}: {blocker.reason}"
        return EditResult(
            path=entry.op.path,
            op=entry.op.op,
            applied=False,
            reason=reason,
            diff=entry.diff,
            bytes_changed=entry.bytes_changed,
        )

    def _commit(
        self,
        planned: list[_Planned],
        cycle_dir: Path,
        manifest: list[dict[str, Any]],
        index: set[str],
    ) -> list[EditResult]:
        todo = [p for p in planned if p.status == _STATUS_OK]
        if not todo:
            return [
                EditResult(path=p.op.path, op=p.op.op, applied=False, reason=p.reason)
                for p in planned
            ]
        try:
            for entry in todo:
                self._backup(entry, cycle_dir, manifest, index)
            # The manifest is written *before* the files it describes are
            # touched. A crash between the two costs a redundant backup; a crash
            # the other way round costs the ability to undo the night.
            self._write_manifest(cycle_dir, manifest)
        except OSError as e:
            reason = f"backup failed: {type(e).__name__}: {e}"
            log.error("backup failed, nothing written", dir=str(cycle_dir), err=str(e)[:200])
            return [
                EditResult(path=p.op.path, op=p.op.op, applied=False, reason=reason, diff=p.diff)
                for p in planned
            ]

        written: list[_Planned] = []
        try:
            for entry in todo:
                self._write(entry.target, entry.after)
                written.append(entry)
        except OSError as e:
            # Preconditions cannot fail here - they were all checked - so this is
            # a disk saying no. Put back what we already changed rather than
            # leaving the proposal half landed.
            self._rollback(written)
            reason = f"write failed: {type(e).__name__}: {e}"
            log.error("write failed, proposal rolled back", err=str(e)[:200])
            return [
                EditResult(path=p.op.path, op=p.op.op, applied=False, reason=reason, diff=p.diff)
                for p in planned
            ]

        results: list[EditResult] = []
        for entry in planned:
            applied = entry.status == _STATUS_OK
            results.append(
                EditResult(
                    path=entry.op.path,
                    op=entry.op.op,
                    applied=applied,
                    reason="" if applied else entry.reason,
                    diff=entry.diff,
                    bytes_changed=entry.bytes_changed,
                )
            )
        return results

    def _rollback(self, written: list[_Planned]) -> None:
        for entry in reversed(written):
            try:
                if entry.before is None:
                    entry.target.unlink(missing_ok=True)
                else:
                    self._write(entry.target, entry.before)
            except OSError as e:  # best effort; the backup is still on disk
                log.error("rollback failed", path=entry.rel, err=str(e)[:200])

    # -- disk ----------------------------------------------------------------

    def _write(self, target: Path, text: str) -> None:
        """Atomic replace, preserving the file's mode.

        Without the `chmod`, every file the loop touches inherits `mkstemp`'s
        0600 and an executable script quietly stops being executable - a change
        nobody proposed, reviewed, or would think to look for.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = NEW_FILE_MODE
        try:
            mode = stat.S_IMODE(target.stat().st_mode)
        except OSError:
            pass
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=".reflect-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.chmod(tmp, mode)
            os.replace(tmp, target)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise

    def _write_manifest(self, cycle_dir: Path, manifest: list[dict[str, Any]]) -> None:
        cycle_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"cycle_dir": str(cycle_dir), "entries": manifest}, indent=2, ensure_ascii=False
        )
        self._write(cycle_dir / MANIFEST_NAME, payload + "\n")

    def _load_manifest(self, cycle_dir: Path) -> list[dict[str, Any]]:
        path = cycle_dir / MANIFEST_NAME
        try:
            data = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            return []
        if isinstance(data, dict):
            data = data.get("entries")
        if not isinstance(data, list):
            return []
        return [e for e in data if isinstance(e, dict) and e.get("path")]

    def _backup(
        self,
        entry: _Planned,
        cycle_dir: Path,
        manifest: list[dict[str, Any]],
        index: set[str],
    ) -> None:
        """Copy the original aside, once per cycle per path.

        Once, not once per proposal: if two proposals touch the same file, the
        state to restore is the one from before the *first* of them, and a
        second backup would overwrite it with a half-edited copy.
        """
        if entry.rel in index:
            return
        name = entry.rel + ".orig" if entry.rel == MANIFEST_NAME else entry.rel
        existed = entry.before is not None
        digest = ""
        if existed:
            dest = cycle_dir / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry.target, dest)
            digest = _sha256_path(dest)
        manifest.append(
            {
                "path": entry.rel,
                "op": entry.op.op,
                # False for a create, which is what tells revert to delete the
                # file rather than restore a backup that was never made.
                "existed_before": existed,
                "sha256": digest,
                "backup": name if existed else "",
            }
        )
        index.add(entry.rel)

    # -- revert --------------------------------------------------------------

    def revert(self, cycle_id: str) -> ApplyReport:
        """Undo one cycle from its manifest. Safe to run twice, and to run late.

        Reverting walks the manifest backwards and re-checks containment on
        every path in it: the manifest is a file on disk like any other, and a
        module whose entire job is refusing to write outside the workspace does
        not get to make an exception for its own bookkeeping.

        Running it a second time is a no-op rather than an error, because the
        realistic sequence is a person running it, being unsure it worked, and
        running it again.
        """
        cycle_dir = self.backup_root / _safe_cycle_id(cycle_id)
        report = ApplyReport(cycle_id=cycle_id, backup_dir=str(cycle_dir))
        entries = self._load_manifest(cycle_dir)
        if not entries:
            log.warn("nothing to revert", cycle=cycle_id, dir=str(cycle_dir))
            return report
        for entry in reversed(entries):
            report.results.append(self._revert_one(entry, cycle_dir))
        log.info(
            "revert done",
            cycle=cycle_id,
            restored=report.applied_count,
            skipped=report.failed_count,
            dry_run=self.dry_run,
        )
        return report

    def _revert_one(self, entry: dict[str, Any], cycle_dir: Path) -> EditResult:
        rel = str(entry.get("path") or "")
        existed = bool(entry.get("existed_before"))
        op = "restore" if existed else "delete"
        target, _resolved, err = self._resolve(rel)
        if err:
            log.warn("manifest entry rejected", path=rel, reason=err)
            return EditResult(path=rel, op=op, applied=False, reason=err)
        current, read_err = self._load(target)
        if read_err:
            return EditResult(path=rel, op=op, applied=False, reason=read_err)

        if not existed:
            if current is None and not target.exists():
                return EditResult(path=rel, op=op, applied=False, reason="already absent")
            diff = unified_diff(rel, current or "", "")
            if self.dry_run:
                return EditResult(
                    path=rel, op=op, reason="dry run", diff=diff, bytes_changed=diff_bytes(diff)
                )
            try:
                target.unlink()
            except OSError as e:
                return EditResult(path=rel, op=op, applied=False, reason=f"unlink failed: {e}")
            return EditResult(
                path=rel, op=op, applied=True, diff=diff, bytes_changed=diff_bytes(diff)
            )

        source = cycle_dir / str(entry.get("backup") or rel)
        try:
            source.resolve().relative_to(cycle_dir.resolve())
        except (OSError, ValueError):
            reason = "backup path escapes the cycle directory"
            return EditResult(path=rel, op=op, applied=False, reason=reason)
        original, backup_err = self._load(source)
        if original is None:
            return EditResult(
                path=rel, op=op, applied=False, reason=backup_err or "backup file missing"
            )
        if current == original:
            return EditResult(path=rel, op=op, applied=False, reason="already matches backup")
        diff = unified_diff(rel, current or "", original)
        if self.dry_run:
            return EditResult(
                path=rel, op=op, reason="dry run", diff=diff, bytes_changed=diff_bytes(diff)
            )
        try:
            self._write(target, original)
        except OSError as e:
            return EditResult(path=rel, op=op, applied=False, reason=f"restore failed: {e}")
        return EditResult(path=rel, op=op, applied=True, diff=diff, bytes_changed=diff_bytes(diff))
