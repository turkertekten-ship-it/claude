"""The connector contract.

A connector's job is narrow on purpose: yield `RawDocument`s and keep a cursor
so the next run can be incremental. It does not chunk, embed, or index - those
are downstream stages that must not be re-implemented per source.

Incrementality is content-hash based rather than timestamp based. Timestamps
lie (mirrors, rebases, re-uploads, clock skew); a hash of the text does not.
Connectors may *additionally* use a cursor (a commit sha, an ETag, a since-date)
to avoid fetching bytes at all, which is faster but only ever an optimization
layered on top of the hash check.

That optimization is also the failure this module exists to prevent. A connector
that short-circuits on an unchanged head sha, or stops at a page budget, yields
a *subset* of its source; a base class that reads every run's yield as the
source's full inventory concludes that the 3,997 files it did not hear about
have been deleted, writes that conclusion into the cursor as the new hash map,
and then reports all 3,997 as brand new on the following run. One bad run of
accounting corrupts every run after it. So the rule here is: the hash map only
ever *grows*, and "gone" is only ever inferred from a run that both promised to
enumerate the whole source (`Connector.enumerates_source`) and actually reached
the end of the iterator.
"""

from __future__ import annotations

import contextlib
import copy
import json
import os
import tempfile
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from oodarag.models import IngestDelta, RawDocument
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("ingest")

#: Error strings ride in the delta, get printed by the CLI and end up in
#: reports, so they are bounded twice over: in length, because an exception
#: message can carry a whole response body, and in count, because a source that
#: fails 100k documents must not also cost 100k resident strings. `delta.failed`
#: keeps the true count either way.
MAX_ERROR_CHARS = 300
MAX_ERRORS = 50

#: Ceiling on tracked content hashes per source. The map only grows (see the
#: module docstring), so a source that renames every document daily would grow
#: the state file without bound - and that file is parsed in full at the start
#: of every run. Eviction costs one re-emit of a document nobody has seen in a
#: long time, which is the safe direction to be wrong in: it can turn a
#: "unchanged" into a "new", never a "changed" into an "unchanged".
MAX_TRACKED_HASHES = 100_000

#: Vanished documents named in the cursor. The untruncated total travels beside
#: it as "removed_count", so a reader of a capped list cannot mistake it for the
#: whole story - which is exactly what a bare `removed[:100]` invites.
MAX_REMOVED_REPORTED = 100


class StateStore(Protocol):
    """Where connectors persist their cursors between runs."""

    def get(self, key: str) -> dict[str, Any]: ...
    def set(self, key: str, value: dict[str, Any]) -> None: ...


class JsonStateStore:
    """File-backed state. Written atomically so a crash mid-write cannot
    corrupt the cursor and silently turn the next run into a full re-ingest.

    Reading is total. Every way a state file can be unusable - truncated JSON, a
    JSON document that is not an object, bytes that are not UTF-8, a directory
    where the file should be, a value that belongs to an older schema - degrades
    to "no state for that key". A nightly job that re-reads everything is an
    expensive night; a nightly job that raises on line one is an outage nobody
    notices until someone asks why the index stopped growing.

    Construction never raises. A state directory that cannot be created is
    reported when the write is attempted, by `set`, so the caller finds out
    with the run's documents already in hand rather than before it started.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, dict[str, Any]] = {}
        with contextlib.suppress(OSError):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text("utf-8"))
        except (ValueError, OSError) as e:
            # ValueError covers JSONDecodeError *and* the UnicodeDecodeError of a
            # file truncated mid-codepoint; OSError covers "it is a directory".
            log.warn("state file unreadable, starting clean", path=str(self.path), err=str(e))
            return
        if not isinstance(loaded, dict):
            log.warn("state file is not an object, starting clean", path=str(self.path))
            return
        self._data = {str(k): v for k, v in loaded.items() if isinstance(v, dict)}

    def get(self, key: str) -> dict[str, Any]:
        # Deep, not shallow: a cursor is a snapshot handed to the connector, and
        # a connector that edits the nested map it was given - `blob_shas`, say -
        # must not be editing what the store still holds. The copy is one dict
        # walk per run, against a crawl.
        value = self._data.get(key)
        return copy.deepcopy(value) if isinstance(value, dict) else {}

    def set(self, key: str, value: dict[str, Any]) -> None:
        # Copied in for the mirror-image reason: `_flush` rewrites every key, so
        # a caller that kept a reference and mutated it later would otherwise
        # smuggle those edits into some unrelated key's write.
        self._data[key] = copy.deepcopy(value)
        self._flush()

    def _flush(self) -> None:
        # Re-created rather than assumed: a long-lived process can outlive a
        # `rm -rf` of its state directory, and mkstemp below would then fail.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, default=str)
                fh.flush()
                # The rename is atomic; the bytes behind it are not. Without the
                # fsync a crash can leave the new name pointing at content the
                # page cache never wrote - the corrupt cursor this class exists
                # to rule out, arrived by the back door.
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise


class MemoryStateStore:
    """State for one process. Useful in tests and one-shot runs; note that it is
    not the same as passing no store at all, which means "re-ingest everything"."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any]:
        value = self._data.get(key)
        return copy.deepcopy(value) if isinstance(value, dict) else {}

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = copy.deepcopy(value)


