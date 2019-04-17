#
# scmver.git
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import re

from . import core, util


__all__ = ['parse', 'version', 'run']

_TAG = 'git.tag'

_version_re = re.compile(r"""
    \A
    git \s+
    version \s+

    (?P<release>
        [0-9]+ (?:\. [0-9]+)+
    )
    (?P<alpha>[a-z]+)?
    (?:
        - rc (?P<rc>[0-9]+)
    )?
    # Git for Windows
    (?:
        \. (?P<windows_s>windows | msysgit)
        \. (?P<windows_n>[0-9]+)
    )?
    \Z
""", re.VERBOSE)


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


def version():
    m = _version_re.match(run('--version')[0].strip())
    if not m:
        return ()

    v = tuple(map(int, m.group('release').split('.')))
    if len(v) < 4:
        v += (0,) * (4 - len(v))
    if m.group('alpha'):
        v += (m.group('alpha'),)
    if m.group('rc'):
        v += ('rc', int(m.group('rc')))
    if m.group('windows_s'):
        v += (m.group('windows_s'), int(m.group('windows_n')))
    return v


def run(*args, **kwargs):
    return util.exec_((util.which('git'),) + args, **kwargs)
