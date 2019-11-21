from torfcli._main import run
from torfcli import _errors as err
import pytest
import torf
import os
from datetime import datetime


def test_nonexisting_input():
    nonexisting_path = '/no/such/file'
    with pytest.raises(err.ReadError, match=rf'^{nonexisting_path}: No such file or directory$'):
        run(['-i', nonexisting_path, '-o', 'out.torrent'])


def test_existing_output(create_torrent, tmpdir):
    outfile = tmpdir.join('out.torrent')
    outfile.write('some existing file content')
    with create_torrent() as infile:
        with pytest.raises(err.WriteError, match=rf'^{str(outfile)}: File exists$') as exc_info:
            run(['-i', infile, '-o', str(outfile)])


def test_unwritable_output(create_torrent):
    unwritable_path = '/out.torrent'
    with create_torrent() as infile:
        with pytest.raises(err.WriteError, match=rf'^{unwritable_path}: Permission denied$') as exc_info:
            run(['-i', infile, '-o', unwritable_path])


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
        assert_torrents_equal(orig, new, trackers=None)

def test_add_tracker(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--tracker', 'http://tracker3', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://tracker1'], ['http://tracker2'], ['http://tracker3']])

def test_replace_trackers(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--notracker', '--tracker', 'http://tracker10', '--tracker', 'http://tracker20', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, trackers=[['http://tracker10'], ['http://tracker20']])

def test_invalid_tracker_url(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(trackers=['http://tracker1', 'http://tracker2']) as infile:
        orig = torf.Torrent.read(infile)
        with pytest.raises(err.ParseError, match=r'^not a url: Invalid URL$'):
            run(['-i', infile, '--tracker', 'not a url', '-o', outfile])
        assert not os.path.exists(outfile)


def test_remove_webseeds(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        run(['-i', infile, '--nowebseed', '-o', outfile])
        new = torf.Torrent.read(outfile)
        assert_torrents_equal(orig, new, webseeds=None)

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

def test_invalid_webseed_url(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent(webseeds=['http://webseed1', 'http://webseed2']) as infile:
        orig = torf.Torrent.read(infile)
        with pytest.raises(err.ParseError, match=r'^not a url: Invalid URL$'):
            run(['-i', infile, '--webseed', 'not a url', '-o', outfile])
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

def test_invalid_creation_date(create_torrent, tmpdir, assert_torrents_equal):
    outfile = str(tmpdir.join('out.torrent'))
    with create_torrent() as infile:
        orig = torf.Torrent.read(infile)
        with pytest.raises(err.ParseError, match=r'^foo: Invalid date$'):
            run(['-i', infile, '--date', 'foo', '-o', outfile])
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
        assert tuple(new.files) == ('new content/some file',)
        assert new.filetree == {'new content': {'some file': torf.Torrent.File(name='some file',
                                                                               path='new content/some file',
                                                                               dir='new content',
                                                                               size=14)}}
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
        assert tuple(new.files) == ('new content/some image.jpg',)
        assert new.filetree == {'new content': {'some image.jpg': torf.Torrent.File(name='some image.jpg',
                                                                                    path='new content/some image.jpg',
                                                                                    dir='new content',
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
        assert tuple(new.files) == tuple(path.replace(orig.name, 'new name')
                                         for path in orig.files)
        assert new.filetree == {'new name': {'Anotherthing.iso': torf.Torrent.File(name='Anotherthing.iso',
                                                                      path='new name/Anotherthing.iso',
                                                                      dir='new name', size=9),
                                             'Something.jpg': torf.Torrent.File(name='Something.jpg',
                                                                   path='new name/Something.jpg',
                                                                   dir='new name', size=9),
                                             'Thirdthing.txt': torf.Torrent.File(name='Thirdthing.txt',
                                                                    path='new name/Thirdthing.txt',
                                                                    dir='new name', size=9)}}
