---
description: Forge a rough ask into a checkable prompt — seven slots, an adversarial reading pass, and a linter that has to exit 0.
argument-hint: [the raw ask, or a path to a prompt file]
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent
---

Forge this into a prompt that can be checked: **$ARGUMENTS**

Read `.claude/skills/prompt-forge/SKILL.md` first and work its four phases.

1. **Observe.** Write the raw ask to a scratch file verbatim — do not tidy it
   on the way in, since the untidiness is the data. Run
   `python3 tools/prompt_forge.py lint --profile <task|build|research|system|chat> <file>`
   and record which slots are absent and which hazards fired. No interpreting
   yet.
2. **Orient.** Send the raw ask to the `prompt-critic` subagent and ask for the
   readings under which the resulting work would differ. Its report is
   second-hand — keep only the divergences you can point at in the text.
3. **Decide.** For each gap take exactly one of three moves: get the evidence
   (read the file, run the command), ask the user one question with the options
   named, or write an escape clause into the prompt. Inventing a plausible
   requirement is not one of the three.
4. **Act.** `python3 tools/prompt_forge.py compile --profile <P> <file>`, fill
   the `<<MISSING:` markers with what you established, and re-lint until it
   exits 0.

Deliver, in this order: the forged prompt in a single fenced block ready to
paste; the before and after scores; one line per gap saying how you closed it;
and any question you still need answered.

If the ask is already unambiguous and the linter exits 0, say so and hand it back
unchanged. Padding a good prompt with ceremonial sections makes it worse, and
"this one needs nothing" is a complete answer.
