# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Handle pyproject.toml files."""

import subprocess
import os
import tomllib
import logging
from packaging.utils import canonicalize_name
from packaging.requirements import Requirement

from .logging import logger, colorize_updated_version
from .dependencies import (
    get_latest_version,
    get_python_platform_from_req,
    get_min_python_version_from_req,
    check_requirement,
    is_newer_version,
)


def handle_pyproject_toml(
    pyproject_path: str,
    command: str | None = None,
    packages=None,
    exclude_newer: str | None = None,
    exclude_newer_package: str | None = None,
    exclude_packages=None,
    constraint_file: str | None = None,
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
        project = pyproject.get("project", {})
        if not project:
            logger.warning(f"no project defined in {pyproject_path}")
            return updatable
        if pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {}):
            logger.warning(f"[tool.poetry.dependencies] detected in {pyproject_path}")
            logger.warning(
                "consider migrating to uv, see https://docs.astral.sh/uv/guides/migration/"
            )
        projectname = project.get("name", None)
        logger.debug(f"found project name {projectname}")
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
                exclude_packages=exclude_packages,
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
                exclude_packages=exclude_packages,
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
                exclude_packages=exclude_packages,
                constraint_file=constraint_file,
                color=color,
            )
        # update legacy uv dev dependencies
        # See https://docs.astral.sh/uv/concepts/projects/dependencies/#legacy-dev-dependencies
        tool_uv = pyproject.get("tool", {}).get("uv", {})
        deps = tool_uv.get("dev-dependencies", [])
        if deps:
            logger.warning(
                f"Found legacy tool.uv.dev-dependencies in {pyproject_path}, replace with dependency-groups.dev"
            )
            logger.warning(
                "See https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies"
            )
            updatable += update_pyproject_dependencies(
                deps,
                project_dir,
                projectname,
                group="dev",
                command=command,
                packages=packages,
                exclude_newer=exclude_newer,
                exclude_newer_package=exclude_newer_package,
                exclude_packages=exclude_packages,
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
    group: str | None = None,
    optional=False,
    command: str | None = None,
    packages=None,
    exclude_newer: str | None = None,
    exclude_newer_package: str | None = None,
    exclude_packages=None,
    constraint_file: str | None = None,
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
            logger.info(f"skip filtered package {pkg_req.name!r}")
            continue
        if exclude_packages and canonicalize_name(pkg_req.name) in exclude_packages:
            logger.info(f"skip excluded package {pkg_req.name!r}")
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
            if not is_newer_version(spec.version, latest_version):
                logger.warning(
                    f"{pkg_req.name} latest version {latest_version} is older than specified version {spec.version}"
                )
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
    group: str | None = None,
    optional: bool = False,
) -> None:
    """Update one package in pyproject.toml."""
    command = [
        "uv",
        "add",
        "--project",
        projectdir,
        "--frozen",
        "--color=never",
        "--upgrade-package",
        package,
    ]
    if logger.getEffectiveLevel() <= logging.DEBUG:
        command.append("--verbose")
    else:
        command.append("--quiet")
    if optional and group:
        command.append("--optional")
        command.append(group)
    elif group:
        command.append("--group")
        command.append(group)
    command.append(f"{dependency}")
    logger.debug(f"running {' '.join(command)}")
    subprocess.check_call(command)
