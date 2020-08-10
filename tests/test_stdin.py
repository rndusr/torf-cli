import os
import re
import sys
from unittest.mock import patch

import torf

from torfcli import _errors, _vars, run


def test_reading_valid_torrent_data_from_stdin(capsys, monkeypatch, clear_ansi, create_torrent, regex):
    with create_torrent(name='Foo', comment='Bar.') as torrent_file:
        monkeypatch.setattr(sys, 'stdin', open(torrent_file, 'rb'))
        run(['-i', '-'])
    cap = capsys.readouterr()
    assert clear_ansi(cap.out) == regex(r'^Name\tFoo$', flags=re.MULTILINE)
    assert clear_ansi(cap.out) == regex(r'^Comment\tBar.$', flags=re.MULTILINE)
    assert cap.err == ''

def test_reading_invalid_torrent_data_from_stdin(capsys, tmp_path, monkeypatch, clear_ansi, regex):
    torrent = torf.Torrent(name='Foo', comment='Bar.')
    r, w = os.pipe()
    monkeypatch.setattr(sys, 'stdin', os.fdopen(r))
    os.fdopen(w, 'wb').write(torrent.dump(validate=False))

    with patch('sys.exit') as mock_exit:
        run(['-i', '-'])
    mock_exit.assert_called_once_with(_errors.Code.READ)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f"{_vars.__appname__}: Invalid metainfo: Missing 'piece length' in ['info']\n"

def test_reading_valid_magnet_URI_from_stdin(capsys, monkeypatch, clear_ansi, regex):
    magnet = torf.Magnet('7edbb76b446f87617393537fffa48af733cb4127', dn='Foo', xl=12345)
    r, w = os.pipe()
    monkeypatch.setattr(sys, 'stdin', os.fdopen(r))
    os.fdopen(w, 'wb').write(str(magnet).encode('utf-8'))

    run(['-i', '-'])
    cap = capsys.readouterr()
    assert clear_ansi(cap.out) == regex(r'^Name\tFoo$', flags=re.MULTILINE)
    assert clear_ansi(cap.out) == regex(r'^Size\t12345$', flags=re.MULTILINE)
    assert cap.err == ''

def test_reading_invalid_magnet_URI_from_stdin(capsys, monkeypatch, clear_ansi, create_torrent, regex):
    magnet = 'magnet:?xt=urn:btih:7edbb76b446f87617393537fffa48af733cb4127&dn=Foo&xl=one+million+things'
    r, w = os.pipe()
    monkeypatch.setattr(sys, 'stdin', os.fdopen(r))
    os.fdopen(w, 'wb').write(magnet.encode('utf-8'))

    with patch('sys.exit') as mock_exit:
        run(['-i', '-'])
    mock_exit.assert_called_once_with(_errors.Code.READ)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: one million things: Invalid exact length ("xl")\n'
