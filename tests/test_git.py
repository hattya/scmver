#
# test_git
#
#   Copyright (c) 2019-2023 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
from pathlib import Path
import unittest
import unittest.mock

from scmver import core, git, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('git') and git.version() >= (1, 7, 10), 'requires Git 1.7.10+')
class GitTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = Path.cwd()
        self._dir = self.tempdir()
        self.root = Path(self._dir.name)
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self._cwd)
        self._dir.cleanup()

    def init(self):
        git.run('init')
        git.run('config', 'user.name', 'scmver')
        git.run('config', 'user.email', 'scmver@example.com')

    def touch(self, path):
        with open(path, 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.git'):
            with self.subTest(name=name):
                self.assertIsNone(git.parse(Path(), name=name))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        git.run('add', '.')
        git.run('commit', '-m', '.')

        info = git.parse(Path(), name='.git')
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

        info = git.parse(Path(), name='.git')
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
            with self.subTest(tag=tag):
                info = git.parse(Path(), name='.git', **{'git.tag': pat})
                self.assertEqual(info.tag, tag)
                self.assertEqual(info.distance, 0)
                self.assertIsNotNone(info.revision)
                self.assertFalse(info.dirty)
                self.assertEqual(info.branch, 'master')

    def test_i18n(self):
        self.init()
        git.run('checkout', '-b', '\u30d6\u30e9\u30f3\u30c1')
        self.touch('\u30d5\u30a1\u30a4\u30eb')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        git.run('tag', '\u30bf\u30b0')

        info = git.parse(Path(), name='.git')
        self.assertEqual(info.tag, '\u30bf\u30b0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, '\u30d6\u30e9\u30f3\u30c1')

    def test_detached_HEAD(self):
        self.init()
        self.touch('spam')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        self.touch('eggs')
        git.run('add', '.')
        git.run('commit', '-m', '.')
        git.run('checkout', 'HEAD~1')

        info = git.parse(Path(), name='.git')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertIsNone(info.branch)

    def test_status(self):
        self.init()
        self.touch('file')

        self.assertEqual(git.parse(Path(), name='.git'), core.SCMInfo(branch='master'))

        git.run('add', '.')

        self.assertEqual(git.parse(Path(), name='.git'), core.SCMInfo(dirty=True, branch='master'))

    def test_version(self):
        self.assertGreaterEqual(len(git.version()), 4)

        with unittest.mock.patch(f'{git.__name__}.run') as run:
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
                run.return_value = (out.format(v) if v else '', '')
                self.assertEqual(git.version(), e)

    def test_run(self):
        env = {}
        git.run('help', env=env)
        self.assertEqual(env, {})
