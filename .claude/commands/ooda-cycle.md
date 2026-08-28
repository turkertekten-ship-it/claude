---
description: Run one OODA cycle (observe, orient, decide, act) - dry-run by default
argument-hint: "[--dry-run | --cycles N | --json]"
---

```bash
cd /home/user/claude && PYTHONPATH=src python3 -m oodarag.cli loop --cycles 1 ${ARGUMENTS:---dry-run}
```

`--dry-run` is the right first move: it decides and explains, and the **Act**
phase executes nothing. It is not read-only overall - Observe still runs every
connector and writes what they yield to the index. Expect ~27s, most of it HTTP
backoff against blocked hosts.

Report the decision line and each outcome, e.g. (observed):

```
cycle 1: 3 docs ingested, 2 actions decided, acted: alert=done, run_eval=dry_run
    alert     done     a required capability is unavailable; the corpus is incomplete
    run_eval  dry_run  the corpus changed; retrieval quality must be re-measured
```

Then say what the policy would have done for real, and why. Rules and their
priorities are in `src/oodarag/ooda/policy.py`; integrity outranks freshness.
`journal --cycle N` reconstructs any cycle in full.
