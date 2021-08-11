#
# test_fossil
#
#   Copyright (c) 2019-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import unittest

from scmver import fossil as fsl, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('fossil') and fsl.version() >= (1, 32), 'requires Fossil 1.32+')
class FossilTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

        self._checkout = os.path.join(self._root, 'scmver')
        os.environ['FOSSIL_HOME'] = self._root
        os.environ['FOSSIL_USER'] = 'scmver'

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self):
        repo = self._checkout + '.fossil'
        fsl.run('init', repo)
        os.makedirs(self._checkout)
        os.chdir(self._checkout)
        fsl.run('open', repo)

    def touch(self, path):
        with open(os.path.join(self._checkout, path), 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.fslckout', '_FOSSIL_'):
            with self.subTest(name=name):
                self.assertIsNone(fsl.parse('.', name=name))

        self.init()
        self.assertIsNotNone(fsl.parse('.', name='_FOSSIL_'))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        fsl.run('add', '.')
        fsl.run('commit', '-m', '.')

        info = fsl.parse('.', name='_FOSSIL_')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 2)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'trunk')

    def test_simple(self):
        self.init()
        self.touch('file')
        fsl.run('add', '.')
        fsl.run('commit', '-m', '.')
        fsl.run('tag', 'add', 'v1.0', 'current')

        info = fsl.parse('.', name='_FOSSIL_')
        self.assertEqual(info.tag, 'v1.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'trunk')

    def test_match(self):
        self.init()
        self.touch('file')
        fsl.run('add', '.')
        fsl.run('commit', '-m', '.')
        fsl.run('tag', 'add', 'v1.0', 'current')
        fsl.run('tag', 'add', 'spam-1.0', 'current')

        for pat, tag in (
            (r'v\d+\..+', 'v1.0'),
            (r'spam-\d+\..+', 'spam-1.0'),
        ):
            with self.subTest(tag=tag):
                info = fsl.parse('.', name='_FOSSIL_', **{'fossil.tag': pat})
                self.assertEqual(info.tag, tag)
                self.assertEqual(info.distance, 0)
                self.assertIsNotNone(info.revision)
                self.assertFalse(info.dirty)
                self.assertEqual(info.branch, 'trunk')

        info = fsl.parse('.', name='_FOSSIL_', **{'fossil.tag': r'__scmver__'})
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 2)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'trunk')

    def test_i18n(self):
        self.check_locale()

        self.init()
        self.touch('\u30d5\u30a1\u30a4\u30eb')
        fsl.run('add', '.')
        fsl.run('commit', '--branch', '\u30d6\u30e9\u30f3\u30c1', '-m', '.')
        fsl.run('tag', 'add', '\u30bf\u30b0', 'current')

        info = fsl.parse('.', name='_FOSSIL_')
        self.assertEqual(info.tag, '\u30bf\u30b0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, '\u30d6\u30e9\u30f3\u30c1')

    def test_status(self):
        self.init()
        self.touch('file1')
        self.touch('file2')

        info = fsl.parse('.', name='_FOSSIL_')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'trunk')

        fsl.run('add', '.')

        info = fsl.parse('.', name='_FOSSIL_')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 0)
        self.assertIsNotNone(info.revision)
        self.assertTrue(info.dirty)
        self.assertEqual(info.branch, 'trunk')

    def test_branch(self):
        self.init()
        self.touch('file')
        fsl.run('add', '.')
        fsl.run('commit', '--branch', 'spam', '--close', '-m', '.')

        info = fsl.parse('.', name='_FOSSIL_')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 2)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'spam')

    def test_version(self):
        self.assertGreaterEqual(len(fsl.version()), 2)

        run = fsl.run
        try:
            # >= 1.18 (check-in e0303181a568fe959aaa0fa69d6437ba9895fb3c)
            new = 'This is fossil version {} [{}] {} UTC'
            # <  1.18
            old = 'This is fossil version [{}] {} UTC'
            for out, e in (
                (new.format('2.8', 'f8d7f76bfd', '2019-02-20 15:01:32'), (2, 8)),
                (old.format('0448438c56', '2011-05-28 18:51:22'), ()),
                ('', ()),
            ):
                fsl.run = lambda *a, **kw: (out, '')
                self.assertEqual(fsl.version(), e)
        finally:
            fsl.run = run

    def test_run(self):
        env = {}
        fsl.run('help', env=env)
        self.assertEqual(env, {})
