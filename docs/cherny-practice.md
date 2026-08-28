---
provenance: enforced
---

# The Cherny corpus

> What follows is a working practice set for Claude Code, assembled from
> material by and about Boris Cherny, cross-checked against Anthropic's own
> documentation. It exists because a practice you cannot cite is a preference.
> Every claim below carries a source; the ones that could not be sourced are in
> `provenance/unknowns.md` instead, and are not here.

## Observed — whose material this is, and how much of it was reachable

Boris Cherny (`@bcherny`) describes himself, on his own About page, as "a Software Engineer at Anthropic, where I created Claude Code", previously at Instagram, and the author of O'Reilly's *Programming TypeScript*. [src:CHERNY-BLOG-REPO-2026-08-27]

> A search summary instead described him as "creator and Head of Claude Code"
> and as having spent "five years at Meta as a Principal Engineer". Neither the
> title nor the tenure is confirmed by his own page, which says Instagram and
> gives no duration. The primary wording is used above; the discrepancy is
> noted rather than averaged. [src:CHERNY-IDENTITY-2026-08-27]

The owner's request named "borris churney". No record in this repository has the owner confirming that this means Boris Cherny; the identification is an inference from phonetic similarity and subject matter, and is registered as an open question in `provenance/unknowns.md` under U-7. [src:CHERNY-IDENTITY-2026-08-27]

The bulk of the corpus comes from a third-party GitHub compilation that transcribes Cherny's X threads into Markdown: seven dated collections totalling **60 tips**, spanning 2026-01-03 to 2026-04-16. [src:CHERNY-TIPS-REPO-2026-08-27]

That compilation is **not a primary source**. Cherny's own posts on `x.com`, every long-form interview about him, and Anthropic's own `anthropic.com` engineering blog were all unreachable from this container: the egress proxy refused them. [src:EGRESS-BLOCKED-2026-08-27]

All 60 tips have now been checked against the screenshots of the original posts bundled in the compilation. Roughly 35 transcribe faithfully; the rest fail, and they fail in **both** directions. [src:SCREENSHOT-AUDIT-2026-08-27]

It drops material that changes meaning — most seriously the sandbox exception in tip 12 of the January thread, and the line "Other teams maintain their own CLAUDE.md's". [src:SCREENSHOT-AUDIT-2026-08-27]

It also **invents**: four separate bullets in the 2026-03-30 collection appear in no post, written in Cherny's voice, and the entire squash-merge rationale in the 2026-03-25 file is the compiler's own. [src:SCREENSHOT-AUDIT-2026-08-27]

It reassigns attribution, turning "our version of @danshipper's Compounding Engineering" into "Boris's version", and "We call this test time compute" into "Boris calls this". [src:SCREENSHOT-AUDIT-2026-08-27]

And it mis-transcribes: the shell aliases `za, zb, zc` became `2a, 2b, 2c`, and the handle `@amorriscode` became `@amorisscode`. [src:SCREENSHOT-AUDIT-2026-08-27]

What held up perfectly was the numbers: every PR statistic and every test-time-compute quotation checked out exactly. [src:SCREENSHOT-AUDIT-2026-08-27]

> An earlier version of this document, working from a single checked tip,
> concluded that "the compilation understates rather than embellishes". The
> full audit falsified that. A sample of one told us the direction of the error
> and was wrong about it, which is a fair warning about what a single
> spot-check buys you.

For the January thread specifically there is a better secondary source than the compilation: an independent transcription carrying all 23 posts with per-post timestamps, which preserves what the compilation drops. [src:CHERNY-THREAD-MIRROR-2026-01-02]

One **primary** source was reachable and was read in full: an unpublished draft, `_drafts/Tips-for-Using-Claude-Code.md`, in Cherny's own blog repository `bcherny/bcherny.github.io`, front matter dated 2025-04-13, which opens "I created Claude Code as a research project". [src:CHERNY-OWN-DRAFT-2025-04-13]

That draft is genuinely unfinished, and its gaps are load-bearing: its section lettering runs out of order, and nine subsections — including all five under "Multi-Claude" — are headings with no body at all, while a tenth carries only the fragment `.mcp.json`. [src:CHERNY-OWN-DRAFT-2025-04-13]

