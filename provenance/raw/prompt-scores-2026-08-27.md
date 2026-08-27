# Prompt scores — capture 2026-08-27

Both columns measured with the same linter (the version at this commit), so the
difference is the file edit and not a rule change. "Before" files were taken
from commit 8b59cd6 with 'git show HEAD:<path>'.

## python3 tools/prompt_forge.py score --profile task <before>
```
fleet-sync.md     78/100  C  weakest: structure
ingest-chats.md   82/100  B  weakest: structure
```

## python3 tools/prompt_forge.py score --profile task .claude/commands/*.md
```
.claude/commands/fact-check.md     94/100  A  weakest: structure
.claude/commands/fleet-sync.md     90/100  A  weakest: structure
.claude/commands/ingest-chats.md  100/100  A  weakest: structure
.claude/commands/observe.md        94/100  A  weakest: structure
.claude/commands/ooda-loop.md      86/100  B  weakest: structure
.claude/commands/prompt-audit.md  100/100  A  weakest: structure
.claude/commands/prompt.md         98/100  A  weakest: structure
.claude/commands/source.md         92/100  A  weakest: precision
```

## python3 tools/prompt_forge.py score --profile system prompts/*.md
```
prompts/README.md              48/100  F  weakest: structure
prompts/archive-ingest.md      90/100  A  weakest: structure
prompts/base-operator.md       94/100  A  weakest: structure
prompts/builder.md             94/100  A  weakest: precision
prompts/portable-preamble.md   98/100  A  weakest: precision
prompts/prompt-smith.md       100/100  A  weakest: structure
prompts/researcher.md          92/100  A  weakest: bounds
```

## bash tests/run_all.sh (tail)
```
  ok   prompt-smith.md has no error-level finding
  ok   researcher.md has no error-level finding

all cases passed

ALL CHECKS PASSED
```
