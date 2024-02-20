#! /usr/bin/env python
#
# setup.py -- scmver setup script
#

import os
import sys

from setuptools import setup, Command

# ensure to load the current version
sys.path.insert(0, os.path.dirname(__file__))

import scmver


class test(Command):

    description = 'run unit tests'
    user_options = [('failfast', 'f', 'stop on first fail or error')]

    boolean_options = ['failfast']

    def initialize_options(self):
        self.failfast = False

    def finalize_options(self):
        pass

    def run(self):
        import unittest

        # run unittest discover
        argv = [sys.argv[0], 'discover', '--start-directory', 'tests']
        if self.verbose:
            argv.append('--verbose')
        if self.failfast:
            argv.append('--failfast')
        unittest.main(None, argv=argv)


setup(
    version=scmver.get_version(**scmver.load_project()),
    cmdclass={
        'test': test,
    },
)
