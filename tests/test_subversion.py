#
# test_subversion
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

from scmver import core, subversion as svn, util
from base import SCMVerTestCase


@unittest.skipUnless(util.which('svn') and util.which('svnadmin'), 'requires Subversion')
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
                self.switch(path)
                self.assertEqual(svn.parse('.', name='.svn', **kwargs), core.SCMInfo(tag, 0, 3, False, branch))

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
