#
# test_util
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from pathlib import Path
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

        out, err = util.exec_((Path(sys.executable), '-V'))
        self.assertEqual(version_of(out), 'Python {}.{}.{}'.format(*sys.version_info))
        self.assertEqual(err, '')

        cmd = 'import sys; getattr(sys.stdout, "buffer", sys.stdout).write("\\U0001d70b = 3.14".encode("utf-8"))'
        out, err = util.exec_((Path(sys.executable), '-c', cmd), encoding='utf-8')
        self.assertEqual(out, '\U0001d70b = 3.14')
        self.assertEqual(err, '')

    def test_command(self):
        sh = 'sh' if sys.platform != 'win32' else 'cmd'
        self.assertEqual(Path(util.command(sh)).stem, sh)
        self.assertEqual(Path(util.command('__scmver.util__', sh)).stem, sh)

        with self.assertRaisesRegex(OSError, r': __scmver\.util__$'):
            util.command('__scmver.util__')
        with self.assertRaisesRegex(OSError, r': __scmver\.util__$'):
            util.command('__scmver.util__', '__test_util__')

    def test_which(self):
        sh = 'sh' if sys.platform != 'win32' else 'cmd'
        self.assertNotEqual(util.which(sh), sh)
        self.assertEqual(Path(util.which(sh)).stem, sh)
        self.assertIsNone(util.which('__scmver.util__'))
