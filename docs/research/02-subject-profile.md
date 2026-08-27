---
provenance: enforced
---

# The subject, and the firm

> Framing, not a claim: this is the profile the system is designed around,
> written because a system tailored to a person needs that person written down
> first. Every line is sourced or it is not here. The gaps are large and are
> named as gaps rather than smoothed over — the firm's own website and its
> primary regulatory filing record were both unreachable from this container.

## Observed — the person

- Türker Tekten has been **CFO and Board Member of WAM Asset & Portfolio Management since 2022**. [src:SUBJECT-IDENTITY-2026-08-27]
- Immediately prior he was **Chief Financial Officer and Partner at Actera Group, from 2007 to 2021** — fourteen years. [src:SUBJECT-IDENTITY-2026-08-27]
- Before that: **CAO and CFO at Morgan Stanley in 2006–2007**; **COO and CFO at SBA Hong Kong Ltd, 2003–2006**; **Assistant Vice President at JPMorgan Chase Bank, 1995–2002**; **Internal Auditor at Türkiye İş Bankası, 1992–1995**. [src:SUBJECT-IDENTITY-2026-08-27]
- He holds an undergraduate degree from **Bilkent University, 1992**. [src:SUBJECT-IDENTITY-2026-08-27]
- The same profile records **board and audit committee memberships at several companies**, without enumerating them. [src:SUBJECT-IDENTITY-2026-08-27]

> Reading: this is a thirty-four-year career whose spine is control, not
> origination — internal audit, then a controller-side track through two global
> banks, then fourteen years owning the finance function of a large private
> equity firm. He is not a novice being sold a dashboard. He has personally
> signed off the numbers this system would touch, which raises the bar on
> auditability and lowers it on hand-holding.

## Observed — the firm

- The legal entity is **WAM Gayrimenkul ve Girişim Sermayesi Portföy Yönetimi A.Ş.**, recorded in KAP with an Istanbul, Teşvikiye address. [src:WAM-FIRM-2026-08-27]
- It was **established in 2022** and provides portfolio management services to institutional investors through the **venture capital investment funds (GSYF) and real estate investment funds (GYF)** it manages. [src:WAM-FIRM-2026-08-27]
- GSYF participation is restricted to **qualified investors (nitelikli yatırımcı)**; investors without that status cannot invest. [src:WAM-FIRM-2026-08-27]
- Neither `www.wamportfoy.com` nor `kap.org.tr` could be read: both returned **EGRESS_BLOCKED** from the network proxy. [src:EGRESS-BLOCKED-WAM-KAP-2026-08-27]

> The firm's fund names, fund sizes, portfolio holdings, AUM, shareholders and
> the rest of its board are therefore **unestablished**. That is registered as
> U-7, and it has a hard consequence: every fund-level number produced by the
> system built on this branch is a worked example over seeded data. Nothing may
> present it as a reading of the real book.

## Observed — what the working files show

- Four spreadsheets tracking **HCP Quant, HCP Focus, HCP Black and HCP Bricks** monthly returns, allocation and return history — Finnish-titled (*Kuukausituotot, Allokaatio ja Tuottohistoria*) — three of them modified within a day of capture. [src:DRIVE-WORKFILES-2026-08-27]
- The HCP Quant sheet carries a monthly `Ex date / Period return / Indexed base value` series running to **26.08.2026**, i.e. maintained to the day. [src:DRIVE-WORKFILES-2026-08-27]
- A **Pitch Challenge** tracker recording **nine events from March 2022 to September 2025** — İstanbul ×5, Ankara ×2, İzmir ×2 — with **498 pitches delivered** and **395 unique startups**. [src:DRIVE-WORKFILES-2026-08-27]
- Its collaborator list names **Alesta Elektronik Teknoloji Yatırım A.Ş., APY Ventures, Girişim'23, Gdz Elektrik, Karşıyaka Belediyesi Kolektif Girişimcilik Merkezi, TEB, Moka and İş Bankası**. [src:DRIVE-WORKFILES-2026-08-27]
- An investor pipeline sheet, `To-Do Potential investors_Master_080521`, tracking named contacts at **Yıldız Holding, Anadolu Holding, Eko Group, Tekfen and Arçelik** with an owner, an action and a status per row. [src:DRIVE-WORKFILES-2026-08-27]
- Course materials from 2023–24 in **Bilişim Sistemleri (information systems), Karar Teorisi (decision theory) and Bilgisayar Ağları (computer networks)**. [src:DRIVE-WORKFILES-2026-08-27]

> Reading, and the surprise. Two things here were not expected walking in.
> First, the pipeline sheet is from **May 2021** and still sits among the
> recent files: a fundraising process tracked in a spreadsheet, with follow-up
> state that a spreadsheet cannot chase. Second, and more telling, the fund
> trackers are **hand-maintained to the current day**. Someone is typing
> monthly return series into a grid by hand, in 2026. That is the single most
> concrete piece of evidence in this profile about where his time goes, and it
> matches the fund-administration finding that manual data entry remains the
> top operational headache. [src:FUNDADMIN-AI-2026]
>
> The coursework is the other signal. A CFO of thirty-plus years taking
> information systems and decision theory is not being sold on this; he is
> already trying to build the capability himself.

## Observed — the operating environment

- Turkish CPI inflation was **31.75% year-on-year in July 2026**, down from 32.11% in June, with the TCMB's own year-end 2026 projection revised **up** to 26%. [src:TCMB-MACRO-2026-08]
- The TCMB policy rate stands at **37%**, with overnight lending at 40% and overnight borrowing at 35.5%. [src:TCMB-MACRO-2026-08]
- The lira reached a **record low of about 47.2 per USD** in July 2026. [src:TCMB-MACRO-2026-08]
- On **23 July 2026** the SPK decided that exchange-traded GYF and GSYF participation units held by investment funds must be valued at **the founder's last announced unit value rather than the exchange price**, with portfolio management companies required to comply by **31 July 2026** — an eight-day window. [src:SPK-VALUATION-2026-07-23]

> The macro numbers are not background colour, they are a design constraint. At
> 31.75% inflation a nominal return of 30% is a real loss, and a report that
> shows only the nominal figure is not neutral — it is wrong in a direction
> that flatters. Every figure this system emits therefore carries a real-terms
> twin.
>
> The SPK decision is the other constraint, and it is the sharper one. Eight
> days from publication to compliance is not a timescale a quarterly review
> catches. It is the worked example for why the Observe phase watches the
> regulator continuously. Its exact scope is press-reported rather than read
> from the bulletin, which is registered as U-8.

## What was not established

Named in full in `provenance/unknowns.md`: what WAM actually manages (U-7), the
operative text of the SPK decision (U-8), and whether a system of this shape is
wanted at all (U-9). The third is the important one. Everything here is
inference from a public career record, a firm profile and a file listing.
Nobody has asked him what his week contains, what he already runs, or what he
has tried and abandoned.
