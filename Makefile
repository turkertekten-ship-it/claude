# NOTE — five targets below were removed rather than left advertised.
#
# `demo`, `index`, `query`, `eval` and `loop` all invoked `python3 -m
# oodarag.cli`, and this tree has no `src/oodarag/cli.py`; `eval` also named
# `evals/goldens.jsonl`, and there is no `evals/`. They came in with the
# ingest-core root commit, where the CLI was planned and not written, and ran
# here for the whole life of this branch as targets that could only traceback.
#
# A sibling branch's checker found them in 1.6 seconds. CLAUDE.md's own rule is
# that a capability table is not evidence of capability -- a Makefile is a
# capability table that people type.
PY ?= python3
export PYTHONPATH := src

.PHONY: help install test lint demo index query eval loop clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install in editable mode with dev extras
	$(PY) -m pip install -e ".[dev]"

test: ## Run the full test suite (stdlib unittest, no deps needed)
	$(PY) -m unittest discover -s tests -v

lint: ## Compile-check every module
	$(PY) -m compileall -q src

clean:
	rm -rf .oodarag .data **/__pycache__ .pytest_cache
