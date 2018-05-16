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

from . import __vars__ as _vars
from . import _util as _util


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
""".strip()


def _get_args(argv):
    argp = argparse.ArgumentParser(add_help=False)

    argp.add_argument('--help', '-h', action='store_true')
    argp.add_argument('--version', action='store_true')

    argp.add_argument('PATH', nargs='?')
    argp.add_argument('--exclude', '-e', action='append', default=[])
    argp.add_argument('--in', '-i')
    argp.add_argument('--out', '-o')
    argp.add_argument('--yes', '-y', action='store_true')
    argp.add_argument('--magnet', '-m', action='store_true')

    argp.add_argument('--name', '-n')
    argp.add_argument('--tracker', '-t', action='append')
    argp.add_argument('--notracker', '-T', action='store_true')
    argp.add_argument('--webseed', '-w', action='append')
    argp.add_argument('--nowebseed', '-W', action='store_true')
    argp.add_argument('--private', '-p', action='store_true')
    argp.add_argument('--noprivate', '-P', action='store_true')
    argp.add_argument('--xseed', '-x', action='store_true')
    argp.add_argument('--noxseed', '-X', action='store_true')
    argp.add_argument('--date', '-d')
    argp.add_argument('--nodate', '-D', action='store_true')
    argp.add_argument('--comment', '-c')
    argp.add_argument('--nocomment', '-C', action='store_true')
    argp.add_argument('--nocreator', '-R', action='store_true')

    return vars(argp.parse_args(argv))


def run(argv=sys.argv[1:]):
    args = _get_args(argv)
    if args['help']:
        print(_HELP)
    elif args['version']:
        print(_VERSION_INFO)
    else:
        # Figure out our modus operandi
        if args['in']:
            if args['out'] or args['magnet']:
                _edit_mode(args)
            else:
                _info_mode(args)
        elif args['PATH']:
            _create_mode(args)
        else:
            raise CLIError(f'Missing PATH or --in argument (see `{_vars.__appname__} -h`)',
                           error_code=errno.EINVAL)


def _info_mode(args):
    try:
        torrent = torf.Torrent.read(args['in'])
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)
    else:
        _show_torrent_info(torrent)


def _create_mode(args):
    try:
        torrent = torf.Torrent(path=args['PATH'],
                               name=args['name'],
                               exclude=args['exclude'],
                               trackers=args['tracker'],
                               webseeds=args['webseed'],
                               private=args['private'],
                               randomize_infohash=args['xseed'],
                               comment=args['comment'],
                               created_by=None if args['nocreator'] else _DEFAULT_CREATOR)
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)

    if args['date']:
        try:
            torrent.creation_date = _util.parse_date(args['date'])
        except ValueError:
            raise CLIError(f'{args["date"]}: Invalid date', error_code=errno.EINVAL)
    elif not args['nodate']:
        torrent.creation_date = _util.parse_date('today')

    # Get user confirmation about overwriting existing output file
    _check_output_file_exists(torrent, args)
    _show_torrent_info(torrent)
    _hash_pieces(torrent)
    _write_torrent(torrent, args)


def _edit_mode(args):
    try:
        torrent = torf.Torrent.read(args['in'])
    except torf.TorfError as e:
        raise CLIError(e, error_code=e.errno)

    def set_or_remove(arg_name, attr_name):
        arg_noname = 'no' + arg_name
        if args[arg_name] and args[arg_noname]:
            raise CLIError(f'Conflicting arguments: --{arg_name}, --{arg_noname}',
                           error_code=errno.EINVAL)
        elif args[arg_noname]:
            setattr(torrent, attr_name, None)
        elif args[arg_name]:
            try:
                setattr(torrent, attr_name, args[arg_name])
            except torf.TorfError as e:
                raise CLIError(e, error_code=e.errno)

    set_or_remove('comment', 'comment')
    set_or_remove('private', 'private')
    set_or_remove('xseed', 'randomize_infohash')

    def list_set_or_remove(arg_name, attr_name):
        arg_noname = 'no' + arg_name
        if args[arg_noname]:
            setattr(torrent, attr_name, None)
        if args[arg_name]:
            old_list = getattr(torrent, attr_name) or []
            new_list = old_list + args[arg_name]
            try:
                setattr(torrent, attr_name, new_list)
            except torf.TorfError as e:
                raise CLIError(e, error_code=e.errno)

    list_set_or_remove('tracker', 'trackers')
    list_set_or_remove('webseed', 'webseeds')

    if args['nocreator']:
        torrent.created_by = None

    if args['date']:
        try:
            torrent.creation_date = _util.parse_date(args['date'])
        except ValueError:
            raise CLIError(f'{args["date"]}: Invalid date', error_code=errno.EINVAL)
    elif args['nodate']:
        torrent.creation_date = None

    if args['PATH']:
        try:
            torrent.path = args['PATH']
        except torf.TorfError as e:
            raise CLIError(e, error_code=e.errno)
        else:
            _hash_pieces(torrent)

    if args['name']:
        torrent.name = args['name']

    _show_torrent_info(torrent)
    _write_torrent(torrent, args)


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


def _get_torrent_filepath(torrent, args):
    if args['magnet'] and not args['out']:
        # Create only magnet link
        return None
    elif args['out']:
        # User-given torrent file path
        torrent_filepath = args['out']
    else:
        # Default to torrent's name in cwd
        torrent_filepath = torrent.name + '.torrent'
    return torrent_filepath


def _check_output_file_exists(torrent, args):
    torrent_filepath = _get_torrent_filepath(torrent, args)
    if torrent_filepath and os.path.exists(torrent_filepath):
        if os.path.isdir(torrent_filepath):
            raise CLIError(f'{torrent_filepath}: {os.strerror(errno.EISDIR)}',
                           error_code=errno.EISDIR)
        elif not args['yes'] and not _util.ask_yes_no(f'{torrent_filepath}: Overwrite file?', default='n'):
            raise CLIError(f'{torrent_filepath}: {os.strerror(errno.EEXIST)}',
                           error_code=errno.EEXIST)


def _write_torrent(torrent, args):
    torrent_filepath = _get_torrent_filepath(torrent, args)

    if args['magnet'] or not torrent_filepath:
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
