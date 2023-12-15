#
# scmver.git
#
#   Copyright (c) 2019-2023 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import os
import re
import sys
from typing import cast, Any, Optional, Tuple, Union

from . import core, util
from ._typing import Path


__all__ = ['parse', 'version', 'run']

_TAG = 'git.tag'
# environ
_env: Tuple[str, ...] = ('GIT_CONFIG_NOSYSTEM', 'GIT_CONFIG_SYSTEM', 'GIT_CONFIG_GLOBAL', 'HOME', 'XDG_CONFIG_HOME')

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


def parse(root: Path, name: Optional[str] = '.git', **kwargs: Any) -> Optional[core.SCMInfo]:
    if name == '.git':
        args = ['describe', '--dirty=+', '--tags', '--abbrev=40', '--long', '--always']
        if _TAG in kwargs:
            args += ('--match', kwargs[_TAG])
        out = run(*args, cwd=root)[0].strip().rsplit('-', 2)

        branch: Optional[str] = run('rev-parse', '--abbrev-ref', 'HEAD', cwd=root)[0].strip()
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
    return None


def version() -> Tuple[Union[int, str], ...]:
    m = _version_re.match(run('--version')[0].strip())
    if not m:
        return ()

    v: Tuple[Union[int, str], ...] = tuple(map(int, m.group('release').split('.')))
    if len(v) < 4:
        v += (0,) * (4 - len(v))
    if m.group('alpha'):
        v += (m.group('alpha'),)
    if m.group('rc'):
        v += ('rc', int(m.group('rc')))
    if m.group('windows_s'):
        v += (m.group('windows_s'), int(m.group('windows_n')))
    return v


def run(*args: str, **kwargs: Any) -> Tuple[str, str]:
    env = {k: os.environ[k] for k in _env if k in os.environ}
    if 'env' in kwargs:
        env.update(kwargs['env'])
    kwargs['env'] = env
    if sys.platform == 'win32':
        kwargs['encoding'] = 'utf-8'
    return util.exec_((cast(str, util.which('git')), '-c', 'core.quotepath=false') + args, **kwargs)
