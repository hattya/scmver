#
# scmver.cli
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

import click

from . import _compat as five
from . import __version__


__all__ = ['run']


def run(args=None):
    cli(args=args, prog_name=__package__)


class _Group(click.Group):

    def get_command(self, ctx, name):
        m = {n: super(_Group, self).get_command(ctx, n) for n in self.list_commands(ctx) if n.startswith(name)}
        if name in m:
            return m[name]
        elif len(m) > 1:
            ctx.fail('command "{}" is ambiguous: {}'.format(name, ' '.join(sorted(m))))
        for cmd in five.values(m):
            return cmd


@click.command(cls=_Group)
@click.version_option(version=__version__)
def cli():
    """A package version manager based on SCM tags."""
