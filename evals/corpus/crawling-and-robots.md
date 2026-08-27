<!-- source: https://oodarag.example/handbook/crawling-and-robots -->
# Crawling, robots.txt and Politeness

A crawler that ignores the site it is reading gets blocked, and deserves to be.
Three rules keep a crawl welcome: obey robots.txt, rate limit yourself, and
bound every dimension of the crawl in advance.

## robots.txt

Before fetching anything from a host, fetch its robots.txt and parse the group
whose User-agent line matches your agent, falling back to the wildcard group.
Within a group, Allow and Disallow rules are matched by longest prefix, with
Allow winning ties, so a broad Disallow can be narrowed by a more specific
Allow. An unreachable robots.txt is not permission: a 5xx response should be
treated as disallow-all until it recovers, while a 404 genuinely means no
restrictions were published. The Crawl-delay directive, where present, sets the
minimum interval between requests to that host and should be respected even
when it is slower than your own configured rate.

## Politeness and rate limiting

Requests to one host go through a token bucket, so bursts are permitted but the
long-run average stays under the configured rate. Retries use exponential
backoff with jitter, because synchronized retries from many workers reproduce
exactly the load spike that caused the first failure. Send a descriptive
User-agent string with a contact URL: an operator who can see who you are will
usually mail you before they ban you.

## Bounds

Every network stage is bounded on four axes: total requests, total bytes,
link depth, and wall-clock time. The failure this prevents is concrete. A
calendar page generates a "next month" link forever, and a crawler without a
depth or request bound will follow it until something else breaks.

## Canonical URLs and deduplication

The same page is reachable through tracking parameters, print views, trailing
slashes and mixed case hosts. Normalize the URL before deciding whether a page
has been seen: lowercase the host, drop the fragment, strip known tracking
parameters, and prefer the canonical link the page declares. Keep the URL you
actually fetched as the citation target, though, because a reader following a
citation must land on the page the text came from.
