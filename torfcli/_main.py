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
import textwrap
import itertools
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
            if cfg['out']:
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
        _show_torrent_info(torrent, cfg)
        if not cfg['nomagnet']:
            _info('Magnet', torrent.magnet(), _util.human_readable(cfg))


def _create_mode(cfg):
    try:
        torrent = torf.Torrent(
            path=cfg['PATH'],
            name=cfg['name'] or None,
            exclude=cfg['exclude'],
            trackers=() if cfg['notracker'] else cfg['tracker'],
            webseeds=() if cfg['nowebseed'] else cfg['webseed'],
            private=False if cfg['noprivate'] else cfg['private'],
            source=None if cfg['nosource'] or not cfg['source'] else cfg['source'],
            randomize_infohash=False if cfg['noxseed'] else cfg['xseed'],
            comment=None if cfg['nocomment'] else cfg['comment'],
            created_by=None if cfg['nocreator'] else _config.DEFAULT_CREATOR
        )
    except torf.TorfError as e:
        raise MainError(e, errno=e.errno)

    if not cfg['nodate']:
        try:
            torrent.creation_date = _util.parse_date(cfg['date'] or 'now')
        except ValueError:
            raise MainError(f'{cfg["date"]}: Invalid date', errno=errno.EINVAL)

    if cfg['max_piece_size']:
        max_piece_size = cfg['max_piece_size'] * 1048576
        if torrent.piece_size > max_piece_size:
            try:
                torrent.piece_size = max_piece_size
            except torf.PieceSizeError as e:
                raise MainError(e, errno=errno.EINVAL)

    _check_output_file_exists(torrent, cfg)
    _show_torrent_info(torrent, cfg)
    _hash_pieces(torrent, cfg)
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
    set_or_remove('source', 'source')
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
            # Setting torrent.path overwrites torrent.name, so it's important to
            # do that after
            if cfg['name']:
                torrent.name = cfg['name']
            _show_torrent_info(torrent, cfg)
            _hash_pieces(torrent, cfg)

    if not cfg['PATH']:
        if cfg['name']:
            torrent.name = cfg['name']
        _show_torrent_info(torrent, cfg)
    _write_torrent(torrent, cfg)


def _show_torrent_info(torrent, cfg):
    human_readable = _util.human_readable(cfg)
    lines = []
    lines.append(('Name', torrent.name))
    if torrent.is_ready:
        lines.append(('Info Hash', torrent.infohash))
    size = _util.bytes2string(torrent.size) if human_readable else torrent.size
    lines.append(('Size', size))
    if torrent.comment:
        if human_readable:
            # Split lines into paragraphs, then wrap each paragraph at max
            # width. chain() is used to flatten the resulting list of lists.
            comment = tuple(itertools.chain(*(
                textwrap.wrap(line, width=75) or [''] # Preserve empty lines
                for line in torrent.comment.splitlines())))
        else:
            comment = torrent.comment.splitlines()
        lines.append(('Comment', comment))

    if torrent.creation_date:
        lines.append(('Created', torrent.creation_date.isoformat(sep=' ', timespec='seconds')))
    if torrent.created_by:
        lines.append(('Created By', torrent.created_by))
    if torrent.source:
        lines.append(('Source', torrent.source))
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
            if human_readable:
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
        piece_size = _util.bytes2string(torrent.piece_size) if human_readable else torrent.piece_size
        lines.append(('Piece Size', piece_size))
    if torrent.piece_size:
        lines.append(('Piece Count', torrent.pieces))

    files = tuple(torrent.files)
    lines.append(('File Count', len(files)))
    if torrent.exclude:
        lines.append(('Exclude', torrent.exclude))
    if human_readable:
        lines.append(('Files', _util.make_filetree(torrent.filetree)))
    else:
        lines.append(('Files', files))

    for label,value in lines:
        _info(label, value, human_readable)


