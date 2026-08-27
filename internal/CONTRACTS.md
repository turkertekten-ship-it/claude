# oodarag module contracts

Frozen interface spec. Every module below is implemented independently against
*this file*, so the signatures here are normative: an implementation that
changes one breaks its callers.

Existing, already-built and NOT to be modified:
`models.py`, `util/{http,text,hashing,logging,ratelimit}.py`,
`scrape/{html,robots,crawler}.py`, `ingest/{base,web,github}.py`.

House rules (they are visible in every existing file, match them):
- Python 3.11, `from __future__ import annotations`, full type hints.
- **Zero third-party imports.** stdlib only. `numpy` may only appear inside a
  `try: import numpy except ImportError:` fast path with a stdlib fallback.
- Module docstrings explain *why the design is this way*, not what the code does.
- Comments earn their place by recording a decision or a trap, never by
  narrating the next line.
- Dataclasses with `slots=True` for data; `Protocol` for interfaces.
- Errors are counted and carried in a report object, never allowed to abort a
  batch. Network/IO degrade, they do not crash.
- Logging via `from oodarag.util.logging import get_logger` -> `log = get_logger("<stage>")`.

---

## `oodarag/normalize.py`

```python
@dataclass(slots=True)
class NormalizeReport:
    seen: int = 0
    kept: int = 0
    dropped_thin: int = 0
    dropped_duplicate: int = 0
    redacted: int = 0
    def as_dict(self) -> dict[str, Any]: ...

class Normalizer:
    def __init__(self, *, min_words: int = 25, dedupe: bool = True) -> None: ...
    def normalize(self, raw: RawDocument) -> Document | None: ...
    def normalize_all(self, raws: Iterable[RawDocument]) -> tuple[list[Document], NormalizeReport]: ...
```
Responsibilities: `util.text.clean` + `redact_secrets` (redaction is defence in
depth here - connectors already redact, this is the second gate), drop documents
under `min_words`, dedupe on `content_hash` *and* on `metadata["canonical"]`,
carry `authority` through into `Document.metadata`.

## `oodarag/chunk.py`

```python
@dataclass(slots=True)
class ChunkConfig:
    target_tokens: int = 320
    overlap_tokens: int = 64
    min_tokens: int = 48
    max_tokens: int = 640
    respect_code_fences: bool = True

class Chunker:
    def __init__(self, config: ChunkConfig | None = None) -> None: ...
    def chunk(self, doc: Document) -> list[Chunk]: ...
    def chunk_all(self, docs: Iterable[Document]) -> list[Chunk]: ...

def build_context_header(doc: Document, heading_path: list[str], ordinal: int, total: int) -> str: ...
```
Split on markdown sections (`util.text.split_markdown_sections`), then pack
sentences to `target_tokens` with `overlap_tokens` of carry-over. Never split a
fenced code block. Every chunk gets `context_header` from `build_context_header`
(title + heading path + position), `char_start`/`char_end` set to real offsets
into `doc.text`, and `chunk_id = stable_id(doc.doc_id, str(ordinal))`.

## `oodarag/embed/base.py`

```python
class Embedder(Protocol):
    name: str
    dim: int
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...

def cosine(a: Sequence[float], b: Sequence[float]) -> float: ...
def l2_normalize(vec: list[float]) -> list[float]: ...

class EmbeddingCache:
    """Content-hash keyed, so re-indexing an unchanged corpus costs no compute."""
    def __init__(self, path: str | Path | None = None) -> None: ...
    def get(self, model: str, content_hash: str) -> list[float] | None: ...
    def put(self, model: str, content_hash: str, vec: list[float]) -> None: ...
    def flush(self) -> None: ...
```

## `oodarag/embed/hashing.py`

```python
class HashingEmbedder:
    """Signed-hashing-trick embedder: deterministic, dependency-free, no model download."""
    def __init__(self, dim: int = 512, *, ngram: int = 4, use_ngrams: bool = True,
                 salt: str = "oodarag", cache: EmbeddingCache | None = None) -> None: ...
    name: str   # e.g. "hash-512-n4"
    dim: int
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...
```
Tokens via `util.text.tokenize`, sublinear TF (`1 + log(tf)`), plus
`util.text.char_ngrams` for subword robustness at a lower weight. Bucket with
`util.hashing.blake_bucket`, sign with `blake_sign` so collisions cancel.
L2-normalize the result. Must be exactly reproducible across processes.

## `oodarag/index/store.py`

