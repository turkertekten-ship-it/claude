---
name: divide
description: Divide a request into a numbered task list with checkable done-conditions. Use when a request bundles several pieces of work, when asked to plan or break something down, or before starting any multi-step task.
argument-hint: [request to divide]
---

# Divide a request into tasks

Divide the following request into tasks. If no request is given below, divide
the user's most recent request instead.

$ARGUMENTS

## How to divide it

1. **List the tasks.** Number them. Each task gets an imperative subject - the
   verb first - and a done-condition somebody else could check without asking
   you what you meant. "Improve error handling" is not a task. "Return 422 with
   the field name on invalid input, covered by a test" is.
2. **Order them by dependency**, not by how interesting they are. If task 3
   needs task 1's output, say so.
3. **Register them.** More than one task means one `TaskCreate` call per task,
   then `TaskUpdate` to `in_progress` before starting each and `completed` only
   once its done-condition actually holds. Where those tools are unavailable,
   keep the numbered list in the reply and track progress there.
4. **Say what you are not doing.** Scope you are dropping stays on the list,
   marked dropped, with the reason. Silent narrowing is the failure this whole
   mechanism exists to prevent.
5. **Name the uncertainty.** A task you cannot yet size becomes a task to find
   out, with its own done-condition.

If the request genuinely is one atomic task, say so explicitly and give the
one-item list. That is a valid division. Skipping the division is not.

The list goes in your reply to the user, not in internal reasoning.
