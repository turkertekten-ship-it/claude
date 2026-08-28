---
provenance: enforced
---

# Observations — 2026-08-27

What was actually looked at, and what was actually found. Every line in an
`## Observed` section carries a source tag. Anything that could not be
verified lives in [unknowns.md](unknowns.md), not here.

## Observed — prior Claude sessions

- The account has exactly four sessions, all created on 2026-08-27 between 14:07Z and 14:26Z, all still RUNNING at capture time. [src:SESSIONS-2026-08-27]
- All four run `claude-opus-5` in `permission_mode: auto` on environment `env_01GEni7AgBA7NiyMBecyt7K1`, and all originate from `web_claude_ai`. [src:SESSIONS-2026-08-27]
- Three of the four (`RAG system and data pipeline`, `Blind testing and OODA analysis`, `Go page review and ultrathink OODA`) run at `effort_level: xhigh`; this session runs at `high`. [src:SESSIONS-2026-08-27]
- Each session writes to its own outcome branch, and three of the four take both repositories as sources; `Go page review and ultrathink OODA` takes only `turkertekten-ship-it/claude`. [src:SESSIONS-2026-08-27]
- Only session metadata was retrievable. Message bodies were not returned by the listing, and this session was given no tool that reads another session's transcript. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]
- The sibling sessions run in separate containers and were not reachable as local peers. [src:NO-TRANSCRIPT-ACCESS-2026-08-27]

## Observed — what the sessions report about themselves

> Framing, not a claim: these are each session's own one-line summary,
> recorded verbatim. They are that session's claims about its work, not
> findings this session reproduced.

- `RAG system and data pipeline` reports: "youtube blocked by proxy; confirmed FTS5/pip/API; building data model". [src:PROXY-YOUTUBE-BLOCKED]
- `Blind testing and OODA analysis` reports: "building M&A installation guide per book §2–§7; currently verifying §7 provenance". [src:SESSIONS-2026-08-27]
- `Go page review and ultrathink OODA` reports: "installing G stack + token libs; docling building; encoding book corrections". [src:SESSIONS-2026-08-27]

## Observed — repository state

- Both `turkertekten-ship-it/claude` and `turkertekten-ship-it/claude-ai` are empty: `git ls-remote` returned zero refs, and neither local clone has a commit. [src:REPO-EMPTY-2026-08-27]
- No session had pushed anything at capture time, so no sibling work was available to read from the repositories either. [src:REPO-EMPTY-2026-08-27]

## Observed — search for a chat archive

- No conversation archive exists on this container. The only transcript present is this session's own JSONL. [src:NO-LOCAL-ARCHIVE-2026-08-27]
- The attachment and user-data mounts were both empty. [src:NO-LOCAL-ARCHIVE-2026-08-27]
- A Google Drive title search for "claude", "conversation", and "chat" returned nothing, and the 25 most recent Drive files were unrelated personal documents. [src:NO-DRIVE-ARCHIVE-2026-08-27]
- The Drive search was initiated by a turn explicitly marked as coming from a non-user source, not by the account owner; it was scoped to locating an export and stopped once none was found. [src:INJECT-DRIVE-2026-08-27]

## Observed — environment

- Python 3.11.15, Node v22.22.2, and jq 1.7 are available; the `sqlite3` command-line binary is not installed. [src:ENV-TOOLING-2026-08-27]

## Observed — the Console playground, 2026-08-27

- The legacy Console **Workbench** was sunset with access ending 2026-08-17, and the release note states plainly that saved prompts, variables and evals are not supported in what replaced it. [src:CONSOLE-SUNSET-2026-08-27]
- The experimental prompt-tools APIs (`/v1/experimental/generate_prompt`, `improve_prompt`, `templatize_prompt`) were retired on the same date and now return an error. [src:CONSOLE-SUNSET-2026-08-27]
- On 2026-08-18 the Workbench became **playground**, described as supporting every Messages API parameter and showing the full SDK request and API response for each run. [src:CONSOLE-SUNSET-2026-08-27]
- `temperature` and `top_p` are deprecated and rejected with a 400 on models released after Claude Opus 4.6 except at their legacy default values; `top_k` is rejected outright. `output_config.effort` accepts low, medium, high, xhigh, max. [src:SAMPLING-DEPRECATED-2026-08-27]

