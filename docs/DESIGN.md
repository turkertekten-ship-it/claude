# The system

A decision-support system for the CFO and board member of a small, regulated,
Turkish fund manager. Designed against the evidence in `docs/research/`, not
against what this kind of system is usually sold as.

Source tags resolve to `provenance/sources.yaml`. Claims without a tag are
design argument, not fact. Everything the delegated research produced is marked
second-hand in `docs/research/` and is used here as a lead, not a finding.

---

## 1. The one thing

**It watches the obligations and the numbers that keep four fund licences
clean, and it makes every figure it emits traceable to the source and honest
about inflation.** It is a control system, not an investment system.

It deliberately does **not** do three things.

**No deal sourcing.** Managers rate AI ineffective there by 64%
[src:PE-AI-SURVEY-2026], and the arithmetic from the canonical success is worse
than the survey: the delegated research reports EQT's Motherbrain took ten
years and grew from three to about twenty engineers to attribute roughly
fifteen investments [src:DELEGATED-RECON-2026-08-27]. At WAM's scale that is a
rounding error against one partner's phone.

**No portfolio-monitoring dashboard.** Rated ineffective by 75%
[src:PE-AI-SURVEY-2026]. Dashboards are the canonical thing that gets built,
demoed, and then stops being opened in week three.

**No language model anywhere near a number.** Models read documents and draft
prose. Deterministic code owns money, dates, obligations, NAV and every ratio.
This is the fund-administration consensus — AI as a supporting layer over a
numerical core whose controls do the real work [src:FUNDADMIN-AI-2026] — and it
is the boundary an auditor can actually inspect.

### Why build rather than buy

The strongest general evidence says don't: external vendor tools succeed about
twice as often as internal builds, and roughly 95% of pilots produce no
measurable P&L impact [src:MIT-PILOT-FAILURE-2026]. That evidence is taken
seriously here, and it wins almost everywhere — fund accounting, custody,
document storage and audit should all be bought.

It loses in exactly one place, for a reason that is specific to this firm.
Tebliğ VII-128.10 requires a capital-markets institution to keep **both its
primary and its secondary information systems inside Turkey**
[src:SPK-DATA-RESIDENCY-VII-128-10]. If that binds a portföy yönetim şirketi,
the US-hosted fund-ops stack cannot be the system of record, and the vendor
finding does not transfer because the vendors are not deployable. Add that no
vendor sells SPK obligation tracking with TÜFE restatement in Turkish, and the
buildable surface narrows to something one numerate person can own.

**This is the load-bearing assumption of the whole design, and it is not
settled.** It rests on legal commentary rather than the SPK's own text, and is
registered as AIR-4. If counsel reads VII-128.10 and says it binds narrowly or
not at all, a meaningful part of this document should be replaced by a
purchase order. That is the honest position, and it is the first question to
resolve.

---

## 2. What OODA means here, literally

| Phase | Concretely | Artefact |
|---|---|---|
| **Observe** | Poll Resmî Gazete, SPK bulletins, TSPB circulars, and KAP filtered to `VPG, VBR, VBI, VIK, WQQ`; pull TÜFE and TCMB FX and policy rate; read the obligation calendar's clock | New rows in the document store, new points in the series store, a delta per connector |
| **Orient** | Chunk and index the new documents with verified provenance; restate every TRY figure to a common period; compute the real-terms twin of every nominal number | An index that can cite, and a paired (nominal, real) view of every figure |
| **Decide** | Run the rule set. Deterministic predicates over typed state. No model involved | A list of Actions, each naming the rule that fired and the facts that satisfied it |
| **Act** | Draft — never send. Render the brief, the alert, the filing checklist, the LP note | Markdown on disk, plus an append-only JSONL decision journal |

The journal is the point of the whole loop. "The system said so" is not an
answer to an inspector; "rule `OBL-FILE-DUE` fired on 2026-09-14 because
obligation `SPK-CAPADQ-MONTHLY` was 4 business days from due and unsatisfied,
evidence at this URI, hash `abc…`" is.

---

## 3. Architecture, and the one boundary that matters