```python
class Store:
    """SQLite-backed document/chunk/vector store. WAL mode, one file."""
    def __init__(self, path: str | Path = ".oodarag/index.db") -> None: ...
    def upsert_documents(self, docs: Iterable[Document]) -> int: ...
    def upsert_chunks(self, chunks: Iterable[Chunk],
                      vectors: Mapping[str, Sequence[float]] | None = None) -> int: ...
    def replace_document_chunks(self, doc_id: str, chunks: list[Chunk],
                                vectors: Mapping[str, Sequence[float]] | None = None) -> int: ...
    def get_document(self, doc_id: str) -> Document | None: ...
    def get_chunk(self, chunk_id: str) -> Chunk | None: ...
    def get_chunks(self, chunk_ids: Sequence[str]) -> dict[str, Chunk]: ...
    def iter_chunks(self) -> Iterator[Chunk]: ...
    def iter_vectors(self) -> Iterator[tuple[str, list[float]]]: ...
    def get_vector(self, chunk_id: str) -> list[float] | None: ...
    def documents(self) -> list[Document]: ...
    def delete_document(self, doc_id: str) -> int: ...
    def stats(self) -> dict[str, Any]: ...
    def close(self) -> None: ...
    def __enter__(self); def __exit__(self, *exc)
```
Vectors serialize with `array("f", vec).tobytes()`. Schema carries a
`meta(schema_version)` row; opening an index written by a newer version is an
explicit error, not a crash. `stats()` returns at least
`{documents, chunks, vectors, bytes, sources: {name: count}}`.

## `oodarag/index/bm25.py`

```python
@dataclass(slots=True)
class BM25Params:
    k1: float = 1.4
    b: float = 0.75

class BM25Index:
    def __init__(self, params: BM25Params | None = None) -> None: ...
    def add(self, chunk_id: str, text: str) -> None: ...
    def build(self, chunks: Iterable[Chunk]) -> BM25Index: ...   # returns self
    def search(self, query: str, k: int = 20) -> list[tuple[str, float]]: ...
    def __len__(self) -> int: ...
```
Index `chunk.indexed_text` (context header included - that is the whole point of
the header). Tokenize with `util.text.tokenize`.

## `oodarag/index/dense.py`

```python
class DenseIndex:
    def __init__(self, dim: int) -> None: ...
    def add(self, chunk_id: str, vector: Sequence[float]) -> None: ...
    def build(self, pairs: Iterable[tuple[str, Sequence[float]]]) -> DenseIndex: ...
    def search(self, vector: Sequence[float], k: int = 20) -> list[tuple[str, float]]: ...
    def __len__(self) -> int: ...
```
Exhaustive cosine over L2-normalized vectors (a dot product). Optional numpy
fast path behind try/except with an identical-result stdlib fallback.

## `oodarag/retrieve.py`

```python
@dataclass(slots=True)
class RetrievalConfig:
    k: int = 8
    candidates: int = 40
    rrf_k: int = 60
    dense_weight: float = 1.0
    lexical_weight: float = 1.0

class HybridRetriever:
    def __init__(self, store: Store, embedder: Embedder, bm25: BM25Index,
                 dense: DenseIndex, config: RetrievalConfig | None = None) -> None: ...
    def retrieve(self, query: str, k: int | None = None,
                 *, source_filter: str | None = None) -> list[ScoredChunk]: ...

def rrf_fuse(rankings: Mapping[str, list[tuple[str, float]]], *, rrf_k: int = 60,
             weights: Mapping[str, float] | None = None) -> list[tuple[str, float, dict[str, float]]]: ...
```
Reciprocal Rank Fusion, because the two arms produce incomparable score scales
and normalizing them is guesswork. Every returned `ScoredChunk.components` must
carry `bm25_rank`, `dense_rank`, `bm25`, `dense`, `rrf`, and its `document` must
be populated so citations work.

## `oodarag/rerank.py`

```python
@dataclass(slots=True)
class RerankConfig:
    mmr_lambda: float = 0.7          # 1.0 = pure relevance, 0.0 = pure diversity
    authority_weight: float = 0.15
    recency_half_life_days: float = 0.0   # 0 disables recency

class Reranker:
    def __init__(self, embedder: Embedder, config: RerankConfig | None = None) -> None: ...
    def rerank(self, query: str, scored: list[ScoredChunk], k: int = 8) -> list[ScoredChunk]: ...
```
MMR for diversity (three near-identical chunks from one page is a wasted context
window), plus a source-authority nudge from `document.metadata["authority"]`.
Writes `components["mmr"]`, `["authority"]`, `["final"]`.

## `oodarag/generate.py`

```python
@dataclass(slots=True)
class GenerationConfig:
    max_context_tokens: int = 2000
    min_confidence: float = 0.12
    max_sentences: int = 6

class ExtractiveGenerator:
    """Answers using only sentences that appear verbatim in retrieved chunks.

    Extractive by default so the zero-dependency install still answers questions
    and so every citation is verifiable by string containment rather than trust.
    """
    name: str = "extractive"
    def __init__(self, config: GenerationConfig | None = None) -> None: ...
    def generate(self, question: str, scored: list[ScoredChunk]) -> Answer: ...

def verify_citations(answer_text: str, citations: list[Citation],
                     scored: list[ScoredChunk]) -> list[Citation]: ...
def build_prompt(question: str, scored: list[ScoredChunk], max_tokens: int = 2000) -> str: ...
```
Must abstain (`Answer.abstained=True`, empty citations) when the best score is
below `min_confidence` - "I don't know" beats a confident wrong answer with a
fabricated source. `build_prompt` exists so a hosted model can be dropped in
later without reworking retrieval.

