# System prompts

Each file here is a complete prompt, meant to be pasted into a session's system
prompt or appended via `append_system_prompt`. They are deliberately short: a
prompt nobody reads to the end enforces nothing.

| File | Use |
|---|---|
| `base-operator.md` | The default. Every session in this fleet starts here. |
| `researcher.md` | Sessions whose job is to establish facts rather than build. |
| `builder.md` | Sessions writing code against facts already established. |
| `archive-ingest.md` | Sessions processing a conversation export. |
| `prompt-smith.md` | Sessions whose output is other prompts. |
| `portable-preamble.md` | Not a session prompt — the block to paste into a chat, a project's custom instructions, or a terminal that cannot read this repository. |

They inherit one rule: **an unsourced claim does not get written down.** The
prompts state it; `tools/verify_provenance.py` enforces it.

These files are themselves prompts, so they are held to the prompt standard:

```bash
python3 tools/prompt_forge.py score --profile system prompts/*.md
```

`README.md` scores badly there and should: it is documentation about prompts,
not a prompt. Everything else in this directory is expected to hold an A or a
B, and `tests/test_prompt_forge.py` fails the build if any of them acquires an
error-level finding.
