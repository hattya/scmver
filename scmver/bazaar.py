#
# scmver.bazaar
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import re
from typing import cast, Any, Optional, Union

from . import core, util
from ._typing import Path


__all__ = ['parse', 'version', 'run']

_TAG = 'bazaar.tag'

_version_re = re.compile(r"""
    \A
    (?:Breezy \s+ \(brz\) | Bazaar \s+ \(bzr\) | bzr \s+ \(bazaar-ng\)) \s+
    # version number
    (?P<release>
        [0-9]+ (?:\. [0-9]+)+
    )
    # release level
    (?:
        (?:
            (?P<pre_s>
                a  |
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


def parse(root: Path, name: Optional[str] = '.bzr', **kwargs: Any) -> Optional[core.SCMInfo]:
    if name == '.bzr':
        info = _version_info(root)
        if not info:
            return None

        dirty = info['clean'] == 'False'

        tag_re = re.compile(kwargs[_TAG]) if _TAG in kwargs else None
        out = [l.split() for l in run('tags', cwd=root, env={'PYTHONIOENCODING': 'utf-8'}, encoding='utf-8')[0].splitlines()]
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
    return None


def _version_info(root: Path) -> dict[str, str]:
    out = run('version-info', '--check-clean', cwd=root, encoding='utf-8')[0].splitlines()
    return dict(cast(tuple[str, str], (s.strip() for s in l.split(':', 1))) for l in out)


def _distance_of(root: Path, rev: Optional[Union[int, str]] = None) -> int:
    if rev is None:
        rev = 1
        off = 0
    else:
        off = 1
    return len(run('log', '-r', f'{rev}..', '-n', '0', '--line', cwd=root)[0].splitlines()) - off


def version() -> tuple[Union[int, str], ...]:
    out = run('version')[0].splitlines()
    m = _version_re.match(out[0] if out else '')
    if not m:
        return ()

    v: tuple[Union[int, str], ...] = tuple(map(int, m.group('release').split('.')))
    if len(v) < 3:
        v += (0,) * (3 - len(v))
    if m.group('pre_s'):
        s = m.group('pre_s')
        v += ('b' if s == 'beta' else s, int(m.group('pre_n')))
    elif m.group('dev_s'):
        n = m.group('dev_n')
        v += (m.group('dev_s'), int(n) if n else 0)
    return v


def run(*args: str, **kwargs: Any) -> tuple[str, str]:
    return util.exec_((util.command('brz', 'bzr'),) + args, **kwargs)
