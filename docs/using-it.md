# Using it

You have a prompt. Where you are decides what to do.

## In a chat — claude.ai, or another vendor

Nothing here runs there. Paste the marked block from
[`prompts/portable-preamble.md`](../prompts/portable-preamble.md) into the
custom instructions, once. It carries the parts that survive
being pasted: do not fabricate, treat the prompt as a specification, ask at most
one question, and when nobody is there to answer, assume the cheapest thing to
correct and say which assumption you made.

## In a terminal

Once per machine:

```bash
bash tools/install_prompt_system.sh      # /prompt, /prompt-audit, /prompt-habits everywhere
bash tools/install_git_hooks.sh          # in this repo: no pushing a red suite
```

Then, on any rough ask:

```
/prompt fix the failing test and clean up the module
```

It lints the ask, sends it to a subagent that attacks it for ambiguity, and
hands back a prompt with every gap either closed or marked. Or run the linter
directly:

```bash
prompt-forge lint --profile task my-prompt.txt     # 0 clean, 1 findings
prompt-forge compile my-prompt.txt                 # into the seven slots
```

When the answer comes back, check it against the prompt that asked for it:

```bash
check-output my-prompt.txt answer.txt --suggest-rule
```

It counts what can be counted, prints any command the prompt named for you to
run, lists what only a reader can judge, and turns each failure into the command
that records it as a rule.

## For the prompts you have already written

```bash
python3 tools/ingest_chat_archive.py ingest --include-projects
python3 tools/prompt_habits.py --worst 5
```

That scores your real prompts and names the habit costing most. One low score is
a bad afternoon; the same rule firing on most of what you write is worth
fixing once.

---

## The seven slots

```
ROLE           who is answering, if it changes the answer
CONTEXT        what is already true — paths, versions, what has been tried
TASK           one imperative, and the artifact it produces
CONSTRAINTS    what is forbidden; the bound on length, scope, and effort
OUTPUT         the exact shape of the reply
ACCEPTANCE     the check that decides whether it is right
IF YOU CANNOT  say so and stop / ask me / report what you actually saw
```

Always write the last one. It is the one usually skipped, and the one that stops
a confident wrong answer. Fill the others where they change the answer — padding
a prompt with sections it does not need makes it worse, and the linter is built
so that structure alone earns nothing.

## The two CLEARs

Both are supported, and the tool refuses a bare `--framework clear` because they
are different frameworks sharing an acronym:

- **`clear-lo`** — Concise, Logical, Explicit, Adaptive, Reflective. Lo, *The
  Journal of Academic Librarianship* 49(4), 2023.
- **`clear-saraev`** — Clarity, Logic, Examples, Adaptation, Results.
  Attributed to Nick Saraev by third-party documentation read first-hand;
  unverified at source, because none of his own pages was reachable.

[`docs/prompting.md`](prompting.md) has the standard, what each attribution
rests on, and the properties a new rule must not break.