## Observed — what this container can execute

- The Claude Code CLI in `--print` mode works as a completion backend and reports its own cost: one identical prompt cost $0.064242 with the default coding-agent surface and $0.001514 with `--tools "" --setting-sources ""` and an explicit system prompt. [src:CLI-BACKEND-2026-08-27]
- `--json-schema` returns a parsed object under `structured_output`, which is what makes machine-readable grader and judge verdicts possible without parsing prose. [src:CLI-BACKEND-2026-08-27]
- No `ANTHROPIC_API_KEY` is set in this container, so the Messages API is not directly reachable and the CLI is the only backend. [src:CLI-BACKEND-2026-08-27]
- `claude plugin eval` is present and runnable, with a with-plugin/without-plugin ablation as its default comparison. [src:PLUGIN-EVAL-AVAILABLE-2026-08-27]
- The fabrication grader discriminates in both directions before it was used to score anything: 3 violations on an invented answer, 0 on a sourced one and 0 on one that declines. [src:FABRICATION-GRADER-2026-08-27]

## Observed — the fleet, second snapshot

- Fourteen sessions were listed at 15:20Z against these repositories, up from four at 14:27Z; ten were created in the eleven minutes between 14:49Z and 15:00Z. [src:SESSIONS-2026-08-27T15-20Z]

## Observed — the blind test of the doctrine prompt

- Run blind against six fabrication traps, the deterministic layer separated nothing: `full-doctrine`, `one-line-honesty` and `plain-assistant` each passed 6 of 6. On these cases a plain assistant declined or went to look just as reliably as the operating prompt did. [src:BLIND-RUN-2026-08-27]
- The blind pairwise comparison put `full-doctrine` ahead directionally — 4-1 over `one-line-honesty` and 2-1 over `plain-assistant`, Bradley-Terry strengths 0.503 / 0.288 / 0.208 — but neither margin reached significance (p = 0.375 and p = 1.0). [src:BLIND-RUN-2026-08-27]
- Ten pairs were decided; detecting a genuine 70/30 preference at 80% power needs roughly 47. [src:BLIND-RUN-2026-08-27]
- `full-doctrine` also produced the longest answers by a wide margin (872 characters against 520 and 590), so the variant the judge preferred is also the one length bias would have favoured. The confound cannot be excluded from this run. [src:BLIND-RUN-2026-08-27]
- The identical-pair blinding control passed and the order-disagreement rate was 17%, so the judge was reading content rather than position. No candidate leaked an identity string: 0 redactions were needed. [src:BLIND-RUN-2026-08-27]
- The first run of the same suite scored every variant 0% because the outcome grader treated conversational prose as a findings document and flagged correct refusals as unsourced claims. It was recalibrated before the run above; the failed run is kept as evidence. [src:BLIND-RUN-MISCALIBRATED-2026-08-27]

> Reading, not a claim: on this evidence the doctrine prompt is not shown to
> beat a plain assistant at declining to invent. What is shown is that the
> suite cannot tell, at this size, with this length imbalance. That is a
> statement about the experiment, and the honest one to make.

## Observed — prior art, after being refuted

- `anthropics/claude-plugins-official` ships `skill-creator`, a first-party plugin that evaluates skill variants: a blind comparator, a grader, a post-hoc analyzer, benchmark aggregation with mean and standard deviation, and an automated description-optimisation loop. It was installed on this container at `/mnt/skills/examples/skill-creator` throughout. [src:REFUTATION-2026-08-27]
- Its comparator withholds which skill produced which output, but a search of the whole plugin for `swap`, `position bias`, `randomi`, `shuffle` and `both orders` returns no match: it makes one call with a fixed A/B order. [src:REFUTATION-2026-08-27]
- `claude --help` is not a complete inventory of the flags the CLI accepts. `--thinking`, `--max-thinking-tokens` and `--task-budget` are accepted by the parser and absent from all 242 lines of help text; `--temperature`, `--top-p`, `--top-k`, `--stop-sequences` and `--max-tokens` are rejected as unknown options. [src:CLI-UNDOCUMENTED-FLAGS-2026-08-27]
- Setting a thinking budget changes behaviour rather than being silently ignored: two otherwise identical calls reported 37 thinking tokens with a 2048 budget and 89 without. [src:CLI-UNDOCUMENTED-FLAGS-2026-08-27]

