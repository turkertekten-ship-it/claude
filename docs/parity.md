# Claude Code ↔ Console playground: what transfers, what does not

This document exists because the obvious plan for "bring Claude Code up to
playground level" was wrong, and the reason it was wrong is worth writing down
rather than quietly routing around.

## The thing being matched moved

The Anthropic Console **Workbench** — the prompt pane with saved prompts,
`{{variables}}` and an Evaluate tab — was **sunset on 17 August 2026**, ten
days before this was written. The release note is explicit that its three
signature features did not survive the move: *"Saved prompts, variables, and
evals are not supported in the updated Workbench."*
([release notes](https://platform.claude.com/docs/en/release-notes/overview))

The experimental prompt-tools APIs went with it —
`/v1/experimental/generate_prompt`, `/v1/experimental/improve_prompt` and
`/v1/experimental/templatize_prompt` were retired on the same date and now
return an error. ([release notes](https://platform.claude.com/docs/en/release-notes/overview))

What replaced it, on 18 August 2026, is **playground**: *"Playground supports
every Messages API parameter and includes templates that demonstrate API
features such as code execution and web search. It shows the full SDK request
and the API response for each run."*
([release notes](https://platform.claude.com/docs/en/release-notes/overview))

So there are two different targets hiding inside one word, and they want
opposite things:

| Target | What it is | What parity means |
|---|---|---|
| **playground** (current) | A full-parameter Messages API request builder with a response inspector | Show the exact request before sending it, and the full response after |
| **Workbench** (retired) | Prompt authoring with variables, saved versions, and an evals grid | Rebuild it somewhere it cannot be sunset — in the repository |

This repository does both, and the second is the larger half.

> The retired Workbench's feature set is documented outside the sunset docs, in
> Anthropic's own teaching material: `prompt_evaluations/02_workbench_evals/`
> in [anthropics/courses](https://github.com/anthropics/courses/tree/master/prompt_evaluations)
> walks through `{{VARIABLE}}` templating, the variables dialog, the Evaluate
> grid, per-row human scores, version labels and an "+ Add Comparison" control.
> That notebook is the parity checklist used below.

## The parameter sweep that cannot be built

The first feature anyone wants from a playground is a temperature sweep. It is
not available, and not because of a missing flag:

> *"Models released after Claude Opus 4.6 do not support setting temperature. A
> value of 1.0 will be accepted for backwards compatibility, all other values
> will be rejected with a 400 error."*
> ([Messages API](https://platform.claude.com/docs/en/api/messages))

All three are marked **Deprecated** unconditionally in the schema; the 400 is
scoped to models released after Opus 4.6. The backwards-compatibility carve-outs
are not symmetrical, and an earlier draft here flattened them into "except
legacy default values", which is wrong for `top_p`:

| Parameter | Accepted on post-4.6 models | Note |
|---|---|---|
| `temperature` | exactly `1.0` | which is its documented default |
| `top_p` | any value `>= 0.99` | a *range*; `top_p` has no documented default |
| `top_k` | nothing | any value returns a 400 |

The Python SDK v1.0, released 20 August 2026, *"removes long-deprecated
surface, including … the `temperature`, `top_p`, and `top_k` parameters on
Messages methods."*
([release notes](https://platform.claude.com/docs/en/release-notes/overview))

A temperature sweep in 2026 is therefore not a parity gap. It is a feature
request for an API that no longer exists. What replaced it as the quality dial
is **effort** — `output_config.effort` at `low | medium | high | xhigh | max`
([Messages API](https://platform.claude.com/docs/en/api/messages)) — which the
Claude Code CLI exposes directly as `--effort`. The workbench varies it the
same way it varies anything else: by declaring a variant per level and
comparing them. There is no separate sweep command, and no sweep of the
parameters above, because those are the ones the API now rejects.

## The matrix

Legend: **CC** = stock Claude Code; **WB** = this repository's `workbench/`.

### Prompt authoring

| Capability | playground | CC | WB | Notes |
|---|---|---|---|---|
| System prompt control | yes | `--system-prompt` | per variant | Also `--append-system-prompt` |
| `{{variable}}` templating | retired with Workbench | no | yes | Strict: an unfilled placeholder is an error, not an empty string |
| Saved prompt versions | retired with Workbench | no | yes | They are files in git, which is a stronger guarantee than a saved prompt in a console that can be sunset |
| Multi-turn message arrays | yes | via `--input-format stream-json` | no | See *Not built* below |
| Assistant prefill | yes | no | no | Incompatible with thinking on current models ([thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)) |
| Prompt generator / improver | retired | no | no | The endpoints return an error |

### Parameters

| Capability | playground | CC | WB |
|---|---|---|---|
| Model selection | yes | `--model` | per variant |
| Effort | yes | `--effort` | per variant |
| Extended thinking | yes | `--effort`, plus undocumented `--thinking` / `--max-thinking-tokens` | per variant |
| `temperature` / `top_p` / `top_k` | rejected by current models | no flag | deliberately not built |
| `max_tokens` | yes | `CLAUDE_CODE_MAX_OUTPUT_TOKENS` — **not honoured here** | sent, no observed effect |
| `stop_sequences` | yes | no flag | not reachable without an API key |
| Structured output schema | yes | `--json-schema` | per variant |
| Tool definitions | yes | `--tools`, MCP | per variant, on/off |
| Budget ceiling | no | `--max-budget-usd` | per variant |

### Inspection

| Capability | playground | CC | WB |
|---|---|---|---|
| See the request before sending | yes | no | `workbench plan` |
| Full response envelope | yes | `--output-format json` | stored per run |
| Token counts | yes | in the JSON envelope | rolled up per variant |
| Cost | Console usage pages | `total_cost_usd` | summed, never estimated |

### Evaluation — where the workbench goes past both

| Capability | playground | CC | WB |
|---|---|---|---|
| Eval grid over test cases | retired with Workbench | `claude plugin eval` | yes |
| Deterministic graders | — | `tool_used` and others | 11 deterministic + 6 environmental |
| LLM judge | — | `llm` grader, judge model defaults to haiku | yes, odd-panel majority |
| Grade by shell command | — | not documented | `command` grader |
| With/without ablation | — | `--ablation with-without` | — use `claude plugin eval` |
| **N-way prompt variant comparison** | not documented | no | yes |
| **Blind identity stripping** | not documented | no | yes |
| **Both-order position swap** | not documented | no | yes |
| **Significance testing** | not documented | no | Wilson, exact McNemar, bootstrap, Bradley-Terry |
| **Identical-pair blinding control** | not documented | no | yes |

The last five rows are the point. Everything above them is catching up; those
are the part that did not exist to copy.

Two honesty notes on that table, because both were overstated in an earlier
draft of this file:

- The playground column reads **"not documented"**, not "no". Its UI is behind
  authentication and the Help Center article describing it is on a domain this
  container cannot reach, so what controls it exposes is genuinely unknown —
  recorded as `U-7` in `provenance/unknowns.md`. The retired Workbench *did*
  ship a side-by-side output comparison mode, in July 2024, with human scoring.
  Whether anything equivalent survives is not established here.
- The Claude Code column names `tool_used` because `claude plugin eval --help`
  in this container names it. The fuller grader list reported by a delegated
  research pass — `regex`, `tool_order`, `file_exists`, `baseline` — is
  plausible and partly corroborated by that help text, which mentions `llm` and
  `baseline` as the paid graders, but the complete list was not verified
  first-hand and is not asserted as one.

## Why blind comparison had to be written rather than borrowed

A prior-art sweep found that the standard tools do not do it:

- **promptfoo** (24.6k stars) has 66 assertion types and a `select-best`
  grader. `matchesSelectBest` in `src/matchers/comparison.ts` makes **a single
  call** with all candidates in fixed order and parses the first integer out of
  the reply. Neither the code nor its documentation mentions position bias,
  swapping or randomisation.
- **openai/evals** ships 18 declarative model-graded YAML templates including a
  pairwise `battle.yaml`. Grepping `evals/elsuite/modelgraded/` for
  `shuffle|randomi|position|swap|permut` returns nothing.
- **lm-sys/FastChat** does do it, and is the reference — but only on a code path
  that is not its default. In the optional `--mode pairwise-baseline` /
  `pairwise-all` modes, `play_a_match_pair` in `fastchat/llm_judge/common.py`
  calls the judge twice with the answers transposed, and
  `display_result_pairwise` in `show_result.py` scores any pair whose two
  verdicts disagree **as a tie**. MT-Bench's default and recommended mode is
  single-answer 1-10 grading, which grades each answer once with no pairwise
  comparison and no swap at all.

The reason it matters is measured. In *Judging LLM-as-a-Judge with MT-Bench and
Chatbot Arena* ([arXiv 2306.05685](https://arxiv.org/abs/2306.05685)), judge
consistency under a swapped presentation order — the share of pairs where the
verdict survives the swap — was **65.0% for GPT-4, 46.2% for GPT-3.5 and 23.8%
for Claude-v1** on the default prompt. The paper's own prescription is quoted
verbatim: *"A conservative approach is to call a judge twice by swapping the
order of two answers and only declare a win when an answer is preferred in both
orders."*

That is exactly what `workbench/blind.py` implements, and
`tests/test_workbench.py` proves it by scripting a judge that always picks
whatever is shown first and checking the harness records a tie.

Two further findings from the same paper shape the implementation:

- **Verbosity bias.** Answers padded with rephrased duplicates that add no
  information were preferred over the originals in **91.3%** of trials by
  Claude-v1 and GPT-3.5 (GPT-4: 8.7%) — *while the judge prompt already
  contained the instruction not to be influenced by length*. The workbench
  carries that instruction anyway, and also reports mean output length per
  variant, because the instruction demonstrably does not suffice.
- **Self-preference.** GPT-4 favoured its own output by ~10 percentage points
  of win rate and Claude-v1 by ~25. The paper hedges this hard — *"our study
  cannot determine whether the models exhibit a self-enhancement bias"* — so
  the workbench does not refuse a same-family judge; it warns, and says why.

> Access note, recorded rather than glossed: `arxiv.org` is blocked by this
> container's egress proxy. The MT-Bench figures above were confirmed against
> two independent full-text mirrors on GitHub that agree exactly, and against
> the FastChat implementation they describe. That is corroboration, not a
> reading of the canonical PDF, and it is marked as such in
> `provenance/sources.yaml`.

## Not built, and why

- **Multi-turn message arrays.** `claude -p` takes a single prompt string.
  Multi-turn is reachable via `--input-format stream-json`; no suite here needed
  it, so it is not implemented rather than half-implemented.
- **`stop_sequences`.** No CLI flag under any spelling probed, and no
  `ANTHROPIC_API_KEY` in this environment to reach the Messages API directly.
  `max_tokens` *was* on this list until a fact-checker pointed out that
  `claude --help` is not a complete inventory of accepted flags: probing the
  parser directly turned up `--thinking`, `--max-thinking-tokens` and
  `--task-budget`, none of which appear in the help text, and the documented
  `CLAUDE_CODE_MAX_OUTPUT_TOKENS` is documented as covering output length.
  Thinking control is wired through per variant and verified working. The
  lesson is worth keeping: absence from `--help` is not absence from the parser.

- **An output-token cap.** `CLAUDE_CODE_MAX_OUTPUT_TOKENS` is plumbed through
  per variant, and `tools/parity_check.py` records it as **FAIL**: measured at
  32, 64, 512 and 4096 it never changed the ceiling the backend reported
  (`maxOutputTokens` stayed 32000) and the output exceeded the cap every time.
  The variable is documented; it did not work in this container. The plumbing
  stays because it may work elsewhere, the conformance harness stays red
  because here it does not, and this row is the reason a matrix should be
  executed rather than believed.
- **The Batch API's 50% discount.** ([pricing](https://platform.claude.com/docs/en/about-claude/pricing))
  Real money for a large sweep, and unreachable without an API key.
- **`count_tokens` before sending.** The endpoint exists
  ([count_tokens](https://platform.claude.com/docs/en/api/messages-count-tokens));
  again, no API key. `workbench plan` shows character counts instead and says so.
- **Human grading rows.** The retired Workbench had a per-row human score
  column. Nothing here collects one.
- **A price table.** Deliberately absent. Costs come from the backend's own
  `total_cost_usd`. A hard-coded price is a fact that goes stale without anyone
  noticing, and this repository's whole premise is not writing down facts it
  cannot source at the moment of reading.

## The gap that was actually open — corrected

An earlier draft of this file claimed that no prompt-workbench or eval plugin
existed for Claude Code across `awesome-claude-code`,
`anthropics/claude-plugins-official` and `anthropics/claude-code`. **That was
wrong, and it was wrong in an avoidable way.**

`anthropics/claude-plugins-official` ships **`skill-creator`**, a first-party
plugin that is a variant-evaluation harness: `agents/comparator.md`,
`agents/grader.md`, `agents/analyzer.md`, `scripts/run_eval.py`,
`scripts/aggregate_benchmark.py` (mean ± stddev with deltas),
`scripts/run_loop.py` (an automated description-optimisation loop that proposes
variants and selects a `best_description` by held-out score). Its comparator is
explicitly blind: *"You receive two outputs labeled A and B, but you do NOT
know which skill produced which."*

It was installed on the machine this was written on, at
`/mnt/skills/examples/skill-creator`, and listed among the session's own
available skills the entire time. The claim was made from a prior-art sweep of
remote repositories without checking what was already mounted locally — Orient
running ahead of Observe, which is the failure this repository exists to
prevent. A hostile fact-checker told to refute the claim found it in minutes.

### What the corrected landscape looks like

| Tool | Scope of comparison | Blind? | Both orders? |
|---|---|---|---|
| `claude plugin eval` | with-plugin vs without-plugin | arms are fixed | no |
| `skill-creator` | with-skill vs baseline, or version A vs B | **yes** — labels A/B, identity withheld | **no** |
| promptfoo `select-best` | N candidates, one call | no | no |
| openai/evals `battle.yaml` | pairwise | no | no |
| FastChat `pairwise-*` modes | pairwise | yes | **yes** |
| this workbench | N prompt variants, all pairs | yes, with an identical-pair control | **yes** |

So the honest statement is narrower than the one it replaces: blind comparison
was **already** available first-party for skills. What none of the
Claude-Code-side tools do is judge each pair **in both presentation orders and
count a win only when the verdict survives the swap** — the mitigation the
MT-Bench measurements call for. Grepping `skill-creator` for
`swap|position bias|randomi|shuffle|both orders` returns nothing; its comparator
makes one call with A and B in a fixed order.

That, plus N-way prompt-variant comparison and the significance layer, is what
remains genuinely additive here. It is a smaller claim than "the niche is open",
and it is the one the evidence supports.

**Use `skill-creator` instead of this** when the thing under test is a skill and
you want its improve-loop and post-hoc analyzer. Reach for the workbench when
you need the swap protocol, more than two variants, or a p-value.
