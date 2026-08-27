PY ?= python3
export PYTHONPATH := src

.PHONY: help install test lint check review clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install in editable mode with dev extras
	$(PY) -m pip install -e ".[dev]"

test: ## Run the full test suite (stdlib unittest, no deps needed)
	PYTHONPATH=src:. $(PY) -m unittest discover -s tests -t . -v

lint: ## Compile-check every module
	$(PY) -m compileall -q src

check: ## Everything a reviewer runs: lint, tests, and the evidence checkers
	bash tests/run_all.sh

review: ## Check this repository's claims against its own data
	PYTHONPATH=src:. $(PY) -m tools.ultrareview .

clean:
	rm -rf .oodarag .data **/__pycache__ .pytest_cache
