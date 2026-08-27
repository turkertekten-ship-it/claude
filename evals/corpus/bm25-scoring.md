<!-- source: https://oodarag.example/handbook/bm25-scoring -->
# BM25 Scoring Explained

BM25 is the lexical ranking function that a retrieval system should have to
beat before anyone reaches for a neural model. It scores a document against a
query by summing, over the query terms, an inverse document frequency weight
multiplied by a saturating term frequency factor.

## Inverse document frequency

The idf weight answers "how surprising is this term?". A term appearing in
almost every document discriminates nothing, so its weight collapses toward
zero; a term appearing in three documents out of ten thousand carries most of
the ranking signal. The usual form is the logarithm of the ratio between the
number of documents that do not contain the term and the number that do, with
a half-count smoothing that keeps a term present in every document from going
negative.

## Saturating term frequency

Raw term frequency is a bad signal: a page that repeats "latency" forty times
is not forty times more about latency than a page that says it once. BM25 damps
this with the parameter k1, which controls how quickly the contribution
saturates. Around 1.2 to 1.6 is the conventional range; this pipeline uses 1.4.
As k1 approaches zero the score reduces to a binary "does the term occur",
which is exactly what you want for very short fields such as titles.

## Length normalization

Long documents contain more terms by accident, so without a correction they
win every query. The parameter b, between zero and one, sets how strongly a
document's length relative to the average length is used to discount its score.
At b equal to zero there is no length normalization at all; at b equal to one
the correction is full. The default value of b is 0.75, a compromise that has
survived two decades of benchmarks and a sensible starting point for chunked
corpora where lengths are already fairly uniform.

## What BM25 cannot do

BM25 matches strings, not meaning. A question phrased as "how do I stop the
crawler from hammering a site" will not match a passage about "rate limiting"
unless the words overlap. Stemming and synonym expansion patch a little of
this and introduce their own errors: conflating two distinct identifiers in a
code corpus cites the wrong symbol. The honest fix is a second, dense arm and
a fusion step, not more aggressive query rewriting.
