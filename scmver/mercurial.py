#
# scmver.mercurial
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import re

from . import core, util


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


def parse(root, name='.hg', **kwargs):
    if name == '.hg':
        out = run('identify', '-ib', cwd=root)[0].strip().split()
        if len(out) == 2:
            try:
                null = int(out[0][:-1]) == 0
            except ValueError:
                null = False
            dirty = out[0].endswith('+')
            branch = out[1]
            if null:
                return core.SCMInfo(dirty=dirty, branch=branch)

            pat = "'re:{}'".format(kwargs[_TAG]) if _TAG in kwargs else ''
            args = ['log', '-r', '.', '-T', "{node}\t{latesttag(" + pat + ") % '{tag}\t{changes}\t'}"]
            out = run(*args, cwd=root)[0].split('\t')
            if len(out) >= 3:
                return core.SCMInfo(_tag_of(out[1]), int(out[2]), out[0], dirty, branch)
    elif name == '.hg_archival.txt':
        p = os.path.join(root, name)
        try:
            with open(p) as fp:
                meta = {'latesttag': []}
                for l in fp:
                    k, v = (s.strip() for s in l.split(':', 1))
                    if k == 'latesttag':
                        meta[k].append(v)
                    else:
                        meta[k] = v
        except (OSError, IOError):
            pass
        else:
            if _TAG in kwargs:
                tag_re = re.compile(kwargs[_TAG])
                for tag in meta['latesttag']:
                    if (tag != 'null'
                        and tag_re.match(tag)):
                        break
                else:
                    raise ValueError('no such tag')
            else:
                tag = meta['latesttag'][0]
            return core.SCMInfo(_tag_of(tag), int(meta.get('changessincelatesttag', meta['latesttagdistance'])), meta['node'], False, meta['branch'])


def _tag_of(tag):
    return tag if tag != 'null' else '0.0'


def version():
    out = run('version')[0].splitlines()
    m = _version_re.match(out[0] if out else '')
    if not m:
        return ()

    v = tuple(map(int, m.group('release').split('.')))
    if len(v) < 3:
        v += (0,) * (3 - len(v))
    if m.group('alpha'):
        v += (m.group('alpha'),)
    if m.group('rc'):
        rc = m.group('rc')
        v += ('rc', int(rc[2:]) if rc != 'rc' else 0)
    return v


def run(*args, **kwargs):
    kwargs['env'] = _env
    return util.exec_((util.which('hg'),) + args, **kwargs)
