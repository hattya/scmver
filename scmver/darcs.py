#
# scmver.darcs
#
#   Copyright (c) 2021 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import re
import sys
from typing import Any, Dict, Optional, Tuple, cast

from . import core, util


__all__ = ['parse', 'version', 'run']

_TAG = 'darcs.tag'
# environ
_env: Tuple[str, ...] = ('DARCS_TESTING_PREFS_DIR', 'DARCS_TMPDIR', 'TMPDIR')
if sys.platform == 'win32':
    _env += ('APPDATA', 'TMP', 'TEMP')
else:
    _env += ('HOME',)

_version_re = re.compile(r"""
    \A
    (?P<release>
        [0-9]+ (?:\. [0-9]+)+
    )
    \s+
    \(
        release
    \)
    \Z
""", re.VERBOSE)


def parse(root: str, name: Optional[str] = '_darcs', **kwargs: Any) -> Optional[core.SCMInfo]:
    if name == '_darcs':
        info = _show_repo(root)
        if not info:
            return None

        dirty = run('whatsnew')[0].strip() != 'No changes!'
        branch = os.path.basename(info['Root'])
        if info['Num Patches'] == '0':
            return core.SCMInfo(dirty=dirty, branch=branch)

        tag_re = re.compile(kwargs[_TAG]) if _TAG in kwargs else None
        for tag in run('show', 'tags')[0].splitlines():
            if (not tag_re
                or tag_re.match(tag)):
                return core.SCMInfo(tag, _distance_of(root, tag), info['Weak Hash'], dirty, branch)
        return core.SCMInfo(distance=int(info['Num Patches']),
                            revision=info['Weak Hash'],
                            dirty=dirty,
                            branch=branch)
    return None


def _show_repo(root: str) -> Dict[str, str]:
    out = run('show', 'repo', cwd=root)[0].replace('\r', '').splitlines()
    return dict(cast(Tuple[str, str], (s.strip() for s in l.split(':', 1))) for l in out)


def _distance_of(root: str, tag: str) -> int:
    return int(run('log', '--from-tag', tag, '--count', cwd=root)[0]) - 1


def version() -> Tuple[int, ...]:
    m = _version_re.match(run('--version')[0].strip())
    if (not m
        or not m.group('release')):
        return ()

    return tuple(map(int, m.group('release').split('.')))


def run(*args: str, **kwargs: Any) -> Tuple[str, str]:
    env = {k: os.environ[k] for k in _env if k in os.environ}
    if 'env' in kwargs:
        env.update(kwargs['env'])
    kwargs['env'] = env
    return util.exec_((cast(str, util.which('darcs')),) + args, **kwargs)
