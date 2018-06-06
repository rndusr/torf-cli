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
import sys
import os
import errno
import time
import datetime
from collections import abc

from . import _vars
from . import _config
from . import _util
from ._errors import MainError, CLIError


def run(args=sys.argv[1:]):
    cfg = _config.get_cfg(args)

    if cfg['help']:
        print(_config.HELP_TEXT)
    elif cfg['version']:
        print(_config.VERSION_TEXT)
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
            raise CLIError(f'Missing PATH or --in (see `{_vars.__appname__} -h`)')


def _info_mode(cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise MainError(e, errno=e.errno)
    else:
        _show_torrent_info(torrent)


def _create_mode(cfg):
    try:
        torrent = torf.Torrent(
            path=cfg['PATH'],
            name=cfg['name'] or None,
            exclude=cfg['exclude'],
            trackers=() if cfg['notracker'] else cfg['tracker'],
            webseeds=() if cfg['nowebseed'] else cfg['webseed'],
            private=False if cfg['noprivate'] else cfg['private'],
            randomize_infohash=False if cfg['noxseed'] else cfg['xseed'],
            comment=None if cfg['nocomment'] else cfg['comment'],
            created_by=None if cfg['nocreator'] else _config.DEFAULT_CREATOR
        )
    except torf.TorfError as e:
        raise MainError(e, errno=e.errno)

    if not cfg['nodate']:
        try:
            torrent.creation_date = _util.parse_date(cfg['date'] or 'today')
        except ValueError:
            raise MainError(f'{cfg["date"]}: Invalid date', errno=errno.EINVAL)

    _check_output_file_exists(torrent, cfg)
    _show_torrent_info(torrent)
    _hash_pieces(torrent)
    _write_torrent(torrent, cfg)


def _edit_mode(cfg):
    # Read existing torrent
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise MainError(e, errno=e.errno)

    _check_output_file_exists(torrent, cfg)

    def set_or_remove(arg_name, attr_name):
        if cfg.get('no' + arg_name):
            setattr(torrent, attr_name, None)
        elif cfg[arg_name]:
            try:
                setattr(torrent, attr_name, cfg[arg_name])
            except torf.TorfError as e:
                raise MainError(e, errno=e.errno)

    set_or_remove('comment', 'comment')
    set_or_remove('private', 'private')
    set_or_remove('xseed', 'randomize_infohash')

    def list_set_or_remove(arg_name, attr_name):
        if cfg.get('no' + arg_name):
            setattr(torrent, attr_name, None)
        if cfg[arg_name]:
            old_list = getattr(torrent, attr_name) or []
            new_list = old_list + cfg[arg_name]
            try:
                setattr(torrent, attr_name, new_list)
            except torf.TorfError as e:
                raise MainError(e, errno=e.errno)

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
            raise MainError(f'{cfg["date"]}: Invalid date', errno=errno.EINVAL)

    if cfg['PATH']:
        list_set_or_remove('exclude', 'exclude')
        try:
            torrent.path = cfg['PATH']
        except torf.TorfError as e:
            raise MainError(e, errno=e.errno)
        else:
            _hash_pieces(torrent)

    # Setting torrent.path overwrites torrent.name, so it's important to do that
    # after hashing
    if cfg['name']:
        torrent.name = cfg['name']

    # Output file may have appeared while we were hashing; better check again
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
            raise MainError(f'{torrent_filepath}: {os.strerror(errno.EISDIR)}',
                            errno=errno.EISDIR)
        elif not cfg['yes'] and not _util.ask_yes_no(f'{torrent_filepath}: Overwrite file?', default='n'):
            raise MainError(f'{torrent_filepath}: {os.strerror(errno.EEXIST)}',
                            errno=errno.EEXIST)


def _write_torrent(torrent, cfg):
    torrent_filepath = _get_torrent_filepath(torrent, cfg)

    if cfg['magnet'] or not torrent_filepath:
        _info('Magnet URI', torrent.magnet())

    if torrent_filepath:
        try:
            torrent.write(torrent_filepath, overwrite=True)
        except torf.TorfError as e:
            raise MainError(e, errno=e.errno)
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
        raise MainError(e, errno=e.errno)
    except KeyboardInterrupt:
        raise MainError('Aborted', errno=errno.ECANCELED)
    finally:
        if not canceled:
            _info('Info Hash', torrent.infohash)
