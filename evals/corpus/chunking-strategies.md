<!-- source: https://oodarag.example/handbook/chunking-strategies -->
# Chunking Strategies for Retrieval

A chunk is the unit a retriever can return, so chunking decides the ceiling on
everything downstream. Chunks that are too large bury one relevant sentence in
a page of unrelated context and waste the generation budget. Chunks that are
too small lose the antecedents that make them readable: a passage saying "it
depends on the corpus" is unrankable, because nothing in it says what "it" is.

## Fixed windows

The simplest strategy slices the document every N tokens with a fixed stride.
It is fast and it is uniform, which makes token budgeting trivial, but it cuts
mid-sentence and mid-table and it ignores the document's own structure. Use it
as a baseline to beat, not as a destination.

## Structural splitting

Markdown, HTML and source files already carry a hierarchy. Splitting on
headings first, then packing sentences inside each section, keeps semantically
related text together and gives every chunk a heading path for free. Fenced
code blocks are never split: half a function is worse than no function, and a
heading-looking line inside a fence is a comment, not a section boundary.

## Overlap

Neighbouring chunks share a carry-over window, typically 15 to 25 percent of
the target size. Overlap exists to survive a bad cut: when the sentence that
answers the question sits one line after a boundary, the previous chunk still
carries it. The cost is index size and duplicate hits, so deduplicate by
sentence at generation time rather than shrinking the overlap to zero. This
pipeline targets 320 tokens per chunk with 64 tokens of overlap, a minimum of
48 tokens, and a hard ceiling of 640.

## Contextual headers

Every chunk is prefixed with a short deterministic header naming the document
title, the heading path, and the chunk's position, and that header is indexed
and embedded together with the body. This is contextual retrieval: it restores
the antecedents that slicing destroyed, and it costs nothing at query time.
A chunk that says "the default is 0.75" becomes findable once its header says
it belongs to "BM25 Scoring > Length normalization".

## Offsets are provenance

Each chunk records the character range it occupies in its source document.
Without real offsets a quote cannot be traced back, and an answer that cannot
be traced is indistinguishable from an invented one.
