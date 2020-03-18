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
import datetime

import torf
from . import _vars
from . import _config
from . import _ui
from . import _util
from . import _errors

# Seconds between progress updates
PROGRESS_INTERVAL = 0.5


def run(args=sys.argv[1:]):
    cfg = _config.get_cfg(args)

    if cfg['help']:
        print(_config.HELP_TEXT)
    elif cfg['version']:
        print(_config.VERSION_TEXT)
    else:
        # Abstraction layer that formats human/machine readable output
        ui = _ui.UI(cfg)
        # Figure out our modus operandi
        if cfg['PATH'] and not cfg['in']:
            _create_mode(ui, cfg)
        elif not cfg['PATH'] and not cfg['out'] and cfg['in']:
            _info_mode(ui, cfg)
        elif cfg['out'] and cfg['in']:
            _edit_mode(ui, cfg)
        elif cfg['PATH'] and not cfg['out'] and cfg['in']:
            _verify_mode(ui, cfg)
        else:
            raise _errors.CliError(f'Not sure what to do (see USAGE in `{_vars.__appname__} -h`)')

def _info_mode(ui, cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise _errors.Error(e)
    else:
        ui.show_torrent_info(torrent)

def _create_mode(ui, cfg):
    trackers = [tier.split(',') for tier in cfg['tracker']]
    try:
        torrent = torf.Torrent(
            path=cfg['PATH'],
            name=cfg['name'] or None,
            exclude_globs=cfg['exclude'],
            trackers=() if cfg['notracker'] else trackers,
            webseeds=() if cfg['nowebseed'] else cfg['webseed'],
            private=False if cfg['noprivate'] else cfg['private'],
            source=None if cfg['nosource'] or not cfg['source'] else cfg['source'],
            randomize_infohash=False if cfg['noxseed'] else cfg['xseed'],
            comment=None if cfg['nocomment'] else cfg['comment'],
            created_by=None if cfg['nocreator'] else _config.DEFAULT_CREATOR
        )
    except torf.TorfError as e:
        raise _errors.Error(e)

    if cfg['nodate']:
        torrent.creation_date = None
    elif cfg['date']:
        torrent.creation_date = cfg['date']
    else:
        torrent.creation_date = datetime.datetime.now()

    if cfg['max_piece_size']:
        torrent.piece_size = cfg['max_piece_size']

    ui.check_output_file_exists(_util.get_torrent_filepath(torrent, cfg))
    ui.show_torrent_info(torrent)
    _hash_pieces(ui, torrent)
    _write_torrent(ui, torrent, cfg)

def _edit_mode(ui, cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise _errors.Error(e)

    # Make sure we can write before we start editing
    ui.check_output_file_exists(_util.get_torrent_filepath(torrent, cfg))

    # Make changes according to CLI args
    def set_or_remove(arg_name, attr_name):
        if cfg.get('no' + arg_name):
            setattr(torrent, attr_name, None)
        elif cfg[arg_name]:
            try:
                setattr(torrent, attr_name, cfg[arg_name])
            except torf.TorfError as e:
                raise _errors.Error(e)
    set_or_remove('comment', 'comment')
    set_or_remove('private', 'private')
    set_or_remove('source', 'source')
    set_or_remove('xseed', 'randomize_infohash')

    def list_set_or_remove(arg_name, attr_name, split_values_at=None):
        if cfg.get('no' + arg_name):
            setattr(torrent, attr_name, None)
        if cfg[arg_name]:
            old_list = getattr(torrent, attr_name) or []
            if split_values_at is not None:
                add_list = [tier.split(split_values_at) for tier in cfg[arg_name]]
            else:
                add_list = cfg[arg_name]
            new_list = old_list + add_list
            try:
                setattr(torrent, attr_name, new_list)
            except torf.TorfError as e:
                raise _errors.Error(e)
    list_set_or_remove('tracker', 'trackers', split_values_at=',')
    list_set_or_remove('webseed', 'webseeds')

    if cfg['nocreator']:
        torrent.created_by = None

    if cfg['nodate']:
        torrent.creation_date = None
    elif cfg['date']:
        torrent.creation_date = cfg['date']

    if cfg['PATH']:
        list_set_or_remove('exclude', 'exclude_globs')
        try:
            torrent.path = cfg['PATH']
        except torf.TorfError as e:
            raise _errors.Error(e)
        else:
            # Setting torrent.path overwrites torrent.name, so it's important to
            # do that after
            if cfg['name']:
                torrent.name = cfg['name']
            ui.show_torrent_info(torrent)
            _hash_pieces(ui, torrent)

    if not cfg['PATH']:
        if cfg['name']:
            torrent.name = cfg['name']
        ui.show_torrent_info(torrent)
    _write_torrent(ui, torrent, cfg)

def _verify_mode(ui, cfg):
    try:
        torrent = torf.Torrent.read(cfg['in'])
    except torf.TorfError as e:
        raise _errors.Error(e)
    else:
        ui.show_torrent_info(torrent)
        ui.info('Path', cfg['PATH'])
        ui.info('Info Hash', torrent.infohash)

    success = False
    with ui.StatusReporter() as sr:
        try:
            try:
                success = torrent.verify(cfg['PATH'],
                                         callback=sr.verify_callback,
                                         interval=PROGRESS_INTERVAL)
            except torf.TorfError as e:
                raise _errors.Error(e)
            finally:
                sr.result = sr.SUCCESS if success else sr.FAILURE
            if not success:
                raise _errors.VerifyError(content=cfg["PATH"], torrent=cfg["in"])
        except KeyboardInterrupt:
            sr.result = sr.ABORTED
            raise

def _hash_pieces(ui, torrent):
    success = False
    with ui.StatusReporter() as sr:
        try:
            try:
                success = torrent.generate(callback=sr.generate_callback,
                                           interval=PROGRESS_INTERVAL)
            except torf.TorfError as e:
                raise _errors.Error(e)
            finally:
                sr.result = sr.SUCCESS if success else sr.FAILURE
        except KeyboardInterrupt:
            sr.result = sr.ABORTED
            raise
    if success:
        ui.info('Info Hash', torrent.infohash)

def _write_torrent(ui, torrent, cfg):
    if not torrent.is_ready:
        raise _errors.WriteError('Attempt to write incomplete torrent. '
                                 'Please report this as a bug.')
    if not cfg['nomagnet']:
        ui.info('Magnet', torrent.magnet())
    if not cfg['notorrent']:
        filepath = _util.get_torrent_filepath(torrent, cfg)
        try:
            torrent.write(filepath, overwrite=True)
        except torf.TorfError as e:
            raise _errors.Error(e)
        else:
            ui.info('Torrent', filepath)
