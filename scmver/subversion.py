#
# scmver.subversion
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

import os
import re
import xml.etree.cElementTree as ET

from . import core, util


__all__ = ['parse', 'run']

_TAG = 'subversion.tag'
# layout
_TRUNK = 'subversion.trunk'
_BRANCHES = 'subversion.branches'
_TAGS = 'subversion.tags'
# status
_MODIFIED = frozenset(('added', 'conflicted', 'deleted', 'incomplete', 'missing', 'modified', 'obstructed', 'replaced'))


def parse(root, name='.svn', **kwargs):
    if name == '.svn':
        info = _info(root)
        if not _is_wc_root(root, info):
            return

        revision = int(info.get('Revision', 0))
        branch = _branch_of(info, **kwargs)

        out = run('status', '--xml', cwd=root)[0]
        for e in ET.fromstring(out).iterfind('.//wc-status'):
            if (e.get('item') in _MODIFIED
                or e.get('props') in _MODIFIED):
                dirty = True
                break
        else:
            dirty = False

        tags = _rel(_TAGS, 'tags', **kwargs)
        url = info['Repository Root'] + tags
        r = revision
        tag_re = re.compile(kwargs[_TAG]) if _TAG in kwargs else None
        while r > 0:
            out = run('log', '-r', '{}:0'.format(r), '-v', '--xml', '-l', '10', url, cwd=root)[0]
            for e in ET.fromstring(out).iterfind('./logentry'):
                r = int(e.get('revision'))
                for p in e.iterfind('.//path[@kind="dir"]'):
                    if not p.text.startswith(tags):
                        continue
                    tag = p.text[len(tags):].split('/', 1)[0]
                    if (not tag_re
                        or tag_re.match(tag)):
                        return core.SCMInfo(tag, _distance_of(root, info, r), revision, dirty, branch)
            r -= 1
        return core.SCMInfo(distance=_distance_of(root, info, 0),
                            revision=revision,
                            dirty=dirty,
                            branch=branch)


def _info(root):
    out = run('info', cwd=root)[0].strip().splitlines()
    return dict((s.strip() for s in l.split(':', 1)) for l in out)


def _is_wc_root(root, info):
    root = os.path.normpath(os.path.abspath(root))
    if root == info.get('Working Copy Root Path'):
        return True
    elif info:
        p = os.path.dirname(root)
        return (p == root
                or not os.path.isdir(os.path.join(p, '.svn'))
                or _info(p).get('Repository UUID') == info['Repository UUID'])
    return False


def _distance_of(root, info, rev):
    rev = str(rev)
    i = 0
    out = run('log', '-r', '{}:{}'.format(info.get('Revision', 'BASE'), rev), '--xml', cwd=root)[0]
    for e in ET.fromstring(out).iterfind('./logentry'):
        if e.get('revision') != rev:
            i += 1
    return i


def _branch_of(info, **kwargs):
    url = info['URL']
    trunk = info['Repository Root'] + _rel(_TRUNK, 'trunk', **kwargs)
    if (url == trunk[:-1]
        or url.startswith(trunk)):
        return 'trunk'
    branches = info['Repository Root'] + _rel(_BRANCHES, 'branches', **kwargs)
    if url.startswith(branches):
        return url[len(branches):].split('/', 1)[0]


def _rel(key, default, **kwargs):
    return '/' + os.path.normpath(kwargs.get(key, default)).replace(os.sep, '/').strip('/') + '/'


def run(*args, **kwargs):
    return util.exec_((util.which('svn'), '--non-interactive') + args, **kwargs)
