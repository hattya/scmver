#
# test_git
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import unittest

from scmver import core, git, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('git') and git.version() >= (1, 7, 10), 'requires Git 1.7.10+')
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

    def test_version(self):
        self.assertGreaterEqual(len(git.version()), 4)

        run = git.run
        try:
            out = 'git version {}'
            for v, e in (
                ('2.21.0', (2, 21, 0, 0)),
                ('2.21.0.windows.1', (2, 21, 0, 0, 'windows', 1)),
                ('2.21.0-rc2', (2, 21, 0, 0, 'rc', 2)),
                ('2.21.0-rc2.windows.1', (2, 21, 0, 0, 'rc', 2, 'windows', 1)),
                ('1.8.5.2', (1, 8, 5, 2)),
                ('1.8.5.2.msysgit.0', (1, 8, 5, 2, 'msysgit', 0)),
                ('1.0.0b', (1, 0, 0, 0, 'b')),
                ('', ()),
            ):
                git.run = lambda *a, **kw: (out.format(v) if v else '', '')
                self.assertEqual(git.version(), e)
        finally:
            git.run = run
