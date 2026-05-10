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
import subprocess
from . import needs_program


class LatestTest(unittest.TestCase):
    """Test class for 'puc latest' command."""

    @needs_program('uv')
    def test_pyproject_check(self):
        """Run puc latest"""
        cmd = ["uv", "run", "puc", "latest", "Django", "requests"]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode == 0)
        self.assertIn("Django==", output)
        self.assertIn("requests==", output)
