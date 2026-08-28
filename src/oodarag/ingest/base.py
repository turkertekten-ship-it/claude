"""The connector contract.

A connector's job is narrow on purpose: yield `RawDocument`s and keep a cursor
so the next run can be incremental. It does not chunk, embed, or index - those
are downstream stages that must not be re-implemented per source.

Incrementality is content-hash based rather than timestamp based. Timestamps
lie (mirrors, rebases, re-uploads, clock skew); a hash of the text does not.
Connectors may *additionally* use a cursor (a commit sha, an ETag, a since-date)
to avoid fetching bytes at all, which is faster but only ever an optimization
layered on top of the hash check.
"""

from __future__ import annotations

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

log = get_logger("ingest")


class StateStore(Protocol):
    """Where connectors persist their cursors between runs."""

    def get(self, key: str) -> dict[str, Any]: ...
    def set(self, key: str, value: dict[str, Any]) -> None: ...


class JsonStateStore:
    """File-backed state. Written atomically so a crash mid-write cannot
    corrupt the cursor and silently turn the next run into a full re-ingest."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                log.warn("state file unreadable, starting clean", path=str(self.path), err=str(e))
                loaded = {}
            # Well-formed JSON that is not an object is still not a state file:
            # a truncated write that landed as `[]`, or a hand-edit. Only
            # `JSONDecodeError` was caught, so that file raised `AttributeError`
            # from `get()` on the next run - the one failure mode this class
            # exists to prevent, reached by a different door.
            if not isinstance(loaded, dict):
                log.warn("state file is not an object, starting clean", path=str(self.path))
                loaded = {}
            self._data = loaded

    def get(self, key: str) -> dict[str, Any]:
        value = self._data.get(key, {})
        return dict(value) if isinstance(value, dict) else {}

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value
        self._flush()

    def _flush(self) -> None:
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, default=str)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise


class MemoryStateStore:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any]:
        return dict(self._data.get(key, {}))

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value


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

    @abstractmethod
    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        """Yield documents. `cursor` is whatever this connector stored last run."""

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        """Cursor to persist after a successful run. Override to advance it."""
        return cursor

    def unchanged_external_ids(self) -> set[str]:
        """Ids the source confirmed unchanged *without* sending their bytes.

        Every cost optimisation in this pipeline works by not transferring
        something: a 304 from a conditional GET, a git blob sha that matches the
        stored one, a head commit that has not moved. Each of those means "this
        document is still there and still the same" - but the document is then
        never yielded, and a base class that infers absence from silence reads it
        as a deletion.

        That is not hypothetical. Measured against the real GitHub API: a second
        run over an unchanged repository took the head-sha short circuit, yielded
        nothing, and the run reported every file in the corpus in
        `removed_last_run` while dropping every stored hash - so the saving
        proposed wiping the index and then paid for a full re-ingest on the run
        after. Override this and the ids are carried forward and counted as
        unchanged instead.
        """
        return set()

    def run(self, state: StateStore | None = None, limit: int | None = None) -> ConnectorResult:
        """Fetch documents and report a delta against the previous run.

        Errors from individual documents are counted and carried in the delta
        rather than raised: one unreadable file in a 4,000-file repository must
        not abort the ingest of the other 3,999.
        """
        started = time.monotonic()
        cursor = state.get(self.key) if state else {}
        seen_hashes: dict[str, str] = dict(cursor.get("hashes", {}))
        new_hashes: dict[str, str] = {}
        delta = IngestDelta(source_key=self.key)
        docs: list[RawDocument] = []
        #: Did the walk see the whole source? Only a complete walk can tell
        #: "this document is gone" from "this document was never reached".
        walked_whole_source = True

        try:
            for doc in self.fetch(cursor):
                if limit is not None and len(docs) >= limit:
                    walked_whole_source = False
                    break
                try:
                    digest = doc.content_hash
                    prior = seen_hashes.get(doc.external_id)
                    new_hashes[doc.external_id] = digest
                    if prior is None:
                        delta.new += 1
                    elif prior != digest:
                        delta.changed += 1
                    else:
                        delta.unchanged += 1
                        continue  # unchanged: nothing downstream needs to redo
                    docs.append(doc)
                except Exception as e:  # a single malformed document
                    delta.failed += 1
                    delta.errors.append(f"{doc.external_id}: {type(e).__name__}: {e}")
                    # A document we could not read has not vanished from the
                    # source. Carrying its previous hash forward keeps it out of
                    # `removed_last_run` - downstream deletion is driven off
                    # that list - and stops one bad parse from re-ingesting a
                    # document that never changed.
                    if (stale := seen_hashes.get(doc.external_id)) is not None:
                        new_hashes[doc.external_id] = stale
        except Exception as e:  # the source itself failed
            walked_whole_source = False
            delta.failed += 1
            delta.errors.append(f"{self.key}: {type(e).__name__}: {e}")
            log.error("connector failed", key=self.key, err=str(e)[:300])

        # Documents the source confirmed unchanged without sending bytes. Their
        # previous hash is carried forward so they are neither re-ingested nor
        # mistaken for deletions.
        for external_id in sorted(self.unchanged_external_ids()):
            if external_id in new_hashes:
                continue  # it was yielded after all; the loop already classified it
            prior = seen_hashes.get(external_id)
            if prior is None:
                continue  # never seen before, so "unchanged" says nothing
            new_hashes[external_id] = prior
            delta.unchanged += 1

        # Documents that vanished from the source are reported, not deleted here;
        # deletion is an explicit downstream action so a transient empty response
        # can never wipe an index.
        if walked_whole_source:
            removed = [k for k in seen_hashes if k not in new_hashes]
            hashes = new_hashes
        else:
            # A truncated walk saw a prefix of the source, so absence proves
            # nothing. This used to be approximated by `new_hashes or
            # seen_hashes`, which only covered the all-or-nothing case: a source
            # that failed after its first document reported the other 3,999 as
            # removed and dropped their hashes, so the next run re-ingested the
            # whole repository as new. The same expression was wrong in the
            # other direction on a source that legitimately went empty - the
            # stale hashes were kept, so if those documents ever came back
            # byte-identical they were classified "unchanged", never re-emitted,
            # and stayed missing from the index for good.
            removed = []
            hashes = {**seen_hashes, **new_hashes}
        delta.duration_s = round(time.monotonic() - started, 3)
        next_cursor = self.next_cursor(dict(cursor))
        next_cursor["hashes"] = hashes
        next_cursor["last_run"] = time.time()
        next_cursor["removed_last_run"] = removed[:100]
        if state:
            state.set(self.key, next_cursor)
        log.info(
            "connector run",
            key=self.key, new=delta.new, changed=delta.changed,
            unchanged=delta.unchanged, failed=delta.failed, secs=delta.duration_s,
        )
        return ConnectorResult(documents=docs, delta=delta, cursor=next_cursor)
