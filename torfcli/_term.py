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

import io
import sys
import termios
import tty

# References:
#   https://www.vt100.net/docs/vt100-ug/chapter3.html#DECSCNM
#   http://ascii-table.com/ansi-escape-sequences.php
#   http://ascii-table.com/ansi-escape-sequences-vt-100.php

erase_line         = '\x1b[2K'
erase_to_eol       = '\x1b[K'
reverse_on         = '\x1b[7m'
reverse_off        = '\x1b[0m'
hide_cursor        = '\x1b[?25l'
show_cursor        = '\x1b[?25h'
ensure_line_below  = '\n\x1b[1A'
save_cursor_pos    = '\x1b7'
restore_cursor_pos = '\x1b8'
move_pos1          = '\r'
move_up            = '\x1b[1A'
move_down          = '\x1b[1B'
move_right         = '\x1b[1C'
move_left          = '\x1b[1D'

def echo(*names):
    seqs = ''.join(globals()[name] for name in names)
    print(seqs, end='')

def getch():
    with raw_mode:
        return sys.stdin.read(1)

class _raw_mode():
    _orig_attrs = None

    def enable(self):
        try:
            fd = sys.stdin.fileno()
            self._orig_attrs = termios.tcgetattr(fd)
            tty.setraw(sys.stdin.fileno())
        except io.UnsupportedOperation:
            pass

    def disable(self):
        try:
            if self._orig_attrs is not None:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, self._orig_attrs)
        except io.UnsupportedOperation:
            pass

    def __enter__(self):
        self.enable()

    def __exit__(self, _, __, ___):
        self.disable()

raw_mode = _raw_mode()

class _no_user_input():
    """Disable printing of characters as they are typed and hide cursor"""
    def enable(self):
        try:
            fd = sys.stdin.fileno()
            self._orig_attrs = termios.tcgetattr(fd)
            new = termios.tcgetattr(fd)
            new[3] = new[3] & ~termios.ECHO  # lflags
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            echo('hide_cursor')
        except io.UnsupportedOperation:
            pass

    def disable(self):
        orig_attrs = getattr(self, '_orig_attrs', None)
        if orig_attrs is not None:
            try:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, orig_attrs)
                echo('show_cursor')
            except io.UnsupportedOperation:
                pass

    def __enter__(self):
        self.enable()

    def __exit__(self, _, __, ___):
        self.disable()

no_user_input = _no_user_input()
