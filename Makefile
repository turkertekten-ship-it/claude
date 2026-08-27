PY ?= python3
export PYTHONPATH := src

.PHONY: help install test lint demo index query eval loop clean task-division task-division-check e2e selftest

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

task-division: ## Divide every prompt into tasks, for every project on this machine
	$(PY) tools/install_task_division.py

task-division-check: ## Report whether prompt task division is installed (0 yes, 1 no)
	$(PY) tools/install_task_division.py --check

e2e: ## Integration tests that drive the real claude binary (slow, spends tokens)
	TASK_DIVISION_E2E=1 $(PY) -m unittest tests.test_integration -v

selftest: ## Engine selftest, run twice to catch state it wrote itself
	$(PY) tools/task_division.py selftest && $(PY) tools/task_division.py selftest

clean:
	rm -rf .oodarag .data **/__pycache__ .pytest_cache
