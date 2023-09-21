scmver
======

scmver is a package version manager based on SCM tags.

It can be used to pass the version to the ``setup`` function in a ``setup.py``,
or to generate a file which contains the version.

.. image:: https://img.shields.io/pypi/v/scmver.svg
   :target: https://pypi.org/project/scmver

.. image:: https://github.com/hattya/scmver/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/hattya/scmver/actions/workflows/ci.yml

.. image:: https://ci.appveyor.com/api/projects/status/l9flwehcgr5pxi33?svg=true
   :target: https://ci.appveyor.com/project/hattya/scmver

.. image:: https://codecov.io/gh/hattya/scmver/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/hattya/scmver


Installation
------------

.. code:: console

   $ pip install scmver


Requiements
-----------

- Python 3.8+
- setuptools


Usage
-----

pyproject.toml
--------------

.. code:: toml

   [build-system]
   requires = [
       "setuptools >= 42",
       "scmver[toml] >= 1.5",
   ]
   build-backend = "setuptools.build_meta"

   [tool.scmver]

See Configuration_ for key/value pairs.


setuptools
~~~~~~~~~~

.. code:: python

   from setuptools import setup

   setup(setup_requires=['scmver'],
         scmver=True)

``scmver`` is either following values:

``True``
  It is same as an empty ``dict``.

``callable object``
  It should return a ``dict``.

``dict``
  See Configuration_ for details.


distutils
~~~~~~~~~

.. code:: python

   from distutils.core import setup

   import scmver

   setup(version=scmver.get_version())

See Configuration_ for the ``scmver.get_version`` arguments.


Configuration
-------------

root
  A path of the working directory.

  Default: ``'.'``

spec
  A version specifier to construct the public version indentifiers. It will be
  incremented by the number of commits from the latest tag.

  ``major``
    It will increment the major version.

  ``minor``
    It will increment the minor version.

  ``micro`` or ``patch``
    It will increment the micro (patch) version.

  ``post``
    It will increment the post-release segment.

  ``major.dev``
    It will increment the development release segment after incrementing the
    major version by 1.

  ``minor.dev``
    It will increment the development release segment after incrementing the
    minor version by 1.

  ``micro.dev`` or ``patch.dev``
    It will increment the development release segment after incrementing the
    micro (patch) version by 1.

  Default: ``'post'``

local
  A ``string`` or ``callable object`` to construct the local version
  identifiers.

  ``string``
    A format string.

    Available keywords:

    - ``{distance}``
    - ``{revision}``
    - ``{branch}``
    - ``{utc}``      - Return value of ``datetime.datetime.utcnow()``
    - ``{local}``    - Return value of ``datetime.datetime.now()``

  ``callable object``
    It will be called with ``scmver.core.SCMInfo``.

  Default: ``'{local:%Y-%m-%d}'``

version
  A regular expression object to extract the version from SCM tags. It should
  contain the version group.

write_to
  A path to a file which will be generated using ``template``.

template
  A format string which is used by ``write_to``.

  Available keywords:

  - ``{version}``
  - ``{revision}``
  - ``{branch}``

fallback
  It will be used when there is outside of a working copy.

  ``string``
    It is in the ``'package.module:some.attribute'`` format
    (ex: ``'scmver:version'``).

  ``list``
    It consists of a ``string`` which is described above, and a path to import
    the module.

  ``callable object``
    It should return the version.

bazaar.tag
  A regular expression pattern to filter tags.

darcs.tag
  A regular expression pattern to filter tags.

fossil.tag
  A regular expression pattern to filter tags.

git.tag
  It will be passed to ``git describe`` as ``--match``.

mercurial.tag
  A regular expression pattern to filter tags.

subversion.tag
  A regular expression pattern to filter tags.

subversion.trunk
  A relative repository path of the trunk directory.

  Default: ``'trunk'``

subversion.branches
  A relative repository path of the directory where branches are located.

  Default: ``'branches'``

subversion.tags
  A relative repository path of the directory where tags are located.

  Default: ``'tags'``


License
-------

scmver is distrutbuted under the terms of the MIT License.
