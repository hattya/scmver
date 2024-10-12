#
# scmver._typing
#
#   Copyright (c) 2022-2024 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
from typing import Union


__all__ = ['Path', 'Segment', 'RawSegment']

Path = Union[str, os.PathLike[str]]

Segment = tuple[str, int]
RawSegment = tuple[str, str, str, int]
