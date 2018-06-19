torf-cli
========

torf-cli is a command line tool that can create torrents and magnet links, dump
the metainfo of a torrent, and edit existing torrents (e.g.  to fix a typo
without having to hash all the pieces again).

The output is pleasant to read for humans and easy to parse with common CLI
tools if stdout is not a TTY.

An optional configuration file specifies custom default options and profiles
that give names to sets of options.

Documentation is available as a man page, or you can `read it here
<https://rndusr.github.io/torf-cli/torf.1.html>`_.

The only depdencies are `torf <https://pypi.org/project/torf/>`_ and `pyxdg
<https://pypi.org/project/pyxdg/>`_.


Examples
--------

Create private torrent with two trackers:

.. code:: sh

    $ torf ./docs -t http://bar:123/announce -t http://baz:321/announce --private
           Name  docs
           Size  60.1 KiB
        Created  2018-06-19 14:47:26
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  4
     File Count  3
          Files  docs
                 ├─torf.1
                 ├─torf.1.asciidoc
                 └─torf.1.html
           Path  docs
       Progress  100.00 %  |  Time: 0:00:00  |  58.84 MB/s
      Info Hash  215f506179b6526b582e4fb78ebc24dd1f2a791f
         Magnet  magnet:?xt=urn:btih:215f506179b6526b582e4fb78ebc24dd1f2a791f&dn=docs&xl=61542&tr=http%3A%2F%2Fbar%3A123%2Fannounce&tr=http%3A%2F%2Fbaz%3A321%2Fannounce
        Torrent  docs.torrent


Display metainfo of an existing torrent:

.. code:: sh

    $ torf -i docs.torrent
           Name  docs
      Info Hash  215f506179b6526b582e4fb78ebc24dd1f2a791f
           Size  60.1 KiB
        Created  2018-06-19 14:47:26
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  4
     File Count  3
          Files  docs
                 ├─torf.1
                 ├─torf.1.asciidoc
                 └─torf.1.html
         Magnet  magnet:?xt=urn:btih:215f506179b6526b582e4fb78ebc24dd1f2a791f&dn=docs&xl=61542&tr=http%3A%2F%2Fbar%3A123%2Fannounce&tr=http%3A%2F%2Fbaz%3A321%2Fannounce

Quickly add a comment to an existing torrent:

.. code:: sh

    $ torf -i docs.torrent --comment 'Forgot to add this comment.' -o docs.revised.torrent
           Name  docs
      Info Hash  215f506179b6526b582e4fb78ebc24dd1f2a791f
           Size  60.1 KiB
        Comment  Forgot to add this comment.
        Created  2018-06-19 14:47:26
        Private  yes
       Trackers  http://bar:123/announce
                 http://baz:321/announce
     Piece Size  16 KiB
    Piece Count  4
     File Count  3
          Files  docs
                 ├─torf.1
                 ├─torf.1.asciidoc
                 └─torf.1.html
         Magnet  magnet:?xt=urn:btih:215f506179b6526b582e4fb78ebc24dd1f2a791f&dn=docs&xl=61542&tr=http%3A%2F%2Fbar%3A123%2Fannounce&tr=http%3A%2F%2Fbaz%3A321%2Fannounce
        Torrent  docs.revised.torrent

Get a list of files:

.. code:: sh

    $ torf -i docs.revised.torrent | grep '^Files' | cut -f2-
    docs/torf.1     docs/torf.1.asciidoc    docs/torf.1.html


Installation
------------

The latest release is available on `PyPI <https://pypi.org/project/torf-cli>`_
and on `AUR <https://aur.archlinux.org/packages/python-torf-cli/>`_.


pipsi
`````

The easiest and cleanest installation method is `pipsi
<https://pypi.org/project/pipsi/>`_, which installs each application with all
dependencies in a separate virtual environment in ``~/.local/venvs/`` and links
the executable to ``~/.local/bin/``.

.. code:: sh

    $ pipsi install torf-cli
    $ pipsi upgrade torf-cli
    $ pipsi uninstall torf-cli  # Also removes dependencies

The only drawback is that, at the time of writing, pipsi doesn't make the man
page available.  But you can just `read it in your browser
<https://rndusr.github.io/torf-cli/torf.1.html>`_.


pip
```

The alternative is regular `pip <https://pypi.org/project/torf/>`_, but if you
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
