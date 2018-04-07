torf-cli
========

torf-cli is a command line tool that can create new torrents and magnet URIs,
dump the metainfo of a torrent in a readable and parsable format and edit
existing torrents (e.g. to fix a typo or change the info hash to deal with
cross-seeding issues without hashing the pieces again).

::

    $ torf -h
    torf 1.1

    Create, display and edit torrents

    USAGE
        torf PATH [OPTIONS] [-o TORRENT]
        torf -i TORRENT
        torf -i TORRENT [OPTIONS] -o NEW TORRENT

    ARGUMENTS
        --help,-h              Show this help screen and exit
        --version              Show version information and exit

        PATH                   Path to torrent's content
        --exclude, -e EXCLUDE  Files from PATH to exclude (see below)
                               (may be given multiple times)
        --in, -i FILE          Read metainfo from torrent FILE
        --out, -o FILE         Write metainfo to torrent FILE
                               (defaults to NAME.torrent when creating new torrent)
        --yes, -y              Overwrite FILE without asking
        --magnet, -m           Create magnet link

        --name, -n NAME        Torrent name (defaults to basename of PATH)
        --tracker, -t TRACKER  Announce URL (may be given multiple times)
        --webseed, -w WEBSEED  Webseed URL (BEP19) (may be given multiple times)
        --private, -p          Only use tracker(s) for peer discovery (no DHT/PEX)
        --xseed, -x            Randomize info hash to help with cross-seeding
                               (internally, this adds a random integer to the
                               'info' section of the torrent)
        --date, -d DATE        Creation date as YYYY-MM-DD[ HH:MM[:SS]], 'now' for
                               current local time or 'today' for current local time
                               at midnight
                               (defaults to 'today' when creating new torrent)
        --comment, -c COMMENT  Comment that is stored in the torrent file

        --notracker, -T        Remove any trackers from existing torrent
        --nowebseed, -W        Remove any webseeds from existing torrent
        --noprivate, -P        Make existing torrent public
        --noxseed, -X          De-randomize info hash of existing torrent
        --nodate, -D           Remove date from existing torrent
        --nocomment, -C        Remove comment from existing torrent
        --nocreator, -R        Don't store the name and version of this application
                               in the torrent

        NOTE: With the exception of --nocreator, options starting with '--no' are
              only effective when editing a torrent (i.e. both --in and --out are
              specified).

    EXCLUDING FILES
        The --exclude argument takes a single pattern that is matched against file
        names in PATH.  Any matching files are not included in the torrent.  This
        argument is ignored if PATH is a single file.  Patterns use these special
        characters:
            *      matches everything
            ?      matches any single character
            [SEQ]  matches any character in SEQ
            [!SEQ] matches any character not in SEQ

    PIPING OUTPUT
        If the output is piped, the output is changed to be easier to parse with
        common scripting tools:
            - Leading spaces are removed.
              Example: torf ... | grep '^Name'  # Show only name
            - The delimiter between label and value as well as between multiple
              values (e.g. trackers) is a tab character (	).
              Example: torf ... | cut -f 2-   # Remove labels
            - Numbers are not scaled (e.g. "1024" instead of "1 KiB")

    Homepage: https://github.com/rndusr/torf-cli

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
