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

import torf
import argparse
import sys
import errno
import os
import time
import datetime
from collections import abc
from xdg import BaseDirectory

from . import __vars__ as _vars
from . import _util
from . import _config


class CLIError(Exception):
    def __init__(self, msg=None, error_code=None):
        self.errno = error_code
        if msg is None:
            if error_code is None:
                raise RuntimeError('Both msg and error_code are missing!')
            msg = os.strerror(error_code)
        super().__init__(f'{_vars.__appname__}: {msg}')


_DEFAULT_CREATOR = f'{_vars.__appname__}/{_vars.__version__}'
_VERSION_INFO = f'{_vars.__appname__} {_vars.__version__} <{_vars.__url__}>'
_DEFAULT_PROFILE_FILE = os.path.join(BaseDirectory.xdg_config_home, _vars.__appname__, 'config')
_HELP = f"""
{_VERSION_INFO}

Create, display and edit torrents

USAGE
    {_vars.__appname__} PATH [OPTIONS] [-o TORRENT]
    {_vars.__appname__} -i TORRENT
    {_vars.__appname__} -i TORRENT [OPTIONS] -o NEW TORRENT

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
    --noprivate, -P        Allow clients to use DHT and PEX
    --noxseed, -X          De-randomize info hash of TORRENT
    --nodate, -D           Remove date from TORRENT
    --nocomment, -C        Remove comment from TORRENT
    --nocreator, -R        Remove creator from TORRENT
    --noexclude, -E        Don't exlude any files
    --nomagnet, -M         Don't create magnet link

    --profile, -f PROFILE  Use configuration of PROFILE
    --config, -F CONFIG    Read configuration from CONFIG file

    --yes, -y              Answer all yes/no prompts with "yes"
    --help,-h              Show this help screen and exit
    --version              Show version number and exit
""".strip()


def _get_cfg(argv):
    # Read CLI arguments
    argp = argparse.ArgumentParser(add_help=False)

    argp.add_argument('--help', '-h', action='store_true')
    argp.add_argument('--version', action='store_true')

    argp.add_argument('PATH', nargs='?')
    argp.add_argument('--name', '-n', default='')
    argp.add_argument('--exclude', '-e', default=[], action='append')
    argp.add_argument('--noexclude', '-E', default=False, action='store_true')
    argp.add_argument('--in', '-i', default='')
    argp.add_argument('--out', '-o', default='')
    argp.add_argument('--yes', '-y', default=False, action='store_true')

    argp.add_argument('--magnet', '-m', default=False, action='store_true')
    argp.add_argument('--nomagnet', '-M', default=False, action='store_true')
    argp.add_argument('--tracker', '-t', default=[], action='append')
    argp.add_argument('--notracker', '-T', default=False, action='store_true')
    argp.add_argument('--webseed', '-w', default=[], action='append')
    argp.add_argument('--nowebseed', '-W', default=False, action='store_true')

    argp.add_argument('--private', '-p', default=False, action='store_true')
    argp.add_argument('--noprivate', '-P', default=False, action='store_true')
    argp.add_argument('--date', '-d', default='')
    argp.add_argument('--nodate', '-D', default=False, action='store_true')
    argp.add_argument('--comment', '-c', default='')
    argp.add_argument('--nocomment', '-C', default=False, action='store_true')
    argp.add_argument('--nocreator', '-R', default=False, action='store_true')
    argp.add_argument('--xseed', '-x', default=False, action='store_true')
    argp.add_argument('--noxseed', '-X', default=False, action='store_true')

    argp.add_argument('--config', '-F', default=_DEFAULT_PROFILE_FILE)
    argp.add_argument('--profile', '-f', default=[], action='append')

    cfg = vars(argp.parse_args(argv))

    # Read config file if specified by user or if it exists
    if cfg['config'] != _DEFAULT_PROFILE_FILE or os.path.exists(cfg['config']):
        configfile = cfg['config']

        try:
            cfgfile = _config.read(cfg['config'])
        except OSError as e:
            raise CLIError(f'{configfile}: {os.strerror(e.errno)}',
                           error_code=e.errno)

        # Separate defaults from given CLI arguments
        defaults = {k:argp.get_default(k) for k in cfg}
        cli = {name:value for name,value in cfg.items()
               if cfg[name] != defaults[name]}
        try:
            cfgfile = _config.validate(cfgfile, defaults)
            cfg = _config.combine(cli, cfgfile, defaults)
        except _config.ConfigError as e:
            raise CLIError(f'{configfile}: {e}', error_code=errno.EINVAL)

    return cfg


def run(argv=sys.argv[1:]):
    cfg = _get_cfg(argv)
    if cfg['help']:
        print(_HELP)
    elif cfg['version']:
        print(_VERSION_INFO)
    else:
        # Figure out our modus operandi
        if cfg['in']:
            if cfg['out'] or cfg['magnet']:
                _edit_mode(cfg)
            else:
                _info_mode(cfg)
        elif cfg['PATH']:
            _create_mode(cfg)
        else:
            raise CLIError(f'Missing PATH or --in argument (see `{_vars.__appname__} -h`)',
                           error_code=errno.EINVAL)


