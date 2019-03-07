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
from . import __version__, core


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


def _options(options):
    def _options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _options


_stat_options = (
    click.option('--git-tag',
                 metavar='GLOB',
                 help='Glob pattern to filter tags.'),
    click.option('--hg-tag',
                 metavar='REGEX',
                 help='Regular expression to filter tags.'),
    click.option('--svn-tag',
                 metavar='REGEX',
                 help='Regular expression to filter tags.'),
    click.option('--svn-trunk',
                 metavar='PATH',
                 help='Relative repository path of the trunk directory.'),
    click.option('--svn-branches',
                 metavar='PATH',
                 help='Relative repository path of the branches directory.'),
    click.option('--svn-tags',
                 metavar='PATH',
                 help='Relative repository path of the tags directory.'),
)


@click.command(cls=_Group)
@click.version_option(version=__version__)
def cli():
    """A package version manager based on SCM tags."""


@cli.command()
@_options(_stat_options)
def stat(**opts):
    """Show the working directory status."""

    info = _stat('.', **opts)
    if not info:
        return

    if info.tag != '0.0':
        click.echo('Tag:      {.tag}'.format(info))
    click.echo('Distance: {.distance}'.format(info))
    if info.revision:
        click.echo('Revision: {.revision}'.format(info))
    click.echo('Dirty:    {.dirty}'.format(info))
    if info.branch:
        click.echo('Branch:   {.branch}'.format(info))


def _stat(path, **opts):
    kwargs = {k: opts[n]
              for k, n in (
                  ('git.tag', 'git_tag'),
                  ('mercurial.tag', 'hg_tag'),
                  ('subversion.tag', 'svn_tag'),
                  ('subversion.trunk', 'svn_trunk'),
                  ('subversion.branches', 'svn_branches'),
                  ('subversion.tags', 'svn_tags'),
              )
              if opts[n] is not None}
    return core.stat(path, **kwargs)
