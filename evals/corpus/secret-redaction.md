<!-- source: https://oodarag.example/handbook/secret-redaction -->
# Secret Redaction at the Ingest Boundary

An index is a file that gets copied. It is attached to tickets, synced to
laptops, mounted into containers and handed to whoever is debugging retrieval
this week. A credential that reaches an index is therefore leaked, and it is
leaked in the most durable possible form, because nobody thinks of a database
of chunks as a place where secrets live.

## Redact twice

Redaction runs at the connector boundary, before text is ever returned, and
again during normalization, before anything is written to storage. The second
pass is defence in depth and it is nearly free. The alternative is trusting
every present and future connector to have remembered, which is how a live
credential ends up in an index that then gets copied onto three laptops.

## Normalize before matching

Unicode folding happens before the patterns are applied, never after. NFKC
normalization turns fullwidth and homoglyph-laden text into the plain ASCII
shape the patterns actually match; running redaction first lets exactly those
strings through untouched.

## What the patterns look for

Provider-prefixed keys are the easy case, because vendors chose distinctive
prefixes precisely so that scanners can find them: the GitHub, Slack, AWS and
OpenAI families all begin with a short fixed marker followed by a long
high-entropy tail. Beyond prefixes, three shapes are worth matching: an
Authorization header carrying a bearer credential, an assignment whose left
hand side is a word like password or api key or token, and a PEM private key
block, which is matched from its BEGIN line to its END line so the whole body
disappears rather than the first line only.

## Count what you redact

The number of documents whose text actually changed under redaction is
reported, not swallowed. Counting hits is less useful than counting documents:
one file leaking the same key twelve times is one leaky source to go and fix.
A count that moves from zero to seven between two runs is the only signal
anyone gets that a source has started leaking, and it belongs in the ingest
report next to the error counts.

## Redaction is not a substitute for rotation

A redacted index is safe; the credential that was in the source is not. Treat
every match as an incident: rotate the key, then fix the source.
