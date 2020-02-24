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


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_PATH_unreadable(create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    with create_torrent() as torrent_file:
        with human_readable(hr_enabled):
            with pytest.raises(err.VerifyError) as exc_info:
                run(['path/to/nothing', '-i', torrent_file])
            assert str(exc_info.value) == f'path/to/nothing does not satisfy {torrent_file}'
            cap = capsys.readouterr()
            print(clear_ansi(cap.out))
            if hr_enabled:
                assert clear_ansi(cap.out) == regex('Error  path/to/nothing: Not a directory\n')
            else:
                assert clear_ansi(cap.out) == regex('Error\tpath/to/nothing: Not a directory\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_singlefile_torrent__path_is_dir(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.write_bytes(b'some data')
    assert os.path.isfile(content_path) is True

    with create_torrent(path=content_path) as torrent_file:
        os.remove(content_path)
        content_path.mkdir()
        content_file = (content_path / 'some.file').write_bytes(b'some data')
        assert os.path.isfile(content_path) is False

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
        assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'

    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'Error  {content_path}: Is a directory\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'Error\t{content_path}: Is a directory\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_singlefile_torrent__wrong_size(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'file.jpg'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        content_path.write_text('some data!!!')

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
        assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'

    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'Error  {content_path}: Too big: 12 instead of 9 bytes\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'Error\t{content_path}: Too big: 12 instead of 9 bytes\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_singlefile_torrent__correct_size_but_corrupt(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        content_path.write_text('somm date')

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
            assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'
    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'Error  Corruption in piece 1\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'Error\tCorruption in piece 1\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__path_is_file(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.mkdir()
    file1 = content_path / 'file1.jpg'
    file1.write_text('some data')
    assert os.path.isdir(content_path) is True

    with create_torrent(path=content_path) as torrent_file:
        os.remove(file1)
        os.rmdir(content_path)
        content_path.write_text('some data')
        assert os.path.isdir(content_path) is False

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
            assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'
    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'Error  {content_path}: Not a directory\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'Error\t{content_path}: Not a directory\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__missing_file(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.mkdir()
    file1 = content_path / 'file1.jpg'
    file1.write_text('some data')
    file2 = content_path / 'file2.jpg'
    file2.write_text('some other data')

    with create_torrent(path=content_path) as torrent_file:
        os.remove(file1)

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
            assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'

    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'\s*Error  {file1}: No such file or directory\n')
        assert clear_ansi(cap.out) == regex(rf'\s*Error  Corruption in piece 1, '
                                            rf'at least one of these files is corrupt: {file1}, {file2}\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'\s*Error\t{file1}: No such file or directory\n')
        assert clear_ansi(cap.out) == regex(rf'\s*Error\tCorruption in piece 1, '
                                            rf'at least one of these files is corrupt: {file1}, {file2}\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__wrong_size(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.mkdir()
    file1 = content_path / 'file1.jpg'
    file1.write_text('some data')
    file2 = content_path / 'file2.jpg'
    file2.write_text('some other data')
    file2_size = os.path.getsize(file2)

    with create_torrent(path=content_path) as torrent_file:
        file2.write_text('some more other data')
        assert os.path.getsize(file2) != file2_size

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
            assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'
    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'Error  Corruption in piece 1, '
                                            rf'at least one of these files is corrupt: {file1}, {file2}\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'Error\tCorruption in piece 1, '
                                            rf'at least one of these files is corrupt: {file1}, {file2}\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__correct_size_but_corrupt(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.mkdir()
    file1 = content_path / 'file1.jpg'
    file1.write_text('some data')
    file1_size = os.path.getsize(file1)
    file2 = content_path / 'file2.jpg'
    file2.write_text('some other data')

    with create_torrent(path=content_path) as torrent_file:
        file1.write_text('SOME DATA')
        assert os.path.getsize(file1) == file1_size

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
            assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'
    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'Error  Corruption in piece 1, '
                                            rf'at least one of these files is corrupt: {file1}, {file2}\n')
    else:
        assert clear_ansi(cap.out) == regex(rf'Error\tCorruption in piece 1, '
                                            rf'at least one of these files is corrupt: {file1}, {file2}\n')


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_success(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex):
    content_path = tmp_path / 'content'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        with human_readable(hr_enabled):
            run([str(content_path), '-i', torrent_file])

    cap = capsys.readouterr()
    print(clear_ansi(cap.out))
    if hr_enabled:
        assert clear_ansi(cap.out) == regex(rf'\s*Progress  100.00 %  \|  \d+:\d+:\d+ total  \|  \s*\d+\.\d+ MiB/s$')
    else:
        assert clear_ansi(cap.out) == regex(rf'\s*Progress\t100\.000\t\d+\t\d+\t\d+\t\d+\t\d+\t{content_path}\n$')
