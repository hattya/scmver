#
# test_cli
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
import io
import os
import sys
import textwrap
import unittest

try:
    import click
    import click.testing

    from scmver import _compat as five
    from scmver import __version__, cli, core
except ImportError:
    click = None
from base import SCMVerTestCase


@unittest.skipUnless(click, 'requires click')
class CLITestCase(SCMVerTestCase):

    def setUp(self):
        self._stat = core.stat

    def tearDown(self):
        core.stat = self._stat

    def invoke(self, args):
        runner = click.testing.CliRunner()
        return runner.invoke(cli.cli, args)

    def test_run(self):
        out = io.BytesIO()
        stdout = sys.stdout
        try:
            if five.PY2:
                sys.stdout = out
            else:
                sys.stdout = io.TextIOWrapper(out, encoding='utf-8')
            cli.run(['--version'])
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        finally:
            sys.stdout = stdout
        self.assertEqual(out.getvalue().decode('utf-8').strip(), 'scmver, version {}'.format(__version__))

    def test_generate_without_repository(self):
        core.stat = lambda *a, **kw: None

        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            self.assertEqual(os.stat(path).st_size, 0)

    def test_generate_with_defaults(self):
        rev = self.revision(b'scmver.cli.generate')
        core.stat = lambda *a, **kw: core.SCMInfo('v1.0', 0, rev, False, 'master')

        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0'")

    def test_generate_with_spec(self):
        rev = self.revision(b'scmver.cli.generate')
        core.stat = lambda *a, **kw: core.SCMInfo('v1.0', 1, rev, False, 'master')

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-s', 'minor.dev', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.1.dev'")

    def test_generate_with_local(self):
        rev = self.revision(b'scmver.cli.generate')
        core.stat = lambda *a, **kw: core.SCMInfo('v1.0', 0, rev, True, 'master')

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-l', '{local:%Y%m%d}', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0+{:%Y%m%d}'".format(datetime.datetime.now()))

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-l', 'dirty', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0+dirty'")

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-l', 'def local(info): import time; return time.strftime("%Y%m%d")', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0+{:%Y%m%d}'".format(datetime.datetime.now()))

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-l', 'def local(): return', path])
            self.assertEqual(rv.exit_code, 2)
            self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ "<function local at 0x\w+>" does not have arguments\.$')
            self.assertEqual(os.stat(path).st_size, 0)

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-l', 'local = "dirty"', path])
            self.assertEqual(rv.exit_code, 2)
            self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ Callable object does not found\.$')
            self.assertEqual(os.stat(path).st_size, 0)

    def test_generate_with_version(self):
        rev = self.revision(b'scmver.cli.generate')
        core.stat = lambda *a, **kw: core.SCMInfo('spam-1.0', 0, rev, False, 'master')

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-v', r'spam-(?P<version>\d+\..+)', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0'")

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-v', r'spam-([9-0]+\..+)', path])
            self.assertEqual(rv.exit_code, 2)
            self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ bad character range(?: 9-0 at position 7)?$')
            self.assertEqual(os.stat(path).st_size, 0)

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-v', r'spam-(\d+\..+)', path])
            self.assertEqual(rv.exit_code, 2)
            self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ Regex does not have the version group\.$')
            self.assertEqual(os.stat(path).st_size, 0)

    def test_generate_with_template(self):
        rev = self.revision(b'scmver.cli.generate')
        core.stat = lambda *a, **kw: core.SCMInfo('v1.0', 0, rev, False, 'master')

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-t', "__version__ = '{version}'\\n", path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read(), "__version__ = '1.0'\n")

        with self.tempfile() as path:
            rv = self.invoke(['generate', '-t', "__version__ = '{version}'\\r\\n", path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read(), "__version__ = '1.0'\n")

    def test_stat_without_repository(self):
        core.stat = lambda *a, **kw: None

        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '')

    def test_stat_with_defaults(self):
        rev = self.revision(b'scmver.cli.stat')

        core.stat = lambda *a, **kw: core.SCMInfo(branch='HEAD')
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent("""\
            Distance: 0
            Dirty:    False
            Branch:   HEAD
        """.format(rev)))

        core.stat = lambda *a, **kw: core.SCMInfo('0.0', 1, rev, False, 'master')
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent("""\
            Distance: 1
            Revision: {}
            Dirty:    False
            Branch:   master
        """.format(rev)))

        core.stat = lambda *a, **kw: core.SCMInfo('v1.0', 0, rev, True, 'master')
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent("""\
            Tag:      v1.0
            Distance: 0
            Revision: {}
            Dirty:    True
            Branch:   master
        """.format(rev)))

        core.stat = lambda *a, **kw: core.SCMInfo('v1.0', 0, rev)
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent("""\
            Tag:      v1.0
            Distance: 0
            Revision: {}
            Dirty:    False
        """.format(rev)))


@unittest.skipUnless(click, 'requires click')
class GroupTestCase(unittest.TestCase):

    def group(self):
        return click.group(cls=cli._Group)

    def invoke(self, args):
        @self.group()
        def cli():
            pass

        @cli.command()
        def checkout():
            click.echo('checkout')

        @cli.command()
        def commit():
            click.echo('commit')

        runner = click.testing.CliRunner()
        return runner.invoke(cli, args)

    def test_exact(self):
        rv = self.invoke(['checkout'])
        self.assertIsNone(rv.exception)
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, 'checkout\n')

    def test_match(self):
        rv = self.invoke(['co'])
        self.assertIsNone(rv.exception)
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, 'commit\n')

    def test_ambiguous(self):
        rv = self.invoke(['c'])
        self.assertIsNotNone(rv.exception)
        self.assertEqual(rv.exit_code, 2)
        self.assertEqual(rv.output.splitlines()[-1], 'Error: command "c" is ambiguous: checkout commit')

    def test_unknown(self):
        rv = self.invoke(['clone'])
        self.assertIsNotNone(rv.exception)
        self.assertEqual(rv.exit_code, 2)
        self.assertEqual(rv.output.splitlines()[-1], 'Error: No such command "clone".')
