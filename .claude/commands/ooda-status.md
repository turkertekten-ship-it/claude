---
description: Index and loop state - documents, chunks, embedding coverage, fingerprint, source health
---

Run both, then summarise in three lines or fewer:

```bash
cd /home/user/claude && PYTHONPATH=src python3 -m oodarag.cli status
cd /home/user/claude && PYTHONPATH=src python3 -m oodarag.cli journal --limit 10
```

Read-only, ~0.1s. Flag anything that matters and stay quiet otherwise:

- `index.coverage` below 1.0 - chunks without vectors; the policy treats that
  as an integrity problem outranking freshness.
- `embedder` != `index_fingerprint` - vectors are from a different embedding
  space and must be rebuilt (`index --refit`).
- `source_health` entries with `consecutive_failures` > 1 - a broken source,
  not a blip.
- `journal` printing nothing means no OODA cycle has run yet (`cycles_run: 0`).
  That is empty-because-absent, not empty-because-broken - say which.
