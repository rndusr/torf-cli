from torfcli._main import run
from torfcli import _errors as err
import pytest
from unittest.mock import patch, DEFAULT
import os
import torf
from datetime import datetime, date, time, timedelta


def assert_approximate_date(date1, date2):
    date_min = date2.replace(microsecond=0) - timedelta(seconds=1)
    date_max = date2.replace(microsecond=0) + timedelta(seconds=1)
    assert date_min <= date1 <= date_max


### Basic creation modes

def test_default_torrent_filepath(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    now = datetime.today()
    run([content_path])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.name == 'My Torrent'
    assert len(tuple(t.files)) == 3
    assert_approximate_date(t.creation_date, now)
    assert t.created_by.startswith('torf/')

    cap = capsys.readouterr()
    assert f'Magnet\tmagnet:?xt=urn:btih:' in cap.out
    assert f'Torrent\t{exp_torrent_filename}' in cap.out
    assert 'Name\tMy Torrent' in cap.out
    assert 'File Count\t3' in cap.out
    assert 'Info Hash' in cap.out
    assert 'Created By\ttorf' in cap.out


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
    assert t.created_by.startswith('torf/')

    cap = capsys.readouterr()
    assert f'Magnet\tmagnet:?xt=urn:btih:' in cap.out
    assert f'Torrent\t{exp_torrent_filename}' in cap.out
    assert 'Name\tMy Torrent' in cap.out
    assert 'File Count\t3' in cap.out
    assert 'Info Hash' in cap.out
    assert 'Created By\ttorf' in cap.out


### Error cases

def test_content_path_doesnt_exist(capsys):
    with pytest.raises(err.ReadError, match=r'^/path/doesnt/exist: No such file or directory$') as exc_info:
        run(['/path/doesnt/exist'])


def test_torrent_filepath_exists(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with open(exp_torrent_filepath, 'wb') as f:
        f.write(b'<torrent data>')

    with pytest.raises(err.WriteError, match=rf'^{exp_torrent_filepath}: File exists$') as exc_info:
        run([content_path, '--out', exp_torrent_filepath])


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
    assert f'Magnet\tmagnet:?xt=urn:btih:' in cap.out
    assert f'Torrent\t{exp_torrent_filename}' in cap.out


def test_single_exclude(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--exclude', '*.jpg'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert len(tuple(t.files)) == 2

    cap = capsys.readouterr()
    assert 'Exclude\t*.jpg' in cap.out
    assert 'File Count\t2' in cap.out


def test_multiple_excludes(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--exclude', '*.jpg', '--exclude', '*.txt'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert len(tuple(t.files)) == 1

    cap = capsys.readouterr()
    assert 'Exclude\t*.jpg\t*.txt' in cap.out
    assert 'File Count\t1' in cap.out


def test_exclude_everything(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with pytest.raises(err.ReadError, match=rf'^{content_path}: Empty directory$') as exc_info:
        run([content_path, '--exclude', '*'])


def test_name_option(capsys, mock_content):
    content_path = str(mock_content)
    name = 'Your Torrent'
    exp_torrent_filename = f'{name}.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)
    wrong_torrent_filename = os.path.basename(content_path) + '.torrent'

    run([content_path, '--name', name])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.name == 'Your Torrent'

    cap = capsys.readouterr()
    assert 'Torrent\tYour Torrent.torrent' in cap.out


def test_private_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--private', '--tracker', 'https://foo.bar:123/'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.private == True

    cap = capsys.readouterr()
    assert 'Private\tyes' in cap.out


def test_noprivate_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--private', '--noprivate'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.private == False

    cap = capsys.readouterr()
    assert 'Private\tno' in cap.out


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


def test_max_piece_size_option_given(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content.join('large file')
    with open(large_file, 'ab') as f:
        f.truncate(2**40)
    content_path = str(mock_content)

    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        run([content_path, '--max-piece-size', '2'])
    cap = capsys.readouterr()
    piece_size = [line for line in cap.out.split('\n')
                  if 'Piece Size' in line][0].split('\t')[1]
    assert piece_size == str(2 * 2**20)


def test_max_piece_size_option_not_given(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content.join('large file')
    with open(large_file, 'ab') as f:
        f.truncate(2**40)
    content_path = str(mock_content)

    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        run([content_path])
    cap = capsys.readouterr()
    piece_size = [line for line in cap.out.split('\n')
                  if 'Piece Size' in line][0].split('\t')[1]
    assert piece_size == str(16 * 2**20)


def test_max_piece_size_is_no_power_of_two(capsys, mock_content):
    # Create large sparse file, i.e. a file that isn't actually written to disk
    large_file = mock_content.join('large file')
    with open(large_file, 'ab') as f:
        f.truncate(2**40)
    content_path = str(mock_content)

    with patch.multiple('torfcli._main', _hash_pieces=DEFAULT, _write_torrent=DEFAULT):
        factor = 1.234
        exp_invalid_piece_size = int(factor*2**20)
        exp_error = rf'^Piece size must be a power of 2: {exp_invalid_piece_size}$'
        with pytest.raises(err.CliError, match=exp_error):
            run([content_path, '--max-piece-size', str(factor)])


def test_default_date(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    now = datetime.today().replace(microsecond=0)
    run([content_path])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert_approximate_date(t.creation_date, datetime.today())

    cap = capsys.readouterr()
    exp_dates = [now.isoformat(sep=' '),
                 (now + timedelta(seconds=1)).isoformat(sep=' ')]
    assert (f'Created\t{exp_dates[0]}' in cap.out or
            f'Created\t{exp_dates[1]}' in cap.out)


def test_date_today(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', 'today'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime.combine(date.today(), time(0, 0, 0))

    cap = capsys.readouterr()
    exp_date = date.today().isoformat() + ' 00:00:00'
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
    exp_date = now.isoformat(sep=' ', timespec='seconds')
    assert f'Created\t{exp_date}' in cap.out


def test_user_given_date(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime.combine(date(2000, 1, 2), time(0, 0, 0))

    cap = capsys.readouterr()
    exp_date = date(2000, 1, 2).isoformat() + ' 00:00:00'
    assert f'Created\t{exp_date}' in cap.out


def test_user_given_date_and_time(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02 03:04'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime(2000, 1, 2, 3, 4)

    cap = capsys.readouterr()
    exp_date = datetime(2000, 1, 2, 3, 4).isoformat(sep=' ', timespec='seconds')
    assert f'Created\t{exp_date}' in cap.out


def test_user_given_date_and_time_with_seconds(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02 03:04:05'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == datetime(2000, 1, 2, 3, 4, 5)

    cap = capsys.readouterr()
    exp_date = datetime(2000, 1, 2, 3, 4, 5).isoformat(sep=' ', timespec='seconds')
    assert f'Created\t{exp_date}' in cap.out


def test_invalid_date(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    with pytest.raises(err.CliError, match=r'^foo: Invalid date$'):
        run([content_path, '--date', 'foo'])


def test_nodate_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--date', '2000-01-02 03:04:05', '--nodate'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.creation_date == None

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


def test_notracker_option(capsys, mock_content):
    content_path = str(mock_content)
    exp_torrent_filename = os.path.basename(content_path) + '.torrent'
    exp_torrent_filepath = os.path.join(os.getcwd(), exp_torrent_filename)

    run([content_path, '--tracker', 'https://mytracker.example.org', '--notracker'])

    t = torf.Torrent.read(exp_torrent_filepath)
    assert t.trackers == None

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
    assert t.webseeds == None

    cap = capsys.readouterr()
    assert 'Webseed\t' not in cap.out
