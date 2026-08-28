---
provenance: enforced
---

# What this environment can actually reach

Several sessions in this fleet have goals requiring web, YouTube, or GitHub
research. This is the measured egress policy, so nobody has to rediscover it —
or worse, conclude a source does not exist when it is merely unreachable.

## Observed — the three channels behave differently

- `curl` reached `pypi.org` (200), `raw.githubusercontent.com` (301) and `github.com` (400 — an HTTP response, so the host was reached). [src:EGRESS-MAP-2026-08-27]
- `curl` failed with `CONNECT tunnel failed, response 403` for `arxiv.org`, `docling.org`, `www.youtube.com`, `huggingface.co` and `ibm.com`. [src:EGRESS-MAP-2026-08-27]
- `WebFetch` returned `EGRESS_BLOCKED` for `arxiv.org` and `www.youtube.com`, but succeeded on `github.com` and `raw.githubusercontent.com`. [src:EGRESS-MAP-2026-08-27]
- `WebSearch` returned results summarising pages on `ibm.com`, `infoq.com` and `arxiv.org` even though those hosts are unreachable directly. [src:EGRESS-MAP-2026-08-27]

## What follows

**Blocked to `curl` is not blocked to `WebSearch`.** The search backend fetches
on your behalf, so you can learn what a page says without reaching it. That is
how the Docling facts in this repository were obtained.

**But a search summary is second-hand.** You did not read the page; a model
summarised it for you. Grade it accordingly, and say so in the ledger. Every
prior-art claim recorded here carries that caveat, because arxiv is blocked and
none of those papers was actually opened.

**GitHub is the strongest channel.** `raw.githubusercontent.com` is directly
fetchable, so a public file can be read verbatim rather than summarised. Prefer
reading real source over reading about it — the export-schema work in this
repository was done that way.

**Prefer first-party over commentary.** A blog gave Docling's star count as
37k; the repository page said 65.7k. [src:DOCLING-IBM-2026-08-27] Both were
"sources"; only one was the thing itself.

## Practical order

1. `WebSearch` to find out what exists and where it lives.
2. `WebFetch` on `github.com` / `raw.githubusercontent.com` to read the real
   artifact verbatim.
3. `curl` for anything in the proxy's no-proxy list — package registries work.
4. If only a search summary is obtainable, record the claim as second-hand and
   put the open question in `provenance/unknowns.md`.
