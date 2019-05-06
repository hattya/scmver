#
# test_bazaar
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import textwrap
import unittest

from scmver import core, bazaar as bzr, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('bzr'), 'requires Bazaar')
class BazaarTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

        self.branch = os.path.join(self._root, 'trunk')

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def init(self):
        bzr.run('init-repository', self._root)
        bzr.run('init', self.branch)
        os.chdir(self.branch)
        bzr.run('whoami', '--branch', 'scmver <scmver@example.com>')

    def touch(self, path):
        with open(os.path.join(self.branch, path), 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.bzr'):
            with self.subTest(name=name):
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
            with self.subTest(tag=tag):
                kwargs = {'bazaar.tag': pat}
                self.assertEqual(bzr.parse('.', name='.bzr', **kwargs), core.SCMInfo(tag, 0, '1', False, 'trunk'))

    def test_i18n(self):
        self.check_locale()

        branch = self.branch
        self.branch = os.path.join(os.path.dirname(self.branch), u'\u30d6\u30e9\u30f3\u30c1')
        try:
            self.init()
            self.touch(u'\u30d5\u30a1\u30a4\u30eb')
            bzr.run('add', '.')
            bzr.run('commit', '-m', '_')
            bzr.run('tag', u'\u30bf\u30b0')

            self.assertEqual(bzr.parse('.', name='.bzr'), core.SCMInfo(u'\u30bf\u30b0', 0, '1', False, u'\u30d6\u30e9\u30f3\u30c1'))
        finally:
            self.branch = branch

    def test_version(self):
        self.assertGreaterEqual(len(bzr.version()), 3)

        run = bzr.run
        try:
            # >= 0.10 (revision 1819.1.5)
            new = textwrap.dedent("""\
                Bazaar (bzr) {}
                  ...
            """)
            # <= 0.9
            old = textwrap.dedent("""\
                bzr (bazaar-ng) {}
                  ...
            """)
            for out, e in (
                (new.format('2.1.0'), (2, 1, 0)),
                (new.format('2.1.0rc2'), (2, 1, 0, 'rc', 2)),
                (new.format('2.1.0b4'), (2, 1, 0, 'b', 4)),
                (new.format('2.1.0dev3'), (2, 1, 0, 'dev', 3)),
                (new.format('1.6'), (1, 6, 0)),
                (new.format('1.6rc5'), (1, 6, 0, 'rc', 5)),
                (new.format('1.6beta3'), (1, 6, 0, 'b', 3)),
                (new.format('1.6dev'), (1, 6, 0, 'dev', 0)),
                (old.format('0.9.0'), (0, 9, 0)),
                (old.format('0.8.2'), (0, 8, 2)),
                (old.format('0.0.2.1'), (0, 0, 2, 1)),
                ('', ()),
            ):
                bzr.run = lambda *a, **kw: (out, '')
                self.assertEqual(bzr.version(), e)
        finally:
            bzr.run = run