It is also the *only* Claude Code writing in his own repository. His blog holds 17 published posts, the newest from 2024-07-19, and a search of all of them for "claude" matches nothing — so this material is one unpublished draft, not an excerpt from a larger body of published work. [src:CHERNY-BLOG-REPO-2026-08-27]

> Those empty headings are the sharpest illustration in this whole exercise of
> the rule against expanding a label into content. "Use git worktrees" is a
> heading Cherny wrote and never filled in. What he would have said under it is
> not knowable from the heading, and is not guessed at here.

What was also reachable directly, and therefore carries more weight than the compilation, is Anthropic's live documentation at `code.claude.com`. [src:DOCS-BESTPRACTICES-2026-08-27]

> Where a practice below is corroborated by that documentation, both sources
> are cited, and the documentation is the stronger of the two.

## Observed — the spine: give Claude a way to verify its work

This is the single load-bearing claim of the entire corpus, and the one that is best sourced. Cherny states it three separate times across three months, twice calling it the most important thing. [src:CHERNY-TIPS-REPO-2026-08-27]

In his own words, from the screenshot of the original post: "probably the most important thing to get great results out of Claude Code -- give Claude a way to verify its work. If Claude has that feedback loop, it will 2-3x the quality of the final result." [src:CHERNY-TWEET13-SCREENSHOT-2026-08-27]

The same post continues that verification is domain-specific: "It might be as simple as running a bash command, or running a test suite, or testing the app in a browser or phone simulator. Make sure to invest in making this rock-solid." [src:CHERNY-TWEET13-SCREENSHOT-2026-08-27]

Anthropic's documentation leads its best-practices page with the same principle and explains the failure it prevents: "Claude stops when the work looks done. Without a check it can run, 'looks done' is the only signal available, and you become the verification loop: every mistake waits for you to notice it." [src:DOCS-BESTPRACTICES-2026-08-27]

The documentation names four escalating ways to gate on a check, in increasing order of determinism: in one prompt; across a session via a `/goal` condition re-evaluated after every turn; as a Stop hook that "blocks the turn from ending until it passes"; and by a second opinion from a verification subagent, "so the agent doing the work isn't the one grading it". [src:DOCS-BESTPRACTICES-2026-08-27]

It also states the reporting rule that follows from this: "Have Claude show evidence rather than asserting success". [src:DOCS-BESTPRACTICES-2026-08-27]

By April, Cherny's own prompts had collapsed this into a single reusable step — described as `Claude do blah blah /go`, where `/go` is a skill that tests end-to-end, simplifies, and opens a PR. [src:CHERNY-TIPS-REPO-2026-08-27]

**This repository already implements the deterministic-gate form of this practice**, and did so before the corpus was collected: `tools/verify_provenance.py` is the check, and `.claude/settings.json` runs it on every `Write|Edit` and runs the full suite on `Stop`. [src:REPO-STATE-VERIFY-HOOKS-2026-08-27]

## Observed — parallelism is the productivity claim

Cherny's headline practice is running many sessions at once: five Claude sessions in the terminal, tabs numbered 1–5, with system notifications signalling which one needs input. [src:CHERNY-TIPS-REPO-2026-08-27]

On top of the local five, he runs a further 5–10 sessions on `claude.ai/code`, handing local sessions off to web "using `&`", kicking others off manually in Chrome, and using `--teleport` to move back and forth. [src:CHERNY-THREAD-MIRROR-2026-01-02]

He also starts sessions from the Claude iOS app "every morning and throughout the day, and check[s] in on them later" — a detail the compilation omits entirely. [src:CHERNY-THREAD-MIRROR-2026-01-02] [src:SCREENSHOT-AUDIT-2026-08-27]

By March this had grown: he describes having "dozens of Claudes running at all times", with git worktrees as the mechanism. [src:CHERNY-TIPS-REPO-2026-08-27]

Two search summaries disagreed about whether he uses separate checkouts or git worktrees. The compilation resolves it directly: Boris personally uses multiple git checkouts, while most of the Claude Code team prefers worktrees — and the team calls parallelism "the single biggest productivity unlock". [src:CHERNY-TIPS-REPO-2026-08-27] [src:CHERNY-SEARCH-SETUP-2026-08-27]

