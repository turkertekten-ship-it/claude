# What is not done, and exactly what would close it

Three things. One is a credential, one is a product that no longer exists, and
one is a question the evidence answered in the negative. They are listed with
what would close each, because "not done" without that is just a complaint.

---

## 1. Four capabilities need a credential this container does not have

**State:** implemented, wire-tested against a conforming local server, blocked
on authentication to Anthropic's endpoint.

Direct Messages API access, batch submission at half price, `speed`/fast mode,
and `temperature`/`top_p`/`top_k` on models old enough to accept them.
[src:PARITY-COUNT-CORRECTED-2026-08-28]

`stop_sequences` **was** on this list and came off it: the CLI backend applies
it client-side, verified live, and the row moved from UNREACHABLE to PASS.
[src:STOP-SEQUENCES-CLI-2026-08-28] Of the four above, two need a credential
and two cannot be reached from here at all — `temperature`/`top_p`/`top_k` were
removed from the platform rather than being missing from this tool.

This list used to have eight items. Four came off it without a credential —
`count_tokens`, prompt caching, image input and custom tool definitions — and
they are not on it because the *endpoint* for each is still unreachable while
the *capability* is not. `usage.input_tokens` counts tokens, the CLI caches a
repeated prefix by itself, `Read` passes image bytes to the model, and MCP
contributes tools with your own schema. All four are proved live by
`tools/parity_check.py`. [src:TOKEN-COUNT-DIFFERENTIAL-2026-08-28]
[src:CLI-CAPABILITY-RECOVERY-2026-08-28]

What remains genuinely API-only is the *request-body* form of each: placing a
`cache_control` breakpoint where you choose, an image as a content block,
`tools` in the body. Those rows are still UNREACHABLE and say so, and they name
the endpoint rather than standing in for the capability — which is exactly the
confusion that kept the other four on this list for a day.

Every documented credential path was checked and all are closed:
`ANTHROPIC_API_KEY` unset, no `ant` CLI, no `~/.config/anthropic`, no
`~/.claude/.credentials.json`, and the OAuth token file descriptor the
environment advertises resolves to a pipe the CLI consumed at startup.

**What closes it**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 -m workbench doctor                       # should now report the API backend usable
python3 tools/parity_check.py                     # the remaining rows move off UNREACHABLE
python3 -m workbench run suites/mine.yaml --backend anthropic-api
```

A suite reaches the new parameters per variant:

```yaml
variants:
  - id: cached-and-tooled
    cache_system: true                # the largest cost lever for a suite
    stop_sequences: ["\n\n---"]
    max_output_tokens: 2048           # exact, not the env-var approximation
    tool_defs:
      - name: get_weather
        description: Look up weather
        input_schema: {type: object, properties: {city: {type: string}}}
  - id: legacy-sampling
    model: claude-opus-4-6            # 4.6 and earlier still accept these
    temperature: 0.2
