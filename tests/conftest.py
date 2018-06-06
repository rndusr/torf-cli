import pytest
from unittest import mock
import contextlib
import os
import torf
import functools
import shutil
from types import SimpleNamespace, GeneratorType


@pytest.fixture(autouse=True)
def change_cwd(tmpdir):
    os.chdir(str(tmpdir))
    yield
    shutil.rmtree(str(tmpdir))


@pytest.fixture(autouse=True)
def cfgfile(tmpdir, monkeypatch):
    cfgdir = tmpdir.mkdir('configdir')
    cfgfile = cfgdir.join('config')
    from torfcli import _config
    monkeypatch.setattr(_config, 'DEFAULT_CONFIG_FILE', str(cfgfile))
    return cfgfile


def _assert_torrents_equal(orig, new, ignore=(), **new_attrs):
    attrs = ['comment', 'created_by', 'creation_date', 'files', 'filetree',
             'httpseeds', 'include_md5', 'name', 'piece_size', 'pieces',
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

@pytest.fixture
def assert_torrents_equal():
    return _assert_torrents_equal


@contextlib.contextmanager
def _mock_tty(monkeypatch, is_tty):
    from torfcli import _util
    monkeypatch.setattr(_util, 'is_tty', lambda: bool(is_tty))
    yield

@pytest.fixture
def mock_tty(monkeypatch):
    return functools.partial(_mock_tty, monkeypatch)


@pytest.fixture
def mock_content(tmpdir):
    base = tmpdir.mkdir('My Torrent')
    file1 = base.join('Something.jpg')
    file2 = base.join('Anotherthing.iso')
    file3 = base.join('Thirdthing.txt')
    for f in (file1, file2, file3):
        f.write('some data')
    return base


@pytest.fixture
def mock_create_mode(monkeypatch):
    from torfcli import _main
    mock_create_mode = mock.MagicMock()
    monkeypatch.setattr(_main, '_create_mode', mock_create_mode)
    return mock_create_mode


@contextlib.contextmanager
def _create_torrent(tmpdir, mock_content, **kwargs):
    torrent_file = str(tmpdir.join('test.torrent'))
    kw = {'path': str(mock_content),
          'exclude': ['Original', 'exclusions'],
          'trackers': ['http://some.tracker'],
          'webseeds': ['http://some.webseed'],
          'private': False,
          'randomize_infohash': False,
          'comment': 'Original Comment',
          'created_by': 'Original Creator'}
    kw.update(kwargs)
    try:
        t = torf.Torrent(**kw)
        t.generate()
        t.write(torrent_file)
        yield torrent_file
    finally:
        os.remove(torrent_file)

@pytest.fixture
def create_torrent(tmpdir, mock_content):
    return functools.partial(_create_torrent, tmpdir, mock_content)
