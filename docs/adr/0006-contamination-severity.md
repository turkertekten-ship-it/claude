# ADR 0006 - A verbatim question is contamination unless the document is the answer

**Status:** accepted

## Context

The golden sets are graded against a corpus, and this project indexes itself.
Contamination detection has always had two severities:

* against a question the corpus is supposed to be *unable* to answer, any match
  is fatal and the document is held out for that question;
* against a question it *should* answer, a match was reported and never acted
  on.

The reasoning for the second was written in the code and is sound as far as it
goes: a document matching a positive question's terms is very likely the answer,
and quarantining it would remove the source the case names and turn a passing
case into a failing one.

It is also incomplete. A verbatim match on a positive question finds two kinds
of document, and the rule treated them as one:

1. the document that **answers** the question - `crawler.py` for a question
   about crawl budgets;
2. the document that **quotes** the question while discussing the evaluation -
   `internal/LEARNINGS.md`, `docs/EVALUATION.md`, a docstring that names the
   case it was written to fix.

The second is leakage of the purest kind, and on a self-indexing repository it
accumulates every time a failure is analysed in writing. Eight such documents
were being found at a perfect verbatim score and listed as non-fatal in every
report the project produced (L94, L95).

## Decision

A verbatim match on a positive golden is fatal unless the document is one of
that golden's `expect_sources`. The golden already names which documents are
allowed to contain the answer; that field is the discriminator the old rule
lacked.

Overlap matches on positive goldens remain non-fatal. Sharing most of a
question's distinctive terms is what an answer does, and no field distinguishes
"discusses" from "answers" for a paraphrase.

## Measured

Before implementing, documents quoting a positive question verbatim while not
being one of its expected sources:

| corpus | findings | questions | documents |
|---|---|---|---|
| primary (this repo) | 8, all scoring 1.00 | 4 | LEARNINGS.md, PLAN.md, EVALUATION.md, SKILL.md, expansion.py, rag-design-notes.md |
| external (153 PyPI pages) | 0 | 0 | - |

Zero on the external corpus, which is the regression gate, so the change could
not move the number it would be graded on. Confirmed after the fact:

| | before | after |
|---|---|---|
| external pass | 49/54 | 49/54 |
| external recall@8 / MRR / nDCG@8 | 0.9302 / 0.7643 / 0.7958 | 0.9302 / 0.7643 / 0.7958 |
| external contamination | 5 questions, 22 docs, 28 holdouts | 5 questions, 22 docs, 28 holdouts |
| held-out set | 19/22 | 19/22 |
| primary pass | 18/20 | 19/20 |
| primary contamination | 4 questions, 15 docs, 30 holdouts | 8 questions, 18 docs, 39 holdouts |

The primary pass rate returning to 19/20 - the value the plan recorded before
the corpus decayed - is a coincidence of which case it removed, not a recovery.

## Consequences

The primary corpus is measured against slightly less of itself, and will be
measured against less again as more analysis is written. That is the intended
direction: the part of this repository written in a golden question's own words
is commentary on the evaluation, not corpus for it.

The change cannot flatter the external gate, because the external corpus
contains no writing about this project. If a future corpus ever does, this ADR
stops applying to it cleanly and the exemption list is the thing to revisit.

Nothing here rescues a self-indexing eval. The primary set remains a smoke test
and the external set remains the gate (see `docs/EVALUATION.md`); this only
removes the leakage that could be identified without judgement.
