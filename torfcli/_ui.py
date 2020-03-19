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

import sys
from collections import abc
import textwrap
import types
import os
import time
import datetime
import torf

from . import _util
from . import _errors as err
from . import _term


class UI:
    """Universal abstraction layer to allow different UIs"""

    def _human(self):
        if self._cfg['nohuman']:
            return False
        elif self._cfg['human']:
            return True
        elif sys.stdout.isatty():
            return True
        else:
            return False

    def __init__(self, cfg):
        self._cfg = cfg
        if self._human():
            self._fmt = _HumanFormatter(cfg)
        else:
            self._fmt = _MachineFormatter(cfg)

    def info(self, *args, **kwargs):
        return self._fmt.info(*args, **kwargs)

    def infos(self, *args, **kwargs):
        return self._fmt.infos(*args, **kwargs)

    def show_torrent_info(self, torrent):
        info = self._fmt.info
        info('Name', torrent.name)
        if torrent.is_ready:
            info('Info Hash', torrent.infohash)
        info('Size', self._fmt.size(torrent))
        if torrent.comment:
            info('Comment', self._fmt.comment(torrent))
        if torrent.creation_date:
            info('Created', self._fmt.creation_date(torrent))
        if torrent.created_by:
            info('Created By', torrent.created_by)
        if torrent.source:
            info('Source', torrent.source)
        info('Private', 'yes' if torrent.private else 'no')
        if not self._cfg['nomagnet'] and torrent.is_ready:
            info('Magnet', torrent.magnet())
        if torrent.trackers:
            info('Tracker' + ('s' if len(torrent.trackers) > 1 else ''),
                 self._fmt.trackers(torrent))
        if torrent.webseeds:
            info('Webseed' + ('s' if len(torrent.webseeds) > 1 else ''),
                 self._fmt.webseeds(torrent))
        if torrent.httpseeds:
            info('HTTP Seed' + ('s' if len(torrent.httpseeds) > 1 else ''),
                 self._fmt.httpseeds(torrent))
        if torrent.piece_size:
            info('Piece Size', self._fmt.piece_size(torrent))
        if torrent.piece_size:
            info('Piece Count', torrent.pieces)
        files = tuple(torrent.files)
        info('File Count', len(files))
        if torrent.exclude_globs:
            info('Exclude', torrent.exclude_globs)
        info('Files', self._fmt.files(torrent))

    def StatusReporter(self):
        if self._human():
            return _HumanStatusReporter(self)
        else:
            return _MachineStatusReporter(self)

    def check_output_file_exists(self, filepath):
        if not self._cfg['notorrent']:
            if os.path.exists(filepath):
                if os.path.isdir(filepath):
                    raise err.WriteError(f'{filepath}: Is a directory')
                elif (not self._cfg['yes'] and
                      not self._fmt.dialog_yes_no(f'{filepath}: Overwrite file?')):
                    raise err.WriteError(f'{filepath}: File exists')


class _FormatterBase:
    def __init__(self, cfg):
        self._cfg = cfg

    def webseeds(self, torrent):
        return torrent.webseeds

    def httpseeds(self, torrent):
        return torrent.httpseeds

