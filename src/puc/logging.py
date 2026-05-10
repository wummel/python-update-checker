# Author: Bastian Kleineidam
# Copyright: GPL-v3
"""Logging initialization."""

import logging
import sys

logger = logging.getLogger("puc")


def init_logging(stream=sys.stdout) -> None:
    """Configure the global logger.
    All log messages will be sent to the given stream, default is sys.stdout.
    """
    # do not propagate log message to higher log level handlers (in our case the root level)
    logger.propagate = False
    handler = logging.StreamHandler(stream=stream)
    format = "%(name)s %(levelname)s: %(message)s"
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    # set the log level to INFO, and change to DEBUG with --verbose
    logger.setLevel(logging.INFO)


init_logging()


# ANSI color codes
ansi_colors = {
    'red': '\033[31m',
    'cyan': '\033[36m',
    'green': '\033[32m',
    'reset': '\033[0m',
}


def colorize_updated_version(from_ver: str, to_ver: str) -> str:
    """Colorize an updated version `to_ver` (`from_ver` is the old version).
    Assumes both versions are semver strings.
    Logic for coloring:
    - red: major version change or any change before 1.0.0
    - cyan: minor version change
    - green: patch version change
    """
    # split into parts for comparing
    parts_to_ver = to_ver.split('.')
    parts_from_ver = from_ver.split('.')

    # find the index of the first difference
    index = len(parts_to_ver)
    for i, part in enumerate(parts_to_ver):
        if i >= len(parts_from_ver):
            # '1' --> '1.1'
            index = i
            break
        if part != parts_from_ver[i]:
            # '1.0' --> '1.1'
            index = i
            break

    # coloring
    if index == 0 or (len(parts_to_ver) > 0 and parts_to_ver[0] == '0'):
        color = 'red'
    elif index == 1:
        color = 'cyan'
    else:
        color = 'green'

    # construct the final string
    first_part = ".".join(parts_to_ver[:index])
    second_part = ".".join(parts_to_ver[index:])
    middle_dot = '.' if 0 < index < len(parts_to_ver) else ""
    if second_part:
        # add color
        second_part = f"{ansi_colors[color]}{second_part}{ansi_colors['reset']}"
    return f"{first_part}{middle_dot}{second_part}"
