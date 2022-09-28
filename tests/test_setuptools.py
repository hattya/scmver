#
# test_setuptools
#
#   Copyright (c) 2019-2022 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import distutils.dist
import os
import sys
import textwrap
import unittest

try:
    import tomli
except ImportError:
    tomli = None

from scmver import core, setuptools
from base import SCMVerTestCase


class SetuptoolsTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._dir = self.tempdir()
        self.root = self._dir.name
        os.chdir(self.root)

        self._rev = self.revision(b'scmver.setuptools')

    def tearDown(self):
        os.chdir(self._cwd)
        self._dir.cleanup()

    def init(self, tag='v1.0'):
        with open('.hg_archival.txt', 'w') as fp:
            fp.write(textwrap.dedent(f"""\
                repo: {self._rev}
                node: {self._rev}
                branch: default
                tag: {tag}
            """))
            fp.flush()

    def finalize_version(self, scmver):
        with open('pyproject.toml', 'w') as fp:
            fp.write(textwrap.dedent("""\
                [build-system]
                requires = [
                    "setuptools >= 42",
                    "scmver[toml] >= 1.5",
                ]
                build-backend = "setuptools.build_meta"
            """))
            if scmver is not None:
                fp.write('[tool.scmver]\n')
                for k, v in scmver.items():
                    fp.write(f'{k} = {v!r}\n')
            fp.flush()

        dist = distutils.dist.Distribution()
        setuptools.finalize_version(dist)
        return dist.metadata.version

    def scmver(self, value):
        dist = distutils.dist.Distribution()
        setuptools.scmver(dist, 'scmver', value)
        return dist.metadata.version

    @unittest.skipUnless(tomli, 'requires tomli')
    def test_finalize_version(self):
        self.init()
        self.assertIsNone(self.finalize_version(None))
        self.assertEqual(self.finalize_version({}), '1.0')

    @unittest.skipUnless(tomli, 'requires tomli')
    def test_finalize_version_fallback(self):
        scmver = {'fallback': 'toast:version'}
        with open('toast.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.1'))
            fp.flush()
        sys.path.append(self.root)
        try:
            self.assertEqual(self.finalize_version(scmver), '1.1')
        finally:
            sys.path.pop()

        scmver = {'fallback': ['beans:version', '.']}
        with open('beans.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.2'))
            fp.flush()
        self.assertEqual(self.finalize_version(scmver), '1.2')

    def test_scmver_with_boolean(self):
        self.init()
        self.assertIsNone(self.scmver(False))
        self.assertEqual(self.scmver(True), '1.0')

    def test_scmver_with_callable(self):
        self.assertIsNone(self.scmver(lambda: {}))

    def test_scmver_scm_tag(self):
        self.init()

        value = {'mercurial.tag': r'v\d+\..+'}
        self.assertEqual(self.scmver(value), '1.0')

        with self.assertRaises(ValueError):
            value = {'mercurial.tag': r'__scmver__'}
            self.scmver(value)

    def test_scmver_write_to(self):
        self.init()

        value = {'write_to': '__version__.py'}
        self.assertEqual(self.scmver(value), '1.0')
        with open(value['write_to']) as fp:
            self.assertEqual(fp.read(), core._TEMPLATE.format(version='1.0'))

        value['template'] = "__version__ = '{version}'\n"
        self.assertEqual(self.scmver(value), '1.0')
        with open(value['write_to']) as fp:
            self.assertEqual(fp.read(), value['template'].format(version='1.0'))

    def test_scmver_fallback(self):
        value = {'fallback': lambda: '1.0'}
        self.assertEqual(self.scmver(value), '1.0')

        value = {'fallback': 'toast:version'}
        with open('toast.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.1'))
            fp.flush()
        sys.path.append(self.root)
        try:
            self.assertEqual(self.scmver(value), '1.1')
        finally:
            sys.path.pop()

        value = {'fallback': ['beans:version', '.']}
        with open('beans.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.2'))
            fp.flush()
        self.assertEqual(self.scmver(value), '1.2')
