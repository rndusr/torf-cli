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
import tty, termios
import time
import datetime

from . import __vars__ as _vars

_DEFAULT_CREATOR = f'{_vars.__appname__}/{_vars.__version__}'
_VERSION_INFO = f'{_vars.__appname__} {_vars.__version__} <{_vars.__url__}>'
_HELP = f"""
{_VERSION_INFO}

USAGE
    torf PATH [OPTIONS] [-o FILE]
    torf -i FILE
    torf -i FILE [OPTIONS] -o FILE

ARGUMENTS
    --help,-h              Show this help screen and exit
    --version              Show version information and exit

    PATH                   Path to torrent's content
    --exclude, -e EXCLUDE  Files from PATH to exclude (see below)
                           (may be given multiple times)
    --in, -i FILE          Read metainfo from torrent FILE
    --out, -o FILE         Write metainfo to torrent FILE
                           (defaults to NAME.torrent when creating new torrent)
    --yes, -y              Overwrite FILE without asking
    --magnet, -m           Create magnet link

    --name, -n NAME        Torrent name (defaults to basename of PATH)
    --tracker, -t TRACKER  Announce URL (may be given multiple times)
    --webseed, -w WEBSEED  Webseed URL (BEP19) (may be given multiple times)
    --private, -p          Only use tracker(s) for peer discovery (no DHT/PEX)
    --xseed, -x            Randomize info hash to help with cross-seeding
                           (internally, this adds a random integer to the
                           'info' section of the torrent)
    --source, -s SOURCE    Source string in the torrent's info
    --date, -d DATE        Creation date as YYYY-MM-DD[ HH:MM[:SS]], 'now' for
                           current local time or 'today' for current local time
                           at midnight
                           (defaults to 'today' when creating new torrent)
    --comment, -c COMMENT  Comment that is stored in the torrent file

    --notracker, -T        Remove any trackers from existing torrent
    --nowebseed, -W        Remove any webseeds from existing torrent
    --noprivate, -P        Make existing torrent public
    --noxseed, -X          De-randomize info hash of existing torrent
    --nosource, -S         Remove source string from existing torrent
    --nodate, -D           Remove date from existing torrent
    --nocomment, -C        Remove comment from existing torrent

    NOTE: Options starting with '--no' are only effective when editing a torrent
          (i.e. both --in and --out are specified).

EXCLUDING FILES
    The --exclude argument takes a pattern that is matched against file names in
    PATH and matching files are not included in the torrent.  This argument is
    ignored, if PATH is a single file.  Patterns use these special characters:
        *      matches everything
        ?      matches any single character
        [seq]  matches any character in seq
        [!seq] matches any char not in seq
"""


def _help():
    print(_HELP.strip())
    sys.exit(0)

def _version():
    print(_VERSION_INFO)
    sys.exit(0)


def _get_args():
    argp = argparse.ArgumentParser(add_help=False)

    argp.add_argument('--help', '-h', action='store_true')
    argp.add_argument('--version', action='store_true')

    argp.add_argument('PATH', nargs='?')
    argp.add_argument('--exclude', '-e', action='append')
    argp.add_argument('--in', '-i', metavar='FILE')
    argp.add_argument('--out', '-o', metavar='FILE')
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
    argp.add_argument('--source', '-s')
    argp.add_argument('--nosource', '-S', action='store_true')
    argp.add_argument('--date', '-d')
    argp.add_argument('--nodate', '-D', action='store_true')
    argp.add_argument('--comment', '-c')
    argp.add_argument('--nocomment', '-C', action='store_true')

    return vars(argp.parse_args())


