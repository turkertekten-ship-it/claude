---
description: Report what the prompt workbench can and cannot do in this environment
allowed-tools: Bash
---

```bash
python3 -m workbench doctor && python3 -m workbench graders
```

Relay the output. Be specific about what is *not* controllable here and why —
sampling parameters are deprecated on current models and absent from the CLI,
so their absence is a property of the platform, not a gap in this tool.
