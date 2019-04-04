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

import re
import argparse
import os
import errno
from xdg import BaseDirectory

from . import _errors
from . import _vars


DEFAULT_CONFIG_FILE = os.path.join(BaseDirectory.xdg_config_home, _vars.__appname__, 'config')
DEFAULT_CREATOR = f'{_vars.__appname__}/{_vars.__version__}'
VERSION_TEXT = f'{_vars.__appname__} {_vars.__version__} <{_vars.__url__}>'
HELP_TEXT = f"""
{_vars.__appname__} - {_vars.__description__}

USAGE
    {_vars.__appname__} PATH [OPTIONS] [-o TORRENT]
    {_vars.__appname__} -i TORRENT
    {_vars.__appname__} -i TORRENT [OPTIONS] -o NEW TORRENT

ARGUMENTS
    PATH                   Path to torrent's content
    --exclude, -e EXCLUDE  File matching pattern that is used to exclude
                           files in PATH
    --in, -i TORRENT       Read metainfo from TORRENT
    --out, -o TORRENT      Write metainfo to TORRENT (default: NAME.torrent)
    --name, -n NAME        Torrent name (default: basename of PATH)
    --tracker, -t TRACKER  Announce URL
    --webseed, -w WEBSEED  Webseed URL
    --private, -p          Forbid clients to use DHT and PEX
    --comment, -c COMMENT  Comment that is stored in TORRENT
    --date, -d DATE        Creation date as YYYY-MM-DD[ HH:MM[:SS]], 'now'
                           or 'today' (default: 'now')
    --source, -s SOURCE    Add "source" field
    --xseed, -x            Randomize info hash
    --max-piece-size SIZE  Maximum piece size in multiples of 1 MiB
                           (must be a power of two)

    --notracker, -T        Remove trackers from TORRENT
    --nowebseed, -W        Remove webseeds from TORRENT
    --noprivate, -P        Remove private flag from TORRENT
    --nocomment, -C        Remove comment from TORRENT
    --nodate, -D           Remove date from TORRENT
    --nosource, -S         Remove "source" field from TORRENT
    --noxseed, -X          De-randomize info hash of TORRENT
    --nocreator, -R        Remove creator from TORRENT
    --notorrent, -N        Don't create torrent file
    --nomagnet, -M         Don't create magnet link

    --yes, -y              Answer all yes/no prompts with "yes"
    --config, -f FILE      Read configuration from FILE
                           (default: ~/.config/{_vars.__appname__}/config
    --noconfig, -F         Ignore configuration file
    --profile, -z PROFILE  Use options from PROFILE

    --human, -u            Force human-readable output
    --nohuman, -U          Force machine-readable output
    --help, -h             Show this help screen and exit
    --version, -V          Show version number and exit
""".strip()


class CLIParser(argparse.ArgumentParser):
    def error(self, msg):
        raise _errors.CLIError(msg.capitalize())

_cliparser = CLIParser(add_help=False)

_cliparser.add_argument('PATH', nargs='?')
_cliparser.add_argument('--exclude', '-e', default=[], action='append')
_cliparser.add_argument('--in', '-i', default='')
_cliparser.add_argument('--out', '-o', default='')

_cliparser.add_argument('--name', '-n', default='')
_cliparser.add_argument('--tracker', '-t', default=[], action='append')
_cliparser.add_argument('--webseed', '-w', default=[], action='append')
_cliparser.add_argument('--private', '-p', action='store_true')
_cliparser.add_argument('--comment', '-c', default='')
_cliparser.add_argument('--date', '-d', default='')
_cliparser.add_argument('--source', '-s', default='')
_cliparser.add_argument('--xseed', '-x', action='store_true')
_cliparser.add_argument('--max-piece-size', default=0, type=float)

_cliparser.add_argument('--notracker', '-T', action='store_true')
_cliparser.add_argument('--nowebseed', '-W', action='store_true')
_cliparser.add_argument('--noprivate', '-P', action='store_true')
_cliparser.add_argument('--nocomment', '-C', action='store_true')
_cliparser.add_argument('--nodate', '-D', action='store_true')
_cliparser.add_argument('--nosource', '-S', action='store_true')
_cliparser.add_argument('--noxseed', '-X', action='store_true')
_cliparser.add_argument('--nocreator', '-R', action='store_true')
_cliparser.add_argument('--notorrent', '-N', action='store_true')
_cliparser.add_argument('--nomagnet', '-M', action='store_true')

_cliparser.add_argument('--config', '-f')
_cliparser.add_argument('--noconfig', '-F', action='store_true')
_cliparser.add_argument('--profile', '-z', default=[], action='append')

_cliparser.add_argument('--human', '-u', action='store_true')
_cliparser.add_argument('--nohuman', '-U', action='store_true')
_cliparser.add_argument('--yes', '-y', action='store_true')
_cliparser.add_argument('--help', '-h', action='store_true')
_cliparser.add_argument('--version', '-V', action='store_true')

