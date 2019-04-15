#
# scmver.git
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from . import core, util


__all__ = ['parse', 'run']

_TAG = 'git.tag'


def parse(root, name='.git', **kwargs):
    if name == '.git':
        args = ['describe', '--dirty=+', '--tags', '--abbrev=40', '--long', '--always']
        if _TAG in kwargs:
            args += ('--match', kwargs[_TAG])
        out = run(*args, cwd=root)[0].strip().rsplit('-', 2)

        branch = run('rev-parse', '--abbrev-ref', 'HEAD', cwd=root)[0].strip()
        if branch == 'HEAD':
            branch = run('symbolic-ref', '--short', 'HEAD', cwd=root)[0].strip() or None

        if len(out) == 3:
            return core.SCMInfo(out[0], int(out[1]), out[2][1:].rstrip('+'), out[2].endswith('+'), branch)
        elif out[0]:
            return core.SCMInfo(distance=len(run('rev-list', 'HEAD', '--', cwd=root)[0].splitlines()),
                                revision=out[0].rstrip('+'),
                                dirty=out[0].endswith('+'),
                                branch=branch)
        elif branch:
            return core.SCMInfo(dirty=any(l for l in run('status', '--porcelain', cwd=root)[0].splitlines() if l[0] != '?'),
                                branch=branch)


def run(*args, **kwargs):
    return util.exec_((util.which('git'),) + args, **kwargs)
