#
# scmver._typing
#
#   Copyright (c) 2022-2025 Akinori Hattori <hattya@gmail.com>
#
#   SPDX-License-Identifier: MIT
#

import os
from typing import TypeAlias


__all__ = ['Path', 'Segment', 'RawSegment']

Path: TypeAlias = str | os.PathLike[str]

Segment: TypeAlias = tuple[str, int]
RawSegment: TypeAlias = tuple[str, str, str, int]
