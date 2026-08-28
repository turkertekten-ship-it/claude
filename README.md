# oodarag

An OODA loop over a Turkish fund manager's obligations and numbers, running on
the Python standard library alone.

```
Observe   ->   Orient      ->   Decide      ->   Act
SPK · KAP      chunk/index      rules, not       brief · alert · escalate
Resmî Gazete   restate to       a model          (drafted, never sent)
TÜFE · TCMB    real terms
```

## What this is for

It watches the obligations and the numbers that keep four fund licences clean,
and makes every figure it emits traceable to its source and honest about
inflation. It is a control system for a CFO, not an investment system.

The full argument is in **[docs/DESIGN.md](docs/DESIGN.md)**; the evidence it
was designed against is in [docs/research/](docs/research/). The short version
is that the industry's own surveys rate AI ineffective for deal sourcing (64%)
and portfolio monitoring (75%) — the two things it is usually sold as — and
effective on document-heavy work, so this builds the second and refuses the
first.

## What it deliberately does not do

- **No deal sourcing.** EQT's Motherbrain took ten years and roughly twenty
  engineers to attribute about fifteen investments. At this scale that is a
  rounding error against one partner's phone.
- **No monitoring dashboard.** The thing that gets built, demoed, and stops
  being opened in week three.
- **No language model near a number.** Models read documents and draft prose.
  Deterministic code owns money, dates, obligations and NAV.
- **Nothing is sent.** Every executor writes to disk. Drafting is what a system
  can be trusted with; filing is a decision with a person's name on it.

## The two invariants

**Fund figures are nominal; management-company figures are TMS 29 restated.**
SPK exempts investment funds from inflation accounting while the manager itself
applies it, so the two are different money. `Money` refuses to add them.

**A nominal return is not a return.** At 32% inflation a 40% nominal IRR is
about 6% real. Every metric has a `real_` twin, and the brief prints both.

## Try it

```bash
make demo        # end to end, no network, no API key
make test        # 349 tests, stdlib unittest
```

```bash
PYTHONPATH=src python3 -m oodarag.cli rules        # every rule, and why its threshold is there
PYTHONPATH=src python3 -m oodarag.cli provenance   # which configured facts nobody has confirmed
PYTHONPATH=src python3 -m oodarag.cli obligations  # the calendar, unverified entries marked
PYTHONPATH=src python3 -m oodarag.cli brief        # the Monday-morning page
PYTHONPATH=src python3 -m oodarag.cli eval         # score retrieval against 20 goldens
```

Exit codes are the house rule: `0` clean, `1` findings, `2` could not run. The
demo exits `1` because it finds things.

## Built, and not built

The build ran as a thirteen-agent workflow that hit a session limit with seven
agents unrun. What exists is what exists:

| | |
|---|---|
| `util/`, `models`, `ingest/{base,web,github}`, `scrape/` | prior session |
| `chunk/`, `embed/`, `index/`, `retrieve/` | built, 169 tests |
| `config.py` — the firm as graded data | built, 28 tests |
| `domain/` — money, inflation, obligations, valuation | built, 57 tests |
| `ooda/` — signals, policy, 17 rules, act | built, 29 tests |
| `redact.py`, `answer/` — verified citations, three abstention guards | built, 40 tests |
| `eval/` — metrics, harness, 20 goldens, regression baseline | built |
| `cli.py` — demo, index, query, loop, brief, eval, rules, provenance, obligations | built |
| `ingest/regulatory.py`, `ingest/marketdata.py` | built, 26 tests — **never run against a real host** |

**Measured, not asserted.** `ooda eval` scores 16/20 on the golden set:
recall@5 0.66, MRR 0.46, verified-citation coverage 0.72, abstention rate 0.10.
The first run scored an abstention rate of **0.00** — it answered all four
unanswerable questions — which is the defect those cases exist to catch.

Four cases are red and documented rather than tuned away. Two are the hard case
where the corpus discusses the subject but not the fact asked for; no lexical
signal separates those, and measuring showed the obvious candidates score real
answerable questions *lower* than the unanswerable ones. The other two are a
property of a self-documenting corpus: the words "verify", "fabrication" and
"doctrine" saturate it, so a question about the rule retrieves commentary about
the rule. That one cost a case when the loop log was committed — a 17/20 became
16/20 with no code change. It is recorded rather than baselined away, because
re-saving a baseline to make a drop disappear is exactly what the harness exists
to prevent.

**No live regulatory feed, and it is not a scheduling gap.** Thirteen Turkish
domains — spk.gov.tr, kap.org.tr, resmigazete.gov.tr, tspb.org.tr,
tefas.gov.tr, evds2.tcmb.gov.tr, data.tuik.gov.tr among them — answer **403 to
CONNECT** at this environment's egress gateway. That is an organization policy
denial, and the proxy's own README says to report such denials rather than retry
them. The connectors are written and tested against fixtures; **not one has ever
run against its real host**, so their selectors are the part most likely to be
wrong and the first person with real access should expect to fix them.

What is not speculative is the behaviour around the fetch. A blocked source
yields nothing, logs, and increments a failure count the `CONNECTOR-DOWN` rule
reads. That verdict is taken from the crawl report rather than from an exception,
because the crawler is tolerant by design — it swallows per-URL transport errors
and keeps going, which would otherwise make a dead source look exactly like a
quiet one and leave the loop reporting a healthy regulatory watch over a feed
dark for a month. Market data degrades the same way: with no key and no network
the series arrives marked `bundled`, warns on every read, and `is_bundled` is
true if *any* point is bundled — because live history with a stale tip is the
shape that produces a confidently wrong current figure.

## What could not be established

`wamportfoy.com` and `kap.org.tr` are both blocked by this environment's egress
proxy, so the firm's own filings were never read. Fund sizes, holdings and AUM
are unknown (AIR-1); every fund-level figure the demo prints is a labelled
fixture. The 30 seeded obligations come from research that could not reach a
primary source and all load `UNVERIFIED`. The load-bearing assumption — that
VII-128.10's data-residency rule binds, which is what makes building rather
than buying correct here — rests on legal commentary, not the tebliğ (AIR-4).

Open questions live in [`provenance/unknowns.md`](provenance/unknowns.md), and
the largest of them is AIR-3: nobody has asked the owner what his week actually
contains.

## Verifying the claims

Every factual claim in this repository carries a `[src:ID]` tag resolving to
`provenance/sources.yaml`. The guard is mechanical:

```bash
python3 tools/verify_provenance.py    # 0 clean, 1 violations
```

It rejected three drafts during this session — an interpretation written inside
an `## Observed` section, a dangling source id, and a claim with no tag. See
[CLAUDE.md](CLAUDE.md) for the doctrine it enforces.

## Design principles

1. **Zero required dependencies.** Data security is the top adoption blocker at
   67% for firms like this one, and SPK requires primary and secondary systems
   to sit inside Turkey. Air-gapped reproducibility is the point.
2. **Provenance is load-bearing.** Every chunk carries its source; every
   configured fact carries whether anyone checked it.
3. **Everything is bounded.** Every network stage has a budget on requests,
   bytes and time.
4. **Degrade, don't die.** A missing key, blocked egress or a truncated response
   reduces what the pipeline can do; it never crashes.
5. **Measure, don't assert** — and where nothing has been measured, say so
   instead of asserting.
