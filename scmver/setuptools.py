#
# scmver.setuptools
#
#   Copyright (c) 2019-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

from __future__ import annotations
import configparser
from typing import Any, Optional

import setuptools

from . import core
from ._typing import Path


__all__ = ['finalize_version', 'scmver', 'load_cfg']


def finalize_version(dist: setuptools.Distribution) -> None:
    if (scmver := core.load_project()) is not None:
        dist.metadata.version = core.get_version(**scmver)


def scmver(dist: setuptools.Distribution, key: str, value: Any) -> None:
    if not value:
        return
    elif value is True:
        value = {}
    elif callable(value):
        value = value()

    dist.metadata.version = core.get_version(**value)


def load_cfg(path: Path = 'setup.cfg') -> Optional[dict[str, Any]]:
    scmver: dict[str, Any] = {}
    try:
        cp = configparser.ConfigParser()
        if not cp.read(path):
            return None

        for k, v in cp.items('scmver'):
            if k == 'fallback':
                scmver[k] = [s for v in (v.splitlines() if '\n' in v else v.split(','))
                             if (s := v.strip())]
            else:
                scmver[k] = v
    except configparser.Error:
        pass
    return scmver
