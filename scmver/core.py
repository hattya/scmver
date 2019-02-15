#
# scmver.core
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

import collections
import datetime
import os
import re


__all__ = ['next_version', 'stat', 'SCMInfo', 'Version', 'VersionError']

_pep440_re = re.compile(r"""
    \A
    v?
    # public version identifiers
    (?:             # epoch segment
        (?P<epoch>[0-9]+) !
    )?
    (?P<release>    # release segment
        [0-9]+ (?:\. [0-9]+)*
    )
    (?:             # pre-release segment
        (?P<pre_sep>[-._])?
        (?P<pre_s>
            a  | alpha |
            b  | beta  |
            rc | c     | pre (?:view)?
        )
        (?P<pre_opt_sep>[-._])?
        (?P<pre_n>[0-9]*)
    )?
    (?:             # post-release segment
        (?:
            (?:
                (?P<post_sep>[-._])?
                (?P<post_s>
                    post | r (?:ev)?
                )
                (?P<post_opt_sep>[-._])?
            ) |
            -
        )
        (?P<post_n>(?(post_s)[0-9]*|[0-9]+))
    )?
    (?:             # development release segment
        (?P<dev_sep>[-._])?
        (?P<dev_s>
            dev
        )
        (?P<dev_opt_sep>[-._])?
        (?P<dev_n>[0-9]*)
    )?
    # local version identifiers
    (?:
        \+
        (?P<local>
            [a-z0-9] (?:[a-z0-9-_.]* [a-z0-9])?
        )
    )?
    \Z
""", re.IGNORECASE | re.VERBOSE)
_sep_re = re.compile(r'[-._]')
_version_re = re.compile(r'(?P<version>v?\d+.*)\Z')


def next_version(info, spec='post', local='{local:%Y-%m-%d}', version=_version_re):
    m = version.search(info.tag)
    if not m:
        raise VersionError('cannot parse version from SCM tag')

    pv = Version(m.group('version'))
    if info.distance > 0:
        pv.update(spec, info.distance)

    if callable(local):
        lv = local(info)
    elif info.dirty:
        lv = local.format(distance=info.distance,
                          revision=info.revision,
                          branch=info.branch,
                          utc=datetime.datetime.utcnow(),
                          local=datetime.datetime.now())
    else:
        lv = None
    return str(pv) if not lv else '{}+{}'.format(pv, lv)


def stat(path, **kwargs):
    try:
        import pkg_resources

        impls = [(ep.name, ep.load()) for ep in pkg_resources.iter_entry_points(group='scmver.parse')]
    except ImportError:
        from . import git, mercurial

        impls = [('.git', git.parse), ('.hg', mercurial.parse), ('.hg_archival.txt', mercurial.parse)]

    path = os.path.abspath(path)
    while True:
        for name, parse in impls:
            if (kwargs.get(name, True)
                and os.path.exists(os.path.join(path, name))):
                info = parse(path, name=name, **kwargs)
                if info:
                    return info
        p, path = path, os.path.dirname(path)
        if path == p:
            break


SCMInfo = collections.namedtuple('SCMInfo', ('tag', 'distance', 'revision', 'dirty', 'branch'))
SCMInfo.__new__.__defaults__ = ('0.0', 0, None, False, None)


