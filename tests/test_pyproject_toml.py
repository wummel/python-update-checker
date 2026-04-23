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


class PyprojectTomlTest(unittest.TestCase):
    """Test class for pyproject.toml format."""

    @needs_program('uv')
    def test_pyproject_check(self):
        """Run pcu check"""
        filename = os.path.join(datadir, "pyproject.toml")
        pcu = os.path.join(os.path.dirname(basedir), "pcu")
        cmd = [pcu, "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertIn("update 'argcomplete==", output)
        self.assertIn("update 'ty== ", output)
        self.assertIn("update 'ruff ==", output)
        self.assertIn("update 'tensorflow==", output)
        self.assertIn("update 'certifi===", output)

    @needs_program('uv')
    def test_pyproject_check_package(self):
        """Run pcu check with package filter"""
        filename = os.path.join(datadir, "pyproject.toml")
        pcu = os.path.join(os.path.dirname(basedir), "pcu")
        cmd = [pcu, "--package", "ty", "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertNotIn("update 'argcomplete==", output)
        self.assertIn("update 'ty== ", output)
        self.assertNotIn("update 'ruff ==", output)
        self.assertNotIn("update 'tensorflow==", output)
        self.assertNotIn("update 'certifi===", output)

    @needs_program('uv')
    def test_pyproject_update(self):
        """Run pcu update"""
        # create a temporary directory for updating the file
        origfile = os.path.join(datadir, "pyproject.toml")
        tmpdir = tempdir(dir=basedir)
        shutil.copy(origfile, tmpdir)
        try:
            filename = os.path.join(tmpdir, "pyproject.toml")
            packagedeps = (
                "argcomplete==3.6.1",
                "ty== 0.0.29",
                "ruff ==0.15.9",
                "tensorflow==2.14.0",
                "certifi===2026.1.4",
            )
            with open(filename) as f:
                content = f.read()
                for dep in packagedeps:
                    self.assertIn(dep, content)
            pcu = os.path.join(os.path.dirname(basedir), "pcu")
            cmd = [pcu, "update", filename]
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            output = result.stdout.strip()
            self.assertIn("update 'argcomplete==", output)
            self.assertIn("update 'ty== ", output)
            self.assertIn("update 'ruff ==", output)
            self.assertIn("update 'tensorflow==", output)
            self.assertIn("update 'certifi===", output)
            self.assertIn("skip include-group dependency", output)
            # check that old package versions have been updated
            with open(filename) as f:
                content = f.read()
                for dep in packagedeps:
                    self.assertNotIn(dep, content)
        finally:
            shutil.rmtree(tmpdir)
