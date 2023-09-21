#
# test_subversion
#
#   Copyright (c) 2019-2023 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
from pathlib import Path
import textwrap
import unittest
import unittest.mock

from scmver import core, subversion as svn, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('svn') and util.which('svnadmin') and svn.version() >= (1, 7), 'requires Subversion 1.7+')
class SubversionTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = Path.cwd()
        self._dir = self.tempdir()
        self.root = Path(self._dir.name)
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self._cwd)
        self._dir.cleanup()

    def create(self, name):
        util.exec_(('svnadmin', 'create', self.root / name))

    def checkout(self, repo, wc):
        repo = self.root / repo
        wc = self.root / wc
        svn.run('checkout', repo.as_uri(), wc)
        os.chdir(wc)

    def switch(self, path):
        svn.run('switch', '--ignore-ancestry', '^' + (Path('/') / path).as_posix())

    def test_empty(self):
        for name in ('_', '.svn'):
            with self.subTest(name=name):
                self.assertIsNone(svn.parse(Path(), name=name))

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        self.assertIsNotNone(svn.parse(Path(), name='.svn'))
        self.assertIsNone(svn.parse(Path('trunk'), name='.svn'))

    def test_no_tags(self):
        trunk = Path('trunk')
        branches = Path('branches')
        tags = Path('tags')

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', trunk, branches, tags)
        svn.run('commit', '-m', '_')
        svn.run('copy', trunk, branches / '1.x')
        svn.run('commit', '-m', '_')

        for path, distance, branch in (
            ('', 2, None),
            (trunk, 1, 'trunk'),
            (branches, 2, None),
            (branches / '1.x', 2, '1.x'),
            (tags, 1, None),
        ):
            with self.subTest(path=str(path)):
                self.switch(path)
                self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo(distance=distance, revision=2, branch=branch))

    def test_simple(self):
        trunk = Path('trunk')
        branches = Path('branches')
        tags = Path('tags')

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', trunk, branches, tags)
        svn.run('commit', '-m', '_')
        svn.run('copy', trunk, branches / '1.x')
        svn.run('commit', '-m', '_')
        svn.run('copy', branches / '1.x', tags / '1.0')
        svn.run('commit', '-m', '_')

        for path, branch in (
            ('', None),
            (trunk, 'trunk'),
            (branches, None),
            (branches / '1.x', '1.x'),
            (tags, None),
            (tags / '1.0', None),
        ):
            with self.subTest(path=str(path)):
                self.switch(path)
                self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo('1.0', 0, 3, False, branch))

    def test_match(self):
        trunk = Path('trunk')
        branches = Path('branches')
        tags = Path('tags')

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', trunk, branches, tags)
        svn.run('commit', '-m', '_')
        svn.run('copy', trunk, branches / '1.x')
        svn.run('commit', '-m', '_')
        svn.run('copy', branches / '1.x', tags / '1.0')
        svn.run('copy', branches / '1.x', tags / 'spam-1.0')
        svn.run('commit', '-m', '_')

        for pat, tag in (
            (r'\d\..+', '1.0'),
            (r'spam-\d+\..+', 'spam-1.0'),
        ):
            kwargs = {'subversion.tag': pat}
            for path, branch in (
                ('', None),
                (trunk, 'trunk'),
                (branches, None),
                (branches / '1.x', '1.x'),
                (tags, None),
                (tags / '1.0', None),
            ):
                with self.subTest(path=str(path), tag=tag):
                    self.switch(path)
                    self.assertEqual(svn.parse(Path(), name='.svn', **kwargs), core.SCMInfo(tag, 0, 3, False, branch))

    def test_i18n(self):
        self.check_locale()

        trunk = Path('trunk')
        branches = Path('branches')
        tags = Path('tags')

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', trunk, branches, tags)
        svn.run('commit', '-m', '_')
        svn.run('copy', trunk, branches / '\u30d6\u30e9\u30f3\u30c1')
        svn.run('commit', '-m', '_')
        svn.run('copy', branches / '\u30d6\u30e9\u30f3\u30c1', tags / '\u30bf\u30b0')
        svn.run('commit', '-m', '_')

        for path, branch in (
            ('', None),
            (trunk, 'trunk'),
            (branches, None),
            (branches / '\u30d6\u30e9\u30f3\u30c1', '\u30d6\u30e9\u30f3\u30c1'),
            (tags, None),
            (tags / '\u30bf\u30b0', None),
        ):
            with self.subTest(path=str(path)):
                self.switch(path)
                self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo('\u30bf\u30b0', 0, 3, False, branch))

    def test_monorepo(self):
        trunk = Path('trunk')
        branches = Path('branches')
        tags = Path('tags')

        self.create('repo')
        self.checkout('repo', 'wc')
        for proj in (Path('spam'), Path('eggs'), Path('ham')):
            svn.run('mkdir', proj)
            svn.run('mkdir', proj / trunk, proj / branches, proj / tags)
        svn.run('commit', '-m', '_')
        for proj in (Path('spam'), Path('eggs'), Path('ham')):
            svn.run('copy', proj / trunk, proj / branches / '1.x')
        svn.run('commit', '-m', '_')
        for i in range(3):
            for proj in (Path('spam'), Path('eggs'), Path('ham'))[i:]:
                svn.run('copy', proj / branches / '1.x', proj / tags / f'1.{i}')
            svn.run('commit', '-m', '_')

        for proj, tag, revision in (
            (Path('spam'), '1.0', 3),
            (Path('eggs'), '1.1', 4),
            (Path('ham'), '1.2', 5),
        ):
            kwargs = {
                'subversion.trunk': proj / trunk,
                'subversion.branches': proj / branches,
                'subversion.tags': proj / tags,
            }
            for path, distance, branch in (
                ('', revision, None),
                (trunk, 1, 'trunk'),
                (branches, 2, None),
                (branches / '1.x', 2, '1.x'),
                (tags, revision - 1, None),
                (tags / tag, 3, None),
            ):
                with self.subTest(proj=str(proj), path=str(path), tag=tag):
                    self.switch(proj / path)
                    self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo(distance=distance, revision=5))
                    self.assertEqual(svn.parse(Path(), name='.svn', **kwargs), core.SCMInfo(tag, 0, 5, False, branch))

    def test_status(self):
        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo(revision=0, dirty=True))

        svn.run('commit', '-m', '_')
        svn.run('update')
        self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo(distance=1, revision=1))

        with open('file', 'w'):
            pass
        self.assertEqual(svn.parse(Path(), name='.svn'), core.SCMInfo(distance=1, revision=1))

    def test_version(self):
        self.assertGreaterEqual(len(svn.version()), 3)

        with unittest.mock.patch(f'{svn.__name__}.run') as run:
            # >= 0.14.4 (revision 3553)
            new = textwrap.dedent("""\
                svn, version {} ({})
                   compiled ...

                ...
            """)
            # <= 0.14.3
            old = textwrap.dedent("""\
                Subversion Client, version {} ({})
                   compiled ...

                ...
            """)
            for out, e in (
                (new.format('1.9.0', 'r1692801'), (1, 9, 0)),
                (new.format('1.9.0-SlikSvn', 'SlikSvn/1.9.0'), (1, 9, 0)),
                (new.format('1.9.0-rc3', 'Release Candidate 3'), (1, 9, 0, 'rc', 3)),
                (new.format('1.9.0-rc1-SlikSvn', 'SlikSvn/1.9.0-rc1'), (1, 9, 0, 'rc', 1)),
                (new.format('1.9.0-beta1', 'Beta 1'), (1, 9, 0, 'b', 1)),
                (new.format('1.9.0-beta1-SlikSvn', 'SlikSvn/1.9.0-beta1'), (1, 9, 0, 'b', 1)),
                (new.format('1.9.0-alpha2', 'Alpha 2'), (1, 9, 0, 'a', 2)),
                (new.format('1.9.0-alpha2-SlikSvn', 'SlikSvn/1.9.0-alpha2'), (1, 9, 0, 'a', 2)),
                (new.format('1.9.0-dev', 'under development'), (1, 9, 0, 'dev')),
                (new.format('1.7.0-SlikSvn-1.7.0-X64', 'SlikSvn/1.7.0'), (1, 7, 0)),
                (old.format('0.37.0+', 'dev build'), (0, 37, 0, 'dev')),
                (old.format('0.16.1', 'dev build'), (0, 16, 1, 'dev')),
                (old.format('0.14.3', 'r3200'), (0, 14, 3)),
                (old.format('0.9.0', 'r1302'), (0, 9, 0)),
                ('', ()),
            ):
                run.return_value = (out, '')
                self.assertEqual(svn.version(), e)