def _info_mode(cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)
    else:
        _show_torrent_info(torrent)


def _create_mode(cfg):
    try:
        torrent = torf.Torrent(path=cfg['PATH'],
                               name=cfg['name'] or None,
                               exclude=cfg['exclude'] if not cfg['noexclude'] else (),
                               trackers=cfg['tracker'] if not cfg['notracker'] else None,
                               webseeds=cfg['webseed'] if not cfg['nowebseed'] else None,
                               private=cfg['private'] if not cfg['noprivate'] else False,
                               randomize_infohash=cfg['xseed'] if not cfg['noxseed'] else False,
                               comment=cfg['comment'] if not cfg['nocomment'] else None,
                               created_by=None if cfg['nocreator'] else _DEFAULT_CREATOR)
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)

    if not cfg['nodate']:
        if cfg['date']:
            try:
                torrent.creation_date = _util.parse_date(cfg['date'])
            except ValueError:
                raise CLIError(f'{cfg["date"]}: Invalid date', error_code=errno.EINVAL)
        else:
            torrent.creation_date = _util.parse_date('today')

    # Get user confirmation about overwriting existing output file
    _check_output_file_exists(torrent, cfg)
    _show_torrent_info(torrent)
    _hash_pieces(torrent)
    _write_torrent(torrent, cfg)


def _edit_mode(cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)

    def set_or_remove(arg_name, attr_name):
        arg_noname = 'no' + arg_name
        if cfg[arg_name] and cfg[arg_noname]:
            raise CLIError(f'Conflicting arguments: --{arg_name}, --{arg_noname}',
                           error_code=errno.EINVAL)
        elif cfg[arg_noname]:
            setattr(torrent, attr_name, None)
        elif cfg[arg_name]:
            try:
                setattr(torrent, attr_name, cfg[arg_name])
            except torf.TorfError as e:
                raise CLIError(e, error_code=e.errno)

    set_or_remove('comment', 'comment')
    set_or_remove('private', 'private')
    set_or_remove('xseed', 'randomize_infohash')

    def list_set_or_remove(arg_name, attr_name):
        arg_noname = 'no' + arg_name
        if cfg[arg_noname]:
            setattr(torrent, attr_name, None)
        if cfg[arg_name]:
            old_list = getattr(torrent, attr_name) or []
            new_list = old_list + cfg[arg_name]
            try:
                setattr(torrent, attr_name, new_list)
            except torf.TorfError as e:
                raise CLIError(e, error_code=e.errno)

    list_set_or_remove('tracker', 'trackers')
    list_set_or_remove('webseed', 'webseeds')

    if cfg['nocreator']:
        torrent.created_by = None

    if cfg['nodate']:
        torrent.creation_date = None
    elif cfg['date']:
        try:
            torrent.creation_date = _util.parse_date(cfg['date'])
        except ValueError:
            raise CLIError(f'{cfg["date"]}: Invalid date', error_code=errno.EINVAL)

    if cfg['PATH']:
        try:
            torrent.path = cfg['PATH']
        except torf.TorfError as e:
            raise CLIError(e, error_code=e.errno)
        else:
            _hash_pieces(torrent)

    if cfg['name']:
        torrent.name = cfg['name']

    _show_torrent_info(torrent)
    _write_torrent(torrent, cfg)


def _show_torrent_info(torrent):
    lines = []
    lines.append(('Name', torrent.name))
    if torrent.is_ready:
        lines.append(('Info Hash', torrent.infohash))
    size = _util.bytes2string(torrent.size) if _util.is_tty() else torrent.size
    lines.append(('Size', size))
    if torrent.comment:
        lines.append(('Comment', torrent.comment.split('\n')))

    if torrent.creation_date:
        lines.append(('Creation Date', torrent.creation_date.isoformat(sep=' ', timespec='seconds')))
    if torrent.created_by:
        lines.append(('Created By', torrent.created_by))
    lines.append(('Private', 'yes' if torrent.private else 'no'))

    trackers = []  # List of lines
    if torrent.trackers:
        if all(len(tier) <= 1 for tier in torrent.trackers):
            # One tracker per tier - don't bother with printing tiers
            for tier in torrent.trackers:
                if tier:
                    trackers.append(tier[0])
        else:
            # At least one tier has multiple trackers
            if _util.is_tty():
                for i,tier in enumerate(torrent.trackers, 1):
                    if tier:
                        trackers.append(f'Tier {i}: {tier[0]}')
                        for tracker in tier[1:]:
                            trackers.append(' '*8 + tracker)
            else:
                # Ignore tiers in parsable output, just flatten the list
                for tier in torrent.trackers:
                    trackers.extend(tier)

    if trackers:
        label = 'Tracker' + ('s' if len(trackers) > 1 else '')
        lines.append((label, trackers))

    if torrent.webseeds:
        label = 'Webseed' + ('s' if len(torrent.webseeds) > 1 else '')
        lines.append((label, torrent.webseeds))

    if torrent.httpseeds:
        label = 'HTTP Seed' + ('s' if len(torrent.httpseeds) > 1 else '')
        lines.append((label, torrent.httpseeds))

    if torrent.piece_size:
        piece_size = _util.bytes2string(torrent.piece_size) if _util.is_tty() else torrent.piece_size
        lines.append(('Piece Size', piece_size))
    if torrent.piece_size:
        lines.append(('Piece Count', torrent.pieces))

    files = tuple(torrent.files)
    lines.append(('File Count', len(files)))
    if torrent.exclude:
        lines.append(('Exclude', torrent.exclude))
    if _util.is_tty():
        lines.append(('Files', _util.make_filetree(torrent.filetree)))
    else:
        lines.append(('Files', files))

    for label,value in lines:
        _info(label, value)