```
  Observe ────────────────────────────────────────────────────────────┐
    ingest/regulatory.py   SPK · KAP · Resmî Gazete · TSPB            │
    ingest/marketdata.py   TÜİK TÜFE · TCMB FX, policy rate           │
    redact.py              TCKN / VKN / IBAN scrubbed AT the boundary  │
                                                                       │
  Orient ──────────────────────────────────────────────────────────┐  │
    chunk/ embed/ index/ retrieve/    ← MODEL MAY TOUCH THIS       │  │
    domain/inflation.py               ← DETERMINISTIC ONLY         │  │
                                                                   │  │
  ═══════════════════ THE BOUNDARY ══════════════════════════════  │  │
                                                                   │  │
  Decide ──────────────────────────────────────────────────────┐  │  │
    domain/money.py  valuation.py  obligations.py   DETERMINISTIC │  │
    ooda/policy.py   ooda/rules.py                  DETERMINISTIC │  │
                                                                 │  │  │
  Act ───────────────────────────────────────────────────────┐  │  │  │
    answer/verify.py   citations checked against sources     │  │  │  │
    ooda/act.py        brief · alert · escalate — never send │  │  │  │
    decision journal (JSONL, append-only)                    │  │  │  │
```

Above the boundary a model may read a PDF, pull a field out of an appraisal
report, and draft a paragraph. Below it, nothing but Python arithmetic on
`Decimal` touches a lira. Between them sits one gate: **an extracted value is a
proposal until a human or a deterministic reconciliation accepts it.**

That gate exists because purpose-built legal retrieval systems still
hallucinate. The delegated research reports Stanford measuring Lexis+ AI at
about 17% and Westlaw's AI-Assisted Research at about 33%
[src:DELEGATED-RECON-2026-08-27]. Those are vendors who did nothing but this.
Anything built here will be worse, so the design assumes extraction is wrong
some of the time and makes that survivable rather than pretending otherwise.

Citations are therefore **verified, not decorative**: `answer/verify.py` checks
that the quoted span actually occurs in the retrieved chunk it claims, drops
the ones that do not, and converts an answer with no surviving citation into an
abstention. An abstention is a good outcome. A confident wrong number in a
report to a qualified investor is not.

---

## 4. The correctness invariant

If this system does only one thing correctly, it should be this.

**Fund figures are nominal. Management-company figures are TMS 29 restated.
They may never be added, compared, or charted together without a flag.**

SPK decision 16.02.2024 no. 11/255 exempts investment funds from inflation
accounting, while other capital-markets entities — including the management
company — applied TMS 29 from the period ending 31.12.2023
[src:SPK-FUND-TMS29-EXEMPTION]. At 31.75% CPI [src:TCMB-MACRO-2026-08] a
consolidated view that mixes the two is not slightly off; it is wrong by
roughly a third per year of divergence, in the flattering direction.

So every monetary value in the system carries its **restatement basis** and the
**period** it is stated in. Adding two amounts on different bases raises. There
is no default and no inference — because whether the fund exemption still holds
in 2026 was not established (AIR-5), and a system that guesses that would be
guessing the invariant.

The second invariant is smaller and just as sharp. **A nominal return is not a
return.** At 32% inflation, a 40% nominal IRR is about 6% real —
`(1.40/1.32) − 1` — and the naive subtraction that gives 8% is wrong by a third
of the answer. Every metric has a `real_` twin and the brief always prints
both.

---

## 5. The policy engine

Rules are Python predicates over typed state. They are boring on purpose: an
auditor must be able to read one and say whether it is right.

Each carries a materiality threshold and a cooldown, because the failure mode
of an alerting system is not missing an event — it is firing until nobody reads
it, and then missing every event. Rules marked **digest** never interrupt; they
accumulate into the weekly brief.

