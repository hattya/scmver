scmver Changelog
================

Version 1.9
-----------

* Support Python 3.14.


Version 1.8
-----------

Release date: 2024-10-12

* Improve error handling when a command is not found.
* Improve support for dotted options in pyproject.toml.
* Load setup.cfg or pyproject.toml in scmver script.
* Drop Python 3.8 support.
* Support Python 3.13.


Version 1.7
-----------

Release date: 2024-02-11

* Improve type annotations.
* Add support for ``tomllib``.
* Add ``root`` to ``sys.path`` when ``fallback`` is a string.
* Generate unspecified values as empty strings.


Version 1.6
-----------

Release date: 2023-10-14

* Drop Python 3.7 support.
* Support Python 3.12.


Version 1.5
-----------

Release date: 2022-11-07

* Add support for pyproject.toml.
* Add support for ``os.PathLike``.
* Support Python 3.11.


Version 1.4
-----------

Release date: 2022-04-27

* Add support for Darcs
* Drop Python 3.6 support.
* Pass necessary environment variables for Git


Version 1.3
-----------

Release date: 2021-11-11

* Fix branch detection with Fossil 2.17.
* Support Python 3.10.


Version 1.2
-----------

Release date: 2021-08-24

* Fix tag detection with Fossil 2.16.
* Drop Python 2.7 support.
* Add type annotations.


Version 1.1
-----------

Release date: 2020-11-04

* Add support for Breezy.
* Drop Python 3.5 support.
* Support Python 3.9.


Version 1.0
-----------

Release date: 2019-11-25

* Drop Python 3.4 support.
* Support Python 3.8.


Version 0.4
-----------

Release date: 2019-05-31

* Add functions to retrieve versions of VCSes.

  * ``bazaar.version``
  * ``git.version``
  * ``mercurial.version``
  * ``subversion.version``

* Add ``--bzr-tag`` option to scmver script.
* Add support for Unicode branches and tags.
* Add support for Fossil.
* Improve support for ``.hg_archival.txt`` of Mercurial.
* Make tag detection of Subversion more robust.


Version 0.3
-----------

Release date: 2019-04-01

* Add support for Bazaar.
* Improve branch detection of Git.
* Improve change detection of Git.
* Fix root detection of Subversion.


Version 0.2
-----------

Release date: 2019-03-21

* Add support for Subversion.
* Do not abbreviate revisions of Git.
* Add scmver script.


Version 0.1
-----------

Release date: 2019-02-28

* Initial release.
