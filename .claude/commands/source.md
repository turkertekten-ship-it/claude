---
description: Capture a finding into the provenance ledger correctly, so a claim can cite it.
argument-hint: [what you established, and how]
allowed-tools: Bash, Read, Edit
---

Record this finding in the ledger: **$ARGUMENTS**

1. Re-run the command that produced it, so the evidence is current rather than
   remembered. If you cannot re-run it, say so in the entry's `note`.
2. Append to `provenance/sources.yaml`:

```yaml
  - id: SHORT-DESCRIPTIVE-ID-YYYY-MM-DD
    kind: tool_output | filesystem | api | user_statement | repo_state
    collected_at: "ISO-8601"
    method: "the exact command or tool call"
    evidence: >-
      The output itself, or a path under provenance/raw/.
```

3. Output longer than a few lines goes verbatim into `provenance/raw/` and the
   entry points at the file. Do not paraphrase evidence into the ledger — a
   summary is not a capture.
4. If the finding came from another session, another agent, or a fetched
   document, mark it second-hand in `note` and name the reporter. It is a lead,
   not a verified fact.
5. Now write the claim wherever it belongs, tagged `[src:YOUR-ID]`, and run
   `python3 tools/verify_provenance.py`.

If re-running produced something different from what you expected to record,
that difference is the interesting part. Record what you saw, not what you
meant to see.
