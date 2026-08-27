---
provenance: delegated-research
---

# The CFO-office and fund-operations stack

> Delegated research, recorded verbatim. This is a subagent's report:
> second-hand under the doctrine in CLAUDE.md, and not promoted to
> established fact anywhere in this repository. The agent reported that
> page fetching was blocked in its environment, so its findings rest on
> search summaries. Confidence grades are the agent's own. Verify anything
> load-bearing against the primary source before acting on it.

**Headline.** This research leg gathered NO new external evidence — the WebSearch budget was exhausted (200/200) before I started and the egress proxy 403s every non-GitHub domain — but first-hand testing against his own oodarag code found three live, silent data-corruption bug classes in Turkish financial text (a 1000x number-parsing error, broken Turkish case-folding, and citation offsets that return the wrong substring), which are more decision-relevant than any survey statistic I was asked to fetch.

## Findings

### 1. The external research this task asked for could not be performed at all; treat every unsourced number in this domain as still unknown

*Confidence: high* · [source](curl -sS $HTTPS_PROXY/__agentproxy/status ; WebSearch tool refusal, 2026-08-27T15:24Z)

WebSearch returned 'this session has used its web search budget (200 of 200 WebSearch calls)' on the first call. Direct fetch probes then returned HTTP 000/403 for arxiv.org, aclanthology.org, eur-lex.europa.eu, www.spk.gov.tr, kap.org.tr, www.resmigazete.gov.tr, en.wikipedia.org, huggingface.co, hbr.org, www2.deloitte.com, www.mckinsey.com, www.bain.com, wsj.com, fortune.com, medium.com. Only api.github.com (200) and raw.githubusercontent.com (301) were reachable. Proxy status endpoint recorded 20 distinct blocked hosts. Consequence: I could NOT obtain measured time-savings for capital-call extraction, LLM document-extraction error rates, fund-admin vendor benchmarks, LLM valuation incidents, Turkish OCR accuracy literature, cost benchmarks, KVKK guidance, or EU AI Act text.

### 2. Turkish thousands separators cause a SILENT 1000x error in Python number parsing — the single most dangerous defect found

*Confidence: high* · [source](/tmp/claude-0/-home-user/e00ed53e-d4d3-5430-8d55-f3fd47147994/scratchpad/tr_eval.py section D, tr_eval2.py section I)

float('1.500') returns 1.5 with no exception, but '1.500' in Turkish notation means 1500. Verified across '1.500'->1.5, '2.750'->2.75, '12.000'->12.0, '1.234'->1.234, '0.500'->0.5: every one a 1.00E+3x understatement, raised silently. Critically, the LOUD cases are safe: '1.250.000,00', '47.850.000,00', '1,5', '0,05' all raise ValueError on float() and InvalidOperation on Decimal(). So the failure mode is inverted from intuition — malformed-looking Turkish amounts fail safely; the clean-looking ones (a plain 4-digit amount) corrupt silently. A capital call for 1.500 TL parsed as 1.5 TL would pass every type check.

### 3. Python's .lower() is wrong for Turkish and silently breaks entity/counterparty name matching

*Confidence: high* · [source](scratchpad/tr_eval.py section C)

'İSTANBUL'.lower() yields 'i̇stanbul' — that is 'i' (U+0069) PLUS COMBINING DOT ABOVE (U+0307), two codepoints, so it does NOT equal 'istanbul' and a case-insensitive join fails. 'IŞIK'.lower() yields 'işik' where Turkish-correct is 'ışık'. 'İŞ BANKASI'.lower() yields 'i̇ş bankasi'. .casefold() behaves identically — it does not fix this. Turkish requires I->ı and İ->i before lowering. This is a dedupe, counterparty-matching and LP-name-matching hazard, not a cosmetic one.

### 4. Citation offsets silently return the WRONG substring on Turkish text — a live provenance bug, since models.py already stores char_start/char_end

*Confidence: high* · [source](scratchpad/tr_eval5.py section L; src/oodarag/models.py:95-96)

src/oodarag/models.py lines 95-96 define char_start:int and char_end:int. A Turkish paragraph measured 263 chars in NFC vs 278 in NFD — 5.7% length drift, one extra codepoint per Turkish diacritic. Offsets [235:262] located against the raw (NFD) extractor output, replayed against an NFC-normalized store, returned 'ğişim tablosu incelenmiştir' instead of the intended 'özkaynak değişim tablosu'. The returned text is still fluent Turkish, so a reviewer spot-checking a citation may not notice. For a pipeline whose stated principle is 'Citations are verified against retrieved chunks', this defeats the control itself.

