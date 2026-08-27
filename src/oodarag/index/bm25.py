"""Okapi BM25 over chunks, with the Turkish morphology problem solved explicitly.

BM25 is here rather than SQLite's FTS5 for one reason: FTS5's scoring is a
black box you cannot reweight, and this pipeline fuses the lexical arm with a
dense arm and then reranks. A retriever whose lexical score cannot be
decomposed is a retriever whose bad answers cannot be explained. Everything
below is a few hundred lines and every number in a result can be traced to a
term, a document frequency and a length normalisation.

**The Turkish problem.** Turkish is agglutinative: `fon` (fund) appears in a
real corpus as `fonun`, `fonlar`, `fonların`, `fonlarının`, `fonda`, `fondan`,
`fona`, `fonu`. A bag-of-words index treats all of those as unrelated terms, so
a query for `fon` matches none of them. There are two standard fixes:

*Character n-grams.* Rejected. They multiply the posting lists by roughly the
average token length, they flatten IDF into uselessness because every n-gram is
common, and — the decisive objection — they match across morpheme boundaries.
`fonksiyon` (function) shares the trigram `fon` with `fon` (fund) and would be
retrieved for it. In a corpus about fund management that is not a rounding
error, it is a wrong answer with a citation attached.

*Light suffix stripping.* Chosen. A curated list of Turkish inflectional
suffixes (plural, possessive, the six cases, the copula) is peeled off, longest
first, at most three rounds, never below a three-character stem. `fonksiyon`
survives it untouched; `fonlarının` reduces to `fon`.

The stemmer is deliberately *not* applied destructively. Each token is indexed
twice: the surface form at full weight and its stem at ``stem_weight`` (0.5).
That way an exact match always outranks a morphological one, an over-stemmed
English word (`state` -> `sta`) costs nothing because the surface form is still
there at full weight, and no recall is lost when the stemmer is wrong. The
price is a larger index, which is the cheap resource here.

**Tokenisation.** ``util.text.tokenize_all`` uses ``[A-Za-z0-9_]``, which
silently mangles Turkish: `değerleme` becomes `de` + `erleme` and `İstanbul`
becomes `stanbul`. So ASCII text takes the shared ``tokenize_all`` path
verbatim — identical behaviour, including the `snake_case` and `dotted.path`
joining that matters for a half-code corpus — and non-ASCII text takes a
Unicode-aware path with the same shape. Turkish casing rules (`İ` -> `i`,
`I` -> `ı`) are applied only to tokens that actually contain a Turkish-specific
character, so `IBM` does not become `ıbm` in a mixed corpus.

**Persistence.** The built index serialises to a zlib-compressed JSON blob in
the Store. Not pickle, not marshal: an index file gets copied between machines
and unpickling one is arbitrary code execution. JSON is bigger and slower and
it is the correct tradeoff.
"""

from __future__ import annotations

import json
import math
import re
import time
import zlib
from collections import Counter
from collections.abc import Collection, Iterable
from typing import TYPE_CHECKING, Any

from oodarag.models import Chunk
from oodarag.util.logging import get_logger
from oodarag.util.text import tokenize_all

if TYPE_CHECKING:  # pragma: no cover - import cycle only matters to a type checker
    from oodarag.index.store import Store

log = get_logger("bm25")

#: Same shape as util.text._TOKEN_RE, widened from [A-Za-z0-9_] to \w so that
#: `ğ ü ş ı ö ç` survive tokenisation. On pure-ASCII input the two are
#: character-for-character identical, which is why the ASCII fast path can
#: delegate to tokenize_all without changing any result.
_UNICODE_TOKEN_RE = re.compile(r"\w+(?:[.\-/]\w+)*", re.UNICODE)

#: Characters that mark a token as Turkish for casing purposes.
_TR_CHARS = frozenset("ğüşıöçĞÜŞİÖÇı")
_COMBINING_DOT = "̇"

