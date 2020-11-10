#
# test_core
#
#   Copyright (c) 2019-2020 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import datetime
import os
import textwrap

from scmver import core
from base import SCMVerTestCase


class CoreTestCase(SCMVerTestCase):

    def assertVersion(self, version, normalized):
        v = core.Version(version)
        self.assertEqual(repr(v), '<Version({})>'.format(version))
        self.assertEqual(str(v), version)
        self.assertEqual(str(v.normalize()), normalized)

        v = core.Version(version.upper())
        self.assertEqual(repr(v), '<Version({})>'.format(version.upper()))
        self.assertEqual(str(v), version.upper())
        self.assertEqual(str(v.normalize()), normalized)

    def test_generate(self):
        rev = self.revision(b'scmver.core.generate')
        info = core.SCMInfo(revision=rev, branch='master')

        with self.tempfile() as path:
            core.generate(path, '1.0')
            with open(path) as fp:
                self.assertEqual(fp.read(), textwrap.dedent("""\
                    # file generated by scmver; DO NOT EDIT.

                    version = '1.0'
                """))

            core.generate(path, '1.0', info, template=textwrap.dedent("""\
                version = '{version}'
                revision = '{revision}'
            """))
            with open(path) as fp:
                self.assertEqual(fp.read(), textwrap.dedent("""\
                    version = '1.0'
                    revision = '{}'
                """.format(rev)))

    def test_load_version(self):
        self.assertEqual(core.load_version('os:name'), os.name)
        self.assertEqual(core.load_version('os:getcwd'), os.getcwd())

        data = textwrap.dedent("""\
            name = __name__
            def file():
                return __file__
        """)

        with self.tempdir() as path:
            spam = os.path.join(path, 'spam.py')
            with open(spam, 'w') as fp:
                fp.write(data)
                fp.flush()
            self.assertEqual(core.load_version('spam:name', path), 'spam')
            self.assertEqual(core.load_version('spam:file', path), spam)

        with self.tempdir() as path:
            os.mkdir(os.path.join(path, 'eggs'))
            eggs = os.path.join(path, 'eggs', '__init__.py')
            ham = os.path.join(path, 'eggs', 'ham.py')
            for p in (eggs, ham):
                with open(p, 'w') as fp:
                    fp.write(data)
                    fp.flush()
            self.assertEqual(core.load_version('eggs:name', path), 'eggs')
            self.assertEqual(core.load_version('eggs:file', path), eggs)
            self.assertEqual(core.load_version('eggs.ham:name', path), 'eggs.ham')
            self.assertEqual(core.load_version('eggs.ham:file', path), ham)

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
        self.assertEqual(v, '1.1.dev+{}.{:%Y-%m-%d}'.format(rev, datetime.datetime.now()))

        v = core.next_version(core.SCMInfo('1.0', 1, rev, True, 'master'),
                              spec='minor.dev',
                              local=lambda info: '{}.{:%Y-%m-%d}'.format(info.revision, datetime.datetime.now()))
        self.assertEqual(v, '1.1.dev+{}.{:%Y-%m-%d}'.format(rev, datetime.datetime.now()))

        with self.assertRaises(core.VersionError):
            core.next_version(core.SCMInfo('', 0, rev, False, 'master'))

    def test_stat(self):
        rev = self.revision(b'scmver.core.stat')

        with self.tempdir() as path:
            from scmver import bazaar as bzr, fossil as fsl, git, mercurial as hg, subversion as svn

            parse = {m: m.parse for m in (bzr, fsl, git, hg, svn)}
            try:
                self.assertIsNone(core.stat(path))
                kwargs = {}

                # Bazaar
                os.mkdir(os.path.join(path, '.bzr'))
                bzr.parse = lambda *a, **kw: None
                self.assertIsNone(core.stat(path))

                info = core.SCMInfo(revision='0', branch='trunk')
                bzr.parse = lambda *a, **kw: info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.bzr'] = False

                # Fossil
                for name in ('.fslckout', '_FOSSIL_'):
                    with open(os.path.join(path, name), 'w'):
                        pass
                    fsl.parse = lambda *a, **kw: None
                    self.assertIsNone(core.stat(path, **kwargs))

                    info = core.SCMInfo(revision=rev, branch='trunk')
                    fsl.parse = lambda *a, **kw: info
                    self.assertEqual(core.stat(path, **kwargs), info)
                    kwargs[name] = False

                # Git
                os.mkdir(os.path.join(path, '.git'))
                git.parse = lambda *a, **kw: None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo(branch='master')
                git.parse = lambda *a, **kw: info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.git'] = False

                # Mercurial
                os.mkdir(os.path.join(path, '.hg'))
                hg.parse = lambda *a, **kw: None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo(branch='default')
                hg.parse = lambda *a, **kw: info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.hg'] = False

                # Subversion
                os.mkdir(os.path.join(path, '.svn'))
                svn.parse = lambda *a, **kw: None
                self.assertIsNone(core.stat(path, **kwargs))

                info = core.SCMInfo()
                svn.parse = lambda *a, **kw: info
                self.assertEqual(core.stat(path, **kwargs), info)
                kwargs['.svn'] = False
            finally:
                for m in parse:
                    m.parse = parse[m]

            info = core.SCMInfo('v1.0', revision=rev, branch='default')
            with open(os.path.join(path, '.hg_archival.txt'), 'w') as fp:
                fp.write(textwrap.dedent("""\
                    repo: {0.revision}
                    node: {0.revision}
                    branch: {0.branch}
                    tag: {0.tag}
                """.format(info)))
                fp.flush()
            self.assertEqual(core.stat(path, **kwargs), info)
            kwargs['.hg_archival.txt'] = False

            self.assertIsNone(core.stat(path, **kwargs))

        with self.tempdir() as path:
            try:
                import pkg_resources
            except ImportError:
                pass
            else:
                iter_entry_points = pkg_resources.iter_entry_points
                pkg_resources.iter_entry_points = lambda *a, **kw: iter(())
                try:
                    self.assertIsNone(core.stat(path))

                    info = core.SCMInfo('v1.0', revision=rev, branch='default')
                    with open(os.path.join(path, '.hg_archival.txt'), 'w') as fp:
                        fp.write(textwrap.dedent("""\
                            repo: {0.revision}
                            node: {0.revision}
                            branch: {0.branch}
                            tag: {0.tag}
                        """.format(info)))
                        fp.flush()
                    self.assertEqual(core.stat(path), info)
                finally:
                    pkg_resources.iter_entry_points = iter_entry_points

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
                self.assertVersion(sep.join(v), '1.0{pre}0'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}0'.format(pre=norm))

                v = ['1.0' + pre]
                self.assertVersion(sep.join(v), '1.0{pre}0'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}0'.format(pre=norm))

                v = ['1.0', pre + '1']
                self.assertVersion(sep.join(v), '1.0{pre}1'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}1'.format(pre=norm))

                v = ['1.0' + pre, '1']
                self.assertVersion(sep.join(v), '1.0{pre}1'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}1'.format(pre=norm))

                v = ['1.0', pre, '1']
                self.assertVersion(sep.join(v), '1.0{pre}1'.format(pre=norm))
                self.assertVersion('1!' + sep.join(v), '1!1.0{pre}1'.format(pre=norm))

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
                self.assertVersion(sep.join(v), '1.0{s}0.dev0'.format(s=s))
                self.assertVersion('1!' + sep.join(v), '1!1.0{s}0.dev0'.format(s=s))

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
