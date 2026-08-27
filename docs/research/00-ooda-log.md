---
provenance: enforced
---

# Loop log — session `claude/ai-system-research-3jpwda`

> Framing, not a claim: the doctrine asks each loop to record what was actually
> looked at, what the reading was, where reality diverged from expectation, and
> what was decided. This is that record for the request "research me and where
> I work, what similar firms do, how the successful ones use and implement AI,
> and build me the perfect system tailored for me". The surprises are the point
> of the file; a loop with no surprise usually means Observe was skipped.

---

## Loop 1 — Who is this, and what is already here

### Observed

- The account owner is Türker Tekten: CFO and Board Member of WAM Asset & Portfolio Management since 2022, previously CFO and Partner at Actera Group 2007–2021, with Morgan Stanley, SBA Hong Kong, JPMorgan and Türkiye İş Bankası before that, and a 1992 Bilkent degree. [src:SUBJECT-IDENTITY-2026-08-27]
- The firm is WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi A.Ş., Istanbul/Teşvikiye, established 2022, managing GSYF and GYF vehicles for qualified investors. [src:WAM-FIRM-2026-08-27]
- Both `www.wamportfoy.com` and `kap.org.tr` returned EGRESS_BLOCKED. [src:EGRESS-BLOCKED-WAM-KAP-2026-08-27]
- The working branch held 16 Python files and 2,583 lines of an OODA-shaped RAG pipeline — HTTP, hashing, text, logging, models, three connectors, three scrapers — with no tests directory, and a Makefile and pyproject already declaring `demo`, `index`, `query`, `eval`, `loop` and an `ooda` console script against modules that did not exist. [src:OODARAG-PRIOR-STATE-2026-08-27]
- Five branches exist on the `claude` remote and one on `claude-ai`; this branch shares no ancestry with any of them. [src:REPO-BRANCHES-2026-08-27]

### Orient — the surprise

Two, and the second reframed the whole session.

The first was the **scaffolding without a building**: a Makefile and a console
script pointing at `oodarag.cli`, `oodarag.eval`, and an OODA loop, none of
which existed. The prior session had built the hard, unglamorous half — HTTP
retries, robots, boilerplate stripping, content-hash incrementality — and
declared the interface for the rest. That is an unusually good place to arrive.

The second was **finding a doctrine already in force**. A sibling branch
carried a `CLAUDE.md` mandating that every factual claim carry a `[src:]` tag
resolving to a ledger, a `provenance/unknowns.md` for what could not be
established, and a `tools/verify_provenance.py` that fails the build on an
unsourced claim. Walking in, the expectation was a greenfield research task.
What was actually there was a house style that treats *unsourced assertion as
a defect*. That is not decoration on this particular request — a system for a
fund CFO lives or dies on whether its outputs are checkable — so it became the
constraint the rest of the work was written against rather than something to
work around.

### Decide

Adopt the doctrine on this branch before writing any research down, and make
every claim carry a source. Falsifier: if `python3 tools/verify_provenance.py`
cannot be made to pass over the research documents without weakening the guard,
the doctrine is unworkable here and should be argued with rather than adopted.

### Act

Doctrine, ledger and verifier taken across with `git checkout <ref> --` (the
branches cannot be merged). Thirteen ledger entries added with verbatim
captures. The guard passes over seven files and forty sources — and it rejected
two drafts on the way, which is the only evidence that it works.
[src:REPO-BRANCHES-2026-08-27]

---

## Loop 2 — What the field actually knows

### Observed

- Managers rate AI ineffective for deal sourcing (64%) and portfolio monitoring (75%); due diligence has the highest integration at 31%. [src:PE-AI-SURVEY-2026]
- Roughly 95% of enterprise GenAI pilots produce no measurable P&L impact, with data readiness the root cause discovered latest, and vendor tools succeeding about twice as often as internal builds. [src:MIT-PILOT-FAILURE-2026]
- The fund-administration pattern is that AI is strongest on document-heavy work and only a supporting layer over the numerical core. [src:FUNDADMIN-AI-2026]
- The canonical success, EQT's Motherbrain, is a programme begun in 2016 with an embedded engineering team, described by EQT as amplifying rather than replacing human judgement. [src:EQT-MOTHERBRAIN-2026]

### Orient — the surprise

