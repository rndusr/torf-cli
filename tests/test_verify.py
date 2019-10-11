from torfcli._main import run
from torfcli._errors import MainError
import pytest
import errno
import torf
import os


def test_torrent_unreadable(mock_content):
    with pytest.raises(MainError, match=r'^nonexisting.torrent: No such file or directory$') as exc_info:
        run([str(mock_content), '-i', 'nonexisting.torrent'])
    assert exc_info.value.errno == errno.ENOENT


def test_PATH_unreadable(create_torrent):
    with create_torrent() as torrent_file:
        t = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=r'^path/to/nothing: No such file or directory$') as exc_info:
            run(['path/to/nothing', '-i', torrent_file])
        assert exc_info.value.errno == errno.ENOENT


def test_singlefile_torrent__path_is_dir(create_torrent, tmpdir):
    content = tmpdir.join('content')
    content.write('some data')
    assert os.path.isfile(content) is True

    with create_torrent(path=content) as torrent_file:
        os.remove(content)
        content = tmpdir.mkdir('content')
        content_file = content.join('some.file')
        content_file.write('some data')
        assert os.path.isfile(content) is False

        t = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=rf'^{content}: Is a directory$') as exc_info:
            run([str(content), '-i', torrent_file])
        assert exc_info.value.errno == errno.EISDIR


def test_singlefile_torrent__mismatching_size(create_torrent, tmpdir):
    content = tmpdir.join('content')
    content.write('some data')

    with create_torrent(path=content) as torrent_file:
        content.write('some data!')

        t = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=rf'^{content}: Mismatching size$') as exc_info:
            run([str(content), '-i', torrent_file])
        assert exc_info.value.errno == errno.EFBIG


def test_multifile_torrent__path_is_file(create_torrent, tmpdir):
    content = tmpdir.mkdir('content')
    file1 = content.join('file1.jpg')
    file1.write('some data')
    assert os.path.isdir(content) is True

    with create_torrent(path=content) as torrent_file:
        os.remove(file1)
        os.rmdir(content)
        content = tmpdir.join('content')
        content.write('some data')
        assert os.path.isdir(content) is False

        t = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=rf'^{content}: Not a directory$') as exc_info:
            run([str(content), '-i', torrent_file])
        assert exc_info.value.errno == errno.ENOTDIR


def test_multifile_torrent__missing_file(create_torrent, tmpdir):
    content = tmpdir.mkdir('content')
    file1 = content.join('file1.jpg')
    file1.write('some data')
    file2 = content.join('file2.jpg')
    file2.write('some other data')

    with create_torrent(path=content) as torrent_file:
        os.remove(file1)

        t = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=rf'^{file1}: No such file or directory$') as exc_info:
            run([str(content), '-i', torrent_file])
        assert exc_info.value.errno == errno.ENOENT


def test_multifile_torrent__mismatching_size(create_torrent, tmpdir):
    content = tmpdir.mkdir('content')
    file1 = content.join('file1.jpg')
    file1.write('some data')
    file2 = content.join('file2.jpg')
    file2.write('some other data')
    file2_size = os.path.getsize(file2)

    with create_torrent(path=content) as torrent_file:
        file2.write('some other data!')
        assert os.path.getsize(file2) != file2_size

        t = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=rf'^{file2}: Mismatching size$') as exc_info:
            run([str(content), '-i', torrent_file])
        assert exc_info.value.errno == errno.EFBIG


def test_mismatching_infohash(create_torrent, tmpdir):
    content = tmpdir.mkdir('content')
    file1 = content.join('file1.jpg')
    file1.write('some data')
    file1_size = os.path.getsize(file1)
    file2 = content.join('file2.jpg')
    file2.write('some other data')

    with create_torrent(path=content) as torrent_file:
        file1.write('some dutu')
        assert os.path.getsize(file1) == file1_size
        t_new = torf.Torrent(path=content)
        t_new.generate()

        t_old = torf.Torrent.read(torrent_file)
        with pytest.raises(MainError, match=rf'^{t_new.infohash}: Mismatching hash$') as exc_info:
            run([str(content), '-i', torrent_file])
        assert exc_info.value.errno == errno.EADV
