#
# scmver.bazaar
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
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
