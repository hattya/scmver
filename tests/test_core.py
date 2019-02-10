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

import unittest

from scmver import core


class CoreTestCase(unittest.TestCase):

    def assertVersion(self, version, normalized):
        v = core.Version(version)
        self.assertEqual(repr(v), '<Version({})>'.format(version))
        self.assertEqual(str(v), version)
        self.assertEqual(str(v.normalize()), normalized)

        v = core.Version(version.upper())
        self.assertEqual(repr(v), '<Version({})>'.format(version.upper()))
        self.assertEqual(str(v), version.upper())
        self.assertEqual(str(v.normalize()), normalized)

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
