#
# test_cli
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import datetime
import io
import os
import textwrap
import unittest
import unittest.mock

try:
    import click
    import click.testing

    from scmver import __version__, cli, core
except ImportError:
    click = None
from base import SCMVerTestCase


requires_click = unittest.skipUnless(click, 'requires click')


@requires_click
@unittest.mock.patch('scmver.core.stat')
class CLITestCase(SCMVerTestCase):

    def invoke(self, args):
        runner = click.testing.CliRunner()
        return runner.invoke(cli.cli, args)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_run(self, stdout, stat):
        try:
            cli.run(['--version'])
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        self.assertEqual(stdout.getvalue().strip(), f'scmver, version {__version__}')

    def test_generate_without_repository(self, stat):
        stat.return_value = None

        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            self.assertEqual(os.stat(path).st_size, 0)

    def test_generate_with_defaults(self, stat):
        rev = self.revision(b'scmver.cli.generate')

        stat.return_value = core.SCMInfo('v1.0', 0, rev, False, 'master')
        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0'")

        stat.return_value = core.SCMInfo('v1.0', 1, rev, False, 'master')
        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], "version = '1.0.post'")

        stat.return_value = core.SCMInfo('v1.0', 0, rev, True, 'master')
        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], f"version = '1.0+{datetime.datetime.now():%Y-%m-%d}'")

        stat.return_value = core.SCMInfo('v1.0', 1, rev, True, 'master')
        with self.tempfile() as path:
            rv = self.invoke(['generate', path])
            self.assertEqual(rv.exit_code, 0)
            with open(path) as fp:
                self.assertEqual(fp.read().splitlines()[-1], f"version = '1.0.post+{datetime.datetime.now():%Y-%m-%d}'")

    def test_generate_with_template(self, stat):
        rev = self.revision(b'scmver.cli.generate')
        stat.return_value = core.SCMInfo('v1.0', 0, rev, False, 'master')

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

    def test_load(self, stat):
        rv = self.invoke(['load', 'os:name'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, f'{os.name}\n')

        rv = self.invoke(['load', 'os:getcwd'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, f'{os.getcwd()}\n')

    def test_next_without_repository(self, stat):
        stat.return_value = None

        rv = self.invoke(['next'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '')

    def test_next_with_defaults(self, stat):
        rev = self.revision(b'scmver.cli.next')

        stat.return_value = core.SCMInfo('v1.0', 0, rev, False, 'master')
        rv = self.invoke(['next'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '1.0\n')

        stat.return_value = core.SCMInfo('v1.0', 1, rev, False, 'master')
        rv = self.invoke(['next'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '1.0.post\n')

        stat.return_value = core.SCMInfo('v1.0', 0, rev, True, 'master')
        rv = self.invoke(['next'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, f'1.0+{datetime.datetime.now():%Y-%m-%d}\n')

        stat.return_value = core.SCMInfo('v1.0', 1, rev, True, 'master')
        rv = self.invoke(['next'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, f'1.0.post+{datetime.datetime.now():%Y-%m-%d}\n')

    def test_next_with_spec(self, stat):
        rev = self.revision(b'scmver.cli.next')
        stat.return_value = core.SCMInfo('v1.0', 1, rev, False, 'master')

        rv = self.invoke(['next', '-s', 'minor.dev'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '1.1.dev\n')

    def test_next_with_local(self, stat):
        rev = self.revision(b'scmver.cli.next')
        stat.return_value = core.SCMInfo('v1.0', 0, rev, True, 'master')

        rv = self.invoke(['next', '-l', '{local:%Y%m%d}'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, f'1.0+{datetime.datetime.now():%Y%m%d}\n')

        rv = self.invoke(['next', '-l', 'dirty'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '1.0+dirty\n')

        rv = self.invoke(['next', '-l', 'def local(info): import time; return time.strftime("%Y%m%d")'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, f'1.0+{datetime.datetime.now():%Y%m%d}\n')

        rv = self.invoke(['next', '-l', 'def local(): return'])
        self.assertEqual(rv.exit_code, 2)
        self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ "<function local at 0x\w+>" does not have arguments\.$')

        rv = self.invoke(['next', '-l', 'local = "dirty"'])
        self.assertEqual(rv.exit_code, 2)
        self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ Callable object does not found\.$')

    def test_next_with_version(self, stat):
        rev = self.revision(b'scmver.cli.next')
        stat.return_value = core.SCMInfo('spam-1.0', 0, rev, False, 'master')

        rv = self.invoke(['next', '-v', r'spam-(?P<version>\d+\..+)'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '1.0\n')

        rv = self.invoke(['next', '-v', r'spam-([9-0]+\..+)'])
        self.assertEqual(rv.exit_code, 2)
        self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ bad character range(?: 9-0 at position 7)?$')

        rv = self.invoke(['next', '-v', r'spam-(\d+\..+)'])
        self.assertEqual(rv.exit_code, 2)
        self.assertRegex(rv.output.splitlines()[-1], r'^Error: .+ Regex does not have the version group\.$')

    def test_stat_without_repository(self, stat):
        stat.return_value = None

        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, '')

    def test_stat_with_defaults(self, stat):
        rev = self.revision(b'scmver.cli.stat')

        stat.return_value = core.SCMInfo(branch='HEAD')
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent("""\
            Distance: 0
            Dirty:    False
            Branch:   HEAD
        """))

        stat.return_value = core.SCMInfo('0.0', 1, rev, False, 'master')
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent(f"""\
            Distance: 1
            Revision: {rev}
            Dirty:    False
            Branch:   master
        """))

        stat.return_value = core.SCMInfo('v1.0', 0, rev, True, 'master')
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent(f"""\
            Tag:      v1.0
            Distance: 0
            Revision: {rev}
            Dirty:    True
            Branch:   master
        """))

        stat.return_value = core.SCMInfo('v1.0', 0, rev)
        rv = self.invoke(['stat'])
        self.assertEqual(rv.exit_code, 0)
        self.assertEqual(rv.output, textwrap.dedent(f"""\
            Tag:      v1.0
            Distance: 0
            Revision: {rev}
            Dirty:    False
        """))


@requires_click
class GroupTestCase(SCMVerTestCase):

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
        self.assertRegex(rv.output.splitlines()[-1], r'^Error: command .c. is ambiguous: checkout commit$')

    def test_unknown(self):
        rv = self.invoke(['clone'])
        self.assertIsNotNone(rv.exception)
        self.assertEqual(rv.exit_code, 2)
        self.assertRegex(rv.output.splitlines()[-1], r'^Error: No such command .clone.\.$')
