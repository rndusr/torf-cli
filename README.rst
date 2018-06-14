torf-cli
========

torf-cli is a command line tool that can create torrents and magnet URIs, dump
the metainfo of a torrent, and edit existing torrents (e.g. to fix a typo
without having to hash all the pieces again).

The output is pleasant to read for humans and easy to parse with common CLI
tools if stdout is not a TTY.

An optional configuration file specifies custom default options and profiles
that give a name to a set of options.

Documentation should be available as a man page after the installation, or you
can `read it here
<https://github.com/rndusr/torf-cli/blob/master/doc/torf.1.asciidoc>`_.

Examples
--------

.. code:: sh

    $ torf ./doc -t http://bar:123/announce -t http://baz:321/announce --private
             Name  doc
             Size  15.77 KiB
    Creation Date  2018-06-13 00:00:00
          Private  yes
         Trackers  http://bar:123/announce
                   http://baz:321/announce
       Piece Size  16 KiB
      Piece Count  1
       File Count  2
            Files  doc
                   ├─man
                   │ └─man1
                   │   └─torf.1
                   └─manpage.md
             Path  doc
         Progress  100.00 %  |  Time: 0:00:00  |  15.44 MB/s
        Info Hash  f574f59b61d9b108b21cd5e4cc9036bcff55c11a
     Torrent File  doc.torrent

    $ torf -i doc.torrent
             Name  doc
        Info Hash  f574f59b61d9b108b21cd5e4cc9036bcff55c11a
             Size  15.77 KiB
    Creation Date  2018-06-13 00:00:00
          Private  yes
         Trackers  http://bar:123/announce
                   http://baz:321/announce
       Piece Size  16 KiB
      Piece Count  1
       File Count  2
            Files  doc
                   ├─man
                   │ └─man1
                   │   └─torf.1
                   └─manpage.md

    $ torf -i doc.torrent --comment 'Forgot to add this comment.' -o doc.revised.torrent
             Name  doc
        Info Hash  f574f59b61d9b108b21cd5e4cc9036bcff55c11a
             Size  15.77 KiB
          Comment  Forgot to add this comment.
    Creation Date  2018-06-13 00:00:00
          Private  yes
         Trackers  http://bar:123/announce
                   http://baz:321/announce
       Piece Size  16 KiB
      Piece Count  1
       File Count  2
            Files  doc
                   ├─man
                   │ └─man1
                   │   └─torf.1
                   └─manpage.md
     Torrent File  doc.revised.torrent

    $ torf -i doc.revised.torrent | grep '^Files'
    Files   doc/man/man1/torf.1     doc/manpage.md

Installation
------------

The `latest release <https://pypi.org/project/torf-cli>`_ can be installed from PyPI.

.. code:: sh

   $ pip3 install torf-cli         # Installs torf system-wide (/usr/local/)
   $ pip3 install --user torf-cli  # Installs torf in your home (~/.local/)

The `latest development version <https://github.com/rndusr/torf-cli>`_ is
available on GitHub in the `master` branch.

.. code:: sh

   $ pip3 install [--user] git+https://github.com/rndusr/torf-cli.git

Contributing
------------

Bug reports and feature requests are welcome in the `issue tracker
<https://github.com/rndusr/torf-cli/issues>`_.

License
-------

torf-cli is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the `GNU General Public License
<https://www.gnu.org/licenses/gpl-3.0.txt>`_ for more details.
