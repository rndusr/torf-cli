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
from . import _errors as err


def run(args=sys.argv[1:]):
    cfg = _config.get_cfg(args)

    if cfg['help']:
        print(_config.HELP_TEXT)
    elif cfg['version']:
        print(_config.VERSION_TEXT)
    else:
        # Figure out our modus operandi
        if cfg['PATH'] and not cfg['in']:
            _create_mode(cfg)
        elif not cfg['PATH'] and not cfg['out'] and cfg['in']:
            _info_mode(cfg)
        elif cfg['out'] and cfg['in']:
            _edit_mode(cfg)
        elif cfg['PATH'] and not cfg['out'] and cfg['in']:
            _verify_mode(cfg)
        else:
            raise err.CliError(f'Not sure what to do (see USAGE in `{_vars.__appname__} -h`)')


def _info_mode(cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise err.Error(e)
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
        raise err.Error(e)

    if cfg['nodate']:
        torrent.creation_date = None
    elif cfg['date']:
        torrent.creation_date = cfg['date']
    else:
        torrent.creation_date = datetime.datetime.now()

    if cfg['max_piece_size']:
        torrent.piece_size = cfg['max_piece_size']

    _check_output_file_exists(torrent, cfg)
    _show_torrent_info(torrent, cfg)
    _hash_pieces(torrent, cfg)
    _write_torrent(torrent, cfg)


def _edit_mode(cfg):
    # Read existing torrent
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise err.Error(e)

    _check_output_file_exists(torrent, cfg)

    def set_or_remove(arg_name, attr_name):
        if cfg.get('no' + arg_name):
            setattr(torrent, attr_name, None)
        elif cfg[arg_name]:
            try:
                setattr(torrent, attr_name, cfg[arg_name])
            except torf.TorfError as e:
                raise err.Error(e)

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
                raise err.Error(e)

    list_set_or_remove('tracker', 'trackers')
    list_set_or_remove('webseed', 'webseeds')

    if cfg['nocreator']:
        torrent.created_by = None

    if cfg['nodate']:
        torrent.creation_date = None
    elif cfg['date']:
        torrent.creation_date = cfg['date']

    if cfg['PATH']:
        list_set_or_remove('exclude', 'exclude')
        try:
            torrent.path = cfg['PATH']
        except torf.TorfError as e:
            raise err.Error(e)
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


def _verify_mode(cfg):
    human_readable = _util.human_readable(cfg)

    # Read existing torrent
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise err.Error(e)
    else:
        _show_torrent_info(torrent, cfg)
        _info('Path', torrent.path, human_readable)
        _info('Info Hash', torrent.infohash, human_readable)

    if human_readable:
        status_reporter = HumanStatusReporter()
    else:
        status_reporter = MachineStatusReporter()
    with _util.disabled_echo(cfg):
        success = False
        try:
            success = torrent.verify(cfg['PATH'],
                                     callback=status_reporter.verify_callback,
                                     interval=0.5)
        except torf.TorfError as e:
            raise err.Error(e)
        finally:
            status_reporter.cleanup(success)
    if not success:
        raise err.VerifyError(content=cfg["PATH"], torrent=cfg["in"])


def _show_torrent_info(torrent, cfg):
    human_readable = _util.human_readable(cfg)
    lines = []
    lines.append(('Name', torrent.name))
    if torrent.is_ready:
        lines.append(('Info Hash', torrent.infohash))
    if human_readable:
        size = lines.append(('Size', _util.bytes2string(torrent.size, include_bytes=True)))
    else:
        lines.append(('Size', torrent.size))
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
    if value is None:
        return
    elif human_readable:
        print('\x1b[0E\x1b[2K', end='')
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
        print(f'{label}{sep}{value}', flush=True)
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
                raise err.WriteError(f'{torrent_filepath}: {os.strerror(errno.EISDIR)}')
            elif not cfg['yes'] and not _util.ask_yes_no(f'{torrent_filepath}: Overwrite file?',
                                                         cfg, default='n'):
                raise err.WriteError(f'{torrent_filepath}: {os.strerror(errno.EEXIST)}')


def _write_torrent(torrent, cfg):
    human_readable = _util.human_readable(cfg)

    if not cfg['nomagnet']:
        _info('Magnet', torrent.magnet(), human_readable)

    if not cfg['notorrent']:
        torrent_filepath = _get_torrent_filepath(torrent, cfg)
        try:
            torrent.write(torrent_filepath, overwrite=True)
        except torf.TorfError as e:
            raise err.Error(e)
        else:
            _info('Torrent', f'{torrent_filepath}', human_readable)


def _hash_pieces(torrent, cfg):
    human_readable = _util.human_readable(cfg)
    _info('Path', torrent.path, human_readable)
    if human_readable:
        status_reporter = HumanStatusReporter()
    else:
        status_reporter = MachineStatusReporter()
    with _util.disabled_echo(cfg):
        success = False
        try:
            success = torrent.generate(callback=status_reporter.generate_callback,
                                       interval=0.5)
        except torf.TorfError as e:
            raise err.Error(e)
        finally:
            status_reporter.cleanup(success)
            if success:
                _info('Info Hash', torrent.infohash, human_readable)


class StatusReporterBase():
    def __init__(self):
        self._start_time = time.time()
        self._progress = _util.Average(samples=5)
        self._time_left = _util.Average(samples=3)
        self.fraction_done = 0
        self.time_left = datetime.timedelta(0)
        self.time_elapsed = datetime.timedelta(0)
        self.time_total = datetime.timedelta(0)
        self.eta = datetime.datetime.now()
        self.bytes_per_sec = 0

    def cleanup(self, success):
        pass

    def generate_callback(self, torrent, filepath, pieces_done, pieces_total):
        info = self._get_progress_string(torrent, filepath, pieces_done, pieces_total)
        _info('Progress', info, self._human_readable, newline=not self._human_readable)

    def verify_callback(self, torrent, filepath, pieces_done, pieces_total,
                        piece_index, piece_hash, exception):
        if exception:
            _info('Error', str(exception), self._human_readable)
        else:
            info = self._get_progress_string(torrent, filepath, pieces_done, pieces_total)
            _info('Progress', info, self._human_readable, newline=not self._human_readable)

    def _get_progress_string(self, torrent, filepath, pieces_done, pieces_total):
        progress = self._progress
        time_left = self._time_left
        self.fraction_done = pieces_done / pieces_total
        if pieces_done < pieces_total:
            progress.add(pieces_done)
            # Make sure we have enough samples to make estimates
            if len(progress.values) >= 2:
                self.time_elapsed = datetime.timedelta(seconds=round(time.time() - self._start_time))
                time_diff = progress.times[-1] - progress.times[0]
                pieces_diff = progress.values[-1] - progress.values[0]
                bytes_diff = pieces_diff * torrent.piece_size
                self.bytes_per_sec = bytes_diff / time_diff + 0.001  # Prevent ZeroDivisionError
                bytes_left = (pieces_total - pieces_done) * torrent.piece_size
                self._time_left.add(bytes_left / self.bytes_per_sec)
                self.time_left = datetime.timedelta(seconds=round(time_left.avg))
                self.time_total = self.time_elapsed + self.time_left
                self.eta = datetime.datetime.now() + self.time_left
        else:
            # The last piece was hashed
            self.time_left = datetime.timedelta(seconds=0)
            self.time_elapsed = datetime.timedelta(seconds=round(time.time() - self._start_time))
            self.time_total = self.time_elapsed
            self.eta = datetime.datetime.now()
            self.bytes_per_sec = torrent.size / (self.time_total.total_seconds() + 0.001)  # Prevent ZeroDivisionError
        return self._make_progress_string(torrent, filepath, pieces_done, pieces_total)


class HumanStatusReporter(StatusReporterBase):
    """
    References:
      https://www.vt100.net/docs/vt100-ug/chapter3.html#DECSCNM
      http://ascii-table.com/ansi-escape-sequences.php
    """
    _human_readable = True

    def __init__(self):
        super().__init__()
        self._is_initialized = False    # Whether _init() was called
        self._is_cleanedup = False      # Whether cleanup() was called

    def _init(self):
        # Ensure one line below for filename/progress bar
        print('\n\x1b[1A', end='')
        self._is_initialized = True

    def cleanup(self, success):
        if self._is_initialized and not self._is_cleanedup:
            if success:
                # Final "Progress" line is a performance summary, which we keep
                # by moving on to the next line
                print(f'\n', end='')
            else:
                # Keep last progress info intact so the user can see where it
                # stopped
                print('\n\n', end='')
            self._is_cleanedup = True

    def _make_progress_string(self, torrent, filepath, pieces_done, pieces_total):
        if not self._is_initialized:
            self._init()
        msg = f'{self.fraction_done * 100:.2f} %'
        if pieces_done < pieces_total:
            eta_str = '{0:%H}:{0:%M}:{0:%S}'.format(self.eta)
            msg += (f'  |  {self.time_elapsed} elapsed, {self.time_left} left, {self.time_total} total'
                    f'  |  ETA: {eta_str}'
                    f'  |  {self.bytes_per_sec/1045876:.2f} MiB/s')

            # Display current file/progress bar in line below
            progress_bar = _util.progress_bar(os.path.basename(filepath), self.fraction_done)
            msg = ('\x1b7'      # Store cursor position
                   '\x1b[1B' +  # Move one line down
                   progress_bar +
                   '\x1b8'      # Restore cursor position
                   + msg)
        else:
            msg += f'  |  {self.time_total} total  |  {self.bytes_per_sec/1045876:.2f} MiB/s'
        return msg


class MachineStatusReporter(StatusReporterBase):
    _human_readable = False
    def _make_progress_string(self, torrent, filepath, pieces_done, pieces_total):
        return '\t'.join((f'{self.fraction_done * 100:.3f}',
                          f'{round(self.time_elapsed.total_seconds())}',
                          f'{round(self.time_left.total_seconds())}',
                          f'{round(self.time_total.total_seconds())}',
                          f'{round(self.eta.timestamp())}',
                          f'{round(self.bytes_per_sec)}',
                          f'{filepath}'))
