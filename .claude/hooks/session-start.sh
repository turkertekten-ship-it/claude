#!/bin/bash
# SessionStart hook for oodarag.
#
# This project has ZERO required runtime dependencies (ADR 0001), so there is
# nothing to install. The hook's whole job is to make the first minute of a
# fresh web/CI session productive: confirm the interpreter is usable, put
# PYTHONPATH=src in the session environment so `python3 -m oodarag.cli` works,
# and print the orientation the agent would otherwise spend three tool calls
# discovering.
#
# Contract: fast (well under a second), read-only (it never touches the index,
# the corpus or the config), and it ALWAYS exits 0. A missing tool is reported
# as a line of context, never as a failed session.

set -uo pipefail

note() { printf '%s\n' "$*"; }

# Bash builtins only - this must still work if PATH is broken, which is
# exactly the situation where the orientation matters most.
_self="${BASH_SOURCE[0]}"
SELF_ROOT="$(cd "${_self%/*}/../.." 2>/dev/null && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$SELF_ROOT}"
if ! cd "$ROOT" 2>/dev/null; then
  # Never fail silently: an unusable project dir is a finding, not a no-op.
  note "oodarag: CLAUDE_PROJECT_DIR=$ROOT is not enterable; falling back to $SELF_ROOT"
  cd "$SELF_ROOT" 2>/dev/null || { note "oodarag: no usable project directory; skipping orientation"; exit 0; }
fi

# --- interpreter -----------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  note "oodarag: python3 NOT FOUND on PATH. Nothing in this repo can run until it is"
  note "         installed (Python 3.11+ required for stdlib tomllib). Not fixing this"
  note "         automatically - installing an interpreter is not a hook's job."
  exit 0
fi

PYV="$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || echo unknown)"
PYMINOR="$(python3 -c 'import sys; print(sys.version_info[1] if sys.version_info[0]==3 else 0)' 2>/dev/null || echo 0)"

# --- session environment ---------------------------------------------------
# The package is not installed; it is imported from src/. Persist that for the
# session so every later command is just `python3 -m oodarag.cli ...`.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PYTHONPATH=src' >> "$CLAUDE_ENV_FILE"
fi

# --- import check (read-only; opens no database, makes no request) ---------
IMPORT_STATUS="$(PYTHONPATH=src python3 -c 'import oodarag; print("ok " + oodarag.__version__)' 2>&1 | tail -1)"

note "oodarag - OODA-driven RAG pipeline, Python ${PYV}, stdlib only (no install step)."
if [ "${PYMINOR:-0}" -lt 11 ] 2>/dev/null; then
  note "  WARNING: Python 3.11+ is required (stdlib tomllib); this is ${PYV}. Expect config load to fail."
fi
case "$IMPORT_STATUS" in
  ok*) note "  import oodarag: ${IMPORT_STATUS}" ;;
  *)   note "  import oodarag FAILED: ${IMPORT_STATUS}" ;;
esac
note "  Run everything as: PYTHONPATH=src python3 -m oodarag.cli <cmd>   (Makefile exports it for you)"
note "  Key commands: preflight (probe reachability FIRST - see internal/CAPABILITY-PROTOCOL.md)"
note "                index | query \"...\" | eval --exclude-source chat | loop --dry-run | status | journal"
note "                make test (stdlib unittest) | make lint | make demo"
note "  Read CLAUDE.md before changing anything. Blocked egress is expected and is a design input, not a bug."

exit 0
