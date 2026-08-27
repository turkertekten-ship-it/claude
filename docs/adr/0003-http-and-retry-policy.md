# ADR 0003 - urllib, with an explicit retry policy

**Status:** accepted

## Context

Every connector needs HTTP with retries, rate limiting, conditional requests and
size caps. `requests` is the default choice.

## Decision

`util/http.py`, built on `urllib`, with a token-bucket rate limiter, an explicit
retry policy, ETag conditional GETs, hard response-size caps, and redirects
followed only for safe methods.

## Consequences

`requests` would have provided connection pooling and a nicer API. It would not
have provided any of the behaviour above, which would have had to be written
regardless - and it would have made the core non-stdlib for the sake of the two
things it does give. urllib reads `HTTPS_PROXY` and `NO_PROXY` from the
environment, which is how this runs inside an egress-filtered container with no
special casing.

**The retry policy is where the substance is.** Naive "retry 5xx" is wrong for
the APIs this actually talks to:

- **GitHub signals rate limiting with HTTP 403**, not 429 - both primary quota
  exhaustion and secondary limits. Treating every 403 as permanent turns the most
  common GitHub failure into a hard failure mid-ingest. So 403 is retried only
  when the headers or body say rate limit, and a permission denial still fails
  fast. (LEARNINGS L3)
- **`Retry-After` beats exponential backoff** when the server sends it, and
  GitHub's `x-ratelimit-reset` is honoured as the wait when it does not.
- **Responses are capped in bytes**, streamed and aborted past the cap, so one
  pathological URL cannot exhaust memory.
