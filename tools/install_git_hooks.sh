#!/usr/bin/env bash
# Point git at this repository's versioned hooks.
#
# Git hooks are not cloned, so `githooks/` is committed and `core.hooksPath`
# points at it. One command, run once per clone.
#
# Exit: 0 configured · 2 could not run
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 2
git config core.hooksPath githooks || exit 2
printf 'core.hooksPath = %s\n' "$(git config core.hooksPath)"
printf 'pre-push will refuse a red suite. Deliberate override: git push --no-verify\n'