> The disagreement is recorded rather than smoothed over, because the way it
> resolved — a primary-derived source distinguishing his habit from his team's —
> is exactly the distinction a summary would have flattened.

A subagent tasked with reading the workflow documentation reported the mechanics the tips assume: `claude --worktree <name>` creates an isolated checkout, and a subagent frontmatter field `isolation: worktree` gives an agent its own. Only the existence of the `isolation` field is corroborated first-hand. [src:DOCS-WORKFLOWS-SUBAGENT-2026-08-27]

For fan-out beyond hand-managed sessions, `/batch <instruction>` splits a change across subagents, each working in its own worktree and opening a pull request. [src:DOCS-BESTPRACTICES-2026-08-27]

The two sources give different bounds for that fan-out: the documentation says "5 to 30 subagents", while Cherny's 2026-03-30 tip says "as many worktree agents as it takes (dozens, hundreds, even thousands)". [src:BATCH-FANOUT-DISCREPANCY-2026-08-27]

The documented rationale for parallel *review* is not throughput but independence: "A fresh context improves code review since Claude won't be biased toward code it just wrote." [src:DOCS-BESTPRACTICES-2026-08-27]

Anthropic generalises that into a theory they call test time compute — the post says "We call this", not "I call this": more tokens on a coding problem gives a better result, and **separate context windows** make it better still — which is why "one agent can cause bugs and another (using the same exact model) can find them". [src:CHERNY-TIPS-REPO-2026-08-27]

He draws the analogy explicitly to human teams, and concludes that "multiple uncorrelated context windows" — in his hedged wording, "tends to be a good approach" — will hold until agents "probably" write bug-free code. [src:CHERNY-TIPS-REPO-2026-08-27]

## Observed — plan before code

Most of his sessions start in plan mode, entered with shift+tab twice; for a PR he iterates on the plan until he likes it, then switches to auto-accept edits and Claude "can usually 1-shot it". [src:CHERNY-TIPS-REPO-2026-08-27]

The team's version is stronger: start *every* complex task in plan mode, and "pour your energy into the plan so Claude can 1-shot the implementation". [src:CHERNY-TIPS-REPO-2026-08-27]

Two team habits are worth lifting: have one Claude write the plan and a second review it as a staff engineer; and when something goes sideways, switch back to plan mode and re-plan rather than pushing on. [src:CHERNY-TIPS-REPO-2026-08-27]

The documentation names the workflow "Explore first, then plan, then code", with four phases — Explore, Plan, Implement, Commit. [src:DOCS-BESTPRACTICES-2026-08-27]

It also bounds the practice, which the tips do not: "If you could describe the diff in one sentence, skip the plan." [src:DOCS-BESTPRACTICES-2026-08-27]

A subagent tasked with reading those pages reported that three workflow names widely attributed to Anthropic — "explore-plan-code-commit", "TDD", and "safe YOLO mode" — do **not** appear as named workflows in the current documentation. This is an absence claim taken on report, and absence is the weakest thing to take second-hand. [src:DOCS-WORKFLOWS-SUBAGENT-2026-08-27]

Two of the three are his own names, from his 2025 draft: "Explore, plan, code, commit" and "Safe yolo mode" are its section headings verbatim. "TDD" is not his coinage — the draft's heading is "Write tests, commit; code, iterate, commit", and it invokes TDD as an existing practice: "There has been a lot written about TDD". [src:CHERNY-OWN-DRAFT-2025-04-13]

> So the names are authentic but dated: they are what he called these workflows
> in 2025, not what the current documentation calls them. Anyone citing them as
> current Anthropic guidance is citing a rename that already happened.

## Observed — the 2025 primary draft, and what it says the 2026 tips do not

The draft states the rationale that the whole verification theme grows out of: "When Claude has a target to iterate against -- a visual mock, a test case, or another kind of output -- its outputs tend to significantly improve." [src:CHERNY-OWN-DRAFT-2025-04-13]

