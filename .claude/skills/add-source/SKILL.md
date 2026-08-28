---
name: add-source
description: Add a new ingestion source to the oodarag corpus - a filesystem tree, a GitHub repo, a web crawl seed, a YouTube manifest, or a brand-new connector. Use when asked to ingest, index, crawl, connect or pull in content from somewhere new, to enable a disabled `[[source]]` in oodarag.toml, or to write a connector. Covers the mandatory order: probe reachability first, then configure, then index, then re-run the eval. Not for tuning retrieval on a corpus that is already indexed.
---

# Adding an ingestion source

Order matters. Doing these out of order is how a session spends forty minutes
building against a host it cannot reach.

## 1. Probe FIRST — reachability is a design input

Before editing any config:

```bash
cd /home/user/claude && PYTHONPATH=src python3 -m oodarag.cli preflight
```

Then probe the *specific* host the new source needs, from where the pipeline
actually runs — the container, not the agent's fetch tool. They are different
egress paths with different policies (`internal/CAPABILITY-PROTOCOL.md`):

```bash
PYTHONPATH=src python3 - <<'PY'
from oodarag.util.http import HttpClient
try:
    r = HttpClient().get("https://pypi.org/robots.txt")   # <- the host you need
    print("ok", r.status, len(r.body), "bytes")
except Exception as e:
    print("blocked:", type(e).__name__, e)
PY
```

Both outcomes observed here:

```
ok 200 325 bytes                                            # pypi.org
blocked: TransportError URLError: <urlopen error Tunnel connection failed: 403 Forbidden>   # en.wikipedia.org
```

`Tunnel connection failed: 403` is a **policy denial**, not a transient error.
It costs ~8s of backoff before it gives up. Detect it once and take the
fallback; do not retry it in a loop.

**A blocked seed is a silent empty crawl.** Verified in this container against
`en.wikipedia.org`: the run reports

```
! [robots] robots unreachable host=en.wikipedia.org ... policy=deny
  [ingest.web] web connector report ... fetched=0 bytes=0 duration_s=8.0
  [ingest] connector run key=web:... new=0 changed=0 unchanged=0 failed=0
```

`failed=0`, `errors: []`, exit 0. Nothing in the index report says the source
contributed nothing because it was *blocked* rather than *empty*. That
distinction only exists if you probed.

If the host is blocked, walk the escalation ladder (see the `preflight` skill)
before giving up. Rung 5 is the one this repo uses most: capture what a
reachable path can see into a manifest committed to the repo, and let the
pipeline consume that offline — `corpus/ibm-technology/manifest.json` and the
`youtube` source exist precisely because youtube.com is blocked here.

## 2. Add the `[[source]]` block

Sources live in `oodarag.toml`. Every block needs `type`; the rest are
connector options. `enabled = false` keeps a block documented but inert.

```toml
[[source]]
type      = "filesystem"
root      = "corpus/handbook"
patterns  = ["**/*.md"]
authority = 1.0            # reranker trust weight: official docs > a blog post
```

```toml
[[source]]
type      = "github"
owner     = "owner"
repo      = "repo"
resources = ["repo", "issues", "pulls", "releases"]
```

```toml
[[source]]
type        = "web"
seeds       = ["https://pypi.org/project/requests/"]   # must be reachable - probe it
max_pages   = 20
max_fetches = 60
max_depth   = 2
authority   = 0.8
```

Bounds are not optional (`CLAUDE.md` non-negotiable 3): budget the **work**
(fetches, bytes, depth, wall-clock), not just the accepted output. A crawl
capped only on pages kept can still fetch forever.

Add a comment saying *why* the source is in the corpus and what it is expected
to contribute. Blocks in this file already do.

## 3. Index

```bash
PYTHONPATH=src python3 -m oodarag.cli index
PYTHONPATH=src python3 -m oodarag.cli index --refit   # after a chunker/embedder change
```

Read the per-source delta in the JSON report — `new`, `changed`, `unchanged`,
`failed`, `errors`, `duration_s`:

- `new > 0` — it worked.
- `new=0` with everything else 0 — **explain the empty before moving on.**
  Blocked (rung 1 of the ladder), filtered (patterns match nothing — verify
  with `find <root> -name '<pattern>'`), deduplicated (already in the index
  under another source), or genuinely absent. Observed here: a source pointed
  at `scripts/` returned all zeros because `scripts/` is an empty directory —
  genuinely absent, not blocked.
