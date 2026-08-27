# WebSearch captures — Boris Cherny, 2026-08-27

Verbatim tool output from the `WebSearch` tool. These are the SEARCH TOOL'S OWN
SUMMARIES of pages that could not be fetched from this container (see
EGRESS-BLOCKED-2026-08-27). They are recorded here as what the tool returned,
not as what the underlying pages say. Treat as second-hand.

---

## Query 1: "Boris Cherny Claude Code creator"

Returned links included: ycombinator.com/library/NJ-inside-claude-code-with-its-creator-boris-cherny,
newsletter.pragmaticengineer.com/p/building-claude-code-with-boris-cherny,
getpushtoprod.substack.com/p/how-the-creator-of-claude-code-actually,
linkedin.com/in/bcherny/, x.com/bcherny/status/2007179832300581177,
fortune.com/2026/06/08/..., howborisusesclaudecode.com/

Tool summary, verbatim:

> Boris Cherny is the creator and Head of Claude Code at Anthropic. He
> previously spent five years at Meta as a Principal Engineer and is the author
> of the book Programming TypeScript.
>
> Boris runs 5 instances of Claude Code simultaneously in his terminal using 5
> separate git checkouts of the same repo, numbering his tabs 1-5 for easy
> reference and using system notifications to know when any Claude needs input.
> Boris also runs 5 to 10 sessions on claude.ai/code in parallel with his local
> instances.

---

## Query 2: "Boris Cherny how he uses Claude Code CLAUDE.md plan mode parallel instances git worktrees tips"

Tool summary, verbatim (excerpts):

> Boris ships 20-30 PRs a day by running 5 parallel Claude instances. He works
> across five terminal tabs (each a separate checkout), starting Claude in plan
> mode, iterating on the plan, then letting it one-shot the implementation.
>
> Most of Boris's sessions start in Plan mode (Shift+Tab twice). ... He puts it:
> "once there is a good plan, it will one-shot the implementation almost every
> time."
>
> The Claude Code team shares a single CLAUDE.md for their entire repo. They
> check it into Git and the whole team contributes multiple times a week.
> Anytime Claude does something incorrectly, they add it to the CLAUDE.md so it
> knows not to do it next time.
>
> Boris uses Opus with thinking for everything. Even though it's bigger and
> slower than Sonnet, he says you have to steer it less and it's better at tool
> use, so it's almost always faster in the end.

NOTE — internal disagreement between Query 1 and Query 2 on a factual detail:
Query 1's summary says "5 separate git checkouts"; Query 2's says "each in its
own git worktree". This was later resolved by a primary-derived source; see
CHERNY-TIPS-REPO-2026-08-27, file claude-boris-10-tips-01-feb-26.md tip 1/,
which states Boris personally uses multiple git checkouts while most of the
Claude Code team prefers worktrees.

---

## Query 3: "Boris Cherny Claude Code tips prompting be specific context /clear escape interrupt course correct"

Tool summary, verbatim (excerpts):

> Plan mode is essentially a way to build really good prompts—you're doing the
> orchestration to bring all the context Claude needs into a single session so
> it can execute correctly.
>
> The most important thing to get great results out of Claude Code is to give
> Claude a way to verify its work—if Claude has that feedback loop, it will
> 2–3x the quality of the final result.

---

## Query 4: "Boris Cherny Claude Code does he use subagents hooks MCP custom slash commands vanilla setup"

Tool summary, verbatim (excerpts):

> Boris uses specialized subagents for common tasks like code-simplifier for
> cleaning up code after Claude finishes and verify-app for testing Claude Code
> end-to-end.
>
> Boris uses a PostToolUse hook to format Claude's code, where the hook handles
> the last 10% to avoid formatting errors in CI.
>
> Boris uses /commit-push-pr dozens of times daily.

A search-result title also recorded, not verified:
"Head Of Anthropic's Claude Code Says Prompt Engineering Not That Important"
(searchenginejournal.com). The underlying article was NOT fetched; the claim
is a headline only and is NOT treated as established. See unknowns U-9.
