"""Embedder selection, the hosted-API client, and the cache in front of both.

Three separate jobs live here because they share one invariant: **embedding
never fails**. Indexing a corpus is a long, expensive, partially-completed
operation, and the ways a hosted embedding API breaks - no key in the
environment, egress blocked by the container, a 401 from a rotated key, a 429
after the retry budget is spent, a proxy returning HTML, a response truncated
mid-JSON - are all ordinary rather than exceptional. Any of them raising into
the indexer would discard the work already done and leave a half-built index
that looks complete. So :class:`HostedEmbedder` catches everything, logs the
downgrade loudly, and hands back deterministic hashing vectors instead.

The subtle part is not the catching, it is the *space*. A hosted vector and a
hashing vector of the same dimension are not comparable - they are different
coordinate systems that happen to have the same shape - and an index containing
both scores nonsense at query time while looking perfectly healthy. Two rules
follow, and they are the opinionated core of this module:

1. A single :meth:`HostedEmbedder.embed` call returns vectors from exactly one
   space. If batch 7 of 12 fails, the batches that already succeeded are thrown
   away and the whole call is re-embedded with the fallback. Hashing is cheap;
   a silently mixed index is not.
2. The degrade is sticky and visible. ``.degraded`` and ``.space`` tell the
   caller what it actually got, so an index can record the space alongside the
   vectors and refuse to mix them later.

A response whose vectors are the wrong length is treated as malformed for the
same reason: better to fall back wholesale than to interleave dimensions.
"""

from __future__ import annotations

import inspect
import json
import math
import os
import tempfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from oodarag.embed.hashing import DEFAULT_DIM, MIN_DIM, HashingEmbedder
from oodarag.models import Chunk
from oodarag.util.hashing import content_hash
from oodarag.util.http import HttpClient, HttpError, RetryPolicy
from oodarag.util.logging import get_logger
from oodarag.util.text import truncate_tokens

log = get_logger("embed")

#: OpenAI-compatible by default; anything speaking the same shape works, and the
#: parser also accepts the ``{"embeddings": [...]}`` shape used by Cohere/Voyage.
DEFAULT_ENDPOINT = "https://api.openai.com/v1/embeddings"
DEFAULT_MODEL = "text-embedding-3-small"

#: Checked in order. The first is ours so a user can point this at one provider
#: without disturbing whatever else on the machine reads OPENAI_API_KEY.
API_KEY_ENV: tuple[str, ...] = ("OODARAG_EMBED_API_KEY", "OPENAI_API_KEY")

#: Most hosted models cut off around 8k tokens and answer a longer input with a
#: 400 for the whole batch, so inputs are truncated before they are sent.
MAX_INPUT_TOKENS = 8000