- `failed > 0` — read `errors`. One bad document must not abort the rest, and
  it does not; the count is the signal.

Expect the run to spend ~25s on HTTP backoff against blocked hosts before the
circuit breaker opens them (`circuit opened; host treated as unreachable
... cooldown_s=300`). That is the known cost of the blocked-egress environment,
not a hang.

## 4. Re-run the eval — confirm nothing regressed

A new source changes term statistics and competes for the top-k window. It can
make retrieval *worse*.

```bash
PYTHONPATH=src python3 -m oodarag.cli eval --exclude-source chat
```

Observed doing exactly this: adding a small `.github` source took the index
from 88 to 89 documents; pass rate held at 18/20, but nDCG@8 moved 0.5094 →
0.4990. Pass rate alone would have said "no change". Capture a before-run and
diff it — see the `eval-gate` skill, which also covers the contamination line
and the `known-limitation` case that must keep failing.

If the new source is one that records the evaluation itself (transcripts,
notes, anything quoting the golden questions), it must be held out with
`--exclude-source <system>` or the numbers measure a leak.

**Then re-read the negative cases.** A wider corpus can answer a question it
could not before, and nothing detects it: the contamination checker asks whether
a document *contains* a question, never whether one *answers* it. Widening from
266 to 349 pages invalidated three of fourteen negatives at once - `openpyxl`
arrived and "which package reads and writes spreadsheet files?" stopped being
unanswerable, `pip-tools` arrived with `--generate-hashes`, `portalocker` with
"an easy API to file locking" (L81). Left alone they punish the system for being
right, and they are expensive in a second way: a stale negative is contaminated
by every document that now matches it, and quarantine held **31 documents** out
of an evaluation they belonged in.

Deciding whether a page answers a question is the judgement the pipeline itself
cannot make, so this is a read of the failing negatives after every widening,
not a check that can be automated here.

## Writing a new connector

Only when no existing type fits. Subclass `oodarag.ingest.base.Connector` in
`src/oodarag/ingest/`, and wire the new `type` into `Config.build_connectors()`
in `src/oodarag/config.py`.

**The contract is deliberately narrow: a connector yields `RawDocument`s and
keeps a cursor. It never chunks, embeds, or indexes.** Those are downstream
stages and must not be re-implemented per source.

```python
class Connector(ABC):
    key: str = "connector"        # stable across runs; it keys the cursor in the StateStore
    authority: float = 1.0        # reranker trust weight

    def fetch(self, cursor: dict) -> Iterator[RawDocument]: ...
    def next_cursor(self, cursor: dict) -> dict: ...
```

`RawDocument(source_system, external_id, uri, title, text, metadata,
fetched_at)`. `external_id` must be **stable across runs** — a GitHub path+sha,
a video id, a session uuid — or incremental ingest cannot tell "changed" from
"new".

Incrementality is **content-hash based, not timestamp based**. Timestamps lie
(mirrors, rebases, re-uploads, clock skew). A cursor (commit sha, ETag,
since-date) is an optimization layered on top of the hash check, never a
replacement for it.

Errors from individual documents are counted into the delta, not raised: one
unreadable file in a 4,000-file repo must not abort the other 3,999.

### Secrets are redacted at the connector boundary

Non-negotiable. Every document's text goes through
`oodarag.util.text.redact_secrets` **before** it leaves the connector — not in
the chunker, not before display. An index is a file that gets copied around;
once a token is in it, it is out.

```python
from oodarag.util.text import redact_secrets

yield RawDocument(..., text=redact_secrets(body))
```

Follow the existing connectors: `ingest/web.py`, `ingest/chat.py` and
`ingest/github.py` all redact at the point of construction. If you add a
pattern class (a new token format), add it to `redact_secrets` and add a test
asserting the redaction path actually fires — an untriggered guard is untested,
not correct.

### Provenance

Every document carries the URI it came from, pinned to an immutable identifier
where one exists (a commit sha, not a branch name). Citations are verified
against retrieved chunks, never generated.

## Checklist

1. `preflight` run, and the specific host probed from the container.
2. Blocked? Ladder walked, rung used recorded, fallback named.
3. `[[source]]` block added with bounds and a comment saying why.
4. `index` run; the delta explained — especially any zero.
5. `eval --exclude-source chat` before and after; nDCG and recall compared, not
   just pass rate.
6. New connector: redacts secrets, keeps a cursor, chunks nothing; `make test`
   passes (~2 min, no network needed).
