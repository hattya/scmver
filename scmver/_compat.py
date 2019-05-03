#
# scmver._compat
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import sys


__all__ = ['PY2', 'basestring', 'getcwd', 'unicode', 'urlunquote', 'values']


PY2 = sys.version_info[0] == 2
if PY2:
    from os import getcwdu as getcwd
    import urllib

    basestring = basestring
    unicode = unicode

    def urlunquote(s, encoding='utf-8', errors='replace'):
        return urllib.unquote(s).encode('raw_unicode_escape').decode(encoding, errors)

    def values(d):
        return d.itervalues()
else:
    from os import getcwd
    from urllib.parse import unquote as urlunquote

    basestring = str
    unicode = str

    def values(d):
        return d.values()