### 5. The fix for the offset bug is already available in the codebase: clean() converges NFC and NFD

*Confidence: high* · [source](scratchpad/tr_eval5.py section M, tr_eval.py section E)

clean(NFC_text) == clean(NFD_text) evaluated True, and clean() changed length by 0 chars vs raw NFC. normalize_unicode() applies NFKC. So the rule is: normalize exactly once at ingest, persist the normalized text as the canonical artifact, and capture every char_start/char_end against that canonical form — never against the PDF extractor's raw output. NFKC also correctly repairs PDF ligatures ('ﬁnansal'->'finansal') and fullwidth digits ('１.２５０'->'1.250'), and leaves 'İ' and 'ı' intact.

### 6. The existing tokenizer alters 46.1% of Turkish words, because its regex is ASCII-only

*Confidence: high* · [source](scratchpad/tr_eval.py sections A and B; src/oodarag/util/text.py:17)

_TOKEN_RE = [A-Za-z0-9_]+ in src/oodarag/util/text.py excludes ç ğ ı İ ö ş ü. Measured over 5 realistic Turkish fund documents (89 non-numeric words): 41 damaged = 46.1%. Examples: 'şirket'->['irket'], 'değer'->['de','er'], 'katılma'->['kat','lma'], 'taşınmaz'->['ta','nmaz'], 'özkaynak'->['zkaynak'], 'yatırım'->['yat','r','m'], 'İstanbul'->['stanbul'], 'gerçeğe uygun değer'->['ger','e','e','uygun','de','er'].

### 7. NULL RESULT, reported against my own hypothesis: that 46.1% corruption did NOT measurably degrade retrieval

*Confidence: medium* · [source](scratchpad/tr_eval3.py section J, tr_eval4.py section K)

I expected fragmentation to wreck BM25 and tested it. On a 6-query/5-doc set, recall@1 was 6/6 = 100% for BOTH the current ASCII tokenizer and a Unicode-aware replacement. On a 400-document Turkish corpus, precision@10 was 1.00 for both; the ASCII tokenizer matched 15.4% of the corpus per probe vs 13.3% for the fixed one, and produced a 84-token vocabulary vs 78. Reason: the mangling is deterministic and symmetric — the query is corrupted the same way as the document, so the fragments still align. CAVEAT: both corpora were synthetic/templated, so this is a weak null result, not proof. It does mean the tokenizer is a lower priority than the number-parsing and offset bugs, which are silently wrong rather than merely ugly.

### 8. Float arithmetic and Python's default rounding both diverge from Turkish accounting expectations

*Confidence: high* · [source](scratchpad/tr_eval2.py section H)

