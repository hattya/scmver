#
# scmver.git
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

from . import core, util


__all__ = ['parse', 'run']

_TAG = 'git.tag'


def parse(root, name='.git', **kwargs):
    if name == '.git':
        args = ['describe', '--dirty=+', '--tags', '--long', '--always']
        if _TAG in kwargs:
            args += ('--match', kwargs[_TAG])
        out = run(*args, cwd=root)[0].strip().rsplit('-', 2)

        branch = run('rev-parse', '--abbrev-ref', 'HEAD', cwd=root)[0].strip()
        if len(out) == 3:
            return core.SCMInfo(out[0], int(out[1]), out[2][1:].rstrip('+'), out[2].endswith('+'), branch)
        elif out[0]:
            return core.SCMInfo(distance=len(run('rev-list', 'HEAD', '--', cwd=root)[0].splitlines()),
                                revision=out[0].rstrip('+'),
                                dirty=out[0].endswith('+'),
                                branch=branch)
        elif branch:
            return core.SCMInfo(branch=branch)


def run(*args, **kwargs):
    return util.exec_((util.which('git'),) + args, **kwargs)
