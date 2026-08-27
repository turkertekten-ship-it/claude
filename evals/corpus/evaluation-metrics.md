<!-- source: https://oodarag.example/handbook/evaluation-metrics -->
# Evaluating Retrieval Quality

A retrieval change is settled by numbers before and after, one knob at a time.
The golden set is a list of questions with the documents that should answer
them; the harness runs each question through the pipeline and scores the ranked
result.

## Recall at k

Recall at k is the share of the labelled relevant documents that appear
anywhere in the top k results. It ignores order entirely, which is the point:
it answers "did retrieval even find the evidence", and it is the metric to fix
first, because nothing a reranker does can recover a document that was never
retrieved.

## Mean reciprocal rank

Reciprocal rank is one divided by the position of the first relevant result, so
rank one scores 1.0, rank two scores 0.5, and rank ten scores 0.1. MRR is the
mean of that across questions. It is the right metric when one good passage is
enough to answer, and it rewards putting the answer first rather than merely
somewhere on the page.

## Normalized discounted cumulative gain

nDCG credits every relevant result but discounts each one by the logarithm of
its position, then divides by the score of the ideal ranking so the result
lands between zero and one. With binary gains the numerator is the sum, over
relevant hits, of one divided by the base-two logarithm of one plus the rank.
It is the metric to watch when several passages each contribute part of the
answer.

## Citation coverage

Citation coverage is the share of answers whose citations all resolve back to a
chunk that was actually retrieved and quoted. It measures honesty rather than
relevance, and it is the check that catches a generator that has begun to
invent sources.

## Abstention and false abstention

Abstention rate is the share of questions the pipeline declined to answer.
False abstention rate is the share of answerable questions it declined anyway.
Both are reported because raising the confidence floor always improves the
apparent accuracy of the answers that remain: without the false abstention
number, silence looks like precision. A golden set should therefore contain
questions the corpus deliberately does not cover, so that a correct abstention
is a scored outcome rather than a failure.
