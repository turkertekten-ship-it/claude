"""Core data structures that flow through the pipeline.

    RawDocument -> Document -> Chunk -> ScoredChunk -> Answer

Every stage produces an immutable-ish dataclass carrying provenance forward, so
an answer can always be traced back to the byte range of the source it came
from. Provenance is not decoration: `Answer.citations` is verified against
`Chunk.doc_id` before an answer is returned.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from oodarag.util.hashing import content_hash, stable_id
from oodarag.util.text import redact_secrets


def _now() -> float:
    return time.time()


def _redacted(value: Any) -> Any:
    """Every string inside a metadata structure, redacted, shape preserved.

    Metadata is not incidental: it is written into the index, and the rule is
    about the index file, not about what gets embedded. The web connector built
    `metadata["description"]` from `page.text` - the *unredacted* one, since the
    connector redacted only the copy it put in `text` - so a credential on a
    crawled page reached the index in full while the body beside it was clean.

    Recursive because metadata nests: `headings` is a list, and a connector is
    free to store a dict.
    """
    if isinstance(value, str):
        return redact_secrets(value)
    # A tuple comes back as a list, deliberately: metadata is serialised to
    # JSON in the store, where a tuple is a list regardless. Preserving the type
    # here would be a fiction that survives exactly until the first round trip,
    # and falling through to "return unchanged" would leak.
    if isinstance(value, (list, tuple)):
        return [_redacted(v) for v in value]
    if isinstance(value, dict):
        return {k: _redacted(v) for k, v in value.items()}
    return value


@dataclass(slots=True)
class RawDocument:
    """What a connector hands back, before normalization.

    `external_id` is the source system's own identifier (a GitHub path + sha, a
    YouTube video id, a chat session uuid). It must be stable across runs so
    incremental ingestion can tell "changed" from "new".
    """

    source_system: str
    external_id: str
    uri: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    fetched_at: float = field(default_factory=_now)
    #: When the *source* says the content last changed, if it says. Distinct
    #: from `fetched_at`, which is when we asked.
    #:
    #: Without this, `Document.updated_at` was the fetch time for every
    #: connector, so the reranker's recency factor scored a GitHub issue last
    #: touched in January as brand new because it was fetched a moment ago -
    #: and every document ingested in one run got the same date, which is why
    #: recency turned out to move nothing on either eval corpus (L43). The
    #: connectors already read the real dates; they had nowhere to put them.
    #:
    #: Left as None when the source does not say. That is not the same as
    #: "now", and pretending otherwise is what made a fetch time look like a
    #: fact about the content.
    source_updated_at: float | None = None

    def __post_init__(self) -> None:
        """Redaction happens here because here is the boundary.

        The rule is that secrets are redacted before text can reach an index,
        and an index is a file that gets copied around. It was being kept by
        each connector calling `redact_secrets` on the body it had just built -
        a convention seven connectors had to remember, and the YouTube one did
        not: captions, a curated notes file and the manifest summary all went in
        untouched.

        Titles were worse, because every connector missed them. A title is not
        decoration: `chunking._context_header` puts it at the front of
        `Chunk.indexed_text`, so it is embedded, indexed and searchable. The
        chat connector builds its title from the user's own first message, and
        a commit title is a commit's subject line - both ordinary places for a
        pasted token to sit.

        Metadata was the third hole, and the one that shows why "before it can
        reach an index file" is the right way to state the rule rather than
        "before it can be embedded": nothing embeds `metadata["description"]`,
        and it is written into the index all the same.

        `RawDocument` is the one type every connector must construct, so the
        guarantee is structural here and a convention anywhere else. The
        connectors' own calls stay - `redact_secrets` is idempotent, verified
        for every pattern it carries - and cost one measured extra pass:
        277 ms over 144 documents and 1.05 MiB, against an 8.3 s index.
        """
        self.text = redact_secrets(self.text)
        self.title = redact_secrets(self.title)
        self.uri = redact_secrets(self.uri)
        self.metadata = _redacted(self.metadata)

    @property
    def content_hash(self) -> str:
        return content_hash(self.text, self.title)


@dataclass(slots=True)
class Document:
    """A normalized document: canonical text plus provenance."""

    doc_id: str
    source_system: str
    external_id: str
    uri: str
    title: str
    text: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)

    @classmethod
    def from_raw(cls, raw: RawDocument, text: str, metadata: dict[str, Any]) -> Document:
        return cls(
            doc_id=stable_id(raw.source_system, raw.external_id),
            source_system=raw.source_system,
            external_id=raw.external_id,
            uri=raw.uri,
            title=raw.title,
            text=text,
            content_hash=content_hash(text, raw.title),
            metadata=metadata,
            created_at=raw.fetched_at,
            # The source's own date when it gave one, the fetch time otherwise.
            updated_at=(raw.source_updated_at
                        if raw.source_updated_at is not None else raw.fetched_at),
        )


@dataclass(slots=True)
class Chunk:
    """A retrievable unit.

    `context_header` is the contextual-retrieval prefix: a short, deterministic
    description of where the chunk sits in its document (title, heading path,
    timestamp, speaker). It is embedded and indexed *with* the body, which is
    what stops a chunk like "it depends on the chunk size" from being retrieved
    with no idea what "it" is.
    """

    chunk_id: str
    doc_id: str
    ordinal: int
    text: str
    context_header: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    char_start: int = 0
    char_end: int = 0

    @property
    def indexed_text(self) -> str:
        """The text actually embedded and indexed."""
        return f"{self.context_header}\n\n{self.text}".strip() if self.context_header else self.text

    @property
    def token_estimate(self) -> int:
        from oodarag.util.text import estimate_tokens

        return estimate_tokens(self.indexed_text)

    @property
    def content_hash(self) -> str:
        return content_hash(self.indexed_text)


@dataclass(slots=True)
class ScoredChunk:
    """A retrieved chunk with the score breakdown that put it there.

    Keeping the components (not just the fused score) is what makes retrieval
    debuggable: you can see whether a hit came from the lexical arm, the dense
    arm, or only survived because of the reranker.
    """

    chunk: Chunk
    score: float
    components: dict[str, float] = field(default_factory=dict)
    document: Document | None = None

    @property
    def citation_uri(self) -> str:
        return self.document.uri if self.document else self.chunk.doc_id

    @property
    def citation_title(self) -> str:
        return self.document.title if self.document else self.chunk.doc_id


@dataclass(slots=True)
class Citation:
    marker: int
    chunk_id: str
    doc_id: str
    title: str
    uri: str
    quote: str
    score: float
    #: Where the cited chunk begins and ends **in the document text as
    #: indexed** - not in the file. Those differ: the filesystem connector
    #: strips YAML front matter, `clean()` normalises whitespace, and redaction
    #: replaces secrets with placeholders of a different length. A first version
    #: of this field published `file:///x.md#char=0,190` as an RFC 5147 range
    #: and the first three citations checked against the real corpus pointed at
    #: the front matter the ingest had removed (L78).
    #:
    #: Paired with `content_hash`, which identifies the text the offsets address,
    #: the two are a precise reference to what was actually read - the doctrine's
    #: "pinned to an immutable identifier where one exists". Alone they are a
    #: guess about a file.
    char_start: int = 0
    char_end: int = 0
    #: Hash of the document text these offsets index.
    content_hash: str = ""

    @property
    def span(self) -> str:
        """Human-readable provenance: which characters of which text.

        Deliberately not a uri fragment. `#char=` on a `file://` uri is a claim
        about the file, and this is a claim about the normalised text - the same
        distinction that made the first version of this wrong.
        """
        if self.char_end > self.char_start >= 0 and self.content_hash:
            return f"chars {self.char_start}-{self.char_end} of {self.content_hash}"
        return ""


@dataclass(slots=True)
class Answer:
    question: str
    text: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    abstained: bool = False
    generator: str = "extractive"
    retrieved: list[ScoredChunk] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_retrieved: bool = False) -> dict[str, Any]:
        out: dict[str, Any] = {
            "question": self.question,
            "answer": self.text,
            "confidence": round(self.confidence, 4),
            "abstained": self.abstained,
            "generator": self.generator,
            "citations": [{**asdict(c), "span": c.span} for c in self.citations],
            "metrics": self.metrics,
        }
        if include_retrieved:
            out["retrieved"] = [
                {
                    "chunk_id": s.chunk.chunk_id,
                    "doc_id": s.chunk.doc_id,
                    "score": round(s.score, 4),
                    "components": {k: round(v, 4) for k, v in s.components.items()},
                    "uri": s.citation_uri,
                    "preview": s.chunk.text[:200],
                }
                for s in self.retrieved
            ]
        return out

    def to_json(self, include_retrieved: bool = False) -> str:
        return json.dumps(self.to_dict(include_retrieved), indent=2, ensure_ascii=False)


@dataclass(slots=True)
class IngestDelta:
    """What one connector run changed. Drives the Observe phase of the loop."""

    source_key: str
    new: int = 0
    changed: int = 0
    unchanged: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    duration_s: float = 0.0
    #: External ids present on the previous run and absent from this one.
    #: Detected here but never acted on downstream: the document stayed in the
    #: index and stayed citable, so an answer could quote text that no longer
    #: exists in its source. Pruning is a separate, guarded action - see
    #: IndexPipeline.prune - because a source that returns nothing for a
    #: transient reason must not be able to empty an index.
    removed: list[str] = field(default_factory=list)
    source_system: str = ""

    @property
    def touched(self) -> int:
        return self.new + self.changed

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
