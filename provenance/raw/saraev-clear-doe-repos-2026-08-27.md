# Two repositories, cloned and read in full — 2026-08-27T17:00Z

Both are public GitHub repositories, cloned through this session's git proxy
(`git clone --depth 1`) after `add_repo` confirmed anonymous read access. This
matters: the earlier research reached neither, because search-index coverage
did not surface them and the fetch tool could not reach their hosts. Reading a
cloned file is first-hand as to **what the file says**; it remains third-party
as to **what Nick Saraev said**, since neither repository is his.

---

## 1. `Pvragon/ai-workspace-reference`

File: `team-lib/context/indexed/nick-saraev-doe-framework.md` (274 lines).
Frontmatter: `maintainer: pvragon`, `created: 2026-02-18`, and a `sources:`
list naming three YouTube videos of his, a LinkedIn post, a course page, and
`nick-saraev.kit.com/aaa09595c6`.

### It documents a CLEAR framework, and attributes it to Saraev

Quoted verbatim, heading and table:

    ## The CLEAR Framework (Effective AI Communication)

    Saraev's framework for writing effective prompts and directives:

    | Letter | Component | Description |
    | :--- | :--- | :--- |
    | **C** | Clarity | Precise problem definition with measurable outcomes |
    | **L** | Logic | Structured thinking AI can follow |
    | **E** | Examples | Specific scenarios and edge cases |
    | **A** | Adaptation | Iterative refinement based on feedback |
    | **R** | Results | Validation that output matches business needs |

**This is a different framework from Lo's, sharing an acronym.** Lo's five are
Concise, Logical, Explicit, Adaptive, Reflective. Three of the five letters
expand differently here: Clarity/Concise, Examples/Explicit, Results/Reflective.

### The directive layer's field list, verbatim

    **What a directive contains**:

    - The goal/objective of the task
    - Inputs the agent will receive
    - Process steps (sequence and logic)
    - Which tools/scripts to use
    - Edge cases and how to handle them
    - Definition of Done (explicit success criteria)
    - Guardrails (what the agent must NOT do)

### Other quoted material

    "You cannot run a million dollar a month operation on a system that only
    works most of the time."

    "In business, even a 1% rate of inaccuracy can lead to a revenue reduction
    of 50% or more."

    "A Python script does not hallucinate. It either works or errors out."

    "AI is the decision maker, but reliable code does the actual work."

    "The people making the most money in 2026 probably won't be the best at
    automation tools. They'll be the best at identifying business problems,
    translating those problems into prompts, and then orchestrating AI to
    solve them."

Error compounding, quoted: `0.9^5 = 0.59 (59% overall success rate)`.

Self-annealing loop, quoted: Catch → Read → Diagnose → Fix → Rewrite → Retry,
where **Fix** updates the execution script and **Rewrite** updates the
directive "to warn future instances".

---

## 2. `A1pha3/text-matrix`

File: `content/posts/video/ai-agents-full-course-2026-nick-saraev-200k-views.md`
(156 lines, Chinese). Its own description states it is reconstructed from the
subtitles ("据字幕重建") of *AI Agents Full Course 2026*, YouTube `EsTrWCV0Ph4`,
and dates itself 2026-04-29.

### The prompt contract, quoted then translated

    - **提示词契约（prompt contract）**：把含糊需求拆成目标、约束、输出格式、
      失败条件四段写清楚再开工；配套的"反向提示"（reverse prompting）是反过来
      让模型先问你 5 个澄清问题，把没说的偏好挖出来，再生成契约。

Translation by this session: *"**Prompt contract**: before starting, break a
vague requirement into four written parts — goal, constraints, output format,
and failure conditions. Its companion, 'reverse prompting', inverts this: have
the model first ask you five clarifying questions to surface the preferences
you did not state, then generate the contract."*

### The iceberg technique, quoted then translated

    - **上下文冰山（iceberg technique）**：别把整个代码库或整份大文档一次性塞进
      上下文。提示词里只放"水面之上"的全局/项目规则和当前任务，其余留给工具按需
      去读——要用哪个文件才 read 哪个。

Translation: *"**Context iceberg**: do not stuff an entire codebase or a whole
long document into context at once. Put only what is 'above the waterline' in
the prompt — the global and project rules, and the current task — and leave the
rest for tools to read on demand: read a file only when it is needed."*

### Definition of done, quoted then translated

    每转一圈，上下文就更大一点。转个三四圈，模型会撞到一个大多数人漏掉、所以
    老是失望的东西——**完成的定义（definition of done）**：一组约束和技术规格，
    告诉模型"到此可以不用再循环了"。

Translation: *"Each turn of the loop grows the context. After three or four
turns the model runs into the thing most people leave out, which is why they
are perpetually disappointed — the **definition of done**: a set of constraints
and technical specifications telling the model 'you can stop looping now'."*

### The self-modifying instruction file, quoted then translated

    开始任何任务前先读完本文件；文件底部有一个会增长的"已学规则"区。
    当用户纠正你、或你犯错时，立刻往"已学规则"区追加一条新规则，
    按序号写成祈使句，格式：[类别] 永远/绝不 做 X，因为 Y。

    ── 已学规则 ──
    1. 【前端】绝不默认深色模式，因为用户不喜欢。

Translation: *"Read this whole file before starting any task; at the bottom
there is a growing 'learned rules' section. When the user corrects you, or you
make a mistake, immediately append a new rule to that section, numbered and
written as an imperative, in the format: [category] Always/Never do X, because
Y. — Learned rules — 1. [frontend] Never default to dark mode, because the user
dislikes it."*

The article also states the precedence order it attributes to him: global
`agents.md` / `claude.md` / `gemini.md` (Claude's under `~/.claude/`), then the
project-local file, then skills, then the inline prompt for this turn.

### Other techniques it attributes to the same course

Randomised multi-agent consensus (same task, slightly varied prompts, take the
mode; minority answers kept as divergent leads); an agent chatroom of debating
personas; a sub-agent review loop (implement → review with fresh context → fix
→ re-check); model routing by task difficulty; multi-agent MCP orchestration;
video-to-action.

---

## What these two sources are, stated plainly

Third-party documentation, read first-hand and quoted above. Neither is
Saraev's own page and neither video was watched: `youtube.com` remains refused
by this container's egress gateway. They agree with each other on the shape of
his method without being copies of each other — one is an English framework
reference sourced to three videos, the other a Chinese subtitle reconstruction
of a fourth. That is corroboration, not proof of wording.
