#
# scmver.bazaar
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import re

from . import core, util


__all__ = ['parse', 'version', 'run']

_TAG = 'bazaar.tag'

_version_re = re.compile(r"""
    \A
    (?:Bazaar \s+ \(bzr\) | bzr \s+ \(bazaar-ng\)) \s+
    # version number
    (?P<release>
        [0-9]+ (?:\. [0-9]+)+
    )
    # release level
    (?:
        (?:
            (?P<pre_s>
                b  | beta |
                rc
            )
            (?P<pre_n>[0-9]+)
        ) |
        (?:
            (?P<dev_s>
                dev
            )
            (?P<dev_n>[0-9]*)
        )
    )?
    \Z
""", re.VERBOSE)


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


def version():
    out = run('version')[0].splitlines()
    m = _version_re.match(out[0] if out else '')
    if not m:
        return ()

    v = tuple(map(int, m.group('release').split('.')))
    if len(v) < 3:
        v += (0,) * (3 - len(v))
    if m.group('pre_s'):
        s = m.group('pre_s')
        v += ('b' if s == 'beta' else s, int(m.group('pre_n')))
    elif m.group('dev_s'):
        n = m.group('dev_n')
        v += (m.group('dev_s'), int(n) if n else 0)
    return v


def run(*args, **kwargs):
    return util.exec_((util.which('bzr'),) + args, **kwargs)