@runtime_checkable
class Embedder(Protocol):
    """What the rest of the pipeline is allowed to assume about an embedder.

    Two members, both required by the index: the dimension (so a store can be
    allocated before any text arrives) and a batch embed. Anything conforming to
    this - hashing, hosted, cached, a test double - is interchangeable.

    ``dim`` is declared read-only rather than as a plain attribute so that an
    implementation which computes it - :class:`EmbeddingCache` delegates to the
    embedder it wraps - still satisfies the protocol.
    """

    @property
    def dim(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def _resolve_key(explicit: str | None, env_names: Sequence[str]) -> str:
    if explicit:
        return str(explicit).strip()
    for name in env_names:
        if value := os.environ.get(name, "").strip():
            return value
    return ""


class HostedEmbedder:
    """Calls a hosted embedding API; degrades to :class:`HashingEmbedder` forever after."""

    __slots__ = (
        "model", "dim", "endpoint", "batch_size", "max_input_tokens", "send_dimensions",
        "stats", "_key", "_client", "_fallback", "_degraded", "_reason",
    )

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        dim: int = DEFAULT_DIM,
        endpoint: str | None = None,
        api_key: str | None = None,
        api_key_env: Sequence[str] = API_KEY_ENV,
        batch_size: int = 64,
        max_input_tokens: int = MAX_INPUT_TOKENS,
        client: HttpClient | None = None,
        fallback: Embedder | None = None,
        timeout: float = 30.0,
        send_dimensions: bool = True,
    ) -> None:
        self.model = str(model)
        # Clamped the same way HashingEmbedder clamps, so the declared dimension
        # and the dimension the fallback actually produces cannot disagree.
        self.dim = max(MIN_DIM, int(dim))
        self.endpoint = str(endpoint or DEFAULT_ENDPOINT)
        self.batch_size = max(1, int(batch_size))
        self.max_input_tokens = max(16, int(max_input_tokens))
        self.send_dimensions = bool(send_dimensions)
        self.stats: dict[str, int] = {
            "texts": 0, "hosted_texts": 0, "fallback_texts": 0,
            "batches": 0, "batch_failures": 0, "empty_skipped": 0,
        }
        self._key = _resolve_key(api_key, api_key_env)
        # The fallback must share the declared dim or the two spaces are not even
        # shape-compatible and the index cannot be salvaged after a downgrade.
        self._fallback = fallback if fallback is not None else HashingEmbedder(self.dim)
        fallback_dim = int(getattr(self._fallback, "dim", self.dim))
        if fallback_dim != self.dim:
            # The fallback is the path that always works, so it wins the
            # argument. Announcing a dimension the degraded path cannot produce
            # would hand the index two incompatible shapes.
            log.error(
                "fallback dim disagrees with declared dim, adopting the fallback's",
                declared=self.dim, fallback=fallback_dim,
            )
            self.dim = fallback_dim
        self._client = client
        self._degraded = False
        self._reason = ""
        if not self._key:
            self._degrade("no api key in environment")
        elif self._client is None:
            # Retries live in the client (backoff, Retry-After, 429/5xx); this
            # class only decides what to do once they are exhausted.
            self._client = HttpClient(
                timeout=timeout,
                rate_per_sec=8.0,
                retry=RetryPolicy(attempts=3, base_delay=0.5, max_delay=15.0),
            )

    # ------------------------------------------------------------------ state

    @property
    def degraded(self) -> bool:
        return self._degraded

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def name(self) -> str:
        return f"hosted:{self.model}"

    @property
    def space(self) -> str:
        """The vector space actually being produced right now, for the index to record."""
        return self._fallback_space() if self._degraded else f"{self.model}@{self.dim}"

    def _fallback_space(self) -> str:
        return str(
            getattr(self._fallback, "space", None)
            or getattr(self._fallback, "name", "hash")
        )

    def _degrade(self, reason: str) -> None:
        if self._degraded:
            return
        self._degraded = True
        self._reason = reason
        # error, not warn: the vectors in this index are now a different space
        # from any produced earlier in the run, and somebody has to know that.
        log.error(
            "embedding downgraded to deterministic hashing",
            reason=reason, model=self.model, endpoint=self.endpoint, space=self._fallback_space(),
        )

    # ----------------------------------------------------------------- embed

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch. Never raises; may quietly become the hashing embedder."""
        items = [t if isinstance(t, str) else ("" if t is None else str(t)) for t in texts]
        if not items:
            return []
        self.stats["texts"] += len(items)
        if self._degraded:
            self.stats["fallback_texts"] += len(items)
            return self._fallback.embed(items)

        # Empty inputs are a 400 on most providers and would take the whole
        # batch down with them, so they never leave the process.
        sendable = [
            (i, truncate_tokens(t, self.max_input_tokens))
            for i, t in enumerate(items)
            if t.strip()
        ]
        out: list[list[float]] = [[0.0] * self.dim for _ in items]
        self.stats["empty_skipped"] += len(items) - len(sendable)

        for start in range(0, len(sendable), self.batch_size):
            window = sendable[start : start + self.batch_size]
            vectors = self._embed_batch([t for _, t in window])
            if vectors is None:
                self.stats["fallback_texts"] += len(items)
                return self._fallback.embed(items)  # one call, one space
            for (idx, _), vec in zip(window, vectors, strict=True):
                out[idx] = vec
        self.stats["hosted_texts"] += len(sendable)
        return out

    def _embed_batch(self, batch: list[str]) -> list[list[float]] | None:
        """One request. Returns None on any failure, having already logged it."""
        self.stats["batches"] += 1
        for include_dimensions in (self.send_dimensions, False):
            payload: dict[str, Any] = {"model": self.model, "input": batch}
            if include_dimensions:
                payload["dimensions"] = self.dim
            try:
                response = self._client.request(  # type: ignore[union-attr]
                    "POST",
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self._key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    body=json.dumps(payload).encode("utf-8"),
                )
                vectors = _parse_embeddings(response.json(), len(batch), self.dim)
                if vectors is None:
                    self.stats["batch_failures"] += 1
                    self._degrade("malformed or truncated response")
                    return None
                return vectors
            except HttpError as e:
                # A provider that does not know `dimensions` answers 400. Worth
                # exactly one retry without it before giving up on the provider.
                if e.status == 400 and include_dimensions:
                    log.warn("provider rejected dimensions, retrying without", model=self.model)
                    continue
                self.stats["batch_failures"] += 1
                self._degrade(f"http {e.status}")
                return None
            except Exception as e:  # transport, TLS, proxy, JSON, anything
                self.stats["batch_failures"] += 1
                self._degrade(f"{type(e).__name__}: {str(e)[:160]}")
                return None
        return None


def _parse_embeddings(payload: Any, expected: int, dim: int) -> list[list[float]] | None:
    """Validate a provider response hard, because a half-valid one is the danger.

    A truncated or partially-populated response is not a smaller answer, it is a
    silently misaligned one: vector 3 ends up on chunk 4 and the index is subtly
    wrong in a way no test on the happy path would catch. So the count, the
    ordering key, the dimension and the finiteness of every component are all
    checked, and anything short of complete is rejected.
    """
    if not isinstance(payload, dict):
        return None
    rows: Any = payload.get("data")
    vectors: list[Any]
    if isinstance(rows, list):
        indexed: list[tuple[int, Any]] = []
        for position, row in enumerate(rows):
            if not isinstance(row, dict):
                return None
            order = row.get("index", position)
            indexed.append((order if isinstance(order, int) else position, row.get("embedding")))
        indexed.sort(key=lambda pair: pair[0])
        vectors = [vec for _, vec in indexed]
    elif isinstance(payload.get("embeddings"), list):
        vectors = list(payload["embeddings"])
    else:
        return None

    if len(vectors) != expected:
        return None
    out: list[list[float]] = []
    for vec in vectors:
        if not isinstance(vec, list) or len(vec) != dim:
            return None
        try:
            row = [float(v) for v in vec]
        except (TypeError, ValueError):
            return None
        if not all(math.isfinite(v) for v in row):
            return None
        out.append(row)
    return out


# --------------------------------------------------------------------- factory


def _filter_kwargs(target: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Drop kwargs the target does not accept, loudly.

    The factory is fed from config files, and a config file eventually contains
    a key for a different embedder. Raising TypeError there would stop a run
    over a stray tuning knob; dropping it silently would let someone believe a
    setting is in force when it is not. So: drop and log.
    """
    try:
        params = inspect.signature(target).parameters
    except (TypeError, ValueError):  # pragma: no cover - builtins only
        return dict(kwargs)
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return dict(kwargs)
    kept = {k: v for k, v in kwargs.items() if k in params}
    if dropped := sorted(set(kwargs) - set(kept)):
        log.warn(
            "ignoring unsupported embedder options",
            target=getattr(target, "__name__", target),
            options=dropped,
        )
    return kept


