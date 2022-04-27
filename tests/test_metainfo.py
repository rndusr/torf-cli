import datetime
import json
from unittest.mock import patch

import pytest
import torf

from torfcli import _errors as err
from torfcli import _vars, run


@pytest.fixture
def nonstandard_torrent(tmp_path):
    (tmp_path / 'content').mkdir()
    (tmp_path / 'content' / 'file1').write_text('foo')
    (tmp_path / 'content' / 'file2').write_text('bar')
    (tmp_path / 'content' / 'dir').mkdir()
    (tmp_path / 'content' / 'dir' / 'file3').write_text('baz')

    t = torf.Torrent(path=tmp_path / 'content', private=True,
                     trackers=('https://foo.example.org',))
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
                                   'announce': 'https://foo.example.org',
                                   'info': {'name': 'content',
                                            'piece length': 16384,
                                            'private': 1,
                                            'files': [{'length': 3, 'path': ['dir', 'file3']},
                                                      {'length': 3, 'path': ['file1']},
                                                      {'length': 3, 'path': ['file2']}]}}

def test_metainfo_with_verbosity_level_one(capsys, nonstandard_torrent):
    run(['-i', nonstandard_torrent, '--metainfo', '--verbose'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out) == {'created by': f'torf {torf.__version__}',
                                   'announce': 'https://foo.example.org',
                                   'foo': 'bar',
                                   'info': {'baz': [1, 2, 3],
                                            'private': 1,
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
                                   'announce': 'https://foo.example.org',
                                   'foo': 'bar',
                                   'info': {'baz': [1, 2, 3],
                                            'private': 1,
                                            'files': [{'length': 3, 'path': ['dir', 'file3'], 'sneaky': 'pete'},
                                                      {'length': 3, 'path': ['file1']},
                                                      {'length': 3, 'path': ['file2']}],
                                            'name': 'content',
                                            'piece length': 16384,
                                            'pieces': 'YscFPSkTuTXkBSgIyyaqj/HVRXU='}}

def test_metainfo_uses_one_and_zero_for_boolean_values(capsys, create_torrent):
    with create_torrent(private=True) as torrent_file:
        run(['-i', torrent_file, '--metainfo'])
    cap = capsys.readouterr()
    assert cap.err == ''
    assert json.loads(cap.out)['info']['private'] == 1

def test_metainfo_with_disabled_validation(capsys, tmp_path):
    with open(tmp_path / 'nonstandard.torrent', 'wb') as f:
        f.write(b'd1:2i3e4:thisl2:is3:note5:validd2:is2:ok8:metainfol3:but4:thateee')
    torf.Torrent.read(tmp_path / 'nonstandard.torrent', validate=False)

    with patch('sys.exit') as mock_exit:
        run(['-i', str(tmp_path / 'nonstandard.torrent'), '--metainfo'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f"{_vars.__appname__}: Invalid metainfo: Missing 'info'\n"
    assert json.loads(cap.out) == {}

    run(['-i', str(tmp_path / 'nonstandard.torrent'), '--metainfo', '--novalidate'])
    cap = capsys.readouterr()
    assert cap.err == f"{_vars.__appname__}: WARNING: Invalid metainfo: Missing 'name' in ['info']\n"
    assert json.loads(cap.out) == {}

    run(['-i', str(tmp_path / 'nonstandard.torrent'), '--metainfo', '--novalidate', '--verbose'])
    cap = capsys.readouterr()
    assert cap.err == f"{_vars.__appname__}: WARNING: Invalid metainfo: Missing 'name' in ['info']\n"
    assert json.loads(cap.out) == {"2": 3,
                                   "this": ["is", "not"],
                                   "valid": {"is": "ok",
                                             "metainfo": ["but", "that"]}}

def test_metainfo_with_unreadable_torrent(capsys):
    with patch('sys.exit') as mock_exit:
        run(['-i', 'no/such/path.torrent', '--metainfo'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: no/such/path.torrent: No such file or directory\n'
    assert json.loads(cap.out) == {}

def test_metainfo_when_creating_torrent(capsys, mock_content):
    run([str(mock_content), '--metainfo', '-vv'])
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert 'info' in j
    assert 'name' in j['info']
    assert 'pieces' in j['info']

def test_metainfo_when_editing_torrent(capsys, create_torrent):
    date = '1999-07-23 14:00'
    with create_torrent(trackers=['http://foo', 'http://bar']) as orig_torrent:
        run(['-i', str(orig_torrent),
             '--comment', 'This comment was not here before.',
             '--date', date,
             '--nowebseed', '--webseed', 'https://new.webseeds',
             '-o', 'new.torrent', '--metainfo', '-v'])
    cap = capsys.readouterr()
    assert cap.err == ''
    j = json.loads(cap.out)
    assert 'info' in j
    assert 'name' in j['info']
    assert 'pieces' not in j['info']
    assert j['comment'] == 'This comment was not here before.'
    assert j['creation date'] == datetime.datetime.strptime(date, '%Y-%m-%d %H:%M').timestamp()
    assert j['url-list'] == ['https://new.webseeds']
    assert j['announce-list'] == [['http://foo'], ['http://bar']]
    assert j['announce'] == 'http://foo'


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
    assert json.loads(cap.out) == {}

def test_metainfo_with_magnet_uri(capsys, regex):
    magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=My+Torrent&xl=142631'
              '&tr=https%3A%2F%2Flocalhost%3A123%2Fannounce&&tr=https%3A%2F%2Flocalhost%3A456%2Fannounce')
    run(['-i', magnet, '--metainfo'])
    cap = capsys.readouterr()
    assert cap.err == regex(rf'^{_vars.__appname__}: https://localhost:123/file\?info_hash='
                            r'%E1g%B1%FB%B4\.%A7/%05%1FOPC%27%030%8E%FB%8F%D1: [\w\s]+\n'
                            rf'{_vars.__appname__}: https://localhost:456/file\?info_hash='
                            r'%E1g%B1%FB%B4\.%A7/%05%1FOPC%27%030%8E%FB%8F%D1: [\w\s]+\n$')
    j = json.loads(cap.out)
    assert j == {'announce': 'https://localhost:123/announce',
                 'announce-list': [['https://localhost:123/announce'], ['https://localhost:456/announce']],
                 'info': {'name': 'My Torrent', 'length': 142631}}
