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
PROJECT:=$(shell egrep "name[[:space:]]*=" pyproject.toml | cut -d'"' -f2)
VERSION:=$(shell egrep "version[[:space:]]*=" pyproject.toml | cut -d'"' -f2)

# exclude packages that are newer than this
EXCLUDE_NEWER:="7 days"
# Pytest options:
# --full-trace: print full stacktrace on errors
PYTESTOPTS?=--full-trace
# which test modules to run
TESTS ?= tests/
# set test options
TESTOPTS=
# python files and directories
PY_FILES_DIRS:=\
  pcu \
  tests

# Release configuration
RELEASE_NAME:=$(subst -,_,$(PROJECT))-$(VERSION)
RELEASE_SOURCE:=$(RELEASE_NAME).tar.gz
RELEASE_BRANCH:=main
RELEASE_TAG:=$(VERSION)
RELEASE_FILES:=\
  scripts \
  tests \
  .gitignore \
  .ruff.toml \
  COPYING \
  Makefile \
  pcu \
  pyproject.toml \
  README.md


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
	./pcu --exclude-newer=$(EXCLUDE_NEWER) check pyproject.toml

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
	# upgrade pyproject.toml dependencies
	./pcu --exclude-newer=$(EXCLUDE_NEWER) update pyproject.toml
	# upgrade inline depencencies in pcu script
	sed -i -e 's/"packaging>=.*"/"packaging>=$(shell grep "packaging>=" pyproject.toml  | cut -d'"' -f2 | cut -d= -f2)"/' pcu
	# upgrade depencencies in uv lock file
	uv lock --exclude-newer=$(EXCLUDE_NEWER) --upgrade
	# install upgraded package versions in virtual environment
	$(MAKE) init


############ Testing ############

.PHONY: test
test: ## run tests
	uv run --isolated -- pytest $(PYTESTOPTS) $(TESTOPTS) $(TESTS)

.PHONY: typecheck
typecheck:	## run the ty type checker
	ty check $(PY_FILES_DIRS)


############ Release  ############

.PHONY: distclean
distclean:
	rm -rf dist tests/__pycache__

# Releases are tagged with the version, ie. "0.5"
.PHONY: release
release: distclean checkrelease	## create release
	if [ ! -f dist/$(RELEASE_SOURCE) ]; then \
	  mkdir -p dist; \
	  git checkout tags/$(RELEASE_TAG) && \
	  tar \
	    --sort=name \
		--mtime='$(shell git log -1 --pretty=%cI)' \
		--owner=0 --group=0 --numeric-owner \
		--pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
		--gzip \
		--create \
		--file dist/$(RELEASE_SOURCE) $(RELEASE_FILES) && \
	  git checkout $(RELEASE_BRANCH); \
	  echo "Released dist/$(RELEASE_SOURCE)"; \
	fi

# export GITHUB_TOKEN for the gh command
# Generate a fine grained access token with:
# - Restricted to this repository
# - Repository permission: Metadata -> Read (displayed as "Read access to metadata" in token view)
# - Repository permission: Contents -> Read and write (displayed as "Read and Write access to code" in token view)
# - Expiration in 90 days
# After that run "export GITHUB_TOKEN=<token-content>"
.PHONY: release-gh
release-gh:	## upload a new release to github
	gh release create \
	  --title "Release $(RELEASE_TAG)" \
	  --notes-from-tag \
	  --latest \
	  --draft=false \
	  --prerelease=false \
	  --verify-tag \
	  "$(RELEASE_TAG)" \
	  dist/$(RELEASE_SOURCE)

.PHONY: checkrelease
checkrelease: lint test typecheck checkgit	## check release conditions

.PHONY: checkgit
checkgit:	## various git release checks
# check that the current branch is the release branch
	@if [ "$(shell git rev-parse --abbrev-ref HEAD)" != "$(RELEASE_BRANCH)" ]; then \
	  echo "ERROR: current branch is not '$(RELEASE_BRANCH)', but '$(shell git rev-parse --abbrev-ref HEAD;)'"; \
	  false; \
	fi
# check for uncommitted versions
	@if [ -n "$(shell git status --porcelain --untracked-files=all)" ]; then \
	  echo "ERROR: uncommitted changes"; \
	  git status --porcelain --untracked-files=all; \
	  false; \
	fi
# check that release tag exists
	@if [ -z "$(shell git tag -l -- $(RELEASE_TAG))" ]; then \
	  echo "ERROR: git tag \"$(RELEASE_TAG)\" does not exist, execute 'git tag -a $(RELEASE_TAG) -m \"$(RELEASE_TAG)\"'"; \
	  false; \
	fi
# check that release tags is pushed to remote
	@if ! git ls-remote --exit-code --tags origin $(RELEASE_TAG); then \
	  echo "ERROR: git tag \"$(RELEASE_TAG)\" does not exist on remote repo, execute 'git push --tags'"; \
	fi