def get_embedder(name: str = "auto", **kw: Any) -> Embedder:
    """Build an embedder. Returns something usable for every input, always.

    ``auto`` picks the hosted provider only when a key is actually resolvable,
    which is the difference between "configured" and "will work": constructing a
    HostedEmbedder without a key succeeds and then degrades on first use, and
    the log line for that reads like a failure rather than like the deliberate
    offline default it usually is.

    An unrecognised name is a warning and a hashing embedder, not an exception.
    A typo in a config file should cost retrieval quality, not the run.
    """
    key = str(name or "auto").strip().lower()
    if key in ("hash", "hashing", "local", "stdlib", "offline", "deterministic"):
        return HashingEmbedder(**_filter_kwargs(HashingEmbedder.__init__, kw))
    if key in ("hosted", "api", "remote", "openai", "provider"):
        return HostedEmbedder(**_filter_kwargs(HostedEmbedder.__init__, kw))
    if key != "auto":
        log.warn("unknown embedder name, using deterministic hashing", name=name)
        return HashingEmbedder(**_filter_kwargs(HashingEmbedder.__init__, kw))

    env_names = kw.get("api_key_env", API_KEY_ENV)
    if _resolve_key(kw.get("api_key"), env_names):
        log.info("embedder: hosted", model=kw.get("model", DEFAULT_MODEL))
        return HostedEmbedder(**_filter_kwargs(HostedEmbedder.__init__, kw))
    log.info("embedder: deterministic hashing (no api key found)", checked=list(env_names))
    return HashingEmbedder(**_filter_kwargs(HashingEmbedder.__init__, kw))


# ----------------------------------------------------------------------- cache