class _HumanFormatter(_FormatterBase):
    def size(self, torrent):
        return _util.bytes2string(torrent.size, include_bytes=True)

    def creation_date(self, torrent):
        return torrent.creation_date.isoformat(sep=' ', timespec='seconds')

    def piece_size(self, torrent):
        return _util.bytes2string(torrent.piece_size)

    def files(self, torrent):
        return _util.make_filetree(torrent.filetree)

    def comment(self, torrent):
        # Split lines into paragraphs, then wrap each paragraph at max width.
        list_of_lines = tuple(textwrap.wrap(line, width=75) or [''] # Preserve empty lines
                              for line in torrent.comment.splitlines())
        return tuple(line
                     for lines in list_of_lines
                     for line in lines)

    def trackers(self, torrent):
        lines = []
        if all(len(tier) <= 1 for tier in torrent.trackers):
            # One tracker per tier - don't bother with printing tiers
            for tier in torrent.trackers:
                if tier:
                    lines.append(tier[0])
        else:
            # At least one tier has multiple trackers
            tier_label_width = len('Tier :') + len(str(len(torrent.trackers)))
            for i,tier in enumerate(torrent.trackers, 1):
                if tier:
                    lines.append(f'Tier {i}: {tier[0]}')
                    for tracker in tier[1:]:
                        lines.append(' ' * tier_label_width + ' ' + tracker)
        return lines

    def info(self, key, value, newline=True):
        _term.echo('erase_line', 'move_pos1')
        sep = '  '
        label_width = 11
        label = key.rjust(label_width)
        # Show multiple values as indented list
        if not isinstance(value, str) and isinstance(value, abc.Iterable):
            if value:
                # Print one indented value per line
                value_parts = [f'{value[0]}']
                indent = len(label) * ' '
                for item in value[1:]:
                    value_parts.append(f'{indent}{sep}{item}')
                value = '\n'.join(value_parts)
            else:
                value = ''

        if newline:
            sys.stdout.write(f'{label}{sep}{value}\n')
        else:
            sys.stdout.write(f'{label}{sep}{value}')
            sys.stdout.flush()

    def infos(self, pairs):
        for key, value in pairs:
            self.info(key, value)

    DIALOG_YES_NO_ANSWERS = {'y': True, 'n': False,
                             'Y': True, 'N': False,
                             '\x03': False,  # ctrl-c
                             '\x07': False,  # ctrl-g
                             '\x1b': False}  # escape
    def dialog_yes_no(self, question):
        while True:
            sys.stdout.write(f'{question} [y|n] ')
            sys.stdout.flush()
            key = _term.getch()
            _term.echo('erase_line', 'move_pos1')
            answer = self.DIALOG_YES_NO_ANSWERS.get(key, None)
            if answer is not None:
                return answer

class _MachineFormatter(_FormatterBase):
    def size(self, torrent):
        return int(torrent.size)

    def creation_date(self, torrent):
        return int(torrent.creation_date.timestamp())

    def piece_size(self, torrent):
        return int(torrent.piece_size)

    def files(self, torrent):
        return '\t'.join(str(f) for f in torrent.files)

    def comment(self, torrent):
        return torrent.comment.splitlines()

    def trackers(self, torrent):
        return [url
                for tier in torrent.trackers
                for url in tier]

    def info(self, key, value, newline=None):
        # Join multiple values with a tab character
        if not isinstance(value, str) and isinstance(value, abc.Iterable):
            value = '\t'.join(str(v) for v in value)
        sys.stdout.write(f'{key}\t{value}\n')
        sys.stdout.flush()

    def infos(self, pairs):
        for key, value in pairs:
            self.info(key, value)

    def dialog_yes_no(self, *_, **__):
        return False


class _StatusReporterBase():
    def __init__(self, ui):
        self._ui = ui
        self._start_time = time.time()
        self._progress = _util.Average(samples=5)
        self._time_left = _util.Average(samples=3)
        self._info = types.SimpleNamespace(
            torrent=None, filepath=None,
            pieces_done=0, pieces_total=0,
            fraction_done=0, bytes_per_sec=0,
            time_left=datetime.timedelta(0),
            time_elapsed=datetime.timedelta(0),
            time_total=datetime.timedelta(0),
            eta=datetime.datetime.now() + datetime.timedelta(300))

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        pass

    def keep_progress_summary(self):
        pass

    def keep_progress(self):
        pass

    def generate_callback(self, torrent, filepath, pieces_done, pieces_total):
        self._update_progress_info(torrent, filepath, pieces_done, pieces_total)
        self._ui.info('Progress', self._get_progress_string(self._info), newline=False)

    def verify_callback(self, torrent, filepath, pieces_done, pieces_total,
                        piece_index, piece_hash, exception):
        if exception:
            self._ui.info('Error', self._format_error(exception, torrent))
        self._update_progress_info(torrent, filepath, pieces_done, pieces_total)
        self._ui.info('Progress', self._get_progress_string(self._info), newline=False)

    def _update_progress_info(self, torrent, filepath, pieces_done, pieces_total):
        info = self._info
        info.torrent = torrent
        info.filepath = filepath
        info.pieces_done = pieces_done
        info.pieces_total = pieces_total
        info.fraction_done = pieces_done / pieces_total
        progress = self._progress
        if pieces_done < pieces_total:
            progress.add(pieces_done)
            # Make sure we have enough samples to make estimates
            if len(progress.values) >= 2:
                info.time_elapsed = datetime.timedelta(seconds=round(time.time() - self._start_time))
                time_diff = progress.times[-1] - progress.times[0]
                pieces_diff = progress.values[-1] - progress.values[0]
                bytes_diff = pieces_diff * torrent.piece_size
                info.bytes_per_sec = bytes_diff / time_diff + 0.001  # Prevent ZeroDivisionError
                bytes_left = (pieces_total - pieces_done) * torrent.piece_size
                self._time_left.add(bytes_left / info.bytes_per_sec)
                info.time_left = datetime.timedelta(seconds=round(self._time_left.avg))
                info.time_total = info.time_elapsed + info.time_left
                info.eta = datetime.datetime.now() + info.time_left
        else:
            # The last piece was hashed
            info.time_elapsed = datetime.timedelta(seconds=round(time.time() - self._start_time))
            info.time_total = info.time_elapsed
            info.bytes_per_sec = torrent.size / (info.time_total.total_seconds() + 0.001)  # Prevent ZeroDivisionError
            info.time_left = datetime.timedelta(seconds=0)
            info.eta = datetime.datetime.now()

    def _get_progress_string(self, info):
        return str(info)

