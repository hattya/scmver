#
# test_setuptools
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import distutils.dist
import os
import sys
import textwrap

from scmver import core, setuptools
from base import SCMVerTestCase


class SetuptoolsTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

        self._rev = self.revision(b'scmver.setuptools')

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self, tag='v1.0'):
        with open(os.path.join(self._root, '.hg_archival.txt'), 'w') as fp:
            fp.write(textwrap.dedent("""\
                repo: {node}
                node: {node}
                branch: default
                latesttag: {tag}
                latesttagdistance: 0
                changessincelatesttag: 0
            """.format(node=self._rev, tag=tag)))
            fp.flush()

    def scmver(self, value):
        dist = distutils.dist.Distribution()
        setuptools.scmver(dist, 'scmver', value)
        return dist.metadata.version

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
        sys.path.append(self._root)
        try:
            self.assertEqual(self.scmver(value), '1.1')
        finally:
            sys.path.pop()

        value = {'fallback': ['beans:version', '.']}
        with open('beans.py', 'w') as fp:
            fp.write(core._TEMPLATE.format(version='1.2'))
            fp.flush()
        self.assertEqual(self.scmver(value), '1.2')
