#
# scmver
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

__author__ = 'Akinori Hattori <hattya@gmail.com>'
try:
    from .__version__ import version as __version__
except ImportError:
    __version__ = 'unknown'

from .core import *