Its favourite workflow for verifiable changes is test-first: have Claude write tests from input/output pairs *without running them*, commit those, then have Claude write code until they pass — explicitly instructing it not to edit the tests. [src:CHERNY-OWN-DRAFT-2025-04-13]

The screenshot loop is the same shape: give Claude a way to screenshot, give it a mock, and have it iterate until the two match — "The first version might be pretty good, but after 2-3 iterations it will look even better." [src:CHERNY-OWN-DRAFT-2025-04-13]

On specificity he gives a number: generic instructions land "in the first shot 30% of the time", and more specific instructions can improve that "2-3x". [src:CHERNY-OWN-DRAFT-2025-04-13]

The draft documents an escalation ladder for extended thinking during planning, verbatim: `"think" < "think hard" < "megathink" < "think harder" < "ultrathink"`. [src:CHERNY-OWN-DRAFT-2025-04-13]

His habit for maintaining `CLAUDE.md` is mechanical rather than periodic: press `#` mid-session to have an instruction folded into the right file, "frequently as I code, to document commands, files, and style guidelines as I go", then include those changes in the commit "so that others on my team can benefit". [src:CHERNY-OWN-DRAFT-2025-04-13]

He treats the file as a prompt to be tuned, not a config to be filled: he runs it through a prompt improver and adds emphasis such as "IMPORTANT" or "YOU MUST" to improve adherence. [src:CHERNY-OWN-DRAFT-2025-04-13]

Two scope figures he gives for delegation: he drives git "90%+ of the time" through Claude, and "90%+ of my Github interactions" as well. [src:CHERNY-OWN-DRAFT-2025-04-13]

The draft names three course-correction tools — interrupt with Escape (which "retains everything in context"), double-tap Escape to edit an earlier prompt and re-run, and asking Claude to undo its changes. [src:CHERNY-OWN-DRAFT-2025-04-13]

It recommends `/clear` often, on the grounds that irrelevant accumulated context "can hurt performance, and occasionally distract and side track Claude". [src:CHERNY-OWN-DRAFT-2025-04-13]

For large multi-step tasks — migrations, "fixing all 100 lint errors" — it prescribes a Markdown scratchpad: have Claude write the errors to a checklist file, then work down it one by one, verifying and checking off each before moving on. [src:CHERNY-OWN-DRAFT-2025-04-13]

It also describes the `#` key as the way to have Claude fold an instruction into the relevant `CLAUDE.md` as you work, with those changes then included in commits so the team benefits. [src:CHERNY-OWN-DRAFT-2025-04-13]

And it warns against the mistake it expects readers to make: "A common mistake I see is people dumping content into their CLAUDE.md without taking the time to iterate on that content." [src:CHERNY-OWN-DRAFT-2025-04-13]

## Observed — the permissions question, and a retracted claim

> An earlier version of this document reported a reversal here: that he
> recommended `--dangerously-skip-permissions` in 2025 and prohibited it in
> 2026. **That was wrong, and it is retracted.** It came from trusting the
> compilation, which drops the half of the January post that resolves it.

His position is one conditional practice, held consistently for 21 months. In the same January 2026 thread, minutes apart, tip 10 says "I don't use `--dangerously-skip-permissions`. Instead, I use `/permissions` to pre-allow common bash commands that I know are safe in my environment", and tip 12 says "I will also use either `--permission-mode=dontAsk` or `--dangerously-skip-permissions` in a sandbox to avoid permission prompts for the session, so Claude can cook without being blocked on me." [src:CHERNY-PERMISSIONS-CONDITIONAL-2026-08-27]

The 2025 draft says the same thing — use the flag, but "in a container without internet access", because the risks are "data loss, your system getting borked, or even data exfiltration". [src:CHERNY-OWN-DRAFT-2025-04-13]

So the rule is not "never" and not "always": **not as your default, yes inside a sandbox for long-running work.** The compilation flattened that into a prohibition by omitting one sentence. [src:CHERNY-PERMISSIONS-CONDITIONAL-2026-08-27]

> This is the single most instructive failure in the whole exercise. The
> retracted claim was well-formed, dated, double-sourced and wrong, because
> both its sources were the same lossy compilation wearing two hats. A citation
> that resolves is not the same as a citation that is independent.

## Observed — what he says most recently, and how it changed

