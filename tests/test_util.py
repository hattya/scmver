#
# test_util
#
#   Copyright (c) 2019-2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import sys

from scmver import util
from base import SCMVerTestCase


class UtilTestCase(SCMVerTestCase):

    def test_exec(self):
        def version_of(s):
            v = s.split('.')[:3]
            for i, c in enumerate(v[2]):
                if not c.isdigit():
                    v[2] = v[2][:i]
                    break
            return '.'.join(v)

        out, err = util.exec_((sys.executable, '-V'))
        self.assertEqual(version_of(out), 'Python {}.{}.{}'.format(*sys.version_info))
        self.assertEqual(err, '')

        cmd = 'import sys; getattr(sys.stdout, "buffer", sys.stdout).write("\\U0001d70b = 3.14".encode("utf-8"))'
        out, err = util.exec_((sys.executable, '-c', cmd), encoding='utf-8')
        self.assertEqual(out, '\U0001d70b = 3.14')
        self.assertEqual(err, '')

    def test_which(self):
        sh = 'sh' if sys.platform != 'win32' else 'cmd'
        self.assertNotEqual(util.which(sh), sh)
        self.assertIsNone(util.which('__scmver.util__'))
