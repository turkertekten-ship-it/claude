# Research dossier — SECOND-HAND — 2026-08-27

> Framing, not a claim. Final synthesis returned by the `saraev-clear-research`
> workflow (run wf_6fda65f2-c1d, 10 agents, 335 tool calls, 6/6 sweep angles,
> 165 raw claims). Stored verbatim so it can be read as what it is: a set of
> leads. Its own opening paragraph states the constraint governing all of it —
> only github.com and raw.githubusercontent.com were ever fetched, everything
> else arrived through the search tool's summariser, and that summariser was
> caught attributing other authors' work to Saraev. Nothing here was promoted
> to a claim in this repository without a separate first-hand capture.

---

# Nick Saraev: research dossier

**Provenance grade — read before citing anything below.** Four research passes and two adversarial verification passes fed this dossier. Three of the four passes reported that they **fetched zero web pages**: the session's egress proxy returned `403 CONNECT` / `EGRESS_BLOCKED` for every host tried (nicksaraev.com, leftclick.ai, youtube.com, sciencedirect.com, digitalrepository.unm.edu, and even en.wikipedia.org and example.com), so `WebSearch` was the only working channel. The fourth pass (the one supplying most of Section 3) was truncated in the material handed to me before it stated its verification method, so its quotes carry the same caveat until re-checked.

Consequences, stated plainly:

- A quote below is **verbatim** only in the sense that it is a page/post/video/product **title** as the search index rendered it, or a phrase that an exact-phrase query returned the source page for. Body-text quotes are the search layer's rendering, not text anyone read on the page.
- The **only** URLs actually fetched and read are on `github.com` / `raw.githubusercontent.com` (Section 4, DOE).
- One research pass detected the search summariser **confabulating**: asked about "Saraev Monte Carlo prompt iteration," it attributed third parties' Andrej Karpathy autoresearch write-ups (Damian Galarza, Schalk Neethling, sidsaladi) to Saraev outright. Nothing that rests on that summariser's *attributions* has been promoted to a claim.

Re-verify from an unrestricted network before publishing any quote here.

---

## 1. Who Nick Saraev is