Twelve monthly accruals of a 2% fee on 1,250,000.00 TRY: float gives 24999.999999999996, Decimal gives 25000.00. round(2.675, 2) returns 2.67 (binary float + banker's rounding) where TR accounting expects half-up 2.68 — Decimal('2.675').quantize(Decimal('0.01'), ROUND_HALF_UP) gives 2.68. round(0.5)=0, round(1.5)=2, round(2.5)=2 confirms Python uses banker's rounding, not half-up. 0.1+0.2==0.3 is False. Any fee, NAV or KDV figure must be Decimal with an explicit ROUND_HALF_UP quantize.

### 9. His config.py already applies the correct numeric discipline — this is a strength to preserve, not a gap

*Confidence: high* · [source](src/oodarag/config.py:31, 134-150, 436)

src/oodarag/config.py imports Decimal and reads decimals from strings, with the comment 'TOML floats would silently round a threshold, and a threshold is compared against money.' It also separates valuation_drift_real (Decimal 0.05) from valuation_drift_nominal (Decimal 0.25), with a comment noting that at ~32% inflation a nominal rule 'would fire every month'. That is the correct real-vs-nominal treatment for a TMS 29 environment and is unusual to get right.

### 10. The pre-existing ledger's fund-administration finding is the one that should anchor the architecture, but its numbers are vendor-sourced

*Confidence: medium* · [source](provenance/sources.yaml [src:FUNDADMIN-AI-2026]; docs/research/01-field-evidence.md)

provenance/sources.yaml entry FUNDADMIN-AI-2026 records AI as strongest on document-heavy processes (extraction, onboarding) and only a supporting layer on the numerical core. The ledger's own note flags that the 98% IR-professional, 78% and 66% fund-accountant figures 'come from vendor-published content marketing their own products' and 'should be treated as low-confidence vendor claims, not survey findings'. I could not independently verify any of them this session. The qualitative pattern is what should be relied on; the percentages should not be quoted to an LP or an auditor.

### 11. The PE-survey and MIT figures in the brief were themselves never read from primary sources

*Confidence: medium* · [source](provenance/sources.yaml [src:PE-AI-SURVEY-2026], [src:MIT-PILOT-FAILURE-2026], [src:EQT-MOTHERBRAIN-2026])

sources.yaml notes for PE-AI-SURVEY-2026 state the S&P and Deloitte figures were 'read from the search summary and secondary write-ups rather than the primary survey PDFs; the primary documents were not obtained'. MIT-PILOT-FAILURE-2026 states the paper 'was not fetched' and came via Forbes/CIO Dive/Yahoo Finance. EQT-MOTHERBRAIN-2026 notes descriptions 'originate largely from EQT's own pages' and 'no independent evaluation of Motherbrain's returns impact was found'. These remain unverified at primary-source level, and I could not upgrade them.

### 12. NO GOOD EVIDENCE EXISTS in this session on Turkish-language OCR and document-extraction error rates

*Confidence: low*

This was a core question in the brief and I must report it unanswered. I obtained zero measured accuracy figures for OCR or LLM extraction on Turkish financial PDFs — no character error rate, no field-level extraction accuracy, no scanned-vs-native comparison, no benchmark on KAP filings, ekspertiz raporu or bank statements. aclanthology.org, arxiv.org and huggingface.co were all blocked. Do not let any downstream design assume a Turkish extraction accuracy number. The structural hazards I did verify (dotless-i, NFD decomposition, comma decimals) are real regardless of what the OCR rate turns out to be.

### 13. NO GOOD EVIDENCE EXISTS in this session on realistic annual cost of the stack at 5-15 people

*Confidence: low*

I could reach no pricing pages, no vendor rate cards, no analyst cost benchmarks, and no case studies on overspend patterns. Any figure offered for an all-in annual cost at WAM's headcount would be invented. This needs to be built bottom-up from actual quotes (model API metered spend, document-extraction vendor, storage, one integrator's day rate) rather than cited.

### 14. NO GOOD EVIDENCE EXISTS in this session on documented LLM-arithmetic or LLM-valuation incidents

*Confidence: low*

The brief asked for concrete incidents where LLM arithmetic or LLM-driven valuation caused problems. I found none, because I could not search. What I can offer instead is the mechanical case above: float/Decimal and TR-separator behaviour verified first-hand. The argument for a deterministic numeric core does not actually need an incident anecdote — the 1000x silent parse and the banker's-rounding divergence are sufficient and reproducible on his own machine.

### 15. KVKK and EU AI Act specifics are UNVERIFIED RECALL — named here only so the right documents get pulled, not as findings

*Confidence: low*

UNVERIFIED RECALL, confirm before any reliance: KVKK is Law 6698; cross-border transfer sits in Article 9, amended in 2024 to add standard contractual clauses (standart sözleşme) notifiable to the Authority alongside the older explicit-consent and adequacy routes — this is the mechanism that governs sending fund or LP personal data to a third-country model API. EU AI Act Article 2 is generally understood to reach third-country providers/deployers where the system's OUTPUT is used in the Union, which is the hook that could catch a Turkish manager with EU LPs. I could not fetch kvkk.gov.tr, eur-lex.europa.eu or artificialintelligenceact.eu (all blocked) and therefore verified none of this. Article numbers, dates and thresholds must be checked against primary text or Turkish counsel before they shape a policy.

### 16. The SPK 23 July 2026 valuation decision — the intended worked example for regulatory-change detection — is still not confirmed at primary source

*Confidence: medium* · [source](provenance/unknowns.md U-8; provenance/sources.yaml [src:SPK-VALUATION-2026-07-23])

unknowns.md entry U-8 records that the decision is established only through Turkish financial press (yatirimx.com.tr, paraajansi.com.tr); the bulletin number, precise scope and operative wording are unknown, and the SPK bulletin was never retrieved. www.spk.gov.tr and kap.org.tr were blocked again this session, so U-8 remains open. The ledger's own guidance applies: an obligation seeded from this should carry a verify flag rather than being presented as settled law.

### 17. Turkish text extracted from PDFs commonly arrives decomposed, and naive matching misses it without error

*Confidence: high* · [source](scratchpad/tr_eval2.py section G)

