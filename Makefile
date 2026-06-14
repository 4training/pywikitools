.PHONY: help test lint format coverage clean clean-pyc clean-test

.DEFAULT_GOAL := help

PYTHON ?= ./env/bin/python
RUFF ?= ./env/bin/ruff
COVERAGE ?= ./env/bin/coverage

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

BROWSER := python3 -c "$$BROWSER_PYSCRIPT"

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help: ## show this help
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

test: ## run the test suite
	$(PYTHON) -m unittest discover -s pywikitools/test

lint: ## check style with ruff
	$(RUFF) check .
	$(RUFF) format --check .

format: ## auto-format code with ruff
	$(RUFF) format .

coverage: ## run tests with coverage report and open HTML in browser
	$(COVERAGE) run --source=pywikitools/,pywikitools/correctbot/ --omit=pywikitools/user-config.py -m unittest discover -s pywikitools/test
	$(COVERAGE) report -m
	$(COVERAGE) html
	$(BROWSER) htmlcov/index.html

clean: clean-pyc clean-test ## remove cache and coverage artifacts

# Skip ./env
FIND_EXCLUDE_ENV = -path './env' -prune -o

clean-pyc: ## remove __pycache__ directories
	find . $(FIND_EXCLUDE_ENV) -name '__pycache__' -type d -print -exec rm -fr {} +

clean-test: ## remove coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
