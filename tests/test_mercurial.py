#
# test_mercurial
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

import contextlib
import os
import textwrap
import unittest

from scmver import core, mercurial, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('hg'), 'requires Mercurial')
class MercurialTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self):
        mercurial.run('init')
        with open(os.path.join('.hg', 'hgrc'), 'w') as fp:
            fp.write(textwrap.dedent("""\
                [ui]
                username = scmver <scmver@example.com>
            """))
            fp.flush()

    @contextlib.contextmanager
    def archive(self):
        with self.tempdir() as path:
            mercurial.run('archive', path)
            os.chdir(path)
            try:
                yield path
            finally:
                os.chdir(self._root)

    def touch(self, path):
        with open(os.path.join(self._root, path), 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.hg', '.hg_archival.txt'):
            self.assertIsNone(mercurial.parse('.', name=name))

    def test_no_tags(self):
        self.init()
        self.assertEqual(mercurial.parse('.', name='.hg'), core.SCMInfo(branch='default'))

        self.touch('file')
        mercurial.run('add', '.')
        mercurial.run('commit', '-m', '.')

        info = mercurial.parse('.', name='.hg')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'default')

        with self.archive():
            info = mercurial.parse('.', name='.hg_archival.txt')
            self.assertEqual(info.tag, '0.0')
            self.assertEqual(info.distance, 1)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'default')

    def test_simple(self):
        self.init()
        self.touch('file')
        mercurial.run('add', '.')
        mercurial.run('commit', '-m', '.')
        mercurial.run('tag', 'v1.0')

        info = mercurial.parse('.', name='.hg')
        self.assertEqual(info.tag, 'v1.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'default')

        with self.archive():
            info = mercurial.parse('.', name='.hg_archival.txt')
            self.assertEqual(info.tag, 'v1.0')
            self.assertEqual(info.distance, 1)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'default')

    def test_match(self):
        self.init()
        self.touch('file')
        mercurial.run('add', '.')
        mercurial.run('commit', '-m', '.')
        mercurial.run('tag', 'v1.0', 'spam-1.0')

        for pat, tag in ((r'v\d+\..*', 'v1.0'),
                         (r'spam-\d+\..*', 'spam-1.0')):
            info = mercurial.parse('.', name='.hg', **{'mercurial.tag': pat})
            self.assertEqual(info.tag, tag)
            self.assertEqual(info.distance, 1)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'default')

        info = mercurial.parse('.', name='.hg', **{'mercurial.tag': r'__scmver__'})
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 2)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'default')

        with self.archive():
            for pat, tag in ((r'v\d+\..*', 'v1.0'),
                             (r'spam-\d+\..*', 'spam-1.0')):
                info = mercurial.parse('.', name='.hg_archival.txt', **{'mercurial.tag': pat})
                self.assertEqual(info.tag, tag)
                self.assertEqual(info.distance, 1)
                self.assertIsNotNone(info.revision)
                self.assertFalse(info.dirty)
                self.assertEqual(info.branch, 'default')

            with self.assertRaises(ValueError):
                mercurial.parse('.', name='.hg_archival.txt', **{'mercurial.tag': r'__scmver__'})