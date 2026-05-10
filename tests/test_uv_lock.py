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
"""Test pyproject.toml format."""

import unittest
import os
import subprocess
import shutil
from . import basedir, datadir, needs_program, tempdir


class UvLockTest(unittest.TestCase):
    """Test class for uv.lock format."""

    @needs_program('uv')
    def test_uvlock_check(self):
        """Run puc check"""
        filename = os.path.join(datadir, "uv.lock")
        cmd = ["uv", "run", "puc", "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertIn("found update 'ty==", output)
        self.assertIn("found update 'ruff==", output)

    @needs_program('uv')
    def test_uvlock_check_package(self):
        """Run puc check with package filter"""
        filename = os.path.join(datadir, "uv.lock")
        cmd = ["uv", "run", "puc", "--package", "ty", "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertIn("found update 'ty==", output)
        self.assertNotIn("found update 'ruff==", output)

    @needs_program('uv')
    def test_uvlock_update(self):
        """Run puc update"""
        # create a temporary directory for updating the file
        origfile = os.path.join(datadir, "uv.lock")
        tmpdir = tempdir(dir=basedir)
        shutil.copy(origfile, tmpdir)
        projectfile = os.path.join(datadir, "pyproject_compatible.toml")
        shutil.copy(projectfile, os.path.join(tmpdir, "pyproject.toml"))
        try:
            filename = os.path.join(tmpdir, "uv.lock")
            cmd = ["uv", "run", "puc", "update", filename]
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            output = result.stdout.strip()
            self.assertIn("updating 'ty==", output)
            self.assertIn("updating 'ruff==", output)
        finally:
            shutil.rmtree(tmpdir)