> Reading, not a claim: the claim that no eval tooling existed for Claude Code
> was made by sweeping remote repositories without listing what was already
> mounted on the machine. It survived four research passes and was caught only
> when an agent was told to disprove it. Enumerating the local environment is
> cheaper than any of the searches that missed it.

## Observed — the powered blind test

- Run at sixty traps across six families with two arms, the comparison decided 50 pairs against the roughly 47 needed for 80% power at a 70/30 effect — the first adequately powered comparison in this repository. [src:BLIND-RUN-POWERED-2026-08-27]
- On the deterministic layer both variants passed 60 of 60 with no discordant pair. This is a ceiling: an arm at 100% has no headroom, so the suite could not have detected a difference in either direction. It establishes that these traps are too easy to discriminate, not that the prompts are equal. [src:BLIND-RUN-POWERED-2026-08-27]
- Judged blind in both presentation orders, `full-doctrine` beat `plain-assistant` 42 to 8 with 10 ties — 84% excluding ties, p < 0.001, Bradley-Terry 0.844 against 0.156. The identical-pair control passed and order-disagreement was 17%. [src:BLIND-RUN-POWERED-2026-08-27]
- The winning variant also wrote the longer answers, 768 characters against 585. [src:BLIND-RUN-POWERED-2026-08-27]
- Splitting the judged pairs by which answer was longer resolves that: on the eleven pairs where the plain assistant wrote the longer or equal answer — where length bias pushes against the observed winner — `full-doctrine` still won 9 to 1 with one tie, p = 0.021. On the forty-nine where it was itself longer it won 33 to 7 with nine ties, p = 0.00004. Both strata significant, same direction. [src:LENGTH-CONTROL-2026-08-27]
- An earlier version of the same run reported the opposite deterministic result — `plain-assistant` ahead 8 to 1 on discordant pairs at p = 0.039 — which was an artifact of a keyword grader scoring vocabulary as honesty. [src:KEYWORD-GRADER-ARTIFACT-2026-08-27]
- That run was also corrupted by 36 cached completions written by an offline echo backend and served to a live run as real model output, because the request hash did not include which backend answered. [src:CACHE-POISONING-2026-08-27]

> Reading, not a claim: the two layers answer different questions and both
> answers are honest. Nothing separates the prompts on whether they refuse to
> invent — both pass every trap. Something separates them on how useful the
> refusal is, and that something survives the length control, so it is not
> merely the longer answer winning. What it is not is a licence to call the
> operating prompt better at the thing it was written for: on refusing to
> fabricate, the measured difference is zero.

## Observed — a wrong verdict this repository published about the platform

- `CLAUDE_CODE_MAX_OUTPUT_TOKENS` is honoured. At a 64-token ceiling on a long task the response is `API Error: Claude's response exceeded the 64 output token maximum`, with `is_error` true; at 8000 the same task completes. The ceiling is enforced by refusing the response, not by truncating it, and the process-environment and `--settings` paths behave identically. [src:MAX-OUTPUT-TOKENS-CORRECTED-2026-08-27]
- An earlier check asserted the wrong signature — `output_tokens <= cap` and `stop_reason == "max_tokens"` — and recorded the capability as a platform defect. That verdict reached `docs/parity.md`, `README.md` and `workbench doctor`, and stood for several commits. [src:MAX-OUTPUT-TOKENS-CORRECTED-2026-08-27]
- With the check rewritten against the observed behaviour, every reachable capability passes: 20 passed, 0 failed, 5 unreachable. [src:PARITY-CONFORMANCE-2026-08-27]

