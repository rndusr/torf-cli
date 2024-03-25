import os
import re
from datetime import date, datetime, time, timedelta
from unittest.mock import DEFAULT, patch

import pytest
import torf

from torfcli import _errors as err
from torfcli import _vars, run


def assert_approximate_date(date1, date2):
    date_min = date2.replace(microsecond=0) - timedelta(seconds=1)
    date_max = date2.replace(microsecond=0) + timedelta(seconds=1)
    assert date_min <= date1 <= date_max


### Basic creation modes

@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_default_torrent_filepath(capsys, mock_content, human_readable, hr_enabled, clear_ansi, assert_no_ctrl, regex):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    now = datetime.today()
    with human_readable(hr_enabled):
        run([content_path])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.name == 'My Torrent'
    assert len(tuple(t.files)) == 3
    assert_approximate_date(t.creation_date, now)
    assert t.created_by.startswith('torf')

    cap = capsys.readouterr()
    if hr_enabled:
        out_cleared = clear_ansi(cap.out)
        assert out_cleared == regex(rf'^\s*Magnet  magnet:\?xt=urn:btih:{t.infohash}&dn=My\+Torrent&xl=\d+$', flags=re.MULTILINE)
        assert out_cleared == regex(rf'^\s*Torrent  {exp_torrent_filename}$', flags=re.MULTILINE)
        assert out_cleared == regex(r'^\s*Name  My Torrent$', flags=re.MULTILINE)
        assert out_cleared == regex(r'^\s*File Count  3$', flags=re.MULTILINE)
        assert out_cleared == regex(rf'^\s*Info Hash  {t.infohash}$', flags=re.MULTILINE)
        assert out_cleared == regex(rf'^\s*Created By  torf {re.escape(_vars.__version__)}$', flags=re.MULTILINE)
    else:
        assert_no_ctrl(cap.out)
        assert cap.out == regex(rf'^Magnet\tmagnet:\?xt=urn:btih:{t.infohash}&dn=My\+Torrent&xl=\d+$', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Torrent\t{exp_torrent_filename}$', flags=re.MULTILINE)
        assert cap.out == regex(r'^Name\tMy Torrent$', flags=re.MULTILINE)
        assert cap.out == regex(r'^File Count\t3$', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Info Hash\t{t.infohash}$', flags=re.MULTILINE)
        assert cap.out == regex(rf'^Created By\ttorf {re.escape(_vars.__version__)}$', flags=re.MULTILINE)


def test_user_given_torrent_filepath(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = 'foo.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    now = datetime.today()
    run([content_path, '--out', exp_torrent_filename])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.name == 'My Torrent'
    assert len(tuple(t.files)) == 3
    assert_approximate_date(t.creation_date, now)
    assert t.created_by.startswith('torf')

    cap = capsys.readouterr()
    assert 'Magnet\tmagnet:?xt=urn:btih:' in cap.out
    assert f'Torrent\t{exp_torrent_filename}' in cap.out
    assert 'Name\tMy Torrent' in cap.out
    assert 'File Count\t3' in cap.out
    assert 'Info Hash' in cap.out
    assert 'Created By\ttorf' in cap.out


### Error cases

@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_content_path_is_empty_directory(capsys, tmp_path, human_readable, hr_enabled):
    (tmp_path / 'empty').mkdir()
    with human_readable(hr_enabled):
        with patch('sys.exit') as mock_exit:
            run([str(tmp_path / 'empty')])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {tmp_path / "empty"}: Empty or all files excluded\n'

@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_content_path_is_empty_file(capsys, tmp_path, human_readable, hr_enabled):
    (tmp_path / 'empty').write_bytes(b'')
    with human_readable(hr_enabled):
        with patch('sys.exit') as mock_exit:
            run([str(tmp_path / 'empty')])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {tmp_path / "empty"}: Empty or all files excluded\n'

@pytest.mark.parametrize('hr_enabled', (True, False), ids=('human_readable=True', 'human_readable=False'))
def test_content_path_doesnt_exist(capsys, human_readable, hr_enabled):
    with human_readable(hr_enabled):
        with patch('sys.exit') as mock_exit:
            run(['/path/doesnt/exist'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: /path/doesnt/exist: No such file or directory\n'

def test_torrent_filepath_exists(capsys, mock_content, human_readable):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with open(exp_torrent_filepath, 'wb') as f:
        f.write(b'<torrent data>')

    with human_readable(False):
        with patch('sys.exit') as mock_exit:
            run([content_path, '--out', exp_torrent_filepath])
    mock_exit.assert_called_once_with(err.Code.WRITE)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {exp_torrent_filepath}: File exists\n'

    with human_readable(True):
        with patch('torfcli._ui._HumanFormatter.dialog_yes_no') as mock_dialog:
            with patch('sys.exit') as mock_exit:
                mock_dialog.return_value = False
                run([content_path, '--out', exp_torrent_filepath])
            mock_exit.assert_called_once_with(err.Code.WRITE)
            cap = capsys.readouterr()
            assert cap.err == f'{_vars.__appname__}: {exp_torrent_filepath}: File exists\n'

            with patch('sys.exit') as mock_exit:
                mock_dialog.return_value = True
                run([content_path, '--out', exp_torrent_filepath])
            mock_exit.assert_not_called()
            cap = capsys.readouterr()
            assert cap.err == ''
            assert torf.Torrent.read(exp_torrent_filepath).name == mock_content.name


### Options

def test_nomagnet_option(capsys, mock_content):
    content_path = str(mock_content)
    run([content_path, '--nomagnet'])

    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)
    assert os.path.exists(exp_torrent_filepath)

    cap = capsys.readouterr()
    assert 'Magnet\t' not in cap.out
    assert 'Torrent\t' in cap.out

    assert 'Name\tMy Torrent' in cap.out
    assert 'File Count\t3' in cap.out
    assert 'Info Hash' in cap.out
    assert 'Created By\ttorf' in cap.out


def test_notorrent_option(capsys, mock_content):
    content_path = str(mock_content)
    run([content_path, '--notorrent'])

    unexp_torrent_filename = os.path.basename(content_path) + '.torrent'
    unexp_torrent_filepath = os.path.join(os.getcwd(), unexp_torrent_filename)
    assert not os.path.exists(unexp_torrent_filepath)

    cap = capsys.readouterr()
    assert 'Magnet\t' in cap.out
    assert 'Torrent\t' not in cap.out

    assert 'Name\tMy Torrent' in cap.out
    assert 'File Count\t3' in cap.out
    assert 'Info Hash' in cap.out
    assert 'Created By\ttorf' in cap.out


def test_yes_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with open(exp_torrent_filepath, 'wb') as f:
        f.write(b'<some file content>')
    assert os.path.exists(exp_torrent_filepath)

    run([content_path, '--out', exp_torrent_filename, '--yes'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.name == 'My Torrent'

    cap = capsys.readouterr()
    assert 'Magnet\tmagnet:?xt=urn:btih:' in cap.out
    assert f'Torrent\t{exp_torrent_filename}' in cap.out


def test_exclude_glob(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--exclude', '*.jpg'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert len(tuple(t.files)) == 2

    cap = capsys.readouterr()
    assert 'Exclude\t*.jpg' in cap.out
    assert 'File Count\t2' in cap.out


def test_excludes_regex(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with patch('sys.exit') as mock_exit:
        run([content_path, '--exclude-regex', '*'])
    mock_exit.assert_called_once_with(err.Code.CLI)
    cap = capsys.readouterr()
    assert cap.out == ''
    assert cap.err == f'{_vars.__appname__}: Invalid regular expression: *: Nothing to repeat at position 0\n'

    run([content_path, '--exclude-regex', r'.*\.jpg$'])
    t = torf.Torrent.read(exp_torrent_filepath)
    assert len(tuple(t.files)) == 2
    cap = capsys.readouterr()
    assert cap.err == ''
    assert 'Exclude\t.*\\.jpg$' in cap.out
    assert 'File Count\t2' in cap.out


def test_multiple_excludes(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--exclude', '*.jpg', '--exclude-regex', 'txt$'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert len(tuple(t.files)) == 1

    cap = capsys.readouterr()
    assert 'Exclude\t*.jpg\ttxt$' in cap.out
    assert 'File Count\t1' in cap.out


def test_exclude_everything(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with patch('sys.exit') as mock_exit:
        run([content_path, '--exclude', '*'])
    mock_exit.assert_called_once_with(err.Code.READ)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: {content_path}: Empty or all files excluded\n'
    assert not os.path.exists(exp_torrent_filepath)


def test_include_glob(capsys, tmp_path):
    content = tmp_path / 'My Content'
    content.mkdir()
    new_file1 = content / 'file1.jpg'
    new_file1.write_text('image data')
    new_file2 = content / 'file2.jpg'
    new_file2.write_text('image data')

    exp_torrent_filepath = content.name + '.torrent'
    run([str(content), '--exclude', '*.jpg', '--include', '*file2*'])
    t = torf.Torrent.read(exp_torrent_filepath)
    assert tuple(t.files) == (torf.File('My Content/file2.jpg', size=10),)

    cap = capsys.readouterr()
    assert 'Exclude\t*.jpg' in cap.out
    assert 'Include\t*file2*' in cap.out
    assert 'File Count\t1' in cap.out


def test_include_regex(capsys, tmp_path):
    content = tmp_path / 'My Content'
    content.mkdir()
    new_file1 = content / 'file1.jpg'
    new_file1.write_text('image data')
    new_file2 = content / 'file2.jpg'
    new_file2.write_text('image data')

    exp_torrent_filepath = content.name + '.torrent'
    run([str(content), '--exclude', '*file*', '--include-regex', r'file2\.jpg$'])
    t = torf.Torrent.read(exp_torrent_filepath)
    assert tuple(t.files) == (torf.File('My Content/file2.jpg', size=10),)

    cap = capsys.readouterr()
    print(cap.out)
    assert 'Exclude\t*file*' in cap.out
    assert 'Include\tfile2\\.jpg$' in cap.out
    assert 'File Count\t1' in cap.out


def test_name_option(capsys, mock_content):
    content_path = str(mock_content)
    name = 'Your Torrent'
    exp_torrent_filename = f'{name}.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)
    wrong_torrent_filename = os.path.basename(content_path) + '.torrent'

    run([content_path, '--name', name])
    assert not os.path.exists(wrong_torrent_filename)

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.name == 'Your Torrent'

    cap = capsys.readouterr()
    assert f'Name\t{name}' in cap.out
    assert 'Torrent\tYour Torrent.torrent' in cap.out


def test_private_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--private', '--tracker', 'https://foo.bar:123/'])
    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.private is True

    cap = capsys.readouterr()
    assert 'Private\tyes' in cap.out

def test_private_enabled_and_no_trackers_given(capsys, mock_content):
    run([str(mock_content), '--private'])
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: WARNING: Torrent is private and has no trackers\n'
    assert os.path.exists(str(mock_content) + '.torrent')

def test_noprivate_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--private', '--noprivate'])
    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.private is False

    cap = capsys.readouterr()
    assert 'Private\tno' in cap.out

def test_missing_private_option_does_not_set_private_field(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path])
    t = torf.Torrent.read(exp_torrent_filepath)
    assert 'private' not in t.metainfo['info']
    assert t.private is None


def test_source_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--source', 'SOURCE'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.source == 'SOURCE'

    cap = capsys.readouterr()
    assert 'Source\tSOURCE' in cap.out


def test_nosource_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--source', 'SOURCE', '--nosource'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.source is None

    cap = capsys.readouterr()
    assert 'Source\t' not in cap.out


def test_xseed_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path])
    cap = capsys.readouterr()
    hash_line_1 = [line for line in cap.out.split('\n')
                   if 'Info Hash' in line][0]
    hash_1 = torf.Torrent.read(exp_torrent_filepath).infohash

    run([content_path, '--xseed', '--yes'])
    cap = capsys.readouterr()
    hash_line_2 = [line for line in cap.out.split('\n')
                   if 'Info Hash' in line][0]
    hash_2 = torf.Torrent.read(exp_torrent_filepath).infohash

    assert hash_line_1 != hash_line_2
    assert hash_1 != hash_2


def test_noxseed_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--xseed', '--noxseed'])
    cap = capsys.readouterr()
    hash_line_1 = [line for line in cap.out.split('\n')
                   if 'Info Hash' in line][0]
    hash_1 = torf.Torrent.read(exp_torrent_filepath).infohash

    run([content_path, '--yes'])
    cap = capsys.readouterr()
    hash_line_2 = [line for line in cap.out.split('\n')
                   if 'Info Hash' in line][0]
    hash_2 = torf.Torrent.read(exp_torrent_filepath).infohash

    assert hash_line_1 == hash_line_2
    assert hash_1 == hash_2


def test_max_piece_size_option_not_taking_effect(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content / 'large file'
    with open(large_file, 'ab') as f:
        f.truncate(2**20)
    content_path = str(mock_content)
    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        run([content_path, '--max-piece-size', '8'])
    cap = capsys.readouterr()
    piece_size = [line for line in cap.out.split('\n')
                  if 'Piece Size' in line][0].split('\t')[1]
    assert int(piece_size) < 8 * 1048576

def test_max_piece_size_option_smaller_than_default(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content / 'large file'
    with open(large_file, 'ab') as f:
        f.truncate(5**20)
    content_path = str(mock_content)
    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        run([content_path, '--max-piece-size', '2'])
    cap = capsys.readouterr()
    piece_size = [line for line in cap.out.split('\n')
                  if 'Piece Size' in line][0].split('\t')[1]
    assert int(piece_size) == 2 * 1048576

def test_max_piece_size_option_larger_than_default(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content / 'large file'
    with open(large_file, 'ab') as f:
        f.truncate(5**20)
    content_path = str(mock_content)
    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        run([content_path, '--max-piece-size', '128'])
    cap = capsys.readouterr()
    piece_size = [line for line in cap.out.split('\n')
                  if 'Piece Size' in line][0].split('\t')[1]
    assert int(piece_size) == 128 * 1048576

def test_max_piece_size_option_not_given(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content / 'large file'
    with open(large_file, 'ab') as f:
        f.truncate(2**40)
    content_path = str(mock_content)

    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        run([content_path])
    cap = capsys.readouterr()
    piece_size = [line for line in cap.out.split('\n')
                  if 'Piece Size' in line][0].split('\t')[1]
    assert int(piece_size) == torf.Torrent().piece_size_max

def test_max_piece_size_is_no_power_of_two(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content / 'large file'
    with open(large_file, 'ab') as f:
        f.truncate(2**40)
    content_path = str(mock_content)

    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        factor = 1.234
        exp_invalid_piece_size = int(factor * 2**20)
        with patch('sys.exit') as mock_exit:
            run([content_path, '--max-piece-size', str(factor)])
        mock_exit.assert_called_once_with(err.Code.CLI)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: Piece size must be divisible by 16 KiB: {exp_invalid_piece_size}\n'


def test_default_date(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    now = datetime.today().replace(microsecond=0)
    run([content_path])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert_approximate_date(t.creation_date, datetime.today())

    cap = capsys.readouterr()
    exp_dates = [int(now.timestamp()), int((now + timedelta(seconds=1)).timestamp())]
    assert any(f'Created\t{exp_date}' in cap.out for exp_date in exp_dates)


def test_date_today(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', 'today'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime.combine(date.today(), time(0, 0, 0))

    cap = capsys.readouterr()
    exp_date = int(datetime.today()
                   .replace(hour=0, minute=0, second=0, microsecond=0)
                   .timestamp())
    assert f'Created\t{exp_date}' in cap.out


def test_date_now(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    now = datetime.today()
    run([content_path, '--date', 'now'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert_approximate_date(t.creation_date, now)

    cap = capsys.readouterr()
    exp_dates = [int(now.timestamp()), int((now + timedelta(seconds=1)).timestamp())]
    assert any(f'Created\t{exp_date}' in cap.out for exp_date in exp_dates)


def test_user_given_date(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime.combine(date(2000, 1, 2), time(0, 0, 0))

    cap = capsys.readouterr()
    exp_date = int(datetime.strptime('2000-01-02', '%Y-%m-%d').timestamp())
    assert f'Created\t{exp_date}' in cap.out


def test_user_given_date_and_time(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02 03:04'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime(2000, 1, 2, 3, 4)

    cap = capsys.readouterr()
    exp_date = int(datetime.strptime('2000-01-02 03:04', '%Y-%m-%d %H:%M').timestamp())
    assert f'Created\t{exp_date}' in cap.out


def test_user_given_date_and_time_with_seconds(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02 03:04:05'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime(2000, 1, 2, 3, 4, 5)

    cap = capsys.readouterr()
    exp_date = int(datetime.strptime('2000-01-02 03:04:05', '%Y-%m-%d %H:%M:%S').timestamp())
    assert f'Created\t{exp_date}' in cap.out


def test_invalid_date(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with patch('sys.exit') as mock_exit:
        run([content_path, '--date', 'foo'])
    mock_exit.assert_called_once_with(err.Code.CLI)
    cap = capsys.readouterr()
    assert cap.err == f'{_vars.__appname__}: foo: Invalid date\n'
    assert not os.path.exists(exp_torrent_filepath)


def test_nodate_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02 03:04:05', '--nodate'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date is None

    cap = capsys.readouterr()
    assert 'Created\t' not in cap.out


def test_comment_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--comment', 'This is a comment.'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.comment == 'This is a comment.'

    cap = capsys.readouterr()
    assert 'Comment\tThis is a comment.' in cap.out


def test_nocomment_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--comment', 'This is a comment.', '--nocomment'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.comment is None

    cap = capsys.readouterr()
    assert 'Comment\t' not in cap.out


def test_creator_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--creator', 'Mbombo'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.created_by == 'Mbombo'

    cap = capsys.readouterr()
    assert 'Created By\tMbombo' in cap.out


def test_nocreator_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--nocreator'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.created_by is None

    cap = capsys.readouterr()
    assert 'Created By\t' not in cap.out


def test_single_tracker(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--tracker', 'https://mytracker.example.org'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.trackers == [['https://mytracker.example.org']]

    cap = capsys.readouterr()
    assert 'Tracker\thttps://mytracker.example.org' in cap.out


def test_multiple_trackers(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path,
         '--tracker', 'https://tracker1.example.org/foo',
         '--tracker', 'https://tracker2.example.org/bar/',
         '--tracker', 'https://tracker3.example.org/baz'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.trackers == [['https://tracker1.example.org/foo'],
                          ['https://tracker2.example.org/bar/'],
                          ['https://tracker3.example.org/baz']]

    cap = capsys.readouterr()
    assert 'Trackers\thttps://tracker1.example.org/foo' in cap.out
    assert '\thttps://tracker2.example.org/bar/' in cap.out
    assert '\thttps://tracker3.example.org/baz' in cap.out

def test_multiple_tracker_tiers(capsys, mock_content, human_readable, clear_ansi, regex):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with human_readable(True):
        run([content_path,
             '--tracker', 'http://foo,http://bar',
             '--tracker', 'http://a,http://b,http://c',
             '--tracker', 'http://asdf'])
        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.trackers == [['http://foo', 'http://bar'],
                              ['http://a', 'http://b', 'http://c'],
                              ['http://asdf']]
        cap = capsys.readouterr()
        assert clear_ansi(cap.out) == regex(r'^(\s*)Trackers  Tier 1: http://foo\n'
                                            r'\1                  http://bar\n'
                                            r'\1          Tier 2: http://a\n'
                                            r'\1                  http://b\n'
                                            r'\1                  http://c\n'
                                            r'\1          Tier 3: http://asdf\n',
                                            flags=re.MULTILINE)

    with human_readable(False):
        run([content_path, '-y',
             '--tracker', 'http://foo,http://bar',
             '--tracker', 'http://a,http://b,http://c',
             '--tracker', 'http://asdf'])
        t = torf.Torrent.read(exp_torrent_filepath)
        assert t.trackers == [['http://foo', 'http://bar'],
                              ['http://a', 'http://b', 'http://c'],
                              ['http://asdf']]
        cap = capsys.readouterr()
        assert cap.out == regex(r'^Trackers\thttp://foo\thttp://bar\t'
                                r'http://a\thttp://b\thttp://c\thttp://asdf\n',
                                flags=re.MULTILINE)

def test_notracker_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--tracker', 'https://mytracker.example.org', '--notracker'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.trackers == []

    cap = capsys.readouterr()
    assert 'Tracker\t' not in cap.out


def test_single_webseed(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--webseed', 'https://mywebseed.example.org/foo'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.webseeds == ['https://mywebseed.example.org/foo']

    cap = capsys.readouterr()
    assert 'Webseed\thttps://mywebseed.example.org/foo' in cap.out


def test_multiple_webseeds(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path,
         '--webseed', 'https://webseed1.example.org/foo',
         '--webseed', 'https://webseed2.example.org/bar/',
         '--webseed', 'https://webseed3.example.org/baz'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.webseeds == ['https://webseed1.example.org/foo',
                          'https://webseed2.example.org/bar/',
                          'https://webseed3.example.org/baz']

    cap = capsys.readouterr()
    assert 'Webseeds\thttps://webseed1.example.org/foo' in cap.out
    assert '\thttps://webseed2.example.org/bar/' in cap.out
    assert '\thttps://webseed3.example.org/baz' in cap.out


def test_nowebseed_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--webseed', 'https://mywebseed.example.org/foo', '--nowebseed'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.webseeds == []

    cap = capsys.readouterr()
    assert 'Webseed\t' not in cap.out


@pytest.mark.parametrize(
    argnames='merges, exp_result',
    argvalues=(
        (
            [
                '{"creation date": 1352534887}',
                '{"created by": null, "info": {"name": "New Name"}, "nosuchkey": null}',
                (
                    '{'
                    '"my stuff": {"my numbers": [57, [1, 2, 3]], "my strings": ["foo", "bar"]},'
                    '"info": {"foo": [{"bar": 123}, "baz"], "your strings": []}'
                    '}'
                ),
            ],
            {
                'creation_date': datetime(2012, 11, 10, 9, 8, 7),
                'created_by': None,
                'name': 'New Name',
                'path_map': {
                    ('my stuff', 'my numbers'): [57, [1, 2, 3]],
                    ('my stuff', 'my strings'): ['foo', 'bar'],
                    ('info', 'foo'): [{'bar': 123}, 'baz'],
                    ('info', 'your strings'): [],
                },
            },
        ),
        (
            ['"Hello, World!"'],
            err.CliError("Not a JSON object: Hello, World!"),
        ),
    ),
    ids=lambda v: repr(v),
)
def test_merge_option(merges, exp_result, capsys, mock_content, assert_torrents_equal, tmp_path):
    content_path = str(mock_content)
    torrent_filepath = str(tmp_path / 'my.torrent')
    cmd = [content_path, '-o', torrent_filepath]
    for merge in merges:
        cmd.extend(('--merge', merge))

    if isinstance(exp_result, err.Error):
        with patch('sys.exit') as mock_exit:
            run(cmd)
        mock_exit.assert_called_once_with(exp_result.exit_code)
        cap = capsys.readouterr()
        assert cap.err == f'{_vars.__appname__}: {str(exp_result)}\n'
        assert not os.path.exists(torrent_filepath)
    else:
        run(cmd)
        new = torf.Torrent.read(torrent_filepath)
        for attr, exp_value in exp_result.items():
            if attr == 'path_map':
                for path, exp_value in exp_value.items():
                    path = list(path)
                    value = new.metainfo
                    while path:
                        key = path.pop(0)
                        value = value[key]
                    assert value == exp_value
            else:
                value = getattr(new, attr)
                assert value == exp_value
