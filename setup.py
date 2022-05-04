#! /usr/bin/env python
#
# setup.py -- scmver setup script
#

import os
import sys

from setuptools import setup, Command

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

        self.run_command('egg_info')
        # run unittest discover
        argv = [sys.argv[0], 'discover', '--start-directory', 'tests']
        if self.verbose:
            argv.append('--verbose')
        if self.failfast:
            argv.append('--failfast')
        unittest.main(None, argv=argv)


cmdclass = {
    'test': test,
}

setup(version=scmver.get_version(**{
          'root': os.path.dirname(os.path.abspath(__file__)),
          'spec': 'micro',
          'write_to': os.path.join('scmver', '__version__.py'),
          'fallback': 'scmver:__version__',
      }),
      cmdclass=cmdclass,
      entry_points={
          'console_scripts': [
              'scmver = scmver.cli:run [cli]',
          ],
          'distutils.setup_keywords': [
              'scmver = scmver.setuptools:scmver'
          ],
          'scmver.parse': [
              '.bzr = scmver.bazaar:parse',
              '_darcs = scmver.darcs:parse',
              '.fslckout = scmver.fossil:parse',
              '_FOSSIL_ = scmver.fossil:parse',
              '.git = scmver.git:parse',
              '.hg = scmver.mercurial:parse',
              '.hg_archival.txt = scmver.mercurial:parse',
              '.svn = scmver.subversion:parse',
          ],
          'setuptools.finalize_distribution_options': [
              'scmver = scmver.setuptools:finalize_version',
          ],
      })
