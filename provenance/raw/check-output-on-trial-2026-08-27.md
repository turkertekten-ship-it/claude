# check_output against the A/B trial's real answers — 2026-08-27

The checker was written after the trial and run against the trial's own
outputs. Both arms' answers to the summary task, checked against the forged
prompt that stated the constraints.

## The forged arm — the one the model judge scored 4/5
```
5/6 checkable constraint(s) held, 1 not machine-checkable

  ok   ONE_PARAGRAPH    one paragraph                1 paragraphs
  ok   NO_LISTS         no list markup               0 list line(s)
  ok   NO_HEADINGS      no headings                  0 heading(s)
  ok   NO_BOLD_LABELS   no bold labels               0 bold-led line(s)
  FAIL MAX_COUNT        at most 80 words             86 words
  ok   NO_PREAMBLE      no preamble                  opens 'The team will shorten cache invalidation fro'

  not machine-checkable — read these yourself:
    · Keep the two numbers that decide it — the 4x traffic increase and the 2% of cache load — and say
```

## The raw arm
```
3/6 checkable constraint(s) held, 1 not machine-checkable

  FAIL ONE_PARAGRAPH    one paragraph                5 paragraphs
  ok   NO_LISTS         no list markup               0 list line(s)
  ok   NO_HEADINGS      no headings                  0 heading(s)
  FAIL NO_BOLD_LABELS   no bold labels               1 bold-led line(s)
  FAIL MAX_COUNT        at most 80 words             90 words
  ok   NO_PREAMBLE      no preamble                  opens '**Cache invalidation: proposed change**'
```

The 86-word overrun is the failure that caused the tool to be written. The
model judge found it by reading; this finds it by counting, and also catches
the raw arm's bold label, which the judge folded into a single prose note.
