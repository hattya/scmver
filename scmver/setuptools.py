#
# scmver.setuptools
#
#   Copyright (c) 2019 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from . import core


__all__ = ['scmver']


def scmver(dist, key, value):
    if not value:
        return
    elif value is True:
        value = {}
    elif callable(value):
        value = value()

    dist.metadata.version = core.get_version(**value)
