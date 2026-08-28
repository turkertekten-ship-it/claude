---
description: Forge a rough ask into a checkable prompt — seven slots, an adversarial reading pass, and a linter that has to exit 0.
argument-hint: [the raw ask, or a path to a prompt file]
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent
---

Forge this into a prompt that can be checked: **$ARGUMENTS**

If `$ARGUMENTS` is empty, ask what to forge and stop. There is nothing here to
work on, and an empty imperative is exactly the input this command teaches
sessions to refuse.

**If the argument is a path, never write to it.** Output the forged prompt and
let the owner apply it. A committed system prompt rewritten in place by a
command they ran to *inspect* it is the one outcome here that destroys
something.

Read `.claude/skills/prompt-forge/SKILL.md` first and work its four phases.

1. **Observe.** If `$ARGUMENTS` is a path, lint that file directly. Otherwise
   write the ask verbatim to a scratch file outside the repository — do not
   tidy it on the way in, since the untidiness is the data. Then
   `python3 tools/prompt_forge.py lint --profile <task|build|research|system|chat|directive> <file>`
   and record which slots are absent and which hazards fired. No interpreting
   yet.
2. **Orient.** Send the raw ask to the `prompt-critic` subagent and ask for the
   readings under which the resulting work would differ. Its report is
   second-hand — keep only the divergences you can point at in the text.
2b. **Reverse the prompt, when the ask is thin.** If three or more slots are
   absent and the owner is here to answer, invert the direction before
   forging: ask up to five clarifying questions in one message, aimed at the
   preferences they did not state, and build the prompt from the answers. Five
   questions asked once cost a turn; a wrong reading of a thin ask costs the
   work. Skip this entirely when nobody is there to answer — see step 3. (The
   technique is documented as Saraev's "reverse prompting"; `docs/prompting.md`
   says what that attribution rests on.)

3. **Decide.** For each absent slot take exactly one of three moves: get the
   evidence (read the file, run the command), ask the owner one question with
   the options named, or write an escape clause into the prompt. Inventing a
   plausible requirement is not one of the three. Hazard findings are not gaps
   — rewrite the offending phrase.
4. **Act.** `python3 tools/prompt_forge.py compile --profile <P> <file>`, fill
   the `<<MISSING:` markers with what you established, and re-lint until it
   exits 0 — meaning no error and no warn findings. Info findings are advisory.

Deliver, in this order: the forged prompt in a single fenced block ready to
paste; the before and after scores; one line per gap saying how you closed it;
and any question you still need answered.

If the ask is already unambiguous and the linter exits 0, say so and hand it back
unchanged. Padding a good prompt with ceremonial sections makes it worse, and
"this one needs nothing" is a complete answer.
