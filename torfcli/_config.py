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

import argparse
import itertools
import os
import re

import torf
from xdg import BaseDirectory

from . import _errors, _utils, _vars

DEFAULT_CONFIG_FILE = os.path.join(BaseDirectory.xdg_config_home, _vars.__appname__, 'config')
DEFAULT_CREATOR = f'{_vars.__appname__} {_vars.__version__}'
VERSION_TEXT = f'{_vars.__appname__} {_vars.__version__} <{_vars.__url__}>'
HELP_TEXT = f"""
{_vars.__appname__} - {_vars.__description__}

USAGE
    {_vars.__appname__} PATH [OPTIONS] [-o TORRENT]    # Create torrent
    {_vars.__appname__} -i INPUT                       # Display torrent
    {_vars.__appname__} -i INPUT [OPTIONS] -o TORRENT  # Edit torrent
    {_vars.__appname__} -i TORRENT PATH                # Verify file content

ARGUMENTS
    PATH                   Path to torrent's content
    --exclude, -e PATTERN  Exclude files that match this glob pattern
                           (e.g. "*.txt")
    --include PATTERN      Include excluded files that match this glob
                           pattern
    --exclude-regex, -er PATTERN
                           Exclude files that match this regular expression
                           (e.g. ".*\\.txt$")
    --include-regex, -ir PATTERN
                           Include excluded files that match this regular
                           expression
    --in, -i INPUT         Read metainfo from torrent file or magnet URI
    --out, -o TORRENT      Write metainfo to TORRENT (default: NAME.torrent)
    --name, -n NAME        Torrent name (default: basename of PATH)
    --tracker, -t TRACKER  List of comma-separated announce URLs; may be
                           given multiple times for multiple tiers
    --webseed, -w WEBSEED  Webseed URL; may be given multiple times
    --private, -p          Forbid clients to use DHT and PEX
    --comment, -c COMMENT  Comment that is stored in the torrent file
    --date, -d DATE        Creation date as YYYY-MM-DD[ HH:MM[:SS]], 'now'
                           or 'today' (default: 'now')
    --source, -s SOURCE    Add "source" field
    --xseed, -x            Randomize info hash
    --max-piece-size SIZE  Maximum piece size in multiples of 1 MiB
                           (must be a power of two)

    --notracker, -T        Remove trackers from INPUT
    --nowebseed, -W        Remove webseeds from INPUT
    --noprivate, -P        Remove private flag from INPUT
    --nocomment, -C        Remove comment from INPUT
    --nodate, -D           Remove date from INPUT
    --nosource, -S         Remove "source" field from INPUT
    --noxseed, -X          De-randomize info hash of INPUT
    --nocreator, -R        Remove creator from INPUT
    --notorrent, -N        Don't create torrent file
    --nomagnet, -M         Don't create magnet URI
    --novalidate, -V       Don't check SOURCE and/or TORRENT for errors

    --yes, -y              Answer all yes/no prompts with "yes"
    --config, -f FILE      Read configuration from FILE
                           (default: ~/.config/{_vars.__appname__}/config
    --noconfig, -F         Ignore configuration file
    --profile, -z PROFILE  Use options from PROFILE

    --verbose, -v          Increase verbosity
    --json, -j             Print a single JSON object
    --metainfo, -m         Print torrent metainfo as JSON object
    --human, -u            Force human-readable output
    --nohuman, -U          Force machine-readable output
    --threads THREADS      Number of threads to use for hashing
    --help, -h             Show this help screen and exit
    --version              Show version number and exit
""".strip()


class CLIParser(argparse.ArgumentParser):
    def error(self, msg):
        msg = msg[0].upper() + msg[1:]
        raise _errors.CliError(msg)

_cliparser = CLIParser(add_help=False)

_cliparser.add_argument('PATH', nargs='?')
_cliparser.add_argument('--basename', '-b', action='store_true')
_cliparser.add_argument('--exclude', '-e', default=[], action='append')
_cliparser.add_argument('--exclude-regex', '-er', default=[], action='append')
_cliparser.add_argument('--include', default=[], action='append')
_cliparser.add_argument('--include-regex', '-ir', default=[], action='append')
_cliparser.add_argument('--in', '-i', default='')
_cliparser.add_argument('--out', '-o', default='')

_cliparser.add_argument('--name', '-n', default='')
_cliparser.add_argument('--tracker', '-t', default=[], action='append')
_cliparser.add_argument('--webseed', '-w', default=[], action='append')
_cliparser.add_argument('--private', '-p', action='store_true', default=None)
_cliparser.add_argument('--comment', '-c')
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
_cliparser.add_argument('--novalidate', '-V', action='store_true')

