#
# test_setuptools
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
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
                    "setuptools >= 42.0",
                    "scmver[toml] >= 1.5",
                ]
                build-backend = "setuptools.build_meta"
            """))
            if scmver is not None:
                fp.write('[tool.scmver]\n')
                for k, v in scmver.items():
                    if isinstance(v, str):
                        fp.write(f'{k} = "{v}"\n')
                    elif isinstance(v, list):
                        fp.write(f'{k} = [')
                        fp.write(', '.join(f'"{v}"' for v in v))
                        fp.write(']\n')
                    elif isinstance(v, dict):
                        fp.write(f'{k} = {{')
                        fp.write(', '.join(f'{k} = "{v}"' for k, v in v.items()))
                        fp.write('}\n')
            fp.flush()

        dist = distutils.dist.Distribution()
        setuptools.finalize_version(dist)
        return dist.metadata.version

    def scmver(self, value):
        dist = distutils.dist.Distribution()
        setuptools.scmver(dist, 'scmver', value)
        return dist.metadata.version

    @unittest.skipUnless(sys.version_info >= (3, 11) or tomli, 'requires tomli')
    def test_finalize_version(self):
        self.init()
        self.assertIsNone(self.finalize_version(None))
        self.assertEqual(self.finalize_version({}), '1.0')

    @unittest.skipUnless(sys.version_info >= (3, 11) or tomli, 'requires tomli')
    def test_finalize_version_fallback(self):
        os.mkdir('src')

        scmver = {'fallback': 'toast:version'}
        with open('toast.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.1'))
            fp.flush()
        self.assertEqual(self.finalize_version(scmver), '1.1')

        scmver = {'fallback': ['beans:version', 'src']}
        with open(os.path.join('src', 'beans.py'), 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.2'))
            fp.flush()
        self.assertEqual(self.finalize_version(scmver), '1.2')

        scmver = {'fallback': {'attr': 'bacon:version'}}
        with open('bacon.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.3'))
            fp.flush()
        self.assertEqual(self.finalize_version(scmver), '1.3')

        scmver = {'fallback': {'attr': 'sausage:version', 'path': 'src'}}
        with open(os.path.join('src', 'sausage.py'), 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.4'))
            fp.flush()
        self.assertEqual(self.finalize_version(scmver), '1.4')

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
        os.mkdir('src')

        value = {'fallback': lambda: '1.0'}
        self.assertEqual(self.scmver(value), '1.0')

        value = {'fallback': 'tomato:version'}
        with open('tomato.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.1'))
            fp.flush()
        self.assertEqual(self.scmver(value), '1.1')

        value = {'fallback': ['lobster:version', 'src']}
        with open(os.path.join('src', 'lobster.py'), 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.2'))
            fp.flush()
        self.assertEqual(self.scmver(value), '1.2')

        value = {'fallback': None}
        self.assertIsNone(self.scmver(value))
