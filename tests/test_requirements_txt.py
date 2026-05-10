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
"""Test requirements.txt format."""

import unittest
import os
import subprocess
import shutil
from . import basedir, datadir, needs_program, tempdir


class RequirementsTxtTest(unittest.TestCase):
    """Test class for requirements.txt format."""

    @needs_program('uv')
    def test_requirements_check(self):
        """Run puc check"""
        filename = os.path.join(datadir, "requirements.txt")
        cmd = ["uv", "run", "puc", "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertIn("found update 'argcomplete==", output)
        self.assertIn("found update 'ty== ", output)
        self.assertIn("found update 'ruff ==", output)
        self.assertIn("found update 'pywin32==", output)
        self.assertIn("found update 'certifi===", output)

    @needs_program('uv')
    def test_requirements_check_package(self):
        """Run puc check with package filter"""
        filename = os.path.join(datadir, "requirements.txt")
        cmd = ["uv", "run", "puc", "--package", "ty", "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertNotIn("found update 'argcomplete==", output)
        self.assertIn("found update 'ty== ", output)
        self.assertNotIn("found update 'ruff ==", output)
        self.assertNotIn("found update 'pywin32==", output)
        self.assertNotIn("found update 'certifi===", output)

    @needs_program('uv')
    def test_requirements_update(self):
        """Run puc update"""
        # create a temporary directory for updating the file
        origfile = os.path.join(datadir, "requirements.txt")
        otherfile = os.path.join(datadir, "other-requirements.txt")
        tmpdir = tempdir(dir=basedir)
        shutil.copy(origfile, tmpdir)
        shutil.copy(otherfile, tmpdir)
        try:
            filename = os.path.join(tmpdir, "requirements.txt")
            packagedeps = (
                "argcomplete==3.6.1",
                "ruff ==0.15.9",
                "pywin32==310",
                "certifi===2026.1.4",
            )
            with open(filename) as f:
                content = f.read()
                for dep in packagedeps:
                    self.assertIn(dep, content)
            cmd = ["uv", "run", "puc", "update", filename]
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            output = result.stdout.strip()
            self.assertIn("updating 'argcomplete==", output)
            self.assertIn("updating 'ruff ==", output)
            self.assertIn("updating 'pywin32==", output)
            self.assertIn("updating 'certifi===", output)
            # from other-requirements.txt
            self.assertIn("updating 'ty== ", output)
            # check that old package versions have been updated
            with open(filename) as f:
                content = f.read()
                for dep in packagedeps:
                    self.assertNotIn(dep, content)
        finally:
            shutil.rmtree(tmpdir)
