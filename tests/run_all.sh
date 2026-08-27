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
run python3 tests/test_install_user_scope.py
run python3 tools/ingest_chat_archive.py selfcheck

# The oodarag pipeline suite. Unconditional: the pipeline is built, so a tree
# where this cannot run is a broken tree, not an incomplete one. -t . makes the
# repo root the import root, which the blind-test suites need for
# `tests.support.httpserver`.
echo "== oodarag suite =="
PYTHONPATH=src python3 -m unittest discover -s tests -t . -q || status=1
echo

if [ "$status" -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "CHECKS FAILED"
fi
exit "$status"
