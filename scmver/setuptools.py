#
# scmver.setuptools
#
#   Copyright (c) 2019-2022 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from typing import Any

import setuptools

from . import core


__all__ = ['finalize_version', 'scmver']


def finalize_version(dist: setuptools.Distribution) -> None:
    scmver = core.load_project()
    if scmver is not None:
        dist.metadata.version = core.get_version(**scmver)


def scmver(dist: setuptools.Distribution, key: str, value: Any) -> None:
    if not value:
        return
    elif value is True:
        value = {}
    elif callable(value):
        value = value()

    dist.metadata.version = core.get_version(**value)
