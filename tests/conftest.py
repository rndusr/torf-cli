import contextlib
import functools
import os
import re
from types import GeneratorType
from unittest import mock

import pytest
import torf


@pytest.fixture
def regex():
    # https://kalnytskyi.com/howto/assert-str-matches-regex-in-pytest/
    class _regex:
        def __init__(self, pattern, flags=0, show_groups=False):
            self._regex = re.compile(pattern, flags)
            self._show_groups = show_groups

        def __eq__(self, string):
            match = self._regex.search(string)
            if match is not None and self._show_groups:
                print(match.groups())
                return False
            else:
                return bool(match)

        def __repr__(self):
            return self._regex.pattern
    return _regex


@pytest.fixture(autouse=True)
def change_cwd(tmp_path):
    orig_dir = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        yield
    finally:
        os.chdir(orig_dir)


@pytest.fixture(autouse=True)
def cfgfile(tmp_path, monkeypatch):
    cfgdir = tmp_path / 'configdir'
    cfgdir.mkdir()
    cfgfile = cfgdir / 'config'
    from torfcli import _config
    monkeypatch.setattr(_config, 'DEFAULT_CONFIG_FILE', str(cfgfile))
    return cfgfile


def _assert_torrents_equal(orig, new, path_map=None, ignore=(), **new_attrs, ):
    attrs = ['comment', 'created_by', 'creation_date', 'files', 'filetree',
             'httpseeds', 'name', 'piece_size', 'pieces',
             'private', 'randomize_infohash', 'size', 'source', 'trackers',
             'webseeds']
    for attr in attrs:
        if attr not in new_attrs and attr not in ignore:
            orig_val, new_val = getattr(orig, attr), getattr(new, attr)
            if isinstance(orig_val, GeneratorType):
                orig_val, new_val = tuple(orig_val), tuple(new_val)
            assert orig_val == new_val

    for attr,val in new_attrs.items():
        assert getattr(new, attr) == val

    if path_map:
        for path, exp_value in path_map.items():
            path = list(path)
            value = new.metainfo
            while path:
                key = path.pop(0)
                value = value[key]
            assert value == exp_value


@pytest.fixture
def assert_torrents_equal():
    return _assert_torrents_equal


@pytest.fixture
def human_readable(monkeypatch):
    @contextlib.contextmanager
    def _human_readable(monkeypatch, human_readable):
        from torfcli import _ui
        monkeypatch.setattr(_ui.UI, '_human', lambda self: bool(human_readable))
        yield
    return functools.partial(_human_readable, monkeypatch)


@pytest.fixture
def mock_content(tmp_path):
    base = tmp_path / 'My Torrent'
    base.mkdir()
    file1 = base / 'Something.jpg'
    file2 = base / 'Anotherthing.iso'
    file3 = base / 'Thirdthing.txt'
    for f in (file1, file2, file3):
        f.write_text('some data')
    return base


@pytest.fixture
def mock_create_mode(monkeypatch):
    from torfcli import _main
    mock_create_mode = mock.MagicMock()
    monkeypatch.setattr(_main, '_create_mode', mock_create_mode)
    return mock_create_mode


@contextlib.contextmanager
def _create_torrent(tmp_path, mock_content, **kwargs):
    torrent_file = str(tmp_path / 'test.torrent')
    kw = {'path': str(mock_content),
          'exclude_globs': ['Original', 'exclusions'],
          'trackers': ['http://some.tracker'],
          'webseeds': ['http://some.webseed'],
          'private': False,
          'randomize_infohash': False,
          'comment': 'Original Comment',
          'created_by': 'Original Creator'}
    kw.update(kwargs)
    t = torf.Torrent(**kw)
    t.generate()
    t.write(torrent_file)
    try:
        yield torrent_file
    finally:
        if os.path.exists(torrent_file):
            os.remove(torrent_file)

@pytest.fixture
def create_torrent(tmp_path, mock_content):
    return functools.partial(_create_torrent, tmp_path, mock_content)


ansi_regex = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
erase_line_regex = re.compile(r'^(.*?)\x1b\[2K.*?$', flags=re.MULTILINE)
@pytest.fixture
def clear_ansi():
    def _clear_ansi(string):
        string = erase_line_regex.sub(r'\1', string)
        string = ansi_regex.sub('', string)
        string = re.sub(r'\x1b[78]', '', string)
        string = re.sub(r'(?:\r|^).*\r', '', string, flags=re.MULTILINE)
        return string
    return _clear_ansi

@pytest.fixture
def assert_no_ctrl():
    """Assert string doesn't contain control sequences except for \n and \t"""
    def _assert_no_ctrl(string):
        for c in string:
            assert ord(c) >= 32 or c in ('\n', '\t')
    return _assert_no_ctrl
