#
# base
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import contextlib
import hashlib
import locale
import os
import shutil
import sys
import tempfile
import textwrap
import unittest

try:
    import tomli
except ImportError:
    tomli = None


__all__ = ['requires_tomli', 'SCMVerTestCase']


requires_tomli = unittest.skipUnless(sys.version_info >= (3, 11) or tomli, 'requires tomli')


class SCMVerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._lc = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, '')

    @classmethod
    def tearDownClass(cls):
        locale.setlocale(locale.LC_ALL, cls._lc)

    def check_locale(self):
        if locale.getpreferredencoding(False).lower() not in ('cp932', 'euc-jp', 'utf-8'):
            self.skipTest('requires UTF-8 or Japanese locale')

    def tempdir(self):
        return tempfile.TemporaryDirectory(prefix='scmver-')

    @contextlib.contextmanager
    def tempfile(self):
        fd, path = tempfile.mkstemp(prefix='scmver-')
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
                os.chmod(path, 0o700)
                func(path)
            else:
                raise
        shutil.rmtree(path, onerror=onerror)

    def write_sync(self, fp, data):
        fp.write(textwrap.dedent(data))
        fp.flush()