def run():
    args = _get_args()
    if args['help']:
        _help()
    elif args['version']:
        _version()

    # Figure out our modus operandi
    if args['in']:
        if args['out'] or args['magnet']:
            mode = 'edit'
        else:
            mode = 'read'
    elif args['PATH']:
        mode = 'create'
    else:
        _error(CLIError(f'Missing PATH or --in argument (see `{_vars.__appname__} -h`)',
                        error_code=errno.EINVAL))

    # Get a Torrent instance from existing file or a fresh one and apply args
    torrent = _get_torrent(args)

    if mode != 'read':
        # Allow magnet-only generation but default to writing torrent file if
        # --magnet is not given
        if args['out'] or not args['magnet']:
            # Get torrent filepath and open it early so we can fail before we went
            # through the time consuming hashing process
            torrent_filepath = _get_torrent_filepath(torrent, args)
            if not torrent_filepath:
                sys.exit(0)
        else:
            torrent_filepath = None

    if mode == 'read':
        _show_torrent_info(torrent)

    elif mode == 'create':
        if torrent.creation_date is None and not args['nodate']:
            torrent.creation_date = _parse_date('today')
        _show_torrent_info(torrent)
        _hash_pieces(torrent, torrent_filepath)
        _write_torrent(torrent, torrent_filepath, magnet=args['magnet'])

    elif mode == 'edit':
        _show_torrent_info(torrent)
        if not torrent.is_ready:
            # PATH was changed
            _hash_pieces(torrent, torrent_filepath)
        _write_torrent(torrent, torrent_filepath, magnet=args['magnet'])

    else:
        raise RuntimeError(f'Unimplemented mode: {mode}')


def _get_torrent(args):
    try:
        # Read metainfo from existing file or create blank Torrent
        if args['in']:
            torrent = torf.Torrent.read(args['in'])
        else:
            torrent = torf.Torrent()

        # Set content file(s) to given PATH
        if args['PATH']:
            torrent.path = args['PATH']

        # Set creation date if user specified one
        try:
            creation_date = _parse_date(args['date'])
        except ValueError as e:
            _error(CLIError(str(e), error_code=errno.EINVAL))

        # Set attributes to given OPTIONS
        for attr,value in (('name',               args['name']),
                           ('exclude',            args['exclude']),
                           ('trackers',           args['tracker']),
                           ('webseeds',           args['webseed']),
                           ('private',            args['private']),
                           ('randomize_infohash', args['xseed']),
                           ('source',             args['source']),
                           ('creation_date',      creation_date),
                           ('comment',            args['comment']),
                           ('created_by',         _DEFAULT_CREATOR)):
            if value:
                setattr(torrent, attr, value)

        # Set attributes to given OPTIONS
        for attr,remove in (('trackers',           args['notracker']),
                            ('webseeds',           args['nowebseed']),
                            ('private',            args['noprivate']),
                            ('randomize_infohash', args['noxseed']),
                            ('source',             args['nosource']),
                            ('creation_date',      args['nodate']),
                            ('comment',            args['nocomment'])):
            if remove:
                setattr(torrent, attr, None)
    except torf.TorfError as e:
        _error(e)
    else:
        return torrent


def _get_torrent_filepath(torrent, args):
    if not args['out']:
        torrent_filepath = torrent.name + '.torrent'
    else:
        torrent_filepath = args['out']

    if os.path.exists(torrent_filepath):
        if os.path.isdir(torrent_filepath):
            _error(CLIError(f'{torrent_filepath}: {strerror(errno.EISDIR)}',
                            error_code=errno.EISDIR))
        elif not args['yes'] and not _ask_yes_no(f'{torrent_filepath}: Overwrite file?'):
            return None
    return torrent_filepath


def _hash_pieces(torrent, torrent_filepath):
    _info('Local Path', torrent.path)

    start_time = time.time()
    progress = Average(samples=5)
    time_left = Average(samples=10)
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
        _clear_line()
        _info('Progress', msg, end='', flush=True)

    canceled = True
    try:
        canceled = not torrent.generate(callback=progress_callback, interval=0.5)
    except torf.TorfError as e:
        _error(e)
    except KeyboardInterrupt:
        print()
        _error(CLIError('Aborted', error_code=errno.ECANCELED))
    finally:
        if not canceled:
            print()
            _info('Info Hash', torrent.infohash)

