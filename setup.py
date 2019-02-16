#! /usr/bin/env python
#
# setup.py -- scmver setup script
#

import os
import sys

from setuptools import setup, Command

import scmver
import scmver.git


root = os.path.dirname(os.path.abspath(__file__))
si = scmver.git.parse(root)
if si:
    version = scmver.next_version(si, spec='micro')
    scmver.generate(os.path.join(root, 'scmver', '__version__.py'), version)
else:
    try:
        version = scmver.load_version('scmver:__version__')
    except ImportError:
        version = None


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

setup(name='scmver',
      version=version,
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
      zip_safe=False,
      entry_points={
          'scmver.parse': [
              '.git = scmver.git:parse',
              '.hg = scmver.mercurial:parse',
              '.hg_archival.txt = scmver.mercurial:parse',
          ],
      })