class EmbeddingCache:
    """Content-hash keyed memoisation in front of any embedder.

    Re-indexing is the common case, not the rare one: the ingest layer is
    incremental, so most chunks on most runs are byte-identical to the ones
    already embedded. Paying a hosted provider - or 40ms of blake2b - to
    rediscover that is waste, and with a hosted provider it is waste that costs
    money and rate-limit budget.

    The key includes the embedder's *space*, read at call time rather than at
    construction, which matters precisely at the moment a HostedEmbedder
    degrades mid-run: from then on the keys change, so hosted vectors are never
    served to a caller now receiving hashing vectors, and the two never mix.
    """

    __slots__ = ("embedder", "path", "max_entries", "stats", "_store")

    def __init__(
        self,
        embedder: Embedder,
        path: str | Path | None = None,
        max_entries: int = 50_000,
    ) -> None:
        self.embedder = embedder
        self.path = Path(path) if path else None
        self.max_entries = max(1, int(max_entries))
        self.stats: dict[str, int] = {"hits": 0, "misses": 0, "evicted": 0, "loaded": 0}
        self._store: dict[str, list[float]] = {}
        if self.path:
            self.load()

    @property
    def dim(self) -> int:
        return int(getattr(self.embedder, "dim", 0))

    @property
    def space(self) -> str:
        return str(
            getattr(self.embedder, "space", None)
            or getattr(self.embedder, "name", type(self.embedder).__name__)
        )

    def __len__(self) -> int:
        return len(self._store)

    def key(self, text: str) -> str:
        return content_hash(self.space, str(self.dim), text or "")

    def get(self, text: str) -> list[float] | None:
        return self._store.get(self.key(text))

    def put(self, text: str, vector: list[float]) -> None:
        self._store[self.key(text)] = list(vector)
        self._evict()

    def clear(self) -> None:
        self._store.clear()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed with memoisation. Satisfies the Embedder protocol, so it wraps transparently."""
        items = [t if isinstance(t, str) else ("" if t is None else str(t)) for t in texts]
        out: list[list[float] | None] = [None] * len(items)
        pending: dict[str, list[int]] = {}
        for i, text in enumerate(items):
            cached = self._store.get(self.key(text))
            if cached is not None:
                self.stats["hits"] += 1
                out[i] = list(cached)
            else:
                # Duplicates inside one batch are a cache miss exactly once.
                pending.setdefault(text, []).append(i)
        if pending:
            unique = list(pending)
            self.stats["misses"] += len(unique)
            vectors = self.embedder.embed(unique)
            for text, vector in zip(unique, vectors, strict=True):
                self.put(text, vector)
                for i in pending[text]:
                    out[i] = list(vector)
        return [v if v is not None else [0.0] * self.dim for v in out]

    def embed_chunks(self, chunks: Iterable[Chunk]) -> list[list[float]]:
        """Embed ``indexed_text`` - header plus body - which is what retrieval sees."""
        return self.embed([c.indexed_text for c in chunks])

    def _evict(self) -> None:
        # Insertion order, not recency: within a run each chunk is embedded once,
        # so an LRU would spend bookkeeping to reproduce FIFO.
        while len(self._store) > self.max_entries:
            self._store.pop(next(iter(self._store)))
            self.stats["evicted"] += 1

    # ------------------------------------------------------------ persistence

    def load(self, path: str | Path | None = None) -> int:
        """Load a cache file. A missing or corrupt file is an empty cache, never an error."""
        target = Path(path) if path else self.path
        if not target or not target.exists():
            return 0
        try:
            raw = json.loads(target.read_text("utf-8"))
            entries = raw.get("entries") if isinstance(raw, dict) else None
            if not isinstance(entries, dict):
                raise ValueError("no entries object")
        except (OSError, ValueError, TypeError) as e:
            # A truncated cache file is the normal outcome of a killed process.
            # Rebuilding it costs time; refusing to start costs the run.
            log.warn(
                "embedding cache unreadable, starting empty",
                path=str(target), err=str(e)[:160],
            )
            return 0
        loaded = 0
        for k, v in entries.items():
            if not isinstance(k, str) or not isinstance(v, list):
                continue
            try:
                vector = [float(x) for x in v]
            except (TypeError, ValueError):
                continue
            if not vector or not all(math.isfinite(x) for x in vector):
                continue
            self._store[k] = vector
            loaded += 1
        self.stats["loaded"] += loaded
        self._evict()
        return loaded

    def save(self, path: str | Path | None = None) -> bool:
        """Write atomically. Returns False rather than raising if the disk says no."""
        target = Path(path) if path else self.path
        if not target:
            return False
        payload = {"version": 1, "space": self.space, "dim": self.dim, "entries": self._store}
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=target.parent, prefix=target.name, suffix=".tmp",
                delete=False,
            ) as fh:
                # json emits float repr, which round-trips exactly, so a cached
                # vector is bit-identical to a freshly computed one.
                json.dump(payload, fh)
                tmp = Path(fh.name)
            os.replace(tmp, target)
            return True
        except OSError as e:
            log.warn("embedding cache not saved", path=str(target), err=str(e)[:160])
            return False
