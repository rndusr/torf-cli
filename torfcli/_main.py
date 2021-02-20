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
import os.path

import torf

from . import _config, _errors, _utils, _vars

# Seconds between progress updates
PROGRESS_INTERVAL = 0.5


def run(ui):
    cfg = ui.cfg
    if cfg['help']:
        print(_config.HELP_TEXT)
    elif cfg['version']:
        print(_config.VERSION_TEXT)
    else:
        # Figure out our modus operandi
        if cfg['PATH'] and not cfg['in']:
            return _create_mode(ui, cfg)
        elif cfg['in'] and (
                # Create new torrent file
                cfg['out']
                # Create new magnet URI
                or cfg['name'] or cfg['tracker'] or cfg['webseed']
                or cfg['notracker'] or cfg['nowebseed']
        ):
            return _edit_mode(ui, cfg)
        elif not cfg['PATH'] and not cfg['out'] and cfg['in']:
            return _info_mode(ui, cfg)
        elif cfg['PATH'] and not cfg['out'] and cfg['in']:
            return _verify_mode(ui, cfg)
        else:
            raise _errors.CliError(f'Not sure what to do (see USAGE in `{_vars.__appname__} -h`)')


def _info_mode(ui, cfg):
    torrent = _utils.get_torrent(cfg, ui)
    ui.show_torrent(torrent)
    if not _utils.is_magnet(cfg['in']):
        try:
            ui.info('Magnet', torrent.magnet())
        except torf.TorfError as e:
            if cfg['validate']:
                raise _errors.Error(e)
            else:
                ui.warn(_errors.Error(e))
    return torrent

def _create_mode(ui, cfg):
    trackers = [tier.split(',') for tier in cfg['tracker']]
    try:
        torrent = torf.Torrent(
            path=cfg['PATH'],
            name=cfg['name'] or None,
            exclude_globs=cfg['exclude'],
            exclude_regexs=cfg['exclude_regex'],
            include_globs=cfg['include'],
            include_regexs=cfg['include_regex'],
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

    ui.check_output_file_exists(_utils.get_torrent_filepath(torrent, cfg))
    ui.show_torrent(torrent)
    _hash_pieces(ui, torrent, threads=cfg['threads'])
    _write_torrent(ui, torrent, cfg)
    return torrent

def _edit_mode(ui, cfg):
    torrent = _utils.get_torrent(cfg, ui)

    # Make sure we can write before we start editing
    ui.check_output_file_exists(_utils.get_torrent_filepath(torrent, cfg))

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
        list_set_or_remove('exclude_regex', 'exclude_regexs')
        list_set_or_remove('include', 'include_globs')
        list_set_or_remove('include_regex', 'include_regexs')
        try:
            torrent.path = cfg['PATH']
        except torf.TorfError as e:
            raise _errors.Error(e)
        else:
            # Setting torrent.path overwrites torrent.name, so we must set any
            # custom name after setting path
            if cfg['name']:
                torrent.name = cfg['name']
            ui.show_torrent(torrent)
            _hash_pieces(ui, torrent)
    else:
        if cfg['name']:
            torrent.name = cfg['name']
        ui.show_torrent(torrent)
    _write_torrent(ui, torrent, cfg)
    return torrent

def _verify_mode(ui, cfg):
    torrent = _utils.get_torrent(cfg, ui)
    ui.show_torrent(torrent)
    ui.info('Path', cfg['PATH'])
    try:
        ui.info('Info Hash', torrent.infohash)
    except torf.TorfError as e:
        raise _errors.Error(e)

    with ui.StatusReporter() as sr:
        skip_files = cfg['verbose'] > 0
        try:
            path = cfg['PATH']
            if path[-1] == os.path.sep:
                path = os.path.join(path, torrent.metainfo['info'].get('name', ''))
            success = torrent.verify(path,
                                     callback=sr.verify_callback,
                                     interval=PROGRESS_INTERVAL,
                                     skip_on_error=skip_files)
        except torf.TorfError as e:
            raise _errors.Error(e)
        except KeyboardInterrupt:
            sr.keep_progress()
            raise
        else:
            sr.keep_progress_summary()
            if not success:
                raise _errors.VerifyError(content=cfg['PATH'], torrent=cfg['in'])
    return torrent

def _hash_pieces(ui, torrent, threads=0):
    with ui.StatusReporter() as sr:
        try:
            success = torrent.generate(callback=sr.generate_callback,
                                       interval=PROGRESS_INTERVAL,
                                       threads=threads or None)
        except torf.TorfError as e:
            raise _errors.Error(e)
        except KeyboardInterrupt:
            sr.keep_progress()
            raise
        else:
            sr.keep_progress_summary()
            if success:
                try:
                    ui.info('Info Hash', torrent.infohash)
                except torf.TorfError as e:
                    raise _errors.Error(e)

def _write_torrent(ui, torrent, cfg):
    try:
        torrent.validate()
    except torf.TorfError as e:
        if cfg['notorrent']:
            # Not writing torrent file; do not fail because,
            # e.g., magnet URI lacks ['info']
            pass
        elif cfg['validate']:
            # Croak with validation error
            raise _errors.Error(e)
        else:
            # Report validation error but write torrent/magnet anyway
            ui.warn(_errors.Error(e))

    if not cfg['nomagnet']:
        try:
            ui.info('Magnet', torrent.magnet())
        except torf.TorfError:
            # Error was already reported
            pass

    if not cfg['notorrent']:
        filepath = _utils.get_torrent_filepath(torrent, cfg)
        try:
            torrent.write(filepath, overwrite=True, validate=cfg['validate'])
        except torf.WriteError as e:
            # Errors other than WriteError should already be reported by
            # torrent.validate() above
            raise _errors.Error(e)
        else:
            ui.info('Torrent', filepath)

    if torrent.private and not torrent.trackers:
        ui.warn('Torrent is private and has no trackers')
