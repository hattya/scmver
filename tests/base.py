#
# base
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

import contextlib
import hashlib
import os
import shutil
import stat
import tempfile
import unittest

from scmver import _compat as five


__all__ = ['SCMVerTestCase']


class SCMVerTestCase(unittest.TestCase):

    if five.PY2:
        assertRegex = unittest.TestCase.assertRegexpMatches

    def mkdtemp(self):
        return tempfile.mkdtemp(prefix='scmver-')

    def mkstemp(self):
        return tempfile.mkstemp(prefix='scmver-')

    @contextlib.contextmanager
    def tempdir(self):
        path = self.mkdtemp()
        try:
            yield path
        finally:
            self.rmtree(path)

    @contextlib.contextmanager
    def tempfile(self):
        fd, path = self.mkstemp()
        try:
            os.close(fd)
            yield path
        finally:
            os.unlink(path)

    def revision(self, data):
        m = hashlib.new('sha1')
        m.update(data)
        return m.hexdigest()

    def rmtree(self, path):
        def onerror(func, path, exc_info):
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise
        shutil.rmtree(path, onerror=onerror)