The corpus's most recent primary-derived statement is from 2026-05-24, recovered from a mirrored X digest after `x.com` itself proved unreachable. [src:CHERNY-X-2026-05-24]

Asked what his biggest tip is, he answers: "These days my #1 tip is: use auto mode", explaining that "Auto mode means no more permission prompts. It is the key building block for multi-clauding: start a session, then while it runs, work on another session in parallel." [src:CHERNY-X-2026-05-24]

Two days earlier he noted auto mode had reached the Pro plan and gained Sonnet 4.6 support alongside Opus 4.7. [src:CHERNY-X-2026-05-24]

> Note what moved. In January, March and April his headline was verification.
> By May the headline is auto mode — but read the reason: auto mode is offered
> as the enabler of *parallelism*, not as a replacement for verification. The
> two sit in different layers, and this document keeps verification as the
> spine because that is what every source, including the documentation, treats
> as the quality lever.

## Observed — the loops claim, and what deflates it

By mid-2026 his stated method had moved past prompting altogether: "I don't prompt Claude anymore. I have loops running that prompt Claude and figuring out what to do. My job is to write loops." [src:CHERNY-LOOPS-2026-08-28]

This resolves the "prompt engineering is not that important" headline that U-9 was opened for: the claim is that polishing prompts is the wrong lever, not that specificity is worthless. The method he prescribes instead is the one already at the centre of this corpus — give the model a task that is too hard, give it tools to verify the work, see where it struggles, then fix that with better prompting, a skill, or an MCP. [src:CHERNY-LOOPS-2026-08-28]

The name "loop engineering" is **not his**: it is a third-party coinage by Addy Osmani and Peter Steinberger, and so is the tidy "sense-decide-act-check" definition that circulates with it. [src:LOOP-ENGINEERING-KB-2026-08-28]

Several widely-repeated numbers around this material are weaker than their circulation suggests. The "4% of all public GitHub commits" figure is SemiAnalysis's estimate, not Anthropic's measurement; his "200%" and "~70%" per-engineer productivity figures come from different interviews and do not agree; and Anthropic itself reportedly cautioned that the lines-of-code productivity framing was "almost certainly an overstatement". [src:LOOP-ENGINEERING-KB-2026-08-28]

Auto mode, which the May post calls his #1 tip, has published limits: a measured 93% permission-acceptance rate against the rhetorical "99%", a 0.4% false-positive rate, and a **17% false-negative** rate. [src:LOOP-ENGINEERING-KB-2026-08-28]

> That 17% is the number to carry. It is the documented cost of the practice he
> now leads with, and no summary of his advice that this session found mentions
> it. Reporting the #1 tip without it would be promotional rather than useful.

> Grading, stated plainly: this section is second-hand at best. Every
> underlying talk and article sits on a host the proxy refuses, so none of it
> was read at the source. It is here because the deflationary parts are the
> parts a promotional corpus would not invent — and it is deliberately kept out
> of `.claude/skills/cherny/SKILL.md`, which draws only on material read
> directly.

## Observed — CLAUDE.md is a living artifact, not a config file

His team shares a single `CLAUDE.md` **for the Claude Code repo**, checked into git, with the whole team contributing multiple times a week — and other teams at Anthropic maintain their own, each responsible for keeping theirs current. [src:CHERNY-THREAD-MIRROR-2026-01-02] [src:SCREENSHOT-AUDIT-2026-08-27]

> That second half matters and the compilation dropped it. "One shared
> CLAUDE.md" is a rule about one repository, not a company-wide single file.

The maintenance loop is the point: whenever Claude does something wrong, add it to `CLAUDE.md` so it does not repeat. [src:CHERNY-TIPS-REPO-2026-08-27]

The team's sharper phrasing is to end every correction with "Update your CLAUDE.md so you don't make that mistake again", and to keep editing until the mistake rate measurably drops. [src:CHERNY-TIPS-REPO-2026-08-27]

Cherny extends the loop into code review: tag `@claude` on a coworker's PR to fold a lesson into `CLAUDE.md` as part of that PR. He calls it "our version of @danshipper's Compounding Engineering" — the team's application of a concept he credits to Dan Shipper, not his own coinage. [src:CHERNY-PERMISSIONS-CONDITIONAL-2026-08-27] [src:SCREENSHOT-AUDIT-2026-08-27]

