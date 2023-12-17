#
# scmver.cli
#
#   Copyright (c) 2019-2023 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import re
from typing import Any, Callable, Dict, Optional, Sequence

try:
    import click
except ImportError:
    raise SystemExit("Missing dependencies, try 'pip install scmver[cli]'")

from . import __version__, core


__all__ = ['run']

F = Callable[..., Any]


def run(args: Optional[Sequence[str]] = None) -> None:
    cli(args=args, prog_name=__package__)


class _Group(click.Group):

    def get_command(self, ctx: click.Context, name: str) -> Optional[click.Command]:
        m = {n: super(_Group, self).get_command(ctx, n) for n in self.list_commands(ctx) if n.startswith(name)}
        if name in m:
            return m[name]
        elif len(m) > 1:
            ctx.fail(f'command "{name}" is ambiguous: {" ".join(sorted(m))}')
        for cmd in m.values():
            return cmd
        return None


class _Local(click.ParamType):

    name = 'text'
    CO_VARARGS = 0x0004

    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        m: Dict[str, Any] = {}
        try:
            exec(value, {}, m)
        except (NameError, SyntaxError):
            return value

        for v in m.values():
            if callable(v):
                if (v.__code__.co_argcount < 1
                    and not v.__code__.co_flags & self.CO_VARARGS):
                    self.fail(f'"{v}" does not have arguments.', param, ctx)
                return v
        self.fail('Callable object does not found.', param, ctx)


class _Regex(click.ParamType):

    name = 'regex'

    def __init__(self, group: Optional[Sequence[str]] = None) -> None:
        super().__init__()
        self.group = group or []

    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        try:
            value = re.compile(value)
        except re.error as e:
            self.fail(str(e), param, ctx)
        for g in self.group:
            if g not in value.groupindex:
                self.fail(f'Regex does not have the {g} group.', param, ctx)
        return value


def _options(options: Sequence[F]) -> F:
    def _options(func: F) -> F:
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
    click.option('--bzr-tag',
                 metavar='REGEX',
                 help='Regular expression to filter tags.'),
    click.option('--darcs-tag',
                 metavar='REGEX',
                 help='Regular expression to filter tags.'),
    click.option('--fsl-tag',
                 metavar='REGEX',
                 help='Regular expression to filter tags.'),
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


@click.group(cls=_Group)
@click.version_option(version=__version__)
def cli() -> None:
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
def generate(file: str, template: Optional[str], **opts: Any) -> None:
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
def load(spec: str, path: Optional[str]) -> None:
    """Show a value of the specified object.

    SPEC is in the "package.module:some.attribute" format.
    """

    click.echo(core.load_version(spec, path))


@cli.command()
@_options(_next_version_options)
@_options(_stat_options)
def next(**opts: Any) -> None:
    """Calculate a next version from the version."""

    info = _stat('.', **opts)
    if not info:
        return

    click.echo(_next_version(info, **opts))


@cli.command()
@_options(_stat_options)
def stat(**opts: Any) -> None:
    """Show the working directory status."""

    info = _stat('.', **opts)
    if not info:
        return

    if info.tag != '0.0':
        click.echo(f'Tag:      {info.tag}')
    click.echo(f'Distance: {info.distance}')
    if info.revision:
        click.echo(f'Revision: {info.revision}')
    click.echo(f'Dirty:    {info.dirty}')
    if info.branch:
        click.echo(f'Branch:   {info.branch}')


def _next_version(info: core.SCMInfo, **opts: Any) -> Optional[str]:
    kwargs = {k: opts[k]
              for k in ('spec', 'local', 'version')
              if opts[k] is not None}
    return core.next_version(info, **kwargs)


def _stat(path: str, **opts: Any) -> Optional[core.SCMInfo]:
    kwargs = {k: opts[n]
              for k, n in (
                  ('bazaar.tag', 'bzr_tag'),
                  ('darcs.tag', 'darcs_tag'),
                  ('fossil.tag', 'fsl_tag'),
                  ('git.tag', 'git_tag'),
                  ('mercurial.tag', 'hg_tag'),
                  ('subversion.tag', 'svn_tag'),
                  ('subversion.trunk', 'svn_trunk'),
                  ('subversion.branches', 'svn_branches'),
                  ('subversion.tags', 'svn_tags'),
              )
              if opts[n] is not None}
    return core.stat(path, **kwargs)
