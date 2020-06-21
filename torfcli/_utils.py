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

import base64
import contextlib
import datetime
import io
import json
import os
import sys
import time
from collections import abc

import torf

from . import _errors


def get_torrent(cfg, ui):
    """
    Read --in parameter and return torf.Torrent instance

    The --in parameter may be the path to a torrent file, a magnet URI or "-".
    If "-", stdin is read and interpreted as the content of a torrent file or a
    magnet URI.
    """
    # Create torf.Torrent instance from INPUT
    if not cfg['in']:
        raise RuntimeError('--in option not given; mode detection is probably kaput')

    def get_torrent_from_magnet(string, fallback_exc):
        # Parse magnet URI from stdin
        try:
            magnet = torf.Magnet.from_string(string)
        except torf.TorfError as exc:
            # Raise magnet parsing error if INPUT looks like magnet URI,
            # torrent parsing error otherwise.
            if string.startswith('magnet:'):
                raise _errors.Error(exc)
            else:
                raise _errors.Error(fallback_exc)
        else:
            # Get "info" section (files, sizes, etc) unless the user is not
            # interested in a complete torrent, e.g. when editing a magnet URI
            if not cfg['notorrent']:
                def callback(exc):
                    ui.error(_errors.Error(exc), exit=False)
                magnet.get_info(callback=callback)
            torrent = magnet.torrent()
            torrent.created_by = None
            return torrent

    if cfg['in'] == '-' and not os.path.exists('-'):
        data = os.read(sys.stdin.fileno(), torf.Torrent.MAX_TORRENT_FILE_SIZE)
        try:
            # Read torrent data from stdin
            return torf.Torrent.read_stream(io.BytesIO(data), validate=cfg['validate'])
        except torf.TorfError as exc:
            # Parse magnet URI from stdin
            return get_torrent_from_magnet(data.decode('utf-8'), exc)
    else:
        try:
            # Read torrent data from file path
            return torf.Torrent.read(cfg['in'], validate=cfg['validate'])
        except torf.TorfError as exc:
            # Parse magnet URI from string
            return get_torrent_from_magnet(cfg['in'], exc)


def get_torrent_filepath(torrent, cfg):
    """Return the file path of the output torrent file"""
    if cfg['out']:
        # User-given torrent file path
        return cfg['out']
    else:
        # Default to torrent's name in cwd
        return torrent.name + '.torrent'


def is_magnet(string):
    return not os.path.exists(string) and string.startswith('magnet:')


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


_C_DOWN       = '\u2502'  # │
_C_DOWN_RIGHT = '\u251C'  # ├
_C_RIGHT      = '\u2500'  # ─
_C_CORNER     = '\u2514'  # └
def make_filetree(tree, parents_is_last=(), plain_bytes=False):
    lines = []
    items = tuple(tree.items())
    max_i = len(items) - 1

    for i,(name,node) in enumerate(items):
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
                    indent += '  '
                else:
                    indent += f'{_C_DOWN} '

            # If this is the last node, use '└' to stop the line, otherwise
            # branch off with '├'.
            if is_last:
                indent += f'{_C_CORNER}{_C_RIGHT}'
            else:
                indent += f'{_C_DOWN_RIGHT}{_C_RIGHT}'

        if isinstance(node, torf.File):
            lines.append(f'{indent}{name} [{bytes2string(node.size, plain_bytes=plain_bytes)}]')
        else:
            lines.append(f'{indent}{name}')
            # Descend into child node
            sub_parents_is_last = parents_is_last + (is_last,)
            lines.extend(make_filetree(node, parents_is_last=sub_parents_is_last,
                                       plain_bytes=plain_bytes))
    return lines


_DATE_FORMATS = ('%Y-%m-%d %H:%M:%S',
                 '%Y-%m-%dT%H:%M:%S',
                 '%Y-%m-%d %H:%M',
                 '%Y-%m-%dT%H:%M',
                 '%Y-%m-%d')
def parse_date(date_str):
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
        raise ValueError('Invalid date')


