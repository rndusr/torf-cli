import os
import re
from datetime import datetime
from unittest.mock import patch

import pytest
import torf

from torfcli import _config as config
from torfcli import _errors as err
from torfcli import _vars, run


def test_nonexisting_input(capsys):
    nonexisting_path = '/no/such/file'
    with patch('sys.exit') as mock_exit:
        run(['-i', nonexisting_path, '-o', 'out.torrent'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {nonexisting_path}: No such file or directory\n'

def test_existing_output(capsys, tmp_path, create_torrent):
    outfile = tmp_path / 'out.torrent'
    outfile.write_text('some existing file content')
    with create_torrent() as infile:
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '-o', str(outfile)])
        mock_exit.assert_called_once_with(err.Code.WRITE)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {outfile}: File exists\n'

def test_unwritable_output(capsys, create_torrent):
    unwritable_path = '/out.torrent'
    with create_torrent() as infile:
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '-o', unwritable_path])
        mock_exit.assert_called_once_with(err.Code.WRITE)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {unwritable_path}: Permission denied\n'


def test_no_changes(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new)


def test_edit_comment(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(comment='A comment') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--comment', 'A different comment', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, comment='A different comment')

def test_remove_comment(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(comment='A comment') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nocomment', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, comment=None)


def test_remove_creator(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(created_by='The creator') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nocreator', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, created_by=None)

def test_remove_creator_even_when_creator_provided(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(created_by='The creator') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nocreator', '--creator', 'A conflicting creator', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, created_by=None)

def test_edit_creator(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(created_by='The creator') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--creator', 'A different creator', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, created_by='A different creator')

def test_edit_default_creator(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(created_by='The creator') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--creator', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, created_by=config.DEFAULT_CREATOR)


def test_remove_private(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(private=True) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--noprivate', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, private=None)

def test_add_private(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(private=False) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--private', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, private=True)

def test_add_private_and_remove_all_trackers(create_torrent, tmp_path, assert_torrents_equal, capsys):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(private=False) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--private', '--notracker', '-o', outfile])
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: WARNING: Torrent is private and has no trackers\n'
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, private=True, trackers=())


def test_edit_source(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(source='the source') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--source', 'another source', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, source='another source')

def test_remove_source(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(source='the source') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nosource', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, source=None)


def test_remove_xseed(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(randomize_infohash=True) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--noxseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, randomize_infohash=False)
        assert orig.infohash != new.infohash

def test_add_xseed(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(randomize_infohash=False) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--xseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, randomize_infohash=True)
        assert orig.infohash != new.infohash


def test_remove_trackers(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--notracker', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[])

def test_add_trackers(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--tracker', 'http://a', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://tracker1', 'http://a'], ['http://tracker2']])

    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(trackers=['http://foo', 'http://bar']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile,
             '--tracker', 'http://a,http://b',
             '--tracker', 'http://x',
             '--tracker', 'http://y',
             '-o', outfile, '-y'])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://foo', 'http://a', 'http://b'],
                                                   ['http://bar', 'http://x'],
                                                   ['http://y']])

def test_replace_trackers(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--notracker', '--tracker', 'http://tracker10', '--tracker', 'http://tracker20', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://tracker10'], ['http://tracker20']])

def test_invalid_tracker_url(capsys, create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '--tracker', 'not a url', '-o', outfile])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: not a url: Invalid URL\n'
        assert not os.path.exists(outfile)



def test_remove_webseeds(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nowebseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=[])

def test_add_webseed(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--webseed', 'http://webseed3', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=['http://webseed1', 'http://webseed2', 'http://webseed3'])

def test_replace_webseeds(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nowebseed', '--webseed', 'http://webseed10', '--webseed', 'http://webseed20', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=['http://webseed10', 'http://webseed20'])

def test_invalid_webseed_url(capsys, create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '--webseed', 'not a url', '-o', outfile])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: not a url: Invalid URL\n'
        assert not os.path.exists(outfile)


def test_edit_creation_date(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--date', '3000-05-30 15:03:01', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, creation_date=datetime(3000, 5, 30, 15, 3, 1))

def test_remove_creation_date(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nodate', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, creation_date=None)

def test_invalid_creation_date(capsys, create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent() as infile:
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '--date', 'foo', '-o', outfile])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: foo: Invalid date\n'
        assert not os.path.exists(outfile)


def test_edit_path(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    new_content = tmp_path / 'new content'
    new_content.mkdir()
    new_file = new_content / 'some file'
    new_file.write_text('different data')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, str(new_content), '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, ignore=('files', 'filetree', 'name',
                                                 'piece_size', 'pieces', 'size'))
        assert tuple(new.files) == (torf.File('new content/some file', size=14),)
        assert new.filetree == {'new content': {'some file': torf.File('new content/some file', size=14)}}
        assert new.name == 'new content'
        assert new.size == len('different data')


def test_edit_path_with_exclude_option(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    new_content = tmp_path / 'new content'
    new_content.mkdir()
    new_file1 = new_content / 'some image.jpg'
    new_file1.write_text('image data')
    new_file2 = new_content / 'some text.txt'
    new_file2.write_text('text data')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, str(new_content), '--exclude', '*.txt', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, ignore=('files', 'filetree', 'name',
                                                 'piece_size', 'pieces', 'size'))
        assert tuple(new.files) == (torf.File('new content/some image.jpg', size=10),)
        assert new.filetree == {'new content': {'some image.jpg': torf.File('new content/some image.jpg',
                                                                            size=10)}}
        assert new.name == 'new content'
        assert new.size == len('image data')


def test_edit_path_with_exclude_regex_option(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    new_content = tmp_path / 'new content'
    new_content.mkdir()
    new_file1 = new_content / 'some image.jpg'
    new_file1.write_text('image data')
    new_file2 = new_content / 'some text.txt'
    new_file2.write_text('text data')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, str(new_content), '--exclude-regex', r'.*\.txt$', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, ignore=('files', 'filetree', 'name',
                                                 'piece_size', 'pieces', 'size'))
        assert tuple(new.files) == (torf.File('new content/some image.jpg', size=10),)
        assert new.filetree == {'new content': {'some image.jpg': torf.File('new content/some image.jpg',
                                                                            size=10)}}
        assert new.name == 'new content'
        assert new.size == len('image data')


def test_edit_name(create_torrent, tmp_path, assert_torrents_equal):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--name', 'new name', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, ignore=('name', 'files', 'filetree'))

        assert new.name == 'new name'
        for of,nf in zip(orig.files, new.files):
            assert nf.parts[0] == 'new name'
            assert nf.parts[1:] == of.parts[1:]

        assert new.filetree == {'new name': {'Anotherthing.iso': torf.File('new name/Anotherthing.iso', size=9),
                                             'Something.jpg': torf.File('new name/Something.jpg', size=9),
                                             'Thirdthing.txt': torf.File('new name/Thirdthing.txt', size=9)}}


def test_edit_invalid_torrent_with_validation_enabled(tmp_path, capsys):
    infile = tmp_path / 'in.torrent'
    outfile = tmp_path / 'out.torrent'
    with open(infile, 'wb') as f:
        f.write(b'd1:2i3e4:thisl2:is3:note5:validd2:is2:ok8:metainfol3:but4:thateee')
    with patch('sys.exit') as mock_exit:
        run(['-i', str(infile), '--name', 'New Name', '-o', str(outfile)])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f"{_vars.__appname__}: Invalid metainfo: Missing 'info'\n"
    assert cap.out == ''
    assert not os.path.exists(outfile)

def test_edit_invalid_torrent_with_validation_disabled(tmp_path, capsys, regex):
    infile = tmp_path / 'in.torrent'
    outfile = tmp_path / 'out.torrent'
    with open(infile, 'wb') as f:
        f.write(b'd1:2i3e4:thisl2:is3:note5:validd2:is2:ok8:metainfol3:but4:thateee')
    run(['-i', str(infile), '--name', 'New Name', '-o', str(outfile), '--novalidate'])
    cap = capsys.readouterr()
    assert cap.err == f"{_vars.__appname__}: WARNING: Invalid metainfo: Missing 'piece length' in ['info']\n"
    assert cap.out == regex(r'^Name\tNew Name$', flags=re.MULTILINE)
    assert cap.out == regex(fr'^Torrent\t{outfile}$', flags=re.MULTILINE)
    assert os.path.exists(outfile)


def test_edit_magnet_uri_and_dont_create_torrent(capsys, regex):
    magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=My+Torrent&xl=142631'
              '&tr=https%3A%2F%2Flocalhost%3A123%2Fannounce')
    run(['-i', magnet, '--name', 'New Name', '--notracker', '--webseed', 'http://foo',
         '--notorrent'])
    cap = capsys.readouterr()
    assert cap.err == ''
    new_magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=New+Name&xl=142631'
                  '&ws=http%3A%2F%2Ffoo')
    assert cap.out == regex(fr'^Magnet\t{re.escape(new_magnet)}\n$', flags=re.MULTILINE)

def test_edit_magnet_uri_and_create_torrent_with_validation_enabled(capsys, tmp_path, regex):
    magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=My+Torrent&xl=142631'
              '&tr=https%3A%2F%2Flocalhost%3A123%2Fannounce')
    outfile = tmp_path / 'out.torrent'
    with patch('sys.exit') as mock_exit:
        run(['-i', magnet, '--name', 'New Name', '--notracker', '--tracker', 'http://bar',
             '-o', str(outfile)])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == (f"{_vars.__appname__}: https://localhost:123/file?info_hash=%E1g%B1%FB%B4.%A7/%05%1FOPC%27%030%8E%FB%8F%D1"
                       f': Connection refused\n'
                       f"{_vars.__appname__}: Invalid metainfo: Missing 'piece length' in ['info']\n")

def test_edit_magnet_uri_and_create_torrent_with_validation_disabled(capsys, tmp_path, regex):
    magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=My+Torrent&xl=142631'
              '&tr=https%3A%2F%2Flocalhost%3A123%2Fannounce')
    outfile = tmp_path / 'out.torrent'
    run(['-i', magnet, '--name', 'New Name', '--notracker', '--tracker', 'http://bar',
         '-o', str(outfile), '--novalidate'])
    cap = capsys.readouterr()
    assert cap.err == (f"{_vars.__appname__}: https://localhost:123/file?info_hash=%E1g%B1%FB%B4.%A7/%05%1FOPC%27%030%8E%FB%8F%D1"
                       f': Connection refused\n'
                       f"{_vars.__appname__}: WARNING: Invalid metainfo: Missing 'piece length' in ['info']\n")
    new_magnet = ('magnet:?xt=urn:btih:e167b1fbb42ea72f051f4f50432703308efb8fd1&dn=New+Name&xl=142631'
                  '&tr=http%3A%2F%2Fbar')
    assert cap.out == regex(fr'^Magnet\t{re.escape(new_magnet)}$', flags=re.MULTILINE)
    assert cap.out == regex(fr'^Torrent\t{re.escape(str(outfile))}$', flags=re.MULTILINE)
    torrent = torf.Torrent.read(outfile, validate=False)
    assert torrent.size == 142631
    assert torrent.name == 'New Name'
    assert torrent.trackers == [['http://bar']]


@pytest.mark.parametrize(
    argnames='merges, exp_result',
    argvalues=(
        (
            [
                '{"creation date": 1352534887}',
                '{"info": {"foo": ["Hello", "World!"], "bar": "baz", "private": null, "nosuchkey": null}}',
                '{"created by": null}',
            ],
            {
                'creation_date': datetime(2012, 11, 10, 9, 8, 7),
                'created_by': None,
                'private': None,
                'path_map': {
                    ('info', 'foo'): ['Hello', 'World!'],
                    ('info', 'bar'): 'baz',
                },
            },
        ),
        (
            ['["Hello", "World!"]'],
            err.CliError("Not a JSON object: ['Hello', 'World!']"),
        ),
    ),
    ids=lambda v: repr(v),
)
def test_merge_option(merges, exp_result, create_torrent, tmp_path, assert_torrents_equal, capsys):
    outfile = str(tmp_path / 'out.torrent')
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        cmd = ['-i', infile, '-o', outfile]
        for merge in merges:
            cmd.extend(('--merge', merge))

        if isinstance(exp_result, err.Error):
            with patch('sys.exit') as mock_exit:
                run(cmd)
            mock_exit.assert_called_once_with(exp_result.exit_code)
            cap = capsys.readouterr()
            assert cap.err == f'{_vars.__appname__}: {str(exp_result)}\n'
        else:
            run(cmd)
            new = torf.Torrent.read(outfile)
            assert_torrents_equal(orig, new, **exp_result)
