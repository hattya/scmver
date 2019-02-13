#
# test_core
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

import datetime
import hashlib
import os

from scmver import core
from base import SCMVerTestCase


class CoreTestCase(SCMVerTestCase):

    def assertVersion(self, version, normalized):
        v = core.Version(version)
        self.assertEqual(repr(v), '<Version({})>'.format(version))
        self.assertEqual(str(v), version)
        self.assertEqual(str(v.normalize()), normalized)

        v = core.Version(version.upper())
        self.assertEqual(repr(v), '<Version({})>'.format(version.upper()))
        self.assertEqual(str(v), version.upper())
        self.assertEqual(str(v.normalize()), normalized)

    def revision(self, data):
        m = hashlib.new('sha1')
        m.update(data)
        return m.hexdigest()

    def test_next_version(self):
        rev = self.revision(b'scmver.core.next_version')

        for tag in ('v1.0', '1.0', 'spam-1.0'):
            for i, post in enumerate(('', '.post', '.post2', '.post3')):
                v = core.next_version(core.SCMInfo(tag, i, rev, False, 'master'))
                self.assertEqual(v, '1.0' + post)

            for i, micro in enumerate(('', '.1', '.2', '.3')):
                v = core.next_version(core.SCMInfo(tag, i, rev, False, 'master'),
                                      spec='micro')
                self.assertEqual(v, '1.0' + micro)

        v = core.next_version(core.SCMInfo('1.0', 1, rev, True, 'master'),
                              spec='minor.dev',
                              local='{revision}.{local:%Y-%m-%d}')
        self.assertEqual(v, '1.1.dev+{}.{:%Y-%m-%d}'.format(rev, datetime.datetime.now()))

        v = core.next_version(core.SCMInfo('1.0', 1, rev, True, 'master'),
                              spec='minor.dev',
                              local=lambda info: '{}.{:%Y-%m-%d}'.format(info.revision, datetime.datetime.now()))
        self.assertEqual(v, '1.1.dev+{}.{:%Y-%m-%d}'.format(rev, datetime.datetime.now()))

        with self.assertRaises(core.VersionError):
            core.next_version(core.SCMInfo('', 0, rev, False, 'master'))

    def test_stat(self):
        with self.tempdir() as path:
            self.assertIsNone(core.stat(path))
            kwargs = {}

            os.mkdir(os.path.join(path, '.git'))
            self.assertIsNone(core.stat(path, **kwargs))
            kwargs['.git'] = False

            self.assertIsNone(core.stat(path, **kwargs))

    def test_invalid_version(self):
        for v in ('', 'version', '1.0-', '1.0+', '1.0+_'):
            with self.assertRaises(core.VersionError):
                core.Version(v)

    def test_pre_version(self):
        for sep in ('.', '-', '_', ''):
            for pre in ('a', 'alpha', 'b', 'beta', 'rc', 'c', 'pre', 'preview'):
                if pre == 'alpha':
                    norm = 'a'
                elif pre == 'beta':
                    norm = 'b'
                elif pre in ('c', 'pre', 'preview'):
                    norm = 'rc'
                else:
                    norm = pre

                v = ['1.0', pre]
                self.assertVersion(sep.join(v), '1.0{pre}0'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}0'.format(pre=norm))

                v = ['1.0' + pre]
                self.assertVersion(sep.join(v), '1.0{pre}0'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}0'.format(pre=norm))

                v = ['1.0', pre + '1']
                self.assertVersion(sep.join(v), '1.0{pre}1'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}1'.format(pre=norm))

                v = ['1.0' + pre, '1']
                self.assertVersion(sep.join(v), '1.0{pre}1'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}1'.format(pre=norm))

                v = ['1.0', pre, '1']
                self.assertVersion(sep.join(v), '1.0{pre}1'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}1'.format(pre=norm))

        self.assertEqual(core.Version('1.0a').pre, ('a', -1))
        self.assertEqual(core.Version('1.0a1').pre, ('a', 1))

    def test_release_version(self):
        for v in ('1', '1.0', '1.0.0'):
            self.assertVersion(v, v)
            self.assertVersion('1!' + v, '1!' + v)

        v = core.Version('1.0')
        self.assertEqual(v.epoch, 0)
        self.assertEqual(v.release, (1, 0))
        self.assertIsNone(v.pre)
        self.assertIsNone(v.post)
        self.assertIsNone(v.dev)
        self.assertIsNone(v.local)

    def test_post_version(self):
        for sep in ('.', '-', '_', ''):
            for post in ('post', 'r', 'rev'):
                v = ['1.0', post]
                self.assertVersion(sep.join(v), '1.0.post0')
                self.assertVersion('1!' + sep.join(v), '1!1.0.post0')

                v = ['1.0' + post]
                self.assertVersion(sep.join(v), '1.0.post0')
                self.assertVersion('1!' + sep.join(v), '1!1.0.post0')

                v = ['1.0', post + '1']
                self.assertVersion(sep.join(v), '1.0.post1')
                self.assertVersion('1!' + sep.join(v), '1!1.0.post1')

                v = ['1.0' + post, '1']
                self.assertVersion(sep.join(v), '1.0.post1')
                self.assertVersion('1!' + sep.join(v), '1!1.0.post1')

                v = ['1.0', post, '1']
                self.assertVersion(sep.join(v), '1.0.post1')
                self.assertVersion('1!' + sep.join(v), '1!1.0.post1')

        self.assertVersion('1.0-1', '1.0.post1')
        self.assertVersion('1!1.0-1', '1!1.0.post1')

        self.assertEqual(core.Version('1.0.post').post, ('post', -1))
        self.assertEqual(core.Version('1.0.post1').post, ('post', 1))
        self.assertEqual(core.Version('1.0-1').post, (None, 1))

    def test_dev_version(self):
        for sep in ('.', '-', '_', ''):
            v = ['1.0', 'dev']
            self.assertVersion(sep.join(v), '1.0.dev0')
            self.assertVersion('1!' + sep.join(v), '1!1.0.dev0')

            v = ['1.0dev']
            self.assertVersion(sep.join(v), '1.0.dev0')
            self.assertVersion('1!' + sep.join(v), '1!1.0.dev0')

            v = ['1.0', 'dev1']
            self.assertVersion(sep.join(v), '1.0.dev1')
            self.assertVersion('1!' + sep.join(v), '1!1.0.dev1')

            v = ['1.0dev', '1']
            self.assertVersion(sep.join(v), '1.0.dev1')
            self.assertVersion('1!' + sep.join(v), '1!1.0.dev1')

            v = ['1.0', 'dev', '1']
            self.assertVersion(sep.join(v), '1.0.dev1')
            self.assertVersion('1!' + sep.join(v), '1!1.0.dev1')

            for s in ('a', 'b', 'rc', '.post'):
                v = ['1.0', s.strip('.'), 'dev']
                self.assertVersion(sep.join(v), '1.0{s}0.dev0'.format(s=s))
                self.assertVersion('1!' + sep.join(v), '1!1.0{s}0.dev0'.format(s=s))

        self.assertEqual(core.Version('1.0.dev').dev, ('dev', -1))
        self.assertEqual(core.Version('1.0.dev1').dev, ('dev', 1))

    def test_local_version(self):
        self.assertVersion('1.0+local', '1.0+local')
        self.assertVersion('1.0+00100', '1.0+100')
        self.assertVersion('1.0+2019-02-10', '1.0+2019.2.10')

    def test_update(self):
        v = core.Version('1.0')
        v.update('')
        self.assertEqual(str(v), '1.0')

        for spec in (
            'major', 'minor', 'micro', 'patch',
            'pre', 'post', 'dev',
            'major.dev', 'minor.dev', 'micro.dev', 'patch.dev',
        ):
            with self.assertRaises(core.VersionError):
                core.Version('1.0+local').update(spec)

    def test_update_pre_version(self):
        for g, e in (
                ('1a', '1a1'), ('1a0', '1a1'),
                ('1b', '1b1'), ('1b0', '1b1'),
                ('1rc', '1rc1'), ('1rc0', '1rc1'),
        ):
            v = core.Version(g)
            v.update('pre')
            self.assertEqual(str(v), e)

        for g, e in (
                ('1a', '1a'), ('1a0', '1a0'),
                ('1b', '1b'), ('1b0', '1b0'),
                ('1rc', '1rc'), ('1rc0', '1rc0'),
        ):
            v = core.Version(g)
            v.update('pre', 0)
            self.assertEqual(str(v), e)

        for g, e in (
                ('1a0', '1a'), ('1a1', '1a0'),
                ('1b0', '1b'), ('1b1', '1b0'),
                ('1rc0', '1rc'), ('1rc1', '1rc0'),
        ):
            v = core.Version(g)
            v.update('pre', -1)
            self.assertEqual(str(v), e)

        with self.assertRaises(core.VersionError):
            core.Version('1.0').update('pre')

    def test_update_release_version(self):
        for spec, tests in (
            ('major', (('0', '1'), ('0.0', '1.0'), ('0.0.0', '1.0.0'))),
            ('minor', (('1', '1.1'), ('1.0', '1.1'), ('1.0.0', '1.1.0'))),
            ('micro', (('1', '1.0.1'), ('1.0', '1.0.1'), ('1.0.0', '1.0.1'))),
            ('patch', (('1', '1.0.1'), ('1.0', '1.0.1'), ('1.0.0', '1.0.1'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('major', (('1', '1'), ('1.0', '1.0'), ('1.0.0', '1.0.0'))),
            ('minor', (('1', '1.0'), ('1.0', '1.0'), ('1.0.0', '1.0.0'))),
            ('micro', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
            ('patch', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec, 0)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('major', (('0', '0'), ('0.0', '0.0'), ('0.0.0', '0.0.0'))),
            ('minor', (('1', '1.0'), ('1.0', '1.0'), ('1.0.0', '1.0.0'))),
            ('micro', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
            ('patch', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec, -1)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('major', (('0a', '1'), ('0b', '1'), ('0rc', '1'), ('0.post', '1'), ('0.dev', '1'))),
            ('minor', (('0a', '0.1'), ('0b', '0.1'), ('0rc', '0.1'), ('0.post', '0.1'), ('0.dev', '0.1'))),
            ('micro', (('0a', '0.0.1'), ('0b', '0.0.1'), ('0rc', '0.0.1'), ('0.post', '0.0.1'), ('0.dev', '0.0.1'))),
            ('patch', (('0a', '0.0.1'), ('0b', '0.0.1'), ('0rc', '0.0.1'), ('0.post', '0.0.1'), ('0.dev', '0.0.1'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec)
                self.assertEqual(str(v), e)

    def test_update_post_version(self):
        for g, e in (
            ('1.0', '1.0.post'), ('1.0.post', '1.0.post1'), ('1.0.post0', '1.0.post1'),
            ('1.0-0', '1.0-1'),
        ):
            v = core.Version(g)
            v.update('post')
            self.assertEqual(str(v), e)

        for g, e in (
            ('1.0', '1.0.post'), ('1.0.post', '1.0.post'), ('1.0.post0', '1.0.post0'),
            ('1.0-0', '1.0-0'),
        ):
            v = core.Version(g)
            v.update('post', 0)
            self.assertEqual(str(v), e)

        for g, e in (
            ('1.0', '1.0'), ('1.0.post0', '1.0.post'), ('1.0.post1', '1.0.post0'),
            ('1.0-0', '1.0-0'), ('1.0-1', '1.0-0'),
        ):
            v = core.Version(g)
            v.update('post', -1)
            self.assertEqual(str(v), e)

    def test_update_dev_version(self):
        for spec, tests in (
            ('dev', (('1.0.dev', '1.0.dev1'), ('1.0.dev0', '1.0.dev1'))),
            ('major.dev', (('0', '1.dev'), ('0.0', '1.0.dev'), ('0.1', '1.0.dev'))),
            ('minor.dev', (('1', '1.1.dev'), ('1.0', '1.1.dev'), ('1.0.0', '1.1.0.dev'), ('1.0.1', '1.1.0.dev'))),
            ('micro.dev', (('1', '1.0.1.dev'), ('1.0', '1.0.1.dev'), ('1.0.0', '1.0.1.dev'), ('1.0.0.0', '1.0.1.0.dev'), ('1.0.0.1', '1.0.1.0.dev'))),
            ('patch.dev', (('1', '1.0.1.dev'), ('1.0', '1.0.1.dev'), ('1.0.0', '1.0.1.dev'), ('1.0.0.0', '1.0.1.0.dev'), ('1.0.0.1', '1.0.1.0.dev'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('dev', (('1.0.dev', '1.0.dev'), ('1.0.dev0', '1.0.dev0'))),
            ('major.dev', (('0.0', '1.0.dev'), ('0.0.dev', '1.0.dev'))),
            ('minor.dev', (('1.0', '1.1.dev'), ('1.0.dev', '1.1.dev'))),
            ('micro.dev', (('1.0.0', '1.0.1.dev'), ('1.0.0.dev', '1.0.1.dev'))),
            ('patch.dev', (('1.0.0', '1.0.1.dev'), ('1.0.0.dev', '1.0.1.dev'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec, 0)
                self.assertEqual(str(v), e)

        for g, e in (
            ('1.0.dev0', '1.0.dev'), ('1.0.dev1', '1.0.dev0'),
        ):
            v = core.Version(g)
            v.update('dev', -1)
            self.assertEqual(str(v), e)

        for spec in ('dev', '_.dev'):
            with self.assertRaises(core.VersionError):
                core.Version('1.0').update(spec)

        for spec in ('major.dev', 'minor.dev', 'micro.dev', 'patch.dev'):
            with self.assertRaises(core.VersionError):
                core.Version('1.0').update(spec, -1)
