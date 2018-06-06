# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details
# http://www.gnu.org/licenses/gpl-3.0.txt

import os
from xdg import BaseDirectory

__version__     = '1.2'
__appname__     = 'torf'
__url__         = 'https://github.com/rndusr/torf-cli'
__description__ = 'CLI tool to create, read and edit torrent files and produce magnet URIs'

DEFAULT_CONFIG_FILE = os.path.join(BaseDirectory.xdg_config_home, __appname__, 'config')
DEFAULT_CREATOR = f'{__appname__}/{__version__}'
VERSION_TEXT = f'{__appname__} {__version__} <{__url__}>'
HELP_TEXT = f"""
{VERSION_TEXT}

Create, display and edit torrents

USAGE
    {__appname__} PATH [OPTIONS] [-o TORRENT]
    {__appname__} -i TORRENT
    {__appname__} -i TORRENT [OPTIONS] -o NEW TORRENT

ARGUMENTS
    PATH                   Path to torrent's content
    --in, -i TORRENT       Read metainfo from TORRENT
    --out, -o TORRENT      Write metainfo to TORRENT (default: NAME.torrent)
    --magnet, -m           Create magnet link
    --exclude, -e EXCLUDE  File matching pattern that is used to exclude
                           files in PATH

    --name, -n NAME        Torrent name (default: basename of PATH)
    --tracker, -t TRACKER  Announce URL
    --webseed, -w WEBSEED  Webseed URL
    --private, -p          Forbid clients to use DHT and PEX
    --xseed, -x            Randomize info hash
    --date, -d DATE        Creation date as YYYY-MM-DD[ HH:MM[:SS]], 'now'
                           or 'today' (default: 'today')
    --comment, -c COMMENT  Comment that is stored in TORRENT

    --notracker, -T        Remove trackers from TORRENT
    --nowebseed, -W        Remove webseeds from TORRENT
    --noprivate, -P        Remove private flag from TORRENT
    --noxseed, -X          De-randomize info hash of TORRENT
    --nodate, -D           Remove date from TORRENT
    --nocomment, -C        Remove comment from TORRENT
    --nocreator, -R        Remove creator from TORRENT

    --config, -f FILE      Read configuration from FILE
                           (default: ~/.config/{__appname__}/config
    --noconfig, -F         Ignore configuration file
    --profile, -z PROFILE  Use options from PROFILE

    --yes, -y              Answer all yes/no prompts with "yes"
    --help, -h             Show this help screen and exit
    --version, -V          Show version number and exit
""".strip()
