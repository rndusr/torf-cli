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

import os
import errno


class MainError(Exception):
    def __init__(self, msg=None, errno=None):
        self.errno = errno
        if msg is None:
            if errno is None:
                raise RuntimeError('Both msg and errno are missing!')
            msg = os.strerror(errno)
        super().__init__(msg)


class CLIError(MainError):
    def __init__(self, msg=None):
        super().__init__(msg, errno=errno.EINVAL)


class ConfigError(MainError):
    pass
