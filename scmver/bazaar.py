#
# scmver.bazaar
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

from . import core, util


__all__ = ['parse', 'run']

_TAG = 'bazaar.tag'


def parse(root, name='.bzr', **kwargs):
    if name == '.bzr':
        info = _version_info(root)
        if not info:
            return

        dirty = info['clean'] == 'False'

        tag_re = re.compile(kwargs[_TAG]) if _TAG in kwargs else None
        out = [l.split() for l in run('tags', cwd=root)[0].splitlines()]
        out.sort(key=lambda v: v[1], reverse=True)
        for tag, rev in out:
            if (rev == info['revno']
                and (not tag_re
                     or tag_re.match(tag))):
                return core.SCMInfo(tag, _distance_of(root, rev), info['revno'], dirty, info['branch-nick'])
        return core.SCMInfo(distance=_distance_of(root),
                            revision=info['revno'],
                            dirty=dirty,
                            branch=info['branch-nick'])


def _version_info(root):
    out = run('version-info', '--check-clean', cwd=root)[0].splitlines()
    return dict((s.strip() for s in l.split(':', 1)) for l in out)


def _distance_of(root, rev=None):
    if rev is None:
        rev = 1
        off = 0
    else:
        off = 1
    return len(run('log', '-r', '{}..'.format(rev), '-n', '0', '--line', cwd=root)[0].splitlines()) - off


def run(*args, **kwargs):
    return util.exec_((util.which('bzr'),) + args, **kwargs)
