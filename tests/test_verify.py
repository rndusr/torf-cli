from torfcli._main import run
from torfcli import _errors as err
import pytest
import torf
import os
import re


def test_torrent_unreadable(mock_content):
    with pytest.raises(err.ReadError, match=r'^nonexisting.torrent: No such file or directory$'):
        run([str(mock_content), '-i', 'nonexisting.torrent'])


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_PATH_unreadable(create_torrent, human_readable, hr_enabled, capsys, clear_ansi, regex, assert_no_ctrl):
    with create_torrent() as torrent_file:
        with human_readable(hr_enabled):
            with pytest.raises(err.VerifyError) as exc_info:
                run(['path/to/nothing', '-i', torrent_file])
            assert str(exc_info.value) == f'path/to/nothing does not satisfy {torrent_file}'
    cap = capsys.readouterr()
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(r'^\s*Error  path/to/nothing: Not a directory$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(r'^Error\tpath/to/nothing: Not a directory$', flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_singlefile_torrent__path_is_dir(tmp_path, create_torrent, human_readable, hr_enabled,
                                         capsys, clear_ansi, assert_no_ctrl, regex):
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
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  {content_path}: Is a directory$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Error\t{content_path}: Is a directory$', flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_singlefile_torrent__wrong_size(tmp_path, create_torrent, human_readable, hr_enabled,
                                        capsys, clear_ansi, assert_no_ctrl, regex):
    content_path = tmp_path / 'file.jpg'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        content_path.write_text('some data!!!')

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
        assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'

    cap = capsys.readouterr()
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  {content_path}: Too big: 12 instead of 9 bytes$',
                                            flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Error\t{content_path}: Too big: 12 instead of 9 bytes$',
                                flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_singlefile_torrent__correct_size_but_corrupt(tmp_path, create_torrent, human_readable, hr_enabled,
                                                      capsys, clear_ansi, assert_no_ctrl, regex):
    content_path = tmp_path / 'content'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        content_path.write_text('somm date')

        with pytest.raises(err.VerifyError) as exc_info:
            with human_readable(hr_enabled):
                run([str(content_path), '-i', torrent_file])
            assert str(exc_info.value) == f'{content_path} does not satisfy {torrent_file}'
    cap = capsys.readouterr()
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  Corruption in piece 1$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Error\tCorruption in piece 1$', flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__path_is_file(tmp_path, create_torrent, human_readable, hr_enabled,
                                         capsys, clear_ansi, assert_no_ctrl, regex):
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
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  {content_path}: Not a directory$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Error\t{content_path}: Not a directory$', flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__missing_file(tmp_path, create_torrent, human_readable, hr_enabled,
                                         capsys, clear_ansi, assert_no_ctrl, regex):
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
    if hr_enabled:
        print(clear_ansi(cap.out))
        print(cap.out)
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  {file1}: No such file or directory$',
                                            flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  Corruption in piece 1, at least one of these files is corrupt:$',
                                            flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*      {file1}$', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*      {file2}$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Error\t{file1}: No such file or directory$', flags=re.MULTILINE)
        assert cap.out == regex((rf'^Error\tCorruption in piece 1, at least one of these files is corrupt:\t{file1}\t{file2}$'),
                                flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__wrong_size(tmp_path, create_torrent, human_readable, hr_enabled,
                                       capsys, clear_ansi, assert_no_ctrl, regex):
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
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  {file2}: Too big: 20 instead of 15 bytes$',
                                            flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  Corruption in piece 1, at least one of these files is corrupt:$',
                                            flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*      {file1}$', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*      {file2}$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Error\t{file2}: Too big: 20 instead of 15 bytes$', flags=re.MULTILINE)
        assert cap.out == regex((rf'^Error\tCorruption in piece 1, at least one of these files is corrupt:\t{file1}\t{file2}$'),
                                flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_multifile_torrent__correct_size_but_corrupt(tmp_path, create_torrent, human_readable, hr_enabled,
                                                     capsys, clear_ansi, assert_no_ctrl, regex):
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
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Error  Corruption in piece 1, at least one of these files is corrupt:$',
                                            flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*      {file1}$', flags=re.MULTILINE)
        assert clear_ansi(cap.out) == regex(rf'^\s*      {file2}$', flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex((rf'^Error\tCorruption in piece 1, at least one of these files is corrupt:\t{file1}\t{file2}$'),
                                flags=re.MULTILINE)


@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_success(tmp_path, create_torrent, human_readable, hr_enabled, capsys, clear_ansi, assert_no_ctrl, regex):
    content_path = tmp_path / 'content'
    content_path.write_text('some data')

    with create_torrent(path=content_path) as torrent_file:
        with human_readable(hr_enabled):
            run([str(content_path), '-i', torrent_file])

    cap = capsys.readouterr()
    if hr_enabled:
        print(clear_ansi(cap.out))
        assert clear_ansi(cap.out) == regex(rf'^\s*Progress  100.00 %  \|  \d+:\d+:\d+ total  \|  \s*\d+\.\d+ MiB/s$',
                                            flags=re.MULTILINE)
    else:
        print(repr(cap.out))
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Progress\t100\.000\t\d+\t\d+\t\d+\t\d+\t\d+\t{content_path}$',
                                flags=re.MULTILINE)
