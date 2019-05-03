#
# test_util
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import sys
import unittest

from scmver import util


class UtilTestCase(unittest.TestCase):

    def test_exec(self):
        for args in (
            (sys.executable, r'-V'),
            (sys.executable, u'-V'),
        ):
            out, err = util.exec_(args)
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
