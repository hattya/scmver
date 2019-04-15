#
# scmver.cli
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import re

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


class _Local(click.ParamType):

    name = 'text'
    CO_VARARGS = 0x0004

    def convert(self, value, param, ctx):
        try:
            m = {}
            exec(value, {}, m)
        except (NameError, SyntaxError):
            return value
        else:
            for v in five.values(m):
                if callable(v):
                    if (v.__code__.co_argcount < 1
                        and not v.__code__.co_flags & self.CO_VARARGS):
                        self.fail('"{}" does not have arguments.'.format(v), param, ctx)
                    return v
            else:
                self.fail('Callable object does not found.', param, ctx)


class _Regex(click.ParamType):

    name = 'regex'

    def __init__(self, group=None):
        super(_Regex, self).__init__()
        self.group = group or []

    def convert(self, value, param, ctx):
        try:
            value = re.compile(value)
        except re.error as e:
            self.fail(str(e), param, ctx)
        for g in self.group:
            if g not in value.groupindex:
                self.fail('Regex does not have the {} group.'.format(g), param, ctx)
        return value


def _options(options):
    def _options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _options


_next_version_options = (
    click.option('-s', '--spec',
                 help='Construct public version identifiers.'),
    click.option('-l', '--local',
                 type=_Local(),
                 help='Construct local version identifiers.'),
    click.option('-v', '--version',
                 type=_Regex(group=['version']),
                 help='Regular expression to extract the version.'),
)
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
@click.argument('file',
                type=click.Path(dir_okay=False, writable=True),
                required=True,
                nargs=1)
@_options(_next_version_options)
@click.option('-t', '--template',
              help='File template.')
@_options(_stat_options)
def generate(file, template, **opts):
    """Generate a file with the version."""

    info = _stat('.', **opts)
    if not info:
        return
    version = _next_version(info, **opts)

    kwargs = {}
    if template is not None:
        kwargs['template'] = template.replace('\\r\\n', '\n').replace('\\n', '\n')
    core.generate(file, version, info, **kwargs)


@cli.command()
@click.argument('spec')
@click.option('-p', '--path',
              help='Search path for modules.')
def load(spec, path):
    """Show a value of the specified object.

    SPEC is in the "package.module:some.attribute" format.
    """

    click.echo(core.load_version(spec, path))


@cli.command()
@_options(_next_version_options)
@_options(_stat_options)
def next(**opts):
    """Calculate a next version from the version."""

    info = _stat('.', **opts)
    if not info:
        return

    click.echo(_next_version(info, **opts))


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


def _next_version(info, **opts):
    kwargs = {k: opts[k]
              for k in ('spec', 'local', 'version')
              if opts[k] is not None}
    return core.next_version(info, **kwargs)


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