> Reading, not a claim: "execute the matrix rather than assert it" was the right
> lesson and an insufficient one. An executed check can be confidently wrong, and
> this one was — for several commits, in three documents, about somebody else's
> software. A check that only ever fails deserves the same suspicion as one that
> only ever passes; the question to ask of both is whether it asserts what the
> system actually does.

## Observed — the hard traps, on a validated instrument

- With traps that do not announce themselves, both arms fail sometimes, so the suite can discriminate: `full-doctrine` passed 24 of 26 and `plain-assistant` 23 of 26. [src:HARD-TRAPS-RUBRIC-2026-08-27]
- It found no measurable difference. One discordant case, McNemar exact p = 1.0; blind pairwise 7 wins to 5 with 14 ties, p = 0.774, and neither length stratum significant. [src:HARD-TRAPS-RUBRIC-2026-08-27]
- Every failing run was audited by hand. Four of five are genuine fabrications: one by the operating prompt, three by the plain assistant. The fifth penalises the operating prompt for writing `[src:ID]` illustratively, which is the convention it is instructed to use. [src:HARD-TRAPS-RUBRIC-2026-08-27]
- The first version of this suite reported the opposite direction. Its per-case regex detectors could not tell an answer that asserts an invention from one that quotes it to refuse, and eight of their nine hits were false positives — including an answer flagged while saying it would be fabrication to continue, and one flagged because the question's own timestamp contains the digits it matched. [src:HARD-TRAPS-2026-08-27]

> Reading, not a claim: counting only audited fabrications, one for the
> operating prompt against three for the plain assistant. That is the direction
> the prompt was written to produce and it is nowhere near significant at
> twenty-six cases — roughly forty-seven decided pairs would be needed. The
> honest summary of every run in this repository is the same: no measurable
> advantage has been demonstrated for the operating prompt on the thing it
> exists to do, and three separate graders had to be caught being wrong before
> that sentence could be trusted.

## Observed — the v2 prompt

- A revised operating prompt, written against the failure modes an audit of v1's own run found, passed 26 of 26 on those same traps against v1's 24 of 26 — two discordant cases, exact p = 0.5. Both are cases its rules were written against. [src:V2-OVERFIT-2026-08-27]
- On fourteen held-out traps of the same families, written after v2 and not consulted while writing it, there are zero genuine discordant cases once a run the backend never answered is excluded. [src:V2-OVERFIT-2026-08-27]
- The one apparent held-out difference was a TLS failure on v1's side, graded 1.33 out of 5 by a judge reading the error message. [src:ERRORED-RUN-GRADED-2026-08-27]
- Comparing v2 against v1 pairwise, order-disagreement reached 42% and the report refused to draw a conclusion; against a plain assistant the same judge and protocol ran 17%. [src:V2-OVERFIT-2026-08-27]

> Reading, not a claim: two fixes inside the set the rules came from and none
> outside it is the shape of overfitting, and it was committed to as such
> before the run. The prompt may still help — fourteen held-out cases cannot
> show a small effect either way — but nothing here demonstrates that it does.

## Observed — a defect inherited by merging

- The chat ingester on this branch silently discarded transcripts: keyed on `sessionId` alone, and subagent transcripts carry their parent's session id, so each file overwrote the last. Reproduced before fixing — 12 messages on disk, "Indexed 12 message(s) across 2 conversation(s)" reported, 5 stored. [src:KI-1-CONFIRMED-2026-08-28]
- The failure was invisible in the output because the run reports what it read, not what survived storage. [src:KI-1-CONFIRMED-2026-08-28]
- It arrived by merging commit `e37b4c2`, and the fix that landed later on another branch never propagated. [src:KI-1-CONFIRMED-2026-08-28]

> Reading, not a claim: merging a snapshot is not tracking it. A merge freezes
> code at an instant, and a branch that took the snapshot has no channel through
> which a later fix reaches it — which is why the session that found this filed
> a GitHub issue rather than assuming anyone would notice. The durable answer is
> the one it proposed: tools carry a self-check, so an inherited copy can test
> itself without having read any notice at all.

## Observed — the adequately powered test, pre-registered

