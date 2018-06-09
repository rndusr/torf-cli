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
import sys
import time


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
                make_filetree(subtree, parents_is_last=sub_parents_is_last))
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
def bytes2string(b):
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