class Average():
    def __init__(self, samples):
        self.times = []
        self.values = []
        self.samples = samples

    def add(self, value):
        self.times.append(time.time())
        self.values.append(value)
        while len(self.values) > self.samples:
            self.times.pop(0)
            self.values.pop(0)

    @property
    def avg(self):
        return sum(self.values) / len(self.values)


def _write_torrent(torrent, torrent_filepath, magnet=False):
    if magnet:
        _info('Magnet URI', torrent.magnet())

    if torrent_filepath:
        try:
            torrent.write(torrent_filepath, overwrite=True)
        except torf.TorfError as e:
            _error(e)
        else:
            _info('Torrent File', f'{torrent_filepath}')


_INFO_LABEL_WIDTH = 13
def _info(label, value, **kwargs):
    if label:
        print(f'{label.rjust(_INFO_LABEL_WIDTH)}\t{value}', **kwargs)
    else:
        print(f"{''.rjust(_INFO_LABEL_WIDTH)}\t{value}", **kwargs)


def _show_torrent_info(torrent):
    lines = []
    lines.append(('Name', torrent.name))
    if torrent.is_ready:
        lines.append(('Info Hash', torrent.infohash))
    lines.append(('Size', _bytes2string(torrent.size)))
    if torrent.comment:
        lines.append(('Comment', torrent.comment))
    if torrent.creation_date:
        lines.append(('Creation Date', torrent.creation_date.isoformat(sep=' ', timespec='seconds')))
    if torrent.created_by:
        lines.append(('Created By', torrent.created_by))
    if torrent.private:
        lines.append(('Private', 'yes'))

    trackers = []  # List of lines
    if torrent.trackers:
        if all(len(tier) <= 1 for tier in torrent.trackers):
            # One tracker per tier - print tracker per line
            for tier in torrent.trackers:
                if tier:
                    trackers.append(tier[0])
        else:
            # At least one tier has multiple trackers
            for i,tier in enumerate(torrent.trackers, 1):
                if tier:
                    trackers.append(f'Tier #{i}: {tier[0]}')
                    for tracker in tier[1:]:
                        trackers.append(' '*9 + tracker)

    # Prepend 'Trackers' to first line and indent the remaining ones
    if trackers:
        label = 'Tracker' + ('s' if len(trackers) > 1 else '')
        lines.append((label, trackers[0]))
        for line in trackers[1:]:
            lines.append(('', line))

    if torrent.webseeds:
        label = 'Webseed' + ('s' if len(torrent.webseeds) > 1 else '')
        lines.append((label, torrent.webseeds[0]))
        for webseed in torrent.webseeds[1:]:
            lines.append(('', webseed))

    if torrent.httpseeds:
        label = 'HTTP Seed' + ('s' if len(torrent.httpseeds) > 1 else '')
        lines.append((label, torrent.httpseeds[0]))
        for httpseed in torrent.httpseeds[1:]:
            lines.append(('', httpseed))

    if torrent.piece_size:
        lines.append(('Pieces', f'{torrent.pieces} * {_bytes2string(torrent.piece_size)}'))

    lines_files = _make_filetree(torrent.filetree)
    filenum = len(tuple(torrent.files))
    topdir_str = lines_files.pop(0)
    if torrent.exclude:
        topdir_str += f" [excluding: {', '.join(torrent.exclude)}]"
    lines.append((f"{filenum} File{'s' if filenum != 1 else ''}", topdir_str))
    for line in lines_files:
        lines.append(('', line))

    for label,value in lines:
        _info(label, value)