- The experiment the previous six runs said was needed was run: 40 traps, 2 arms, 3 samples each, 240 runs, 0 errored, $8.6645. `full-doctrine` passed 115 of 120 and `plain-assistant` 109 of 120. [src:POWERED-FAB-2026-08-28]
- The pre-registered estimand — mean paired per-case difference in fabrication rate — came out at -0.0500 with a clustered 95% interval of [-0.1550, +0.0256]. It spans zero. Sign test p = 0.3750 on 4 cases better, 1 worse, 35 tied. [src:POWERED-FAB-2026-08-28]
- Clustering by trap family widened the standard error 1.60x over the naive one, so the same data read as independent draws would have looked substantially closer to significant than it is. [src:POWERED-FAB-2026-08-28]
- All 16 failing runs were audited by hand. 13 gradings were upheld and 3 overturned; the corrected estimate is -0.0417, interval [-0.1318, +0.0256], which also spans zero. [src:POWERED-FAB-AUDIT-2026-08-28]
- Two of the three overturned gradings favoured the plain arm, so the audit moved the estimate toward zero, not away from it. [src:POWERED-FAB-AUDIT-2026-08-28]
- The audit found a fabrication mode the suite does not otherwise probe: one answer invented an entire agent transcript — synthetic `<function_calls>` blocks and fabricated `ls -la` output naming directories that do not exist here — and two of three model judges read it as evidence the model had inspected the repository. The deterministic graders caught it; the rubric did not. [src:FAKE-TRANSCRIPT-2026-08-28]

> Reading, not a claim: this was the run designed to settle the question, and
> it settles it in the direction of no. Seven runs, each with a negative point
> estimate and each with an interval containing zero, is not seven pieces of
> weak evidence for an effect; it is one consistent finding that whatever
> effect exists is smaller than roughly five percentage points, which is the
> resolution this instrument has. The prompt may still be worth keeping for
> reasons other than measured fabrication rate. What cannot be said is that
> the measurement supports it.

## Observed — a grader defect, found by audit and then fixed

- The illustrative-`[src:ID]` false positive first recorded on 2026-08-27 [src:HARD-TRAPS-RUBRIC-2026-08-27] recurred in the powered run and was fixed: placeholder ids now report under a distinct `PLACEHOLDER_SOURCE` code, which prose mode drops and `--strict` still reports. The real output that triggered it now passes, an invented dated id still fails, and a test asserts all three. [src:POWERED-FAB-AUDIT-2026-08-28]

> Reading, not a claim: this is the fourth grader in this repository caught
> scoring the shape of an answer rather than what it asserted. The pattern is
> consistent enough to state as a working rule — every grader here has been
> wrong at least once, and the ones that were never audited are not the
> exceptions, they are the ones not yet checked.

## Observed — a capability that was written off as unreachable

- Token counting does not need the credential this container lacks. `claude -p --output-format json` reports `usage.input_tokens` from the model's own tokenizer; subtracting a calibrated empty baseline gives the count of any text. [src:TOKEN-COUNT-DIFFERENTIAL-2026-08-28]
- The method was proved before being used, not after: the empty baseline returned 231 tokens on three identical probes, and two 11-token strings measured 22 concatenated. `tools/parity_check.py` now exercises both properties on live calls and reports PASS. [src:TOKEN-COUNT-DIFFERENTIAL-2026-08-28]
- Isolation mattered more than the arithmetic. Without `--tools "" --setting-sources ""` the frame was 3632 tokens rather than 231, and would have drifted with whatever the working directory happened to contain. [src:TOKEN-COUNT-DIFFERENTIAL-2026-08-28]
- The operating prompt is **573 tokens**. [src:OPERATING-PROMPT-TOKENS-2026-08-28]

> Reading, not a claim: the parity matrix carried this row as unreachable on
> the strength of a statement that was true about the endpoint and false about
> the capability — `/v1/messages/count_tokens` does need a key; counting tokens
> does not. That is the failure mode this repository is least protected
> against, because nothing in it was fabricated: a correct fact was left
> standing in for a question nobody re-asked. The suite contains a trap,
> `spec-05`, that asks precisely this, and both arms were graded correct for
> refusing it. The refusal was right when it was made and is now obsolete.
> Doctrine offers two honest moves for an unknown — go get a source, or record
> it as unknown — and this repository had been taking the second one for a day
> without re-checking whether the first had become available.

