from torfcli import run
from torfcli import _errors as err
from torfcli import _vars

import pytest
from unittest.mock import patch
import json
import torf
import base64

@pytest.fixture
def nonstandard_torrent(tmp_path):
    (tmp_path / 'content').mkdir()
    (tmp_path / 'content' / 'file1').write_text('foo')
    (tmp_path / 'content' / 'file2').write_text('bar')
    (tmp_path / 'content' / 'dir').mkdir()
    (tmp_path / 'content' / 'dir' / 'file3').write_text('baz')

    t = torf.Torrent(path=tmp_path / 'content')
    t.metainfo['foo'] = 'bar'
    t.metainfo['info']['baz'] = (1, 2, 3)
    t.metainfo['info']['files'][0]['sneaky'] = 'pete'
    t.generate()
    t.write(tmp_path / 'nonstandard.torrent')
    return str(tmp_path / 'nonstandard.torrent')

def test_metainfo_with_verbosity_level_zero(capsys, nonstandard_torrent):
    run(['-i', nonstandard_torrent, '--metainfo'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {'created by': f'torf {torf.__version__}',
                                   'info': {'name': 'content',
                                            'piece length': 16384,
                                            'files': [{'length': 3, 'path': ['dir', 'file3']},
                                                      {'length': 3, 'path': ['file1']},
                                                      {'length': 3, 'path': ['file2']}]}}

def test_metainfo_with_verbosity_level_one(capsys, nonstandard_torrent):
    run(['-i', nonstandard_torrent, '--metainfo', '--verbose'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {'created by': f'torf {torf.__version__}',
                                   'foo': 'bar',
                                   'info': {'baz': [1, 2, 3],
                                            'files': [{'length': 3, 'path': ['dir', 'file3'], 'sneaky': 'pete'},
                                                      {'length': 3, 'path': ['file1']},
                                                      {'length': 3, 'path': ['file2']}],
                                            'name': 'content',
                                            'piece length': 16384}}

def test_metainfo_with_verbosity_level_two(capsys, nonstandard_torrent):
    run(['-i', nonstandard_torrent, '--metainfo', '--verbose', '--verbose'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {'created by': f'torf {torf.__version__}',
                                   'foo': 'bar',
                                   'info': {'baz': [1, 2, 3],
                                            'files': [{'length': 3, 'path': ['dir', 'file3'], 'sneaky': 'pete'},
                                                      {'length': 3, 'path': ['file1']},
                                                      {'length': 3, 'path': ['file2']}],
                                            'name': 'content',
                                            'piece length': 16384,
                                            'pieces': 'YscFPSkTuTXkBSgIyyaqj/HVRXU='}}

def test_metainfo_does_not_need_to_be_valid_with_verbose_option(capsys, tmp_path):
    with open(tmp_path / 'nonstandard.torrent', 'wb') as f:
        f.write(b'd1:2i3e4:thisl2:is3:note5:validd2:is2:ok8:metainfol3:but4:thateee')
    t = torf.Torrent.read(tmp_path / 'nonstandard.torrent', validate=False)

    with patch('sys.exit') as mock_exit:
        run(['-i', str(tmp_path / 'nonstandard.torrent'), '--metainfo'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f"{_vars.__appname__}: Invalid metainfo: Missing 'info'\n"
    assert cap.out == ''

    run(['-i', str(tmp_path / 'nonstandard.torrent'), '--metainfo', '--verbose'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {"2": 3,
                                   "this": ["is", "not"],
                                   "valid": {"is": "ok",
                                             "metainfo": ["but", "that"]}}

    run(['-i', str(tmp_path / 'nonstandard.torrent'), '--metainfo', '--verbose', '--verbose'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {"2": 3,
                                   "this": ["is", "not"],
                                   "valid": {"is": "ok",
                                             "metainfo": ["but", "that"]}}

def test_metainfo_with_unreadable_torrent(capsys):
    with patch('sys.exit') as mock_exit:
        run(['-i', 'no/such/path.torrent', '--metainfo'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: no/such/path.torrent: No such file or directory\n'

def test_metainfo_when_creating_torrent(capsys, mock_content):
    run([str(mock_content), '--metainfo', '-vv'])
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert 'info' in j
    assert 'name' in j['info']
    assert 'pieces' in j['info']

def test_metainfo_when_editing_torrent(capsys, create_torrent):
    with create_torrent() as orig_torrent:
        run(['-i', str(orig_torrent),
             '--comment', 'This comment was not here before.',
             '--webseed', 'https://new.webseeds',
             '-o', 'new.torrent', '--metainfo', '-v'])
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert 'info' in j
    assert 'name' in j['info']
    assert 'pieces' not in j['info']
    assert j['comment'] == 'This comment was not here before.'
    assert 'https://new.webseeds' in j['url-list']

def test_metainfo_when_verifying_torrent(capsys, create_torrent, mock_content, tmp_path):
    with create_torrent(path=mock_content) as torrent_file:
        run(['-i', str(torrent_file), str(mock_content), '--metainfo'])
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert 'info' in j
    assert 'name' in j['info']
    assert 'pieces' not in j['info']

    with create_torrent(path=mock_content) as torrent_file:
        wrong_content = (tmp_path / 'wrong_content')
        wrong_content.write_text('foo')
        with patch('sys.exit') as mock_exit:
            run(['-i', str(torrent_file), str(wrong_content), '--metainfo'])
    mock_exit.assert_called_once_with(err.Code.VERIFY)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {wrong_content} does not satisfy {torrent_file}\n'
    assert cap.out == ''
