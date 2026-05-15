# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Handle pyproject.toml files."""

import subprocess
import os
import tomllib
from packaging.utils import canonicalize_name
from packaging.requirements import Requirement

from .logging import logger, colorize_updated_version
from .dependencies import (
    get_latest_version,
    get_python_platform_from_req,
    get_min_python_version_from_req,
    check_requirement,
)


def handle_pyproject_toml(
    pyproject_path: str,
    command: None | str = None,
    packages=None,
    exclude_newer: None | str = None,
    exclude_newer_package: None | str = None,
    constraint_file: None | str = None,
    color: bool = True,
) -> int:
    """Check or update pinned dependencies of a pyproject.toml file.
    Specification: https://packaging.python.org/en/latest/specifications/pyproject-toml/
    Friendly guide: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
    """
    logger.info(f"{command} pyproject file {pyproject_path}")
    updatable = 0
    project_dir = os.path.abspath(os.path.dirname(pyproject_path))
    # parse pyproject.toml
    with open(pyproject_path, "rb") as f:
        try:
            pyproject = tomllib.load(f)
        except Exception as exc:
            logger.error(f"error parsing {pyproject_path}: {exc}")
            return updatable
        project = pyproject.get("project", dict())
        if not project:
            logger.warning(f"no project defined in {pyproject_path}")
            return updatable
        projectname = project.get("name", None)
        # project dependencies
        if "dependencies" in project:
            updatable += update_pyproject_dependencies(
                project["dependencies"],
                project_dir,
                projectname,
                command=command,
                packages=packages,
                exclude_newer=exclude_newer,
                exclude_newer_package=exclude_newer_package,
                constraint_file=constraint_file,
                color=color,
            )
        # update optional dependencies
        for group, deps in project.get("optional-dependencies", {}).items():
            updatable += update_pyproject_dependencies(
                deps,
                project_dir,
                projectname,
                group=group,
                optional=True,
                command=command,
                packages=packages,
                exclude_newer=exclude_newer,
                exclude_newer_package=exclude_newer_package,
                constraint_file=constraint_file,
                color=color,
            )
        # update dependency groups
        for group, deps in pyproject.get("dependency-groups", {}).items():
            updatable += update_pyproject_dependencies(
                deps,
                project_dir,
                projectname,
                group=group,
                command=command,
                packages=packages,
                exclude_newer=exclude_newer,
                exclude_newer_package=exclude_newer_package,
                constraint_file=constraint_file,
                color=color,
            )
    if command == "update":
        logger.info(f"updated {updatable} package version(s) in {pyproject_path}")
    return updatable


def update_pyproject_dependencies(
    dependencies: list[str | dict],
    project_dir: str,
    projectname: str,
    group: None | str = None,
    optional=False,
    command: None | str = None,
    packages=None,
    exclude_newer: None | str = None,
    exclude_newer_package: None | str = None,
    constraint_file: None | str = None,
    color: bool = True,
) -> int:
    """Update given dependency list of a pyproject.toml file."""
    updatable = 0
    for dep in dependencies:
        if isinstance(dep, dict):
            logger.debug(f"skip include-group dependency {dep!r} in group {group}")
            continue
        try:
            pkg_req = Requirement(dep)
        except Exception as exc:
            logger.debug(f"error parsing requirement: {exc}")
            logger.info(f"skip unsupported dependency {dep!r}")
            continue
        if check_requirement(pkg_req, projectname=projectname) is None:
            continue

        # respect optional package filter
        if packages and canonicalize_name(pkg_req.name) not in packages:
            continue
        try:
            latest_version = get_latest_version(
                pkg_req.name,
                exclude_newer=exclude_newer,
                exclude_newer_package=exclude_newer_package,
                constraint_file=constraint_file,
                python_platform=get_python_platform_from_req(pkg_req),
                python_version=get_min_python_version_from_req(pkg_req),
            )
        except subprocess.CalledProcessError as exc:
            # error getting latest version
            err = f"{exc}, output={exc.output}, stderr={exc.stderr}"
            logger.warning(f"error getting latest version for '{pkg_req}': {err}")
            latest_version = None
        spec = next(s for s in pkg_req.specifier)
        if latest_version is not None and latest_version != spec.version:
            updatable += 1
            version = (
                colorize_updated_version(spec.version, latest_version)
                if color
                else latest_version
            )
            if command == "check":
                logger.warning(f"found update '{dep}' --> {version}")
            else:
                logger.info(f"updating '{dep}' --> {version}")
                newdep = dep.replace(spec.version, latest_version, 1)
                update_pyproject_pkg(
                    newdep, pkg_req.name, project_dir, group=group, optional=optional
                )
    return updatable


def update_pyproject_pkg(
    dependency: str,
    package: str,
    projectdir: str,
    group: None | str = None,
    optional: bool = False,
) -> None:
    """Update one package in pyproject.toml."""
    command = [
        "uv",
        "add",
        "--project",
        projectdir,
        "--quiet",
        "--frozen",
        "--color=never",
        f"--upgrade-package={package}",
    ]
    if optional and group:
        command.append("--optional")
        command.append(group)
    elif group:
        command.append("--group")
        command.append(group)
    command.append(f"{dependency}")
    logger.debug(f"running {' '.join(command)}")
    subprocess.check_call(command)
