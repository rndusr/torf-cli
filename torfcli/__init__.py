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


def run():
    from ._main import run
    from ._errors import MainError
    from ._vars import __appname__
    import sys
    import errno

    try:
        run()

    except MainError as e:
        print(f'{__appname__}: {e}', file=sys.stderr)
        sys.exit(e.errno or 1)

    except KeyboardInterrupt:
        print(f'{__appname__}: Aborted', file=sys.stderr)

        # Close stdout and stderr before the python interpreter tries it outside
        # of our scope, which might fail if a pipe was broken, resuling in an
        # ugly BrokePipeError message.
        # https://stackoverflow.com/a/18954489
        for fd in (sys.stdout, sys.stderr):
            try:
                fd.close()
            except IOError:
                pass
        sys.exit(errno.ECANCELED)