_INFO_LABEL_WIDTH = 13
def _info(label, value, newline=True):
    if _util.is_tty():
        # Make output human-readable
        label = f'{label.rjust(_INFO_LABEL_WIDTH)}'
        sep = '  '
        if not isinstance(value, str) and isinstance(value, abc.Iterable):
            value_parts = [f'{value[0]}']
            indent = len(label) * ' '
            for item in value[1:]:
                value_parts.append(f'{indent}{sep}{item}')
            value = '\n'.join(value_parts)
    else:
        # Make output easy to parse
        sep = '\t'
        if not isinstance(value, str) and isinstance(value, abc.Iterable):
            value = sep.join(value)

    if newline:
        print(f'{label}{sep}{value}')
    else:
        print(f'{label}{sep}{value}', end='', flush=True)


def _get_torrent_filepath(torrent, cfg):
    if cfg['magnet'] and not cfg['out']:
        # Create only magnet link
        return None
    elif cfg['out']:
        # User-given torrent file path
        torrent_filepath = cfg['out']
    else:
        # Default to torrent's name in cwd
        torrent_filepath = torrent.name + '.torrent'
    return torrent_filepath


def _check_output_file_exists(torrent, cfg):
    torrent_filepath = _get_torrent_filepath(torrent, cfg)
    if torrent_filepath and os.path.exists(torrent_filepath):
        if os.path.isdir(torrent_filepath):
            raise CLIError(f'{torrent_filepath}: {os.strerror(errno.EISDIR)}',
                           error_code=errno.EISDIR)
        elif not cfg['yes'] and not _util.ask_yes_no(f'{torrent_filepath}: Overwrite file?', default='n'):
            raise CLIError(f'{torrent_filepath}: {os.strerror(errno.EEXIST)}',
                           error_code=errno.EEXIST)


def _write_torrent(torrent, cfg):
    torrent_filepath = _get_torrent_filepath(torrent, cfg)

    if cfg['magnet'] or not torrent_filepath:
        _info('Magnet URI', torrent.magnet())

    if torrent_filepath:
        try:
            torrent.write(torrent_filepath, overwrite=True)
        except torf.TorfError as e:
            raise CLIError(e, error_code=e.errno)
        else:
            _info('Torrent File', f'{torrent_filepath}')


def _hash_pieces(torrent):
    _info('Path', torrent.path)

    start_time = time.time()
    progress = _util.Average(samples=5)
    time_left = _util.Average(samples=10)
    def progress_callback(torrent, filepath, pieces_done, pieces_total):
        msg = f'{pieces_done / pieces_total * 100:.2f} %'
        if pieces_done < pieces_total:
            progress.add(pieces_done)
            if len(progress.values) >= 2:
                time_diff = progress.times[-1] - progress.times[0]
                pieces_diff = progress.values[-1] - progress.values[0]
                bytes_diff = pieces_diff * torrent.piece_size
                bytes_per_sec = bytes_diff / time_diff
                bytes_left = (pieces_total - pieces_done) * torrent.piece_size
                time_left.add(bytes_left / bytes_per_sec)
                time_left_avg = datetime.timedelta(seconds=int(time_left.avg) + 1)
                eta = datetime.datetime.now() + time_left_avg
                eta_str = '{0:%H}:{0:%M}:{0:%S}'.format(eta)
                msg += f'  |  ETA: {eta_str}  |  {time_left_avg} left  |  {bytes_per_sec/1048576:.2f} MB/s'
        else:
            total_time_diff = datetime.timedelta(seconds=round(time.time() - start_time))
            bytes_per_sec = torrent.size / (total_time_diff.total_seconds()+1)
            msg += f'  |  {bytes_per_sec/1045876:.2f} MB/s  |  Time: {total_time_diff}'
        _util.clear_line()
        _info('Progress', msg, newline=False)

    canceled = True
    try:
        try:
            canceled = not torrent.generate(callback=progress_callback, interval=0.5)
        finally:
            print()
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)
    except KeyboardInterrupt:
        raise CLIError('Aborted', error_code=errno.ECANCELED)
    finally:
        if not canceled:
            _info('Info Hash', torrent.infohash)
