# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Handle requirements.txt files."""

import subprocess
import os
import re
import io
from packaging.utils import canonicalize_name

from .logging import logger, colorize_updated_version
from .dependencies import (
    get_latest_version,
    get_python_platform_from_req,
    get_min_python_version_from_req,
    parse_requirement,
)


# maximum recursion level for requirements.txt
max_rec_level = 5


def handle_requirements_txt(
    requirements_txt_path: str,
    command: None | str = None,
    packages=None,
    exclude_newer: None | str = None,
    exclude_newer_package: None | str = None,
    constraint_file: None | str = None,
    color: bool = True,
    rec_level: int = 0,
    handled_files: list[str] | None = None,
) -> int:
    """Check or update pinned dependencies of a requirements.txt file."""
    msg = f"{command} requirements file {requirements_txt_path}"
    if rec_level > 0:
        msg += f", recursion level {rec_level}"
    logger.info(msg)
    if rec_level > max_rec_level:
        logger.error(f"recursion level greater than maximum {max_rec_level}, ignoring")
        return 0
    if handled_files is None:
        handled_files = [os.path.abspath(requirements_txt_path)]
    else:
        handled_files.append(os.path.abspath(requirements_txt_path))
    output = io.StringIO()
    updatable = 0
    with open(requirements_txt_path) as f:
        for line in f:
            pkg_req = parse_requirement(
                line, exclude_newer=exclude_newer, constraint_file=constraint_file
            )
            if pkg_req is None:
                output.write(line)
            elif isinstance(pkg_req, str):
                output.write(line)
                base_dir = os.path.dirname(requirements_txt_path)
                requirements_txt_child = os.path.join(base_dir, pkg_req)
                if os.path.abspath(requirements_txt_child) not in handled_files:
                    updatable += handle_requirements_txt(
                        requirements_txt_child,
                        command,
                        packages=packages,
                        exclude_newer=exclude_newer,
                        exclude_newer_package=exclude_newer_package,
                        constraint_file=constraint_file,
                        color=color,
                        rec_level=rec_level + 1,
                        handled_files=handled_files,
                    )
            else:
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
                    logger.warning(
                        f"error getting latest version for {pkg_req.name!r}: {err}"
                    )
                    latest_version = None
                spec = next(s for s in pkg_req.specifier)
                if packages and canonicalize_name(pkg_req.name) not in packages:
                    output.write(line)
                elif latest_version is not None and latest_version != spec.version:
                    updatable += 1
                    version = (
                        colorize_updated_version(spec.version, latest_version)
                        if color
                        else latest_version
                    )
                    if command == "check":
                        logger.warning(f"found update '{line.strip()}' --> {version}")
                        output.write(line)
                    else:
                        logger.info(f"updating '{line.strip()}' --> {version}")
                        output.write(
                            re.sub(
                                rf"(===?\s*){re.escape(spec.version)}",
                                rf"\g<1>{latest_version}",
                                line,
                                count=1,
                            )
                        )
                else:
                    output.write(line)
    if command == "update":
        if updatable > 0:
            with open(requirements_txt_path, "w") as f:
                f.write(output.getvalue())
        logger.info("updated {updatable} package version(s) in {requirements_txt_path}")
    return updatable
