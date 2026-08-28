# A/B trial — forged prompt against raw ask — 2026-08-27

Run `wf_057c0dd0-44b`, 12 agents. Four tasks, each attempted twice: once from a
realistic sloppy ask, once from the same intent expressed in the seven slots.
A separate judge scored both outputs against five criteria fixed in advance,
shown them under neutral labels ONE and TWO, never told which arm was which,
with the display order alternating by task. Un-blinded only after scoring.

## Result

| task | raw | forged | criteria |
|---|---|---|---|
| refactor | **5** | **5** | 5 |
| tests | **2** | **5** | 5 |
| summary | **3** | **4** | 5 |
| error | **3** | **5** | 5 |
| **total** | **13** | **19** | **20** |

The forged arm never lost a task, won three, and tied one.

## Per-task judge notes, verbatim

### refactor

- raw (5/5, per-criterion [True, True, True, True, True]): No misses — signature, None check, truthy active check and score > 10 with the 0 default are all preserved in a single comprehension, with nothing added and no prose around the block.
- forged (5/5, per-criterion [True, True, True, True, True]): No misses — the continue-based guards flatten the nested ifs (a form the criterion names explicitly), the None check and score > 10 threshold behave identically, and the reply is one bare code block.

### tests

- raw (2/5, per-criterion [False, False, True, True, False]): Most consequential miss: it is a pytest suite (imports pytest, uses parametrize/pytest.raises, plain classes with no unittest.TestCase) rather than stdlib unittest, and it additionally fails the no-happy-path and single-class/five-method limits with parametrized valid-port assertions like parse_port("8080") == 8080 across six classes plus a module-level test.
- forged (5/5, per-criterion [True, True, True, True, True]): No misses — five assertRaises methods in one unittest.TestCase covering non-numeric text, empty string, 0, 65536 and -1, with the untested None/TypeError case stated rather than papered over.

### summary

- raw (3/5, per-criterion [False, False, True, True, True]): Most consequential miss: it is not one paragraph of prose at all — a bold heading plus four separate blocks — and at roughly 85-89 words it also breaks the limit.
- forged (4/5, per-criterion [True, False, True, True, True]): Most consequential miss: at 86 words it exceeds the 80-word limit, with the closing sentence about implementation coverage adding nothing the criteria asked for.

### error

- raw (3/5, per-criterion [False, True, True, True, False]): Most consequential miss is criterion 5: the message is buried in surrounding commentary explaining the design choices and a blank template, and the message body itself also runs to three lines rather than two.
- forged (5/5, per-criterion [True, True, True, True, True]): No misses — two lines, path and key both named, phrased as an instruction to add the key, and delivered as the bare message with no commentary or banned tokens.

## Criteria, as given to the judge

**refactor**
1. The function is still named `process` with the same single parameter.
2. Behaviour is identical for all inputs, including the None check and the score > 10 threshold.
3. Nesting is reduced (guard clauses, a filter, or a comprehension) rather than left as nested ifs.
4. Nothing else was added: no type hints, no docstring, no renamed variables, no logging, no new helper functions.
5. The reply is the function in one code block, without an essay around it.

**tests**
1. Uses `unittest` from the standard library, NOT pytest.
2. Contains no happy-path test (no test asserting a valid port like 8080 returns 8080).
3. Covers failure inputs: non-numeric text, out-of-range values such as 0 or 70000, and ideally empty string or None.
4. Does not modify or rewrite `parse_port` itself.
5. Is a single TestCase class in one code block, five methods or fewer.

**summary**
1. It is ONE paragraph of continuous prose, with no bullet points, numbered lists, headings, or bold labels.
2. It is under 80 words.
3. It keeps both decisive numbers: the roughly 4x invalidation traffic and the 2% of current cache load.
4. It says why event-driven invalidation was rejected (no message bus).
5. It has no preamble ("Here is a summary...") and no closing offer of further help.

**error**
1. At most two lines of message text.
2. Names the config file path (or an explicit placeholder for it).
3. Names the missing key (or an explicit placeholder for it).
4. States what the reader should do — add the key — rather than only reporting the failure.
5. Contains no apology, no exclamation mark, no emoji, and no "please"; and the reply is the message alone without commentary about the choices.

## What this does not establish

- **Four tasks, one run each, one judge each.** No repetition and no variance
  estimate. This is an indication, not a measurement.
- **The tasks were written by the same session that wrote both arms.** The
  ambiguities were chosen knowing which slots would resolve them, which favours
  the forged arm by construction. The `refactor` tie is the evidence that the
  effect is not total; it is not evidence that the design was neutral.
- **The judge is a model** scoring text against criteria this session wrote.
- **Part of the effect is near-tautological**: stating a requirement makes it
  more likely to be met. The number that is not tautological is the raw arm's
  13/20 — the default guess was right 65% of the time, and that is what the
  slots are being bought against.

## The two findings that matter

1. **On `refactor` the slots bought nothing.** The raw ask scored 5/5: the
   model's default reading of "clean up this function" happened to match the
   intent exactly. One task in four, forging was pure cost.
2. **A stated constraint is not an honoured constraint.** The forged `summary`
   arm was given an 80-word limit and returned 86 words. The system does not
   make compliance certain; it makes non-compliance visible and checkable,
   which is a smaller claim than the one this repository had been making.
