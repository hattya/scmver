#
# test_bazaar
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#

import os
import unittest

from scmver import core, bazaar as bzr, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('bzr'), 'requires Bazaar')
class BazaarTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self):
        bzr.run('init-repository', self._root)
        bzr.run('init', 'trunk')
        os.chdir('trunk')
        bzr.run('whoami', '--branch', 'scmver <scmver@example.com>')

    def touch(self, path):
        with open(os.path.join(self._root, 'trunk', path), 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.bzr'):
            self.assertIsNone(bzr.parse('.', name=name))

        self.init()
        self.assertIsNone(bzr.parse('..', name='.bzr'))
        self.assertEqual(bzr.parse('.', name='.bzr'), core.SCMInfo(revision='0', dirty=True, branch='trunk'))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        bzr.run('add', '.')
        bzr.run('commit', '-m', '_')

        self.assertEqual(bzr.parse('.', name='.bzr'), core.SCMInfo(distance=1, revision='1', branch='trunk'))

    def test_simple(self):
        self.init()
        self.touch('file')
        bzr.run('add', '.')
        bzr.run('commit', '-m', '_')
        bzr.run('tag', 'v1.0')

        self.assertEqual(bzr.parse('.', name='.bzr'), core.SCMInfo('v1.0', 0, '1', False, 'trunk'))

    def test_match(self):
        self.init()
        self.touch('file')
        bzr.run('add', '.')
        bzr.run('commit', '-m', '_')
        bzr.run('tag', 'v1.0')
        bzr.run('tag', 'spam-1.0')

        for pat, tag in (
            (r'v\d+\..+', 'v1.0'),
            (r'spam-\d+\..+', 'spam-1.0'),
        ):
            kwargs = {'bazaar.tag': pat}
            self.assertEqual(bzr.parse('.', name='.bzr', **kwargs), core.SCMInfo(tag, 0, '1', False, 'trunk'))
