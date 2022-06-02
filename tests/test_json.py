import json
import time
from unittest.mock import patch

import pytest

from torfcli import _errors as err
from torfcli import _vars, run


def test_json_contains_standard_fields(capsys, mock_content):
    now = time.time()
    run([str(mock_content), '--json'])
    cap = capsys.readouterr()
    j = json.loads(cap.out)
    assert isinstance(j['Name'], str)
    assert isinstance(j['Size'], int)
    assert j['Created'] == pytest.approx(now - 1, abs=2)
    assert j['Created By'] == f'{_vars.__appname__} {_vars.__version__}'
    assert isinstance(j['Piece Size'], int)
    assert isinstance(j['Piece Count'], int)
    assert isinstance(j['File Count'], int)
    assert isinstance(j['Files'], list)
    for f in j['Files']:
        assert isinstance(f, dict)
        assert tuple(f.keys()) == ('Path', 'Size')
        assert isinstance(f['Path'], str)
        assert isinstance(f['Size'], int)
    assert isinstance(j['Info Hash'], str)
    assert len(j['Info Hash']) == 40
    assert j['Magnet'].startswith('magnet:?xt=urn:btih:')
    assert isinstance(j['Torrent'], str)

def test_json_does_not_contain_progress(capsys, mock_content):
    run([str(mock_content), '--json'])
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert 'Progress' not in j

def test_json_contains_cli_errors(capsys):
    with patch('sys.exit') as mock_exit:
        run(['--foo', '--json'])
    mock_exit.assert_called_once_with(err.Code.CLI)
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert j['Error'] == ['Unrecognized arguments: --foo']

def test_json_contains_config_errors(capsys, cfgfile):
    cfgfile.write_text('''
    foo
    ''')
    with patch('sys.exit') as mock_exit:
        run(['--json'])
    mock_exit.assert_called_once_with(err.Code.CONFIG)
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert j['Error'] == [f'{cfgfile}: Unrecognized arguments: --foo']

def test_json_contains_regular_errors(capsys):
    with patch('sys.exit') as mock_exit:
        run(['-i', 'path/to/nonexisting.torrent', '--json'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert j['Error'] == ['path/to/nonexisting.torrent: No such file or directory']

def test_json_contains_sigint(capsys, mock_create_mode, mock_content):
    mock_create_mode.side_effect = KeyboardInterrupt()
    with patch('sys.exit') as mock_exit:
        run([str(mock_content), '--json'])
    mock_exit.assert_called_once_with(err.Code.ABORTED)
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert j['Error'] == ['Aborted']

def test_json_contains_verification_errors(capsys, tmp_path, create_torrent):
    content_path = tmp_path / 'file.jpg'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        content_path.write_text('some data!!!')
        with patch('sys.exit') as mock_exit:
            run([str(content_path), '-i', torrent_file, '--json'])
    mock_exit.assert_called_once_with(err.Code.VERIFY)
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert j['Error'] == [f'{content_path}: Too big: 12 instead of 9 bytes',
                          f'{content_path} does not satisfy {torrent_file}']

def test_json_with_magnet_uri(capsys, regex):
    # Notice the double "&" in the URI, which is syntactically correct but
    # should be fixed in the output.
    magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=My+Torrent&xl=142631'
              '&tr=https%3A%2F%2Flocalhost%3A123%2Fannounce&&tr=https%3A%2F%2Flocalhost%3A456%2Fannounce')
    run(['-i', magnet, '--json'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {
        "Error": ['https://localhost:123/file?info_hash=%E1g%B1%FB%B4.%A7/%05%1FOPC%27%030%8E%FB%8F%D1: Connection refused',
                  'https://localhost:456/file?info_hash=%E1g%B1%FB%B4.%A7/%05%1FOPC%27%030%8E%FB%8F%D1: Connection refused'],
        'Name': 'My Torrent',
        'Size': 142631,
        'Trackers': ['https://localhost:123/announce', 'https://localhost:456/announce'],
        'File Count': 1,
        'Files': [
            {'Path': 'My Torrent', 'Size': 142631},
        ],
        'Magnet': magnet.replace('&&', '&'),
    }
