"""Okapi BM25, implemented from first principles over an inverted index.

The lexical arm exists because the dense arm cannot do its job alone. A 512-dim
hashing embedder blurs exactly the tokens a technical corpus is queried by:
`ImportError`, `blake2b`, `--dry-run`, `v0.1.0`. Those are rare literal strings
whose whole value is that they match exactly, and a vector space that puts
`chunking` next to `chunked` will just as happily put `blake2b` next to
`blake2s`. BM25 scores them the other way round: the rarer the term, the louder
the hit.

SQLite's FTS5 was the obvious alternative and was rejected on three counts. It
is a compile-time option, so it is present in most CPython builds and absent in
some, which makes it a dependency wearing a disguise. Its ranking function is
BM25 with `k1`/`b` baked in, so the two knobs this corpus most wants to tune
would be out of reach. And it tokenizes with its own unicode61 tokenizer, which
splits `snake_case` and `dotted.paths` apart - precisely the tokens
`util.text.tokenize` is built to keep whole. Sharing one tokenizer with the
embedder is what lets the two arms agree on what a "term" even is.

Scoring accumulates over postings rather than sweeping every document: only a
document containing a query term can score above zero, so the work is
proportional to the matches, not to the corpus. The index is append-only by
design - `build()` replaces its contents, `add()` extends them, and neither
deletes. Deletion would need a tombstone in every postings list a document
touches; a full rebuild is one tokenize pass over the corpus and is what
`Pipeline.refresh_indexes` does anyway.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from oodarag.models import Chunk
from oodarag.util.logging import get_logger
from oodarag.util.text import tokenize

log = get_logger("bm25")


@dataclass(slots=True)
class BM25Params:
    """Okapi's two knobs.

    `k1` sets how fast term frequency saturates: the second occurrence of a word
    should count for much less than the first, and the tenth for almost nothing.
    The default sits a little above the usual 1.2 because half this corpus is
    code and documentation, where a repeated identifier genuinely is a stronger
    signal than a repeated word in prose.

    `b` sets how hard long documents are penalised. 0.75 is the standard
    compromise; 0 ignores length entirely and lets a long chunk win by sheer
    surface area, 1.0 fully normalises and punishes the thorough section that
    happens to answer the question.
    """

    k1: float = 1.4
    b: float = 0.75


class BM25Index:
    """In-memory BM25 over chunk text, keyed by `chunk_id`."""

    def __init__(self, params: BM25Params | None = None) -> None:
        self.params = params or BM25Params()
        #: Documents dropped because they tokenized to nothing (see `add`).
        self.skipped_empty = 0
        #: Repeat `chunk_id`s ignored (see `add`).
        self.skipped_duplicate = 0
        self._ids: list[str] = []
        self._lengths: list[int] = []
        self._postings: dict[str, list[tuple[int, int]]] = {}
        self._positions: dict[str, int] = {}
        self._total_tokens = 0

    def __len__(self) -> int:
        return len(self._ids)

    @property
    def avgdl(self) -> float:
        """Mean document length in tokens; 0.0 for an empty index."""
        return self._total_tokens / len(self._ids) if self._ids else 0.0

    @property
    def vocabulary(self) -> int:
        return len(self._postings)

    def add(self, chunk_id: str, text: str) -> None:
        """Index one document under `chunk_id`.

        Two documents are silently *not* indexed, both counted rather than
        raised. A repeat `chunk_id` is ignored because appending it again would
        double its term frequencies and its length, corrupting every score in
        the index rather than just its own. A document with no content tokens
        (pure stopwords, punctuation, an empty string) is dropped because it can
        never appear in any postings list, so keeping it would do nothing except
        drag `avgdl` down and shift everyone else's length normalisation.
        """
        if chunk_id in self._positions:
            self.skipped_duplicate += 1
            log.debug("duplicate chunk_id ignored", chunk_id=chunk_id)
            return
        tokens = tokenize(text)
        if not tokens:
            self.skipped_empty += 1
            log.debug("no content tokens, not indexed", chunk_id=chunk_id)
            return

        doc_index = len(self._ids)
        self._ids.append(chunk_id)
        self._lengths.append(len(tokens))
        self._positions[chunk_id] = doc_index
        self._total_tokens += len(tokens)
        for term, tf in Counter(tokens).items():
            self._postings.setdefault(term, []).append((doc_index, tf))

    def build(self, chunks: Iterable[Chunk]) -> BM25Index:
        """Replace the index contents with `chunks`. Returns self.

        Replacing rather than appending is what makes a periodic
        `refresh_indexes()` safe to call on a long-lived instance: an appending
        `build` would turn the second refresh into a corpus of duplicates.
        """
        self._reset()
        for chunk in chunks:
            # indexed_text, never text: the context header carries the document
            # title and heading path, which is how a chunk whose body says "it
            # depends on the chunk size" is still found by a query about
            # chunking. Indexing the bare body would throw that away and make
            # the header dead weight that only the embedder benefits from.
            self.add(chunk.chunk_id, chunk.indexed_text)
        log.info(
            "bm25 built",
            docs=len(self._ids),
            terms=len(self._postings),
            avgdl=round(self.avgdl, 1),
            empty=self.skipped_empty,
            duplicates=self.skipped_duplicate,
        )
        return self

    def search(self, query: str, k: int = 20) -> list[tuple[str, float]]:
        """Top-`k` `(chunk_id, score)` pairs, highest score first.

        An empty index, an empty query, a query of terms nobody uses, and a
        non-positive `k` all return `[]`. Retrieval is a best-effort stage that
        one arm of a hybrid retriever depends on; raising here would take down
        an answer the dense arm could still have produced.
        """
        if k <= 0 or not self._ids:
            return []
        # Query term frequency weights linearly, so asking "cache cache" leans
        # twice as hard on `cache`. Counting first means a term repeated in the
        # query walks its postings list once instead of once per occurrence.
        query_terms = Counter(tokenize(query))
        if not query_terms:
            return []

        n = len(self._ids)
        avgdl = self._total_tokens / n
        k1 = self.params.k1
        b = self.params.b
        lengths = self._lengths
        scores: dict[int, float] = {}

        for term, qtf in query_terms.items():
            postings = self._postings.get(term)
            if not postings:
                continue
            df = len(postings)
            idf = math.log((n - df + 0.5) / (df + 0.5))
            if idf <= 0.0:
                # Smoothed IDF goes negative once a term is in more than half
                # the corpus, which would let a common word actively push a
                # matching document *down* the ranking. Clamping at zero is the
                # fix; the `ln(x + 1)` variant that can never go negative was
                # rejected because it quietly keeps paying for a term that
                # carries no information. Skipping the walk is the same
                # arithmetic as adding 0.0 to each posting, minus the O(df)
                # scan. The trap: on a corpus of one or two documents *every*
                # term is in more than half of it, so search legitimately
                # returns nothing - two chunks contain no lexical evidence.
                continue
            weight = idf * qtf
            for doc_index, tf in postings:
                # Okapi BM25: idf * tf(k1 + 1) / (tf + k1(1 - b + b|d|/avgdl)).
                denominator = tf + k1 * (1.0 - b + b * lengths[doc_index] / avgdl)
                contribution = weight * tf * (k1 + 1.0) / denominator
                scores[doc_index] = scores.get(doc_index, 0.0) + contribution

        if not scores:
            return []
        # Ties broken by chunk_id so the ranking is a total order: near-identical
        # boilerplate chunks score identically far more often than float
        # arithmetic suggests, and without this the winner would depend on dict
        # insertion order, i.e. on the order the store happened to yield rows.
        ranked = sorted(
            ((self._ids[i], score) for i, score in scores.items()),
            key=lambda pair: (-pair[1], pair[0]),
        )
        return ranked[:k]

    def _reset(self) -> None:
        self._ids = []
        self._lengths = []
        self._postings = {}
        self._positions = {}
        self._total_tokens = 0
        self.skipped_empty = 0
        self.skipped_duplicate = 0

    def __repr__(self) -> str:
        return (
            f"BM25Index(docs={len(self._ids)}, terms={len(self._postings)}, "
            f"k1={self.params.k1}, b={self.params.b})"
        )