@dataclass(slots=True)
class ConnectorResult:
    """Everything one connector run produced, plus how it went."""

    documents: list[RawDocument] = field(default_factory=list)
    delta: IngestDelta = field(default_factory=lambda: IngestDelta(source_key=""))
    cursor: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.documents)


class Connector(ABC):
    """Base class for every source connector."""

    #: Stable identifier for this connector instance, e.g. "github:owner/repo".
    #: It keys the cursor in the StateStore, so it must not change between runs
    #: for the same logical source.
    key: str = "connector"

    #: Free-form weight used by the reranker: how much this source is trusted
    #: relative to others. Official docs outrank a stranger's blog post.
    authority: float = 1.0

    #: Does `fetch` list the *whole* source on every run, or only the part its
    #: cursor decided was worth fetching? Defaults to no, because the expensive
    #: mistake is the one made by accident: a connector that skips unchanged
    #: blobs, obeys a page budget or gets 304s back yields a subset, and for it
    #: "I did not see it" says nothing at all about "it was deleted". Set this
    #: only if every run really does enumerate every document - and even then,
    #: removals are inferred only from runs that reached the end of the stream.
    enumerates_source: bool = False

    @abstractmethod
    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        """Yield documents. `cursor` is whatever this connector stored last run."""

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        """Cursor to persist after a successful run. Override to advance it."""
        return cursor

    def run(self, state: StateStore | None = None, limit: int | None = None) -> ConnectorResult:
        """Fetch documents and report a delta against the previous run.

        Errors from individual documents are counted and carried in the delta
        rather than raised: one unreadable file in a 4,000-file repository must
        not abort the ingest of the other 3,999. The same rule covers the source
        failing outright and the state store refusing the cursor - both are
        recorded, and neither throws away the documents already in hand.
        """
        started = time.monotonic()
        cursor = self._load_cursor(state)
        seen_hashes = _hash_map(cursor.get("hashes"))
        new_hashes: dict[str, str] = {}
        delta = IngestDelta(source_key=self.key)
        docs: list[RawDocument] = []
        # Did we reach the end of the source's stream? Only a run that did
        # can say anything about what is *missing* from the source.
        complete = True
        stream: Any = ()

        try:
            stream = self.fetch(cursor)
            for doc in stream:
                if limit is not None and len(docs) >= limit:
                    # The break is what makes this run a sample: whatever the
                    # iterator still held is unread, which is not the same thing
                    # as absent. Note it happens *before* the hash is recorded,
                    # so `new_hashes` is knowingly partial from here on.
                    complete = False
                    break
                external_id = str(getattr(doc, "external_id", "") or "")
                if not external_id:
                    # Downstream ids derive from it and so does the hash map; a
                    # document without one cannot be tracked, and admitting it
                    # would collapse every such document onto one key.
                    _record_failure(delta, type(doc).__name__, "document has no external_id")
                    continue
                if external_id in new_hashes:
                    _record_failure(delta, external_id, "duplicate external_id in one run")
                    continue
                try:
                    digest = doc.content_hash
                except Exception as e:  # a single malformed document
                    # It exists, we just could not read it. Carrying its prior
                    # hash keeps it out of the removed list now, and guarantees
                    # the next clean read counts as "changed" rather than
                    # "unchanged" - a document that failed was never delivered.
                    if (prior := seen_hashes.get(external_id)) is not None:
                        new_hashes[external_id] = prior
                    _record_failure(delta, external_id, f"{type(e).__name__}: {e}")
                    continue
                prior = seen_hashes.get(external_id)
                new_hashes[external_id] = digest
                if prior is None:
                    delta.new += 1
                elif prior != digest:
                    delta.changed += 1
                else:
                    delta.unchanged += 1
                    continue  # unchanged: nothing downstream needs to redo
                docs.append(doc)
        except Exception as e:  # the source itself failed
            complete = False
            _record_failure(delta, self.key, f"{type(e).__name__}: {e}")
            log.error("connector failed", key=self.key,
                      err=redact_secrets(str(e))[:MAX_ERROR_CHARS])
        finally:
            # A generator holding a socket, a subprocess or - like the web
            # connector - a report it only finalizes in its own `finally` must
            # be closed here, before we read the connector's state below.
            # Leaving that to the garbage collector works by luck in CPython and
            # not at all elsewhere.
            _close(stream)

        # Ordered least-recently-seen first so the cap evicts the entries least
        # likely to still exist at the source.
        stale = {k: v for k, v in seen_hashes.items() if k not in new_hashes}
        if complete and self.enumerates_source:
            # The only case where forgetting is right: this connector promised
            # to list everything and got to the end of the list. An empty run
            # then genuinely means an empty source, and the stale keys really
            # are gone.
            hashes = dict(new_hashes)
            removed = sorted(stale)
        else:
            # Everything else merges. In particular a run that yielded zero
            # documents keeps the old map rather than resetting it: for a
            # cursor-driven connector zero documents is the *success* case ("no
            # page changed"), and treating it as an empty source would both
            # declare every document deleted and re-ingest the lot next run.
            hashes = {**stale, **new_hashes}
            removed = []

        next_cursor = self._advance(cursor, delta)
        next_cursor["hashes"] = _bounded(hashes)
        next_cursor["last_run"] = time.time()
        next_cursor["complete_run"] = complete
        next_cursor["removed_last_run"] = removed[:MAX_REMOVED_REPORTED]
        next_cursor["removed_count"] = len(removed)
        if state is not None:
            try:
                state.set(self.key, next_cursor)
            except Exception as e:
                # The documents are real whether or not the cursor survived; the
                # cost is that the next run re-reads them. Staying quiet would
                # make an unwritable state directory look like a permanently
                # expensive source rather than a broken one.
                _record_failure(delta, f"{self.key}: cursor not persisted",
                                f"{type(e).__name__}: {e}")
                log.error("state write failed", key=self.key,
                          err=redact_secrets(str(e))[:MAX_ERROR_CHARS])
        delta.duration_s = round(time.monotonic() - started, 3)
        log.info(
            "connector run",
            key=self.key, new=delta.new, changed=delta.changed,
            unchanged=delta.unchanged, failed=delta.failed, removed=len(removed),
            complete=complete, secs=delta.duration_s,
        )
        return ConnectorResult(documents=docs, delta=delta, cursor=next_cursor)

    # ----------------------------------------------------------------- helpers

    def _load_cursor(self, state: StateStore | None) -> dict[str, Any]:
        """The stored cursor, or an empty one. A broken store is a slow run, not
        a failed one: everything it holds is reconstructible by re-reading."""
        if state is None:
            return {}
        try:
            cursor = state.get(self.key)
        except Exception as e:
            log.warn("state unreadable, running as if fresh", key=self.key,
                     err=f"{type(e).__name__}: {e}"[:MAX_ERROR_CHARS])
            return {}
        return cursor if isinstance(cursor, dict) else {}

    def _advance(self, cursor: dict[str, Any], delta: IngestDelta) -> dict[str, Any]:
        """`next_cursor` is connector code and can be wrong; the run is not its
        hostage. A refusal to advance holds the previous cursor, which is the
        conservative end: the next run redoes work, it does not skip it."""
        try:
            advanced = self.next_cursor(dict(cursor))
        except Exception as e:
            _record_failure(delta, f"{self.key}: next_cursor", f"{type(e).__name__}: {e}")
            log.error("next_cursor failed, holding the previous one", key=self.key,
                      err=redact_secrets(str(e))[:MAX_ERROR_CHARS])
            return dict(cursor)
        return advanced if isinstance(advanced, dict) else dict(cursor)


