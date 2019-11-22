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

def run():
    from ._main import run
    from . import _errors
    from ._vars import __appname__

    try:
        run()
    except _errors.Error as e:
        if str(e):
            print(f'{__appname__}: {e}', file=sys.stderr)
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        print(f'{__appname__}: Aborted', file=sys.stderr)
        sys.exit(_errors.Code.ABORTED)
    except BrokenPipeError:
        print(f'{__appname__}: Broken pipe', file=sys.stderr)
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
                    sys.exit(_errors.Code.BROKEN_PIPE)
