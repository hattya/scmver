#
# scmver.util
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import locale
import os
import subprocess
import sys

from . import _compat as five


__all__ = ['exec_', 'which']


def exec_(args, cwd=None, env=None, encoding=None, errors='strict'):
    if five.PY2:
        fs_enc = sys.getfilesystemencoding() or 'ascii'
        args = tuple(a.encode(fs_enc, 'replace') if isinstance(a, five.unicode) else a for a in args)
    env = env.copy() if env else {}
    env['LC_MESSAGES'] = 'C'
    for k in ('LC_ALL', 'LANG', 'PATH', 'LD_LIBRARY_PATH', 'SystemRoot'):
        if k in os.environ:
            env[k] = os.environ[k]
    if encoding is None:
        encoding = locale.getpreferredencoding(False)

    if cwd:
        path = five.getcwd()
        os.chdir(cwd)
    try:
        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        out, err = proc.communicate()
    finally:
        if cwd:
            os.chdir(path)
    return out.decode(encoding, errors), err.decode(encoding, errors)


def which(name):
    cands = []
    if sys.platform == 'win32':
        cands += (name + ext for ext in os.environ['PATHEXT'].split(os.pathsep))
    cands.append(name)
    for p in os.environ['PATH'].split(os.pathsep):
        for n in cands:
            name = os.path.join(p, n)
            if os.path.isfile(name):
                return name