_cliparser.add_argument('--yes', '-y', action='store_true')
_cliparser.add_argument('--config', '-f')
_cliparser.add_argument('--noconfig', '-F', action='store_true')
_cliparser.add_argument('--profile', '-z', default=[], action='append')

_cliparser.add_argument('--verbose', '-v', action='count', default=0)
_cliparser.add_argument('--json', '-j', action='store_true')
_cliparser.add_argument('--metainfo', '-m', action='store_true')
_cliparser.add_argument('--human', '-u', action='store_true')
_cliparser.add_argument('--nohuman', '-U', action='store_true')
_cliparser.add_argument('--threads', type=int, default=0)
_cliparser.add_argument('--help', '-h', action='store_true')
_cliparser.add_argument('--version', action='store_true')
_cliparser.add_argument('--debug-file')


def parse_early_args(args):
    # Parse only some arguments we need to figure out how to report errors.
    # Ignore all other arguments and any errors we might encounter.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--json', '-j', action='store_true')
    parser.add_argument('--human', '-u', action='store_true')
    parser.add_argument('--nohuman', '-U', action='store_true')
    return vars(parser.parse_known_args(args)[0])


def parse_args(args):
    cfg = vars(_cliparser.parse_args(args))

    # Validate creation date
    if cfg['date']:
        try:
            cfg['date'] = _utils.parse_date(cfg['date'] or 'now')
        except ValueError:
            raise _errors.CliError(f'{cfg["date"]}: Invalid date')

    # Validate max piece size
    if cfg['max_piece_size']:
        cfg['max_piece_size'] = cfg['max_piece_size'] * 1048576
        if cfg['max_piece_size'] > torf.Torrent.piece_size_max:
            torf.Torrent.piece_size_max = cfg['max_piece_size']
        try:
            torf.Torrent().piece_size = cfg['max_piece_size']
        except torf.PieceSizeError as e:
            raise _errors.CliError(e)

    # Validate tracker URLs
    for tier in cfg['tracker']:
        for url in tier.split(','):
            try:
                torf.Torrent().trackers = url
            except torf.URLError as e:
                raise _errors.CliError(e)

    # Validate webseed URLs
    for webseed in cfg['webseed']:
        try:
            torf.Torrent().webseeds = (webseed,)
        except torf.URLError as e:
            raise _errors.CliError(e)

    # Validate regular expressions
    for regex in itertools.chain(cfg['exclude_regex'], cfg['include_regex']):
        try:
            re.compile(regex)
        except re.error as e:
            raise _errors.CliError(f'Invalid regular expression: {regex}: '
                                   f'{str(e)[0].upper()}{str(e)[1:]}')

    cfg['validate'] = not cfg['novalidate']

    return cfg


def get_cfg(cliargs):
    """Combine values from CLI, config file, profiles and defaults"""
    clicfg = parse_args(cliargs)

    if clicfg['debug_file']:
        import logging
        logging.basicConfig(level=logging.DEBUG, format='%(message)s',
                            filename=clicfg['debug_file'])

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
    except _errors.CliError as e:
        raise _errors.ConfigError(f'{cfgfile}: {e}')

    # Apply profiles specified in config file or on CLI
    def apply_profile(profname):
        prof = filecfg.get(profname)
        if prof is None:
            raise _errors.ConfigError(f'{cfgfile}: No such profile: {profname}')
        else:
            profargs.extend(_cfg2args(prof))

    profargs = []
    for profname in cfg['profile']:
        apply_profile(profname)

    # Combine arguments from profiles with arguments from global config and CLI
    args = _cfg2args(filecfg) + profargs + cliargs
    try:
        return parse_args(args)
    except _errors.CliError as e:
        raise _errors.ConfigError(f'{cfgfile}: {e}')

def _check_illegal_configfile_arguments(cfg, cfgfile):
    for arg in ('in', 'name', 'out', 'config', 'noconfig', 'profile', 'help', 'version'):
        if arg in cfg:
            raise _errors.ConfigError(f'{cfgfile}: Not allowed in config file: {arg}')


_re_bool = re.compile(r'^(\S+)$')
_re_assign = re.compile(r'^(\S+)\s*=\s*(.*)\s*$')

def _readfile(filepath):
    """Read INI-style file into dictionary"""

    # Catch any errors from the OS
    try:
        with open(filepath, 'r') as f:
            lines = tuple(line.strip() for line in f.readlines())
    except OSError as e:
        raise _errors.ConfigError(f'{filepath}: {os.strerror(e.errno)}')

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
        value = os.environ.get(varname, '$' + varname)
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
