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
<https://github.com/rndusr/torf-cli/blob/master/doc/manpage.md>`_.

Example
-------

.. code:: sh

    $ torf ./foo -t http://bar:123/announce -t http://baz:321/announce

Read 'foo.torrent' and display its metainfo

.. code:: sh

    $ torf -i foo.torrent

Read 'foo.torrent', edit its comment, remove the date and write the result to
'bar.torrent'

.. code:: sh

    $ torf -i foo.torrent -c 'This torrent has changed' -D -o bar.torrent

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