def _record_failure(delta: IngestDelta, subject: str, message: str) -> None:
    """Count one failure and, if there is room left, describe it.

    Messages are redacted before they are kept: they are built from exception
    text, which routinely carries the URL that failed, and that URL routinely
    carries a token. `delta.errors` is copied into logs, reports and issue
    bodies, none of which are a good place for one.
    """
    delta.failed += 1
    if len(delta.errors) < MAX_ERRORS:
        delta.errors.append(redact_secrets(f"{subject}: {message}")[:MAX_ERROR_CHARS])
    elif len(delta.errors) == MAX_ERRORS:
        delta.errors.append("... further errors suppressed; see the failed count")


def _hash_map(value: Any) -> dict[str, str]:
    """The stored hash map, or an empty one for anything that is not one.

    A state file is a file: it gets hand-edited, half-written by an older
    version of this code, or restored from a backup of a different source. Each
    of those has to cost a re-ingest, not an AttributeError on the first line of
    a nightly run. Entries that are not `str -> str` are dropped rather than
    coerced, so a mangled entry re-reads its document instead of comparing a
    hash against something that was never one.
    """
    if not isinstance(value, dict):
        return {}
    return {str(k): v for k, v in value.items() if isinstance(v, str)}


def _bounded(hashes: dict[str, str]) -> dict[str, str]:
    """Trim the hash map to `MAX_TRACKED_HASHES`, oldest entries first."""
    excess = len(hashes) - MAX_TRACKED_HASHES
    if excess <= 0:
        return hashes
    log.warn("hash map full, forgetting the oldest entries",
             cap=MAX_TRACKED_HASHES, dropped=excess)
    return dict(list(hashes.items())[excess:])


def _close(stream: Any) -> None:
    """Release a `fetch` iterator we may have stopped pulling from."""
    closer = getattr(stream, "close", None)
    if closer is None:
        return
    try:
        closer()
    except Exception as e:
        log.warn("closing the fetch stream failed",
                 err=f"{type(e).__name__}: {e}"[:MAX_ERROR_CHARS])
