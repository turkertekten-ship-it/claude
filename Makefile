PY ?= python3
export PYTHONPATH := src

# Nightly loop knobs: make schedule KIND=launchd AT=23:00
KIND ?= systemd
AT   ?= 22:30

.PHONY: help install test lint demo index query eval loop clean \
        reflect reflect-apply reflect-queue reflect-status reflect-rules schedule

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install in editable mode with dev extras
	$(PY) -m pip install -e ".[dev]"

test: ## Run the full test suite (stdlib unittest, no deps needed)
	$(PY) -m unittest discover -s tests -v

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

# -- the nightly self-improvement loop ---------------------------------------

reflect: ## Dry-run tonight's improvement cycle (changes nothing)
	$(PY) -m oodarag.cli reflect run

reflect-apply: ## Run the cycle and actually apply the safe-tier edits
	$(PY) -m oodarag.cli reflect run --apply

reflect-queue: ## Proposals waiting on your accept/dismiss
	$(PY) -m oodarag.cli reflect queue

reflect-status: ## What the loop has observed and learned so far
	$(PY) -m oodarag.cli reflect status

reflect-rules: ## Every rule and the confidence it has earned
	$(PY) -m oodarag.cli reflect rules

schedule: ## Emit an end-of-day schedule: make schedule KIND=systemd AT=22:30
	$(PY) -m oodarag.cli reflect schedule --kind $(KIND) --at $(AT)

clean:
	rm -rf .oodarag .data **/__pycache__ .pytest_cache
