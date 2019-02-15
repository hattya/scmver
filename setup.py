#! /usr/bin/env python
#
# setup.py -- scmver setup script
#

from __future__ import print_function
import os
import subprocess
import sys
import time

from setuptools import setup, Command


def whence(cmd):
    cands = []
    if sys.platform == 'win32':
        cands.extend(cmd + ext for ext in ('.exe', '.bat', '.cmd'))
    cands.append(cmd)
    for p in os.environ['PATH'].split(os.pathsep):
        for n in cands:
            cmd = os.path.join(p, n)
            if os.path.isfile(cmd):
                return cmd


def exec_(argv, env=None):
    proc = subprocess.Popen(argv,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=env,
                            universal_newlines=True)
    out, err = proc.communicate()
    if proc.returncode:
        print('+', *argv, file=sys.stderr)
        for l in err.splitlines():
            print(l, file=sys.stderr)
        return ''
    return out


version = ''

if os.path.isdir('.git'):
    env = {'LANGUAGE': 'C'}
    if 'SystemRoot' in os.environ:
        env['SystemRoot'] = os.environ['SystemRoot']
    out = exec_([whence('git'), 'describe', '--tags', '--dirty=+', '--long', '--always'], env=env)
    v = out.strip().rsplit('-', 2)
    if len(v) == 3:
        if v[1] == '0':
            version = v[0]
        else:
            v[0] = v[0][1:]
            version = '{}.{}'.format(*v)
    else:
        out = exec_([whence('git'), 'rev-list', 'HEAD', '--'], env=env)
        version = '0.0.{}'.format(len(out.splitlines()) if out else '0')
    if v[-1].endswith('+'):
        version += time.strftime('+%Y-%m-%d')

if version:
    with open(os.path.join('scmver', '__version__.py'), 'w') as fp:
        stdout = sys.stdout
        try:
            sys.stdout = fp
            print('#')
            print('# scmver.__version__')
            print('#')
            print('# this file is automatically generated by setup.py')
            print()
            print("version = '{}'".format(version))
        finally:
            sys.stdout = stdout
else:
    version = 'unknown'
    try:
        with open(os.path.join('scmver', '__version__.py')) as fp:
            for l in fp:
                if l.startswith('version = '):
                    version = l.split('=', 1)[1].strip("\n '")
                    break
    except (OSError, IOError):
        pass


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
