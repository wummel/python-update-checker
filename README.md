python-check-updates
=====================
Python-check-updates updates pinned dependencies in `pyproject.toml` or
`requirements.txt` to the latest versions.  
Pinning dependencies is an important part for [reproducible builds](https://en.wikipedia.org/wiki/Reproducible_builds).


Features
---------

* updates pinned dependencies, ignores unpinned dependencies
* supports both pyproject.toml and requirements.txt formats
* supports `[project.dependencies]`, `[project.optional-dependencies]` and `[dependency-groups]` in pyproject.toml
* can run in check only mode, ie. it checks if updates are available
* limit updates to specific packages
* limit updates with package version constraints (ie. "django<6")
* limit updates to versions that were uploaded prior to a given date
* (limited) support for environment markers, ie. `"pywin32==311; os_name=='nt'"`
* runs on Linux, MacOS and Windows platforms


Examples
---------

```bash
# check all pinned packages for updates in requirements.txt
pcu check requirements.txt

# check all pinned packages for updates in several requirements.txt-style files
pcu check requirements/*.txt

# update all pinned packages for updates in pyproject.toml
# limit updates to versions that are at least 10 days old
pcu --exclude-newer="10 days" update pyproject.toml

# update only the django package version in pyproject.toml
# limit updates to django versions less than 6
pcu --package="django" --constraints="django<6" update pyproject.toml
```

After updating versions in pyproject.toml, run `uv lock --upgrade` to update
the transitive dependencies in `uv.lock`.


Installation
-------------

1) Install python uv (https://docs.astral.sh/uv/getting-started/installation/)
2) For Linux and MacOS:
   
   ```bash
   mkdir -p ~/.local/bin
   cp pcu ~/.local/bin
   export PATH=$PATH:~/.local/bin
   ```


Architecture
-------------

Dependencies are

* [uv](https://docs.astral.sh/uv/):
  The uv binary must be available for the script to call.  
  Pcu uses `echo "package" | uv pip compile -` to get latest package versions.  
  Pcu uses `uv add "package==<version>"` to update pyproject.toml dependencies.

* [packaging](https://packaging.pypa.io/):
  Parses requirements.txt dependencies with the packaging.requirements.Requirement class.

Pcu needs Python >= 3.11 since it uses the tomllib Python module.

Pcu consists of a single python script. The script uses [inline script metadata](https://peps.python.org/pep-0723/) to be executed directly with `uv run --script`.


Limitations
------------

* No library api is available, only the pcu command line interface as a single script.
* Pcu only supports environment markers `os_name`, `sys_platform` with `==` operator.
* References (`-r`) inside requirements.txt are not supported.  
  You can provide multiple requirements.txt files as arguments to pcu instead.
* Constraint references (`-c`) inside requirements.txt are not supported.  
  Use the `--constraints` option from pcu instead.
