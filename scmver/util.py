#
# scmver.util
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import subprocess
import sys


__all__ = ['exec_', 'which']


def exec_(args, cwd=None, env=None):
    env = env.copy() if env else {}
    env['LANGUAGE'] = 'C'
    for k in ('PATH', 'LD_LIBRARY_PATH', 'SystemRoot'):
        if k in os.environ:
            env[k] = os.environ[k]
    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=cwd,
                            env=env,
                            universal_newlines=True)
    return proc.communicate()


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