def _show_extended_torrent_info(torrent):
    # Show non-standard values
    standard_keys = ('info', 'announce', 'announce-list', 'creation date',
                     'created by', 'comment', 'encoding', 'url-list', 'httpseeds')
    for key,value in torrent.metainfo.items():
        if key not in standard_keys:
            lines.append((key, value))

    for label,value in lines:
        _info(label, value)


_C_DOWN       = '\u2502'  # │
_C_DOWN_RIGHT = '\u251C'  # ├
_C_RIGHT      = '\u2500'  # ─
_C_CORNER     = '\u2514'  # └
def _make_filetree(tree, parents_is_last=()):
    lines = []
    items = tuple(tree.items())
    max_i = len(items)-1

    for i,(name,subtree) in enumerate(items):
        is_last = i >= max_i

        # Assemble indentation string (`parents_is_last` being empty means
        # this is the top node)
        indent = ''
        if parents_is_last:
            # `parents_is_last` holds the `is_last` values of our ancestors.
            # This lets us construct the correct indentation string: For
            # each parent, if it has any siblings below it in the directory,
            # print a vertical bar ('|') that leads to the siblings.
            # Otherwise the indentation string for that parent is empty.
            # We ignore the first/top/root node because it isn't indented.
            for parent_is_last in parents_is_last[1:]:
                if parent_is_last:
                    indent += f'  '
                else:
                    indent += f'{_C_DOWN} '

            # If this is the last node, use '└' to stop the line, otherwise
            # branch off with '├'.
            if is_last:
                indent += f'{_C_CORNER}{_C_RIGHT}'
            else:
                indent += f'{_C_DOWN_RIGHT}{_C_RIGHT}'

        lines.append(f'{indent}{name}')

        if subtree is not None:
            # Descend into child node
            sub_parents_is_last = parents_is_last + (is_last,)
            lines.extend(
                _make_filetree(subtree, parents_is_last=sub_parents_is_last))
    return lines


_DATE_FORMATS = ('%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%dT%H:%M',
                '%Y-%m-%d')
def _parse_date(date_str):
    if date_str == 'now':
        return datetime.datetime.now()
    elif date_str == 'today':
        return datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(date_str, str):
        for f in _DATE_FORMATS:
            try:
                return datetime.datetime.strptime(date_str, f)
            except ValueError:
                pass
        raise ValueError(f'Invalid date: {date_str}')


_PREFIXES = ((1024**4, 'Ti'), (1024**3, 'Gi'), (1024**2, 'Mi'), (1024, 'Ki'))
def _bytes2string(b):
    string = str(b)
    unit = ''
    for minval,_unit in _PREFIXES:
        if b >= minval:
            unit = _unit
            string = f'{b/minval:.02f}'
            # Remove trailing zeros
            while string[-1] in ('0', '.'):
                string = string[:-1]
            break
    return f'{string} {unit}B'


_ANSWERS = {'y': True, 'n': False,
           'Y': True, 'N': False,
           '\x03': False,  # ctrl-c
           '\x07': False,  # ctrl-g
           '\x1b': False}  # escape
def _ask_yes_no(question):
    while True:
        print(question, end=' [y|n] ', flush=True)
        key = _getch()
        _clear_line()
        answer = _ANSWERS.get(key, None)
        if answer is not None:
            return answer


class CLIError(Exception):
    def __init__(self, msg, error_code=1):
        self.errno = error_code
        super().__init__(f'{_vars.__appname__}: {msg}')

def _error(exc):
    print(str(exc), file=sys.stderr)
    if exc.errno > 0:
        sys.exit(exc.errno)


def _clear_line():
    print('\x1b[2K\x1b[1`', end='', flush=True)

_old_term_settings = termios.tcgetattr(sys.stdin.fileno())
def _enable_raw_mode():
    global _old_term_settings
    _old_term_settings = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())

def _disable_raw_mode():
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _old_term_settings)

def _getch():
    _enable_raw_mode()
    key = sys.stdin.read(1)
    _disable_raw_mode()
    return key

