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
run python3 tests/test_prompt_forge.py
run python3 tests/test_prompt_habits.py
run python3 tests/test_learn_rule.py
run python3 tests/test_check_output.py
run python3 tests/test_install_check.py
run python3 tools/learn_rule.py review
run bash tools/install_prompt_system.sh --check

if [ "$status" -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "CHECKS FAILED"
fi
exit "$status"
