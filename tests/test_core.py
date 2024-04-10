#
# test_core
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import datetime
import os
from pathlib import Path
import sys
import textwrap
import unittest
import unittest.mock

from scmver import core
from base import requires_tomli, SCMVerTestCase


class CoreTestCase(SCMVerTestCase):

    def assertVersion(self, version, normalized):
        v = core.Version(version)
        self.assertEqual(repr(v), f'<Version({version})>')
        self.assertEqual(str(v), version)
        self.assertEqual(str(v.normalize()), normalized)

        v = core.Version(version.upper())
        self.assertEqual(repr(v), f'<Version({version.upper()})>')
        self.assertEqual(str(v), version.upper())
        self.assertEqual(str(v.normalize()), normalized)

    def write_sync(self, fp, data):
        fp.write(textwrap.dedent(data))
        fp.flush()

    def test_generate(self):
        rev = self.revision(b'scmver.core.generate')
        info = core.SCMInfo(revision=rev, branch='master')
        template = textwrap.dedent("""\
            version = '{version}'
            revision = '{revision}'
            branch = '{branch}'
        """)

        with self.tempfile() as path:
            path = Path(path)
            core.generate(path, '1.0')
            with path.open() as fp:
                self.assertEqual(fp.read(), textwrap.dedent("""\
                    # file generated by scmver; DO NOT EDIT.

                    version = '1.0'
                """))

            core.generate(path, '1.0', info, template)
            with path.open() as fp:
                self.assertEqual(fp.read(), textwrap.dedent(f"""\
                    version = '1.0'
                    revision = '{info.revision}'
                    branch = '{info.branch}'
                """))

            core.generate(path, None, core.SCMInfo(), template)
            with path.open() as fp:
                self.assertEqual(fp.read(), textwrap.dedent("""\
                    version = ''
                    revision = ''
                    branch = ''
                """))

    def test_load_version(self):
        self.assertEqual(core.load_version('os:name'), os.name)
        self.assertEqual(core.load_version('os:getcwd'), os.getcwd())

        data = """\
            name = __name__
            def file():
                return __file__
        """

        with self.tempdir() as path:
            path = Path(path)
            spam = path / 'spam.py'
            with spam.open('w') as fp:
                self.write_sync(fp, data)
            self.assertEqual(core.load_version('spam:name', path), 'spam')
            self.assertEqual(core.load_version('spam:file', path), str(spam))

        with self.tempdir() as path:
            path = Path(path)
            eggs = path / 'eggs' / '__init__.py'
            ham = path / 'eggs' / 'ham.py'
            eggs.parent.mkdir(parents=True)
            for p in (eggs, ham):
                with p.open('w') as fp:
                    self.write_sync(fp, data)
            self.assertEqual(core.load_version('eggs:name', path), 'eggs')
            self.assertEqual(core.load_version('eggs:file', path), str(eggs))
            self.assertEqual(core.load_version('eggs.ham:name', path), 'eggs.ham')
            self.assertEqual(core.load_version('eggs.ham:file', path), str(ham))

        with self.assertRaises(ValueError):
            core.load_version('_')

    def test_next_version(self):
        rev = self.revision(b'scmver.core.next_version')

        for tag in ('v1.0', '1.0', 'spam-1.0'):
            for i, post in enumerate(('', '.post', '.post2', '.post3')):
                v = core.next_version(core.SCMInfo(tag, i, rev, False, 'master'))
                self.assertEqual(v, '1.0' + post)

            for i, micro in enumerate(('', '.1', '.2', '.3')):
                v = core.next_version(core.SCMInfo(tag, i, rev, False, 'master'),
                                      spec='micro')
                self.assertEqual(v, '1.0' + micro)

        v = core.next_version(core.SCMInfo('1.0', 1, rev, True, 'master'),
                              spec='minor.dev',
                              local='{revision}.{local:%Y-%m-%d}')
        self.assertEqual(v, f'1.1.dev+{rev}.{datetime.datetime.now():%Y-%m-%d}')

        v = core.next_version(core.SCMInfo('1.0', 1, rev, True, 'master'),
                              spec='minor.dev',
                              local=lambda info: f'{info.revision}.{datetime.datetime.now():%Y-%m-%d}')
        self.assertEqual(v, f'1.1.dev+{rev}.{datetime.datetime.now():%Y-%m-%d}')

        with self.assertRaises(core.VersionError):
            core.next_version(core.SCMInfo('', 0, rev, False, 'master'))

    @requires_tomli
    @unittest.mock.patch.dict('sys.modules')
    def test_load_project(self):
        with self.tempdir() as path:
            path = Path(path) / 'pyproject.toml'
            with path.open('w') as fp:
                self.write_sync(fp, """\
                    [build-system]
                    requires = [
                        "setuptools >= 42.0",
                        "scmver[toml] >= 1.7",
                    ]
                    build-backend = "setuptools.build_meta"
                """)
            self.assertIsNone(core.load_project(path))

            with path.open('a') as fp:
                self.write_sync(fp, """\
                    [tool._]
                """)
            self.assertIsNone(core.load_project(path))

            with path.open('a') as fp:
                self.write_sync(fp, """\
                    [tool.scmver]
                """)
            self.assertEqual(core.load_project(path), {
                'root': str(path.parent),
            })

            with path.open('a') as fp:
                self.write_sync(fp, """\
                    root = ".."
                """)
            self.assertEqual(core.load_project(path), {
                'root': str(path.parent / '..'),
            })

            with path.open('a') as fp:
                self.write_sync(fp, """\
                    write_to = "snake_case"
                """)
            self.assertEqual(core.load_project(path), {
                'root': str(path.parent / '..'),
                'write_to': 'snake_case',
            })

            with path.open('a') as fp:
                self.write_sync(fp, """\
                    write-to = "kebab-case"
                """)
            self.assertEqual(core.load_project(path), {
                'root': str(path.parent / '..'),
                'write_to': 'kebab-case',
            })

            # ImportError
            if sys.version_info >= (3, 11):
                toml = 'tomllib'
            else:
                toml = 'tomli'
            for m in tuple(sys.modules):
                if m.startswith(toml):
                    del sys.modules[m]
            sys.modules[toml] = None
            self.assertIsNone(core.load_project(path))

    def test_stat(self):
        rev = self.revision(b'scmver.core.stat')

        with self.tempdir() as path:
            with unittest.mock.patch('scmver.bazaar.parse') as bzr_parse, \
                 unittest.mock.patch('scmver.darcs.parse') as darcs_parse, \
                 unittest.mock.patch('scmver.fossil.parse') as fsl_parse, \
                 unittest.mock.patch('scmver.git.parse') as git_parse, \
                 unittest.mock.patch('scmver.mercurial.parse') as hg_parse, \
                 unittest.mock.patch('scmver.subversion.parse') as svn_parse:
                path = Path(path)
                self.assertIsNone(core.stat(path))
                kwargs = {}

                # Bazaar
                (path / '.bzr').mkdir()
                bzr_parse.return_value = None
                self.assertIsNone(core.stat(path))

                info = core.SCMInfo(revision='0', branch='trunk')
                bzr_parse.return_value = info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.bzr'] = False

                # Darcs
                (path / '_darcs').mkdir()
                darcs_parse.return_value = None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo(branch='scmver')
                darcs_parse.return_value = info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['_darcs'] = False

                # Fossil
                for name in ('.fslckout', '_FOSSIL_'):
                    with (path / name).open('w'):
                        pass
                    fsl_parse.return_value = None
                    self.assertIsNone(core.stat(path, **kwargs))

                    info = core.SCMInfo(revision=rev, branch='trunk')
                    fsl_parse.return_value = info
                    self.assertEqual(core.stat(path, **kwargs), info)
                    kwargs[name] = False

                # Git
                (path / '.git').mkdir()
                git_parse.return_value = None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo(branch='master')
                git_parse.return_value = info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.git'] = False

                # Mercurial
                (path / '.hg').mkdir()
                hg_parse.return_value = None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo(branch='default')
                hg_parse.return_value = info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.hg'] = False

                # Subversion
                (path / '.svn').mkdir()
                svn_parse.return_value = None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo()
                svn_parse.return_value = info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.svn'] = False

            info = core.SCMInfo('v1.0', revision=rev, branch='default')
            with (path / '.hg_archival.txt').open('w') as fp:
                self.write_sync(fp, f"""\
                    repo: {info.revision}
                    node: {info.revision}
                    branch: {info.branch}
                    tag: {info.tag}
                """)
            self.assertEqual(core.stat(path, **kwargs), info)
            kwargs['.hg_archival.txt'] = False

            self.assertIsNone(core.stat(path, **kwargs))

        with self.tempdir() as path, \
             unittest.mock.patch('importlib.metadata.entry_points') as entry_points:
            path = Path(path)
            entry_points.return_value = {}

            self.assertIsNone(core.stat(path))

            info = core.SCMInfo('v1.0', revision=rev, branch='default')
            with (path / '.hg_archival.txt').open('w') as fp:
                self.write_sync(fp, f"""\
                    repo: {info.revision}
                    node: {info.revision}
                    branch: {info.branch}
                    tag: {info.tag}
                """)
            self.assertEqual(core.stat(path), info)

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
                self.assertVersion(sep.join(v), f'1.0{norm}0')
                self.assertVersion('1!' + sep.join(v), f'1!1.0{norm}0')

                v = ['1.0' + pre]
                self.assertVersion(sep.join(v), f'1.0{norm}0')
                self.assertVersion('1!' + sep.join(v), f'1!1.0{norm}0')

                v = ['1.0', pre + '1']
                self.assertVersion(sep.join(v), f'1.0{norm}1')
                self.assertVersion('1!' + sep.join(v), f'1!1.0{norm}1')

                v = ['1.0' + pre, '1']
                self.assertVersion(sep.join(v), f'1.0{norm}1')
                self.assertVersion('1!' + sep.join(v), f'1!1.0{norm}1')

                v = ['1.0', pre, '1']
                self.assertVersion(sep.join(v), f'1.0{norm}1')
                self.assertVersion('1!' + sep.join(v), f'1!1.0{norm}1')

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
                self.assertVersion(sep.join(v), f'1.0{s}0.dev0')
                self.assertVersion('1!' + sep.join(v), f'1!1.0{s}0.dev0')

        self.assertEqual(core.Version('1.0.dev').dev, ('dev', -1))
        self.assertEqual(core.Version('1.0.dev1').dev, ('dev', 1))

    def test_local_version(self):
        self.assertVersion('1.0+local', '1.0+local')
        self.assertVersion('1.0+00100', '1.0+100')
        self.assertVersion('1.0+2019-02-10', '1.0+2019.2.10')

    def test_update_version(self):
        v = core.Version('1.0')
        v.update('')
        self.assertEqual(str(v), '1.0')

        for spec in (
            'major', 'minor', 'micro', 'patch',
            'pre', 'post', 'dev',
            'major.dev', 'minor.dev', 'micro.dev', 'patch.dev',
        ):
            with self.assertRaises(core.VersionError):
                core.Version('1.0+local').update(spec)

    def test_update_pre_version(self):
        for g, e in (
            ('1a', '1a1'), ('1a0', '1a1'),
            ('1b', '1b1'), ('1b0', '1b1'),
            ('1rc', '1rc1'), ('1rc0', '1rc1'),
        ):
            v = core.Version(g)
            v.update('pre')
            self.assertEqual(str(v), e)

        for g, e in (
            ('1a', '1a'), ('1a0', '1a0'),
            ('1b', '1b'), ('1b0', '1b0'),
            ('1rc', '1rc'), ('1rc0', '1rc0'),
        ):
            v = core.Version(g)
            v.update('pre', 0)
            self.assertEqual(str(v), e)

        for g, e in (
            ('1a0', '1a'), ('1a1', '1a0'),
            ('1b0', '1b'), ('1b1', '1b0'),
            ('1rc0', '1rc'), ('1rc1', '1rc0'),
        ):
            v = core.Version(g)
            v.update('pre', -1)
            self.assertEqual(str(v), e)

        with self.assertRaises(core.VersionError):
            core.Version('1.0').update('pre')

    def test_update_release_version(self):
        for spec, tests in (
            ('major', (('0', '1'), ('0.0', '1.0'), ('0.0.0', '1.0.0'))),
            ('minor', (('1', '1.1'), ('1.0', '1.1'), ('1.0.0', '1.1.0'))),
            ('micro', (('1', '1.0.1'), ('1.0', '1.0.1'), ('1.0.0', '1.0.1'))),
            ('patch', (('1', '1.0.1'), ('1.0', '1.0.1'), ('1.0.0', '1.0.1'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('major', (('1', '1'), ('1.0', '1.0'), ('1.0.0', '1.0.0'))),
            ('minor', (('1', '1.0'), ('1.0', '1.0'), ('1.0.0', '1.0.0'))),
            ('micro', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
            ('patch', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec, 0)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('major', (('0', '0'), ('0.0', '0.0'), ('0.0.0', '0.0.0'))),
            ('minor', (('1', '1.0'), ('1.0', '1.0'), ('1.0.0', '1.0.0'))),
            ('micro', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
            ('patch', (('1', '1.0.0'), ('1.0', '1.0.0'), ('1.0.0', '1.0.0'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec, -1)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('major', (('0a', '1'), ('0b', '1'), ('0rc', '1'), ('0.post', '1'), ('0.dev', '1'))),
            ('minor', (('0a', '0.1'), ('0b', '0.1'), ('0rc', '0.1'), ('0.post', '0.1'), ('0.dev', '0.1'))),
            ('micro', (('0a', '0.0.1'), ('0b', '0.0.1'), ('0rc', '0.0.1'), ('0.post', '0.0.1'), ('0.dev', '0.0.1'))),
            ('patch', (('0a', '0.0.1'), ('0b', '0.0.1'), ('0rc', '0.0.1'), ('0.post', '0.0.1'), ('0.dev', '0.0.1'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec)
                self.assertEqual(str(v), e)

    def test_update_post_version(self):
        for g, e in (
            ('1.0', '1.0.post'), ('1.0.post', '1.0.post1'), ('1.0.post0', '1.0.post1'),
            ('1.0-0', '1.0-1'),
        ):
            v = core.Version(g)
            v.update('post')
            self.assertEqual(str(v), e)

        for g, e in (
            ('1.0', '1.0.post'), ('1.0.post', '1.0.post'), ('1.0.post0', '1.0.post0'),
            ('1.0-0', '1.0-0'),
        ):
            v = core.Version(g)
            v.update('post', 0)
            self.assertEqual(str(v), e)

        for g, e in (
            ('1.0', '1.0'), ('1.0.post0', '1.0.post'), ('1.0.post1', '1.0.post0'),
            ('1.0-0', '1.0-0'), ('1.0-1', '1.0-0'),
        ):
            v = core.Version(g)
            v.update('post', -1)
            self.assertEqual(str(v), e)

    def test_update_dev_version(self):
        for spec, tests in (
            ('dev', (('1.0.dev', '1.0.dev1'), ('1.0.dev0', '1.0.dev1'))),
            ('major.dev', (('0', '1.dev'), ('0.0', '1.0.dev'), ('0.1', '1.0.dev'))),
            ('minor.dev', (('1', '1.1.dev'), ('1.0', '1.1.dev'), ('1.0.0', '1.1.0.dev'), ('1.0.1', '1.1.0.dev'))),
            ('micro.dev', (('1', '1.0.1.dev'), ('1.0', '1.0.1.dev'), ('1.0.0', '1.0.1.dev'), ('1.0.0.0', '1.0.1.0.dev'), ('1.0.0.1', '1.0.1.0.dev'))),
            ('patch.dev', (('1', '1.0.1.dev'), ('1.0', '1.0.1.dev'), ('1.0.0', '1.0.1.dev'), ('1.0.0.0', '1.0.1.0.dev'), ('1.0.0.1', '1.0.1.0.dev'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec)
                self.assertEqual(str(v), e)

        for spec, tests in (
            ('dev', (('1.0.dev', '1.0.dev'), ('1.0.dev0', '1.0.dev0'))),
            ('major.dev', (('0.0', '1.0.dev'), ('0.0.dev', '1.0.dev'))),
            ('minor.dev', (('1.0', '1.1.dev'), ('1.0.dev', '1.1.dev'))),
            ('micro.dev', (('1.0.0', '1.0.1.dev'), ('1.0.0.dev', '1.0.1.dev'))),
            ('patch.dev', (('1.0.0', '1.0.1.dev'), ('1.0.0.dev', '1.0.1.dev'))),
        ):
            for g, e in tests:
                v = core.Version(g)
                v.update(spec, 0)
                self.assertEqual(str(v), e)

        for g, e in (
            ('1.0.dev0', '1.0.dev'), ('1.0.dev1', '1.0.dev0'),
        ):
            v = core.Version(g)
            v.update('dev', -1)
            self.assertEqual(str(v), e)

        for spec in ('dev', '_.dev'):
            with self.assertRaises(core.VersionError):
                core.Version('1.0').update(spec)

        for spec in ('major.dev', 'minor.dev', 'micro.dev', 'patch.dev'):
            with self.assertRaises(core.VersionError):
                core.Version('1.0').update(spec, -1)
