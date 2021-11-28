#
# test_darcs
#
#   Copyright (c) 2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import unittest

from scmver import darcs, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('darcs'), 'requires Darcs')
class DarcsTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

        self.branch = 'r'
        os.environ['DARCS_TESTING_PREFS_DIR'] = self._root
        with open('author', 'w') as fp:
            print('scmver <scmver@example.com>', file=fp)

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self):
        os.chdir(self._root)
        darcs.run('init', self.branch)
        os.chdir(self.branch)

    def clone(self, branch):
        os.chdir(self._root)
        darcs.run('clone', self.branch, branch)
        os.chdir(branch)

    def touch(self, path):
        with open(os.path.join(path), 'w'):
            pass

    def test_empty(self):
        for name in ('_', '_darcs'):
            with self.subTest(name=name):
                self.assertIsNone(darcs.parse('.', name=name))

        self.init()
        self.assertIsNotNone(darcs.parse('.', name='_darcs'))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        darcs.run('add', 'file')
        darcs.run('record', '-am', '.')

        info = darcs.parse('.', name='_darcs')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, self.branch)

    def test_simple(self):
        self.init()
        self.touch('file')
        darcs.run('add', 'file')
        darcs.run('record', '-am', '.')
        darcs.run('tag', 'v1.0')

        info = darcs.parse('.', name='_darcs')
        self.assertEqual(info.tag, 'v1.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, self.branch)

    def test_match(self):
        self.init()
        self.touch('file')
        darcs.run('add', 'file')
        darcs.run('record', '-am', '.')
        darcs.run('tag', 'v1.0')
        darcs.run('tag', 'spam-1.0')

        for pat, tag, d, in (
            (r'v\d+\..+', 'v1.0', 1),
            (r'spam-\d+\..+', 'spam-1.0', 0),
        ):
            with self.subTest(tag=tag):
                info = darcs.parse('.', name='_darcs', **{'darcs.tag': pat})
                self.assertEqual(info.tag, tag)
                self.assertEqual(info.distance, d)
                self.assertIsNotNone(info.revision)
                self.assertFalse(info.dirty)
                self.assertEqual(info.branch, self.branch)

        info = darcs.parse('.', name='_darcs', **{'darcs.tag': r'__scmver__'})
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 3)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, self.branch)

    def test_i18n(self):
        self.check_locale()

        self.init()
        self.clone('\u30d6\u30e9\u30f3\u30c1')
        self.touch('\u30d5\u30a1\u30a4\u30eb')
        darcs.run('add', '\u30d5\u30a1\u30a4\u30eb')
        darcs.run('record', '-am', '.')
        darcs.run('tag', '\u30bf\u30b0')

        info = darcs.parse('.', name='_darcs')
        self.assertEqual(info.tag, '\u30bf\u30b0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, '\u30d6\u30e9\u30f3\u30c1')

    def test_status(self):
        self.init()
        self.touch('file')

        info = darcs.parse('.', name='_darcs')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, self.branch)

        darcs.run('add', 'file')

        info = darcs.parse('.', name='_darcs')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNone(info.revision)
        self.assertTrue(info.dirty)
        self.assertEqual(info.branch, self.branch)

    def test_version(self):
        self.assertGreaterEqual(len(darcs.version()), 2)

        run = darcs.run
        try:
            for out, e in (
                ('2.5 (release)', (2, 5)),
                ('2.16.4 (release)', (2, 16, 4)),
                ('', ()),
            ):
                darcs.run = lambda *a, **kw: (out, '')
                self.assertEqual(darcs.version(), e)
        finally:
            darcs.run = run

    def test_run(self):
        env = {}
        darcs.run('help', env=env)
        self.assertEqual(env, {})