## `oodarag/pipeline.py`

```python
@dataclass(slots=True)
class PipelineConfig:
    root: Path = Path(".oodarag")
    embed_dim: int = 512
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

class Pipeline:
    """Wires the stages together and owns the store handles."""
    def __init__(self, config: PipelineConfig | None = None) -> None: ...
    def ingest(self, connectors: Sequence[Connector]) -> list[IngestDelta]: ...
    def index_documents(self, docs: Sequence[Document]) -> dict[str, int]: ...
    def refresh_indexes(self) -> None: ...     # rebuild bm25 + dense from the store
    def ask(self, question: str, k: int | None = None) -> Answer: ...
    def stats(self) -> dict[str, Any]: ...
    def close(self) -> None: ...
```

## `oodarag/evals/harness.py`

```python
@dataclass(slots=True)
class Golden:
    question: str
    relevant_uris: list[str] = field(default_factory=list)
    relevant_doc_ids: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    should_abstain: bool = False

@dataclass(slots=True)
class EvalReport:
    n: int = 0
    recall_at_k: float = 0.0
    mrr: float = 0.0
    ndcg_at_k: float = 0.0
    citation_coverage: float = 0.0
    abstention_rate: float = 0.0
    false_abstention_rate: float = 0.0
    per_question: list[dict[str, Any]] = field(default_factory=list)
    def as_dict(self) -> dict[str, Any]: ...
    def render(self) -> str: ...       # a readable table for the terminal

def load_goldens(path: str | Path) -> list[Golden]: ...
def evaluate(pipeline: Pipeline, goldens: Sequence[Golden], k: int = 8) -> EvalReport: ...
```
Metrics computed from first principles - `recall@k`, `MRR`, `nDCG@k` with binary
gains, citation coverage (share of answers whose citations all resolve to a
retrieved chunk), and a false-abstention rate so tuning `min_confidence` upward
is visibly a trade-off rather than a free win.

## `oodarag/ooda/loop.py`

```python
@dataclass(slots=True)
class Observation:
    """Observe: facts about the world, no judgement."""
    stats: dict[str, Any]
    deltas: list[IngestDelta]
    eval_report: dict[str, Any] | None = None
    stale_sources: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

@dataclass(slots=True)
class Orientation:
    """Orient: what the facts mean, scored."""
    staleness: float          # 0..1
    quality: float            # 0..1, from the eval report
    error_rate: float
    coverage_gaps: list[str]
    notes: list[str]

@dataclass(slots=True)
class Action:
    kind: str                 # reingest | reindex | retune | backfill | alert | noop
    target: str = ""
    reason: str = ""
    params: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class CycleReport:
    cycle: int
    observation: Observation
    orientation: Orientation
    decided: list[Action]
    results: list[dict[str, Any]]
    duration_s: float
    def as_dict(self) -> dict[str, Any]: ...
    def render(self) -> str: ...

@dataclass(slots=True)
class LoopPolicy:
    staleness_threshold: float = 0.25
    quality_floor: float = 0.55
    max_actions_per_cycle: int = 3
    dry_run: bool = False

class OodaLoop:
    def __init__(self, pipeline: Pipeline, connectors: Sequence[Connector],
                 policy: LoopPolicy | None = None, goldens_path: str | Path | None = None) -> None: ...
    def observe(self) -> Observation: ...
    def orient(self, obs: Observation) -> Orientation: ...
    def decide(self, orientation: Orientation, obs: Observation) -> list[Action]: ...
    def act(self, actions: Sequence[Action]) -> list[dict[str, Any]]: ...
    def cycle(self) -> CycleReport: ...
    def run(self, cycles: int = 1, interval_s: float = 0.0) -> list[CycleReport]: ...
```
The four phases stay genuinely separate: `decide` is a pure function of the
orientation (so a policy change is testable without a network), and `act` is the
only phase permitted to mutate anything. `dry_run` runs everything but `act`.

## `oodarag/cli.py`

```python
def main(argv: list[str] | None = None) -> int: ...
```
Subcommands, each mapping to a Makefile target already written:
`demo`, `index`, `query <question>`, `eval`, `loop [--cycles N] [--dry-run]`,
`stats`. `argparse` only. Returns a process exit code; never raises to the
terminal - a failure prints a diagnosis and returns non-zero.
`demo` must work end-to-end **offline**, from the seed corpus in `evals/corpus/`.
