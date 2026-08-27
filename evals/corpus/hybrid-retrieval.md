<!-- source: https://oodarag.example/handbook/hybrid-retrieval -->
# Hybrid Retrieval and Rank Fusion

Hybrid retrieval runs a lexical arm and a dense arm over the same corpus and
merges their results. The two arms are kept because they fail differently.
BM25 finds the exact identifier, the rare error string and the version number
that an embedding model has never seen. Dense retrieval finds the paraphrase
that shares no words at all with the question. Either arm alone has a blind
spot the other covers.

## Why the scores are never added

BM25 produces an unbounded sum of idf-weighted term contributions, so its scale
depends on how rare the query terms happen to be in this particular corpus.
Cosine similarity is bounded in the range minus one to one and, for real text,
spends nearly all its time in a narrow band above zero. Adding the two is
meaningless; averaging them is worse, because the result still looks reasonable.
Per-query min-max normalization was rejected as well: it forces the top hit of
each arm to exactly 1.0 whether it was a perfect match or the best of a bad
lot, which is a fabricated score.

## Reciprocal Rank Fusion

Reciprocal Rank Fusion reads only the thing both arms mean identically: rank
order. A chunk's contribution from one arm is weight divided by the sum of a
constant and the rank it holds in that arm, and the contributions are summed
across arms. The constant, conventionally 60, is the single knob and its effect
is legible: it sets how much better rank one is than rank ten. Nothing here can
be miscalibrated, because nothing is calibrated. Each arm votes with its
ordering and the votes add up.

What RRF gives up is worth stating: the fused score is ordinal, so it cannot
distinguish the best of forty excellent chunks from the best of forty terrible
ones. Each arm's raw score therefore rides along in the score components.

## Over-fetch, then cut

Both arms are queried for far more candidates than the caller wants, typically
forty to produce eight. Fusion can only rank what it was handed, and a chunk
that both arms place tenth is usually a better answer than the one a single arm
places first. It cannot win if the arms were only asked for eight results.

## Diversity after fusion

Maximal Marginal Relevance reranks the fused list, trading a little relevance
for coverage so that three near-identical chunks from one page do not consume
the whole context window. A source authority weight nudges trusted sources up.