```

Sampling parameters sent to a model released after Opus 4.6 are refused before
the request leaves, rather than returning a 400 you have to decode.

**What does not close it:** nothing available inside this container. This is
the one item that was never mine to fix.

---

## 2. The Console Workbench was sunset on 2026-08-17

**State:** impossible, and not in the sense of "hard".

Access ended ten days before this was written, and the release note is explicit
that saved prompts, variables and evals are not supported in what replaced it.
Parity with a live Workbench UI cannot be demonstrated by anyone, including the
Console.

**What closes it:** nothing. What was done instead is the only thing available —
the retired half was rebuilt here, in files under version control, where it
cannot be sunset again. `suites/` holds the eval sets, `{{variables}}` render
strictly, and prompt versions are git history rather than console state.

The *current* playground is a full-parameter Messages API request builder with a
response inspector. That target is matched: 18 of 18 generally-available
parameters and 6 of 6 beta ones, checked by `tools/api_surface_check.py` rather
than asserted.

---

## 3. The operating prompt is not shown to reduce fabrication

**State:** answered, in the negative, across eight runs on two model families
— the seventh adequately powered and pre-registered, the eighth replicating it
on a second family. [src:SONNET-VALID-2026-08-28]

The deterministic layer separated nothing. The blind judge preferred the prompt
decisively on easy traps — 42 to 8, p < 0.001, and the preference survived a
length control — but that advantage vanished on traps hard enough to make both
arms fail: 7 to 5 with 14 ties, p = 0.77. A revision written against the
audited failures fixed two cases on the set its rules came from and none on
fourteen held-out traps, which is the shape of overfitting and was committed to
as such before the run.

Counting only hand-audited fabrications on the hard set: one for the operating
prompt, three for a plain assistant. That is the direction the prompt was
written to produce, and nowhere near significant at twenty-six cases.

**The seventh run closed the power question.** The owner authorised it, so the
cheaper route above was taken: 40 traps, two arms, three samples each, 240 runs
at $8.66, with the analysis pre-registered and run unmodified. Mean paired
difference −0.050, clustered 95% CI [−0.155, +0.026]. It spans zero. Hand
auditing all 16 failures moved it to −0.042, [−0.132, +0.026] — toward zero,
because two of the three overturned gradings favoured the plain arm.
[src:POWERED-FAB-2026-08-28] [src:POWERED-FAB-AUDIT-2026-08-28]

The stratified half of that analysis had silently never run — the run file
never carried the key the stratum lookup read. Repaired: tuned (26 cases)
−0.0256 [−0.1000, +0.0400], p = 1.0; held-out (14 cases) −0.0952
[−0.2667, +0.0000], p = 0.25. Both span zero, and the headline is unchanged.
[src:STRATIFICATION-NEVER-RAN-2026-08-28]

So the state is now: answered in the negative across eight runs on two model
families, one of them
adequately powered for the effect size the earlier six suggested. Any real
effect is under roughly five percentage points.

**The second family ran too, and agrees.** Forty traps, two arms, on a
different model family: the prompt 120/120 against 109/120, mean paired
difference −0.0917, CI [−0.2045, +0.0000], p = 0.1250.
[src:SONNET-VALID-2026-08-28] Negative again, spanning zero again.

**And the control that was missing now exists.** Every trap suite here shared a
blind spot: all cases are traps, so a perfect score could mean the prompt spots
traps or that it declines everything. On forty questions where declining would
be wrong, both arms answered 80 of 80 on Sonnet. On Haiku the operating prompt
answered 78 of 80, declining two questions any assistant should answer — so it
over-refuses at roughly 2.5% on the family the null was measured on.
[src:OVER-REFUSAL-HAIKU-2026-08-29]
[src:NO-OVER-REFUSAL-2026-08-28]

**What is still open, and it is narrower than before:** why so few cases
discriminate. Thirty-six of forty were ties, and four discordant cases against
zero floors the two-sided sign test at p = 0.125. The limit is the suite's
discriminating power, not the sample size.

**What closes the remainder:** traps that separate the arms more often. More
repeats will not.

**What does not close it:** re-running the same suites hoping for a different
sign. That is the failure this repository exists to catch, and it would be
caught.

---

> **Four rows left this list without anyone spending anything.** `count_tokens`
> was unreachable only as an endpoint — the capability was reachable the whole
> time through `usage.input_tokens`, and the operating prompt turns out to be
> 573 tokens — measured against the file now kept as
> `prompts/base-operator-v1.md`, before v3 replaced it as the default.
> [src:TOKEN-COUNT-DIFFERENTIAL-2026-08-28] [src:V3-PROMOTION-2026-08-29]
> [src:OPERATING-PROMPT-TOKENS-2026-08-28] Asking the same question of the rest
> moved prompt caching, image input and custom tool definitions too: all three
> work through the CLI, none needs a key, and the matrix read 27 passed,
> 0 failed, 9 unreachable — three rows added for playground fields it had no
> row for at all. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
> [src:CLI-TRANSPORT-ROWS-2026-08-28]
>
> The lesson is not about tokens: an item can sit on a blocked list because the
> sentence justifying it is true about the thing it names and false about the
> thing you wanted. A false sentence would have been caught by the guard this
> repository is built around. A true one, standing in for a question nobody
> re-asked, is invisible to it — and nothing here detects that.

## 4. Two things left open by a spending decision, not by evidence

**`U-12` — v3's fabrication guardrail is single-sample.** Closing it costs
~$6.50: `suites/fabrication-v3-guard.yaml` with `repeats: 3` on
`claude-haiku-4-5`, analysed with `tools/analyse_fabrication.py`. Not run
because this session spent $54.28 against an authorised ~$20-40
[src:SPEND-ACCOUNTING-2026-08-29], and the owner expressed no preference when
asked, so the call was mine: stop.

**`U-13` — the geography concentration is unexplained.** v1 declined 11 of 80
geography runs and 0 of 98 across six other categories. That the defect is real
and that v3 fixes it are both established; what the defect *is* is not.
[src:V3-GEOGRAPHY-2026-08-29]

Both are cheap, both are specified precisely enough to run without re-deriving
anything, and neither blocks the work that is done.

---

> The honest summary: one item needs a key, one needs a time machine, and one
> has an answer that is simply not the answer anyone wanted — now established
> at a sample size that makes it an answer rather than an absence of one.