| id | fires when | severity | sign-off |
|---|---|---|---|
| `OBL-DUE-SOON` | an unsatisfied obligation is inside the horizon (21d) | medium · digest | — |
| `OBL-ESCALATE` | unsatisfied and inside 5 business days | high | named owner |
| `OBL-OVERDUE` | past due and unsatisfied | critical | named owner |
| `OBL-UNVERIFIED` | an obligation seeded from low-confidence research is about to drive an alert | high | counsel |
| `NAV-DRIFT-REAL` | fund unit value moves > 5% in real terms period-on-period | medium | — |
| `NAV-DRIFT-NOMINAL` | > 25% nominal — usually a data error, not a valuation event | high | fund müdürü |
| `NAV-BASIS-MIX` | two amounts on different restatement bases reach one computation | critical | — |
| `NAV-STALE` | no unit value published for a fund within its own announced cadence | high | — |
| `APPRAISAL-STALE` | a GYF asset's appraisal is older than 365 days | high | — |
| `APPRAISAL-MISSING` | a GYF holding has no appraisal on file at all | critical | — |
| `VAL-SOURCE-CHANGED` | an exchange-traded GYF/GSYF unit's valuation input is not the founder's last announced value | critical | — |
| `FX-MOVE` | TRY/USD moves > 3% in a day | low · digest | — |
| `REAL-RETURN-NEGATIVE` | a fund's trailing real return turns negative while nominal stays positive | medium | — |
| `CPI-STALE` | TÜFE series has no point for the closed month | high | — |
| `CAPADQ-FILING` | monthly capital-adequacy filing window opens (5 business days) | high | named owner |
| `EQUITY-FLOOR` | management-company equity approaches its AUM-tiered minimum | critical | board |
| `LP-QUALIFICATION` | a pipeline contact's qualified-investor status is unrecorded or post-dates the 18.12.2025 threshold change | medium · digest | — |
| `REG-CHANGE` | a watched keyword appears in Resmî Gazete or an SPK bulletin | high | compliance |
| `REG-DEADLINE-SHORT` | a detected change carries a compliance date inside 30 days | critical | compliance |
| `IDX-STALE` | a corpus has not refreshed in 7 days — retrieval is answering from a stale world | medium | — |
| `CITE-COVERAGE-LOW` | answers fall below 0.6 verified-citation coverage | high | — |
| `CONNECTOR-DOWN` | one source fails 3 runs running | medium | — |
| `MODEL-CHANGED` | the embedding model or a prompt changed without the eval set being re-run | high | — |

That last rule is not decoration. The delegated research reports Two Sigma
paying roughly $90m in a January 2025 SEC settlement over a failure of model
*change control* rather than model quality
[src:DELEGATED-RECON-2026-08-27]. A model inventory, a frozen eval set re-run on
every change, and validation by someone who did not build it is a minimum
viable SR 11-7 — and it costs a spreadsheet and a test file.

`REG-DEADLINE-SHORT` earns its place from a live example: the SPK's 23 July
2026 valuation decision gave portfolio managers until 31 July to comply
[src:SPK-VALUATION-2026-07-23]. Eight days. No quarterly review catches that.

---

## 6. The domain model

Deterministic, `Decimal`, and provenance-carrying throughout.

- **Money** — amount, currency, **restatement basis**, **stated period**.
  Refuses to mix currencies or bases. Parses Turkish formatting, where
  `1.234.567,89` is one and a quarter million. `float("1.500")` is `1.5`, a
  1000× error that raises nothing and sits directly in the path of capital-call
  and appraisal figures — the delegated research found exactly that class of
  bug live in this repository's own code
  [src:DELEGATED-RECON-2026-08-27].
- **PriceIndex** — the TÜFE series. Refuses to interpolate a missing month
  rather than inventing one.
- **Fund** — `code`, `kind`, and nothing else the firm has not confirmed.
  `FundRef` has no `size` or `aum` field, because none was obtainable (AIR-1) and
  there should be nowhere to put a guess.
- **Obligation** — authority, cadence, **due rule**, owner, severity, evidence
  URI, and a `verify` flag carried through from low-confidence research. An
  obligation seeded from a press report is not presented as a legal deadline.
- **Appraisal / NavPoint** — valuer identity, method, date, expiry, and the
  resolution that approved it. Built for external reliance: since 31 July 2026
  other institutions must book WAM's exchange-traded units at WAM's own last
  announced value, which makes that number the highest-consequence figure the
  firm produces.

Metrics: `moic`, `dpi`, `rvpi`, `tvpi`, `xirr`, `nav_per_unit`, fee drag,
carried interest with hurdle and catch-up — each with a `real_` variant that
restates every cashflow to a common period before computing.

Turkish business-day arithmetic matters more than it looks: "within 6 business
days of month end" has to skip weekends and Turkish public holidays, and the
religious holidays are lunar and must be refreshed annually. A calendar that
silently drifts is worse than no calendar.

