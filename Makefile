# This Makefile is only used by developers.

############# Settings ############
# use Bash as shell, not sh
SHELL := bash
# execute makefile in a single bash process instead of one per target
.ONESHELL:
# set Bash flags
.SHELLFLAGS := -eu -o pipefail -c
# remove target files if a rule fails, forces reruns of aborted rules
.DELETE_ON_ERROR:
# warn for undefined variables
MAKEFLAGS += --warn-undefined-variables
# disable builtin default rules
MAKEFLAGS += --no-builtin-rules


############ Configuration ############
VERSION:=$(shell grep "version" pyproject.toml | cut -d '"' -f2)
# Pytest options:
# --full-trace: print full stacktrace on errors
PYTESTOPTS?=--full-trace
# which test modules to run
TESTS ?= tests/
# set test options
TESTOPTS=
# python files and directories
PY_FILES_DIRS:=pcu tests

############ Default target ############

# `make help` displays all targets documented with `##`in the target line
.PHONY: help
help:	## display this help section
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help


############ Installation and provisioning  ############

.PHONY: init
init: ## install python virtual env and required development packages
	uv sync


############ Linting and syntax checks ############

.PHONY: lint
lint: lint-py lint-shell

.PHONY: lint-py
lint-py: ## lint python code
	ruff check $(PY_FILES_DIRS)

.PHONY: lint-shell
lint-shell:
	shellcheck -x scripts/*.sh

.PHONY: audit
audit: ## run audit checks
	uv audit

.PHONY: reformat
reformat: ## format the python code
	ruff check --fix $(PY_FILES_DIRS)
	ruff format $(PY_FILES_DIRS)

.PHONY: checkoutdated checkoutdated-py checkoutdated-gh
checkoutdated: checkoutdated-py checkoutdated-gh

checkoutdated-py:	## Check for outdated package requirements
	pcu --exclude-newer="7 days" check pyproject.toml

checkoutdated-gh:	## check for outdated github projects
# github-check-outdated is a local tool which compares a given version with the latest available github release version
# see https://gist.github.com/wummel/ef14989766009effa4e262b01096fc8c for an example implementation
	@echo "Check for outdated Github tools"
	github-check-outdated astral-sh uv "$(shell uv --version | cut -f2 -d" ")"
	github-check-outdated python cpython v$(shell python --version | cut -f2 -d" ") '^v3\.14\.[0-9]+$$'


.PHONY: upgradeoutdated
upgradeoutdated:	upgradeoutdated-gh upgradeoutdated-py

.PHONY: upgradeoutdated-gh
upgradeoutdated-gh:
	sed -i -e 's/uv_version_dev = ".*"/uv_version_dev = "$(shell github-check-outdated astral-sh uv 0 | cut -f4 -d" ")"/' pyproject.toml
	sed -i -e 's/python_version_dev = ".*"/python_version_dev = "$(shell github-check-outdated python cpython 0 '^v3\.14\.[0-9]+$$' | cut -f4 -d" " | cut -b2-)"/' pyproject.toml
	scripts/install_dev.sh

.PHONY: upgradeoutdated-py
upgradeoutdated-py:	## upgrade dependencies in pyproject.toml and uv.lock
	pcu --exclude-newer="7 days" update pyproject.toml
	uv lock --upgrade
	$(MAKE) init


############ Testing ############

.PHONY: test
test: ## run tests
	uv run --isolated -- pytest $(PYTESTOPTS) $(TESTOPTS) $(TESTS)

.PHONY: typecheck
typecheck:	## run the ty type checker
	ty check $(PY_FILES_DIRS)