#: Turkish inflectional suffixes. Derivational ones (-lik, -ci, -sel) are
#: deliberately absent: they change meaning, and conflating `fon` with `fonlu`
#: buys recall by spending precision on a corpus where precision is the point.
_TR_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            # plural
            "lar", "ler",
            # possessive
            "imiz", "ımız", "umuz", "ümüz", "iniz", "ınız", "unuz", "ünüz",
            "leri", "ları", "im", "ım", "um", "üm", "in", "ın", "un", "ün",
            "si", "sı", "su", "sü", "i", "ı", "u", "ü",
            # genitive
            "nin", "nın", "nun", "nün",
            # ablative
            "nden", "ndan", "den", "dan", "ten", "tan",
            # locative
            "nde", "nda", "de", "da", "te", "ta",
            # dative
            "ye", "ya", "na", "ne", "e", "a",
            # accusative
            "yi", "yı", "yu", "yü", "ni", "nı", "nu", "nü",
            # instrumental / comitative
            "yle", "yla", "ile", "le", "la",
            # relative
            "ki",
            # copula
            "dir", "dır", "dur", "dür", "tir", "tır", "tur", "tür",
        },
        key=lambda s: (-len(s), s),
    )
)

MIN_STEM_LEN = 3
MAX_STEM_ROUNDS = 3

BM25_BLOB_NAME = "bm25"
_FORMAT_VERSION = 1

_NOT_STEMMABLE = re.compile(r"[0-9._\-/]")


def tr_lower(token: str) -> str:
    """Lowercase, applying Turkish casing only to evidently Turkish tokens.

    `str.lower()` maps `İ` to `i` + U+0307 (two code points), which then fails
    to match a plain `i`. Turkish also lowercases `I` to `ı`, which is right for
    `ILAÇ` and wrong for `IBM`; the Turkish-character test decides which.
    """
    if _TR_CHARS.isdisjoint(token) and "İ" not in token:
        return token.lower()
    return token.replace("İ", "i").replace("I", "ı").lower().replace(_COMBINING_DOT, "")


def tokenize_index_text(text: str) -> list[str]:
    """Tokens for indexing and querying. ASCII delegates to `tokenize_all`."""
    if not text:
        return []
    if text.isascii():
        return tokenize_all(text)
    return [tr_lower(m.group(0)) for m in _UNICODE_TOKEN_RE.finditer(text)]


def turkish_stem(token: str) -> str:
    """Peel Turkish inflectional suffixes. Returns the token unchanged when no
    rule applies, when the token looks like an identifier or number, or when
    stripping would leave a stem shorter than three characters."""
    if len(token) <= MIN_STEM_LEN or _NOT_STEMMABLE.search(token):
        return token
    stem = token
    for _ in range(MAX_STEM_ROUNDS):
        for suffix in _TR_SUFFIXES:
            if (
                len(suffix) < len(stem)
                and stem.endswith(suffix)
                and len(stem) - len(suffix) >= MIN_STEM_LEN
            ):
                stem = stem[: -len(suffix)]
                break
        else:
            break
    return stem


def expand_terms(tokens: Iterable[str], stem_weight: float) -> tuple[dict[str, float], int]:
    """(term -> weight, surface token count).

    The count returned is of *surface* tokens only. Using the expanded count as
    the BM25 document length would inflate every Turkish document's length by
    the number of tokens the stemmer touched, and BM25's length normalisation
    would then penalise Turkish text for being Turkish.
    """
    weights: dict[str, float] = {}
    surface = 0
    for token in tokens:
        surface += 1
        weights[token] = weights.get(token, 0.0) + 1.0
        stem = turkish_stem(token)
        if stem != token:
            weights[stem] = weights.get(stem, 0.0) + stem_weight
    return weights, surface


