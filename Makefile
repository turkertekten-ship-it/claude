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

demo: ## Full end-to-end demo: ingest seed corpus, index, query, eval
	$(PY) -m oodarag.cli demo

index: ## Ingest + index all configured sources
	$(PY) -m oodarag.cli index

query: ## Ask a question: make query Q="what is RAG?"
	$(PY) -m oodarag.cli query "$(Q)"

eval: ## Run the evaluation harness against evals/goldens.jsonl
	$(PY) -m oodarag.cli eval --exclude-source chat

eval-external: ## Evaluate against the external corpus (no self-reference)
	$(PY) -m oodarag.cli --config oodarag-external.toml index
	$(PY) -m oodarag.cli --config oodarag-external.toml eval \
		--goldens evals/goldens-external.jsonl --min-pass-rate 0.78

loop: ## Run one OODA cycle
	$(PY) -m oodarag.cli loop --cycles 1

clean:
	rm -rf .oodarag .data **/__pycache__ .pytest_cache
