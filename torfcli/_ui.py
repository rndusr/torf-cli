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

import datetime
import os
import shutil
import sys
import textwrap
import time
import types
from collections import abc

import torf

from . import _errors as err
from . import _term, _utils, _vars

LABEL_WIDTH = 11
LABEL_SEPARATOR = '  '
STATUS_SEPARATOR = ' | '

class UI:
    """Universal abstraction layer to allow different UIs"""

    def __init__(self, cfg=None):
        if cfg is not None:
            self.cfg = cfg

    def _human(self):
        if self._cfg.get('nohuman'):
            return False
        elif self._cfg.get('human'):
            return True
        elif sys.stdout.isatty():
            return True
        else:
            return False

    @property
    def cfg(self):
        return self._cfg

    @cfg.setter
    def cfg(self, cfg):
        self._cfg = cfg
        if cfg.get('json'):
            self._fmt = _JSONFormatter(cfg)
        elif cfg.get('metainfo'):
            self._fmt = _MetainfoFormatter(cfg)
        elif self._human():
            self._fmt = _HumanFormatter(cfg)
        else:
            self._fmt = _MachineFormatter(cfg)

    def error(self, exc, exit=True):
        if self._cfg['json']:
            self.info('Error', exc)
        else:
            sys.stderr.write(f'{_vars.__appname__}: {exc}\n')
        if exit:
            sys.exit(getattr(exc, 'exit_code', err.Code.GENERIC))

    def warn(self, msg):
        sys.stderr.write(f'{_vars.__appname__}: WARNING: {msg}\n')

    def info(self, key, value, newline=True):
        return self._fmt.info(key, value, newline=newline)

    def infos(self, pairs):
        return self._fmt.infos(pairs)

    def show_torrent(self, torrent):
        info = self.info
        if torrent.name is not None:
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
        if torrent.private is not None:
            info('Private', self._fmt.private(torrent))
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
        info('File Count', len(torrent.files))
        exclude_patterns = [p for p in torrent.exclude_globs]
        exclude_patterns.extend(r.pattern for r in torrent.exclude_regexs)
        if exclude_patterns:
            info('Exclude', exclude_patterns)
        include_patterns = [p for p in torrent.include_globs]
        include_patterns.extend(r.pattern for r in torrent.include_regexs)
        if include_patterns:
            info('Include', include_patterns)
        info('Files', self._fmt.files(torrent))

    def StatusReporter(self):
        if self._cfg['json'] or self._cfg['metainfo']:
            return _QuietStatusReporter(self)
        elif self._human():
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

    def terminate(self, torrent):
        fmt = getattr(self, '_fmt', None)
        if fmt:
            fmt.terminate(torrent)


class _FormatterBase:
    def __init__(self, cfg):
        self._cfg = cfg

    def webseeds(self, torrent):
        return torrent.webseeds

    def httpseeds(self, torrent):
        return torrent.httpseeds

    def terminate(self, torrent):
        pass

class _HumanFormatter(_FormatterBase):
    def private(self, torrent):
        return 'yes' if torrent.private else 'no'

    def size(self, torrent):
        return _utils.bytes2string(torrent.size, plain_bytes=self._cfg['verbose'] > 0)

    def creation_date(self, torrent):
        return torrent.creation_date.isoformat(sep=' ', timespec='seconds')

    def piece_size(self, torrent):
        return _utils.bytes2string(torrent.piece_size, plain_bytes=self._cfg['verbose'] > 0)

    def files(self, torrent):
        return _utils.make_filetree(torrent.filetree, plain_bytes=self._cfg['verbose'] > 0)

    def comment(self, torrent):
        # Split lines into paragraphs, then wrap each paragraph at max width.
        list_of_lines = tuple(textwrap.wrap(line, width=75) or ['']  # Preserve empty lines
                              for line in torrent.comment.splitlines())
        return tuple(line
                     for lines in list_of_lines
                     for line in lines)

    def trackers(self, torrent):
        lines = []
        if len(torrent.trackers) == 1 and len(torrent.trackers[0]) == 1:
            # Single tracker in single tier - don't bother displaying tiers
            for tier in torrent.trackers:
                if tier:
                    lines.append(tier[0])
        else:
            # Show which tier each tracker belongs to
            tier_label_width = len('Tier :') + len(str(len(torrent.trackers)))
            for i,tier in enumerate(torrent.trackers, 1):
                if tier:
                    lines.append(f'Tier {i}: {tier[0]}')
                    for tracker in tier[1:]:
                        lines.append(' ' * tier_label_width + ' ' + tracker)
        return lines

    def info(self, key, value, newline=True):
        label = key.rjust(LABEL_WIDTH)
        # Show multiple values as indented list
        if not isinstance(value, str) and isinstance(value, abc.Iterable):
            if value:
                # Print one indented value per line
                value_parts = [f'{value[0]}']
                indent = len(label) * ' '
                for item in value[1:]:
                    value_parts.append(f'{indent}{LABEL_SEPARATOR}{item}')
                value = f'{_term.erase_to_eol}\n'.join(value_parts)
            else:
                value = ''
        else:
            value = str(value)
        value += _term.erase_to_eol

        _term.echo('move_pos1')
        if newline:
            sys.stdout.write(f'{label}{LABEL_SEPARATOR}{value}\n')
        else:
            sys.stdout.write(f'{label}{LABEL_SEPARATOR}{value}')
            _utils.flush(sys.stdout)

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
            _utils.flush(sys.stdout)
            key = _term.getch()
            _term.echo('erase_line', 'move_pos1')
            answer = self.DIALOG_YES_NO_ANSWERS.get(key, None)
            if answer is not None:
                return answer

