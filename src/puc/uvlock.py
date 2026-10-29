# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Handle uv.lock files."""

import subprocess
import os
import tomllib
import re
from packaging.utils import canonicalize_name

from .logging import logger, colorize_updated_version
from .dependencies import (
    get_latest_version,
    is_newer_version,
)


def handle_uv_lock(
    uvlock_path: str,
    command: str | None = None,
    packages=None,
    exclude_newer: str | None = None,
    exclude_newer_package: str | None = None,
    exclude_packages=None,
    constraint_file: str | None = None,
    color: bool = True,
) -> int:
    """Check or update pinned dependencies of a uv.lock file."""
    # warn about constraint_file?
    logger.info(f"{command} lock file {uvlock_path}")
    updatable = 0
    project_dir = os.path.abspath(os.path.dirname(uvlock_path))
    # parse pyproject.toml
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    min_python_ver = None
    if os.path.isfile(pyproject_path):
        with open(pyproject_path, "rb") as f:
            try:
                pyproject = tomllib.load(f)
                py_req = pyproject.get("project", {}).get("requires-python")
                if py_req and re.match(r">=\d+\.\d+$", py_req):
                    min_python_ver = py_req[2:]
            except Exception as exc:
                logger.error(f"error parsing {pyproject_path}: {exc}")
    # parse uv.lock
    with open(uvlock_path, "rb") as f:
        try:
            uvlock = tomllib.load(f)
        except Exception as exc:
            logger.error(f"error parsing {uvlock_path}: {exc}")
            return updatable
    uvpackages = uvlock.get("package", [])
    if not uvpackages:
        logger.warning(f"no packages defined in {uvlock_path}")
        return updatable

    for uvpackage in uvpackages:
        name = uvpackage.get("name", None)
        if name is None:
            logger.warning(f"missing name in package {uvpackage}")
            continue
        # respect package filter
        if packages and canonicalize_name(name) not in packages:
            logger.info(f"skip filtered package {name!r}")
            continue
        if exclude_packages and canonicalize_name(name) in exclude_packages:
            logger.info(f"skip excluded package {name!r}")
            continue
        # check source
        if not check_source_registry(uvpackage, name):
            continue
        version = uvpackage.get("version", None)
        if version is None:
            logger.warning(f"missing version in package {uvpackage}")
            continue
        updatable += update_uvlock_dependency(
            name,
            version,
            project_dir,
            command=command,
            exclude_newer=exclude_newer,
            exclude_newer_package=exclude_newer_package,
            constraint_file=constraint_file,
            color=color,
            min_python_ver=min_python_ver,
        )
    if command == "update":
        logger.info(f"updated {updatable} package version(s) in {uvlock_path}")
    return updatable


def check_source_registry(uvpackage, name):
    """Check for a registry source, other known non-registry
    sources are skipped.
    """
    # check package source for skip reasons
    source = uvpackage.get("source", {})
    skip_sources = (
        "virtual",  # virtual packages (ie. the project itself)
        "editable",  # editable packages
        "path",  # local packages provided by file path
        "git",  # git packages provided by URL
        "directory",  # directory packages provided by local path
    )
    for skip_source in skip_sources:
        if skip_source in source:
            logger.info(f"skip {skip_source} package {name!r}")
            return False
    if "registry" not in source:
        logger.warning(f"no registry entry found for package {name!r}")
    return True


def update_uvlock_dependency(
    package,
    version,
    project_dir: str,
    command: str | None = None,
    exclude_newer: str | None = None,
    exclude_newer_package: str | None = None,
    constraint_file: str | None = None,
    color: bool = True,
    min_python_ver: str | None = None,
) -> int:
    """Update uv lock dependency."""
    try:
        latest_version = get_latest_version(
            package,
            exclude_newer=exclude_newer,
            exclude_newer_package=exclude_newer_package,
            constraint_file=constraint_file,
            python_version=min_python_ver,
        )
    except subprocess.CalledProcessError as exc:
        # error getting latest version
        err = f"{exc}, output={exc.output}, stderr={exc.stderr}"
        logger.warning(f"error getting latest version for '{package}': {err}")
        return 0
    if latest_version == version:
        return 0
    if not is_newer_version(version, latest_version):
        logger.warning(
            f"{package} latest version {latest_version} is older than specified version {version}"
        )
        return 0
    newversion = (
        colorize_updated_version(version, latest_version) if color else latest_version
    )
    if command == "check":
        logger.warning(f"found update '{package}=={version}' --> {newversion}")
    else:
        logger.info(f"updating '{package}=={version}' --> {newversion}")
        update_uvlock_pkg(package, project_dir, exclude_newer=exclude_newer)
    return 1


def update_uvlock_pkg(
    package: str,
    projectdir: str,
    exclude_newer: str | None = None,
) -> None:
    """Update one package in pyproject.toml."""
    command = [
        "uv",
        "lock",
        "--project",
        projectdir,
        "--quiet",
        "--color=never",
        "--upgrade-package",
        package,
    ]
    if exclude_newer:
        command.extend(
            (
                "--exclude-newer",
                exclude_newer,
            )
        )
    logger.debug(f"running {' '.join(command)}")
    subprocess.check_call(command)
