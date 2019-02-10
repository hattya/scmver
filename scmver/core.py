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

import re


__all__ = ['Version', 'VersionError']

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


class VersionError(ValueError):
    pass