## Observed — three more capabilities that were never actually blocked

- Asking the count_tokens question of every other blocked row — *is this true of the endpoint, or of the capability?* — moved three of the remaining seven. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
- **Prompt caching works through the CLI**, unprompted. A repeated system prefix wrote 5611 tokens to cache on the first call and read 5407 back on the second, with no `cache_control` set by us. This was listed as "the largest cost lever" and missing. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
- **Image input works through the CLI.** The model described a generated 64×64 PNG it had never seen as red in the top-left and blue elsewhere, which is what the file contains. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
- **Custom tool definitions work over MCP.** A tool named, described and schema'd entirely by this repository was offered to the model, chosen by it, and called — returning a keyed digest, `539e62e4`, that cannot be derived from its arguments. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
- The matrix moved from 20 passed / 8 unreachable to **24 passed, 0 failed, 8 unreachable**. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
- Two constraints found while proving it: an image path outside the CLI's working directory returns "the file doesn't exist", and a system prefix under the model's minimum cacheable length reports zeroes in every cache field — which is not caching failing. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]
- The caching probe passed, then failed on a second run with `created=0, read=5611`, because the first run's cache entry was still live. The capability was working both times; the assertion required a cold cache. [src:PARITY-PROBE-OVERSPEC-2026-08-28]

> Reading, not a claim: four rows in total came off the blocked list in one
> sitting, and not one of them needed a credential, a purchase, or a new
> feature. They needed the question asked in the other direction. Every one of
> those rows had a *true* sentence attached — the endpoint really does need a
> key — and the truth of the sentence is what stopped anyone re-reading it. A
> falsehood would have been caught by the guard this repository is built
> around; a true statement standing in for a question nobody re-asked is
> invisible to it. That is the more dangerous of the two, and there is no tool
> here that detects it.
>
> The over-specified caching probe is the same lesson turned inward: a check
> that goes red for being run twice is testing the schedule, not the feature.

## Observed — three playground fields the matrix had no row for

- The playground draft carries `messages`, `stream` and `speed`. Two are reachable from the CLI: two user turns over `--input-format stream-json` returned two results in one invocation, the second recalling a value only the first carried; and a streamed response arrived as 12 newline-delimited events rather than one blocking payload. [src:CLI-TRANSPORT-ROWS-2026-08-28]
- `speed` is not, and now says why: `fast_mode_state='off'`, `fast_mode_disabled_reason='sdk_opt_in_required'`. [src:CLI-TRANSPORT-ROWS-2026-08-28]
- The matrix stands at **26 passed, 0 failed, 9 unreachable**. [src:CLI-TRANSPORT-ROWS-2026-08-28]

- Two earlier versions of the multi-turn probe each gave a confident wrong answer. `claude -p` invoked from inside a session reports *that session's* id, so a `--resume` probe recalled a word already in this conversation and passed while proving nothing. Replacing it with a hex token then made a working capability fail, because the model declined the token as suspicious. [src:PROBE-CONFOUNDS-2026-08-28]

> Reading, not a claim: the second of those is the one worth carrying
> elsewhere. A refusal and a transport failure look identical when the check is
> "did the expected string come back", so any harness that carries nonce-shaped
> strings through a model will record capabilities as broken that are not. The
> fix was to carry an ordinary fact — a desk number — generated in-process and
> never printed before the call, so it could arrive by no route but the one
> under test.

## Observed — an audit of this repository's own prose, by a subagent

- A fact-checker run over the day's three commits found no numeric drift, no point estimate quoted without its interval, and no blockquote smuggling claims past the guard. It found three staleness defects instead: `docs/remaining.md` still listed all eight capabilities as credential-blocked after four had been proved otherwise; `README.md` still reported the old matrix count; and `CLAUDE.md` still described `parity_check.py` as red on one row. All three are fixed. [src:CLI-CAPABILITY-RECOVERY-2026-08-28]

