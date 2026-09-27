# python-update-checker

Python-update-checker (puc) checks or updates pinned dependencies
in `pyproject.toml`, `requirements.txt` or `uv.lock` files.

If you are developing an application you should pin all dependencies.
When developing a library, only development dependencies should be pinned.

See [https://github.com/astral-sh/uv/issues/6794] for a discussion
about different pinning strategies.

## Quickstart

```bash
# update dependencies in pyproject.toml to the latest version
uvx --from python-update-checker puc --exclude-newer="7 days" update pyproject.toml
# install updated dependencies in virtual environment
uv sync
```

## Features

* updates pinned dependencies, ignores unpinned dependencies
* supports pyproject.toml, uv.lock and requirements.txt formats
* supports `[project.dependencies]`, `[project.optional-dependencies]`
  and `[dependency-groups]` in pyproject.toml
* supports legacy dependency format `[tool.uv.dev-dependencies]`
  in pyproject.toml
* supports recursive references (`-r`) in requirements.txt formats
* can run in check only mode, ie. it checks if updates are available
* limit updates to specific packages
* can ignore packages
* limit updates with package version constraints (ie. `"django<6"`)
* limit updates to versions that were uploaded prior to a given date
* (limited) support for environment markers, ie. `"pywin32==311; os_name=='nt'"`
* runs on Linux, MacOS and Windows platforms

## Examples

```bash

$ # check all pinned packages for updates in pyproject.toml
$ puc check pyproject.toml
puc INFO: check pyproject file pyproject.toml
puc WARNING: found update 'ty==0.0.29' --> 0.0.32

$ # update all pinned packages in pyproject.toml
$ # limit updates to versions that are at least 7 days old
$ puc --exclude-newer="7 days" update pyproject.toml
puc INFO: update pyproject file pyproject.toml
puc INFO: updating 'ty==0.0.29' --> 0.0.31
puc INFO: Wrote 1 updated package version(s) to pyproject.toml
$ # update the project environment after upgrading pyproject.toml
$ uv sync

$ # check all pinned packages for updates in requirements.txt
$ puc check requirements.txt
puc INFO: check requirements file requirements.txt
puc WARNING: found update 'argcomplete==3.6.1' --> 3.6.3
puc WARNING: found update 'Django==5.2.0' --> 6.0.4

$ # update only the django package version in requirements.txt
$ # limit updates to django versions less than 6
$ puc --package="Django" --constraints="Django<6" update requirements.txt
puc INFO: update requirements file requirements.txt
puc INFO: updating 'Django==5.2.0' --> 5.2.13
puc INFO: Wrote 1 updated package version(s) to requirements.txt
```

## Script behaviour

The exit code of `puc check` is non-zero when updates are available.

Checking a `pyproject.toml` or `uv.lock`file with `puc` should be done
from the directory of the `pyproject.toml` file,
especially if your project relies on a [project directory](https://docs.astral.sh/uv/concepts/projects/layout/)
(for example to define additional package indexes in pyproject.toml).

After updating versions in pyproject.toml, run `uv lock --upgrade` to update
the transitive dependencies in `uv.lock` and `uv sync` to update your
virtual environment.

Pinned dependencies are packages with `==` or `===` constraints
and no wildcards in the version.

## Installation

1) Install [python uv](https://docs.astral.sh/uv/getting-started/installation/)
2) Install puc with `uv pip install python-update-checker`
  or run with `uvx --from python-update-checker puc ...`

## Architecture

Dependencies are

* [uv](https://docs.astral.sh/uv/):
  The uv binary must be available for the script to call.  
  puc uses `echo "package" | uv pip compile -` to get latest package versions.  
  puc uses `uv add "package==<version>"` to update pyproject.toml
  dependencies and `uv lock --upgrade-package` to update uv.lock dependencies.

* [packaging](https://packaging.pypa.io/):
  Parses dependencies with the packaging.requirements.Requirement class.

puc needs Python >= 3.11 since it uses the tomllib Python module.

## Updating minimum version requirements

Dependencies like `requests>=1.12` or `django>5` specify a
minimum version requirement.

Minimum requirements are necessary to work with different versioned
dependencies, since different distributions package different
versions of those dependencies.
Minimum requirements change when the project uses a
feature that is only available in newer versions of a dependency.
This cannot be determined automatically by puc.
So minimum version requirements should be updated manually.

## Limitations

* No support for custom dependency formats in pyproject.toml
  (eg. `[tool.poetry.dependencies]`).
* puc has limited support for environment markers.
* Constraint references (`-c`) inside requirements.txt are not supported.  
  Use the `--constraints` option instead.
* No support for updating non-pinned dependencies.