The documentation pushes hard the other way, on size: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." [src:DOCS-MEMORY-2026-08-27]

Its pruning test is a single question: "For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it." [src:DOCS-BESTPRACTICES-2026-08-27]

It names the failure mode that results from ignoring this — "The over-specified CLAUDE.md" — and prescribes ruthless pruning. [src:DOCS-BESTPRACTICES-2026-08-27]

There is a real tension here between "add every correction" and "cut every line that isn't load-bearing"; the documentation resolves it by directing standing procedures to skills and file-scoped instructions to `.claude/rules/` with `paths:` frontmatter, leaving `CLAUDE.md` for what must be in every session. [src:DOCS-MEMORY-2026-08-27]

One structural fact constrains all of this: "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself", so it shapes behaviour without enforcing it. [src:DOCS-MEMORY-2026-08-27]

Which is why the documentation is explicit that enforcement is a different mechanism: "To block an action regardless of what Claude decides, use a PreToolUse hook instead." [src:DOCS-MEMORY-2026-08-27]

## Observed — the customization primitives, and what each is for

Cherny's stated position is that his setup is "surprisingly vanilla" and that Claude Code works well out of the box, with no one correct way to use it. [src:CHERNY-TIPS-REPO-2026-08-27]

**Slash commands** are for every inner-loop workflow done many times a day; they live in `.claude/commands/`, are checked into git, and save repeated prompting. [src:CHERNY-TIPS-REPO-2026-08-27]

His worked example, which the compilation dropped: he and Claude use `/commit-push-pr` "dozens of times every day", and the command "uses inline bash to pre-compute git status and a few other pieces of info to make the command run quickly and avoid back-and-forth with the model". [src:CHERNY-THREAD-MIRROR-2026-01-02] [src:SCREENSHOT-AUDIT-2026-08-27]

> That second sentence is the transferable part, and it is the part that went
> missing: a command is faster when it hands the model the state up front
> instead of making it go and look.

**Subagents** live in `.claude/agents/` and automate common workflows; his named examples are `code-simplifier`, which cleans up after Claude finishes, and `verify-app`, which holds detailed end-to-end testing instructions. [src:CHERNY-TIPS-REPO-2026-08-27]

The team adds two uses: append "use subagents" to throw more compute at a problem, and offload tasks to subagents to keep the main context window clean. [src:CHERNY-TIPS-REPO-2026-08-27]

The documentation gives the reason this works — a subagent runs in its own context window and "doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read". [src:DOCS-SUBAGENTS-2026-08-27]

Its stated best practices for subagents are, verbatim: "Design focused subagents: each subagent should excel at one specific task"; "Write detailed descriptions: Claude uses the description to decide when to delegate"; "Limit tool access: grant only necessary permissions for security and focus"; "Check into version control: share project subagents with your team". [src:DOCS-SUBAGENTS-2026-08-27]

**Skills** are the team's answer to repetition: if you do something more than once a day, turn it into a skill or a command, and commit it. [src:CHERNY-TIPS-REPO-2026-08-27]

**Hooks** are for what must happen deterministically. Cherny's standing example is a `PostToolUse` hook that formats Claude's code, "to handle the last 10%" and avoid CI formatting failures. [src:CHERNY-TIPS-REPO-2026-08-27]

His other named hook uses are loading context at `SessionStart`, logging every bash command at `PreToolUse`, routing permission prompts to WhatsApp at `PermissionRequest`, and poking Claude to continue at `Stop`. [src:CHERNY-TIPS-REPO-2026-08-27]

**Permissions**: he is explicit that you should *not* use `--dangerously-skip-permissions`, and should instead pre-allow known-safe commands via `/permissions`, checked into the team's `.claude/settings.json`. [src:CHERNY-TIPS-REPO-2026-08-27]

By April, auto mode had arrived, and he frames it as the safer alternative to skipping permissions and as what makes running more parallel sessions practical. [src:CHERNY-TIPS-REPO-2026-08-27]

