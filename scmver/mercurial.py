#
# scmver.mercurial
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction,
#   including without limitation the rights to use, copy, modify, merge,
#   publish, distribute, sublicense, and/or sell copies of the Software,
#   and to permit persons to whom the Software is furnished to do so,
#   subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#   ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#   CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#

import os
import re

from . import core, util


__all__ = ['parse', 'run']

_TAG = 'mercurial.tag'
_ENV = {'HGRCPATH': ''}


def parse(root, name='.hg', **kwargs):
    if name == '.hg':
        out = run('id', '-ib', cwd=root)[0].strip().split()
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


def run(*args, **kwargs):
    kwargs['env'] = _ENV
    return util.exec_((util.which('hg'),) + args, **kwargs)
