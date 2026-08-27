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

# The oodarag pipeline suite, once it exists. test_pipeline_e2e.py is the
# marker: it is the suite that exercises the whole pipeline, so if it is absent
# the pipeline is not finished and there is nothing meaningful to run. Guarded
# rather than unconditional so this script stays useful on a tree where only the
# substrate is built.
if [ -f tests/test_pipeline_e2e.py ]; then
    echo "== oodarag suite =="
    PYTHONPATH=src python3 -m unittest discover -s tests -t . -q || status=1
    echo
fi

if [ "$status" -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "CHECKS FAILED"
fi
exit "$status"