The documentation, rather than the compilation, is the source for what the classifier does: it "reviews most actions instead of you and blocks only what looks risky". The compilation's gloss that it will "pause and ask" on risky commands appears in no post. [src:DOCS-BESTPRACTICES-2026-08-27] [src:SCREENSHOT-AUDIT-2026-08-27]

The through-line across all five primitives is that configuration is checked into git and shared with the team, not kept personal. [src:CHERNY-TIPS-REPO-2026-08-27]

## Observed — model, effort, and how he actually drives the tool

He named Opus 4.5 with thinking as his model for everything on 2026-01-03, and the reasoning is throughput rather than quality alone: you have to steer it less and it is better at tool use, so it is "almost always faster than using a smaller model in the end". [src:CHERNY-TIPS-REPO-2026-08-27]

On effort, as of 2026-02-12 when the slider had three levels, his stated preference was "High for everything" — then the top setting. By 2026-04-16 the same compilation records five levels (`low`, `medium`, `high`, `xhigh`, `max`), so "high" had become the middle one. [src:CHERNY-TIPS-REPO-2026-08-27]

He does most of his coding by speaking rather than typing; the team's rationale is that you speak ~3x faster than you type and your prompts get more detailed as a result. [src:CHERNY-TIPS-REPO-2026-08-27]

He writes a substantial amount of code from the mobile app, and has remote control enabled for all sessions so a session can be moved between phone, web, desktop and terminal. [src:CHERNY-TIPS-REPO-2026-08-27]

He runs standing automation loops rather than one-shot sessions — among them `/loop 5m /babysit` to shepherd PRs to production, `/loop 30m /slack-feedback`, and `/loop 1h /pr-pruner` to close stale PRs. [src:CHERNY-TIPS-REPO-2026-08-27]

His advice on that pattern is to turn workflows into skills and then into loops. [src:CHERNY-TIPS-REPO-2026-08-27]

By April he had turned down the display of intermediate work entirely, using focus mode to look only at the final result, on the stated grounds that he generally trusts the model to run the right commands. [src:CHERNY-TIPS-REPO-2026-08-27]

> That last one is the corpus's most conditional claim: it presupposes the
> verification loop of the first section actually exists. Trusting the result
> without the check is not the practice being described.

## Observed — shipping discipline

The volume claim is specific and self-reported via a contribution graph: 266 contributions on 2026-03-24, from 141 PRs. [src:CHERNY-TIPS-REPO-2026-08-27]

Those PRs are always squash-merged, and their size distribution was a median of 118 lines, p90 of 498, and p99 of 2,978, across 45,032 lines changed. [src:CHERNY-TIPS-REPO-2026-08-27]

What he actually said about those PRs was four words — "141 PRs, always squashed" — offered in reply to someone asking how big his PRs were, not volunteered as advice. Everything the compilation adds about clean history, `git bisect` and keeping PRs small is the compiler's commentary, not his. [src:SCREENSHOT-AUDIT-2026-08-27]

> Reading small-PR discipline out of that distribution is a reasonable
> inference, and it is *our* inference. It is left here as an inference rather
> than promoted into something he recommended.

He also reports that Anthropic built its Code Review feature because code output per engineer was "up 200% this year" as of 2026-03-10, i.e. across roughly ten weeks and review became the bottleneck. [src:CHERNY-TIPS-REPO-2026-08-27]

> Note the direction of causation being claimed: the constraint moved from
> writing code to checking it. Every practice in this corpus that looks like
> overhead — planning, verification, adversarial review — is a response to that
> move.

## Observed — where the corpus contradicts itself or is unresolved

A search result carried the headline "Head Of Anthropic's Claude Code Says Prompt Engineering Not That Important", which sits in tension with the corpus's emphasis on detailed specs and plan quality. The article was unreachable and the claim is **not** established; it is recorded in U-9. [src:CHERNY-SEARCH-SETUP-2026-08-27]

The documentation warns about the adversarial-review practice this corpus recommends: "A reviewer prompted to find gaps will usually report some, even when the work is sound, because that is what it was asked to do." [src:DOCS-BESTPRACTICES-2026-08-27]

