PY ?= python3
export PYTHONPATH := src

.PHONY: help install test lint demo index query eval loop reachability skills verify clean

# Tests assert on return values, not on log lines; the logs are noise there.
export OODARAG_LOG_LEVEL ?= warn

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install in editable mode with dev extras
	$(PY) -m pip install -e ".[dev]"

test: ## Run every check: unit tests plus the provenance guard
	$(PY) -m unittest discover -s tests
	@bash tests/run_all.sh

unit: ## Run only the unit tests, verbosely
	$(PY) -m unittest discover -s tests -v

verify: ## Run only the provenance guard
	$(PY) tools/verify_provenance.py

lint: ## Compile-check every module
	$(PY) -m compileall -q src

demo: ## Full end-to-end demo: ingest seed corpus, index, query, eval
	$(PY) -m oodarag.cli demo

index: ## Ingest + index all configured sources
	$(PY) -m oodarag.cli index

query: ## Ask a question: make query Q="what is RAG?"
	$(PY) -m oodarag.cli query "$(Q)"

eval: ## Run the evaluation harness against evals/goldens.jsonl
	$(PY) -m oodarag.cli eval

loop: ## Run one OODA cycle
	$(PY) -m oodarag.cli loop --cycles 1

reachability: ## Report what this host can fetch, and why not
	$(PY) -m oodarag.cli reachability

skills: ## Discover and lint every SKILL.md reachable from here
	$(PY) -m oodarag.cli skills

clean:
	rm -rf .oodarag .data **/__pycache__ .pytest_cache