The expectation walking in was that the evidence would be mushy and
directionless. It is not. It is **sharply negative in exactly the places this
kind of system is usually sold**, and the two rejected use cases — deal sourcing
and portfolio monitoring — are precisely the two a generic "AI for private
equity" build would have led with.

The genuinely uncomfortable finding is the vendor one: external tools succeed
about twice as often as internal builds. Recorded rather than dropped, because
it argues against this entire exercise. The narrow answer is that no vendor
sells a Turkish-language SPK obligation monitor with TMS 29 restatement, and
where a vendor *does* cover the job — fund accounting, custody, audit — the
evidence says buy it and this system should not compete.

### Decide

Design against the evidence rather than the pitch: the model reads documents
and drafts language; deterministic code owns money, dates, obligations and NAV.
Falsifier: if the eval harness shows retrieval cannot reliably ground answers
in Turkish regulatory text, the document half is unfounded too and only the
deterministic half should ship.

### Act

`docs/research/01-field-evidence.md`, sourced throughout, with the vendor
finding and the low-confidence vendor percentages both marked rather than
smoothed. Four research lanes and a code fleet dispatched against it.

---

## Loop 3 — Who he actually is inside that firm

### Observed

- WAM Portföy's paid-in capital is 30,000,000 TRY against a 75,000,000 TRY ceiling, and its shareholders are Mehmet İlhan Gülay 49%, İhsan Gülay 24.5%, Mehmet Gülay 24.5%, Can İkinci 1% and Türker Tekten 1%. [src:WAM-OWNERSHIP-2026-08-27]
- The firm discloses under company code VPG and manages at least four funds: VBR, VBI, VIK and WQQ. [src:WAM-FUND-CODES-2026-08-27]
- His HCP fund trackers carry monthly return series maintained to within a day of capture, and a fundraising pipeline from May 2021 still sits among his recent files. [src:DRIVE-WORKFILES-2026-08-27]
- A delegated agent reported all of the above plus much more, from search snippets only, having found every page fetch blocked. [src:SUBAGENT-PROFILE-2026-08-27]

### Orient — the surprise

**He is not a salaried CFO.** He holds 1% of the equity, matched exactly by the
General Manager's 1%, inside a firm 98% held by one family. The working
assumption up to this point had been the ordinary one — a hired finance chief
who needs a system that demonstrates he did his job. That is the wrong product.
An owner-operator with a board seat needs something that protects the licence
and the family's capital, and that lets two professional managers run four
regulated funds without a back office.

The smaller surprise is more actionable: the fund trackers are **hand-maintained
to the current day**. Someone is typing monthly return series into a grid in
2026. That is the most concrete available evidence about where his time goes,
and it matches the field finding that manual entry remains the bottleneck.
[src:FUNDADMIN-AI-2026]

A third thing worth recording as a caution rather than a finding: the delegated
agent's report was excellent and almost entirely unverifiable — every page
fetch it attempted was blocked, so a long, confident document rested on search
snippets. It labelled its own confidence honestly, which is the only reason it
was usable.

### Decide

Re-run the two load-bearing claims first-hand before writing them down, per the
doctrine that a subagent's report is second-hand. Falsifier: if the independent
search returns a different ownership split, the agent's whole report is suspect
and none of it may be used.

### Act

Re-run first-hand. The independent search returned the same split *with* the
underlying lira amounts the agent's version lacked, so both are recorded as
first-hand under their own ids and the agent's report is kept separately as
second-hand. One correction issued against this session's own earlier framing:
the Pitch Challenge series is reported to be run by Geometry Venture
Development, not by him; what is established is that he keeps a tracker of it.
[src:PITCH-CHALLENGE-ORGANISER-2026-08-27]

Then `src/oodarag/config.py`: the firm as data, every field graded SOURCED,
ASSUMED or OWNER, with a report that names its own unconfirmed fields, and a
`FundRef` that has nowhere to put a fund size because no fund size was
obtainable.

---

## Still open

U-7 (what WAM actually manages), U-8 (the operative text of the 23 July 2026
SPK decision) and U-9 (whether a system of this shape is wanted at all) are
unresolved and registered. The third is the one that matters: everything here
is inference from a public record and a file listing, and nobody has asked him
what his week contains or what he has already tried and abandoned.
