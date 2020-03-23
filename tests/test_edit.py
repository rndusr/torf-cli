from torfcli import run
from torfcli import _errors as err
from torfcli import _vars

import pytest
from unittest.mock import patch
import torf
import os
from datetime import datetime


def test_nonexisting_input(capsys):
    nonexisting_path = '/no/such/file'
    with patch('sys.exit') as mock_exit:
        run(['-i', nonexisting_path, '-o', 'out.torrent'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {nonexisting_path}: No such file or directory\n'

def test_existing_output(capsys, tmpdir, create_torrent):
    outfile = tmpdir.join('out.torrent')
    outfile.write('some existing file content')
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


def test_no_changes(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new)


def test_edit_comment(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(comment='A comment') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--comment', 'A different comment', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, comment='A different comment')

def test_remove_comment(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(comment='A comment') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nocomment', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, comment=None)


def test_remove_creator(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(created_by='The creator') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nocreator', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, created_by=None)


def test_remove_private(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(private=True) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--noprivate', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, private=False)

def test_add_private(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(private=False) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--private', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, private=True)


def test_edit_source(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(source='the source') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--source', 'another source', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, source='another source')

def test_remove_source(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(source='the source') as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nosource', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, source=None)


def test_remove_xseed(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(randomize_infohash=True) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--noxseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, randomize_infohash=False)
        assert orig.infohash != new.infohash

def test_add_xseed(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(randomize_infohash=False) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--xseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, randomize_infohash=True)
        assert orig.infohash != new.infohash


def test_remove_trackers(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--notracker', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[])

def test_add_trackers(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--tracker', 'http://a', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://tracker1', 'http://a'], ['http://tracker2']])

    outfile = str(tmpdir.join('out.torrent'))
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

def test_replace_trackers(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--notracker', '--tracker', 'http://tracker10', '--tracker', 'http://tracker20', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://tracker10'], ['http://tracker20']])

def test_invalid_tracker_url(capsys, create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '--tracker', 'not a url', '-o', outfile])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: not a url: Invalid URL\n'
        assert not os.path.exists(outfile)



def test_remove_webseeds(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nowebseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=[])

def test_add_webseed(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--webseed', 'http://webseed3', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=['http://webseed1', 'http://webseed2', 'http://webseed3'])

def test_replace_webseeds(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nowebseed', '--webseed', 'http://webseed10', '--webseed', 'http://webseed20', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=['http://webseed10', 'http://webseed20'])

def test_invalid_webseed_url(capsys, create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '--webseed', 'not a url', '-o', outfile])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: not a url: Invalid URL\n'
        assert not os.path.exists(outfile)


def test_edit_creation_date(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--date', '3000-05-30 15:03:01', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, creation_date=datetime(3000, 5, 30, 15, 3, 1))

def test_remove_creation_date(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nodate', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, creation_date=None)

def test_invalid_creation_date(capsys, create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        with patch('sys.exit') as mock_exit:
            run(['-i', infile, '--date', 'foo', '-o', outfile])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: foo: Invalid date\n'
        assert not os.path.exists(outfile)


def test_edit_path(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    new_content = tmpdir.mkdir('new content')
    new_file = new_content.join('some file')
    new_file.write('different data')
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


def test_edit_path_with_exclude_option(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    new_content = tmpdir.mkdir('new content')
    new_file1 = new_content.join('some image.jpg')
    new_file1.write('image data')
    new_file2 = new_content.join('some text.txt')
    new_file2.write('text data')
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


def test_edit_name(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--name', 'new name', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, ignore=('name', 'files', 'filetree'))

        assert new.name == 'new name'
        orig_files = orig.files
        for of,nf in zip(orig.files, new.files):
            assert nf.parts[0] == 'new name'
            assert nf.parts[1:] == of.parts[1:]

        assert new.filetree == {'new name': {'Anotherthing.iso': torf.File('new name/Anotherthing.iso', size=9),
                                             'Something.jpg': torf.File('new name/Something.jpg', size=9),
                                             'Thirdthing.txt': torf.File('new name/Thirdthing.txt', size=9)}}
