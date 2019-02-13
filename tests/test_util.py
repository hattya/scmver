#
# test_util
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

import sys
import unittest

from scmver import util


class UtilTestCase(unittest.TestCase):

    def test_exec(self):
        out, err = util.exec_((sys.executable, '-V'))
        ver = 'Python {}.{}.{}'.format(*sys.version_info)
        if sys.version_info[0] == 2:
            self.assertEqual(out, '')
            self.assertEqual(err.strip(), ver)
        else:
            self.assertEqual(out.strip(), ver)
            self.assertEqual(err, '')

    def test_which(self):
        sh = 'sh' if sys.platform != 'win32' else 'cmd'
        self.assertNotEqual(util.which(sh), sh)
        self.assertIsNone(util.which('__scmver.util__'))
