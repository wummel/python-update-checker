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
        """Run pcu check"""
        filename = os.path.join(datadir, "requirements.txt")
        pcu = os.path.join(os.path.dirname(basedir), "pcu")
        cmd = [pcu, "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertIn("update 'argcomplete==", output)
        self.assertIn("update 'ty== ", output)
        self.assertIn("update 'ruff ==", output)
        self.assertIn("update 'pywin32==", output)
        self.assertIn("update 'certifi===", output)

    @needs_program('uv')
    def test_requirements_check_package(self):
        """Run pcu check with package filter"""
        filename = os.path.join(datadir, "requirements.txt")
        pcu = os.path.join(os.path.dirname(basedir), "pcu")
        cmd = [pcu, "--package", "ty", "check", filename]
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
        output = result.stdout.strip()
        self.assertTrue(result.returncode > 0)
        self.assertNotIn("update 'argcomplete==", output)
        self.assertIn("update 'ty== ", output)
        self.assertNotIn("update 'ruff ==", output)
        self.assertNotIn("update 'pywin32==", output)
        self.assertNotIn("update 'certifi===", output)

    @needs_program('uv')
    def test_requirements_update(self):
        """Run pcu update"""
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
            pcu = os.path.join(os.path.dirname(basedir), "pcu")
            cmd = [pcu, "update", filename]
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            output = result.stdout.strip()
            self.assertIn("update 'argcomplete==", output)
            self.assertIn("update 'ruff ==", output)
            self.assertIn("update 'pywin32==", output)
            self.assertIn("update 'certifi===", output)
            # from other-requirements.txt
            self.assertIn("update 'ty== ", output)
            # check that old package versions have been updated
            with open(filename) as f:
                content = f.read()
                for dep in packagedeps:
                    self.assertNotIn(dep, content)
        finally:
            shutil.rmtree(tmpdir)
