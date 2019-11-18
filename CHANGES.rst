scmver Changelog
================

Version 1.0
-----------

* Drop Python 3.4 support.


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
