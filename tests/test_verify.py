from torfcli._main import run
from torfcli import _errors as err
import pytest
import errno
import torf
import os
import re


def test_torrent_unreadable(mock_content):
    with pytest.raises(err.ReadError, match=r'^nonexisting.torrent: No such file or directory$'):
        run([str(mock_content), '-i', 'nonexisting.torrent'])


def test_PATH_unreadable(create_torrent, human_readable, capsys, clear_ansi):
    with create_torrent() as torrent_file:
        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run(['path/to/nothing', '-i', torrent_file])
            assert str(exc_info.value) == f'path/to/nothing does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  path/to/nothing: Not a directory\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run(['path/to/nothing', '-i', torrent_file])
            assert str(exc_info.value) == f'path/to/nothing does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\tpath/to/nothing: Not a directory\n')


def test_singlefile_torrent__path_is_dir(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
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

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  {content}: Is a directory\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\t{content}: Is a directory\n')


def test_singlefile_torrent__file_too_big(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
    content = tmpdir.join('content')
    content.write('some data')

    with create_torrent(path=content) as torrent_file:
        content.write('some data!!!')

        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  {content}: Too big: 12 instead of 9 bytes\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\t{content}: Too big: 12 instead of 9 bytes\n')


def test_singlefile_torrent__wrong_size(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
    content = tmpdir.join('content')
    content.write('some data')

    with create_torrent(path=content) as torrent_file:
        content.write('some dat')

        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  Corruption in piece 1\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\tCorruption in piece 1\n')


def test_singlefile_torrent__correct_size_but_corrupt(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
    content = tmpdir.join('content')
    content.write('some data')

    with create_torrent(path=content) as torrent_file:
        content.write('somm date')

        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  Corruption in piece 1\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\tCorruption in piece 1\n')


def test_multifile_torrent__path_is_file(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
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

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  {content}: Not a directory\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\t{content}: Not a directory\n')


def test_multifile_torrent__missing_file(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
    content = tmpdir.mkdir('content')
    file1 = content.join('file1.jpg')
    file1.write('some data')
    file2 = content.join('file2.jpg')
    file2.write('some other data')

    with create_torrent(path=content) as torrent_file:
        os.remove(file1)

        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert re.search((rf'\s*Error  {file1}: No such file or directory\n'
                              rf'\s*Error  Corruption in piece 1, at least one of these files is corrupt: '
                              rf'{file1}, {file2}\n$'), clear_ansi(cap.out))

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert re.search((rf'\s*Error\t{file1}: No such file or directory\n'
                              rf'\s*Error\tCorruption in piece 1, at least one of these files is corrupt: '
                              rf'{file1}, {file2}\n$'), clear_ansi(cap.out))


def test_multifile_torrent__wrong_size(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
    content = tmpdir.mkdir('content')
    file1 = content.join('file1.jpg')
    file1.write('some data')
    file2 = content.join('file2.jpg')
    file2.write('some other data')
    file2_size = os.path.getsize(file2)

    with create_torrent(path=content) as torrent_file:
        file2.write('some more other data')
        assert os.path.getsize(file2) > file2_size

        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error  Corruption in piece 1, '
                                                f'at least one of these files is corrupt: '
                                                f'{file1}, {file2}\n')

        with human_readable(False):
            with pytest.raises(err.VerifyError) as exc_info:
                run([str(content), '-i', torrent_file])
            assert str(exc_info.value) == f'{content} does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert clear_ansi(cap.out).endswith(f'Error\tCorruption in piece 1, '
                                                f'at least one of these files is corrupt: '
                                                f'{file1}, {file2}\n')


def test_success(tmpdir, create_torrent, human_readable, capsys, clear_ansi):
    content = tmpdir.join('content')
    content.write('some data')

    with create_torrent(path=content) as torrent_file:
        t = torf.Torrent.read(torrent_file)

        with human_readable(True):
            run([str(content), '-i', torrent_file])
            cap = capsys.readouterr()
            assert re.search(rf'\s*Progress  100.00 %  \|  \d+:\d+:\d+ total  \|  \d+\.\d+ MiB/s\n$',
                              clear_ansi(cap.out))

        with human_readable(False):
            run([str(content), '-i', torrent_file])
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            assert re.search(rf'\s*Progress\t100\.000\t\d+\t\d+\t\d+\t\d+\t\d+\t{content}\n$',
                             clear_ansi(cap.out))