class _HumanStatusReporter(_StatusReporterBase):
    def __enter__(self):
        _term.no_user_input.enable()
        _term.echo('ensure_line_below')
        return self

    def keep_progress_summary(self):
        # The first of the final "Progress" lines is a performance summary.
        # Keep the summary but erase the progress bar blow.
        _term.echo('erase_to_eol', 'move_down', 'erase_line', 'move_up')
        sys.stdout.write('\n')

    def keep_progress(self):
        # Keep progress info fully intact so we can see how far it got
        sys.stdout.write('\n\n')

    def __exit__(self, _, __, ___):
        _term.no_user_input.disable()

    def _get_progress_string(self, info):
        perc_str = f'{info.fraction_done * 100:5.2f} %'
        bps_str = f'{info.bytes_per_sec/1045876:6.2f} MiB/s'
        if info.pieces_done < info.pieces_total:
            progress_bar = self._progress_bar(os.path.basename(info.filepath), info.fraction_done, 45)
            first_line = ' '.join((perc_str, progress_bar, bps_str))
            eta_str = '{0:%H}:{0:%M}:{0:%S}'.format(info.eta)
            second_line = (f'{info.time_elapsed} elapsed  |  {info.time_left} left '
                           f' |  {info.time_total} total  |  ETA: {eta_str}')
            return ''.join((_term.save_cursor_pos,
                            _term.erase_to_eol,
                            _term.move_down,
                            second_line,
                            _term.restore_cursor_pos,
                            first_line))
        else:
            return ''.join((f'{perc_str}  |  {info.time_total} total  |  {bps_str}',
                            _term.erase_to_eol))

    def _progress_bar(self, text, fraction_done, width):
        if len(text) > width:
            half = int(width/2)
            text = text[:half] + '…' + text[-(width-half-1):]
        elif len(text) < width:
            text += ' ' * (width - len(text))
        assert len(text) == width, f'len({text!r}) != {width}'
        pos = int(fraction_done * width)
        return ''.join(('▕',
                        _term.reverse_on,
                        text[:pos],
                        _term.reverse_off,
                        text[pos:],
                        '▏'))

    def _format_error(self, exception, torrent):
        if isinstance(exception, torf.VerifyContentError) and len(torrent.files) > 1:
            lines = [f'Corruption in piece {exception.piece_index+1}, '
                     f'at least one of these files is corrupt:']
            for filepath in exception.files:
                lines.append(f'  {filepath}')
            return lines
        else:
            return str(exception)

class _MachineStatusReporter(_StatusReporterBase):
    def _get_progress_string(self, info):
        return '\t'.join((f'{info.fraction_done * 100:.3f}',
                          f'{round(info.time_elapsed.total_seconds())}',
                          f'{round(info.time_left.total_seconds())}',
                          f'{round(info.time_total.total_seconds())}',
                          f'{round(info.eta.timestamp())}',
                          f'{round(info.bytes_per_sec)}',
                          f'{info.filepath}'))

    def _format_error(self, exception, torrent):
        if isinstance(exception, torf.VerifyContentError) and len(torrent.files) > 1:
            lines = [f'Corruption in piece {exception.piece_index+1}, '
                     f'at least one of these files is corrupt:']
            lines.extend(exception.files)
            return lines
        else:
            return str(exception)
