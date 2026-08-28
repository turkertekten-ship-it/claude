#!/usr/bin/env bash
# Run a tool's `selfcheck` against every remote branch's copy of it.
#
# A fix on one branch does not reach a branch that merged the broken version.
# This says which branches are actually affected, rather than guessing from
# commit ancestry — a branch may have taken the fix by any route.
#
# Usage: tools/fleet_selfcheck.sh [path-in-repo]   (default: the chat ingester)
# Exit:  0 all present copies pass · 1 at least one fails · 2 could not run
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

TOOL="${1:-tools/ingest_chat_archive.py}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git fetch --all --prune >/dev/null 2>&1 || { echo "fetch failed" >&2; exit 2; }

status=0
printf '%-46s %-9s %s\n' "BRANCH" "COPY" "SELFCHECK"
for ref in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v '/HEAD$'); do
    branch="${ref#origin/}"
    if git show "$ref:$TOOL" > "$TMP/t.py" 2>/dev/null; then
        if python3 "$TMP/t.py" selfcheck >/dev/null 2>&1; then
            printf '%-46s %-9s %s\n' "$branch" "present" "PASS"
        else
            printf '%-46s %-9s %s\n' "$branch" "present" "FAIL"
            status=1
        fi
    else
        printf '%-46s %-9s %s\n' "$branch" "absent" "-"
    fi
done

[ "$status" -eq 0 ] && echo && echo "All present copies pass." \
                    || { echo; echo "At least one branch carries a defective copy."; }
exit "$status"
