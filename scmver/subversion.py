#
# scmver.subversion
#
#   Copyright (c) 2019-2022 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import re
from typing import cast, Any, Dict, Mapping, Optional, Tuple, Union
import urllib.parse
import xml.etree.ElementTree as ET

from . import core, util
from ._typing import Path


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
    # number tag
    (?:
        (?:
            -
            (?P<pre_s>
                alpha |
                beta  |
                rc
            )
            (?P<pre_n>[0-9]+)
        ) |
        (?:
            - dev |
            \+
        )
    )?
    (?:
        # sliksvn
        - SlikSvn .*?
    )?
    # version tag
    \s+
    \(
        (?P<tag>.+)
    \)
""", re.VERBOSE)


def parse(root: Path, name: Optional[str] = '.svn', **kwargs: Any) -> Optional[core.SCMInfo]:
    if name == '.svn':
        info = _info(root)
        if not _is_wc_root(root, info):
            return None

        revision = int(info.get('Revision', 0))
        branch = _branch_of(info, **kwargs)

        out = cast(ET.Element, run('status', '--xml', cwd=root)[0])
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
            try:
                out = cast(ET.Element, run('log', '-r', f'{r}:0', '-v', '--xml', '-l', '10', url, cwd=root)[0])
            except SyntaxError:
                break
            for e in out.iterfind('./logentry'):
                r = int(cast(str, e.get('revision')))
                for p in e.iterfind('.//path[@kind="dir"]'):
                    p.text = cast(str, p.text)
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
    return None


def _info(root: Path) -> Dict[str, str]:
    out = cast(str, run('info', cwd=root)[0]).strip().splitlines()
    return dict(cast(Tuple[str, str], (s.strip() for s in l.split(':', 1))) for l in out)


def _is_wc_root(root: Path, info: Mapping[str, str]) -> bool:
    root = os.path.abspath(root)
    if os.path.normcase(root) == os.path.normcase(info.get('Working Copy Root Path', '')):
        return True
    elif info:
        p = os.path.dirname(root)
        return (p == root
                or not os.path.isdir(os.path.join(p, '.svn'))
                or _info(p).get('Repository UUID') != info['Repository UUID'])
    return False


def _distance_of(root: Path, info: Mapping[str, str], rev: Union[int, str]) -> int:
    rev = str(rev)
    i = 0
    out = cast(ET.Element, run('log', '-r', f'{info.get("Revision", "BASE")}:{rev}', '--xml', cwd=root)[0])
    for e in out.iterfind('./logentry'):
        if e.get('revision') != rev:
            i += 1
    return i


def _branch_of(info: Mapping[str, str], **kwargs: str) -> Optional[str]:
    url = info['URL']
    trunk = info['Repository Root'] + _rel(_TRUNK, 'trunk', **kwargs)
    if (url == trunk[:-1]
        or url.startswith(trunk)):
        return 'trunk'
    branches = info['Repository Root'] + _rel(_BRANCHES, 'branches', **kwargs)
    if url.startswith(branches):
        return urllib.parse.unquote(url[len(branches):].split('/', 1)[0])
    return None


def _rel(key: str, default: str, **kwargs: str) -> str:
    return '/' + os.path.normpath(kwargs.get(key, default)).replace(os.sep, '/').strip('/') + '/'


def version() -> Tuple[Union[int, str], ...]:
    out = cast(str, run('--version')[0]).splitlines()
    m = _version_re.match(out[0] if out else '')
    if not m:
        return ()

    v: Tuple[Union[int, str], ...] = tuple(map(int, m.group('release').split('.')))
    if m.group('pre_s'):
        s = m.group('pre_s')
        v += (s[0] if s != 'rc' else s, int(m.group('pre_n')))
    elif m.group('tag') in ('under development', 'dev build'):
        v += ('dev',)
    return v


def run(*args: str, **kwargs: Any) -> Tuple[Union[str, ET.Element], str]:
    xml = '--xml' in args
    if xml:
        kwargs['encoding'] = 'utf-8'
    out, err = util.exec_((cast(str, util.which('svn')), '--non-interactive') + args, **kwargs)
    return ET.fromstring(out.encode('utf-8')) if xml else out, err
