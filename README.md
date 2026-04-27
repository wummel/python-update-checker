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
$ # check all pinned packages for updates in pyproject.toml
$ pcu check pyproject.toml
INFO: handling pyproject file pyproject.toml
WARNING: update 'ty==0.0.29' --> 0.0.32

$ # update all pinned packages in pyproject.toml
$ # limit updates to versions that are at least 7 days old
$ pcu --exclude-newer="7 days" update pyproject.toml
INFO: handling pyproject file pyproject.toml
WARNING: update 'ty==0.0.29' --> 0.0.31
INFO: Wrote 1 updated package versions to pyproject.toml

$ # check all pinned packages for updates in requirements.txt
$ pcu check requirements.txt
INFO: handling requirements file requirements.txt
WARNING: update 'argcomplete==3.6.1' --> 3.6.3
WARNING: update 'Django==5.2.0' --> 6.0.4

$ # update only the django package version in requirements.txt
$ # limit updates to django versions less than 6
$ pcu --package="Django" --constraints="Django<6" update requirements.txt
INFO: handling requirements file requirements.txt
WARNING: update 'Django==5.2.0' --> 5.2.13
INFO: Wrote 1 updated package versions to requirements.txt
```

Script behaviour
-----------------

The exit code of `pcu check` is non-zero when updates are available.

Checking a `pyproject.toml` with `pcu` should be done from the project of the `pyproject.toml` file,
especially if your project relies on a [project directory](https://docs.astral.sh/uv/concepts/projects/layout/) (for example to define additional packages index in pyproject.toml).

After updating versions in pyproject.toml, run `uv lock --upgrade` to update
the transitive dependencies in `uv.lock`.

Pinned dependencies are packages with `==` or `===` constraints and no wildcards in the version.


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
This enables simple packaging and installation.


Limitations
------------

* No library api is available, only the `pcu` command line interface.
* No support for custom dependency formats in pyproject.toml
  (eg. `[tool.poetry.dependencies]`).
* Pcu has limited support for environment markers.
* Constraint references (`-c`) inside requirements.txt are not supported.  
  Use the `--constraints` option instead.
