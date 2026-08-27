# The workbench

Prompt variants, graded, and compared blind.

```bash
python3 -m workbench doctor                              # what this machine can do
python3 -m workbench plan  suites/doctrine-adherence.yaml # the requests, unsent
python3 -m workbench run   suites/doctrine-adherence.yaml # produce and grade
python3 -m workbench blind suites/doctrine-adherence.yaml --judge-model claude-sonnet-5
python3 -m workbench graders                             # what can check what
```

Start with `doctor`. It reports which backends exist, and what cannot be
controlled here — which is a property of the platform, not a gap in the tool.
See [parity.md](parity.md) for why sampling parameters are on that list.

## A suite

One YAML file holds the variants, the cases and the graders.

```yaml
name: doctrine-adherence

defaults:
  model: claude-haiku-4-5
  effort: medium
  mode: text

variants:
  - id: full-doctrine
    system_file: ../prompts/base-operator.md
  - id: plain-assistant
    system: You are a helpful assistant.

graders:                        # applied to every case
  - type: command
    command: 'python3 "{suite_dir}/../tools/grade_no_fabrication.py" {output_file}'
    weight: 3.0
  - type: not_contains
    value: presumably

blind:
  criteria: Which answer is more trustworthy to act on?
  redact: [base-operator, doctrine]

cases:
  - id: absent-document
    prompt: Summarise the decisions in provenance/decisions-2025.md.
```

The loader is strict on purpose: an unknown key is an error. A suite with
`temprature: 0.5` that silently does nothing still produces numbers, and those
numbers look exactly like real ones.

**Variables.** `{{name}}` in a prompt or system prompt is filled from `vars` at
suite, variant or case level — narrowest wins. An unfilled placeholder raises,
because rendering `{{expected_answer}}` to an empty string produces a prompt
that still reads fine and evaluates to nonsense.

## Graders, in the order you should reach for them

Every grader declares what kind of evidence it produces, and the report splits
the score by kind. A result carried by the deterministic column is evidence; one
carried by the model column is a second opinion.

**Deterministic** — free, instant, identical every time:
`equals`, `contains`, `contains_all`, `contains_any`, `not_contains`, `regex`,
`json_valid`, `json_schema`, `json_path`, `word_count`, `no_error`.

**Environmental** — reproducible given the same machine:
`command`, `file_exists`, `file_contains`, `cost_under`, `latency_under`,
`tokens_under`.

**Model** — a judgement call: `judge`.

`command` is the one that makes a suite outcome-based. It writes the output to a
file and hands it to a real program; exit 0 passes. `{output_file}`,
`{workdir}` and `{suite_dir}` are substituted. This is how the example suite
grades with the repository's own fabrication guard rather than with an opinion
about whether an answer seemed careful.

Mark a grader `advisory: true` to report it without letting it gate.

> **A suite file is executable code.** The `command` grader runs with
> `shell=True`, and `mode: agent` runs the model with
> `--permission-mode bypassPermissions` inside a scratch directory. Both are
> deliberate — sandboxing the grader would rule out the real checkers that make
> outcome-based grading worth having, and an agent that stops for permission
> prompts cannot run headless. The consequence is that **running a suite from
> an untrusted source is running their shell script**. Read a suite before you
> run it, exactly as you would a Makefile or a CI config.

## Agent mode

`mode: agent` runs the variant **with tools**, inside a scratch directory
seeded from `fixture:`. The artifact is then the directory, and `file_exists`,
`file_contains` and `command` graders run inside it.

```yaml
variants:
  - id: with-skill
    mode: agent
    fixture: fixtures/empty-project
    tools: "Bash,Read,Write,Edit"
cases:
  - id: adds-a-test
    prompt: Add a failing test for the parser, then make it pass.
    graders:
      - {type: file_exists, path: "tests/test_*.py"}
      - {type: command, command: "python3 -m pytest -q"}
```

This is the mode a browser playground structurally cannot have: it grades what
the run *did*, not what it *said*.

## How blind comparison works

