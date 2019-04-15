#
# base
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
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
