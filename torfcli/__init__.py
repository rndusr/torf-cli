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


def run(args=sys.argv[1:]):
    from . import _config, _errors, _main, _ui

    # Only parse --json, --human and --nohuman so UI can report errors.
    ui = _ui.UI(_config.parse_early_args(args))

    # Parse the rest of the args; report any errors as specified by early args.
    torrent = None
    try:
        ui.cfg = _config.get_cfg(args)
    except (_errors.CliError, _errors.ConfigError) as e:
        ui.error(e)
    else:
        try:
            torrent = _main.run(ui)
        except _errors.Error as e:
            ui.error(e)
        except KeyboardInterrupt:
            ui.error(_errors.Error('Aborted', code=_errors.Code.ABORTED))
    finally:
        ui.terminate(torrent)
