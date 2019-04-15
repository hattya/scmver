#
# scmver._compat
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import sys


__all__ = ['PY2', 'basestring', 'values']


PY2 = sys.version_info[0] == 2
if PY2:
    basestring = basestring

    def values(d):
        return d.itervalues()
else:
    basestring = str

    def values(d):
        return d.values()
