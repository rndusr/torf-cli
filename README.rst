torf-cli
========

torf-cli is a command line tool that can create new torrents and magnet URIs,
dump the metainfo of a torrent in a readable and parsable format and edit
existing torrents (e.g. to fix a typo or change the info hash to deal with
cross-seeding issues without hashing the pieces again).

::

    $ torf -h
    torf 1.1 <https://github.com/rndusr/torf-cli>

    Create, display and edit torrents

    USAGE
        torf PATH [OPTIONS] [-o TORRENT]
        torf -i TORRENT
        torf -i TORRENT [OPTIONS] -o NEW TORRENT

    ARGUMENTS
        PATH                   Path to torrent's content
        --in, -i TORRENT       Read metainfo from TORRENT
        --out, -o TORRENT      Write metainfo to TORRENT (default: NAME.torrent)
        --magnet, -m           Create magnet link

        --exclude, -e EXCLUDE  File matching pattern that is used to exclude
                               files in PATH
        --yes, -y              Answer all yes/no prompts with "yes"

        --name, -n NAME        Torrent name (default: basename of PATH)
        --tracker, -t TRACKER  Announce URL
        --webseed, -w WEBSEED  Webseed URL
        --private, -p          Disable DHT and PEX
        --xseed, -x            Randomize info hash
        --date, -d DATE        Creation date as YYYY-MM-DD[ HH:MM[:SS]], 'now'
                               or 'today' (default: 'today')
        --comment, -c COMMENT  Comment that is stored in TORRENT

        --notracker, -T        Remove trackers from TORRENT
        --nowebseed, -W        Remove webseeds from TORRENT
        --noprivate, -P        Make TORRENT public
        --noxseed, -X          De-randomize info hash of TORRENT
        --nodate, -D           Remove date from TORRENT
        --nocomment, -C        Remove comment from TORRENT
        --nocreator, -R        Don't store application/version in TORRENT

        --help,-h              Show this help screen and exit
        --version              Show version number and exit


Examples
--------

Create 'foo.torrent' with two trackers

.. code:: sh

    $ torf path/to/foo -t http://bar.example.org:6881/announce -t http://baz.something.com:6881/announce

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