class BM25Index:
    """An in-memory Okapi BM25 index that can round-trip through a Store.

    Deletions are tombstones. Physically removing a chunk means walking every
    posting list it appears in, which is O(vocabulary) for one deletion; a
    tombstone is O(1) and makes document frequencies slightly stale until
    :meth:`compact` runs. Stale df moves scores by a fraction of a percent on a
    corpus of any size, which is a much better trade than making incremental
    deletes quadratic.
    """

    __slots__ = (
        "k1", "b", "stem_weight",
        "_ids", "_pos", "_lengths", "_live", "_postings",
        "_live_count", "_total_len", "_built_at",
    )

    def __init__(self, k1: float = 1.2, b: float = 0.75, stem_weight: float = 0.5) -> None:
        self.k1 = float(k1)
        self.b = float(b)
        self.stem_weight = float(stem_weight)
        self._ids: list[str] = []
        self._pos: dict[str, int] = {}
        self._lengths: list[float] = []
        self._live: list[bool] = []
        self._postings: dict[str, list[tuple[int, float]]] = {}
        self._live_count = 0
        self._total_len = 0.0
        self._built_at = 0.0

    # ------------------------------------------------------------- building

    def add(self, chunk: Chunk) -> None:
        """Index one chunk. Re-adding an existing chunk_id tombstones the old
        entry, so a re-chunked document does not accumulate ghost postings."""
        text = chunk.indexed_text
        if not text.strip():
            return
        if chunk.chunk_id in self._pos:
            self.delete(chunk.chunk_id)
        weights, surface = expand_terms(tokenize_index_text(text), self.stem_weight)
        if not weights:
            return
        idx = len(self._ids)
        self._ids.append(chunk.chunk_id)
        self._pos[chunk.chunk_id] = idx
        self._lengths.append(float(surface))
        self._live.append(True)
        self._live_count += 1
        self._total_len += float(surface)
        for term, tf in weights.items():
            self._postings.setdefault(term, []).append((idx, tf))

    def build(self, chunks: Iterable[Chunk]) -> BM25Index:
        """Discard everything and index the given chunks. Returns self."""
        self._ids.clear()
        self._pos.clear()
        self._lengths.clear()
        self._live.clear()
        self._postings.clear()
        self._live_count = 0
        self._total_len = 0.0
        for chunk in chunks:
            self.add(chunk)
        self._built_at = time.time()
        log.info("bm25 built", docs=self._live_count, terms=len(self._postings))
        return self

    def build_from_store(self, store: Store) -> BM25Index:
        return self.build(store.iter_chunks())

    def delete(self, chunk_id: str) -> bool:
        idx = self._pos.get(chunk_id)
        if idx is None or not self._live[idx]:
            return False
        self._live[idx] = False
        self._live_count -= 1
        self._total_len -= self._lengths[idx]
        return True

    def compact(self) -> BM25Index:
        """Rebuild without tombstones. Cheap enough to run after a bulk delete
        and pointless to run after one."""
        if all(self._live):
            return self
        keep = [i for i, live in enumerate(self._live) if live]
        remap = {old: new for new, old in enumerate(keep)}
        self._ids = [self._ids[i] for i in keep]
        self._lengths = [self._lengths[i] for i in keep]
        self._live = [True] * len(keep)
        self._pos = {cid: i for i, cid in enumerate(self._ids)}
        postings: dict[str, list[tuple[int, float]]] = {}
        for term, plist in self._postings.items():
            kept = [(remap[i], tf) for i, tf in plist if i in remap]
            if kept:
                postings[term] = kept
        self._postings = postings
        self._live_count = len(keep)
        self._total_len = sum(self._lengths)
        return self

    # ------------------------------------------------------------ searching

    @property
    def avgdl(self) -> float:
        return (self._total_len / self._live_count) if self._live_count else 0.0

    def _idf(self, df: int) -> float:
        """Lucene's BM25 IDF, not the textbook one.

        The classic `log((N - df + 0.5) / (df + 0.5))` goes *negative* once a
        term appears in more than half the corpus, which means a document is
        punished for containing the word `the`. The `1 +` form is monotonic and
        non-negative, which is the behaviour anyone reading a score expects.
        """
        n = self._live_count
        if n <= 0 or df <= 0:
            return 0.0
        return math.log(1.0 + (n - df + 0.5) / (df + 0.5))

    def search(
        self, query: str, k: int = 20, allowed: Collection[str] | None = None
    ) -> list[tuple[str, float]]:
        """Top-k `(chunk_id, score)`, highest first.

        An empty index, an empty query, or a query whose every term is unknown
        all return `[]`. `allowed`, when given, restricts results to that set of
        chunk ids — the filter push-down from the retriever, applied inside the
        scoring loop so a narrow filter over a wide corpus does not first score
        the whole corpus.
        """
        if not self._live_count or not query or k <= 0:
            return []
        tokens = tokenize_index_text(query)
        if not tokens:
            return []
        qterms, _ = expand_terms(tokens, self.stem_weight)
        avgdl = self.avgdl or 1.0
        k1, b = self.k1, self.b
        scores: dict[int, float] = {}
        for term, qw in qterms.items():
            plist = self._postings.get(term)
            if not plist:
                continue
            idf = self._idf(len(plist))
            if idf <= 0.0:
                continue
            for idx, tf in plist:
                if not self._live[idx]:
                    continue
                if allowed is not None and self._ids[idx] not in allowed:
                    continue
                denom = tf + k1 * (1.0 - b + b * (self._lengths[idx] / avgdl))
                if denom <= 0.0:
                    continue
                scores[idx] = scores.get(idx, 0.0) + qw * idf * (tf * (k1 + 1.0)) / denom
        if not scores:
            return []
        # Sort on a rounded score with the chunk id as tiebreak, so two runs
        # over the same corpus produce byte-identical output. Ties are common:
        # a one-term query against duplicated boilerplate ties every hit.
        ranked = sorted(
            ((self._ids[i], round(s, 9)) for i, s in scores.items()),
            key=lambda kv: (-kv[1], kv[0]),
        )
        return ranked[:k]

    # ---------------------------------------------------------- persistence

    def to_bytes(self) -> bytes:
        payload = {
            "format": _FORMAT_VERSION,
            "k1": self.k1,
            "b": self.b,
            "stem_weight": self.stem_weight,
            "built_at": self._built_at,
            "ids": self._ids,
            "lengths": self._lengths,
            "live": [1 if x else 0 for x in self._live],
            # Flat [idx, tf, idx, tf, ...] pairs: half the JSON of a list of
            # two-element lists, and it decodes with a slice.
            "postings": {
                term: [v for pair in plist for v in (pair[0], round(pair[1], 4))]
                for term, plist in self._postings.items()
            },
        }
        return zlib.compress(json.dumps(payload, ensure_ascii=False).encode("utf-8"), 6)

    @classmethod
    def from_bytes(cls, blob: bytes) -> BM25Index | None:
        """Rebuild from a serialised blob. Returns None on anything malformed —
        a corrupt index is a reason to rebuild, never a reason to abort a query."""
        try:
            payload = json.loads(zlib.decompress(blob).decode("utf-8"))
        except (zlib.error, json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            log.error("bm25 blob unreadable", err=str(e)[:200])
            return None
        if not isinstance(payload, dict) or payload.get("format") != _FORMAT_VERSION:
            log.error("bm25 blob has an unknown format", got=str(payload.get("format"))[:20])
            return None
        try:
            index = cls(
                k1=float(payload.get("k1", 1.2)),
                b=float(payload.get("b", 0.75)),
                stem_weight=float(payload.get("stem_weight", 0.5)),
            )
            index._ids = [str(x) for x in payload["ids"]]
            index._lengths = [float(x) for x in payload["lengths"]]
            index._live = [bool(x) for x in payload["live"]]
            if not (len(index._ids) == len(index._lengths) == len(index._live)):
                raise ValueError("id/length/live arrays disagree")
            index._pos = {cid: i for i, cid in enumerate(index._ids)}
            postings: dict[str, list[tuple[int, float]]] = {}
            for term, flat in payload["postings"].items():
                postings[term] = [
                    (int(flat[i]), float(flat[i + 1])) for i in range(0, len(flat) - 1, 2)
                ]
            index._postings = postings
            index._live_count = sum(1 for x in index._live if x)
            index._total_len = sum(
                length for length, live in zip(index._lengths, index._live, strict=True) if live
            )
            index._built_at = float(payload.get("built_at", 0.0))
        except (KeyError, TypeError, ValueError, IndexError) as e:
            log.error("bm25 blob malformed", err=str(e)[:200])
            return None
        return index

    def save(self, store: Store, name: str = BM25_BLOB_NAME) -> None:
        store.put_blob(
            name,
            self.to_bytes(),
            {
                "docs": self._live_count,
                "terms": len(self._postings),
                "k1": self.k1,
                "b": self.b,
                "stem_weight": self.stem_weight,
                "format": _FORMAT_VERSION,
            },
        )
        log.info("bm25 saved", docs=self._live_count, terms=len(self._postings))

    @classmethod
    def load(cls, store: Store, name: str = BM25_BLOB_NAME) -> BM25Index | None:
        blob = store.get_blob(name)
        if blob is None:
            return None
        return cls.from_bytes(blob.payload)

    @classmethod
    def ensure(
        cls,
        store: Store,
        name: str = BM25_BLOB_NAME,
        *,
        rebuild_if_stale: bool = True,
        **kwargs: Any,
    ) -> BM25Index:
        """Load the persisted index, rebuilding it if it is missing or stale.

        Staleness is decided by comparing the index's live document count with
        the store's chunk count. That is a coarse check and it is on purpose: it
        catches the case that actually happens (an ingest ran and nobody
        reindexed) without reading every chunk to compare hashes on every
        process start.
        """
        index = cls.load(store, name)
        chunk_count = int(store.stats().get("chunks", 0))
        if index is not None and (not rebuild_if_stale or len(index) == chunk_count):
            return index
        if index is not None:
            log.warn("bm25 index stale, rebuilding", indexed=len(index), chunks=chunk_count)
        fresh = cls(**kwargs).build_from_store(store)
        try:
            fresh.save(store, name)
        except Exception as e:  # a read-only store must not break retrieval
            log.warn("bm25 index could not be persisted", err=str(e)[:200])
        return fresh

    # ----------------------------------------------------------- reporting

    def __len__(self) -> int:
        return self._live_count

    def __contains__(self, chunk_id: str) -> bool:
        idx = self._pos.get(chunk_id)
        return idx is not None and self._live[idx]

    def stats(self) -> dict[str, Any]:
        return {
            "documents": self._live_count,
            "tombstones": len(self._ids) - self._live_count,
            "terms": len(self._postings),
            "postings": sum(len(p) for p in self._postings.values()),
            "avgdl": round(self.avgdl, 3),
            "k1": self.k1,
            "b": self.b,
            "stem_weight": self.stem_weight,
            "built_at": self._built_at,
        }

    def term_frequencies(self, chunk_id: str) -> Counter[str]:
        """Every indexed term for one chunk. Diagnostics only: this walks the
        whole vocabulary, so it is for "why did this not match?", not for a loop."""
        idx = self._pos.get(chunk_id)
        out: Counter[str] = Counter()
        if idx is None:
            return out
        for term, plist in self._postings.items():
            for i, tf in plist:
                if i == idx:
                    out[term] = tf
        return out

    def __repr__(self) -> str:
        return f"<BM25Index docs={self._live_count} terms={len(self._postings)}>"
