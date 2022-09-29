#
# scmver._typing
#
#   Copyright (c) 2022 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import sys
from typing import Tuple, Union


__all__ = ['Path', 'Segment', 'RawSegment']

if sys.version_info >= (3, 9):
    Path = Union[str, os.PathLike[str]]
else:
    Path = Union[str, os.PathLike]

Segment = Tuple[str, int]
RawSegment = Tuple[str, str, str, int]
