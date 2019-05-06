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
        self.distribution.fetch_build_eggs(self.distribution.tests_require)
        try:
            import unittest2 as unittest
        except ImportError:
            import unittest

        self.run_command('egg_info')
        # run unittest discover
        argv = [sys.argv[0], 'discover', '--start-directory', 'tests']
        if self.verbose:
            argv.append('--verbose')
        if self.failfast:
            argv.append('--failfast')
        unittest.main(None, argv=argv)


try:
    with open('README.rst') as fp:
        long_description = fp.read()
except (OSError, IOError):
    long_description = ''

packages = ['scmver']
package_data = {}

cmdclass = {
    'test': test,
}

tests_require = ['unittest2; python_version <= "2.7"']

setup(name='scmver',
      version=scmver.get_version(**{
          'root': os.path.dirname(os.path.abspath(__file__)),
          'spec': 'micro',
          'write_to': os.path.join('scmver', '__version__.py'),
          'fallback': 'scmver:__version__',
      }),
      description='A package version manager based on SCM tags',
      long_description=long_description,
      author='Akinori Hattori',
      author_email='hattya@gmail.com',
      url='https://github.com/hattya/scmver',
      license='MIT',
      packages=packages,
      package_data=package_data,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Version Control',
          'Topic :: System :: Software Distribution',
          'Topic :: Utilities',
      ],
      cmdclass=cmdclass,
      tests_require=tests_require,
      extras_require={
          'cli': ['click'],
          'test': tests_require,
      },
      entry_points={
          'console_scripts': [
              'scmver = scmver.cli:run [cli]',
          ],
          'distutils.setup_keywords': [
              'scmver = scmver.setuptools:scmver'
          ],
          'scmver.parse': [
              '.bzr = scmver.bazaar:parse',
              '.fslckout = scmver.fossil:parse',
              '_FOSSIL_ = scmver.fossil:parse',
              '.git = scmver.git:parse',
              '.hg = scmver.mercurial:parse',
              '.hg_archival.txt = scmver.mercurial:parse',
              '.svn = scmver.subversion:parse',
          ],
      })
