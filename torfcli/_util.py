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
import termios
import tty
import io
import sys
import time
import torf
import contextlib


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
def make_filetree(tree, parents_is_last=()):
    lines = []
    items = tuple(tree.items())
    max_i = len(items)-1

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
                    indent += f'  '
                else:
                    indent += f'{_C_DOWN} '

            # If this is the last node, use '└' to stop the line, otherwise
            # branch off with '├'.
            if is_last:
                indent += f'{_C_CORNER}{_C_RIGHT}'
            else:
                indent += f'{_C_DOWN_RIGHT}{_C_RIGHT}'

        if isinstance(node, torf.Torrent.File):
            lines.append(f'{indent}{name} [{bytes2string(node.size, include_bytes=True)}]')
        else:
            lines.append(f'{indent}{name}')
            # Descend into child node
            sub_parents_is_last = parents_is_last + (is_last,)
            lines.extend(
                make_filetree(node, parents_is_last=sub_parents_is_last))

    return lines


def progress_bar(text, fraction_done, width=80):
    if len(text) > width:
        half = int(width/2)
        text = text[:half] + '…' + text[-(width-half-1):]
    elif len(text) < width:
        text += ' ' * (width - len(text))
    assert len(text) == width, f'len({text!r}) != {width}'
    pos = int(fraction_done * width)
    bar = ('\x1b[K'   +  # Erase line
           '\x1b[4m'  +  # Reverse video on
           text[:pos] +
           '\x1b[0m'  +  # Reverse video off
           text[pos:])
    return "▕" + bar + "▏"


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
def bytes2string(b, include_bytes=False):
    string = str(b)
    prefix = ''
    for minval,_prefix in _PREFIXES:
        if b >= minval:
            prefix = _prefix
            string = f'{b/minval:.02f}'
            # Remove trailing zeros after the point
            while string[-1] == '0':
                string = string[:-1]
            if string[-1] == '.':
                string = string[:-1]
            break
    if include_bytes and prefix:
        return f'{string} {prefix}B / {b:,} B'
    else:
        return f'{string} {prefix}B'


_ANSWERS = {'y': True, 'n': False,
            'Y': True, 'N': False,
            '\x03': False,  # ctrl-c
            '\x07': False,  # ctrl-g
            '\x1b': False}  # escape
def ask_yes_no(question, cfg, default='n'):
    if not human_readable(cfg):
        return _ANSWERS.get(default)

    while True:
        print(question, end=' [y|n] ', flush=True)
        key = getch()
        clear_line(cfg)
        answer = _ANSWERS.get(key, None)
        if answer is not None:
            return answer


def human_readable(cfg):
    if cfg['nohuman']:
        return False
    elif cfg['human']:
        return True
    else:
        return sys.stdout.isatty()


@contextlib.contextmanager
def disabled_echo(cfg):
    if human_readable(cfg):
        try:
            # Disable echo
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            new = termios.tcgetattr(fd)
            new[3] = new[3] & ~termios.ECHO  # lflags
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            # Hide cursor
            print('\x1b[?25l', end='')
            try:
                yield
            finally:
                # Enable echo
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                # Show cursor
                print('\x1b[?25h', end='')
        except io.UnsupportedOperation:
            yield
    else:
        yield


def clear_line(cfg):
    if human_readable(cfg):
        print('\x1b[2K\x1b[0E', end='', flush=True)


def getch():
    enable_raw_mode()
    key = sys.stdin.read(1)
    disable_raw_mode()
    return key


_old_term_settings = None
def enable_raw_mode():
    global _old_term_settings
    _old_term_settings = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())


def disable_raw_mode():
    if _old_term_settings is not None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _old_term_settings)
