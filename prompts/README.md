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

All four inherit one rule: **an unsourced claim does not get written down.**
The prompts state it; `tools/verify_provenance.py` enforces it.

[`DERIVATION.md`](DERIVATION.md) is the audit trail for `base-operator.md`: one
row per rule, naming the evidence it came from. A rule with an empty evidence
column does not belong in the prompt, which is the check that keeps this a
reconstruction rather than a persona.
