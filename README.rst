torf-cli
========

torf-cli is a command line tool that can create, read and edit torrent files and
magnet URIs and verify that a file system path contains a torrent's data.

The output is pleasant to read for humans or easy to parse with common CLI
tools.

An optional configuration file specifies custom default options and profiles
that combine commonly used options.

Documentation is available as a man page, or you can `read it here
<https://rndusr.github.io/torf-cli/torf.1.html>`_.

The only dependencies are `torf <https://pypi.org/project/torf/>`_ and `pyxdg
<https://pypi.org/project/pyxdg/>`_.


Examples
--------

Create private torrent with two trackers and a specific creation date:

.. code:: sh

    $ torf ./docs -t http://bar:123/announce -t http://baz:321/announce \
                  --private --date '2020-03-31 21:23:42'
           Name  docs
           Size  74.43 KiB
        Created  2020-03-31 21:23:42
     Created By  torf 3.1.0
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  5
     File Count  3
          Files  docs
                 ├─torf.1 [14.53 KiB]
                 ├─torf.1.asciidoc [10.56 KiB]
                 └─torf.1.html [49.34 KiB]
       Progress  100.00 % | 0:00:00 total | 72.69 MiB/s
      Info Hash  0a9dfcf07feb2a82da11b509e8929266d8510a02
         Magnet  magnet:?xt=urn:btih:0a9dfcf07feb2a82da11b509e8929266d8510a02&dn=docs&xl=76217&tr=http%3A%2F%2Fbar%3A123%2Fannounce&tr=http%3A%2F%2Fbaz%3A321%2Fannounce
        Torrent  docs.torrent

Display information about an existing torrent:

.. code:: sh

    $ torf -i docs.torrent
           Name  docs
      Info Hash  0a9dfcf07feb2a82da11b509e8929266d8510a02
           Size  74.43 KiB
        Created  2020-03-31 21:23:42
     Created By  torf 3.1.0
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  5
     File Count  3
          Files  docs
                 ├─torf.1 [14.53 KiB]
                 ├─torf.1.asciidoc [10.56 KiB]
                 └─torf.1.html [49.34 KiB]
         Magnet  magnet:?xt=urn:btih:0a9dfcf07feb2a82da11b509e8929266d8510a02&dn=docs&xl=76217&tr=http%3A%2F%2Fbar%3A123%2Fannounce&tr=http%3A%2F%2Fbaz%3A321%2Fannounce

Quickly add a comment to an existing torrent:

.. code:: sh

    $ torf -i docs.torrent --comment 'Forgot to add this comment.' -o docs.revised.torrent
           Name  docs
      Info Hash  0a9dfcf07feb2a82da11b509e8929266d8510a02
           Size  74.43 KiB
        Comment  Forgot to add this comment.
        Created  2020-03-31 21:23:42
     Created By  torf 3.1.0
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  5
     File Count  3
          Files  docs
                 ├─torf.1 [14.53 KiB]
                 ├─torf.1.asciidoc [10.56 KiB]
                 └─torf.1.html [49.34 KiB]
         Magnet  magnet:?xt=urn:btih:0a9dfcf07feb2a82da11b509e8929266d8510a02&dn=docs&xl=76217&tr=http%3A%2F%2Fbar%3A123%2Fannounce&tr=http%3A%2F%2Fbaz%3A321%2Fannounce
        Torrent  docs.revised.torrent

Verify the files in ``docs``:

.. code:: sh

    $ <edit torf.1.html>
    $ torf -i docs.revised.torrent docs
           Name  docs
      Info Hash  0a9dfcf07feb2a82da11b509e8929266d8510a02
           Size  74.43 KiB
        Comment  Forgot to add this comment.
        Created  2020-03-31 21:23:42
     Created By  torf 3.1.0
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  5
     File Count  3
          Files  docs
                 ├─torf.1 [14.53 KiB]
                 ├─torf.1.asciidoc [10.56 KiB]
                 └─torf.1.html [49.34 KiB]
           Path  docs
      Info Hash  0a9dfcf07feb2a82da11b509e8929266d8510a02
          Error  docs/torf.1.html: Too big: 50523 instead of 50522 bytes
          Error  Corruption in piece 2, at least one of these files is corrupt:
                   docs/torf.1.asciidoc
                   docs/torf.1.html
       Progress  100.00 % | 0:00:00 total | 72.69 MiB/s
    torf: docs does not satisfy docs.revised.torrent

Get a list of files via grep and cut:

.. code:: sh

    $ torf -i docs.revised.torrent | grep '^Files' | cut -f2-
    docs/torf.1     docs/torf.1.asciidoc    docs/torf.1.html

Get a list of files via `jq <https://stedolan.github.io/jq/>`_:

.. code:: sh

    $ torf -i docs.revised.torrent --json | jq .Files
    [
      "docs/torf.1",
      "docs/torf.1.asciidoc",
      "docs/torf.1.html"
    ]

Get metainfo as JSON:

.. code:: sh

    $ torf -i docs.revised.torrent -m
    {
        "announce": "http://bar:123/announce",
        "announce-list": [
            [
                "http://bar:123/announce"
            ],
            [
                "http://baz:321/announce"
            ]
        ],
        "comment": "Forgot to add this comment.",
        "created by": "torf 3.1.0",
        "creation date": 1585682622,
        "info": {
            "name": "docs",
            "piece length": 16384,
            "private": 1,
            "files": [
                {
                    "length": 14877,
                    "path": [
                        "torf.1"
                    ]
                },
                {
                    "length": 10818,
                    "path": [
                        "torf.1.asciidoc"
                    ]
                },
                {
                    "length": 50522,
                    "path": [
                        "torf.1.html"
                    ]
                }
            ]
        }
    }


Installation
------------

The latest release is available on `PyPI <https://pypi.org/project/torf-cli>`_
and on `AUR <https://aur.archlinux.org/packages/torf-cli/>`_.


pipx
````

The easiest and cleanest installation method is `pipx
<https://pipxproject.github.io/pipx/>`__, which installs each application with all
dependencies in a separate virtual environment in ``~/.local/venvs/`` and links
the executable to ``~/.local/bin/``.

.. code:: sh

    $ pipx install torf-cli
    $ pipx upgrade torf-cli
    $ pipx uninstall torf-cli  # Also removes dependencies

The only drawback is that, at the time of writing, pipx doesn't make the man
page available, but `it's also available here
<https://rndusr.github.io/torf-cli/torf.1.html>`_.


pip
```

The alternative is regular `pip <https://pypi.org/project/torf/>`__, but if you
decide to uninstall, you have to manually uninstall the dependencies.

.. code:: sh

    $ pip3 install torf-cli         # Installs system-wide (/usr/local/)
    $ pip3 install --user torf-cli  # Installs in your home (~/.local/)

The `latest development version <https://github.com/rndusr/torf-cli>`_ is
available on GitHub in the master branch.

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
