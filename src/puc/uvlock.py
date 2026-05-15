# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Handle uv.lock files."""

import subprocess
import os
import tomllib
from packaging.utils import canonicalize_name

from .logging import logger, colorize_updated_version
from .dependencies import (
    get_latest_version,
    is_newer_version,
)


def handle_uv_lock(
    uvlock_path: str,
    command: None | str = None,
    packages=None,
    exclude_newer: None | str = None,
    exclude_newer_package: None | str = None,
    constraint_file: None | str = None,
    color: bool = True,
) -> int:
    """Check or update pinned dependencies of a uv.lock file."""
    # warn about constraint_file?
    logger.info(f"{command} lock file {uvlock_path}")
    updatable = 0
    project_dir = os.path.abspath(os.path.dirname(uvlock_path))
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
        version = uvpackage.get("version", None)
        if version is None:
            logger.warning(f"missing version in package {uvpackage}")
            continue
        updatable += update_uvlock_dependency(
            name,
            version,
            project_dir,
            command=command,
            packages=packages,
            exclude_newer=exclude_newer,
            exclude_newer_package=exclude_newer_package,
            constraint_file=constraint_file,
            color=color,
        )
    if command == "update":
        logger.info(f"updated {updatable} package version(s) in {uvlock_path}")
    return updatable


def update_uvlock_dependency(
    package,
    version,
    project_dir: str,
    command: None | str = None,
    packages=None,
    exclude_newer: None | str = None,
    exclude_newer_package: None | str = None,
    constraint_file: None | str = None,
    color: bool = True,
) -> int:
    """Update uv lock dependency."""
    # respect optional package filter
    if packages and canonicalize_name(package) not in packages:
        return 0

    try:
        latest_version = get_latest_version(
            package,
            exclude_newer=exclude_newer,
            exclude_newer_package=exclude_newer_package,
            constraint_file=constraint_file,
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
    exclude_newer: None | str = None,
) -> None:
    """Update one package in pyproject.toml."""
    command = [
        "uv",
        "lock",
        "--project",
        projectdir,
        "--quiet",
        "--color=never",
        f"--upgrade-package={package}",
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