Several tips describe features, settings and model versions as of early 2026; feature names and defaults move, and nothing here was re-checked against the current release except where a documentation source is cited alongside. [src:CHERNY-TIPS-REPO-2026-08-27]

---

## The surprises

> Orient, per `.claude/skills/ooda/SKILL.md`: where reality diverged from what
> was assumed walking in. A loop with no surprise usually means Observe was
> skipped, so these are recorded rather than tidied away.
>
> **The material was reachable by a route nobody would search first.** The
> assumption after the egress probe was that this task was mostly blocked:
> `x.com`, every interview, every tip site, and `anthropic.com` itself all
> refused. The primary source turned out to sit in a plain file in Cherny's own
> GitHub Pages repository, reachable because `raw.githubusercontent.com` is
> allowed. The lesson generalises: "the site is blocked" is not "the content is
> unreachable" until the source repository has been checked too.
>
> **The compilation understated rather than embellished.** The expectation
> going into the fidelity check was the usual failure of third-party
> transcription — embroidery, invented emphasis. The screenshot showed the
> opposite: two of three paragraphs dropped, nothing added. That inverts which
> way the corpus is likely to be wrong, and it is why the corpus quotes the
> screenshot over the transcription wherever both exist.
>
> **The corpus's centre of gravity was already installed here.** The
> expectation was that a practice set from a different author would need
> reconciling against this repository's doctrine. Instead its most-repeated
> rule — give the work a runnable check and show the output — was already
> implemented as `tools/verify_provenance.py` plus the `PostToolUse` and `Stop`
> hooks. The convergence is the reason the installation is small: almost
> nothing had to be argued for.
>
> **The famous workflow names are dated, not current.** "Explore, plan, code,
> commit" and "safe yolo mode" read as canonical Anthropic terminology. They
> are Cherny's own names from an unpublished 2025 draft, and the current
> documentation uses neither. Anything citing them as present-day guidance is
> citing a rename that already happened.
>
> **The reversal I thought I had found was not real.** The 2025 draft and the
> 2026 thread say the same conditional thing; the compilation had dropped the
> sentence that reconciles them, and I wrote up the artifact as a finding. It
> took reading 65 screenshots to catch. The lesson is not "check your sources"
> — it is that two citations drawn from one secondary source are one citation,
> however different their ids look.
>
> **The compilation invents, and I had concluded it only omits.** One
> spot-check said "understates rather than embellishes"; sixty said it also
> writes new bullets in Cherny's voice. A single sample can tell you an error
> exists and still mislead you about its direction.

## How this repository applies it

> This section states decisions, not facts, so it is outside the enforced
> sections above. It is the "Decide" half of the loop that produced this file.

The corpus and this repository's existing doctrine converge on one thing from
opposite directions, and that convergence is what made installing it worthwhile
rather than decorative:

| Cherny corpus | This repository's doctrine |
|---|---|
| Give Claude a way to verify its work | A claim is either sourced or it is not written down |
| Multiple uncorrelated context windows find what one cannot | An agent auditing a document it did not write has no stake in it |
| Add every correction back into `CLAUDE.md` | Capture every finding in the ledger as you go |
| Have Claude show evidence, not assert success | Report what you did, not what you set out to do |

The installation therefore adds no new philosophy. It adds the operational half
that the doctrine was missing: the doctrine said *be honest*, and the corpus
says *build the loop that makes honesty checkable*.

What was installed, and where:

- `.claude/skills/cherny/SKILL.md` — the practice set, loadable on demand in any session.
- `prompts/cherny-operator.md` — the same practices as a system prompt, for sessions started outside this repository.
- `.claude/commands/verify-loop.md` — turns the spine practice into one invocable step.
- `.claude/agents/verifier.md` — the second-opinion agent, deliberately given no ability to edit what it judges.

What was deliberately *not* installed:

- Anything requiring a tool this environment does not have. Worktree fan-out,
  the Chrome extension, voice input and the mobile app are all real practices
  from the corpus that a headless container cannot exercise; they are recorded
  above and left unimplemented rather than faked.
- Any change to `src/oodarag/`. The RAG pipeline on this branch advertises CLI
  targets that do not exist; that is recorded as an observation, not repaired
  under cover of an unrelated task.
