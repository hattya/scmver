#
# scmver.subversion
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import re
import xml.etree.cElementTree as ET

from . import _compat as five
from . import core, util


__all__ = ['parse', 'version', 'run']

_TAG = 'subversion.tag'
# layout
_TRUNK = 'subversion.trunk'
_BRANCHES = 'subversion.branches'
_TAGS = 'subversion.tags'
# status
_MODIFIED = frozenset(('added', 'conflicted', 'deleted', 'incomplete', 'missing', 'modified', 'obstructed', 'replaced'))

_version_re = re.compile(r"""
    \A
    (?:svn | Subversion \s+ Client) , \s+
    version \s+
    # version number
    (?P<release>
        [0-9]+ (?:\. [0-9]+)+
    )
    # version tag
    \s+
    \(
        (?:
            # pre-release
            (?:
                (?P<pre_s>
                    Alpha                 |
                    Beta                  |
                    Release \s+ Candidate
                )
                \s*
                (?P<pre_n>[0-9]+)
            ) |
            # final release
            r [0-9]+
        )
    \)
""", re.IGNORECASE | re.VERBOSE)


def parse(root, name='.svn', **kwargs):
    if name == '.svn':
        info = _info(root)
        if not _is_wc_root(root, info):
            return

        revision = int(info.get('Revision', 0))
        branch = _branch_of(info, **kwargs)

        out = run('status', '--xml', cwd=root)[0]
        for e in out.iterfind('.//wc-status'):
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
            for e in out.iterfind('./logentry'):
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
    if os.path.normcase(root) == os.path.normcase(info.get('Working Copy Root Path', '')):
        return True
    elif info:
        p = os.path.dirname(root)
        return (p == root
                or not os.path.isdir(os.path.join(p, '.svn'))
                or _info(p).get('Repository UUID') != info['Repository UUID'])
    return False


def _distance_of(root, info, rev):
    rev = str(rev)
    i = 0
    out = run('log', '-r', '{}:{}'.format(info.get('Revision', 'BASE'), rev), '--xml', cwd=root)[0]
    for e in out.iterfind('./logentry'):
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
        return five.urlunquote(url[len(branches):].split('/', 1)[0])


def _rel(key, default, **kwargs):
    return '/' + os.path.normpath(kwargs.get(key, default)).replace(os.sep, '/').strip('/') + '/'


def version():
    out = run('--version')[0].splitlines()
    m = _version_re.match(out[0] if out else '')
    if not m:
        return ()

    v = tuple(map(int, m.group('release').split('.')))
    if m.group('pre_s'):
        s = m.group('pre_s').lower()
        v += ('rc' if s == 'release candidate' else s[0], int(m.group('pre_n')))
    return v


def run(*args, **kwargs):
    xml = '--xml' in args
    if xml:
        kwargs['encoding'] = 'utf-8'
    out, err = util.exec_((util.which('svn'), '--non-interactive') + args, **kwargs)
    return ET.fromstring(out.encode('utf-8')) if xml else out, err
