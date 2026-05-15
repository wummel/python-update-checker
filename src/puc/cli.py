# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""CLI to update pinned dependencies in pyproject.toml or requirements.txt files.
Needs uv (https://docs.astral.sh/uv/).
"""

import subprocess
import argparse
import sys
import logging
import os
import shlex
import tempfile
from packaging.utils import canonicalize_name
from typing import TextIO, Any

from .dependencies import (
    get_latest_version,
)
from .logging import logger
from .pyprojecttoml import handle_pyproject_toml
from .requirementstxt import handle_requirements_txt
from .uvlock import handle_uv_lock


def usage(msg: str | None = None) -> None:
    """Print usage info"""
    if msg:
        logger.error(msg)
    p = get_option_parser()
    logger.info(p.format_usage())
    sys.exit(-1)


def handle_latest(package, optargs, constraint_file):
    """Print latest version of package."""
    exclude_newer = optargs.exclude_newer
    try:
        latest_version = get_latest_version(
            package,
            exclude_newer=exclude_newer,
            constraint_file=constraint_file,
        )
        logger.info(f"{package}=={latest_version}")
    except subprocess.CalledProcessError as exc:
        # error getting latest version
        err = f"{exc}, output={exc.output}, stderr={exc.stderr}"
        logger.warning(f"error getting latest version for '{package}': {err}")


def supports_color(handle: TextIO | Any) -> bool:
    """Determine if given file handle is a TTY suitable for color output."""
    return hasattr(handle, "isatty") and handle.isatty()


def get_option_parser() -> argparse.ArgumentParser:
    """Initialize and return the option parser.
    @return: parser
    @rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exclude-newer",
        dest="exclude_newer",
        help="Limit package versions to those that were uploaded prior to the given date",
    )
    parser.add_argument(
        "--constraints",
        dest="constraints",
        help="Constrain versions using the given requirements file or string",
    )
    parser.add_argument(
        "--package",
        dest="packages",
        action="append",
        help="Only update the given package, can be given multiple times",
    )
    parser.add_argument(
        "--no-color",
        action="store_false",
        dest="color",
        default=supports_color(sys.stdout),
        help="Do not print colored updated versions.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="Print debug messages.",
    )
    subparsers = parser.add_subparsers(help='commands', dest='command')
    parser_check = subparsers.add_parser('check', help='check for updated versions')
    parser_check.add_argument(
        "dep_files",
        nargs="+",
        help="pyproject.toml or requirements.txt file",
    )

    parser_update = subparsers.add_parser('update', help='update to latest versions')
    parser_update.add_argument(
        "dep_files",
        nargs="+",
        help="pyproject.toml or requirements.txt file",
    )

    parser_latest = subparsers.add_parser(
        'latest', help='get latest version of packages'
    )
    parser_latest.add_argument(
        "packages",
        nargs="+",
        help="package names",
    )
    return parser


def handle_dependency_file(dep_file: str, optargs, constraint_file):
    """Check a dependency file for updates."""
    if not os.path.isfile(dep_file):
        usage(f"file {dep_file} not found or not a regular file")
    # limit to 1MB to prevent denial-of-service
    if os.stat(dep_file).st_size > 1024 * 1014:
        usage(f"file {dep_file} is >1 MB")
    dep_file_normalized = os.path.basename(dep_file).lower()
    if optargs.packages:
        packages = [canonicalize_name(name) for name in optargs.packages]
    else:
        packages = None
    if dep_file_normalized == "pyproject.toml":
        # pyproject.toml format
        updatable = handle_pyproject_toml(
            dep_file,
            packages=packages,
            command=optargs.command,
            exclude_newer=optargs.exclude_newer,
            constraint_file=constraint_file,
            color=optargs.color,
        )
    elif dep_file_normalized == "uv.lock":
        # pyproject.toml format
        updatable = handle_uv_lock(
            dep_file,
            packages=packages,
            command=optargs.command,
            exclude_newer=optargs.exclude_newer,
            constraint_file=constraint_file,
            color=optargs.color,
        )
    elif dep_file_normalized.endswith((".txt", ".in")):
        # requirements.txt format
        updatable = handle_requirements_txt(
            dep_file,
            packages=packages,
            command=optargs.command,
            exclude_newer=optargs.exclude_newer,
            constraint_file=constraint_file,
            color=optargs.color,
        )
    else:
        usage(
            f"no pyproject.toml or requirements.txt format detected for file {dep_file!r}"
        )
    return updatable


def main() -> int:
    """Parse options and check or update dependencies."""
    logger.info(f"{shlex.join(sys.argv)}")
    # parse options
    try:
        optargs = get_option_parser().parse_args(sys.argv[1:])
    except argparse.ArgumentError as exc:
        logger.exception(exc)
        usage()
    # handle options
    if optargs.debug:
        logger.setLevel(logging.DEBUG)
    remove_constraint_file = False
    constraints = optargs.constraints
    constraint_file = None
    # if constraints is a string write it in a temporary constraint file
    if constraints:
        if os.path.isfile(constraints):
            constraint_file = constraints
        else:
            _fd, constraint_file = tempfile.mkstemp(
                suffix=".txt", prefix="puc-constraints-"
            )
            with open(constraint_file, "w") as f:
                f.write(constraints)
            remove_constraint_file = True
    # handle all given dependency files
    try:
        if optargs.command in ("check", "update"):
            for dep_file in optargs.dep_files:
                updatable = handle_dependency_file(dep_file, optargs, constraint_file)
        elif optargs.command == "latest":
            for package in optargs.packages:
                handle_latest(package, optargs, constraint_file)
        elif not optargs.command:
            usage("missing command")
        else:
            usage(f"unknown command {optargs.command}")
    except Exception as exc:
        logger.error(f"error handling command {optargs.command}: {exc}")
        return -1
    finally:
        if remove_constraint_file and constraint_file:
            os.unlink(constraint_file)
    # check command returns non-zero exit code when updates are available
    return 1 if optargs.command == "check" and updatable > 0 else 0