class _MachineFormatter(_FormatterBase):
    def private(self, torrent):
        return 'yes' if torrent.private else 'no'

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
        _utils.flush(sys.stdout)

    def infos(self, pairs):
        for key, value in pairs:
            self.info(key, value)

    def dialog_yes_no(self, *_, **__):
        return False


class _JSONFormatter(_MachineFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._info = {}

    def private(self, torrent):
        return torrent.private

    def files(self, torrent):
        return torrent.files

    def info(self, key, value, newline=None):
        # Join multiple values with a tab character
        if not isinstance(value, str) and isinstance(value, abc.Iterable):
            value = tuple(value)
        if key == 'Error':
            errors = self._info.get(key, [])
            errors.append(value)
            self._info[key] = errors
        else:
            self._info[key] = value

    def terminate(self, torrent):
        sys.stdout.write(_utils.json_dumps(self._info))
        _utils.flush(sys.stdout)


class _MetainfoFormatter(_JSONFormatter):
    def info(self, key, value, newline=None):
        pass

    def terminate(self, torrent):
        if torrent is None:
            mi = {}
        elif self._cfg['verbose'] <= 0:
            # Show only standard fields
            mi = _utils.metainfo(torrent.metainfo, all_fields=False, remove_pieces=True)
        elif self._cfg['verbose'] == 1:
            # Show all fields except for ['info']['pieces']
            mi = _utils.metainfo(torrent.metainfo, all_fields=True, remove_pieces=True)
        elif self._cfg['verbose'] >= 2:
            # Show all fields
            mi = _utils.metainfo(torrent.metainfo, all_fields=True, remove_pieces=False)
        sys.stdout.write(_utils.json_dumps(mi))
        _utils.flush(sys.stdout)


class _StatusReporterBase():
    def __init__(self, ui):
        self._ui = ui
        self._start_time = time.time()
        self._progress = _utils.Average(samples=5)
        self._time_left = _utils.Average(samples=3)
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
        bps_str = f'{_utils.bytes2string(info.bytes_per_sec, trailing_zeros=True)}/s'
        if info.pieces_done < info.pieces_total:
            term_width,_ = shutil.get_terminal_size()
            term_width = min(term_width, 76)
            # Available width minus label ("   Progress  ")
            status_width = term_width - LABEL_WIDTH - len(LABEL_SEPARATOR)
            line1 = self._progress_line1(info.fraction_done, os.path.basename(info.filepath),
                                         perc_str, bps_str, status_width)
            line2 = self._progress_line2(info, status_width)
            return ''.join((_term.save_cursor_pos,
                            _term.erase_to_eol,
                            _term.move_down,
                            line2,
                            _term.restore_cursor_pos,
                            line1))
        else:
            return STATUS_SEPARATOR.join((perc_str, f'{info.time_total} total', bps_str))

    def _progress_line1(self, fraction_done, filename, percent_str, bps_str, status_width):
        progress_bar_width = (status_width - len('99.99 % ') - len(' 999.99 MiB/s') - 1)
        if progress_bar_width >= 10:
            progress_bar = self._progress_bar(filename, fraction_done,
                                              width=progress_bar_width)
            return ' '.join((percent_str, progress_bar, bps_str))
        elif status_width >= 23:
            return STATUS_SEPARATOR.join((percent_str, bps_str))
        else:
            return percent_str

    def _progress_bar(self, text, fraction_done, width):
        text_width = width - 2
        if len(text) > text_width:
            half = int(text_width / 2)
            text = text[:half] + '…' + text[-(text_width - half - 1) :]
        elif len(text) < text_width:
            text += ' ' * (text_width - len(text))
        pos = int(fraction_done * text_width)
        return ''.join(('▕', _term.reverse_on, text[:pos], _term.reverse_off, text[pos:], '▏'))

    def _progress_line2(self, info, status_width):
        items = {'elapsed' : f'{info.time_elapsed} elapsed',
                 'left'    : f'{info.time_left} left',
                 'total'   : f'{info.time_total} total',
                 'eta'     : f'ETA: {"{0:%H}:{0:%M}:{0:%S}".format(info.eta)}'}
        priority = iter(('left', 'total', 'elapsed', 'eta'))
        order = ('elapsed', 'left', 'total', 'eta')
        parts = []
        priority = iter(priority)
        while True:
            try:
                name = next(priority)
            except StopIteration:
                break
            position = order.index(name)
            part = items[name]
            parts.insert(position, part)
            if len(STATUS_SEPARATOR.join(parts)) > status_width:
                # Always keep at least the time left to completion, even if it
                # looks ugly
                if len(parts) > 1:
                    del parts[parts.index(part)]
                break

        line = STATUS_SEPARATOR.join(parts)
        if len(line) < status_width:
            # Remove any garbage that might still be there from previous draw
            # when terminal was wider
            return line + _term.erase_to_eol
        else:
            return line

    def _format_error(self, exception, torrent):
        if isinstance(exception, torf.VerifyContentError) and len(exception.files) > 1:
            lines = [f'Corruption in piece {exception.piece_index + 1}, '
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
        if isinstance(exception, torf.VerifyContentError) and len(exception.files) > 1:
            lines = [f'Corruption in piece {exception.piece_index + 1}, '
                     f'at least one of these files is corrupt:']
            lines.extend(exception.files)
            return lines
        else:
            return str(exception)

class _QuietStatusReporter(_MachineStatusReporter):
    def generate_callback(self, torrent, filepath, pieces_done, pieces_total):
        pass

    def verify_callback(self, torrent, filepath, pieces_done, pieces_total,
                        piece_index, piece_hash, exception):
        if exception:
            self._ui.info('Error', self._format_error(exception, torrent))