- He describes himself on his YouTube channel's About page as someone who "makes money with AI and teaches others how they can too" (https://www.youtube.com/channel/UCbo-KbSjJDG6JWQ_MTZ_rNA/about)
- His channel page states he is "Make.com and N8N certified" (https://www.youtube.com/channel/UCbo-KbSjJDG6JWQ_MTZ_rNA)
- His own About page says he "pivoted from a path in medicine" (https://nicksaraev.com/about/)
- The same About page carries the headline revenue figure "scaled to a combined $160,000/mo in revenue". The verified fragment is that phrase alone; the attribution of it to LeftClick and 1SecondCopy specifically is the research pass's reading, not part of the confirmed quote (https://nicksaraev.com/about/)
- His About page claims "His content has been viewed over 50 million times" (https://nicksaraev.com/about/)
- He positions his paid community as "the largest AI community on Skool by revenue" — a phrase that exact-phrase search returned across his /projects/, /about/ and /biography/ pages (https://nicksaraev.com/projects/)
- LeftClick's homepage claims it has "generated over $10M in revenue for clients across 20+ industries" (https://leftclick.ai/)
- LeftClick publishes a 1SecondCopy case study titled "$10.5 k/mo to $92 k/mo with cold email systems" (https://leftclick.ai/case-studies/1secondcopy)
- LeftClick sells fixed-price engagements: its pricing page is titled "Pricing — Fixed-Price AI Engagements | LeftClick AI" (https://leftclick.ai/pricing)
- He runs a paid Skool community titled "Maker School: AI Automation" (https://www.skool.com/makerschool/about)
- He runs a **second, separate** Skool community titled "Maker Zero: Claude Code, AI" (https://www.skool.com/maker-zero/about)
- He runs a main YouTube channel (https://www.youtube.com/@nicksaraev) and a second one titled "Nick Saraev Daily Updates" (https://www.youtube.com/@nicksaraevdaily)
- His free lead magnet is titled "Your 110 Step Roadmap to $25K/Month With Automation" (https://leftclicker.gumroad.com/l/110-steps)
- His Gumroad store ships n8n artifacts, e.g. "AI Asset Generator in n8n" (https://leftclicker.gumroad.com/l/oejie), "The N8N Instagram Parasite System (10K Followers In 15 Days)" (https://leftclicker.gumroad.com/l/mcpkm), and "Scrape Google Maps Emails WITHOUT Paying for APIs" (https://leftclicker.gumroad.com/l/wngwgy)
- He publishes platform-comparison content: "Make.com vs N8N in 2025 (AI Agents, Key Features, & More)" (https://nicksaraev.com/n8n-vs-make-2025/)
- His YouTube output is agency-business-building as much as tool tutorial — e.g. "How I'd Start an AI Automation Agency With $100" (https://www.youtube.com/watch?v=RC_JkBjf1Hk), "How I Onboard AI Automation Agency Retainer Clients" (https://www.youtube.com/watch?v=THHnEiOnm1M), "How to Pick a Niche for your AI Automation Agency in 2025" (https://www.youtube.com/watch?v=xwZW4hzTVZQ)
- He also publishes long-form Claude Code instruction: "CLAUDE CODE ADVANCED FULL COURSE (3 HOURS)" (https://www.youtube.com/watch?v=UPtmKh1vMN8) and "I Built a $1M/y SaaS with Claude Code, Here's How" (https://www.youtube.com/watch?v=K65vd9EYbDU)
- On his own LinkedIn he posted "Maker School quickly grew from $0 to $290k/month." (https://www.linkedin.com/posts/nick-saraev_maker-school-quickly-grew-from-0-to-290k-activity-7371552400421154816-twSg)
- On his own LinkedIn he posted "I've gone from 0 to 280k+ IG followers in 7 months." (https://www.linkedin.com/posts/nick-saraev_ive-gone-from-0-to-280k-ig-followers-in-activity-7359230837281734656-F_-Y)
- n8n lists him as a verified creator: "Nick Saraev - n8n Creator" (https://n8n.io/creators/nicksaraev/)
- n8n's official X account has promoted one of his builds: "Nick Saraev shows how you can set up a smart AI-powered Linkedin DM system using automatic profile enrichment and personal messages - in under one hour!" (https://x.com/n8n_io/status/1919407265393586474)
- A GitHub profile that the verification pass identified as his — on the basis of its links to nicksaraev.com, @nicksaraev and Maker School — describes him as a "Developer, entrepreneur, and AI leader with 400K+ YouTube subscribers. He founded Maker School, the largest AI community on Skool by revenue." This is one of the very few pages actually fetched and read (https://github.com/nickjwells)
- That profile lists 20 repositories, none of which is a named framework or prompt library (https://github.com/nickjwells)
- Third-party framing of his method, from an independent operator: "he puts out at least 1 long-form youtube video a day on 2 channels. and 1 IG per day - his videos are not high quality productions." (https://x.com/moritzkremb/status/1950849880928202829)
- An independent complaints/review surface exists for Maker School; the reviews themselves were not read (https://www.trustpilot.com/review/nicksaraev.com)

---

## 2. The CLEAR framework: actual provenance

**Author: Leo S. Lo. Not Nick Saraev.**

The framework originates in a single-authored 2023 article, "The CLEAR path: A framework for enhancing information literacy through prompt engineering," in *The Journal of Academic Librarianship*, Volume 49, Issue 4, article 102720, DOI `10.1016/j.acalib.2023.102720` (https://www.sciencedirect.com/science/article/abs/pii/S0099133323000599). It is deposited in the University of New Mexico's institutional repository under University Libraries faculty scholarly publications (https://digitalrepository.unm.edu/ulls_fsp/211/) and indexed independently on BibBase (https://bibbase.org/network/publication/lo-theclearpathaframeworkforenhancinginformationliteracythroughpromptengineering-2023) and Penn State PURE (https://pure.psu.edu/en/publications/the-clear-path-a-framework-for-enhancing-information-literacy-thr/). A third-party 2026 article names the author possessively in its title: "Prompt Engineering: How Lo's CLEAR Framework Holds Up in 2026" (https://medkharbach.com/prompt-engineering-clear-framework/).

At the time of publication Lo was Dean of the College of University Libraries & Learning Sciences at the University of New Mexico (https://digitalrepository.unm.edu/ulls_fsp/211/). He became University Librarian and Dean of Libraries at the University of Virginia effective 15 September 2025 (https://library.virginia.edu/news/2025/leo-lo-named-uva-librarian-and-dean-libraries), so any source calling him "UVA" is describing his current post, not the 2023 byline. He previously held leadership roles at Penn State, Alabama and Kansas State (https://www.arl.org/news/leo-s-lo-to-helm-the-university-of-virginia-uva-library-as-university-librarian-and-dean-of-libraries/) — which is why a Penn State research-output page also indexes the article.

**Stated purpose:** "The CLEAR Framework for Prompt Engineering is designed to optimize interactions with AI language models like ChatGPT… academic librarians can empower students with critical thinking skills for the ChatGPT era." (https://digitalrepository.unm.edu/ulls_fsp/211/)

**The five components.** The abstract states "five core principles—Concise, Logical, Explicit, Adaptive, and Reflective" (https://www.sciencedirect.com/science/article/abs/pii/S0099133323000599). The per-component wording below traces to the UNM full-text deposit, but was surfaced through search rather than read in the PDF — treat it as Lo's phrasing pending eyes-on verification:

| Letter | Term | Definition as surfaced |
|---|---|---|
| C | Concise | "A concise prompt eliminates unnecessary information, allowing AI models to focus on the key aspects of the task, resulting in more precise and relevant responses." (https://digitalrepository.unm.edu/cgi/viewcontent.cgi?article=1214&context=ulls_fsp) |
| L | Logical | "a logical structured prompt helps the AI model understand the context and relationships between various concepts." (https://digitalrepository.unm.edu/cgi/viewcontent.cgi?article=1214&context=ulls_fsp) |
| E | Explicit | "Explicit prompts provide precise instructions regarding the desired output format, content, or scope, reducing the likelihood of irrelevant responses." (https://digitalrepository.unm.edu/cgi/viewcontent.cgi?article=1214&context=ulls_fsp) |
| A | Adaptive | "Adaptive prompts highlight the need for flexibility, and experimenting with various prompt formulations and adjusting based on AI model performance ensures a balance between creativity and focus." (https://digitalrepository.unm.edu/cgi/viewcontent.cgi?article=1214&context=ulls_fsp) |
| R | Reflective | "Reflective prompts emphasize the importance of continuous evaluation. By assessing AI-generated content and using feedback to refine future prompts, users can continually enhance their prompt engineering techniques." (https://digitalrepository.unm.edu/cgi/viewcontent.cgi?article=1214&context=ulls_fsp) |

A widely repeated secondary gloss splits the acronym into build-then-iterate: "The Concise, Logical and Explicit elements help you engineer an initial prompt, while the Adaptive and Reflective elements reflect the fact that almost all forms of information seeking are iterative." That is a library guide's interpretation, not confirmed as Lo's own framing (https://guides.lib.unc.edu/c.php?g=1419039&p=10519662). Lo's expansion is what university library guides teach (https://guides.library.tamucc.edu/prompt-engineering/clear), and CLEAR references in the healthcare prompt-engineering literature also resolve to Lo's expansion rather than a separate clinical framework (https://www.sciencedirect.com/science/article/abs/pii/S1471595325002987).

**Is Saraev connected to CLEAR? No evidence that he is.** Two independent passes ran fifteen distinct queries between them (enumerated in Section 5) pairing his name, his companies and his community with CLEAR as framework / method / system / acronym / "C.L.E.A.R." Not one returned a page attributing CLEAR to him. The single exact-phrase co-occurrence of "Nick Saraev" and "CLEAR" was a LinkedIn post of his where *clear* is an ordinary English adjective: "Nick Saraev - I made $38.41 on YouTube. To be clear" (https://www.linkedin.com/posts/nick-saraev_i-made-3841-on-youtube-to-be-clear-activity-7384960325701521408-6_ub).

Two limits on that negative, stated honestly: nicksaraev.com and youtube.com were both unreachable, so this rests on search-index coverage, not on inspection of his pages, and video interiors are not searchable at all. But the positive attribution does not depend on the negative: Lo's dated, peer-reviewed 2023 publication establishes priority regardless of whether Saraev has ever mentioned the acronym.

**Competing CLEARs that are not Lo's** (all unverified expansions, listed so they are not mistaken for his): Context / Language / Examples / Audience / Request (https://aipromptsx.com/prompts/frameworks/clear); a 2026 "CLEAR Method" post whose own acronym the search tool rendered two conflicting ways (https://automatemyjob.co.uk/blog/clear-prompt-engineering-framework-2026); and a Context / Logic / Examples / Action / Refinement-or-Result variant for Optimizely instruction agents (https://chappytastic.co.uk/part-1-the-clear-framework-explained-foundations-for-building-effective-instruction-agents/). None attributes itself to Lo. None attributes itself to Saraev either.

---

## 3. Saraev's documented method

**This section is thin in a specific place, and the gap matters.** What is documented is his *business and scoping* method — how he decides what to automate, how he packages it, how he prices it. On **prompting technique specifically, this dossier has nothing verified at all.** The dedicated prompting research pass returned a self-declared failure: it could not confirm a single technique in his own wording, and every prompting item it surfaced came from a third-party AI summary of one video. Those are quarantined in Section 4. Do not present them as his method.

The rules below are quoted. Each traces to a page on his own site; per the provenance note, the wording was surfaced by search rather than read on the page.

1. **Apply a three-part test before selling an automation.** Build it only where "there's a clear deliverable (a document, email, CRM, line-item, etc.), it solves a hot-button pain point (something that impacts revenue), and you can template most of it" (https://nicksaraev.com/5-more-automations-you-can-sell-today-for-1-500-or-10-000/)
2. **Make the output tangible, because the system itself is invisible.** "Automations are all intangible cloud-based systems. However, the best automation systems produce something tangible—something the client can see, feel touch. Examples: documents, emails, CRMs, assets, etc." (https://nicksaraev.com/5-more-automations-you-can-sell-today-for-1-500-or-10-000/)
3. **Define "pressing problem" economically, not technically.** A pressing problem is "anything that impacts your ability to generate revenue, save money, or free founder time" (https://nicksaraev.com/5-more-automations-you-can-sell-today-for-1-500-or-10-000/)
4. **Price against the client's bleed, not your build hours — and charge for speed.** "When a business is actively losing money or potential customers due to inefficiencies, they are willing to pay a percentage of that money to rectify the problem, and often pay more if it's rectified quickly." (https://nicksaraev.com/5-more-automations-you-can-sell-today-for-1-500-or-10-000/)
5. **Package every automation the same way.** "~$1,500-$5,000 USD fixed price (no add-ons), or a lower monthly retainer, as well as charge an hourly rate to implement it or make tweaks, as well as a monthly maintenance fee" (https://nicksaraev.com/5-more-automations-you-can-sell-today-for-1-500-or-10-000/)
6. **Productize: ship the same thing every time.** "Productization is when you provide the same, or very similar, deliverables every time you work with someone." (https://nicksaraev.com/productization-101/)
7. **Productization exists to cure two named failures.** "Most agencies struggle with scope creep and variable COGS which eats up their margins." (https://nicksaraev.com/productization-101/)
8. **The unit-economics justification for productizing.** It "lets you reverse engineer your costs, determine your COGS ahead of time with reasonable accuracy, and staff easily and manage resources based on output" (https://nicksaraev.com/productization-101/) — and he ranks it as "one of the highest-ROI things you can do to crush it in the agency space, and it synergizes wonderfully with automation." (https://nicksaraev.com/productization-101/)
9. **Treat automation as a time-shifting trade, not free leverage.** "Automation, at its core, is essentially front-loading your work. You spend a certain amount of time, energy, or money at time x so that you don't have to repeatedly spend those resources at time y." (https://nicksaraev.com/the-small-business-automation-problem/)
10. **Below capacity, sell — do not systemize.** "if you're a small business owner operating under capacity, the highest ROI thing you can probably do is spend more time and efforts on sales—not on 'brushing up' your business automations" (https://nicksaraev.com/the-small-business-automation-problem/)
11. **Net maintenance cost against the per-action saving before building.** "Automations aren't gifts from above—they're processes that take time and energy to create." (https://nicksaraev.com/the-small-business-automation-problem/)
12. **Decide by expected value.** "The expected value of a decision (EV) is equal to its impact (I) and the likelihood that you're successful at it (P)." This is the one formally named decision framework found on his site (https://nicksaraev.com/know/)
13. **Bias to action over planning.** "an ounce of movement is worth a pound of strategy" (https://nicksaraev.com/next-few-months/)
14. **Take asymmetric bets deliberately** — he frames large uncertain bets as a "classic asymmetric bet … willing and happy to take it" (https://nicksaraev.com/next-few-months/)
15. **Aim for competence, not mastery.** "Many try to become the best, but in doing so, never even get to good." (https://nicksaraev.com/how-i-learned-photography-in-16-hours/)

*Gap disclosure:* the source findings for this section were **truncated mid-sentence** in the material handed to me, at a sixteenth rule beginning "He defines the standard to aim for — competence,". That rule is omitted rather than completed, and there may be further rules in the original pass that never reached this dossier.

*What is missing and was specifically looked for:* how he structures system prompts for n8n/Make.com AI nodes; how he tests or evaluates prompts; how he enforces or repairs structured output (JSON validation, retries); whether he publishes copyable prompt templates. **None of these was established.**

---

## 4. Contested or unverifiable

**The "DOE framework."** Six mutually independent third-party GitHub repositories — the only pages any pass actually fetched and read — attribute a named three-layer framework to him: Directive → Orchestration → Execution (https://github.com/Vibe-Marketer/Agentic-Workflows-Template/blob/main/README.md; https://raw.githubusercontent.com/datacraftdevelopment/ClaudeAgent_v3/main/README.md; https://raw.githubusercontent.com/Pvragon/ai-workspace-reference/762e7476aa128f02b7d8fd100b034e0a7001ca59/team-lib/context/indexed/nick-saraev-doe-framework.md). One asserts the naming is his own deliberate act: "Give your system a NAME so it's memorable and reusable (his is 'DOE')." (https://raw.githubusercontent.com/sam3690/personal-brand/main/content/knowledge-base/winning-post-patterns.md). It is nonetheless **not established**, for three reasons. (a) It is an agent/workflow architecture, not a prompting framework. (b) No source he controls confirms he coined the acronym; the two videos cited as its origin, "Agentic Workflows: Beginner to Pro" (https://www.youtube.com/watch?v=MxyRjL7NG18) and "the n8n killer? AGENTIC WORKFLOWS: Full Beginner's Guide" (https://www.youtube.com/watch?v=bA-WmidVSGo), do not contain "DOE" in their titles, and one repo hedges to "inspired by Nick Saraev's approach" (https://github.com/Wilson-E/automation/blob/2023e3ac5f1e740a4605beab1c4c55d6a390482a/CLAUDE.md). (c) The name is unstable across sources — "DOE framework", "DO framework" (https://github.com/splitwireml/second_brain/blob/e6c319854cd1a9515632a9fc82b912ebfe172774/concepts/ai-automation-path.md), "Directive-Orchestrative-Executive (DOE)" (https://github.com/JesseBeckerGBH/wnba-ensemble/blob/49de6b413f9de4db60d7879f6fe32a7bf10265d7/gemini_brain_prompt.md) — which is the signature of downstream summarisers naming a pattern rather than an author branding one. A separate third-party LinkedIn post title also circulates the name (https://www.linkedin.com/posts/bob-mwathu_theres-a-new-way-to-build-ai-agentic-systems-activity-7413147110675750912-cRU4).

**Prompting techniques attributed to his video CxbHw93oWP0.** A video titled "$2.4M of Prompt Engineering Hacks in 53 Mins (GPT, Claude)" exists on his channel (https://www.youtube.com/watch?v=CxbHw93oWP0) — that is a *title*, and nobody watched it. Every technique below comes from a machine-generated third-party summary of it (https://my.infocaptor.com/hub/summaries/nick-saraev/$2-4m-of-prompt-engineering-hacks-in-53-mins-gpt-claude-CxbHw93oWP0) and is a **lead to check against the real transcript, never a Saraev quote**: "Use the API playground or workbench models instead of consumer models for better control over prompts. A 250-token prompt can be 5% more accurate than an 800-token one"; "Shorter prompts lead to better model performance; focus on improving information density"; "Understand the different prompt types: system, user, and assistant"; "Define output formats explicitly to ensure structured data"; "Iterate prompts with data to refine accuracy using a Monte Carlo approach"; "Use one or few-shot prompting to improve accuracy. Distinguish between conversational engines and knowledge engines; use retrieval-augmented generation for factual data." The Monte Carlo item is the most contaminated — it is the exact query that triggered the confabulation described in the provenance note. Two further recaps of the same video exist and were also unread (https://medium.com/@ferreradaniel/2-4m-of-prompt-engineering-hacks-in-53-minutes-the-ultimate-guide-to-ai-prompt-mastery-b9103e66bbc9; https://www.facebook.com/groups/526497757501957/posts/3345132818971756/).

**Named prompting techniques from a Chinese-language recap** — 提示词契约 (prompt contract), 反向提示 (reverse prompting), 上下文冰山 (iceberg technique) — attributed to his "AI Agents Full Course 2026" by a single secondary source in translation. All three are generic industry terms; there is no evidence he coined them or presents them as a framework (https://raw.githubusercontent.com/A1pha3/text-matrix/main/content/posts/video/ai-agents-full-course-2026-nick-saraev-200k-views.md).

**Maker School revenue.** Irreconcilable across his own properties, with no dates attached to most figures: $290k/month on his LinkedIn (https://www.linkedin.com/posts/nick-saraev_maker-school-quickly-grew-from-0-to-290k-activity-7371552400421154816-twSg); "$330,000/mo" on his FAQ (https://nicksaraev.com/nick-saraev-faq/); $250K/mo on leftclick.ai (https://leftclick.ai/); versus an independent Skool tracker's "Maker School: $217K/Month With a 90-Day Money-Back Guarantee" (https://www.skoolfiles.com/blog/maker-school-nick-saraev-skool). These may be different snapshots. That is a guess, not a finding.

**YouTube subscriber count.** Likewise inconsistent: 307,845 self-reported as of 2026-03-10 (https://nicksaraev.com/the-next-leg/); "400K+" on his GitHub profile (https://github.com/nickjwells); "460K on YouTube" per his X bio (https://x.com/nicksaraev). No current figure was established.

**1SecondCopy's peak revenue.** Given variously as "$92 k/mo" in a LeftClick case-study title (https://leftclick.ai/case-studies/1secondcopy), and as $90K/mo, ~$1M ARR, and ~$30,000/mo elsewhere. Which is peak, which is average, and which period each covers is undetermined.

**The client logo wall.** A roster including Anthropic, MrBeast, Notion, Wix, HeyGen, VEED, Lightricks and Durable was reported by the search tool as appearing on the LeftClick homepage, but was never read on the page (https://leftclick.ai/). Logo walls routinely conflate "client", "used our free content" and "appeared in a video". The nature of any Anthropic relationship is entirely unestablished.

**Maker School price, guarantee and contents** — "$184/month… your first client for an AI automation business in 90 days or your money back" and "218 exclusive videos & guides… over 50 templates/scripts" — are the search tool's paraphrase of the Skool about page, not read text (https://www.skool.com/makerschool/about).

**Media features** (Popular Mechanics, Apple News, Bloomberg, "Amazon Kindle best-seller") are self-asserted on his own bio pages with no independent confirmation of any specific article found (https://nicksaraev.com/about/). **Biographical details** — born February 1996, Bulgarian-Canadian, Calgary-based (https://nicksaraev.com/nick-saraev-faq/); founded 1SecondCopy at 25 and LeftClick at 27 (https://nicksaraev.carrd.co/) — are self-asserted and were not read on the page. **Airtable is not established as part of his stack** and should not be asserted; Make.com, n8n and Claude Code are well evidenced (https://www.youtube.com/channel/UCbo-KbSjJDG6JWQ_MTZ_rNA). A cosine-similarity few-shot-selection technique surfaced on one of his posts may be him relaying a third party's trick rather than his own method (https://nicksaraev.com/ai-generated-stock-photos-set-to-dethrone-shutterstock/). Apify's account of the 1SecondCopy stack is Apify's framing, not his words (https://blog.apify.com/nick-saraev-and-apify/).

Sites ranking for his name that were **excluded as affiliate, review-funnel or course-piracy pages**, and which sourced nothing here: makerschoolnicksaraev.com, nicksaraevskool.com, udcourse.com, ecashminer.com, scamrisk.com, buldrr.com.

---

## 5. Open questions

**What was searched, verbatim where recorded.**

CLEAR ↔ Saraev (fifteen queries across two independent passes): "Nick Saraev CLEAR framework prompt"; "site:nicksaraev.com CLEAR framework"; `"Saraev" "CLEAR" prompt framework Concise Logical Explicit Adaptive Reflective`; `"Nick Saraev" prompting framework "C.L.E.A.R." OR "CLEAR method" youtube`; `"Nick Saraev" "CLEAR framework"`; plus ten further searches pairing "Nick Saraev" / "Saraev" / "Maker School" / "leftclick" with CLEAR as framework, method, system, acronym, C.L.E.A.R. and prompting. All negative.

CLEAR origin: exact-phrase searches for the five candidate section headings ("Concise: brevity and clarity in prompts", "Logical: structured and coherent prompts", …); a targeted search for a "Context-Limitations-Examples-…" expansion, which returned only Lo-derived guides; roughly a dozen searches converging on Concise/Logical/Explicit/Adaptive/Reflective.

Saraev prompting: `Nick Saraev "Monte Carlo" prompt iteration testing prompts output format JSON` (produced the confabulation); `nicksaraev.com prompt engineering system prompt AI agents` (zero nicksaraev.com results); exact-phrase attempts on "cosine similarity … Saraev" and `"Stable Diffusion-ready prompts"` (could not pin quotes to URLs); `"I make $300k/mo from my Skool community"` (returned unrelated videos, so the phrase was **not** treated as verified even though a LinkedIn slug contains it — a slug is a label, not content).

**Unresolved:**

1. Does any Saraev property use CLEAR as a named framework? Unverifiable here — nicksaraev.com and leftclick.ai are egress-blocked and the search tool ignored both `site:` and `allowed_domains` scoping (a `site:nicksaraev.com CLEAR` query returned only Wikipedia pages for "Clear", "ClearHealth", "ClearOS", "Clearblue" — a tool artifact, not evidence about the site).
2. Does the paywalled Maker School curriculum (reported as 218+ videos) contain a CLEAR lesson? Behind a paywall and not indexed; absence from search results proves nothing.
3. Does he say "DOE" out loud? Closing this requires watching bA-WmidVSGo or MxyRjL7NG18 and searching nicksaraev.com for the term.
4. What is actually in "$2.4M of Prompt Engineering Hacks in 53 Mins"? **The single highest-value next step in this whole dossier.** Search the real transcript for the string "250" / "800" tokens first — that is the most falsifiable of the leads.
5. Lo's article: the exact online-first date (July 2023 issue date vs. an April 2023 online date, unreconciled), the verbatim byline affiliation string, his own in-text definitional sentences, and whether CLEAR appeared anywhere before the journal article.
6. Whether the aipromptsx and AutomateMyJob CLEAR variants are independent coinages or rebrandings of Lo's; and whether the Optimizely variant's fifth letter is Refinement or Result.
7. Corporate facts: legal entity names, registration, headcount, whether LeftClick has employees beyond him, whether 1SecondCopy still operates. Wholly unestablished.
8. What "10,000+ graduates" counts as a graduate; what any Anthropic relationship consists of; his newsletter's contents (no URL located).
9. Zero YouTube transcripts were obtained for **any** video. Nothing in this dossier verifies the contents, claims or accuracy of a single Saraev video.

**Method failures worth recording:** `WebFetch` and `curl` were both blocked at the tunnel (`curl: (56) CONNECT tunnel failed, response 403`); per `/root/.ccr/README.md` this is an organisation egress-policy denial to be reported, not routed around, so no archive.org, Google cache or r.jina.ai mirror was attempted. Reading the proxy's own status endpoint and README was in some passes denied by the Bash permission classifier. One pass exhausted a 200-call search budget mid-sweep, losing a planned Crossref/DOI authorship confirmation.

---

## 6. Source table

"Date accessed" is uniform because all passes ran on 2026-08-27. For every row except S-51 through S-58 and S-61, "accessed" means **surfaced through the search index** — the page itself was not fetched. Only the GitHub rows were read.

| id | url | kind | date accessed | description |
|---|---|---|---|---|
| S-01 | https://www.youtube.com/channel/UCbo-KbSjJDG6JWQ_MTZ_rNA/about | primary | 2026-08-27 | His YouTube About page; self-description |
| S-02 | https://www.youtube.com/channel/UCbo-KbSjJDG6JWQ_MTZ_rNA | primary | 2026-08-27 | His main channel page; Make.com/n8n certification claim |
| S-03 | https://nicksaraev.com/about/ | primary | 2026-08-27 | His About page; medicine pivot, $160k/mo, 50M views, media claims |
| S-04 | https://nicksaraev.com/projects/ | primary | 2026-08-27 | Projects page; "largest AI community on Skool by revenue" |
| S-05 | https://leftclick.ai/ | primary | 2026-08-27 | Agency homepage; $10M client-revenue claim, unread logo wall |
| S-06 | https://leftclick.ai/case-studies/1secondcopy | primary | 2026-08-27 | Case study title stating $10.5k→$92k/mo via cold email |
| S-07 | https://leftclick.ai/pricing | primary | 2026-08-27 | Pricing page title; fixed-price engagement model |
| S-08 | https://www.skool.com/makerschool/about | primary | 2026-08-27 | Paid community; price/guarantee/contents unread |
| S-09 | https://www.skool.com/maker-zero/about | primary | 2026-08-27 | Second, separate free community titled for Claude Code |
| S-10 | https://www.youtube.com/@nicksaraev | primary | 2026-08-27 | Main channel handle |
| S-11 | https://www.youtube.com/@nicksaraevdaily | primary | 2026-08-27 | Second channel, "Nick Saraev Daily Updates" |
| S-12 | https://leftclicker.gumroad.com/l/110-steps | primary | 2026-08-27 | Free lead magnet: 110-step roadmap to $25K/mo |
| S-13 | https://leftclicker.gumroad.com/l/oejie | primary | 2026-08-27 | Gumroad product: AI Asset Generator in n8n |
| S-14 | https://leftclicker.gumroad.com/l/mcpkm | primary | 2026-08-27 | Gumroad product: n8n Instagram growth system |
| S-15 | https://leftclicker.gumroad.com/l/wngwgy | primary | 2026-08-27 | Gumroad product: Google Maps email scraping without paid APIs |
| S-16 | https://nicksaraev.com/n8n-vs-make-2025/ | primary | 2026-08-27 | Platform comparison post title |
| S-17 | https://nicksaraev.com/5-more-automations-you-can-sell-today-for-1-500-or-10-000/ | primary | 2026-08-27 | Source of scoping test, tangibility, pricing and packaging rules (2025-07-26) |
| S-18 | https://www.linkedin.com/posts/nick-saraev_maker-school-quickly-grew-from-0-to-290k-activity-7371552400421154816-twSg | primary | 2026-08-27 | His LinkedIn: Maker School $0→$290k/month |
| S-19 | https://www.linkedin.com/posts/nick-saraev_ive-gone-from-0-to-280k-ig-followers-in-activity-7359230837281734656-F_-Y | primary | 2026-08-27 | His LinkedIn: 0→280k+ Instagram followers in 7 months |
| S-20 | https://n8n.io/creators/nicksaraev/ | secondary | 2026-08-27 | Official n8n creator profile |
| S-21 | https://x.com/n8n_io/status/1919407265393586474 | secondary | 2026-08-27 | n8n's official account promoting one of his builds |
| S-22 | https://blog.apify.com/nick-saraev-and-apify/ | secondary | 2026-08-27 | Vendor write-up naming Apify + Make.com behind 1SecondCopy |
| S-23 | https://www.skoolfiles.com/blog/maker-school-nick-saraev-skool | secondary | 2026-08-27 | Independent Skool revenue tracker; $217K/mo cross-check |
| S-24 | https://x.com/moritzkremb/status/1950849880928202829 | secondary | 2026-08-27 | Independent operator's observation on his publishing cadence |
| S-25 | https://www.trustpilot.com/review/nicksaraev.com | secondary | 2026-08-27 | Independent review surface for Maker School; reviews unread |
| S-26 | https://www.sciencedirect.com/science/article/abs/pii/S0099133323000599 | primary | 2026-08-27 | Publisher record for Lo's CLEAR paper; DOI, volume, issue, abstract |
| S-27 | https://digitalrepository.unm.edu/ulls_fsp/211/ | primary | 2026-08-27 | UNM repository deposit; purpose statement and Lo's affiliation |
| S-28 | https://digitalrepository.unm.edu/cgi/viewcontent.cgi?article=1214&context=ulls_fsp | primary | 2026-08-27 | UNM full-text PDF; per-component definitions (surfaced, not opened) |
| S-29 | https://library.virginia.edu/news/2025/leo-lo-named-uva-librarian-and-dean-libraries | primary | 2026-08-27 | UVA announcement of Lo's 2025-09-15 appointment |
| S-30 | https://www.arl.org/news/leo-s-lo-to-helm-the-university-of-virginia-uva-library-as-university-librarian-and-dean-of-libraries/ | primary | 2026-08-27 | ARL announcement listing Lo's prior institutions |
| S-31 | https://guides.library.tamucc.edu/prompt-engineering/clear | secondary | 2026-08-27 | University library guide teaching Lo's CLEAR |
| S-32 | https://guides.lib.unc.edu/c.php?g=1419039&p=10519662 | secondary | 2026-08-27 | Library guide's build-vs-iterate gloss on the acronym |
| S-33 | https://medkharbach.com/prompt-engineering-clear-framework/ | secondary | 2026-08-27 | 2026 article naming "Lo's CLEAR Framework" in its title |
| S-34 | https://bibbase.org/network/publication/lo-theclearpathaframeworkforenhancinginformationliteracythroughpromptengineering-2023 | secondary | 2026-08-27 | Independent bibliographic index of the paper |
| S-35 | https://pure.psu.edu/en/publications/the-clear-path-a-framework-for-enhancing-information-literacy-thr/ | secondary | 2026-08-27 | Penn State research-output index of the paper |
| S-36 | https://aipromptsx.com/prompts/frameworks/clear | secondary | 2026-08-27 | Competing CLEAR variant: Context/Language/Examples/Audience/Request |
| S-37 | https://automatemyjob.co.uk/blog/clear-prompt-engineering-framework-2026 | secondary | 2026-08-27 | Competing 2026 "CLEAR Method"; its own expansion unsettled |
| S-38 | https://chappytastic.co.uk/part-1-the-clear-framework-explained-foundations-for-building-effective-instruction-agents/ | secondary | 2026-08-27 | Competing CLEAR for Optimizely instruction agents |
| S-39 | https://www.sciencedirect.com/science/article/abs/pii/S1471595325002987 | secondary | 2026-08-27 | Nursing literature reference resolving to Lo's expansion |
| S-40 | https://www.linkedin.com/posts/nick-saraev_i-made-3841-on-youtube-to-be-clear-activity-7384960325701521408-6_ub | primary | 2026-08-27 | Only Saraev/"CLEAR" co-occurrence found; ordinary adjective |
| S-41 | https://www.linkedin.com/posts/bob-mwathu_theres-a-new-way-to-build-ai-agentic-systems-activity-7413147110675750912-cRU4 | secondary | 2026-08-27 | Third-party post naming a "DOE Framework" for Saraev |
| S-42 | https://www.youtube.com/watch?v=CxbHw93oWP0 | primary | 2026-08-27 | "$2.4M of Prompt Engineering Hacks in 53 Mins" — title only, unwatched |
| S-43 | https://my.infocaptor.com/hub/summaries/nick-saraev/$2-4m-of-prompt-engineering-hacks-in-53-mins-gpt-claude-CxbHw93oWP0 | secondary | 2026-08-27 | Machine-generated summary; sole origin of the quarantined prompting leads |
| S-44 | https://medium.com/@ferreradaniel/2-4m-of-prompt-engineering-hacks-in-53-minutes-the-ultimate-guide-to-ai-prompt-mastery-b9103e66bbc9 | secondary | 2026-08-27 | Third-party recap of the same video; unread |
| S-45 | https://www.facebook.com/groups/526497757501957/posts/3345132818971756/ | secondary | 2026-08-27 | Group post claiming 14 insights from the same video; unread |
| S-46 | https://nicksaraev.com/productization-101/ | primary | 2026-08-27 | Productization definition, scope-creep/COGS diagnosis, ROI claim |
| S-47 | https://nicksaraev.com/the-small-business-automation-problem/ | primary | 2026-08-27 | Front-loading model of automation; sell-before-systemize heuristic |
| S-48 | https://nicksaraev.com/know/ | primary | 2026-08-27 | Expected-value decision framework |
| S-49 | https://nicksaraev.com/next-few-months/ | primary | 2026-08-27 | Bias-to-action maxim; asymmetric-bet framing |
| S-50 | https://nicksaraev.com/how-i-learned-photography-in-16-hours/ | primary | 2026-08-27 | Competence-over-mastery maxim (2026-05-03) |
| S-51 | https://github.com/nickjwells | primary | 2026-08-27 | GitHub profile identified as his; fetched and read; 20 repos, no named framework |
| S-52 | https://raw.githubusercontent.com/datacraftdevelopment/ClaudeAgent_v3/main/README.md | secondary | 2026-08-27 | Fetched; ties the 3-layer architecture to video MxyRjL7NG18 |
| S-53 | https://raw.githubusercontent.com/Pvragon/ai-workspace-reference/762e7476aa128f02b7d8fd100b034e0a7001ca59/team-lib/context/indexed/nick-saraev-doe-framework.md | secondary | 2026-08-27 | Fetched; fullest third-party DOE write-up, cites bA-WmidVSGo (2025-11-25) |
| S-54 | https://github.com/Vibe-Marketer/Agentic-Workflows-Template/blob/main/README.md | secondary | 2026-08-27 | Fetched; template "Based on Nick Saraev's DOE framework" |
| S-55 | https://raw.githubusercontent.com/sam3690/personal-brand/main/content/knowledge-base/winning-post-patterns.md | secondary | 2026-08-27 | Fetched; asserts the DOE naming is his own deliberate branding |
| S-56 | https://github.com/Wilson-E/automation/blob/2023e3ac5f1e740a4605beab1c4c55d6a390482a/CLAUDE.md | secondary | 2026-08-27 | Fetched; hedges to "inspired by Nick Saraev's approach" |
| S-57 | https://github.com/splitwireml/second_brain/blob/e6c319854cd1a9515632a9fc82b912ebfe172774/concepts/ai-automation-path.md | secondary | 2026-08-27 | Fetched; calls it the "DO Framework" — naming instability |
| S-58 | https://github.com/JesseBeckerGBH/wnba-ensemble/blob/49de6b413f9de4db60d7879f6fe32a7bf10265d7/gemini_brain_prompt.md | secondary | 2026-08-27 | Fetched; third spelling, "Directive-Orchestrative-Executive" |
| S-59 | https://www.youtube.com/watch?v=bA-WmidVSGo | primary | 2026-08-27 | Cited DOE-origin video; title contains no acronym; unwatched |
| S-60 | https://www.youtube.com/watch?v=MxyRjL7NG18 | primary | 2026-08-27 | Second cited DOE-origin video; title contains no acronym; unwatched |
| S-61 | https://raw.githubusercontent.com/A1pha3/text-matrix/main/content/posts/video/ai-agents-full-course-2026-nick-saraev-200k-views.md | secondary | 2026-08-27 | Fetched; Chinese-language recap attributing named prompting terms to him |
| S-62 | https://nicksaraev.com/nick-saraev-faq/ | primary | 2026-08-27 | His FAQ; birth/location and $4M+/yr, $330k/mo figures — wording unread |
| S-63 | https://nicksaraev.carrd.co/ | primary | 2026-08-27 | His carrd bio; founding sequence and ages — wording unread |
| S-64 | https://nicksaraev.com/the-next-leg/ | primary | 2026-08-27 | Self-reported 307,845 subscribers as of 2026-03-10 — wording unread |
| S-65 | https://x.com/nicksaraev | primary | 2026-08-27 | His X bio; cross-platform follower counts — wording unread |
| S-66 | https://nicksaraev.com/ai-generated-stock-photos-set-to-dethrone-shutterstock/ | primary | 2026-08-27 | Post title; possible cosine-similarity few-shot passage, attribution unclear |
| S-67 | https://www.youtube.com/watch?v=RC_JkBjf1Hk | primary | 2026-08-27 | Video title: starting an AI automation agency with $100 |
| S-68 | https://www.youtube.com/watch?v=THHnEiOnm1M | primary | 2026-08-27 | Video title: onboarding retainer clients |
| S-69 | https://www.youtube.com/watch?v=xwZW4hzTVZQ | primary | 2026-08-27 | Video title: picking an agency niche |
| S-70 | https://www.youtube.com/watch?v=UPtmKh1vMN8 | primary | 2026-08-27 | Video title: 3-hour advanced Claude Code course |
| S-71 | https://www.youtube.com/watch?v=K65vd9EYbDU | primary | 2026-08-27 | Video title: building a $1M/y SaaS with Claude Code |
| S-72 | https://www.youtube.com/watch?v=7cIlwOmofwI | primary | 2026-08-27 | Video title carrying a "+$2.8M Earned" figure; referent unverified |
