# RAG design notes

Reference notes on retrieval-augmented generation, written for this repository.

**Provenance.** These are authored notes, not a transcript or a quotation of any
video. Where a claim comes from published IBM material, the URL is given inline
and the claim is attributed to that page. Everything else is a design position
taken by this project, and marked as such. See
`corpus/ibm-technology/manifest.json` for why no video transcripts are included.

---

## What RAG is for

A language model answers from what it absorbed during training. That knowledge
is frozen at a point in time, cannot include anything private, and offers no way
to check where an answer came from.

Retrieval-augmented generation puts a retrieval step in front of generation: the
question is used to fetch passages from a corpus you control, and those passages
are given to the model as the material to answer from. IBM's explanation of the
framework attributes two advantages to it - the model gets current and
trustworthy facts, and the reader can see where the information came from, which
makes the output checkable rather than merely fluent
([ibm.com/think/videos/rag](https://www.ibm.com/think/videos/rag),
[IBM Research](https://research.ibm.com/blog/retrieval-augmented-generation-RAG)).

The second advantage is the one this project treats as primary. Freshness can be
bought other ways. Traceability cannot: without it, a wrong answer and a right
answer look identical.

## The stages, and what goes wrong in each

RAG adds several steps to inference - embedding generation, vector search, and
prompt construction ([IBM: vector databases for
RAG](https://www.ibm.com/think/topics/rag-vector-database)). Each is a place the
system can fail quietly.

### Chunking

Documents are split before they are retrieved, and a poorly chosen split
fragments meaning or reduces precision (IBM, as above). IBM's chunking tutorial
describes several strategies
([ibm.com](https://www.ibm.com/think/tutorials/chunking-strategies-for-rag-with-langchain-watsonx-ai)):

- **Semantic chunking** groups sentences by the similarity of their embeddings,
  producing context-aware chunks.
- **Document-based chunking** splits on the document's own structure - markdown
  sections, tables, images, Python classes and functions.
- **Agentic chunking** has the model decide the split points by reasoning about
  meaning and structure.

*This project's position:* structure first, size second. The author already put
boundaries in the document - headings, function definitions, speaker turns - and
those boundaries are free, deterministic, and better than anything inferred. Size
limits pack within them. Semantic chunking costs an embedding pass over every
candidate boundary; agentic chunking costs a model call per document. Neither has
earned that cost against structural splitting on the corpora here, and the eval
harness exists to make that a measurement rather than an opinion.

### Retrieval

Vector search is increasingly combined with keyword search, metadata filtering
and graph-based retrieval, to capture both semantic meaning and structured
relationships (IBM, vector databases for RAG).

*This project's position:* dense and lexical retrieval fail in uncorrelated
ways, which is the condition under which combining them helps. Dense retrieval
finds paraphrase - "how do I split documents" matching a passage about chunking
that never says "split". Lexical retrieval finds exact tokens - an error code, a
flag, a version string - that an embedder blurs away. They are fused by rank
rather than by score, because their scores are not on comparable scales and any
calibration between them drifts as the corpus changes.

### Generation

*This project's position:* the citation contract is enforced, not requested. A
model asked to cite will sometimes cite a source that does not support the claim,
or emit a marker that indexes nothing. Markers are therefore verified against the
chunks actually retrieved, invalid ones are stripped rather than shipped, and
coverage below a floor abstains. An honest "the retrieved sources do not cover
this" is a correct answer; a fluent guess is not.

### Agentic retrieval

Agentic retrieval lets the model decide what, when and how to retrieve, running
multiple retrieval actions, refining queries, or asking for more context during
generation (IBM, vector databases for RAG).

*This project's position:* worth doing once single-shot retrieval is measured
and its failures are understood. Adding a loop on top of a retriever whose recall
is unknown multiplies the cost of every failure and makes the cause harder to
find. The eval harness comes first.

## Evaluation

*This project's position, and the one it is most opinionated about:* a RAG
system without an evaluation harness is not engineered, it is demonstrated.

The metrics that matter are not one number:

- **recall@k** bounds everything downstream - a generator cannot cite what was
  never retrieved.
- **precision@k** measures what fraction of a fixed context budget was wasted.
- **MRR and nDCG@k** measure ranking quality, which is what a reranker changes.
- **citation coverage** measures grounding of the answer, not the retrieval.
- **abstention correctness** measures the behaviour that separates a grounded
  system from a confident one - and it needs negative cases, questions the
  corpus genuinely cannot answer.

And the number nobody reports: **contamination**. If the corpus contains the
evaluation questions, every metric above is measuring a leak. Any system that
indexes its own repository, notes, or session logs will eventually index the
questions it is evaluated on. See `internal/LEARNINGS.md` L10 for three separate
instances of this happening during the construction of this repository, each of
which made the metrics look *better*.