For 'şirket', 'değer', 'İstanbul', 'güncel', 'çeyrek', NFC and NFD forms are visually identical but differ in codepoint count (6 vs 7, 5 vs 6, 8 vs 9, 6 vs 7, 6 vs 7). A naive set/dict lookup of the NFC form against an NFD-keyed store returned False, and '==' returned False. Any hash-keyed dedupe, any obligation-keyword match, and any exact-phrase filter built without normalization will silently under-match Turkish documents.

## Implications for a small Istanbul GSYF/GYF manager

- Treat this leg as a failed collection, not a completed research pass. The brief's questions on Turkish OCR rates, extraction accuracy, costs, KVKK and the EU AI Act are still open. Do not let a design document quietly fill them with plausible numbers — that is exactly the failure CLAUDE.md section 1 exists to prevent.
- Fix the Turkish number parser before anything else. A single Decimal-returning parse_tr_amount() that rejects ambiguous strings is the highest-value hour of work available: float('1.500') = 1.5 is a 1000x error that raises nothing, and it sits directly in the path of capital-call and appraisal figures.
- Pin the normalization boundary now, while the chunker is still unwritten. Normalize once at ingest with the existing clean(), store that as canonical, and derive every char_start/char_end from it. models.py already has the offset fields, so the bug is reachable the moment chunking lands — and it returns fluent, wrong Turkish rather than an error.
- Add a Turkish-correct casefold (I->ı, İ->i before .lower()) anywhere names are compared: LP names, counterparties, portfolio companies, fund codes. .casefold() does not do this and 'İŞ BANKASI' will not match 'iş bankası' without it.
- Deprioritise the ASCII tokenizer relative to the above. I tested my own assumption that it wrecks retrieval and it did not — recall@1 and precision@10 were unchanged on synthetic Turkish corpora because the corruption is symmetric. Fix it for legibility and future embedding work, not as an emergency.
- Keep the Decimal discipline already in config.py and extend it with an explicit ROUND_HALF_UP quantize at every money boundary. Python's round() is banker's rounding and round(2.675,2)=2.67 where Turkish accounting expects 2.68.
- The real-vs-nominal split already encoded in valuation_drift_real / valuation_drift_nominal is the right instinct for a 31.75% CPI environment and should govern every threshold in the system, not just valuation drift.
- Before any policy on what may leave the building, get the KVKK Article 9 transfer mechanism confirmed by Turkish counsel rather than from this report — I could not reach kvkk.gov.tr and have deliberately marked that entire area unverified recall.
- Resolve U-8 by having someone read the SPK weekly bulletin for the week of 23 July 2026 directly. A regulatory-change rule built on press coverage of a decision is worse than no rule, and it is currently the system's flagship example.
- When search budget is restored, re-run this leg with a strict priority order: Turkish OCR/extraction benchmarks first (nothing else is Turkey-specific and unguessable), then KVKK/EU AI Act primary text, then costs. The PE/MIT survey figures are already adequate at the confidence level they can support.

## Structured data

