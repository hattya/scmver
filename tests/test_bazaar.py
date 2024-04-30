#
# test_bazaar
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
from pathlib import Path
import textwrap
import unittest
import unittest.mock

from scmver import core, bazaar as bzr, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('bzr') or util.which('brz'), 'requires Bazaar or Breezy')
@unittest.mock.patch.dict('os.environ')
class BazaarTestCase(SCMVerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if brz := util.which('brz'):
            os.environ['PATH'] = f'{Path(brz).resolve().parent}{os.pathsep}{os.environ["PATH"]}'

    def setUp(self):
        self._cwd = Path.cwd()
        self._dir = self.tempdir()
        self.root = Path(self._dir.name)
        os.chdir(self.root)

        self.branch = self.root / 'trunk'

    def tearDown(self):
        os.chdir(self._cwd)
        self._dir.cleanup()

    def init(self):
        bzr.run('init-repo', self.root)
        bzr.run('init', self.branch)
        os.chdir(self.branch)
        bzr.run('whoami', '--branch', 'scmver <scmver@example.com>')

    def touch(self, path):
        with open(path, 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.bzr'):
            with self.subTest(name=name):
                self.assertIsNone(bzr.parse(Path(), name=name))

        self.init()
        self.assertIsNone(bzr.parse(Path('..'), name='.bzr'))
        self.assertEqual(bzr.parse(Path(), name='.bzr'), core.SCMInfo(revision='0', dirty=True, branch='trunk'))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        bzr.run('add', '.')
        bzr.run('commit', '-m', '_')

        self.assertEqual(bzr.parse(Path(), name='.bzr'), core.SCMInfo(distance=1, revision='1', branch='trunk'))

    def test_simple(self):
        self.init()
        self.touch('file')
        bzr.run('add', '.')
        bzr.run('commit', '-m', '_')
        bzr.run('tag', 'v1.0')

        self.assertEqual(bzr.parse(Path(), name='.bzr'), core.SCMInfo('v1.0', 0, '1', False, 'trunk'))

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
                self.assertEqual(bzr.parse(Path(), name='.bzr', **kwargs), core.SCMInfo(tag, 0, '1', False, 'trunk'))

    def test_i18n(self):
        self.check_locale()

        branch = self.branch
        try:
            self.branch = self.branch.parent / '\u30d6\u30e9\u30f3\u30c1'
            self.init()
            self.touch('\u30d5\u30a1\u30a4\u30eb')
            bzr.run('add', '.')
            bzr.run('commit', '-m', '_')
            bzr.run('tag', '\u30bf\u30b0')

            self.assertEqual(bzr.parse(Path(), name='.bzr'), core.SCMInfo('\u30bf\u30b0', 0, '1', False, '\u30d6\u30e9\u30f3\u30c1'))
        finally:
            self.branch = branch

    def test_status(self):
        self.init()
        self.touch('spam')
        bzr.run('add', '.')
        bzr.run('commit', '-m', '_')

        self.assertEqual(bzr.parse(Path(), name='.bzr'), core.SCMInfo(distance=1, revision='1', branch='trunk'))

        self.touch('eggs')

        self.assertEqual(bzr.parse(Path(), name='.bzr'), core.SCMInfo(distance=1, revision='1', dirty=True, branch='trunk'))

    def test_version(self):
        self.assertGreaterEqual(len(bzr.version()), 3)

        with unittest.mock.patch(f'{bzr.__name__}.run') as run:
            # Breezy
            brz = textwrap.dedent("""\
                Breezy (brz) {}
                  ...
            """)
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
                (brz.format('3.1.0'), (3, 1, 0)),
                (brz.format('3.1a1'), (3, 1, 0, 'a', 1)),
                (brz.format('3.0b1'), (3, 0, 0, 'b', 1)),
                (brz.format('3.0.0dev1'), (3, 0, 0, 'dev', 1)),
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
                run.return_value = (out, '')
                self.assertEqual(bzr.version(), e)
