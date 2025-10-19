#
# scmver.mercurial
#
#   Copyright (c) 2019-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import os
import re
from typing import cast, Any

from . import core, util
from ._typing import Path


__all__ = ['parse', 'version', 'run']

_TAG = 'mercurial.tag'
# environ
_env = {'HGRCPATH': ''}

_version_re = re.compile(r"""
    \A
    Mercurial \s+
    .*
    version \s+

    (?P<release>
        [0-9]+ (?:\. [0-9]+)+
    )
    (?P<alpha>[a-z]+)?
    (?:
        -? (?P<rc>rc [0-9]*)
    )?
    (?:[+)] | \Z)
""", re.VERBOSE)


def parse(root: Path, name: str | None = '.hg', **kwargs: Any) -> core.SCMInfo | None:
    if name == '.hg':
        env = {'HGENCODING': 'utf-8'}
        out = run('identify', '-ib', cwd=root, env=env, encoding='utf-8')[0].strip().split()
        if len(out) == 2:
            try:
                null = int(out[0].rstrip('+')) == 0
            except ValueError:
                null = False
            dirty = out[0].endswith('+')
            branch = out[1]
            if null:
                return core.SCMInfo(dirty=dirty, branch=branch)

            pat = "'re:{}'".format(''.join(map(r'\x{:02x}'.format, bytes(kwargs[_TAG], 'utf-8')))) if _TAG in kwargs else ''
            tmpl = "{node}\t{latesttag(" + pat + ") % '{tag}\t{changes}\t'}"
            out = run('log', '-r', '.', '-T', tmpl, cwd=root, env=env, encoding='utf-8')[0].split('\t')
            if len(out) >= 3:
                return core.SCMInfo(_tag_of(out[1]), int(out[2]), out[0], dirty, branch)
    elif name == '.hg_archival.txt':
        p = os.path.join(root, name)
        try:
            # NOTE: tags should also be encoded in UTF-8, but they are
            # encoded in the local encoding...
            with open(p, encoding='utf-8') as fp:
                meta: dict[str, str | list[str]] = {'tag': []}
                for l in fp:
                    k, v = (s.strip() for s in l.split(':', 1))
                    if k in ('tag', 'latesttag'):
                        cast(list[str], meta['tag']).append(v)
                    else:
                        meta[k] = v
        except OSError:
            pass
        else:
            if _TAG in kwargs:
                tag_re = re.compile(kwargs[_TAG])
                for tag in meta['tag']:
                    if (tag != 'null'
                        and tag_re.match(tag)):
                        break
                else:
                    raise ValueError('no such tag')
            else:
                tag = meta['tag'][0]
            return core.SCMInfo(_tag_of(tag), int(cast(str, meta.get('changessincelatesttag', 0))), cast(str, meta['node']), False, cast(str, meta['branch']))
    return None


def _tag_of(tag: str) -> str:
    return tag if tag != 'null' else '0.0'


def version() -> tuple[int | str, ...]:
    out = run('version')[0].splitlines()
    m = _version_re.match(out[0] if out else '')
    if not m:
        return ()

    v: tuple[int | str, ...] = tuple(map(int, m.group('release').split('.')))
    if len(v) < 3:
        v += (0,) * (3 - len(v))
    if m.group('alpha'):
        v += (m.group('alpha'),)
    if m.group('rc'):
        rc = m.group('rc')
        v += ('rc', int(rc[2:]) if rc != 'rc' else 0)
    return v


def run(*args: str, **kwargs: Any) -> tuple[str, str]:
    env = _env
    if 'env' in kwargs:
        env |= kwargs['env']
    kwargs['env'] = env
    return util.exec_((util.command('hg'),) + args, **kwargs)