```json
[{"capability":"turkish_amount_parsing","evidence_of_value":"First-hand: float('1.500')=1.5 silently vs TR meaning 1500, a 1.00E+3x error; malformed-looking forms ('1.250.000,00','0,05') fail loudly with ValueError/InvalidOperation, so only the clean-looking case corrupts","failure_mode":"Silent 1000x understatement of a capital call, appraisal or NAV figure that passes all type checks","deterministic_or_model":"deterministic","fits_small_firm":"yes - single function, hours of work, highest value in the whole stack"},{"capability":"citation_span_verification","evidence_of_value":"First-hand: Turkish paragraph 263 chars NFC vs 278 NFD (5.7% drift); offsets from raw extractor output replayed against normalized store returned 'ğişim tablosu incelenmiştir' instead of 'özkaynak değişim tablosu'","failure_mode":"Provenance control returns fluent but wrong Turkish; reviewer spot-check does not catch it","deterministic_or_model":"deterministic","fits_small_firm":"yes - normalize once at ingest, derive all offsets from canonical text"},{"capability":"turkish_entity_name_matching","evidence_of_value":"First-hand: 'İSTANBUL'.lower()='i̇stanbul' (i + U+0307, 2 codepoints, != 'istanbul'); 'IŞIK'.lower()='işik' not 'ışık'; .casefold() identical and does not fix it","failure_mode":"LP, counterparty and portfolio-company joins silently under-match; duplicate records","deterministic_or_model":"deterministic","fits_small_firm":"yes - I->ı, İ->i before .lower()"},{"capability":"unicode_normalization_of_pdf_text","evidence_of_value":"First-hand: NFC/NFD forms of şirket, değer, İstanbul, güncel, çeyrek differ in codepoint count and fail == and set-membership; clean() converges them (True); NFKC also repairs ligature 'ﬁnansal'->'finansal'","failure_mode":"Exact-phrase filters and hash dedupe silently under-match Turkish documents","deterministic_or_model":"deterministic","fits_small_firm":"yes - already implemented in util/text.py, just needs to be the single ingest boundary"},{"capability":"money_arithmetic_nav_fees","evidence_of_value":"First-hand: 12 monthly 2% accruals on 1,250,000.00 TRY give float 24999.999999999996 vs Decimal 25000.00; round(2.675,2)=2.67 vs ROUND_HALF_UP 2.68; round() is banker's rounding","failure_mode":"Sub-cent drift accumulating into reconciliation breaks; rounding convention mismatch with TR accounting","deterministic_or_model":"deterministic","fits_small_firm":"yes - config.py already reads Decimal from strings for this reason"},{"capability":"tms29_real_vs_nominal_thresholds","evidence_of_value":"First-hand code read: config.py separates valuation_drift_real (0.05) from valuation_drift_nominal (0.25), noting a nominal rule at ~32% inflation 'would fire every month'","failure_mode":"Alert fatigue from inflation-driven nominal moves, or missed real impairment","deterministic_or_model":"deterministic","fits_small_firm":"yes - already encoded"},{"capability":"document_extraction_capital_calls_appraisals","evidence_of_value":"NOT ESTABLISHED THIS SESSION. Ledger FUNDADMIN-AI-2026 records the qualitative pattern that AI is strongest on document-heavy extraction, but its percentages are flagged vendor-sourced and low-confidence. No measured time-saving or field-level accuracy obtained","failure_mode":"Unknown for Turkish documents; the structural hazards above apply to whatever extractor is used","deterministic_or_model":"model_with_deterministic_validation","fits_small_firm":"probably - but unquantified; requires human-in-loop until a field-level accuracy is measured on real WAM documents"},{"capability":"turkish_ocr_accuracy","evidence_of_value":"NO EVIDENCE. aclanthology.org, arxiv.org, huggingface.co all blocked; zero CER or field-accuracy figures obtained","failure_mode":"Unknown - do not assume a rate","deterministic_or_model":"unknown","fits_small_firm":"unknown - must be measured on his own corpus before any commitment"},{"capability":"contract_side_letter_obligation_extraction","evidence_of_value":"NOT ESTABLISHED THIS SESSION. Document-shaped, so it sits in the category the ledger supports, but no measured evidence gathered","failure_mode":"Missed or hallucinated obligation; a false obligation is worse than none","deterministic_or_model":"model_with_deterministic_validation","fits_small_firm":"probably - requires every extracted obligation to carry a verifiable citation span, which depends on the offset fix"},{"capability":"regulatory_change_monitoring","evidence_of_value":"WEAK. The intended worked example (SPK decision 23 July 2026) is itself unconfirmed - press-sourced only, bulletin never retrieved, U-8 still open; spk.gov.tr and kap.org.tr blocked again this session","failure_mode":"A rule that fires on a misread of a decision is worse than no rule","deterministic_or_model":"model_for_detection_human_for_interpretation","fits_small_firm":"yes if every obligation carries a verify flag until confirmed at primary source"},{"capability":"lp_letter_board_pack_first_draft","evidence_of_value":"NOT ESTABLISHED THIS SESSION. No measured time-saving obtained","failure_mode":"Model asserting a number it computed rather than quoting one the deterministic core produced","deterministic_or_model":"model_for_prose_deterministic_for_every_number","fits_small_firm":"yes - lowest regulatory risk, numbers must be injected not generated"},{"capability":"reconciliation_bank_statements","evidence_of_value":"NOT ESTABLISHED THIS SESSION","failure_mode":"TR amount format hazard applies directly; a silent 1000x parse in a reconciliation would appear as a break of exactly 999x the true value","deterministic_or_model":"deterministic","fits_small_firm":"yes - matching logic is rules, not model"},{"capability":"audit_preparation_evidence_assembly","evidence_of_value":"NOT ESTABLISHED THIS SESSION. No evidence gathered on controls that make an LLM output admissible in an audited process","failure_mode":"Unverifiable provenance chain; citation offsets that resolve to the wrong substring would be discovered by an auditor, not by the system","deterministic_or_model":"deterministic_retrieval_with_model_summarisation","fits_small_firm":"yes - but depends entirely on the offset/normalization fix being correct"},{"capability":"portfolio_monitoring_dashboard","evidence_of_value":"EVIDENCE AGAINST. Ledger PE-AI-SURVEY-2026: 75% of PE managers rated AI ineffective for portfolio monitoring (secondary source, primary PDF not obtained)","failure_mode":"Builds the thing practitioners rank lowest","deterministic_or_model":"deterministic","fits_small_firm":"no - do not build as an AI capability"},{"capability":"deal_sourcing","evidence_of_value":"EVIDENCE AGAINST. Ledger PE-AI-SURVEY-2026: 64% rated AI ineffective for deal sourcing (secondary source)","failure_mode":"Highest-marketed, lowest-rated use case","deterministic_or_model":"n/a","fits_small_firm":"no"},{"capability":"annual_cost_of_stack_5_15_people","evidence_of_value":"NO EVIDENCE. No pricing, rate cards, benchmarks or overspend case studies reachable","failure_mode":"Any number quoted would be invented","deterministic_or_model":"n/a","fits_small_firm":"unknown - must be built bottom-up from real quotes"},{"capability":"kvkk_eu_ai_act_compliance_posture","evidence_of_value":"UNVERIFIED RECALL ONLY. kvkk.gov.tr, eur-lex.europa.eu, artificialintelligenceact.eu all blocked. Recalled pointers (KVKK Law 6698 Art. 9 cross-border transfer with 2024 standard-contract route; EU AI Act Art. 2 reaching third-country deployers where output is used in the Union) are named only to direct document retrieval","failure_mode":"Building a data-egress policy on recalled article numbers","deterministic_or_model":"n/a","fits_small_firm":"requires Turkish counsel, not a research report"}]
```