class Version(object):

    __slots__ = ('epoch', 'release', '_pre', '_post', '_dev', 'local')

    def __init__(self, version):
        m = _pep440_re.match(version.strip())
        if not m:
            raise VersionError('invalid version: {!r}'.format(version))

        self.epoch = int(m.group('epoch')) if m.group('epoch') else 0
        self.release = tuple(map(int, m.group('release').split('.')))
        for g in ('pre', 'post', 'dev'):
            s = m.group(g + '_s')
            n = m.group(g + '_n')
            setattr(self, '_' + g, (m.group(g + '_sep') or '', s, m.group(g + '_opt_sep') or '', int(n) if n else -1) if s or n else None)
        self.local = m.group('local')

    def __repr__(self):
        return '<{}({})>'.format(self.__class__.__name__, self)

    def __str__(self):
        def seg(v):
            return (v[0], v[1], v[2], str(v[3]) if v[3] >= 0 else '')

        buf = []
        if self.epoch != 0:
            buf.append('{}!'.format(self.epoch))
        buf.append('.'.join(map(str, self.release)))
        if self._pre:
            buf += seg(self._pre)
        if self._post:
            if self._post[1]:
                buf += seg(self._post)
            else:
                buf.append('-{}'.format(self._post[3]))
        if self._dev:
            buf += seg(self._dev)
        if self.local:
            buf.append('+{}'.format(self.local))
        return ''.join(buf)

    @property
    def pre(self):
        if self._pre:
            return self._pre[1::2]

    @property
    def post(self):
        if self._post:
            return self._post[1::2]

    @property
    def dev(self):
        if self._dev:
            return self._dev[1::2]

    def normalize(self):
        def seg(s, v, sep='.'):
            return (sep, s, '', v[3] if v[3] >= 0 else 0)

        v = self.__class__(str(self).lower())
        if v._pre:
            s = v._pre[1]
            if s == 'alpha':
                s = 'a'
            elif s == 'beta':
                s = 'b'
            elif s in ('c', 'pre', 'preview'):
                s = 'rc'
            v._pre = seg(s, v._pre, sep='')
        if v._post:
            v._post = seg('post', v._post)
        if v._dev:
            v._dev = seg('dev', v._dev)
        if v.local:
            v.local = '.'.join(str(int(s)) if s.isdigit() else s for s in _sep_re.split(v.local))
        return v

    def update(self, spec, value=1):
        if self.local:
            raise VersionError('local version identifiers exists')

        def update(ver, val):
            if ver < 0:
                return val if val > 0 else -1
            return ver + val

        def zero(v):
            return v if v >= 0 else 0

        spec = spec.lower()
        if spec == 'major':
            self.release = (zero(self.release[0] + value),) + self.release[1:]
            self._pre = self._post = self._dev = None
        elif spec == 'minor':
            if len(self.release) < 2:
                self.release += (zero(value),)
            else:
                self.release = self.release[:1] + (zero(self.release[1] + value),) + self.release[2:]
            self._pre = self._post = self._dev = None
        elif spec in ('micro', 'patch'):
            if len(self.release) < 2:
                self.release += (0, zero(value),)
            elif len(self.release) < 3:
                self.release += (zero(value),)
            else:
                self.release = self.release[:2] + (zero(self.release[2] + value),) + self.release[3:]
            self._pre = self._post = self._dev = None
        elif spec in ('pre', 'dev'):
            v = getattr(self, '_' + spec)
            if not v:
                raise VersionError('{}release segment does not exist'.format('pre-' if spec != 'dev' else 'development '))
            setattr(self, '_' + spec, v[:3] + (update(v[3], value),))
        elif spec == 'post':
            if self._post:
                if self._post[1]:
                    self._post = self._post[:3] + (update(self._post[3], value),)
                else:
                    self._post = self._post[:3] + (zero(self._post[3] + value),)
            elif value >= 0:
                self._post = ('.', 'post', '', value if value > 1 else -1)
        elif spec.endswith('.dev'):
            spec = spec[:-len('.dev')]
            if spec == 'major':
                i = 1
            elif spec == 'minor':
                i = 2
            elif spec in ('micro', 'patch'):
                i = 3
            else:
                raise VersionError('invalid segment specifier')
            if value < 0:
                raise VersionError('invalid value')

            self.release = self.release[:i] + (0,) * (len(self.release) - i)
            self.update(spec)
            self._dev = ('.', 'dev', '', value if value > 1 else -1)


class VersionError(ValueError):
    pass