_PREFIXES = ((1024**4, 'Ti'), (1024**3, 'Gi'), (1024**2, 'Mi'), (1024, 'Ki'))
def bytes2string(b, plain_bytes=False, trailing_zeros=False):
    string = str(b)
    prefix = ''
    for minval,_prefix in _PREFIXES:
        if b >= minval:
            prefix = _prefix
            string = f'{b/minval:.02f}'
            # Remove trailing zeros after the point
            while not trailing_zeros and string[-1] == '0':
                string = string[:-1]
            if not trailing_zeros:
                if string[-1] == '.':
                    string = string[:-1]
            break
    if plain_bytes and prefix:
        return f'{string} {prefix}B / {b:,} B'
    else:
        return f'{string} {prefix}B'


@contextlib.contextmanager
def caught_BrokenPipeError():
    try:
        yield
    except BrokenPipeError:
        # Prevent Python interpreter from printing redundant error message
        # "BrokenPipeError: [Errno 32] Broken pipe" and exit with correct exit
        # code.
        # https://bugs.python.org/issue11380#msg248579
        try:
            sys.stdout.flush()
        finally:
            try:
                sys.stdout.close()
            finally:
                try:
                    sys.stderr.flush()
                finally:
                    sys.stderr.close()
                    sys.exit(0)

def flush(f):
    with caught_BrokenPipeError():
        f.flush()


# torf.Torrent.metainfo stores boolean values (i.e. "private") as True/False
# and JSON converts them to true/false, but bencode doesn't know booleans
# and uses integers (1/0) instead.
def bool2int(obj):
    if isinstance(obj, bool):
        return int(obj)
    elif isinstance(obj, abc.Mapping):
        return {k:bool2int(v) for k,v in obj.items()}
    elif isinstance(obj, abc.Iterable) and not isinstance(obj, (str, bytes, bytearray)):
        return [bool2int(item) for item in obj]
    else:
        return obj

_main_fields = ('announce', 'announce-list', 'comment',
                'created by', 'creation date', 'encoding',
                'info', 'url-list', 'httpseed')
_info_fields = ('files', 'length', 'md5sum', 'name', 'piece length', 'private')
_files_fields = ('length', 'path', 'md5sum')
def metainfo(dct, all_fields=False, remove_pieces=True):
    """
    Return user-friendly copy of metainfo `dct`

    all_fields: Whether to remove any non-standard entries in `dct`
    remove_pieces: Whether to remove ['info']['pieces']
    """

    def copy(obj, only=(), exclude=()):
        if isinstance(obj, abc.Mapping):
            cp = type(obj)()
            for k,v in obj.items():
                if k not in exclude and (not only or k in only):
                    cp[k] = copy(v)
            return cp
        elif isinstance(obj, abc.Iterable) and not isinstance(obj, (str, bytes, bytearray)):
            return [copy(v) for v in obj]
        else:
            return obj

    new = copy(dct)

    if remove_pieces:
        if 'pieces' in new.get('info', {}):
            del new['info']['pieces']

    if not all_fields:
        # Remove non-standard top-level fields
        for k in tuple(new):
            if k not in _main_fields:
                del new[k]

        # Remove non-standard fields in "info" or "info" itself if non-dict
        if 'info' in new:
            if not isinstance(new['info'], dict):
                del new['info']
            else:
                for k in tuple(new['info']):
                    if k not in _info_fields:
                        del new['info'][k]

                if 'files' in new['info'] and isinstance(new['info']['files'], list):
                    for file in new['info']['files']:
                        for k in tuple(file):
                            if k not in _files_fields:
                                del file[k]

    if 'info' in new and not new['info']:
        del new['info']

    return bool2int(new)

def json_dumps(obj):
    def default(obj):
        if isinstance(obj, datetime.datetime):
            return int(obj.timestamp())
        elif isinstance(obj, (bytes, bytearray)):
            return base64.standard_b64encode(obj).decode()
        else:
            return str(obj)
    return json.dumps(obj, allow_nan=False, indent=4, default=default) + '\n'
