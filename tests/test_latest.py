# Copyright (C) 2026 Bastian Kleineidam
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Test latest version printing for packages."""

import unittest
import os
import subprocess
import shutil
from . import basedir, datadir, needs_program, tempdir


class LatestTest(unittest.TestCase):
    """Test class for 'pcu latest' command."""

    @needs_program('uv')
    def test_pyproject_check(self):
        """Run pcu latest"""
        pcu = os.path.join(os.path.dirname(basedir), "pcu")
        cmd = [pcu, "latest", "Django", "requests"]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode == 0)
        self.assertIn("Django==", output)
        self.assertIn("requests==", output)
