#! /usr/bin/env python
#
# setup.py -- scmver setup script
#

import os
import sys

from setuptools import setup

# ensure to load the current version
sys.path.insert(0, os.path.dirname(__file__))

import scmver

setup(
    version=scmver.get_version(**scmver.load_project()),
)
