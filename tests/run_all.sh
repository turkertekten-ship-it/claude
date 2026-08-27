#!/usr/bin/env bash
# Every check in this repository, in one place. 0 clean, 1 findings.
set -uo pipefail
cd "$(dirname "$0")/.."

status=0
run() {
    echo "== $* =="
    "$@" || status=1
    echo
}

run python3 tools/verify_provenance.py
run python3 tests/test_verify_provenance.py
run python3 tests/test_ingest_chat_archive.py
run python3 tests/test_probe_egress.py
run python3 tests/test_install_skills_user_scope.py

if [ "$status" -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "CHECKS FAILED"
fi
exit "$status"