## Sources cited by the agent

- curl -sS $HTTPS_PROXY/__agentproxy/status — proxy state and 20 recorded blocked hosts, 2026-08-27T15:24Z
- WebSearch tool refusal: 'this session has used its web search budget (200 of 200 WebSearch calls)', 2026-08-27T15:24Z
- Domain reachability probe: arxiv.org, export.arxiv.org, en.wikipedia.org, eur-lex.europa.eu, aclanthology.org, huggingface.co, www.spk.gov.tr, kap.org.tr, www.resmigazete.gov.tr, openai.com, docs.anthropic.com all HTTP 000/403; api.github.com 200
- /home/user/claude/src/oodarag/util/text.py — ASCII _TOKEN_RE at line 17, normalize_unicode/clean
- /home/user/claude/src/oodarag/models.py:95-96 — char_start/char_end citation offset fields
- /home/user/claude/src/oodarag/config.py:31,134-150,436 — Decimal-from-string discipline, real vs nominal drift thresholds
- /tmp/claude-0/-home-user/e00ed53e-d4d3-5430-8d55-f3fd47147994/scratchpad/tr_eval.py — sections A-E: tokenizer corruption, dotless-i, TR number parsing, NFKC
- /tmp/claude-0/-home-user/e00ed53e-d4d3-5430-8d55-f3fd47147994/scratchpad/tr_eval2.py — sections F-I: collisions, NFD forms, float vs Decimal, silent 1000x
- /tmp/claude-0/-home-user/e00ed53e-d4d3-5430-8d55-f3fd47147994/scratchpad/tr_eval3.py — section J: BM25 recall@1 current vs Unicode-aware
- /tmp/claude-0/-home-user/e00ed53e-d4d3-5430-8d55-f3fd47147994/scratchpad/tr_eval4.py — section K: 400-doc scale test, precision@10, vocabulary size
- /tmp/claude-0/-home-user/e00ed53e-d4d3-5430-8d55-f3fd47147994/scratchpad/tr_eval5.py — sections L-M: citation span drift, clean() round-trip convergence
- /home/user/claude/provenance/sources.yaml — [src:FUNDADMIN-AI-2026], [src:PE-AI-SURVEY-2026], [src:MIT-PILOT-FAILURE-2026], [src:EQT-MOTHERBRAIN-2026] and their low-confidence notes
- /home/user/claude/provenance/unknowns.md — U-7 (WAM fund data), U-8 (SPK decision text), U-9 (whether the system is wanted)
- /home/user/claude/docs/research/01-field-evidence.md — the pre-existing evidence base this leg was asked to extend
- /home/user/claude/CLAUDE.md — anti-fabrication doctrine governing how these findings are recorded