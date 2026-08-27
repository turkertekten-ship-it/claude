#!/usr/bin/env bash
# Run every check this repository knows how to run, in the order that fails fastest.
#
# Referenced by turkertekten-ship-it/claude-ai's CLAUDE.md as the way to check
# work done under this project's doctrine. Keep it dependency-free: it has to
# run in CI, in an air-gapped container, and on a laptop with nothing installed.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2
export PYTHONPATH="src:.:${PYTHONPATH:-}"
PY="${PY:-python3}"
status=0

step() {
    # The label has to be saved before the shift, or the failure line reports
    # the command's first word instead of the step that failed - every step
    # then announces itself as "python3", which is exactly no information.
    local label="$1"
    printf '\n=== %s ===\n' "$label"
    shift
    "$@" || { printf '!! failed: %s\n' "$label"; status=1; }
}

step "compile all sources"        "$PY" -m compileall -q src tools tests
step "unit tests"                 "$PY" -m unittest discover -s tests -t . -v
step "ultrareview data checkers"  "$PY" -m tools.ultrareview . --quiet

printf '\n=== result ===\n'
if [ "$status" -eq 0 ]; then
    echo "all checks passed"
else
    echo "one or more checks failed"
fi
exit "$status"
