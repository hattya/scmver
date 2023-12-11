#
# scmver._typing
#
#   Copyright (c) 2022-2023 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
import sys
from typing import TYPE_CHECKING, Tuple, Union


__all__ = ['Path', 'Segment', 'RawSegment']

if (TYPE_CHECKING
    or sys.version_info >= (3, 9)):
    Path = Union[str, os.PathLike[str]]
else:
    Path = Union[str, os.PathLike]

Segment = Tuple[str, int]
RawSegment = Tuple[str, str, str, int]
