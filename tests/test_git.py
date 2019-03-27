#
# test_git
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

from scmver import core, git, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('git'), 'requires Git')
class GitTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self):
        git.run('init')
        git.run('config', 'user.name', 'scmver')
        git.run('config', 'user.email', 'scmver@example.com')

    def touch(self, path):
        with open(os.path.join(self._root, path), 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.git'):
            self.assertIsNone(git.parse('.', name=name))

        self.init()
        self.assertEqual(git.parse('.', name='.git'), core.SCMInfo(branch='master'))

        self.touch('file')
        self.assertEqual(git.parse('.', name='.git'), core.SCMInfo(branch='master'))

        git.run('add', '.')
        self.assertEqual(git.parse('.', name='.git'), core.SCMInfo(dirty=True, branch='master'))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        git.run('add', '.')
        git.run('commit', '-m', '.')

        info = git.parse('.', name='.git')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'master')

    def test_simple(self):
        self.init()
        self.touch('file')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        git.run('tag', 'v1.0')

        info = git.parse('.', name='.git')
        self.assertEqual(info.tag, 'v1.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'master')

    def test_match(self):
        self.init()
        self.touch('file')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        git.run('tag', 'v1.0')
        git.run('tag', 'spam-1.0')

        for pat, tag in (
            ('v*.*', 'v1.0'),
            ('spam-*.*', 'spam-1.0'),
        ):
            info = git.parse('.', name='.git', **{'git.tag': pat})
            self.assertEqual(info.tag, tag)
            self.assertEqual(info.distance, 0)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'master')

    def test_detached_HEAD(self):
        self.init()
        self.touch('spam')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        self.touch('eggs')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        git.run('checkout', 'HEAD~1')

        info = git.parse('.', name='.git')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertIsNone(info.branch)