def parse_args(args):
    return vars(_cliparser.parse_args(args))


def get_cfg(cliargs):
    """Combine values from CLI, config file, profiles and defaults"""
    clicfg = parse_args(cliargs)

    # If we don't need to read a config file, return parsed CLI arguments
    cfgfile = clicfg['config'] or DEFAULT_CONFIG_FILE
    if clicfg['noconfig'] or (not clicfg['config'] and not os.path.exists(cfgfile)):
        return clicfg

    # Read config file
    filecfg = _readfile(cfgfile)

    # Check for illegal arguments
    _check_illegal_configfile_arguments(filecfg, cfgfile)
    for cfg in filecfg.values():
        if isinstance(cfg, dict):
            _check_illegal_configfile_arguments(cfg, cfgfile)

    # Parse combined arguments from config file and CLI to allow --profile in
    # CLI and config file
    try:
        cfg = parse_args(_cfg2args(filecfg) + cliargs)
    except _errors.CLIError as e:
        raise _errors.ConfigError(f'{cfgfile}: {e}', errno=e.errno)

    # Apply profiles specified in config file or on CLI
    def apply_profile(profname):
        prof = filecfg.get(profname)
        if prof is None:
            raise _errors.ConfigError(f'{cfgfile}: No such profile: {profname}', errno=errno.EINVAL)
        else:
            profargs.extend(_cfg2args(prof))

    profargs = []
    for profname in cfg['profile']:
        apply_profile(profname)

    # Combine arguments from profiles with arguments from global config and CLI
    args = _cfg2args(filecfg) + profargs + cliargs
    try:
        return parse_args(args)
    except _errors.CLIError as e:
        raise _errors.ConfigError(f'{cfgfile}: {e}', errno=e.errno)

def _check_illegal_configfile_arguments(cfg, cfgfile):
    for arg in ('config', 'noconfig', 'profile', 'help', 'version'):
        if arg in cfg:
            raise _errors.ConfigError(f'{cfgfile}: Not allowed in config file: {arg}',
                                      errno=errno.EINVAL)


_re_bool = re.compile(r'^(\S+)$')
_re_assign = re.compile(r'^(\S+)\s*=\s*(.*)\s*$')

def _readfile(filepath):
    """Read INI-style file into dictionary"""

    # Catch any errors from the OS
    try:
        with open(filepath, 'r') as f:
            lines = tuple(l.strip() for l in f.readlines())
    except OSError as e:
        raise _errors.ConfigError(f'{filepath}: {os.strerror(e.errno)}', errno=e.errno)

    # Parse lines
    cfg = subcfg = {}
    for line in lines:
        # Skip empty lines and comments
        if not line or line[0] == '#':
            continue

        # Start new profile
        if line[0] == '[' and line[-1] == ']':
            profile_name = line[1:-1]
            cfg[profile_name] = subcfg = {}
            continue

        # Boolean option
        bool_match = _re_bool.match(line)
        if bool_match:
            name = bool_match.group(1)
            subcfg[name] = True
            continue

        # String option
        assign_match = _re_assign.match(line)
        if assign_match:
            name = assign_match.group(1)
            value = assign_match.group(2).strip()

            # Strip off optional quotes
            if value:
                if value[0] == value[-1] == '"' or value[0] == value[-1] == "'":
                    value = value[1:-1]

            value = _resolve_envvars(value)

            # Multiple occurences of the same name turn its value into a list
            if name in subcfg:
                if not isinstance(subcfg[name], list):
                    subcfg[name] = [subcfg[name]]
                subcfg[name].append(value)
            else:
                subcfg[name] = value

            continue

    return cfg


def _resolve_envvars(string):
    def resolve(m):
        # The string of \ chars is halfed because every \ escapes the next \.
        esc_count = len(m.group(1))
        esc_str = int(esc_count / 2) * '\\'
        varname = m.group(2) or m.group(3)
        value =  os.environ.get(varname, '$'+varname)
        # Uneven number of \ means $varname is escaped, even number of \ means
        # it is not.
        if esc_count and esc_count % 2 != 0:
            return f'{esc_str}${varname}'
        else:
            return f'{esc_str}{value}'
    regex = re.compile(r'(\\*)\$(?:(\w+)|\{(\w+)\})')
    return regex.sub(resolve, string)


def _cfg2args(cfg):
    args = []
    for name,value in cfg.items():
        option = '--' + name

        # Option with parameter
        if isinstance(value, str):
            args.extend((option, value))

        # Switch without parameter
        elif isinstance(value, (bool, type(None))):
            args.append(option)

        # Option that can occur multiple times
        elif isinstance(value, list):
            for item in value:
                args.extend((option, item))
    return args
