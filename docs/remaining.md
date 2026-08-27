# What is not done, and exactly what would close it

Three things. One is a credential, one is a product that no longer exists, and
one is a question the evidence answered in the negative. They are listed with
what would close each, because "not done" without that is just a complaint.

---

## 1. Eight capabilities need a credential this container does not have

**State:** implemented, wire-tested against a conforming local server, blocked
on authentication to Anthropic's endpoint.

`stop_sequences`, an exact `max_tokens`, `count_tokens` before sending, batch
submission at half price, custom tool definitions with your own schema, prompt
caching, image and document input, and `temperature`/`top_p`/`top_k` on models
old enough to accept them.

Every documented credential path was checked and all are closed:
`ANTHROPIC_API_KEY` unset, no `ant` CLI, no `~/.config/anthropic`, no
`~/.claude/.credentials.json`, and the OAuth token file descriptor the
environment advertises resolves to a pipe the CLI consumed at startup.

**What closes it**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 -m workbench doctor                       # should now report the API backend usable
python3 tools/parity_check.py                     # the eight rows move off UNREACHABLE
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

**State:** answered, in the negative, across six runs.

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

**What closes it:** roughly forty-seven decided pairs, which at the observed
discordance rate means several hundred cases rather than tens. The cheaper route
is repeated sampling per case rather than new cases — published work puts the
minimum detectable effect at 13.2% for one sample per question and 7.5% for ten.
Neither was run, because six experiments agreeing on a small-or-absent effect is
weak grounds for spending a large amount of someone else's money to see the same
thing a seventh time.

**What does not close it:** re-running the same suites hoping for a different
sign. That is the failure this repository exists to catch, and it would be
caught.

---

> The honest summary: one item needs a key, one needs a time machine, and one
> has an answer that is simply not the answer anyone wanted.
