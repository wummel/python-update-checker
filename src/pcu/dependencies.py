# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Dependency helper functions."""

import subprocess
import re
from packaging.requirements import Requirement
from packaging.markers import Variable, MarkerList
from packaging.version import parse as parse_version
from .logging import logger


def get_latest_version(
    package: str,
    exclude_newer: None | str = None,
    constraint_file: None | str = None,
    python_platform: str | None = None,
    python_version: str | None = None,
) -> str:
    """Get the latest version of a package.
    `python_platform` defines the platform for which requirements should be resolved.
    `python_version` defines the minimum Python version that must be supported by the resolved requirements. If a patch version is omitted, the minimum patch version is assumed. For example, 3.8 is mapped to 3.8.0.
    """
    cmd = [
        "uv",
        "pip",
        "compile",
        "-",
        "--color=never",
        "--quiet",
        "--no-deps",
        "--no-header",
        "--no-annotate",
        "--no-progress",
    ]
    if exclude_newer:
        cmd.extend(("--exclude-newer", exclude_newer))
    if constraint_file:
        cmd.extend(("--constraints", constraint_file))
    if python_platform:
        cmd.extend(("--python-platform", python_platform))
    if python_version:
        cmd.extend(("--python-version", python_version))
    logger.debug(f"running '{' '.join(cmd)}' with input {package!r}")
    result = subprocess.run(
        cmd, check=True, text=True, input=package, capture_output=True
    )
    package_spec = result.stdout.strip()
    return package_spec.split("==", 1)[1]


def get_python_platform(
    os_name: str | None = None, sys_platform: str | None = None
) -> str | None:
    """Translate os_name or sys_platform values into python uv --python-platform values.
    The translation is very coarse and not complete, but should be suitable for common
    cases.
    See https://peps.python.org/pep-0508/#environment-markers and
    https://docs.astral.sh/uv/reference/cli/#uv-pip-compile--python-platform
    """
    if os_name == "nt":
        return "windows"
    if os_name == "posix":
        return "linux"
    if sys_platform == "win32":
        return "windows"
    if sys_platform == "linux":
        return "linux"
    if sys_platform == "darwin":
        return "macos"
    return None


def check_requirement(
    pkg_req: Requirement, projectname: str | None = None
) -> Requirement | None:
    """Check if requirement is pinned, else log and return None."""
    if projectname and pkg_req.name == projectname:
        logger.info(f"skip project name dependency {pkg_req}")
        return None
    if pkg_req.url:
        logger.info(f"skip URL-pinned package dependency '{pkg_req}'")
        return None
    if len(pkg_req.specifier) < 1:
        logger.info(f"skip non-versioned dependency '{pkg_req}'")
        return None
    if len(pkg_req.specifier) > 1:
        logger.info(f"skip multi-versioned dependency '{pkg_req}'")
        return None
    for spec in pkg_req.specifier:
        if spec.operator not in ('==', '==='):
            logger.info(f"skip unpinned dependency '{pkg_req}'")
            return None
        if "*" in spec.version:
            logger.info(f"skip unpinned *-patterned version dependency '{pkg_req}'")
            return None
        return pkg_req
    return None


def get_python_platform_from_req(pkg_req: Requirement) -> str | None:
    """Determine value to use for 'uv pip compile --python-platform'"""
    if not pkg_req.marker:
        return None
    markerlist = pkg_req.marker._markers
    return get_python_platform(
        os_name=get_marker_value(markerlist, "os_name", opfilter=("==",)),
        sys_platform=get_marker_value(markerlist, "sys_platform", opfilter=("==",)),
    )


def get_min_python_version_from_req(pkg_req: Requirement) -> str | None:
    """Determine value to use for 'uv pip compile --python-version'"""
    if not pkg_req.marker:
        return None
    markerlist = pkg_req.marker._markers
    return get_marker_value(markerlist, "python_version", opfilter=(">=", ""))


def parse_requirement(
    line: str,
    exclude_newer: None | str = None,
    constraint_file: None | str = None,
) -> None | str | Requirement:
    """Parse one line of a requirements.txt file."""
    line = line.strip()
    if not line or line.startswith("#"):
        # ignore comments
        return None
    if line.endswith("\\"):
        line = line[:-1]
    if line.startswith("--hash"):
        logger.info(f"ignore requirements hash {line!r}")
        return None
    if re.search(r"^-r\s+", line):
        # recursion
        return line.split(maxsplit=1)[1].strip()
    if re.search(r"^-c\s+", line):
        logger.info(
            f"ignore constraints reference {line!r}, use pcu --constraints instead"
        )
        return None
    if line.startswith("./"):
        # ignore local file references
        logger.info(f"skip local-file pinned dependency {line!r}")
        return None
    if line.lower().startswith(("http://", "https://")):
        # ignore local file references
        logger.info(f"skip URL-pinned dependency {line!r}")
        return None
    # remove trailing comment
    line = re.sub("#.*$", "", line)
    try:
        pkg_req = Requirement(line)
    except Exception as exc:
        logger.debug(f"error parsing exception: {exc}")
        logger.info(f"skip unsupported dependency {line!r}")
        return None
    return check_requirement(pkg_req)


def get_marker_value(
    markerlist: MarkerList, varname: str, opfilter: tuple[str, ...] | None = None
) -> str | None:
    """Search variable definitions in markerlist.
    `varname`: variable name to match
    `opfilter`: optional operator string to match.
    """
    for marker in markerlist:
        if isinstance(marker, tuple):
            left, op, right = marker
            if opfilter and op.serialize() not in opfilter:
                continue
            if isinstance(left, Variable):
                var = left.value
                value = right.value
            else:
                var = right.value
                value = left.value
            if var == varname:
                return value
    return None


def is_newer_version(old_version, new_version):
    """Check that new_version is newer than old_version."""
    return parse_version(new_version) > parse_version(old_version)
