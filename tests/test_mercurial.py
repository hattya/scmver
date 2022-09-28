#
# test_mercurial
#
#   Copyright (c) 2019-2022 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import contextlib
import os
import textwrap
import unittest
import unittest.mock

from scmver import core, mercurial as hg, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('hg') and hg.version() >= (3, 6), 'requires Mercurial 3.6+')
class MercurialTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._dir = self.tempdir()
        self.root = self._dir.name
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self._cwd)
        self._dir.cleanup()

    def init(self):
        hg.run('init')
        with open(os.path.join('.hg', 'hgrc'), 'w') as fp:
            fp.write(textwrap.dedent("""\
                [ui]
                username = scmver <scmver@example.com>
            """))
            fp.flush()

    @contextlib.contextmanager
    def archive(self):
        with self.tempdir() as path:
            hg.run('archive', path, env={'HGENCODING': 'utf-8'})
            os.chdir(path)
            try:
                yield path
            finally:
                os.chdir(self.root)

    def touch(self, path):
        with open(path, 'w'):
            pass

    def test_empty(self):
        for name in ('_', '.hg', '.hg_archival.txt'):
            with self.subTest(name=name):
                self.assertIsNone(hg.parse('.', name=name))

        self.init()
        self.assertEqual(hg.parse('.', name='.hg'), core.SCMInfo(branch='default'))

    def test_no_tags(self):
        self.init()
        self.touch('file')
        hg.run('add', '.')
        hg.run('commit', '-m', '.')

        info = hg.parse('.', name='.hg')
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'default')

        with self.archive():
            info = hg.parse('.', name='.hg_archival.txt')
            self.assertEqual(info.tag, '0.0')
            self.assertEqual(info.distance, 1)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'default')

    def test_simple(self):
        self.init()
        self.touch('file')
        hg.run('add', '.')
        hg.run('commit', '-m', '.')
        hg.run('tag', 'v1.0')

        info = hg.parse('.', name='.hg')
        self.assertEqual(info.tag, 'v1.0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'default')

        with self.archive():
            info = hg.parse('.', name='.hg_archival.txt')
            self.assertEqual(info.tag, 'v1.0')
            self.assertEqual(info.distance, 1)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'default')

        hg.run('update', '-Cr', 'v1.0')
        with self.archive():
            info = hg.parse('.', name='.hg_archival.txt')
            self.assertEqual(info.tag, 'v1.0')
            self.assertEqual(info.distance, 0)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, 'default')

    def test_match(self):
        self.init()
        self.touch('file')
        hg.run('add', '.')
        hg.run('commit', '-m', '.')
        hg.run('tag', 'v1.0', 'spam-1.0')

        for pat, tag in (
            (r'v\d+\..+', 'v1.0'),
            (r'spam-\d+\..+', 'spam-1.0'),
        ):
            with self.subTest(tag=tag):
                info = hg.parse('.', name='.hg', **{'mercurial.tag': pat})
                self.assertEqual(info.tag, tag)
                self.assertEqual(info.distance, 1)
                self.assertIsNotNone(info.revision)
                self.assertFalse(info.dirty)
                self.assertEqual(info.branch, 'default')

        info = hg.parse('.', name='.hg', **{'mercurial.tag': r'__scmver__'})
        self.assertEqual(info.tag, '0.0')
        self.assertEqual(info.distance, 2)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, 'default')

        with self.archive():
            for pat, tag in (
                (r'v\d+\..+', 'v1.0'),
                (r'spam-\d+\..+', 'spam-1.0'),
            ):
                with self.subTest(tag=tag):
                    info = hg.parse('.', name='.hg_archival.txt', **{'mercurial.tag': pat})
                    self.assertEqual(info.tag, tag)
                    self.assertEqual(info.distance, 1)
                    self.assertIsNotNone(info.revision)
                    self.assertFalse(info.dirty)
                    self.assertEqual(info.branch, 'default')

            with self.assertRaises(ValueError):
                hg.parse('.', name='.hg_archival.txt', **{'mercurial.tag': r'__scmver__'})

        hg.run('update', '-Cr', 'v1.0')
        with self.archive():
            for pat, tag in (
                (r'v\d+\..+', 'v1.0'),
                (r'spam-\d+\..+', 'spam-1.0'),
            ):
                info = hg.parse('.', name='.hg_archival.txt', **{'mercurial.tag': pat})
                self.assertEqual(info.tag, tag)
                self.assertEqual(info.distance, 0)
                self.assertIsNotNone(info.revision)
                self.assertFalse(info.dirty)
                self.assertEqual(info.branch, 'default')

            with self.assertRaises(ValueError):
                hg.parse('.', name='.hg_archival.txt', **{'mercurial.tag': r'__scmver__'})

    def test_i18n(self):
        self.check_locale()

        self.init()
        hg.run('branch', '\u30d6\u30e9\u30f3\u30c1')
        self.touch('\u30d5\u30a1\u30a4\u30eb')
        hg.run('add', '.')
        hg.run('commit', '-m', '.')
        hg.run('tag', '\u30bf\u30b0')

        info = hg.parse('.', name='.hg')
        self.assertEqual(info.tag, '\u30bf\u30b0')
        self.assertEqual(info.distance, 1)
        self.assertIsNotNone(info.revision)
        self.assertFalse(info.dirty)
        self.assertEqual(info.branch, '\u30d6\u30e9\u30f3\u30c1')

        with self.archive():
            info = hg.parse('.', name='.hg_archival.txt')
            self.assertEqual(info.tag, '\u30bf\u30b0')
            self.assertEqual(info.distance, 1)
            self.assertIsNotNone(info.revision)
            self.assertFalse(info.dirty)
            self.assertEqual(info.branch, '\u30d6\u30e9\u30f3\u30c1')

    def test_status(self):
        self.init()
        self.touch('file')

        self.assertEqual(hg.parse('.', name='.hg'), core.SCMInfo(branch='default'))

        hg.run('add', '.')

        self.assertEqual(hg.parse('.', name='.hg'), core.SCMInfo(dirty=True, branch='default'))

    @unittest.mock.patch('scmver.mercurial.run')
    def test_lt_hg36(self, run):
        run.side_effect = [
            ('0123456789ab default', ''),
            ('', "hg: parse error: unknown function 'latesttag'"),
        ]

        self.assertIsNone(hg.parse('.', name='.hg'))

    def test_version(self):
        self.assertGreaterEqual(len(hg.version()), 3)

        with unittest.mock.patch(f'{hg.__name__}.run') as run:
            # >= 0.6c (changeset 849:8933ef744325)
            new = textwrap.dedent("""\
                Mercurial Distributed SCM (version {})

                ...
            """)
            # <= 0.6b
            old = textwrap.dedent("""\
                Mercurial version {}

                ...
            """)
            for out, e in (
                (new.format('4.6.2'), (4, 6, 2)),
                (new.format('4.6'), (4, 6, 0)),
                (new.format('4.6rc1'), (4, 6, 0, 'rc', 1)),
                (new.format('4.6rc0'), (4, 6, 0, 'rc', 0)),
                (new.format('4.5.3'), (4, 5, 3)),
                (new.format('4.5'), (4, 5, 0)),
                (new.format('4.5-rc'), (4, 5, 0, 'rc', 0)),
                (old.format('0.6b'), (0, 6, 0, 'b')),
                (old.format('0.6'), (0, 6, 0)),
                ('', ()),
            ):
                run.return_value = (out, '')
                self.assertEqual(hg.version(), e)

    def test_run(self):
        env = {}
        hg.run('help', env=env)
        self.assertEqual(env, {})