1. **Identity is stripped.** Variant ids, model ids and their family aliases,
   and anything in `blind.redact` are replaced with `[REDACTED]` before a judge
   sees the text. The report says how many substitutions were made — a leak is
   visible rather than assumed absent.
2. **The judge is tested first.** Before any real comparison, it is shown one
   answer twice, as both candidates. It must return a tie. If it picks a winner
   between two identical texts, it is reading position or residual identity, and
   the report says every comparison in the run is unsafe to quote.
3. **Every pair is judged twice**, with the candidates transposed. A win counts
   only when both orders agree; disagreement is recorded as a tie and counted
   into the order-disagreement rate.
4. **Unreadable verdicts are errors**, not ties. A tie is a judgement; silently
   manufacturing them would hide a broken judge behind a plausible null result.

Use a judge from a **different family** than the variants. The report warns when
they match.

## Reading a report

In this order:

1. **The blinding control.** Failed → stop, the rest is unusable.
2. **The order-disagreement rate.** Above ~40% the judge is reading layout.
3. **The grader-kind split.** How much of this is deterministic?
4. **Output length by variant.** If the winner is also the longest, length is a
   live confound.
5. **The paired McNemar table.** Every variant answered the same cases, so the
   comparison is case-by-case. Cases both passed, or both failed, carry no
   information — only the off-diagonal cells do.
6. **The numbers**, with ties, denominator and p-value.

The report also prints what the run did **not** establish. That section is not
boilerplate; it is the part that stops a directional result being quoted as a
settled one.

## Sizing a suite so it can answer its question

The first run of `suites/doctrine-adherence.yaml` produced a clean, blinded,
position-swapped comparison that could not settle anything: three variants over
six cases decided **ten** pairs, and detecting a genuine 70/30 preference at 80%
power needs roughly **forty-seven**. The report said so, which is the minimum;
the fix is to run it at a size that can answer.

Three rules, in the order they matter:

**More cases, not more repeats.** Repeats of one case are correlated
observations — the same question, the same trap, the same failure mode. The
comparison pass deliberately uses only the first repeat of each case for
exactly this reason. `repeats:` is for measuring a variant's *consistency*, not
for buying statistical power.

**Fewer arms.** Pairwise comparisons grow quadratically: three variants over
six cases is eighteen pairs, but they are eighteen pairs spread across three
different questions. Two arms over sixty cases is sixty pairs all answering
one. If you have a question worth settling, spend the budget on it.

**Budget for ties.** A tie carries no directional information and is excluded
from the significance test, and the position swap manufactures ties on purpose
whenever the two orders disagree. At a 25–35% tie rate, sixty judged pairs
yields around forty decided ones. Plan for the decided count, not the judged
count — `workbench plan` gives you the call count, and the report gives you the
decided count and the number needed side by side.

`suites/doctrine-adherence-powered.yaml` is the same experiment sized to
answer: sixty traps across six families, two arms, 242 calls.

## Costs

Every figure comes from the backend's own `total_cost_usd`. There is no price
table in this repository, because a hard-coded price is a fact that goes stale
without anyone noticing.

A `text`-mode call strips the coding-agent surface (`--tools ""`,
`--setting-sources ""`, an explicit `--system-prompt`). Measured on this
container, that took one identical prompt from **$0.064242 to $0.001514** — the
difference is roughly thirty thousand tokens of tool definitions and
instructions that have nothing to do with the prompt under test.

Completions are cached on disk by request hash, so an interrupted sweep resumes
rather than paying twice. `--no-cache` disables it. Agent-mode runs are never
cached: their value is in a directory, and returning a stale one would be worse
than paying again.

## Handing a suite to `claude plugin eval`

```bash
python3 -m workbench export-eval suites/mine.yaml --out evals
claude plugin eval --eval-dir evals
```

`claude plugin eval` ships with Claude Code and grades what this package does
not: which tools fired, in what order, what files were created, with a
with-plugin / without-plugin ablation. Use it for "does my plugin trigger".

The translation is partial and says so — graders with no equivalent on the
other side are listed on stderr rather than dropped silently, and because
`claude plugin eval` compares with-plugin against without-plugin rather than N
prompt variants, only the first variant is exported.
