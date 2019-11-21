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

from enum import IntEnum
import torf
from collections import defaultdict


class Code(IntEnum):
    GENERIC     = 1
    CLI         = 2
    CONFIG      = 3
    READ        = 4
    WRITE       = 5
    PARSE       = 6
    VERIFY      = 7
    ABORTED     = 128
    BROKEN_PIPE = 129


class Error(Exception):
    """
    Automatically return the appropriate subclass instance based on error code
    or passed message.

    >>> Error('foo', code=Code.READ)
    ReadError('foo')
    >>> Error(torf.ReadError(errno.ENOENT, 'foo'))
    ReadError('foo: No such file or directory')
    >>> Error(torf.PathEmptyError('foo'))
    ReadError('foo: Empty directory')
    """

    _subclsmap = defaultdict(
        lambda: Code.GENERIC,
        {torf.ReadError               : Code.READ,
         torf.PathNotFoundError       : Code.READ,
         torf.PathEmptyError          : Code.READ,
         torf.WriteError              : Code.WRITE,
         torf.ParseError              : Code.PARSE,
         torf.MetainfoError           : Code.PARSE,
         torf.URLError                : Code.PARSE,
         torf.PieceSizeError          : Code.PARSE,
         torf.VerifyNotDirectoryError : Code.VERIFY,
         torf.VerifyIsDirectoryError  : Code.VERIFY,
         torf.VerifyFileSizeError     : Code.VERIFY,
         torf.VerifyContentError      : Code.VERIFY})

    @classmethod
    def _get_exception_cls(cls, msg, code):
        if code is None:
            # If `msg` is a torf.*Error, translate it into an error code
            code = cls._subclsmap[type(msg)]
        assert code in Code, f'Not an error code: {code}'
        # Translate error code name to exception class
        cls_name = code.name.capitalize() + 'Error'
        try:
            return globals()[cls_name]
        except KeyError:
            return None

    def __new__(cls, msg='Unspecified error', code=None, **kwargs):
        subcls = cls._get_exception_cls(msg, code)
        if subcls is not None:
            self = super(Error, cls).__new__(subcls)
        else:
            self = super().__new__(cls)
        return self

    def __init__(self, msg=None, code=None):
        msg = msg or 'Unspecified error'
        self._exit_code = code or _codes[type(self)]
        super().__init__(str(msg))

    @property
    def exit_code(self):
        return self._exit_code

class CliError(Error):
    def __init__(self, msg, code=None):
        super().__init__(msg, code=Code.CLI)

class ConfigError(Error):
    def __init__(self, msg, code=None):
        super().__init__(msg, code=Code.CONFIG)

class ReadError(Error):
    def __init__(self, msg, code=None):
        super().__init__(msg, code=Code.READ)

class WriteError(Error):
    def __init__(self, msg, code=None):
        super().__init__(msg, code=Code.WRITE)

class ParseError(Error):
    def __init__(self, msg, code=None):
        super().__init__(msg, code=Code.PARSE)

class VerifyError(Error):
    def __init__(self, content=None, code=None, torrent=None):
        if torrent is None:
            # Content is a complete message
            super().__init__(content, code=Code.VERIFY)
        else:
            # Content is a path
            super().__init__(f'{content} does not satisfy {torrent}', code=Code.VERIFY)