> Reading, not a claim: every one of those three was the exact failure this
> repository had just finished writing about — true prose left standing next to
> a newer fact, invisible to a guard that only checks whether claims are
> sourced. The guard cannot catch it, and neither could the person who wrote
> both halves an hour apart. Something that had not read them being written was
> what caught it.

## Observed — an adversarial review, and a correction to what was published

- A five-dimension review with an independent refutation pass produced 15 candidate findings; 8 were verified and 8 confirmed. Nothing was refuted, which is a caution about the method rather than a compliment to it, so every finding was re-derived by hand before being acted on. [src:ADVERSARIAL-REVIEW-2026-08-28]
- **Two holes in the provenance guard itself.** A claim carrying a malformed `[src:` satisfied the sourcing check, because the check tested for the substring while the regex that resolves ids never matched it — so an invented statistic passed the whole guard and it exited 0. And a `### ` subheading under `## Observed` ended the enforced region, disabling the check for everything below it; an indented fence did the same file-wide. [src:ADVERSARIAL-REVIEW-2026-08-28]
- **The stratified analysis had never run.** `RunResult.to_dict()` never wrote the `cases` key the stratum lookup read, so all 40 cases were labelled tuned and the held-out block never printed. [src:STRATIFICATION-NEVER-RAN-2026-08-28]
- Repaired on the same run data: ALL CASES unchanged at −0.0500 [−0.1550, +0.0256]; **tuned, 26 cases: −0.0256 [−0.1000, +0.0400], sign test p = 1.0000**; **heldout, 14 cases: −0.0952 [−0.2667, +0.0000], 3 better, 0 worse, 11 tied, sign test p = 0.2500**. Both strata span zero. [src:STRATIFICATION-NEVER-RAN-2026-08-28]
- `compare()` pooled runs for blind judging without consulting `CaseRun.errored` — the one path that never did — so the earlier claim that errored runs are excluded was true of grading and false of judging. [src:ADVERSARIAL-REVIEW-2026-08-28]
- `bradley_terry` ranked an undefeated 10-0 player third, with strength 3.67e-09, because absolute-scale smoothing was combined with per-iteration renormalisation. [src:ADVERSARIAL-REVIEW-2026-08-28]
- `contains_any` given a scalar `values: hello` iterated it character by character and reported "matched 5/5" against unrelated English text. [src:ADVERSARIAL-REVIEW-2026-08-28]

> Reading, not a claim: the correction that matters is the stratification. The
> headline never moved, but a block headed "stratum: tuned (40 cases)" was
> printed and reported as though the pre-registered held-out check had run,
> and it had not. The signal was there to be read — that block reproduced the
> ALL CASES numbers to the digit — and reproducing them exactly is what a
> stratum containing every case does. It was noticed and not pursued.
>
> The held-out numbers now available are the ones the pre-registration wanted
> and they are still null: p = 0.25 on fourteen cases, an interval whose upper
> bound touches zero only because a percentile bootstrap over discrete data
> has an atom there. The direction is cleaner on the held-out set than the
> tuned one, which is the opposite of the overfitting pattern found in an
> earlier run, and at fourteen cases it is not something to build on.
>
> Two of the eight defects were in the fabrication guard, and both made it
> exit 0 while missing an invented claim. A guard that fails loudly is a bug;
> a guard that certifies wrongly is the thing it was built to prevent, wearing
> its own uniform.

## Conclusion

The honest answer to "look through all my previous claude chats" is bounded:
three sibling sessions exist and their titles, goals, models, branches and
self-reported summaries are known [src:SESSIONS-2026-08-27], but their
conversation contents were not reachable by any means available here
[src:NO-TRANSCRIPT-ACCESS-2026-08-27], and no exported archive exists on disk
[src:NO-LOCAL-ARCHIVE-2026-08-27] or in Drive [src:NO-DRIVE-ARCHIVE-2026-08-27].

Everything downstream of this file is built on that record alone. The chat
contents were not reconstructed, summarised, or guessed at.
