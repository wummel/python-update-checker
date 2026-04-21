python-check-updates
=====================
Python-check-updates (pcu) updates pinned dependencies in `pyproject.toml` or
`requirements.txt` to the latest versions.  
Pinning dependencies is an important part for [reproducible builds](https://en.wikipedia.org/wiki/Reproducible_builds).


Features
---------

* updates pinned dependencies, ignores unpinned dependencies
* supports both pyproject.toml and requirements.txt formats
* supports `[project.dependencies]`, `[project.optional-dependencies]` and `[dependency-groups]` in pyproject.toml
* supports recursive references (-r) in requirements.txt formats
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
pcu check requirements/*.in

# update all pinned packages in pyproject.toml
# limit updates to versions that are at least 10 days old
pcu --exclude-newer="10 days" update pyproject.toml

# update only the django package version in pyproject.toml
# limit updates to django versions less than 6
pcu --package="django" --constraints="django<6" update pyproject.toml
```

If your project relies on a [project directory](https://docs.astral.sh/uv/concepts/projects/layout/) (for example to define additional packages index in pyproject.toml), run `pcu` from your project root directory.

After updating versions in pyproject.toml, run `uv lock --upgrade` to update
the transitive dependencies in `uv.lock`.


Installation
-------------

1) Install [python uv](https://docs.astral.sh/uv/getting-started/installation/)
2) Copy the [pcu](https://raw.githubusercontent.com/wummel/python-check-updates/refs/heads/main/pcu) script into a PATH directory.

Example for Linux and MacOS:

   ```bash
   # create directory
   mkdir -p ~/.local/bin
   # download pcu
   curl https://raw.githubusercontent.com/wummel/python-check-updates/refs/heads/main/pcu > ~/.local/bin/pcu
   chmod 0755 ~/.local/bin/pcu
   # add directory to PATH
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
  Parses dependencies with the packaging.requirements.Requirement class.

Pcu needs Python >= 3.11 since it uses the tomllib Python module.

Pcu consists of a single python script. The script uses [inline script metadata](https://peps.python.org/pep-0723/) to be executed directly with `uv run --script`.  
This enables easy packaging and installation.


Limitations
------------

* No library api is available, only the `pcu` command line interface.
* No support for custom dependency formats in pyproject.toml
  (eg. `[tool.poetry.dependencies]`).
* Pcu has limited support for environment markers.
* Constraint references (`-c`) inside requirements.txt are not supported.  
  Use the `--constraints` option instead.
