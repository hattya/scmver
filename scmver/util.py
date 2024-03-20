#
# scmver.util
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import locale
import os
import subprocess
import sys
from typing import List, Mapping, Optional, Sequence, Tuple

from ._typing import Path


__all__ = ['exec_', 'command', 'which']


def exec_(args: Sequence[Path], cwd: Optional[Path] = None, env: Optional[Mapping[str, str]] = None,
          encoding: Optional[str] = None, errors: str = 'strict') -> Tuple[str, str]:
    env = dict(env) if env else {}
    env['LC_MESSAGES'] = 'C'
    for k in ('LC_ALL', 'LANG', 'PATH', 'LD_LIBRARY_PATH', 'SystemRoot'):
        if k in os.environ:
            env[k] = os.environ[k]
    if encoding is None:
        encoding = locale.getpreferredencoding(False)

    proc = subprocess.run(args,
                          capture_output=True,
                          cwd=cwd,
                          env=env)
    return proc.stdout.decode(encoding, errors), proc.stderr.decode(encoding, errors)


def command(name: str, *args: str) -> str:
    if (path := which(name)) is not None:
        return path
    for a in args:
        if (path := which(a)) is not None:
            return path
    raise OSError(f'command not found: {name}')


def which(name: str) -> Optional[str]:
    cands: List[str] = []
    if sys.platform == 'win32':
        cands += (name + ext for ext in os.environ['PATHEXT'].split(os.pathsep))
    cands.append(name)
    for p in os.environ['PATH'].split(os.pathsep):
        for n in cands:
            name = os.path.join(p, n)
            if os.path.isfile(name):
                return name
    return None