_INFO_LABEL_WIDTH = 11
def _info(label, value, human_readable, newline=True):
    if human_readable:
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
    if cfg['out']:
        # User-given torrent file path
        return cfg['out']
    else:
        # Default to torrent's name in cwd
        return torrent.name + '.torrent'


def _check_output_file_exists(torrent, cfg):
    if not cfg['notorrent']:
        torrent_filepath = _get_torrent_filepath(torrent, cfg)
        if os.path.exists(torrent_filepath):
            if os.path.isdir(torrent_filepath):
                raise MainError(f'{torrent_filepath}: {os.strerror(errno.EISDIR)}',
                                errno=errno.EISDIR)
            elif not cfg['yes'] and not _util.ask_yes_no(f'{torrent_filepath}: Overwrite file?', cfg, default='n'):
                raise MainError(f'{torrent_filepath}: {os.strerror(errno.EEXIST)}',
                                errno=errno.EEXIST)


def _write_torrent(torrent, cfg):
    human_readable = _util.human_readable(cfg)

    if not cfg['nomagnet']:
        _info('Magnet', torrent.magnet(), human_readable)

    if not cfg['notorrent']:
        torrent_filepath = _get_torrent_filepath(torrent, cfg)
        try:
            torrent.write(torrent_filepath, overwrite=True)
        except torf.TorfError as e:
            raise MainError(e, errno=e.errno)
        else:
            _info('Torrent', f'{torrent_filepath}', human_readable)


def _hash_pieces(torrent, cfg):
    human_readable = _util.human_readable(cfg)

    _info('Path', torrent.path, human_readable)

    start_time = time.time()
    progress = _util.Average(samples=5)
    time_left = _util.Average(samples=3)
    def progress_callback(torrent, filepath, pieces_done, pieces_total):
        if human_readable:
            msg = f'{pieces_done / pieces_total * 100:.2f} %'
        else:
            msg = f'{pieces_done / pieces_total * 100}'

        if pieces_done < pieces_total:
            progress.add(pieces_done)
            if len(progress.values) >= 2:
                time_diff = progress.times[-1] - progress.times[0]
                pieces_diff = progress.values[-1] - progress.values[0]
                bytes_diff = pieces_diff * torrent.piece_size
                bytes_per_sec = bytes_diff / time_diff + 0.001  # Prevent ZeroDivisionError
                bytes_left = (pieces_total - pieces_done) * torrent.piece_size
                time_left.add(bytes_left / bytes_per_sec)
                time_left_avg = datetime.timedelta(seconds=int(time_left.avg))
                eta = datetime.datetime.now() + time_left_avg
                if human_readable:
                    eta_str = '{0:%H}:{0:%M}:{0:%S}'.format(eta)
                    msg += f'  |  ETA: {eta_str}  |  {time_left_avg} left  |  {bytes_per_sec/1048576:.2f} MB/s'
                else:
                    msg += f'\t{eta.timestamp():.0f}\t{time_left_avg.total_seconds():.0f}\t{bytes_per_sec:.0f}'
            elif not human_readable:
                # Don't print the first line, which can't contain all fields
                return

        else:
            # Print final line
            total_time_diff = datetime.timedelta(seconds=round(time.time() - start_time))
            bytes_per_sec = torrent.size / (total_time_diff.total_seconds() + 0.001)  # Prevent ZeroDivisionError
            if human_readable:
                msg += f'  |  Time: {total_time_diff}  |  {bytes_per_sec/1045876:.2f} MB/s'
            else:
                msg += f'\t{total_time_diff.total_seconds():.0f}\t{bytes_per_sec:.0f}'
        _util.clear_line(cfg)
        _info('Progress', msg, human_readable, newline=False)
        if not human_readable:
            print('', flush=True)

    canceled = True
    try:
        try:
            canceled = not torrent.generate(callback=progress_callback, interval=0.5)
        finally:
            if human_readable:
                print()
    except torf.TorfError as e:
        raise MainError(e, errno=e.errno)
    finally:
        if not canceled:
            _info('Info Hash', torrent.infohash, human_readable)