---

## 7. Monday morning

One command, one page.

```
$ ooda loop --cycles 1 && ooda brief
```

**The brief.** What changed at the regulator since Friday, with a citation per
line. What is due in the next 21 days, by owner, with the upstream inputs each
deadline actually depends on — the binding constraint is almost never the
filing date, it is the appraisal that has to exist first. Every fund's unit
value, nominal and real, with the drift flag. TÜFE and TRY/USD with what they
did to the real numbers. Anything the system refused to answer, and why.

**What it replaces.** The hand-maintained fund trackers — someone is typing
monthly return series into a grid in 2026 [src:DRIVE-WORKFILES-2026-08-27], and
that is the single most concrete piece of evidence about where the time goes.
The mental compliance calendar. The tab-by-tab reconstruction of what a number
meant three months ago.

**Weekly:** the digest rules, the eval report (did last week's change make
retrieval better or worse), and the provenance report naming every configured
fact nobody has confirmed.

**Quarterly:** the filing pack checklist with evidence links, and the real-terms
performance view beside the regulatory nominal one — never merged.

---

## 8. Sequence, and when to stop

Ordered by what fails cheapest.

1. **The deterministic core, alone.** Money with Turkish parsing, TÜFE
   restatement, the obligation calendar, the rules. No retrieval, no model. If
   this is all that ever ships it is still worth the effort, because it is the
   half that touches the numbers.
2. **The regulatory watch.** Resmî Gazete, SPK bulletins, KAP on the real
   watchlist. Read-only, no extraction into any computation yet.
3. **Extraction, gated.** Appraisal reports and filings, into *proposals* a
   human accepts. Never straight into a NAV.
4. **The Pitch Challenge corpus** — 498 pitches, 395 startups
   [src:DRIVE-WORKFILES-2026-08-27] — as a retrieval corpus and CRM, not a
   predictor. The delegated research notes Hone Capital needed roughly 30,000
   deals to isolate about twenty predictive features
   [src:DELEGATED-RECON-2026-08-27]; 395 companies will fit noise. "Who pitched
   in this space, who was in the room, what happened since" is the useful
   question, and it needs retrieval, not a model.

**Tripwires — stop if any of these is true.**

- Counsel reads VII-128.10 and it does not bind as assumed (AIR-4). Buy instead.
- The brief goes unopened for three consecutive weeks. It is not useful; find
  out what he actually opens.
- Any rule fires more than twice a week without a human acting on it. Raise its
  threshold or demote it to digest. Alert fatigue is how this dies.
- Verified-citation coverage sits below 0.6 on the eval set. Retrieval is not
  grounding; ship the deterministic half alone.
- Anyone starts describing this to an LP as an AI capability. The delegated
  research notes the SEC fining two advisers $400,000 combined in March 2024
  purely for describing AI they did not have
  [src:DELEGATED-RECON-2026-08-27]. Say what it is: a compliance calendar with a
  citation trail.

---

## 9. Honest limits

This cannot value an illiquid asset, and should never appear to. It flags a
stale appraisal; a licensed valuer produces the number.

It cannot tell you a filing is correct — only that it is due, and what fed it.

Its extraction will be wrong sometimes. Every design decision above assumes
that: verified citations, abstention, the proposal gate, the human sign-off
column. If those are removed to make it faster, it becomes a liability.

Its regulatory knowledge is a snapshot read through commentary, from a
container where the SPK's and KAP's own sites were unreachable
[src:EGRESS-BLOCKED-WAM-KAP-2026-08-27]. Every article number and business-day
count in the seeded calendar carries a `verify` flag until a human confirms the
tebliğ text. The delegated research was explicit that these are second-hand
[src:DELEGATED-RECON-2026-08-27], and the calendar is built to say so rather
than to look authoritative.

And the largest limit: **nobody has asked him what his week actually contains**
(AIR-3). This is designed from a public career record, a shareholder table and a
file listing. The adoption sequence is a proposal, not an agreed plan, and the
first conversation should be about what he already runs and what he has already
tried and abandoned — because the research is unambiguous that the systems that
fail are the ones designed for a workflow nobody checked.
