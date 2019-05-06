#
# test_subversion
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import textwrap
import unittest

from scmver import core, subversion as svn, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('svn') and util.which('svnadmin') and svn.version() >= (1, 7), 'requires Subversion 1.7+')
class SubversionTestCase(SCMVerTestCase):

    def setUp(self):
        self._cwd = os.getcwd()
        self._root = self.mkdtemp()
        os.chdir(self._root)

    def tearDown(self):
        os.chdir(self._cwd)
        self.rmtree(self._root)

    def create(self, name):
        util.exec_(('svnadmin', 'create', os.path.join(self._root, name)))

    def checkout(self, repo, wc):
        repo = os.path.join(self._root, repo)
        wc = os.path.join(self._root, wc)
        svn.run('checkout', 'file:///{}'.format(repo.replace(os.sep, '/')), wc)
        os.chdir(wc)

    def switch(self, path):
        svn.run('switch', '--ignore-ancestry', '^' + os.path.normpath(os.path.join(os.sep, path)).replace(os.sep, '/'))

    def test_empty(self):
        for name in ('_', '.svn'):
            with self.subTest(name=name):
                self.assertIsNone(svn.parse('.', name=name))

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        self.assertIsNotNone(svn.parse('.', name='.svn'))
        self.assertIsNone(svn.parse('trunk', name='.svn'))

    def test_no_tags(self):
        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        svn.run('commit', '-m', '_')
        svn.run('copy', 'trunk', os.path.join('branches', '1.x'))
        svn.run('commit', '-m', '_')

        for path, distance, branch in (
            ('', 2, None),
            ('trunk', 1, 'trunk'),
            ('branches', 2, None),
            ('branches/1.x', 2, '1.x'),
            ('tags', 1, None),
        ):
            with self.subTest(path=path):
                self.switch(path)
                self.assertEqual(svn.parse('.', name='.svn'), core.SCMInfo(distance=distance, revision=2, branch=branch))

    def test_simple(self):
        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        svn.run('commit', '-m', '_')
        svn.run('copy', 'trunk', os.path.join('branches', '1.x'))
        svn.run('commit', '-m', '_')
        svn.run('copy', os.path.join('branches', '1.x'), os.path.join('tags', '1.0'))
        svn.run('commit', '-m', '_')

        for path, branch in (
            ('', None),
            ('trunk', 'trunk'),
            ('branches', None),
            ('branches/1.x', '1.x'),
            ('tags', None),
            ('tags/1.0', None),
        ):
            with self.subTest(path=path):
                self.switch(path)
                self.assertEqual(svn.parse('.', name='.svn'), core.SCMInfo('1.0', 0, 3, False, branch))

    def test_match(self):
        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        svn.run('commit', '-m', '_')
        svn.run('copy', 'trunk', os.path.join('branches', '1.x'))
        svn.run('commit', '-m', '_')
        svn.run('copy', os.path.join('branches', '1.x'), os.path.join('tags', '1.0'))
        svn.run('copy', os.path.join('branches', '1.x'), os.path.join('tags', 'spam-1.0'))
        svn.run('commit', '-m', '_')

        for pat, tag in (
            (r'\d\..+', '1.0'),
            (r'spam-\d+\..+', 'spam-1.0'),
        ):
            kwargs = {'subversion.tag': pat}
            for path, branch in (
                ('', None),
                ('trunk', 'trunk'),
                ('branches', None),
                ('branches/1.x', '1.x'),
                ('tags', None),
                ('tags/1.0', None),
            ):
                with self.subTest(path=path, tag=tag):
                    self.switch(path)
                    self.assertEqual(svn.parse('.', name='.svn', **kwargs), core.SCMInfo(tag, 0, 3, False, branch))

    def test_i18n(self):
        self.check_locale()

        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        svn.run('commit', '-m', '_')
        svn.run('copy', 'trunk', os.path.join('branches', u'\u30d6\u30e9\u30f3\u30c1'))
        svn.run('commit', '-m', '_')
        svn.run('copy', os.path.join('branches', u'\u30d6\u30e9\u30f3\u30c1'), os.path.join('tags', u'\u30bf\u30b0'))
        svn.run('commit', '-m', '_')

        for path, branch in (
            ('', None),
            ('trunk', 'trunk'),
            ('branches', None),
            (u'branches/\u30d6\u30e9\u30f3\u30c1', u'\u30d6\u30e9\u30f3\u30c1'),
            ('tags', None),
            (u'tags/\u30bf\u30b0', None),
        ):
            with self.subTest(path=path):
                self.switch(path)
                self.assertEqual(svn.parse('.', name='.svn'), core.SCMInfo(u'\u30bf\u30b0', 0, 3, False, branch))

    def test_status(self):
        self.create('repo')
        self.checkout('repo', 'wc')
        svn.run('mkdir', 'trunk', 'branches', 'tags')
        self.assertEqual(svn.parse('.', name='.svn'), core.SCMInfo(revision=0, dirty=True))

        svn.run('commit', '-m', '_')
        svn.run('update')
        self.assertEqual(svn.parse('.', name='.svn'), core.SCMInfo(distance=1, revision=1))

        with open('file', 'w'):
            pass
        self.assertEqual(svn.parse('.', name='.svn'), core.SCMInfo(distance=1, revision=1))

    def test_version(self):
        self.assertGreaterEqual(len(svn.version()), 3)

        run = svn.run
        try:
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
                (new.format('1.9.0', 'Release Candidate 3'), (1, 9, 0, 'rc', 3)),
                (new.format('1.9.0', 'Beta 1'), (1, 9, 0, 'b', 1)),
                (new.format('1.9.0', 'Alpha 2'), (1, 9, 0, 'a', 2)),
                (old.format('0.14.3', 'r3200'), (0, 14, 3)),
                (old.format('0.9.0', 'r1302'), (0, 9, 0)),
                ('', ()),
            ):
                svn.run = lambda *a, **kw: (out, '')
                self.assertEqual(svn.version(), e)
        finally:
            svn.run = run
