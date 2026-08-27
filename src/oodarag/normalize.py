"""The gate every document passes through before it is allowed near an index.

Three things happen here, and each exists because of a specific way a retrieval
corpus rots:

1. **Canonical text.** `util.text.clean` folds unicode and collapses whitespace
   *before* anything is hashed, so two copies of the same page that differ only
   in non-breaking spaces produce the same fingerprint. Hashing the bytes a
   connector happened to receive would make dedupe useless on exactly the
   documents that need it most - mirrors, re-uploads, re-renders.

2. **Redaction, a second time.** Connectors already redact; this is the second
   gate. Defence in depth is nearly free here, and the alternative is trusting
   every present *and future* connector to have remembered - which is how a live
   token ends up in an index file that then gets copied onto three laptops. The
   number of documents that actually *changed* under redaction is reported
   rather than swallowed: a count going from 0 to 7 between runs is the only
   signal anyone gets that a source started leaking.

3. **Dropping.** Thin documents and duplicates never reach the index. A hundred
   five-word stubs distort IDF for every query in the corpus and answer nothing,
   and a document indexed three times spends the context window saying the same
   sentence three times.

Dedupe is deliberately scoped to one batch. Cross-run dedupe belongs to the
store, which upserts by `doc_id`; a Normalizer that remembered forever would
silently drop a document on re-ingest - the precise opposite of what a re-ingest
is for. `normalize_all` therefore starts a fresh registry, and `reset()` exists
for callers that drive `normalize()` one document at a time.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from typing import Any

from oodarag.models import Document, RawDocument
from oodarag.util.http import normalize_url
from oodarag.util.logging import get_logger
from oodarag.util.text import clean, estimate_tokens, redact_secrets, summarize, tokenize_all

log = get_logger("normalize")

#: Fallback titles are cut here: a title is a context header, not a paragraph.
_TITLE_CHARS = 120


@dataclass(slots=True)
class NormalizeReport:
    """Counters for one normalization batch.

    `redacted` counts documents whose text *changed*, not redaction hits: one
    document leaking the same key twelve times is one leaky document, and the
    per-document number is the one that maps onto a source to go fix.
    """

    seen: int = 0
    kept: int = 0
    dropped_thin: int = 0
    dropped_duplicate: int = 0
    redacted: int = 0

    @property
    def dropped(self) -> int:
        return self.dropped_thin + self.dropped_duplicate

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Normalizer:
    """`RawDocument` -> `Document`, or nothing at all.

    Returning `None` rather than raising is the whole design: a document that
    fails the gate is a counted, reportable fact about the corpus, not an
    exception that aborts the other 4,000 documents in the batch.
    """

    def __init__(self, *, min_words: int = 25, dedupe: bool = True) -> None:
        self.min_words = min_words
        self.dedupe = dedupe
        self.report = NormalizeReport()
        # hash/canonical -> doc_id of the document that claimed it first. Keeping
        # the winner's id (rather than a bare set) is what lets the log say which
        # document a duplicate collided with, which is the only useful form of
        # that message.
        self._by_hash: dict[str, str] = {}
        self._by_canonical: dict[str, str] = {}

    def reset(self) -> None:
        """Start a new batch: fresh counters, fresh dedupe registry."""
        self.report = NormalizeReport()
        self._by_hash.clear()
        self._by_canonical.clear()

    def normalize(self, raw: RawDocument) -> Document | None:
        """Normalize one document, counting the outcome into `self.report`."""
        self.report.seen += 1

        # Clean first, redact second. NFKC folding can turn a fullwidth or
        # homoglyph-laden secret into the ASCII shape the redaction patterns
        # actually match; doing it the other way round lets that key through.
        text = clean(raw.text)
        redacted = redact_secrets(text)
        was_redacted = redacted != text
        if was_redacted:
            text = redacted
            self.report.redacted += 1
            log.warn(
                "redacted secret material",
                source=raw.source_system, uri=raw.uri or raw.external_id,
            )

        words = self._word_count(text)
        if words < self.min_words:
            self.report.dropped_thin += 1
            log.debug("dropped thin document", uri=raw.uri, words=words, floor=self.min_words)
            return None

        title = self._title(raw, text)
        if title != raw.title:
            # `Document.from_raw` folds the title into the content hash, so the
            # derived title has to be in place before the id is computed.
            raw = replace(raw, title=title)

        metadata = dict(raw.metadata)
        metadata["authority"] = _as_float(metadata.get("authority"), 1.0)
        metadata["word_count"] = words
        metadata["redacted"] = was_redacted
        canonical = self._canonical(metadata, raw.uri)
        if canonical:
            metadata["canonical"] = canonical

        doc = Document.from_raw(raw, text, metadata)

        if self.dedupe:
            if (first := self._duplicate_of(doc, canonical)) is not None:
                self.report.dropped_duplicate += 1
                log.debug("dropped duplicate", uri=raw.uri, same_as=first)
                return None
            self._by_hash[doc.content_hash] = doc.doc_id
            if canonical:
                self._by_canonical[canonical] = doc.doc_id

        self.report.kept += 1
        return doc

    def normalize_all(self, raws: Iterable[RawDocument]) -> tuple[list[Document], NormalizeReport]:
        """Normalize a batch. Errors are counted, never raised at the caller."""
        self.reset()
        docs: list[Document] = []
        for raw in raws:
            try:
                if (doc := self.normalize(raw)) is not None:
                    docs.append(doc)
            except Exception as e:
                # One pathological document must not cost the batch. The report has
                # no `failed` field, so a failure shows up as `seen - kept - dropped`
                # and the detail lives in the log - inventing a drop reason here
                # would make a crash indistinguishable from a policy decision.
                log.error(
                    "normalize failed",
                    source=getattr(raw, "source_system", "?"),
                    id=getattr(raw, "external_id", "?"),
                    err=f"{type(e).__name__}: {e}"[:200],
                )
        log.info("normalize batch", **self.report.as_dict())
        return docs, self.report

    # ------------------------------------------------------------------ internals

    def _duplicate_of(self, doc: Document, canonical: str) -> str | None:
        """The doc_id this document duplicates, or None.

        Two gates, because they catch different things: the content hash catches
        the same text served from two unrelated URLs, and the canonical catches
        the same URL wearing a tracking query string or a print-view path even
        when a banner or timestamp made the text differ by a byte.
        """
        if (first := self._by_hash.get(doc.content_hash)) is not None:
            return first
        if canonical and (first := self._by_canonical.get(canonical)) is not None:
            return first
        return None

    def _word_count(self, text: str) -> int:
        words = len(tokenize_all(text))
        # The tokenizer only sees latin/digit runs, so a CJK document tokenizes
        # to nothing. Without this fallback the thin-document gate would quietly
        # delete every non-latin document in the corpus.
        return words or estimate_tokens(text)

    def _title(self, raw: RawDocument, text: str) -> str:
        """A usable title, derived if the connector had none.

        An empty title is not cosmetic: it is the first segment of every chunk's
        context header, so a document without one produces chunks that cannot
        say where they came from.
        """
        if title := " ".join(clean(raw.title).split()):
            return title[:_TITLE_CHARS]
        for line in text.split("\n"):
            if line.startswith("#"):
                if heading := line.lstrip("#").strip(" #"):
                    return heading[:_TITLE_CHARS]
                break
        return (summarize(text, _TITLE_CHARS) or raw.uri or raw.external_id)[:_TITLE_CHARS]

    def _canonical(self, metadata: dict[str, Any], uri: str) -> str:
        """The dedupe key from `metadata["canonical"]`, normalized when it is a URL.

        Non-web connectors put non-URL identifiers here (a repo path, a video
        id); running those through `normalize_url` would invent a scheme and a
        host, so they are used verbatim. `uri` is *not* used as a fallback
        canonical - every document has a uri, so that would turn the canonical
        gate into a second, weaker copy of the doc_id check.
        """
        value = metadata.get("canonical")
        if not isinstance(value, str) or not value.strip():
            return ""
        value = value.strip()
        if "://" not in value:
            return value
        try:
            return normalize_url(value)
        except ValueError:  # a malformed declared canonical is not worth a crash
            log.debug("unparseable canonical", value=value[:200], uri=uri)
            return value


def _as_float(value: Any, default: float) -> float:
    """Authority arrives from connector metadata and JSON state, so it can be a
    string. A bad value must not make the reranker explode much later."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
