#
# scmver.fossil
#
#   Copyright (c) 2019-2022 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import re
import sys
from typing import cast, Any, Dict, List, Optional, Tuple

from . import core, util
from ._typing import Path


__all__ = ['parse', 'version', 'run']

_TAG = 'fossil.tag'
# environ
_env: Tuple[str, ...] = ('FOSSIL_HOME', 'FOSSIL_USER', 'SQLITE_TMPDIR', 'USER', 'LOGNAME', 'USERNAME', 'TMPDIR')
if sys.platform == 'win32':
    _env += ('LOCALAPPDATA', 'APPDATA', 'HOMEDRIVE', 'HOMEPATH', 'TMP', 'TEMP', 'USERPROFILE')
else:
    _env += ('HOME',)

_timeline_re = re.compile(r"""
    \A
    \d{2}:\d{2}:\d{2}
    \s+
    \[
        (?P<check_in>[0-9a-z]+)
    \]
    \s+
    .+
    \(
        user: \s+ (?P<user> .+?)
        (?:
            \s+
            tags: \s+ (?P<tags> .+)
        )?
    \)
    \Z
""", re.VERBOSE)
_version_re = re.compile(r"""
    \A
    This \s+ is \s+ fossil \s+
    version \s+

    (?:
        (?P<release>
            [0-9]+ (?:\. [0-9]+)+
        )
        \s+
    )?
    \[
        (?P<check_in>[0-9a-z]{10})
    \]
    \s+
    (?P<date>\d{4}-\d{2}-\d{2} \s+ \d{2}:\d{2}:\d{2} \s+ UTC)
    \Z
""", re.VERBOSE)


def parse(root: Path, name: Optional[str] = '.fslckout', **kwargs: Any) -> Optional[core.SCMInfo]:
    if name in ('.fslckout', '_FOSSIL_'):
        info, changes = _status(root)
        if not info:
            return None

        revision = info['checkout'].split()[0]
        dirty = bool(changes)
        branch = _branch_of(root) or _branch_of(root, closed=True)

        # NOTE: "-n 0" does not work with <= 1.36
        distance = 0
        tag_re = re.compile(kwargs[_TAG]) if _TAG in kwargs else None
        for l in run('timeline', 'parents', 'current', '-n', str(0x7fff), '-t', 'ci', '-W', '0', cwd=root)[0].splitlines():
            m = _timeline_re.match(l)
            if not m:
                continue
            elif (m.group('tags')
                  and len(m.group('tags').split(',')) > 1):
                for tag in run('tag', 'list', m.group('check_in'), cwd=root)[0].splitlines():
                    if (tag != branch
                        and not tag.startswith('branch=')
                        and (not tag_re
                             or tag_re.match(tag))):
                        return core.SCMInfo(tag, distance, revision, dirty, branch)
            distance += 1
        return core.SCMInfo(distance=distance,
                            revision=revision,
                            dirty=dirty,
                            branch=branch)
    return None


def _status(root: Path) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    info = {}
    changes: Dict[str, List[str]] = {}
    for l in run('status', cwd=root)[0].splitlines():
        v = l.split(None, 1)
        if v[0].endswith(':'):
            info[v[0].rstrip(':')] = v[1]
        else:
            if v[0] not in changes:
                changes[v[0]] = []
            changes[v[0]].append(v[1])
    return info, changes


def _branch_of(root: Path, closed: bool = False) -> Optional[str]:
    args = ['branch', 'list']
    if closed:
        args += ('-c',)
    for l in run(*args, cwd=root)[0].splitlines():
        v = l.split()
        if (len(v) > 1
            and '*' in v[0]):
            return v[1]
    return None


def version() -> Tuple[int, ...]:
    m = _version_re.match(run('version')[0].strip())
    if (not m
        or not m.group('release')):
        return ()

    return tuple(map(int, m.group('release').split('.')))


def run(*args: str, **kwargs: Any) -> Tuple[str, str]:
    env = {k: os.environ[k] for k in _env if k in os.environ}
    if 'env' in kwargs:
        env.update(kwargs['env'])
    kwargs['env'] = env
    kwargs['encoding'] = 'utf-8'
    return util.exec_((cast(str, util.which('fossil')),) + args, **kwargs)
